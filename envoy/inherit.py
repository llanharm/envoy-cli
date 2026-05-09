"""Env file inheritance — merge a child .env on top of one or more parent files."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envoy.parser import parse_env_file, write_env_file


@dataclass
class InheritResult:
    base_files: List[Path]
    child_file: Path
    merged: Dict[str, str]
    overridden_keys: List[str] = field(default_factory=list)
    inherited_keys: List[str] = field(default_factory=list)

    @property
    def total_keys(self) -> int:
        return len(self.merged)

    def to_dict(self) -> dict:
        return {
            "base_files": [str(p) for p in self.base_files],
            "child_file": str(self.child_file),
            "total_keys": self.total_keys,
            "overridden_keys": self.overridden_keys,
            "inherited_keys": self.inherited_keys,
        }


def inherit_env(
    base_paths: List[Path],
    child_path: Path,
    output_path: Optional[Path] = None,
    dry_run: bool = False,
) -> InheritResult:
    """Merge one or more base env files with a child, child values win.

    Args:
        base_paths: Ordered list of base .env files (earlier = lower priority).
        child_path: Child .env whose values override the bases.
        output_path: Where to write the merged result. Defaults to child_path.
        dry_run: When True the merged file is not written to disk.

    Returns:
        InheritResult describing the merged environment.
    """
    if not base_paths:
        raise ValueError("At least one base file is required.")

    merged: Dict[str, str] = {}
    for base in base_paths:
        merged.update(parse_env_file(base))

    child_env = parse_env_file(child_path)

    inherited_keys = [k for k in merged if k not in child_env]
    overridden_keys = [k for k in child_env if k in merged]

    merged.update(child_env)
    # Keys present only in child (new keys) are silently included.

    if not dry_run:
        dest = output_path or child_path
        write_env_file(dest, merged)

    return InheritResult(
        base_files=list(base_paths),
        child_file=child_path,
        merged=merged,
        overridden_keys=sorted(overridden_keys),
        inherited_keys=sorted(inherited_keys),
    )
