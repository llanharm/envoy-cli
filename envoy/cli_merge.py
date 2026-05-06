"""CLI sub-command: envoy merge — merge multiple .env files."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envoy.merge import MergeConflictError, Strategy, merge_env_files
from envoy.parser import write_env_file


def build_merge_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    p = subparsers.add_parser(
        "merge",
        help="Merge two or more .env files into one.",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help=".env files to merge (at least two required).",
    )
    p.add_argument(
        "--strategy",
        choices=[s.value for s in Strategy],
        default=Strategy.LAST.value,
        help="Conflict resolution strategy (default: last).",
    )
    p.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help="Write merged result to FILE instead of stdout.",
    )
    p.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Output result as JSON (includes conflict details).",
    )
    p.add_argument(
        "--set",
        dest="overrides",
        metavar="KEY=VALUE",
        action="append",
        default=[],
        help="Override a key after merging (repeatable).",
    )
    return p


def _parse_overrides(pairs: List[str]) -> dict:
    result = {}
    for pair in pairs:
        if "=" not in pair:
            raise argparse.ArgumentTypeError(f"--set value must be KEY=VALUE, got: {pair!r}")
        k, _, v = pair.partition("=")
        result[k.strip()] = v
    return result


def cmd_merge(args: argparse.Namespace) -> int:
    if len(args.files) < 2:
        print("error: merge requires at least two .env files.", file=sys.stderr)
        return 1

    strategy = Strategy(args.strategy)

    try:
        overrides = _parse_overrides(args.overrides)
    except argparse.ArgumentTypeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        result = merge_env_files(args.files, strategy=strategy, overrides=overrides or None)
    except MergeConflictError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except (FileNotFoundError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.as_json:
        print(json.dumps(result.to_dict(), indent=2))
        return 0

    if not result.ok:
        for conflict in result.conflicts:
            sources = ", ".join(f"{p}={v}" for p, v in conflict.values.items())
            print(f"warning: conflict on '{conflict.key}' — {sources}", file=sys.stderr)

    if args.output:
        write_env_file(args.output, result.merged)
        print(f"Merged {len(args.files)} files → {args.output} ({len(result.merged)} keys).")
    else:
        for key, value in result.merged.items():
            print(f"{key}={value}")

    return 0
