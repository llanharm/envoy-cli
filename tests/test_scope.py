"""Tests for envoy.scope."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envoy.scope import (
    ScopeError,
    ScopeResult,
    apply_scope,
    load_scopes,
)


@pytest.fixture()
def scope_file(tmp_path: Path) -> Path:
    data = {
        "backend": ["DB_HOST", "DB_PORT", "SECRET_KEY"],
        "frontend": ["API_URL", "PUBLIC_KEY"],
    }
    p = tmp_path / ".envscopes"
    p.write_text(json.dumps(data))
    return p


@pytest.fixture()
def sample_env() -> dict:
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "SECRET_KEY": "s3cr3t",
        "API_URL": "https://api.example.com",
        "PUBLIC_KEY": "pk_live_abc",
        "UNSCOPED_VAR": "orphan",
    }


def test_load_scopes_returns_dict(scope_file: Path) -> None:
    scopes = load_scopes(scope_file)
    assert "backend" in scopes
    assert "frontend" in scopes
    assert scopes["backend"] == ["DB_HOST", "DB_PORT", "SECRET_KEY"]


def test_load_scopes_raises_when_file_missing(tmp_path: Path) -> None:
    with pytest.raises(ScopeError, match="not found"):
        load_scopes(tmp_path / "nonexistent.json")


def test_load_scopes_raises_on_invalid_json(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid json")
    with pytest.raises(ScopeError, match="Invalid JSON"):
        load_scopes(bad)


def test_load_scopes_raises_when_root_not_dict(tmp_path: Path) -> None:
    p = tmp_path / "list.json"
    p.write_text(json.dumps(["backend", "frontend"]))
    with pytest.raises(ScopeError, match="JSON object"):
        load_scopes(p)


def test_load_scopes_raises_on_non_list_value(tmp_path: Path) -> None:
    p = tmp_path / "bad_scope.json"
    p.write_text(json.dumps({"backend": "DB_HOST"}))
    with pytest.raises(ScopeError, match="list of strings"):
        load_scopes(p)


def test_apply_scope_returns_matched_keys(sample_env: dict) -> None:
    scopes = {"backend": ["DB_HOST", "DB_PORT", "SECRET_KEY"]}
    result = apply_scope(sample_env, "backend", scopes)
    assert isinstance(result, ScopeResult)
    assert set(result.matched.keys()) == {"DB_HOST", "DB_PORT", "SECRET_KEY"}
    assert result.total_matched == 3


def test_apply_scope_excludes_non_scope_keys(sample_env: dict) -> None:
    scopes = {"backend": ["DB_HOST", "DB_PORT", "SECRET_KEY"]}
    result = apply_scope(sample_env, "backend", scopes)
    assert "API_URL" in result.excluded
    assert "UNSCOPED_VAR" in result.excluded
    assert result.total_excluded == 3


def test_apply_scope_raises_on_unknown_scope(sample_env: dict) -> None:
    scopes = {"backend": ["DB_HOST"]}
    with pytest.raises(ScopeError, match="'staging' not defined"):
        apply_scope(sample_env, "staging", scopes)


def test_apply_scope_error_lists_available_scopes(sample_env: dict) -> None:
    scopes = {"backend": ["DB_HOST"], "frontend": ["API_URL"]}
    with pytest.raises(ScopeError, match="backend"):
        apply_scope(sample_env, "unknown", scopes)


def test_scope_result_to_dict(sample_env: dict) -> None:
    scopes = {"frontend": ["API_URL", "PUBLIC_KEY"]}
    result = apply_scope(sample_env, "frontend", scopes)
    d = result.to_dict()
    assert d["scope"] == "frontend"
    assert d["total_matched"] == 2
    assert "API_URL" in d["matched"]
