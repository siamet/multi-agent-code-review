"""Builds a KnowledgeGraph from one or more parsed files."""

from typing import Dict, List, Optional, Tuple

from src.parsing.ast_nodes import ASTNode
from src.graph.knowledge_graph import KnowledgeGraph
from src.graph.entity_extractor import EntityExtractor
from src.graph.relationship import RelationshipType


class GraphBuilder:
    """Builds a KnowledgeGraph from parsed AST trees.

    Supports multi-file graph construction and incremental updates.
    """

    def __init__(self, graph: Optional[KnowledgeGraph] = None) -> None:
        self._graph = graph or KnowledgeGraph()
        self._extractor = EntityExtractor()

    def add_file(self, ast_root: ASTNode, file_path: str) -> None:
        """Extract entities/relationships from one file and add to graph."""
        result = self._extractor.extract(ast_root, file_path)
        for entity in result.entities:
            self._graph.add_entity(entity)
        for src_id, tgt_id, rel_type, metadata in result.relationships:
            self._graph.add_relationship(src_id, tgt_id, rel_type, metadata)

    def add_files(self, files: List[Tuple[ASTNode, str]]) -> None:
        """Add multiple files to the graph."""
        for ast_root, file_path in files:
            self.add_file(ast_root, file_path)

    def update_file(self, ast_root: ASTNode, file_path: str) -> None:
        """Re-extract a file: removes old entities, adds new ones."""
        self._graph.remove_file_entities(file_path)
        self.add_file(ast_root, file_path)

    def resolve_cross_file_references(self) -> None:
        """Resolve unresolved call/inheritance references across files.

        Matches 'unresolved:name' target IDs to actual entity IDs
        using a name-based lookup. Ambiguous matches are skipped.
        """
        # Build name -> entity_id index
        name_index: Dict[str, List[str]] = {}
        for entity in self._graph.entities.values():
            name_index.setdefault(entity.name, []).append(entity.id)

        # Find edges with unresolved targets
        edges_to_resolve: List[Tuple[str, str, RelationshipType, dict]] = []
        for src, tgt, data in self._graph.networkx_graph.edges(data=True):
            if isinstance(tgt, str) and tgt.startswith("unresolved:"):
                edges_to_resolve.append((src, tgt, data["type"], data.get("metadata", {})))

        # Resolve each edge
        for src_id, old_tgt, rel_type, metadata in edges_to_resolve:
            name = old_tgt.removeprefix("unresolved:")
            candidates = name_index.get(name, [])

            # Only resolve if there's exactly one match (unambiguous)
            if len(candidates) == 1:
                new_tgt = candidates[0]
                # Don't create self-loops
                if new_tgt != src_id:
                    self._graph.networkx_graph.remove_edge(src_id, old_tgt)
                    self._graph.add_relationship(src_id, new_tgt, rel_type, metadata)

    def build(self) -> KnowledgeGraph:
        """Return the constructed graph."""
        return self._graph
