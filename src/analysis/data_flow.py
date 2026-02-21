"""Basic data flow analysis on control flow graphs."""

from dataclasses import dataclass, field
from typing import Dict, List, Set

from src.parsing.ast_nodes import ASTNode, NodeType
from src.analysis.cfg import ControlFlowGraph


@dataclass(frozen=True)
class Definition:
    """A variable definition (assignment) at a specific location."""

    variable: str
    block_id: str

    def __hash__(self) -> int:
        return hash((self.variable, self.block_id))


@dataclass(frozen=True)
class Use:
    """A variable use (read) at a specific location."""

    variable: str
    block_id: str

    def __hash__(self) -> int:
        return hash((self.variable, self.block_id))


@dataclass
class DataFlowResult:
    """Results of data flow analysis.

    Attributes:
        reaching_definitions: For each block, the set of definitions
            that reach the entry of that block.
        use_def_chains: For each use, the set of definitions that
            may have produced the used value.
        def_use_chains: For each definition, the set of uses that
            may consume the defined value.
    """

    reaching_definitions: Dict[str, Set[Definition]] = field(default_factory=dict)
    use_def_chains: Dict[Use, Set[Definition]] = field(default_factory=dict)
    def_use_chains: Dict[Definition, Set[Use]] = field(default_factory=dict)


class DataFlowAnalyzer:
    """Performs basic data flow analysis on a ControlFlowGraph.

    Computes reaching definitions and use-def/def-use chains
    using a standard iterative worklist algorithm.
    """

    def analyze(self, cfg: ControlFlowGraph) -> DataFlowResult:
        """Run data flow analysis on a CFG.

        Args:
            cfg: The control flow graph to analyze.

        Returns:
            DataFlowResult with reaching definitions and chains.
        """
        # Extract definitions and uses from each block
        block_defs = self._extract_definitions(cfg)
        block_uses = self._extract_uses(cfg)

        # Compute reaching definitions
        reaching = self._compute_reaching_definitions(cfg, block_defs)

        # Build use-def and def-use chains
        ud_chains: Dict[Use, Set[Definition]] = {}
        du_chains: Dict[Definition, Set[Use]] = {}

        for block_id, uses in block_uses.items():
            reaching_at_block = reaching.get(block_id, set())
            for use in uses:
                matching_defs = {d for d in reaching_at_block if d.variable == use.variable}
                ud_chains[use] = matching_defs
                for d in matching_defs:
                    du_chains.setdefault(d, set()).add(use)

        return DataFlowResult(
            reaching_definitions=reaching,
            use_def_chains=ud_chains,
            def_use_chains=du_chains,
        )

    def _extract_definitions(self, cfg: ControlFlowGraph) -> Dict[str, Set[Definition]]:
        """Extract variable definitions from each block."""
        defs: Dict[str, Set[Definition]] = {}
        for block_id, block in cfg.blocks.items():
            block_defs: Set[Definition] = set()
            for stmt in block.statements:
                for name in self._find_defined_names(stmt):
                    block_defs.add(Definition(name, block_id))
            defs[block_id] = block_defs
        return defs

    def _extract_uses(self, cfg: ControlFlowGraph) -> Dict[str, Set[Use]]:
        """Extract variable uses from each block."""
        uses: Dict[str, Set[Use]] = {}
        for block_id, block in cfg.blocks.items():
            block_uses: Set[Use] = set()
            for stmt in block.statements:
                for name in self._find_used_names(stmt):
                    block_uses.add(Use(name, block_id))
            uses[block_id] = block_uses
        return uses

    def _compute_reaching_definitions(
        self,
        cfg: ControlFlowGraph,
        block_defs: Dict[str, Set[Definition]],
    ) -> Dict[str, Set[Definition]]:
        """Iterative worklist algorithm for reaching definitions."""
        reaching: Dict[str, Set[Definition]] = {bid: set() for bid in cfg.blocks}

        changed = True
        while changed:
            changed = False
            for block_id in cfg.blocks:
                # IN[B] = union of OUT[P] for all predecessors P
                new_in: Set[Definition] = set()
                for pred in cfg.get_predecessors(block_id):
                    pred_out = reaching.get(pred.id, set()) | block_defs.get(pred.id, set())
                    new_in |= pred_out

                if new_in != reaching[block_id]:
                    reaching[block_id] = new_in
                    changed = True

        return reaching

    def _find_defined_names(self, node: ASTNode) -> List[str]:
        """Find variable names defined (assigned) in a statement."""
        names: List[str] = []
        if node.node_type == NodeType.ASSIGNMENT:
            for child in node.children:
                if child.node_type == NodeType.IDENTIFIER and child.name:
                    names.append(child.name)
                    break  # Only first identifier is the target
        return names

    def _find_used_names(self, node: ASTNode) -> List[str]:
        """Find variable names used (read) in a statement."""
        names: List[str] = []
        for desc in node.get_descendants(NodeType.IDENTIFIER):
            if desc.name:
                names.append(desc.name)
        return names
