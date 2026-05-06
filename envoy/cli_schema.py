"""CLI sub-command: envoy schema — validate a .env file against a schema spec."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from envoy.parser import parse_env_file, EnvParseError
from envoy.schema import SchemaField, validate_schema, SchemaResult


# ---------------------------------------------------------------------------
# schema spec loader (simple JSON format)
# ---------------------------------------------------------------------------

def _load_schema(path: str) -> List[SchemaField]:
    """Load schema from a JSON file.

    Expected format::

        [
          {"key": "APP_NAME", "required": true, "pattern": null, "description": ""},
          ...
        ]
    """
    raw = json.loads(Path(path).read_text())
    fields = []
    for item in raw:
        fields.append(
            SchemaField(
                key=item["key"],
                required=item.get("required", True),
                pattern=item.get("pattern"),
                description=item.get("description", ""),
            )
        )
    return fields


# ---------------------------------------------------------------------------
# formatting
# ---------------------------------------------------------------------------

def _format_result_text(result: SchemaResult) -> str:
    if result.ok:
        return "schema validation passed — no violations found"
    lines = [f"schema validation failed ({len(result.violations)} violation(s)):"]
    for v in result.violations:
        lines.append(f"  [{v.code}] {v.key}: {v.message}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# parser + command
# ---------------------------------------------------------------------------

def build_schema_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # noqa: SLF001
    p = subparsers.add_parser(
        "schema",
        help="validate a .env file against a JSON schema spec",
    )
    p.add_argument("env_file", help="path to the .env file")
    p.add_argument("schema_file", help="path to the JSON schema spec")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="output_format",
        help="output format (default: text)",
    )
    return p


def cmd_schema(args: argparse.Namespace) -> int:
    try:
        env = parse_env_file(args.env_file)
    except (EnvParseError, FileNotFoundError) as exc:
        print(f"error reading env file: {exc}", file=sys.stderr)
        return 1

    try:
        schema = _load_schema(args.schema_file)
    except (json.JSONDecodeError, KeyError, FileNotFoundError) as exc:
        print(f"error reading schema file: {exc}", file=sys.stderr)
        return 1

    result = validate_schema(env, schema)

    if args.output_format == "json":
        print(json.dumps([v.to_dict() for v in result.violations], indent=2))
    else:
        print(_format_result_text(result))

    return 0 if result.ok else 1
