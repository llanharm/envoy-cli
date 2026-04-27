"""Human-readable and JSON report generation for env file analysis."""

from __future__ import annotations

import json
from typing import Dict, List, Optional

from envoy.diff import EnvDiff
from envoy.redact import RedactResult


def _section(title: str, items: List[str], indent: int = 2) -> str:
    pad = " " * indent
    lines = [f"  {title}"]
    for item in items:
        lines.append(f"{pad}  {item}")
    return "\n".join(lines)


def render_text(
    diff: Optional[EnvDiff] = None,
    redact_result: Optional[RedactResult] = None,
    title: str = "envoy report",
) -> str:
    """Render a plain-text report combining diff and redaction info."""
    lines: List[str] = [f"=== {title} ==="]

    if diff is not None:
        lines.append("\n[diff]")
        if diff.added:
            lines.append(_section("added", sorted(diff.added)))
        if diff.removed:
            lines.append(_section("removed", sorted(diff.removed)))
        if diff.changed:
            lines.append(_section("changed", sorted(diff.changed)))
        if not (diff.added or diff.removed or diff.changed):
            lines.append("  no changes")

    if redact_result is not None:
        lines.append("\n[redaction]")
        if redact_result.redacted_keys:
            lines.append(
                _section(
                    "redacted keys",
                    sorted(redact_result.redacted_keys),
                )
            )
        else:
            lines.append("  no sensitive keys detected")

    return "\n".join(lines)


def render_json(
    diff: Optional[EnvDiff] = None,
    redact_result: Optional[RedactResult] = None,
    title: str = "envoy report",
) -> str:
    """Render a JSON report combining diff and redaction info."""
    payload: Dict = {"title": title}

    if diff is not None:
        payload["diff"] = {
            "added": sorted(diff.added),
            "removed": sorted(diff.removed),
            "changed": sorted(diff.changed),
            "unchanged": sorted(diff.unchanged),
        }

    if redact_result is not None:
        payload["redaction"] = {
            "redacted_keys": sorted(redact_result.redacted_keys),
            "values": redact_result.redacted,
        }

    return json.dumps(payload, indent=2)
