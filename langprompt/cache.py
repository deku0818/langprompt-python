"""Simple in-memory cache implementation."""

from __future__ import annotations

import time
from typing import Any, Generic, TypeVar


T = TypeVar("T")


class CacheEntry(Generic[T]):
    """Cache entry with expiration."""

    def __init__(self, value: T, ttl: int):
        """Initialize cache entry.

        Args:
            value: Cached value
            ttl: Time-to-live in seconds
        """
        self.value = value
        self.expires_at = time.time() + ttl

    def is_expired(self) -> bool:
        """Check if entry is expired."""
        return time.time() > self.expires_at


class Cache:
    """Simple in-memory cache with TTL support.

    Cache is disabled by default to ensure data freshness.
    Enable via config.enable_cache = True.
    """

    def __init__(self, enabled: bool = False, default_ttl: int = 3600):
        """Initialize cache.

        Args:
            enabled: Whether cache is enabled
            default_ttl: Default TTL in seconds
        """
        self.enabled = enabled
        self.default_ttl = default_ttl
        self._store: dict[str, CacheEntry[Any]] = {}

    def get(self, key: str) -> Any | None:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if not self.enabled:
            return None

        entry = self._store.get(key)
        if entry is None:
            return None

        if entry.is_expired():
            del self._store[key]
            return None

        return entry.value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        if not self.enabled:
            return

        ttl = ttl if ttl is not None else self.default_ttl
        self._store[key] = CacheEntry(value, ttl)

    def delete(self, key: str) -> None:
        """Delete value from cache.

        Args:
            key: Cache key
        """
        self._store.pop(key, None)

    def clear(self) -> None:
        """Clear all cache entries."""
        self._store.clear()

    def cleanup_expired(self) -> int:
        """Remove expired entries.

        Returns:
            Number of entries removed
        """
        expired_keys = [
            key for key, entry in self._store.items() if entry.is_expired()
        ]

        for key in expired_keys:
            del self._store[key]

        return len(expired_keys)

    @staticmethod
    def make_key(project_id: str, resource: str, *identifiers: str) -> str:
        """Create cache key.

        Format: langprompt:{project_id}:{resource}:{identifiers}

        Args:
            project_id: Project ID
            resource: Resource type (e.g., "prompt", "version")
            *identifiers: Additional identifiers

        Returns:
            Cache key

        Examples:
            >>> Cache.make_key("proj-123", "prompt", "greeting")
            'langprompt:proj-123:prompt:greeting'
            >>> Cache.make_key("proj-123", "version", "greeting", "production")
            'langprompt:proj-123:version:greeting:production'
        """
        parts = ["langprompt", project_id, resource] + list(identifiers)
        return ":".join(parts)
