"""
BioCodeTeacher Backend - FastAPI application entry point.
Provides API endpoints for bioinformatics code explanation, repository management, and chat.
"""

import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from routers import repos, files, explain, chat

# Detect if running as a PyInstaller bundle
IS_PRODUCTION = getattr(sys, 'frozen', False)


def get_base_path() -> str:
    """Return base path -- _MEIPASS when frozen by PyInstaller, else backend dir."""
    if IS_PRODUCTION and hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


app = FastAPI(
    title="BioCodeTeacher API",
    description="Bioinformatics code explanation API for single-cell, spatial, and pathology analysis",
    version="1.0.0",
)

# CORS only needed in dev mode (separate frontend/backend ports)
if not IS_PRODUCTION:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Register routers
app.include_router(repos.router, prefix="/api/repos", tags=["repositories"])
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(explain.router, prefix="/api/explain", tags=["explanations"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])


@app.get("/api/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "features": {
            "streaming": True,
            "local_repos": True,
            "github_clone": True,
        },
    }


# In production, serve the pre-built frontend from frontend_dist/
if IS_PRODUCTION:
    _dist_path = os.path.join(get_base_path(), 'frontend_dist')

    # Mount assets directory for JS/CSS bundles
    app.mount("/assets", StaticFiles(directory=os.path.join(_dist_path, "assets")), name="static_assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve frontend SPA — try exact file first, fall back to index.html."""
        file_path = os.path.join(_dist_path, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(_dist_path, "index.html"))
else:
    @app.get("/")
    async def root():
        """Health check endpoint (dev mode only)."""
        return {"status": "ok", "service": "BioCodeTeacher API"}
