"""Unit tests for security headers middleware, CORS, and GZip compression.

Tests verify:
- Security headers are present on all responses (CSP, X-Content-Type-Options, X-Frame-Options, HSTS)
- GZip compression activates for responses > 1KB
- CORS only allows configured origins
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client():
    """Sync test client for the FastAPI app."""
    with TestClient(app) as c:
        yield c


class TestSecurityHeaders:
    """Tests for security headers middleware."""

    def test_csp_header_present(self, client: TestClient):
        response = client.get("/api/health")
        assert response.headers.get("content-security-policy") == "default-src 'self'"

    def test_x_content_type_options_header(self, client: TestClient):
        response = client.get("/api/health")
        assert response.headers.get("x-content-type-options") == "nosniff"

    def test_x_frame_options_header(self, client: TestClient):
        response = client.get("/api/health")
        assert response.headers.get("x-frame-options") == "DENY"

    def test_hsts_header(self, client: TestClient):
        response = client.get("/api/health")
        hsts = response.headers.get("strict-transport-security")
        assert hsts is not None
        assert "max-age=31536000" in hsts

    def test_all_security_headers_on_single_response(self, client: TestClient):
        response = client.get("/api/health")
        assert "content-security-policy" in response.headers
        assert "x-content-type-options" in response.headers
        assert "x-frame-options" in response.headers
        assert "strict-transport-security" in response.headers


class TestCORS:
    """Tests for CORS configuration."""

    def test_cors_allows_configured_origin(self, client: TestClient):
        """CORS should allow the configured origin (localhost:5173 in dev)."""
        response = client.options(
            "/api/health",
            headers={
                "origin": "http://localhost:5173",
                "access-control-request-method": "GET",
            },
        )
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"

    def test_cors_rejects_unknown_origin(self, client: TestClient):
        """CORS should not return allow-origin for unknown origins."""
        response = client.options(
            "/api/health",
            headers={
                "origin": "http://evil-site.com",
                "access-control-request-method": "GET",
            },
        )
        # When origin is not allowed, the access-control-allow-origin header
        # should either be absent or not match the requesting origin
        allow_origin = response.headers.get("access-control-allow-origin")
        assert allow_origin != "http://evil-site.com"


class TestGZipCompression:
    """Tests for GZip compression middleware."""

    def test_gzip_middleware_is_registered(self):
        """GZipMiddleware should be registered on the app."""
        from starlette.middleware.gzip import GZipMiddleware

        middleware_classes = [m.cls for m in app.user_middleware]
        assert GZipMiddleware in middleware_classes

    def test_gzip_minimum_size_configured(self):
        """GZipMiddleware should be configured with minimum_size=1000."""
        from starlette.middleware.gzip import GZipMiddleware

        for m in app.user_middleware:
            if m.cls == GZipMiddleware:
                assert m.kwargs.get("minimum_size") == 1000
                break
        else:
            pytest.fail("GZipMiddleware not found in app middleware")
