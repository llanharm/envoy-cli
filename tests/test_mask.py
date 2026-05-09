"""Tests for envoy.mask and envoy.cli_mask."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from envoy.mask import DEFAULT_MASK, MaskResult, _partial_mask, mask_env
from envoy.cli_mask import build_mask_parser, cmd_mask


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_env(tmp_path: Path) -> Path:
    f = tmp_path / ".env"
    f.write_text("API_KEY=supersecret\nDB_HOST=localhost\nSECRET_TOKEN=abc123xyz\n")
    return f


@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    subs = root.add_subparsers(dest="command")
    build_mask_parser(subs)
    return root


# ---------------------------------------------------------------------------
# Unit tests — mask_env
# ---------------------------------------------------------------------------

def test_sensitive_key_is_masked():
    env = {"API_KEY": "s3cr3t", "HOST": "localhost"}
    result = mask_env(env)
    assert result.masked["API_KEY"] == DEFAULT_MASK
    assert result.masked["HOST"] == "localhost"


def test_total_masked_count():
    env = {"SECRET": "x", "TOKEN": "y", "NAME": "bob"}
    result = mask_env(env)
    assert result.total_masked == 2
    assert "NAME" in result.keys_skipped


def test_partial_mask_reveals_edges():
    value = "abcdefghijklmnop"
    out = _partial_mask(value)
    assert out.startswith("abcd")
    assert out.endswith("mnop")
    assert DEFAULT_MASK in out


def test_partial_mask_short_value_fully_masked():
    assert _partial_mask("short") == DEFAULT_MASK


def test_partial_flag_in_mask_env():
    env = {"PASSWORD": "abcdefghijklmnop"}
    result = mask_env(env, partial=True)
    assert result.masked["PASSWORD"] != DEFAULT_MASK
    assert DEFAULT_MASK in result.masked["PASSWORD"]


def test_custom_mask_string():
    env = {"API_KEY": "value"}
    result = mask_env(env, mask="[REDACTED]")
    assert result.masked["API_KEY"] == "[REDACTED]"


def test_only_keys_restricts_masking():
    env = {"API_KEY": "secret", "SECRET": "also_secret"}
    result = mask_env(env, only_keys=["API_KEY"])
    assert result.masked["API_KEY"] == DEFAULT_MASK
    assert result.masked["SECRET"] == "also_secret"


def test_extra_patterns_extend_detection():
    env = {"MY_CUSTOM_CRED": "val", "PLAIN": "ok"}
    result = mask_env(env, extra_patterns=[r"CRED"])
    assert result.masked["MY_CUSTOM_CRED"] == DEFAULT_MASK
    assert result.masked["PLAIN"] == "ok"


def test_to_dict_has_expected_keys():
    result = mask_env({"TOKEN": "abc", "HOST": "h"})
    d = result.to_dict()
    assert set(d.keys()) == {"masked", "keys_masked", "keys_skipped", "total_masked"}


# ---------------------------------------------------------------------------
# CLI tests — cmd_mask
# ---------------------------------------------------------------------------

def test_cmd_mask_missing_file_returns_one(parser: argparse.ArgumentParser, tmp_path: Path):
    args = parser.parse_args(["mask", str(tmp_path / "nope.env")])
    assert cmd_mask(args) == 1


def test_cmd_mask_text_output_exits_zero(parser: argparse.ArgumentParser, tmp_env: Path, capsys):
    args = parser.parse_args(["mask", str(tmp_env)])
    code = cmd_mask(args)
    assert code == 0
    out = capsys.readouterr().out
    assert "API_KEY=" in out
    assert "supersecret" not in out


def test_cmd_mask_json_output(parser: argparse.ArgumentParser, tmp_env: Path, capsys):
    args = parser.parse_args(["mask", str(tmp_env), "--format", "json"])
    code = cmd_mask(args)
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert "masked" in data
    assert data["masked"]["DB_HOST"] == "localhost"
