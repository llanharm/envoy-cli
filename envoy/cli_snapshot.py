"""CLI subcommands for snapshot management."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envoy.snapshot import SnapshotStore
from envoy.report import render_text
from envoy.diff import diff_envs

_DEFAULT_STORE = Path(".envoy") / "snapshots.json"


def build_snapshot_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    snap_parser = subparsers.add_parser("snapshot", help="Manage .env snapshots")
    snap_sub = snap_parser.add_subparsers(dest="snap_cmd", required=True)

    # capture
    cap = snap_sub.add_parser("capture", help="Capture a snapshot of an .env file")
    cap.add_argument("env_file", help="Path to .env file")
    cap.add_argument("--label", default=None, help="Optional label for the snapshot")
    cap.add_argument("--store", default=str(_DEFAULT_STORE), help="Snapshot store path")

    # list
    ls = snap_sub.add_parser("list", help="List captured snapshots")
    ls.add_argument("env_file", nargs="?", default=None, help="Filter by .env file path")
    ls.add_argument("--store", default=str(_DEFAULT_STORE), help="Snapshot store path")

    # compare
    cmp = snap_sub.add_parser("compare", help="Diff two snapshots of an .env file")
    cmp.add_argument("env_file", help="Path to .env file")
    cmp.add_argument("--store", default=str(_DEFAULT_STORE), help="Snapshot store path")
    cmp.add_argument("--index-a", type=int, default=-2, help="Index of first snapshot (default: second-to-last)")
    cmp.add_argument("--index-b", type=int, default=-1, help="Index of second snapshot (default: last)")

    snap_parser.set_defaults(func=cmd_snapshot)


def cmd_snapshot(args: argparse.Namespace) -> int:
    store = SnapshotStore(store_path=args.store)

    if args.snap_cmd == "capture":
        snap = store.capture(args.env_file, label=args.label)
        label_str = f" [{snap.label}]" if snap.label else ""
        print(f"Snapshot captured{label_str}: {snap.captured_at}  ({len(snap.values)} keys)")
        return 0

    if args.snap_cmd == "list":
        snaps = store.list_snapshots(args.env_file)
        if not snaps:
            print("No snapshots found.")
            return 0
        for i, s in enumerate(snaps):
            label_str = f" [{s.label}]" if s.label else ""
            print(f"  [{i}]{label_str} {s.captured_at}  {s.path}  ({len(s.values)} keys)")
        return 0

    if args.snap_cmd == "compare":
        try:
            diff = store.compare(args.env_file, index_a=args.index_a, index_b=args.index_b)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        title = f"Snapshot diff: {args.env_file}"
        print(render_text(title, diff, None))
        return 0

    return 1
