"""CLI helpers for the `envoy audit` sub-command."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import List

from envoy.audit import AuditEntry, AuditLog

DEFAULT_LOG_PATH = os.environ.get("ENVOY_AUDIT_LOG", ".envoy_audit.log")


def _format_entry(entry: AuditEntry) -> str:
    ts = entry.timestamp[:19].replace("T", " ")
    parts = [f"[{ts}] {entry.action.upper():6s}  {entry.env_file}"]
    if entry.vault_path:
        parts.append(f"  vault={entry.vault_path}")
    if entry.dry_run:
        parts.append("  (dry-run)")
    if entry.user:
        parts.append(f"  user={entry.user}")
    changes: List[str] = []
    if entry.keys_added:
        changes.append(f"+{len(entry.keys_added)} added")
    if entry.keys_removed:
        changes.append(f"-{len(entry.keys_removed)} removed")
    if entry.keys_changed:
        changes.append(f"~{len(entry.keys_changed)} changed")
    if changes:
        parts.append("  [" + ", ".join(changes) + "]")
    return "".join(parts)


def build_audit_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("audit", help="Show audit log of env operations")
    p.add_argument(
        "--log",
        default=DEFAULT_LOG_PATH,
        metavar="FILE",
        help="Path to audit log file (default: %(default)s)",
    )
    p.add_argument(
        "--tail",
        type=int,
        default=20,
        metavar="N",
        help="Show last N entries (default: %(default)s)",
    )
    p.add_argument(
        "--action",
        choices=["push", "pull", "diff"],
        default=None,
        help="Filter by action type",
    )
    p.set_defaults(func=cmd_audit)


def cmd_audit(args: argparse.Namespace) -> int:
    log = AuditLog(Path(args.log))
    entries = log.tail(args.tail)

    if args.action:
        entries = [e for e in entries if e.action == args.action]

    if not entries:
        print("No audit entries found.")
        return 0

    for entry in entries:
        print(_format_entry(entry))

    return 0
