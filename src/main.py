"""Main entry point for the multi-agent code review system."""

import argparse
import sys
from typing import Optional, Union

from src.utils.logger import setup_logging, get_logger
from src.config.settings import get_settings
from src.parsing.python_parser import PythonParser
from src.parsing.javascript_parser import JavaScriptParser, TypeScriptParser
from src.parsing.java_parser import JavaParser
from src.parsing.ast_nodes import NodeType

logger = get_logger(__name__)


def analyze_file(file_path: str, language: Optional[str] = None) -> None:
    """Analyze a single source file.

    Args:
        file_path: Path to source file
        language: Programming language (auto-detected if not specified)
    """
    logger.info(f"Analyzing file: {file_path}")

    # Detect language and choose parser
    if language:
        language = language.lower()
    else:
        # Auto-detect from file extension
        if file_path.endswith(".py"):
            language = "python"
        elif file_path.endswith(".js") or file_path.endswith(".jsx"):
            language = "javascript"
        elif file_path.endswith(".ts") or file_path.endswith(".tsx"):
            language = "typescript"
        elif file_path.endswith(".java"):
            language = "java"
        else:
            logger.error(f"Unsupported file type: {file_path}")
            return

    # Choose appropriate parser
    parser: Union[PythonParser, JavaScriptParser, TypeScriptParser, JavaParser]
    if language == "python":
        parser = PythonParser()
    elif language == "javascript":
        parser = JavaScriptParser()
    elif language == "typescript":
        parser = TypeScriptParser()
    elif language == "java":
        parser = JavaParser()
    else:
        logger.error(f"Unsupported language: {language}")
        return

    # Parse the file
    ast = parser.parse_file(file_path)

    if ast:
        logger.info(f"Successfully parsed {file_path}")
        logger.info(f"AST root: {ast}")

        # Print some basic statistics
        classes = ast.get_descendants(NodeType.CLASS)
        functions = ast.get_descendants(NodeType.FUNCTION)

        print(f"\n Analysis Results for {file_path}")
        print(f"   Classes found: {len(classes)}")
        print(f"   Functions found: {len(functions)}")
        print(f"   Total lines: {ast.end_line}")
    else:
        logger.error(f"Failed to parse {file_path}")


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = argparse.ArgumentParser(
        description="Multi-Agent AI System for Automated Code Review & Refactoring"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze code files")
    analyze_parser.add_argument("path", help="Path to file or directory to analyze")
    analyze_parser.add_argument(
        "--language",
        choices=["python", "javascript", "java", "typescript"],
        help="Programming language (auto-detected if not specified)",
    )

    # Version command
    subparsers.add_parser("version", help="Show version information")

    args = parser.parse_args()

    # Setup logging
    settings = get_settings()
    setup_logging(level=settings.log_level, log_file=settings.log_file)

    # Handle commands
    if args.command == "analyze":
        analyze_file(args.path, args.language)
        return 0

    elif args.command == "version":
        print("Multi-Agent Code Review System v0.1.0")
        print("Phase 0: Foundation & Infrastructure")
        return 0

    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
