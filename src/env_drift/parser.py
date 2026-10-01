"""Dotenv parsing for env-drift.

Pure stdlib. Supports the subset of the dotenv format that shows up in real
environment files: ``KEY=value``, an optional ``export`` prefix, ``#`` comments,
single/double quoted values, inline comments after unquoted values, and blank
lines. Values are never expanded or interpolated here -- expansion is a separate
concern in :mod:`env_drift.expand`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

__all__ = ["ParsedEnv", "parse_file", "parse_text"]

_EXPORT_PREFIXES = ("export ", "export\t")
_QUOTES = ("'", '"')


@dataclass(frozen=True)
class ParsedEnv:
    """Result of parsing a single environment file.

    ``values`` maps key -> value for active assignments. ``commented_keys``
    holds keys that appear only in commented-out assignments, which matters for
    the "pending removal" signal (a key disabled in one environment but still
    live in another).
    """

    values: dict[str, field] = field(default_factory=dict)  # type: ignore[assignment]
    commented_keys: tuple[str, ...] = ()

    def __len__(self) -> int:
        return len(self.values)


def _strip_inline_comment(raw: str) -> str:
    """Drop a trailing ``# comment`` from an *unquoted* value.

    ``B=plain#not-a-comment`` is a common mistake, so only a ``#`` preceded by
    whitespace or at the start of the value is treated as a comment.
    """
    for index, char in enumerate(raw):
        if char != "#":
            continue
        if index == 0 or raw[index - 1] in " \t":
            return raw[:index].rstrip()
    return raw


def _clean_value(raw: str) -> str:
    """Normalize a raw right-hand side: unquote, or strip a trailing comment."""
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in _QUOTES:
        return value[1:-1]
    return _strip_inline_comment(value)


def _split_assignment(line: str) -> tuple[str, str] | None:
    """Return ``(key, raw_value)`` for an assignment line, else ``None``."""
    if "=" not in line:
        return None
    key, _, raw_value = line.partition("=")
    key = key.strip()
    if not key:
        return None
    return key, raw_value


def parse_text(text: str) -> ParsedEnv:
    """Parse dotenv ``text`` into active values plus commented-out keys."""
    values: dict[str, str] = {}
    commented: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("#"):
            body = line.lstrip("#").strip()
            assignment = _split_assignment(body)
            if assignment is None:
                continue
            key = assignment[0]
            if key not in values and key not in commented:
                commented.append(key)
            continue

        for prefix in _EXPORT_PREFIXES:
            if line.startswith(prefix):
                line = line[len(prefix) :].lstrip()
                break

        assignment = _split_assignment(line)
        if assignment is None:
            # Not an assignment (e.g. a stray "echo" line); ignore it.
            continue

        key, raw_value = assignment
        values[key] = _clean_value(raw_value)
        # A key that is commented out and then re-enabled below is active, so
        # it must not linger in the pending-removal list.
        if key in commented:
            commented.remove(key)

    return ParsedEnv(values=values, commented_keys=tuple(commented))


def parse_file(path: str | Path) -> ParsedEnv:
    """Parse the dotenv file at ``path`` using UTF-8, replacing bad bytes."""
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    return parse_text(text)
