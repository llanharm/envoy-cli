"""Tests for envoy.cli_tag."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from envoy.cli_tag import build_tag_parser, cmd_tag


@pytest.fixture()
def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="cmd")
    build_tag_parser(sub)
    return root


@pytest.fixture()
def tmp_env(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nSECRET_KEY=abc\nPORT=5432\n")
    return p


@pytest.fixture()
def tag_file(tmp_path: Path) -> Path:
    return tmp_path / ".env-tags.json"


def _make_args(parser: argparse.ArgumentParser, argv: list) -> argparse.Namespace:
    return parser.parse_args(argv)


def test_build_tag_parser_returns_parser(parser: argparse.ArgumentParser) -> None:
    assert isinstance(parser, argparse.ArgumentParser)


def test_set_tag_exits_zero(parser, tmp_path, tag_file) -> None:
    args = _make_args(parser, ["tag", "set", "DB_HOST", "database", "infra", f"--tag-file={tag_file}"])
    assert cmd_tag(args) == 0
    data = json.loads(tag_file.read_text())
    assert data["DB_HOST"] == ["database", "infra"]


def test_set_tag_overwrites_existing(parser, tmp_path, tag_file) -> None:
    tag_file.write_text(json.dumps({"DB_HOST": ["old"]}))
    args = _make_args(parser, ["tag", "set", "DB_HOST", "new", f"--tag-file={tag_file}"])
    cmd_tag(args)
    data = json.loads(tag_file.read_text())
    assert data["DB_HOST"] == ["new"]


def test_remove_tag_exits_zero(parser, tag_file) -> None:
    tag_file.write_text(json.dumps({"DB_HOST": ["database"]}))
    args = _make_args(parser, ["tag", "remove", "DB_HOST", f"--tag-file={tag_file}"])
    assert cmd_tag(args) == 0
    data = json.loads(tag_file.read_text())
    assert "DB_HOST" not in data


def test_remove_missing_key_returns_one(parser, tag_file) -> None:
    tag_file.write_text(json.dumps({}))
    args = _make_args(parser, ["tag", "remove", "GHOST", f"--tag-file={tag_file}"])
    assert cmd_tag(args) == 1


def test_list_exits_zero(parser, tmp_env, tag_file) -> None:
    tag_file.write_text(json.dumps({"DB_HOST": ["database"]}))
    args = _make_args(parser, ["tag", "list", str(tmp_env), f"--tag-file={tag_file}"])
    assert cmd_tag(args) == 0


def test_list_missing_env_returns_one(parser, tag_file) -> None:
    tag_file.write_text(json.dumps({}))
    args = _make_args(parser, ["tag", "list", "/no/such/.env", f"--tag-file={tag_file}"])
    assert cmd_tag(args) == 1


def test_list_json_output(parser, tmp_env, tag_file, capsys) -> None:
    tag_file.write_text(json.dumps({"DB_HOST": ["infra"]}))
    args = _make_args(parser, ["tag", "list", str(tmp_env), f"--tag-file={tag_file}", "--json"])
    cmd_tag(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "tagged" in data
    assert "untagged" in data
