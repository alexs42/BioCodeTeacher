"""
Tests for the OpenRouter service - model configuration, reasoning support, and API interactions.
"""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.openrouter import (
    OpenRouterService,
    DEFAULT_MODEL,
    REASONING_MODELS,
    OPENROUTER_API_URL,
    LINE_EXPLAIN_SYSTEM,
    LINE_EXPLAIN_TEMPLATE,
    ARCHITECTURE_SYSTEM,
    ARCHITECTURE_TEMPLATE,
    CHAT_SYSTEM,
)


class TestOpenRouterServiceConfig:
    """Tests for OpenRouterService initialization and configuration."""

    def test_default_model_is_opus_46(self):
        """Default model should be Claude Opus 4.6."""
        assert DEFAULT_MODEL == "anthropic/claude-opus-4.6"

    def test_reasoning_models_set(self):
        """REASONING_MODELS should contain GPT-5.4 and Gemini 3.1 Pro."""
        assert "openai/gpt-5.4" in REASONING_MODELS
        assert "google/gemini-3.1-pro-preview" in REASONING_MODELS
        assert len(REASONING_MODELS) == 2

    def test_init_with_defaults(self):
        """Service initializes with default model and no reasoning."""
        service = OpenRouterService("test-key")
        assert service.model == DEFAULT_MODEL
        assert service.api_key == "test-key"
        assert service.reasoning_effort is None

    def test_init_with_custom_model(self):
        """Service accepts custom model."""
        service = OpenRouterService("test-key", model="openai/gpt-5.4")
        assert service.model == "openai/gpt-5.4"

    def test_init_with_reasoning_effort(self):
        """Service stores reasoning effort."""
        service = OpenRouterService("test-key", model="openai/gpt-5.4", reasoning_effort="medium")
        assert service.reasoning_effort == "medium"

    def test_headers_include_auth(self):
        """Headers should include Authorization with bearer token."""
        service = OpenRouterService("sk-test-123")
        assert service.headers["Authorization"] == "Bearer sk-test-123"
        assert service.headers["Content-Type"] == "application/json"
        assert service.headers["X-Title"] == "CodeTeacher"
        assert "HTTP-Referer" in service.headers

    def test_api_url_constant(self):
        """API URL should point to OpenRouter."""
        assert OPENROUTER_API_URL == "https://openrouter.ai/api/v1/chat/completions"


class TestOpenRouterPayloadConstruction:
    """Tests for payload construction including reasoning effort."""

    @pytest.mark.asyncio
    async def test_complete_payload_without_reasoning(self):
        """complete() should not include reasoning for non-reasoning models."""
        service = OpenRouterService("test-key", model="anthropic/claude-opus-4.6")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "test response"}}]
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            await service.complete("test prompt")

            call_kwargs = mock_client.post.call_args
            payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
            assert "reasoning" not in payload
            assert payload["model"] == "anthropic/claude-opus-4.6"

    @pytest.mark.asyncio
    async def test_complete_payload_with_reasoning_for_gpt54(self):
        """complete() should include reasoning for GPT-5.4 when effort is set."""
        service = OpenRouterService("test-key", model="openai/gpt-5.4", reasoning_effort="medium")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "test response"}}]
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            await service.complete("test prompt")

            call_kwargs = mock_client.post.call_args
            payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
            assert "reasoning" in payload
            assert payload["reasoning"] == {"effort": "medium"}

    @pytest.mark.asyncio
    async def test_complete_payload_no_reasoning_for_non_reasoning_model_even_with_effort(self):
        """complete() should NOT add reasoning for non-reasoning model even if effort is set."""
        service = OpenRouterService("test-key", model="anthropic/claude-opus-4.6", reasoning_effort="medium")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "test response"}}]
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            await service.complete("test prompt")

            call_kwargs = mock_client.post.call_args
            payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
            assert "reasoning" not in payload

    @pytest.mark.asyncio
    async def test_complete_payload_no_reasoning_when_effort_is_none(self):
        """complete() should NOT add reasoning when effort is None (even for reasoning models)."""
        service = OpenRouterService("test-key", model="openai/gpt-5.4", reasoning_effort=None)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "test response"}}]
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            await service.complete("test prompt")

            call_kwargs = mock_client.post.call_args
            payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
            assert "reasoning" not in payload

    @pytest.mark.asyncio
    async def test_complete_includes_system_prompt(self):
        """complete() should include system prompt in messages when provided."""
        service = OpenRouterService("test-key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "test response"}}]
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            await service.complete("user prompt", system_prompt="system prompt")

            call_kwargs = mock_client.post.call_args
            payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
            messages = payload["messages"]
            assert len(messages) == 2
            assert messages[0]["role"] == "system"
            assert messages[0]["content"] == "system prompt"
            assert messages[1]["role"] == "user"
            assert messages[1]["content"] == "user prompt"

    @pytest.mark.asyncio
    async def test_complete_without_system_prompt(self):
        """complete() should not include system message when no system prompt."""
        service = OpenRouterService("test-key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "test response"}}]
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            await service.complete("user prompt")

            call_kwargs = mock_client.post.call_args
            payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
            messages = payload["messages"]
            assert len(messages) == 1
            assert messages[0]["role"] == "user"

    @pytest.mark.asyncio
    async def test_complete_api_error_raises(self):
        """complete() should raise on API errors."""
        service = OpenRouterService("test-key")

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            with pytest.raises(Exception, match="OpenRouter API error"):
                await service.complete("test")

    @pytest.mark.asyncio
    async def test_complete_max_tokens_and_temperature(self):
        """complete() should pass max_tokens and temperature."""
        service = OpenRouterService("test-key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "test"}}]
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            await service.complete("test", max_tokens=8000, temperature=0.3)

            call_kwargs = mock_client.post.call_args
            payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
            assert payload["max_tokens"] == 8000
            assert payload["temperature"] == 0.3
            assert payload["stream"] is False


class TestPromptTemplates:
    """Tests for prompt templates."""

    def test_line_explain_system_prompt_exists(self):
        """LINE_EXPLAIN_SYSTEM should be a non-empty string."""
        assert isinstance(LINE_EXPLAIN_SYSTEM, str)
        assert len(LINE_EXPLAIN_SYSTEM) > 0
        assert "CodeTeacher" in LINE_EXPLAIN_SYSTEM

    def test_line_explain_template_has_placeholders(self):
        """LINE_EXPLAIN_TEMPLATE should have the required placeholders."""
        assert "{filename}" in LINE_EXPLAIN_TEMPLATE
        assert "{language}" in LINE_EXPLAIN_TEMPLATE
        assert "{line_number}" in LINE_EXPLAIN_TEMPLATE
        assert "{line_code}" in LINE_EXPLAIN_TEMPLATE
        assert "{context_before}" in LINE_EXPLAIN_TEMPLATE
        assert "{context_after}" in LINE_EXPLAIN_TEMPLATE

    def test_line_explain_template_can_be_formatted(self):
        """LINE_EXPLAIN_TEMPLATE should be formattable with expected params."""
        result = LINE_EXPLAIN_TEMPLATE.format(
            filename="test.py",
            language="python",
            line_number=5,
            line_code="x = 1",
            context_before="# before",
            context_after="# after",
        )
        assert "test.py" in result
        assert "python" in result
        assert "x = 1" in result

    def test_architecture_system_prompt_exists(self):
        """ARCHITECTURE_SYSTEM should be a non-empty string."""
        assert isinstance(ARCHITECTURE_SYSTEM, str)
        assert "CodeTeacher" in ARCHITECTURE_SYSTEM

    def test_architecture_template_has_placeholders(self):
        """ARCHITECTURE_TEMPLATE should have file_tree and key_files_content."""
        assert "{file_tree}" in ARCHITECTURE_TEMPLATE
        assert "{key_files_content}" in ARCHITECTURE_TEMPLATE

    def test_chat_system_prompt_exists(self):
        """CHAT_SYSTEM should be a non-empty string."""
        assert isinstance(CHAT_SYSTEM, str)
        assert "CodeTeacher" in CHAT_SYSTEM
