"""Generate .env.example template files from existing .env files.

Strips all values, preserving keys, comments, and structure so the
template can be safely committed to version control.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from envoy.parser import parse_env_file, validate_key


@dataclass
class TemplateResult:
    source: Path
    destination: Path
    keys_written: list[str] = field(default_factory=list)
    keys_skipped: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.keys_written) + len(self.keys_skipped)


def generate_template(
    source: Path,
    destination: Optional[Path] = None,
    placeholder: str = "",
    skip_keys: Optional[list[str]] = None,
    overwrite: bool = False,
) -> TemplateResult:
    """Read *source* .env and write a value-stripped template to *destination*.

    Args:
        source: Path to the real .env file.
        destination: Output path; defaults to source with ``.example`` appended.
        placeholder: Value to use instead of an empty string (e.g. ``"<CHANGE_ME>"``).
        skip_keys: Keys to omit entirely from the template.
        overwrite: If *False* and destination exists, raise ``FileExistsError``.

    Returns:
        A :class:`TemplateResult` describing what was written.
    """
    if destination is None:
        destination = source.with_suffix(".env.example") if source.suffix == "" else Path(str(source) + ".example")

    if destination.exists() and not overwrite:
        raise FileExistsError(
            f"Template already exists: {destination}. Pass overwrite=True to replace it."
        )

    skip_set: set[str] = set(skip_keys or [])
    env = parse_env_file(source)

    result = TemplateResult(source=source, destination=destination)
    lines: list[str] = []

    # Preserve header comment
    lines.append(f"# Generated from {source.name} — do NOT commit real values\n")

    for key, _value in env.items():
        if not validate_key(key):
            result.keys_skipped.append(key)
            continue
        if key in skip_set:
            result.keys_skipped.append(key)
            continue
        lines.append(f"{key}={placeholder}\n")
        result.keys_written.append(key)

    destination.write_text("".join(lines), encoding="utf-8")
    return result
