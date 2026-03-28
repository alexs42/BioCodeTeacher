"""
In-memory cache for LLM explanations to avoid redundant API calls.
"""

import hashlib
from typing import Optional, Dict
from datetime import datetime, timedelta


class ExplanationCache:
    """
    Simple in-memory cache for code explanations.
    Uses content hash as key to handle file changes.
    """

    def __init__(self, max_size: int = 1000, ttl_minutes: int = 60):
        """
        Initialize the cache.

        Args:
            max_size: Maximum number of cached entries
            ttl_minutes: Time-to-live for cache entries in minutes
        """
        self._cache: Dict[str, dict] = {}
        self._max_size = max_size
        self._ttl = timedelta(minutes=ttl_minutes)

    def _make_key(self, file_path: str, content: str, line_number: int, request_type: str) -> str:
        """Create a unique cache key based on content hash and line."""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:16]
        return f"{request_type}:{file_path}:{content_hash}:{line_number}"

    def _make_arch_key(self, repo_id: str, file_tree_hash: str) -> str:
        """Create cache key for architecture analysis."""
        return f"arch:{repo_id}:{file_tree_hash}"

    def _cleanup_expired(self):
        """Remove expired entries."""
        now = datetime.now()
        expired = [
            key for key, entry in self._cache.items()
            if now - entry["timestamp"] > self._ttl
        ]
        for key in expired:
            del self._cache[key]

    def _enforce_size_limit(self):
        """Remove oldest entries if cache exceeds max size."""
        if len(self._cache) > self._max_size:
            # Sort by timestamp and remove oldest
            sorted_keys = sorted(
                self._cache.keys(),
                key=lambda k: self._cache[k]["timestamp"]
            )
            to_remove = len(self._cache) - self._max_size
            for key in sorted_keys[:to_remove]:
                del self._cache[key]

    def get(
        self,
        file_path: str,
        content: str,
        line_number: int,
        request_type: str = "line"
    ) -> Optional[str]:
        """
        Get a cached explanation if available.

        Args:
            file_path: Path to the file
            content: Current file content
            line_number: Line being explained
            request_type: Type of explanation (line, range, etc.)

        Returns:
            Cached explanation or None
        """
        self._cleanup_expired()

        key = self._make_key(file_path, content, line_number, request_type)
        entry = self._cache.get(key)

        if entry:
            return entry["explanation"]
        return None

    def set(
        self,
        file_path: str,
        content: str,
        line_number: int,
        explanation: str,
        request_type: str = "line"
    ):
        """
        Cache an explanation.

        Args:
            file_path: Path to the file
            content: Current file content
            line_number: Line being explained
            explanation: The LLM explanation
            request_type: Type of explanation
        """
        key = self._make_key(file_path, content, line_number, request_type)

        self._cache[key] = {
            "explanation": explanation,
            "timestamp": datetime.now(),
        }

        self._enforce_size_limit()

    def get_architecture(self, repo_id: str, file_tree_hash: str) -> Optional[str]:
        """Get cached architecture analysis."""
        self._cleanup_expired()
        key = self._make_arch_key(repo_id, file_tree_hash)
        entry = self._cache.get(key)
        return entry["explanation"] if entry else None

    def set_architecture(self, repo_id: str, file_tree_hash: str, analysis: str):
        """Cache architecture analysis."""
        key = self._make_arch_key(repo_id, file_tree_hash)
        self._cache[key] = {
            "explanation": analysis,
            "timestamp": datetime.now(),
        }
        self._enforce_size_limit()

    def clear(self):
        """Clear all cached entries."""
        self._cache.clear()

    def stats(self) -> dict:
        """Get cache statistics."""
        return {
            "entries": len(self._cache),
            "max_size": self._max_size,
            "ttl_minutes": self._ttl.total_seconds() / 60,
        }


# Global instance
explanation_cache = ExplanationCache()
