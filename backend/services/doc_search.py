"""
Documentation search service for bioinformatics libraries.

Fetches API reference documentation from known library doc sites,
extracts function signatures and descriptions, and caches results
for injection into chat prompts.
"""

import hashlib
import re
from datetime import datetime, timedelta
from html.parser import HTMLParser
from typing import Optional

import httpx

from services.code_parser import code_parser
from services.persistent_store import persistent_store

# Sentinel for negative cache entries (fetch failed / 404)
_NEGATIVE_CACHE = "__NEGATIVE__"
_NEGATIVE_TTL = timedelta(minutes=30)

# ── Known bioinformatics library documentation URLs ──────────────

KNOWN_LIBRARIES: dict[str, dict] = {
    # Python scverse ecosystem
    "scanpy": {
        "base": "https://scanpy.readthedocs.io/en/stable/",
        "api_pattern": "generated/scanpy.{func}.html",
        "aliases": ["sc"],
    },
    "anndata": {
        "base": "https://anndata.readthedocs.io/en/stable/",
        "api_pattern": "generated/anndata.{func}.html",
        "aliases": ["ad"],
    },
    "squidpy": {
        "base": "https://squidpy.readthedocs.io/en/stable/",
        "api_pattern": "generated/squidpy.{func}.html",
        "aliases": ["sq"],
    },
    "scvi": {
        "base": "https://docs.scvi-tools.org/en/stable/",
        "api_pattern": "api/reference/scvi.{func}.html",
        "aliases": ["scvi"],
    },
    "cellrank": {
        "base": "https://cellrank.readthedocs.io/en/stable/",
        "api_pattern": "generated/cellrank.{func}.html",
        "aliases": [],
    },
    "mudata": {
        "base": "https://mudata.readthedocs.io/en/stable/",
        "api_pattern": "generated/mudata.{func}.html",
        "aliases": ["mu"],
    },
    "scvelo": {
        "base": "https://scvelo.readthedocs.io/en/stable/",
        "api_pattern": "generated/scvelo.{func}.html",
        "aliases": ["scv"],
    },
    "decoupler": {
        "base": "https://decoupler-py.readthedocs.io/en/stable/",
        "api_pattern": "generated/decoupler.{func}.html",
        "aliases": ["dc"],
    },
    # Spatial
    "spatialdata": {
        "base": "https://spatialdata.readthedocs.io/en/stable/",
        "api_pattern": "generated/spatialdata.{func}.html",
        "aliases": [],
    },
    # Core scientific Python
    "numpy": {
        "base": "https://numpy.org/doc/stable/",
        "api_pattern": "reference/generated/numpy.{func}.html",
        "aliases": ["np"],
    },
    "pandas": {
        "base": "https://pandas.pydata.org/docs/",
        "api_pattern": "reference/api/pandas.{func}.html",
        "aliases": ["pd"],
    },
    "scipy": {
        "base": "https://docs.scipy.org/doc/scipy/",
        "api_pattern": "reference/generated/scipy.{func}.html",
        "aliases": [],
    },
    "matplotlib": {
        "base": "https://matplotlib.org/stable/",
        "api_pattern": "api/_as_gen/matplotlib.{func}.html",
        "aliases": ["plt", "mpl"],
    },
    "seaborn": {
        "base": "https://seaborn.pydata.org/",
        "api_pattern": "generated/seaborn.{func}.html",
        "aliases": ["sns"],
    },
    "sklearn": {
        "base": "https://scikit-learn.org/stable/",
        "api_pattern": "modules/generated/sklearn.{func}.html",
        "aliases": ["scikit_learn"],
    },
    # Pathology
    "openslide": {
        "base": "https://openslide.org/api/python/",
        "api_pattern": "",
        "aliases": [],
    },
    # Bioinformatics
    "pysam": {
        "base": "https://pysam.readthedocs.io/en/stable/",
        "api_pattern": "api.html",
        "aliases": [],
    },
    "biopython": {
        "base": "https://biopython.org/wiki/Documentation",
        "api_pattern": "",
        "aliases": ["Bio"],
    },
}

# Build reverse lookup: alias → canonical name
_ALIAS_MAP: dict[str, str] = {}
for _lib, _info in KNOWN_LIBRARIES.items():
    _ALIAS_MAP[_lib] = _lib
    for _alias in _info.get("aliases", []):
        _ALIAS_MAP[_alias] = _lib


# ── Sphinx HTML extractor ────────────────────────────────────────

class _SphinxDocExtractor(HTMLParser):
    """Extract function signature and first description paragraph from
    Sphinx-generated API reference HTML (ReadTheDocs / PyData theme)."""

    def __init__(self):
        super().__init__()
        self._in_dt = False
        self._in_dd = False
        self._in_p = False
        self._dt_depth = 0
        self._dd_depth = 0
        self._signature = ""
        self._description = ""
        self._done = False

    def handle_starttag(self, tag, attrs):
        if self._done:
            return
        if tag == "dt":
            self._in_dt = True
            self._dt_depth += 1
        elif tag == "dd" and self._signature:
            self._in_dd = True
            self._dd_depth += 1
        elif tag == "p" and self._in_dd and self._dd_depth == 1:
            self._in_p = True

    def handle_endtag(self, tag):
        if self._done:
            return
        if tag == "dt":
            self._dt_depth -= 1
            if self._dt_depth <= 0:
                self._in_dt = False
        elif tag == "dd":
            self._dd_depth -= 1
            if self._dd_depth <= 0:
                self._in_dd = False
                if self._description:
                    self._done = True
        elif tag == "p" and self._in_p:
            self._in_p = False
            if self._description.strip():
                self._done = True

    def handle_data(self, data):
        if self._done:
            return
        if self._in_dt and self._dt_depth == 1:
            # Accumulate ALL text fragments inside <dt> (Sphinx splits
            # signatures across nested <span> elements)
            self._signature += data
        elif self._in_p and not self._done:
            self._description += data

    @property
    def result(self) -> Optional[str]:
        # Normalize whitespace from accumulated span fragments
        sig = " ".join(self._signature.split())
        desc = self._description.strip()
        if not sig:
            return None
        parts = [f"```\n{sig}\n```"]
        if desc:
            # Cap description at ~300 chars
            if len(desc) > 300:
                desc = desc[:297] + "..."
            parts.append(desc)
        return "\n\n".join(parts)


def _extract_sphinx_doc(html: str) -> Optional[str]:
    """Extract the first function signature + description from Sphinx HTML."""
    extractor = _SphinxDocExtractor()
    try:
        extractor.feed(html)
    except Exception:
        return None
    return extractor.result


# ── Main service ─────────────────────────────────────────────────

# Function reference patterns in user questions
_FUNC_REF_PATTERNS = [
    # sc.pp.normalize_total, scanpy.pp.normalize_total
    re.compile(r'(?:sc|scanpy)\.([a-z]+\.[a-z_]+)'),
    # sq.gr.spatial_neighbors
    re.compile(r'(?:sq|squidpy)\.([a-z]+\.[a-z_]+)'),
    # ad.AnnData, anndata.AnnData
    re.compile(r'(?:ad|anndata)\.([A-Za-z_]+)'),
    # np.array, numpy.array
    re.compile(r'(?:np|numpy)\.([a-z_]+)'),
    # pd.DataFrame, pandas.read_csv
    re.compile(r'(?:pd|pandas)\.([A-Za-z_]+)'),
    # Generic: library.module.function
    re.compile(r'([a-z_]+)\.([a-z]+\.[a-z_]+)'),
]


class DocSearchService:
    """Fetches and caches API documentation for bioinformatics libraries."""

    def __init__(self, max_cache: int = 500, ttl_hours: int = 24):
        self._cache: dict[str, dict] = {}
        self._max_cache = max_cache
        self._ttl = timedelta(hours=ttl_hours)

    def detect_libraries(self, imports: list[str]) -> list[str]:
        """Map import names to known library canonical names."""
        found = []
        for imp in imports:
            canonical = _ALIAS_MAP.get(imp)
            if canonical and canonical not in found:
                found.append(canonical)
        return found

    def extract_function_refs(
        self, question: str,
    ) -> list[tuple[str, str]]:
        """Extract (library, function) pairs from the user's question text.

        Detection is regex-based against known library prefixes (sc., np., etc.).
        Returns at most 2 references to stay within context budget.
        """
        refs: list[tuple[str, str]] = []

        for pattern in _FUNC_REF_PATTERNS:
            for match in pattern.finditer(question):
                groups = match.groups()
                if len(groups) == 1:
                    # Pattern matched a known prefix (e.g., sc.pp.normalize_total)
                    func_name = groups[0]
                    # Determine library from the pattern prefix
                    prefix = match.group(0).split(".")[0]
                    lib = _ALIAS_MAP.get(prefix)
                    if lib and (lib, func_name) not in refs:
                        refs.append((lib, func_name))
                elif len(groups) == 2:
                    # Generic library.module.function
                    lib_name, func_name = groups
                    lib = _ALIAS_MAP.get(lib_name)
                    if lib and (lib, func_name) not in refs:
                        refs.append((lib, func_name))

            if len(refs) >= 2:
                break

        return refs[:2]

    def _cache_key(self, library: str, func: str) -> str:
        raw = f"{library}:{func}"
        return hashlib.md5(raw.encode()).hexdigest()[:16]

    def _get_cached(self, key: str) -> Optional[str]:
        """Check in-memory cache, then disk cache. Returns text, _NEGATIVE_CACHE, or None."""
        entry = self._cache.get(key)
        if entry:
            ttl = _NEGATIVE_TTL if entry["text"] == _NEGATIVE_CACHE else self._ttl
            if datetime.now() - entry["fetched_at"] > ttl:
                del self._cache[key]
            else:
                return entry["text"]

        # Try disk cache
        disk_entry = persistent_store.load_doc_cache(key)
        if disk_entry:
            fetched_at = datetime.fromisoformat(disk_entry["fetched_at"])
            is_negative = disk_entry["text"] == _NEGATIVE_CACHE
            ttl = _NEGATIVE_TTL if is_negative else self._ttl
            if datetime.now() - fetched_at <= ttl:
                # Promote to in-memory cache
                self._cache[key] = {"text": disk_entry["text"], "fetched_at": fetched_at}
                return disk_entry["text"]

        return None

    def _put_cache(self, key: str, text: str) -> None:
        if len(self._cache) >= self._max_cache:
            # Evict oldest entry
            oldest_key = min(self._cache, key=lambda k: self._cache[k]["fetched_at"])
            del self._cache[oldest_key]
        now = datetime.now()
        self._cache[key] = {"text": text, "fetched_at": now}
        # Persist to disk
        try:
            persistent_store.save_doc_cache(key, {
                "text": text,
                "fetched_at": now.isoformat(),
            })
        except Exception:
            pass  # Disk write failure is non-critical

    async def fetch_doc(self, library: str, func_name: str) -> Optional[str]:
        """Fetch documentation for a specific function from a known library.

        Returns extracted signature + description, or None on failure.
        Uses two-tier caching (in-memory + disk) with negative caching
        for failed lookups (30min TTL) to avoid repeated network penalties.
        """
        lib_info = KNOWN_LIBRARIES.get(library)
        if not lib_info or not lib_info.get("api_pattern"):
            return None

        # Check cache (in-memory → disk)
        key = self._cache_key(library, func_name)
        cached = self._get_cached(key)
        if cached == _NEGATIVE_CACHE:
            return None  # Known-bad lookup, skip network
        if cached is not None:
            return cached

        # Build URL
        url = lib_info["base"] + lib_info["api_pattern"].format(func=func_name)

        try:
            async with httpx.AsyncClient(
                timeout=3.0, follow_redirects=True
            ) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    self._put_cache(key, _NEGATIVE_CACHE)
                    return None

                doc_text = _extract_sphinx_doc(resp.text)
                if doc_text:
                    self._put_cache(key, doc_text)
                    return doc_text
                else:
                    self._put_cache(key, _NEGATIVE_CACHE)
                    return None

        except (httpx.TimeoutException, httpx.HTTPError, Exception):
            self._put_cache(key, _NEGATIVE_CACHE)
            return None

    async def get_relevant_docs(
        self,
        imports: list[str],
        question: str,
        file_content: Optional[str] = None,
        language: Optional[str] = None,
    ) -> Optional[str]:
        """Get documentation relevant to the user's question.

        Detects libraries from imports and function references from the
        question text, fetches docs for up to 2 functions, and returns
        a formatted documentation block for prompt injection.
        """
        # Detect libraries from imports
        libraries = self.detect_libraries(imports)

        # Also detect from file content imports if provided
        if file_content and language:
            file_imports = code_parser.extract_imports(file_content, language)
            for lib in self.detect_libraries(file_imports):
                if lib not in libraries:
                    libraries.append(lib)

        if not libraries:
            return None

        # Extract function references from the question
        refs = self.extract_function_refs(question)
        if not refs:
            return None

        # Fetch docs (sequentially to respect rate limits; max 2 fetches)
        doc_parts: list[str] = []
        for lib, func in refs:
            doc = await self.fetch_doc(lib, func)
            if doc:
                doc_parts.append(f"**{lib}.{func}**\n{doc}")

        if not doc_parts:
            return None

        # Cap total documentation at ~1000 chars
        result = "\n\n".join(doc_parts)
        if len(result) > 1000:
            result = result[:997] + "..."

        return result


# Global singleton
doc_search_service = DocSearchService()
