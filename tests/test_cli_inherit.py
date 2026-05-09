"""Tests for envoy.cli_inherit."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from envoy.cli_inherit import build_inherit_parser, cmd_inherit
from envoy.parser import write_env_file


@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command")
    build_inherit_parser(sub)
    return root


@pytest.fixture()
def base_env(tmp_path: Path) -> Path:
    p = tmp_path / "base.env"
    write_env_file(p, {"HOST": "localhost", "PORT": "5432"})
    return p


@pytest.fixture()
def child_env(tmp_path: Path) -> Path:
    p = tmp_path / "child.env"
    write_env_file(p, {"PORT": "9999", "APP": "demo"})
    return p


def _make_args(parser: argparse.ArgumentParser, base: Path, child: Path, **kwargs) -> argparse.Namespace:
    argv = ["inherit", str(child), "--base", str(base)]
    for k, v in kwargs.items():
        argv.append(f"--{k.replace('_', '-')}")
        if v is not True:
            argv.append(str(v))
    return parser.parse_args(argv)


def test_build_inherit_parser_returns_parser(parser: argparse.ArgumentParser) -> None:
    assert isinstance(parser, argparse.ArgumentParser)


def test_missing_child_returns_one(parser: argparse.ArgumentParser, base_env: Path, tmp_path: Path) -> None:
    args = parser.parse_args(["inherit", str(tmp_path / "nope.env"), "--base", str(base_env)])
    assert cmd_inherit(args) == 1


def test_missing_base_returns_one(parser: argparse.ArgumentParser, child_env: Path, tmp_path: Path) -> None:
    args = parser.parse_args(["inherit", str(child_env), "--base", str(tmp_path / "nope.env")])
    assert cmd_inherit(args) == 1


def test_successful_inherit_exits_zero(parser: argparse.ArgumentParser, base_env: Path, child_env: Path) -> None:
    args = _make_args(parser, base_env, child_env, dry_run=True)
    assert cmd_inherit(args) == 0


def test_json_output_is_valid(parser: argparse.ArgumentParser, base_env: Path, child_env: Path, capsys) -> None:
    args = parser.parse_args(["inherit", str(child_env), "--base", str(base_env), "--dry-run", "--json"])
    rc = cmd_inherit(args)
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "total_keys" in data
    assert "overridden_keys" in data


def test_writes_output_file(parser: argparse.ArgumentParser, base_env: Path, child_env: Path, tmp_path: Path) -> None:
    out = tmp_path / "merged.env"
    args = parser.parse_args(["inherit", str(child_env), "--base", str(base_env), "--output", str(out)])
    rc = cmd_inherit(args)
    assert rc == 0
    assert out.exists()
    content = out.read_text()
    assert "HOST" in content
    assert "APP" in content
