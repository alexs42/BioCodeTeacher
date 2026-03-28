"""
Code parsing utilities for extracting context around lines.
"""

import re
from typing import List, Tuple


class CodeParser:
    """
    Utilities for parsing and extracting code context.
    """

    @staticmethod
    def get_line_with_context(
        content: str,
        line_number: int,
        context_lines: int = 10
    ) -> Tuple[str, str, str]:
        """
        Extract a line and its surrounding context.

        Args:
            content: Full file content
            line_number: 1-indexed line number
            context_lines: Number of lines before/after to include

        Returns:
            Tuple of (context_before, target_line, context_after)
        """
        lines = content.splitlines()
        total_lines = len(lines)

        # Convert to 0-indexed
        idx = line_number - 1

        if idx < 0 or idx >= total_lines:
            raise ValueError(f"Line {line_number} out of range (file has {total_lines} lines)")

        # Extract target line
        target_line = lines[idx]

        # Extract context before
        start = max(0, idx - context_lines)
        context_before = "\n".join(
            f"{i + 1}: {lines[i]}" for i in range(start, idx)
        )

        # Extract context after
        end = min(total_lines, idx + context_lines + 1)
        context_after = "\n".join(
            f"{i + 1}: {lines[i]}" for i in range(idx + 1, end)
        )

        return context_before, target_line, context_after

    @staticmethod
    def get_line_range(
        content: str,
        start_line: int,
        end_line: int
    ) -> str:
        """
        Extract a range of lines.

        Args:
            content: Full file content
            start_line: 1-indexed start line
            end_line: 1-indexed end line (inclusive)

        Returns:
            String with the line range, prefixed with line numbers
        """
        lines = content.splitlines()
        total_lines = len(lines)

        # Validate range
        start_idx = start_line - 1
        end_idx = end_line

        if start_idx < 0:
            start_idx = 0
        if end_idx > total_lines:
            end_idx = total_lines

        # Extract with line numbers
        return "\n".join(
            f"{i + 1}: {lines[i]}" for i in range(start_idx, end_idx)
        )

    @staticmethod
    def find_function_bounds(
        content: str,
        line_number: int,
        language: str
    ) -> Tuple[int, int]:
        """
        Find the start and end of the function containing a line.
        Simple heuristic-based detection.

        Args:
            content: Full file content
            line_number: 1-indexed line number
            language: Programming language

        Returns:
            Tuple of (start_line, end_line) 1-indexed
        """
        lines = content.splitlines()
        idx = line_number - 1

        # Language-specific function patterns
        function_patterns = {
            "python": ["def ", "async def ", "class "],
            "javascript": ["function ", "const ", "let ", "var ", "async ", "class "],
            "typescript": ["function ", "const ", "let ", "var ", "async ", "class ", "interface ", "type "],
            "java": ["public ", "private ", "protected ", "class ", "interface "],
            "go": ["func ", "type "],
            "rust": ["fn ", "impl ", "struct ", "enum "],
        }

        patterns = function_patterns.get(language, ["function ", "def ", "class "])

        # Find function start (search backwards)
        start = idx
        for i in range(idx, -1, -1):
            line = lines[i].lstrip()
            if any(line.startswith(p) for p in patterns):
                start = i
                break

        # Find function end (search forwards for matching indentation or next function)
        if language in ["python"]:
            # Python uses indentation
            base_indent = len(lines[start]) - len(lines[start].lstrip())
            end = idx
            for i in range(idx + 1, len(lines)):
                stripped = lines[i].lstrip()
                if stripped and (len(lines[i]) - len(stripped)) <= base_indent:
                    if any(stripped.startswith(p) for p in patterns) or not lines[i].strip():
                        end = i - 1
                        break
                end = i
        else:
            # Brace-based languages: count braces
            brace_count = 0
            started = False
            end = idx
            for i in range(start, len(lines)):
                line = lines[i]
                brace_count += line.count("{") - line.count("}")
                if "{" in line:
                    started = True
                if started and brace_count <= 0:
                    end = i
                    break
                end = i

        return start + 1, end + 1  # Convert back to 1-indexed

    @staticmethod
    def extract_imports(content: str, language: str) -> List[str]:
        """
        Extract import/dependency statements from source code.

        Args:
            content: File content
            language: Programming language

        Returns:
            List of imported module/path strings
        """
        imports = []

        if language in ("python",):
            # Python: import X, from X import Y
            for match in re.finditer(r'^import\s+(\S+)', content, re.MULTILINE):
                imports.append(match.group(1).split('.')[0])
            for match in re.finditer(r'^from\s+(\S+)\s+import', content, re.MULTILINE):
                imports.append(match.group(1).split('.')[0])

        elif language in ("javascript", "typescript", "jsx", "tsx"):
            # JS/TS: import ... from 'X', require('X')
            for match in re.finditer(r'''import\s+.*?from\s+['"]([^'"]+)['"]''', content):
                imports.append(match.group(1))
            for match in re.finditer(r'''require\s*\(\s*['"]([^'"]+)['"]\s*\)''', content):
                imports.append(match.group(1))

        elif language in ("go",):
            # Go: import "X" or import ( "X" )
            for match in re.finditer(r'"([^"]+)"', content[:2000]):
                path = match.group(1)
                if '/' in path or '.' in path:
                    imports.append(path)

        elif language in ("rust",):
            # Rust: use X::Y
            for match in re.finditer(r'^use\s+(\S+)', content, re.MULTILINE):
                imports.append(match.group(1).rstrip(';'))

        elif language in ("java", "kotlin", "scala"):
            # Java/Kotlin/Scala: import X.Y.Z
            for match in re.finditer(r'^import\s+(\S+)', content, re.MULTILINE):
                imports.append(match.group(1).rstrip(';'))

        elif language in ("c", "cpp"):
            # C/C++: #include <X> or #include "X"
            for match in re.finditer(r'#include\s+[<"]([^>"]+)[>"]', content):
                imports.append(match.group(1))

        elif language in ("ruby",):
            # Ruby: require 'X', require_relative 'X'
            for match in re.finditer(r'''require(?:_relative)?\s+['"]([^'"]+)['"]''', content):
                imports.append(match.group(1))

        elif language in ("php",):
            # PHP: use X\Y\Z, require/include
            for match in re.finditer(r'^use\s+(\S+)', content, re.MULTILINE):
                imports.append(match.group(1).rstrip(';'))

        # Deduplicate while preserving order
        seen = set()
        unique = []
        for imp in imports:
            if imp not in seen:
                seen.add(imp)
                unique.append(imp)
        return unique


# Global instance
code_parser = CodeParser()
