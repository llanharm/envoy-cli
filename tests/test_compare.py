"""Tests for envoy.compare."""
import pytest

from envoy.compare import compare_env_files, CompareResult


@pytest.fixture()
def env_a(tmp_path):
    p = tmp_path / "a.env"
    p.write_text("APP_NAME=myapp\nSECRET_KEY=abc123\nDEBUG=true\n")
    return str(p)


@pytest.fixture()
def env_b(tmp_path):
    p = tmp_path / "b.env"
    p.write_text("APP_NAME=myapp\nSECRET_KEY=xyz789\nNEW_VAR=hello\n")
    return str(p)


@pytest.fixture()
def env_c(tmp_path):
    p = tmp_path / "c.env"
    p.write_text("APP_NAME=otherapp\nSECRET_KEY=abc123\n")
    return str(p)


def test_requires_at_least_two_files(env_a):
    with pytest.raises(ValueError, match="at least two"):
        compare_env_files([env_a])


def test_returns_compare_result(env_a, env_b):
    result = compare_env_files([env_a, env_b])
    assert isinstance(result, CompareResult)


def test_all_keys_sorted_union(env_a, env_b):
    result = compare_env_files([env_a, env_b])
    assert result.all_keys == sorted(["APP_NAME", "SECRET_KEY", "DEBUG", "NEW_VAR"])


def test_matrix_has_none_for_missing_key(env_a, env_b):
    result = compare_env_files([env_a, env_b])
    # DEBUG only in env_a
    assert result.matrix["DEBUG"][env_b] is None
    assert result.matrix["DEBUG"][env_a] == "true"


def test_missing_in_reports_absent_keys(env_a, env_b):
    result = compare_env_files([env_a, env_b])
    missing = result.missing_in(env_b)
    assert "DEBUG" in missing
    assert "APP_NAME" not in missing


def test_keys_unique_to(env_a, env_b):
    result = compare_env_files([env_a, env_b])
    assert result.keys_unique_to(env_a) == ["DEBUG"]
    assert result.keys_unique_to(env_b) == ["NEW_VAR"]


def test_divergent_keys_detects_differing_values(env_a, env_b):
    result = compare_env_files([env_a, env_b])
    divergent = result.divergent_keys()
    assert "SECRET_KEY" in divergent
    assert "APP_NAME" not in divergent


def test_sensitive_values_masked_by_default(env_a, env_b):
    result = compare_env_files([env_a, env_b])
    assert result.matrix["SECRET_KEY"][env_a] == "***"
    assert result.matrix["SECRET_KEY"][env_b] == "***"


def test_sensitive_values_visible_when_mask_off(env_a, env_b):
    result = compare_env_files([env_a, env_b], mask_secrets=False)
    assert result.matrix["SECRET_KEY"][env_a] == "abc123"


def test_three_file_comparison(env_a, env_b, env_c):
    result = compare_env_files([env_a, env_b, env_c])
    assert len(result.files) == 3
    divergent = result.divergent_keys()
    # APP_NAME differs between a/b (myapp) and c (otherapp)
    assert "APP_NAME" in divergent
