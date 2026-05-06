"""Tests for envoy.cli_encrypt."""
import argparse
import os

import pytest

pytest.importorskip("cryptography", reason="cryptography not installed")

from envoy.cli_encrypt import build_encrypt_parser, cmd_decrypt, cmd_encrypt
from envoy.encrypt import generate_key


@pytest.fixture()
def tmp_env(tmp_path):
    p = tmp_path / ".env"
    p.write_text("DB_PASS=secret\nPORT=5432\n")
    return p


@pytest.fixture()
def key():
    return generate_key()


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"key": None, "keys": None, "generate_key": False, "in_place": False, "output": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_build_encrypt_parser_adds_subcommands():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    build_encrypt_parser(sub)
    ns = parser.parse_args(["encrypt", "some.env"])
    assert ns.file == "some.env"


def test_generate_key_flag_prints_and_exits_zero(capsys, key):
    args = _make_args(file="x", generate_key=True)
    rc = cmd_encrypt(args)
    out = capsys.readouterr().out.strip()
    assert rc == 0
    assert len(out) > 10


def test_encrypt_prints_to_stdout(tmp_env, key, capsys):
    args = _make_args(file=str(tmp_env), key=key)
    rc = cmd_encrypt(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "DB_PASS=" in out


def test_encrypt_in_place_overwrites_file(tmp_env, key):
    args = _make_args(file=str(tmp_env), key=key, in_place=True)
    rc = cmd_encrypt(args)
    assert rc == 0
    content = tmp_env.read_text()
    assert "secret" not in content


def test_encrypt_writes_to_output_file(tmp_env, key, tmp_path):
    out_file = tmp_path / "out.env"
    args = _make_args(file=str(tmp_env), key=key, output=str(out_file))
    rc = cmd_encrypt(args)
    assert rc == 0
    assert out_file.exists()
    assert "secret" not in out_file.read_text()


def test_decrypt_round_trips(tmp_env, key, tmp_path):
    enc_file = tmp_path / "enc.env"
    enc_args = _make_args(file=str(tmp_env), key=key, output=str(enc_file))
    cmd_encrypt(enc_args)

    dec_file = tmp_path / "dec.env"
    dec_args = _make_args(file=str(enc_file), key=key, output=str(dec_file))
    rc = cmd_decrypt(dec_args)
    assert rc == 0
    content = dec_file.read_text()
    assert "DB_PASS=secret" in content


def test_missing_key_exits_one(tmp_env, monkeypatch):
    monkeypatch.delenv("ENVOY_ENCRYPT_KEY", raising=False)
    args = _make_args(file=str(tmp_env), key=None)
    with pytest.raises(SystemExit) as exc_info:
        cmd_encrypt(args)
    assert exc_info.value.code == 1


def test_invalid_key_returns_one(tmp_env, capsys):
    args = _make_args(file=str(tmp_env), key="not-valid")
    rc = cmd_encrypt(args)
    assert rc == 1
    assert "error" in capsys.readouterr().err
