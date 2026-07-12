"""Preflight guards for SQL programs executed by psql-based runners.

The runner is an output-comparison primitive, not a host-command sandbox.  It
therefore accepts PostgreSQL SQL but refuses psql meta commands and COPY
PROGRAM before spawning a process.  Tests that intentionally exercise host or
server program execution belong in a separately isolated external harness.
"""

from __future__ import annotations

import re


class UnsafeSqlError(ValueError):
    """Raised when a SQL file requests capabilities outside the basic runner."""


# Any unquoted backslash is outside the basic runner's SQL-only contract.  This
# catches the full psql meta-command alphabet (including punctuation commands
# such as ``\.``), rather than trying to maintain an incomplete allowlist.
_PSQL_META = re.compile(r"\\")
_TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|;")
_STRUCTURAL_TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|[();]")


def _identifier_start(character: str) -> bool:
    return character == "_" or character.isalpha() or ord(character) >= 128


def _identifier_continue(character: str) -> bool:
    return _identifier_start(character) or character.isdigit()


def _dollar_tag_at(content: str, index: int) -> str | None:
    """Return a PostgreSQL dollar-quote delimiter beginning at ``index``."""

    if content[index] != "$":
        return None
    if index and (
        _identifier_continue(content[index - 1]) or content[index - 1] == "$"
    ):
        return None
    end = content.find("$", index + 1)
    if end < 0:
        return None
    tag = content[index + 1 : end]
    if tag and (
        not _identifier_start(tag[0])
        or any(not _identifier_continue(character) for character in tag[1:])
    ):
        return None
    return content[index : end + 1]


def _escape_string_prefix(content: str, quote_index: int) -> bool:
    prefix_index = quote_index - 1
    return (
        prefix_index >= 0
        and content[prefix_index] in "Ee"
        and (
            prefix_index == 0
            or not _identifier_continue(content[prefix_index - 1])
        )
    )


def _mask_non_code(
    content: str,
    *,
    standard_conforming_strings: bool,
) -> str:
    """Replace SQL strings/comments/quoted identifiers with spaces.

    Newlines are retained so diagnostics can still report the relevant line.
    PostgreSQL nested block comments and dollar-quoted bodies are handled.
    """

    masked = ["\n" if character == "\n" else " " for character in content]
    index = 0
    length = len(content)
    while index < length:
        if content.startswith("--", index):
            end = content.find("\n", index + 2)
            index = length if end < 0 else end
            continue
        if content.startswith("/*", index):
            depth = 1
            cursor = index + 2
            while cursor < length and depth:
                if content.startswith("/*", cursor):
                    depth += 1
                    cursor += 2
                elif content.startswith("*/", cursor):
                    depth -= 1
                    cursor += 2
                else:
                    cursor += 1
            index = cursor
            continue
        character = content[index]
        if character == "'":
            backslash_escapes = (
                not standard_conforming_strings
                or _escape_string_prefix(content, index)
            )
            cursor = index + 1
            while cursor < length:
                if (
                    backslash_escapes
                    and content[cursor] == "\\"
                    and cursor + 1 < length
                ):
                    cursor += 2
                    continue
                if content[cursor] == "'":
                    if cursor + 1 < length and content[cursor + 1] == "'":
                        cursor += 2
                        continue
                    cursor += 1
                    break
                cursor += 1
            index = cursor
            continue
        if character == '"':
            cursor = index + 1
            while cursor < length:
                if content[cursor] == '"':
                    if cursor + 1 < length and content[cursor + 1] == '"':
                        cursor += 2
                        continue
                    cursor += 1
                    break
                cursor += 1
            index = cursor
            continue
        if character == "$":
            tag = _dollar_tag_at(content, index)
            if tag is not None:
                opening_end = index + len(tag)
                end = content.find(tag, opening_end)
                index = length if end < 0 else end + len(tag)
                continue
        masked[index] = character
        index += 1
    return "".join(masked)


def validate_sql_for_basic_runner(content: str) -> None:
    """Reject local psql meta commands and server-side COPY PROGRAM."""

    # psql can operate with standard_conforming_strings either on or off, and
    # a SQL file may change the setting during execution.  Reject a dangerous
    # construct if it is visible under either lexical interpretation instead
    # of letting an ambiguous backslash-before-quote hide a later meta command.
    code_variants = (
        _mask_non_code(content, standard_conforming_strings=True),
        _mask_non_code(content, standard_conforming_strings=False),
    )
    meta_matches = [
        match
        for code in code_variants
        if (match := _PSQL_META.search(code)) is not None
    ]
    if meta_matches:
        meta = min(meta_matches, key=lambda match: match.start())
        line = content.count("\n", 0, meta.start()) + 1
        raise UnsafeSqlError(
            f"psql meta commands are forbidden by the basic runner (line {line})"
        )

    for code in code_variants:
        statement_tokens: list[str] = []
        for match in _TOKEN.finditer(code):
            token = match.group(0).upper()
            if token == ";":
                if (
                    "COPY" in statement_tokens
                    and "FROM" in statement_tokens
                    and "STDIN" in statement_tokens
                ):
                    raise UnsafeSqlError(
                        "COPY FROM STDIN is outside the SQL-only basic runner because psql data mode can contain meta commands"
                    )
                if "COPY" in statement_tokens and "PROGRAM" in statement_tokens:
                    raise UnsafeSqlError(
                        "COPY PROGRAM is forbidden by the basic runner; use an isolated external harness"
                    )
                statement_tokens = []
            else:
                statement_tokens.append(token)
        if "COPY" in statement_tokens and "PROGRAM" in statement_tokens:
            raise UnsafeSqlError(
                "COPY PROGRAM is forbidden by the basic runner; use an isolated external harness"
            )
        if (
            "COPY" in statement_tokens
            and "FROM" in statement_tokens
            and "STDIN" in statement_tokens
        ):
            raise UnsafeSqlError(
                "COPY FROM STDIN is outside the SQL-only basic runner because psql data mode can contain meta commands"
            )


def _find_statement_end(
    content: str,
    start: int,
    *,
    standard_conforming_strings: bool,
) -> int | None:
    """Find the next code-level semicolon without scanning COPY payload bytes.

    The external COPY validator alternates between SQL mode and psql COPY data
    mode.  Masking the whole file first would be incorrect because arbitrary
    payload bytes can look like unterminated SQL strings or comments.
    """

    index = start
    length = len(content)
    while index < length:
        if content.startswith("--", index):
            end = content.find("\n", index + 2)
            index = length if end < 0 else end + 1
            continue
        if content.startswith("/*", index):
            depth = 1
            cursor = index + 2
            while cursor < length and depth:
                if content.startswith("/*", cursor):
                    depth += 1
                    cursor += 2
                elif content.startswith("*/", cursor):
                    depth -= 1
                    cursor += 2
                else:
                    cursor += 1
            if depth:
                raise UnsafeSqlError(
                    "external-copy-ingest SQL has an unterminated block comment"
                )
            index = cursor
            continue
        character = content[index]
        if character == "'":
            backslash_escapes = (
                not standard_conforming_strings
                or _escape_string_prefix(content, index)
            )
            cursor = index + 1
            while cursor < length:
                if (
                    backslash_escapes
                    and content[cursor] == "\\"
                    and cursor + 1 < length
                ):
                    cursor += 2
                    continue
                if content[cursor] == "'":
                    if cursor + 1 < length and content[cursor + 1] == "'":
                        cursor += 2
                        continue
                    cursor += 1
                    break
                cursor += 1
            else:
                raise UnsafeSqlError(
                    "external-copy-ingest SQL has an unterminated string literal"
                )
            index = cursor
            continue
        if character == '"':
            cursor = index + 1
            while cursor < length:
                if content[cursor] == '"':
                    if cursor + 1 < length and content[cursor + 1] == '"':
                        cursor += 2
                        continue
                    cursor += 1
                    break
                cursor += 1
            else:
                raise UnsafeSqlError(
                    "external-copy-ingest SQL has an unterminated quoted identifier"
                )
            index = cursor
            continue
        if character == "$":
            tag = _dollar_tag_at(content, index)
            if tag is not None:
                opening_end = index + len(tag)
                end = content.find(tag, opening_end)
                if end < 0:
                    raise UnsafeSqlError(
                        "external-copy-ingest SQL has an unterminated dollar-quoted body"
                    )
                index = end + len(tag)
                continue
        if character == ";":
            return index
        index += 1
    return None


def _statement_tokens(statement: str) -> tuple[str, ...]:
    code_variants = (
        _mask_non_code(statement, standard_conforming_strings=True),
        _mask_non_code(statement, standard_conforming_strings=False),
    )
    token_variants = tuple(
        tuple(match.group(0).upper() for match in _STRUCTURAL_TOKEN.finditer(code))
        for code in code_variants
    )
    if token_variants[0] != token_variants[1]:
        raise UnsafeSqlError(
            "external-copy-ingest SQL has ambiguous string escaping"
        )
    for code in code_variants:
        if _PSQL_META.search(code) is not None:
            raise UnsafeSqlError(
                "external-copy-ingest permits no psql meta command outside a COPY terminator"
            )
    return token_variants[0]


def _copy_direction(tokens: tuple[str, ...]) -> tuple[str, str | None] | None:
    """Return the top-level COPY direction and endpoint token, if present."""

    if not tokens or tokens[0] != "COPY":
        return None
    depth = 0
    for index, token in enumerate(tokens[1:], 1):
        if token == "(":
            depth += 1
        elif token == ")":
            if depth == 0:
                raise UnsafeSqlError(
                    "external-copy-ingest COPY statement has unbalanced parentheses"
                )
            depth -= 1
        elif depth == 0 and token in {"FROM", "TO"}:
            endpoint = tokens[index + 1] if index + 1 < len(tokens) else None
            return token, endpoint
    return None


def _copy_payload_end(content: str, start: int) -> int:
    """Validate one non-empty inline data block and return the next SQL byte."""

    cursor = start
    payload_lines = 0
    while cursor < len(content):
        newline = content.find("\n", cursor)
        line_end = len(content) if newline < 0 else newline
        line = content[cursor:line_end]
        if line.endswith("\r"):
            line = line[:-1]
        if line == r"\.":
            if payload_lines == 0:
                raise UnsafeSqlError(
                    "external-copy-ingest COPY FROM STDIN payload must not be empty"
                )
            return len(content) if newline < 0 else newline + 1
        payload_lines += 1
        if newline < 0:
            break
        cursor = newline + 1
    raise UnsafeSqlError(
        "external-copy-ingest COPY FROM STDIN payload is missing a standalone \\. terminator"
    )


def validate_sql_for_external_copy_ingest(content: str) -> None:
    """Require a self-contained, manifest-hash-bound psql COPY program.

    Every direct COPY statement in this harness must use ``FROM STDIN``.  Its
    payload must follow in the same SQL file and end with a standalone ``\.``
    line.  The harness may therefore invoke ``psql -f <manifest SQL>`` without
    an external payload file or an out-of-band stdin stream.  This is a
    conservative structural check, not a complete PostgreSQL parser.
    """

    if "\x00" in content:
        raise UnsafeSqlError("external-copy-ingest SQL must not contain NUL bytes")

    cursor = 0
    copy_blocks = 0
    while cursor < len(content):
        ends = (
            _find_statement_end(
                content,
                cursor,
                standard_conforming_strings=True,
            ),
            _find_statement_end(
                content,
                cursor,
                standard_conforming_strings=False,
            ),
        )
        if ends[0] != ends[1]:
            raise UnsafeSqlError(
                "external-copy-ingest SQL has ambiguous statement boundaries"
            )
        end = ends[0]
        statement_end = len(content) if end is None else end + 1
        tokens = _statement_tokens(content[cursor:statement_end])
        direction = _copy_direction(tokens)
        if direction is None:
            if tokens and tokens[0] == "COPY":
                raise UnsafeSqlError(
                    "external-copy-ingest COPY statement has no top-level FROM STDIN direction"
                )
            cursor = statement_end
            continue
        if direction != ("FROM", "STDIN"):
            raise UnsafeSqlError(
                "external-copy-ingest permits only COPY ... FROM STDIN; external "
                "payload files, PROGRAM, COPY TO, and out-of-band input are forbidden"
            )
        if end is None:
            raise UnsafeSqlError(
                "external-copy-ingest COPY FROM STDIN statement must end with a semicolon"
            )

        newline = content.find("\n", end + 1)
        if newline < 0 or content[end + 1 : newline].strip(" \t\r"):
            raise UnsafeSqlError(
                "external-copy-ingest COPY FROM STDIN payload must start on the next line"
            )
        copy_blocks += 1
        cursor = _copy_payload_end(content, newline + 1)

    if copy_blocks == 0:
        raise UnsafeSqlError(
            "external-copy-ingest SQL must contain at least one inline "
            "COPY ... FROM STDIN data block"
        )


__all__ = [
    "UnsafeSqlError",
    "validate_sql_for_basic_runner",
    "validate_sql_for_external_copy_ingest",
]
