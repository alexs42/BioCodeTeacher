"""
In-memory store for architecture analysis results.
Persists per repo_id so context can enrich subsequent explanations.
Optionally writes through to disk via PersistentStore.
"""

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

from models.schemas import ArchitectureContextSummary
from services.code_parser import code_parser

if TYPE_CHECKING:
    from services.persistent_store import PersistentStore


class ArchitectureStore:
    """Stores architecture analysis results per repository."""

    def __init__(self, persistent: Optional["PersistentStore"] = None):
        self._store: Dict[str, ArchitectureContextSummary] = {}
        self._display_md: Dict[str, str] = {}  # repo_id -> rendered markdown
        self._file_indexes: Dict[str, dict] = {}
        self._persistent = persistent

    def save(self, repo_id: str, summary: ArchitectureContextSummary,
             display_md: Optional[str] = None) -> None:
        """Save or overwrite architecture analysis for a repo."""
        self._store[repo_id] = summary
        if display_md is not None:
            self._display_md[repo_id] = display_md
        self._file_indexes.pop(repo_id, None)  # invalidate cached index

        # Write through to disk
        if self._persistent:
            repo_path = self._persistent.get_repo_path(repo_id)
            if repo_path:
                self._persistent.save_architecture(
                    repo_path, summary,
                    display_md or self._display_md.get(repo_id, ""),
                )

    def load_from_disk(self, repo_id: str, repo_path: str) -> bool:
        """Hydrate in-memory store from disk cache. Returns True if found."""
        if not self._persistent:
            return False
        result = self._persistent.load_architecture(repo_path)
        if result is None:
            return False
        summary, display_md = result
        # Update repo_id to match current session
        summary.repo_id = repo_id
        self._store[repo_id] = summary
        self._display_md[repo_id] = display_md
        self._file_indexes.pop(repo_id, None)
        return True

    def get_display_md(self, repo_id: str) -> Optional[str]:
        """Get the rendered markdown overview for display."""
        return self._display_md.get(repo_id)

    def get(self, repo_id: str) -> Optional[ArchitectureContextSummary]:
        """Get the full architecture summary for a repo."""
        return self._store.get(repo_id)

    def get_context_block(self, repo_id: str) -> Optional[str]:
        """Get the condensed context block for prompt injection."""
        summary = self._store.get(repo_id)
        return summary.context_block if summary else None

    def get_file_context(self, repo_id: str, file_path: str,
                         file_content: Optional[str] = None,
                         language: Optional[str] = None) -> Optional[str]:
        """Get file-specific architecture context for prompt injection.

        Returns targeted context if the file is in the component index,
        lightweight cross-referenced context if imports match known components,
        or None if no architecture analysis exists.
        """
        summary = self._store.get(repo_id)
        if not summary:
            return None

        index = self._get_file_index(repo_id, summary)
        norm_path = self._normalize_path(file_path)

        # Direct match: file is in the component index
        if norm_path in index:
            return self._format_indexed_context(index[norm_path], summary)

        # Lightweight: cross-reference file's imports with known components
        if file_content and language:
            return self._format_crossref_context(
                file_path, file_content, language, index, summary
            )

        # Fall back to generic context block
        return None

    def has_analysis(self, repo_id: str) -> bool:
        """Check if analysis exists for a repo."""
        return repo_id in self._store

    def clear(self, repo_id: str) -> None:
        """Remove analysis for a repo."""
        self._store.pop(repo_id, None)
        self._file_indexes.pop(repo_id, None)

    def get_status(self, repo_id: str, repo_path: Optional[str] = None) -> dict:
        """Get status info for a repo's analysis, including staleness check."""
        summary = self._store.get(repo_id)
        if not summary:
            return {"has_analysis": False}

        result = {
            "has_analysis": True,
            "timestamp": summary.timestamp,
            "component_count": len(summary.components),
            "patterns": summary.patterns,
            "is_stale": False,
        }

        # Check if any analyzed files have been modified since the analysis
        if repo_path:
            try:
                analysis_time = datetime.fromisoformat(summary.timestamp)
                # Ensure UTC-aware for consistent comparison
                if analysis_time.tzinfo is None:
                    analysis_time = analysis_time.replace(tzinfo=timezone.utc)
                for comp in summary.components:
                    file_path = Path(repo_path) / comp.path
                    if file_path.exists():
                        mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
                        if mtime > analysis_time:
                            result["is_stale"] = True
                            break
            except (ValueError, OSError):
                pass  # If we can't check, assume not stale

        return result

    def get_file_context_data(self, repo_id: str, file_path: str) -> Optional[dict]:
        """Get structured file context data for frontend display.

        Returns dict with role, imports, importers, patterns — or None.
        """
        summary = self._store.get(repo_id)
        if not summary:
            return None

        index = self._get_file_index(repo_id, summary)
        norm_path = self._normalize_path(file_path)

        if norm_path not in index:
            return None

        entry = index[norm_path]
        return {
            "file": entry["path"],
            "role": entry["role"],
            "imports": [
                {"path": d, "role": index.get(self._normalize_path(d), {}).get("role")}
                for d in entry["dependencies"]
            ],
            "imported_by": entry["imported_by"],
            "patterns": summary.patterns,
        }

    # --- Private helpers ---

    @staticmethod
    def _normalize_path(p: str) -> str:
        """Normalize path for fuzzy matching.

        Handles file paths (services/openrouter.py) and Python module
        paths (services.openrouter) by stripping extensions then
        converting dots to slashes.
        """
        p = p.replace("\\", "/").strip("/")
        for ext in (".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java",
                     ".kt", ".scala", ".rb", ".php", ".c", ".cpp", ".h"):
            if p.endswith(ext):
                p = p[:-len(ext)]
                break
        # Convert Python module dots to slashes: services.openrouter -> services/openrouter
        p = p.replace(".", "/")
        return p

    def _get_file_index(self, repo_id: str,
                        summary: ArchitectureContextSummary) -> dict:
        """Get or build the path-indexed component map with reverse deps."""
        if repo_id in self._file_indexes:
            return self._file_indexes[repo_id]

        index: Dict[str, dict] = {}
        # Forward index
        for comp in summary.components:
            norm = self._normalize_path(comp.path)
            index[norm] = {
                "path": comp.path,
                "role": comp.role,
                "dependencies": comp.dependencies,
                "imported_by": [],
            }
        # Reverse deps
        for comp in summary.components:
            for dep in comp.dependencies:
                dep_norm = self._normalize_path(dep)
                if dep_norm in index:
                    index[dep_norm]["imported_by"].append({
                        "path": comp.path,
                        "role": comp.role,
                    })

        self._file_indexes[repo_id] = index
        return index

    def _format_indexed_context(self, entry: dict,
                                summary: ArchitectureContextSummary) -> str:
        """Format targeted context for a file that's in the component index."""
        lines = [f"**This file** ({entry['path']}): {entry['role']}"]

        if entry["dependencies"]:
            dep_parts = []
            # Look up roles for dependencies when possible
            index = self._file_indexes.get(summary.repo_id, {})
            for dep in entry["dependencies"]:
                dep_norm = self._normalize_path(dep)
                if dep_norm in index:
                    dep_parts.append(f"{dep} ({index[dep_norm]['role']})")
                else:
                    dep_parts.append(dep)
            lines.append(f"**Imports from project**: {', '.join(dep_parts)}")

        if entry["imported_by"]:
            importer_parts = [
                f"{imp['path']} ({imp['role']})"
                for imp in entry["imported_by"]
            ]
            lines.append(f"**Imported by**: {', '.join(importer_parts)}")

        if summary.patterns:
            lines.append(
                f"**Architecture patterns**: {', '.join(summary.patterns)}"
            )

        return "\n".join(lines)

    def _format_crossref_context(
        self, file_path: str, file_content: str, language: str,
        index: dict, summary: ArchitectureContextSummary,
    ) -> Optional[str]:
        """Format lightweight context by cross-referencing imports."""
        imports = code_parser.extract_imports(file_content, language)
        if not imports:
            return None

        # Match imports against known components.
        # Python extract_imports returns base module only (e.g., "services" from
        # "from services.openrouter import ..."), so also match prefix.
        matched = []
        for imp in imports:
            imp_norm = self._normalize_path(imp)
            for idx_key, entry in index.items():
                if (imp_norm == idx_key
                        or idx_key.endswith("/" + imp_norm)
                        or idx_key.startswith(imp_norm + "/")):
                    matched.append(f"{entry['path']} ({entry['role']})")
                    break

        # Check if any known components import this file
        importers = []
        file_norm = self._normalize_path(file_path)
        for entry in index.values():
            for dep in entry["dependencies"]:
                dep_norm = self._normalize_path(dep)
                if dep_norm == file_norm or file_norm.endswith("/" + dep_norm):
                    importers.append(f"{entry['path']} ({entry['role']})")
                    break

        if not matched and not importers:
            return None

        lines = []
        if matched:
            lines.append(
                f"**This file imports from**: {', '.join(matched)}"
            )
        if importers:
            lines.append(f"**Imported by**: {', '.join(importers)}")
        if summary.patterns:
            lines.append(
                f"**Architecture patterns**: {', '.join(summary.patterns)}"
            )
        # Append condensed overview for broader context
        overview_words = summary.context_block.split()[:100]
        lines.append(
            f"**Project overview**: {' '.join(overview_words)}..."
        )
        return "\n".join(lines)


# Global instance — wired to persistent store for disk caching
def _create_store() -> ArchitectureStore:
    from services.persistent_store import persistent_store
    return ArchitectureStore(persistent=persistent_store)

architecture_store = _create_store()
