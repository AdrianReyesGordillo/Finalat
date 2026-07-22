"""Fina Agent — Autonomous LLM-driven financial advisor using Bedrock Claude.

Unlike the rigid state machine, this agent uses Claude's tool_use capability
to autonomously decide when it has enough information to query instruments
and run the optimizer. The conversation feels natural and adaptive.

Architecture:
  1. Claude receives a system prompt defining Fina's personality and goals.
  2. Claude has access to tools: get_instruments, run_optimizer.
  3. Claude drives the conversation — asking questions naturally.
  4. When Claude decides it has enough info, it calls the tools.
  5. Claude then presents results in a friendly, personalized way.
"""

import asyncio
import json
import logging
import time
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.models.instruments import Instrument
from backend.services.optimizer import InstrumentData, Optimizer

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """Eres Fina, una asesora financiera inteligente y amigable para usuarios en México. Tu trabajo es ayudar a las personas a encontrar las mejores opciones para hacer crecer su dinero.

PERSONALIDAD:
- Eres cálida, directa y profesional
- Tuteas al usuario
- Usas español mexicano natural (sin ser demasiado informal)
- Eres concisa pero clara
- Nunca uses emojis

OBJETIVO:
Tu meta es entender la situación financiera del usuario para recomendarle la mejor distribución de inversión. Para esto necesitas recopilar:
1. Su nombre (para personalizar)
2. Cuánto dinero tiene disponible para invertir (o cuánto puede aportar mensualmente)
3. En qué plazo necesita el dinero (corto, mediano, largo)
4. Su tolerancia al riesgo (conservador, moderado, agresivo)
5. Si necesita liquidez inmediata o puede dejar el dinero quieto
6. Si estaría dispuesto a usar una tarjeta de débito/crédito para acceder a mejores tasas

FLUJO:
- Pregunta de forma conversacional, NO como un formulario
- Puedes inferir información del contexto (si dice "soy estudiante y tengo 5mil ahorrados", ya tienes el monto)
- Haz de 1 a 2 preguntas por mensaje, no bombardees al usuario
- Cuando tengas suficiente información, usa las herramientas para buscar instrumentos y calcular la mejor distribución
- Presenta los resultados de forma clara y amigable, explicando por qué cada instrumento fue elegido

REGLAS DE NEGOCIO:
- Solo hablas de finanzas personales en México
- Si preguntan sobre otro tema, redirige amablemente a finanzas
- Las tasas son referenciales y pueden variar
- Nunca prometas rendimientos garantizados
- Si el usuario no tiene claro el plazo o riesgo, ayúdalo con ejemplos prácticos

HERRAMIENTAS:
Tienes acceso a herramientas para consultar instrumentos financieros disponibles y calcular la distribución óptima. Úsalas cuando tengas la información necesaria del usuario."""

# ---------------------------------------------------------------------------
# Tool Definitions (Bedrock Converse toolConfig format)
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS = [
    {
        "toolSpec": {
            "name": "get_available_instruments",
            "description": "Consulta los instrumentos financieros disponibles en la base de datos (CETES, cuentas de ahorro, fondos, etc). Devuelve nombre, tasa, riesgo, liquidez y montos mínimos/máximos.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "risk_filter": {
                            "type": "string",
                            "description": "Filtrar por nivel de riesgo: 'low', 'medium', 'high', o 'all' para ver todos.",
                            "enum": ["low", "medium", "high", "all"],
                        }
                    },
                    "required": [],
                }
            },
        }
    },
    {
        "toolSpec": {
            "name": "calculate_optimal_distribution",
            "description": "Calcula la distribución óptima de inversión basada en el capital del usuario, tolerancia al riesgo y preferencias de liquidez. Devuelve qué porcentaje poner en cada instrumento y el rendimiento esperado.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "total_capital": {
                            "type": "number",
                            "description": "Monto total a invertir en pesos mexicanos.",
                        },
                        "risk_tolerance": {
                            "type": "string",
                            "description": "Tolerancia al riesgo del usuario.",
                            "enum": ["low", "medium", "high"],
                        },
                        "liquidity_preference": {
                            "type": "string",
                            "description": "Preferencia de liquidez: 'immediate' (necesita el dinero disponible), 'short-term' (puede esperar días), 'flexible' (puede dejarlo quieto meses).",
                            "enum": ["immediate", "short-term", "flexible"],
                        },
                        "max_instruments": {
                            "type": "integer",
                            "description": "Máximo de instrumentos a recomendar (default: 5).",
                        },
                    },
                    "required": ["total_capital", "risk_tolerance", "liquidity_preference"],
                }
            },
        }
    },
]

# ---------------------------------------------------------------------------
# Greeting
# ---------------------------------------------------------------------------

GREETING = (
    "Hola, soy **Fina**, tu asesora financiera. "
    "Estoy aquí para ayudarte a encontrar las mejores opciones "
    "para hacer crecer tu dinero en México.\n\n"
    "Para empezar, ¿cómo te llamas y qué te trae por aquí?"
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_OUTPUT_TOKENS = 2048
TEMPERATURE = 0.7
BEDROCK_TIMEOUT = 30
MAX_TOOL_ITERATIONS = 3  # Max tool call loops before forcing a text response


# ---------------------------------------------------------------------------
# Tool Execution
# ---------------------------------------------------------------------------


async def _execute_tool(
    tool_name: str, tool_input: dict, db: AsyncSession
) -> dict:
    """Execute a tool call and return the result as a dict."""

    if tool_name == "get_available_instruments":
        return await _tool_get_instruments(tool_input, db)
    elif tool_name == "calculate_optimal_distribution":
        return await _tool_calculate_distribution(tool_input, db)
    else:
        return {"error": f"Unknown tool: {tool_name}"}


async def _tool_get_instruments(params: dict, db: AsyncSession) -> dict:
    """Fetch available instruments from the database."""
    risk_filter = params.get("risk_filter", "all")

    stmt = select(Instrument).where(Instrument.last_fetch_status == "success")
    if risk_filter != "all":
        stmt = stmt.where(Instrument.risk_level == risk_filter)

    result = await db.execute(stmt)
    instruments = result.scalars().all()

    if not instruments:
        return {"instruments": [], "message": "No hay instrumentos disponibles con esos criterios."}

    data = []
    for inst in instruments:
        data.append({
            "name": inst.name,
            "institution": inst.institution if hasattr(inst, "institution") else "N/A",
            "annual_rate": float(inst.annual_rate),
            "risk_level": inst.risk_level,
            "liquidity_tier": inst.liquidity_tier,
            "min_investment": float(inst.min_investment),
            "max_investment": float(inst.max_investment) if inst.max_investment else None,
        })

    return {"instruments": data, "count": len(data)}


async def _tool_calculate_distribution(params: dict, db: AsyncSession) -> dict:
    """Run the optimizer with the given parameters."""
    total_capital = float(params.get("total_capital", 0))
    risk_tolerance = params.get("risk_tolerance", "medium")
    liquidity_preference = params.get("liquidity_preference", "flexible")
    max_instruments = int(params.get("max_instruments", 5))

    if total_capital <= 0:
        return {"error": "El capital debe ser mayor a 0."}

    # Fetch instruments
    stmt = select(Instrument).where(Instrument.last_fetch_status == "success")
    result = await db.execute(stmt)
    instruments = result.scalars().all()

    if not instruments:
        return {"error": "No hay instrumentos disponibles para calcular."}

    # Convert to optimizer format
    instrument_data = [
        InstrumentData(
            id=inst.id,
            name=inst.name,
            annual_rate=float(inst.annual_rate),
            min_investment=float(inst.min_investment),
            max_investment=float(inst.max_investment) if inst.max_investment else None,
            risk_level=inst.risk_level,
            liquidity_tier=inst.liquidity_tier,
            tiered_rates=inst.tiered_rates,
        )
        for inst in instruments
    ]

    # Run optimizer
    optimizer = Optimizer(instrument_data)
    output = optimizer.allocate(
        total_capital=total_capital,
        risk_tolerance=risk_tolerance,
        liquidity_preference=liquidity_preference,
        max_instruments=max_instruments,
    )

    allocations = [
        {
            "instrument_name": a.instrument_name,
            "allocated_amount": a.allocated_amount,
            "effective_rate": a.effective_rate,
            "projected_annual_return": a.projected_annual_return,
        }
        for a in output.allocations
    ]

    return {
        "allocations": allocations,
        "total_expected_return": output.total_expected_return,
        "unallocated_capital": output.unallocated_capital,
        "message": output.message,
    }


# ---------------------------------------------------------------------------
# Bedrock Converse with Tool Use
# ---------------------------------------------------------------------------


def _create_bedrock_client() -> Any:
    """Create a boto3 Bedrock Runtime client."""
    client_kwargs: dict[str, Any] = {
        "service_name": "bedrock-runtime",
        "region_name": settings.AWS_REGION,
    }
    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        client_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
        client_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
    return boto3.client(**client_kwargs)


def _converse_sync(
    client: Any,
    model_id: str,
    system_prompt: str,
    messages: list[dict],
    tools: list[dict],
) -> dict:
    """Synchronous Bedrock Converse API call with tool support.

    Returns the raw response dict from the Converse API.
    """
    request_params: dict[str, Any] = {
        "modelId": model_id,
        "system": [{"text": system_prompt}],
        "messages": messages,
        "inferenceConfig": {
            "maxTokens": MAX_OUTPUT_TOKENS,
            "temperature": TEMPERATURE,
        },
    }

    if tools:
        request_params["toolConfig"] = {"tools": tools}

    return client.converse(**request_params)


def _parse_response(response: dict) -> tuple[str | None, list[dict]]:
    """Parse Bedrock Converse response into text and tool_use blocks.

    Returns:
        (text_content, tool_calls) where tool_calls is a list of
        {tool_use_id, name, input} dicts.
    """
    output = response.get("output", {})
    message = output.get("message", {})
    content_blocks = message.get("content", [])

    text_parts = []
    tool_calls = []

    for block in content_blocks:
        if "text" in block:
            text_parts.append(block["text"])
        elif "toolUse" in block:
            tool_use = block["toolUse"]
            tool_calls.append({
                "tool_use_id": tool_use["toolUseId"],
                "name": tool_use["name"],
                "input": tool_use["input"],
            })

    text = "\n".join(text_parts) if text_parts else None
    return text, tool_calls


# ---------------------------------------------------------------------------
# Main Agent Function
# ---------------------------------------------------------------------------


async def fina_chat(
    conversation_messages: list[dict],
    db: AsyncSession,
) -> tuple[str, dict | None]:
    """Run the Fina agent with tool-use loop.

    Args:
        conversation_messages: List of messages in Bedrock Converse format.
            Each message has 'role' ('user'|'assistant') and 'content' (list of blocks).
        db: Database session for tool execution.

    Returns:
        (assistant_text, investment_result) where investment_result is the
        optimizer output dict if a calculation was performed, else None.
    """
    start_time = time.time()
    investment_result = None

    try:
        client = _create_bedrock_client()

        messages = list(conversation_messages)
        iterations = 0

        while iterations < MAX_TOOL_ITERATIONS:
            iterations += 1

            # Call Bedrock
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    _converse_sync,
                    client,
                    settings.BEDROCK_MODEL_ID,
                    SYSTEM_PROMPT,
                    messages,
                    TOOL_DEFINITIONS,
                ),
                timeout=BEDROCK_TIMEOUT,
            )

            stop_reason = response.get("stopReason", "")
            text_content, tool_calls = _parse_response(response)

            # If no tool calls, we're done — return the text
            if not tool_calls:
                final_text = text_content or "Lo siento, no pude generar una respuesta."
                latency_ms = (time.time() - start_time) * 1000
                logger.info(
                    "Fina agent completed",
                    extra={"latency_ms": round(latency_ms), "iterations": iterations},
                )
                return final_text, investment_result

            # Tool calls detected — execute them and continue the loop
            # First, add the assistant's response (with tool_use blocks) to messages
            assistant_content = []
            if text_content:
                assistant_content.append({"text": text_content})
            for tc in tool_calls:
                assistant_content.append({
                    "toolUse": {
                        "toolUseId": tc["tool_use_id"],
                        "name": tc["name"],
                        "input": tc["input"],
                    }
                })
            messages.append({"role": "assistant", "content": assistant_content})

            # Execute each tool and build toolResult blocks
            tool_results_content = []
            for tc in tool_calls:
                result = await _execute_tool(tc["name"], tc["input"], db)

                # Capture optimizer results for the response
                if tc["name"] == "calculate_optimal_distribution" and "allocations" in result:
                    investment_result = result

                tool_results_content.append({
                    "toolResult": {
                        "toolUseId": tc["tool_use_id"],
                        "content": [{"json": result}],
                    }
                })

            # Add tool results as a user message
            messages.append({"role": "user", "content": tool_results_content})

        # If we exhausted iterations, return whatever text we have
        final_text = text_content or "Ya tengo la información. Permíteme un momento para procesarla."
        return final_text, investment_result

    except asyncio.TimeoutError:
        logger.warning("Fina agent timed out after %.1fs", time.time() - start_time)
        return (
            "Lo siento, tardé demasiado en procesar tu consulta. ¿Puedes intentar de nuevo?",
            None,
        )
    except (ClientError, BotoCoreError) as e:
        logger.error("Bedrock API error in fina_agent: %s", str(e))
        return (
            "Lo siento, no pude conectarme al servicio de IA en este momento. Intenta de nuevo en unos segundos.",
            None,
        )
    except Exception as e:
        logger.error("Unexpected error in fina_agent: %s: %s", type(e).__name__, str(e))
        return (
            "Ocurrió un error inesperado. Por favor intenta de nuevo.",
            None,
        )
