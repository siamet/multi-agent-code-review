"""Relationship types for the code knowledge graph."""

from enum import Enum


class RelationshipType(str, Enum):
    """Types of relationships between code entities in the knowledge graph."""

    CALLS = "calls"
    INHERITS = "inherits"
    IMPLEMENTS = "implements"
    USES = "uses"
    IMPORTS = "imports"
    DEPENDS_ON = "depends_on"
    HAS_METHOD = "has_method"
    HAS_FIELD = "has_field"
    HAS_PARAMETER = "has_parameter"
    CONTAINS = "contains"
