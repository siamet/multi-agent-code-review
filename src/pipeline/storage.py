"""Storage protocols and in-memory implementation."""

from typing import Any, Dict, Optional, Protocol


class StorageBackend(Protocol):
    """Protocol for persisting analysis results."""

    def save_result(self, result: Any, project_id: str) -> None:
        """Save an analysis result for a project."""
        ...

    def load_result(self, project_id: str) -> Optional[Any]:
        """Load a previously saved analysis result."""
        ...


class InMemoryStorage:
    """Simple in-memory storage for testing and development."""

    def __init__(self) -> None:
        self._store: Dict[str, Any] = {}

    def save_result(self, result: Any, project_id: str) -> None:
        """Save a result."""
        self._store[project_id] = result

    def load_result(self, project_id: str) -> Optional[Any]:
        """Load a result."""
        return self._store.get(project_id)

    @property
    def size(self) -> int:
        """Number of stored results."""
        return len(self._store)
