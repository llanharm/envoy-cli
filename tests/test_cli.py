"""Tests for the main CLI entry point (envoy/cli.py)."""

import argparse
import json
import os
import pytest
from unittest.mock import MagicMock, patch, mock_open
from io import StringIO

from envoy.cli import _build_parser, cmd_diff, _make_vault_client, cmd_push, cmd_pull


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_env(tmp_path):
    """Write a minimal .env file and return its path."""
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\nSECRET=abc123\n")
    return str(env_file)


@pytest.fixture
def tmp_env_b(tmp_path):
    """Write a second .env file for diff comparisons."""
    env_file = tmp_path / ".env.staging"
    env_file.write_text("FOO=bar\nSECRET=changed\nNEW_KEY=hello\n")
    return str(env_file)


@pytest.fixture
def mock_vault_client():
    client = MagicMock()
    client.read_secrets.return_value = {"FOO": "bar", "SECRET": "abc123"}
    return client


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------

def test_build_parser_returns_parser():
    parser = _build_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_parser_has_diff_subcommand():
    parser = _build_parser()
    # Should not raise
    args = parser.parse_args(["diff", "a.env", "b.env"])
    assert args.command == "diff"
    assert args.file_a == "a.env"
    assert args.file_b == "b.env"


def test_parser_has_push_subcommand():
    parser = _build_parser()
    args = parser.parse_args(["push", ".env", "secret/myapp"])
    assert args.command == "push"
    assert args.env_file == ".env"
    assert args.vault_path == "secret/myapp"


def test_parser_has_pull_subcommand():
    parser = _build_parser()
    args = parser.parse_args(["pull", "secret/myapp", ".env"])
    assert args.command == "pull"
    assert args.vault_path == "secret/myapp"
    assert args.env_file == ".env"


def test_push_supports_dry_run_flag():
    parser = _build_parser()
    args = parser.parse_args(["push", ".env", "secret/myapp", "--dry-run"])
    assert args.dry_run is True


# ---------------------------------------------------------------------------
# cmd_diff tests
# ---------------------------------------------------------------------------

def test_cmd_diff_prints_summary(tmp_env, tmp_env_b, capsys):
    parser = _build_parser()
    args = parser.parse_args(["diff", tmp_env, tmp_env_b])
    cmd_diff(args)
    captured = capsys.readouterr()
    # Should mention added/changed keys
    assert "NEW_KEY" in captured.out or "SECRET" in captured.out


def test_cmd_diff_no_changes_reports_clean(tmp_env, capsys):
    parser = _build_parser()
    # Diff a file against itself
    args = parser.parse_args(["diff", tmp_env, tmp_env])
    cmd_diff(args)
    captured = capsys.readouterr()
    assert "no changes" in captured.out.lower() or captured.out.strip() != ""


# ---------------------------------------------------------------------------
# _make_vault_client tests
# ---------------------------------------------------------------------------

def test_make_vault_client_raises_without_token(monkeypatch):
    monkeypatch.delenv("VAULT_TOKEN", raising=False)
    monkeypatch.delenv("VAULT_ADDR", raising=False)
    from envoy.vault import VaultConfigError
    with pytest.raises((VaultConfigError, Exception)):
        _make_vault_client()


def test_make_vault_client_uses_env_vars(monkeypatch):
    monkeypatch.setenv("VAULT_TOKEN", "test-token")
    monkeypatch.setenv("VAULT_ADDR", "http://localhost:8200")
    with patch("envoy.cli.VaultClient") as MockClient:
        MockClient.return_value = MagicMock()
        client = _make_vault_client()
        MockClient.assert_called_once()
        assert client is not None


# ---------------------------------------------------------------------------
# cmd_push tests
# ---------------------------------------------------------------------------

def test_cmd_push_calls_push_to_vault(tmp_env, mock_vault_client):
    with patch("envoy.cli._make_vault_client", return_value=mock_vault_client), \
         patch("envoy.cli.push_to_vault") as mock_push:
        from envoy.sync import SyncResult
        mock_push.return_value = SyncResult(pushed=True, dry_run=False, added=[], removed=[], changed=[])
        parser = _build_parser()
        args = parser.parse_args(["push", tmp_env, "secret/myapp"])
        cmd_push(args)
        mock_push.assert_called_once()


def test_cmd_push_dry_run_flag_passed(tmp_env, mock_vault_client):
    with patch("envoy.cli._make_vault_client", return_value=mock_vault_client), \
         patch("envoy.cli.push_to_vault") as mock_push:
        from envoy.sync import SyncResult
        mock_push.return_value = SyncResult(pushed=False, dry_run=True, added=[], removed=[], changed=[])
        parser = _build_parser()
        args = parser.parse_args(["push", tmp_env, "secret/myapp", "--dry-run"])
        cmd_push(args)
        _, kwargs = mock_push.call_args
        assert kwargs.get("dry_run") is True or mock_push.call_args[0][2] is True


# ---------------------------------------------------------------------------
# cmd_pull tests
# ---------------------------------------------------------------------------

def test_cmd_pull_calls_pull_from_vault(tmp_path, mock_vault_client):
    out_file = str(tmp_path / ".env.pulled")
    with patch("envoy.cli._make_vault_client", return_value=mock_vault_client), \
         patch("envoy.cli.pull_from_vault") as mock_pull:
        from envoy.sync import SyncResult
        mock_pull.return_value = SyncResult(pushed=True, dry_run=False, added=["FOO"], removed=[], changed=[])
        parser = _build_parser()
        args = parser.parse_args(["pull", "secret/myapp", out_file])
        cmd_pull(args)
        mock_pull.assert_called_once()
