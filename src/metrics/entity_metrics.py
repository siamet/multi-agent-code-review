"""Per-entity code metrics computed from AST trees."""

from dataclasses import dataclass
from typing import Tuple

from src.parsing.ast_nodes import ASTNode, NodeType


# NodeTypes that represent control-flow branches
_BRANCH_TYPES = {NodeType.IF, NodeType.FOR, NodeType.WHILE, NodeType.TRY}


@dataclass
class EntityMetrics:
    """Computed metrics for a single code entity.

    Attributes:
        entity_id: ID of the entity these metrics belong to.
        lines_of_code: Total lines of code.
        logical_lines: Non-blank, non-comment lines.
        cyclomatic_complexity: McCabe cyclomatic complexity.
        nesting_depth_max: Maximum nesting depth of control structures.
        nesting_depth_avg: Average nesting depth.
        parameter_count: Number of parameters.
        return_count: Number of return statements.
        branch_count: Number of branch statements (if/for/while/try).
        loop_count: Number of loops (for/while).
        comment_count: Number of comment nodes.
        call_count: Number of function/method calls.
    """

    entity_id: str
    lines_of_code: int = 0
    logical_lines: int = 0
    cyclomatic_complexity: int = 1
    nesting_depth_max: int = 0
    nesting_depth_avg: float = 0.0
    parameter_count: int = 0
    return_count: int = 0
    branch_count: int = 0
    loop_count: int = 0
    comment_count: int = 0
    call_count: int = 0


class EntityMetricsCalculator:
    """Computes per-entity metrics from ASTNode trees."""

    def compute(self, node: ASTNode, entity_id: str) -> EntityMetrics:
        """Compute all metrics for a single entity's AST subtree.

        Args:
            node: Root ASTNode of the entity (function, class, etc.).
            entity_id: The entity's ID.

        Returns:
            EntityMetrics with all computed values.
        """
        metrics = EntityMetrics(entity_id=entity_id)
        metrics.lines_of_code = self._compute_loc(node)
        metrics.logical_lines = self._compute_logical_lines(node)
        metrics.cyclomatic_complexity = self._compute_cyclomatic(node)
        max_depth, avg_depth = self._compute_nesting_depth(node)
        metrics.nesting_depth_max = max_depth
        metrics.nesting_depth_avg = avg_depth
        metrics.parameter_count = self._count_type(node, NodeType.PARAMETER)
        metrics.return_count = self._count_type(node, NodeType.RETURN)
        metrics.branch_count = self._count_branches(node)
        metrics.loop_count = self._count_loops(node)
        metrics.comment_count = self._count_type(node, NodeType.COMMENT)
        metrics.call_count = self._count_type(node, NodeType.CALL)
        return metrics

    def _compute_loc(self, node: ASTNode) -> int:
        """Lines of code from start to end line."""
        if node.end_line <= 0 or node.start_line <= 0:
            return 0
        return max(node.end_line - node.start_line + 1, 0)

    def _compute_logical_lines(self, node: ASTNode) -> int:
        """Count non-comment, non-blank logical lines (approximate).

        Counts direct statement-level children as logical lines.
        """
        count = 0
        for child in node.children:
            if child.node_type not in (
                NodeType.COMMENT,
                NodeType.UNKNOWN,
                NodeType.BLOCK,
            ):
                count += 1
            # Recurse into blocks
            if child.node_type == NodeType.BLOCK:
                count += self._compute_logical_lines(child)
        return count

    def _compute_cyclomatic(self, node: ASTNode) -> int:
        """Compute McCabe cyclomatic complexity.

        Starts at 1 and adds 1 for each decision point:
        IF, FOR, WHILE, TRY, boolean AND/OR operators.
        """
        complexity = 1
        complexity += self._count_decision_points(node)
        return complexity

    def _count_decision_points(self, node: ASTNode) -> int:
        """Recursively count decision points in the AST."""
        count = 0
        if node.node_type in _BRANCH_TYPES:
            count += 1
        # Count boolean operators (and/or) as decision points
        if node.node_type == NodeType.BINARY_OP:
            op_text = node.source_text.strip()
            if " and " in op_text or " or " in op_text:
                count += 1
            elif "&&" in op_text or "||" in op_text:
                count += 1
        for child in node.children:
            count += self._count_decision_points(child)
        return count

    def _compute_nesting_depth(self, node: ASTNode) -> Tuple[int, float]:
        """Compute max and average nesting depth of control structures.

        Returns:
            (max_depth, avg_depth) tuple.
        """
        depths: list[int] = []
        self._collect_nesting_depths(node, 0, depths)
        if not depths:
            return 0, 0.0
        return max(depths), sum(depths) / len(depths)

    def _collect_nesting_depths(self, node: ASTNode, current_depth: int, depths: list) -> None:
        """Collect depths of all control-flow nodes."""
        if node.node_type in _BRANCH_TYPES:
            depths.append(current_depth + 1)
            for child in node.children:
                self._collect_nesting_depths(child, current_depth + 1, depths)
        else:
            for child in node.children:
                self._collect_nesting_depths(child, current_depth, depths)

    def _count_type(self, node: ASTNode, node_type: NodeType) -> int:
        """Count descendants of a given type."""
        return len(node.get_descendants(node_type))

    def _count_branches(self, node: ASTNode) -> int:
        """Count branch statements (if/for/while/try)."""
        count = 0
        for bt in _BRANCH_TYPES:
            count += len(node.get_descendants(bt))
        return count

    def _count_loops(self, node: ASTNode) -> int:
        """Count loop statements (for/while)."""
        return len(node.get_descendants(NodeType.FOR)) + len(node.get_descendants(NodeType.WHILE))
