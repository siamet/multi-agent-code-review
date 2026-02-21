"""Symbol table and scope analysis."""

from dataclasses import dataclass
from typing import Dict, List, Optional

from src.parsing.ast_nodes import ASTNode, NodeType


@dataclass
class Symbol:
    """A symbol (variable, function, class, etc.) in a scope.

    Attributes:
        name: The symbol's name.
        symbol_type: Kind of symbol (variable, parameter, function, class, import).
        scope_id: ID of the scope this symbol is defined in.
        definition_node: The ASTNode where this symbol is defined.
        type_annotation: Optional type annotation string.
    """

    name: str
    symbol_type: str
    scope_id: str
    definition_node: Optional[ASTNode] = None
    type_annotation: Optional[str] = None


class Scope:
    """A lexical scope containing symbol definitions.

    Scopes form a chain: each scope has an optional parent. Symbol
    lookup walks up the chain until the symbol is found.
    """

    def __init__(self, scope_id: str, parent: Optional["Scope"] = None) -> None:
        self.scope_id = scope_id
        self.parent = parent
        self.symbols: Dict[str, Symbol] = {}
        self.children: List["Scope"] = []

    def define(self, symbol: Symbol) -> None:
        """Define a symbol in this scope."""
        self.symbols[symbol.name] = symbol

    def lookup(self, name: str) -> Optional[Symbol]:
        """Look up a symbol, searching up the scope chain."""
        if name in self.symbols:
            return self.symbols[name]
        if self.parent is not None:
            return self.parent.lookup(name)
        return None

    def lookup_local(self, name: str) -> Optional[Symbol]:
        """Look up a symbol only in this scope (no parent search)."""
        return self.symbols.get(name)


# Mapping from NodeType to symbol_type string
_NODE_TO_SYMBOL_TYPE: Dict[NodeType, str] = {
    NodeType.FUNCTION: "function",
    NodeType.METHOD: "method",
    NodeType.CONSTRUCTOR: "constructor",
    NodeType.CLASS: "class",
    NodeType.PARAMETER: "parameter",
    NodeType.VARIABLE: "variable",
    NodeType.FIELD: "field",
    NodeType.IMPORT: "import",
    NodeType.ASSIGNMENT: "variable",
}


class SymbolTable:
    """Manages scoped symbol resolution for a file.

    Builds a hierarchy of scopes from an AST tree and supports
    symbol resolution within any scope.
    """

    def __init__(self) -> None:
        self._scopes: Dict[str, Scope] = {}
        self._global_scope: Optional[Scope] = None

    def build_from_ast(self, ast_root: ASTNode) -> None:
        """Build the symbol table from an AST root.

        Args:
            ast_root: Root ASTNode (typically MODULE).
        """
        self._global_scope = Scope("global")
        self._scopes["global"] = self._global_scope
        self._walk(ast_root, self._global_scope)

    def resolve(self, name: str, scope_id: str) -> Optional[Symbol]:
        """Resolve a name in the given scope (searches up chain)."""
        scope = self._scopes.get(scope_id)
        if scope is None:
            return None
        return scope.lookup(name)

    def get_definitions(self, name: str) -> List[Symbol]:
        """Find all definitions of a name across all scopes."""
        results: List[Symbol] = []
        for scope in self._scopes.values():
            sym = scope.lookup_local(name)
            if sym is not None:
                results.append(sym)
        return results

    def get_scope(self, scope_id: str) -> Optional[Scope]:
        """Get a scope by ID."""
        return self._scopes.get(scope_id)

    @property
    def global_scope(self) -> Optional[Scope]:
        """The top-level global scope."""
        return self._global_scope

    @property
    def scope_count(self) -> int:
        """Number of scopes."""
        return len(self._scopes)

    def _walk(self, node: ASTNode, current_scope: Scope) -> None:
        """Recursively walk the AST, building scopes and symbols."""
        symbol_type = _NODE_TO_SYMBOL_TYPE.get(node.node_type)

        # Define symbol if this node produces one
        if symbol_type and node.name:
            sym = Symbol(
                name=node.name,
                symbol_type=symbol_type,
                scope_id=current_scope.scope_id,
                definition_node=node,
            )
            current_scope.define(sym)

        # Create a new scope for scope-creating constructs
        scope_creators = {
            NodeType.CLASS,
            NodeType.FUNCTION,
            NodeType.METHOD,
            NodeType.CONSTRUCTOR,
        }
        new_scope = current_scope
        if node.node_type in scope_creators:
            scope_id = f"{current_scope.scope_id}.{node.name or 'anon'}"
            new_scope = Scope(scope_id, parent=current_scope)
            current_scope.children.append(new_scope)
            self._scopes[scope_id] = new_scope

        # Also handle ASSIGNMENT nodes that define variables
        if node.node_type == NodeType.ASSIGNMENT and not node.name:
            # Try to extract the target name from first IDENTIFIER child
            for child in node.children:
                if child.node_type == NodeType.IDENTIFIER and child.name:
                    sym = Symbol(
                        name=child.name,
                        symbol_type="variable",
                        scope_id=current_scope.scope_id,
                        definition_node=node,
                    )
                    current_scope.define(sym)
                    break

        for child in node.children:
            self._walk(child, new_scope)
