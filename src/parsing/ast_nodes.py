"""Unified AST node representation for multi-language support.

This module provides a language-agnostic AST representation that can be used
across Python, JavaScript, Java, and TypeScript codebases.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


class NodeType(str, Enum):
    """Unified node types across all supported languages."""

    # Structural
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    CONSTRUCTOR = "constructor"

    # Statements
    IMPORT = "import"
    ASSIGNMENT = "assignment"
    RETURN = "return"
    IF = "if"
    FOR = "for"
    WHILE = "while"
    TRY = "try"
    THROW = "throw"

    # Expressions
    CALL = "call"
    BINARY_OP = "binary_op"
    UNARY_OP = "unary_op"
    LITERAL = "literal"
    IDENTIFIER = "identifier"

    # Declarations
    VARIABLE = "variable"
    PARAMETER = "parameter"
    FIELD = "field"

    # Other
    COMMENT = "comment"
    BLOCK = "block"
    UNKNOWN = "unknown"


@dataclass
class ASTNode:
    """Unified AST node representation.

    This class provides a language-agnostic representation of AST nodes,
    allowing uniform analysis across different programming languages.

    Attributes:
        node_type: The type of this node (from NodeType enum)
        name: The identifier or name of this node (if applicable)
        source_text: The original source code text for this node
        start_line: Starting line number (1-indexed)
        end_line: Ending line number (1-indexed)
        start_column: Starting column number (0-indexed)
        end_column: Ending column number (0-indexed)
        children: Child nodes
        parent: Parent node reference
        attributes: Language-specific or additional attributes
        language: Source language (python, javascript, java, typescript)
    """

    node_type: NodeType
    name: Optional[str] = None
    source_text: str = ""
    start_line: int = 0
    end_line: int = 0
    start_column: int = 0
    end_column: int = 0
    children: List["ASTNode"] = field(default_factory=list)
    parent: Optional["ASTNode"] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    language: str = ""

    def __post_init__(self):
        """Set parent references for all children."""
        for child in self.children:
            child.parent = self

    def add_child(self, child: "ASTNode") -> None:
        """Add a child node and set its parent reference.

        Args:
            child: The child node to add
        """
        child.parent = self
        self.children.append(child)

    def get_descendants(self, node_type: Optional[NodeType] = None) -> List["ASTNode"]:
        """Get all descendant nodes, optionally filtered by type.

        Args:
            node_type: Optional filter for specific node type

        Returns:
            List of matching descendant nodes
        """
        descendants = []

        for child in self.children:
            if node_type is None or child.node_type == node_type:
                descendants.append(child)
            descendants.extend(child.get_descendants(node_type))

        return descendants

    def get_ancestors(self) -> List["ASTNode"]:
        """Get all ancestor nodes from parent to root.

        Returns:
            List of ancestor nodes
        """
        ancestors = []
        current = self.parent

        while current is not None:
            ancestors.append(current)
            current = current.parent

        return ancestors

    def find_by_name(self, name: str) -> List["ASTNode"]:
        """Find all descendant nodes with the given name.

        Args:
            name: Name to search for

        Returns:
            List of matching nodes
        """
        results = []

        if self.name == name:
            results.append(self)

        for child in self.children:
            results.extend(child.find_by_name(name))

        return results

    def depth(self) -> int:
        """Calculate the depth of this node in the tree.

        Returns:
            Depth (root = 0)
        """
        return len(self.get_ancestors())

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation.

        Returns:
            Dictionary representation of the node
        """
        return {
            "node_type": self.node_type.value,
            "name": self.name,
            "source_text": self.source_text[:100] + "..."
            if len(self.source_text) > 100
            else self.source_text,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "start_column": self.start_column,
            "end_column": self.end_column,
            "language": self.language,
            "attributes": self.attributes,
            "num_children": len(self.children),
        }

    def __repr__(self) -> str:
        """String representation of the node."""
        name_str = f" '{self.name}'" if self.name else ""
        return (
            f"ASTNode({self.node_type.value}{name_str}, "
            f"line {self.start_line}-{self.end_line}, "
            f"{len(self.children)} children)"
        )
