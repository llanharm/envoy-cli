"""Tests for envoy.history."""

import json
import time
from pathlib import Path

import pytest

from envoy.history import HistoryEntry, HistoryStore


@pytest.fixture
def store(tmp_path):
    return HistoryStore(tmp_path / ".envoy" / "history.json")


def test_record_creates_entry(store):
    entry = store.record("/app/.env", "edit", added=["NEW_KEY"])
    assert isinstance(entry, HistoryEntry)
    assert entry.event == "edit"
    assert "NEW_KEY" in entry.added


def test_record_persists_to_disk(store, tmp_path):
    store.record("/app/.env", "push", changed=["DB_URL"])
    raw = json.loads((tmp_path / ".envoy" / "history.json").read_text())
    assert len(raw["entries"]) == 1
    assert raw["entries"][0]["event"] == "push"


def test_query_returns_all_by_default(store):
    store.record("/a/.env", "edit")
    store.record("/b/.env", "push")
    assert len(store.query()) == 2


def test_query_filters_by_path(store):
    store.record("/a/.env", "edit")
    store.record("/b/.env", "push")
    results = store.query(path="/a/.env")
    assert len(results) == 1
    assert results[0].path == "/a/.env"


def test_query_filters_by_event(store):
    store.record("/a/.env", "edit")
    store.record("/a/.env", "rotate")
    results = store.query(event="rotate")
    assert len(results) == 1
    assert results[0].event == "rotate"


def test_query_respects_limit(store):
    for i in range(5):
        store.record("/a/.env", "edit", added=[f"KEY_{i}"])
    results = store.query(limit=3)
    assert len(results) == 3


def test_query_returns_most_recent_first(store):
    store.record("/a/.env", "edit", added=["FIRST"])
    time.sleep(0.01)
    store.record("/a/.env", "edit", added=["SECOND"])
    results = store.query()
    assert results[0].added == ["SECOND"]


def test_clear_removes_all(store):
    store.record("/a/.env", "edit")
    store.record("/b/.env", "push")
    removed = store.clear()
    assert removed == 2
    assert store.query() == []


def test_clear_by_path_removes_only_matching(store):
    store.record("/a/.env", "edit")
    store.record("/b/.env", "push")
    removed = store.clear(path="/a/.env")
    assert removed == 1
    remaining = store.query()
    assert all(e.path == "/b/.env" for e in remaining)


def test_reload_from_disk(tmp_path):
    path = tmp_path / ".envoy" / "history.json"
    s1 = HistoryStore(path)
    s1.record("/app/.env", "merge", removed=["OLD"])
    s2 = HistoryStore(path)
    results = s2.query()
    assert len(results) == 1
    assert results[0].removed == ["OLD"]


def test_entry_to_dict_round_trip():
    entry = HistoryEntry(
        timestamp=1_700_000_000.0,
        path="/x/.env",
        event="pull",
        added=["A"],
        removed=["B"],
        changed=["C"],
        actor="ci",
    )
    d = entry.to_dict()
    restored = HistoryEntry.from_dict(d)
    assert restored.event == "pull"
    assert restored.actor == "ci"
    assert restored.added == ["A"]
