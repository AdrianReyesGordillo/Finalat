"""Per-user rate limiting middleware using an in-memory sliding window counter.

Limits each user (identified by user_id from auth, or client IP for
unauthenticated requests) to 100 requests per 60-second window.
Returns HTTP 429 with the standard error envelope when exceeded.
"""

import time
import threading
from collections import deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.utils.response import rate_limited_response

# Configuration
MAX_REQUESTS = 100
WINDOW_SECONDS = 60
CLEANUP_INTERVAL_SECONDS = 300  # Clean up stale entries every 5 minutes


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Sliding window rate limiter middleware.

    Tracks request timestamps per user (or IP for unauthenticated requests)
    using a deque per key. Thread-safe via a lock protecting the shared state.
    Periodically cleans up expired entries to prevent memory leaks.
    """

    def __init__(self, app, max_requests: int = MAX_REQUESTS, window_seconds: int = WINDOW_SECONDS):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # key -> deque of timestamps (floats)
        self._requests: dict[str, deque] = {}
        self._lock = threading.Lock()
        self._last_cleanup = time.time()

    def _get_client_key(self, request: Request) -> str:
        """Extract the rate-limit key from the request.

        Uses user_id from request.state (set by auth middleware) if available,
        otherwise falls back to the client IP address.
        """
        # Auth middleware sets request.state.user_id for authenticated requests
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"

        # Fallback to client IP for unauthenticated requests
        client = request.client
        if client:
            return f"ip:{client.host}"
        return "ip:unknown"

    def _cleanup_stale_entries(self, now: float) -> None:
        """Remove entries that have no requests within the current window.

        Called periodically to prevent unbounded memory growth from
        users who made requests in the past but are no longer active.
        """
        if now - self._last_cleanup < CLEANUP_INTERVAL_SECONDS:
            return

        self._last_cleanup = now
        cutoff = now - self.window_seconds
        keys_to_remove = []

        for key, timestamps in self._requests.items():
            # Remove expired timestamps from the left
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()
            # Mark empty deques for removal
            if not timestamps:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self._requests[key]

    def _is_rate_limited(self, key: str) -> bool:
        """Check if the key has exceeded the rate limit.

        Uses a sliding window: counts requests within the last
        `window_seconds` seconds. If the count is at or above
        `max_requests`, the request is rate-limited.

        Returns True if limited, False if allowed.
        """
        now = time.time()

        with self._lock:
            self._cleanup_stale_entries(now)

            if key not in self._requests:
                self._requests[key] = deque()

            timestamps = self._requests[key]
            cutoff = now - self.window_seconds

            # Remove expired timestamps from the front of the deque
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()

            # Check if limit exceeded
            if len(timestamps) >= self.max_requests:
                return True

            # Record this request
            timestamps.append(now)
            return False

    async def dispatch(self, request: Request, call_next):
        """Process the request through rate limiting."""
        key = self._get_client_key(request)

        if self._is_rate_limited(key):
            return JSONResponse(
                status_code=429,
                content=rate_limited_response(),
            )

        response = await call_next(request)
        return response
