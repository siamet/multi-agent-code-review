"""Pytest configuration and shared fixtures."""

import pytest
from pathlib import Path


@pytest.fixture
def sample_python_file():
    """Path to sample Python file for testing.

    Returns:
        Path to sample.py
    """
    return Path(__file__).parent / "fixtures" / "sample.py"


@pytest.fixture
def sample_python_code():
    """Sample Python code as string.

    Returns:
        Python code string
    """
    return '''
def hello_world():
    """Print hello world."""
    print("Hello, World!")

class Person:
    """A person class."""

    def __init__(self, name: str):
        self.name = name

    def greet(self):
        return f"Hello, {self.name}!"
'''


@pytest.fixture
def fixtures_dir():
    """Get fixtures directory path.

    Returns:
        Path to fixtures directory
    """
    return Path(__file__).parent / "fixtures"
