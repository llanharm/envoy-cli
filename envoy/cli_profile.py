"""CLI commands for profile management."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envoy.profile import Profile, ProfileError, ProfileStore

_DEFAULT_STORE = Path(".envoy_profiles.json")


def build_profile_parser(parent: argparse._SubParsersAction) -> argparse.ArgumentParser:
    p = parent.add_parser("profile", help="Manage named env-file profiles")
    sub = p.add_subparsers(dest="profile_cmd", required=True)

    add_p = sub.add_parser("add", help="Register a new profile")
    add_p.add_argument("name", help="Profile name")
    add_p.add_argument("env_file", help="Path to .env file")
    add_p.add_argument("--description", default="", help="Short description")
    add_p.add_argument("--tags", nargs="*", default=[], metavar="TAG")
    add_p.add_argument("--store", default=str(_DEFAULT_STORE), metavar="PATH")

    rm_p = sub.add_parser("remove", help="Remove a profile")
    rm_p.add_argument("name", help="Profile name to remove")
    rm_p.add_argument("--store", default=str(_DEFAULT_STORE), metavar="PATH")

    ls_p = sub.add_parser("list", help="List profiles")
    ls_p.add_argument("--tag", default=None, help="Filter by tag")
    ls_p.add_argument("--store", default=str(_DEFAULT_STORE), metavar="PATH")

    return p


def cmd_profile(args: argparse.Namespace) -> int:
    store = ProfileStore(Path(args.store))

    if args.profile_cmd == "add":
        if not Path(args.env_file).exists():
            print(f"error: env file not found: {args.env_file}", file=sys.stderr)
            return 1
        try:
            store.add(Profile(
                name=args.name,
                env_file=args.env_file,
                description=args.description,
                tags=args.tags,
            ))
            print(f"Profile '{args.name}' added.")
        except ProfileError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    elif args.profile_cmd == "remove":
        try:
            store.remove(args.name)
            print(f"Profile '{args.name}' removed.")
        except ProfileError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    elif args.profile_cmd == "list":
        profiles = store.list_profiles(tag=args.tag)
        if not profiles:
            print("No profiles found.")
        for p in profiles:
            tags = ", ".join(p.tags) if p.tags else "-"
            desc = p.description or "-"
            print(f"  {p.name:<20} {p.env_file:<35} tags=[{tags}]  {desc}")

    return 0
