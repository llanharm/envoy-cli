"""Tests for envoy.tag."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envoy.tag import TagError, load_tags, save_tags, tag_env


@pytest.fixture()
def tag_file(tmp_path: Path) -> Path:
    return tmp_path / ".env-tags.json"


# ---------------------------------------------------------------------------
# load_tags
# ---------------------------------------------------------------------------

def test_load_tags_returns_dict(tag_file: Path) -> None:
    tag_file.write_text(json.dumps({"DB_HOST": ["database"]}))
    result = load_tags(tag_file)
    assert result == {"DB_HOST": ["database"]}


def test_load_tags_raises_when_missing(tag_file: Path) -> None:
    with pytest.raises(TagError, match="not found"):
        load_tags(tag_file)


def test_load_tags_raises_on_invalid_json(tag_file: Path) -> None:
    tag_file.write_text("not json")
    with pytest.raises(TagError, match="Invalid JSON"):
        load_tags(tag_file)


def test_load_tags_raises_when_not_object(tag_file: Path) -> None:
    tag_file.write_text(json.dumps(["a", "b"]))
    with pytest.raises(TagError, match="JSON object"):
        load_tags(tag_file)


def test_load_tags_raises_when_tags_not_list(tag_file: Path) -> None:
    tag_file.write_text(json.dumps({"KEY": "not-a-list"}))
    with pytest.raises(TagError, match="list of strings"):
        load_tags(tag_file)


# ---------------------------------------------------------------------------
# save_tags
# ---------------------------------------------------------------------------

def test_save_tags_creates_file(tag_file: Path) -> None:
    save_tags(tag_file, {"FOO": ["bar"]})
    assert tag_file.exists()
    assert json.loads(tag_file.read_text()) == {"FOO": ["bar"]}


# ---------------------------------------------------------------------------
# tag_env
# ---------------------------------------------------------------------------

ENV = {"DB_HOST": "localhost", "SECRET_KEY": "s3cr3t", "PORT": "5432"}
TAGS = {"DB_HOST": ["database", "infra"], "SECRET_KEY": ["security"]}


def test_tagged_keys_present() -> None:
    result = tag_env(ENV, TAGS)
    assert "DB_HOST" in result.tagged
    assert "SECRET_KEY" in result.tagged


def test_untagged_keys_present() -> None:
    result = tag_env(ENV, TAGS)
    assert "PORT" in result.untagged


def test_all_tags_sorted() -> None:
    result = tag_env(ENV, TAGS)
    assert result.all_tags == sorted({"database", "infra", "security"})


def test_filter_tag_limits_tagged() -> None:
    result = tag_env(ENV, TAGS, filter_tag="database")
    assert list(result.tagged.keys()) == ["DB_HOST"]
    assert "SECRET_KEY" in result.untagged


def test_total_tagged_count() -> None:
    result = tag_env(ENV, TAGS)
    assert result.total_tagged == 2


def test_empty_tags_all_untagged() -> None:
    result = tag_env(ENV, {})
    assert result.tagged == {}
    assert set(result.untagged) == set(ENV.keys())


def test_to_dict_keys() -> None:
    result = tag_env(ENV, TAGS)
    d = result.to_dict()
    assert set(d.keys()) == {"tagged", "untagged", "all_tags"}
