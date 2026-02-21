"""Tests for KnowledgeGraph."""

import pytest

from src.graph.knowledge_graph import KnowledgeGraph
from src.graph.relationship import RelationshipType
from src.models.code_entity import CodeEntity, EntityType
from src.models.source_location import SourceLocation


def _make_entity(
    entity_id: str,
    name: str,
    entity_type: EntityType,
    file_path: str = "test.py",
) -> CodeEntity:
    """Helper to create a CodeEntity for testing."""
    return CodeEntity(
        id=entity_id,
        name=name,
        entity_type=entity_type,
        location=SourceLocation(file_path=file_path, start_line=1, end_line=10),
        language="python",
    )


class TestKnowledgeGraph:
    """Tests for KnowledgeGraph entity and relationship management."""

    @pytest.fixture
    def graph(self) -> KnowledgeGraph:
        return KnowledgeGraph()

    def test_add_and_get_entity(self, graph: KnowledgeGraph) -> None:
        entity = _make_entity("c1", "MyClass", EntityType.CLASS)
        graph.add_entity(entity)
        assert graph.get_entity("c1") is entity
        assert graph.entity_count == 1

    def test_get_nonexistent_entity(self, graph: KnowledgeGraph) -> None:
        assert graph.get_entity("missing") is None

    def test_get_entities_by_type(self, graph: KnowledgeGraph) -> None:
        graph.add_entity(_make_entity("c1", "A", EntityType.CLASS))
        graph.add_entity(_make_entity("f1", "foo", EntityType.FUNCTION))
        graph.add_entity(_make_entity("c2", "B", EntityType.CLASS))
        classes = graph.get_entities_by_type(EntityType.CLASS)
        assert len(classes) == 2
        assert {e.name for e in classes} == {"A", "B"}

    def test_get_entities_by_file(self, graph: KnowledgeGraph) -> None:
        graph.add_entity(_make_entity("c1", "A", EntityType.CLASS, "a.py"))
        graph.add_entity(_make_entity("c2", "B", EntityType.CLASS, "b.py"))
        result = graph.get_entities_by_file("a.py")
        assert len(result) == 1
        assert result[0].name == "A"

    def test_add_and_query_relationship(self, graph: KnowledgeGraph) -> None:
        graph.add_entity(_make_entity("c1", "A", EntityType.CLASS))
        graph.add_entity(_make_entity("m1", "foo", EntityType.METHOD))
        graph.add_relationship("c1", "m1", RelationshipType.HAS_METHOD)
        assert graph.has_relationship("c1", "m1")
        assert graph.has_relationship("c1", "m1", RelationshipType.HAS_METHOD)
        assert not graph.has_relationship("c1", "m1", RelationshipType.CALLS)
        assert graph.relationship_count == 1

    def test_get_relationships_outgoing(self, graph: KnowledgeGraph) -> None:
        graph.add_entity(_make_entity("c1", "A", EntityType.CLASS))
        graph.add_entity(_make_entity("m1", "foo", EntityType.METHOD))
        graph.add_relationship("c1", "m1", RelationshipType.HAS_METHOD)
        rels = graph.get_relationships("c1", direction="outgoing")
        assert len(rels) == 1
        assert rels[0][1] == "m1"
        assert rels[0][2] == RelationshipType.HAS_METHOD

    def test_get_relationships_incoming(self, graph: KnowledgeGraph) -> None:
        graph.add_entity(_make_entity("c1", "A", EntityType.CLASS))
        graph.add_entity(_make_entity("m1", "foo", EntityType.METHOD))
        graph.add_relationship("c1", "m1", RelationshipType.HAS_METHOD)
        rels = graph.get_relationships("m1", direction="incoming")
        assert len(rels) == 1
        assert rels[0][0] == "c1"

    def test_get_relationships_filtered(self, graph: KnowledgeGraph) -> None:
        graph.add_entity(_make_entity("f1", "foo", EntityType.FUNCTION))
        graph.add_entity(_make_entity("f2", "bar", EntityType.FUNCTION))
        graph.add_entity(_make_entity("f3", "baz", EntityType.FUNCTION))
        graph.add_relationship("f1", "f2", RelationshipType.CALLS)
        graph.add_relationship("f1", "f3", RelationshipType.DEPENDS_ON)
        rels = graph.get_relationships("f1", direction="outgoing", rel_type=RelationshipType.CALLS)
        assert len(rels) == 1
        assert rels[0][1] == "f2"


class TestKnowledgeGraphQueries:
    """Tests for structural query methods."""

    @pytest.fixture
    def graph(self) -> KnowledgeGraph:
        g = KnowledgeGraph()
        # Build: ClassA -> method_a, ClassA -> method_b
        # method_a CALLS method_b
        g.add_entity(_make_entity("c1", "ClassA", EntityType.CLASS))
        g.add_entity(_make_entity("m1", "method_a", EntityType.METHOD))
        g.add_entity(_make_entity("m2", "method_b", EntityType.METHOD))
        g.add_entity(_make_entity("f1", "field_x", EntityType.FIELD))
        g.add_relationship("c1", "m1", RelationshipType.HAS_METHOD)
        g.add_relationship("c1", "m2", RelationshipType.HAS_METHOD)
        g.add_relationship("c1", "f1", RelationshipType.HAS_FIELD)
        g.add_relationship("m1", "m2", RelationshipType.CALLS)
        return g

    def test_get_callers(self, graph: KnowledgeGraph) -> None:
        callers = graph.get_callers("m2")
        assert len(callers) == 1
        assert callers[0].name == "method_a"

    def test_get_callees(self, graph: KnowledgeGraph) -> None:
        callees = graph.get_callees("m1")
        assert len(callees) == 1
        assert callees[0].name == "method_b"

    def test_get_class_methods(self, graph: KnowledgeGraph) -> None:
        methods = graph.get_class_methods("c1")
        assert len(methods) == 2
        assert {m.name for m in methods} == {"method_a", "method_b"}

    def test_get_class_fields(self, graph: KnowledgeGraph) -> None:
        fields = graph.get_class_fields("c1")
        assert len(fields) == 1
        assert fields[0].name == "field_x"

    def test_find_cycles(self) -> None:
        g = KnowledgeGraph()
        g.add_entity(_make_entity("a", "A", EntityType.CLASS))
        g.add_entity(_make_entity("b", "B", EntityType.CLASS))
        g.add_entity(_make_entity("c", "C", EntityType.CLASS))
        g.add_relationship("a", "b", RelationshipType.DEPENDS_ON)
        g.add_relationship("b", "c", RelationshipType.DEPENDS_ON)
        g.add_relationship("c", "a", RelationshipType.DEPENDS_ON)
        cycles = g.find_cycles()
        assert len(cycles) >= 1
        # The cycle should contain all three
        assert set(cycles[0]) == {"a", "b", "c"}

    def test_no_cycles(self) -> None:
        g = KnowledgeGraph()
        g.add_entity(_make_entity("a", "A", EntityType.CLASS))
        g.add_entity(_make_entity("b", "B", EntityType.CLASS))
        g.add_relationship("a", "b", RelationshipType.DEPENDS_ON)
        assert g.find_cycles() == []

    def test_get_inheritance_chain(self) -> None:
        g = KnowledgeGraph()
        g.add_entity(_make_entity("a", "Base", EntityType.CLASS))
        g.add_entity(_make_entity("b", "Mid", EntityType.CLASS))
        g.add_entity(_make_entity("c", "Child", EntityType.CLASS))
        g.add_relationship("c", "b", RelationshipType.INHERITS)
        g.add_relationship("b", "a", RelationshipType.INHERITS)
        chain = g.get_inheritance_chain("c")
        assert [e.name for e in chain] == ["Mid", "Base"]


class TestKnowledgeGraphFileOps:
    """Tests for file-level operations."""

    def test_remove_file_entities(self) -> None:
        g = KnowledgeGraph()
        g.add_entity(_make_entity("c1", "A", EntityType.CLASS, "a.py"))
        g.add_entity(_make_entity("c2", "B", EntityType.CLASS, "b.py"))
        g.add_relationship("c1", "c2", RelationshipType.DEPENDS_ON)
        g.remove_file_entities("a.py")
        assert g.entity_count == 1
        assert g.get_entity("c1") is None
        assert g.get_entity("c2") is not None

    def test_to_dict(self) -> None:
        g = KnowledgeGraph()
        g.add_entity(_make_entity("c1", "A", EntityType.CLASS))
        g.add_entity(_make_entity("m1", "foo", EntityType.METHOD))
        g.add_relationship("c1", "m1", RelationshipType.HAS_METHOD)
        d = g.to_dict()
        assert "c1" in d["entities"]
        assert "m1" in d["entities"]
        assert len(d["relationships"]) == 1

    def test_merge(self) -> None:
        g1 = KnowledgeGraph()
        g1.add_entity(_make_entity("c1", "A", EntityType.CLASS))
        g2 = KnowledgeGraph()
        g2.add_entity(_make_entity("c2", "B", EntityType.CLASS))
        g2.add_relationship("c2", "c1", RelationshipType.INHERITS)
        g1.merge(g2)
        assert g1.entity_count == 2
        assert g1.relationship_count == 1
