"""
Tests for Pydantic request/response schemas.
Validates defaults, field constraints, and the new reasoning_effort fields.
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.schemas import (
    RepoLoadRequest,
    FileNode,
    RepoLoadResponse,
    FileContentRequest,
    FileContentResponse,
    LineExplainRequest,
    RangeExplainRequest,
    ArchitectureRequest,
    ChatRequest,
    ChatMessage,
    ChatResponse,
    StreamMessage,
    TokenInfo,
    ExplanationResponse,
)


class TestRepoSchemas:
    """Tests for repository-related schemas."""

    def test_repo_load_request_optional_fields(self):
        """RepoLoadRequest should allow empty creation."""
        req = RepoLoadRequest()
        assert req.path is None
        assert req.github_url is None
        assert req.github_token is None

    def test_repo_load_request_with_path(self):
        """RepoLoadRequest accepts a path."""
        req = RepoLoadRequest(path="/some/path")
        assert req.path == "/some/path"

    def test_repo_load_request_with_github_url(self):
        """RepoLoadRequest accepts a github url."""
        req = RepoLoadRequest(github_url="https://github.com/user/repo")
        assert req.github_url == "https://github.com/user/repo"

    def test_file_node_file(self):
        """FileNode for a file."""
        node = FileNode(name="test.py", path="test.py", type="file", language="python")
        assert node.type == "file"
        assert node.language == "python"
        assert node.children is None

    def test_file_node_directory_with_children(self):
        """FileNode for a directory with children."""
        child = FileNode(name="test.py", path="src/test.py", type="file")
        parent = FileNode(name="src", path="src", type="directory", children=[child])
        assert parent.type == "directory"
        assert len(parent.children) == 1
        assert parent.children[0].name == "test.py"


class TestExplanationSchemas:
    """Tests for explanation request schemas."""

    def test_line_explain_request_default_model(self):
        """LineExplainRequest default model should be Claude Opus 4.6."""
        req = LineExplainRequest(
            api_key="test-key",
            repo_id="repo1",
            file_path="test.py",
            line_number=1,
        )
        assert req.model == "anthropic/claude-opus-4.6"

    def test_line_explain_request_reasoning_effort_default_none(self):
        """LineExplainRequest reasoning_effort should default to None."""
        req = LineExplainRequest(
            api_key="test-key",
            repo_id="repo1",
            file_path="test.py",
            line_number=1,
        )
        assert req.reasoning_effort is None

    def test_line_explain_request_with_reasoning_effort(self):
        """LineExplainRequest accepts reasoning_effort."""
        req = LineExplainRequest(
            api_key="test-key",
            repo_id="repo1",
            file_path="test.py",
            line_number=1,
            reasoning_effort="medium",
        )
        assert req.reasoning_effort == "medium"

    def test_line_explain_request_custom_model(self):
        """LineExplainRequest accepts custom model."""
        req = LineExplainRequest(
            api_key="test-key",
            model="openai/gpt-5.4",
            repo_id="repo1",
            file_path="test.py",
            line_number=1,
        )
        assert req.model == "openai/gpt-5.4"

    def test_line_explain_request_line_number_ge_1(self):
        """LineExplainRequest should reject line_number < 1."""
        with pytest.raises(Exception):
            LineExplainRequest(
                api_key="test-key",
                repo_id="repo1",
                file_path="test.py",
                line_number=0,
            )

    def test_line_explain_request_context_lines_default(self):
        """LineExplainRequest context_lines defaults to 10."""
        req = LineExplainRequest(
            api_key="test-key",
            repo_id="repo1",
            file_path="test.py",
            line_number=1,
        )
        assert req.context_lines == 10

    def test_line_explain_request_context_lines_max(self):
        """LineExplainRequest context_lines max is 50."""
        with pytest.raises(Exception):
            LineExplainRequest(
                api_key="test-key",
                repo_id="repo1",
                file_path="test.py",
                line_number=1,
                context_lines=51,
            )

    def test_range_explain_request_default_model(self):
        """RangeExplainRequest default model should be Claude Opus 4.6."""
        req = RangeExplainRequest(
            api_key="test-key",
            repo_id="repo1",
            file_path="test.py",
            start_line=1,
            end_line=10,
        )
        assert req.model == "anthropic/claude-opus-4.6"

    def test_range_explain_request_reasoning_effort(self):
        """RangeExplainRequest accepts reasoning_effort."""
        req = RangeExplainRequest(
            api_key="test-key",
            repo_id="repo1",
            file_path="test.py",
            start_line=1,
            end_line=10,
            reasoning_effort="high",
        )
        assert req.reasoning_effort == "high"

    def test_architecture_request_default_model(self):
        """ArchitectureRequest default model should be Claude Opus 4.6."""
        req = ArchitectureRequest(
            api_key="test-key",
            repo_id="repo1",
        )
        assert req.model == "anthropic/claude-opus-4.6"

    def test_architecture_request_reasoning_effort(self):
        """ArchitectureRequest accepts reasoning_effort."""
        req = ArchitectureRequest(
            api_key="test-key",
            repo_id="repo1",
            reasoning_effort="medium",
        )
        assert req.reasoning_effort == "medium"

    def test_architecture_request_max_files_default(self):
        """ArchitectureRequest max_files defaults to 50."""
        req = ArchitectureRequest(api_key="test-key", repo_id="repo1")
        assert req.max_files == 50

    def test_architecture_request_max_files_limits(self):
        """ArchitectureRequest max_files has bounds [1, 200]."""
        with pytest.raises(Exception):
            ArchitectureRequest(api_key="test-key", repo_id="repo1", max_files=0)
        with pytest.raises(Exception):
            ArchitectureRequest(api_key="test-key", repo_id="repo1", max_files=201)


class TestChatSchemas:
    """Tests for chat-related schemas."""

    def test_chat_request_default_model(self):
        """ChatRequest default model should be Claude Opus 4.6."""
        req = ChatRequest(
            api_key="test-key",
            repo_id="repo1",
            message="hello",
        )
        assert req.model == "anthropic/claude-opus-4.6"

    def test_chat_request_reasoning_effort(self):
        """ChatRequest accepts reasoning_effort."""
        req = ChatRequest(
            api_key="test-key",
            repo_id="repo1",
            message="hello",
            reasoning_effort="medium",
        )
        assert req.reasoning_effort == "medium"

    def test_chat_request_optional_fields(self):
        """ChatRequest file_path and line_range are optional."""
        req = ChatRequest(
            api_key="test-key",
            repo_id="repo1",
            message="hello",
        )
        assert req.file_path is None
        assert req.line_range is None
        assert req.history == []

    def test_chat_request_with_history(self):
        """ChatRequest accepts message history."""
        req = ChatRequest(
            api_key="test-key",
            repo_id="repo1",
            message="follow up",
            history=[
                ChatMessage(role="user", content="hello"),
                ChatMessage(role="assistant", content="hi"),
            ],
        )
        assert len(req.history) == 2

    def test_chat_message_roles(self):
        """ChatMessage only allows 'user' or 'assistant' roles."""
        msg_user = ChatMessage(role="user", content="test")
        assert msg_user.role == "user"

        msg_asst = ChatMessage(role="assistant", content="test")
        assert msg_asst.role == "assistant"

    def test_chat_response(self):
        """ChatResponse holds response and diagram info."""
        resp = ChatResponse(response="test answer", has_diagram=True, diagram="graph TD")
        assert resp.response == "test answer"
        assert resp.has_diagram is True
        assert resp.diagram == "graph TD"

    def test_chat_response_defaults(self):
        """ChatResponse defaults."""
        resp = ChatResponse(response="test")
        assert resp.has_diagram is False
        assert resp.diagram is None


class TestStreamSchemas:
    """Tests for WebSocket streaming schemas."""

    def test_stream_message_types(self):
        """StreamMessage accepts valid types."""
        for msg_type in ["start", "chunk", "end", "error"]:
            msg = StreamMessage(type=msg_type)
            assert msg.type == msg_type

    def test_stream_message_with_content(self):
        """StreamMessage can include content and metadata."""
        msg = StreamMessage(type="chunk", content="test data", metadata={"key": "value"})
        assert msg.content == "test data"
        assert msg.metadata == {"key": "value"}

    def test_stream_message_optional_fields(self):
        """StreamMessage content and metadata are optional."""
        msg = StreamMessage(type="start")
        assert msg.content is None
        assert msg.metadata is None
