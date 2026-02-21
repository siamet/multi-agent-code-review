"""In-memory code knowledge graph backed by NetworkX."""

from typing import Any, Dict, List, Optional, Tuple

import networkx as nx

from src.models.code_entity import CodeEntity, EntityType
from src.graph.relationship import RelationshipType


class KnowledgeGraph:
    """In-memory code knowledge graph backed by a NetworkX DiGraph.

    Entities are stored as node attributes. Relationships are stored as
    edge attributes with a 'type' key holding the RelationshipType.
    """

    def __init__(self) -> None:
        self._graph: nx.DiGraph = nx.DiGraph()
        self._entities: Dict[str, CodeEntity] = {}

    # --- Entity management ---

    def add_entity(self, entity: CodeEntity) -> None:
        """Add a code entity to the graph."""
        self._entities[entity.id] = entity
        self._graph.add_node(entity.id)

    def get_entity(self, entity_id: str) -> Optional[CodeEntity]:
        """Get an entity by ID, or None if not found."""
        return self._entities.get(entity_id)

    def get_entities_by_type(self, entity_type: EntityType) -> List[CodeEntity]:
        """Get all entities of a given type."""
        return [e for e in self._entities.values() if e.entity_type == entity_type]

    def get_entities_by_file(self, file_path: str) -> List[CodeEntity]:
        """Get all entities from a given file."""
        return [e for e in self._entities.values() if e.location.file_path == file_path]

    # --- Relationship management ---

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: RelationshipType,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a relationship (edge) between two entities.

        Creates nodes if they don't exist yet (for forward references).
        """
        if not self._graph.has_node(source_id):
            self._graph.add_node(source_id)
        if not self._graph.has_node(target_id):
            self._graph.add_node(target_id)
        self._graph.add_edge(
            source_id,
            target_id,
            type=rel_type,
            metadata=metadata or {},
        )

    def get_relationships(
        self,
        entity_id: str,
        direction: str = "outgoing",
        rel_type: Optional[RelationshipType] = None,
    ) -> List[Tuple[str, str, RelationshipType, Dict[str, Any]]]:
        """Get relationships for an entity.

        Args:
            entity_id: The entity to query.
            direction: 'outgoing', 'incoming', or 'both'.
            rel_type: Optional filter by relationship type.

        Returns:
            List of (source_id, target_id, rel_type, metadata) tuples.
        """
        results: List[Tuple[str, str, RelationshipType, Dict[str, Any]]] = []

        if direction in ("outgoing", "both"):
            for _, target, data in self._graph.out_edges(entity_id, data=True):
                if rel_type is None or data.get("type") == rel_type:
                    results.append((entity_id, target, data["type"], data.get("metadata", {})))

        if direction in ("incoming", "both"):
            for source, _, data in self._graph.in_edges(entity_id, data=True):
                if rel_type is None or data.get("type") == rel_type:
                    results.append((source, entity_id, data["type"], data.get("metadata", {})))

        return results

    def has_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: Optional[RelationshipType] = None,
    ) -> bool:
        """Check if a relationship exists between two entities."""
        if not self._graph.has_edge(source_id, target_id):
            return False
        if rel_type is None:
            return True
        edge_data = self._graph.edges[source_id, target_id]
        return bool(edge_data.get("type") == rel_type)

    # --- Query methods ---

    def get_callers(self, entity_id: str) -> List[CodeEntity]:
        """Get entities that call this entity."""
        rels = self.get_relationships(
            entity_id, direction="incoming", rel_type=RelationshipType.CALLS
        )
        return [self._entities[src] for src, _, _, _ in rels if src in self._entities]

    def get_callees(self, entity_id: str) -> List[CodeEntity]:
        """Get entities that this entity calls."""
        rels = self.get_relationships(
            entity_id, direction="outgoing", rel_type=RelationshipType.CALLS
        )
        return [self._entities[tgt] for _, tgt, _, _ in rels if tgt in self._entities]

    def get_class_methods(self, class_id: str) -> List[CodeEntity]:
        """Get all methods of a class."""
        rels = self.get_relationships(
            class_id,
            direction="outgoing",
            rel_type=RelationshipType.HAS_METHOD,
        )
        return [self._entities[tgt] for _, tgt, _, _ in rels if tgt in self._entities]

    def get_class_fields(self, class_id: str) -> List[CodeEntity]:
        """Get all fields of a class."""
        rels = self.get_relationships(
            class_id,
            direction="outgoing",
            rel_type=RelationshipType.HAS_FIELD,
        )
        return [self._entities[tgt] for _, tgt, _, _ in rels if tgt in self._entities]

    def get_imports(self, module_id: str) -> List[CodeEntity]:
        """Get all entities imported by a module."""
        rels = self.get_relationships(
            module_id,
            direction="outgoing",
            rel_type=RelationshipType.IMPORTS,
        )
        return [self._entities[tgt] for _, tgt, _, _ in rels if tgt in self._entities]

    def get_inheritance_chain(self, class_id: str) -> List[CodeEntity]:
        """Get the inheritance chain (parent classes) for a class."""
        chain: List[CodeEntity] = []
        current = class_id
        visited = set()
        while current not in visited:
            visited.add(current)
            rels = self.get_relationships(
                current,
                direction="outgoing",
                rel_type=RelationshipType.INHERITS,
            )
            if not rels:
                break
            parent_id = rels[0][1]
            if parent_id in self._entities:
                chain.append(self._entities[parent_id])
            current = parent_id
        return chain

    def get_dependents(self, entity_id: str) -> List[CodeEntity]:
        """Get entities that depend on this entity (incoming DEPENDS_ON)."""
        rels = self.get_relationships(
            entity_id,
            direction="incoming",
            rel_type=RelationshipType.DEPENDS_ON,
        )
        return [self._entities[src] for src, _, _, _ in rels if src in self._entities]

    def get_dependencies(self, entity_id: str) -> List[CodeEntity]:
        """Get entities this entity depends on (outgoing DEPENDS_ON)."""
        rels = self.get_relationships(
            entity_id,
            direction="outgoing",
            rel_type=RelationshipType.DEPENDS_ON,
        )
        return [self._entities[tgt] for _, tgt, _, _ in rels if tgt in self._entities]

    def find_cycles(self, limit: int = 100) -> List[List[str]]:
        """Find circular dependencies in the graph.

        Args:
            limit: Maximum number of cycles to return.

        Returns:
            List of cycles, each as a list of entity IDs.
        """
        cycles: List[List[str]] = []
        for cycle in nx.simple_cycles(self._graph):
            cycles.append(cycle)
            if len(cycles) >= limit:
                break
        return cycles

    # --- Graph properties ---

    @property
    def entity_count(self) -> int:
        """Number of entities with CodeEntity data."""
        return len(self._entities)

    @property
    def relationship_count(self) -> int:
        """Number of relationships (edges) in the graph."""
        return int(self._graph.number_of_edges())

    @property
    def networkx_graph(self) -> nx.DiGraph:
        """Access the underlying NetworkX graph for advanced queries."""
        return self._graph

    @property
    def entities(self) -> Dict[str, CodeEntity]:
        """Access all entities by ID."""
        return dict(self._entities)

    # --- File-level operations for incremental updates ---

    def remove_file_entities(self, file_path: str) -> None:
        """Remove all entities and their relationships from a given file."""
        entity_ids = [e.id for e in self._entities.values() if e.location.file_path == file_path]
        for eid in entity_ids:
            if self._graph.has_node(eid):
                self._graph.remove_node(eid)
            del self._entities[eid]

    # --- Serialization ---

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the graph to a dictionary."""
        return {
            "entities": {eid: e.to_dict() for eid, e in self._entities.items()},
            "relationships": [
                {
                    "source": src,
                    "target": tgt,
                    "type": data["type"].value,
                    "metadata": data.get("metadata", {}),
                }
                for src, tgt, data in self._graph.edges(data=True)
            ],
        }

    def merge(self, other: "KnowledgeGraph") -> None:
        """Merge another graph into this one."""
        for entity in other._entities.values():
            self.add_entity(entity)
        for src, tgt, data in other._graph.edges(data=True):
            self.add_relationship(src, tgt, data["type"], data.get("metadata", {}))
