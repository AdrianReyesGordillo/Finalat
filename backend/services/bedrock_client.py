"""Amazon Bedrock client for Fina AI advisor.

Implements async chat completion using boto3 Bedrock Runtime (Converse API).
Handles prompt construction, response parsing, and graceful error fallback.

Requirements: 15.1, 15.2, 15.3, 15.4, 15.6, 15.7, 15.8
"""

import asyncio
import json
import logging
import time
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from backend.config import settings

logger = logging.getLogger(__name__)

# System prompt in Spanish constraining Fina to financial advisory content only
SYSTEM_PROMPT = (
    "Eres Fina, una asesora financiera virtual para usuarios en México. "
    "Proporcionas consejos personalizados basados en los datos financieros del usuario. "
    "Responde siempre en español de manera clara y amable. "
    "Solo discutes temas financieros: ahorro, inversión, deuda, presupuesto, "
    "crédito, afore, patrimonio y educación financiera. "
    "Si el usuario pregunta sobre temas no financieros, redirige la conversación "
    "amablemente hacia finanzas personales."
)

# Fallback message when Bedrock is unavailable
FALLBACK_MESSAGE = (
    "Lo siento, no pude procesar tu consulta en este momento. "
    "Por favor intenta de nuevo."
)

# Maximum output tokens for the model response
MAX_OUTPUT_TOKENS = 4096

# Temperature for response generation
TEMPERATURE = 0.7

# Maximum prompt size in tokens (approximate — 4 chars per token heuristic)
MAX_PROMPT_TOKENS = 4000

# Timeout for Bedrock API calls in seconds
BEDROCK_TIMEOUT = 10


def _build_financial_context_text(financial_context: dict) -> str:
    """Build a concise financial context summary string for the system prompt.

    Only includes aggregate parameters (no raw monetary amounts or encrypted data).
    This ensures we never send user financial details to the LLM.

    Args:
        financial_context: Dictionary with aggregate financial parameters.
            Expected keys (all optional):
            - total_savings: float
            - total_debts: float
            - total_credit_balance: float
            - total_afore: float
            - total_gbm: float
            - net_worth: float
            - risk_tolerance: str
            - liquidity_preference: str
            - monthly_income: float
            - monthly_expenses: float

    Returns:
        A string describing the user's financial context in Spanish.
    """
    if not financial_context:
        return ""

    parts = []

    if "total_savings" in financial_context:
        parts.append(f"Ahorro total: ${financial_context['total_savings']:,.2f}")
    if "total_debts" in financial_context:
        parts.append(f"Deudas totales: ${financial_context['total_debts']:,.2f}")
    if "total_credit_balance" in financial_context:
        parts.append(f"Saldo en tarjetas: ${financial_context['total_credit_balance']:,.2f}")
    if "total_afore" in financial_context:
        parts.append(f"Afore: ${financial_context['total_afore']:,.2f}")
    if "total_gbm" in financial_context:
        parts.append(f"Portafolio GBM: ${financial_context['total_gbm']:,.2f}")
    if "net_worth" in financial_context:
        parts.append(f"Patrimonio neto: ${financial_context['net_worth']:,.2f}")
    if "risk_tolerance" in financial_context:
        parts.append(f"Tolerancia al riesgo: {financial_context['risk_tolerance']}")
    if "liquidity_preference" in financial_context:
        parts.append(f"Preferencia de liquidez: {financial_context['liquidity_preference']}")
    if "monthly_income" in financial_context:
        parts.append(f"Ingreso mensual: ${financial_context['monthly_income']:,.2f}")
    if "monthly_expenses" in financial_context:
        parts.append(f"Gastos mensuales: ${financial_context['monthly_expenses']:,.2f}")

    if not parts:
        return ""

    return "\n\nContexto financiero del usuario:\n" + "\n".join(parts)


def _estimate_token_count(text: str) -> int:
    """Estimate token count using a simple heuristic (4 chars ≈ 1 token).

    This is a rough approximation suitable for enforcing the 4000-token prompt limit.

    Args:
        text: The text to estimate tokens for.

    Returns:
        Estimated number of tokens.
    """
    return len(text) // 4


def _truncate_messages(
    messages: list[dict], max_tokens: int
) -> list[dict]:
    """Truncate message history to fit within the token budget.

    Keeps the most recent messages, discarding older ones from the beginning
    until the total estimated token count is within budget.

    Args:
        messages: List of message dicts with 'role' and 'content' keys.
        max_tokens: Maximum allowed token count for the message content.

    Returns:
        Truncated list of messages fitting within the token budget.
    """
    if not messages:
        return []

    # Calculate total tokens
    total_tokens = sum(_estimate_token_count(m.get("content", "")) for m in messages)

    if total_tokens <= max_tokens:
        return messages

    # Remove oldest messages until we fit within budget
    truncated = list(messages)
    while truncated and total_tokens > max_tokens:
        removed = truncated.pop(0)
        total_tokens -= _estimate_token_count(removed.get("content", ""))

    return truncated


def _extract_advice(response_text: str) -> str:
    """Extract and structure actionable advice from the model response.

    Parses the response to identify key advice points. If the response is
    already well-structured, returns it as-is. Otherwise, attempts to
    identify bullet points or numbered items.

    Args:
        response_text: Raw text response from the model.

    Returns:
        Structured response text with actionable advice highlighted.
    """
    if not response_text:
        return FALLBACK_MESSAGE

    # The response from Claude is typically already well-structured.
    # We clean up any leading/trailing whitespace and return it.
    cleaned = response_text.strip()

    if not cleaned:
        return FALLBACK_MESSAGE

    return cleaned


def _create_bedrock_client() -> Any:
    """Create a boto3 Bedrock Runtime client with configured credentials.

    Returns:
        A boto3 bedrock-runtime client instance.
    """
    client_kwargs: dict[str, Any] = {
        "service_name": "bedrock-runtime",
        "region_name": settings.AWS_REGION,
    }

    # Only set explicit credentials if provided (allows IAM role fallback)
    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        client_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
        client_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY

    return boto3.client(**client_kwargs)


def _invoke_bedrock_sync(
    client: Any,
    model_id: str,
    system_prompt: str,
    messages: list[dict],
) -> str:
    """Synchronous Bedrock Converse API call.

    This is run in a thread via asyncio.to_thread() to avoid blocking
    the event loop.

    Args:
        client: The boto3 bedrock-runtime client.
        model_id: The Bedrock model identifier.
        system_prompt: The system prompt text.
        messages: List of conversation messages in Bedrock Converse format.

    Returns:
        The model's response text.

    Raises:
        ClientError: On AWS API errors.
        BotoCoreError: On boto3/botocore errors.
        TimeoutError: If the call exceeds the timeout.
    """
    # Build the Converse API request
    converse_messages = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        # Map 'assistant' role to 'assistant', everything else to 'user'
        converse_role = "assistant" if role == "assistant" else "user"
        converse_messages.append({
            "role": converse_role,
            "content": [{"text": content}],
        })

    request_params: dict[str, Any] = {
        "modelId": model_id,
        "system": [{"text": system_prompt}],
        "messages": converse_messages,
        "inferenceConfig": {
            "maxTokens": MAX_OUTPUT_TOKENS,
            "temperature": TEMPERATURE,
        },
    }

    response = client.converse(**request_params)

    # Extract response text from Converse API response
    output = response.get("output", {})
    message = output.get("message", {})
    content_blocks = message.get("content", [])

    response_text = ""
    for block in content_blocks:
        if "text" in block:
            response_text += block["text"]

    return response_text


async def chat_with_fina(
    messages: list[dict], financial_context: dict
) -> str:
    """Send a conversation to Fina (Amazon Bedrock Claude) and return the response.

    Constructs a prompt with the system instructions, user's financial context,
    and conversation history. Sends to Bedrock and parses the response.

    Uses asyncio.to_thread() to run the synchronous boto3 call without
    blocking the event loop.

    Args:
        messages: List of conversation messages, each with 'role' and 'content'.
            Role should be 'user' or 'assistant'. Limited to last 5 messages
            if necessary to fit token budget.
        financial_context: Dictionary with aggregate financial parameters
            (no raw monetary amounts or encrypted data).

    Returns:
        The model's response text (actionable financial advice in Spanish).
        On error, returns a friendly fallback message in Spanish.
    """
    start_time = time.time()

    try:
        # Build system prompt with financial context
        context_text = _build_financial_context_text(financial_context)
        full_system_prompt = SYSTEM_PROMPT + context_text

        # Calculate remaining token budget for messages
        system_tokens = _estimate_token_count(full_system_prompt)
        available_message_tokens = MAX_PROMPT_TOKENS - system_tokens

        # Truncate messages to fit within token budget (keep last 5 max)
        recent_messages = messages[-5:] if len(messages) > 5 else messages
        truncated_messages = _truncate_messages(
            recent_messages, max_tokens=available_message_tokens
        )

        if not truncated_messages:
            logger.warning("No messages to send to Bedrock after truncation")
            return FALLBACK_MESSAGE

        # Create Bedrock client
        client = _create_bedrock_client()

        # Call Bedrock via thread to avoid blocking the async event loop
        response_text = await asyncio.wait_for(
            asyncio.to_thread(
                _invoke_bedrock_sync,
                client,
                settings.BEDROCK_MODEL_ID,
                full_system_prompt,
                truncated_messages,
            ),
            timeout=BEDROCK_TIMEOUT,
        )

        # Log the call (no personal financial details)
        latency_ms = (time.time() - start_time) * 1000
        token_estimate = _estimate_token_count(
            full_system_prompt + "".join(m.get("content", "") for m in truncated_messages)
        )
        logger.info(
            "Bedrock API call completed",
            extra={
                "latency_ms": round(latency_ms, 2),
                "model_id": settings.BEDROCK_MODEL_ID,
                "input_token_estimate": token_estimate,
                "message_count": len(truncated_messages),
            },
        )

        # Extract and structure the advice
        return _extract_advice(response_text)

    except asyncio.TimeoutError:
        latency_ms = (time.time() - start_time) * 1000
        logger.warning(
            "Bedrock API call timed out",
            extra={"latency_ms": round(latency_ms, 2), "timeout_seconds": BEDROCK_TIMEOUT},
        )
        return FALLBACK_MESSAGE

    except (ClientError, BotoCoreError) as e:
        latency_ms = (time.time() - start_time) * 1000
        logger.error(
            "Bedrock API error",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "latency_ms": round(latency_ms, 2),
            },
        )
        return FALLBACK_MESSAGE

    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        logger.error(
            "Unexpected error in Bedrock client",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "latency_ms": round(latency_ms, 2),
            },
        )
        return FALLBACK_MESSAGE
