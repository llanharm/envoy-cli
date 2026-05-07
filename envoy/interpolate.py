"""Variable interpolation for .env files.

Supports ${VAR} and $VAR style references within values,
with detection of missing and circular dependencies.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_REF_RE = re.compile(r"\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


@dataclass
class InterpolateResult:
    resolved: Dict[str, str]
    unresolved_keys: List[str] = field(default_factory=list)
    circular_keys: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.unresolved_keys and not self.circular_keys


def _refs(value: str) -> List[str]:
    """Return all variable names referenced in *value*."""
    return [m.group(1) or m.group(2) for m in _REF_RE.finditer(value)]


def _resolve_one(
    key: str,
    env: Dict[str, str],
    resolved: Dict[str, str],
    visiting: set,
    circular: set,
    missing: set,
) -> Optional[str]:
    if key in resolved:
        return resolved[key]
    if key not in env:
        missing.add(key)
        return None
    if key in visiting:
        circular.add(key)
        return None

    visiting.add(key)
    raw = env[key]

    def _replace(m: re.Match) -> str:
        ref = m.group(1) or m.group(2)
        val = _resolve_one(ref, env, resolved, visiting, circular, missing)
        return val if val is not None else m.group(0)

    value = _REF_RE.sub(_replace, raw)
    visiting.discard(key)
    resolved[key] = value
    return value


def interpolate(env: Dict[str, str]) -> InterpolateResult:
    """Resolve variable references inside *env* values.

    Returns an :class:`InterpolateResult` with the fully resolved mapping
    and lists of any keys that could not be resolved.
    """
    resolved: Dict[str, str] = {}
    circular: set = set()
    missing: set = set()

    for key in env:
        _resolve_one(key, env, resolved, set(), circular, missing)

    # Keys whose *own* value depends on a missing external reference.
    unresolved = sorted(
        k for k in env if k not in resolved or missing.intersection(_refs(env[k]))
    )
    return InterpolateResult(
        resolved=resolved,
        unresolved_keys=unresolved,
        circular_keys=sorted(circular),
    )
