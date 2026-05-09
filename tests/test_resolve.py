"""Tests for envoy.resolve."""
from __future__ import annotations

import pytest

from envoy.resolve import resolve_env_files, ResolveResult


@pytest.fixture()
def env_base(tmp_path):
    p = tmp_path / "base.env"
    p.write_text("APP=base\nDEBUG=false\nBASE_ONLY=yes\n")
    return str(p)


@pytest.fixture()
def env_override(tmp_path):
    p = tmp_path / "override.env"
    p.write_text("APP=prod\nEXTRA=1\n")
    return str(p)


@pytest.fixture()
def env_top(tmp_path):
    p = tmp_path / "top.env"
    p.write_text("APP=local\nLOCAL=true\n")
    return str(p)


def test_requires_at_least_one_file():
    with pytest.raises(ValueError, match="at least one"):
        resolve_env_files([])


def test_single_file_returns_its_values(env_base):
    result = resolve_env_files([env_base])
    assert result.effective["APP"] == "base"
    assert result.effective["DEBUG"] == "false"
    assert result.total_keys == 3


def test_later_file_overrides_earlier(env_base, env_override):
    result = resolve_env_files([env_base, env_override])
    assert result.effective["APP"] == "prod"


def test_earlier_unique_keys_preserved(env_base, env_override):
    result = resolve_env_files([env_base, env_override])
    assert "BASE_ONLY" in result.effective
    assert "EXTRA" in result.effective


def test_three_layers_last_wins(env_base, env_override, env_top):
    result = resolve_env_files([env_base, env_override, env_top])
    assert result.effective["APP"] == "local"


def test_sources_track_winning_file(env_base, env_override):
    result = resolve_env_files([env_base, env_override])
    assert result.sources["APP"].endswith("override.env")
    assert result.sources["BASE_ONLY"].endswith("base.env")


def test_overridden_records_shadowed_files(env_base, env_override):
    result = resolve_env_files([env_base, env_override])
    assert "APP" in result.overridden
    assert any("base.env" in p for p in result.overridden["APP"])


def test_unique_keys_not_in_overridden(env_base, env_override):
    result = resolve_env_files([env_base, env_override])
    assert "BASE_ONLY" not in result.overridden
    assert "EXTRA" not in result.overridden


def test_base_dict_is_lowest_priority(env_base):
    result = resolve_env_files([env_base], base={"APP": "from_base_dict", "SEED": "yes"})
    assert result.effective["APP"] == "base"  # file wins over base dict
    assert result.effective["SEED"] == "yes"


def test_to_dict_contains_expected_keys(env_base):
    result = resolve_env_files([env_base])
    d = result.to_dict()
    assert set(d.keys()) == {"effective", "sources", "overridden", "files", "total_keys", "total_overridden"}


def test_files_list_matches_input(env_base, env_override):
    result = resolve_env_files([env_base, env_override])
    assert len(result.files) == 2
