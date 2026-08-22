"""Shared cleanup-bookend builders for factor-regress SQL scripts.

These helpers encode the ``alter_sequence`` good idiom as a safe-by-construction
builder. The two determinism invariants that fix the 53.93% two-round failure
mass are enforced structurally:

  * every DROP carries ``IF EXISTS`` (idempotent across run-01/run-02);
  * ``DROP OWNED BY`` is unreachable in pre-cleanup (the role may not exist on
    a fresh database, which crashes the run before the target statement).

A bare ``DROP`` or a pre-cleanup ``DROP OWNED BY`` cannot be constructed through
the public API. Bracket markers surround each region so
``regression_style.audit_cleanup_bookends`` can locate them without parsing
ambiguous SQL.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final, Sequence

__all__ = [
    "CLEANUP_BEGIN",
    "CLEANUP_END",
    "PRE_CLEANUP_BEGIN",
    "PRE_CLEANUP_END",
    "CleanupBookend",
    "DropSpec",
    "build_cleanup",
    "build_pre_cleanup",
    "guarded_drop_owned_by",
    "guarded_drop_role",
    "idempotent_drop",
]

# Bracket markers consumed by regression_style.audit_cleanup_bookends to locate
# the pre-cleanup and cleanup regions. They are SQL line comments, so psql never
# echoes them (the runner uses -q -t -A) and _split_sql_statements masks them
# out, leaving the DROP TABLE anchor as the first/last executable statement.
PRE_CLEANUP_BEGIN: Final[str] = "-- cleanup-bookend: pre-cleanup-begin"
PRE_CLEANUP_END: Final[str] = "-- cleanup-bookend: pre-cleanup-end"
CLEANUP_BEGIN: Final[str] = "-- cleanup-bookend: cleanup-begin"
CLEANUP_END: Final[str] = "-- cleanup-bookend: cleanup-end"

# Object kinds whose drop syntax is ``DROP <KIND> IF EXISTS <name>[<args>] [CASCADE]``.
# ROLE is excluded: DROP ROLE does not accept CASCADE -> use guarded_drop_role.
# Standard-syntax kinds with a single name and no ON/USING/(s AS t) clause are
# members: CONVERSION, ACCESS METHOD, EVENT TRIGGER, and the four TEXT SEARCH
# object kinds (CONFIGURATION/DICTIONARY/PARSER/TEMPLATE) all share this form.
# Genuinely complex kinds needing USING/ON/(s AS t) clauses (CAST, TRIGGER,
# POLICY, RULE, TRANSFORM, OPERATOR CLASS/FAMILY, CONSTRAINT) remain absent;
# renders pass such drops through a dedicated builder when needed in later phases.
_DROP_KINDS: Final[frozenset[str]] = frozenset(
    {
        "ACCESS METHOD",
        "AGGREGATE",
        "COLLATION",
        "CONVERSION",
        "DOMAIN",
        "EVENT TRIGGER",
        "EXTENSION",
        "FUNCTION",
        "INDEX",
        "MATERIALIZED VIEW",
        "OPERATOR",
        "PROCEDURE",
        "SCHEMA",
        "SEQUENCE",
        "TABLE",
        "TEXT SEARCH CONFIGURATION",
        "TEXT SEARCH DICTIONARY",
        "TEXT SEARCH PARSER",
        "TEXT SEARCH TEMPLATE",
        "TYPE",
        "VIEW",
    }
)

# A plain (unquoted) identifier segment, mirroring regression_style's
# _normalize_identifier per-segment pattern without lowercasing on emit.
_PLAIN_SEGMENT_RE: Final[re.Pattern[str]] = re.compile(r"[A-Za-z_][A-Za-z0-9_$]*")
# A properly-quoted identifier segment: "..." with "" escaping a literal ".
_QUOTED_SEGMENT_RE: Final[re.Pattern[str]] = re.compile(r'"(?:[^"]|"")*"')
# args is either empty or a parenthesized argument-type list. We reject any
# statement-terminator or quote that would allow injection.
_ARGS_RE: Final[re.Pattern[str]] = re.compile(r"\([A-Za-z0-9_,$. ]*\)")


_RESIDUAL_SELECT: Final[str] = "SELECT 1 AS residual_check_no_objects;"


@dataclass(frozen=True)
class DropSpec:
    """A validated, idempotent DROP specification.

    ``kind`` must be a member of the supported allowlist (not ROLE, not
    DATABASE); ``name`` a plain, quoted, or dot-qualified identifier; ``args``
    an optional ``(type, ...)`` list. A bare DROP is impossible to express.
    """

    kind: str
    name: str
    args: str = ""
    cascade: bool = True


@dataclass(frozen=True)
class CleanupBookend:
    """An immutable, bracket-wrapped sequence of cleanup statements."""

    statements: tuple[str, ...]
    drop_kinds: tuple[str, ...] = ()


def _split_qualified_segments(name: str) -> tuple[str, ...]:
    """Split a (possibly dot-qualified) identifier on top-level '.' only.

    Dots inside a quoted segment are preserved as part of that segment.
    """
    segments: list[str] = []
    current: list[str] = []
    in_quote = False
    for ch in name:
        if ch == '"':
            in_quote = not in_quote
            current.append(ch)
        elif ch == "." and not in_quote:
            segments.append("".join(current))
            current = []
        else:
            current.append(ch)
    segments.append("".join(current))
    return tuple(segments)


def _is_valid_identifier(name: str) -> bool:
    """True if ``name`` is a plain, quoted, or dot-qualified-mix identifier."""
    segments = _split_qualified_segments(name)
    if not segments or any(seg == "" for seg in segments):
        return False
    for seg in segments:
        if seg.startswith('"'):
            if _QUOTED_SEGMENT_RE.fullmatch(seg) is None:
                return False
        elif _PLAIN_SEGMENT_RE.fullmatch(seg) is None:
            return False
    return True


def _validate_identifier(name: str, field: str) -> str:
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"{field} must be a non-empty identifier")
    if not _is_valid_identifier(name):
        raise ValueError(f"{field} is not a valid plain or quoted identifier: {name!r}")
    return name


def _validate_identifier_list(names: Sequence[str], field: str) -> tuple[str, ...]:
    if not names:
        raise ValueError(f"{field} must be a non-empty sequence")
    return tuple(_validate_identifier(n, field) for n in names)


def _validate_args(args: str) -> str:
    if not isinstance(args, str):
        raise ValueError("DropSpec.args must be a string")
    if args == "":
        return ""
    if _ARGS_RE.fullmatch(args) is None:
        raise ValueError(f"DropSpec.args must be empty or a parenthesized type list: {args!r}")
    return args


def _require_kind(kind: str) -> str:
    if not isinstance(kind, str) or kind.upper() != kind:
        raise ValueError(f"DropSpec.kind must be an uppercase allowlist member: {kind!r}")
    if kind not in _DROP_KINDS:
        raise ValueError(
            f"DropSpec.kind {kind!r} is not supported; use guarded_drop_role for roles"
        )
    return kind


def idempotent_drop(spec: DropSpec) -> str:
    """Return ``DROP <kind> IF EXISTS <name><args> [CASCADE];`` always."""
    kind = _require_kind(spec.kind)
    name = _validate_identifier(spec.name, "DropSpec.name")
    args = _validate_args(spec.args)
    suffix = " CASCADE" if spec.cascade else ""
    return f"DROP {kind} IF EXISTS {name}{args}{suffix};"


def guarded_drop_owned_by(role: str) -> str:
    """Return ``DROP OWNED BY <role> CASCADE;`` (post-target cleanup only)."""
    r = _validate_identifier(role, "role")
    return f"DROP OWNED BY {r} CASCADE;"


def guarded_drop_role(role: str) -> str:
    """Return ``DROP ROLE IF EXISTS <role>;`` (safe in pre-cleanup and cleanup)."""
    r = _validate_identifier(role, "role")
    return f"DROP ROLE IF EXISTS {r};"


def _append_table_drop(
    statements: list[str], drop_kinds: list[str], tables: Sequence[str]
) -> None:
    names = _validate_identifier_list(tables, "tables")
    statements.append(f"DROP TABLE IF EXISTS {', '.join(names)} CASCADE;")
    drop_kinds.append("TABLE")


def _append_schema_drops(
    statements: list[str], drop_kinds: list[str], schemas: Sequence[str]
) -> None:
    for schema in schemas:
        s = _validate_identifier(schema, "schemas")
        statements.append(f"DROP SCHEMA IF EXISTS {s} CASCADE;")
        drop_kinds.append("SCHEMA")


def _ensure_non_empty(statements: list[str]) -> None:
    """Append a residual SELECT when only the begin marker is present."""
    if len(statements) == 1:
        statements.append(_RESIDUAL_SELECT)


def build_pre_cleanup(
    *,
    tables: Sequence[str] = (),
    specs: Sequence[DropSpec] = (),
    schemas: Sequence[str] = (),
    roles: Sequence[str] = (),
) -> CleanupBookend:
    """Build the idempotent pre-cleanup bookend (safe on a fresh database).

    Order: tables (anchor) -> specs (caller's reverse-dependency order) ->
    schemas -> roles (``DROP ROLE IF EXISTS`` only). ``DROP OWNED BY`` is
    unreachable here. Emits a residual ``SELECT`` when nothing is dropped so the
    region is never empty and the bracket markers stay meaningful.
    """
    statements: list[str] = [PRE_CLEANUP_BEGIN]
    drop_kinds: list[str] = []
    if tables:
        _append_table_drop(statements, drop_kinds, tables)
    for spec in specs:
        statements.append(idempotent_drop(spec))
        drop_kinds.append(spec.kind)
    _append_schema_drops(statements, drop_kinds, schemas)
    for role in roles:
        statements.append(guarded_drop_role(role))
    _ensure_non_empty(statements)
    statements.append(PRE_CLEANUP_END)
    return CleanupBookend(tuple(statements), tuple(drop_kinds))


def build_cleanup(
    *,
    tables: Sequence[str] = (),
    specs: Sequence[DropSpec] = (),
    schemas: Sequence[str] = (),
    roles: Sequence[str] = (),
    drop_owned: bool = False,
    reset_role: bool = False,
) -> CleanupBookend:
    """Build the post-target cleanup bookend.

    Order: optional ``RESET ROLE`` -> specs (reverse-dependency) -> schemas ->
    roles (``DROP OWNED BY`` then ``DROP ROLE IF EXISTS`` when ``drop_owned``) ->
    tables LAST (the DROP TABLE anchor the table-bookend gate expects).
    """
    statements: list[str] = [CLEANUP_BEGIN]
    drop_kinds: list[str] = []
    if reset_role:
        statements.append("RESET ROLE;")
    for spec in specs:
        statements.append(idempotent_drop(spec))
        drop_kinds.append(spec.kind)
    _append_schema_drops(statements, drop_kinds, schemas)
    for role in roles:
        if drop_owned:
            statements.append(guarded_drop_owned_by(role))
        statements.append(guarded_drop_role(role))
    if tables:
        _append_table_drop(statements, drop_kinds, tables)
    _ensure_non_empty(statements)
    statements.append(CLEANUP_END)
    return CleanupBookend(tuple(statements), tuple(drop_kinds))
