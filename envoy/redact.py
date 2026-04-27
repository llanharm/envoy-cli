"""Redaction utilities for masking sensitive values in .env files."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

# Patterns that suggest a key holds a sensitive value
_SENSITIVE_PATTERNS: List[re.Pattern] = [
    re.compile(r"(secret|password|passwd|token|api[_-]?key|private[_-]?key"
               r"|auth|credential|cert|signing)", re.IGNORECASE),
]

_REDACTED = "[REDACTED]"


@dataclass
class RedactResult:
    original: Dict[str, str]
    redacted: Dict[str, str]
    redacted_keys: Set[str] = field(default_factory=set)


def is_sensitive(key: str, extra_patterns: Optional[List[str]] = None) -> bool:
    """Return True if *key* looks like it holds a sensitive value."""
    patterns = list(_SENSITIVE_PATTERNS)
    for pat in extra_patterns or []:
        patterns.append(re.compile(pat, re.IGNORECASE))
    return any(p.search(key) for p in patterns)


def redact(
    env: Dict[str, str],
    extra_patterns: Optional[List[str]] = None,
    explicit_keys: Optional[Set[str]] = None,
) -> RedactResult:
    """Return a copy of *env* with sensitive values replaced by [REDACTED]."""
    redacted: Dict[str, str] = {}
    redacted_keys: Set[str] = set()

    for key, value in env.items():
        if (explicit_keys and key in explicit_keys) or is_sensitive(
            key, extra_patterns
        ):
            redacted[key] = _REDACTED
            redacted_keys.add(key)
        else:
            redacted[key] = value

    return RedactResult(
        original=dict(env),
        redacted=redacted,
        redacted_keys=redacted_keys,
    )
