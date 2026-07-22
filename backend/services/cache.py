"""In-memory LRU Cache with TTL, scoped per user_id.

Implements an LRU (Least Recently Used) eviction policy with a maximum of 500 entries
and a 5-minute TTL per entry. All cache keys are scoped by user_id to ensure data
isolation between users.

Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7, 16.8
"""

import threading
import time
from collections import OrderedDict
from typing import Any


class LRUCache:
    """Thread-safe in-memory LRU cache with TTL and user-scoped keys.

    Args:
        max_size: Maximum number of entries in the cache. Defaults to 500.
        ttl_seconds: Time-to-live for each entry in seconds. Defaults to 300 (5 minutes).
    """

    def __init__(self, max_size: int = 500, ttl_seconds: int = 300) -> None:
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds
        # OrderedDict maintains insertion/access order for LRU tracking.
        # Each value is a tuple of (data, timestamp).
        self._store: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._lock = threading.Lock()

    @property
    def size(self) -> int:
        """Current number of entries in the cache."""
        with self._lock:
            return len(self._store)

    def _make_key(self, user_id: str, key: str) -> str:
        """Build the internal cache key: {user_id}:{key}.

        The caller provides key in the format {module}:{resource_key}, so the
        full internal key becomes {user_id}:{module}:{resource_key}.
        """
        return f"{user_id}:{key}"

    def _is_expired(self, timestamp: float) -> bool:
        """Check if an entry has exceeded its TTL."""
        return (time.time() - timestamp) >= self._ttl_seconds

    def get(self, user_id: str, key: str) -> Any | None:
        """Retrieve a cached value.

        Returns None if the key does not exist or has expired. Expired entries
        are removed on access. A successful get moves the entry to the most
        recently used position.

        Args:
            user_id: The user's Firebase UID.
            key: The cache key in format '{module}:{resource_key}'.

        Returns:
            The cached value, or None if not found or expired.
        """
        internal_key = self._make_key(user_id, key)

        with self._lock:
            if internal_key not in self._store:
                return None

            value, timestamp = self._store[internal_key]

            # Check TTL expiry
            if self._is_expired(timestamp):
                del self._store[internal_key]
                return None

            # Move to end (most recently used)
            self._store.move_to_end(internal_key)
            return value

    def set(self, user_id: str, key: str, value: Any) -> None:
        """Store a value in the cache.

        If the key already exists, it is updated and moved to the most recently
        used position. If the cache is at capacity, the least recently used
        entry is evicted before inserting the new one.

        Args:
            user_id: The user's Firebase UID.
            key: The cache key in format '{module}:{resource_key}'.
            value: The value to cache.
        """
        internal_key = self._make_key(user_id, key)
        now = time.time()

        with self._lock:
            # If key exists, update it and move to end
            if internal_key in self._store:
                self._store[internal_key] = (value, now)
                self._store.move_to_end(internal_key)
                return

            # Evict LRU entry if at capacity
            if len(self._store) >= self._max_size:
                # popitem(last=False) removes the oldest (least recently used) entry
                self._store.popitem(last=False)

            # Insert new entry at end (most recently used)
            self._store[internal_key] = (value, now)

    def invalidate(self, user_id: str, module: str) -> None:
        """Invalidate all cache entries for a specific module and user.

        Removes all entries whose key matches the pattern {user_id}:{module}:*.

        Args:
            user_id: The user's Firebase UID.
            module: The module name (e.g., 'ahorro', 'creditos').
        """
        prefix = f"{user_id}:{module}:"

        with self._lock:
            keys_to_delete = [
                k for k in self._store if k.startswith(prefix)
            ]
            for k in keys_to_delete:
                del self._store[k]

    def invalidate_user(self, user_id: str) -> None:
        """Invalidate all cache entries for a user.

        Removes all entries whose key starts with {user_id}:.

        Args:
            user_id: The user's Firebase UID.
        """
        prefix = f"{user_id}:"

        with self._lock:
            keys_to_delete = [
                k for k in self._store if k.startswith(prefix)
            ]
            for k in keys_to_delete:
                del self._store[k]

    def clear(self) -> None:
        """Remove all entries from the cache."""
        with self._lock:
            self._store.clear()


# Module-level singleton instance for application-wide use.
cache = LRUCache()
