"""Builds control flow graphs from function ASTNodes."""

from typing import List

from src.parsing.ast_nodes import ASTNode, NodeType
from src.analysis.cfg import BasicBlock, ControlFlowGraph


class CFGBuilder:
    """Builds a ControlFlowGraph from a function/method ASTNode.

    Handles IF, FOR, WHILE, TRY, and RETURN as control flow constructs.
    Unsupported constructs are treated as single-statement blocks.
    """

    def __init__(self) -> None:
        self._counter = 0

    def build(self, function_node: ASTNode) -> ControlFlowGraph:
        """Build a CFG from a function AST node.

        Args:
            function_node: ASTNode of a function/method.

        Returns:
            ControlFlowGraph for the function.
        """
        name = function_node.name or "anonymous"
        self._counter = 0
        cfg = ControlFlowGraph(name)

        # Create entry and exit blocks
        entry = self._new_block()
        exit_block = BasicBlock(id="exit")
        cfg.add_block(entry)
        cfg.add_block(exit_block)
        cfg.entry_block = entry
        cfg.exit_block = exit_block

        # Find the body (BLOCK child or direct children)
        body = self._get_body_children(function_node)

        # Process the body statements
        last_block_id = self._process_statements(body, entry.id, exit_block.id, cfg)

        # Connect last block to exit if not already connected
        if last_block_id and last_block_id != exit_block.id:
            if not cfg.networkx_graph.has_edge(last_block_id, exit_block.id):
                cfg.add_edge(last_block_id, exit_block.id)

        return cfg

    def _process_statements(
        self,
        statements: List[ASTNode],
        current_id: str,
        exit_id: str,
        cfg: ControlFlowGraph,
    ) -> str:
        """Process a list of statements, building blocks and edges.

        Returns the ID of the last block created.
        """
        for stmt in statements:
            if stmt.node_type == NodeType.IF:
                current_id = self._process_if(stmt, current_id, exit_id, cfg)
            elif stmt.node_type == NodeType.FOR:
                current_id = self._process_loop(stmt, current_id, exit_id, cfg, "for")
            elif stmt.node_type == NodeType.WHILE:
                current_id = self._process_loop(stmt, current_id, exit_id, cfg, "while")
            elif stmt.node_type == NodeType.TRY:
                current_id = self._process_try(stmt, current_id, exit_id, cfg)
            elif stmt.node_type == NodeType.RETURN:
                block = cfg.get_block(current_id)
                if block:
                    block.statements.append(stmt)
                cfg.add_edge(current_id, exit_id, label="return")
                # After return, create a new unreachable block
                new = self._new_block()
                cfg.add_block(new)
                current_id = new.id
            else:
                # Regular statement: add to current block
                block = cfg.get_block(current_id)
                if block:
                    block.statements.append(stmt)
        return current_id

    def _process_if(
        self,
        node: ASTNode,
        current_id: str,
        exit_id: str,
        cfg: ControlFlowGraph,
    ) -> str:
        """Process an IF node, creating true/false branches."""
        # Create blocks for true branch, false branch, and merge
        true_block = self._new_block()
        false_block = self._new_block()
        merge_block = self._new_block()
        cfg.add_block(true_block)
        cfg.add_block(false_block)
        cfg.add_block(merge_block)

        cfg.add_edge(current_id, true_block.id, label="true")
        cfg.add_edge(current_id, false_block.id, label="false")

        # Process true branch children
        true_children = self._get_body_children(node)
        true_end = self._process_statements(true_children, true_block.id, exit_id, cfg)
        if true_end != exit_id:
            cfg.add_edge(true_end, merge_block.id)

        # False branch is just the merge point for simple if
        cfg.add_edge(false_block.id, merge_block.id)

        return merge_block.id

    def _process_loop(
        self,
        node: ASTNode,
        current_id: str,
        exit_id: str,
        cfg: ControlFlowGraph,
        loop_type: str,
    ) -> str:
        """Process a FOR or WHILE loop."""
        header = self._new_block()
        body = self._new_block()
        after = self._new_block()
        cfg.add_block(header)
        cfg.add_block(body)
        cfg.add_block(after)

        cfg.add_edge(current_id, header.id)
        cfg.add_edge(header.id, body.id, label="true")
        cfg.add_edge(header.id, after.id, label="false")

        # Process loop body
        body_children = self._get_body_children(node)
        body_end = self._process_statements(body_children, body.id, exit_id, cfg)
        # Back edge to header
        if body_end != exit_id:
            cfg.add_edge(body_end, header.id, label="back")

        return after.id

    def _process_try(
        self,
        node: ASTNode,
        current_id: str,
        exit_id: str,
        cfg: ControlFlowGraph,
    ) -> str:
        """Process a TRY block."""
        try_block = self._new_block()
        except_block = self._new_block()
        after = self._new_block()
        cfg.add_block(try_block)
        cfg.add_block(except_block)
        cfg.add_block(after)

        cfg.add_edge(current_id, try_block.id)
        cfg.add_edge(try_block.id, except_block.id, label="exception")
        cfg.add_edge(try_block.id, after.id)
        cfg.add_edge(except_block.id, after.id)

        return after.id

    def _get_body_children(self, node: ASTNode) -> List[ASTNode]:
        """Get the body statements from a function/if/loop node."""
        for child in node.children:
            if child.node_type == NodeType.BLOCK:
                return child.children
        # If no BLOCK child, return direct children that aren't
        # identifiers/params (i.e., skip the name/params)
        return [
            c
            for c in node.children
            if c.node_type
            not in (
                NodeType.IDENTIFIER,
                NodeType.PARAMETER,
                NodeType.UNKNOWN,
            )
        ]

    def _new_block(self) -> BasicBlock:
        """Create a new uniquely-identified block."""
        self._counter += 1
        return BasicBlock(id=f"block_{self._counter}")
