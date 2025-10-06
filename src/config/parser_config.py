"""Configuration for code parsers."""

from typing import Dict, List
from pydantic import BaseModel


class ParserConfig(BaseModel):
    """Configuration for multi-language parsers.

    Attributes:
        supported_languages: List of supported language names
        language_extensions: Mapping of language to file extensions
        max_file_size_mb: Maximum file size to parse (in MB)
        timeout_seconds: Parse timeout in seconds
        skip_patterns: File patterns to skip
    """

    supported_languages: List[str] = [
        "python",
        "javascript",
        "typescript",
        "java",
    ]

    language_extensions: Dict[str, List[str]] = {
        "python": [".py", ".pyi"],
        "javascript": [".js", ".jsx", ".mjs"],
        "typescript": [".ts", ".tsx"],
        "java": [".java"],
    }

    max_file_size_mb: float = 10.0
    timeout_seconds: int = 30

    skip_patterns: List[str] = [
        "__pycache__",
        "node_modules",
        ".git",
        ".venv",
        "venv",
        "build",
        "dist",
        "*.min.js",
        "*.bundle.js",
    ]

    def get_language_for_file(self, file_path: str) -> str:
        """Detect language from file extension.

        Args:
            file_path: Path to source file

        Returns:
            Language name or "unknown"
        """
        for language, extensions in self.language_extensions.items():
            if any(file_path.endswith(ext) for ext in extensions):
                return language
        return "unknown"

    def should_skip_file(self, file_path: str) -> bool:
        """Check if file should be skipped based on patterns.

        Args:
            file_path: Path to check

        Returns:
            True if file should be skipped
        """
        return any(pattern in file_path for pattern in self.skip_patterns)
