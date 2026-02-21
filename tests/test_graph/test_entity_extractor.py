"""Tests for EntityExtractor."""

import pytest

from src.graph.entity_extractor import EntityExtractor
from src.graph.relationship import RelationshipType
from src.models.code_entity import EntityType
from src.parsing.ast_nodes import ASTNode, NodeType


def _make_node(
    node_type: NodeType,
    name: str = None,
    children: list = None,
    language: str = "python",
    start_line: int = 1,
    end_line: int = 5,
    source_text: str = "",
    attributes: dict = None,
) -> ASTNode:
    """Helper to create ASTNode for testing."""
    node = ASTNode(
        node_type=node_type,
        name=name,
        source_text=source_text,
        start_line=start_line,
        end_line=end_line,
        start_column=0,
        end_column=0,
        language=language,
        attributes=attributes or {},
    )
    for child in children or []:
        node.add_child(child)
    return node


class TestEntityExtractor:
    """Tests for entity extraction from AST trees."""

    @pytest.fixture
    def extractor(self) -> EntityExtractor:
        return EntityExtractor()

    def test_extract_module(self, extractor: EntityExtractor) -> None:
        root = _make_node(NodeType.MODULE, source_text="# module")
        result = extractor.extract(root, "test.py")
        assert len(result.entities) == 1
        assert result.entities[0].entity_type == EntityType.MODULE
        assert result.entities[0].name == "test"
        assert result.file_path == "test.py"

    def test_extract_class(self, extractor: EntityExtractor) -> None:
        cls = _make_node(
            NodeType.CLASS,
            name="MyClass",
            start_line=3,
            end_line=10,
        )
        root = _make_node(NodeType.MODULE, children=[cls])
        result = extractor.extract(root, "test.py")
        classes = [e for e in result.entities if e.entity_type == EntityType.CLASS]
        assert len(classes) == 1
        assert classes[0].name == "MyClass"

    def test_extract_function(self, extractor: EntityExtractor) -> None:
        func = _make_node(
            NodeType.FUNCTION,
            name="my_func",
            source_text="def my_func(x):",
            start_line=1,
            end_line=3,
        )
        root = _make_node(NodeType.MODULE, children=[func])
        result = extractor.extract(root, "test.py")
        funcs = [e for e in result.entities if e.entity_type == EntityType.FUNCTION]
        assert len(funcs) == 1
        assert funcs[0].name == "my_func"
        assert funcs[0].signature == "def my_func(x):"

    def test_extract_method_in_class(self, extractor: EntityExtractor) -> None:
        method = _make_node(
            NodeType.METHOD,
            name="do_stuff",
            start_line=5,
            end_line=8,
        )
        cls = _make_node(
            NodeType.CLASS,
            name="MyClass",
            children=[method],
            start_line=3,
            end_line=10,
        )
        root = _make_node(NodeType.MODULE, children=[cls])
        result = extractor.extract(root, "test.py")

        methods = [e for e in result.entities if e.entity_type == EntityType.METHOD]
        assert len(methods) == 1
        assert methods[0].name == "do_stuff"

        # Should have a HAS_METHOD relationship from class to method
        has_method_rels = [r for r in result.relationships if r[2] == RelationshipType.HAS_METHOD]
        assert len(has_method_rels) == 1

    def test_extract_field(self, extractor: EntityExtractor) -> None:
        fld = _make_node(
            NodeType.FIELD,
            name="x",
            start_line=4,
            end_line=4,
        )
        cls = _make_node(
            NodeType.CLASS,
            name="MyClass",
            children=[fld],
            start_line=3,
            end_line=10,
        )
        root = _make_node(NodeType.MODULE, children=[cls])
        result = extractor.extract(root, "test.py")

        has_field_rels = [r for r in result.relationships if r[2] == RelationshipType.HAS_FIELD]
        assert len(has_field_rels) == 1

    def test_extract_call_relationship(self, extractor: EntityExtractor) -> None:
        callee_id = _make_node(
            NodeType.IDENTIFIER,
            name="bar",
            start_line=2,
            end_line=2,
        )
        call = _make_node(
            NodeType.CALL,
            children=[callee_id],
            start_line=2,
            end_line=2,
        )
        func = _make_node(
            NodeType.FUNCTION,
            name="foo",
            children=[call],
            start_line=1,
            end_line=3,
        )
        root = _make_node(NodeType.MODULE, children=[func])
        result = extractor.extract(root, "test.py")

        call_rels = [r for r in result.relationships if r[2] == RelationshipType.CALLS]
        assert len(call_rels) == 1
        assert call_rels[0][1].startswith("unresolved:bar")

    def test_extract_import(self, extractor: EntityExtractor) -> None:
        imp = _make_node(
            NodeType.IMPORT,
            source_text="import os",
            start_line=1,
            end_line=1,
        )
        root = _make_node(NodeType.MODULE, children=[imp])
        result = extractor.extract(root, "test.py")

        imports = [e for e in result.entities if e.entity_type == EntityType.IMPORT]
        assert len(imports) == 1

        import_rels = [r for r in result.relationships if r[2] == RelationshipType.IMPORTS]
        assert len(import_rels) == 1

    def test_containment_relationship(self, extractor: EntityExtractor) -> None:
        func = _make_node(
            NodeType.FUNCTION,
            name="foo",
            start_line=2,
            end_line=5,
        )
        root = _make_node(NodeType.MODULE, children=[func])
        result = extractor.extract(root, "test.py")

        contains_rels = [r for r in result.relationships if r[2] == RelationshipType.CONTAINS]
        assert len(contains_rels) == 1

    def test_entity_ids_are_deterministic(self, extractor: EntityExtractor) -> None:
        root = _make_node(
            NodeType.MODULE,
            children=[
                _make_node(NodeType.FUNCTION, name="foo"),
            ],
        )
        r1 = extractor.extract(root, "test.py")
        r2 = extractor.extract(root, "test.py")
        ids1 = [e.id for e in r1.entities]
        ids2 = [e.id for e in r2.entities]
        assert ids1 == ids2

    def test_lines_of_code(self, extractor: EntityExtractor) -> None:
        func = _make_node(
            NodeType.FUNCTION,
            name="foo",
            start_line=1,
            end_line=10,
        )
        root = _make_node(NodeType.MODULE, children=[func])
        result = extractor.extract(root, "test.py")
        funcs = [e for e in result.entities if e.entity_type == EntityType.FUNCTION]
        assert funcs[0].lines_of_code == 10


class TestEntityExtractorWithParsers:
    """Integration tests using real parsers."""

    @pytest.fixture
    def extractor(self) -> EntityExtractor:
        return EntityExtractor()

    def test_extract_from_python_ast(self, extractor: EntityExtractor, sample_python_file) -> None:
        from src.parsing.python_parser import PythonParser

        parser = PythonParser()
        ast = parser.parse_file(str(sample_python_file))
        assert ast is not None

        result = extractor.extract(ast, str(sample_python_file))
        assert len(result.entities) > 0

        # Should find the Calculator class and calculate_total function
        names = {e.name for e in result.entities}
        assert "Calculator" in names

        # Should find methods
        entity_types = {e.entity_type for e in result.entities}
        assert EntityType.MODULE in entity_types
        assert EntityType.CLASS in entity_types
        assert EntityType.FUNCTION in entity_types
