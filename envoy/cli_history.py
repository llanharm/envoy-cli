"""CLI sub-commands for browsing .env change history."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from envoy.history import HistoryStore


_DEFAULT_STORE = Path.home() / ".envoy" / "history.json"


def build_history_parser(parent: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = parent.add_parser("history", help="Browse .env change history")
    sub = p.add_subparsers(dest="history_cmd", required=True)

    ls = sub.add_parser("list", help="List recorded history entries")
    ls.add_argument("--path", metavar="FILE", help="Filter by env file path")
    ls.add_argument("--event", metavar="EVENT", help="Filter by event type")
    ls.add_argument("--limit", type=int, default=20, metavar="N")
    ls.add_argument("--json", dest="as_json", action="store_true")
    ls.add_argument("--store", default=str(_DEFAULT_STORE), metavar="FILE")

    cl = sub.add_parser("clear", help="Delete history entries")
    cl.add_argument("--path", metavar="FILE", help="Clear only entries for this file")
    cl.add_argument("--store", default=str(_DEFAULT_STORE), metavar="FILE")

    return p


def _format_entry(entry) -> str:
    ts = datetime.fromtimestamp(entry.timestamp).strftime("%Y-%m-%d %H:%M:%S")
    actor = f" [{entry.actor}]" if entry.actor else ""
    parts = []
    if entry.added:
        parts.append(f"+{len(entry.added)} added")
    if entry.removed:
        parts.append(f"-{len(entry.removed)} removed")
    if entry.changed:
        parts.append(f"~{len(entry.changed)} changed")
    summary = ", ".join(parts) if parts else "no key changes"
    return f"{ts}  {entry.event:10s}  {entry.path}{actor}  ({summary})"


def cmd_history(args: argparse.Namespace) -> int:
    store = HistoryStore(Path(args.store))

    if args.history_cmd == "list":
        entries = store.query(
            path=getattr(args, "path", None),
            event=getattr(args, "event", None),
            limit=args.limit,
        )
        if not entries:
            print("No history entries found.")
            return 0
        if args.as_json:
            print(json.dumps([e.to_dict() for e in entries], indent=2))
        else:
            for e in entries:
                print(_format_entry(e))
        return 0

    if args.history_cmd == "clear":
        removed = store.clear(path=getattr(args, "path", None))
        print(f"Cleared {removed} history entry/entries.")
        return 0

    return 1
