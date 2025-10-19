"""Code entity model for representing code elements."""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

from src.models.source_location import SourceLocation


class EntityType(str, Enum):
    """Types of code entities."""

    MODULE = "module"
    CLASS = "class"
    INTERFACE = "interface"
    FUNCTION = "function"
    METHOD = "method"
    CONSTRUCTOR = "constructor"
    VARIABLE = "variable"
    FIELD = "field"
    PARAMETER = "parameter"
    IMPORT = "import"


class CodeEntity(BaseModel):
    """Represents a code entity (class, function, variable, etc.).

    This is the fundamental building block for code analysis, representing
    any identifiable element in the source code.

    Attributes:
        id: Unique identifier for this entity
        name: Name of the entity
        entity_type: Type of entity (from EntityType enum)
        location: Source code location
        language: Programming language (python, javascript, java, typescript)
        parent_id: ID of parent entity (for nested entities)
        children_ids: IDs of child entities
        docstring: Documentation string if present
        signature: Function/method signature
        modifiers: Access modifiers (public, private, static, etc.)
        annotations: Type annotations or decorators
        complexity: Cyclomatic complexity (for functions/methods)
        lines_of_code: Number of lines of code
        metadata: Additional language-specific metadata
        created_at: Timestamp when entity was created in DB
    """

    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Entity name")
    entity_type: EntityType = Field(..., description="Type of entity")
    location: SourceLocation = Field(..., description="Source location")
    language: str = Field(..., description="Programming language")

    parent_id: Optional[str] = Field(default=None, description="Parent entity ID")
    children_ids: List[str] = Field(default_factory=list, description="Child entity IDs")

    docstring: Optional[str] = Field(default=None, description="Documentation string")
    signature: Optional[str] = Field(default=None, description="Function/method signature")
    modifiers: List[str] = Field(default_factory=list, description="Access modifiers")
    annotations: List[str] = Field(default_factory=list, description="Type annotations/decorators")

    complexity: Optional[int] = Field(default=None, ge=1, description="Cyclomatic complexity")
    lines_of_code: int = Field(default=0, ge=0, description="Lines of code")

    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")

    def is_function_like(self) -> bool:
        """Check if this entity is function-like (function, method, constructor).

        Returns:
            True if entity is a function, method, or constructor
        """
        return self.entity_type in {
            EntityType.FUNCTION,
            EntityType.METHOD,
            EntityType.CONSTRUCTOR,
        }

    def is_class_like(self) -> bool:
        """Check if this entity is class-like (class, interface).

        Returns:
            True if entity is a class or interface
        """
        return self.entity_type in {EntityType.CLASS, EntityType.INTERFACE}

    def is_public(self) -> bool:
        """Check if this entity is public.

        Returns:
            True if entity has public access
        """
        if "public" in self.modifiers:
            return True
        if "private" in self.modifiers or "protected" in self.modifiers:
            return False
        # Python convention: names not starting with _ are public
        return not self.name.startswith("_")

    def is_static(self) -> bool:
        """Check if this entity is static.

        Returns:
            True if entity is static
        """
        return "static" in self.modifiers or "staticmethod" in self.annotations

    def add_child(self, child_id: str) -> None:
        """Add a child entity ID.

        Args:
            child_id: ID of child entity
        """
        if child_id not in self.children_ids:
            self.children_ids.append(child_id)

    def qualified_name(self, separator: str = ".") -> str:
        """Get the fully qualified name (requires parent entities).

        Args:
            separator: Separator between name components

        Returns:
            Qualified name like "module.Class.method"

        Note:
            This is a simple version. Full implementation would need parent entities.
        """
        return self.name

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "name": self.name,
            "entity_type": self.entity_type.value,
            "location": self.location.to_string(),
            "language": self.language,
            "parent_id": self.parent_id,
            "num_children": len(self.children_ids),
            "signature": self.signature,
            "modifiers": self.modifiers,
            "complexity": self.complexity,
            "lines_of_code": self.lines_of_code,
        }

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "entity_12345",
                "name": "calculate_total",
                "entity_type": "method",
                "location": {
                    "file_path": "src/models/order.py",
                    "start_line": 45,
                    "end_line": 62,
                    "start_column": 4,
                    "end_column": 20,
                },
                "language": "python",
                "parent_id": "entity_12340",
                "docstring": "Calculate the total price including tax.",
                "signature": "def calculate_total(self, tax_rate: float) -> float",
                "modifiers": ["public"],
                "annotations": [],
                "complexity": 5,
                "lines_of_code": 17,
            }
        }
