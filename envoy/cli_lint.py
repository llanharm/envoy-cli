"""CLI sub-commands for .env linting."""
from __future__ import annotations

import argparse
import json
import sys

from envoy.lint import LintIssue, lint_env_file


def build_lint_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser("lint", help="Lint a .env file for common issues")
    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 on warnings as well as errors",
    )
    return p


def _format_issue_text(issue: LintIssue) -> str:
    key_part = f" [{issue.key}]" if issue.key else ""
    return f"  line {issue.line:>3}{key_part}  {issue.code}  {issue.message}"


def cmd_lint(args: argparse.Namespace) -> int:
    """Run lint and print results; returns exit code."""
    try:
        result = lint_env_file(args.file)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps([i.to_dict() for i in result.issues], indent=2))
    else:
        if result.ok:
            print(f"OK  {args.file} — no issues found.")
        else:
            print(f"Linting {args.file}:")
            for issue in result.issues:
                print(_format_issue_text(issue))
            print(f"\n{len(result.issues)} issue(s) found.")

    errors = [i for i in result.issues if i.code.startswith("E")]
    warnings = [i for i in result.issues if i.code.startswith("W")]

    if errors:
        return 1
    if args.strict and warnings:
        return 1
    return 0
