"""Unit tests for the rate limiting middleware.

Tests cover:
- Requests under limit are allowed (HTTP 200)
- Requests at/above limit return HTTP 429 with proper error envelope
- Sliding window resets after window expires
- User_id-based keying vs IP-based fallback
- Different users have independent limits
"""

import time

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from backend.middleware.rate_limiter import RateLimiterMiddleware


def _create_test_app(max_requests: int = 5, window_seconds: int = 60) -> FastAPI:
    """Create a minimal FastAPI app with rate limiter for testing."""
    app = FastAPI()
    app.add_middleware(
        RateLimiterMiddleware,
        max_requests=max_requests,
        window_seconds=window_seconds,
    )

    @app.get("/test")
    async def test_endpoint():
        return {"message": "ok"}

    @app.get("/authed")
    async def authed_endpoint(request: Request):
        return {"user": getattr(request.state, "user_id", None)}

    return app


class TestRateLimiterAllowsRequests:
    """Tests that requests under the limit pass through."""

    def test_first_request_allowed(self):
        app = _create_test_app(max_requests=5, window_seconds=60)
        client = TestClient(app)
        response = client.get("/test")
        assert response.status_code == 200
        assert response.json() == {"message": "ok"}

    def test_requests_under_limit_allowed(self):
        app = _create_test_app(max_requests=5, window_seconds=60)
        client = TestClient(app)
        for _ in range(5):
            response = client.get("/test")
            assert response.status_code == 200


class TestRateLimiterBlocks:
    """Tests that requests over the limit get HTTP 429."""

    def test_exceeding_limit_returns_429(self):
        app = _create_test_app(max_requests=5, window_seconds=60)
        client = TestClient(app)
        # Use up the limit
        for _ in range(5):
            response = client.get("/test")
            assert response.status_code == 200

        # Next request should be rate limited
        response = client.get("/test")
        assert response.status_code == 429

    def test_429_response_has_correct_envelope(self):
        app = _create_test_app(max_requests=5, window_seconds=60)
        client = TestClient(app)
        # Exhaust limit
        for _ in range(5):
            client.get("/test")

        response = client.get("/test")
        assert response.status_code == 429
        body = response.json()
        assert body["success"] is False
        assert body["data"] is None
        assert body["error"]["code"] == "RATE_LIMITED"
        assert body["error"]["message"] is not None


class TestRateLimiterSlidingWindow:
    """Tests for sliding window expiry behavior."""

    def test_window_resets_after_expiry(self):
        app = _create_test_app(max_requests=3, window_seconds=1)
        client = TestClient(app)
        # Exhaust the 3-request limit
        for _ in range(3):
            response = client.get("/test")
            assert response.status_code == 200

        # Should be limited now
        response = client.get("/test")
        assert response.status_code == 429

        # Wait for the window to expire
        time.sleep(1.1)

        # Should be allowed again
        response = client.get("/test")
        assert response.status_code == 200


class TestRateLimiterUserIsolation:
    """Tests that different users have independent rate limits."""

    def test_same_client_is_rate_limited(self):
        """Requests from the same client share a rate limit bucket."""
        app = _create_test_app(max_requests=2, window_seconds=60)
        client = TestClient(app)

        # First "user" makes 2 requests (at limit)
        for _ in range(2):
            response = client.get("/test")
            assert response.status_code == 200

        # Third request should be blocked (same IP from test client)
        response = client.get("/test")
        assert response.status_code == 429

    def test_authenticated_user_key_used(self):
        """When request.state.user_id is set, it's used as the rate limit key."""
        from starlette.middleware.base import BaseHTTPMiddleware

        class FakeAuthMiddleware(BaseHTTPMiddleware):
            """Simulates auth middleware setting user_id on request state."""

            async def dispatch(self, request, call_next):
                user_id = request.headers.get("X-User-Id", None)
                if user_id:
                    request.state.user_id = user_id
                return await call_next(request)

        app = FastAPI()

        # In Starlette, middleware added later via add_middleware wraps the
        # ones added earlier (LIFO). So we add rate limiter first, then auth.
        # This means auth runs BEFORE rate limiter (auth is outermost).
        app.add_middleware(RateLimiterMiddleware, max_requests=2, window_seconds=60)
        app.add_middleware(FakeAuthMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"message": "ok"}

        client = TestClient(app)

        # User A makes 2 requests (at limit)
        for _ in range(2):
            response = client.get("/test", headers={"X-User-Id": "user-a"})
            assert response.status_code == 200

        # User A is now limited
        response = client.get("/test", headers={"X-User-Id": "user-a"})
        assert response.status_code == 429

        # User B should still be allowed (different key)
        response = client.get("/test", headers={"X-User-Id": "user-b"})
        assert response.status_code == 200
