# BioCodeTeacher

**v0.45** — An AI-powered educational tool that helps graduate students and postdocs understand bioinformatics code — not just *what* it does, but *why* it matters biologically. Provides deep, context-aware explanations for single-cell RNA-seq (Scanpy, Seurat), spatial transcriptomics (Squidpy, BANKSY), and digital pathology (OpenSlide, CLAM, PathML) codebases.

![Python](https://img.shields.io/badge/Python-3.10--3.13-green) ![React](https://img.shields.io/badge/React-18+-61dafb) ![TypeScript](https://img.shields.io/badge/TypeScript-5+-3178c6) ![Tests](https://img.shields.io/badge/Tests-179%20passing-brightgreen) ![License](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey)

Freely distributed for non-commercial use under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). No warranty expressed or implied.

## Why BioCodeTeacher?

Students can *run* tutorial code but can't *adapt* it to their own data. They copy-paste from Scanpy/Seurat tutorials, tweak parameters blindly, and don't understand the statistical or biological reasoning behind each step.

A generic code explainer says:
> "Calls `normalize_total` on `adata` with `target_sum` parameter..."

BioCodeTeacher says:
> "CPM normalization — scales each cell's counts so they sum to 10,000, making cells comparable despite different sequencing depths. This compensates for the fact that some cells are captured with more mRNA molecules than others. The `1e4` value is conventional; the exact number doesn't matter because you'll log-transform next..."

Every explanation includes biological motivation, data structure changes (AnnData slots, Seurat assays), parameter guidance with sensible ranges, pipeline position, common mistakes, and cross-tool equivalents (Scanpy ↔ Seurat).

## Features

### Three-Tier Context System

**Tier 1 — Repository Overview**: Load a repo and BioCodeTeacher analyzes it using a 4-phase agentic process (structure scan, key file identification, deep analysis, synthesis). Identifies analysis pipeline stages, frameworks (Snakemake, Nextflow, nf-core), data formats, and biological decision points. Cached to disk for instant subsequent loads.

**Tier 2 — File Summary**: Click any file for an AI-generated educational summary: which pipeline stage it implements, what data objects it consumes/produces, key biological decisions encoded in parameters, and connections to upstream/downstream analysis steps.

**Tier 3 — Line Explanation**: Click any line (or drag to select a range) for a detailed explanation with:
- **Biological Significance** — why this step matters biologically
- **Data State** — what changed in the AnnData/Seurat object
- **Parameter Guide** — what each parameter controls, sensible ranges, behavior at extremes
- **Pipeline Position** — where this falls in the canonical pipeline (QC → normalization → HVG → PCA → integration → clustering → annotation → DE → trajectory)
- **Common Mistakes** — bioinformatics-specific gotchas
- **Cross-Tool Reference** — equivalent in the other ecosystem (Scanpy ↔ Seurat)

Breadcrumb navigation (`repo > file > line`) lets you move between tiers.

### Bioinformatics-Aware Analysis

- **Pipeline detection**: Recognizes Snakemake, Nextflow, nf-core, CWL, Cell Ranger, and R targets workflows
- **Framework recognition**: scverse ecosystem (Scanpy, AnnData, scVI), Seurat/Bioconductor, spatial tools (Squidpy, BANKSY), pathology tools (CLAM, PathML)
- **30+ file formats**: .h5ad (AnnData), .rds (Seurat), .fasta, .fastq, .vcf, .gff/.gtf, .sam, .bed, .smk, .nf, .cwl, .wdl, .ipynb, .Rmd, .svs, and more
- **Directory patterns**: Automatically identifies `workflows/`, `rules/`, `notebooks/`, `analysis/`, `pipelines/` structures

### Core Functionality

- **Splash Screen**: Shows version, changelog, and license on launch. Press SPACE twice to dismiss.
- **Auto-Analysis on Load**: Architecture analysis starts automatically when you open a repo
- **Persistent Analysis Cache**: Analysis stored to `C:\BioCodeTeacher\` (Windows) or `~/.biocodeteacher/` (Linux/Mac). Survives server restarts.
- **Multi-Line Range Explanation**: Click and drag to select multiple lines for combined explanations
- **Interactive Chat**: Context-aware bioinformatics conversations enriched with repo architecture, file summaries, and live API documentation. Quick action buttons for common tasks.
- **Folder Browser**: Navigate and select repositories visually instead of typing paths
- **On-Demand Deep Analysis**: For files not in the initial analysis set, a "Deep analyze" button adds them to the architecture index with one LLM call
- **Cache Staleness Detection**: Warns when analyzed files have been modified since the last analysis

### AI Models

Choose from 7 pre-configured frontier models via [OpenRouter](https://openrouter.ai):

- **Claude Opus 4.6** (default) — Anthropic's strongest model, 1M context
- **Claude Sonnet 4.6** — Fast and capable, 200K context
- **GPT-5.4** — OpenAI with medium reasoning effort, 1M context
- **GPT-5.4 Azure ZDR** — GPT-5.4 via Azure with zero data retention
- **GLM-5 Turbo** — High-speed, competitive performance
- **Gemini 3.1 Pro** — Google's flagship with thinking support, 1M context
- **Gemini 3.0 Flash** — High-speed for quick explanations, 1M context

Add any OpenRouter-compatible model through Settings.

### Visual Design

"Research Lab" aesthetic inspired by fluorescence microscopy — teal/cyan primary (GFP channel), indigo accent (DAPI channel), and amber warnings (PE channel) on deep dark backgrounds. Instrument Sans + Plus Jakarta Sans typography. Microscope icon wordmark with ambient glow effects. Supports dark and light modes.

## Architecture

```
Frontend (React 18 / TypeScript / Vite)     Backend (FastAPI / Python 3.10-3.13)
├── App.tsx (root, Allotment split)          ├── main.py (entry, CORS, static)
├── components/                               ├── routers/
│   ├── splash/SplashScreen.tsx              │   ├── repos.py   (load, browse)
│   ├── context/                             │   ├── files.py   (content, tree)
│   │   ├── ContextPanel.tsx (3-tier)        │   ├── explain.py (explain, WS)
│   │   ├── RepoOverview.tsx (tier 1)        │   └── chat.py    (chat stream)
│   │   ├── FileSummary.tsx  (tier 2)        ├── services/
│   │   └── LineExplanation.tsx (tier 3)     │   ├── openrouter.py (AI + bio prompts)
│   ├── architecture/PhaseTracker.tsx        │   ├── architecture_agent.py (4-phase)
│   ├── chat/ChatBox.tsx                     │   ├── architecture_store.py (memory+disk)
│   ├── code/CodeEditor.tsx                  │   ├── persistent_store.py (disk cache)
│   └── layout/Header.tsx                    │   ├── doc_search.py (API doc fetcher)
├── hooks/useArchitectureAnalysis.ts         │   ├── repo_manager.py (Git/local)
├── store/codeStore.ts (Zustand)             │   ├── code_parser.py (imports)
├── config/version.ts (version + changelog)  │   └── explanation_cache.py (LRU)
├── services/api.ts (REST + WebSocket)       └── models/schemas.py (Pydantic)
└── styles/theme.css (Research Lab theme)
```

## Quick Start

### Option A: Standalone Application (no setup)

**Windows:**
1. Download the latest `BioCodeTeacher.zip` from [Releases](https://github.com/alexs42/BioCodeTeacher/releases)
2. Extract and double-click `BioCodeTeacher.exe`
3. Browser opens automatically — paste your [OpenRouter API key](https://openrouter.ai/keys) and go

**macOS:**
1. Download `BioCodeTeacher.dmg` from [Releases](https://github.com/alexs42/BioCodeTeacher/releases)
2. Open the DMG and drag BioCodeTeacher to Applications
3. Right-click > Open on first launch (unsigned app — bypasses Gatekeeper)
4. Browser opens automatically — paste your [OpenRouter API key](https://openrouter.ai/keys) and go

No Python or Node.js required on either platform.

### Option B: From Source (all platforms)

**Prerequisites:** Python 3.10–3.13 (not 3.14+), Node.js 18+, [OpenRouter API Key](https://openrouter.ai/keys)

```bash
git clone https://github.com/alexs42/BioCodeTeacher.git
cd BioCodeTeacher
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

BioCodeTeacher works best with bioinformatics codebases — Scanpy/Seurat analysis scripts, Snakemake/Nextflow pipelines, Jupyter notebooks with single-cell workflows, or digital pathology projects — but it can explain any codebase.

### Three-Tier Navigation

- **Repo loaded, no file selected** → Repository Overview with pipeline stages, framework detection, architecture diagrams
- **File selected, no line clicked** → File Summary with pipeline role, data flow, biological decisions, learning objectives
- **Line or range selected** → Line Explanation with biological significance, data state changes, parameter guides, cross-tool references

Click breadcrumbs (`repo > file > line`) to navigate back up.

### Chat

The chat panel is open and ready at the bottom — no expand click needed. The chat assistant has deep knowledge of single-cell analysis, spatial transcriptomics, and digital pathology. Chat is enriched with 4 tiers of context: (1) file-specific architecture role, (2) project-level context block, (3) cached file summaries, and (4) live API documentation fetched from ReadTheDocs for referenced functions. Educational prompt suggestions get you started immediately:

- **Teach me this repo** — architecture walkthrough with pros/cons
- **Critique this code** — review with concrete improvement suggestions
- **Tutorial mode** — step-by-step file walkthrough
- **Analyze architecture** — trigger the 4-phase agentic analysis
- **Explain with examples** — concrete usage examples
- **Find potential bugs** — code review for issues
- **Create diagram** — generate Mermaid diagrams

Or ask domain-specific questions like "Why use Leiden over Louvain?" or "What resolution should I use for clustering?"

## Building

### macOS

```bash
./build.sh
# Output: dist/BioCodeTeacher.app + dist/BioCodeTeacher.dmg
```

Builds frontend, creates Python venv, runs PyInstaller to produce a `.app` bundle, then wraps it in a `.dmg` with an Applications shortcut for drag-and-drop install. No code signing — first launch requires right-click > Open to bypass Gatekeeper.

### Windows

```cmd
build.bat
REM Output: dist\BioCodeTeacher\BioCodeTeacher.exe
```

Uses the `py` launcher to find Python 3.10–3.13, builds frontend, bundles with PyInstaller. Includes retry loops for Dropbox file locks.

Both platforms use `biocodeteacher.spec` — a cross-platform PyInstaller spec with `platform.system()` detection. UPX compression is disabled on macOS (breaks Gatekeeper).

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/repos/browse` | GET | Browse filesystem directories |
| `/api/repos/load` | POST | Load repository (returns `has_cached_analysis`) |
| `/api/files/content` | GET | Get file content with language detection |
| `/api/files/tree` | GET | Get repository file tree |
| `/api/explain/line` | POST | Explain single line |
| `/api/explain/range` | POST | Explain code range |
| `/api/explain/architecture-content/{repo_id}` | GET | Get cached architecture overview |
| `/api/explain/architecture-status/{repo_id}` | GET | Check analysis existence + staleness |
| `/api/explain/file-context/{repo_id}` | GET | File-specific architecture context |
| `/api/explain/file-summary/{repo_id}` | GET | Cached file summary |
| `/api/explain/stream` | WS | Streaming (line, range, architecture_agent, file_summary, analyze_file) |
| `/api/chat/stream` | WS | Streaming chat responses |

Swagger UI at `http://localhost:8000/docs` when backend is running.

## Persistent Storage

Analysis is cached to disk so it survives server restarts:

- **Windows:** `C:\BioCodeTeacher\repos\<hash>\`
- **Linux/Mac:** `~/.biocodeteacher/repos/<hash>/`

Each repo directory contains `architecture.json`, `architecture_display.md`, `meta.json`, and `file_summaries/`. File summaries are invalidated when the file content changes.

## Development

### Testing

**Backend (179 tests):**
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
| test_chat_router.py | 15 | Chat endpoints + context injection |
| test_persistent_store.py | 16 | Disk persistence, path hashing |
| test_doc_search.py | 32 | Doc search: library detection, HTML extraction, caching |

**Frontend (31 unit tests):**
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

## Versioning

Version is tracked in `frontend/src/config/version.ts`. The splash screen displays the current version on every launch.

- Increment **0.01** for small changes (bug fixes, minor UI tweaks)
- Increment **0.1** for big changes (new features, major refactors)
- Update `APP_VERSION` and `CHANGELOG` before each build

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "API key is required" | Enter OpenRouter key in setup modal or settings |
| Backend connection error | Check port 8000 is free, backend is running |
| Python 3.14+ build failure | Install Python 3.12 or 3.13 alongside 3.14 |
| Dropbox locks `dist/` during build | Pause Dropbox sync or move project outside Dropbox |
| macOS "app is damaged" | Right-click > Open to bypass Gatekeeper |
| Slow explanations | Switch to Gemini 3.0 Flash for speed |
| "Model not found" | Verify model ID at [OpenRouter Models](https://openrouter.ai/models) |

## Configuration

### Model Configuration

Edit `frontend/src/config/models.ts` to add pre-configured models. For reasoning models, also add the ID to `REASONING_MODELS` in `backend/services/openrouter.py`.

### Storage

- **API keys**: Browser localStorage only (never sent to our servers)
- **Model preferences**: Browser localStorage
- **Architecture analysis**: Disk cache (`C:\BioCodeTeacher\` or `~/.biocodeteacher/`)
- **File summaries**: Disk cache (per-repo, invalidated by file path hash)
- **Documentation cache**: Disk cache (global `doc_cache/`, 24h TTL per entry)
- **Explanation cache**: In-memory (cleared on restart)
- **Chat history**: Session only (cleared on refresh)

## Security & Privacy

- API keys stored locally in your browser only
- No data sent to our servers — all communication is direct to OpenRouter
- Code only leaves your machine when sent to OpenRouter for explanation
- Analysis cache stored locally on your filesystem
- Open source — audit the code yourself

## Origin

BioCodeTeacher is a specialized fork of [CodeTeacher](https://github.com/alexs42/CodeTeacher), rewritten with domain-aware prompts, bioinformatics framework detection, extended file format support, and a research-inspired visual theme. The core engine (FastAPI streaming, Monaco editor, three-tier context, persistent storage) is shared; everything user-facing is specialized for computational biology education.

## License

This project is licensed under the **Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0)**.

You are free to use, share, and adapt this software for non-commercial purposes. This software is provided "as is" without warranty of any kind. No license beyond CC BY-NC 4.0 is provided or implied. See the [LICENSE](LICENSE) file for full terms and disclaimer.

## Acknowledgments

- [OpenRouter](https://openrouter.ai) for unified AI model access
- [Anthropic](https://anthropic.com) for Claude models
- [Monaco Editor](https://microsoft.github.io/monaco-editor/) for the code editor
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- The [scverse](https://scverse.org/) community for the single-cell analysis ecosystem
- [Seurat](https://satijalab.org/seurat/) / [Bioconductor](https://bioconductor.org/) for the R single-cell ecosystem

---

*BioCodeTeacher — understand the biology behind the code.*
