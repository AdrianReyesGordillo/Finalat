"""Simple in-memory cache with TTL for expensive operations.

Cache keys are scoped by user_id to prevent data leakage between users.
Use user_key() to generate per-user cache keys.

Includes a max-size cap to prevent unbounded memory growth.
"""
import time
from typing import Any

_cache: dict[str, dict] = {}
_MAX_CACHE_SIZE = 500  # Max entries before eviction


def user_key(base_key: str, user_id: str) -> str:
    """Generate a user-scoped cache key.

    Example: user_key("gi_records", "abc123") -> "u:abc123:gi_records"
    """
    return f"u:{user_id}:{base_key}"


def _evict_expired():
    """Remove all expired entries."""
    now = time.time()
    expired = [k for k, v in _cache.items() if now > v["expires"]]
    for k in expired:
        del _cache[k]


def get(key: str) -> Any | None:
    """Get a cached value if it exists and hasn't expired."""
    entry = _cache.get(key)
    if entry is None:
        return None
    if time.time() > entry["expires"]:
        del _cache[key]
        return None
    return entry["value"]


def set(key: str, value: Any, ttl_seconds: int = 300):
    """Cache a value with a TTL (default 5 minutes)."""
    # Evict if at capacity
    if len(_cache) >= _MAX_CACHE_SIZE:
        _evict_expired()
        # If still over limit, remove oldest entries
        if len(_cache) >= _MAX_CACHE_SIZE:
            sorted_keys = sorted(_cache.keys(), key=lambda k: _cache[k]["expires"])
            for k in sorted_keys[:len(_cache) - _MAX_CACHE_SIZE + 1]:
                del _cache[k]

    _cache[key] = {
        "value": value,
        "expires": time.time() + ttl_seconds
    }


def invalidate(key: str):
    """Remove a specific key from cache."""
    _cache.pop(key, None)


def invalidate_prefix(prefix: str):
    """Remove all keys starting with a prefix."""
    keys_to_remove = [k for k in _cache if k.startswith(prefix)]
    for k in keys_to_remove:
        del _cache[k]


def invalidate_user(user_id: str):
    """Remove all cached data for a specific user."""
    invalidate_prefix(f"u:{user_id}:")


def clear():
    """Clear all cached data."""
    _cache.clear()
