"""Symmetric encryption/decryption of .env file values using Fernet."""
from __future__ import annotations

import base64
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:  # pragma: no cover
    Fernet = None  # type: ignore
    InvalidToken = Exception  # type: ignore


class EncryptError(Exception):
    """Raised when encryption/decryption fails."""


@dataclass
class EncryptResult:
    encrypted: Dict[str, str] = field(default_factory=dict)
    skipped: List[str] = field(default_factory=list)
    key_used: Optional[str] = None

    @property
    def total_encrypted(self) -> int:
        return len(self.encrypted)


def _require_cryptography() -> None:
    if Fernet is None:
        raise EncryptError(
            "'cryptography' package is required. Install it with: pip install cryptography"
        )


def generate_key() -> str:
    """Generate a new Fernet key and return it as a URL-safe base64 string."""
    _require_cryptography()
    return Fernet.generate_key().decode()


def encrypt_env(
    env: Dict[str, str],
    key: str,
    keys_to_encrypt: Optional[List[str]] = None,
) -> EncryptResult:
    """Encrypt values in *env* for the given keys (or all keys if None)."""
    _require_cryptography()
    try:
        fernet = Fernet(key.encode())
    except Exception as exc:
        raise EncryptError(f"Invalid encryption key: {exc}") from exc

    result = EncryptResult(key_used=key)
    targets = keys_to_encrypt if keys_to_encrypt is not None else list(env.keys())

    for k, v in env.items():
        if k in targets:
            result.encrypted[k] = fernet.encrypt(v.encode()).decode()
        else:
            result.skipped.append(k)
    return result


def decrypt_env(
    env: Dict[str, str],
    key: str,
) -> Dict[str, str]:
    """Decrypt all values in *env* that look like Fernet tokens."""
    _require_cryptography()
    try:
        fernet = Fernet(key.encode())
    except Exception as exc:
        raise EncryptError(f"Invalid encryption key: {exc}") from exc

    decrypted: Dict[str, str] = {}
    for k, v in env.items():
        try:
            decrypted[k] = fernet.decrypt(v.encode()).decode()
        except (InvalidToken, Exception):
            decrypted[k] = v  # leave non-encrypted values as-is
    return decrypted
