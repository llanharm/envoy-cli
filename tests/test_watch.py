"""Tests for envoy.watch."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from envoy.watch import EnvWatcher, WatchEvent, _file_hash


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("FOO=bar\nBAZ=qux\n")
    return p


def test_file_hash_changes_on_write(env_file: Path) -> None:
    h1 = _file_hash(env_file)
    env_file.write_text("FOO=changed\n")
    h2 = _file_hash(env_file)
    assert h1 != h2


def test_raises_with_no_paths(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="At least one path"):
        EnvWatcher(paths=[], on_change=lambda e: None)


def test_no_event_when_file_unchanged(env_file: Path) -> None:
    events: list[WatchEvent] = []
    watcher = EnvWatcher(paths=[env_file], on_change=events.append, interval=0)
    watcher.watch(max_iterations=3)
    assert events == []


def test_event_fired_on_change(env_file: Path) -> None:
    events: list[WatchEvent] = []

    call_count = 0

    def on_change(event: WatchEvent) -> None:
        events.append(event)

    watcher = EnvWatcher(paths=[env_file], on_change=on_change, interval=0)
    # Seed internal state
    watcher._seed()

    # Mutate the file
    env_file.write_text("FOO=newval\nBAZ=qux\nNEW=key\n")
    watcher._check_once()

    assert len(events) == 1
    ev = events[0]
    assert ev.path == env_file
    assert ev.has_changes()


def test_event_diff_contains_added_key(env_file: Path) -> None:
    events: list[WatchEvent] = []
    watcher = EnvWatcher(paths=[env_file], on_change=events.append, interval=0)
    watcher._seed()
    env_file.write_text("FOO=bar\nBAZ=qux\nEXTRA=1\n")
    watcher._check_once()
    assert "EXTRA" in events[0].diff.added


def test_event_diff_contains_removed_key(env_file: Path) -> None:
    events: list[WatchEvent] = []
    watcher = EnvWatcher(paths=[env_file], on_change=events.append, interval=0)
    watcher._seed()
    env_file.write_text("FOO=bar\n")
    watcher._check_once()
    assert "BAZ" in events[0].diff.removed


def test_event_diff_contains_changed_value(env_file: Path) -> None:
    events: list[WatchEvent] = []
    watcher = EnvWatcher(paths=[env_file], on_change=events.append, interval=0)
    watcher._seed()
    env_file.write_text("FOO=modified\nBAZ=qux\n")
    watcher._check_once()
    assert "FOO" in events[0].diff.changed
    assert events[0].diff.changed["FOO"] == ("bar", "modified")


def test_watch_event_timestamp(env_file: Path) -> None:
    events: list[WatchEvent] = []
    watcher = EnvWatcher(paths=[env_file], on_change=events.append, interval=0)
    watcher._seed()
    before = time.time()
    env_file.write_text("FOO=ts\n")
    watcher._check_once()
    after = time.time()
    assert before <= events[0].detected_at <= after
