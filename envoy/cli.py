"""Command-line interface for envoy-cli.

Provides commands for parsing, diffing, and syncing .env files
with vault backends.
"""

import sys
import argparse
from pathlib import Path

from envoy.parser import parse_env_file, write_env_file, EnvParseError
from envoy.diff import diff_envs, has_changes, summary
from envoy.sync import push_to_vault, pull_from_vault, SyncResult
from envoy.vault import VaultClient, VaultConfigError


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy",
        description="Manage and audit .env files across projects with vault sync support.",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    # --- diff ---
    diff_parser = subparsers.add_parser(
        "diff",
        help="Show differences between two .env files.",
    )
    diff_parser.add_argument("base", metavar="BASE", help="Base .env file path.")
    diff_parser.add_argument("target", metavar="TARGET", help="Target .env file path.")
    diff_parser.add_argument(
        "--no-mask",
        action="store_true",
        default=False,
        help="Show actual secret values instead of masked output.",
    )

    # --- push ---
    push_parser = subparsers.add_parser(
        "push",
        help="Push a .env file to Vault.",
    )
    push_parser.add_argument("env_file", metavar="ENV_FILE", help="Path to the .env file.")
    push_parser.add_argument("vault_path", metavar="VAULT_PATH", help="Vault secret path.")
    push_parser.add_argument("--dry-run", action="store_true", default=False,
                             help="Preview changes without writing to Vault.")
    push_parser.add_argument("--vault-url", default="http://127.0.0.1:8200",
                             help="Vault server URL (default: http://127.0.0.1:8200).")
    push_parser.add_argument("--vault-token", default=None,
                             help="Vault token (falls back to VAULT_TOKEN env var).")

    # --- pull ---
    pull_parser = subparsers.add_parser(
        "pull",
        help="Pull secrets from Vault into a .env file.",
    )
    pull_parser.add_argument("vault_path", metavar="VAULT_PATH", help="Vault secret path.")
    pull_parser.add_argument("env_file", metavar="ENV_FILE", help="Destination .env file path.")
    pull_parser.add_argument("--dry-run", action="store_true", default=False,
                             help="Preview changes without writing the file.")
    pull_parser.add_argument("--vault-url", default="http://127.0.0.1:8200",
                             help="Vault server URL (default: http://127.0.0.1:8200).")
    pull_parser.add_argument("--vault-token", default=None,
                             help="Vault token (falls back to VAULT_TOKEN env var).")

    return parser


def cmd_diff(args: argparse.Namespace) -> int:
    """Handle the `diff` subcommand."""
    try:
        base_env = parse_env_file(Path(args.base))
        target_env = parse_env_file(Path(args.target))
    except EnvParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"error: file not found — {exc.filename}", file=sys.stderr)
        return 1

    result = diff_envs(base_env, target_env)

    if not has_changes(result):
        print("No differences found.")
        return 0

    mask = not args.no_mask
    print(summary(result, mask=mask))
    return 0


def _make_vault_client(args: argparse.Namespace) -> VaultClient | None:
    """Construct a VaultClient from CLI args, printing errors on failure."""
    try:
        return VaultClient(url=args.vault_url, token=args.vault_token)
    except VaultConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return None


def cmd_push(args: argparse.Namespace) -> int:
    """Handle the `push` subcommand."""
    client = _make_vault_client(args)
    if client is None:
        return 1

    try:
        result: SyncResult = push_to_vault(
            env_path=Path(args.env_file),
            vault_path=args.vault_path,
            client=client,
            dry_run=args.dry_run,
        )
    except (EnvParseError, FileNotFoundError, VaultConfigError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(result.message)
    return 0


def cmd_pull(args: argparse.Namespace) -> int:
    """Handle the `pull` subcommand."""
    client = _make_vault_client(args)
    if client is None:
        return 1

    try:
        result: SyncResult = pull_from_vault(
            vault_path=args.vault_path,
            env_path=Path(args.env_file),
            client=client,
            dry_run=args.dry_run,
        )
    except (VaultConfigError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(result.message)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point for the envoy CLI."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    dispatch = {
        "diff": cmd_diff,
        "push": cmd_push,
        "pull": cmd_pull,
    }

    return dispatch[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
