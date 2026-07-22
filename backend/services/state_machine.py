"""Deterministic Conversation State Machine for the Fina AI Advisor.

Implements a finite state machine (FSM) that drives the Fina advisor chat flow.
States follow a deterministic sequence: WELCOME → COLLECT_CAPITAL → COLLECT_RISK →
COLLECT_LIQUIDITY → COLLECT_MAX_INSTRUMENTS → GENERATE_RECOMMENDATION →
PRESENT_RESULTS → FOLLOW_UP (or TERMINATED on session limit).

The state machine persists session state in the conversation_sessions table,
tracks collected parameters, and enforces a 20-interaction limit per session.

Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 14.8, 14.9
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.conversation import ConversationSession


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_INTERACTIONS = 20


# ---------------------------------------------------------------------------
# State enum
# ---------------------------------------------------------------------------


class ConversationState(str, Enum):
    """All possible states in the Fina advisor conversation FSM."""

    WELCOME = "welcome"
    COLLECT_CAPITAL = "collect_capital"
    COLLECT_RISK = "collect_risk"
    COLLECT_LIQUIDITY = "collect_liquidity"
    COLLECT_MAX_INSTRUMENTS = "collect_max_instruments"
    GENERATE_RECOMMENDATION = "generate_recommendation"
    PRESENT_RESULTS = "present_results"
    FOLLOW_UP = "follow_up"
    TERMINATED = "terminated"


# ---------------------------------------------------------------------------
# State transitions
# ---------------------------------------------------------------------------

TRANSITIONS: dict[ConversationState, ConversationState] = {
    ConversationState.WELCOME: ConversationState.COLLECT_CAPITAL,
    ConversationState.COLLECT_CAPITAL: ConversationState.COLLECT_RISK,
    ConversationState.COLLECT_RISK: ConversationState.COLLECT_LIQUIDITY,
    ConversationState.COLLECT_LIQUIDITY: ConversationState.COLLECT_MAX_INSTRUMENTS,
    ConversationState.COLLECT_MAX_INSTRUMENTS: ConversationState.GENERATE_RECOMMENDATION,
    ConversationState.GENERATE_RECOMMENDATION: ConversationState.PRESENT_RESULTS,
    ConversationState.PRESENT_RESULTS: ConversationState.FOLLOW_UP,
    # FOLLOW_UP loops back to COLLECT_CAPITAL on "adjust"
    ConversationState.FOLLOW_UP: ConversationState.COLLECT_CAPITAL,
}


# ---------------------------------------------------------------------------
# Input validators per collection state
# ---------------------------------------------------------------------------


def _parse_positive_number(text: str) -> float | None:
    """Parse a positive number from user input. Returns None if invalid."""
    text = text.strip().replace(",", "").replace("$", "")
    try:
        value = float(text)
        return value if value > 0 else None
    except (ValueError, TypeError):
        return None


def _validate_risk(text: str) -> bool:
    """Validate risk tolerance input (low, medium, high)."""
    return text.strip().lower() in ("low", "medium", "high", "bajo", "medio", "alto")


def _validate_liquidity(text: str) -> bool:
    """Validate liquidity preference input."""
    return text.strip().lower() in (
        "immediate", "short-term", "flexible",
        "inmediata", "corto-plazo", "flexible",
    )


def _parse_max_instruments(text: str) -> int | None:
    """Parse max instruments (1-10) from user input. Returns None if invalid."""
    text = text.strip()
    try:
        value = int(text)
        return value if 1 <= value <= 10 else None
    except (ValueError, TypeError):
        return None


VALIDATORS: dict[ConversationState, Any] = {
    ConversationState.COLLECT_CAPITAL: lambda x: _parse_positive_number(x) is not None,
    ConversationState.COLLECT_RISK: _validate_risk,
    ConversationState.COLLECT_LIQUIDITY: _validate_liquidity,
    ConversationState.COLLECT_MAX_INSTRUMENTS: lambda x: _parse_max_instruments(x) is not None,
}


# ---------------------------------------------------------------------------
# Prompt messages per state
# ---------------------------------------------------------------------------

STATE_PROMPTS: dict[ConversationState, str] = {
    ConversationState.WELCOME: (
        "¡Hola! Soy Fina, tu asesora de inversiones. "
        "Te ayudaré a encontrar la mejor distribución de tu capital en los instrumentos "
        "financieros disponibles en México. ¿Comenzamos?"
    ),
    ConversationState.COLLECT_CAPITAL: (
        "¿Cuánto capital deseas invertir? Por favor indica el monto en pesos mexicanos."
    ),
    ConversationState.COLLECT_RISK: (
        "¿Cuál es tu tolerancia al riesgo? Puedes elegir: bajo (low), medio (medium) o alto (high)."
    ),
    ConversationState.COLLECT_LIQUIDITY: (
        "¿Cuál es tu preferencia de liquidez? Opciones: inmediata (immediate), "
        "corto-plazo (short-term) o flexible."
    ),
    ConversationState.COLLECT_MAX_INSTRUMENTS: (
        "¿En cuántos instrumentos como máximo deseas distribuir tu inversión? (1 a 10)"
    ),
    ConversationState.GENERATE_RECOMMENDATION: (
        "Procesando tu recomendación con los parámetros proporcionados..."
    ),
    ConversationState.PRESENT_RESULTS: (
        "Aquí tienes tu recomendación de inversión:"
    ),
    ConversationState.FOLLOW_UP: (
        "¿Qué te gustaría hacer ahora? Puedes:\n"
        "• Ajustar los parámetros y generar una nueva recomendación (escribe 'ajustar')\n"
        "• Hacer preguntas sobre los instrumentos recomendados\n"
        "• Terminar la conversación (escribe 'terminar')"
    ),
    ConversationState.TERMINATED: (
        "La sesión ha alcanzado el límite de interacciones. "
        "Aquí tienes un resumen de tu última recomendación. ¡Hasta la próxima!"
    ),
}

RETRY_PROMPTS: dict[ConversationState, str] = {
    ConversationState.COLLECT_CAPITAL: (
        "No entendí el monto. Por favor ingresa una cantidad positiva en pesos (ej: 50000)."
    ),
    ConversationState.COLLECT_RISK: (
        "Opción no válida. Por favor elige: bajo (low), medio (medium) o alto (high)."
    ),
    ConversationState.COLLECT_LIQUIDITY: (
        "Opción no válida. Por favor elige: inmediata (immediate), "
        "corto-plazo (short-term) o flexible."
    ),
    ConversationState.COLLECT_MAX_INSTRUMENTS: (
        "Por favor ingresa un número entre 1 y 10."
    ),
}


# ---------------------------------------------------------------------------
# Result data class
# ---------------------------------------------------------------------------


@dataclass
class StateMachineResult:
    """Result of processing a user input through the state machine."""

    state: ConversationState
    message: str
    done: bool = False
    needs_optimizer: bool = False
    collected_params: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# State Machine Service
# ---------------------------------------------------------------------------


class StateMachine:
    """Deterministic conversation FSM for the Fina AI advisor.

    Manages state transitions, input validation, parameter collection,
    and interaction counting. Persists state to the conversation_sessions table.

    Args:
        session: Database session for persistence.
        user_id: The authenticated user's Firebase UID.
    """

    def __init__(self, db_session: AsyncSession, user_id: str) -> None:
        self._db = db_session
        self._user_id = user_id
        self._conversation: ConversationSession | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_or_create_session(self) -> ConversationSession:
        """Retrieve the active session or create a new one.

        Returns:
            The current ConversationSession instance.
        """
        if self._conversation is not None:
            return self._conversation

        # Try to find an existing non-terminated session
        stmt = (
            select(ConversationSession)
            .where(
                ConversationSession.user_id == self._user_id,
                ConversationSession.current_state != ConversationState.TERMINATED.value,
            )
            .order_by(ConversationSession.updated_at.desc())
            .limit(1)
        )
        result = await self._db.execute(stmt)
        session = result.scalar_one_or_none()

        if session is None:
            session = ConversationSession(
                id=str(uuid.uuid4()),
                user_id=self._user_id,
                current_state=ConversationState.WELCOME.value,
                collected_params={},
                messages=[],
                interaction_count=0,
            )
            self._db.add(session)
            await self._db.flush()

        self._conversation = session
        return session

    def get_state(self) -> ConversationState:
        """Get the current conversation state.

        Returns:
            The current ConversationState enum value.

        Raises:
            RuntimeError: If no session has been loaded.
        """
        if self._conversation is None:
            raise RuntimeError("No session loaded. Call get_or_create_session() first.")
        return ConversationState(self._conversation.current_state)

    async def process_input(self, user_input: str) -> StateMachineResult:
        """Process user input and advance the state machine.

        Validates input for the current state, stores valid parameters,
        transitions to the next state, and enforces the interaction limit.

        Args:
            user_input: The user's message text.

        Returns:
            A StateMachineResult with the new state, response message,
            and whether the conversation is done or needs the optimizer.
        """
        session = await self.get_or_create_session()
        current_state = ConversationState(session.current_state)

        # Check if session is already terminated
        if current_state == ConversationState.TERMINATED:
            return StateMachineResult(
                state=ConversationState.TERMINATED,
                message=STATE_PROMPTS[ConversationState.TERMINATED],
                done=True,
            )

        # Increment interaction count
        session.interaction_count += 1

        # Add user message to history
        self._add_message(session, "user", user_input)

        # Check interaction limit
        if session.interaction_count >= MAX_INTERACTIONS:
            session.current_state = ConversationState.TERMINATED.value
            message = STATE_PROMPTS[ConversationState.TERMINATED]
            self._add_message(session, "assistant", message)
            await self._db.flush()
            return StateMachineResult(
                state=ConversationState.TERMINATED,
                message=message,
                done=True,
            )

        # Handle WELCOME state — any input advances to COLLECT_CAPITAL
        if current_state == ConversationState.WELCOME:
            session.current_state = ConversationState.COLLECT_CAPITAL.value
            message = STATE_PROMPTS[ConversationState.COLLECT_CAPITAL]
            self._add_message(session, "assistant", message)
            await self._db.flush()
            return StateMachineResult(
                state=ConversationState.COLLECT_CAPITAL,
                message=message,
            )

        # Handle FOLLOW_UP state
        if current_state == ConversationState.FOLLOW_UP:
            return await self._handle_follow_up(session, user_input)

        # Handle collection states (COLLECT_*)
        if current_state in VALIDATORS:
            return await self._handle_collection_state(session, current_state, user_input)

        # Handle PRESENT_RESULTS — any input advances to FOLLOW_UP
        if current_state == ConversationState.PRESENT_RESULTS:
            session.current_state = ConversationState.FOLLOW_UP.value
            message = STATE_PROMPTS[ConversationState.FOLLOW_UP]
            self._add_message(session, "assistant", message)
            await self._db.flush()
            return StateMachineResult(
                state=ConversationState.FOLLOW_UP,
                message=message,
            )

        # Fallback — should not reach here normally
        message = STATE_PROMPTS.get(current_state, "Estado desconocido.")
        await self._db.flush()
        return StateMachineResult(
            state=current_state,
            message=message,
        )

    async def reset_session(self) -> ConversationSession:
        """Reset the current session to WELCOME state.

        Clears collected parameters, messages, and interaction count.

        Returns:
            The reset ConversationSession instance.
        """
        session = await self.get_or_create_session()
        session.current_state = ConversationState.WELCOME.value
        session.collected_params = {}
        session.messages = []
        session.interaction_count = 0
        await self._db.flush()
        return session

    async def add_message(self, role: str, content: str) -> None:
        """Add a message to the session history.

        Args:
            role: The message role ('user' or 'assistant').
            content: The message content text.
        """
        session = await self.get_or_create_session()
        self._add_message(session, role, content)
        await self._db.flush()

    async def transition_state(self, new_state: ConversationState) -> None:
        """Manually transition to a new state.

        Used by the advisor router to set state after optimizer/bedrock processing.

        Args:
            new_state: The target ConversationState.
        """
        session = await self.get_or_create_session()
        session.current_state = new_state.value
        await self._db.flush()

    def get_collected_params(self) -> dict[str, Any] | None:
        """Get the collected optimizer parameters.

        Returns:
            Dictionary with collected params or None if no session loaded.
        """
        if self._conversation is None:
            return None
        return self._conversation.collected_params or {}

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _add_message(
        self, session: ConversationSession, role: str, content: str
    ) -> None:
        """Append a message to the session message history."""
        messages = list(session.messages or [])
        messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        session.messages = messages

    async def _handle_collection_state(
        self,
        session: ConversationSession,
        current_state: ConversationState,
        user_input: str,
    ) -> StateMachineResult:
        """Handle input validation and parameter storage for collection states."""
        validator = VALIDATORS[current_state]

        if not validator(user_input):
            # Invalid input — stay in current state, return retry prompt
            message = RETRY_PROMPTS.get(current_state, "Entrada no válida. Intenta de nuevo.")
            self._add_message(session, "assistant", message)
            await self._db.flush()
            return StateMachineResult(
                state=current_state,
                message=message,
            )

        # Valid input — store parameter
        self._store_param(session, current_state, user_input)

        # Transition to next state
        next_state = TRANSITIONS[current_state]
        session.current_state = next_state.value

        # Check if we reached GENERATE_RECOMMENDATION
        if next_state == ConversationState.GENERATE_RECOMMENDATION:
            # Signal that the optimizer should be invoked
            message = STATE_PROMPTS[ConversationState.GENERATE_RECOMMENDATION]
            self._add_message(session, "assistant", message)
            await self._db.flush()
            return StateMachineResult(
                state=next_state,
                message=message,
                needs_optimizer=True,
                collected_params=session.collected_params,
            )

        # Normal transition — return the next state's prompt
        message = STATE_PROMPTS[next_state]
        self._add_message(session, "assistant", message)
        await self._db.flush()
        return StateMachineResult(
            state=next_state,
            message=message,
        )

    async def _handle_follow_up(
        self, session: ConversationSession, user_input: str
    ) -> StateMachineResult:
        """Handle the FOLLOW_UP state options: adjust, end, or question."""
        text = user_input.strip().lower()

        if text in ("ajustar", "adjust", "cambiar"):
            # Loop back to COLLECT_CAPITAL, reset collected params
            session.current_state = ConversationState.COLLECT_CAPITAL.value
            session.collected_params = {}
            message = STATE_PROMPTS[ConversationState.COLLECT_CAPITAL]
            self._add_message(session, "assistant", message)
            await self._db.flush()
            return StateMachineResult(
                state=ConversationState.COLLECT_CAPITAL,
                message=message,
            )

        if text in ("terminar", "end", "salir", "exit"):
            # End conversation
            session.current_state = ConversationState.TERMINATED.value
            message = "¡Gracias por usar Fina! Hasta la próxima."
            self._add_message(session, "assistant", message)
            await self._db.flush()
            return StateMachineResult(
                state=ConversationState.TERMINATED,
                message=message,
                done=True,
            )

        # Any other input is treated as a question — stay in FOLLOW_UP
        # The advisor router will route this to Bedrock for a contextual answer
        message = STATE_PROMPTS[ConversationState.FOLLOW_UP]
        await self._db.flush()
        return StateMachineResult(
            state=ConversationState.FOLLOW_UP,
            message=message,
        )

    def _store_param(
        self,
        session: ConversationSession,
        state: ConversationState,
        user_input: str,
    ) -> None:
        """Store the validated parameter for the current collection state."""
        params = dict(session.collected_params or {})
        text = user_input.strip()

        if state == ConversationState.COLLECT_CAPITAL:
            params["total_capital"] = _parse_positive_number(text)

        elif state == ConversationState.COLLECT_RISK:
            # Normalize to English values
            risk_map = {"bajo": "low", "medio": "medium", "alto": "high"}
            normalized = text.lower()
            params["risk_tolerance"] = risk_map.get(normalized, normalized)

        elif state == ConversationState.COLLECT_LIQUIDITY:
            # Normalize to English values
            liquidity_map = {
                "inmediata": "immediate",
                "corto-plazo": "short-term",
                "corto plazo": "short-term",
            }
            normalized = text.lower()
            params["liquidity_preference"] = liquidity_map.get(normalized, normalized)

        elif state == ConversationState.COLLECT_MAX_INSTRUMENTS:
            params["max_instruments"] = _parse_max_instruments(text)

        session.collected_params = params
