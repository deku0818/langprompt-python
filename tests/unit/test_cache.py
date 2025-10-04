"""Tests for cache module."""

import time

import pytest

from langprompt.cache import Cache, CacheEntry


def test_cache_entry_expiration():
    """Test cache entry expiration."""
    entry = CacheEntry("value", ttl=1)
    assert not entry.is_expired()

    time.sleep(1.1)
    assert entry.is_expired()


def test_cache_disabled_by_default():
    """Test cache is disabled by default."""
    cache = Cache()
    assert cache.enabled is False

    # Operations should no-op when disabled
    cache.set("key", "value")
    assert cache.get("key") is None


def test_cache_enabled():
    """Test cache when enabled."""
    cache = Cache(enabled=True, default_ttl=60)
    assert cache.enabled is True

    # Set and get
    cache.set("key", "value")
    assert cache.get("key") == "value"


def test_cache_expiration():
    """Test cache entry expiration."""
    cache = Cache(enabled=True, default_ttl=1)

    cache.set("key", "value")
    assert cache.get("key") == "value"

    # Wait for expiration
    time.sleep(1.1)
    assert cache.get("key") is None


def test_cache_custom_ttl():
    """Test cache with custom TTL."""
    cache = Cache(enabled=True, default_ttl=60)

    cache.set("key", "value", ttl=1)
    assert cache.get("key") == "value"

    time.sleep(1.1)
    assert cache.get("key") is None


def test_cache_delete():
    """Test cache deletion."""
    cache = Cache(enabled=True)

    cache.set("key", "value")
    assert cache.get("key") == "value"

    cache.delete("key")
    assert cache.get("key") is None


def test_cache_clear():
    """Test cache clear."""
    cache = Cache(enabled=True)

    cache.set("key1", "value1")
    cache.set("key2", "value2")

    cache.clear()

    assert cache.get("key1") is None
    assert cache.get("key2") is None


def test_cache_cleanup_expired():
    """Test cleanup of expired entries."""
    cache = Cache(enabled=True, default_ttl=1)

    cache.set("key1", "value1", ttl=10)  # Won't expire
    cache.set("key2", "value2", ttl=1)  # Will expire

    time.sleep(1.1)

    # Cleanup expired entries
    removed = cache.cleanup_expired()
    assert removed == 1

    assert cache.get("key1") == "value1"
    assert cache.get("key2") is None


def test_cache_make_key():
    """Test cache key generation."""
    key = Cache.make_key("proj-123", "prompt", "greeting")
    assert key == "langprompt:proj-123:prompt:greeting"

    key = Cache.make_key("proj-123", "version", "greeting", "production")
    assert key == "langprompt:proj-123:version:greeting:production"
