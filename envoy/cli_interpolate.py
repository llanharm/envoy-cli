"""CLI sub-command: envoy interpolate

Resolves variable references in a .env file and prints or writes the result.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envoy.interpolate import interpolate
from envoy.parser import parse_env_file, write_env_file


def build_interpolate_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser(
        "interpolate",
        help="Resolve $VAR / ${VAR} references inside a .env file.",
    )
    p.add_argument("file", help="Path to the .env file.")
    p.add_argument(
        "--output", "-o",
        metavar="FILE",
        help="Write resolved values to FILE instead of stdout.",
    )
    p.add_argument(
        "--format",
        choices=["env", "json"],
        default="env",
        help="Output format (default: env).",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 if any references cannot be resolved.",
    )
    p.set_defaults(func=cmd_interpolate)
    return p


def cmd_interpolate(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    env = parse_env_file(path)
    result = interpolate(env)

    if args.strict and not result.ok:
        if result.circular_keys:
            print(f"error: circular references: {', '.join(result.circular_keys)}", file=sys.stderr)
        if result.unresolved_keys:
            print(f"error: unresolved keys: {', '.join(result.unresolved_keys)}", file=sys.stderr)
        return 1

    if args.format == "json":
        text = json.dumps(result.resolved, indent=2)
    else:
        lines = [f"{k}={v}" for k, v in result.resolved.items()]
        text = "\n".join(lines)

    if args.output:
        out = Path(args.output)
        if args.format == "env":
            write_env_file(out, result.resolved)
        else:
            out.write_text(text)
        print(f"Written to {out}")
    else:
        print(text)

    return 0
