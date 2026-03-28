"""
Repository management endpoints.
"""

import platform
import string
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from models.schemas import (
    RepoLoadRequest,
    RepoLoadResponse,
    BrowseResponse,
    DirectoryEntry,
)
from services.repo_manager import repo_manager
from services.persistent_store import persistent_store
from services.architecture_store import architecture_store

router = APIRouter()


@router.get("/browse", response_model=BrowseResponse)
async def browse_directory(path: str = Query(default="")):
    """
    Browse filesystem directories for repo selection.

    If path is empty, returns filesystem roots.
    Otherwise returns immediate subdirectories of the given path.
    """
    if not path.strip():
        # Return filesystem roots
        if platform.system() == "Windows":
            drives = []
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if Path(drive).exists():
                    drives.append(DirectoryEntry(name=f"{letter}:", path=drive))
            return BrowseResponse(current="", directories=drives)
        else:
            return BrowseResponse(current="/", parent=None, directories=[
                DirectoryEntry(name=d.name, path=str(d))
                for d in sorted(Path("/").iterdir())
                if d.is_dir() and not d.name.startswith(".")
            ])

    target = Path(path).resolve()
    if not target.exists() or not target.is_dir():
        raise HTTPException(status_code=400, detail=f"Directory not found: {path}")

    # Compute parent (None for filesystem roots)
    parent = str(target.parent) if target.parent != target else None

    try:
        dirs = sorted(
            [
                DirectoryEntry(name=d.name, path=str(d))
                for d in target.iterdir()
                if d.is_dir() and not d.name.startswith(".")
            ],
            key=lambda d: d.name.lower(),
        )
    except PermissionError:
        raise HTTPException(status_code=403, detail=f"Permission denied: {path}")

    return BrowseResponse(
        current=str(target),
        parent=parent,
        directories=dirs,
    )


@router.post("/load", response_model=RepoLoadResponse)
async def load_repository(request: RepoLoadRequest):
    """
    Load a repository from local path or GitHub URL.

    Either `path` or `github_url` must be provided.
    """
    # Validate input first
    if not request.path and not request.github_url:
        raise HTTPException(
            status_code=400,
            detail="Either 'path' or 'github_url' must be provided"
        )

    try:
        if request.path:
            result = await repo_manager.load_local(request.path)
        else:
            result = await repo_manager.clone_github(
                request.github_url,
                request.github_token
            )

        repo_id = result["repo_id"]
        root_path = result["root_path"]

        # Register with persistent store and check for cached analysis
        persistent_store.register_repo(repo_id, root_path)
        has_cached = persistent_store.has_architecture(root_path)
        if has_cached:
            architecture_store.load_from_disk(repo_id, root_path)

        source = "local" if request.path else "GitHub"
        return RepoLoadResponse(
            success=True,
            repo_id=repo_id,
            root_path=root_path,
            file_tree=result["file_tree"],
            file_count=result["file_count"],
            message=f"Loaded {source} repository with {result['file_count']} files",
            has_cached_analysis=has_cached,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load repository: {str(e)}")


@router.delete("/{repo_id}")
async def unload_repository(repo_id: str):
    """
    Unload a repository and clean up any temporary files.
    """
    try:
        repo_manager.cleanup_repo(repo_id)
        return {"success": True, "message": f"Repository {repo_id} unloaded"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
