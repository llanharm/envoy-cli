"""Audit log for tracking .env file changes and vault sync operations."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


@dataclass
class AuditEntry:
    timestamp: str
    action: str          # 'push', 'pull', 'diff'
    env_file: str
    vault_path: Optional[str]
    keys_added: List[str] = field(default_factory=list)
    keys_removed: List[str] = field(default_factory=list)
    keys_changed: List[str] = field(default_factory=list)
    dry_run: bool = False
    user: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


class AuditLog:
    def __init__(self, log_path: str | Path) -> None:
        self.log_path = Path(log_path)

    def _current_user(self) -> str:
        return os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"

    def record(
        self,
        action: str,
        env_file: str,
        vault_path: Optional[str] = None,
        keys_added: Optional[List[str]] = None,
        keys_removed: Optional[List[str]] = None,
        keys_changed: Optional[List[str]] = None,
        dry_run: bool = False,
    ) -> AuditEntry:
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            action=action,
            env_file=str(env_file),
            vault_path=vault_path,
            keys_added=keys_added or [],
            keys_removed=keys_removed or [],
            keys_changed=keys_changed or [],
            dry_run=dry_run,
            user=self._current_user(),
        )
        self._append(entry)
        return entry

    def _append(self, entry: AuditEntry) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry.to_dict()) + "\n")

    def read_all(self) -> List[AuditEntry]:
        if not self.log_path.exists():
            return []
        entries: List[AuditEntry] = []
        with self.log_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    entries.append(AuditEntry(**data))
        return entries

    def tail(self, n: int = 20) -> List[AuditEntry]:
        return self.read_all()[-n:]
