"""Track and query the change history of .env files over time."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


HISTORY_VERSION = 1


@dataclass
class HistoryEntry:
    timestamp: float
    path: str
    event: str  # "push", "pull", "edit", "rotate", "merge"
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    changed: List[str] = field(default_factory=list)
    actor: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "path": self.path,
            "event": self.event,
            "added": self.added,
            "removed": self.removed,
            "changed": self.changed,
            "actor": self.actor,
        }

    @staticmethod
    def from_dict(data: dict) -> "HistoryEntry":
        return HistoryEntry(
            timestamp=data["timestamp"],
            path=data["path"],
            event=data["event"],
            added=data.get("added", []),
            removed=data.get("removed", []),
            changed=data.get("changed", []),
            actor=data.get("actor"),
        )


class HistoryStore:
    def __init__(self, store_path: Path) -> None:
        self._path = store_path
        self._entries: List[HistoryEntry] = []
        if store_path.exists():
            self._load()

    def _load(self) -> None:
        raw = json.loads(self._path.read_text())
        self._entries = [HistoryEntry.from_dict(e) for e in raw.get("entries", [])]

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {"version": HISTORY_VERSION, "entries": [e.to_dict() for e in self._entries]}
        self._path.write_text(json.dumps(data, indent=2))

    def record(
        self,
        path: str,
        event: str,
        added: List[str] = (),
        removed: List[str] = (),
        changed: List[str] = (),
        actor: Optional[str] = None,
    ) -> HistoryEntry:
        entry = HistoryEntry(
            timestamp=time.time(),
            path=path,
            event=event,
            added=list(added),
            removed=list(removed),
            changed=list(changed),
            actor=actor,
        )
        self._entries.append(entry)
        self._save()
        return entry

    def query(
        self,
        path: Optional[str] = None,
        event: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[HistoryEntry]:
        results = [
            e for e in self._entries
            if (path is None or e.path == path)
            and (event is None or e.event == event)
        ]
        results = list(reversed(results))
        if limit is not None:
            results = results[:limit]
        return results

    def clear(self, path: Optional[str] = None) -> int:
        before = len(self._entries)
        if path is None:
            self._entries = []
        else:
            self._entries = [e for e in self._entries if e.path != path]
        self._save()
        return before - len(self._entries)
