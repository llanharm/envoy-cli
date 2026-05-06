"""Merge multiple .env files with conflict detection and resolution strategies."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from envoy.parser import parse_env_file


class Strategy(str, Enum):
    FIRST = "first"   # keep value from the first file that defines the key
    LAST = "last"     # keep value from the last file that defines the key
    STRICT = "strict" # raise on any conflict


@dataclass
class MergeConflict:
    key: str
    values: Dict[str, str]  # path -> value

    def to_dict(self) -> dict:
        return {"key": self.key, "values": self.values}


@dataclass
class MergeResult:
    merged: Dict[str, str]
    conflicts: List[MergeConflict] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.conflicts) == 0

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "merged": self.merged,
            "conflicts": [c.to_dict() for c in self.conflicts],
            "sources": self.sources,
        }


class MergeConflictError(Exception):
    """Raised when strategy=strict and a conflict is detected."""

    def __init__(self, conflicts: List[MergeConflict]) -> None:
        keys = ", ".join(c.key for c in conflicts)
        super().__init__(f"Merge conflicts on keys: {keys}")
        self.conflicts = conflicts


def merge_env_files(
    paths: List[str],
    strategy: Strategy = Strategy.LAST,
    overrides: Optional[Dict[str, str]] = None,
) -> MergeResult:
    """Merge *paths* into a single env mapping.

    Args:
        paths:     Ordered list of .env file paths to merge.
        strategy:  Conflict resolution strategy (first / last / strict).
        overrides: Optional key-value pairs applied after merging.

    Returns:
        A :class:`MergeResult` describing the merged env and any conflicts.
    """
    if len(paths) < 2:
        raise ValueError("merge_env_files requires at least two paths")

    seen: Dict[str, str] = {}          # key -> winning value
    origin: Dict[str, str] = {}        # key -> path that set it
    conflict_map: Dict[str, Dict[str, str]] = {}  # key -> {path: value}

    for path in paths:
        env = parse_env_file(path)
        for key, value in env.items():
            if key not in seen:
                seen[key] = value
                origin[key] = path
            elif seen[key] != value:
                if key not in conflict_map:
                    conflict_map[key] = {origin[key]: seen[key]}
                conflict_map[key][path] = value
                if strategy is Strategy.LAST:
                    seen[key] = value
                    origin[key] = path
                # FIRST: keep existing value; STRICT: collect then raise

    conflicts = [
        MergeConflict(key=k, values=v) for k, v in conflict_map.items()
    ]

    if strategy is Strategy.STRICT and conflicts:
        raise MergeConflictError(conflicts)

    if overrides:
        seen.update(overrides)

    return MergeResult(merged=seen, conflicts=conflicts, sources=list(paths))
