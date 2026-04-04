"""
LLM API service supporting OpenRouter, OpenAI, and Anthropic providers.
Supports both streaming and non-streaming responses.
Supports reasoning effort configuration for thinking models.
"""

import json
from typing import AsyncGenerator, Optional
import httpx

DEFAULT_MODEL = "anthropic/claude-opus-4.6"

# Provider API endpoints
PROVIDER_URLS = {
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
    "openai": "https://api.openai.com/v1/chat/completions",
    "anthropic": "https://api.anthropic.com/v1/messages",
}

# Models that support the reasoning.effort parameter (OpenRouter format)
REASONING_MODELS = {
    "openai/gpt-5.4",
    "gpt-5.4",
    "google/gemini-3.1-pro-preview",
}


class OpenRouterService:
    """
    Service for interacting with AI models via OpenRouter, OpenAI, or Anthropic APIs.
    Handles streaming responses for real-time UI updates.
    Supports configurable model selection and reasoning effort.
    """

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        reasoning_effort: Optional[str] = None,
        provider_routing: Optional[dict] = None,
        provider: str = "openrouter",
    ):
        self.api_key = api_key
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.provider_routing = provider_routing
        self.provider = provider
        self.api_url = PROVIDER_URLS.get(provider, PROVIDER_URLS["openrouter"])

        # Build provider-specific headers
        if provider == "anthropic":
            self.headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            }
        elif provider == "openai":
            self.headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
        else:  # openrouter
            self.headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/alexs42/BioCodeTeacher",
                "X-Title": "BioCodeTeacher",
            }

    def _build_payload(self, messages: list, max_tokens: int, temperature: float, stream: bool) -> dict:
        """Build provider-appropriate request payload."""
        if self.provider == "anthropic":
            # Anthropic: system is a top-level param, not a message
            system_text = ""
            user_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system_text = msg["content"]
                else:
                    user_messages.append(msg)
            payload = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": user_messages,
                "stream": stream,
            }
            if system_text:
                payload["system"] = system_text
        else:
            # OpenRouter and OpenAI: identical payload format
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": stream,
            }
            # Reasoning effort (OpenRouter and OpenAI direct)
            if self.reasoning_effort and self.model in REASONING_MODELS:
                payload["reasoning"] = {"effort": self.reasoning_effort}
            # Provider routing (OpenRouter only)
            if self.provider == "openrouter" and self.provider_routing:
                payload["provider"] = self.provider_routing

        return payload

    async def stream_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """Stream a completion, yielding text chunks as they arrive."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = self._build_payload(messages, max_tokens, temperature, stream=True)

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST", self.api_url, headers=self.headers, json=payload,
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise Exception(f"API error ({self.provider}): {response.status_code} - {error_text.decode()}")

                if self.provider == "anthropic":
                    async for chunk in self._parse_anthropic_stream(response):
                        yield chunk
                else:
                    async for chunk in self._parse_openai_stream(response):
                        yield chunk

    async def _parse_openai_stream(self, response) -> AsyncGenerator[str, None]:
        """Parse OpenAI/OpenRouter SSE stream."""
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data = line[6:]
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    if "choices" in chunk and len(chunk["choices"]) > 0:
                        content = chunk["choices"][0].get("delta", {}).get("content", "")
                        if content:
                            yield content
                except json.JSONDecodeError:
                    continue

    async def _parse_anthropic_stream(self, response) -> AsyncGenerator[str, None]:
        """Parse Anthropic SSE stream (event: type / data: json pairs)."""
        event_type = ""
        async for line in response.aiter_lines():
            if line.startswith("event: "):
                event_type = line[7:]
            elif line.startswith("data: "):
                data = line[6:]
                if event_type == "content_block_delta":
                    try:
                        chunk = json.loads(data)
                        text = chunk.get("delta", {}).get("text", "")
                        if text:
                            yield text
                    except json.JSONDecodeError:
                        continue
                elif event_type == "message_stop":
                    break

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """Get a complete (non-streaming) response."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = self._build_payload(messages, max_tokens, temperature, stream=False)

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                self.api_url, headers=self.headers, json=payload,
            )
            if response.status_code != 200:
                raise Exception(f"API error ({self.provider}): {response.status_code} - {response.text}")

            data = response.json()
            if self.provider == "anthropic":
                return data["content"][0]["text"]
            return data["choices"][0]["message"]["content"]

    async def validate_key(self) -> bool:
        """Validate that the API key is working."""
        try:
            await self.complete(
                prompt="Say 'ok' and nothing else.",
                max_tokens=10,
                temperature=0,
            )
            return True
        except Exception:
            return False


# Prompt templates for BioCodeTeacher
LINE_EXPLAIN_SYSTEM = """You are BioCodeTeacher, an expert bioinformatics educator specializing in single-cell genomics, spatial transcriptomics, and computational pathology.

Your students are graduate students and postdocs who can run tutorial code but struggle to adapt it. They need to understand the biological and statistical reasoning behind every step — not just the code mechanics.

When explaining code:
1. ALWAYS lead with the biological or statistical motivation — why this operation exists
2. Explain what happens to the data structure (AnnData slots, Seurat objects, DataFrame columns)
3. Give parameter impact with sensible ranges and what happens at extremes
4. Anticipate the next question the student will have — and answer it proactively
5. Flag common mistakes and misconceptions (e.g., "UMAP distances are NOT meaningful")
6. When relevant, connect to immunology, reproductive biology, or tissue architecture
7. Provide the equivalent in the other ecosystem (Scanpy ↔ Seurat) when applicable

Format responses in Markdown with clear sections. Be educational and precise. Use analogies from biology (cell signaling pathways, immune cascades, tissue organization) to explain computational concepts."""

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
[1-2 sentence explanation of what this line accomplishes — lead with the biological "why"]

## Biological Significance
[Why does this step matter biologically? What biological phenomenon does it address? E.g., normalization compensates for variable capture efficiency across cells; leiden clustering reflects the biological reality that cells exist in discrete transcriptional states. For pathology code, connect to tissue architecture, tumor microenvironment, or diagnostic significance. For immunology-related data, note relevant immune cell biology (T cell exhaustion markers, B cell isotype switching, macrophage polarization, etc.). For reproductive biology, note relevant developmental stages, cell fate decisions, or tissue organization.]

## Data State
[What changed in the data object after this line executes?
- For AnnData: which slots were modified/created (.X, .obs, .var, .obsm, .layers, .uns, .obsp)?
- For Seurat: which assays/reductions/metadata changed?
- For DataFrames/arrays: what shape/type transformations occurred?
- For pathology: what coordinate system or resolution level is being used?
Show before → after when helpful.]

## Parameter Guide
[For each parameter in the line:
- What it controls biologically/statistically
- Sensible range for typical experiments
- What happens at extremes (too high / too low)
- Default value and when to change it
E.g., "resolution=1.0 in leiden — controls cluster granularity. Higher = more clusters. For immune cells, try 0.8-1.5 (they're transcriptionally distinct). For tumor cells, you may need 0.3-0.6 (they're more continuous)."]

## Pipeline Position
[Where does this step fall in the canonical analysis pipeline? What must come before it? What typically follows? Flag if something is out of order.
Standard single-cell pipeline: QC → Normalize → HVG → PCA → Integration → Neighbors → Cluster → UMAP → DE → Annotate → Trajectory]

## Token Breakdown
| Token | Type | Meaning |
|-------|------|---------|
[Break down each meaningful token/keyword/symbol]

## Common Mistakes
[What do students typically get wrong here? E.g., "Running PCA on raw counts instead of log-normalized data", "Using per-cell DE instead of pseudobulk", "Interpreting UMAP distances as biological similarity"]

## Cross-Tool Reference
[If this uses Scanpy/Python, show the Seurat/R equivalent (and vice versa). Include parameter mapping. If not applicable (pure Python/R or non-bio code), omit this section.]

## Learn More
[2-3 concepts the student should explore. Prioritize biological concepts over programming ones. E.g., "Read about the negative binomial distribution underlying scRNA-seq count data" rather than "Learn about Python list comprehensions"]

## Diagram
```mermaid
[ONLY if a diagram would genuinely help understanding — e.g., showing data flow, pipeline stage, or cell state transitions. Otherwise omit this section entirely.]
```
"""

ARCHITECTURE_SYSTEM = """You are BioCodeTeacher, analyzing a bioinformatics codebase.
Identify analysis pipelines (QC → normalization → feature selection → dim reduction → integration → clustering → annotation → DE → trajectory).
Recognize bioinformatics frameworks (Snakemake, Nextflow, CWL), data formats (AnnData/h5ad, Seurat/rds, SingleCellExperiment, SpatialData, loom), and domain-specific patterns (MIL for pathology, spatial statistics, velocity estimation, pseudotime inference).
Provide clear, educational explanations with visual diagrams. Help the student understand not just structure, but the scientific logic behind the pipeline design."""

ARCHITECTURE_TEMPLATE = """Analyze this bioinformatics codebase structure:

**Files**:
{file_tree}

**Key Files Content**:
{key_files_content}

Provide:
## Overview
[What does this project do scientifically? What biological question is it answering? 2-3 sentences. Identify the domain: single-cell, spatial transcriptomics, digital pathology, multi-omics, etc.]

## Analysis Pipeline
[Map the code to the canonical analysis pipeline. Which stages are implemented? What's the data flow from raw input to biological insight? Flag any non-standard or innovative approaches.]

## Entry Points
[Where does execution start? Snakefile, main.nf, Jupyter notebooks, scripts/run.py, etc.]

## Core Components
[Main modules/scripts and their responsibilities. For each, note which pipeline stage it implements and what data formats it consumes/produces.]

## Data Flow
[How data moves through the system — trace the journey from raw reads/counts to biological conclusions. Note format conversions (e.g., 10X → AnnData → h5ad)]

## Architecture Diagram
```mermaid
graph TD
[Create a diagram showing pipeline stages and component relationships, with data formats on edges]
```

## Key Biological Decisions
[Parameters or choices in the code that encode biological assumptions. E.g., "Uses 2000 HVGs — standard for scRNA-seq but may miss rare cell types", "Leiden resolution 0.5 — produces coarse clusters, may merge related subtypes"]

## Key Dependencies
[Bioinformatics libraries and their roles. Note ecosystem (scverse, Bioconductor, etc.)]

## Recommended Learning Path
[Suggest an order for reading the code that builds understanding incrementally — start with data loading, then QC, etc.]
"""

CHAT_SYSTEM = """You are BioCodeTeacher, a bioinformatics research assistant helping graduate students and postdocs understand computational biology code.

You have deep knowledge of:
- Single-cell analysis: Scanpy, Seurat v5, scVI-tools, CellRank, scVelo, CellTypist
- Spatial transcriptomics: Squidpy, SpatialData, BANKSY, Cell2location, Tangram
- Digital pathology: OpenSlide, CLAM, PathML, hover_net, TIAToolbox, foundation models (UNI, CONCH, Virchow)
- Statistics: negative binomial models, batch effect correction, multiple testing, pseudobulk DE, spatial statistics
- Immunology: T/B cell biology, immune cell markers, cytokine signaling, tumor microenvironment
- Reproductive biology: gametogenesis, embryonic development, placental biology, fertility-related single-cell studies

You have access to the current file context they're viewing.

When they ask "why", explain the biological motivation — not just code mechanics.
When they ask "how", show both the code AND the conceptual framework.
Be proactive: anticipate follow-up questions and answer them. If they ask about normalization, also briefly mention why log-transform follows. If they ask about clustering, note that resolution choice is subjective.
Reference line numbers. Use code blocks with syntax highlighting.
Flag common pitfalls proactively: "By the way, if you're planning to do DE after this, remember to use pseudobulk — per-cell DE inflates significance."
When relevant, tie concepts to real biological systems: immune responses, developmental trajectories, tissue architecture.

When a **Project & File Context** block is provided, use it to:
- Connect the student's question to the broader analysis pipeline (QC → normalization → HVG → PCA → integration → clustering → annotation → DE → trajectory)
- Reference the file's role, dependencies, and pipeline stage
- Note how the current code affects downstream analysis steps
- Mention domain-specific considerations (single-cell, spatial, pathology) detected in the project

When a **Current Documentation** block is provided, prefer it over your training data for parameter names, defaults, and API signatures. When no documentation is provided and you cite specific parameter defaults, note that the student should verify against their installed version's docs."""

# ============ Chat Context Templates ============

CHAT_CONTEXT_PREFIX = """**Project & File Context:**
{context_block}

---

"""

CHAT_FILE_SUMMARY_PREFIX = """**File Summary:**
{file_summary}

---

"""

CHAT_DOC_PREFIX = """**Current Documentation:**
{documentation}

---

"""

# ============ Architecture Agent Prompts ============

ARCH_IDENTIFY_SYSTEM = """You are a bioinformatics architect analyzing a computational biology project.
Select the most scientifically and architecturally significant files to understand this codebase.
Prioritize pipeline definition files, analysis notebooks, and scripts that encode key biological decisions.
Respond ONLY with valid JSON, no markdown formatting."""

ARCH_IDENTIFY_TEMPLATE = """Analyze this bioinformatics project to identify the most important files for understanding its analysis pipeline and architecture.

**Framework Hints**: {framework_hints}
**Language Distribution**: {language_counts}
**Total Files**: {total_files}

**File Tree**:
{file_tree}

**Config Files Content**:
{config_content}

Select 8-15 files that are most important for understanding the analysis. Prioritize:
- Pipeline definition files (Snakefile, main.nf, Makefile, workflow scripts)
- Analysis notebooks (Jupyter .ipynb, R Markdown .Rmd) — often the most important files
- Configuration files with biological parameters (e.g., QC thresholds, clustering resolution)
- Data loading/preprocessing scripts
- Entry points and main application files
- Core analysis functions/modules
- Visualization and reporting scripts

Respond with JSON:
{{"files": [{{"path": "relative/path/to/file", "reason": "brief reason including pipeline stage"}}]}}"""

ARCH_ANALYZE_SYSTEM = """You are a bioinformatics architect performing deep analysis of a computational biology codebase.
Analyze pipeline stages, data transformations, biological decisions, and component relationships.
Respond ONLY with valid JSON, no markdown formatting."""

ARCH_ANALYZE_TEMPLATE = """Analyze these key files from a {framework} bioinformatics project.

**Files and Their Imports**:
{files_with_imports}

**File Contents**:
{file_contents}

Produce a structured analysis as JSON:
{{
  "components": [
    {{"path": "file/path", "role": "one sentence describing this component's responsibility and which pipeline stage it implements", "dependencies": ["paths it imports from within the project"], "pipeline_stage": "e.g. QC, normalization, clustering, DE, visualization, utility"}}
  ],
  "patterns": ["list of patterns detected — both software patterns (pipeline, notebook-driven, config-driven) AND biological analysis patterns (standard scRNA-seq, integration workflow, spatial analysis, MIL classification)"],
  "data_flow": "Description of how biological data moves through the system — from raw input to biological insight (2-3 sentences). Note data formats used (h5ad, rds, csv, tiff, svs).",
  "entry_points": ["list of entry point files"],
  "biological_decisions": ["list of key biological parameter choices or assumptions encoded in the code, e.g. 'Uses 2000 HVGs', 'Leiden resolution 0.8', 'Filters cells with >20% mito'"],
  "domain": "single-cell | spatial | pathology | multi-omics | genomics | other"
}}"""

ARCH_SYNTHESIZE_SYSTEM = """You are BioCodeTeacher, creating an educational overview of a bioinformatics codebase.
Help graduate students and postdocs understand the scientific logic behind the code organization.
Use Mermaid diagrams to illustrate pipeline stages and data flow.
Connect code structure to biological reasoning — explain WHY the pipeline is organized this way.
When relevant, mention connections to immunology (immune cell populations, cytokine signaling, TME), reproductive biology (gametogenesis, embryonic development, placental biology), and tissue architecture."""

ARCH_SYNTHESIZE_TEMPLATE = """Create an educational architecture overview of this bioinformatics project.

**Project Framework**: {framework}
**Analysis Data**:
{analysis_json}

Produce TWO sections separated by `---CONTEXT_BLOCK---`:

SECTION 1 - Full educational overview in Markdown:
## Overview
[What biological question does this project address? What data type and analysis domain? 2-3 sentences. If it involves immune cells, developmental biology, or reproductive tissues, highlight that.]

## Analysis Pipeline
[Map the code to the canonical pipeline stages. Which stages are implemented? What biological assumptions drive each stage? E.g., "QC filtering at 20% mitochondrial reads — this threshold works for most tissues but may need adjustment for metabolically active cells like cardiomyocytes or hepatocytes."]

## Architecture
[Describe the code organization pattern (notebook-driven, Snakemake pipeline, modular scripts, etc.) and why it suits this type of analysis]

## Core Components
[For each key component: what it does scientifically, which pipeline stage it implements, and how it connects to others]

## Pipeline Diagram
```mermaid
graph TD
[Create a clear diagram showing pipeline stages with data formats on edges. E.g., raw_counts -->|"filter + normalize"| processed -->|"PCA + neighbors"| graph -->|"leiden"| clusters]
```

## Data Flow
[Trace the journey of biological data through the system — from raw input (FASTQ, 10X, h5ad, SVS) to biological insight (cell types, trajectories, biomarkers, spatial domains)]

## Data Flow Diagram
```mermaid
sequenceDiagram
[Create a sequence diagram showing a typical analysis run — from data loading through each processing step to output]
```

## Key Biological Decisions
[Educational explanation of the biological assumptions and parameter choices encoded in this codebase. Help the student understand that these choices are NOT arbitrary — they reflect real biological constraints. E.g., "The 2000 HVG cutoff balances computational cost against information loss — for specialized analyses (rare cell types, subtle immune states), you might need 3000-5000."]

## Key Dependencies
[Bioinformatics libraries, their roles, and which ecosystem they belong to (scverse, Bioconductor, etc.)]

## Learning Path
[Recommended order for reading the code files, building from data loading to advanced analysis. Start with the simplest concepts.]

---CONTEXT_BLOCK---

SECTION 2 - Condensed context summary (under 500 words) for injecting into future prompts:
[Project name/type, domain (single-cell/spatial/pathology), framework, pipeline stages implemented, key files per stage, data formats, biological parameters/thresholds used, key libraries. Dense, factual, no formatting. Include which organism/tissue if detectable.]"""

LINE_EXPLAIN_CONTEXT_PREFIX = """**Project Architecture Context:**
{context_block}

Use this context to explain how the selected code connects to the broader analysis pipeline. Reference specific pipeline stages, data transformations, and biological decisions when relevant. Proactively note how this step affects downstream analysis.

---

"""

FILE_CONTEXT_PREFIX = """**Architecture Context for This File:**
{file_context}

Use this context to explain how the selected code connects to the broader analysis pipeline. Reference the file's pipeline stage, its role in the data flow, and any biological parameters it encodes. If this file processes immune cells, developmental data, or reproductive tissue, highlight relevant biology.

---

"""

# --- File Summary Prompts ---

FILE_SUMMARY_SYSTEM = """You are BioCodeTeacher, an expert bioinformatics educator. Generate a clear, educational file summary that helps a graduate student understand what this file does in the analysis pipeline, what biological decisions it encodes, and how it connects to the rest of the project.

Be proactive: anticipate what the student will need to know next. If this file does QC, mention that normalization typically follows. If it does clustering, note that resolution is the key parameter to tune. Connect code to biology — every computational step has a biological justification."""

FILE_SUMMARY_TEMPLATE = """Analyze this file from a {framework} bioinformatics project and provide a student-friendly summary.

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
What does this file do scientifically? What biological question does it help answer? (2-3 sentences)

## Pipeline Stage
Which stage(s) of the analysis pipeline does this file implement? (QC, normalization, feature selection, dim reduction, integration, clustering, visualization, DE, annotation, trajectory, spatial analysis, pathology inference, etc.)

## Role in Architecture
How does this file fit into the overall project? Is it a pipeline step, utility, visualization, or configuration?

## Data Flow
What data format does this file consume? What does it produce? Trace the input → transformation → output. Note AnnData slots, Seurat assays, or file formats involved.

## Key Components
List the main functions, classes, or analysis steps with one-line descriptions. For each, note which biological operation it performs.

## Key Biological Decisions
What parameters or choices in this file encode biological assumptions? E.g., "Filters cells with >5000 genes — removes likely doublets. Threshold may need adjusting for cell types with naturally high gene counts (e.g., neurons)."

## Connections
What does this file depend on? What depends on it? How does data flow through it? What happens if you change a parameter here — what downstream steps are affected?

## Learning Objectives
What should a student understand after studying this file? Prioritize biological/statistical concepts:
- What biological phenomenon does this code address?
- What statistical assumptions does it make?
- What would go wrong if you skipped this step?
- What's the equivalent approach in the other ecosystem (Scanpy ↔ Seurat)?
"""

FILE_SUMMARY_CONTEXT_PREFIX = """**File Summary Context:**
{file_summary}

Use this context to ground the line explanation in the file's broader purpose, pipeline stage, and biological significance. Proactively connect the specific line to the file's overall analysis goals.

---

"""
