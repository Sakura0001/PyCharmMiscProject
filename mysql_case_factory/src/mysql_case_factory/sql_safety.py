"""Preflight guards for SQL programs executed by mysql-based runners.

The runner is an output-comparison primitive, not a host-command sandbox. It
accepts ordinary MySQL SQL but rejects client commands, server-file access,
administrative control, and topology mutation before spawning a process.
Those tests belong in a separately isolated external harness.
"""

from __future__ import annotations

import re


class UnsafeSqlError(ValueError):
    """Raised when a SQL file requests capabilities outside the basic runner."""


SqlSafetyError = UnsafeSqlError


def _mask_non_code(content: str) -> str:
    """Mask MySQL strings, comments, and quoted identifiers, retaining lines."""

    masked = ["\n" if character == "\n" else " " for character in content]
    index = 0
    length = len(content)
    while index < length:
        dash_comment = (
            content.startswith("--", index)
            and index + 2 < length
            and content[index + 2].isspace()
        )
        if dash_comment or content.startswith("#", index):
            end = content.find("\n", index + (2 if dash_comment else 1))
            index = length if end < 0 else end
            continue
        if content.startswith("/*!", index) or content.startswith("/*M!", index):
            end = content.find("*/", index + 3)
            body_end = length if end < 0 else end
            for cursor in range(index + 3, body_end):
                masked[cursor] = content[cursor]
            index = length if end < 0 else end + 2
            continue
        if content.startswith("/*", index):
            end = content.find("*/", index + 2)
            index = length if end < 0 else end + 2
            continue
        delimiter = content[index]
        if delimiter in {"'", '"', "`"}:
            cursor = index + 1
            while cursor < length:
                if delimiter != "`" and content[cursor] == "\\" and cursor + 1 < length:
                    cursor += 2
                    continue
                if content[cursor] == delimiter:
                    if cursor + 1 < length and content[cursor + 1] == delimiter:
                        cursor += 2
                        continue
                    cursor += 1
                    break
                cursor += 1
            index = cursor
            continue
        masked[index] = content[index]
        index += 1
    return "".join(masked)


def validate_sql_for_basic_runner(content: str) -> None:
    """Reject capabilities unsafe or nondeterministic in the basic MySQL mode."""

    if not isinstance(content, str):
        raise TypeError("SQL content must be a string")
    if "\x00" in content:
        raise SqlSafetyError("SQL must not contain NUL bytes")

    code = _mask_non_code(content)
    meta = re.search(
        r"(?im)(?:^|;)\s*(?:SOURCE|SYSTEM|TEE|NOTEE|PAGER|NOPAGER|DELIMITER)\b",
        code,
    )
    if meta is not None:
        line = content.count("\n", 0, meta.start()) + 1
        raise SqlSafetyError(f"mysql client commands are forbidden (line {line})")
    backslash = re.search(r"\\", code)
    if backslash is not None:
        line = content.count("\n", 0, backslash.start()) + 1
        raise SqlSafetyError(f"mysql client backslash commands are forbidden (line {line})")

    forbidden = (
        (r"\bINTO\s+(?:OUTFILE|DUMPFILE)\b", "server outfile access"),
        (r"\bLOAD_FILE\s*\(", "server file reads"),
        (r"\bLOAD\s+DATA(?:\s+LOCAL)?\s+INFILE\b", "LOAD DATA file access"),
        (
            r"\b(?:INSTALL|UNINSTALL)\s+(?:PLUGIN|COMPONENT)\b",
            "plugin/component administration",
        ),
        (r"(?:^|;)\s*(?:SHUTDOWN|RESTART)\b", "server lifecycle control"),
        (r"\bSET\s+PERSIST(?:_ONLY)?\b", "persistent server variables"),
        (
            r"(?:^|;)\s*(?:CHANGE\s+REPLICATION\s+SOURCE|CHANGE\s+MASTER|"
            r"START\s+REPLICA|STOP\s+REPLICA|RESET\s+REPLICA|"
            r"START\s+SLAVE|STOP\s+SLAVE|RESET\s+SLAVE)\b",
            "replication control",
        ),
        (r"(?:^|;)\s*CLONE\s+INSTANCE\b", "instance cloning"),
    )
    for pattern, capability in forbidden:
        match = re.search(pattern, code, flags=re.IGNORECASE | re.MULTILINE)
        if match is not None:
            line = content.count("\n", 0, match.start()) + 1
            raise SqlSafetyError(
                f"{capability} is outside the basic runner; "
                f"use an isolated external harness (line {line})"
            )


__all__ = ["UnsafeSqlError", "validate_sql_for_basic_runner"]
