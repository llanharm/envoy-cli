"""Tests for envoy.lint."""
from __future__ import annotations

import os
import pytest

from envoy.lint import lint_env_file, LintResult


@pytest.fixture()
def tmp_env(tmp_path):
    """Return a helper that writes a .env file and returns its path."""
    def _write(content: str) -> str:
        p = tmp_path / ".env"
        p.write_text(content)
        return str(p)
    return _write


def test_clean_file_has_no_issues(tmp_env):
    path = tmp_env("FOO=bar\nBAR=baz\n")
    result = lint_env_file(path)
    assert result.ok
    assert result.issues == []


def test_detects_lowercase_key(tmp_env):
    path = tmp_env("foo=bar\n")
    result = lint_env_file(path)
    codes = result.error_codes()
    assert "W001" in codes


def test_detects_duplicate_key(tmp_env):
    path = tmp_env("FOO=bar\nFOO=baz\n")
    result = lint_env_file(path)
    assert "E002" in result.error_codes()


def test_detects_empty_value(tmp_env):
    path = tmp_env("FOO=\n")
    result = lint_env_file(path)
    assert "W002" in result.error_codes()


def test_detects_unquoted_space_in_value(tmp_env):
    path = tmp_env("FOO=hello world\n")
    result = lint_env_file(path)
    assert "W003" in result.error_codes()


def test_ignores_quoted_space_in_value(tmp_env):
    path = tmp_env('FOO="hello world"\n')
    result = lint_env_file(path)
    assert "W003" not in result.error_codes()


def test_detects_long_value(tmp_env):
    path = tmp_env(f"FOO={'x' * 300}\n")
    result = lint_env_file(path)
    assert "W004" in result.error_codes()


def test_detects_invalid_syntax(tmp_env):
    path = tmp_env("THIS IS NOT VALID\n")
    result = lint_env_file(path)
    assert "E001" in result.error_codes()


def test_ignores_comments_and_blanks(tmp_env):
    path = tmp_env("# comment\n\nFOO=bar\n")
    result = lint_env_file(path)
    assert result.ok


def test_issue_to_dict_has_expected_keys(tmp_env):
    path = tmp_env("foo=bar\n")
    result = lint_env_file(path)
    assert result.issues
    d = result.issues[0].to_dict()
    assert set(d.keys()) == {"line", "key", "code", "message"}


def test_raises_on_missing_file():
    with pytest.raises(OSError):
        lint_env_file("/nonexistent/.env")
