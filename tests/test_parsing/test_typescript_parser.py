"""Tests for TypeScript parser."""

import pytest
from src.parsing.javascript_parser import TypeScriptParser
from src.parsing.ast_nodes import NodeType


class TestTypeScriptParser:
    """Test suite for TypeScript parser."""

    @pytest.fixture
    def parser(self):
        """Create a TypeScript parser instance.

        Returns:
            TypeScriptParser instance
        """
        return TypeScriptParser()

    def test_parser_initialization(self, parser):
        """Test that parser initializes correctly."""
        assert parser is not None
        assert parser.language == "typescript"

    def test_parse_simple_code(self, parser, sample_typescript_code):
        """Test parsing simple TypeScript code."""
        ast = parser.parse_string(sample_typescript_code)

        assert ast is not None
        assert ast.node_type == NodeType.MODULE
        assert ast.language == "typescript"
        assert len(ast.children) > 0

    def test_parse_file(self, parser, sample_typescript_file):
        """Test parsing a TypeScript file."""
        ast = parser.parse_file(str(sample_typescript_file))

        assert ast is not None
        assert ast.node_type == NodeType.MODULE

        # Should find class and function definitions
        classes = ast.get_descendants(NodeType.CLASS)
        functions = ast.get_descendants(NodeType.FUNCTION)

        assert len(classes) > 0, "Should find at least one class or interface"
        assert len(functions) > 0, "Should find at least one function"

    def test_extract_class_names(self, parser, sample_typescript_file):
        """Test extracting class names from parsed code."""
        ast = parser.parse_file(str(sample_typescript_file))

        classes = ast.get_descendants(NodeType.CLASS)
        class_names = [cls.name for cls in classes if cls.name]

        # Should find both class and interface
        assert "Calculator" in class_names
        assert "Person" in class_names

    def test_extract_function_names(self, parser, sample_typescript_file):
        """Test extracting function names from parsed code."""
        ast = parser.parse_file(str(sample_typescript_file))

        functions = ast.get_descendants(NodeType.FUNCTION)
        function_names = [fn.name for fn in functions if fn.name]

        assert "helloWorld" in function_names

    def test_node_positions(self, parser, sample_typescript_code):
        """Test that node positions are correctly extracted."""
        ast = parser.parse_string(sample_typescript_code)

        # Root should have valid positions
        assert ast.start_line > 0
        assert ast.end_line >= ast.start_line

        # All descendants should have valid positions
        for node in ast.get_descendants():
            assert node.start_line > 0
            assert node.end_line >= node.start_line
            assert node.start_column >= 0

    def test_parse_typed_functions(self, parser):
        """Test parsing typed functions."""
        code = "function add(a: number, b: number): number { return a + b; }"
        ast = parser.parse_string(code)

        assert ast is not None
        functions = ast.get_descendants(NodeType.FUNCTION)
        assert len(functions) > 0

    def test_parse_interface(self, parser):
        """Test parsing interface declarations."""
        code = """
        interface User {
            name: string;
            age: number;
        }
        """
        ast = parser.parse_string(code)

        assert ast is not None
        # Interfaces are mapped to CLASS node type
        classes = ast.get_descendants(NodeType.CLASS)
        assert len(classes) > 0

    def test_parse_invalid_code(self, parser):
        """Test parsing invalid TypeScript code."""
        invalid_code = "function incomplete("

        # Should not raise exception, but may return partial tree
        ast = parser.parse_string(invalid_code)

        # tree-sitter is fault-tolerant, so we should still get a result
        assert ast is not None

    def test_parse_nonexistent_file(self, parser):
        """Test parsing a file that doesn't exist."""
        result = parser.parse_file("/nonexistent/file.ts")
        assert result is None

    def test_file_validation(self, parser, sample_typescript_file):
        """Test file validation."""
        # Valid file should pass
        assert parser.validate_file(str(sample_typescript_file))

        # Nonexistent file should raise error
        with pytest.raises(FileNotFoundError):
            parser.validate_file("/nonexistent/file.ts")
