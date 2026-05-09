"""Tag env file keys with arbitrary labels for grouping and filtering."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


class TagError(Exception):
    """Raised when tag operations fail."""


@dataclass
class TagResult:
    tagged: Dict[str, List[str]]  # key -> list of tags
    untagged: List[str]           # keys with no tags
    all_tags: List[str]           # sorted unique tags across all keys

    def to_dict(self) -> dict:
        return {
            "tagged": self.tagged,
            "untagged": self.untagged,
            "all_tags": self.all_tags,
        }

    @property
    def total_tagged(self) -> int:
        return len(self.tagged)


def load_tags(tag_file: Path) -> Dict[str, List[str]]:
    """Load a JSON tag map from *tag_file*.

    Expected format::

        {"DB_HOST": ["database", "infra"], "SECRET_KEY": ["security"]}
    """
    if not tag_file.exists():
        raise TagError(f"Tag file not found: {tag_file}")
    try:
        data = json.loads(tag_file.read_text())
    except json.JSONDecodeError as exc:
        raise TagError(f"Invalid JSON in tag file: {exc}") from exc
    if not isinstance(data, dict):
        raise TagError("Tag file must be a JSON object mapping keys to tag lists")
    for k, v in data.items():
        if not isinstance(v, list) or not all(isinstance(t, str) for t in v):
            raise TagError(f"Tags for key '{k}' must be a list of strings")
    return data


def save_tags(tag_file: Path, tags: Dict[str, List[str]]) -> None:
    """Persist *tags* to *tag_file* as pretty-printed JSON."""
    tag_file.write_text(json.dumps(tags, indent=2, sort_keys=True))


def tag_env(
    env: Dict[str, str],
    tags: Dict[str, List[str]],
    filter_tag: Optional[str] = None,
) -> TagResult:
    """Build a :class:`TagResult` for *env* using *tags*.

    If *filter_tag* is given only keys carrying that tag are included in
    ``tagged``; the rest move to ``untagged``.
    """
    tagged: Dict[str, List[str]] = {}
    untagged: List[str] = []
    all_tag_set: set = set()

    for key in env:
        key_tags = tags.get(key, [])
        if filter_tag is not None:
            if filter_tag in key_tags:
                tagged[key] = key_tags
                all_tag_set.update(key_tags)
            else:
                untagged.append(key)
        else:
            if key_tags:
                tagged[key] = key_tags
                all_tag_set.update(key_tags)
            else:
                untagged.append(key)

    return TagResult(
        tagged=tagged,
        untagged=sorted(untagged),
        all_tags=sorted(all_tag_set),
    )
