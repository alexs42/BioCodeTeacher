"""
Tests for the documentation search service.
"""

import pytest
from unittest.mock import patch
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.doc_search import (
    DocSearchService,
    _extract_sphinx_doc,
    _ALIAS_MAP,
    KNOWN_LIBRARIES,
)


class TestLibraryDetection:
    """Tests for mapping imports to known libraries."""

    def test_detect_scanpy(self):
        svc = DocSearchService()
        assert svc.detect_libraries(["scanpy"]) == ["scanpy"]

    def test_detect_alias_sc(self):
        svc = DocSearchService()
        assert svc.detect_libraries(["sc"]) == ["scanpy"]

    def test_detect_multiple(self):
        svc = DocSearchService()
        result = svc.detect_libraries(["scanpy", "numpy", "os"])
        assert "scanpy" in result
        assert "numpy" in result
        assert len(result) == 2  # os is not a known library

    def test_detect_pandas_alias(self):
        svc = DocSearchService()
        assert svc.detect_libraries(["pd"]) == ["pandas"]

    def test_detect_anndata_alias(self):
        svc = DocSearchService()
        assert svc.detect_libraries(["ad"]) == ["anndata"]

    def test_detect_unknown_library(self):
        svc = DocSearchService()
        assert svc.detect_libraries(["some_unknown_lib"]) == []

    def test_no_duplicates(self):
        svc = DocSearchService()
        result = svc.detect_libraries(["scanpy", "sc"])
        assert result == ["scanpy"]


class TestFunctionRefExtraction:
    """Tests for extracting function references from user questions."""

    def test_scanpy_function(self):
        svc = DocSearchService()
        refs = svc.extract_function_refs(
            "What does sc.pp.normalize_total do?"
        )
        assert len(refs) >= 1
        assert refs[0] == ("scanpy", "pp.normalize_total")

    def test_scanpy_full_name(self):
        svc = DocSearchService()
        refs = svc.extract_function_refs(
            "How does scanpy.tl.leiden work?"
        )
        assert len(refs) >= 1
        assert refs[0] == ("scanpy", "tl.leiden")

    def test_numpy_function(self):
        svc = DocSearchService()
        refs = svc.extract_function_refs(
            "What is np.array?"
        )
        assert len(refs) >= 1
        assert refs[0] == ("numpy", "array")

    def test_pandas_function(self):
        svc = DocSearchService()
        refs = svc.extract_function_refs(
            "How do I use pd.DataFrame?"
        )
        assert len(refs) >= 1
        assert refs[0] == ("pandas", "DataFrame")

    def test_max_two_refs(self):
        svc = DocSearchService()
        refs = svc.extract_function_refs(
            "Compare sc.pp.normalize_total, sc.pp.log1p, and sc.tl.pca"
        )
        assert len(refs) <= 2

    def test_no_refs_in_question(self):
        svc = DocSearchService()
        refs = svc.extract_function_refs(
            "What is normalization?"
        )
        assert refs == []


class TestSphinxExtraction:
    """Tests for HTML doc extraction."""

    def test_basic_sphinx_html(self):
        html = """
        <dl class="py function">
          <dt id="scanpy.pp.normalize_total">
            <code>scanpy.pp.normalize_total(adata, target_sum=10000)</code>
          </dt>
          <dd>
            <p>Normalize each cell by total counts over all genes.</p>
            <p>More details here.</p>
          </dd>
        </dl>
        """
        result = _extract_sphinx_doc(html)
        assert result is not None
        assert "normalize_total" in result
        assert "Normalize each cell" in result

    def test_empty_html(self):
        assert _extract_sphinx_doc("") is None

    def test_no_dt_html(self):
        html = "<div><p>No function signature here.</p></div>"
        assert _extract_sphinx_doc(html) is None

    def test_real_pydata_sphinx_nested_spans(self):
        """Regression: real Sphinx/PyData HTML wraps signatures in nested spans."""
        html = """
        <dl class="py function">
        <dt class="sig sig-object py" id="scanpy.pp.normalize_total">
        <span class="sig-prename descclassname"><span class="pre">scanpy.pp.</span></span>
        <span class="sig-name descname"><span class="pre">normalize_total</span></span>
        <span class="sig-paren">(</span>
        <em class="sig-param"><span class="n"><span class="pre">adata</span></span></em>,
        <em class="sig-param"><span class="n"><span class="pre">target_sum</span></span>
        <span class="o"><span class="pre">=</span></span>
        <span class="default_value"><span class="pre">None</span></span></em>,
        <em class="sig-param"><span class="n"><span class="pre">inplace</span></span>
        <span class="o"><span class="pre">=</span></span>
        <span class="default_value"><span class="pre">True</span></span></em>
        <span class="sig-paren">)</span>
        </dt>
        <dd>
          <p>Normalize each cell by total counts over all genes.</p>
        </dd>
        </dl>
        """
        result = _extract_sphinx_doc(html)
        assert result is not None
        assert "normalize_total" in result
        assert "adata" in result
        assert "target_sum" in result
        assert "Normalize each cell" in result

    def test_signature_not_truncated_at_first_span(self):
        """Regression: must accumulate all text in <dt>, not just first fragment."""
        html = """
        <dl>
          <dt>
            <span class="pre">my_module.</span>
            <span class="pre">my_func</span>
            <span>(</span><span>x</span><span>)</span>
          </dt>
          <dd><p>Does something.</p></dd>
        </dl>
        """
        result = _extract_sphinx_doc(html)
        assert result is not None
        assert "my_func" in result
        assert "my_module." in result
        # Must NOT be just "my_module." (the old truncated behavior)
        sig_line = result.split("\n")[1]  # line inside ```
        assert "my_func" in sig_line

    def test_long_description_truncated(self):
        long_desc = "A" * 500
        html = f"""
        <dl>
          <dt>func()</dt>
          <dd><p>{long_desc}</p></dd>
        </dl>
        """
        result = _extract_sphinx_doc(html)
        assert result is not None
        assert len(result) < 600  # signature + truncated description


class TestCaching:
    """Tests for in-memory cache behavior."""

    def test_cache_hit(self):
        svc = DocSearchService()
        key = svc._cache_key("scanpy", "pp.normalize_total")
        svc._put_cache(key, "cached doc text")
        assert svc._get_cached(key) == "cached doc text"

    def test_cache_miss(self):
        svc = DocSearchService()
        assert svc._get_cached("nonexistent_key") is None

    def test_cache_max_size(self):
        svc = DocSearchService(max_cache=3)
        for i in range(5):
            svc._put_cache(f"key_{i}", f"doc_{i}")
        # Cache should not exceed max_cache
        assert len(svc._cache) <= 3

    @patch("services.doc_search.persistent_store")
    def test_cache_eviction(self, mock_ps):
        from datetime import datetime, timedelta

        mock_ps.load_doc_cache.return_value = None  # No disk fallback

        svc = DocSearchService(max_cache=2)
        svc._put_cache("old", "old doc")
        # Manually age the entry
        svc._cache["old"]["fetched_at"] = datetime.now() - timedelta(hours=1)
        svc._put_cache("new1", "new doc 1")
        svc._put_cache("new2", "new doc 2")
        # "old" should have been evicted from in-memory
        assert "old" not in svc._cache

    @patch("services.doc_search.persistent_store")
    def test_negative_cache(self, mock_ps):
        from services.doc_search import _NEGATIVE_CACHE

        mock_ps.load_doc_cache.return_value = None

        svc = DocSearchService()
        key = svc._cache_key("scanpy", "nonexistent_func")
        svc._put_cache(key, _NEGATIVE_CACHE)
        # Negative entry should be retrievable
        assert svc._get_cached(key) == _NEGATIVE_CACHE

    @patch("services.doc_search.persistent_store")
    def test_negative_cache_expires_faster(self, mock_ps):
        from datetime import datetime, timedelta
        from services.doc_search import _NEGATIVE_CACHE

        mock_ps.load_doc_cache.return_value = None  # No disk fallback

        svc = DocSearchService()
        key = "neg_test"
        svc._cache[key] = {"text": _NEGATIVE_CACHE, "fetched_at": datetime.now() - timedelta(minutes=31)}
        assert svc._get_cached(key) is None  # Should be expired

    @patch("services.doc_search.persistent_store")
    def test_positive_cache_survives_30min(self, mock_ps):
        from datetime import datetime, timedelta

        mock_ps.load_doc_cache.return_value = None

        svc = DocSearchService()
        key = "pos_test"
        svc._cache[key] = {"text": "real doc text", "fetched_at": datetime.now() - timedelta(hours=1)}
        assert svc._get_cached(key) == "real doc text"  # Should still be valid


class TestAliasMap:
    """Tests for the alias reverse lookup."""

    def test_canonical_names(self):
        assert _ALIAS_MAP["scanpy"] == "scanpy"
        assert _ALIAS_MAP["numpy"] == "numpy"
        assert _ALIAS_MAP["pandas"] == "pandas"

    def test_aliases(self):
        assert _ALIAS_MAP["sc"] == "scanpy"
        assert _ALIAS_MAP["np"] == "numpy"
        assert _ALIAS_MAP["pd"] == "pandas"
        assert _ALIAS_MAP["ad"] == "anndata"
        assert _ALIAS_MAP["sq"] == "squidpy"

    def test_all_libraries_have_self_alias(self):
        for lib in KNOWN_LIBRARIES:
            assert _ALIAS_MAP[lib] == lib


@pytest.mark.asyncio
class TestDocSearchIntegration:
    """Integration tests for the full doc search flow."""

    async def test_get_relevant_docs_no_imports(self):
        svc = DocSearchService()
        result = await svc.get_relevant_docs(
            imports=[], question="What is normalization?"
        )
        assert result is None

    async def test_get_relevant_docs_no_function_refs(self):
        svc = DocSearchService()
        result = await svc.get_relevant_docs(
            imports=["scanpy"], question="What is normalization?"
        )
        assert result is None

    async def test_get_relevant_docs_unknown_library(self):
        svc = DocSearchService()
        result = await svc.get_relevant_docs(
            imports=["some_random_lib"],
            question="What does some_random_lib.foo do?",
        )
        assert result is None
