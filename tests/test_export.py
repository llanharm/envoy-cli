"""Tests for envoy.export."""

import json

import pytest

from envoy.export import ExportError, ExportFormat, ExportResult, export_env


@pytest.fixture()
def simple_env():
    return {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET": "p@ss w0rd!"}


# ---------------------------------------------------------------------------
# Shell format
# ---------------------------------------------------------------------------

def test_shell_format_uses_export_keyword(simple_env):
    result = export_env(simple_env, fmt=ExportFormat.SHELL)
    assert result.format == ExportFormat.SHELL
    for line in result.content.splitlines():
        assert line.startswith("export ")


def test_shell_format_without_export_keyword(simple_env):
    result = export_env(simple_env, fmt=ExportFormat.SHELL, export_keyword=False)
    for line in result.content.splitlines():
        assert not line.startswith("export ")


def test_shell_format_quotes_special_chars():
    result = export_env({"KEY": "hello world"}, fmt=ExportFormat.SHELL)
    assert "'hello world'" in result.content


def test_shell_format_with_prefix(simple_env):
    result = export_env(simple_env, fmt=ExportFormat.SHELL, prefix="APP_")
    for line in result.content.splitlines():
        assert "APP_" in line


# ---------------------------------------------------------------------------
# JSON format
# ---------------------------------------------------------------------------

def test_json_format_is_valid_json(simple_env):
    result = export_env(simple_env, fmt=ExportFormat.JSON)
    data = json.loads(result.content)
    assert data["DB_HOST"] == "localhost"
    assert data["DB_PORT"] == "5432"


def test_json_format_with_prefix(simple_env):
    result = export_env(simple_env, fmt=ExportFormat.JSON, prefix="PRE_")
    data = json.loads(result.content)
    assert all(k.startswith("PRE_") for k in data)


# ---------------------------------------------------------------------------
# Docker format
# ---------------------------------------------------------------------------

def test_docker_format_has_no_quotes():
    result = export_env({"KEY": "value"}, fmt=ExportFormat.DOCKER)
    assert result.content == "KEY=value"


def test_docker_format_multiline(simple_env):
    result = export_env(simple_env, fmt=ExportFormat.DOCKER)
    lines = result.content.splitlines()
    assert len(lines) == len(simple_env)
    for line in lines:
        assert "=" in line
        assert not line.startswith("export")


def test_docker_format_with_prefix(simple_env):
    result = export_env(simple_env, fmt=ExportFormat.DOCKER, prefix="X_")
    for line in result.content.splitlines():
        assert line.startswith("X_")


# ---------------------------------------------------------------------------
# ExportResult metadata
# ---------------------------------------------------------------------------

def test_result_key_count(simple_env):
    result = export_env(simple_env)
    assert result.key_count == len(simple_env)


def test_result_str_returns_content(simple_env):
    result = export_env(simple_env, fmt=ExportFormat.JSON)
    assert str(result) == result.content


# ---------------------------------------------------------------------------
# String format coercion
# ---------------------------------------------------------------------------

def test_accepts_string_format(simple_env):
    result = export_env(simple_env, fmt="json")
    assert result.format == ExportFormat.JSON


def test_raises_on_unknown_format(simple_env):
    with pytest.raises(ExportError, match="Unknown format"):
        export_env(simple_env, fmt="toml")


def test_empty_env_produces_empty_output():
    result = export_env({}, fmt=ExportFormat.SHELL)
    assert result.content == ""
    assert result.key_count == 0
