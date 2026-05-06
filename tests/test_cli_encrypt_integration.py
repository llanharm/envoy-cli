"""Integration test: encrypt CLI subcommand wired via build_encrypt_parser."""
import argparse

import pytest

pytest.importorskip("cryptography", reason="cryptography not installed")

from envoy.cli_encrypt import build_encrypt_parser
from envoy.encrypt import generate_key


@pytest.fixture()
def parser():
    p = argparse.ArgumentParser(prog="envoy")
    sub = p.add_subparsers(dest="command")
    build_encrypt_parser(sub)
    return p


@pytest.fixture()
def env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("API_KEY=super-secret\nDEBUG=true\n")
    return f


def test_full_encrypt_decrypt_cycle_via_parser(parser, env_file, tmp_path):
    key = generate_key()
    enc_out = tmp_path / "enc.env"
    dec_out = tmp_path / "dec.env"

    enc_args = parser.parse_args(["encrypt", str(env_file), "--key", key, "--output", str(enc_out)])
    assert enc_args.func(enc_args) == 0
    assert "super-secret" not in enc_out.read_text()

    dec_args = parser.parse_args(["decrypt", str(enc_out), "--key", key, "--output", str(dec_out)])
    assert dec_args.func(dec_args) == 0
    content = dec_out.read_text()
    assert "API_KEY=super-secret" in content
    assert "DEBUG=true" in content


def test_encrypt_only_specified_keys(parser, env_file, tmp_path):
    key = generate_key()
    out = tmp_path / "partial.env"
    args = parser.parse_args(
        ["encrypt", str(env_file), "--key", key, "--keys", "API_KEY", "--output", str(out)]
    )
    assert args.func(args) == 0
    content = out.read_text()
    assert "super-secret" not in content
    assert "DEBUG=true" in content


def test_decrypt_leaves_plain_values_intact(parser, env_file, tmp_path):
    key = generate_key()
    out = tmp_path / "dec.env"
    # Decrypt a file that was never encrypted — values should be preserved
    args = parser.parse_args(["decrypt", str(env_file), "--key", key, "--output", str(out)])
    assert args.func(args) == 0
    content = out.read_text()
    assert "API_KEY=super-secret" in content
    assert "DEBUG=true" in content
