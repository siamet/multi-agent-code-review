"""Facade for computing both entity and structural metrics."""

from dataclasses import dataclass, field
from typing import Dict

from src.graph.knowledge_graph import KnowledgeGraph
from src.metrics.entity_metrics import EntityMetrics, EntityMetricsCalculator
from src.metrics.structural_metrics import (
    StructuralMetrics,
    StructuralMetricsCalculator,
)
from src.parsing.ast_nodes import ASTNode


@dataclass
class MetricsResult:
    """Combined metrics result for all entities.

    Attributes:
        entity_metrics: Per-entity AST-based metrics.
        structural_metrics: Per-entity graph-based metrics.
    """

    entity_metrics: Dict[str, EntityMetrics] = field(default_factory=dict)
    structural_metrics: Dict[str, StructuralMetrics] = field(default_factory=dict)


class MetricsCalculator:
    """Coordinates entity and structural metrics computation."""

    def __init__(self) -> None:
        self._entity_calc = EntityMetricsCalculator()
        self._structural_calc = StructuralMetricsCalculator()

    def compute_all(
        self,
        graph: KnowledgeGraph,
        ast_map: Dict[str, ASTNode],
    ) -> MetricsResult:
        """Compute all metrics for entities in the graph.

        Args:
            graph: The knowledge graph with entities/relationships.
            ast_map: Mapping of file_path -> root ASTNode.

        Returns:
            MetricsResult with both entity and structural metrics.
        """
        result = MetricsResult()

        # Compute entity metrics using AST nodes
        result.entity_metrics = self._compute_entity_metrics(graph, ast_map)

        # Compute structural metrics from graph
        result.structural_metrics = self._structural_calc.compute_all(graph)

        return result

    def _compute_entity_metrics(
        self,
        graph: KnowledgeGraph,
        ast_map: Dict[str, ASTNode],
    ) -> Dict[str, EntityMetrics]:
        """Compute entity metrics by matching entities to AST nodes."""
        metrics: Dict[str, EntityMetrics] = {}

        for file_path, ast_root in ast_map.items():
            entities = graph.get_entities_by_file(file_path)
            ast_nodes_by_line = self._index_ast_by_line(ast_root)

            for entity in entities:
                ast_node = ast_nodes_by_line.get(entity.location.start_line)
                if ast_node is not None:
                    metrics[entity.id] = self._entity_calc.compute(ast_node, entity.id)

        return metrics

    def _index_ast_by_line(self, root: ASTNode) -> Dict[int, ASTNode]:
        """Build an index of AST nodes by their start line.

        Prefers nodes that are significant (classes, functions, etc.)
        over generic nodes.
        """
        index: Dict[int, ASTNode] = {}
        self._collect_by_line(root, index)
        return index

    def _collect_by_line(self, node: ASTNode, index: Dict[int, ASTNode]) -> None:
        """Recursively collect nodes indexed by start line."""
        # Only index "significant" nodes
        from src.parsing.ast_nodes import NodeType

        significant = {
            NodeType.MODULE,
            NodeType.CLASS,
            NodeType.FUNCTION,
            NodeType.METHOD,
            NodeType.CONSTRUCTOR,
            NodeType.FIELD,
        }
        if node.node_type in significant:
            index[node.start_line] = node
        for child in node.children:
            self._collect_by_line(child, index)
