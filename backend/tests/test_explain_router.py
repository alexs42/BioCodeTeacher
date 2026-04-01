"""
Tests for the explain router endpoints - both REST and WebSocket.
Uses mocked OpenRouter service to avoid real API calls.
"""

import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from services.explanation_cache import explanation_cache


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the global explanation cache before each test."""
    explanation_cache.clear()
    yield
    explanation_cache.clear()


class TestExplainLineEndpoint:
    """Tests for POST /api/explain/line."""

    def test_explain_line_requires_api_key(self, client: TestClient, temp_repo: str):
        """Explain line should fail without api_key."""
        # Load repo first
        load_resp = client.post("/api/repos/load", json={"path": temp_repo})
        repo_id = load_resp.json()["repo_id"]

        response = client.post("/api/explain/line", json={
            "repo_id": repo_id,
            "file_path": "main.py",
            "line_number": 1,
        })
        # Should fail validation - api_key is required
        assert response.status_code == 422

    @patch("routers.explain.OpenRouterService")
    def test_explain_line_success(self, mock_service_cls, client: TestClient, temp_repo: str):
        """Explain line should return explanation on success."""
        load_resp = client.post("/api/repos/load", json={"path": temp_repo})
        repo_id = load_resp.json()["repo_id"]

        mock_instance = MagicMock()
        mock_instance.complete = AsyncMock(return_value="This is a sample module docstring.")
        mock_service_cls.return_value = mock_instance

        response = client.post("/api/explain/line", json={
            "api_key": "test-key",
            "repo_id": repo_id,
            "file_path": "main.py",
            "line_number": 1,
        })
        assert response.status_code == 200
        data = response.json()
        assert "explanation" in data
        assert data["explanation"] == "This is a sample module docstring."

    @patch("routers.explain.OpenRouterService")
    def test_explain_line_passes_model(self, mock_service_cls, client: TestClient, temp_repo: str):
        """Explain line should pass model to OpenRouterService."""
        load_resp = client.post("/api/repos/load", json={"path": temp_repo})
        repo_id = load_resp.json()["repo_id"]

        mock_instance = MagicMock()
        mock_instance.complete = AsyncMock(return_value="explanation")
        mock_service_cls.return_value = mock_instance

        response = client.post("/api/explain/line", json={
            "api_key": "test-key",
            "model": "openai/gpt-5.4",
            "reasoning_effort": "medium",
            "repo_id": repo_id,
            "file_path": "main.py",
            "line_number": 3,
        })
        assert response.status_code == 200
        mock_service_cls.assert_called_once_with("test-key", "openai/gpt-5.4", "medium", None)

    @patch("routers.explain.OpenRouterService")
    def test_explain_line_default_model(self, mock_service_cls, client: TestClient, temp_repo: str):
        """Explain line should use default model when none specified."""
        load_resp = client.post("/api/repos/load", json={"path": temp_repo})
        repo_id = load_resp.json()["repo_id"]

        mock_instance = MagicMock()
        mock_instance.complete = AsyncMock(return_value="explanation")
        mock_service_cls.return_value = mock_instance

        response = client.post("/api/explain/line", json={
            "api_key": "test-key",
            "repo_id": repo_id,
            "file_path": "main.py",
            "line_number": 4,
        })
        assert response.status_code == 200
        mock_service_cls.assert_called_once_with("test-key", "anthropic/claude-opus-4.6", None, None)

    def test_explain_line_invalid_file(self, client: TestClient, temp_repo: str):
        """Explain line should fail for non-existent file."""
        load_resp = client.post("/api/repos/load", json={"path": temp_repo})
        repo_id = load_resp.json()["repo_id"]

        response = client.post("/api/explain/line", json={
            "api_key": "test-key",
            "repo_id": repo_id,
            "file_path": "nonexistent.py",
            "line_number": 1,
        })
        assert response.status_code in (400, 404, 500)

    @patch("routers.explain.OpenRouterService")
    def test_explain_line_caches_result(self, mock_service_cls, client: TestClient, temp_repo: str):
        """Second identical request should return cached result."""
        load_resp = client.post("/api/repos/load", json={"path": temp_repo})
        repo_id = load_resp.json()["repo_id"]

        mock_instance = MagicMock()
        mock_instance.complete = AsyncMock(return_value="explanation text")
        mock_service_cls.return_value = mock_instance

        payload = {
            "api_key": "test-key",
            "repo_id": repo_id,
            "file_path": "main.py",
            "line_number": 1,
        }

        # First call
        resp1 = client.post("/api/explain/line", json=payload)
        assert resp1.status_code == 200
        assert resp1.json()["cached"] is False

        # Second call - should be cached
        resp2 = client.post("/api/explain/line", json=payload)
        assert resp2.status_code == 200
        assert resp2.json()["cached"] is True
        assert resp2.json()["explanation"] == "explanation text"


class TestExplainRangeEndpoint:
    """Tests for POST /api/explain/range."""

    @patch("routers.explain.OpenRouterService")
    def test_explain_range_success(self, mock_service_cls, client: TestClient, temp_repo: str):
        """Explain range should return explanation."""
        load_resp = client.post("/api/repos/load", json={"path": temp_repo})
        repo_id = load_resp.json()["repo_id"]

        mock_instance = MagicMock()
        mock_instance.complete = AsyncMock(return_value="range explanation")
        mock_service_cls.return_value = mock_instance

        response = client.post("/api/explain/range", json={
            "api_key": "test-key",
            "repo_id": repo_id,
            "file_path": "main.py",
            "start_line": 1,
            "end_line": 5,
        })
        assert response.status_code == 200
        assert response.json()["explanation"] == "range explanation"

    @patch("routers.explain.OpenRouterService")
    def test_explain_range_passes_reasoning(self, mock_service_cls, client: TestClient, temp_repo: str):
        """Explain range should pass reasoning_effort to service."""
        load_resp = client.post("/api/repos/load", json={"path": temp_repo})
        repo_id = load_resp.json()["repo_id"]

        mock_instance = MagicMock()
        mock_instance.complete = AsyncMock(return_value="explanation")
        mock_service_cls.return_value = mock_instance

        response = client.post("/api/explain/range", json={
            "api_key": "test-key",
            "model": "openai/gpt-5.4",
            "reasoning_effort": "high",
            "repo_id": repo_id,
            "file_path": "main.py",
            "start_line": 1,
            "end_line": 5,
        })
        assert response.status_code == 200
        mock_service_cls.assert_called_once_with("test-key", "openai/gpt-5.4", "high", None)


class TestArchitectureEndpoint:
    """Tests for POST /api/explain/architecture."""

    @patch("routers.explain.OpenRouterService")
    def test_architecture_success(self, mock_service_cls, client: TestClient, temp_repo: str):
        """Architecture analysis should return analysis."""
        load_resp = client.post("/api/repos/load", json={"path": temp_repo})
        repo_id = load_resp.json()["repo_id"]

        mock_instance = MagicMock()
        mock_instance.complete = AsyncMock(return_value="architecture analysis")
        mock_service_cls.return_value = mock_instance

        response = client.post("/api/explain/architecture", json={
            "api_key": "test-key",
            "repo_id": repo_id,
        })
        assert response.status_code == 200
        assert response.json()["analysis"] == "architecture analysis"

    @patch("routers.explain.OpenRouterService")
    def test_architecture_passes_reasoning(self, mock_service_cls, client: TestClient, temp_repo: str):
        """Architecture should pass reasoning_effort."""
        load_resp = client.post("/api/repos/load", json={"path": temp_repo})
        repo_id = load_resp.json()["repo_id"]

        mock_instance = MagicMock()
        mock_instance.complete = AsyncMock(return_value="analysis")
        mock_service_cls.return_value = mock_instance

        response = client.post("/api/explain/architecture", json={
            "api_key": "test-key",
            "model": "openai/gpt-5.4",
            "reasoning_effort": "medium",
            "repo_id": repo_id,
        })
        assert response.status_code == 200
        mock_service_cls.assert_called_once_with("test-key", "openai/gpt-5.4", "medium", None)


class TestExplainWebSocket:
    """Tests for WebSocket /api/explain/stream."""

    @patch("routers.explain.OpenRouterService")
    def test_ws_line_explanation_stream(self, mock_service_cls, client: TestClient, temp_repo: str):
        """WebSocket should stream line explanation chunks."""
        load_resp = client.post("/api/repos/load", json={"path": temp_repo})
        repo_id = load_resp.json()["repo_id"]

        async def mock_stream(*args, **kwargs):
            yield "chunk1"
            yield "chunk2"

        mock_instance = MagicMock()
        mock_instance.stream_completion = mock_stream
        mock_service_cls.return_value = mock_instance

        with client.websocket_connect("/api/explain/stream") as ws:
            ws.send_json({
                "type": "line",
                "api_key": "test-key",
                "model": "anthropic/claude-opus-4.6",
                "repo_id": repo_id,
                "file_path": "main.py",
                "line_number": 1,
                "context_lines": 5,
            })

            # Should get: start, chunk, chunk, end
            msg1 = ws.receive_json()
            assert msg1["type"] == "start"

            msg2 = ws.receive_json()
            assert msg2["type"] == "chunk"
            assert msg2["content"] == "chunk1"

            msg3 = ws.receive_json()
            assert msg3["type"] == "chunk"
            assert msg3["content"] == "chunk2"

            msg4 = ws.receive_json()
            assert msg4["type"] == "end"

    @patch("routers.explain.OpenRouterService")
    def test_ws_requires_api_key(self, mock_service_cls, client: TestClient):
        """WebSocket should return error when api_key is missing."""
        with client.websocket_connect("/api/explain/stream") as ws:
            ws.send_json({
                "type": "line",
                "repo_id": "test",
                "file_path": "test.py",
                "line_number": 1,
            })

            msg = ws.receive_json()
            assert msg["type"] == "error"
            assert "API key" in msg["content"]

    @patch("routers.explain.OpenRouterService")
    def test_ws_unknown_request_type(self, mock_service_cls, client: TestClient):
        """WebSocket should return error for unknown request type."""
        with client.websocket_connect("/api/explain/stream") as ws:
            ws.send_json({
                "type": "unknown",
                "api_key": "test-key",
            })

            msg = ws.receive_json()
            assert msg["type"] == "error"
            assert "Unknown" in msg["content"] or "unknown" in msg["content"]

    @patch("routers.explain.OpenRouterService")
    def test_ws_passes_reasoning_effort(self, mock_service_cls, client: TestClient, temp_repo: str):
        """WebSocket should pass reasoning_effort to service."""
        load_resp = client.post("/api/repos/load", json={"path": temp_repo})
        repo_id = load_resp.json()["repo_id"]

        async def mock_stream(*args, **kwargs):
            yield "test"

        mock_instance = MagicMock()
        mock_instance.stream_completion = mock_stream
        mock_service_cls.return_value = mock_instance

        with client.websocket_connect("/api/explain/stream") as ws:
            ws.send_json({
                "type": "line",
                "api_key": "test-key",
                "model": "openai/gpt-5.4",
                "reasoning_effort": "medium",
                "repo_id": repo_id,
                "file_path": "main.py",
                "line_number": 1,
            })

            # Consume messages
            ws.receive_json()  # start
            ws.receive_json()  # chunk
            ws.receive_json()  # end

            mock_service_cls.assert_called_with("test-key", "openai/gpt-5.4", "medium", None)
