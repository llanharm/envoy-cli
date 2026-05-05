"""Key rotation support: rename or replace keys across a .env file."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy.parser import parse_env_file, write_env_file, validate_key


@dataclass
class RotateResult:
    renamed: List[str] = field(default_factory=list)
    replaced: Dict[str, str] = field(default_factory=dict)  # old_key -> new_key
    skipped: List[str] = field(default_factory=list)
    output_path: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "renamed": self.renamed,
            "replaced": self.replaced,
            "skipped": self.skipped,
            "output_path": self.output_path,
        }

    @property
    def total_changes(self) -> int:
        return len(self.renamed) + len(self.replaced)


def rotate_keys(
    env_path: str,
    renames: Dict[str, str],
    *,
    output_path: Optional[str] = None,
    overwrite: bool = False,
) -> RotateResult:
    """Rename keys in *env_path* according to *renames* mapping.

    Parameters
    ----------
    env_path:    Path to the source .env file.
    renames:     Mapping of {old_key: new_key}.
    output_path: Where to write the result.  Defaults to *env_path* when
                 *overwrite* is True, otherwise required.
    overwrite:   Allow writing back to the original file.

    Returns a :class:`RotateResult` describing what changed.
    """
    if output_path is None and not overwrite:
        raise ValueError(
            "Provide output_path or set overwrite=True to write back to the source file."
        )

    dest = output_path or env_path
    result = RotateResult(output_path=dest)

    # Validate all target key names up-front.
    for old_key, new_key in renames.items():
        try:
            validate_key(new_key)
        except ValueError as exc:
            raise ValueError(f"Invalid target key name {new_key!r}: {exc}") from exc

    env = parse_env_file(env_path)
    rotated: Dict[str, str] = {}

    for key, value in env.items():
        if key in renames:
            new_key = renames[key]
            if new_key in env and new_key not in renames:
                # Target key already exists and is not itself being rotated away.
                result.skipped.append(key)
                rotated[key] = value
                continue
            rotated[new_key] = value
            result.renamed.append(key)
            result.replaced[key] = new_key
        else:
            rotated[key] = value

    write_env_file(dest, rotated)
    return result
