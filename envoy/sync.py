"""Sync logic between local .env files and Vault."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, NamedTuple, Optional

from envoy.diff import diff_envs
from envoy.parser import parse_env_file, write_env_file
from envoy.vault import VaultClient


class SyncResult(NamedTuple):
    pushed: int
    pulled: int
    skipped: int
    path: str
    vault_path: str


def push_to_vault(
    env_path: str,
    vault_path: str,
    client: VaultClient,
    dry_run: bool = False,
) -> SyncResult:
    """Push local .env file contents to Vault.

    Returns a SyncResult describing what was written.
    """
    local: Dict[str, str] = parse_env_file(env_path)

    try:
        remote: Dict[str, str] = client.read_secrets(vault_path)
    except Exception:
        remote = {}

    diff = diff_envs(local, remote)
    changed_count = len(diff.added) + len(diff.changed) + len(diff.removed)

    if changed_count and not dry_run:
        client.write_secrets(vault_path, local)

    return SyncResult(
        pushed=changed_count if not dry_run else 0,
        pulled=0,
        skipped=len(diff.unchanged),
        path=env_path,
        vault_path=vault_path,
    )


def pull_from_vault(
    env_path: str,
    vault_path: str,
    client: VaultClient,
    dry_run: bool = False,
    merge: bool = False,
) -> SyncResult:
    """Pull secrets from Vault and write to a local .env file.

    If *merge* is True, existing local keys not present in Vault are kept.
    """
    remote: Dict[str, str] = client.read_secrets(vault_path)

    if merge and Path(env_path).exists():
        local: Dict[str, str] = parse_env_file(env_path)
        merged = {**local, **remote}
    else:
        local = {}
        merged = remote

    diff = diff_envs(remote, local)
    changed_count = len(diff.added) + len(diff.changed) + len(diff.removed)

    if not dry_run:
        write_env_file(env_path, merged)

    return SyncResult(
        pushed=0,
        pulled=changed_count if not dry_run else 0,
        skipped=len(diff.unchanged),
        path=env_path,
        vault_path=vault_path,
    )
