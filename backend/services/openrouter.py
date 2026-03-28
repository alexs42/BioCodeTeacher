"""
OpenRouter API service for frontier model interactions.
Supports both streaming and non-streaming responses.
Supports reasoning effort configuration for thinking models.
"""

import json
from typing import AsyncGenerator, Optional
import httpx

# OpenRouter API configuration
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "anthropic/claude-opus-4.6"

# Models that support the reasoning.effort parameter
REASONING_MODELS = {
    "openai/gpt-5.4",
    "google/gemini-3.1-pro-preview",
}


class OpenRouterService:
    """
    Service for interacting with AI models via OpenRouter API.
    Handles streaming responses for real-time UI updates.
    Supports configurable model selection and reasoning effort.
    """

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, reasoning_effort: Optional[str] = None):
        """
        Initialize OpenRouter service.

        Args:
            api_key: OpenRouter API key
            model: Model ID to use (e.g., "anthropic/claude-opus-4.6")
            reasoning_effort: Optional reasoning effort level ("medium", "high", etc.)
        """
        self.api_key = api_key
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5173",  # Required by OpenRouter
            "X-Title": "CodeTeacher",
        }

    async def stream_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a completion from Claude, yielding chunks as they arrive.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt for context
            max_tokens: Maximum tokens in response
            temperature: Creativity setting (0-1)

        Yields:
            Text chunks as they stream in
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        # Add reasoning effort for supported models
        if self.reasoning_effort and self.model in REASONING_MODELS:
            payload["reasoning"] = {"effort": self.reasoning_effort}

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                OPENROUTER_API_URL,
                headers=self.headers,
                json=payload,
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise Exception(f"OpenRouter API error: {response.status_code} - {error_text.decode()}")

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """
        Get a complete (non-streaming) response from Claude.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens in response
            temperature: Creativity setting

        Returns:
            Complete response text
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }

        # Add reasoning effort for supported models
        if self.reasoning_effort and self.model in REASONING_MODELS:
            payload["reasoning"] = {"effort": self.reasoning_effort}

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                OPENROUTER_API_URL,
                headers=self.headers,
                json=payload,
            )

            if response.status_code != 200:
                raise Exception(f"OpenRouter API error: {response.status_code} - {response.text}")

            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def validate_key(self) -> bool:
        """
        Validate that the API key is working.

        Returns:
            True if key is valid, False otherwise
        """
        try:
            # Send a minimal request to validate
            response = await self.complete(
                prompt="Say 'ok' and nothing else.",
                max_tokens=10,
                temperature=0,
            )
            return True
        except Exception:
            return False


# Prompt templates for CodeTeacher
LINE_EXPLAIN_SYSTEM = """You are CodeTeacher, an expert programming instructor.
Your goal is to explain code clearly and educationally.
Format your responses in Markdown with clear sections.
Be concise but thorough. Use analogies when helpful."""

LINE_EXPLAIN_TEMPLATE = """**File**: {filename}
**Language**: {language}
**Line {line_number}**:
```{language}
{line_code}
```

**Context** (surrounding code):
```{language}
{context_before}
>>> {line_code}  # LINE TO EXPLAIN
{context_after}
```

Provide a structured explanation with these sections:

## Purpose
[1-2 sentence explanation of what this line accomplishes]

## Token Breakdown
| Token | Type | Meaning |
|-------|------|---------|
[Break down each meaningful token/keyword/symbol]

## Parameters/Arguments
[If applicable, explain each parameter. Skip if not relevant.]

## How It Fits
[Explain relationship to surrounding code - what comes before feeds into this, what this produces for later]

## Learn More
[1-2 related concepts the reader should explore to deepen understanding]

## Diagram
```mermaid
[ONLY if a diagram would genuinely help understanding, provide a small mermaid diagram. Otherwise omit this section entirely.]
```
"""

ARCHITECTURE_SYSTEM = """You are CodeTeacher, analyzing a codebase architecture.
Provide clear, educational explanations with visual diagrams.
Focus on the high-level structure and how components interact."""

ARCHITECTURE_TEMPLATE = """Analyze this codebase structure:

**Files**:
{file_tree}

**Key Files Content**:
{key_files_content}

Provide:
## Overview
[What does this project do? 2-3 sentences]

## Entry Points
[Where does execution start? List main entry files]

## Core Components
[Main modules/classes and their responsibilities]

## Data Flow
[How data moves through the system]

## Architecture Diagram
```mermaid
graph TD
[Create a diagram showing component relationships]
```

## Key Dependencies
[Important external libraries and what they're used for]
"""

CHAT_SYSTEM = """You are CodeTeacher, helping a user understand code.
You have access to the current file context they're viewing.
Be helpful, educational, and concise.
If they ask about specific code, reference line numbers.
Use code blocks with syntax highlighting when showing code."""

# ============ Architecture Agent Prompts ============

ARCH_IDENTIFY_SYSTEM = """You are a software architect analyzing a project structure.
Select the most architecturally significant files to understand this codebase.
Respond ONLY with valid JSON, no markdown formatting."""

ARCH_IDENTIFY_TEMPLATE = """Analyze this project to identify the most important files for understanding its architecture.

**Framework Hints**: {framework_hints}
**Language Distribution**: {language_counts}
**Total Files**: {total_files}

**File Tree**:
{file_tree}

**Config Files Content**:
{config_content}

Select 8-15 files that are most important for understanding the architecture. Prioritize:
- Entry points and main application files
- Route/controller definitions
- Core service/business logic
- Data models and schemas
- Configuration files that define structure

Respond with JSON:
{{"files": [{{"path": "relative/path/to/file", "reason": "brief reason"}}]}}"""

ARCH_ANALYZE_SYSTEM = """You are a software architect performing deep analysis of a codebase.
Analyze component relationships, patterns, and data flow.
Respond ONLY with valid JSON, no markdown formatting."""

ARCH_ANALYZE_TEMPLATE = """Analyze these key files from a {framework} project.

**Files and Their Imports**:
{files_with_imports}

**File Contents**:
{file_contents}

Produce a structured analysis as JSON:
{{
  "components": [
    {{"path": "file/path", "role": "one sentence describing this component's responsibility", "dependencies": ["paths it imports from within the project"]}}
  ],
  "patterns": ["list of architectural patterns detected, e.g. MVC, layered architecture, event-driven"],
  "data_flow": "Description of how data moves through the system (2-3 sentences)",
  "entry_points": ["list of entry point files"]
}}"""

ARCH_SYNTHESIZE_SYSTEM = """You are CodeTeacher, creating an educational architecture overview.
Produce clear, visual explanations that help developers understand the codebase.
Use Mermaid diagrams to illustrate relationships."""

ARCH_SYNTHESIZE_TEMPLATE = """Create an educational architecture overview based on this analysis.

**Project Framework**: {framework}
**Analysis Data**:
{analysis_json}

Produce TWO sections separated by `---CONTEXT_BLOCK---`:

SECTION 1 - Full educational overview in Markdown:
## Overview
[What does this project do and what technology does it use? 2-3 sentences]

## Architecture
[Describe the architectural pattern and why it's used]

## Core Components
[For each key component: what it does and how it connects to others]

## Architecture Diagram
```mermaid
graph TD
[Create a clear diagram showing component relationships with labeled edges]
```

## Data Flow
[How data moves through the system, from user input to response]

## Data Flow Diagram
```mermaid
sequenceDiagram
[Create a sequence diagram showing a typical request flow]
```

## Key Patterns & Concepts
[Educational explanation of patterns used — help the reader learn system design]

## Key Dependencies
[Important external libraries and their roles]

---CONTEXT_BLOCK---

SECTION 2 - Condensed context summary (under 500 words) for injecting into future prompts:
[Project name/type, framework, architectural pattern, list each component with its role and key files, how they connect. Dense, factual, no formatting.]"""

LINE_EXPLAIN_CONTEXT_PREFIX = """**Project Architecture Context:**
{context_block}

---

"""

FILE_CONTEXT_PREFIX = """**Architecture Context for This File:**
{file_context}

Use this context to explain how the selected code connects to the broader codebase. Reference specific components when relevant.

---

"""

# --- File Summary Prompts ---

FILE_SUMMARY_SYSTEM = """You are CodeTeacher, an expert at explaining code to students learning software development. Generate a clear, educational file summary that helps a student understand what this file does, why it exists, and how it connects to the rest of the project."""

FILE_SUMMARY_TEMPLATE = """Analyze this file from a {framework} project and provide a student-friendly summary.

**File**: `{file_path}`
**Language**: {language}
**Lines**: {line_count}

{arch_context}

**File content**:
```{language}
{content}
```

Write a clear summary with these sections:

## Purpose
What does this file do? Why does it exist in this project? (2-3 sentences)

## Role in Architecture
How does this file fit into the overall project? What layer/pattern does it belong to?

## Key Components
List the main functions, classes, or exports with one-line descriptions.

## Connections
What does this file depend on? What depends on it? How does data flow through it?

## What to Learn Here
What programming concepts or patterns can a student learn from studying this file?
"""

FILE_SUMMARY_CONTEXT_PREFIX = """**File Summary Context:**
{file_summary}

---

"""
