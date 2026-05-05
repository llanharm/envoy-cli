"""Tests for envoy.cli_lint cmd_lint."""
from __future__ import annotations

import argparse
import json
import pytest

from envoy.cli_lint import build_lint_parser, cmd_lint


@pytest.fixture()
def tmp_env(tmp_path):
    def _write(content: str) -> str:
        p = tmp_path / ".env"
        p.write_text(content)
        return str(p)
    return _write


def _make_args(file: str, fmt: str = "text", strict: bool = False) -> argparse.Namespace:
    return argparse.Namespace(file=file, format=fmt, strict=strict)


def test_clean_file_exits_zero(tmp_env, capsys):
    path = tmp_env("FOO=bar\n")
    code = cmd_lint(_make_args(path))
    assert code == 0
    captured = capsys.readouterr()
    assert "OK" in captured.out


def test_error_exits_one(tmp_env, capsys):
    path = tmp_env("FOO=bar\nFOO=baz\n")  # duplicate key → E002
    code = cmd_lint(_make_args(path))
    assert code == 1


def test_warning_exits_zero_without_strict(tmp_env):
    path = tmp_env("foo=bar\n")  # W001 only
    code = cmd_lint(_make_args(path, strict=False))
    assert code == 0


def test_warning_exits_one_with_strict(tmp_env):
    path = tmp_env("foo=bar\n")  # W001 only
    code = cmd_lint(_make_args(path, strict=True))
    assert code == 1


def test_json_output_is_valid(tmp_env, capsys):
    path = tmp_env("foo=bar\nFOO=\n")
    cmd_lint(_make_args(path, fmt="json"))
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert all("code" in item for item in data)


def test_missing_file_exits_two(tmp_path, capsys):
    code = cmd_lint(_make_args(str(tmp_path / "missing.env")))
    assert code == 2
    assert "error" in capsys.readouterr().err


def test_build_lint_parser_registers_subcommand():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="cmd")
    build_lint_parser(sub)
    ns = root.parse_args(["lint", "some.env"])
    assert ns.cmd == "lint"
    assert ns.file == "some.env"
