"""Unit tests for envoy.sync."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from envoy.sync import pull_from_vault, push_to_vault


@pytest.fixture()
def tmp_env(tmp_path):
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nDB_PASS=secret\n")
    return str(p)


@pytest.fixture()
def vault_client():
    client = MagicMock()
    client.read_secrets.return_value = {"DB_HOST": "localhost", "DB_PASS": "secret"}
    return client


# ── push ──────────────────────────────────────────────────────────────────────

def test_push_writes_when_changed(tmp_env, vault_client):
    vault_client.read_secrets.return_value = {}  # remote is empty
    result = push_to_vault(tmp_env, "app/prod", vault_client)
    vault_client.write_secrets.assert_called_once()
    assert result.pushed == 2
    assert result.skipped == 0


def test_push_skips_when_identical(tmp_env, vault_client):
    # remote already matches local
    result = push_to_vault(tmp_env, "app/prod", vault_client)
    vault_client.write_secrets.assert_not_called()
    assert result.pushed == 0
    assert result.skipped == 2


def test_push_dry_run_does_not_write(tmp_env, vault_client):
    vault_client.read_secrets.return_value = {}
    result = push_to_vault(tmp_env, "app/prod", vault_client, dry_run=True)
    vault_client.write_secrets.assert_not_called()
    assert result.pushed == 0


# ── pull ──────────────────────────────────────────────────────────────────────

def test_pull_writes_env_file(tmp_path, vault_client):
    env_path = str(tmp_path / ".env.new")
    result = pull_from_vault(env_path, "app/prod", vault_client)
    assert result.pulled == 2
    with open(env_path) as f:
        content = f.read()
    assert "DB_HOST" in content


def test_pull_dry_run_does_not_write(tmp_path, vault_client):
    env_path = str(tmp_path / ".env.new")
    result = pull_from_vault(env_path, "app/prod", vault_client, dry_run=True)
    assert not (tmp_path / ".env.new").exists()
    assert result.pulled == 0


def test_pull_merge_preserves_local_keys(tmp_env, vault_client):
    vault_client.read_secrets.return_value = {"DB_HOST": "prod-host"}
    result = pull_from_vault(tmp_env, "app/prod", vault_client, merge=True)
    with open(tmp_env) as f:
        content = f.read()
    # DB_PASS was local-only and should survive the merge
    assert "DB_PASS" in content
    assert "prod-host" in content
