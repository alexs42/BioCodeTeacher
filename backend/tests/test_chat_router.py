"""
Tests for the chat router endpoints - both REST and WebSocket.
"""

import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app


class TestChatEndpoint:
    """Tests for POST /api/chat/."""

    @patch("routers.chat.OpenRouterService")
    def test_chat_success(self, mock_service_cls, client: TestClient, temp_repo: str):
        """Chat should return response."""
        load_resp = client.post("/api/repos/load", json={"path": temp_repo})
        repo_id = load_resp.json()["repo_id"]

        mock_instance = MagicMock()
        mock_instance.complete = AsyncMock(return_value="Hello! I can help.")
        mock_service_cls.return_value = mock_instance

        response = client.post("/api/chat/", json={
            "api_key": "test-key",
            "repo_id": repo_id,
            "message": "What does this code do?",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "Hello! I can help."
        assert data["has_diagram"] is False

    @patch("routers.chat.OpenRouterService")
    def test_chat_detects_mermaid_diagram(self, mock_service_cls, client: TestClient, temp_repo: str):
        """Chat should detect mermaid diagrams in response."""
        load_resp = client.post("/api/repos/load", json={"path": temp_repo})
        repo_id = load_resp.json()["repo_id"]

        mock_instance = MagicMock()
        mock_instance.complete = AsyncMock(return_value="Here is a diagram:\n```mermaid\ngraph TD\nA-->B\n```")
        mock_service_cls.return_value = mock_instance

        response = client.post("/api/chat/", json={
            "api_key": "test-key",
            "repo_id": repo_id,
            "message": "Show me a diagram",
        })
        assert response.status_code == 200
        assert response.json()["has_diagram"] is True

    @patch("routers.chat.OpenRouterService")
    def test_chat_passes_model_and_reasoning(self, mock_service_cls, client: TestClient, temp_repo: str):
        """Chat should pass model and reasoning_effort to service."""
        load_resp = client.post("/api/repos/load", json={"path": temp_repo})
        repo_id = load_resp.json()["repo_id"]

        mock_instance = MagicMock()
        mock_instance.complete = AsyncMock(return_value="response")
        mock_service_cls.return_value = mock_instance

        response = client.post("/api/chat/", json={
            "api_key": "test-key",
            "model": "openai/gpt-5.4",
            "reasoning_effort": "medium",
            "repo_id": repo_id,
            "message": "hello",
        })
        assert response.status_code == 200
        mock_service_cls.assert_called_once_with("test-key", "openai/gpt-5.4", "medium", None, provider="openrouter")

    @patch("routers.chat.OpenRouterService")
    def test_chat_with_file_context(self, mock_service_cls, client: TestClient, temp_repo: str):
        """Chat should work with file context."""
        load_resp = client.post("/api/repos/load", json={"path": temp_repo})
        repo_id = load_resp.json()["repo_id"]

        mock_instance = MagicMock()
        mock_instance.complete = AsyncMock(return_value="The file defines functions.")
        mock_service_cls.return_value = mock_instance

        response = client.post("/api/chat/", json={
            "api_key": "test-key",
            "repo_id": repo_id,
            "file_path": "main.py",
            "message": "What does this file do?",
        })
        assert response.status_code == 200

    @patch("routers.chat.OpenRouterService")
    def test_chat_with_history(self, mock_service_cls, client: TestClient, temp_repo: str):
        """Chat should pass history context."""
        load_resp = client.post("/api/repos/load", json={"path": temp_repo})
        repo_id = load_resp.json()["repo_id"]

        mock_instance = MagicMock()
        mock_instance.complete = AsyncMock(return_value="follow up answer")
        mock_service_cls.return_value = mock_instance

        response = client.post("/api/chat/", json={
            "api_key": "test-key",
            "repo_id": repo_id,
            "message": "Tell me more",
            "history": [
                {"role": "user", "content": "What is this?"},
                {"role": "assistant", "content": "It is a Python module."},
            ],
        })
        assert response.status_code == 200

    def test_chat_requires_api_key(self, client: TestClient, temp_repo: str):
        """Chat should fail without api_key."""
        load_resp = client.post("/api/repos/load", json={"path": temp_repo})
        repo_id = load_resp.json()["repo_id"]

        response = client.post("/api/chat/", json={
            "repo_id": repo_id,
            "message": "hello",
        })
        assert response.status_code == 422


class TestChatWebSocket:
    """Tests for WebSocket /api/chat/stream."""

    @patch("routers.chat.OpenRouterService")
    def test_ws_chat_stream(self, mock_service_cls, client: TestClient, temp_repo: str):
        """WebSocket chat should stream response chunks."""
        load_resp = client.post("/api/repos/load", json={"path": temp_repo})
        repo_id = load_resp.json()["repo_id"]

        async def mock_stream(*args, **kwargs):
            yield "Hello"
            yield " there!"

        mock_instance = MagicMock()
        mock_instance.stream_completion = mock_stream
        mock_service_cls.return_value = mock_instance

        with client.websocket_connect("/api/chat/stream") as ws:
            ws.send_json({
                "api_key": "test-key",
                "repo_id": repo_id,
                "message": "hello",
                "history": [],
            })

            msg1 = ws.receive_json()
            assert msg1["type"] == "start"

            msg2 = ws.receive_json()
            assert msg2["type"] == "chunk"
            assert msg2["content"] == "Hello"

            msg3 = ws.receive_json()
            assert msg3["type"] == "chunk"
            assert msg3["content"] == " there!"

            msg4 = ws.receive_json()
            assert msg4["type"] == "end"

    @patch("routers.chat.OpenRouterService")
    def test_ws_chat_requires_api_key(self, mock_service_cls, client: TestClient):
        """WebSocket chat should error without api_key."""
        with client.websocket_connect("/api/chat/stream") as ws:
            ws.send_json({
                "repo_id": "test",
                "message": "hello",
            })

            msg = ws.receive_json()
            assert msg["type"] == "error"
            assert "API key" in msg["content"]

    @patch("routers.chat.OpenRouterService")
    def test_ws_chat_passes_reasoning(self, mock_service_cls, client: TestClient, temp_repo: str):
        """WebSocket chat should pass reasoning_effort."""
        load_resp = client.post("/api/repos/load", json={"path": temp_repo})
        repo_id = load_resp.json()["repo_id"]

        async def mock_stream(*args, **kwargs):
            yield "ok"

        mock_instance = MagicMock()
        mock_instance.stream_completion = mock_stream
        mock_service_cls.return_value = mock_instance

        with client.websocket_connect("/api/chat/stream") as ws:
            ws.send_json({
                "api_key": "test-key",
                "model": "openai/gpt-5.4",
                "reasoning_effort": "medium",
                "repo_id": repo_id,
                "message": "hello",
                "history": [],
            })

            ws.receive_json()  # start
            ws.receive_json()  # chunk
            ws.receive_json()  # end

            mock_service_cls.assert_called_with("test-key", "openai/gpt-5.4", "medium", None, provider="openrouter")
