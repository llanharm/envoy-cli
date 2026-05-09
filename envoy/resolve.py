"""Resolve effective env values by layering multiple .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envoy.parser import parse_env_file


@dataclass
class ResolveResult:
    """Result of layering multiple .env files."""

    effective: Dict[str, str]
    sources: Dict[str, str]  # key -> path that last defined it
    overridden: Dict[str, List[str]]  # key -> list of paths that were shadowed
    files: List[str] = field(default_factory=list)

    @property
    def total_keys(self) -> int:
        return len(self.effective)

    @property
    def total_overridden(self) -> int:
        return len(self.overridden)

    def to_dict(self) -> dict:
        return {
            "effective": self.effective,
            "sources": self.sources,
            "overridden": self.overridden,
            "files": self.files,
            "total_keys": self.total_keys,
            "total_overridden": self.total_overridden,
        }


def resolve_env_files(
    paths: List[str],
    base: Optional[Dict[str, str]] = None,
) -> ResolveResult:
    """Layer env files left-to-right; later files override earlier ones.

    Args:
        paths: Ordered list of .env file paths (lowest to highest priority).
        base:  Optional pre-seeded values (lowest priority of all).

    Returns:
        ResolveResult with the merged effective environment.
    """
    if not paths:
        raise ValueError("resolve_env_files requires at least one path")

    effective: Dict[str, str] = dict(base or {})
    sources: Dict[str, str] = {k: "<base>" for k in effective}
    overridden: Dict[str, List[str]] = {}

    for raw_path in paths:
        path = str(Path(raw_path))
        layer = parse_env_file(path)
        for key, value in layer.items():
            if key in effective:
                overridden.setdefault(key, [])
                overridden[key].append(sources[key])
            effective[key] = value
            sources[key] = path

    return ResolveResult(
        effective=effective,
        sources=sources,
        overridden=overridden,
        files=list(paths),
    )
