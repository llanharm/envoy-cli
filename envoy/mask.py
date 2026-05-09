"""Mask sensitive values in env dicts for safe display or logging."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy.redact import is_sensitive

DEFAULT_MASK = "***"
_PARTIAL_VISIBLE = 4  # characters to reveal at start/end for partial mode


@dataclass
class MaskResult:
    masked: Dict[str, str]
    keys_masked: List[str]
    keys_skipped: List[str]

    @property
    def total_masked(self) -> int:
        return len(self.keys_masked)

    def to_dict(self) -> dict:
        return {
            "masked": self.masked,
            "keys_masked": self.keys_masked,
            "keys_skipped": self.keys_skipped,
            "total_masked": self.total_masked,
        }


def _partial_mask(value: str, mask: str = DEFAULT_MASK) -> str:
    """Show first and last N chars with mask in between."""
    if len(value) <= _PARTIAL_VISIBLE * 2:
        return mask
    return value[:_PARTIAL_VISIBLE] + mask + value[-_PARTIAL_VISIBLE:]


def mask_env(
    env: Dict[str, str],
    *,
    extra_patterns: Optional[List[str]] = None,
    partial: bool = False,
    mask: str = DEFAULT_MASK,
    only_keys: Optional[List[str]] = None,
) -> MaskResult:
    """Return a copy of *env* with sensitive values replaced by *mask*.

    Args:
        env: The parsed env dict to mask.
        extra_patterns: Additional regex patterns passed to is_sensitive.
        partial: When True, reveal first/last chars instead of full mask.
        mask: The replacement string for sensitive values.
        only_keys: If given, restrict masking to these keys only.
    """
    masked: Dict[str, str] = {}
    keys_masked: List[str] = []
    keys_skipped: List[str] = []

    for key, value in env.items():
        if only_keys is not None and key not in only_keys:
            masked[key] = value
            keys_skipped.append(key)
            continue

        if is_sensitive(key, extra_patterns=extra_patterns):
            masked[key] = _partial_mask(value, mask) if partial else mask
            keys_masked.append(key)
        else:
            masked[key] = value
            keys_skipped.append(key)

    return MaskResult(
        masked=masked,
        keys_masked=sorted(keys_masked),
        keys_skipped=sorted(keys_skipped),
    )
