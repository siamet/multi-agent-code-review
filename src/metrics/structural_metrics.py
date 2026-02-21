"""Structural/coupling metrics computed from the knowledge graph."""

from dataclasses import dataclass
from typing import Dict, Set, Tuple

from src.graph.knowledge_graph import KnowledgeGraph
from src.graph.relationship import RelationshipType


@dataclass
class StructuralMetrics:
    """Structural metrics for a code entity (typically class-level).

    Attributes:
        entity_id: ID of the entity.
        fan_in: Number of incoming CALLS relationships.
        fan_out: Number of outgoing CALLS relationships.
        afferent_coupling: Ca — classes that depend on this class.
        efferent_coupling: Ce — classes this class depends on.
        coupling_between_objects: CBO = Ca + Ce.
        lack_of_cohesion: LCOM in [0, 1]. Higher = less cohesive.
        depth_of_inheritance: DIT — length of inheritance chain.
        number_of_children: NOC — direct subclasses.
        instability: Ce / (Ca + Ce). 0 = stable, 1 = unstable.
        abstractness: Ratio of abstract methods to total methods.
    """

    entity_id: str
    fan_in: int = 0
    fan_out: int = 0
    afferent_coupling: int = 0
    efferent_coupling: int = 0
    coupling_between_objects: int = 0
    lack_of_cohesion: float = 0.0
    depth_of_inheritance: int = 0
    number_of_children: int = 0
    instability: float = 0.0
    abstractness: float = 0.0


class StructuralMetricsCalculator:
    """Computes structural metrics from a KnowledgeGraph."""

    def compute(self, graph: KnowledgeGraph, entity_id: str) -> StructuralMetrics:
        """Compute structural metrics for a single entity."""
        metrics = StructuralMetrics(entity_id=entity_id)

        fan_in, fan_out = self._compute_fan_in_out(graph, entity_id)
        metrics.fan_in = fan_in
        metrics.fan_out = fan_out

        ca, ce = self._compute_coupling(graph, entity_id)
        metrics.afferent_coupling = ca
        metrics.efferent_coupling = ce
        metrics.coupling_between_objects = ca + ce

        if ca + ce > 0:
            metrics.instability = ce / (ca + ce)

        entity = graph.get_entity(entity_id)
        if entity and entity.is_class_like():
            metrics.lack_of_cohesion = self._compute_lcom(graph, entity_id)
            metrics.depth_of_inheritance = self._compute_dit(graph, entity_id)
            metrics.number_of_children = self._compute_noc(graph, entity_id)

        return metrics

    def compute_all(self, graph: KnowledgeGraph) -> Dict[str, StructuralMetrics]:
        """Compute structural metrics for all entities in the graph."""
        return {eid: self.compute(graph, eid) for eid in graph.entities}

    def _compute_fan_in_out(self, graph: KnowledgeGraph, entity_id: str) -> Tuple[int, int]:
        """Count incoming and outgoing CALLS edges."""
        fan_in = len(
            graph.get_relationships(
                entity_id,
                direction="incoming",
                rel_type=RelationshipType.CALLS,
            )
        )
        fan_out = len(
            graph.get_relationships(
                entity_id,
                direction="outgoing",
                rel_type=RelationshipType.CALLS,
            )
        )
        return fan_in, fan_out

    def _compute_coupling(self, graph: KnowledgeGraph, entity_id: str) -> Tuple[int, int]:
        """Compute afferent (Ca) and efferent (Ce) coupling.

        Ca = number of distinct classes that depend on this class.
        Ce = number of distinct classes this class depends on.
        Considers CALLS, USES, and DEPENDS_ON relationships.
        """
        dep_types = (
            RelationshipType.CALLS,
            RelationshipType.USES,
            RelationshipType.DEPENDS_ON,
        )

        ca_set: Set[str] = set()
        ce_set: Set[str] = set()

        for rel_type in dep_types:
            for src, _, _, _ in graph.get_relationships(
                entity_id, direction="incoming", rel_type=rel_type
            ):
                ca_set.add(src)
            for _, tgt, _, _ in graph.get_relationships(
                entity_id, direction="outgoing", rel_type=rel_type
            ):
                ce_set.add(tgt)

        return len(ca_set), len(ce_set)

    def _compute_lcom(self, graph: KnowledgeGraph, class_id: str) -> float:
        """Compute Lack of Cohesion of Methods (LCOM).

        For each pair of methods in the class, check if they share
        access to any common field. LCOM = (P - Q) / total_pairs,
        clamped to [0, 1], where P = pairs with no shared fields,
        Q = pairs with shared fields.
        """
        methods = graph.get_class_methods(class_id)
        fields = graph.get_class_fields(class_id)

        if len(methods) <= 1 or not fields:
            return 0.0

        field_ids = {f.id for f in fields}

        # For each method, find which fields it accesses
        method_fields: Dict[str, Set[str]] = {}
        for method in methods:
            accessed = set()
            for _, tgt, rel, _ in graph.get_relationships(
                method.id,
                direction="outgoing",
                rel_type=RelationshipType.USES,
            ):
                if tgt in field_ids:
                    accessed.add(tgt)
            method_fields[method.id] = accessed

        # Count pairs
        method_list = list(method_fields.keys())
        p = 0  # pairs with no shared fields
        q = 0  # pairs with shared fields

        for i in range(len(method_list)):
            for j in range(i + 1, len(method_list)):
                shared = method_fields[method_list[i]] & method_fields[method_list[j]]
                if shared:
                    q += 1
                else:
                    p += 1

        total = p + q
        if total == 0:
            return 0.0
        return max((p - q) / total, 0.0)

    def _compute_dit(self, graph: KnowledgeGraph, class_id: str) -> int:
        """Compute Depth of Inheritance Tree."""
        return len(graph.get_inheritance_chain(class_id))

    def _compute_noc(self, graph: KnowledgeGraph, class_id: str) -> int:
        """Compute Number of Children (direct subclasses)."""
        return len(
            graph.get_relationships(
                class_id,
                direction="incoming",
                rel_type=RelationshipType.INHERITS,
            )
        )
