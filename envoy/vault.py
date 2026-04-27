"""Vault sync support for envoy-cli.

Provides read/write operations between .env files and a HashiCorp Vault
KV secrets engine (v2).
"""
from __future__ import annotations

import os
from typing import Dict, Optional

try:
    import hvac
except ImportError:  # pragma: no cover
    hvac = None  # type: ignore


class VaultConfigError(Exception):
    """Raised when Vault connection/configuration is invalid."""


class VaultClient:
    """Thin wrapper around hvac for envoy vault operations."""

    def __init__(
        self,
        url: Optional[str] = None,
        token: Optional[str] = None,
        mount_point: str = "secret",
    ) -> None:
        if hvac is None:
            raise VaultConfigError(
                "hvac is not installed. Run: pip install hvac"
            )
        self.url = url or os.environ.get("VAULT_ADDR", "http://127.0.0.1:8200")
        self.token = token or os.environ.get("VAULT_TOKEN", "")
        self.mount_point = mount_point

        if not self.token:
            raise VaultConfigError(
                "Vault token not provided. Set VAULT_TOKEN or pass token=."
            )

        self._client = hvac.Client(url=self.url, token=self.token)
        if not self._client.is_authenticated():
            raise VaultConfigError("Vault authentication failed.")

    def read_secrets(self, path: str) -> Dict[str, str]:
        """Read key/value pairs from a Vault KV v2 path."""
        response = self._client.secrets.kv.v2.read_secret_version(
            path=path, mount_point=self.mount_point
        )
        data = response.get("data", {}).get("data", {})
        return {k: str(v) for k, v in data.items()}

    def write_secrets(self, path: str, secrets: Dict[str, str]) -> None:
        """Write key/value pairs to a Vault KV v2 path."""
        self._client.secrets.kv.v2.create_or_update_secret(
            path=path,
            secret=secrets,
            mount_point=self.mount_point,
        )

    def delete_secrets(self, path: str) -> None:
        """Delete all secrets at a Vault KV v2 path."""
        self._client.secrets.kv.v2.delete_metadata_and_all_versions(
            path=path, mount_point=self.mount_point
        )
