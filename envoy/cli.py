"""Main CLI entry-point for envoy-cli."""
from __future__ import annotations

import argparse
import sys

from envoy.diff import diff_envs
from envoy.parser import parse_env_file, EnvParseError
from envoy.report import render_text, render_json
from envoy.redact import redact
from envoy.vault import VaultClient, VaultConfigError
from envoy.sync import push_to_vault, pull_from_vault
from envoy.cli_audit import build_audit_parser, cmd_audit
from envoy.cli_report import build_report_parser, cmd_report
from envoy.cli_snapshot import build_snapshot_parser, cmd_snapshot
from envoy.cli_lint import build_lint_parser, cmd_lint


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy",
        description="Manage and audit .env files across projects",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    # diff
    p_diff = sub.add_parser("diff", help="Diff two .env files")
    p_diff.add_argument("file_a", help="Base .env file")
    p_diff.add_argument("file_b", help="Target .env file")
    p_diff.add_argument("--mask", action="store_true", help="Mask secret values")
    p_diff.add_argument("--format", choices=["text", "json"], default="text")

    # push
    p_push = sub.add_parser("push", help="Push .env to Vault")
    p_push.add_argument("file", help=".env file to push")
    p_push.add_argument("--path", required=True, help="Vault secret path")
    p_push.add_argument("--dry-run", action="store_true")

    # pull
    p_pull = sub.add_parser("pull", help="Pull secrets from Vault into .env")
    p_pull.add_argument("file", help="Destination .env file")
    p_pull.add_argument("--path", required=True, help="Vault secret path")
    p_pull.add_argument("--dry-run", action="store_true")

    build_audit_parser(sub)
    build_report_parser(sub)
    build_snapshot_parser(sub)
    build_lint_parser(sub)

    return parser


def cmd_diff(args: argparse.Namespace) -> int:
    try:
        env_a = parse_env_file(args.file_a)
        env_b = parse_env_file(args.file_b)
    except (EnvParseError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    diff = diff_envs(env_a, env_b)
    redact_result = redact(env_b)
    masked = env_b if not args.mask else {k: redact_result.redacted.get(k, v) for k, v in env_b.items()}

    if args.format == "json":
        print(render_json(diff, redact_result))
    else:
        print(render_text(diff, redact_result, title=f"{args.file_a} → {args.file_b}"))

    return 0 if not diff.has_changes() else 1


def _make_vault_client() -> VaultClient:
    return VaultClient()


def cmd_push(args: argparse.Namespace) -> int:
    try:
        client = _make_vault_client()
        env = parse_env_file(args.file)
    except (VaultConfigError, EnvParseError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    result = push_to_vault(env, client, args.path, dry_run=args.dry_run)
    status = "(dry-run) " if args.dry_run else ""
    print(f"{status}push {args.path}: written={result.written} skipped={result.skipped}")
    return 0


def cmd_pull(args: argparse.Namespace) -> int:
    try:
        client = _make_vault_client()
    except VaultConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    result = pull_from_vault(client, args.path, args.file, dry_run=args.dry_run)
    status = "(dry-run) " if args.dry_run else ""
    print(f"{status}pull {args.path}: written={result.written} skipped={result.skipped}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    dispatch = {
        "diff": cmd_diff,
        "push": cmd_push,
        "pull": cmd_pull,
        "audit": cmd_audit,
        "report": cmd_report,
        "snapshot": cmd_snapshot,
        "lint": cmd_lint,
    }

    if args.command is None:
        parser.print_help()
        return 0

    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
