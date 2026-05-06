"""Tests for envoy.merge."""
import os
import pytest

from envoy.merge import (
    MergeConflict,
    MergeConflictError,
    MergeResult,
    Strategy,
    merge_env_files,
)


@pytest.fixture()
def env_a(tmp_path):
    p = tmp_path / "a.env"
    p.write_text("APP=myapp\nDEBUG=true\nSHARED=alpha\n")
    return str(p)


@pytest.fixture()
def env_b(tmp_path):
    p = tmp_path / "b.env"
    p.write_text("PORT=8080\nSHARED=beta\nEXTRA=yes\n")
    return str(p)


@pytest.fixture()
def env_c(tmp_path):
    p = tmp_path / "c.env"
    p.write_text("SHARED=gamma\nNEW_KEY=new\n")
    return str(p)


def test_requires_at_least_two_files(env_a):
    with pytest.raises(ValueError, match="at least two"):
        merge_env_files([env_a])


def test_merge_combines_disjoint_keys(env_a, env_b):
    result = merge_env_files([env_a, env_b])
    assert "APP" in result.merged
    assert "PORT" in result.merged
    assert "EXTRA" in result.merged


def test_strategy_last_wins_on_conflict(env_a, env_b):
    result = merge_env_files([env_a, env_b], strategy=Strategy.LAST)
    assert result.merged["SHARED"] == "beta"
    assert len(result.conflicts) == 1
    assert result.conflicts[0].key == "SHARED"


def test_strategy_first_wins_on_conflict(env_a, env_b):
    result = merge_env_files([env_a, env_b], strategy=Strategy.FIRST)
    assert result.merged["SHARED"] == "alpha"


def test_strategy_strict_raises_on_conflict(env_a, env_b):
    with pytest.raises(MergeConflictError) as exc_info:
        merge_env_files([env_a, env_b], strategy=Strategy.STRICT)
    assert "SHARED" in str(exc_info.value)
    assert len(exc_info.value.conflicts) == 1


def test_ok_false_when_conflicts_present(env_a, env_b):
    result = merge_env_files([env_a, env_b])
    assert result.ok is False


def test_ok_true_when_no_conflicts(env_a, env_c, tmp_path):
    # env_a has SHARED; env_c also has SHARED — use two files with no overlap
    p = tmp_path / "no_overlap.env"
    p.write_text("UNIQUE_KEY=value\n")
    result = merge_env_files([env_a, str(p)])
    assert result.ok is True


def test_overrides_applied_last(env_a, env_b):
    result = merge_env_files([env_a, env_b], overrides={"SHARED": "override", "NEW": "1"})
    assert result.merged["SHARED"] == "override"
    assert result.merged["NEW"] == "1"


def test_sources_recorded(env_a, env_b):
    result = merge_env_files([env_a, env_b])
    assert env_a in result.sources
    assert env_b in result.sources


def test_to_dict_shape(env_a, env_b):
    result = merge_env_files([env_a, env_b])
    d = result.to_dict()
    assert "ok" in d
    assert "merged" in d
    assert "conflicts" in d
    assert isinstance(d["conflicts"], list)


def test_three_way_merge(env_a, env_b, env_c):
    result = merge_env_files([env_a, env_b, env_c], strategy=Strategy.LAST)
    assert result.merged["SHARED"] == "gamma"
    assert result.merged["APP"] == "myapp"
    assert result.merged["NEW_KEY"] == "new"
