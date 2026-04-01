"""
Pydantic schemas for request/response validation.
"""

from typing import Any, Dict, Optional, List, Literal
from pydantic import BaseModel, Field


# ============ Repository Schemas ============

class RepoLoadRequest(BaseModel):
    """Request to load a repository."""
    path: Optional[str] = Field(None, description="Local filesystem path to repository")
    github_url: Optional[str] = Field(None, description="GitHub repository URL to clone")
    github_token: Optional[str] = Field(None, description="GitHub token for private repos")


class FileNode(BaseModel):
    """Represents a file or directory in the tree."""
    name: str
    path: str
    type: Literal["file", "directory"]
    language: Optional[str] = None
    children: Optional[List["FileNode"]] = None


class RepoLoadResponse(BaseModel):
    """Response after loading a repository."""
    success: bool
    repo_id: str
    root_path: str
    file_tree: FileNode
    file_count: int
    message: Optional[str] = None
    has_cached_analysis: bool = False


# ============ Directory Browse Schemas ============

class DirectoryEntry(BaseModel):
    """A single directory in a browse listing."""
    name: str
    path: str


class BrowseResponse(BaseModel):
    """Response from browsing a directory."""
    current: str
    parent: Optional[str] = None
    directories: List[DirectoryEntry]


# ============ File Schemas ============

class FileContentRequest(BaseModel):
    """Request to read file content."""
    repo_id: str
    file_path: str


class FileContentResponse(BaseModel):
    """Response with file content."""
    path: str
    content: str
    language: str
    line_count: int


# ============ Explanation Schemas ============

class LineExplainRequest(BaseModel):
    """Request to explain a specific line."""
    api_key: str = Field(..., description="API key for the selected provider")
    model: str = Field(
        default="anthropic/claude-opus-4.6",
        description="Model ID to use"
    )
    reasoning_effort: Optional[str] = Field(
        default=None,
        description="Reasoning effort level for thinking models (e.g., 'medium', 'high')"
    )
    provider_routing: Optional[Dict[str, Any]] = Field(
        default=None,
        description="OpenRouter provider routing config (e.g., {only: ['azure'], zdr: true})"
    )
    provider: Optional[str] = Field(default="openrouter", description="API provider: openrouter, openai, or anthropic")
    repo_id: str
    file_path: str
    line_number: int = Field(..., ge=1)
    context_lines: int = Field(default=10, ge=0, le=50)


class RangeExplainRequest(BaseModel):
    """Request to explain a range of lines."""
    api_key: str
    model: str = Field(
        default="anthropic/claude-opus-4.6",
        description="Model ID to use"
    )
    reasoning_effort: Optional[str] = Field(
        default=None,
        description="Reasoning effort level for thinking models (e.g., 'medium', 'high')"
    )
    provider_routing: Optional[Dict[str, Any]] = Field(
        default=None,
        description="OpenRouter provider routing config"
    )
    provider: Optional[str] = Field(default="openrouter", description="API provider: openrouter, openai, or anthropic")
    repo_id: str
    file_path: str
    start_line: int = Field(..., ge=1)
    end_line: int = Field(..., ge=1)


class ArchitectureRequest(BaseModel):
    """Request for repository architecture analysis."""
    api_key: str
    model: str = Field(
        default="anthropic/claude-opus-4.6",
        description="Model ID to use"
    )
    reasoning_effort: Optional[str] = Field(
        default=None,
        description="Reasoning effort level for thinking models (e.g., 'medium', 'high')"
    )
    provider_routing: Optional[Dict[str, Any]] = Field(
        default=None,
        description="OpenRouter provider routing config"
    )
    provider: Optional[str] = Field(default="openrouter", description="API provider: openrouter, openai, or anthropic")
    repo_id: str
    max_files: int = Field(default=50, ge=1, le=200)


class TokenInfo(BaseModel):
    """Information about a single token in the code."""
    token: str
    type: str
    meaning: str
    start_col: Optional[int] = None
    end_col: Optional[int] = None


class ExplanationResponse(BaseModel):
    """Full explanation response."""
    line_number: int
    code_line: str
    purpose: str
    tokens: List[TokenInfo]
    parameters: Optional[str] = None
    context: str
    learn_more: List[str]
    diagram: Optional[str] = None  # Mermaid diagram code


# ============ Chat Schemas ============

class ChatMessage(BaseModel):
    """A single chat message."""
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    """Request for chat with code context."""
    api_key: str
    model: str = Field(
        default="anthropic/claude-opus-4.6",
        description="Model ID to use"
    )
    reasoning_effort: Optional[str] = Field(
        default=None,
        description="Reasoning effort level for thinking models (e.g., 'medium', 'high')"
    )
    provider_routing: Optional[Dict[str, Any]] = Field(
        default=None,
        description="OpenRouter provider routing config"
    )
    provider: Optional[str] = Field(default="openrouter", description="API provider: openrouter, openai, or anthropic")
    repo_id: str
    file_path: Optional[str] = None
    line_range: Optional[tuple[int, int]] = None
    message: str
    history: List[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """Chat response."""
    response: str
    has_diagram: bool = False
    diagram: Optional[str] = None


# ============ Architecture Agent Schemas ============

class ArchitecturePhaseUpdate(BaseModel):
    """Progress update during agentic architecture analysis."""
    phase: str  # "structure_scan", "key_file_identification", "deep_analysis", "synthesis"
    status: str  # "started", "complete", "error"
    detail: Optional[str] = None
    files_selected: Optional[List[str]] = None


class ComponentInfo(BaseModel):
    """Information about a component discovered during analysis."""
    path: str
    role: str
    dependencies: List[str] = Field(default_factory=list)
    pipeline_stage: Optional[str] = None


class ArchitectureContextSummary(BaseModel):
    """Stored architecture context for enriching explanations."""
    repo_id: str
    overview: str  # Populated from LLM's "data_flow" field
    components: List[ComponentInfo] = Field(default_factory=list)
    patterns: List[str] = Field(default_factory=list)
    context_block: str  # Condensed text for prompt injection
    timestamp: str
    domain: str = ""  # e.g. single-cell, spatial, pathology
    biological_decisions: List[str] = Field(default_factory=list)


# ============ WebSocket Schemas ============

class StreamMessage(BaseModel):
    """Message format for WebSocket streaming."""
    type: Literal["start", "chunk", "end", "error"]
    content: Optional[str] = None
    metadata: Optional[dict] = None


# Enable forward references for recursive FileNode
FileNode.model_rebuild()
