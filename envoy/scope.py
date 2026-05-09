"""Scope filtering: restrict env keys to a named subset defined in a scope config."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


class ScopeError(Exception):
    """Raised when scope configuration is invalid or a scope is not found."""


@dataclass
class ScopeResult:
    scope: str
    matched: Dict[str, str] = field(default_factory=dict)
    excluded: List[str] = field(default_factory=list)

    @property
    def total_matched(self) -> int:
        return len(self.matched)

    @property
    def total_excluded(self) -> int:
        return len(self.excluded)

    def to_dict(self) -> dict:
        return {
            "scope": self.scope,
            "matched": self.matched,
            "excluded": self.excluded,
            "total_matched": self.total_matched,
            "total_excluded": self.total_excluded,
        }


def load_scopes(scope_file: Path) -> Dict[str, List[str]]:
    """Load scope definitions from a JSON file.

    Expected format::

        {
            "backend": ["DB_HOST", "DB_PORT", "SECRET_KEY"],
            "frontend": ["API_URL", "PUBLIC_KEY"]
        }
    """
    if not scope_file.exists():
        raise ScopeError(f"Scope file not found: {scope_file}")
    try:
        data = json.loads(scope_file.read_text())
    except json.JSONDecodeError as exc:
        raise ScopeError(f"Invalid JSON in scope file: {exc}") from exc
    if not isinstance(data, dict):
        raise ScopeError("Scope file must be a JSON object mapping scope names to key lists.")
    for name, keys in data.items():
        if not isinstance(keys, list) or not all(isinstance(k, str) for k in keys):
            raise ScopeError(f"Scope '{name}' must map to a list of strings.")
    return data


def apply_scope(
    env: Dict[str, str],
    scope_name: str,
    scopes: Dict[str, List[str]],
) -> ScopeResult:
    """Return only the env keys that belong to *scope_name*."""
    if scope_name not in scopes:
        available = ", ".join(sorted(scopes)) or "(none)"
        raise ScopeError(
            f"Scope '{scope_name}' not defined. Available scopes: {available}"
        )
    allowed: List[str] = scopes[scope_name]
    matched = {k: v for k, v in env.items() if k in allowed}
    excluded = [k for k in env if k not in allowed]
    return ScopeResult(scope=scope_name, matched=matched, excluded=sorted(excluded))
