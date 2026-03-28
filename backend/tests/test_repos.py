"""
Tests for the repository management API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


class TestReposEndpoint:
    """Tests for /api/repos endpoints."""

    def test_health_check(self, client: TestClient):
        """Test the health check endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["features"]["local_repos"] is True
        assert data["features"]["github_clone"] is True

    def test_root_endpoint(self, client: TestClient):
        """Test the root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "CodeTeacher API"

    def test_load_local_repo_success(self, client: TestClient, temp_repo: str):
        """Test loading a local repository successfully."""
        response = client.post(
            "/api/repos/load",
            json={"path": temp_repo}
        )
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "repo_id" in data
        assert data["root_path"] == temp_repo
        assert data["file_tree"] is not None
        assert data["file_count"] > 0
        assert "main.py" in data["message"] or "files" in data["message"].lower()

    def test_load_local_repo_not_exists(self, client: TestClient):
        """Test loading a non-existent path."""
        response = client.post(
            "/api/repos/load",
            json={"path": "/nonexistent/path/that/does/not/exist"}
        )
        assert response.status_code == 400
        assert "not exist" in response.json()["detail"].lower()

    def test_load_repo_no_path_or_url(self, client: TestClient):
        """Test loading without path or URL."""
        response = client.post(
            "/api/repos/load",
            json={}
        )
        assert response.status_code == 400
        assert "path" in response.json()["detail"].lower() or "url" in response.json()["detail"].lower()

    def test_file_tree_structure(self, client: TestClient, temp_repo: str):
        """Test that file tree has correct structure."""
        response = client.post(
            "/api/repos/load",
            json={"path": temp_repo}
        )
        assert response.status_code == 200
        data = response.json()

        file_tree = data["file_tree"]
        assert file_tree["type"] == "directory"
        assert file_tree["children"] is not None

        # Check for expected files
        child_names = [c["name"] for c in file_tree["children"]]
        assert "main.py" in child_names
        assert "index.js" in child_names
        assert "src" in child_names

    def test_file_language_detection(self, client: TestClient, temp_repo: str):
        """Test that file languages are detected correctly."""
        response = client.post(
            "/api/repos/load",
            json={"path": temp_repo}
        )
        assert response.status_code == 200
        data = response.json()

        file_tree = data["file_tree"]
        children = file_tree["children"]

        # Find files by name and check language
        for child in children:
            if child["name"] == "main.py":
                assert child["language"] == "python"
            elif child["name"] == "index.js":
                assert child["language"] == "javascript"

    def test_unload_repo(self, client: TestClient, temp_repo: str):
        """Test unloading a repository."""
        # First load a repo
        load_response = client.post(
            "/api/repos/load",
            json={"path": temp_repo}
        )
        repo_id = load_response.json()["repo_id"]

        # Then unload it
        unload_response = client.delete(f"/api/repos/{repo_id}")
        assert unload_response.status_code == 200
        assert unload_response.json()["success"] is True

    def test_unload_nonexistent_repo(self, client: TestClient):
        """Test unloading a non-existent repository."""
        response = client.delete("/api/repos/nonexistent123")
        assert response.status_code == 404


class TestBrowseEndpoint:
    """Tests for /api/repos/browse endpoint."""

    def test_browse_root(self, client: TestClient):
        """Browsing with empty path returns filesystem roots."""
        response = client.get("/api/repos/browse", params={"path": ""})
        assert response.status_code == 200
        data = response.json()
        assert "directories" in data
        assert len(data["directories"]) > 0
        # Every entry should have name and path
        for d in data["directories"]:
            assert "name" in d
            assert "path" in d

    def test_browse_valid_directory(self, client: TestClient, temp_repo: str):
        """Browsing a valid directory returns its subdirectories."""
        response = client.get("/api/repos/browse", params={"path": temp_repo})
        assert response.status_code == 200
        data = response.json()
        assert data["current"] is not None
        assert "directories" in data

    def test_browse_invalid_directory(self, client: TestClient):
        """Browsing a non-existent path returns 400."""
        response = client.get(
            "/api/repos/browse",
            params={"path": "/nonexistent/path/that/does/not/exist"}
        )
        assert response.status_code == 400

    def test_browse_has_parent(self, client: TestClient, temp_repo: str):
        """Browsing a nested directory returns a parent path."""
        response = client.get("/api/repos/browse", params={"path": temp_repo})
        assert response.status_code == 200
        data = response.json()
        assert data["parent"] is not None
