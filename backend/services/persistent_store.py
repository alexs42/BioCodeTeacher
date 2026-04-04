"""
Cross-platform disk persistence for repo-specific analysis data.

Storage locations:
  Windows: C:\\BioCodeTeacher\\
  Linux/Mac: ~/.biocodeteacher/

Per-repo directory keyed by SHA-256 hash of the resolved repo path.
"""

import hashlib
import json
import os
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

from models.schemas import ArchitectureContextSummary


def _default_base_dir() -> Path:
    """Platform-specific default storage directory."""
    if platform.system() == "Windows":
        return Path("C:/BioCodeTeacher")
    return Path.home() / ".biocodeteacher"


def _path_hash(repo_path: str) -> str:
    """Stable hash from the resolved absolute repo path (first 12 hex chars)."""
    resolved = str(Path(repo_path).resolve())
    return hashlib.sha256(resolved.encode("utf-8")).hexdigest()[:12]


def _file_hash(file_path: str) -> str:
    """Hash a relative file path for summary storage."""
    return hashlib.sha256(file_path.encode("utf-8")).hexdigest()[:12]


def _atomic_write(path: Path, data: str) -> None:
    """Write data atomically: write to .tmp then os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp.write_text(data, encoding="utf-8")
        os.replace(str(tmp), str(path))
    except OSError:
        # Retry once (handles Dropbox / antivirus file locks on Windows)
        try:
            import time
            time.sleep(0.1)
            os.replace(str(tmp), str(path))
        except OSError:
            # Clean up tmp, let the original error propagate
            tmp.unlink(missing_ok=True)
            raise


class PersistentStore:
    """Disk-based persistence for architecture analysis and file summaries."""

    def __init__(self, base_dir: Optional[Path] = None):
        self._base_dir = base_dir or _default_base_dir()
        self._repo_id_to_path: dict[str, str] = {}  # session repo_id -> repo_path

    @property
    def base_dir(self) -> Path:
        return self._base_dir

    def _repo_dir(self, repo_path: str) -> Path:
        """Get the storage directory for a specific repo."""
        return self._base_dir / "repos" / _path_hash(repo_path)

    def register_repo(self, repo_id: str, repo_path: str) -> None:
        """Map a session repo_id to a repo_path and ensure storage dirs exist."""
        self._repo_id_to_path[repo_id] = repo_path
        repo_dir = self._repo_dir(repo_path)
        repo_dir.mkdir(parents=True, exist_ok=True)
        (repo_dir / "file_summaries").mkdir(exist_ok=True)

        # Save/update meta
        meta = {
            "repo_path": repo_path,
            "name": Path(repo_path).name,
            "last_loaded": datetime.now(timezone.utc).isoformat(),
        }
        _atomic_write(repo_dir / "meta.json", json.dumps(meta, indent=2))

    def get_repo_path(self, repo_id: str) -> Optional[str]:
        """Get the repo_path for a session repo_id."""
        return self._repo_id_to_path.get(repo_id)

    # --- Architecture persistence ---

    def save_architecture(
        self, repo_path: str, summary: ArchitectureContextSummary,
        display_md: str,
    ) -> None:
        """Persist architecture analysis to disk."""
        repo_dir = self._repo_dir(repo_path)
        repo_dir.mkdir(parents=True, exist_ok=True)

        _atomic_write(
            repo_dir / "architecture.json",
            summary.model_dump_json(indent=2),
        )
        _atomic_write(repo_dir / "architecture_display.md", display_md)

    def load_architecture(
        self, repo_path: str,
    ) -> Optional[Tuple[ArchitectureContextSummary, str]]:
        """Load cached architecture analysis from disk. Returns (summary, display_md) or None."""
        repo_dir = self._repo_dir(repo_path)
        arch_json = repo_dir / "architecture.json"
        arch_md = repo_dir / "architecture_display.md"

        if not arch_json.exists():
            return None

        try:
            summary = ArchitectureContextSummary.model_validate_json(
                arch_json.read_text(encoding="utf-8")
            )
            display_md = arch_md.read_text(encoding="utf-8") if arch_md.exists() else ""
            return summary, display_md
        except Exception:
            return None

    def has_architecture(self, repo_path: str) -> bool:
        """Quick check: does cached architecture exist for this repo path?"""
        return (self._repo_dir(repo_path) / "architecture.json").exists()

    # --- File summary persistence ---

    def save_file_summary(self, repo_path: str, file_path: str, summary: dict) -> None:
        """Persist a file summary to disk."""
        repo_dir = self._repo_dir(repo_path)
        summaries_dir = repo_dir / "file_summaries"
        summaries_dir.mkdir(parents=True, exist_ok=True)
        _atomic_write(
            summaries_dir / f"{_file_hash(file_path)}.json",
            json.dumps(summary, indent=2),
        )

    def load_file_summary(self, repo_path: str, file_path: str) -> Optional[dict]:
        """Load a cached file summary from disk."""
        path = self._repo_dir(repo_path) / "file_summaries" / f"{_file_hash(file_path)}.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    # --- Documentation cache (global, not per-repo) ---

    def _doc_cache_dir(self) -> Path:
        d = self._base_dir / "doc_cache"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save_doc_cache(self, cache_key: str, content: dict) -> None:
        """Persist a documentation snippet to disk."""
        _atomic_write(
            self._doc_cache_dir() / f"{cache_key}.json",
            json.dumps(content, indent=2),
        )

    def load_doc_cache(self, cache_key: str) -> Optional[dict]:
        """Load a cached documentation snippet from disk."""
        path = self._doc_cache_dir() / f"{cache_key}.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None


# Global singleton
persistent_store = PersistentStore()
