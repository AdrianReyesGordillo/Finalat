"""Tests for the advisor router — Fina AI financial advisor endpoints.

Tests cover:
- POST /api/advisor/chat — state machine advancing, optimizer invocation, Bedrock routing
- POST /api/advisor/reset — session reset
- GET /api/advisor/session — session retrieval
- Bedrock fallback when AI is unavailable
"""

import json
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from backend.main import app
from backend.routers.advisor import get_current_user_id
from backend.services.state_machine import ConversationState


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TEST_USER_ID = "test-user-advisor-123"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
async def setup_db():
    """Ensure tables exist and clear conversation sessions for test isolation."""
    from backend.models.database import create_tables, async_session
    from backend.models.conversation import ConversationSession
    from sqlalchemy import delete

    await create_tables()
    # Clean up any leftover conversation sessions from previous test runs
    async with async_session() as session:
        await session.execute(
            delete(ConversationSession).where(
                ConversationSession.user_id == TEST_USER_ID
            )
        )
        await session.commit()


@pytest.fixture
def client():
    """Create a test client with auth dependency overridden and middleware mocked."""
    # Override the get_current_user_id dependency to return test user
    app.dependency_overrides[get_current_user_id] = lambda: TEST_USER_ID
    # Patch Firebase verify to accept any token
    with patch(
        "backend.middleware.auth.verify_firebase_token",
        new_callable=AsyncMock,
        return_value=TEST_USER_ID,
    ):
        with TestClient(app) as c:
            yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Auth headers with a dummy Bearer token to pass middleware check."""
    return {"Authorization": "Bearer test-token-123"}


# ---------------------------------------------------------------------------
# Tests: POST /api/advisor/chat
# ---------------------------------------------------------------------------


class TestAdvisorChat:
    """Tests for the POST /api/advisor/chat endpoint."""

    def test_initial_message_starts_welcome(self, client, auth_headers):
        """First message should start a new session and advance from WELCOME."""
        response = client.post(
            "/api/advisor/chat",
            json={"message": "Hola"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["state"] == "collect_capital"
        assert data["data"]["done"] is False

    def test_collect_capital_valid_input(self, client, auth_headers):
        """Valid capital amount should advance to collect_risk state."""
        # First advance from WELCOME
        client.post("/api/advisor/chat", json={"message": "Hola"}, headers=auth_headers)

        # Now provide capital
        response = client.post(
            "/api/advisor/chat",
            json={"message": "50000"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["state"] == "collect_risk"

    def test_collect_capital_invalid_input(self, client, auth_headers):
        """Invalid capital amount should remain in collect_capital state."""
        # First advance from WELCOME
        client.post("/api/advisor/chat", json={"message": "Hola"}, headers=auth_headers)

        # Provide invalid capital (negative)
        response = client.post(
            "/api/advisor/chat",
            json={"message": "-100"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["state"] == "collect_capital"  # stays in same state

    def test_full_conversation_flow_to_optimizer(self, client, auth_headers):
        """Full flow through all collection states should trigger optimizer."""
        # WELCOME -> COLLECT_CAPITAL
        client.post("/api/advisor/chat", json={"message": "Hola"}, headers=auth_headers)

        # COLLECT_CAPITAL -> COLLECT_RISK
        client.post("/api/advisor/chat", json={"message": "100000"}, headers=auth_headers)

        # COLLECT_RISK -> COLLECT_LIQUIDITY
        client.post("/api/advisor/chat", json={"message": "medium"}, headers=auth_headers)

        # COLLECT_LIQUIDITY -> COLLECT_MAX_INSTRUMENTS
        client.post("/api/advisor/chat", json={"message": "flexible"}, headers=auth_headers)

        # COLLECT_MAX_INSTRUMENTS -> GENERATE_RECOMMENDATION -> PRESENT_RESULTS
        response = client.post(
            "/api/advisor/chat",
            json={"message": "3"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Should be in present_results state (optimizer ran)
        assert data["data"]["state"] == "present_results"

    def test_empty_message_rejected(self, client, auth_headers):
        """Empty message should be rejected by validation."""
        response = client.post(
            "/api/advisor/chat",
            json={"message": ""},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_follow_up_question_routes_to_bedrock(self, client, auth_headers):
        """In FOLLOW_UP state, non-control questions should route to Bedrock."""
        # Navigate to FOLLOW_UP state
        client.post("/api/advisor/chat", json={"message": "Hola"}, headers=auth_headers)
        client.post("/api/advisor/chat", json={"message": "100000"}, headers=auth_headers)
        client.post("/api/advisor/chat", json={"message": "medium"}, headers=auth_headers)
        client.post("/api/advisor/chat", json={"message": "flexible"}, headers=auth_headers)
        client.post("/api/advisor/chat", json={"message": "3"}, headers=auth_headers)
        # PRESENT_RESULTS -> FOLLOW_UP
        client.post("/api/advisor/chat", json={"message": "ok"}, headers=auth_headers)

        # Now in FOLLOW_UP, ask a question (should route to Bedrock)
        with patch("backend.routers.advisor.chat_with_fina", new_callable=AsyncMock) as mock_bedrock:
            mock_bedrock.return_value = "CETES es un instrumento de bajo riesgo emitido por el gobierno mexicano."
            response = client.post(
                "/api/advisor/chat",
                json={"message": "¿Qué es CETES?"},
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["state"] == "follow_up"
            assert "CETES" in data["data"]["message"]
            assert data["data"]["ai_limited"] is False
            mock_bedrock.assert_called_once()

    def test_follow_up_bedrock_fallback(self, client, auth_headers):
        """When Bedrock returns fallback message, should use rule-based response."""
        # Navigate to FOLLOW_UP state
        client.post("/api/advisor/chat", json={"message": "Hola"}, headers=auth_headers)
        client.post("/api/advisor/chat", json={"message": "100000"}, headers=auth_headers)
        client.post("/api/advisor/chat", json={"message": "medium"}, headers=auth_headers)
        client.post("/api/advisor/chat", json={"message": "flexible"}, headers=auth_headers)
        client.post("/api/advisor/chat", json={"message": "3"}, headers=auth_headers)
        client.post("/api/advisor/chat", json={"message": "ok"}, headers=auth_headers)

        # Mock Bedrock to return fallback
        from backend.services.bedrock_client import FALLBACK_MESSAGE

        with patch("backend.routers.advisor.chat_with_fina", new_callable=AsyncMock) as mock_bedrock:
            mock_bedrock.return_value = FALLBACK_MESSAGE
            response = client.post(
                "/api/advisor/chat",
                json={"message": "¿Qué opinas?"},
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["ai_limited"] is True
            # Should contain the ai_limited notice or a financial tip
            assert len(data["data"]["message"]) > 0

    def test_follow_up_adjust_resets_collection(self, client, auth_headers):
        """In FOLLOW_UP, 'ajustar' should restart collection from COLLECT_CAPITAL."""
        # Navigate to FOLLOW_UP state
        client.post("/api/advisor/chat", json={"message": "Hola"}, headers=auth_headers)
        client.post("/api/advisor/chat", json={"message": "100000"}, headers=auth_headers)
        client.post("/api/advisor/chat", json={"message": "medium"}, headers=auth_headers)
        client.post("/api/advisor/chat", json={"message": "flexible"}, headers=auth_headers)
        client.post("/api/advisor/chat", json={"message": "3"}, headers=auth_headers)
        client.post("/api/advisor/chat", json={"message": "ok"}, headers=auth_headers)

        # Send "ajustar" to restart
        response = client.post(
            "/api/advisor/chat",
            json={"message": "ajustar"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["state"] == "collect_capital"

    def test_follow_up_terminate(self, client, auth_headers):
        """In FOLLOW_UP, 'terminar' should end the session."""
        # Navigate to FOLLOW_UP state
        client.post("/api/advisor/chat", json={"message": "Hola"}, headers=auth_headers)
        client.post("/api/advisor/chat", json={"message": "100000"}, headers=auth_headers)
        client.post("/api/advisor/chat", json={"message": "medium"}, headers=auth_headers)
        client.post("/api/advisor/chat", json={"message": "flexible"}, headers=auth_headers)
        client.post("/api/advisor/chat", json={"message": "3"}, headers=auth_headers)
        client.post("/api/advisor/chat", json={"message": "ok"}, headers=auth_headers)

        # Send "terminar" to end
        response = client.post(
            "/api/advisor/chat",
            json={"message": "terminar"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["state"] == "terminated"
        assert data["data"]["done"] is True


# ---------------------------------------------------------------------------
# Tests: POST /api/advisor/reset
# ---------------------------------------------------------------------------


class TestAdvisorReset:
    """Tests for the POST /api/advisor/reset endpoint."""

    def test_reset_session(self, client, auth_headers):
        """Reset should return a session in WELCOME state with cleared params."""
        # First create a session by chatting
        client.post("/api/advisor/chat", json={"message": "Hola"}, headers=auth_headers)
        client.post("/api/advisor/chat", json={"message": "50000"}, headers=auth_headers)

        # Reset
        response = client.post("/api/advisor/reset", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["state"] == "welcome"
        assert data["data"]["interaction_count"] == 0

    def test_reset_without_existing_session(self, client, auth_headers):
        """Reset without an existing session should create a fresh one."""
        response = client.post("/api/advisor/reset", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["state"] == "welcome"


# ---------------------------------------------------------------------------
# Tests: GET /api/advisor/session
# ---------------------------------------------------------------------------


class TestAdvisorSession:
    """Tests for the GET /api/advisor/session endpoint."""

    def test_get_session_creates_new(self, client, auth_headers):
        """Getting session without prior chat should create a new WELCOME session."""
        response = client.get("/api/advisor/session", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["state"] == "welcome"
        assert data["data"]["interaction_count"] == 0
        assert "session_id" in data["data"]

    def test_get_session_after_chat(self, client, auth_headers):
        """Getting session after chatting should reflect the current state."""
        # Create session and advance
        client.post("/api/advisor/chat", json={"message": "Hola"}, headers=auth_headers)
        client.post("/api/advisor/chat", json={"message": "50000"}, headers=auth_headers)

        response = client.get("/api/advisor/session", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["state"] == "collect_risk"
        assert data["data"]["interaction_count"] == 2


# ---------------------------------------------------------------------------
# Tests: Fallback messages config
# ---------------------------------------------------------------------------


class TestFallbackMessages:
    """Tests for the fallback messages configuration."""

    def test_fallback_messages_loaded(self):
        """Fallback messages JSON should be loaded correctly."""
        from backend.routers.advisor import FALLBACK_MESSAGES

        assert isinstance(FALLBACK_MESSAGES, dict)
        assert "welcome" in FALLBACK_MESSAGES
        assert "fallback_tip" in FALLBACK_MESSAGES
        assert "ai_limited" in FALLBACK_MESSAGES

    def test_get_fallback_message_known_state(self):
        """_get_fallback_message should return state-specific message."""
        from backend.routers.advisor import _get_fallback_message

        msg = _get_fallback_message("welcome")
        assert len(msg) > 0

    def test_get_fallback_message_unknown_state(self):
        """_get_fallback_message for unknown state should return generic tip."""
        from backend.routers.advisor import _get_fallback_message

        msg = _get_fallback_message("nonexistent_state")
        assert len(msg) > 0


# ---------------------------------------------------------------------------
# Tests: Helper functions
# ---------------------------------------------------------------------------


class TestHelperFunctions:
    """Tests for advisor router helper functions."""

    def test_is_fallback_response(self):
        """_is_fallback_response should detect the Bedrock fallback message."""
        from backend.routers.advisor import _is_fallback_response
        from backend.services.bedrock_client import FALLBACK_MESSAGE

        assert _is_fallback_response(FALLBACK_MESSAGE) is True
        assert _is_fallback_response("Some normal response") is False

    def test_format_optimizer_results_empty(self):
        """Formatting empty results should show a message."""
        from backend.routers.advisor import _format_optimizer_results

        result = _format_optimizer_results({
            "allocations": [],
            "total_expected_return": 0,
            "unallocated_capital": 50000,
            "message": "No instruments available."
        })
        assert "No instruments available" in result

    def test_format_optimizer_results_with_allocations(self):
        """Formatting results with allocations should show instrument details."""
        from backend.routers.advisor import _format_optimizer_results

        result = _format_optimizer_results({
            "allocations": [
                {
                    "instrument_name": "Nu México",
                    "allocated_amount": 50000.0,
                    "effective_rate": 15.5,
                    "projected_annual_return": 7750.0,
                }
            ],
            "total_expected_return": 7750.0,
            "unallocated_capital": 0.0,
            "message": None,
        })
        assert "Nu México" in result
        assert "7,750.00" in result
