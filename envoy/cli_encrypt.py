"""CLI sub-commands: encrypt and decrypt .env file values."""
from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional

from envoy.encrypt import EncryptError, decrypt_env, encrypt_env, generate_key
from envoy.parser import parse_env_file, write_env_file


def build_encrypt_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("encrypt", help="Encrypt values in a .env file")
    p.add_argument("file", help="Path to the .env file")
    p.add_argument("--key", help="Fernet key (default: $ENVOY_ENCRYPT_KEY)")
    p.add_argument(
        "--keys",
        nargs="+",
        metavar="KEY",
        help="Specific env keys to encrypt (default: all)",
    )
    p.add_argument("--generate-key", action="store_true", help="Print a new key and exit")
    p.add_argument("--in-place", action="store_true", help="Overwrite the source file")
    p.add_argument("--output", help="Write encrypted env to this file")
    p.set_defaults(func=cmd_encrypt)

    d = subparsers.add_parser("decrypt", help="Decrypt values in a .env file")
    d.add_argument("file", help="Path to the .env file")
    d.add_argument("--key", help="Fernet key (default: $ENVOY_ENCRYPT_KEY)")
    d.add_argument("--in-place", action="store_true", help="Overwrite the source file")
    d.add_argument("--output", help="Write decrypted env to this file")
    d.set_defaults(func=cmd_decrypt)


def _resolve_key(args: argparse.Namespace) -> str:
    key = getattr(args, "key", None) or os.environ.get("ENVOY_ENCRYPT_KEY", "")
    if not key:
        print("error: no encryption key provided (use --key or $ENVOY_ENCRYPT_KEY)", file=sys.stderr)
        sys.exit(1)
    return key


def cmd_encrypt(args: argparse.Namespace) -> int:
    if getattr(args, "generate_key", False):
        print(generate_key())
        return 0

    key = _resolve_key(args)
    try:
        env = parse_env_file(args.file)
        result = encrypt_env(env, key, keys_to_encrypt=getattr(args, "keys", None))
    except EncryptError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    dest = args.output if args.output else (args.file if args.in_place else None)
    if dest:
        write_env_file(dest, result.encrypted | {k: env[k] for k in result.skipped})
        print(f"Encrypted {result.total_encrypted} key(s) → {dest}")
    else:
        for k, v in result.encrypted.items():
            print(f"{k}={v}")
    return 0


def cmd_decrypt(args: argparse.Namespace) -> int:
    key = _resolve_key(args)
    try:
        env = parse_env_file(args.file)
        decrypted = decrypt_env(env, key)
    except EncryptError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    dest = args.output if args.output else (args.file if args.in_place else None)
    if dest:
        write_env_file(dest, decrypted)
        print(f"Decrypted {len(decrypted)} key(s) → {dest}")
    else:
        for k, v in decrypted.items():
            print(f"{k}={v}")
    return 0
