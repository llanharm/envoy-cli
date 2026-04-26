"""Parser for .env files — handles reading, writing, and validating env file contents."""

import re
from typing import Dict, List, Tuple, Optional


ENV_LINE_PATTERN = re.compile(
    r'^(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>.*)$'
)
COMMENT_PATTERN = re.compile(r'^\s*#.*$')


class EnvParseError(Exception):
    """Raised when a .env file cannot be parsed."""
    pass


def parse_env_file(filepath: str) -> Dict[str, str]:
    """Parse a .env file and return a dict of key-value pairs.

    Args:
        filepath: Path to the .env file.

    Returns:
        Dictionary of environment variable names to their values.

    Raises:
        EnvParseError: If the file contains invalid syntax.
        FileNotFoundError: If the file does not exist.
    """
    env_vars: Dict[str, str] = {}

    with open(filepath, 'r', encoding='utf-8') as f:
        for lineno, raw_line in enumerate(f, start=1):
            line = raw_line.rstrip('\n')

            if not line.strip() or COMMENT_PATTERN.match(line):
                continue

            match = ENV_LINE_PATTERN.match(line)
            if not match:
                raise EnvParseError(
                    f"Invalid syntax at {filepath}:{lineno}: {line!r}"
                )

            key = match.group('key')
            value = _strip_quotes(match.group('value').strip())
            env_vars[key] = value

    return env_vars


def write_env_file(filepath: str, env_vars: Dict[str, str]) -> None:
    """Write a dictionary of env vars to a .env file.

    Args:
        filepath: Destination path.
        env_vars: Dictionary of key-value pairs to write.
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        for key, value in env_vars.items():
            value_out = _quote_if_needed(value)
            f.write(f"{key}={value_out}\n")


def _strip_quotes(value: str) -> str:
    """Remove surrounding single or double quotes from a value."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1]
    return value


def _quote_if_needed(value: str) -> str:
    """Wrap value in double quotes if it contains spaces or special chars."""
    if any(c in value for c in (' ', '#', '"', "'", '\\')):
        escaped = value.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'
    return value
