"""Tests for envoy.parser module."""

import os
import tempfile
import pytest

from envoy.parser import parse_env_file, write_env_file, EnvParseError


@pytest.fixture
def tmp_env_file(tmp_path):
    """Returns a factory for creating temporary .env files."""
    def _create(content: str) -> str:
        p = tmp_path / ".env"
        p.write_text(content, encoding='utf-8')
        return str(p)
    return _create


def test_parse_simple_pairs(tmp_env_file):
    path = tmp_env_file("DB_HOST=localhost\nDB_PORT=5432\n")
    result = parse_env_file(path)
    assert result == {"DB_HOST": "localhost", "DB_PORT": "5432"}


def test_parse_ignores_comments(tmp_env_file):
    path = tmp_env_file("# This is a comment\nAPP_ENV=production\n")
    result = parse_env_file(path)
    assert result == {"APP_ENV": "production"}


def test_parse_ignores_blank_lines(tmp_env_file):
    path = tmp_env_file("\nKEY=value\n\n")
    result = parse_env_file(path)
    assert result == {"KEY": "value"}


def test_parse_strips_double_quotes(tmp_env_file):
    path = tmp_env_file('SECRET="my secret value"\n')
    result = parse_env_file(path)
    assert result == {"SECRET": "my secret value"}


def test_parse_strips_single_quotes(tmp_env_file):
    path = tmp_env_file("TOKEN='abc123'\n")
    result = parse_env_file(path)
    assert result == {"TOKEN": "abc123"}


def test_parse_raises_on_invalid_line(tmp_env_file):
    path = tmp_env_file("INVALID LINE\n")
    with pytest.raises(EnvParseError, match="Invalid syntax"):
        parse_env_file(path)


def test_parse_raises_file_not_found():
    with pytest.raises(FileNotFoundError):
        parse_env_file("/nonexistent/.env")


def test_write_and_read_roundtrip(tmp_path):
    filepath = str(tmp_path / ".env")
    original = {"API_KEY": "abc123", "DEBUG": "true"}
    write_env_file(filepath, original)
    result = parse_env_file(filepath)
    assert result == original


def test_write_quotes_values_with_spaces(tmp_path):
    filepath = str(tmp_path / ".env")
    write_env_file(filepath, {"MSG": "hello world"})
    content = open(filepath).read()
    assert 'MSG="hello world"' in content
