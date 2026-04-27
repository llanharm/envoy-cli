"""Tests for envoy.report."""

import json

import pytest

from envoy.diff import diff_envs
from envoy.redact import redact
from envoy.report import render_json, render_text

_A = {"DB_HOST": "localhost", "API_KEY": "secret", "PORT": "5432"}
_B = {"DB_HOST": "prod-db", "API_KEY": "secret", "TIMEOUT": "30"}


@pytest.fixture
def diff():
    return diff_envs(_A, _B)


@pytest.fixture
def redact_result():
    return redact(_A)


# ---------------------------------------------------------------------------
# render_text
# ---------------------------------------------------------------------------

def test_text_contains_title():
    out = render_text(title="my report")
    assert "my report" in out


def test_text_shows_added_keys(diff):
    out = render_text(diff=diff)
    assert "added" in out
    assert "TIMEOUT" in out


def test_text_shows_removed_keys(diff):
    out = render_text(diff=diff)
    assert "removed" in out
    assert "PORT" in out


def test_text_shows_no_changes_when_identical():
    d = diff_envs({"A": "1"}, {"A": "1"})
    out = render_text(diff=d)
    assert "no changes" in out


def test_text_shows_redacted_keys(redact_result):
    out = render_text(redact_result=redact_result)
    assert "API_KEY" in out


def test_text_no_sensitive_when_empty():
    out = render_text(redact_result=redact({"PORT": "8080"}))
    assert "no sensitive keys" in out


# ---------------------------------------------------------------------------
# render_json
# ---------------------------------------------------------------------------

def test_json_is_valid_json(diff, redact_result):
    out = render_json(diff=diff, redact_result=redact_result)
    data = json.loads(out)  # must not raise
    assert "diff" in data
    assert "redaction" in data


def test_json_diff_lists_added(diff):
    data = json.loads(render_json(diff=diff))
    assert "TIMEOUT" in data["diff"]["added"]


def test_json_redaction_lists_keys(redact_result):
    data = json.loads(render_json(redact_result=redact_result))
    assert "API_KEY" in data["redaction"]["redacted_keys"]


def test_json_title_included():
    data = json.loads(render_json(title="custom"))
    assert data["title"] == "custom"
