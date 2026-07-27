"""Firebase JWT verification middleware.

Validates Bearer tokens against Google's public X.509 certificates (RS256).
Extracts user_id (Firebase UID) from validated token and injects into request state.
Returns HTTP 401 for missing, expired, or invalid tokens.
Skips auth for /api/auth/login and /api/auth/register endpoints.
"""

import time
from typing import Optional

import httpx
import jwt
from cryptography.x509 import load_pem_x509_certificate
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.config import settings
from backend.utils.response import unauthorized_response

# Google's public X.509 certificates URL for Firebase token verification
GOOGLE_CERTS_URL = (
    "https://www.googleapis.com/robot/v1/metadata/x509/"
    "securetoken@system.gserviceaccount.com"
)

# Paths that do not require authentication
PUBLIC_PATHS = {
    "/api/auth/login",
    "/api/auth/register",
    "/api/health",
    "/api/chat/greeting",
    "/api/subscription",
    "/api/scrapers/status",
    "/api/scrapers/banxico/tasas-cetes",
    "/api/scrapers/banxico/tasa-objetivo",
    "/docs",
    "/redoc",
    "/openapi.json",
}

# Path prefixes that are public for GET requests only
PUBLIC_GET_PREFIXES = (
    "/api/instruments",
)

# Path prefixes where GET requests are public but auth is attempted if token is present
PUBLIC_GET_OPTIONAL_AUTH_PREFIXES = (
    "/api/courses",
)


class _CertificateCache:
    """In-memory cache for Google's public X.509 certificates.

    Respects the max-age directive from the Cache-Control response header.
    """

    def __init__(self) -> None:
        self._certificates: dict[str, str] = {}
        self._expires_at: float = 0.0

    @property
    def is_expired(self) -> bool:
        """Check if the cached certificates have expired."""
        return time.time() >= self._expires_at

    async def get_certificates(self) -> dict[str, str]:
        """Fetch and cache Google's public certificates.

        Returns cached certificates if they haven't expired.
        Otherwise fetches fresh certificates from Google's endpoint.

        Returns:
            Dict mapping key IDs (kid) to PEM-encoded X.509 certificates.
        """
        if self._certificates and not self.is_expired:
            return self._certificates

        async with httpx.AsyncClient() as client:
            response = await client.get(GOOGLE_CERTS_URL, timeout=10.0)
            response.raise_for_status()

        # Parse max-age from Cache-Control header
        cache_control = response.headers.get("cache-control", "")
        max_age = self._parse_max_age(cache_control)

        self._certificates = response.json()
        self._expires_at = time.time() + max_age

        return self._certificates

    @staticmethod
    def _parse_max_age(cache_control: str) -> int:
        """Extract max-age value from Cache-Control header.

        Args:
            cache_control: The Cache-Control header value.

        Returns:
            max-age in seconds, defaults to 3600 if not found.
        """
        for directive in cache_control.split(","):
            directive = directive.strip().lower()
            if directive.startswith("max-age="):
                try:
                    return int(directive.split("=", 1)[1])
                except (ValueError, IndexError):
                    pass
        return 3600  # Default 1 hour


# Module-level certificate cache instance
_cert_cache = _CertificateCache()


def _get_public_key(kid: str, certificates: dict[str, str]):
    """Extract the RSA public key from the X.509 certificate matching the given kid.

    Args:
        kid: The key ID from the JWT header.
        certificates: Dict mapping key IDs to PEM-encoded X.509 certificates.

    Returns:
        The RSA public key object, or None if kid not found.
    """
    pem_data = certificates.get(kid)
    if not pem_data:
        return None

    cert = load_pem_x509_certificate(pem_data.encode("utf-8"))
    return cert.public_key()


def _extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    """Extract the token from an Authorization header value.

    Args:
        authorization: The Authorization header value (e.g., "Bearer <token>").

    Returns:
        The token string, or None if the header is missing or malformed.
    """
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip() or None


async def verify_firebase_token(token: str) -> Optional[str]:
    """Verify a Firebase ID token and return the user_id (sub claim).

    Validates:
    - Token signature against Google's X.509 certificates (RS256)
    - Issuer (iss) matches https://securetoken.google.com/{project_id}
    - Audience (aud) matches the Firebase project ID
    - Token is not expired (exp)
    - Subject (sub) is not empty

    Args:
        token: The Firebase ID token (JWT) to verify.

    Returns:
        The user_id (Firebase UID) from the sub claim, or None if validation fails.
    """
    project_id = settings.FIREBASE_PROJECT_ID
    if not project_id:
        return None

    try:
        # Decode header without verification to get the kid
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if not kid:
            return None

        # Get certificates (cached)
        certificates = await _cert_cache.get_certificates()

        # Get the public key for this kid
        public_key = _get_public_key(kid, certificates)
        if not public_key:
            return None

        # Verify and decode the token
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=project_id,
            issuer=f"https://securetoken.google.com/{project_id}",
            options={
                "require": ["exp", "iat", "aud", "iss", "sub"],
                "verify_exp": True,
                "verify_iat": True,
                "verify_aud": True,
                "verify_iss": True,
            },
        )

        # Validate sub is not empty
        sub = payload.get("sub", "")
        if not sub:
            return None

        return sub

    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, jwt.DecodeError) as e:
        import logging
        logging.getLogger(__name__).warning("Token verification failed: %s: %s", type(e).__name__, str(e))
        return None
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Token verification unexpected error: %s: %s", type(e).__name__, str(e))
        return None


class FirebaseAuthMiddleware(BaseHTTPMiddleware):
    """Starlette middleware that validates Firebase JWT on every request.

    - Skips authentication for public paths (/api/auth/login, /api/auth/register, /api/health)
    - Extracts Bearer token from Authorization header
    - Validates token against Google's X.509 certificates
    - Injects user_id into request.state on success
    - Returns HTTP 401 JSON response on failure
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        """Process the request through the auth middleware."""
        # Skip auth for public paths
        path = request.url.path.rstrip("/")
        if path in PUBLIC_PATHS or self._is_public_path(path):
            return await call_next(request)

        # Skip auth for GET requests on public-GET prefixes
        if request.method == "GET" and any(
            path.startswith(prefix) for prefix in PUBLIC_GET_PREFIXES
        ):
            # Set a dummy user_id for unauthenticated GET requests
            request.state.user_id = None
            return await call_next(request)

        # Optional auth for GET requests on courses-like prefixes
        # (attempt auth if token present, allow through with user_id=None if not)
        if request.method == "GET" and any(
            path.startswith(prefix) for prefix in PUBLIC_GET_OPTIONAL_AUTH_PREFIXES
        ):
            authorization = request.headers.get("authorization")
            token = _extract_bearer_token(authorization)
            if token:
                user_id = await verify_firebase_token(token)
                request.state.user_id = user_id  # Could be None if token invalid
            else:
                request.state.user_id = None
            return await call_next(request)

        # Extract Bearer token
        authorization = request.headers.get("authorization")
        token = _extract_bearer_token(authorization)

        if not token:
            return JSONResponse(
                status_code=401,
                content=unauthorized_response("Missing or invalid authorization token."),
            )

        # Verify token and extract user_id
        user_id = await verify_firebase_token(token)

        if not user_id:
            return JSONResponse(
                status_code=401,
                content=unauthorized_response("Invalid, expired, or malformed token."),
            )

        # Inject user_id into request state
        request.state.user_id = user_id

        return await call_next(request)

    @staticmethod
    def _is_public_path(path: str) -> bool:
        """Check if a path matches any public path pattern.

        Handles paths with or without trailing slashes and
        allows exact matching against the PUBLIC_PATHS set.
        """
        # Already checked in dispatch, this handles edge cases
        return path in PUBLIC_PATHS
