"""JavaScript/TypeScript code parser using tree-sitter."""

from typing import Optional, Any

try:
    from tree_sitter import Language, Parser
    import tree_sitter_javascript

    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False

from src.parsing.base_parser import BaseParser
from src.parsing.ast_nodes import ASTNode, NodeType
from src.utils.logger import get_logger

logger = get_logger(__name__)


class JavaScriptParser(BaseParser):
    """Parser for JavaScript source code using tree-sitter.

    This parser uses tree-sitter to parse JavaScript code and converts
    the tree-sitter AST to our unified AST representation.
    """

    def __init__(self):
        """Initialize the JavaScript parser."""
        super().__init__("javascript")

        if not TREE_SITTER_AVAILABLE:
            raise ImportError(
                "tree-sitter not available. "
                "Install with: pip install tree-sitter tree-sitter-javascript"
            )

        try:
            # Create parser with JavaScript language
            js_language = Language(tree_sitter_javascript.language())
            self.parser = Parser(js_language)
            logger.info("JavaScript parser initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize JavaScript parser: {e}")
            raise

    def parse_file(self, file_path: str) -> Optional[ASTNode]:
        """Parse a JavaScript file.

        Args:
            file_path: Path to JavaScript file

        Returns:
            Root AST node or None if parsing fails
        """
        try:
            self.validate_file(file_path)
            source_code = self.read_file(file_path)
            return self.parse_string(source_code, file_path)
        except Exception as e:
            logger.error(f"Failed to parse file {file_path}: {e}")
            return None

    def parse_string(self, source_code: str, file_path: str = "<string>") -> Optional[ASTNode]:
        """Parse JavaScript source code from string.

        Args:
            source_code: JavaScript source code
            file_path: Optional file path for context

        Returns:
            Root AST node or None if parsing fails
        """
        try:
            # Parse with tree-sitter
            tree = self.parser.parse(bytes(source_code, "utf8"))
            root_node = tree.root_node

            # Convert to our unified AST
            ast_root = self._convert_node(root_node, source_code, file_path)
            return ast_root

        except Exception as e:
            logger.error(f"Failed to parse JavaScript code: {e}")
            return None

    def _convert_node(self, ts_node: Any, source_code: str, file_path: str) -> ASTNode:
        """Convert tree-sitter node to unified ASTNode.

        Args:
            ts_node: Tree-sitter node
            source_code: Original source code
            file_path: Source file path

        Returns:
            Unified ASTNode
        """
        # Map tree-sitter node types to our NodeType
        node_type = self._map_node_type(ts_node.type)

        # Extract source text for this node
        start_byte = ts_node.start_byte
        end_byte = ts_node.end_byte
        source_text = source_code[start_byte:end_byte]

        # Get position information
        start_line = ts_node.start_point[0] + 1  # Convert to 1-indexed
        start_column = ts_node.start_point[1]
        end_line = ts_node.end_point[0] + 1
        end_column = ts_node.end_point[1]

        # Extract name if applicable
        name = self._extract_name(ts_node, source_code)

        # Create ASTNode
        ast_node = ASTNode(
            node_type=node_type,
            name=name,
            source_text=source_text,
            start_line=start_line,
            end_line=end_line,
            start_column=start_column,
            end_column=end_column,
            language="javascript",
            attributes={"ts_type": ts_node.type},
        )

        # Recursively convert children
        for child in ts_node.children:
            child_node = self._convert_node(child, source_code, file_path)
            ast_node.add_child(child_node)

        return ast_node

    def _map_node_type(self, ts_type: str) -> NodeType:
        """Map tree-sitter node type to unified NodeType.

        Args:
            ts_type: Tree-sitter node type string

        Returns:
            Unified NodeType
        """
        type_mapping = {
            # Structural
            "program": NodeType.MODULE,
            "class_declaration": NodeType.CLASS,
            "function_declaration": NodeType.FUNCTION,
            "function": NodeType.FUNCTION,
            "arrow_function": NodeType.FUNCTION,
            "method_definition": NodeType.METHOD,
            "generator_function_declaration": NodeType.FUNCTION,
            # Statements
            "import_statement": NodeType.IMPORT,
            "export_statement": NodeType.IMPORT,
            "variable_declaration": NodeType.ASSIGNMENT,
            "lexical_declaration": NodeType.ASSIGNMENT,
            "assignment_expression": NodeType.ASSIGNMENT,
            "return_statement": NodeType.RETURN,
            "if_statement": NodeType.IF,
            "for_statement": NodeType.FOR,
            "for_in_statement": NodeType.FOR,
            "while_statement": NodeType.WHILE,
            "do_statement": NodeType.WHILE,
            "try_statement": NodeType.TRY,
            "throw_statement": NodeType.THROW,
            # Expressions
            "call_expression": NodeType.CALL,
            "new_expression": NodeType.CALL,
            "binary_expression": NodeType.BINARY_OP,
            "unary_expression": NodeType.UNARY_OP,
            "update_expression": NodeType.UNARY_OP,
            "identifier": NodeType.IDENTIFIER,
            "number": NodeType.LITERAL,
            "string": NodeType.LITERAL,
            "template_string": NodeType.LITERAL,
            "true": NodeType.LITERAL,
            "false": NodeType.LITERAL,
            "null": NodeType.LITERAL,
            # Declarations
            "variable_declarator": NodeType.VARIABLE,
            "formal_parameters": NodeType.PARAMETER,
            # Other
            "comment": NodeType.COMMENT,
            "statement_block": NodeType.BLOCK,
        }

        return type_mapping.get(ts_type, NodeType.UNKNOWN)

    def _extract_name(self, ts_node: Any, source_code: str) -> Optional[str]:
        """Extract the name identifier from a node if applicable.

        Args:
            ts_node: Tree-sitter node
            source_code: Original source code

        Returns:
            Name string or None
        """
        # For function and class declarations, find the name child
        if ts_node.type in [
            "function_declaration",
            "class_declaration",
            "method_definition",
            "generator_function_declaration",
        ]:
            for child in ts_node.children:
                if child.type == "identifier":
                    start = child.start_byte
                    end = child.end_byte
                    return source_code[start:end]

        # For variable declarators, get the identifier
        if ts_node.type == "variable_declarator":
            for child in ts_node.children:
                if child.type == "identifier":
                    start = child.start_byte
                    end = child.end_byte
                    return source_code[start:end]

        # For identifiers, return the text directly
        if ts_node.type == "identifier":
            start = ts_node.start_byte
            end = ts_node.end_byte
            return source_code[start:end]

        return None


class TypeScriptParser(BaseParser):
    """Parser for TypeScript source code using tree-sitter.

    This parser uses tree-sitter to parse TypeScript code and converts
    the tree-sitter AST to our unified AST representation.
    """

    def __init__(self):
        """Initialize the TypeScript parser."""
        super().__init__("typescript")

        if not TREE_SITTER_AVAILABLE:
            raise ImportError(
                "tree-sitter not available. "
                "Install with: pip install tree-sitter tree-sitter-typescript"
            )

        try:
            # Import TypeScript tree-sitter (separate package)
            import tree_sitter_typescript

            # Create parser with TypeScript language
            ts_language = Language(tree_sitter_typescript.language_typescript())
            self.parser = Parser(ts_language)
            logger.info("TypeScript parser initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize TypeScript parser: {e}")
            raise

    def parse_file(self, file_path: str) -> Optional[ASTNode]:
        """Parse a TypeScript file.

        Args:
            file_path: Path to TypeScript file

        Returns:
            Root AST node or None if parsing fails
        """
        try:
            self.validate_file(file_path)
            source_code = self.read_file(file_path)
            return self.parse_string(source_code, file_path)
        except Exception as e:
            logger.error(f"Failed to parse file {file_path}: {e}")
            return None

    def parse_string(self, source_code: str, file_path: str = "<string>") -> Optional[ASTNode]:
        """Parse TypeScript source code from string.

        Args:
            source_code: TypeScript source code
            file_path: Optional file path for context

        Returns:
            Root AST node or None if parsing fails
        """
        try:
            # Parse with tree-sitter
            tree = self.parser.parse(bytes(source_code, "utf8"))
            root_node = tree.root_node

            # Convert to our unified AST
            ast_root = self._convert_node(root_node, source_code, file_path)
            return ast_root

        except Exception as e:
            logger.error(f"Failed to parse TypeScript code: {e}")
            return None

    def _convert_node(self, ts_node: Any, source_code: str, file_path: str) -> ASTNode:
        """Convert tree-sitter node to unified ASTNode.

        Args:
            ts_node: Tree-sitter node
            source_code: Original source code
            file_path: Source file path

        Returns:
            Unified ASTNode
        """
        # Map tree-sitter node types to our NodeType
        node_type = self._map_node_type(ts_node.type)

        # Extract source text for this node
        start_byte = ts_node.start_byte
        end_byte = ts_node.end_byte
        source_text = source_code[start_byte:end_byte]

        # Get position information
        start_line = ts_node.start_point[0] + 1  # Convert to 1-indexed
        start_column = ts_node.start_point[1]
        end_line = ts_node.end_point[0] + 1
        end_column = ts_node.end_point[1]

        # Extract name if applicable
        name = self._extract_name(ts_node, source_code)

        # Create ASTNode
        ast_node = ASTNode(
            node_type=node_type,
            name=name,
            source_text=source_text,
            start_line=start_line,
            end_line=end_line,
            start_column=start_column,
            end_column=end_column,
            language="typescript",
            attributes={"ts_type": ts_node.type},
        )

        # Recursively convert children
        for child in ts_node.children:
            child_node = self._convert_node(child, source_code, file_path)
            ast_node.add_child(child_node)

        return ast_node

    def _map_node_type(self, ts_type: str) -> NodeType:
        """Map tree-sitter node type to unified NodeType.

        Args:
            ts_type: Tree-sitter node type string

        Returns:
            Unified NodeType
        """
        type_mapping = {
            # Structural
            "program": NodeType.MODULE,
            "class_declaration": NodeType.CLASS,
            "function_declaration": NodeType.FUNCTION,
            "function": NodeType.FUNCTION,
            "arrow_function": NodeType.FUNCTION,
            "method_definition": NodeType.METHOD,
            "method_signature": NodeType.METHOD,
            "generator_function_declaration": NodeType.FUNCTION,
            # TypeScript specific
            "interface_declaration": NodeType.CLASS,
            "type_alias_declaration": NodeType.CLASS,
            # Statements
            "import_statement": NodeType.IMPORT,
            "export_statement": NodeType.IMPORT,
            "variable_declaration": NodeType.ASSIGNMENT,
            "lexical_declaration": NodeType.ASSIGNMENT,
            "assignment_expression": NodeType.ASSIGNMENT,
            "return_statement": NodeType.RETURN,
            "if_statement": NodeType.IF,
            "for_statement": NodeType.FOR,
            "for_in_statement": NodeType.FOR,
            "while_statement": NodeType.WHILE,
            "do_statement": NodeType.WHILE,
            "try_statement": NodeType.TRY,
            "throw_statement": NodeType.THROW,
            # Expressions
            "call_expression": NodeType.CALL,
            "new_expression": NodeType.CALL,
            "binary_expression": NodeType.BINARY_OP,
            "unary_expression": NodeType.UNARY_OP,
            "update_expression": NodeType.UNARY_OP,
            "identifier": NodeType.IDENTIFIER,
            "number": NodeType.LITERAL,
            "string": NodeType.LITERAL,
            "template_string": NodeType.LITERAL,
            "true": NodeType.LITERAL,
            "false": NodeType.LITERAL,
            "null": NodeType.LITERAL,
            # Declarations
            "variable_declarator": NodeType.VARIABLE,
            "formal_parameters": NodeType.PARAMETER,
            "required_parameter": NodeType.PARAMETER,
            "optional_parameter": NodeType.PARAMETER,
            # Other
            "comment": NodeType.COMMENT,
            "statement_block": NodeType.BLOCK,
        }

        return type_mapping.get(ts_type, NodeType.UNKNOWN)

    def _extract_name(self, ts_node: Any, source_code: str) -> Optional[str]:
        """Extract the name identifier from a node if applicable.

        Args:
            ts_node: Tree-sitter node
            source_code: Original source code

        Returns:
            Name string or None
        """
        # For function, class, and interface declarations, find the name child
        if ts_node.type in [
            "function_declaration",
            "class_declaration",
            "method_definition",
            "interface_declaration",
            "type_alias_declaration",
            "generator_function_declaration",
        ]:
            for child in ts_node.children:
                if child.type == "identifier" or child.type == "type_identifier":
                    start = child.start_byte
                    end = child.end_byte
                    return source_code[start:end]

        # For variable declarators, get the identifier
        if ts_node.type == "variable_declarator":
            for child in ts_node.children:
                if child.type == "identifier":
                    start = child.start_byte
                    end = child.end_byte
                    return source_code[start:end]

        # For identifiers, return the text directly
        if ts_node.type in ["identifier", "type_identifier"]:
            start = ts_node.start_byte
            end = ts_node.end_byte
            return source_code[start:end]

        return None
