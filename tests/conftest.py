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


@pytest.fixture
def sample_javascript_file():
    """Path to sample JavaScript file for testing.

    Returns:
        Path to sample.js
    """
    return Path(__file__).parent / "fixtures" / "sample.js"


@pytest.fixture
def sample_javascript_code():
    """Sample JavaScript code as string.

    Returns:
        JavaScript code string
    """
    return """
function helloWorld() {
  console.log("Hello, World!");
}

class Person {
  constructor(name) {
    this.name = name;
  }

  greet() {
    return `Hello, ${this.name}!`;
  }
}
"""


@pytest.fixture
def sample_typescript_file():
    """Path to sample TypeScript file for testing.

    Returns:
        Path to sample.ts
    """
    return Path(__file__).parent / "fixtures" / "sample.ts"


@pytest.fixture
def sample_typescript_code():
    """Sample TypeScript code as string.

    Returns:
        TypeScript code string
    """
    return """
interface Person {
  name: string;
}

function helloWorld(): void {
  console.log("Hello, World!");
}

class Greeter {
  private name: string;

  constructor(name: string) {
    this.name = name;
  }

  greet(): string {
    return `Hello, ${this.name}!`;
  }
}
"""


@pytest.fixture
def sample_java_file():
    """Path to sample Java file for testing.

    Returns:
        Path to sample.java
    """
    return Path(__file__).parent / "fixtures" / "sample.java"


@pytest.fixture
def sample_java_code():
    """Sample Java code as string.

    Returns:
        Java code string
    """
    return """
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}

class Person {
    private String name;

    public Person(String name) {
        this.name = name;
    }

    public String greet() {
        return "Hello, " + this.name + "!";
    }
}
"""
