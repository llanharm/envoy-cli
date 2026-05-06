"""Schema validation for .env files against a declared spec."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re


@dataclass
class SchemaField:
    key: str
    required: bool = True
    pattern: Optional[str] = None
    description: str = ""

    def validate_value(self, value: str) -> Optional[str]:
        """Return an error message if value is invalid, else None."""
        if self.pattern and not re.fullmatch(self.pattern, value):
            return f"value {value!r} does not match pattern {self.pattern!r}"
        return None


@dataclass
class SchemaViolation:
    key: str
    code: str
    message: str

    def to_dict(self) -> Dict[str, str]:
        return {"key": self.key, "code": self.code, "message": self.message}


@dataclass
class SchemaResult:
    violations: List[SchemaViolation] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.violations) == 0

    @property
    def error_codes(self) -> List[str]:
        return [v.code for v in self.violations]


def validate_schema(
    env: Dict[str, str],
    schema: List[SchemaField],
) -> SchemaResult:
    """Validate *env* dict against a list of SchemaField definitions."""
    violations: List[SchemaViolation] = []
    schema_keys = {f.key for f in schema}

    for field_def in schema:
        if field_def.key not in env:
            if field_def.required:
                violations.append(
                    SchemaViolation(
                        key=field_def.key,
                        code="MISSING_REQUIRED",
                        message=f"required key {field_def.key!r} is missing",
                    )
                )
        else:
            err = field_def.validate_value(env[field_def.key])
            if err:
                violations.append(
                    SchemaViolation(
                        key=field_def.key,
                        code="INVALID_VALUE",
                        message=err,
                    )
                )

    for key in env:
        if key not in schema_keys:
            violations.append(
                SchemaViolation(
                    key=key,
                    code="UNDECLARED_KEY",
                    message=f"key {key!r} is not declared in schema",
                )
            )

    return SchemaResult(violations=violations)
