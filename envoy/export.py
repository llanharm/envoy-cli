"""Export .env file contents to various formats (shell, JSON, Docker)."""

from __future__ import annotations

import json
import shlex
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class ExportFormat(str, Enum):
    SHELL = "shell"
    JSON = "json"
    DOCKER = "docker"


class ExportError(Exception):
    """Raised when export cannot be completed."""


@dataclass
class ExportResult:
    format: ExportFormat
    content: str
    key_count: int

    def __str__(self) -> str:
        return self.content


def export_env(
    env: Dict[str, str],
    fmt: ExportFormat = ExportFormat.SHELL,
    prefix: Optional[str] = None,
    export_keyword: bool = True,
) -> ExportResult:
    """Render *env* dict as the requested format.

    Args:
        env: Mapping of key -> value.
        fmt: Target output format.
        prefix: Optional string prepended to every key (shell/docker only).
        export_keyword: Prepend ``export`` to shell assignments when True.

    Returns:
        ExportResult with rendered content and metadata.
    """
    if not isinstance(fmt, ExportFormat):
        try:
            fmt = ExportFormat(fmt)
        except ValueError:
            raise ExportError(
                f"Unknown format {fmt!r}. Choose from: {[f.value for f in ExportFormat]}"
            )

    if fmt == ExportFormat.SHELL:
        content = _to_shell(env, prefix=prefix, export_keyword=export_keyword)
    elif fmt == ExportFormat.JSON:
        content = _to_json(env, prefix=prefix)
    elif fmt == ExportFormat.DOCKER:
        content = _to_docker(env, prefix=prefix)
    else:  # pragma: no cover
        raise ExportError(f"Unhandled format: {fmt}")

    return ExportResult(format=fmt, content=content, key_count=len(env))


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _apply_prefix(key: str, prefix: Optional[str]) -> str:
    return f"{prefix}{key}" if prefix else key


def _to_shell(env: Dict[str, str], *, prefix: Optional[str], export_keyword: bool) -> str:
    lines = []
    keyword = "export " if export_keyword else ""
    for key, value in env.items():
        full_key = _apply_prefix(key, prefix)
        quoted = shlex.quote(value)
        lines.append(f"{keyword}{full_key}={quoted}")
    return "\n".join(lines)


def _to_json(env: Dict[str, str], *, prefix: Optional[str]) -> str:
    data = {_apply_prefix(k, prefix): v for k, v in env.items()}
    return json.dumps(data, indent=2)


def _to_docker(env: Dict[str, str], *, prefix: Optional[str]) -> str:
    """Docker ``--env-file`` compatible format (KEY=VALUE, no quotes)."""
    lines = []
    for key, value in env.items():
        full_key = _apply_prefix(key, prefix)
        lines.append(f"{full_key}={value}")
    return "\n".join(lines)
