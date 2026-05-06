"""Tests for envoy.promote and envoy.cli_promote."""

from __future__ import annotations

import argparse
import json
import os

import pytest

from envoy.promote import promote_env, PromoteResult
from envoy.cli_promote import build_promote_parser, cmd_promote


@pytest.fixture()
def env_src(tmp_path):
    p = tmp_path / "src.env"
    p.write_text("DB_HOST=prod-db\nDB_PORT=5432\nSECRET=abc\n")
    return str(p)


@pytest.fixture()
def env_dst(tmp_path):
    p = tmp_path / "dst.env"
    p.write_text("DB_HOST=staging-db\nAPP_NAME=myapp\n")
    return str(p)


# --- promote_env unit tests ---

def test_promote_adds_new_keys(env_src, env_dst):
    result = promote_env(env_src, env_dst)
    assert "DB_PORT" in result.promoted
    assert "SECRET" in result.promoted


def test_promote_skips_existing_keys_by_default(env_src, env_dst):
    result = promote_env(env_src, env_dst)
    assert "DB_HOST" in result.skipped
    assert "DB_HOST" not in result.promoted


def test_promote_overwrites_when_flag_set(env_src, env_dst):
    result = promote_env(env_src, env_dst, overwrite=True)
    assert "DB_HOST" in result.overwritten
    assert result.overwritten["DB_HOST"] == "prod-db"


def test_promote_filters_to_specified_keys(env_src, env_dst):
    result = promote_env(env_src, env_dst, keys=["DB_PORT"])
    assert "DB_PORT" in result.promoted
    assert "SECRET" not in result.promoted
    assert "SECRET" not in result.skipped


def test_promote_dry_run_does_not_write(env_src, env_dst):
    original = open(env_dst).read()
    result = promote_env(env_src, env_dst, dry_run=True)
    assert result.dry_run is True
    assert open(env_dst).read() == original


def test_promote_writes_to_disk(env_src, env_dst):
    promote_env(env_src, env_dst)
    content = open(env_dst).read()
    assert "DB_PORT" in content
    assert "SECRET" in content


def test_to_dict_contains_expected_keys(env_src, env_dst):
    result = promote_env(env_src, env_dst, dry_run=True)
    d = result.to_dict()
    assert set(d.keys()) == {"source", "destination", "promoted", "skipped", "overwritten", "dry_run"}


def test_missing_key_in_source_is_ignored(env_src, env_dst):
    result = promote_env(env_src, env_dst, keys=["NONEXISTENT"])
    assert result.total_promoted == 0


# --- cli_promote tests ---

@pytest.fixture()
def parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    build_promote_parser(sub)
    return p


def test_cmd_promote_exits_zero(parser, env_src, env_dst):
    args = parser.parse_args(["promote", env_src, env_dst, "--dry-run"])
    assert cmd_promote(args) == 0


def test_cmd_promote_json_output(parser, env_src, env_dst, capsys):
    args = parser.parse_args(["promote", env_src, env_dst, "--dry-run", "--json"])
    rc = cmd_promote(args)
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert "promoted" in out
    assert out["dry_run"] is True


def test_cmd_promote_bad_path_returns_one(parser, tmp_path):
    dst = tmp_path / "dst.env"
    dst.write_text("")
    args = parser.parse_args(["promote", "/no/such/file.env", str(dst)])
    assert cmd_promote(args) == 1
