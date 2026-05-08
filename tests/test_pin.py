"""Tests for envoy.pin."""
import json
from pathlib import Path

import pytest

from envoy.pin import (
    PinResult,
    PinViolation,
    check_pins,
    load_pins,
    save_pins,
)


@pytest.fixture()
def pin_file(tmp_path: Path) -> Path:
    p = tmp_path / "pins.json"
    p.write_text(json.dumps({"APP_ENV": "production", "DEBUG": "false"}))
    return p


def test_load_pins_returns_dict(pin_file: Path):
    pins = load_pins(pin_file)
    assert pins == {"APP_ENV": "production", "DEBUG": "false"}


def test_load_pins_raises_when_missing(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_pins(tmp_path / "nonexistent.json")


def test_load_pins_raises_on_invalid_structure(tmp_path: Path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(["not", "a", "dict"]))
    with pytest.raises(ValueError):
        load_pins(bad)


def test_save_pins_creates_file(tmp_path: Path):
    dest = tmp_path / "sub" / "pins.json"
    save_pins({"KEY": "val"}, dest)
    assert dest.exists()
    assert json.loads(dest.read_text()) == {"KEY": "val"}


def test_check_pins_all_match():
    env = {"APP_ENV": "production", "DEBUG": "false", "EXTRA": "ignored"}
    pins = {"APP_ENV": "production", "DEBUG": "false"}
    result = check_pins(env, pins)
    assert result.ok is True
    assert result.checked == 2
    assert result.violations == []


def test_check_pins_detects_mismatch():
    env = {"APP_ENV": "staging"}
    pins = {"APP_ENV": "production"}
    result = check_pins(env, pins)
    assert result.ok is False
    assert len(result.violations) == 1
    v = result.violations[0]
    assert v.key == "APP_ENV"
    assert v.reason == "mismatch"
    assert v.actual == "staging"
    assert v.expected == "production"


def test_check_pins_detects_missing_key():
    env = {"OTHER": "value"}
    pins = {"APP_ENV": "production"}
    result = check_pins(env, pins)
    assert result.ok is False
    v = result.violations[0]
    assert v.reason == "missing"
    assert v.actual is None


def test_check_pins_empty_pins_always_ok():
    result = check_pins({"A": "1"}, {})
    assert result.ok is True
    assert result.checked == 0


def test_to_dict_structure():
    result = PinResult(
        violations=[PinViolation(key="X", expected="1", actual="2", reason="mismatch")],
        checked=1,
    )
    d = result.to_dict()
    assert d["ok"] is False
    assert d["checked"] == 1
    assert d["violations"][0]["key"] == "X"
