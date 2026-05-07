"""Integration tests: HistoryStore wired through cli_history round-trip."""

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


def test_record_then_list_round_trip(tmp_path, parser, capsys):
    store_path = tmp_path / "history.json"
    s = HistoryStore(store_path)
    s.record("/app/.env", "rotate", changed=["SECRET_KEY"], actor="alice")

    args = parser.parse_args(
        ["history", "list", "--json", "--store", str(store_path)]
    )
    rc = cmd_history(args)
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data[0]["event"] == "rotate"
    assert data[0]["actor"] == "alice"
    assert "SECRET_KEY" in data[0]["changed"]


def test_multiple_events_ordered_newest_first(tmp_path, parser, capsys):
    store_path = tmp_path / "history.json"
    s = HistoryStore(store_path)
    s.record("/app/.env", "edit", added=["ALPHA"])
    s.record("/app/.env", "push", changed=["BETA"])
    s.record("/app/.env", "pull", removed=["GAMMA"])

    args = parser.parse_args(
        ["history", "list", "--json", "--store", str(store_path)]
    )
    cmd_history(args)
    data = json.loads(capsys.readouterr().out)
    events = [e["event"] for e in data]
    assert events == ["pull", "push", "edit"]


def test_clear_then_list_shows_empty(tmp_path, parser, capsys):
    store_path = tmp_path / "history.json"
    s = HistoryStore(store_path)
    s.record("/app/.env", "edit")

    args_clear = parser.parse_args(["history", "clear", "--store", str(store_path)])
    cmd_history(args_clear)
    capsys.readouterr()

    args_list = parser.parse_args(["history", "list", "--store", str(store_path)])
    rc = cmd_history(args_list)
    assert rc == 0
    assert "No history" in capsys.readouterr().out
