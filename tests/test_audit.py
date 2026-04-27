"""Tests for envoy.audit module."""

import json
from pathlib import Path

import pytest

from envoy.audit import AuditEntry, AuditLog


@pytest.fixture
def log_file(tmp_path: Path) -> Path:
    return tmp_path / "audit" / "envoy.log"


@pytest.fixture
def audit(log_file: Path) -> AuditLog:
    return AuditLog(log_file)


def test_record_creates_file(audit: AuditLog, log_file: Path) -> None:
    audit.record(action="diff", env_file=".env")
    assert log_file.exists()


def test_record_returns_entry(audit: AuditLog) -> None:
    entry = audit.record(action="push", env_file=".env", vault_path="secret/app")
    assert isinstance(entry, AuditEntry)
    assert entry.action == "push"
    assert entry.vault_path == "secret/app"


def test_record_writes_valid_json(audit: AuditLog, log_file: Path) -> None:
    audit.record(action="pull", env_file=".env.prod", keys_added=["NEW_KEY"])
    line = log_file.read_text().strip()
    data = json.loads(line)
    assert data["action"] == "pull"
    assert "NEW_KEY" in data["keys_added"]


def test_read_all_empty_when_no_file(audit: AuditLog) -> None:
    assert audit.read_all() == []


def test_read_all_returns_entries(audit: AuditLog) -> None:
    audit.record(action="push", env_file=".env", keys_changed=["DB_PASS"])
    audit.record(action="pull", env_file=".env", keys_added=["NEW"])
    entries = audit.read_all()
    assert len(entries) == 2
    assert entries[0].action == "push"
    assert entries[1].action == "pull"


def test_tail_limits_results(audit: AuditLog) -> None:
    for i in range(10):
        audit.record(action="diff", env_file=f".env.{i}")
    assert len(audit.tail(3)) == 3
    assert len(audit.tail(20)) == 10


def test_dry_run_flag_recorded(audit: AuditLog) -> None:
    audit.record(action="push", env_file=".env", dry_run=True)
    entry = audit.read_all()[0]
    assert entry.dry_run is True


def test_user_field_populated(audit: AuditLog, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USER", "alice")
    entry = audit.record(action="diff", env_file=".env")
    assert entry.user == "alice"


def test_keys_default_to_empty_lists(audit: AuditLog) -> None:
    entry = audit.record(action="diff", env_file=".env")
    assert entry.keys_added == []
    assert entry.keys_removed == []
    assert entry.keys_changed == []
