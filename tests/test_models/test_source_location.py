"""Tests for SourceLocation model."""

import pytest
from pydantic import ValidationError
from src.models.source_location import SourceLocation


class TestSourceLocation:
    """Test suite for SourceLocation model."""

    def test_create_valid_location(self):
        """Test creating a valid source location."""
        loc = SourceLocation(
            file_path="src/main.py",
            start_line=10,
            end_line=20,
            start_column=5,
            end_column=15,
        )

        assert loc.file_path == "src/main.py"
        assert loc.start_line == 10
        assert loc.end_line == 20
        assert loc.start_column == 5
        assert loc.end_column == 15

    def test_line_validation(self):
        """Test that end_line must be >= start_line."""
        # Valid: end_line == start_line
        loc1 = SourceLocation(file_path="test.py", start_line=10, end_line=10)
        assert loc1.start_line == 10

        # Valid: end_line > start_line
        loc2 = SourceLocation(file_path="test.py", start_line=10, end_line=20)
        assert loc2.end_line == 20

        # Invalid: end_line < start_line
        with pytest.raises(ValidationError):
            SourceLocation(file_path="test.py", start_line=20, end_line=10)

    def test_column_validation(self):
        """Test that end_column >= start_column on same line."""
        # Valid when on same line
        loc1 = SourceLocation(
            file_path="test.py",
            start_line=10,
            end_line=10,
            start_column=5,
            end_column=15,
        )
        assert loc1.end_column == 15

        # Invalid when on same line
        with pytest.raises(ValidationError):
            SourceLocation(
                file_path="test.py",
                start_line=10,
                end_line=10,
                start_column=15,
                end_column=5,
            )

    def test_contains(self):
        """Test the contains method."""
        outer = SourceLocation(
            file_path="test.py",
            start_line=10,
            end_line=30,
            start_column=0,
            end_column=10,
        )

        inner = SourceLocation(
            file_path="test.py",
            start_line=15,
            end_line=25,
            start_column=4,
            end_column=8,
        )

        assert outer.contains(inner)
        assert not inner.contains(outer)

    def test_contains_different_files(self):
        """Test contains with different files."""
        loc1 = SourceLocation(file_path="file1.py", start_line=10, end_line=20)
        loc2 = SourceLocation(file_path="file2.py", start_line=15, end_line=18)

        assert not loc1.contains(loc2)
        assert not loc2.contains(loc1)

    def test_overlaps(self):
        """Test the overlaps method."""
        loc1 = SourceLocation(file_path="test.py", start_line=10, end_line=20)
        loc2 = SourceLocation(file_path="test.py", start_line=15, end_line=25)
        loc3 = SourceLocation(file_path="test.py", start_line=30, end_line=40)

        assert loc1.overlaps(loc2)
        assert loc2.overlaps(loc1)
        assert not loc1.overlaps(loc3)
        assert not loc3.overlaps(loc1)

    def test_to_string(self):
        """Test string representation."""
        loc = SourceLocation(
            file_path="src/main.py",
            start_line=42,
            end_line=58,
            start_column=4,
            end_column=25,
            symbol_name="calculate_total",
        )

        string_repr = loc.to_string()
        assert "src/main.py" in string_repr
        assert "42" in string_repr
        assert "58" in string_repr
        assert "calculate_total" in string_repr
