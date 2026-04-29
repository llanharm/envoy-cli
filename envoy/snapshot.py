"""Snapshot support: capture and compare .env file states over time."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from envoy.parser import parse_env_file
from envoy.diff import diff_envs, EnvDiff


@dataclass
class Snapshot:
    path: str
    captured_at: str
    values: Dict[str, str]
    label: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "captured_at": self.captured_at,
            "label": self.label,
            "values": self.values,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        return cls(
            path=data["path"],
            captured_at=data["captured_at"],
            label=data.get("label"),
            values=data["values"],
        )


@dataclass
class SnapshotStore:
    store_path: Path
    _snapshots: List[Snapshot] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.store_path = Path(self.store_path)
        if self.store_path.exists():
            self._load()

    def _load(self) -> None:
        with self.store_path.open() as fh:
            raw = json.load(fh)
        self._snapshots = [Snapshot.from_dict(d) for d in raw]

    def _save(self) -> None:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        with self.store_path.open("w") as fh:
            json.dump([s.to_dict() for s in self._snapshots], fh, indent=2)

    def capture(self, env_path: str, label: Optional[str] = None) -> Snapshot:
        values = parse_env_file(env_path)
        snap = Snapshot(
            path=env_path,
            captured_at=datetime.now(timezone.utc).isoformat(),
            values=values,
            label=label,
        )
        self._snapshots.append(snap)
        self._save()
        return snap

    def list_snapshots(self, env_path: Optional[str] = None) -> List[Snapshot]:
        if env_path is None:
            return list(self._snapshots)
        return [s for s in self._snapshots if s.path == env_path]

    def compare(self, env_path: str, index_a: int = -2, index_b: int = -1) -> EnvDiff:
        snaps = self.list_snapshots(env_path)
        if len(snaps) < 2:
            raise ValueError(f"Need at least 2 snapshots for '{env_path}', found {len(snaps)}.")
        snap_a = snaps[index_a]
        snap_b = snaps[index_b]
        return diff_envs(snap_a.values, snap_b.values)
