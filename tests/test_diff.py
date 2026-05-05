"""Tests for envoy.diff module."""

import pytest
from envoy.diff import diff_envs, EnvDiff, _mask


BASE = {
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "SECRET_KEY": "old-secret",
}

TARGET = {
    "DB_HOST": "localhost",
    "DB_PORT": "5433",
    "NEW_VAR": "shiny",
}


def test_diff_detects_added_keys():
    result = diff_envs(BASE, TARGET)
    assert "NEW_VAR" in result.added
    assert result.added["NEW_VAR"] == "shiny"


def test_diff_detects_removed_keys():
    result = diff_envs(BASE, TARGET)
    assert "SECRET_KEY" in result.removed


def test_diff_detects_changed_values():
    result = diff_envs(BASE, TARGET)
    assert "DB_PORT" in result.changed
    assert result.changed["DB_PORT"] == ("5432", "5433")


def test_diff_detects_unchanged_values():
    result = diff_envs(BASE, TARGET)
    assert "DB_HOST" in result.unchanged


def test_has_changes_true_when_diff_exists():
    result = diff_envs(BASE, TARGET)
    assert result.has_changes is True


def test_has_changes_false_when_identical():
    result = diff_envs(BASE, BASE)
    assert result.has_changes is False


def test_diff_empty_dicts():
    result = diff_envs({}, {})
    assert not result.has_changes


def test_summary_contains_symbols():
    result = diff_envs(BASE, TARGET)
    summary = result.summary()
    assert '+' in summary  # added
    assert '-' in summary  # removed
    assert '~' in summary  # changed


def test_summary_no_changes():
    result = diff_envs(BASE, BASE)
    assert result.summary() == "  (no changes)"


def test_mask_short_value():
    assert _mask("abc") == "***"


def test_mask_long_value():
    masked = _mask("supersecret", visible_chars=4)
    assert masked.startswith("supe")
    assert '*' in masked


def test_mask_empty_string():
    """An empty value should return an empty string, not raise an error."""
    assert _mask("") == ""


def test_mask_default_visible_chars():
    """Default masking should expose only the first few characters."""
    value = "my-secret-password"
    masked = _mask(value)
    # The masked result should be shorter or equal in visible prefix
    # and contain at least one asterisk.
    assert '*' in masked
    assert not masked.endswith(value)  # must not be fully unmasked


def test_mask_preserves_length():
    """Masked value should have the same total length as the original."""
    value = "supersecret"
    masked = _mask(value, visible_chars=4)
    assert len(masked) == len(value)


def test_diff_changed_keys_not_in_added_or_removed():
    """Keys with changed values should not appear in added or removed sets."""
    result = diff_envs(BASE, TARGET)
    assert "DB_PORT" not in result.added
    assert "DB_PORT" not in result.removed
