"""Tests for GraphBuilder."""

import pytest

from src.graph.graph_builder import GraphBuilder
from src.graph.knowledge_graph import KnowledgeGraph
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


class TestGraphBuilder:
    """Tests for multi-file graph building."""

    @pytest.fixture
    def builder(self) -> GraphBuilder:
        return GraphBuilder()

    def test_add_single_file(self, builder: GraphBuilder) -> None:
        root = _make_node(
            NodeType.MODULE,
            children=[
                _make_node(NodeType.CLASS, name="Foo"),
            ],
        )
        builder.add_file(root, "foo.py")
        graph = builder.build()
        assert graph.entity_count >= 2  # MODULE + CLASS

    def test_add_multiple_files(self, builder: GraphBuilder) -> None:
        root1 = _make_node(
            NodeType.MODULE,
            children=[_make_node(NodeType.CLASS, name="A")],
        )
        root2 = _make_node(
            NodeType.MODULE,
            children=[_make_node(NodeType.CLASS, name="B")],
        )
        builder.add_files([(root1, "a.py"), (root2, "b.py")])
        graph = builder.build()
        classes = graph.get_entities_by_type(EntityType.CLASS)
        assert len(classes) == 2

    def test_update_file(self, builder: GraphBuilder) -> None:
        root1 = _make_node(
            NodeType.MODULE,
            children=[_make_node(NodeType.CLASS, name="OldClass")],
        )
        builder.add_file(root1, "a.py")

        root2 = _make_node(
            NodeType.MODULE,
            children=[_make_node(NodeType.CLASS, name="NewClass")],
        )
        builder.update_file(root2, "a.py")
        graph = builder.build()

        names = {e.name for e in graph.get_entities_by_file("a.py")}
        assert "NewClass" in names
        assert "OldClass" not in names

    def test_resolve_cross_file_references(self, builder: GraphBuilder) -> None:
        # File a.py: function foo() that calls bar()
        bar_id = _make_node(
            NodeType.IDENTIFIER,
            name="bar",
            start_line=2,
            end_line=2,
        )
        call = _make_node(
            NodeType.CALL,
            children=[bar_id],
            start_line=2,
            end_line=2,
        )
        func_foo = _make_node(
            NodeType.FUNCTION,
            name="foo",
            children=[call],
            start_line=1,
            end_line=3,
        )
        root_a = _make_node(NodeType.MODULE, children=[func_foo])

        # File b.py: function bar()
        func_bar = _make_node(
            NodeType.FUNCTION,
            name="bar",
            start_line=1,
            end_line=3,
        )
        root_b = _make_node(NodeType.MODULE, children=[func_bar])

        builder.add_files([(root_a, "a.py"), (root_b, "b.py")])
        builder.resolve_cross_file_references()
        graph = builder.build()

        # Find the foo and bar entities
        foo_entities = [e for e in graph.entities.values() if e.name == "foo"]
        bar_entities = [e for e in graph.entities.values() if e.name == "bar"]
        assert len(foo_entities) == 1
        assert len(bar_entities) == 1

        # Check that foo CALLS bar is resolved
        callees = graph.get_callees(foo_entities[0].id)
        assert len(callees) == 1
        assert callees[0].name == "bar"

    def test_build_returns_graph(self, builder: GraphBuilder) -> None:
        graph = builder.build()
        assert isinstance(graph, KnowledgeGraph)

    def test_builder_with_existing_graph(self) -> None:
        existing = KnowledgeGraph()
        builder = GraphBuilder(graph=existing)
        assert builder.build() is existing


class TestGraphBuilderWithParsers:
    """Integration tests with real parsers."""

    def test_build_from_python_file(self, sample_python_file) -> None:
        from src.parsing.python_parser import PythonParser

        parser = PythonParser()
        ast = parser.parse_file(str(sample_python_file))
        assert ast is not None

        builder = GraphBuilder()
        builder.add_file(ast, str(sample_python_file))
        graph = builder.build()

        assert graph.entity_count > 0
        assert graph.relationship_count > 0

        classes = graph.get_entities_by_type(EntityType.CLASS)
        assert len(classes) >= 1
        assert any(c.name == "Calculator" for c in classes)
