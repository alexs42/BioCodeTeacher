"""
Chat endpoints for Q&A about code.
"""

import json
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from models.schemas import ChatRequest, ChatResponse
from services.openrouter import OpenRouterService, CHAT_SYSTEM
from services.repo_manager import repo_manager
from services.code_parser import code_parser

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with code context (non-streaming).
    """
    try:
        # Build context
        context_parts = []

        if request.file_path:
            file_data = await repo_manager.read_file(
                request.repo_id, request.file_path
            )
            content = file_data["content"]
            language = file_data["language"]

            if request.line_range:
                start, end = request.line_range
                code_snippet = code_parser.get_line_range(content, start, end)
                context_parts.append(
                    f"Currently viewing {request.file_path} (lines {start}-{end}):\n```{language}\n{code_snippet}\n```"
                )
            else:
                # Truncate for context window
                truncated = content[:3000] + ("..." if len(content) > 3000 else "")
                context_parts.append(
                    f"Currently viewing {request.file_path}:\n```{language}\n{truncated}\n```"
                )

        # Build message history
        messages_text = ""
        for msg in request.history[-10:]:  # Last 10 messages
            role = "User" if msg.role == "user" else "Assistant"
            messages_text += f"{role}: {msg.content}\n\n"

        prompt = f"""**Code Context**:
{chr(10).join(context_parts) if context_parts else "No file currently open."}

**Conversation History**:
{messages_text if messages_text else "This is the start of the conversation."}

**User Question**:
{request.message}

Provide a helpful, educational response:"""

        service = OpenRouterService(request.api_key, request.model, request.reasoning_effort)
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

                if file_path and repo_id:
                    file_data = await repo_manager.read_file(repo_id, file_path)
                    content = file_data["content"]
                    language = file_data["language"]

                    line_range = request.get("line_range")
                    if line_range:
                        start, end = line_range
                        code_snippet = code_parser.get_line_range(content, start, end)
                        context_parts.append(
                            f"Viewing {file_path} (lines {start}-{end}):\n```{language}\n{code_snippet}\n```"
                        )
                    else:
                        truncated = content[:3000] + ("..." if len(content) > 3000 else "")
                        context_parts.append(
                            f"Viewing {file_path}:\n```{language}\n{truncated}\n```"
                        )

                # Build history
                history = request.get("history", [])
                messages_text = ""
                for msg in history[-10:]:
                    role = "User" if msg["role"] == "user" else "Assistant"
                    messages_text += f"{role}: {msg['content']}\n\n"

                message = request.get("message", "")

                prompt = f"""**Code Context**:
{chr(10).join(context_parts) if context_parts else "No file currently open."}

**Conversation History**:
{messages_text if messages_text else "This is the start of the conversation."}

**User Question**:
{message}

Provide a helpful, educational response:"""

                await websocket.send_json({"type": "start"})

                model = request.get("model", "anthropic/claude-opus-4.6")
                reasoning_effort = request.get("reasoning_effort")
                service = OpenRouterService(api_key, model, reasoning_effort)
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
