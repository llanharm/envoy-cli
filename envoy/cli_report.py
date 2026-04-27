"""CLI sub-commands for generating env reports."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from envoy.diff import diff_envs
from envoy.parser import parse_env_file
from envoy.redact import redact
from envoy.report import render_json, render_text


def build_report_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "report",
        help="Generate a report for one or two .env files",
    )
    p.add_argument("file", help="Primary .env file")
    p.add_argument(
        "--compare",
        metavar="FILE2",
        help="Optional second .env file to diff against",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--no-redact",
        action="store_true",
        help="Skip redaction of sensitive values",
    )
    p.add_argument(
        "--out",
        metavar="FILE",
        help="Write report to FILE instead of stdout",
    )
    p.set_defaults(func=cmd_report)


def cmd_report(args: argparse.Namespace) -> int:
    try:
        env_a = parse_env_file(Path(args.file))
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    diff = None
    if args.compare:
        try:
            env_b = parse_env_file(Path(args.compare))
        except Exception as exc:  # noqa: BLE001
            print(f"error: {exc}", file=sys.stderr)
            return 1
        diff = diff_envs(env_a, env_b)

    redact_result = None if args.no_redact else redact(env_a)

    renderer = render_json if args.fmt == "json" else render_text
    output = renderer(diff=diff, redact_result=redact_result, title=args.file)

    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
    else:
        print(output)

    return 0
