"""Caching protocols and in-memory implementation."""

import time
from typing import Any, Dict, Optional, Protocol, Tuple


class CacheBackend(Protocol):
    """Protocol for caching analysis results."""

    def get(self, key: str) -> Optional[Any]:
        """Get a cached value by key."""
        ...

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a cached value, optionally with a TTL in seconds."""
        ...

    def delete(self, key: str) -> None:
        """Delete a cached value."""
        ...

    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        ...


class InMemoryCache:
    """Simple in-memory cache for testing and development.

    Supports optional TTL (time-to-live) in seconds.
    """

    def __init__(self) -> None:
        # Stores (value, expiry_time) tuples; expiry_time=None means no TTL
        self._store: Dict[str, Tuple[Any, Optional[float]]] = {}

    def get(self, key: str) -> Optional[Any]:
        """Get a cached value, returning None if expired or missing."""
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expiry = entry
        if expiry is not None and time.time() > expiry:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a cached value."""
        expiry = time.time() + ttl if ttl is not None else None
        self._store[key] = (value, expiry)

    def delete(self, key: str) -> None:
        """Delete a cached value."""
        self._store.pop(key, None)

    def exists(self, key: str) -> bool:
        """Check if a key exists and hasn't expired."""
        return self.get(key) is not None

    def clear(self) -> None:
        """Clear all cached entries."""
        self._store.clear()

    @property
    def size(self) -> int:
        """Number of entries (may include expired)."""
        return len(self._store)
