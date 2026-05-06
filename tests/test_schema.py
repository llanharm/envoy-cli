"""Tests for envoy.schema."""
import pytest
from envoy.schema import SchemaField, SchemaResult, SchemaViolation, validate_schema


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _simple_schema(*keys: str, required: bool = True) -> list:
    return [SchemaField(key=k, required=required) for k in keys]


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_valid_env_returns_ok():
    schema = _simple_schema("APP_NAME", "DEBUG")
    result = validate_schema({"APP_NAME": "myapp", "DEBUG": "true"}, schema)
    assert result.ok
    assert result.violations == []


def test_missing_required_key_is_violation():
    schema = _simple_schema("APP_NAME", "SECRET_KEY")
    result = validate_schema({"APP_NAME": "myapp"}, schema)
    assert not result.ok
    assert "MISSING_REQUIRED" in result.error_codes
    assert any(v.key == "SECRET_KEY" for v in result.violations)


def test_optional_missing_key_is_not_violation():
    schema = [SchemaField(key="APP_NAME"), SchemaField(key="DEBUG", required=False)]
    result = validate_schema({"APP_NAME": "myapp"}, schema)
    assert result.ok


def test_undeclared_key_is_violation():
    schema = _simple_schema("APP_NAME")
    result = validate_schema({"APP_NAME": "myapp", "EXTRA": "oops"}, schema)
    assert not result.ok
    assert "UNDECLARED_KEY" in result.error_codes
    assert any(v.key == "EXTRA" for v in result.violations)


def test_pattern_match_passes():
    schema = [SchemaField(key="PORT", pattern=r"\d+")]
    result = validate_schema({"PORT": "8080"}, schema)
    assert result.ok


def test_pattern_mismatch_is_violation():
    schema = [SchemaField(key="PORT", pattern=r"\d+")]
    result = validate_schema({"PORT": "not-a-number"}, schema)
    assert not result.ok
    assert "INVALID_VALUE" in result.error_codes


def test_multiple_violations_collected():
    schema = _simple_schema("A", "B")
    result = validate_schema({"C": "extra"}, schema)
    codes = result.error_codes
    assert codes.count("MISSING_REQUIRED") == 2
    assert "UNDECLARED_KEY" in codes


def test_to_dict_shape():
    v = SchemaViolation(key="FOO", code="MISSING_REQUIRED", message="missing")
    d = v.to_dict()
    assert d == {"key": "FOO", "code": "MISSING_REQUIRED", "message": "missing"}


def test_empty_env_and_empty_schema_is_ok():
    result = validate_schema({}, [])
    assert result.ok


def test_schema_field_description_is_optional():
    f = SchemaField(key="X")
    assert f.description == ""
