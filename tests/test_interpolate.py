"""Tests for envoy.interpolate."""
import pytest

from envoy.interpolate import InterpolateResult, interpolate, _refs


# ---------------------------------------------------------------------------
# _refs helper
# ---------------------------------------------------------------------------

def test_refs_detects_brace_syntax():
    assert _refs("${FOO}") == ["FOO"]


def test_refs_detects_bare_syntax():
    assert _refs("$BAR") == ["BAR"]


def test_refs_detects_multiple():
    assert _refs("${A}:$B") == ["A", "B"]


def test_refs_empty_on_plain_value():
    assert _refs("hello") == []


# ---------------------------------------------------------------------------
# interpolate
# ---------------------------------------------------------------------------

def test_simple_reference_resolved():
    env = {"BASE": "/app", "LOG": "${BASE}/logs"}
    result = interpolate(env)
    assert result.ok
    assert result.resolved["LOG"] == "/app/logs"


def test_chained_references_resolved():
    env = {"A": "hello", "B": "${A} world", "C": "${B}!"}
    result = interpolate(env)
    assert result.ok
    assert result.resolved["C"] == "hello world!"


def test_no_references_passes_through():
    env = {"KEY": "value", "OTHER": "123"}
    result = interpolate(env)
    assert result.ok
    assert result.resolved == env


def test_missing_reference_reported():
    env = {"PATH": "${UNDEFINED}/bin"}
    result = interpolate(env)
    assert not result.ok
    assert "PATH" in result.unresolved_keys


def test_circular_reference_reported():
    env = {"A": "${B}", "B": "${A}"}
    result = interpolate(env)
    assert not result.ok
    assert result.circular_keys  # at least one detected


def test_bare_dollar_syntax_resolved():
    env = {"HOST": "localhost", "URL": "http://$HOST:8080"}
    result = interpolate(env)
    assert result.ok
    assert result.resolved["URL"] == "http://localhost:8080"


def test_result_ok_true_when_no_issues():
    result = InterpolateResult(resolved={"X": "1"})
    assert result.ok


def test_result_ok_false_with_unresolved():
    result = InterpolateResult(resolved={}, unresolved_keys=["A"])
    assert not result.ok


def test_result_ok_false_with_circular():
    result = InterpolateResult(resolved={}, circular_keys=["B"])
    assert not result.ok


def test_partial_resolution_leaves_other_keys_intact():
    env = {"GOOD": "ok", "BAD": "${MISSING}"}
    result = interpolate(env)
    assert result.resolved.get("GOOD") == "ok"
