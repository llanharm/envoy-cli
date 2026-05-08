"""Pin management: lock env keys to specific expected values."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import json


@dataclass
class PinViolation:
    key: str
    expected: str
    actual: Optional[str]
    reason: str  # 'mismatch' | 'missing'

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "expected": self.expected,
            "actual": self.actual,
            "reason": self.reason,
        }


@dataclass
class PinResult:
    violations: List[PinViolation] = field(default_factory=list)
    checked: int = 0

    @property
    def ok(self) -> bool:
        return len(self.violations) == 0

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "checked": self.checked,
            "violations": [v.to_dict() for v in self.violations],
        }


def load_pins(pin_file: Path) -> Dict[str, str]:
    """Load a JSON pin file mapping key -> expected value."""
    if not pin_file.exists():
        raise FileNotFoundError(f"Pin file not found: {pin_file}")
    with pin_file.open() as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("Pin file must be a JSON object mapping keys to expected values.")
    return {str(k): str(v) for k, v in data.items()}


def save_pins(pins: Dict[str, str], pin_file: Path) -> None:
    """Persist pins to a JSON file."""
    pin_file.parent.mkdir(parents=True, exist_ok=True)
    with pin_file.open("w") as fh:
        json.dump(pins, fh, indent=2)
        fh.write("\n")


def check_pins(env: Dict[str, str], pins: Dict[str, str]) -> PinResult:
    """Verify that all pinned keys match expected values in *env*."""
    violations: List[PinViolation] = []
    for key, expected in pins.items():
        actual = env.get(key)
        if actual is None:
            violations.append(PinViolation(key=key, expected=expected, actual=None, reason="missing"))
        elif actual != expected:
            violations.append(PinViolation(key=key, expected=expected, actual=actual, reason="mismatch"))
    return PinResult(violations=violations, checked=len(pins))
