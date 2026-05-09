"""CLI sub-command: envoy mask — display env file with sensitive values masked."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envoy.mask import mask_env
from envoy.parser import EnvParseError, parse_env_file


def build_mask_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser("mask", help="Display env file with sensitive values masked")
    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "--partial",
        action="store_true",
        default=False,
        help="Reveal first/last characters instead of full mask",
    )
    p.add_argument(
        "--mask-char",
        default="***",
        metavar="MASK",
        help="Replacement string for masked values (default: ***)",
    )
    p.add_argument(
        "--only",
        nargs="+",
        metavar="KEY",
        help="Restrict masking to these specific keys",
    )
    p.add_argument(
        "--pattern",
        nargs="+",
        metavar="REGEX",
        dest="extra_patterns",
        help="Extra regex patterns to flag as sensitive",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    return p


def cmd_mask(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    try:
        env = parse_env_file(path)
    except EnvParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    result = mask_env(
        env,
        extra_patterns=getattr(args, "extra_patterns", None),
        partial=args.partial,
        mask=args.mask_char,
        only_keys=getattr(args, "only", None),
    )

    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2))
    else:
        for key, value in result.masked.items():
            print(f"{key}={value}")
        print(
            f"\n# {result.total_masked} key(s) masked, {len(result.keys_skipped)} skipped",
            file=sys.stderr,
        )

    return 0
