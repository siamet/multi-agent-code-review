"""Graph persistence protocols and in-memory implementation."""

from typing import Any, Dict, Optional, Protocol

from src.graph.knowledge_graph import KnowledgeGraph


class GraphPersistence(Protocol):
    """Protocol for graph persistence backends."""

    def save(self, graph: KnowledgeGraph) -> None:
        """Save a knowledge graph."""
        ...

    def load(self) -> KnowledgeGraph:
        """Load a knowledge graph."""
        ...

    def update_file(self, graph: KnowledgeGraph, file_path: str) -> None:
        """Persist updates for a single file."""
        ...


class InMemoryGraphStore:
    """Simple in-memory graph store for testing and development."""

    def __init__(self) -> None:
        self._stored: Optional[Dict[str, Any]] = None

    def save(self, graph: KnowledgeGraph) -> None:
        """Save graph as a dict snapshot."""
        self._stored = graph.to_dict()

    def load(self) -> KnowledgeGraph:
        """Load returns a new empty graph (data not reconstructed).

        Full deserialization is deferred to when a real persistence
        backend (e.g., Neo4j) is implemented.
        """
        return KnowledgeGraph()

    def update_file(self, graph: KnowledgeGraph, file_path: str) -> None:
        """Re-save the whole graph (no incremental optimization)."""
        self.save(graph)

    @property
    def stored_data(self) -> Optional[Dict[str, Any]]:
        """Access the stored dict for inspection in tests."""
        return self._stored
