"""Lint .env files for common issues and style violations."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import re

# Patterns considered risky or malformed
_UNQUOTED_SPACE_RE = re.compile(r'^[A-Z_][A-Z0-9_]*=\S.*\s+\S')
_MISSING_VALUE_RE = re.compile(r'^[A-Z_][A-Z0-9_]*=$')
_LOWERCASE_KEY_RE = re.compile(r'^[a-z]')
_LONG_VALUE_THRESHOLD = 256


@dataclass
class LintIssue:
    line: int
    key: str | None
    code: str
    message: str

    def to_dict(self) -> dict:
        return {
            "line": self.line,
            "key": self.key,
            "code": self.code,
            "message": self.message,
        }


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.issues) == 0

    def error_codes(self) -> List[str]:
        return [i.code for i in self.issues]


def lint_env_file(path: str) -> LintResult:
    """Lint the .env file at *path* and return a LintResult."""
    result = LintResult()
    seen_keys: dict[str, int] = {}

    with open(path, "r", encoding="utf-8") as fh:
        lines = fh.readlines()

    for lineno, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")

        # Skip blanks and comments
        if not line or line.lstrip().startswith("#"):
            continue

        if "=" not in line:
            result.issues.append(LintIssue(lineno, None, "E001", f"Invalid syntax: {line!r}"))
            continue

        key, _, value = line.partition("=")
        key = key.strip()

        if _LOWERCASE_KEY_RE.match(key):
            result.issues.append(LintIssue(lineno, key, "W001", f"Key '{key}' is not uppercase"))

        if key in seen_keys:
            result.issues.append(
                LintIssue(lineno, key, "E002", f"Duplicate key '{key}' (first seen on line {seen_keys[key]})")
            )
        else:
            seen_keys[key] = lineno

        if _MISSING_VALUE_RE.match(line):
            result.issues.append(LintIssue(lineno, key, "W002", f"Key '{key}' has an empty value"))

        if _UNQUOTED_SPACE_RE.match(line):
            result.issues.append(LintIssue(lineno, key, "W003", f"Value for '{key}' contains unquoted spaces"))

        if len(value) > _LONG_VALUE_THRESHOLD:
            result.issues.append(
                LintIssue(lineno, key, "W004", f"Value for '{key}' exceeds {_LONG_VALUE_THRESHOLD} characters")
            )

    return result
