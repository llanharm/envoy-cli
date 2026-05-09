"""CLI sub-commands for the *tag* feature."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envoy.parser import parse_env_file
from envoy.tag import TagError, load_tags, save_tags, tag_env


def build_tag_parser(sub: "argparse._SubParsersAction") -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("tag", help="Tag and filter .env keys")
    sp = p.add_subparsers(dest="tag_cmd", required=True)

    # --- list ---
    ls = sp.add_parser("list", help="Show tags for keys in an env file")
    ls.add_argument("env_file", help="Path to .env file")
    ls.add_argument("--tag-file", default=".env-tags.json", help="Tag map JSON file")
    ls.add_argument("--filter", dest="filter_tag", default=None, help="Only show keys with this tag")
    ls.add_argument("--json", dest="as_json", action="store_true")

    # --- set ---
    st = sp.add_parser("set", help="Assign tags to a key")
    st.add_argument("key", help="Env key to tag")
    st.add_argument("tags", nargs="+", help="One or more tag labels")
    st.add_argument("--tag-file", default=".env-tags.json")

    # --- remove ---
    rm = sp.add_parser("remove", help="Remove a key from the tag map")
    rm.add_argument("key", help="Env key to untag")
    rm.add_argument("--tag-file", default=".env-tags.json")

    return p


def cmd_tag(args: argparse.Namespace) -> int:
    tag_file = Path(args.tag_file)

    if args.tag_cmd == "set":
        try:
            existing = load_tags(tag_file) if tag_file.exists() else {}
        except TagError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        existing[args.key] = args.tags
        save_tags(tag_file, existing)
        print(f"Tagged '{args.key}' with: {', '.join(args.tags)}")
        return 0

    if args.tag_cmd == "remove":
        try:
            existing = load_tags(tag_file)
        except TagError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        if args.key not in existing:
            print(f"Key '{args.key}' has no tags.", file=sys.stderr)
            return 1
        del existing[args.key]
        save_tags(tag_file, existing)
        print(f"Removed tags for '{args.key}'")
        return 0

    # list
    env_path = Path(args.env_file)
    if not env_path.exists():
        print(f"error: file not found: {env_path}", file=sys.stderr)
        return 1
    try:
        env = parse_env_file(env_path)
        tags = load_tags(tag_file) if tag_file.exists() else {}
    except (TagError, Exception) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    result = tag_env(env, tags, filter_tag=getattr(args, "filter_tag", None))

    if args.as_json:
        print(json.dumps(result.to_dict(), indent=2))
        return 0

    if result.tagged:
        print("Tagged keys:")
        for key, key_tags in sorted(result.tagged.items()):
            print(f"  {key}: {', '.join(key_tags)}")
    else:
        print("No tagged keys found.")

    if result.untagged:
        print(f"\nUntagged keys ({len(result.untagged)}): {', '.join(result.untagged)}")

    return 0
