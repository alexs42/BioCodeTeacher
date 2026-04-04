"""
Chat endpoints for Q&A about code.
"""

import json
from typing import Optional
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from models.schemas import ChatRequest, ChatResponse
from services.openrouter import (
    OpenRouterService, CHAT_SYSTEM,
    CHAT_CONTEXT_PREFIX, CHAT_FILE_SUMMARY_PREFIX, CHAT_DOC_PREFIX,
)
from services.repo_manager import repo_manager
from services.code_parser import code_parser
from services.architecture_store import architecture_store
from services.persistent_store import persistent_store
from services.doc_search import doc_search_service

router = APIRouter()


def _build_repo_context(
    repo_id: Optional[str],
    file_path: Optional[str],
    file_content: Optional[str] = None,
    language: Optional[str] = None,
) -> str:
    """Build repo/file context for chat prompt injection (tiers 1-3, sync).

    Mirrors the three-tier context assembly in explain.py:335-356,
    with tighter word budgets to leave room for conversation history.
    This is purely in-memory lookups — no network I/O.
    """
    if not repo_id:
        return ""

    parts: list[str] = []

    # Tier 1: file-specific architecture context (role, deps, pipeline stage)
    # Tier 2 fallback: generic project context block
    if file_path:
        file_ctx = architecture_store.get_file_context(
            repo_id, file_path,
            file_content=file_content, language=language,
        )
    else:
        file_ctx = None

    if file_ctx:
        parts.append(CHAT_CONTEXT_PREFIX.format(context_block=file_ctx))
    else:
        context_block = architecture_store.get_context_block(repo_id)
        if context_block:
            # Truncate to 200 words (tighter than explain's full block)
            words = context_block.split()[:200]
            parts.append(CHAT_CONTEXT_PREFIX.format(
                context_block=" ".join(words)
            ))

    # Tier 3: cached file summary
    if file_path:
        repo_path = persistent_store.get_repo_path(repo_id)
        if repo_path:
            cached_summary = persistent_store.load_file_summary(
                repo_path, file_path
            )
            if cached_summary and cached_summary.get("summary_md"):
                words = cached_summary["summary_md"].split()[:200]
                parts.append(CHAT_FILE_SUMMARY_PREFIX.format(
                    file_summary=" ".join(words)
                ))

    return "".join(parts)


async def _fetch_doc_context(
    message: str,
    file_content: Optional[str] = None,
    language: Optional[str] = None,
) -> str:
    """Fetch documentation for functions referenced in the user's question (tier 4).

    This involves network I/O and is kept separate from _build_repo_context
    so it can run after the WS 'start' event, not blocking chat startup.
    """
    if not message:
        return ""

    imports = (
        code_parser.extract_imports(file_content, language)
        if file_content and language else []
    )
    try:
        doc_snippet = await doc_search_service.get_relevant_docs(
            imports=imports,
            question=message,
            file_content=file_content,
            language=language,
        )
        if doc_snippet:
            return CHAT_DOC_PREFIX.format(documentation=doc_snippet)
    except Exception:
        pass  # Graceful degradation — doc search is best-effort

    return ""


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with code context (non-streaming).
    """
    try:
        # Build context
        context_parts = []
        file_content = None
        file_language = None

        if request.file_path:
            file_data = await repo_manager.read_file(
                request.repo_id, request.file_path
            )
            file_content = file_data["content"]
            file_language = file_data["language"]

            if request.line_range:
                start, end = request.line_range
                code_snippet = code_parser.get_line_range(file_content, start, end)
                context_parts.append(
                    f"Currently viewing {request.file_path} (lines {start}-{end}):\n```{file_language}\n{code_snippet}\n```"
                )
            else:
                # Truncate for context window
                truncated = file_content[:3000] + ("..." if len(file_content) > 3000 else "")
                context_parts.append(
                    f"Currently viewing {request.file_path}:\n```{file_language}\n{truncated}\n```"
                )

        # Build repo/file context (tiers 1-3: sync, in-memory)
        repo_context = _build_repo_context(
            request.repo_id, request.file_path,
            file_content=file_content, language=file_language,
        )

        # Fetch documentation context (tier 4: async, network I/O)
        doc_context = await _fetch_doc_context(
            request.message,
            file_content=file_content, language=file_language,
        )

        # Build message history
        messages_text = ""
        for msg in request.history[-10:]:  # Last 10 messages
            role = "User" if msg.role == "user" else "Assistant"
            messages_text += f"{role}: {msg.content}\n\n"

        prompt = f"""{repo_context}{doc_context}**Code Context**:
{chr(10).join(context_parts) if context_parts else "No file currently open."}

**Conversation History**:
{messages_text if messages_text else "This is the start of the conversation."}

**User Question**:
{request.message}

Provide a helpful, educational response:"""

        service = OpenRouterService(request.api_key, request.model, request.reasoning_effort, getattr(request, 'provider_routing', None), provider=getattr(request, 'provider', 'openrouter'))
        response = await service.complete(prompt, CHAT_SYSTEM)

        # Check if response contains a mermaid diagram
        has_diagram = "```mermaid" in response

        return ChatResponse(
            response=response,
            has_diagram=has_diagram,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.websocket("/stream")
async def stream_chat(websocket: WebSocket):
    """
    WebSocket endpoint for streaming chat responses.

    Client sends JSON:
    {
        "api_key": "...",
        "repo_id": "...",
        "file_path": "..." (optional),
        "line_range": [start, end] (optional),
        "message": "...",
        "history": [{"role": "user"|"assistant", "content": "..."}]
    }
    """
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            request = json.loads(data)

            api_key = request.get("api_key")
            if not api_key:
                await websocket.send_json({
                    "type": "error",
                    "content": "API key is required"
                })
                continue

            try:
                # Build context
                context_parts = []
                file_path = request.get("file_path")
                repo_id = request.get("repo_id")
                file_content = None
                file_language = None

                if file_path and repo_id:
                    file_data = await repo_manager.read_file(repo_id, file_path)
                    file_content = file_data["content"]
                    file_language = file_data["language"]

                    line_range = request.get("line_range")
                    if line_range:
                        start, end = line_range
                        code_snippet = code_parser.get_line_range(file_content, start, end)
                        context_parts.append(
                            f"Viewing {file_path} (lines {start}-{end}):\n```{file_language}\n{code_snippet}\n```"
                        )
                    else:
                        truncated = file_content[:3000] + ("..." if len(file_content) > 3000 else "")
                        context_parts.append(
                            f"Viewing {file_path}:\n```{file_language}\n{truncated}\n```"
                        )

                # Build repo/file context (tiers 1-3: sync, in-memory)
                message = request.get("message", "")
                repo_context = _build_repo_context(
                    repo_id, file_path,
                    file_content=file_content, language=file_language,
                )

                # Send start BEFORE doc fetch so the UI isn't blocked
                await websocket.send_json({"type": "start"})

                # Fetch documentation context (tier 4: async, network I/O)
                doc_context = await _fetch_doc_context(
                    message,
                    file_content=file_content, language=file_language,
                )

                # Build history
                history = request.get("history", [])
                messages_text = ""
                for msg in history[-10:]:
                    role = "User" if msg["role"] == "user" else "Assistant"
                    messages_text += f"{role}: {msg['content']}\n\n"

                prompt = f"""{repo_context}{doc_context}**Code Context**:
{chr(10).join(context_parts) if context_parts else "No file currently open."}

**Conversation History**:
{messages_text if messages_text else "This is the start of the conversation."}

**User Question**:
{message}

Provide a helpful, educational response:"""

                model = request.get("model", "anthropic/claude-opus-4.6")
                reasoning_effort = request.get("reasoning_effort")
                provider_routing = request.get("provider_routing")
                provider = request.get("provider", "openrouter")
                service = OpenRouterService(api_key, model, reasoning_effort, provider_routing, provider=provider)
                async for chunk in service.stream_completion(prompt, CHAT_SYSTEM):
                    await websocket.send_json({
                        "type": "chunk",
                        "content": chunk
                    })

                await websocket.send_json({"type": "end"})

            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "content": str(e)
                })

    except WebSocketDisconnect:
        pass
