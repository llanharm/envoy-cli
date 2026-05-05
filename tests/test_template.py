"""Tests for envoy.template — .env.example generation."""
from pathlib import Path

import pytest

from envoy.template import TemplateResult, generate_template


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "SECRET_KEY=supersecret\n"
        "DEBUG=true\n",
        encoding="utf-8",
    )
    return p


def test_returns_template_result(env_file: Path, tmp_path: Path) -> None:
    dest = tmp_path / ".env.example"
    result = generate_template(env_file, destination=dest)
    assert isinstance(result, TemplateResult)


def test_destination_file_is_created(env_file: Path, tmp_path: Path) -> None:
    dest = tmp_path / ".env.example"
    generate_template(env_file, destination=dest)
    assert dest.exists()


def test_values_are_stripped(env_file: Path, tmp_path: Path) -> None:
    dest = tmp_path / ".env.example"
    generate_template(env_file, destination=dest)
    content = dest.read_text()
    assert "localhost" not in content
    assert "supersecret" not in content


def test_keys_are_preserved(env_file: Path, tmp_path: Path) -> None:
    dest = tmp_path / ".env.example"
    generate_template(env_file, destination=dest)
    content = dest.read_text()
    for key in ("DB_HOST", "DB_PORT", "SECRET_KEY", "DEBUG"):
        assert key in content


def test_placeholder_is_used(env_file: Path, tmp_path: Path) -> None:
    dest = tmp_path / ".env.example"
    generate_template(env_file, destination=dest, placeholder="<CHANGE_ME>")
    content = dest.read_text()
    assert "<CHANGE_ME>" in content


def test_skip_keys_are_omitted(env_file: Path, tmp_path: Path) -> None:
    dest = tmp_path / ".env.example"
    result = generate_template(env_file, destination=dest, skip_keys=["SECRET_KEY"])
    content = dest.read_text()
    assert "SECRET_KEY" not in content
    assert "SECRET_KEY" in result.keys_skipped


def test_keys_written_count(env_file: Path, tmp_path: Path) -> None:
    dest = tmp_path / ".env.example"
    result = generate_template(env_file, destination=dest, skip_keys=["DEBUG"])
    assert len(result.keys_written) == 3
    assert result.total == 4


def test_default_destination_uses_example_suffix(env_file: Path) -> None:
    result = generate_template(env_file, overwrite=True)
    expected = Path(str(env_file) + ".example")
    assert result.destination == expected
    expected.unlink(missing_ok=True)


def test_raises_if_destination_exists_without_overwrite(env_file: Path, tmp_path: Path) -> None:
    dest = tmp_path / ".env.example"
    dest.write_text("existing", encoding="utf-8")
    with pytest.raises(FileExistsError, match="overwrite=True"):
        generate_template(env_file, destination=dest, overwrite=False)


def test_overwrite_replaces_existing(env_file: Path, tmp_path: Path) -> None:
    dest = tmp_path / ".env.example"
    dest.write_text("old content", encoding="utf-8")
    generate_template(env_file, destination=dest, overwrite=True)
    assert "old content" not in dest.read_text()
