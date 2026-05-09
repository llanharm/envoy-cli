"""Tests for envoy.inherit."""
from __future__ import annotations

import pytest
from pathlib import Path

from envoy.inherit import inherit_env, InheritResult
from envoy.parser import write_env_file


@pytest.fixture()
def base_env(tmp_path: Path) -> Path:
    p = tmp_path / "base.env"
    write_env_file(p, {"HOST": "localhost", "PORT": "5432", "DEBUG": "false"})
    return p


@pytest.fixture()
def child_env(tmp_path: Path) -> Path:
    p = tmp_path / "child.env"
    write_env_file(p, {"PORT": "9999", "APP_NAME": "myapp"})
    return p


def test_requires_at_least_one_base(child_env: Path) -> None:
    with pytest.raises(ValueError, match="At least one base"):
        inherit_env(base_paths=[], child_path=child_env)


def test_child_values_override_base(base_env: Path, child_env: Path) -> None:
    result = inherit_env([base_env], child_env, dry_run=True)
    assert result.merged["PORT"] == "9999"  # child wins


def test_base_keys_inherited_when_absent_in_child(base_env: Path, child_env: Path) -> None:
    result = inherit_env([base_env], child_env, dry_run=True)
    assert result.merged["HOST"] == "localhost"
    assert result.merged["DEBUG"] == "false"


def test_child_only_keys_included(base_env: Path, child_env: Path) -> None:
    result = inherit_env([base_env], child_env, dry_run=True)
    assert result.merged["APP_NAME"] == "myapp"


def test_inherited_keys_list(base_env: Path, child_env: Path) -> None:
    result = inherit_env([base_env], child_env, dry_run=True)
    assert "HOST" in result.inherited_keys
    assert "DEBUG" in result.inherited_keys
    assert "PORT" not in result.inherited_keys


def test_overridden_keys_list(base_env: Path, child_env: Path) -> None:
    result = inherit_env([base_env], child_env, dry_run=True)
    assert result.overridden_keys == ["PORT"]


def test_dry_run_does_not_write(base_env: Path, child_env: Path) -> None:
    original = child_env.read_text()
    inherit_env([base_env], child_env, dry_run=True)
    assert child_env.read_text() == original


def test_writes_to_output_path(tmp_path: Path, base_env: Path, child_env: Path) -> None:
    out = tmp_path / "merged.env"
    inherit_env([base_env], child_env, output_path=out)
    assert out.exists()
    content = out.read_text()
    assert "HOST" in content
    assert "APP_NAME" in content


def test_multiple_bases_priority(tmp_path: Path, child_env: Path) -> None:
    b1 = tmp_path / "b1.env"
    b2 = tmp_path / "b2.env"
    write_env_file(b1, {"SHARED": "from_b1", "ONLY_B1": "yes"})
    write_env_file(b2, {"SHARED": "from_b2", "ONLY_B2": "yes"})
    result = inherit_env([b1, b2], child_env, dry_run=True)
    # b2 has higher priority than b1
    assert result.merged["SHARED"] == "from_b2"
    assert result.merged["ONLY_B1"] == "yes"
    assert result.merged["ONLY_B2"] == "yes"


def test_to_dict_shape(base_env: Path, child_env: Path) -> None:
    result = inherit_env([base_env], child_env, dry_run=True)
    d = result.to_dict()
    assert "base_files" in d
    assert "child_file" in d
    assert "total_keys" in d
    assert isinstance(d["overridden_keys"], list)
