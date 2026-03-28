# CodeTeacher - System in Operation

## Application Interface Layout

```mermaid
graph TB
    subgraph UI["CodeTeacher Application Interface"]
        subgraph Header["🎓 Header Bar"]
            Logo["CodeTeacher Logo"]
            Theme["🌓 Dark/Light Toggle"]
            Settings["⚙️ Settings"]
        end

        subgraph LeftPanel["Left Panel - Code Navigation & Viewing"]
            RepoInfo["📦 Repository: backend/"]
            FileTree["📁 File Tree<br/>├── 📁 routers/<br/>│   ├── 📄 repos.py<br/>│   ├── 📄 files.py<br/>│   ├── 📄 explain.py ⭐<br/>│   └── 📄 chat.py<br/>├── 📁 services/<br/>└── 📄 main.py"]
            Editor["Monaco Editor<br/>━━━━━━━━━━━━━━━━━━━━<br/>1  from fastapi import APIRouter<br/>2  from models.schemas import Line...<br/>3  <br/>42 async def explain_line(request): 👈 SELECTED<br/>43     try:<br/>44         file_data = await repo...<br/>━━━━━━━━━━━━━━━━━━━━"]
        end

        subgraph RightPanel["Right Panel - AI Explanations & Chat (Resizable Split)"]
            ExplainSection["📖 Lines 42-45 Explanation (range mode)<br/>━━━━━━━━━━━━━━━━━━━━<br/><br/>## Overview<br/>Defines async endpoint for explaining code<br/><br/>## Step-by-Step Breakdown<br/>1. Read file content from repo<br/>2. Check explanation cache<br/>3. Extract context around line<br/>4. Send to Claude via OpenRouter<br/><br/>## Key Concepts<br/>- Async/await pattern<br/>- Dependency injection<br/>- Caching strategy<br/><br/>▲ Drag sash to resize ▼"]
            ChatSection["💬 Chat Interface (resizable)<br/>━━━━━━━━━━━━━━━━━━━━<br/>[Analyze architecture] [Create diagram]<br/>[Explain with examples] [Find bugs]<br/><br/>You: What does this function return?<br/><br/>🤖 Assistant: The explain_line function<br/>returns a JSON response containing<br/>the explanation text and a cached flag...<br/>━━━━━━━━━━━━━━━━━━━━<br/>[Analyze architecture] [Create diagram]...<br/>📝 Ask a question..."]
        end
    end

    Header --> LeftPanel
    Header --> RightPanel
    LeftPanel --> RightPanel

    style Editor fill:#1e1e1e,stroke:#007acc,color:#d4d4d4
    style ExplainSection fill:#f6f8fa,stroke:#0366d6
    style ChatSection fill:#fff8e6,stroke:#f9a825
```

## User Interaction Flow

```mermaid
sequenceDiagram
    actor User
    participant UI as Frontend UI
    participant API as FastAPI Backend
    participant Claude as Claude Opus 4.6<br/>(via OpenRouter)
    participant Cache as Explanation Cache

    User->>UI: 1. Load Repository<br/>("./backend" or GitHub URL)
    UI->>API: POST /api/repos/load
    API->>API: Scan directory<br/>Build file tree
    API-->>UI: Repository loaded<br/>File tree + metadata
    UI->>UI: Display file tree

    User->>UI: 2. Click file "explain.py"
    UI->>API: GET /api/files/content
    API-->>UI: File content + language
    UI->>UI: Display in Monaco Editor

    User->>UI: 3. Click line 42 (or drag lines 42-45)
    UI->>API: WebSocket: explain line 42<br/>(or range 42-45)
    API->>Cache: Check cache for line 42
    Cache-->>API: Cache miss

    API->>API: Extract context<br/>(10 lines before/after, or full range)
    API->>Claude: Stream request:<br/>"Explain line 42 (or lines 42-45)"

    Note over Claude: Analyzing code...<br/>Generating explanation...

    Claude-->>API: Stream: "## Purpose\n"
    API-->>UI: WebSocket chunk
    UI->>UI: Append to explanation

    Claude-->>API: Stream: "Defines async function..."
    API-->>UI: WebSocket chunk
    UI->>UI: Append to explanation

    Claude-->>API: Stream: "## Token Breakdown..."
    API-->>UI: WebSocket chunk
    UI->>UI: Render as Markdown

    Claude-->>API: Stream complete
    API->>Cache: Store explanation
    API-->>UI: WebSocket end signal

    User->>UI: 4. Type chat question<br/>"What does this return?"
    UI->>API: WebSocket: chat message
    API->>Claude: Stream chat with context
    Claude-->>API: Stream response
    API-->>UI: WebSocket chunks
    UI->>UI: Display in chat
```

## Example Session: Explaining Python Code

```mermaid
graph LR
    subgraph Step1["Step 1: Repository Loaded"]
        A1["Repository: CodeTeacher/backend<br/>Files: 15 Python files<br/>Status: ✅ Ready"]
    end

    subgraph Step2["Step 2: File Selected"]
        B1["File: routers/explain.py<br/>Language: Python<br/>Lines: 418<br/>Editor: Monaco with syntax highlighting"]
    end

    subgraph Step3["Step 3: Line Clicked"]
        C1["Line 42 Selected:<br/><code>async def explain_line(request):</code><br/>Context: 10 lines before/after<br/>Status: 🔄 Requesting explanation..."]
    end

    subgraph Step4["Step 4: Explanation Streaming"]
        D1["✨ Explanation Appearing:<br/>━━━━━━━━━━━━<br/>Purpose ✅<br/>Token Breakdown ✅<br/>Parameters ✅<br/>Context 🔄<br/>Learn More ⏳<br/>Diagram ⏳"]
    end

    subgraph Step5["Step 5: Complete"]
        E1["📚 Full Explanation Shown<br/>💬 Chat Available<br/>🎨 Mermaid Diagram Rendered<br/>💾 Cached for future use"]
    end

    Step1 --> Step2
    Step2 --> Step3
    Step3 --> Step4
    Step4 --> Step5

    style Step1 fill:#e8f5e9
    style Step2 fill:#e3f2fd
    style Step3 fill:#fff3e0
    style Step4 fill:#fce4ec
    style Step5 fill:#f3e5f5
```

## Architecture Explanation Feature

```mermaid
graph TB
    subgraph UserAction["User Clicks 'Analyze Architecture'"]
        Action["📊 Analyze Repository Structure"]
    end

    subgraph BackendProcess["Backend Processing"]
        Scan["Scan File Tree<br/>15 files detected"]
        KeyFiles["Read Key Files:<br/>✓ main.py<br/>✓ package.json<br/>✓ pyproject.toml"]
        BuildPrompt["Build Analysis Prompt:<br/>File tree + Key file contents"]
    end

    subgraph ClaudeAnalysis["Claude Opus 4.6 Analysis"]
        Overview["Generate Overview:<br/>'FastAPI backend for code education'"]
        Components["Identify Components:<br/>- Routers (API endpoints)<br/>- Services (business logic)<br/>- Models (data schemas)"]
        DataFlow["Map Data Flow:<br/>Request → Router → Service → LLM"]
        Diagram["Create Architecture Diagram:<br/>Component relationships"]
    end

    subgraph Display["Display Results"]
        Markdown["Render Markdown:<br/>## Overview<br/>## Entry Points<br/>## Core Components<br/>## Data Flow"]
        Mermaid["Render Mermaid Diagram:<br/>Visual component map"]
        Interactive["User can ask follow-up<br/>questions in chat"]
    end

    UserAction --> BackendProcess
    BackendProcess --> ClaudeAnalysis
    ClaudeAnalysis --> Display

    style UserAction fill:#bbdefb
    style ClaudeAnalysis fill:#c8e6c9
    style Display fill:#fff9c4
```

## Chat Feature in Action

```mermaid
stateDiagram-v2
    [*] --> Idle: User viewing code

    Idle --> ChatOpen: Click chat header or resize sash

    ChatOpen --> QuickAction: Click quick action button
    ChatOpen --> Typing: User types question
    note right of Typing
        "What does the caching<br/>mechanism do here?"
    end note
    note right of QuickAction
        Quick actions:<br/>- Analyze architecture<br/>- Create diagram<br/>- Explain with examples<br/>- Find potential bugs<br/>- Summarize file
    end note

    QuickAction --> Sending: Auto-send predefined prompt
    Typing --> Sending: Press Enter

    Sending --> Streaming: WebSocket connection
    note right of Streaming
        Context sent to Claude:<br/>- Current file: explain.py<br/>- Selected range: lines 42-45<br/>  (or single line +-5)<br/>- Question text<br/>- Chat history
    end note

    Streaming --> Rendering: Chunks received
    note right of Rendering
        Response streams in real-time:<br/>"The caching mechanism in<br/>explanation_cache.py uses<br/>content hashing to..."
    end note

    Rendering --> Complete: Full response received

    Complete --> ChatOpen: Ready for next question
    Complete --> [*]: Close chat
```

## Visual Theme Comparison

```mermaid
graph LR
    subgraph DarkMode["🌙 Dark Mode - Default"]
        DM1["Background: #1e1e1e<br/>Text: #d4d4d4<br/>Accent: #007acc<br/>Code: VS Code Dark+"]
    end

    subgraph LightMode["☀️ Light Mode"]
        LM1["Background: #ffffff<br/>Text: #24292e<br/>Accent: #0366d6<br/>Code: VS Code Light+"]
    end

    Toggle["🌓 Theme Toggle<br/>Instant Switch<br/>Persisted in localStorage"]

    DarkMode <--> Toggle
    Toggle <--> LightMode

    style DarkMode fill:#1e1e1e,stroke:#007acc,color:#d4d4d4
    style LightMode fill:#ffffff,stroke:#0366d6,color:#24292e
    style Toggle fill:#4a4a4a,stroke:#ffca28,color:#ffffff
```

## Real-Time Streaming Visualization

```mermaid
gantt
    title Code Explanation Timeline (Real-Time Streaming)
    dateFormat SSS
    axisFormat %Lms

    section User Action
    Click line 42           :done, click, 000, 50ms

    section Backend
    Check cache             :done, cache, 050, 30ms
    Extract context         :done, context, 080, 40ms
    Build prompt            :done, prompt, 120, 30ms
    Send to Claude          :done, send, 150, 50ms

    section Claude Processing
    Analyze code            :active, analyze, 200, 800ms
    Generate response       :active, generate, 1000, 2000ms

    section UI Updates
    Show loading            :done, loading, 050, 200ms
    Stream Purpose          :done, p1, 250, 300ms
    Stream Token Breakdown  :done, p2, 550, 500ms
    Stream Context          :done, p3, 1050, 400ms
    Stream Learn More       :done, p4, 1450, 300ms
    Render Diagram          :done, p5, 1750, 500ms
    Complete                :milestone, done, 2250, 0ms
```

---

## Summary

This visualization shows CodeTeacher in operation with:

1. **Split-panel interface** - Code on left, explanations on right (resizable)
2. **Interactive file tree** - Click any file to view
3. **Line-by-line explanations** - Click any line for AI explanation
4. **Multi-line range explanations** - Click and drag to explain code blocks
5. **Real-time streaming** - See explanations appear progressively
6. **Resizable chat panel** - Drag sash to expand chat up to ~2/3 of right panel
7. **Quick action buttons** - One-click prompts for architecture, diagrams, examples, bugs, summaries
8. **Context-aware chat** - Ask follow-up questions with line/range context
9. **Visual diagrams** - Mermaid charts for complex concepts
10. **Architecture analysis** - High-level project understanding
11. **Dark/Light themes** - User preference support

The system provides an educational experience that makes code comprehension accessible through AI-powered explanations optimized for learning.
