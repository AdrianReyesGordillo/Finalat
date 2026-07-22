"""Unit tests for the State Machine service.

Tests the deterministic conversation FSM: state transitions, input validation,
parameter collection, interaction limits, and session management.
"""

import pytest
import uuid

from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from backend.services.state_machine import (
    ConversationState,
    StateMachine,
    StateMachineResult,
    TRANSITIONS,
    MAX_INTERACTIONS,
    _parse_positive_number,
    _validate_risk,
    _validate_liquidity,
    _parse_max_instruments,
)
from backend.models.conversation import ConversationSession


# ---------------------------------------------------------------------------
# Fixtures and Helpers
# ---------------------------------------------------------------------------


def _make_session(
    state: str = "welcome",
    params: dict | None = None,
    messages: list | None = None,
    interaction_count: int = 0,
) -> ConversationSession:
    """Create a mock ConversationSession for testing."""
    session = ConversationSession(
        id=str(uuid.uuid4()),
        user_id="test_user_123",
        current_state=state,
        collected_params=params or {},
        messages=messages or [],
        interaction_count=interaction_count,
    )
    return session


def _make_db_session(existing_session: ConversationSession | None = None):
    """Create a mock async database session."""
    db = AsyncMock()

    # Mock execute for select queries
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_session
    db.execute.return_value = mock_result
    db.flush = AsyncMock()
    db.add = MagicMock()

    return db


# ---------------------------------------------------------------------------
# Unit Tests — Input Validators
# ---------------------------------------------------------------------------


class TestInputValidators:
    """Tests for the individual input validation functions."""

    def test_parse_positive_number_valid(self):
        assert _parse_positive_number("50000") == 50000.0
        assert _parse_positive_number("100.50") == 100.50
        assert _parse_positive_number("$1,000") == 1000.0
        assert _parse_positive_number("  25000  ") == 25000.0

    def test_parse_positive_number_invalid(self):
        assert _parse_positive_number("0") is None
        assert _parse_positive_number("-100") is None
        assert _parse_positive_number("abc") is None
        assert _parse_positive_number("") is None

    def test_validate_risk_valid(self):
        assert _validate_risk("low") is True
        assert _validate_risk("medium") is True
        assert _validate_risk("high") is True
        assert _validate_risk("bajo") is True
        assert _validate_risk("medio") is True
        assert _validate_risk("alto") is True
        assert _validate_risk("  LOW  ") is True

    def test_validate_risk_invalid(self):
        assert _validate_risk("extreme") is False
        assert _validate_risk("") is False
        assert _validate_risk("123") is False

    def test_validate_liquidity_valid(self):
        assert _validate_liquidity("immediate") is True
        assert _validate_liquidity("short-term") is True
        assert _validate_liquidity("flexible") is True
        assert _validate_liquidity("inmediata") is True
        assert _validate_liquidity("corto-plazo") is True

    def test_validate_liquidity_invalid(self):
        assert _validate_liquidity("long-term") is False
        assert _validate_liquidity("") is False
        assert _validate_liquidity("xyz") is False

    def test_parse_max_instruments_valid(self):
        assert _parse_max_instruments("1") == 1
        assert _parse_max_instruments("5") == 5
        assert _parse_max_instruments("10") == 10

    def test_parse_max_instruments_invalid(self):
        assert _parse_max_instruments("0") is None
        assert _parse_max_instruments("11") is None
        assert _parse_max_instruments("-1") is None
        assert _parse_max_instruments("abc") is None
        assert _parse_max_instruments("3.5") is None


# ---------------------------------------------------------------------------
# Unit Tests — State Machine Transitions
# ---------------------------------------------------------------------------


class TestStateMachineTransitions:
    """Tests for state machine transition logic."""

    @pytest.mark.asyncio
    async def test_welcome_to_collect_capital(self):
        """WELCOME state advances to COLLECT_CAPITAL on any input."""
        session = _make_session(state="welcome")
        db = _make_db_session(session)
        sm = StateMachine(db_session=db, user_id="test_user_123")

        result = await sm.process_input("Hola, empecemos")

        assert result.state == ConversationState.COLLECT_CAPITAL
        assert not result.done
        assert session.current_state == "collect_capital"

    @pytest.mark.asyncio
    async def test_collect_capital_valid(self):
        """Valid capital input transitions to COLLECT_RISK."""
        session = _make_session(state="collect_capital")
        db = _make_db_session(session)
        sm = StateMachine(db_session=db, user_id="test_user_123")

        result = await sm.process_input("50000")

        assert result.state == ConversationState.COLLECT_RISK
        assert not result.done
        assert session.collected_params["total_capital"] == 50000.0

    @pytest.mark.asyncio
    async def test_collect_capital_invalid_stays(self):
        """Invalid capital input stays in COLLECT_CAPITAL."""
        session = _make_session(state="collect_capital")
        db = _make_db_session(session)
        sm = StateMachine(db_session=db, user_id="test_user_123")

        result = await sm.process_input("no sé")

        assert result.state == ConversationState.COLLECT_CAPITAL
        assert not result.done
        assert session.current_state == "collect_capital"

    @pytest.mark.asyncio
    async def test_collect_risk_valid(self):
        """Valid risk input transitions to COLLECT_LIQUIDITY."""
        session = _make_session(state="collect_risk", params={"total_capital": 50000.0})
        db = _make_db_session(session)
        sm = StateMachine(db_session=db, user_id="test_user_123")

        result = await sm.process_input("medium")

        assert result.state == ConversationState.COLLECT_LIQUIDITY
        assert session.collected_params["risk_tolerance"] == "medium"

    @pytest.mark.asyncio
    async def test_collect_risk_spanish_input(self):
        """Spanish risk input (bajo/medio/alto) is accepted and normalized."""
        session = _make_session(state="collect_risk", params={"total_capital": 50000.0})
        db = _make_db_session(session)
        sm = StateMachine(db_session=db, user_id="test_user_123")

        result = await sm.process_input("bajo")

        assert result.state == ConversationState.COLLECT_LIQUIDITY
        assert session.collected_params["risk_tolerance"] == "low"

    @pytest.mark.asyncio
    async def test_collect_risk_invalid_stays(self):
        """Invalid risk input stays in COLLECT_RISK."""
        session = _make_session(state="collect_risk", params={"total_capital": 50000.0})
        db = _make_db_session(session)
        sm = StateMachine(db_session=db, user_id="test_user_123")

        result = await sm.process_input("extreme")

        assert result.state == ConversationState.COLLECT_RISK

    @pytest.mark.asyncio
    async def test_collect_liquidity_valid(self):
        """Valid liquidity input transitions to COLLECT_MAX_INSTRUMENTS."""
        session = _make_session(
            state="collect_liquidity",
            params={"total_capital": 50000.0, "risk_tolerance": "medium"},
        )
        db = _make_db_session(session)
        sm = StateMachine(db_session=db, user_id="test_user_123")

        result = await sm.process_input("flexible")

        assert result.state == ConversationState.COLLECT_MAX_INSTRUMENTS
        assert session.collected_params["liquidity_preference"] == "flexible"

    @pytest.mark.asyncio
    async def test_collect_max_instruments_triggers_optimizer(self):
        """Valid max instruments input transitions to GENERATE_RECOMMENDATION with needs_optimizer flag."""
        session = _make_session(
            state="collect_max_instruments",
            params={
                "total_capital": 50000.0,
                "risk_tolerance": "medium",
                "liquidity_preference": "flexible",
            },
        )
        db = _make_db_session(session)
        sm = StateMachine(db_session=db, user_id="test_user_123")

        result = await sm.process_input("5")

        assert result.state == ConversationState.GENERATE_RECOMMENDATION
        assert result.needs_optimizer is True
        assert result.collected_params["max_instruments"] == 5

    @pytest.mark.asyncio
    async def test_present_results_to_follow_up(self):
        """PRESENT_RESULTS advances to FOLLOW_UP on any input."""
        session = _make_session(state="present_results")
        db = _make_db_session(session)
        sm = StateMachine(db_session=db, user_id="test_user_123")

        result = await sm.process_input("gracias")

        assert result.state == ConversationState.FOLLOW_UP


# ---------------------------------------------------------------------------
# Unit Tests — Follow-Up Handling
# ---------------------------------------------------------------------------


class TestFollowUpState:
    """Tests for FOLLOW_UP state behavior."""

    @pytest.mark.asyncio
    async def test_follow_up_adjust_loops_back(self):
        """'ajustar' in FOLLOW_UP loops back to COLLECT_CAPITAL."""
        session = _make_session(
            state="follow_up",
            params={"total_capital": 50000.0, "risk_tolerance": "low"},
        )
        db = _make_db_session(session)
        sm = StateMachine(db_session=db, user_id="test_user_123")

        result = await sm.process_input("ajustar")

        assert result.state == ConversationState.COLLECT_CAPITAL
        assert session.collected_params == {}  # Params cleared

    @pytest.mark.asyncio
    async def test_follow_up_end_terminates(self):
        """'terminar' in FOLLOW_UP terminates the session."""
        session = _make_session(state="follow_up")
        db = _make_db_session(session)
        sm = StateMachine(db_session=db, user_id="test_user_123")

        result = await sm.process_input("terminar")

        assert result.state == ConversationState.TERMINATED
        assert result.done is True

    @pytest.mark.asyncio
    async def test_follow_up_question_stays(self):
        """A general question in FOLLOW_UP stays in FOLLOW_UP."""
        session = _make_session(state="follow_up")
        db = _make_db_session(session)
        sm = StateMachine(db_session=db, user_id="test_user_123")

        result = await sm.process_input("¿Qué es CETES?")

        assert result.state == ConversationState.FOLLOW_UP
        assert not result.done


# ---------------------------------------------------------------------------
# Unit Tests — Interaction Limit
# ---------------------------------------------------------------------------


class TestInteractionLimit:
    """Tests for the 20-interaction session limit."""

    @pytest.mark.asyncio
    async def test_interaction_limit_terminates_session(self):
        """Session terminates after reaching MAX_INTERACTIONS."""
        session = _make_session(
            state="collect_capital",
            interaction_count=MAX_INTERACTIONS - 1,  # Next interaction hits the limit
        )
        db = _make_db_session(session)
        sm = StateMachine(db_session=db, user_id="test_user_123")

        result = await sm.process_input("50000")

        assert result.state == ConversationState.TERMINATED
        assert result.done is True
        assert session.interaction_count == MAX_INTERACTIONS

    @pytest.mark.asyncio
    async def test_terminated_session_stays_terminated(self):
        """A terminated session returns done=True without processing."""
        session = _make_session(state="terminated")
        db = _make_db_session(session)
        sm = StateMachine(db_session=db, user_id="test_user_123")

        result = await sm.process_input("hello")

        assert result.state == ConversationState.TERMINATED
        assert result.done is True


# ---------------------------------------------------------------------------
# Unit Tests — Session Management
# ---------------------------------------------------------------------------


class TestSessionManagement:
    """Tests for session creation and reset."""

    @pytest.mark.asyncio
    async def test_create_new_session_when_none_exists(self):
        """Creates a new session when no active session exists."""
        db = _make_db_session(existing_session=None)
        sm = StateMachine(db_session=db, user_id="test_user_123")

        session = await sm.get_or_create_session()

        assert session.current_state == "welcome"
        assert session.collected_params == {}
        assert session.messages == []
        assert session.interaction_count == 0
        db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_reuse_existing_session(self):
        """Reuses an existing non-terminated session."""
        existing = _make_session(state="collect_risk", params={"total_capital": 10000.0})
        db = _make_db_session(existing_session=existing)
        sm = StateMachine(db_session=db, user_id="test_user_123")

        session = await sm.get_or_create_session()

        assert session.current_state == "collect_risk"
        assert session.collected_params["total_capital"] == 10000.0
        db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_reset_session(self):
        """Reset clears state, params, messages, and interaction count."""
        existing = _make_session(
            state="follow_up",
            params={"total_capital": 50000.0},
            messages=[{"role": "user", "content": "hi", "timestamp": "..."}],
            interaction_count=15,
        )
        db = _make_db_session(existing_session=existing)
        sm = StateMachine(db_session=db, user_id="test_user_123")

        session = await sm.reset_session()

        assert session.current_state == "welcome"
        assert session.collected_params == {}
        assert session.messages == []
        assert session.interaction_count == 0

    @pytest.mark.asyncio
    async def test_messages_are_stored(self):
        """Messages are appended to the session history."""
        session = _make_session(state="welcome")
        db = _make_db_session(session)
        sm = StateMachine(db_session=db, user_id="test_user_123")

        await sm.process_input("Hola")

        # Should have both user and assistant messages
        assert len(session.messages) == 2
        assert session.messages[0]["role"] == "user"
        assert session.messages[0]["content"] == "Hola"
        assert session.messages[1]["role"] == "assistant"


# ---------------------------------------------------------------------------
# Unit Tests — Transition Map Completeness
# ---------------------------------------------------------------------------


class TestTransitionMap:
    """Tests that the transition map covers expected states."""

    def test_all_non_terminal_states_have_transitions(self):
        """All non-terminal states (except TERMINATED) have defined transitions."""
        non_terminal = [
            s for s in ConversationState
            if s != ConversationState.TERMINATED
        ]
        for state in non_terminal:
            assert state in TRANSITIONS, f"Missing transition for {state}"

    def test_max_interactions_constant(self):
        """MAX_INTERACTIONS is 20 per requirement 14.9."""
        assert MAX_INTERACTIONS == 20
