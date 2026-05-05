"""CLI sub-command: envoy watch — live monitor .env files for changes."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envoy.watch import EnvWatcher, WatchEvent


def build_watch_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("watch", help="Monitor .env file(s) for changes.")
    p.add_argument("files", nargs="+", type=Path, metavar="FILE", help=".env file(s) to watch.")
    p.add_argument(
        "--interval",
        type=float,
        default=1.0,
        metavar="SECONDS",
        help="Polling interval in seconds (default: 1.0).",
    )
    p.add_argument(
        "--mask",
        action="store_true",
        help="Mask secret values in output.",
    )
    return p


def _print_event(event: WatchEvent, mask: bool = False) -> None:
    from envoy.diff import _mask as mask_val

    print(f"\n[watch] Change detected in {event.path}")
    d = event.diff
    for k in sorted(d.added):
        val = mask_val(d.added[k]) if mask else d.added[k]
        print(f"  + {k}={val}")
    for k in sorted(d.removed):
        print(f"  - {k}")
    for k in sorted(d.changed):
        old_v = mask_val(d.changed[k][0]) if mask else d.changed[k][0]
        new_v = mask_val(d.changed[k][1]) if mask else d.changed[k][1]
        print(f"  ~ {k}: {old_v!r} -> {new_v!r}")


def cmd_watch(args: argparse.Namespace) -> int:
    missing = [str(p) for p in args.files if not p.exists()]
    if missing:
        print(f"error: file(s) not found: {', '.join(missing)}", file=sys.stderr)
        return 1

    print(f"Watching {len(args.files)} file(s) — press Ctrl+C to stop.")

    def on_change(event: WatchEvent) -> None:
        _print_event(event, mask=args.mask)

    watcher = EnvWatcher(paths=args.files, on_change=on_change, interval=args.interval)
    watcher.watch()
    return 0
