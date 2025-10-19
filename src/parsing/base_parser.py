"""Base parser interface for multi-language support."""

from abc import ABC, abstractmethod
from typing import Optional
from pathlib import Path

from src.parsing.ast_nodes import ASTNode
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BaseParser(ABC):
    """Abstract base class for language-specific parsers.

    All language parsers must inherit from this class and implement
    the parse_file and parse_string methods.

    Attributes:
        language: Name of the programming language
    """

    def __init__(self, language: str):
        """Initialize the parser.

        Args:
            language: Programming language name
        """
        self.language = language
        logger.info(f"Initialized {language} parser")

    @abstractmethod
    def parse_file(self, file_path: str) -> Optional[ASTNode]:
        """Parse a source code file and return the AST root.

        Args:
            file_path: Path to the source file

        Returns:
            Root AST node or None if parsing fails

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is too large or invalid
        """
        pass

    @abstractmethod
    def parse_string(self, source_code: str, file_path: str = "<string>") -> Optional[ASTNode]:
        """Parse source code from a string.

        Args:
            source_code: Source code as string
            file_path: Optional file path for error messages

        Returns:
            Root AST node or None if parsing fails
        """
        pass

    def validate_file(self, file_path: str, max_size_mb: float = 10.0) -> bool:
        """Validate that a file exists and is not too large.

        Args:
            file_path: Path to validate
            max_size_mb: Maximum file size in megabytes

        Returns:
            True if file is valid

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is too large
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not path.is_file():
            raise ValueError(f"Not a file: {file_path}")

        # Check file size
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > max_size_mb:
            raise ValueError(f"File too large: {size_mb:.2f}MB (max: {max_size_mb}MB)")

        return True

    def read_file(self, file_path: str) -> str:
        """Read file contents as string.

        Args:
            file_path: Path to file

        Returns:
            File contents as string

        Raises:
            FileNotFoundError: If file doesn't exist
            UnicodeDecodeError: If file encoding is not UTF-8
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            logger.warning(f"Failed to decode {file_path} as UTF-8, trying latin-1")
            with open(file_path, "r", encoding="latin-1") as f:
                return f.read()

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(language='{self.language}')"
