"""CLI sub-command: envoy inherit — apply env inheritance."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envoy.inherit import inherit_env
from envoy.parser import EnvParseError


def build_inherit_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser(
        "inherit",
        help="Merge base .env file(s) into a child .env (child values win).",
    )
    p.add_argument("child", help="Child .env file whose values take priority.")
    p.add_argument(
        "--base",
        dest="bases",
        metavar="FILE",
        action="append",
        required=True,
        help="Base .env file (can be repeated; earlier = lower priority).",
    )
    p.add_argument(
        "--output",
        metavar="FILE",
        help="Write merged result here instead of overwriting child.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print result without writing to disk.",
    )
    p.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Output summary as JSON.",
    )
    return p


def cmd_inherit(args: argparse.Namespace) -> int:
    child = Path(args.child)
    bases = [Path(b) for b in args.bases]
    output = Path(args.output) if getattr(args, "output", None) else None

    for p in bases + [child]:
        if not p.exists():
            print(f"error: file not found: {p}", file=sys.stderr)
            return 1

    try:
        result = inherit_env(
            base_paths=bases,
            child_path=child,
            output_path=output,
            dry_run=args.dry_run,
        )
    except EnvParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.as_json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        dest = output or child
        action = "(dry run)" if args.dry_run else f"→ {dest}"
        print(f"inherit {action}")
        print(f"  total keys   : {result.total_keys}")
        print(f"  inherited    : {len(result.inherited_keys)}  {result.inherited_keys}")
        print(f"  overridden   : {len(result.overridden_keys)}  {result.overridden_keys}")

    return 0
