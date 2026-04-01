"""
Code explanation endpoints with WebSocket streaming support.
"""

import json
from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from models.schemas import (
    LineExplainRequest,
    RangeExplainRequest,
    ArchitectureRequest,
)
from services.openrouter import (
    OpenRouterService,
    LINE_EXPLAIN_SYSTEM,
    LINE_EXPLAIN_TEMPLATE,
    LINE_EXPLAIN_CONTEXT_PREFIX,
    FILE_CONTEXT_PREFIX,
    FILE_SUMMARY_SYSTEM,
    FILE_SUMMARY_TEMPLATE,
    FILE_SUMMARY_CONTEXT_PREFIX,
    ARCHITECTURE_SYSTEM,
    ARCHITECTURE_TEMPLATE,
)
from services.persistent_store import persistent_store
from services.repo_manager import repo_manager
from services.code_parser import code_parser
from services.explanation_cache import explanation_cache
from services.architecture_store import architecture_store
from services.architecture_agent import ArchitectureAgent

router = APIRouter()


@router.post("/line")
async def explain_line(request: LineExplainRequest):
    """
    Get a complete (non-streaming) explanation for a single line.
    For streaming, use the WebSocket endpoint.
    """
    try:
        # Read file content
        file_data = await repo_manager.read_file(request.repo_id, request.file_path)
        content = file_data["content"]
        language = file_data["language"]

        # Check cache
        cached = explanation_cache.get(
            request.file_path, content, request.line_number
        )
        if cached:
            return {"explanation": cached, "cached": True}

        # Get line with context
        context_before, line_code, context_after = code_parser.get_line_with_context(
            content, request.line_number, request.context_lines
        )

        # Build prompt
        prompt = LINE_EXPLAIN_TEMPLATE.format(
            filename=request.file_path,
            language=language,
            line_number=request.line_number,
            line_code=line_code,
            context_before=context_before,
            context_after=context_after,
        )

        # Get explanation from AI model
        service = OpenRouterService(request.api_key, request.model, request.reasoning_effort, getattr(request, 'provider_routing', None), provider=getattr(request, 'provider', 'openrouter'))
        explanation = await service.complete(prompt, LINE_EXPLAIN_SYSTEM)

        # Cache the result
        explanation_cache.set(
            request.file_path, content, request.line_number, explanation
        )

        return {"explanation": explanation, "cached": False}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation failed: {str(e)}")


@router.post("/range")
async def explain_range(request: RangeExplainRequest):
    """
    Explain a range of lines (e.g., a function or code block).
    """
    try:
        file_data = await repo_manager.read_file(request.repo_id, request.file_path)
        content = file_data["content"]
        language = file_data["language"]

        # Get the range
        code_range = code_parser.get_line_range(
            content, request.start_line, request.end_line
        )

        prompt = f"""**File**: {request.file_path}
**Language**: {language}
**Lines {request.start_line}-{request.end_line}**:
```{language}
{code_range}
```

Explain this code block:

## Overview
[What does this code block do as a whole?]

## Step-by-Step
[Explain each significant part]

## Key Concepts
[Programming concepts demonstrated here]

## Diagram
```mermaid
[If helpful, show data flow or logic flow]
```
"""

        service = OpenRouterService(request.api_key, request.model, request.reasoning_effort, getattr(request, 'provider_routing', None), provider=getattr(request, 'provider', 'openrouter'))
        explanation = await service.complete(prompt, LINE_EXPLAIN_SYSTEM)

        return {"explanation": explanation}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation failed: {str(e)}")


@router.post("/architecture")
async def explain_architecture(request: ArchitectureRequest):
    """
    Generate architecture analysis for a repository.
    """
    try:
        repo_path = repo_manager.get_repo_path(request.repo_id)

        # Build file tree string
        def tree_to_string(node, prefix=""):
            result = []
            if node.type == "file":
                result.append(f"{prefix}{node.name}")
            else:
                result.append(f"{prefix}{node.name}/")
                if node.children:
                    for child in node.children:
                        result.extend(tree_to_string(child, prefix + "  "))
            return result

        # Get repository info
        repo_info = await repo_manager.load_local(str(repo_path))
        tree_lines = tree_to_string(repo_info["file_tree"])
        file_tree = "\n".join(tree_lines)

        # Read key files (entry points, configs)
        key_files = []
        key_file_names = [
            "main.py", "app.py", "index.js", "index.ts", "main.go", "main.rs",
            "package.json", "pyproject.toml", "Cargo.toml", "go.mod",
            "README.md", "readme.md",
        ]

        for name in key_file_names:
            try:
                file_data = await repo_manager.read_file(request.repo_id, name)
                # Truncate large files
                content = file_data["content"][:2000]
                key_files.append(f"### {name}\n```\n{content}\n```")
            except:
                pass

        key_files_content = "\n\n".join(key_files) if key_files else "No key files found."

        prompt = ARCHITECTURE_TEMPLATE.format(
            file_tree=file_tree,
            key_files_content=key_files_content,
        )

        service = OpenRouterService(request.api_key, request.model, request.reasoning_effort, getattr(request, 'provider_routing', None), provider=getattr(request, 'provider', 'openrouter'))
        analysis = await service.complete(prompt, ARCHITECTURE_SYSTEM, max_tokens=8000)

        return {"analysis": analysis}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Architecture analysis failed: {str(e)}")


@router.get("/architecture-status/{repo_id}")
async def architecture_status(repo_id: str):
    """Check if architecture analysis exists for a repository."""
    try:
        repo_path = str(repo_manager.get_repo_path(repo_id))
    except ValueError:
        repo_path = None
    return architecture_store.get_status(repo_id, repo_path=repo_path)


@router.get("/architecture-content/{repo_id}")
async def architecture_content(repo_id: str):
    """Get the full rendered architecture overview markdown."""
    display_md = architecture_store.get_display_md(repo_id)
    has_analysis = architecture_store.has_analysis(repo_id)
    status = architecture_store.get_status(repo_id)
    return {
        "has_analysis": has_analysis,
        "content": display_md or "",
        "component_count": status.get("component_count", 0),
        "patterns": status.get("patterns", []),
        "timestamp": status.get("timestamp"),
    }


@router.get("/file-context/{repo_id}")
async def file_context(repo_id: str, file_path: str = Query(...)):
    """Get structured architecture context for a specific file."""
    data = architecture_store.get_file_context_data(repo_id, file_path)
    if data is None:
        return {"found": False}
    return {"found": True, **data}


@router.get("/file-summary/{repo_id}")
async def get_file_summary(repo_id: str, file_path: str = Query(...)):
    """Get cached file summary. Returns {found: false} if not cached."""
    repo_path = persistent_store.get_repo_path(repo_id)
    if not repo_path:
        return {"found": False}
    summary = persistent_store.load_file_summary(repo_path, file_path)
    if summary is None:
        return {"found": False}
    return {"found": True, **summary}


@router.websocket("/stream")
async def stream_explanation(websocket: WebSocket):
    """
    WebSocket endpoint for streaming explanations.

    Client sends JSON:
    {
        "type": "line" | "range" | "architecture",
        "api_key": "...",
        "repo_id": "...",
        "file_path": "...",
        "line_number": 42,
        "context_lines": 10
    }

    Server streams JSON:
    {"type": "start", "metadata": {...}}
    {"type": "chunk", "content": "..."}
    {"type": "end"}
    {"type": "error", "content": "..."}
    """
    await websocket.accept()

    try:
        while True:
            # Receive request
            data = await websocket.receive_text()
            request = json.loads(data)

            request_type = request.get("type", "line")
            api_key = request.get("api_key")

            if not api_key:
                await websocket.send_json({
                    "type": "error",
                    "content": "API key is required"
                })
                continue

            try:
                if request_type == "line":
                    await stream_line_explanation(websocket, request)
                elif request_type == "range":
                    await stream_range_explanation(websocket, request)
                elif request_type == "architecture":
                    await stream_architecture_analysis(websocket, request)
                elif request_type == "architecture_agent":
                    await stream_architecture_agent(websocket, request)
                elif request_type == "analyze_file":
                    await analyze_single_file(websocket, request)
                elif request_type == "file_summary":
                    await stream_file_summary(websocket, request)
                else:
                    await websocket.send_json({
                        "type": "error",
                        "content": f"Unknown request type: {request_type}"
                    })
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "content": str(e)
                })

    except WebSocketDisconnect:
        pass


async def stream_line_explanation(websocket: WebSocket, request: dict):
    """Stream a line explanation."""
    file_data = await repo_manager.read_file(
        request["repo_id"], request["file_path"]
    )
    content = file_data["content"]
    language = file_data["language"]

    line_number = request["line_number"]
    context_lines = request.get("context_lines", 10)

    # Get line with context
    context_before, line_code, context_after = code_parser.get_line_with_context(
        content, line_number, context_lines
    )

    # Send start message
    await websocket.send_json({
        "type": "start",
        "metadata": {
            "line_number": line_number,
            "line_code": line_code,
            "language": language,
        }
    })

    # Build prompt with layered context: repo → file summary → file architecture
    prompt = ""
    file_context = architecture_store.get_file_context(
        request["repo_id"], request["file_path"],
        file_content=content, language=language
    )
    if file_context:
        prompt += FILE_CONTEXT_PREFIX.format(file_context=file_context)
    else:
        context_block = architecture_store.get_context_block(request["repo_id"])
        if context_block:
            prompt += LINE_EXPLAIN_CONTEXT_PREFIX.format(context_block=context_block)

    # Add file summary context if available (three-tier enrichment)
    repo_path = persistent_store.get_repo_path(request["repo_id"])
    if repo_path:
        cached_summary = persistent_store.load_file_summary(repo_path, request["file_path"])
        if cached_summary and cached_summary.get("summary_md"):
            # Use first 500 words of summary as context
            words = cached_summary["summary_md"].split()[:500]
            prompt += FILE_SUMMARY_CONTEXT_PREFIX.format(
                file_summary=" ".join(words)
            )

    prompt += LINE_EXPLAIN_TEMPLATE.format(
        filename=request["file_path"],
        language=language,
        line_number=line_number,
        line_code=line_code,
        context_before=context_before,
        context_after=context_after,
    )

    # Stream response
    model = request.get("model", "anthropic/claude-opus-4.6")
    reasoning_effort = request.get("reasoning_effort")
    provider_routing = request.get("provider_routing")
    provider = request.get("provider", "openrouter")
    service = OpenRouterService(request["api_key"], model, reasoning_effort, provider_routing, provider=provider)
    full_response = ""

    async for chunk in service.stream_completion(prompt, LINE_EXPLAIN_SYSTEM):
        full_response += chunk
        await websocket.send_json({
            "type": "chunk",
            "content": chunk
        })

    # Cache the result
    explanation_cache.set(
        request["file_path"], content, line_number, full_response
    )

    await websocket.send_json({"type": "end"})


async def stream_range_explanation(websocket: WebSocket, request: dict):
    """Stream a range explanation."""
    file_data = await repo_manager.read_file(
        request["repo_id"], request["file_path"]
    )
    content = file_data["content"]
    language = file_data["language"]

    start_line = request["start_line"]
    end_line = request["end_line"]

    code_range = code_parser.get_line_range(content, start_line, end_line)

    await websocket.send_json({
        "type": "start",
        "metadata": {
            "start_line": start_line,
            "end_line": end_line,
            "language": language,
        }
    })

    # Build prompt with file-specific or generic architecture context
    file_context = architecture_store.get_file_context(
        request["repo_id"], request["file_path"],
        file_content=content, language=language
    )
    if file_context:
        arch_prefix = FILE_CONTEXT_PREFIX.format(file_context=file_context)
    else:
        context_block = architecture_store.get_context_block(request["repo_id"])
        arch_prefix = LINE_EXPLAIN_CONTEXT_PREFIX.format(context_block=context_block) if context_block else ""

    prompt = f"""{arch_prefix}**File**: {request["file_path"]}
**Language**: {language}
**Lines {start_line}-{end_line}**:
```{language}
{code_range}
```

Explain this code block with these sections:

## Overview
[What does this code block accomplish?]

## Step-by-Step Breakdown
[Walk through the code logically]

## Key Concepts
[Important programming concepts]

## Diagram
```mermaid
[Show logic flow if helpful]
```
"""

    model = request.get("model", "anthropic/claude-opus-4.6")
    reasoning_effort = request.get("reasoning_effort")
    provider_routing = request.get("provider_routing")
    provider = request.get("provider", "openrouter")
    service = OpenRouterService(request["api_key"], model, reasoning_effort, provider_routing, provider=provider)

    async for chunk in service.stream_completion(prompt, LINE_EXPLAIN_SYSTEM):
        await websocket.send_json({
            "type": "chunk",
            "content": chunk
        })

    await websocket.send_json({"type": "end"})


async def stream_architecture_analysis(websocket: WebSocket, request: dict):
    """Stream architecture analysis."""
    repo_path = repo_manager.get_repo_path(request["repo_id"])
    repo_info = await repo_manager.load_local(str(repo_path))

    def tree_to_string(node, prefix=""):
        result = []
        if node.type == "file":
            result.append(f"{prefix}{node.name}")
        else:
            result.append(f"{prefix}{node.name}/")
            if node.children:
                for child in node.children:
                    result.extend(tree_to_string(child, prefix + "  "))
        return result

    tree_lines = tree_to_string(repo_info["file_tree"])
    file_tree = "\n".join(tree_lines)

    await websocket.send_json({
        "type": "start",
        "metadata": {
            "repo_id": request["repo_id"],
            "file_count": repo_info["file_count"],
        }
    })

    # Read key files
    key_files = []
    key_file_names = [
        "main.py", "app.py", "index.js", "index.ts",
        "package.json", "pyproject.toml", "README.md",
    ]

    for name in key_file_names:
        try:
            file_data = await repo_manager.read_file(request["repo_id"], name)
            content = file_data["content"][:2000]
            key_files.append(f"### {name}\n```\n{content}\n```")
        except:
            pass

    key_files_content = "\n\n".join(key_files) if key_files else "No key files found."

    prompt = ARCHITECTURE_TEMPLATE.format(
        file_tree=file_tree,
        key_files_content=key_files_content,
    )

    model = request.get("model", "anthropic/claude-opus-4.6")
    reasoning_effort = request.get("reasoning_effort")
    provider_routing = request.get("provider_routing")
    provider = request.get("provider", "openrouter")
    service = OpenRouterService(request["api_key"], model, reasoning_effort, provider_routing, provider=provider)

    async for chunk in service.stream_completion(prompt, ARCHITECTURE_SYSTEM, max_tokens=8000):
        await websocket.send_json({
            "type": "chunk",
            "content": chunk
        })

    await websocket.send_json({"type": "end"})


async def stream_architecture_agent(websocket: WebSocket, request: dict):
    """Stream agentic architecture analysis with phase progress."""
    repo_id = request["repo_id"]
    repo_path = repo_manager.get_repo_path(repo_id)
    model = request.get("model", "anthropic/claude-opus-4.6")
    reasoning_effort = request.get("reasoning_effort")
    provider_routing = request.get("provider_routing")
    provider = request.get("provider", "openrouter")
    max_files = request.get("max_files_to_analyze", 15)

    service = OpenRouterService(request["api_key"], model, reasoning_effort, provider_routing, provider=provider)
    agent = ArchitectureAgent(service, repo_id, repo_path, max_files=max_files)

    async for event in agent.analyze():
        if event.type == "phase":
            await websocket.send_json({
                "type": "phase",
                "phase": event.phase,
                "status": event.status,
                "detail": event.detail,
                "files_selected": event.files_selected,
            })
        elif event.type == "chunk":
            await websocket.send_json({
                "type": "chunk",
                "content": event.content,
            })
        elif event.type == "end":
            await websocket.send_json({
                "type": "end",
                "has_context": event.has_context,
            })
        elif event.type == "error":
            await websocket.send_json({
                "type": "error",
                "content": event.content,
            })


async def analyze_single_file(websocket: WebSocket, request: dict):
    """Analyze a single file and add it to the architecture index.

    Makes 1 LLM call to determine the file's role and connections,
    then adds the result to the architecture store's component list.
    """
    from models.schemas import ComponentInfo

    repo_id = request.get("repo_id")
    file_path = request.get("file_path")

    if not repo_id or not file_path:
        await websocket.send_json({
            "type": "error",
            "content": "repo_id and file_path are required"
        })
        return

    # Must have existing architecture analysis to extend
    summary = architecture_store.get(repo_id)
    if not summary:
        await websocket.send_json({
            "type": "error",
            "content": "Run architecture analysis first"
        })
        return

    try:
        file_data = await repo_manager.read_file(repo_id, file_path)
        content = file_data["content"]
        language = file_data["language"]

        imports = code_parser.extract_imports(content, language)

        # Truncate content for prompt
        truncated = content[:4000] if len(content) > 4000 else content

        prompt = f"""Analyze this file from a software project.

**File**: {file_path}
**Language**: {language}
**Imports**: {', '.join(imports) if imports else 'none'}

**Content**:
```{language}
{truncated}
```

Respond with JSON only:
{{"role": "one sentence describing this file's responsibility", "dependencies": ["project-internal file paths this imports from"]}}
"""

        model = request.get("model", "anthropic/claude-opus-4.6")
        reasoning_effort = request.get("reasoning_effort")
        provider_routing = request.get("provider_routing")
        provider = request.get("provider", "openrouter")
        service = OpenRouterService(request["api_key"], model, reasoning_effort, provider_routing, provider=provider)
        response = await service.complete(prompt, system_prompt="You are a software architect. Respond with valid JSON only.", max_tokens=500, temperature=0.3)

        # Parse response
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            role = data.get("role", "Unknown role")
            deps = data.get("dependencies", [])
        else:
            role = "Could not determine role"
            deps = []

        # Add to existing components
        new_component = ComponentInfo(path=file_path, role=role, dependencies=deps)
        summary.components.append(new_component)
        architecture_store.save(repo_id, summary)  # re-save to invalidate index

        await websocket.send_json({
            "type": "file_analyzed",
            "file": file_path,
            "role": role,
            "dependencies": deps,
        })

    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "content": f"File analysis failed: {str(e)}"
        })


async def stream_file_summary(websocket: WebSocket, request: dict):
    """Stream an educational file summary.

    Checks cache first, then generates via LLM if not cached.
    Persists the result for future requests.
    """
    repo_id = request.get("repo_id")
    file_path = request.get("file_path")

    if not repo_id or not file_path:
        await websocket.send_json({
            "type": "error",
            "content": "repo_id and file_path are required"
        })
        return

    # Check disk cache first
    repo_path = persistent_store.get_repo_path(repo_id)
    if repo_path:
        import hashlib
        cached = persistent_store.load_file_summary(repo_path, file_path)
        if cached:
            # Verify content hasn't changed
            try:
                file_data = await repo_manager.read_file(repo_id, file_path)
                content_hash = hashlib.md5(file_data["content"].encode()).hexdigest()
                if cached.get("content_hash") == content_hash:
                    # Send cached summary as a single chunk
                    await websocket.send_json({"type": "start"})
                    await websocket.send_json({
                        "type": "chunk",
                        "content": cached["summary_md"]
                    })
                    await websocket.send_json({"type": "end"})
                    return
            except Exception:
                pass

    try:
        file_data = await repo_manager.read_file(repo_id, file_path)
        content = file_data["content"]
        language = file_data["language"]
        line_count = file_data["line_count"]

        # Build architecture context string if available
        arch_context = ""
        file_ctx = architecture_store.get_file_context(
            repo_id, file_path, file_content=content, language=language
        )
        if file_ctx:
            arch_context = f"**Architecture context:**\n{file_ctx}"
        else:
            ctx_block = architecture_store.get_context_block(repo_id)
            if ctx_block:
                arch_context = f"**Project context:**\n{ctx_block[:500]}"

        # Detect framework from architecture patterns
        summary = architecture_store.get(repo_id)
        framework = ", ".join(summary.patterns) if summary and summary.patterns else "general"

        # Truncate content for prompt
        truncated = content if len(content) <= 6000 else (
            content[:3000] + "\n\n... [truncated] ...\n\n" + content[-2000:]
        )

        prompt = FILE_SUMMARY_TEMPLATE.format(
            framework=framework,
            file_path=file_path,
            language=language,
            line_count=line_count,
            arch_context=arch_context,
            content=truncated,
        )

        model = request.get("model", "anthropic/claude-opus-4.6")
        reasoning_effort = request.get("reasoning_effort")
        provider_routing = request.get("provider_routing")
        provider = request.get("provider", "openrouter")
        service = OpenRouterService(request["api_key"], model, reasoning_effort, provider_routing, provider=provider)

        await websocket.send_json({"type": "start"})

        full_response = ""
        async for chunk in service.stream_completion(
            prompt, FILE_SUMMARY_SYSTEM, max_tokens=3000, temperature=0.4
        ):
            full_response += chunk
            await websocket.send_json({"type": "chunk", "content": chunk})

        await websocket.send_json({"type": "end"})

        # Persist the summary
        if repo_path:
            import hashlib
            content_hash = hashlib.md5(content.encode()).hexdigest()
            persistent_store.save_file_summary(repo_path, file_path, {
                "summary_md": full_response,
                "content_hash": content_hash,
                "file_path": file_path,
                "language": language,
                "line_count": line_count,
            })

    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "content": f"File summary failed: {str(e)}"
        })
