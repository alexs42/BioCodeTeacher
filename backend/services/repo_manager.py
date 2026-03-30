"""
Repository manager for handling local and GitHub repositories.
"""

import os
import uuid
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict
import pathspec
from git import Repo as GitRepo, InvalidGitRepositoryError

from models.schemas import FileNode


# Language detection by file extension
LANGUAGE_MAP = {
    # -- General programming languages --
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".r": "r",
    ".R": "r",
    # -- Web / markup / config --
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".less": "less",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".xml": "xml",
    ".md": "markdown",
    ".sql": "sql",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "bash",
    ".ps1": "powershell",
    ".dockerfile": "dockerfile",
    ".toml": "toml",
    ".ini": "ini",
    ".cfg": "ini",
    ".vue": "vue",
    ".svelte": "svelte",
    # -- Bioinformatics sequence / genomic formats --
    ".fasta": "fasta",
    ".fa": "fasta",
    ".fna": "fasta",
    ".faa": "fasta",
    ".fastq": "fastq",
    ".fq": "fastq",
    ".vcf": "vcf",
    ".gff": "gff",
    ".gff3": "gff",
    ".gtf": "gtf",
    ".sam": "sam",
    ".bed": "bed",
    ".bedgraph": "bed",
    ".wig": "wig",
    ".bigwig": "wig",
    ".maf": "maf",
    # -- Single-cell / spatial data containers --
    ".h5ad": "python",     # AnnData (HDF5-backed)
    ".h5": "hdf5",         # Generic HDF5
    ".hdf5": "hdf5",
    ".loom": "python",     # Loom format
    ".rds": "r",           # R serialized objects (Seurat, SCE)
    ".rda": "r",           # R data archive
    ".mtx": "plaintext",   # Market Exchange (sparse matrix, 10X)
    # -- Workflow languages --
    ".smk": "python",      # Snakemake rules (Python superset)
    ".nf": "groovy",       # Nextflow (Groovy-based)
    ".cwl": "yaml",        # CWL workflows (YAML-based)
    ".wdl": "wdl",         # WDL workflows
    # -- Notebook / literate programming --
    ".ipynb": "json",      # Jupyter notebooks (JSON format)
    ".Rmd": "markdown",    # R Markdown
    ".rmd": "markdown",
    ".qmd": "markdown",    # Quarto documents
    # -- Pathology / imaging --
    ".svs": "plaintext",   # Aperio whole-slide images
    ".ndpi": "plaintext",  # Hamamatsu WSI
    ".tif": "plaintext",   # TIFF (microscopy)
    ".tiff": "plaintext",
}

# Directories to always skip
SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".env",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "target",
    ".idea",
    ".vscode",
    ".vs",
    "coverage",
    ".pytest_cache",
    ".mypy_cache",
    "*.egg-info",
}


class RepoManager:
    """
    Manages loaded repositories, providing file tree and content access.
    """

    def __init__(self):
        # Store loaded repos: repo_id -> repo info
        self._repos: Dict[str, dict] = {}

    def detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext = Path(file_path).suffix.lower()

        # Handle Dockerfile specially
        if Path(file_path).name.lower() == "dockerfile":
            return "dockerfile"

        return LANGUAGE_MAP.get(ext, "plaintext")

    def _load_gitignore(self, repo_path: Path) -> Optional[pathspec.PathSpec]:
        """Load .gitignore patterns if present."""
        gitignore_path = repo_path / ".gitignore"
        if gitignore_path.exists():
            with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
                patterns = f.read().splitlines()
            return pathspec.PathSpec.from_lines("gitwildmatch", patterns)
        return None

    def _should_skip(self, path: Path, gitignore: Optional[pathspec.PathSpec], repo_root: Path) -> bool:
        """Check if path should be skipped."""
        name = path.name

        # Skip hidden files/dirs (except .gitignore, etc.)
        if name.startswith(".") and name not in {".gitignore", ".env.example"}:
            return True

        # Skip known directories
        if path.is_dir() and name in SKIP_DIRS:
            return True

        # Check gitignore
        if gitignore:
            relative = path.relative_to(repo_root)
            if gitignore.match_file(str(relative)):
                return True

        return False

    def _build_file_tree(
        self,
        directory: Path,
        repo_root: Path,
        gitignore: Optional[pathspec.PathSpec],
        max_depth: int = 10,
        current_depth: int = 0,
    ) -> tuple[FileNode, int]:
        """
        Recursively build file tree structure.

        Returns:
            Tuple of (FileNode, file_count)
        """
        if current_depth > max_depth:
            return None, 0

        file_count = 0
        children = []

        try:
            entries = sorted(directory.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
        except PermissionError:
            entries = []

        for entry in entries:
            if self._should_skip(entry, gitignore, repo_root):
                continue

            if entry.is_dir():
                child_node, child_count = self._build_file_tree(
                    entry, repo_root, gitignore, max_depth, current_depth + 1
                )
                if child_node and (child_node.children or child_count > 0):
                    children.append(child_node)
                    file_count += child_count
            else:
                language = self.detect_language(str(entry))
                children.append(
                    FileNode(
                        name=entry.name,
                        path=str(entry.relative_to(repo_root)),
                        type="file",
                        language=language,
                    )
                )
                file_count += 1

        node = FileNode(
            name=directory.name,
            path=str(directory.relative_to(repo_root)) if directory != repo_root else "",
            type="directory",
            children=children if children else None,
        )

        return node, file_count

    async def load_local(self, path: str) -> dict:
        """
        Load a local repository or directory.

        Args:
            path: Absolute or relative path to the repository

        Returns:
            Dictionary with repo info
        """
        repo_path = Path(path).resolve()

        if not repo_path.exists():
            raise ValueError(f"Path does not exist: {path}")

        if not repo_path.is_dir():
            raise ValueError(f"Path is not a directory: {path}")

        repo_id = str(uuid.uuid4())[:8]
        gitignore = self._load_gitignore(repo_path)

        file_tree, file_count = self._build_file_tree(repo_path, repo_path, gitignore)

        # Store repo info
        self._repos[repo_id] = {
            "path": str(repo_path),
            "type": "local",
            "file_count": file_count,
        }

        return {
            "repo_id": repo_id,
            "root_path": str(repo_path),
            "file_tree": file_tree,
            "file_count": file_count,
        }

    async def clone_github(self, github_url: str, token: Optional[str] = None) -> dict:
        """
        Clone a GitHub repository to a temp directory.

        Args:
            github_url: GitHub repository URL
            token: Optional GitHub token for private repos

        Returns:
            Dictionary with repo info
        """
        # Create temp directory
        temp_dir = tempfile.mkdtemp(prefix="biocodeteacher_")

        try:
            # Modify URL for authentication if token provided
            if token:
                # Insert token into URL: https://TOKEN@github.com/user/repo.git
                if github_url.startswith("https://"):
                    github_url = github_url.replace("https://", f"https://{token}@")

            # Clone the repository
            GitRepo.clone_from(github_url, temp_dir, depth=1)  # Shallow clone

            repo_path = Path(temp_dir)
            repo_id = str(uuid.uuid4())[:8]
            gitignore = self._load_gitignore(repo_path)

            file_tree, file_count = self._build_file_tree(repo_path, repo_path, gitignore)

            # Store repo info
            self._repos[repo_id] = {
                "path": str(repo_path),
                "type": "github",
                "url": github_url,
                "file_count": file_count,
                "temp_dir": temp_dir,  # Track for cleanup
            }

            return {
                "repo_id": repo_id,
                "root_path": str(repo_path),
                "file_tree": file_tree,
                "file_count": file_count,
            }

        except Exception as e:
            # Clean up on failure
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise ValueError(f"Failed to clone repository: {str(e)}")

    def get_repo_path(self, repo_id: str) -> Path:
        """Get the root path for a loaded repository."""
        if repo_id not in self._repos:
            raise ValueError(f"Repository not found: {repo_id}")
        return Path(self._repos[repo_id]["path"])

    async def read_file(self, repo_id: str, file_path: str) -> dict:
        """
        Read content of a file in a repository.

        Args:
            repo_id: Repository identifier
            file_path: Relative path to file within repo

        Returns:
            Dictionary with file content and metadata
        """
        repo_path = self.get_repo_path(repo_id)
        full_path = repo_path / file_path

        if not full_path.exists():
            raise ValueError(f"File not found: {file_path}")

        if not full_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        # Read file content
        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            raise ValueError(f"Failed to read file: {str(e)}")

        language = self.detect_language(file_path)
        line_count = content.count("\n") + 1 if content else 0

        return {
            "path": file_path,
            "content": content,
            "language": language,
            "line_count": line_count,
        }

    def cleanup_repo(self, repo_id: str):
        """Clean up a repository (remove temp files for GitHub clones)."""
        if repo_id not in self._repos:
            raise ValueError(f"Repository not found: {repo_id}")

        repo_info = self._repos[repo_id]
        if repo_info.get("temp_dir"):
            shutil.rmtree(repo_info["temp_dir"], ignore_errors=True)
        del self._repos[repo_id]


# Global instance
repo_manager = RepoManager()
