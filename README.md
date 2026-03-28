# CodeTeacher

An AI-powered educational tool that helps students learn and understand code through automatic repository analysis, file summaries, interactive line-by-line explanations, and contextual chat.

![Python](https://img.shields.io/badge/Python-3.10--3.13-green) ![React](https://img.shields.io/badge/React-18+-61dafb) ![TypeScript](https://img.shields.io/badge/TypeScript-5+-3178c6) ![Tests](https://img.shields.io/badge/Tests-141%20passing-brightgreen) ![License](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey)

## Features

### Three-Tier Context System

CodeTeacher automatically orients to your codebase at every level:

**Tier 1 - Repository Overview**: Load a repo and CodeTeacher immediately analyzes it using a 4-phase agentic process (structure scan, key file identification, deep analysis, synthesis). Shows languages, frameworks, component relationships, architecture diagrams, and design patterns. Cached to disk so subsequent loads are instant.

**Tier 2 - File Summary**: Click any file to get an AI-generated educational summary: purpose, role in architecture, key components, connections to other files, and concepts to learn. Clickable import/export badges let you navigate between connected files.

**Tier 3 - Line Explanation**: Click any line (or drag to select a range) for a detailed explanation enriched with both repo-level and file-level context. Includes token breakdown, parameters, how it fits in the codebase, related concepts, and Mermaid diagrams.

Breadcrumb navigation (`repo > file > line`) lets you move between tiers.

### Core Functionality

- **Auto-Analysis on Load**: Architecture analysis starts automatically when you open a repo. No buttons to find.
- **Persistent Analysis Cache**: Analysis stored to `C:\CodeTeacher\` (Windows) or `~/.codeteacher/` (Linux/Mac). Survives server restarts.
- **Multi-Line Range Explanation**: Click and drag to select multiple lines for combined explanations.
- **Interactive Chat**: Context-aware conversations about the code you're viewing. Quick action buttons for common tasks.
- **Folder Browser**: Navigate and select repositories visually instead of typing paths.
- **On-Demand Deep Analysis**: For files not in the initial analysis set, a "Deep analyze" button adds them to the architecture index with one LLM call.
- **Cache Staleness Detection**: Warns when analyzed files have been modified since the last analysis.

### AI Models

Choose from 4 pre-configured frontier models via [OpenRouter](https://openrouter.ai):

- **Claude Opus 4.6** (default) - Anthropic's strongest model, 1M context
- **GPT-5.4** - OpenAI with medium reasoning effort, 1M context
- **Gemini 3.1 Pro** - Google's flagship with thinking support, 1M context
- **Gemini 3.0 Flash** - High-speed for quick explanations, 1M context

Add any OpenRouter-compatible model through Settings.

### Visual Design

"Code Observatory" aesthetic with Bricolage Grotesque + DM Sans typography, warm amber accents on cool blue-dark backgrounds, dot-grid textures, smooth tier transitions, and animated phase tracking.

## Architecture

```
Frontend (React 18 / TypeScript / Vite)     Backend (FastAPI / Python 3.10-3.13)
├── App.tsx (root, Allotment split)          ├── main.py (entry, CORS, static)
├── components/                               ├── routers/
│   ├── context/                             │   ├── repos.py   (load, browse)
│   │   ├── ContextPanel.tsx (3-tier)        │   ├── files.py   (content, tree)
│   │   ├── RepoOverview.tsx (tier 1)        │   ├── explain.py (explain, WS)
│   │   ├── FileSummary.tsx  (tier 2)        │   └── chat.py    (chat stream)
│   │   └── LineExplanation.tsx (tier 3)     ├── services/
│   ├── architecture/PhaseTracker.tsx        │   ├── openrouter.py (AI + prompts)
│   ├── chat/ChatBox.tsx                     │   ├── architecture_agent.py (4-phase)
│   ├── code/CodeEditor.tsx                  │   ├── architecture_store.py (memory+disk)
│   └── layout/Header.tsx                    │   ├── persistent_store.py (disk cache)
├── hooks/useArchitectureAnalysis.ts         │   ├── repo_manager.py (Git/local)
├── store/codeStore.ts (Zustand)             │   ├── code_parser.py (imports)
├── services/api.ts (REST + WebSocket)       │   └── explanation_cache.py (LRU)
└── styles/theme.css (Code Observatory)      └── models/schemas.py (Pydantic)
```

## Quick Start

### Option A: Standalone Executable (Windows, no setup)

1. Download the latest `CodeTeacher.zip` from [Releases](https://github.com/alexs42/CodeTeacher/releases)
2. Extract and double-click `CodeTeacher.exe`
3. Browser opens automatically — paste your [OpenRouter API key](https://openrouter.ai/keys) and go

No Python or Node.js required.

### Option B: From Source (all platforms)

**Prerequisites:** Python 3.10-3.13 (not 3.14+), Node.js 18+, [OpenRouter API Key](https://openrouter.ai/keys)

```bash
git clone https://github.com/alexs42/CodeTeacher.git
cd CodeTeacher
```

**Linux / macOS:** `./start.sh`
**Windows:** `start.bat`

This sets up venvs, installs deps, and starts both servers. Open `http://localhost:5173`.

| | Linux / macOS | Windows |
|---|---|---|
| Both servers | `./start.sh` | `start.bat` |
| Backend only | `./start-backend.sh` | `start-backend.bat` |
| Frontend only | `./start-frontend.sh` | `start-frontend.bat` |
| Verify project | `./verify-project.sh` | `verify-project.bat` |

### First-Time Setup

1. Enter your [OpenRouter API key](https://openrouter.ai/keys) (required, stored locally in browser)
2. Select an AI model (optional, defaults to Claude Opus 4.6)
3. Optionally add a GitHub token for private repos
4. Click **Get Started**

## Usage

### Loading a Repository

Click "Open Repository" in the header. Either type a path / GitHub URL, or click the browse button to navigate folders visually. Once loaded, the right panel immediately begins architecture analysis (or loads cached results instantly).

### Three-Tier Navigation

- **Repo loaded, no file selected** → Repository Overview with architecture analysis, mermaid diagrams, clickable component list
- **File selected, no line clicked** → File Summary with purpose, connections, key components
- **Line or range selected** → Line Explanation with full repo+file context

Click breadcrumbs (`repo > file > line`) to navigate back up.

### Chat

Expand the chat panel at the bottom. Quick actions: "Analyze architecture", "Create diagram", "Explain with examples", "Find potential bugs", "Summarize file". Or type custom questions.

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/repos/browse` | GET | Browse filesystem directories |
| `/api/repos/load` | POST | Load repository (returns `has_cached_analysis`) |
| `/api/files/content` | GET | Get file content with language detection |
| `/api/explain/architecture-content/{repo_id}` | GET | Get cached architecture overview |
| `/api/explain/architecture-status/{repo_id}` | GET | Check analysis existence + staleness |
| `/api/explain/file-context/{repo_id}` | GET | File-specific architecture context |
| `/api/explain/file-summary/{repo_id}` | GET | Cached file summary |
| `/api/explain/line` | POST | Explain single line |
| `/api/explain/range` | POST | Explain code range |
| `/api/explain/stream` | WS | Streaming (line, range, architecture_agent, file_summary, analyze_file) |
| `/api/chat/stream` | WS | Streaming chat responses |

Swagger UI at `http://localhost:8000/docs` when backend is running.

## Persistent Storage

Analysis is cached to disk so it survives server restarts:

- **Windows:** `C:\CodeTeacher\repos\<hash>\`
- **Linux/Mac:** `~/.codeteacher/repos/<hash>\`

Each repo directory contains `architecture.json`, `architecture_display.md`, `meta.json`, and `file_summaries/`. File summaries are invalidated when the file content changes (tracked by MD5 hash).

## Development

### Testing

**Backend (141 tests):**
```bash
cd backend && pytest -q
```

| Suite | Tests | Coverage |
|-------|-------|----------|
| test_repos.py | 13 | Repository API + browse + cache |
| test_files.py | 7 | File operations |
| test_services.py | 33 | ArchitectureStore, RepoManager, CodeParser, Cache |
| test_schemas.py | 28 | Pydantic schema validation |
| test_openrouter_service.py | 21 | OpenRouter, reasoning, payloads |
| test_explain_router.py | 14 | Explain endpoints + WebSocket |
| test_chat_router.py | 9 | Chat endpoints |
| test_persistent_store.py | 16 | Disk persistence, path hashing |

**Frontend (21 unit tests):**
```bash
cd frontend && npx vitest run
```

**E2E (Playwright):**
```bash
npx playwright test
```

**Type checking:**
```bash
cd frontend && npx tsc --noEmit
```

### Building Standalone Executable

```cmd
build.bat
```

Builds frontend, bundles backend + frontend into PyInstaller `--onedir` package. Output: `dist/CodeTeacher/CodeTeacher.exe`. The build script auto-detects Python 3.10-3.13 via the `py` launcher and handles Dropbox file locks with retries.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "API key is required" | Enter OpenRouter key in setup modal or settings |
| Backend connection error | Check port 8000 is free, backend is running |
| Python 3.14+ build failure | Install Python 3.12 or 3.13 alongside 3.14 |
| Dropbox locks `dist/` during build | Pause Dropbox sync or move project outside Dropbox |
| Slow explanations | Switch to Gemini 3.0 Flash for speed |
| "Model not found" | Verify model ID at [OpenRouter Models](https://openrouter.ai/models) |

## Configuration

### Environment Variables (optional)

Create `backend/.env`:
```env
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
CACHE_MAX_SIZE=1000
CACHE_TTL_MINUTES=60
```

### Model Configuration

Edit `frontend/src/config/models.ts` to add pre-configured models. For reasoning models, also add the ID to `REASONING_MODELS` in `backend/services/openrouter.py`.

### Storage

- **API keys**: Browser localStorage only (never sent to our servers)
- **Model preferences**: Browser localStorage
- **Architecture analysis**: Disk cache (`C:\CodeTeacher\` or `~/.codeteacher/`)
- **File summaries**: Disk cache (per-repo, invalidated by content hash)
- **Explanation cache**: In-memory (cleared on restart)
- **Chat history**: Session only (cleared on refresh)

## Security & Privacy

- API keys stored locally in your browser only
- No data sent to our servers — all communication is direct to OpenRouter
- Code only leaves your machine when sent to OpenRouter for explanation
- Analysis cache stored locally on your filesystem
- Open source — audit the code yourself

## License

This project is licensed under the **Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0)**.

You are free to use, share, and adapt this software for non-commercial purposes. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [OpenRouter](https://openrouter.ai) for unified AI model access
- [Anthropic](https://anthropic.com) for Claude models
- [Monaco Editor](https://microsoft.github.io/monaco-editor/) for the code editor
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework

---

*CodeTeacher - Learn code, one line at a time.*
