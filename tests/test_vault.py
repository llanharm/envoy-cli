"""Unit tests for envoy.vault."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from envoy.vault import VaultClient, VaultConfigError


@pytest.fixture()
def mock_hvac(monkeypatch):
    """Patch hvac so tests don't need a real Vault server."""
    fake_hvac = MagicMock()
    fake_client = MagicMock()
    fake_client.is_authenticated.return_value = True
    fake_hvac.Client.return_value = fake_client
    monkeypatch.setattr("envoy.vault.hvac", fake_hvac)
    return fake_hvac, fake_client


def test_raises_when_hvac_missing(monkeypatch):
    monkeypatch.setattr("envoy.vault.hvac", None)
    with pytest.raises(VaultConfigError, match="hvac is not installed"):
        VaultClient(url="http://localhost:8200", token="root")


def test_raises_when_no_token(mock_hvac, monkeypatch):
    monkeypatch.delenv("VAULT_TOKEN", raising=False)
    with pytest.raises(VaultConfigError, match="token"):
        VaultClient(url="http://localhost:8200", token="")


def test_raises_when_auth_fails(mock_hvac, monkeypatch):
    _, fake_client = mock_hvac
    fake_client.is_authenticated.return_value = False
    with pytest.raises(VaultConfigError, match="authentication failed"):
        VaultClient(url="http://localhost:8200", token="bad")


def test_read_secrets_returns_dict(mock_hvac):
    _, fake_client = mock_hvac
    fake_client.secrets.kv.v2.read_secret_version.return_value = {
        "data": {"data": {"KEY": "value", "NUM": 42}}
    }
    vc = VaultClient(url="http://localhost:8200", token="root")
    result = vc.read_secrets("myapp/prod")
    assert result == {"KEY": "value", "NUM": "42"}


def test_write_secrets_calls_hvac(mock_hvac):
    _, fake_client = mock_hvac
    vc = VaultClient(url="http://localhost:8200", token="root")
    vc.write_secrets("myapp/prod", {"A": "1"})
    fake_client.secrets.kv.v2.create_or_update_secret.assert_called_once_with(
        path="myapp/prod", secret={"A": "1"}, mount_point="secret"
    )


def test_delete_secrets_calls_hvac(mock_hvac):
    _, fake_client = mock_hvac
    vc = VaultClient(url="http://localhost:8200", token="root")
    vc.delete_secrets("myapp/prod")
    fake_client.secrets.kv.v2.delete_metadata_and_all_versions.assert_called_once_with(
        path="myapp/prod", mount_point="secret"
    )
