"""Tests for envoy.cli_history."""

import argparse
import json
from pathlib import Path

import pytest

from envoy.cli_history import build_history_parser, cmd_history
from envoy.history import HistoryStore


@pytest.fixture
def parser():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="cmd")
    build_history_parser(sub)
    return root


@pytest.fixture
def store_path(tmp_path):
    return tmp_path / "history.json"


def _make_args(parser, store_path, *extra):
    return parser.parse_args(["history"] + list(extra) + ["--store", str(store_path)])


def _seed(store_path):
    s = HistoryStore(store_path)
    s.record("/a/.env", "edit", added=["FOO"])
    s.record("/b/.env", "push", changed=["BAR"])
    return s


def test_build_history_parser_returns_parser(parser):
    assert parser is not None


def test_list_exits_zero_with_entries(parser, store_path, capsys):
    _seed(store_path)
    args = _make_args(parser, store_path, "list")
    rc = cmd_history(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "edit" in out
    assert "push" in out


def test_list_empty_store_prints_message(parser, store_path, capsys):
    args = _make_args(parser, store_path, "list")
    rc = cmd_history(args)
    assert rc == 0
    assert "No history" in capsys.readouterr().out


def test_list_json_flag_outputs_valid_json(parser, store_path, capsys):
    _seed(store_path)
    args = _make_args(parser, store_path, "list", "--json")
    cmd_history(args)
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)
    assert data[0]["event"] in ("edit", "push")


def test_list_filter_by_path(parser, store_path, capsys):
    _seed(store_path)
    args = _make_args(parser, store_path, "list", "--path", "/a/.env")
    cmd_history(args)
    out = capsys.readouterr().out
    assert "/a/.env" in out
    assert "/b/.env" not in out


def test_list_filter_by_event(parser, store_path, capsys):
    _seed(store_path)
    args = _make_args(parser, store_path, "list", "--event", "push")
    cmd_history(args)
    out = capsys.readouterr().out
    assert "push" in out
    assert "edit" not in out


def test_list_limit_respected(parser, store_path, capsys):
    s = HistoryStore(store_path)
    for i in range(10):
        s.record("/a/.env", "edit", added=[f"K{i}"])
    args = _make_args(parser, store_path, "list", "--limit", "3")
    cmd_history(args)
    lines = [l for l in capsys.readouterr().out.strip().splitlines() if l]
    assert len(lines) == 3


def test_clear_removes_all(parser, store_path, capsys):
    _seed(store_path)
    args = _make_args(parser, store_path, "clear")
    rc = cmd_history(args)
    assert rc == 0
    assert "2" in capsys.readouterr().out
    assert HistoryStore(store_path).query() == []


def test_clear_by_path(parser, store_path, capsys):
    _seed(store_path)
    args = _make_args(parser, store_path, "clear", "--path", "/a/.env")
    cmd_history(args)
    remaining = HistoryStore(store_path).query()
    assert len(remaining) == 1
    assert remaining[0].path == "/b/.env"
