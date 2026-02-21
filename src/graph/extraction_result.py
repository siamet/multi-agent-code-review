"""Result of entity extraction from a single file's AST."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from src.models.code_entity import CodeEntity
from src.graph.relationship import RelationshipType


@dataclass
class ExtractionResult:
    """Holds extracted entities and relationships from a single file.

    Attributes:
        file_path: Path to the source file that was extracted.
        entities: List of CodeEntity objects found in the file.
        relationships: List of (source_id, target_id, rel_type, metadata) tuples.
    """

    file_path: str
    entities: List[CodeEntity] = field(default_factory=list)
    relationships: List[Tuple[str, str, RelationshipType, Dict[str, Any]]] = field(
        default_factory=list
    )
