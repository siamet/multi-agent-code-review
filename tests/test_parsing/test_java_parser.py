"""Tests for Java parser."""

import pytest
from src.parsing.java_parser import JavaParser
from src.parsing.ast_nodes import NodeType


class TestJavaParser:
    """Test suite for Java parser."""

    @pytest.fixture
    def parser(self):
        """Create a Java parser instance.

        Returns:
            JavaParser instance
        """
        return JavaParser()

    def test_parser_initialization(self, parser):
        """Test that parser initializes correctly."""
        assert parser is not None
        assert parser.language == "java"

    def test_parse_simple_code(self, parser, sample_java_code):
        """Test parsing simple Java code."""
        ast = parser.parse_string(sample_java_code)

        assert ast is not None
        assert ast.node_type == NodeType.MODULE
        assert ast.language == "java"
        assert len(ast.children) > 0

    def test_parse_file(self, parser, sample_java_file):
        """Test parsing a Java file."""
        ast = parser.parse_file(str(sample_java_file))

        assert ast is not None
        assert ast.node_type == NodeType.MODULE

        # Should find class definitions
        classes = ast.get_descendants(NodeType.CLASS)
        assert len(classes) > 0, "Should find at least one class"

    def test_extract_class_names(self, parser, sample_java_file):
        """Test extracting class names from parsed code."""
        ast = parser.parse_file(str(sample_java_file))

        classes = ast.get_descendants(NodeType.CLASS)
        class_names = [cls.name for cls in classes if cls.name]

        assert "Calculator" in class_names
        assert "Helper" in class_names

    def test_extract_method_names(self, parser, sample_java_file):
        """Test extracting method names from parsed code."""
        ast = parser.parse_file(str(sample_java_file))

        methods = ast.get_descendants(NodeType.METHOD)
        method_names = [m.name for m in methods if m.name]

        assert "add" in method_names
        assert "subtract" in method_names
        assert "main" in method_names

    def test_extract_constructor(self, parser, sample_java_file):
        """Test extracting constructor declarations."""
        ast = parser.parse_file(str(sample_java_file))

        constructors = ast.get_descendants(NodeType.CONSTRUCTOR)
        assert len(constructors) > 0, "Should find at least one constructor"

    def test_node_positions(self, parser, sample_java_code):
        """Test that node positions are correctly extracted."""
        ast = parser.parse_string(sample_java_code)

        # Root should have valid positions
        assert ast.start_line > 0
        assert ast.end_line >= ast.start_line

        # All descendants should have valid positions
        for node in ast.get_descendants():
            assert node.start_line > 0
            assert node.end_line >= node.start_line
            assert node.start_column >= 0

    def test_parse_package_declaration(self, parser):
        """Test parsing package declarations."""
        code = """
        package com.example.test;

        public class Test {
        }
        """
        ast = parser.parse_string(code)

        assert ast is not None
        imports = ast.get_descendants(NodeType.IMPORT)
        # Package declarations are mapped to IMPORT type
        assert len(imports) > 0

    def test_parse_import_statements(self, parser):
        """Test parsing import statements."""
        code = """
        import java.util.ArrayList;
        import java.util.List;

        public class Test {
        }
        """
        ast = parser.parse_string(code)

        assert ast is not None
        imports = ast.get_descendants(NodeType.IMPORT)
        assert len(imports) >= 2

    def test_parse_invalid_code(self, parser):
        """Test parsing invalid Java code."""
        invalid_code = "public class Incomplete {"

        # Should not raise exception, but may return partial tree
        ast = parser.parse_string(invalid_code)

        # tree-sitter is fault-tolerant, so we should still get a result
        assert ast is not None

    def test_parse_nonexistent_file(self, parser):
        """Test parsing a file that doesn't exist."""
        result = parser.parse_file("/nonexistent/file.java")
        assert result is None

    def test_file_validation(self, parser, sample_java_file):
        """Test file validation."""
        # Valid file should pass
        assert parser.validate_file(str(sample_java_file))

        # Nonexistent file should raise error
        with pytest.raises(FileNotFoundError):
            parser.validate_file("/nonexistent/file.java")
