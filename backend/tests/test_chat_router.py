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


class TestChatContextInjection:
    """Tests that chat prompts include repo/file context when available."""

    @patch("routers.chat.architecture_store")
    @patch("routers.chat.OpenRouterService")
    def test_post_includes_architecture_context(
        self, mock_service_cls, mock_arch_store, client: TestClient, temp_repo: str
    ):
        """POST chat should include architecture context in prompt."""
        load_resp = client.post("/api/repos/load", json={"path": temp_repo})
        repo_id = load_resp.json()["repo_id"]

        # Architecture store returns file-level context
        mock_arch_store.get_file_context.return_value = "This file handles QC filtering in the single-cell pipeline."
        mock_arch_store.get_context_block.return_value = None

        mock_instance = MagicMock()
        mock_instance.complete = AsyncMock(return_value="response")
        mock_service_cls.return_value = mock_instance

        client.post("/api/chat/", json={
            "api_key": "test-key",
            "repo_id": repo_id,
            "file_path": "main.py",
            "message": "What does this do?",
        })

        # Verify the prompt passed to complete() contains architecture context
        prompt_arg = mock_instance.complete.call_args[0][0]
        assert "Project & File Context" in prompt_arg
        assert "QC filtering" in prompt_arg

    @patch("routers.chat.persistent_store")
    @patch("routers.chat.architecture_store")
    @patch("routers.chat.OpenRouterService")
    def test_post_includes_file_summary(
        self, mock_service_cls, mock_arch_store, mock_persist_store,
        client: TestClient, temp_repo: str,
    ):
        """POST chat should include cached file summary in prompt."""
        load_resp = client.post("/api/repos/load", json={"path": temp_repo})
        repo_id = load_resp.json()["repo_id"]

        mock_arch_store.get_file_context.return_value = None
        mock_arch_store.get_context_block.return_value = None
        mock_persist_store.get_repo_path.return_value = temp_repo
        mock_persist_store.load_file_summary.return_value = {
            "summary_md": "This file implements CPM normalization for scRNA-seq data using Scanpy."
        }

        mock_instance = MagicMock()
        mock_instance.complete = AsyncMock(return_value="response")
        mock_service_cls.return_value = mock_instance

        client.post("/api/chat/", json={
            "api_key": "test-key",
            "repo_id": repo_id,
            "file_path": "main.py",
            "message": "Explain this",
        })

        prompt_arg = mock_instance.complete.call_args[0][0]
        assert "File Summary" in prompt_arg
        assert "CPM normalization" in prompt_arg

    @patch("routers.chat.architecture_store")
    @patch("routers.chat.OpenRouterService")
    def test_post_falls_back_to_context_block(
        self, mock_service_cls, mock_arch_store, client: TestClient, temp_repo: str
    ):
        """When no file context, should fall back to generic context block."""
        load_resp = client.post("/api/repos/load", json={"path": temp_repo})
        repo_id = load_resp.json()["repo_id"]

        mock_arch_store.get_file_context.return_value = None
        mock_arch_store.get_context_block.return_value = "Single-cell analysis pipeline using Scanpy."

        mock_instance = MagicMock()
        mock_instance.complete = AsyncMock(return_value="response")
        mock_service_cls.return_value = mock_instance

        client.post("/api/chat/", json={
            "api_key": "test-key",
            "repo_id": repo_id,
            "file_path": "main.py",
            "message": "hello",
        })

        prompt_arg = mock_instance.complete.call_args[0][0]
        assert "Project & File Context" in prompt_arg
        assert "Scanpy" in prompt_arg

    @patch("routers.chat.architecture_store")
    @patch("routers.chat.OpenRouterService")
    def test_post_no_context_graceful(
        self, mock_service_cls, mock_arch_store, client: TestClient, temp_repo: str
    ):
        """When no architecture analysis exists, prompt should work without context."""
        load_resp = client.post("/api/repos/load", json={"path": temp_repo})
        repo_id = load_resp.json()["repo_id"]

        mock_arch_store.get_file_context.return_value = None
        mock_arch_store.get_context_block.return_value = None

        mock_instance = MagicMock()
        mock_instance.complete = AsyncMock(return_value="response")
        mock_service_cls.return_value = mock_instance

        client.post("/api/chat/", json={
            "api_key": "test-key",
            "repo_id": repo_id,
            "message": "hello",
        })

        prompt_arg = mock_instance.complete.call_args[0][0]
        assert "Project & File Context" not in prompt_arg
        assert "Code Context" in prompt_arg

    @patch("routers.chat.architecture_store")
    @patch("routers.chat.OpenRouterService")
    def test_ws_includes_architecture_context(
        self, mock_service_cls, mock_arch_store, client: TestClient, temp_repo: str
    ):
        """WebSocket chat should also include architecture context."""
        load_resp = client.post("/api/repos/load", json={"path": temp_repo})
        repo_id = load_resp.json()["repo_id"]

        mock_arch_store.get_file_context.return_value = "Normalization step in pipeline."
        mock_arch_store.get_context_block.return_value = None

        captured_prompt = {}

        async def mock_stream(prompt, *args, **kwargs):
            captured_prompt["value"] = prompt
            yield "ok"

        mock_instance = MagicMock()
        mock_instance.stream_completion = mock_stream
        mock_service_cls.return_value = mock_instance

        with client.websocket_connect("/api/chat/stream") as ws:
            ws.send_json({
                "api_key": "test-key",
                "repo_id": repo_id,
                "file_path": "main.py",
                "message": "what is this?",
                "history": [],
            })

            ws.receive_json()  # start
            ws.receive_json()  # chunk
            ws.receive_json()  # end

        assert "Project & File Context" in captured_prompt["value"]
        assert "Normalization step" in captured_prompt["value"]

    @patch("routers.chat.architecture_store")
    @patch("routers.chat.OpenRouterService")
    def test_context_block_truncated_to_200_words(
        self, mock_service_cls, mock_arch_store, client: TestClient, temp_repo: str
    ):
        """Context block should be truncated to 200 words max."""
        load_resp = client.post("/api/repos/load", json={"path": temp_repo})
        repo_id = load_resp.json()["repo_id"]

        # Create a 300-word context block
        long_block = " ".join(["word"] * 300)
        mock_arch_store.get_file_context.return_value = None
        mock_arch_store.get_context_block.return_value = long_block

        mock_instance = MagicMock()
        mock_instance.complete = AsyncMock(return_value="response")
        mock_service_cls.return_value = mock_instance

        client.post("/api/chat/", json={
            "api_key": "test-key",
            "repo_id": repo_id,
            "file_path": "main.py",
            "message": "hello",
        })

        prompt_arg = mock_instance.complete.call_args[0][0]
        # The context block in the prompt should have at most 200 "word" tokens
        context_section = prompt_arg.split("---")[0]
        word_count = context_section.count("word")
        assert word_count <= 200
