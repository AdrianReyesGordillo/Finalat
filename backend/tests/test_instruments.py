"""Tests for the Instruments router — /api/instruments endpoints.

Tests cover:
- GET /api/instruments — list all instruments with filters
- GET /api/instruments/{id} — single instrument detail
- POST /api/instruments/refresh — trigger rate scraper (auth required)
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.main import app
from backend.models.database import get_db
from backend.models.instruments import Instrument


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db():
    """Create a mock async database session."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def client(mock_db):
    """Create a test client with DB dependency override."""

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_instrument():
    """Create a sample Instrument model instance."""
    inst = MagicMock(spec=Instrument)
    inst.id = "test-uuid-123"
    inst.name = "Nu México"
    inst.annual_rate = 15.5
    inst.min_investment = 0.01
    inst.max_investment = None
    inst.term = "liquid"
    inst.risk_level = "low"
    inst.liquidity_tier = "immediate"
    inst.tiered_rates = [
        {"min_amount": 0, "max_amount": 50000, "rate": 15.5},
        {"min_amount": 50000, "max_amount": 200000, "rate": 14.5},
    ]
    inst.last_fetch_status = "success"
    inst.last_fetched_at = datetime.now(timezone.utc)
    inst.created_at = datetime.now(timezone.utc)
    inst.updated_at = datetime.now(timezone.utc)
    return inst


@pytest.fixture
def stale_instrument():
    """Create an instrument with a stale last_fetched_at (>7 days old)."""
    inst = MagicMock(spec=Instrument)
    inst.id = "stale-uuid-456"
    inst.name = "CETES 28 días"
    inst.annual_rate = 10.5
    inst.min_investment = 100.0
    inst.max_investment = None
    inst.term = "28"
    inst.risk_level = "low"
    inst.liquidity_tier = "28-day"
    inst.tiered_rates = None
    inst.last_fetch_status = "success"
    inst.last_fetched_at = datetime.now(timezone.utc) - timedelta(days=10)
    inst.created_at = datetime.now(timezone.utc) - timedelta(days=30)
    inst.updated_at = datetime.now(timezone.utc) - timedelta(days=10)
    return inst


# ---------------------------------------------------------------------------
# Test: GET /api/instruments
# ---------------------------------------------------------------------------


class TestListInstruments:
    """Tests for GET /api/instruments."""

    def test_list_instruments_returns_success(self, client, mock_db, sample_instrument):
        """GET /api/instruments returns instruments list with success envelope."""
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [sample_instrument]
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        response = client.get("/api/instruments")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total"] == 1
        assert data["data"]["items"][0]["name"] == "Nu México"
        assert data["data"]["items"][0]["tiered_rates"] is not None

    def test_list_instruments_flags_stale(self, client, mock_db, stale_instrument):
        """Instruments not updated in 7+ days are flagged as stale."""
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [stale_instrument]
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        response = client.get("/api/instruments")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["items"][0]["stale"] is True

    def test_list_instruments_not_stale(self, client, mock_db, sample_instrument):
        """Recent instruments are not flagged as stale."""
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [sample_instrument]
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        response = client.get("/api/instruments")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["items"][0]["stale"] is False

    def test_list_instruments_empty(self, client, mock_db):
        """GET /api/instruments returns empty list when no instruments exist."""
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        response = client.get("/api/instruments")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total"] == 0
        assert data["data"]["items"] == []

    def test_invalid_risk_level_returns_400(self, client, mock_db):
        """Invalid risk_level filter returns a validation error."""
        response = client.get("/api/instruments?risk_level=invalid")

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_invalid_liquidity_tier_returns_400(self, client, mock_db):
        """Invalid liquidity_tier filter returns a validation error."""
        response = client.get("/api/instruments?liquidity_tier=invalid")

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_filter_by_risk_level(self, client, mock_db, sample_instrument):
        """GET /api/instruments?risk_level=low filters correctly."""
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [sample_instrument]
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        response = client.get("/api/instruments?risk_level=low")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_filter_by_liquidity_tier(self, client, mock_db, sample_instrument):
        """GET /api/instruments?liquidity_tier=immediate filters correctly."""
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [sample_instrument]
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        response = client.get("/api/instruments?liquidity_tier=immediate")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


# ---------------------------------------------------------------------------
# Test: GET /api/instruments/{id}
# ---------------------------------------------------------------------------


class TestGetInstrument:
    """Tests for GET /api/instruments/{id}."""

    def test_get_instrument_found(self, client, mock_db, sample_instrument):
        """GET /api/instruments/{id} returns instrument detail when found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_instrument
        mock_db.execute.return_value = mock_result

        response = client.get("/api/instruments/test-uuid-123")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == "test-uuid-123"
        assert data["data"]["name"] == "Nu México"
        assert data["data"]["annual_rate"] == 15.5

    def test_get_instrument_not_found(self, client, mock_db):
        """GET /api/instruments/{id} returns 404 when instrument doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        response = client.get("/api/instruments/nonexistent-id")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# Test: POST /api/instruments/refresh
# ---------------------------------------------------------------------------


class TestRefreshInstruments:
    """Tests for POST /api/instruments/refresh."""

    def test_refresh_without_auth_returns_401(self, client):
        """POST /api/instruments/refresh requires authentication."""
        response = client.post("/api/instruments/refresh")

        assert response.status_code == 401

    @patch("backend.routers.instruments.scrape_all_rates")
    def test_refresh_with_auth_triggers_scraper(self, mock_scrape, client, mock_db):
        """POST /api/instruments/refresh with valid auth triggers the scraper."""
        mock_scrape.return_value = {"updated": 9, "failed": 0, "total": 9}

        # Override the _get_current_user_id dependency to simulate auth
        from backend.routers.instruments import _get_current_user_id

        def override_user():
            return "admin-user-123"

        app.dependency_overrides[_get_current_user_id] = override_user

        with patch(
            "backend.middleware.auth.verify_firebase_token",
            new_callable=AsyncMock,
            return_value="admin-user-123",
        ):
            response = client.post(
                "/api/instruments/refresh",
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["updated"] == 9
        assert data["data"]["failed"] == 0
        assert data["data"]["message"] == "Rate scrape completed."

        # Cleanup override
        del app.dependency_overrides[_get_current_user_id]

    @patch("backend.routers.instruments.scrape_all_rates")
    def test_refresh_scraper_error_returns_500(self, mock_scrape, client, mock_db):
        """POST /api/instruments/refresh returns 500 on scraper failure."""
        mock_scrape.side_effect = Exception("Scraper connection timeout")

        from backend.routers.instruments import _get_current_user_id

        def override_user():
            return "admin-user-123"

        app.dependency_overrides[_get_current_user_id] = override_user

        with patch(
            "backend.middleware.auth.verify_firebase_token",
            new_callable=AsyncMock,
            return_value="admin-user-123",
        ):
            response = client.post(
                "/api/instruments/refresh",
                headers={"Authorization": "Bearer test-token"},
            )

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "SCRAPER_ERROR"

        # Cleanup override
        del app.dependency_overrides[_get_current_user_id]
