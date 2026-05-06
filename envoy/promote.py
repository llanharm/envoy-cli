"""Promote .env values from one environment to another with optional key filtering."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy.parser import parse_env_file, write_env_file


@dataclass
class PromoteResult:
    source: str
    destination: str
    promoted: Dict[str, str] = field(default_factory=dict)
    skipped: Dict[str, str] = field(default_factory=dict)
    overwritten: Dict[str, str] = field(default_factory=dict)
    dry_run: bool = False

    @property
    def total_promoted(self) -> int:
        return len(self.promoted)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "destination": self.destination,
            "promoted": self.promoted,
            "skipped": self.skipped,
            "overwritten": self.overwritten,
            "dry_run": self.dry_run,
        }


def promote_env(
    source_path: str,
    dest_path: str,
    keys: Optional[List[str]] = None,
    overwrite: bool = False,
    dry_run: bool = False,
) -> PromoteResult:
    """Copy keys from source env to destination env.

    Args:
        source_path: Path to the source .env file.
        dest_path: Path to the destination .env file.
        keys: If provided, only promote these keys. Promotes all keys if None.
        overwrite: If True, overwrite existing keys in destination.
        dry_run: If True, compute result without writing to disk.

    Returns:
        PromoteResult describing what was promoted, skipped, or overwritten.
    """
    source_env = parse_env_file(source_path)
    dest_env = parse_env_file(dest_path)

    target_keys = keys if keys is not None else list(source_env.keys())

    result = PromoteResult(
        source=source_path,
        destination=dest_path,
        dry_run=dry_run,
    )

    merged = dict(dest_env)

    for key in target_keys:
        if key not in source_env:
            continue
        value = source_env[key]
        if key in dest_env:
            if overwrite:
                result.overwritten[key] = value
                merged[key] = value
            else:
                result.skipped[key] = value
        else:
            result.promoted[key] = value
            merged[key] = value

    if not dry_run:
        write_env_file(dest_path, merged)

    return result
