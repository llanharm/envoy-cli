"""Multi-file .env comparison: compare two or more env files side by side."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from envoy.parser import parse_env_file
from envoy.redact import is_sensitive


@dataclass
class CompareResult:
    """Result of comparing N env files."""
    files: List[str]
    all_keys: List[str]
    # key -> {filename -> value or None}
    matrix: Dict[str, Dict[str, Optional[str]]] = field(default_factory=dict)

    def missing_in(self, filename: str) -> List[str]:
        """Return keys that are absent from *filename*."""
        return [k for k, row in self.matrix.items() if row.get(filename) is None]

    def keys_unique_to(self, filename: str) -> List[str]:
        """Return keys that exist ONLY in *filename*."""
        result = []
        for key, row in self.matrix.items():
            present_in = [f for f, v in row.items() if v is not None]
            if present_in == [filename]:
                result.append(key)
        return result

    def divergent_keys(self) -> List[str]:
        """Return keys whose values differ across at least two files."""
        divergent = []
        for key, row in self.matrix.items():
            values: Set[str] = {v for v in row.values() if v is not None}
            if len(values) > 1:
                divergent.append(key)
        return divergent


def compare_env_files(
    paths: List[str],
    mask_secrets: bool = True,
) -> CompareResult:
    """Parse each path and build a comparison matrix.

    Args:
        paths: Two or more paths to .env files.
        mask_secrets: If True, replace sensitive values with ``"***"``.

    Returns:
        A :class:`CompareResult` describing how the files relate.

    Raises:
        ValueError: When fewer than two paths are provided.
    """
    if len(paths) < 2:
        raise ValueError("compare_env_files requires at least two files")

    parsed: Dict[str, Dict[str, str]] = {}
    for path in paths:
        parsed[path] = parse_env_file(path)

    all_keys: List[str] = sorted(
        {k for env in parsed.values() for k in env}
    )

    matrix: Dict[str, Dict[str, Optional[str]]] = {}
    for key in all_keys:
        row: Dict[str, Optional[str]] = {}
        for path, env in parsed.items():
            if key in env:
                value = env[key]
                if mask_secrets and is_sensitive(key):
                    value = "***"
                row[path] = value
            else:
                row[path] = None
        matrix[key] = row

    return CompareResult(files=list(paths), all_keys=all_keys, matrix=matrix)
