"""Advisor router — Fina AI financial advisor endpoints.

Wires together: State Machine + Bedrock Client + Optimizer.
Provides:
  POST /api/advisor/chat   — send a message to Fina
  POST /api/advisor/reset  — reset the conversation session
  GET  /api/advisor/session — get current session state

Handles Bedrock timeout/errors with fallback rule-based responses.
Includes a financial context summary in Bedrock prompts (no raw encrypted data).

Requirements: 15.5, 15.11, 15.12, 15.13, 15.14, 15.15, 14.6, 14.7
"""

import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.ahorro import Ahorro
from backend.models.afore import Afore
from backend.models.creditos import Credito
from backend.models.database import get_db
from backend.models.deudas import Deuda
from backend.models.gbm_portfolio import GbmPortfolio
from backend.models.instruments import Instrument
from backend.services.bedrock_client import FALLBACK_MESSAGE, chat_with_fina
from backend.services.encryption import EncryptionError, encryption_service
from backend.services.optimizer import InstrumentData, Optimizer
from backend.services.state_machine import ConversationState, StateMachine
from backend.utils.response import error_response, success_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/advisor", tags=["advisor"])


# ---------------------------------------------------------------------------
# Load fallback messages from JSON config
# ---------------------------------------------------------------------------

_FALLBACK_MESSAGES_PATH = Path(__file__).resolve().parent.parent / "fallback_messages.json"

try:
    with open(_FALLBACK_MESSAGES_PATH, "r", encoding="utf-8") as _f:
        FALLBACK_MESSAGES: dict[str, str] = json.load(_f)
except (FileNotFoundError, json.JSONDecodeError) as exc:
    logger.warning("Could not load fallback_messages.json: %s", exc)
    FALLBACK_MESSAGES = {}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    """Request body for the advisor chat endpoint."""

    message: str = Field(
        ..., min_length=1, max_length=2000, description="User message text."
    )


class ChatResponse(BaseModel):
    """Response body for the advisor chat endpoint."""

    message: str
    state: str
    done: bool = False
    allocations: list[dict] | None = None
    ai_limited: bool = False


class SessionResponse(BaseModel):
    """Response body for the session endpoint."""

    session_id: str
    state: str
    interaction_count: int
    collected_params: dict | None = None
    messages: list[dict] = []


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------


def get_current_user_id(request: Request) -> str:
    """Extract user_id from request.state (set by auth middleware)."""
    return request.state.user_id


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_fallback_message(state: str) -> str:
    """Get a fallback message for the given state, or a generic financial tip."""
    msg = FALLBACK_MESSAGES.get(state)
    if msg:
        return msg
    return FALLBACK_MESSAGES.get(
        "fallback_tip",
        "Lo siento, no pude procesar tu consulta en este momento.",
    )


async def _build_financial_context(
    db: AsyncSession, user_id: str
) -> dict:
    """Build a summary of the user's financial data for Bedrock prompt context.

    Returns aggregate figures only (no raw encrypted data).
    Silently handles decryption failures — partial data is fine here.
    """
    context: dict = {}

    # Ahorro total
    try:
        stmt = select(Ahorro).where(Ahorro.user_id == user_id)
        result = await db.execute(stmt)
        entries = result.scalars().all()
        total = 0.0
        for entry in entries:
            try:
                total += float(encryption_service.decrypt(entry.amount_encrypted))
            except (EncryptionError, ValueError, TypeError):
                pass
        if total > 0:
            context["total_savings"] = round(total, 2)
    except Exception:
        pass

    # Deudas total
    try:
        stmt = select(Deuda).where(Deuda.user_id == user_id)
        result = await db.execute(stmt)
        entries = result.scalars().all()
        total = 0.0
        for entry in entries:
            try:
                total += float(encryption_service.decrypt(entry.total_amount_encrypted))
            except (EncryptionError, ValueError, TypeError):
                pass
        if total > 0:
            context["total_debts"] = round(total, 2)
    except Exception:
        pass

    # Creditos total
    try:
        stmt = select(Credito).where(Credito.user_id == user_id)
        result = await db.execute(stmt)
        entries = result.scalars().all()
        total = 0.0
        for entry in entries:
            try:
                total += float(encryption_service.decrypt(entry.balance_encrypted))
            except (EncryptionError, ValueError, TypeError):
                pass
        if total > 0:
            context["total_credit_balance"] = round(total, 2)
    except Exception:
        pass

    # Afore total
    try:
        stmt = select(Afore).where(Afore.user_id == user_id)
        result = await db.execute(stmt)
        entries = result.scalars().all()
        total = 0.0
        for entry in entries:
            try:
                total += float(encryption_service.decrypt(entry.balance_encrypted))
            except (EncryptionError, ValueError, TypeError):
                pass
        if total > 0:
            context["total_afore"] = round(total, 2)
    except Exception:
        pass

    # GBM total
    try:
        stmt = select(GbmPortfolio).where(GbmPortfolio.user_id == user_id)
        result = await db.execute(stmt)
        entries = result.scalars().all()
        total = 0.0
        for entry in entries:
            try:
                total += float(encryption_service.decrypt(entry.market_value_encrypted))
            except (EncryptionError, ValueError, TypeError):
                pass
        if total > 0:
            context["total_gbm"] = round(total, 2)
    except Exception:
        pass

    # Compute net worth if we have data
    assets = context.get("total_savings", 0) + context.get("total_afore", 0) + context.get("total_gbm", 0)
    liabilities = context.get("total_debts", 0) + context.get("total_credit_balance", 0)
    if assets > 0 or liabilities > 0:
        context["net_worth"] = round(assets - liabilities, 2)

    return context


async def _run_optimizer(db: AsyncSession, params: dict) -> dict:
    """Run the optimizer with collected parameters and available instruments.

    Returns a dict with allocation results suitable for the response.
    """
    # Fetch instruments with successful status
    stmt = select(Instrument).where(Instrument.last_fetch_status == "success")
    result = await db.execute(stmt)
    instruments = result.scalars().all()

    if not instruments:
        return {
            "allocations": [],
            "total_expected_return": 0.0,
            "unallocated_capital": params.get("total_capital", 0),
            "message": "No hay instrumentos disponibles para la asignación.",
        }

    # Convert DB models to optimizer data objects
    instrument_data = [
        InstrumentData(
            id=inst.id,
            name=inst.name,
            annual_rate=float(inst.annual_rate),
            min_investment=float(inst.min_investment),
            max_investment=float(inst.max_investment) if inst.max_investment is not None else None,
            risk_level=inst.risk_level,
            liquidity_tier=inst.liquidity_tier,
            tiered_rates=inst.tiered_rates,
        )
        for inst in instruments
    ]

    # Run optimizer
    optimizer = Optimizer(instrument_data)
    output = optimizer.allocate(
        total_capital=float(params.get("total_capital", 0)),
        risk_tolerance=params.get("risk_tolerance", "medium"),
        liquidity_preference=params.get("liquidity_preference", "flexible"),
        max_instruments=int(params.get("max_instruments", 5)),
    )

    return {
        "allocations": [
            {
                "instrument_name": a.instrument_name,
                "allocated_amount": a.allocated_amount,
                "effective_rate": a.effective_rate,
                "projected_annual_return": a.projected_annual_return,
            }
            for a in output.allocations
        ],
        "total_expected_return": output.total_expected_return,
        "unallocated_capital": output.unallocated_capital,
        "message": output.message,
    }


def _format_optimizer_results(results: dict) -> str:
    """Format optimizer results into a user-friendly message in Spanish."""
    allocations = results.get("allocations", [])
    if not allocations:
        msg = results.get("message", "No hay instrumentos disponibles.")
        return f"Resultado: {msg}"

    lines = ["📊 **Recomendación de inversión:**\n"]
    for i, alloc in enumerate(allocations, 1):
        lines.append(
            f"{i}. **{alloc['instrument_name']}** — "
            f"${alloc['allocated_amount']:,.2f} "
            f"(tasa: {alloc['effective_rate']:.2f}%, "
            f"rendimiento anual: ${alloc['projected_annual_return']:,.2f})"
        )

    lines.append(
        f"\n💰 Rendimiento total esperado: ${results['total_expected_return']:,.2f}/año"
    )
    if results["unallocated_capital"] > 0:
        lines.append(
            f"⚠️ Capital sin asignar: ${results['unallocated_capital']:,.2f}"
        )

    return "\n".join(lines)


def _is_fallback_response(response: str) -> bool:
    """Check if Bedrock returned the fallback message (indicating failure)."""
    return response == FALLBACK_MESSAGE


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/chat")
async def advisor_chat(
    body: ChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Send a message to the Fina AI advisor.

    Advances the state machine, runs the optimizer when ready,
    and routes follow-up questions to Bedrock for contextual answers.
    On Bedrock errors/timeouts, falls back to rule-based responses.
    """
    # Initialize state machine
    sm = StateMachine(db_session=db, user_id=user_id)
    await sm.get_or_create_session()

    current_state = sm.get_state()

    # If in FOLLOW_UP and the input is not a control command, route to Bedrock
    if current_state == ConversationState.FOLLOW_UP:
        text_lower = body.message.strip().lower()
        is_control = text_lower in (
            "ajustar", "adjust", "cambiar",
            "terminar", "end", "salir", "exit",
        )

        if not is_control:
            # Route to Bedrock for contextual answer
            return await _handle_follow_up_question(sm, db, user_id, body.message)

    # Process input through state machine
    result = await sm.process_input(body.message)

    # If optimizer is needed, run it
    allocations_data = None
    ai_limited = False

    if result.needs_optimizer and result.collected_params:
        optimizer_results = await _run_optimizer(db, result.collected_params)
        allocations_data = optimizer_results.get("allocations")

        # Format results message
        formatted_msg = _format_optimizer_results(optimizer_results)

        # Transition to PRESENT_RESULTS
        await sm.transition_state(ConversationState.PRESENT_RESULTS)
        await sm.add_message("assistant", formatted_msg)

        return JSONResponse(
            status_code=200,
            content=success_response(
                ChatResponse(
                    message=formatted_msg,
                    state=ConversationState.PRESENT_RESULTS.value,
                    done=False,
                    allocations=allocations_data,
                    ai_limited=False,
                ).model_dump()
            ),
        )

    return JSONResponse(
        status_code=200,
        content=success_response(
            ChatResponse(
                message=result.message,
                state=result.state.value,
                done=result.done,
                allocations=None,
                ai_limited=ai_limited,
            ).model_dump()
        ),
    )


async def _handle_follow_up_question(
    sm: StateMachine, db: AsyncSession, user_id: str, message: str
) -> JSONResponse:
    """Handle a follow-up question by routing to Bedrock with financial context.

    Falls back to a rule-based response if Bedrock is unavailable.
    """
    ai_limited = False

    # Record user message in session
    await sm.add_message("user", message)

    # Build financial context for Bedrock prompt
    financial_context = await _build_financial_context(db, user_id)

    # Get conversation history for context
    session = await sm.get_or_create_session()
    messages = session.messages or []

    # Send to Bedrock
    bedrock_messages = [
        {"role": m["role"], "content": m["content"]}
        for m in messages[-5:]  # Last 5 messages for context
    ]

    response_text = await chat_with_fina(bedrock_messages, financial_context)

    # Check if Bedrock returned the fallback (indicating error/timeout)
    if _is_fallback_response(response_text):
        ai_limited = True
        # Provide a pre-baked financial tip as fallback
        response_text = _get_fallback_message("fallback_tip")
        ai_notice = FALLBACK_MESSAGES.get("ai_limited", "")
        if ai_notice:
            response_text = f"{ai_notice}\n\n{response_text}"

    # Record assistant response in session
    await sm.add_message("assistant", response_text)

    return JSONResponse(
        status_code=200,
        content=success_response(
            ChatResponse(
                message=response_text,
                state=ConversationState.FOLLOW_UP.value,
                done=False,
                allocations=None,
                ai_limited=ai_limited,
            ).model_dump()
        ),
    )


@router.post("/reset")
async def advisor_reset(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Reset the current advisor conversation session.

    Clears all collected parameters, messages, and interaction count.
    Returns the session in WELCOME state.
    """
    sm = StateMachine(db_session=db, user_id=user_id)
    session = await sm.reset_session()

    return JSONResponse(
        status_code=200,
        content=success_response(
            SessionResponse(
                session_id=session.id,
                state=session.current_state,
                interaction_count=session.interaction_count,
                collected_params=session.collected_params,
                messages=session.messages or [],
            ).model_dump()
        ),
    )


@router.get("/session")
async def advisor_session(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get the current advisor session state.

    Returns session info including current state, interaction count,
    collected parameters, and message history.
    """
    sm = StateMachine(db_session=db, user_id=user_id)
    session = await sm.get_or_create_session()

    return JSONResponse(
        status_code=200,
        content=success_response(
            SessionResponse(
                session_id=session.id,
                state=session.current_state,
                interaction_count=session.interaction_count,
                collected_params=session.collected_params,
                messages=session.messages or [],
            ).model_dump()
        ),
    )
