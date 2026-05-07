"""Profile management: named env-var groups for different environments."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


class ProfileError(Exception):
    """Raised when a profile operation fails."""


@dataclass
class Profile:
    name: str
    env_file: str
    description: str = ""
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "env_file": self.env_file,
            "description": self.description,
            "tags": self.tags,
        }

    @staticmethod
    def from_dict(data: dict) -> "Profile":
        return Profile(
            name=data["name"],
            env_file=data["env_file"],
            description=data.get("description", ""),
            tags=data.get("tags", []),
        )


@dataclass
class ProfileStore:
    store_path: Path
    _profiles: Dict[str, Profile] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        if self.store_path.exists():
            raw = json.loads(self.store_path.read_text())
            self._profiles = {k: Profile.from_dict(v) for k, v in raw.items()}

    def _save(self) -> None:
        self.store_path.write_text(
            json.dumps({k: v.to_dict() for k, v in self._profiles.items()}, indent=2)
        )

    def add(self, profile: Profile) -> None:
        if profile.name in self._profiles:
            raise ProfileError(f"Profile '{profile.name}' already exists.")
        self._profiles[profile.name] = profile
        self._save()

    def remove(self, name: str) -> None:
        if name not in self._profiles:
            raise ProfileError(f"Profile '{name}' not found.")
        del self._profiles[name]
        self._save()

    def get(self, name: str) -> Profile:
        if name not in self._profiles:
            raise ProfileError(f"Profile '{name}' not found.")
        return self._profiles[name]

    def list_profiles(self, tag: Optional[str] = None) -> List[Profile]:
        profiles = list(self._profiles.values())
        if tag:
            profiles = [p for p in profiles if tag in p.tags]
        return profiles
