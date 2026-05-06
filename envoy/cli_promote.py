"""CLI subcommand for promoting .env values between environments."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from envoy.promote import promote_env


def build_promote_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    p = subparsers.add_parser(
        "promote",
        help="Promote env values from one file to another.",
    )
    p.add_argument("source", help="Source .env file path.")
    p.add_argument("destination", help="Destination .env file path.")
    p.add_argument(
        "--keys",
        nargs="+",
        metavar="KEY",
        default=None,
        help="Specific keys to promote. Promotes all keys if omitted.",
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing keys in the destination file.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Show what would be promoted without writing changes.",
    )
    p.add_argument(
        "--json",
        dest="output_json",
        action="store_true",
        default=False,
        help="Output result as JSON.",
    )
    return p


def cmd_promote(args: argparse.Namespace) -> int:
    try:
        result = promote_env(
            source_path=args.source,
            dest_path=args.destination,
            keys=args.keys,
            overwrite=args.overwrite,
            dry_run=args.dry_run,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.output_json:
        print(json.dumps(result.to_dict(), indent=2))
        return 0

    tag = "[dry-run] " if result.dry_run else ""
    print(f"{tag}Promoting from '{result.source}' → '{result.destination}'")

    if result.promoted:
        print(f"  Promoted ({len(result.promoted)}): {', '.join(result.promoted)}")
    if result.overwritten:
        print(f"  Overwritten ({len(result.overwritten)}): {', '.join(result.overwritten)}")
    if result.skipped:
        print(f"  Skipped ({len(result.skipped)}): {', '.join(result.skipped)}")
    if not result.promoted and not result.overwritten:
        print("  Nothing to promote.")

    return 0
