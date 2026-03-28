"""
Tests for backend services (repo_manager, code_parser, explanation_cache, architecture_store).
"""

import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.repo_manager import RepoManager
from services.code_parser import CodeParser, code_parser
from services.explanation_cache import ExplanationCache
from services.architecture_store import ArchitectureStore
from models.schemas import ArchitectureContextSummary, ComponentInfo


class TestRepoManager:
    """Tests for RepoManager service."""

    def test_detect_language_python(self, repo_manager: RepoManager):
        """Test Python language detection."""
        assert repo_manager.detect_language("test.py") == "python"
        assert repo_manager.detect_language("path/to/file.py") == "python"

    def test_detect_language_javascript(self, repo_manager: RepoManager):
        """Test JavaScript language detection."""
        assert repo_manager.detect_language("test.js") == "javascript"
        assert repo_manager.detect_language("test.jsx") == "javascript"

    def test_detect_language_typescript(self, repo_manager: RepoManager):
        """Test TypeScript language detection."""
        assert repo_manager.detect_language("test.ts") == "typescript"
        assert repo_manager.detect_language("test.tsx") == "typescript"

    def test_detect_language_other(self, repo_manager: RepoManager):
        """Test other language detection."""
        assert repo_manager.detect_language("test.go") == "go"
        assert repo_manager.detect_language("test.rs") == "rust"
        assert repo_manager.detect_language("test.java") == "java"
        assert repo_manager.detect_language("test.rb") == "ruby"

    def test_detect_language_unknown(self, repo_manager: RepoManager):
        """Test unknown file extension."""
        assert repo_manager.detect_language("test.xyz") == "plaintext"
        assert repo_manager.detect_language("noextension") == "plaintext"

    def test_detect_language_dockerfile(self, repo_manager: RepoManager):
        """Test Dockerfile detection."""
        assert repo_manager.detect_language("Dockerfile") == "dockerfile"

    @pytest.mark.asyncio
    async def test_load_local_success(self, repo_manager: RepoManager, temp_repo: str):
        """Test loading local repository."""
        result = await repo_manager.load_local(temp_repo)

        assert "repo_id" in result
        assert result["root_path"] == temp_repo
        assert result["file_tree"] is not None
        assert result["file_count"] > 0

    @pytest.mark.asyncio
    async def test_load_local_not_exists(self, repo_manager: RepoManager):
        """Test loading non-existent path."""
        with pytest.raises(ValueError) as exc_info:
            await repo_manager.load_local("/nonexistent/path")
        assert "not exist" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_read_file(self, repo_manager: RepoManager, temp_repo: str):
        """Test reading file content."""
        await repo_manager.load_local(temp_repo)
        # Get the repo_id from the internal storage
        repo_id = list(repo_manager._repos.keys())[0]

        result = await repo_manager.read_file(repo_id, "main.py")

        assert result["path"] == "main.py"
        assert result["language"] == "python"
        assert "def hello" in result["content"]
        assert result["line_count"] > 0

    @pytest.mark.asyncio
    async def test_read_file_not_found(self, repo_manager: RepoManager, temp_repo: str):
        """Test reading non-existent file."""
        await repo_manager.load_local(temp_repo)
        repo_id = list(repo_manager._repos.keys())[0]

        with pytest.raises(ValueError) as exc_info:
            await repo_manager.read_file(repo_id, "nonexistent.py")
        assert "not found" in str(exc_info.value).lower()


class TestCodeParser:
    """Tests for CodeParser service."""

    def test_get_line_with_context(self, sample_python_code: str):
        """Test extracting line with context."""
        before, line, after = code_parser.get_line_with_context(
            sample_python_code, 2, context_lines=1
        )

        assert "Calculate the total" in line
        assert "def calculate_total" in before
        assert "subtotal" in after

    def test_get_line_with_context_first_line(self, sample_python_code: str):
        """Test extracting first line."""
        before, line, after = code_parser.get_line_with_context(
            sample_python_code, 1, context_lines=2
        )

        assert before == ""  # No lines before
        assert "def calculate_total" in line
        assert len(after) > 0

    def test_get_line_with_context_last_line(self, sample_python_code: str):
        """Test extracting last line."""
        lines = sample_python_code.splitlines()
        last_line_num = len(lines)

        before, line, after = code_parser.get_line_with_context(
            sample_python_code, last_line_num, context_lines=2
        )

        assert len(before) > 0
        assert after == ""  # No lines after

    def test_get_line_with_context_invalid_line(self, sample_python_code: str):
        """Test invalid line number."""
        with pytest.raises(ValueError) as exc_info:
            code_parser.get_line_with_context(sample_python_code, 100, context_lines=2)
        assert "out of range" in str(exc_info.value).lower()

    def test_get_line_range(self, sample_python_code: str):
        """Test extracting line range."""
        result = code_parser.get_line_range(sample_python_code, 1, 2)

        assert "1:" in result  # Line numbers included
        assert "2:" in result
        assert "def calculate_total" in result

    def test_get_line_range_single_line(self, sample_python_code: str):
        """Test extracting single line as range."""
        result = code_parser.get_line_range(sample_python_code, 1, 1)

        assert "1:" in result
        assert "def calculate_total" in result

    def test_find_function_bounds_python(self, sample_python_code: str):
        """Test finding function bounds in Python."""
        start, end = code_parser.find_function_bounds(
            sample_python_code, 2, "python"
        )

        assert start == 1  # Function starts at line 1
        assert end >= 3  # Function spans multiple lines


class TestExplanationCache:
    """Tests for ExplanationCache service."""

    def test_cache_set_and_get(self):
        """Test setting and getting cache entries."""
        cache = ExplanationCache()

        cache.set("test.py", "content", 1, "explanation")
        result = cache.get("test.py", "content", 1)

        assert result == "explanation"

    def test_cache_miss(self):
        """Test cache miss returns None."""
        cache = ExplanationCache()

        result = cache.get("test.py", "content", 1)
        assert result is None

    def test_cache_content_change_invalidates(self):
        """Test that changing content invalidates cache."""
        cache = ExplanationCache()

        cache.set("test.py", "original content", 1, "explanation")
        result = cache.get("test.py", "modified content", 1)

        assert result is None  # Different content = cache miss

    def test_cache_different_lines(self):
        """Test cache stores different lines separately."""
        cache = ExplanationCache()

        cache.set("test.py", "content", 1, "explanation for line 1")
        cache.set("test.py", "content", 2, "explanation for line 2")

        assert cache.get("test.py", "content", 1) == "explanation for line 1"
        assert cache.get("test.py", "content", 2) == "explanation for line 2"

    def test_cache_clear(self):
        """Test clearing the cache."""
        cache = ExplanationCache()

        cache.set("test.py", "content", 1, "explanation")
        cache.clear()
        result = cache.get("test.py", "content", 1)

        assert result is None

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = ExplanationCache(max_size=100, ttl_minutes=30)

        stats = cache.stats()

        assert stats["entries"] == 0
        assert stats["max_size"] == 100
        assert stats["ttl_minutes"] == 30

        cache.set("test.py", "content", 1, "explanation")
        stats = cache.stats()

        assert stats["entries"] == 1

    def test_cache_size_limit(self):
        """Test cache enforces size limit."""
        cache = ExplanationCache(max_size=2)

        cache.set("test1.py", "c1", 1, "exp1")
        cache.set("test2.py", "c2", 1, "exp2")
        cache.set("test3.py", "c3", 1, "exp3")  # Should evict oldest

        stats = cache.stats()
        assert stats["entries"] <= 2

    def test_cache_architecture(self):
        """Test architecture cache methods."""
        cache = ExplanationCache()

        cache.set_architecture("repo1", "hash1", "arch analysis")
        result = cache.get_architecture("repo1", "hash1")

        assert result == "arch analysis"

    def test_cache_architecture_miss(self):
        """Test architecture cache miss."""
        cache = ExplanationCache()

        result = cache.get_architecture("repo1", "hash1")
        assert result is None


class TestArchitectureStore:
    """Tests for ArchitectureStore file-specific context."""

    def _make_summary(self, repo_id="repo1"):
        """Create a test ArchitectureContextSummary."""
        return ArchitectureContextSummary(
            repo_id=repo_id,
            overview="Test project overview",
            components=[
                ComponentInfo(
                    path="routers/explain.py",
                    role="API router for code explanations",
                    dependencies=["services/openrouter.py", "services/code_parser.py"],
                ),
                ComponentInfo(
                    path="services/openrouter.py",
                    role="LLM API client via OpenRouter",
                    dependencies=[],
                ),
                ComponentInfo(
                    path="services/code_parser.py",
                    role="Code context extraction and import parsing",
                    dependencies=[],
                ),
                ComponentInfo(
                    path="main.py",
                    role="FastAPI application entry point",
                    dependencies=["routers/explain.py", "routers/repos.py"],
                ),
            ],
            patterns=["Layered architecture", "Router-Service pattern"],
            context_block="CodeTeacher is a FastAPI app with routers and services.",
            timestamp="2026-03-27T12:00:00",
        )

    def test_no_analysis_returns_none(self):
        """get_file_context returns None when no analysis exists."""
        store = ArchitectureStore()
        assert store.get_file_context("repo1", "some/file.py") is None

    def test_indexed_file_returns_targeted_context(self):
        """File in the component index gets targeted context with role and deps."""
        store = ArchitectureStore()
        summary = self._make_summary()
        store.save("repo1", summary)

        result = store.get_file_context("repo1", "routers/explain.py")
        assert result is not None
        assert "API router for code explanations" in result
        assert "services/openrouter.py" in result
        assert "services/code_parser.py" in result
        assert "Layered architecture" in result

    def test_indexed_file_shows_reverse_deps(self):
        """File in the index shows who imports it."""
        store = ArchitectureStore()
        store.save("repo1", self._make_summary())

        result = store.get_file_context("repo1", "services/openrouter.py")
        assert result is not None
        assert "Imported by" in result
        assert "routers/explain.py" in result

    def test_path_normalization(self):
        """Paths with different extensions/separators match correctly."""
        store = ArchitectureStore()
        store.save("repo1", self._make_summary())

        # With extension
        assert store.get_file_context("repo1", "routers/explain.py") is not None
        # Backslashes (Windows)
        assert store.get_file_context("repo1", "routers\\explain.py") is not None

    def test_crossref_file_with_matching_imports(self):
        """File not in index but importing known components gets lightweight context."""
        store = ArchitectureStore()
        store.save("repo1", self._make_summary())

        python_content = "from services.openrouter import OpenRouterService\nimport json\n"
        result = store.get_file_context(
            "repo1", "routers/chat.py",
            file_content=python_content, language="python"
        )
        assert result is not None
        assert "openrouter" in result.lower()

    def test_crossref_no_matching_imports_returns_none(self):
        """File not in index with no matching imports returns None."""
        store = ArchitectureStore()
        store.save("repo1", self._make_summary())

        python_content = "import os\nimport json\n"
        result = store.get_file_context(
            "repo1", "utils/helpers.py",
            file_content=python_content, language="python"
        )
        assert result is None

    def test_index_invalidated_on_save(self):
        """Saving new analysis invalidates the cached file index."""
        store = ArchitectureStore()
        store.save("repo1", self._make_summary())

        # Access to populate cache
        store.get_file_context("repo1", "routers/explain.py")
        assert "repo1" in store._file_indexes

        # Save new analysis
        store.save("repo1", self._make_summary())
        assert "repo1" not in store._file_indexes
