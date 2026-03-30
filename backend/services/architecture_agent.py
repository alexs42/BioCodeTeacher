"""
Multi-phase architecture analysis agent.
Examines a repository in 4 phases to produce a comprehensive understanding.
"""

import json
import re
from datetime import datetime, timezone
from dataclasses import dataclass, field
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional, Tuple

from services.openrouter import (
    OpenRouterService,
    ARCH_IDENTIFY_SYSTEM,
    ARCH_IDENTIFY_TEMPLATE,
    ARCH_ANALYZE_SYSTEM,
    ARCH_ANALYZE_TEMPLATE,
    ARCH_SYNTHESIZE_SYSTEM,
    ARCH_SYNTHESIZE_TEMPLATE,
)
from services.repo_manager import repo_manager
from services.code_parser import code_parser
from services.architecture_store import architecture_store
from models.schemas import ArchitectureContextSummary, ComponentInfo


# Framework detection: filename -> framework name
FRAMEWORK_SIGNATURES = {
    # -- Web / general software frameworks --
    "manage.py": "Django",
    "wsgi.py": "Django",
    "asgi.py": "Django/ASGI",
    "app.py": "Flask/FastAPI",
    "main.py": "Python Application",
    "next.config.js": "Next.js",
    "next.config.ts": "Next.js",
    "next.config.mjs": "Next.js",
    "nuxt.config.ts": "Nuxt.js",
    "nuxt.config.js": "Nuxt.js",
    "angular.json": "Angular",
    "svelte.config.js": "SvelteKit",
    "remix.config.js": "Remix",
    "gatsby-config.js": "Gatsby",
    "vite.config.ts": "Vite",
    "vite.config.js": "Vite",
    "webpack.config.js": "Webpack",
    "Cargo.toml": "Rust",
    "go.mod": "Go",
    "pom.xml": "Java/Maven",
    "build.gradle": "Java/Gradle",
    "build.gradle.kts": "Kotlin/Gradle",
    "Gemfile": "Ruby/Rails",
    "composer.json": "PHP/Composer",
    "pubspec.yaml": "Dart/Flutter",
    "Package.swift": "Swift",
    "CMakeLists.txt": "C/C++ CMake",
    "Makefile": "Make-based",
    "Dockerfile": "Docker",
    "docker-compose.yml": "Docker Compose",
    "docker-compose.yaml": "Docker Compose",
    # -- Bioinformatics pipeline/workflow frameworks --
    "Snakefile": "Snakemake",
    "snakefile": "Snakemake",
    "nextflow.config": "Nextflow",
    "main.nf": "Nextflow",
    "meta.yml": "nf-core Module",
    "environment.yml": "Conda Environment",
    "conda.yml": "Conda Environment",
    # -- R / Bioconductor --
    "renv.lock": "renv (R)",
    "DESCRIPTION": "R Package",
    ".Rprofile": "R Project",
    "_targets.R": "targets (R pipeline)",
    # -- Jupyter / notebook-driven --
    ".jupyter": "Jupyter",
    # -- Bioinformatics config markers --
    "cellranger-count.sh": "Cell Ranger",
    "spaceranger-count.sh": "Space Ranger",
}

# Config/manifest files to read for context
CONFIG_FILES = [
    "package.json", "pyproject.toml", "requirements.txt", "setup.py", "setup.cfg",
    "Cargo.toml", "go.mod", "pom.xml", "build.gradle", "Gemfile",
    "composer.json", "pubspec.yaml",
    # Bioinformatics-specific config
    "environment.yml", "conda.yml", "Snakefile", "nextflow.config",
    "renv.lock", "DESCRIPTION", "_targets.R",
]

# Significant directory names
SIGNIFICANT_DIRS = {
    # General software
    "src", "lib", "app", "api", "routes", "routers", "controllers",
    "components", "models", "services", "utils", "helpers", "middleware",
    "tests", "test", "specs", "views", "templates", "static", "public",
    "config", "core", "domain", "infrastructure", "handlers", "pages",
    # Bioinformatics-specific
    "workflows", "rules", "pipelines", "analysis", "notebooks", "scripts",
    "data", "results", "figures", "envs", "schemas", "modules", "bin",
    "resources", "references", "annotations", "reports", "qc",
    "preprocessing", "clustering", "integration", "visualization",
    "subworkflows", "processes",
}


@dataclass
class StructureScanResult:
    """Result of Phase 1 — structure scan."""
    language_counts: Dict[str, int] = field(default_factory=dict)
    framework_hints: List[str] = field(default_factory=list)
    config_files: List[str] = field(default_factory=list)
    significant_dirs: List[str] = field(default_factory=list)
    total_files: int = 0


@dataclass
class SelectedFile:
    """A file selected for deep analysis."""
    path: str
    reason: str


@dataclass
class AgentEvent:
    """Progress event yielded by the agent."""
    type: str  # "phase", "chunk", "end", "error"
    phase: Optional[str] = None
    status: Optional[str] = None
    detail: Optional[str] = None
    content: Optional[str] = None
    files_selected: Optional[List[str]] = None
    has_context: bool = False


class ArchitectureAgent:
    """
    Multi-phase architecture analysis agent.
    Yields progress events as it works through analysis.
    """

    def __init__(self, service: OpenRouterService, repo_id: str, repo_path: Path,
                 max_files: int = 15):
        self.service = service
        self.repo_id = repo_id
        self.repo_path = repo_path
        self.max_files = max_files

    async def analyze(self) -> AsyncGenerator[AgentEvent, None]:
        """Run full 4-phase analysis, yielding progress events."""
        try:
            # Phase 1: Structure Scan
            yield AgentEvent(type="phase", phase="structure_scan", status="started",
                             detail="Scanning repository structure...")
            scan_result, file_tree_text = self._phase1_structure_scan()
            yield AgentEvent(type="phase", phase="structure_scan", status="complete",
                             detail=f"Found {scan_result.total_files} files across {len(scan_result.language_counts)} languages. "
                                    f"Detected: {', '.join(scan_result.framework_hints) or 'general project'}.")

            # Phase 2: Key File Identification
            yield AgentEvent(type="phase", phase="key_file_identification", status="started",
                             detail="Identifying architecturally significant files...")
            config_content = self._read_config_files(scan_result.config_files)
            selected_files = await self._phase2_identify_files(
                file_tree_text, scan_result, config_content
            )
            file_paths = [f.path for f in selected_files]
            yield AgentEvent(type="phase", phase="key_file_identification", status="complete",
                             detail=f"Selected {len(selected_files)} key files for analysis.",
                             files_selected=file_paths)

            # Phase 3: Deep File Analysis
            yield AgentEvent(type="phase", phase="deep_analysis", status="started",
                             detail="Analyzing component relationships and patterns...")
            analysis_json = await self._phase3_deep_analysis(
                selected_files, scan_result
            )
            yield AgentEvent(type="phase", phase="deep_analysis", status="complete",
                             detail=f"Identified {len(analysis_json.get('components', []))} components "
                                    f"and {len(analysis_json.get('patterns', []))} patterns.")

            # Phase 4: Synthesis (streaming)
            yield AgentEvent(type="phase", phase="synthesis", status="started",
                             detail="Generating architecture overview...")

            display_analysis = ""
            context_block = ""
            framework = ", ".join(scan_result.framework_hints) or "general"

            async for chunk in self.service.stream_completion(
                prompt=ARCH_SYNTHESIZE_TEMPLATE.format(
                    framework=framework,
                    analysis_json=json.dumps(analysis_json, indent=2),
                ),
                system_prompt=ARCH_SYNTHESIZE_SYSTEM,
                max_tokens=8000,
                temperature=0.5,
            ):
                display_analysis += chunk
                yield AgentEvent(type="chunk", content=chunk)

            # Split display analysis and context block
            if "---CONTEXT_BLOCK---" in display_analysis:
                parts = display_analysis.split("---CONTEXT_BLOCK---", 1)
                display_analysis = parts[0].strip()
                context_block = parts[1].strip()
            else:
                # Fallback: use first 500 words as context
                words = display_analysis.split()
                context_block = " ".join(words[:500])

            # Store the result
            components = []
            for comp in analysis_json.get("components", []):
                components.append(ComponentInfo(
                    path=comp.get("path", ""),
                    role=comp.get("role", ""),
                    dependencies=comp.get("dependencies", []),
                ))

            summary = ArchitectureContextSummary(
                repo_id=self.repo_id,
                overview=analysis_json.get("data_flow", ""),
                components=components,
                patterns=analysis_json.get("patterns", []),
                context_block=context_block,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            architecture_store.save(self.repo_id, summary, display_md=display_analysis)

            yield AgentEvent(type="phase", phase="synthesis", status="complete",
                             detail="Architecture analysis complete.")
            yield AgentEvent(type="end", has_context=True)

        except Exception as e:
            yield AgentEvent(type="error", content=str(e))

    def _phase1_structure_scan(self) -> Tuple[StructureScanResult, str]:
        """Phase 1: Scan structure without LLM. Returns scan result and file tree text."""
        result = StructureScanResult()
        file_tree_text = self._build_tree_text(self.repo_path, "", result)
        return result, file_tree_text

    def _build_tree_text(self, path: Path, prefix: str, result: StructureScanResult,
                         depth: int = 0, max_depth: int = 8) -> str:
        """Recursively build tree text and collect stats."""
        if depth > max_depth:
            return ""

        lines = []
        try:
            entries = sorted(path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
        except PermissionError:
            return ""

        skip_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'env',
                     'dist', 'build', '.next', '.nuxt', 'target', '.idea', '.vscode',
                     'coverage', '.pytest_cache', '.mypy_cache', '.tox', '.eggs'}

        for entry in entries:
            name = entry.name
            if name.startswith('.') and name not in ('.gitignore', '.env.example'):
                continue
            if entry.is_dir() and name in skip_dirs:
                continue

            if entry.is_dir():
                lines.append(f"{prefix}{name}/")
                if name.lower() in SIGNIFICANT_DIRS:
                    result.significant_dirs.append(str(entry.relative_to(self.repo_path)))
                lines.append(self._build_tree_text(entry, prefix + "  ", result, depth + 1, max_depth))
            else:
                lines.append(f"{prefix}{name}")
                result.total_files += 1

                # Detect language
                lang = repo_manager.detect_language(name)
                if lang != "plaintext":
                    result.language_counts[lang] = result.language_counts.get(lang, 0) + 1

                # Detect framework
                if name in FRAMEWORK_SIGNATURES:
                    hint = FRAMEWORK_SIGNATURES[name]
                    if hint not in result.framework_hints:
                        result.framework_hints.append(hint)

                # Track config files
                if name in CONFIG_FILES:
                    rel_path = str(entry.relative_to(self.repo_path))
                    result.config_files.append(rel_path)

        return "\n".join(line for line in lines if line)

    def _read_config_files(self, config_paths: List[str], max_per_file: int = 3000,
                           max_files: int = 5) -> str:
        """Read config file contents for Phase 2 context."""
        parts = []
        for path in config_paths[:max_files]:
            full_path = self.repo_path / path
            try:
                content = full_path.read_text(encoding="utf-8", errors="replace")
                if len(content) > max_per_file:
                    content = content[:max_per_file] + "\n... [truncated]"
                parts.append(f"### {path}\n```\n{content}\n```")
            except Exception:
                continue
        return "\n\n".join(parts) if parts else "No config files found."

    async def _phase2_identify_files(self, file_tree_text: str,
                                      scan_result: StructureScanResult,
                                      config_content: str) -> List[SelectedFile]:
        """Phase 2: Use LLM to identify key files."""
        prompt = ARCH_IDENTIFY_TEMPLATE.format(
            framework_hints=", ".join(scan_result.framework_hints) or "None detected",
            language_counts=json.dumps(scan_result.language_counts),
            total_files=scan_result.total_files,
            file_tree=file_tree_text[:8000],  # Cap tree text
            config_content=config_content,
        )

        response = await self.service.complete(
            prompt=prompt,
            system_prompt=ARCH_IDENTIFY_SYSTEM,
            max_tokens=2000,
            temperature=0.3,
        )

        selected = self._parse_file_selection(response)
        if not selected:
            selected = self._fallback_file_selection(scan_result)

        return selected[:self.max_files]

    def _parse_file_selection(self, response: str) -> List[SelectedFile]:
        """Try to parse LLM JSON response for file selection."""
        # Try direct JSON parse
        try:
            data = json.loads(response)
            return [SelectedFile(path=f["path"], reason=f.get("reason", ""))
                    for f in data.get("files", [])]
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

        # Try extracting from markdown code block
        match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', response, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                return [SelectedFile(path=f["path"], reason=f.get("reason", ""))
                        for f in data.get("files", [])]
            except (json.JSONDecodeError, KeyError, TypeError):
                pass

        return []

    def _fallback_file_selection(self, scan_result: StructureScanResult) -> List[SelectedFile]:
        """Heuristic fallback for file selection when LLM fails."""
        selected = []
        # Walk repo and pick likely-important files
        entry_names = {"main.py", "app.py", "index.js", "index.ts", "main.go", "main.rs",
                       "server.py", "server.js", "server.ts", "App.tsx", "App.jsx"}
        config_names = set(CONFIG_FILES) | {"README.md", "readme.md"}
        # Bioinformatics pipeline files
        pipeline_names = {"Snakefile", "snakefile", "main.nf", "nextflow.config",
                          "_targets.R", "run_pipeline.sh", "run_analysis.py"}
        # Bioinformatics analysis pattern keywords in filenames
        bio_keywords = {"qc", "filter", "normalize", "cluster", "umap", "pca",
                        "de", "differential", "trajectory", "velocity", "integrate",
                        "annotate", "celltype", "spatial", "segment", "pathology",
                        "preprocess", "analysis", "workflow"}

        for path in self.repo_path.rglob("*"):
            if not path.is_file():
                continue
            rel = str(path.relative_to(self.repo_path))
            name = path.name
            stem = path.stem.lower()
            # Skip deep nesting and known dirs
            if any(skip in rel for skip in ['node_modules', '__pycache__', '.git', 'venv', 'dist']):
                continue
            if name in pipeline_names:
                selected.append(SelectedFile(path=rel, reason="Pipeline definition"))
            elif name in entry_names:
                selected.append(SelectedFile(path=rel, reason="Entry point"))
            elif name in config_names:
                selected.append(SelectedFile(path=rel, reason="Configuration"))
            elif name.endswith('.ipynb'):
                selected.append(SelectedFile(path=rel, reason="Analysis notebook"))
            elif name.endswith('.smk'):
                selected.append(SelectedFile(path=rel, reason="Snakemake rule"))
            elif name.endswith('.nf'):
                selected.append(SelectedFile(path=rel, reason="Nextflow process"))
            elif name.endswith('.Rmd') or name.endswith('.qmd'):
                selected.append(SelectedFile(path=rel, reason="Analysis notebook (R)"))
            elif any(kw in stem for kw in bio_keywords):
                selected.append(SelectedFile(path=rel, reason="Analysis step"))
            elif any(d in rel for d in ['workflows/', 'rules/', 'pipelines/']):
                selected.append(SelectedFile(path=rel, reason="Pipeline component"))
            elif any(d in rel for d in ['notebooks/', 'analysis/']):
                selected.append(SelectedFile(path=rel, reason="Analysis"))
            elif any(d in rel for d in ['routers/', 'routes/', 'controllers/', 'handlers/']):
                selected.append(SelectedFile(path=rel, reason="Route handler"))
            elif any(d in rel for d in ['models/', 'schemas/']):
                selected.append(SelectedFile(path=rel, reason="Data model"))
            elif any(d in rel for d in ['services/', 'scripts/']):
                selected.append(SelectedFile(path=rel, reason="Service/Script"))

            if len(selected) >= self.max_files:
                break

        return selected

    async def _phase3_deep_analysis(self, selected_files: List[SelectedFile],
                                     scan_result: StructureScanResult) -> dict:
        """Phase 3: Read files, extract imports, send for deep analysis."""
        files_with_imports = []
        file_contents = []
        total_chars = 0
        char_budget = 30000
        per_file_cap = 4000

        for sf in selected_files:
            full_path = self.repo_path / sf.path
            try:
                content = full_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            # Detect language for import extraction
            lang = repo_manager.detect_language(sf.path)
            imports = code_parser.extract_imports(content, lang)

            files_with_imports.append(f"**{sf.path}** ({lang}): imports {imports}")

            # Truncate content if needed
            if len(content) > per_file_cap:
                half = per_file_cap // 2
                content = content[:half] + "\n\n... [truncated] ...\n\n" + content[-half:]

            if total_chars + len(content) > char_budget:
                # Skip this file if we'd exceed budget
                continue

            total_chars += len(content)
            file_contents.append(f"### {sf.path}\n```{lang}\n{content}\n```")

        framework = ", ".join(scan_result.framework_hints) or "general"
        prompt = ARCH_ANALYZE_TEMPLATE.format(
            framework=framework,
            files_with_imports="\n".join(files_with_imports),
            file_contents="\n\n".join(file_contents),
        )

        response = await self.service.complete(
            prompt=prompt,
            system_prompt=ARCH_ANALYZE_SYSTEM,
            max_tokens=4000,
            temperature=0.3,
        )

        # Parse JSON response
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass

        # Fallback structure
        return {
            "components": [{"path": f.path, "role": f.reason, "dependencies": []}
                           for f in selected_files],
            "patterns": scan_result.framework_hints,
            "data_flow": "Could not determine data flow automatically.",
            "entry_points": [f.path for f in selected_files if "entry" in f.reason.lower()],
        }
