"""Tests for envoy.cli_resolve."""
from __future__ import annotations

import argparse
import json

import pytest

from envoy.cli_resolve import build_resolve_parser, cmd_resolve


@pytest.fixture()
def parser():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    build_resolve_parser(sub)
    return root


@pytest.fixture()
def env_a(tmp_path):
    p = tmp_path / "a.env"
    p.write_text("FOO=aaa\nSHARED=from_a\n")
    return p


@pytest.fixture()
def env_b(tmp_path):
    p = tmp_path / "b.env"
    p.write_text("BAR=bbb\nSHARED=from_b\n")
    return p


def _make_args(parser, *extra):
    return parser.parse_args(["resolve", *extra])


def test_build_resolve_parser_returns_parser(parser):
    assert isinstance(parser, argparse.ArgumentParser)


def test_missing_file_returns_one(parser, tmp_path):
    missing = str(tmp_path / "ghost.env")
    args = _make_args(parser, missing)
    assert cmd_resolve(args) == 1


def test_text_output_exits_zero(parser, env_a, env_b, capsys):
    args = _make_args(parser, str(env_a), str(env_b))
    rc = cmd_resolve(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "SHARED=from_b" in out


def test_json_output_is_valid(parser, env_a, env_b, capsys):
    args = _make_args(parser, str(env_a), str(env_b), "--format", "json")
    rc = cmd_resolve(args)
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["effective"]["SHARED"] == "from_b"
    assert data["total_overridden"] == 1


def test_show_sources_annotates_output(parser, env_a, env_b, capsys):
    args = _make_args(parser, str(env_a), str(env_b), "--show-sources")
    cmd_resolve(args)
    out = capsys.readouterr().out
    assert "b.env" in out


def test_show_overrides_lists_shadowed(parser, env_a, env_b, capsys):
    args = _make_args(parser, str(env_a), str(env_b), "--show-overrides")
    cmd_resolve(args)
    out = capsys.readouterr().out
    assert "SHARED" in out
    assert "a.env" in out
