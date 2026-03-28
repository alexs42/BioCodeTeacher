"""
File browsing and reading endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from models.schemas import FileContentResponse
from services.repo_manager import repo_manager

router = APIRouter()


@router.get("/content", response_model=FileContentResponse)
async def get_file_content(
    repo_id: str = Query(..., description="Repository identifier"),
    file_path: str = Query(..., description="Relative path to file")
):
    """
    Read the content of a file in a loaded repository.
    """
    try:
        result = await repo_manager.read_file(repo_id, file_path)
        return FileContentResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")


@router.get("/tree")
async def get_file_tree(repo_id: str = Query(..., description="Repository identifier")):
    """
    Get the file tree structure for a loaded repository.
    Note: The tree is also returned when loading a repository.
    """
    try:
        # Re-scan the repository
        repo_path = repo_manager.get_repo_path(repo_id)
        result = await repo_manager.load_local(str(repo_path))

        # Update the repo ID mapping
        repo_manager._repos[repo_id] = repo_manager._repos.pop(result["repo_id"])

        return {
            "repo_id": repo_id,
            "file_tree": result["file_tree"],
            "file_count": result["file_count"],
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
