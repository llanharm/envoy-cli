"""Tests for envoy.cli_interpolate."""
import argparse
import json
from pathlib import Path

import pytest

from envoy.cli_interpolate import build_interpolate_parser, cmd_interpolate


@pytest.fixture()
def tmp_env(tmp_path: Path):
    def _make(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(content)
        return p
    return _make


def _make_args(file: str, **kwargs) -> argparse.Namespace:
    defaults = {"format": "env", "output": None, "strict": False, "func": cmd_interpolate}
    defaults.update(kwargs)
    defaults["file"] = file
    return argparse.Namespace(**defaults)


def test_build_interpolate_parser_returns_parser():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    p = build_interpolate_parser(sub)
    assert isinstance(p, argparse.ArgumentParser)


def test_missing_file_returns_one(tmp_path: Path):
    args = _make_args(str(tmp_path / "missing.env"))
    assert cmd_interpolate(args) == 1


def test_simple_interpolation_exits_zero(tmp_env, capsys):
    p = tmp_env("BASE=/app\nLOG=${BASE}/logs\n")
    args = _make_args(str(p))
    rc = cmd_interpolate(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "/app/logs" in out


def test_json_format_outputs_json(tmp_env, capsys):
    p = tmp_env("HOST=localhost\nURL=http://${HOST}\n")
    args = _make_args(str(p), format="json")
    cmd_interpolate(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["URL"] == "http://localhost"


def test_strict_mode_fails_on_missing_ref(tmp_env, capsys):
    p = tmp_env("PATH=${UNDEFINED}/bin\n")
    args = _make_args(str(p), strict=True)
    rc = cmd_interpolate(args)
    assert rc == 1


def test_output_file_written(tmp_env, tmp_path: Path):
    p = tmp_env("A=1\nB=${A}2\n")
    out = tmp_path / "resolved.env"
    args = _make_args(str(p), output=str(out))
    rc = cmd_interpolate(args)
    assert rc == 0
    assert out.exists()
    content = out.read_text()
    assert "B=12" in content


def test_no_strict_passes_with_unresolved(tmp_env):
    p = tmp_env("PATH=${MISSING}/bin\n")
    args = _make_args(str(p), strict=False)
    rc = cmd_interpolate(args)
    assert rc == 0
