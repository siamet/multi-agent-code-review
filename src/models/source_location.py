"""Source code location model."""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class SourceLocation(BaseModel):
    """Represents a location in source code.

    This model is used to precisely identify locations of code elements,
    issues, and refactorings in the codebase.

    Attributes:
        file_path: Relative or absolute path to the source file
        start_line: Starting line number (1-indexed)
        end_line: Ending line number (1-indexed)
        start_column: Starting column number (0-indexed)
        end_column: Ending column number (0-indexed)
        symbol_name: Optional name of the symbol at this location
    """

    file_path: str = Field(..., description="Path to the source file")
    start_line: int = Field(..., ge=1, description="Starting line (1-indexed)")
    end_line: int = Field(..., ge=1, description="Ending line (1-indexed)")
    start_column: int = Field(default=0, ge=0, description="Starting column (0-indexed)")
    end_column: int = Field(default=0, ge=0, description="Ending column (0-indexed)")
    symbol_name: Optional[str] = Field(default=None, description="Name of symbol at this location")

    @field_validator("end_line")
    @classmethod
    def validate_end_line(cls, v: int, info) -> int:
        """Ensure end_line >= start_line."""
        if "start_line" in info.data and v < info.data["start_line"]:
            raise ValueError("end_line must be >= start_line")
        return v

    @field_validator("end_column")
    @classmethod
    def validate_end_column(cls, v: int, info) -> int:
        """Ensure end_column >= start_column when on same line."""
        if "start_line" in info.data and "start_column" in info.data and "end_line" in info.data:
            if info.data["start_line"] == info.data["end_line"]:
                if v < info.data["start_column"]:
                    raise ValueError("end_column must be >= start_column when on same line")
        return v

    def contains(self, other: "SourceLocation") -> bool:
        """Check if this location contains another location.

        Args:
            other: Another source location

        Returns:
            True if this location fully contains the other location
        """
        if self.file_path != other.file_path:
            return False

        # Check if other's range is within this range
        if other.start_line < self.start_line or other.end_line > self.end_line:
            return False

        # If on same start line, check start column
        if other.start_line == self.start_line:
            if other.start_column < self.start_column:
                return False

        # If on same end line, check end column
        if other.end_line == self.end_line:
            if other.end_column > self.end_column:
                return False

        return True

    def overlaps(self, other: "SourceLocation") -> bool:
        """Check if this location overlaps with another location.

        Args:
            other: Another source location

        Returns:
            True if there is any overlap
        """
        if self.file_path != other.file_path:
            return False

        # No overlap if one ends before the other starts
        if self.end_line < other.start_line or other.end_line < self.start_line:
            return False

        # If on same line, check column overlap
        if self.start_line == self.end_line and other.start_line == other.end_line:
            if self.start_line == other.start_line:
                return not (
                    self.end_column < other.start_column or other.end_column < self.start_column
                )

        return True

    def to_string(self) -> str:
        """Convert to a human-readable string.

        Returns:
            String representation like "file.py:10:5-15:10"
        """
        result = f"{self.file_path}:{self.start_line}:{self.start_column}"
        if self.end_line != self.start_line or self.end_column != self.start_column:
            result += f"-{self.end_line}:{self.end_column}"
        if self.symbol_name:
            result += f" ({self.symbol_name})"
        return result

    def __str__(self) -> str:
        """String representation."""
        return self.to_string()

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "file_path": "src/models/user.py",
                "start_line": 42,
                "end_line": 58,
                "start_column": 4,
                "end_column": 25,
                "symbol_name": "calculate_total",
            }
        }
