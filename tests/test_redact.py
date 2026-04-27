"""Tests for envoy.redact."""

import pytest

from envoy.redact import RedactResult, is_sensitive, redact

_REDACTED = "[REDACTED]"


# ---------------------------------------------------------------------------
# is_sensitive
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key", [
    "SECRET_KEY", "DB_PASSWORD", "API_TOKEN", "PRIVATE_KEY",
    "AUTH_TOKEN", "AWS_SECRET_ACCESS_KEY", "SIGNING_KEY",
])
def test_sensitive_keys_detected(key):
    assert is_sensitive(key) is True


@pytest.mark.parametrize("key", [
    "APP_NAME", "PORT", "DEBUG", "LOG_LEVEL", "DATABASE_HOST",
])
def test_non_sensitive_keys_not_flagged(key):
    assert is_sensitive(key) is False


def test_extra_pattern_extends_detection():
    assert is_sensitive("MY_INTERNAL_PASSPHRASE", extra_patterns=["passphrase"]) is True


# ---------------------------------------------------------------------------
# redact
# ---------------------------------------------------------------------------

def test_redact_replaces_sensitive_values():
    env = {"DB_PASSWORD": "s3cr3t", "APP_NAME": "myapp"}
    result = redact(env)
    assert result.redacted["DB_PASSWORD"] == _REDACTED
    assert result.redacted["APP_NAME"] == "myapp"


def test_redact_records_redacted_keys():
    env = {"API_KEY": "abc", "HOST": "localhost"}
    result = redact(env)
    assert "API_KEY" in result.redacted_keys
    assert "HOST" not in result.redacted_keys


def test_redact_preserves_original():
    env = {"SECRET": "hidden"}
    result = redact(env)
    assert result.original["SECRET"] == "hidden"


def test_explicit_keys_are_redacted():
    env = {"CUSTOM_VAR": "value", "OTHER": "ok"}
    result = redact(env, explicit_keys={"CUSTOM_VAR"})
    assert result.redacted["CUSTOM_VAR"] == _REDACTED
    assert result.redacted["OTHER"] == "ok"


def test_empty_env_returns_empty_result():
    result = redact({})
    assert result.redacted == {}
    assert result.redacted_keys == set()


def test_result_is_redact_result_instance():
    assert isinstance(redact({"TOKEN": "x"}), RedactResult)
