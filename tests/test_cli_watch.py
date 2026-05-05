"""Tests for envoy.cli_watch."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envoy.cli_watch import build_watch_parser, cmd_watch, _print_event
from envoy.watch import WatchEvent
from envoy.diff import diff_envs


@pytest.fixture()
def tmp_env(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("KEY=value\n")
    return p


def _make_args(files: list[Path], interval: float = 1.0, mask: bool = False) -> argparse.Namespace:
    return argparse.Namespace(files=files, interval=interval, mask=mask)


def test_build_watch_parser_returns_parser() -> None:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    p = build_watch_parser(sub)
    assert isinstance(p, argparse.ArgumentParser)


def test_cmd_watch_missing_file_returns_one(tmp_path: Path) -> None:
    missing = tmp_path / "no_such.env"
    args = _make_args(files=[missing])
    result = cmd_watch(args)
    assert result == 1


def test_cmd_watch_calls_watcher(tmp_env: Path) -> None:
    args = _make_args(files=[tmp_env], interval=0.0)
    with patch("envoy.cli_watch.EnvWatcher") as MockWatcher:
        instance = MockWatcher.return_value
        instance.watch.return_value = None
        result = cmd_watch(args)
    assert result == 0
    MockWatcher.assert_called_once()
    instance.watch.assert_called_once()


def test_print_event_shows_added(capsys: pytest.CaptureFixture[str], tmp_env: Path) -> None:
    diff = diff_envs({}, {"NEW_KEY": "hello"})
    event = WatchEvent(path=tmp_env, diff=diff)
    _print_event(event, mask=False)
    captured = capsys.readouterr()
    assert "NEW_KEY=hello" in captured.out


def test_print_event_masks_values(capsys: pytest.CaptureFixture[str], tmp_env: Path) -> None:
    diff = diff_envs({}, {"SECRET": "s3cr3t"})
    event = WatchEvent(path=tmp_env, diff=diff)
    _print_event(event, mask=True)
    captured = capsys.readouterr()
    assert "s3cr3t" not in captured.out
    assert "SECRET" in captured.out


def test_print_event_shows_removed(capsys: pytest.CaptureFixture[str], tmp_env: Path) -> None:
    diff = diff_envs({"OLD_KEY": "v"}, {})
    event = WatchEvent(path=tmp_env, diff=diff)
    _print_event(event)
    captured = capsys.readouterr()
    assert "OLD_KEY" in captured.out


def test_print_event_shows_changed(capsys: pytest.CaptureFixture[str], tmp_env: Path) -> None:
    diff = diff_envs({"K": "old"}, {"K": "new"})
    event = WatchEvent(path=tmp_env, diff=diff)
    _print_event(event)
    captured = capsys.readouterr()
    assert "old" in captured.out
    assert "new" in captured.out
