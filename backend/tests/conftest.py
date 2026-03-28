"""
Pytest configuration and fixtures for CodeTeacher backend tests.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from services.repo_manager import RepoManager


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def temp_repo():
    """Create a temporary repository with sample files for testing."""
    temp_dir = tempfile.mkdtemp(prefix="codeteacher_test_")

    # Create sample Python file
    py_file = Path(temp_dir) / "main.py"
    py_file.write_text('''"""Sample Python module."""

def hello(name: str) -> str:
    """Return a greeting message."""
    return f"Hello, {name}!"

def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

if __name__ == "__main__":
    print(hello("World"))
''')

    # Create sample JavaScript file
    js_file = Path(temp_dir) / "index.js"
    js_file.write_text('''// Sample JavaScript module

const greet = (name) => {
    return `Hello, ${name}!`;
};

function sum(a, b) {
    return a + b;
}

module.exports = { greet, sum };
''')

    # Create a subdirectory with a file
    subdir = Path(temp_dir) / "src"
    subdir.mkdir()

    utils_file = subdir / "utils.py"
    utils_file.write_text('''"""Utility functions."""

def format_name(first: str, last: str) -> str:
    """Format a full name."""
    return f"{first} {last}"
''')

    # Create .gitignore
    gitignore = Path(temp_dir) / ".gitignore"
    gitignore.write_text('''__pycache__/
*.pyc
node_modules/
''')

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def repo_manager():
    """Create a fresh RepoManager instance for testing."""
    return RepoManager()


@pytest.fixture
def sample_python_code():
    """Sample Python code for testing explanations."""
    return '''def calculate_total(items: list[dict], tax_rate: float = 0.1) -> float:
    """Calculate the total price with tax."""
    subtotal = sum(item["price"] * item["quantity"] for item in items)
    return subtotal * (1 + tax_rate)
'''


@pytest.fixture
def sample_javascript_code():
    """Sample JavaScript code for testing explanations."""
    return '''const fetchUserData = async (userId) => {
    const response = await fetch(`/api/users/${userId}`);
    return response.json();
};
'''
