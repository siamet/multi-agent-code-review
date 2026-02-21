"""Control flow graph representation."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import networkx as nx

from src.parsing.ast_nodes import ASTNode


@dataclass
class BasicBlock:
    """A basic block in a control flow graph.

    Attributes:
        id: Unique block identifier.
        statements: ASTNode statements in this block.
        start_line: First line of the block.
        end_line: Last line of the block.
    """

    id: str
    statements: List[ASTNode] = field(default_factory=list)
    start_line: int = 0
    end_line: int = 0

    @property
    def is_empty(self) -> bool:
        return len(self.statements) == 0


class ControlFlowGraph:
    """Control flow graph for a single function/method.

    Nodes are BasicBlocks. Edges represent control flow with labels
    like 'next', 'true', 'false', 'exception'.
    """

    def __init__(self, function_name: str) -> None:
        self.function_name = function_name
        self._graph: nx.DiGraph = nx.DiGraph()
        self._blocks: Dict[str, BasicBlock] = {}
        self.entry_block: Optional[BasicBlock] = None
        self.exit_block: Optional[BasicBlock] = None

    def add_block(self, block: BasicBlock) -> None:
        """Add a basic block to the CFG."""
        self._blocks[block.id] = block
        self._graph.add_node(block.id)

    def add_edge(self, from_id: str, to_id: str, label: str = "next") -> None:
        """Add a control flow edge between blocks."""
        self._graph.add_edge(from_id, to_id, label=label)

    def get_block(self, block_id: str) -> Optional[BasicBlock]:
        """Get a block by ID."""
        return self._blocks.get(block_id)

    def get_successors(self, block_id: str) -> List[BasicBlock]:
        """Get successor blocks."""
        return [
            self._blocks[nid] for nid in self._graph.successors(block_id) if nid in self._blocks
        ]

    def get_predecessors(self, block_id: str) -> List[BasicBlock]:
        """Get predecessor blocks."""
        return [
            self._blocks[nid] for nid in self._graph.predecessors(block_id) if nid in self._blocks
        ]

    def get_edge_label(self, from_id: str, to_id: str) -> Optional[str]:
        """Get the label on an edge."""
        if self._graph.has_edge(from_id, to_id):
            label = self._graph.edges[from_id, to_id].get("label")
            return str(label) if label is not None else None
        return None

    @property
    def block_count(self) -> int:
        """Number of basic blocks."""
        return len(self._blocks)

    @property
    def edge_count(self) -> int:
        """Number of control flow edges."""
        return int(self._graph.number_of_edges())

    @property
    def blocks(self) -> Dict[str, BasicBlock]:
        """All blocks by ID."""
        return dict(self._blocks)

    @property
    def networkx_graph(self) -> nx.DiGraph:
        """Access underlying graph."""
        return self._graph
