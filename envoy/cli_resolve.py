"""CLI sub-command: resolve — layer multiple .env files and show effective values."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envoy.resolve import resolve_env_files


def build_resolve_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser(
        "resolve",
        help="Layer multiple .env files and display the effective environment.",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Env files in priority order (last file wins).",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text).",
    )
    p.add_argument(
        "--show-sources",
        action="store_true",
        help="Annotate each key with the file it came from.",
    )
    p.add_argument(
        "--show-overrides",
        action="store_true",
        help="List keys that were shadowed by a higher-priority file.",
    )
    p.set_defaults(func=cmd_resolve)
    return p


def cmd_resolve(args: argparse.Namespace) -> int:
    for f in args.files:
        if not Path(f).exists():
            print(f"error: file not found: {f}", file=sys.stderr)
            return 1

    try:
        result = resolve_env_files(args.files)
    except Exception as exc:  # pragma: no cover
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.fmt == "json":
        print(json.dumps(result.to_dict(), indent=2))
        return 0

    # --- text output ---
    print(f"# Resolved from {len(result.files)} file(s)  "
          f"({result.total_keys} keys, {result.total_overridden} overridden)\n")

    for key, value in sorted(result.effective.items()):
        annotation = f"  # {result.sources[key]}" if args.show_sources else ""
        print(f"{key}={value}{annotation}")

    if args.show_overrides and result.overridden:
        print("\n# Overridden keys:")
        for key, shadowed in sorted(result.overridden.items()):
            print(f"  {key}: shadowed in {', '.join(shadowed)}")

    return 0
