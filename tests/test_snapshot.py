"""Tests for envoy.snapshot module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envoy.snapshot import Snapshot, SnapshotStore


@pytest.fixture()
def env_file(tmp_path: Path) -> str:
    p = tmp_path / ".env"
    p.write_text("FOO=bar\nBAZ=qux\n")
    return str(p)


@pytest.fixture()
def store(tmp_path: Path) -> SnapshotStore:
    return SnapshotStore(store_path=tmp_path / "snapshots.json")


def test_capture_returns_snapshot(store: SnapshotStore, env_file: str) -> None:
    snap = store.capture(env_file, label="initial")
    assert isinstance(snap, Snapshot)
    assert snap.values == {"FOO": "bar", "BAZ": "qux"}
    assert snap.label == "initial"
    assert snap.path == env_file


def test_capture_persists_to_disk(store: SnapshotStore, env_file: str, tmp_path: Path) -> None:
    store.capture(env_file)
    assert store.store_path.exists()
    raw = json.loads(store.store_path.read_text())
    assert len(raw) == 1
    assert raw[0]["values"]["FOO"] == "bar"


def test_list_snapshots_all(store: SnapshotStore, env_file: str) -> None:
    store.capture(env_file, label="first")
    store.capture(env_file, label="second")
    snaps = store.list_snapshots()
    assert len(snaps) == 2


def test_list_snapshots_filtered_by_path(store: SnapshotStore, env_file: str, tmp_path: Path) -> None:
    other = tmp_path / "other.env"
    other.write_text("X=1\n")
    store.capture(env_file)
    store.capture(str(other))
    assert len(store.list_snapshots(env_file)) == 1


def test_compare_detects_changes(store: SnapshotStore, env_file: str, tmp_path: Path) -> None:
    store.capture(env_file, label="before")
    # Mutate the file
    Path(env_file).write_text("FOO=changed\nBAZ=qux\nNEW=val\n")
    store.capture(env_file, label="after")
    diff = store.compare(env_file)
    assert "FOO" in diff.changed
    assert "NEW" in diff.added


def test_compare_raises_with_insufficient_snapshots(store: SnapshotStore, env_file: str) -> None:
    store.capture(env_file)
    with pytest.raises(ValueError, match="at least 2"):
        store.compare(env_file)


def test_snapshot_store_loads_existing(env_file: str, tmp_path: Path) -> None:
    store1 = SnapshotStore(store_path=tmp_path / "snaps.json")
    store1.capture(env_file, label="persisted")
    # Load from same path
    store2 = SnapshotStore(store_path=tmp_path / "snaps.json")
    snaps = store2.list_snapshots()
    assert len(snaps) == 1
    assert snaps[0].label == "persisted"


def test_snapshot_to_dict_and_from_dict(env_file: str, store: SnapshotStore) -> None:
    snap = store.capture(env_file, label="roundtrip")
    data = snap.to_dict()
    restored = Snapshot.from_dict(data)
    assert restored.values == snap.values
    assert restored.label == snap.label
    assert restored.captured_at == snap.captured_at
