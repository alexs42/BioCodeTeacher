"""Tests for persistent storage service."""

import json
import tempfile
from pathlib import Path

import pytest

from models.schemas import ArchitectureContextSummary, ComponentInfo
from services.persistent_store import PersistentStore, _path_hash, _file_hash


@pytest.fixture
def tmp_store(tmp_path):
    """Create a PersistentStore using a temp directory."""
    return PersistentStore(base_dir=tmp_path)


@pytest.fixture
def sample_summary():
    """Create a sample architecture summary."""
    return ArchitectureContextSummary(
        repo_id="test-repo",
        overview="A test project",
        components=[
            ComponentInfo(path="main.py", role="Entry point", dependencies=["utils.py"]),
            ComponentInfo(path="utils.py", role="Utilities", dependencies=[]),
        ],
        patterns=["MVC"],
        context_block="This is a test project with main.py and utils.py.",
        timestamp="2026-03-28T10:00:00+00:00",
    )


class TestPathHashing:
    def test_same_path_same_hash(self):
        assert _path_hash("/home/user/project") == _path_hash("/home/user/project")

    def test_different_paths_different_hashes(self):
        assert _path_hash("/home/user/project") != _path_hash("/home/user/other")

    def test_hash_is_12_chars(self):
        assert len(_path_hash("/some/path")) == 12

    def test_file_hash_consistent(self):
        assert _file_hash("src/main.py") == _file_hash("src/main.py")


class TestRepoRegistration:
    def test_register_creates_dirs(self, tmp_store):
        tmp_store.register_repo("abc", "/home/user/myproject")
        repo_dir = tmp_store.base_dir / "repos" / _path_hash("/home/user/myproject")
        assert repo_dir.exists()
        assert (repo_dir / "file_summaries").exists()
        assert (repo_dir / "meta.json").exists()

    def test_register_stores_mapping(self, tmp_store):
        tmp_store.register_repo("abc", "/home/user/myproject")
        assert tmp_store.get_repo_path("abc") == "/home/user/myproject"

    def test_meta_contains_repo_info(self, tmp_store):
        tmp_store.register_repo("abc", "/home/user/myproject")
        repo_dir = tmp_store.base_dir / "repos" / _path_hash("/home/user/myproject")
        meta = json.loads((repo_dir / "meta.json").read_text())
        assert meta["repo_path"] == "/home/user/myproject"
        assert meta["name"] == "myproject"
        assert "last_loaded" in meta

    def test_get_repo_path_unknown(self, tmp_store):
        assert tmp_store.get_repo_path("nonexistent") is None


class TestArchitecturePersistence:
    def test_save_and_load(self, tmp_store, sample_summary):
        repo_path = "/home/user/project"
        tmp_store.save_architecture(repo_path, sample_summary, "# Overview\nHello")

        result = tmp_store.load_architecture(repo_path)
        assert result is not None
        loaded_summary, display_md = result
        assert loaded_summary.overview == "A test project"
        assert len(loaded_summary.components) == 2
        assert loaded_summary.components[0].path == "main.py"
        assert display_md == "# Overview\nHello"

    def test_has_architecture_true(self, tmp_store, sample_summary):
        repo_path = "/home/user/project"
        tmp_store.save_architecture(repo_path, sample_summary, "md")
        assert tmp_store.has_architecture(repo_path) is True

    def test_has_architecture_false(self, tmp_store):
        assert tmp_store.has_architecture("/nonexistent") is False

    def test_load_nonexistent_returns_none(self, tmp_store):
        assert tmp_store.load_architecture("/nonexistent") is None

    def test_overwrite_preserves_latest(self, tmp_store, sample_summary):
        repo_path = "/home/user/project"
        tmp_store.save_architecture(repo_path, sample_summary, "v1")

        sample_summary.overview = "Updated"
        tmp_store.save_architecture(repo_path, sample_summary, "v2")

        result = tmp_store.load_architecture(repo_path)
        assert result is not None
        assert result[0].overview == "Updated"
        assert result[1] == "v2"


class TestFileSummaryPersistence:
    def test_save_and_load(self, tmp_store):
        repo_path = "/home/user/project"
        summary = {"purpose": "Entry point", "role": "Main module"}
        tmp_store.save_file_summary(repo_path, "main.py", summary)

        loaded = tmp_store.load_file_summary(repo_path, "main.py")
        assert loaded is not None
        assert loaded["purpose"] == "Entry point"

    def test_load_nonexistent_returns_none(self, tmp_store):
        assert tmp_store.load_file_summary("/project", "missing.py") is None

    def test_different_files_independent(self, tmp_store):
        repo_path = "/home/user/project"
        tmp_store.save_file_summary(repo_path, "a.py", {"role": "A"})
        tmp_store.save_file_summary(repo_path, "b.py", {"role": "B"})

        assert tmp_store.load_file_summary(repo_path, "a.py")["role"] == "A"
        assert tmp_store.load_file_summary(repo_path, "b.py")["role"] == "B"
