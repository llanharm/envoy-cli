"""Tests for envoy.cli_profile."""
import argparse
import pytest
from pathlib import Path

from envoy.cli_profile import build_profile_parser, cmd_profile


@pytest.fixture
def parser():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    build_profile_parser(sub)
    return root


@pytest.fixture
def tmp_env(tmp_path):
    f = tmp_path / ".env"
    f.write_text("KEY=val\n")
    return f


def _make_args(parser, argv):
    return parser.parse_args(argv)


def test_build_profile_parser_returns_parser(parser):
    assert parser is not None


def test_add_profile_exits_zero(parser, tmp_env, tmp_path):
    store = tmp_path / "p.json"
    args = _make_args(parser, [
        "profile", "add", "dev", str(tmp_env),
        "--store", str(store),
    ])
    assert cmd_profile(args) == 0


def test_add_profile_missing_file_exits_one(parser, tmp_path):
    store = tmp_path / "p.json"
    args = _make_args(parser, [
        "profile", "add", "dev", "/nonexistent/.env",
        "--store", str(store),
    ])
    assert cmd_profile(args) == 1


def test_add_duplicate_profile_exits_one(parser, tmp_env, tmp_path):
    store = tmp_path / "p.json"
    base = ["profile", "add", "dev", str(tmp_env), "--store", str(store)]
    cmd_profile(_make_args(parser, base))
    assert cmd_profile(_make_args(parser, base)) == 1


def test_remove_profile_exits_zero(parser, tmp_env, tmp_path):
    store = tmp_path / "p.json"
    cmd_profile(_make_args(parser, ["profile", "add", "dev", str(tmp_env), "--store", str(store)]))
    args = _make_args(parser, ["profile", "remove", "dev", "--store", str(store)])
    assert cmd_profile(args) == 0


def test_remove_missing_profile_exits_one(parser, tmp_path):
    store = tmp_path / "p.json"
    args = _make_args(parser, ["profile", "remove", "ghost", "--store", str(store)])
    assert cmd_profile(args) == 1


def test_list_profiles_exits_zero(parser, tmp_env, tmp_path):
    store = tmp_path / "p.json"
    cmd_profile(_make_args(parser, ["profile", "add", "dev", str(tmp_env), "--store", str(store)]))
    args = _make_args(parser, ["profile", "list", "--store", str(store)])
    assert cmd_profile(args) == 0


def test_list_empty_store_exits_zero(parser, tmp_path):
    store = tmp_path / "p.json"
    args = _make_args(parser, ["profile", "list", "--store", str(store)])
    assert cmd_profile(args) == 0
