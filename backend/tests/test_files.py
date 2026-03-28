"""
Tests for the file browsing and reading API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


class TestFilesEndpoint:
    """Tests for /api/files endpoints."""

    def test_get_file_content_success(self, client: TestClient, temp_repo: str):
        """Test reading file content successfully."""
        # First load the repo
        load_response = client.post(
            "/api/repos/load",
            json={"path": temp_repo}
        )
        repo_id = load_response.json()["repo_id"]

        # Read main.py
        response = client.get(
            "/api/files/content",
            params={"repo_id": repo_id, "file_path": "main.py"}
        )
        assert response.status_code == 200
        data = response.json()

        assert data["path"] == "main.py"
        assert data["language"] == "python"
        assert "def hello" in data["content"]
        assert "def add" in data["content"]
        assert data["line_count"] > 0

    def test_get_file_content_subdirectory(self, client: TestClient, temp_repo: str):
        """Test reading file from subdirectory."""
        # Load the repo
        load_response = client.post(
            "/api/repos/load",
            json={"path": temp_repo}
        )
        repo_id = load_response.json()["repo_id"]

        # Read src/utils.py
        response = client.get(
            "/api/files/content",
            params={"repo_id": repo_id, "file_path": "src/utils.py"}
        )
        assert response.status_code == 200
        data = response.json()

        assert data["path"] == "src/utils.py"
        assert data["language"] == "python"
        assert "format_name" in data["content"]

    def test_get_file_content_not_found(self, client: TestClient, temp_repo: str):
        """Test reading non-existent file."""
        # Load the repo
        load_response = client.post(
            "/api/repos/load",
            json={"path": temp_repo}
        )
        repo_id = load_response.json()["repo_id"]

        # Try to read non-existent file
        response = client.get(
            "/api/files/content",
            params={"repo_id": repo_id, "file_path": "nonexistent.py"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_file_content_invalid_repo(self, client: TestClient):
        """Test reading file with invalid repo ID."""
        response = client.get(
            "/api/files/content",
            params={"repo_id": "invalid_repo_id", "file_path": "main.py"}
        )
        assert response.status_code == 404

    def test_get_file_content_javascript(self, client: TestClient, temp_repo: str):
        """Test reading JavaScript file."""
        # Load the repo
        load_response = client.post(
            "/api/repos/load",
            json={"path": temp_repo}
        )
        repo_id = load_response.json()["repo_id"]

        # Read index.js
        response = client.get(
            "/api/files/content",
            params={"repo_id": repo_id, "file_path": "index.js"}
        )
        assert response.status_code == 200
        data = response.json()

        assert data["path"] == "index.js"
        assert data["language"] == "javascript"
        assert "greet" in data["content"]
        assert "module.exports" in data["content"]

    def test_get_file_tree(self, client: TestClient, temp_repo: str):
        """Test getting file tree for a loaded repo."""
        # Load the repo
        load_response = client.post(
            "/api/repos/load",
            json={"path": temp_repo}
        )
        repo_id = load_response.json()["repo_id"]

        # Get file tree
        response = client.get(
            "/api/files/tree",
            params={"repo_id": repo_id}
        )
        assert response.status_code == 200
        data = response.json()

        assert "file_tree" in data
        assert data["file_count"] > 0

    def test_line_count_accuracy(self, client: TestClient, temp_repo: str):
        """Test that line count is accurate."""
        # Load the repo
        load_response = client.post(
            "/api/repos/load",
            json={"path": temp_repo}
        )
        repo_id = load_response.json()["repo_id"]

        # Read main.py and count lines
        response = client.get(
            "/api/files/content",
            params={"repo_id": repo_id, "file_path": "main.py"}
        )
        data = response.json()

        # Count actual lines
        actual_lines = data["content"].count("\n") + 1 if data["content"] else 0
        assert data["line_count"] == actual_lines
