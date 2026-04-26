"""Secret diffing utilities — compare two sets of env variables."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class EnvDiff:
    """Represents the diff between two .env files."""
    added: Dict[str, str] = field(default_factory=dict)
    removed: Dict[str, str] = field(default_factory=dict)
    changed: Dict[str, tuple] = field(default_factory=dict)  # key -> (old, new)
    unchanged: Dict[str, str] = field(default_factory=dict)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        lines = []
        for key, value in self.added.items():
            lines.append(f"  + {key}={_mask(value)}")
        for key, value in self.removed.items():
            lines.append(f"  - {key}={_mask(value)}")
        for key, (old, new) in self.changed.items():
            lines.append(f"  ~ {key}: {_mask(old)} -> {_mask(new)}")
        return '\n'.join(lines) if lines else "  (no changes)"


def diff_envs(
    base: Dict[str, str],
    target: Dict[str, str],
    mask_secrets: bool = True,
) -> EnvDiff:
    """Compute the diff between two env dictionaries.

    Args:
        base: The original env variable set.
        target: The new env variable set to compare against.
        mask_secrets: If True, values are masked in output (does not affect diff logic).

    Returns:
        An EnvDiff instance describing additions, removals, and changes.
    """
    result = EnvDiff()
    all_keys = set(base) | set(target)

    for key in sorted(all_keys):
        in_base = key in base
        in_target = key in target

        if in_base and not in_target:
            result.removed[key] = base[key]
        elif in_target and not in_base:
            result.added[key] = target[key]
        elif base[key] != target[key]:
            result.changed[key] = (base[key], target[key])
        else:
            result.unchanged[key] = base[key]

    return result


def _mask(value: str, visible_chars: int = 4) -> str:
    """Partially mask a secret value for safe display."""
    if len(value) <= visible_chars:
        return '*' * len(value)
    return value[:visible_chars] + '*' * (len(value) - visible_chars)
