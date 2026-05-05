"""Tests for envoy.rotate."""

import pytest

from envoy.rotate import rotate_keys, RotateResult
from envoy.parser import parse_env_file


@pytest.fixture()
def tmp_env(tmp_path):
    """Return a helper that writes a .env file and yields its path."""
    def _make(content: str):
        p = tmp_path / ".env"
        p.write_text(content)
        return str(p)
    return _make


def test_rotate_renames_single_key(tmp_env):
    path = tmp_env("DB_HOST=localhost\nDB_PORT=5432\n")
    out = str(path) + ".out"
    result = rotate_keys(path, {"DB_HOST": "DATABASE_HOST"}, output_path=out)
    assert "DB_HOST" in result.renamed
    assert result.replaced["DB_HOST"] == "DATABASE_HOST"
    env = parse_env_file(out)
    assert "DATABASE_HOST" in env
    assert env["DATABASE_HOST"] == "localhost"
    assert "DB_HOST" not in env


def test_rotate_preserves_untouched_keys(tmp_env):
    path = tmp_env("FOO=bar\nBAZ=qux\n")
    out = str(path) + ".out"
    rotate_keys(path, {"FOO": "FOO_NEW"}, output_path=out)
    env = parse_env_file(out)
    assert env["BAZ"] == "qux"


def test_rotate_multiple_keys(tmp_env):
    path = tmp_env("A=1\nB=2\nC=3\n")
    out = str(path) + ".out"
    result = rotate_keys(path, {"A": "ALPHA", "B": "BETA"}, output_path=out)
    assert set(result.renamed) == {"A", "B"}
    env = parse_env_file(out)
    assert env["ALPHA"] == "1"
    assert env["BETA"] == "2"
    assert env["C"] == "3"


def test_overwrite_flag_writes_to_source(tmp_env):
    path = tmp_env("SECRET_KEY=abc\n")
    result = rotate_keys(path, {"SECRET_KEY": "APP_SECRET"}, overwrite=True)
    assert result.output_path == path
    env = parse_env_file(path)
    assert "APP_SECRET" in env
    assert "SECRET_KEY" not in env


def test_raises_without_output_or_overwrite(tmp_env):
    path = tmp_env("X=1\n")
    with pytest.raises(ValueError, match="output_path"):
        rotate_keys(path, {"X": "Y"})


def test_raises_on_invalid_target_key(tmp_env):
    path = tmp_env("X=1\n")
    with pytest.raises(ValueError, match="Invalid target key"):
        rotate_keys(path, {"X": "123invalid"}, overwrite=True)


def test_skips_when_target_key_exists(tmp_env):
    """If the target key already exists and is not being rotated away, skip."""
    path = tmp_env("OLD=1\nNEW=already\n")
    out = str(path) + ".out"
    result = rotate_keys(path, {"OLD": "NEW"}, output_path=out)
    assert "OLD" in result.skipped
    assert result.total_changes == 0


def test_to_dict_contains_expected_keys(tmp_env):
    path = tmp_env("K=v\n")
    out = str(path) + ".out"
    result = rotate_keys(path, {"K": "KEY"}, output_path=out)
    d = result.to_dict()
    assert set(d.keys()) == {"renamed", "replaced", "skipped", "output_path"}
