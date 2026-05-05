"""File-system watcher that detects .env file changes and emits diffs."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Optional

from envoy.diff import diff_envs, EnvDiff
from envoy.parser import parse_env_file


@dataclass
class WatchEvent:
    path: Path
    diff: EnvDiff
    detected_at: float = field(default_factory=time.time)

    def has_changes(self) -> bool:
        return self.diff.has_changes()


def _file_hash(path: Path) -> str:
    """Return MD5 hex-digest of *path* contents."""
    return hashlib.md5(path.read_bytes()).hexdigest()


class EnvWatcher:
    """Poll one or more .env files and invoke a callback on changes."""

    def __init__(
        self,
        paths: list[Path],
        on_change: Callable[[WatchEvent], None],
        interval: float = 1.0,
    ) -> None:
        if not paths:
            raise ValueError("At least one path must be provided.")
        self.paths = paths
        self.on_change = on_change
        self.interval = interval
        self._hashes: Dict[Path, str] = {}
        self._snapshots: Dict[Path, dict] = {}

    def _seed(self) -> None:
        """Capture initial hashes and parsed content."""
        for p in self.paths:
            if p.exists():
                self._hashes[p] = _file_hash(p)
                self._snapshots[p] = parse_env_file(p)

    def _check_once(self) -> None:
        for p in self.paths:
            if not p.exists():
                continue
            current_hash = _file_hash(p)
            if current_hash == self._hashes.get(p):
                continue
            old = self._snapshots.get(p, {})
            new = parse_env_file(p)
            self._hashes[p] = current_hash
            self._snapshots[p] = new
            event = WatchEvent(path=p, diff=diff_envs(old, new))
            self.on_change(event)

    def watch(self, max_iterations: Optional[int] = None) -> None:
        """Block and poll until interrupted or *max_iterations* reached."""
        self._seed()
        iterations = 0
        try:
            while True:
                self._check_once()
                iterations += 1
                if max_iterations is not None and iterations >= max_iterations:
                    break
                time.sleep(self.interval)
        except KeyboardInterrupt:
            pass
