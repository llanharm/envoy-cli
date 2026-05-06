"""Tests for envoy.encrypt."""
import pytest

pytest.importorskip("cryptography", reason="cryptography not installed")

from envoy.encrypt import (
    EncryptError,
    EncryptResult,
    decrypt_env,
    encrypt_env,
    generate_key,
)


@pytest.fixture()
def key() -> str:
    return generate_key()


def test_generate_key_returns_string(key):
    assert isinstance(key, str)
    assert len(key) > 0


def test_encrypt_all_keys(key):
    env = {"DB_HOST": "localhost", "DB_PASS": "secret"}
    result = encrypt_env(env, key)
    assert result.total_encrypted == 2
    assert result.skipped == []
    for v in result.encrypted.values():
        assert v != env.get("DB_HOST") and v != env.get("DB_PASS")


def test_encrypt_subset_of_keys(key):
    env = {"DB_HOST": "localhost", "DB_PASS": "secret", "PORT": "5432"}
    result = encrypt_env(env, key, keys_to_encrypt=["DB_PASS"])
    assert result.total_encrypted == 1
    assert "DB_PASS" in result.encrypted
    assert set(result.skipped) == {"DB_HOST", "PORT"}


def test_decrypt_reverses_encrypt(key):
    env = {"SECRET": "my-value", "OTHER": "plain"}
    encrypted = encrypt_env(env, key)
    # Build a full env with encrypted values for encrypted keys
    mixed = dict(encrypted.encrypted)
    mixed["OTHER"] = "plain"
    decrypted = decrypt_env(mixed, key)
    assert decrypted["SECRET"] == "my-value"
    assert decrypted["OTHER"] == "plain"


def test_decrypt_leaves_plain_values_unchanged(key):
    env = {"A": "not-encrypted"}
    result = decrypt_env(env, key)
    assert result["A"] == "not-encrypted"


def test_invalid_key_raises_on_encrypt():
    with pytest.raises(EncryptError, match="Invalid encryption key"):
        encrypt_env({"K": "v"}, "not-a-valid-key")


def test_invalid_key_raises_on_decrypt():
    with pytest.raises(EncryptError, match="Invalid encryption key"):
        decrypt_env({"K": "v"}, "bad-key")


def test_encrypt_result_key_used_is_stored(key):
    result = encrypt_env({"X": "1"}, key)
    assert result.key_used == key


def test_encrypt_empty_env(key):
    result = encrypt_env({}, key)
    assert result.total_encrypted == 0
    assert result.skipped == []
