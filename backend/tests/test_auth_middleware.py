"""Tests for Firebase JWT verification middleware."""

import time
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.x509 import (
    CertificateBuilder,
    Name,
    NameAttribute,
)
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key
import jwt
import datetime

from backend.middleware.auth import (
    _CertificateCache,
    _extract_bearer_token,
    _get_public_key,
    verify_firebase_token,
    FirebaseAuthMiddleware,
    PUBLIC_PATHS,
)


# --- Helpers ---

def _generate_rsa_key_pair():
    """Generate an RSA private key and matching self-signed X.509 cert."""
    private_key = generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    subject = issuer = Name([
        NameAttribute(NameOID.COMMON_NAME, "test"),
    ])
    cert = (
        CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(1000)
        .not_valid_before(datetime.datetime.utcnow() - datetime.timedelta(days=1))
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
        .sign(private_key, hashes.SHA256())
    )
    cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode("utf-8")
    return private_key, cert_pem


def _create_firebase_token(private_key, project_id: str, uid: str = "test_user_123", expired: bool = False):
    """Create a Firebase-like JWT token."""
    now = datetime.datetime.utcnow()
    payload = {
        "iss": f"https://securetoken.google.com/{project_id}",
        "aud": project_id,
        "sub": uid,
        "iat": now - datetime.timedelta(minutes=5),
        "exp": now - datetime.timedelta(hours=1) if expired else now + datetime.timedelta(hours=1),
        "auth_time": int(now.timestamp()),
    }
    headers = {"kid": "test-key-id"}
    return jwt.encode(payload, private_key, algorithm="RS256", headers=headers)


# --- Tests for _extract_bearer_token ---

class TestExtractBearerToken:
    def test_valid_bearer_token(self):
        assert _extract_bearer_token("Bearer abc123") == "abc123"

    def test_bearer_case_insensitive(self):
        assert _extract_bearer_token("bearer abc123") == "abc123"
        assert _extract_bearer_token("BEARER abc123") == "abc123"

    def test_missing_header(self):
        assert _extract_bearer_token(None) is None

    def test_empty_header(self):
        assert _extract_bearer_token("") is None

    def test_no_bearer_prefix(self):
        assert _extract_bearer_token("Basic abc123") is None

    def test_no_token_after_bearer(self):
        assert _extract_bearer_token("Bearer ") is None

    def test_bearer_only(self):
        assert _extract_bearer_token("Bearer") is None


# --- Tests for _CertificateCache ---

class TestCertificateCache:
    def test_initial_state_is_expired(self):
        cache = _CertificateCache()
        assert cache.is_expired is True

    def test_parse_max_age(self):
        assert _CertificateCache._parse_max_age("max-age=3600") == 3600
        assert _CertificateCache._parse_max_age("public, max-age=19008, must-revalidate") == 19008
        assert _CertificateCache._parse_max_age("no-cache") == 3600  # default
        assert _CertificateCache._parse_max_age("") == 3600  # default

    @pytest.mark.asyncio
    async def test_get_certificates_caches(self):
        cache = _CertificateCache()
        mock_certs = {"key1": "cert1"}

        mock_response = MagicMock()
        mock_response.json.return_value = mock_certs
        mock_response.headers = {"cache-control": "max-age=3600"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_class.return_value = mock_client

            # First call fetches
            result = await cache.get_certificates()
            assert result == mock_certs

            # Second call uses cache (no HTTP call)
            mock_client.get.reset_mock()
            result2 = await cache.get_certificates()
            assert result2 == mock_certs
            mock_client.get.assert_not_called()


# --- Tests for _get_public_key ---

class TestGetPublicKey:
    def test_valid_certificate(self):
        _, cert_pem = _generate_rsa_key_pair()
        certificates = {"test-kid": cert_pem}
        key = _get_public_key("test-kid", certificates)
        assert key is not None

    def test_unknown_kid(self):
        _, cert_pem = _generate_rsa_key_pair()
        certificates = {"test-kid": cert_pem}
        key = _get_public_key("unknown-kid", certificates)
        assert key is None


# --- Tests for verify_firebase_token ---

class TestVerifyFirebaseToken:
    @pytest.mark.asyncio
    async def test_valid_token(self):
        project_id = "test-project"
        private_key, cert_pem = _generate_rsa_key_pair()
        token = _create_firebase_token(private_key, project_id, uid="user123")

        mock_certs = {"test-key-id": cert_pem}

        with patch("backend.middleware.auth.settings") as mock_settings:
            mock_settings.FIREBASE_PROJECT_ID = project_id

            with patch("backend.middleware.auth._cert_cache") as mock_cache:
                mock_cache.get_certificates = AsyncMock(return_value=mock_certs)

                result = await verify_firebase_token(token)
                assert result == "user123"

    @pytest.mark.asyncio
    async def test_expired_token(self):
        project_id = "test-project"
        private_key, cert_pem = _generate_rsa_key_pair()
        token = _create_firebase_token(private_key, project_id, uid="user123", expired=True)

        mock_certs = {"test-key-id": cert_pem}

        with patch("backend.middleware.auth.settings") as mock_settings:
            mock_settings.FIREBASE_PROJECT_ID = project_id

            with patch("backend.middleware.auth._cert_cache") as mock_cache:
                mock_cache.get_certificates = AsyncMock(return_value=mock_certs)

                result = await verify_firebase_token(token)
                assert result is None

    @pytest.mark.asyncio
    async def test_invalid_token(self):
        with patch("backend.middleware.auth.settings") as mock_settings:
            mock_settings.FIREBASE_PROJECT_ID = "test-project"

            result = await verify_firebase_token("invalid.token.value")
            assert result is None

    @pytest.mark.asyncio
    async def test_empty_project_id(self):
        with patch("backend.middleware.auth.settings") as mock_settings:
            mock_settings.FIREBASE_PROJECT_ID = ""

            result = await verify_firebase_token("some.token.here")
            assert result is None

    @pytest.mark.asyncio
    async def test_wrong_audience(self):
        project_id = "test-project"
        private_key, cert_pem = _generate_rsa_key_pair()
        # Create token with different audience
        token = _create_firebase_token(private_key, "wrong-project", uid="user123")

        mock_certs = {"test-key-id": cert_pem}

        with patch("backend.middleware.auth.settings") as mock_settings:
            mock_settings.FIREBASE_PROJECT_ID = project_id

            with patch("backend.middleware.auth._cert_cache") as mock_cache:
                mock_cache.get_certificates = AsyncMock(return_value=mock_certs)

                result = await verify_firebase_token(token)
                assert result is None

    @pytest.mark.asyncio
    async def test_empty_sub(self):
        project_id = "test-project"
        private_key, cert_pem = _generate_rsa_key_pair()

        now = datetime.datetime.utcnow()
        payload = {
            "iss": f"https://securetoken.google.com/{project_id}",
            "aud": project_id,
            "sub": "",  # empty sub
            "iat": now - datetime.timedelta(minutes=5),
            "exp": now + datetime.timedelta(hours=1),
        }
        headers = {"kid": "test-key-id"}
        token = jwt.encode(payload, private_key, algorithm="RS256", headers=headers)

        mock_certs = {"test-key-id": cert_pem}

        with patch("backend.middleware.auth.settings") as mock_settings:
            mock_settings.FIREBASE_PROJECT_ID = project_id

            with patch("backend.middleware.auth._cert_cache") as mock_cache:
                mock_cache.get_certificates = AsyncMock(return_value=mock_certs)

                result = await verify_firebase_token(token)
                assert result is None

    @pytest.mark.asyncio
    async def test_kid_not_in_certs(self):
        project_id = "test-project"
        private_key, cert_pem = _generate_rsa_key_pair()
        token = _create_firebase_token(private_key, project_id, uid="user123")

        # Certs don't contain the kid from the token
        mock_certs = {"different-key-id": cert_pem}

        with patch("backend.middleware.auth.settings") as mock_settings:
            mock_settings.FIREBASE_PROJECT_ID = project_id

            with patch("backend.middleware.auth._cert_cache") as mock_cache:
                mock_cache.get_certificates = AsyncMock(return_value=mock_certs)

                result = await verify_firebase_token(token)
                assert result is None


# --- Tests for FirebaseAuthMiddleware (integration via ASGI) ---

class TestFirebaseAuthMiddleware:
    def test_public_paths(self):
        """Verify that public paths are correctly identified."""
        assert "/api/auth/login" in PUBLIC_PATHS
        assert "/api/auth/register" in PUBLIC_PATHS
        assert "/api/health" in PUBLIC_PATHS

    def test_middleware_skips_public_paths(self):
        """Public paths should not require auth."""
        from starlette.applications import Starlette
        from starlette.middleware import Middleware
        from starlette.routing import Route
        from starlette.responses import JSONResponse as StarletteJSONResponse
        from starlette.testclient import TestClient

        async def login_endpoint(request):
            return StarletteJSONResponse({"status": "ok"})

        app = Starlette(
            routes=[Route("/api/auth/login", login_endpoint)],
            middleware=[Middleware(FirebaseAuthMiddleware)],
        )

        client = TestClient(app)
        response = client.get("/api/auth/login")
        assert response.status_code == 200

    def test_middleware_rejects_missing_token(self):
        """Requests without Authorization header get 401."""
        from starlette.applications import Starlette
        from starlette.middleware import Middleware
        from starlette.routing import Route
        from starlette.responses import JSONResponse as StarletteJSONResponse
        from starlette.testclient import TestClient

        async def protected_endpoint(request):
            return StarletteJSONResponse({"user_id": request.state.user_id})

        app = Starlette(
            routes=[Route("/api/ahorro", protected_endpoint)],
            middleware=[Middleware(FirebaseAuthMiddleware)],
        )

        client = TestClient(app)
        response = client.get("/api/ahorro")
        assert response.status_code == 401
        body = response.json()
        assert body["success"] is False
        assert body["error"]["code"] == "UNAUTHORIZED"

    def test_middleware_rejects_invalid_token(self):
        """Requests with invalid token get 401."""
        from starlette.applications import Starlette
        from starlette.middleware import Middleware
        from starlette.routing import Route
        from starlette.responses import JSONResponse as StarletteJSONResponse
        from starlette.testclient import TestClient

        async def protected_endpoint(request):
            return StarletteJSONResponse({"user_id": request.state.user_id})

        app = Starlette(
            routes=[Route("/api/ahorro", protected_endpoint)],
            middleware=[Middleware(FirebaseAuthMiddleware)],
        )

        client = TestClient(app)
        response = client.get("/api/ahorro", headers={"Authorization": "Bearer invalid-token"})
        assert response.status_code == 401
        body = response.json()
        assert body["success"] is False
        assert body["error"]["code"] == "UNAUTHORIZED"

    def test_middleware_injects_user_id_on_valid_token(self):
        """Valid token results in user_id injected into request.state."""
        from starlette.applications import Starlette
        from starlette.middleware import Middleware
        from starlette.routing import Route
        from starlette.responses import JSONResponse as StarletteJSONResponse
        from starlette.testclient import TestClient

        project_id = "test-project"
        private_key, cert_pem = _generate_rsa_key_pair()
        token = _create_firebase_token(private_key, project_id, uid="firebase_uid_456")

        async def protected_endpoint(request):
            return StarletteJSONResponse({"user_id": request.state.user_id})

        app = Starlette(
            routes=[Route("/api/ahorro", protected_endpoint)],
            middleware=[Middleware(FirebaseAuthMiddleware)],
        )

        mock_certs = {"test-key-id": cert_pem}

        with patch("backend.middleware.auth.settings") as mock_settings:
            mock_settings.FIREBASE_PROJECT_ID = project_id

            with patch("backend.middleware.auth._cert_cache") as mock_cache:
                mock_cache.get_certificates = AsyncMock(return_value=mock_certs)

                client = TestClient(app)
                response = client.get(
                    "/api/ahorro",
                    headers={"Authorization": f"Bearer {token}"},
                )
                assert response.status_code == 200
                body = response.json()
                assert body["user_id"] == "firebase_uid_456"
