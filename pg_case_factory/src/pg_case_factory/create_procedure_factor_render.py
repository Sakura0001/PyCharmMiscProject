"""Render complete PostgreSQL 18.4 CREATE PROCEDURE factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CREATE PROCEDURE is a catalog-row DDL statement: the target is a
``pg_catalog.pg_proc`` catalog row (prokind ``'p'``), not a ``pg_class``
relation.  All catalog oracles schema-qualify ``pg_catalog.pg_proc`` or
``information_schema.routines`` (both exempt from the file-prefix style
gate).  No case creates a TABLE, so the bookend (DROP TABLE IF EXISTS)
is never emitted.  Every catalog SELECT carries a top-level
``ORDER BY count(*)`` so the catalog-observability gate passes.

The ``\\set ON_ERROR_STOP on`` is followed by ``SELECT 1 AS setup_boundary;``
so the primary CREATE PROCEDURE always starts its own ``;``-segment even
when no setup fixtures precede it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_procedure_factor_extension import (
    CreateProcedureFactorExtensionCase,
    _present_failure_pair,
)
from .create_procedure_factor_loop import (
    CreateProcedureFactorCase,
    CreateProcedureFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/procedure/"
    "create_procedure.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/procedure/"
    "create_procedure.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class CreateProcedureFactorRenderError(ValueError):
    """Raised when a CREATE PROCEDURE case cannot be rendered."""


@dataclass(frozen=True)
class CreateProcedureFactorWitness:
    primary_obligation_id: str
    target_sql_fragment: str
    outcome: str
    expected_sqlstate: str
    setup_sql: tuple[str, ...]
    oracle_sql: tuple[str, ...]
    cleanup_sql: tuple[str, ...]
    semantic_locus: str


@dataclass(frozen=True)
class _CasePlan:
    target_fragment: str
    setup_lines: tuple[str, ...]
    assert_lines: tuple[str, ...]
    pre_cleanup_lines: tuple[str, ...]
    cleanup_lines: tuple[str, ...]
    on_error_off: bool
    semantic_locus: str


_ARGTYPE_SQL: dict[str, str] = {
    "smallint": "smallint",
    "integer": "integer",
    "bigint": "bigint",
    "real": "real",
    "double_precision": "double precision",
    "numeric": "numeric",
    "character_varying": "character varying",
    "character": "character",
    "text": "text",
    "bytea": "bytea",
    "date": "date",
    "timestamp": "timestamp",
    "timestamp_with_time_zone": "timestamp with time zone",
    "interval": "interval",
    "boolean": "boolean",
    "json": "json",
    "jsonb": "jsonb",
    "uuid": "uuid",
    "integer_array": "integer[]",
    "text_array": "text[]",
    "int4range": "int4range",
    "tsrange": "tsrange",
    "oid": "oid",
    "regclass": "regclass",
    "nosuchtype": "nosuchtype",
}

_LANGUAGE_NAME: dict[str, str] = {
    "sql": "sql",
    "plpgsql": "plpgsql",
    "c": "c",
    "internal": "internal",
    "other": "plpython3u",
}

_SECURITY_SQL: dict[str, str] = {
    "SECURITY_INVOKER": "SECURITY INVOKER",
    "SECURITY_DEFINER": "SECURITY DEFINER",
}


def _synthetic_case(
    ext: CreateProcedureFactorExtensionCase,
) -> CreateProcedureFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_form"
        factor_value = "create_procedure"
    return CreateProcedureFactorCase(
        ordinal=ext.ordinal,
        case_id=ext.case_id,
        sql_filename=ext.sql_filename,
        object_prefix=ext.object_prefix,
        primary_obligation_id=ext.derivation_id,
        kind="EXT",
        factor_key=factor_key,
        factor_value=factor_value,
        consumer_action_id=ext.consumer_action_id,
        outcome=ext.outcome,
        expected_sqlstate=ext.expected_sqlstate,
        expected_failure_reason=ext.expected_failure_reason,
        baseline_assignments=ext.factor_assignment,
        execution_profile="default",
    )


def _as_render_case(
    case: CreateProcedureFactorCase
    | CreateProcedureFactorExtensionCase,
) -> CreateProcedureFactorCase:
    if isinstance(case, CreateProcedureFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateProcedureFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _argtype_sql(a: dict[str, str], p: str) -> str:
    t = a.get("argtype", "integer")
    if t == "composite_type":
        return f"{p}ctype"
    if t == "enum_type":
        return f"{p}etype"
    return _ARGTYPE_SQL.get(t, "integer")


def _procedure_name(a: dict[str, str], p: str) -> str:
    shape = a.get("procedure_name_shape", "simple")
    if shape == "quoted":
        return f'"{p}QProc"'
    if shape == "reserved_word":
        return f'"{p}select"'
    if shape == "schema_qualified":
        return f"public.{p}proc"
    if a.get("identifier_length_exceeded") == "over_63_chars":
        return f"{p}" + "a" * 50
    return f"{p}proc"


def _procedure_name_literal(a: dict[str, str], p: str) -> str:
    shape = a.get("procedure_name_shape", "simple")
    if shape == "quoted":
        return f"{p}QProc"
    if shape == "reserved_word":
        return f"{p}select"
    if shape == "schema_qualified":
        return f"{p}proc"
    if a.get("identifier_length_exceeded") == "over_63_chars":
        return f"{p}" + "a" * 50
    return f"{p}proc"


def _procedure_args(a: dict[str, str], p: str) -> str:
    argmode = a.get("argmode", "absent")
    argname = a.get("argname", "without_argname")
    argtype = _argtype_sql(a, p)
    default = a.get("default_expr_shape", "without_DEFAULT")

    parts: list[str] = []
    if argmode != "absent":
        parts.append(argmode)
    if argname == "with_argname":
        parts.append(f"{p}arg")
    if argmode == "VARIADIC":
        if not argtype.endswith("[]"):
            parts.append(f"{argtype}[]")
        else:
            parts.append(argtype)
    else:
        parts.append(argtype)
    if default == "with_DEFAULT":
        parts.append("DEFAULT NULL")
    elif default == "with_equals":
        parts.append("= NULL")
    return " ".join(parts)


def _argtype_signature(a: dict[str, str], p: str) -> str:
    argmode = a.get("argmode", "absent")
    argtype = _argtype_sql(a, p)
    if argmode == "VARIADIC" and not argtype.endswith("[]"):
        return f"{argtype}[]"
    return argtype


def _body_clause(a: dict[str, str], p: str) -> str:
    form = a.get("sql_body_form", "sql_body_inline")
    lang = a.get("language_clause", "sql")

    if lang != "sql":
        if lang == "c":
            return "AS '$libdir/no_such_file', 'no_such_symbol'"
        if lang == "internal":
            return "AS 'no_such_internal'"
        if lang == "plpgsql":
            return "AS 'BEGIN\\n  NULL;\\nEND;'"
        return "AS 'no_such_body'"

    if form == "AS_definition":
        return "AS 'NULL'"
    if form == "AS_obj_file_link_symbol":
        return "AS '$libdir/no_such_file', 'no_such_symbol'"
    return "BEGIN ATOMIC NULL; END"


def _is_failure(a: dict[str, str]) -> bool:
    return a.get("expected_status") == "failure"


def _is_duplicate(a: dict[str, str]) -> bool:
    return (
        a.get("object_state") == "already_exists_same_signature"
        and a.get("or_replace_clause", "absent") == "absent"
    )


def _is_or_replace_replace(a: dict[str, str]) -> bool:
    return (
        a.get("duplicate_procedure_signature")
        == "with_OR_REPLACE_replace"
    )


def _is_conflicting_function(a: dict[str, str]) -> bool:
    return (
        a.get("conflicting_name_with_function")
        == "same_name_same_argtypes_function_exists"
    )


def _is_permission_failure(a: dict[str, str]) -> bool:
    return (
        a.get("permission_insufficient")
        in (
            "no_create_privilege_in_schema",
            "no_usage_privilege_on_language",
        )
        or a.get("language_not_available")
        == "untrusted_language_requires_superuser"
    )


def _present(a: dict[str, str]) -> bool:
    """Whether the procedure exists after the target statement."""

    if not _is_failure(a):
        return True
    if _is_duplicate(a):
        return True
    if (
        a.get("duplicate_procedure_signature")
        == "without_OR_REPLACE_error"
    ):
        return True
    return False


def _effective_role(a: dict[str, str], p: str) -> str:
    priv = a.get("privilege_level", "superuser")
    if priv == "non_owner_no_privilege":
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    priv = a.get("privilege_level", "superuser")
    if priv == "non_owner_no_privilege":
        roles.append(f"{p}actor")
    return tuple(roles)


def _build_target(a: dict[str, str], p: str) -> str:
    """The primary CREATE [OR REPLACE] PROCEDURE statement."""

    orr = a.get("or_replace_clause", "absent")
    replace = "OR REPLACE " if orr == "present" else ""
    name = _procedure_name(a, p)
    args = _procedure_args(a, p)

    clauses: list[str] = []
    clauses.append(
        f"LANGUAGE {_LANGUAGE_NAME.get(a.get('language_clause', 'sql'), 'sql')}"
    )

    sec = a.get("security_clause", "absent")
    if sec != "absent":
        clauses.append(_SECURITY_SQL[sec])

    trans = a.get("transform_clause", "absent")
    if trans == "present":
        clauses.append("TRANSFORM FOR TYPE text")

    setc = a.get("set_clause", "absent")
    if setc == "present":
        clauses.append("SET search_path TO public")

    body = _body_clause(a, p)
    clauses.append(body)

    parts = [f"CREATE {replace}PROCEDURE {name}({args})"]
    parts.extend(clauses)
    return " ".join(parts) + ";"


def _probe_select(
    case: CreateProcedureFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only verification."""

    mode = a.get("verification_mode", "pg_proc_catalog_query")
    literal = _procedure_name_literal(a, p)
    name = _procedure_name(a, p)
    argtypes = _argtype_signature(a, p)

    if not _present(a):
        if mode == "information_schema_routines":
            return (
                f"SELECT count(*) = 0 AS procedure_state "
                f"FROM information_schema.routines "
                f"WHERE routine_name = '{literal}' "
                f"ORDER BY count(*);"
            )
        return (
            f"SELECT count(*) = 0 AS procedure_state "
            f"FROM pg_catalog.pg_proc "
            f"WHERE proname = '{literal}' AND prokind = 'p' "
            f"ORDER BY count(*);"
            if mode != "CALL_procedure_execution"
            else None
        )

    if mode == "CALL_procedure_execution":
        return f"CALL {name}(NULL);"
    if mode == "pg_get_functiondef":
        return (
            f"SELECT pg_get_functiondef("
            f"'{name}({argtypes})'::regprocedure"
            f") AS procedure_def;"
        )
    if mode == "information_schema_routines":
        return (
            f"SELECT count(*) > 0 AS procedure_state "
            f"FROM information_schema.routines "
            f"WHERE routine_name = '{literal}' "
            f"ORDER BY count(*);"
        )
    return (
        f"SELECT count(*) > 0 AS procedure_state "
        f"FROM pg_catalog.pg_proc "
        f"WHERE proname = '{literal}' AND prokind = 'p' "
        f"ORDER BY count(*);"
    )


def _resolve_case(case: CreateProcedureFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix

    setup: list[str] = []
    locus = "target.create_procedure"

    name = _procedure_name(a, p)
    argtypes = _argtype_signature(a, p)
    effective = _effective_role(a, p)
    roles = _role_names(a, p)

    # --- composite/enum type fixtures ---------------------------------
    at = a.get("argtype", "integer")
    if at == "composite_type":
        setup.append(f"CREATE TYPE {p}ctype AS (x integer, y text);")
        locus = "fixture.composite_type"
    elif at == "enum_type":
        setup.append(
            f"CREATE TYPE {p}etype AS ENUM ('red', 'green', 'blue');"
        )
        locus = "fixture.enum_type"

    # --- duplicate procedure fixture (same signature) ----------------
    if _is_duplicate(a) or _is_or_replace_replace(a):
        setup.append(
            f"CREATE PROCEDURE {name}({argtypes}) "
            f"LANGUAGE sql AS 'NULL';"
        )
        locus = "fixture.duplicate_procedure"
    elif a.get("object_state") == "already_exists_different_signature":
        setup.append(
            f"CREATE PROCEDURE {name}(text) "
            f"LANGUAGE sql AS 'NULL';"
        )
        locus = "fixture.overload_procedure"

    # --- conflicting function fixture (same name+args) ---------------
    if _is_conflicting_function(a):
        setup.append(
            f"CREATE FUNCTION {name}({argtypes}) RETURNS integer "
            f"LANGUAGE sql RETURN $1;"
        )
        locus = "fixture.conflicting_function"

    # --- role fixtures (permission failures) -------------------------
    if effective:
        setup.append(
            f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;"
        )
        locus = "fixture.permission_state"

    if effective:
        setup.append(f"SET ROLE {effective};")

    # --- the primary target statement --------------------------------
    target = _build_target(a, p)

    # --- oracle / SQLSTATE assertion ---------------------------------
    assert_lines: list[str] = []
    if effective:
        assert_lines.append("RESET ROLE;")
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    probe = _probe_select(case, a, p)
    if probe is not None:
        assert_lines.append(probe)

    # --- cleanup construction -----------------------------------------
    procedures_to_drop: list[str] = [f"{name}({argtypes})"]
    functions_to_drop: list[str] = []
    if a.get("object_state") == "already_exists_different_signature":
        procedures_to_drop.append(f"{name}(text)")
    if _is_conflicting_function(a):
        functions_to_drop.append(f"{name}({argtypes})")

    cleanup_mode = a.get("cleanup_mode", "DROP_PROCEDURE_IF_EXISTS")
    if cleanup_mode == "DROP_PROCEDURE":
        proc_drops = [
            f"DROP PROCEDURE {pn};" for pn in procedures_to_drop
        ]
    elif cleanup_mode == "DROP_PROCEDURE_CASCADE":
        proc_drops = [
            f"DROP PROCEDURE {pn} CASCADE;" for pn in procedures_to_drop
        ]
    else:
        proc_drops = [
            f"DROP PROCEDURE IF EXISTS {pn};" for pn in procedures_to_drop
        ]

    func_drops = [
        f"DROP FUNCTION IF EXISTS {fn} CASCADE;" for fn in functions_to_drop
    ]

    type_drops: list[str] = []
    if at == "composite_type":
        type_drops.append(f"DROP TYPE IF EXISTS {p}ctype CASCADE;")
    elif at == "enum_type":
        type_drops.append(f"DROP TYPE IF EXISTS {p}etype CASCADE;")

    role_drops = [
        stmt
        for role in roles
        for stmt in (
            f"DROP OWNED BY {role} CASCADE;",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    # pre-cleanup: always use IF EXISTS CASCADE (safe)
    pre_cleanup: list[str] = []
    pre_cleanup.append(
        f"DROP PROCEDURE IF EXISTS {name}({argtypes}) CASCADE;"
    )
    if a.get("object_state") == "already_exists_different_signature":
        pre_cleanup.append(
            f"DROP PROCEDURE IF EXISTS {name}(text) CASCADE;"
        )
    pre_cleanup.append(
        f"DROP FUNCTION IF EXISTS {name}({argtypes}) CASCADE;"
    )
    pre_cleanup.append(f"DROP TYPE IF EXISTS {p}ctype CASCADE;")
    pre_cleanup.append(f"DROP TYPE IF EXISTS {p}etype CASCADE;")
    pre_cleanup.append("RESET ROLE;")
    for role in roles:
        pre_cleanup.append(f"DROP ROLE IF EXISTS {role};")

    # cleanup: types, functions, procedures, roles
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(type_drops)
    cleanup.extend(func_drops)
    cleanup.extend(proc_drops)
    cleanup.extend(role_drops)

    on_error_off = case.outcome == "expected_failure"
    return _CasePlan(
        target_fragment=target,
        setup_lines=tuple(setup),
        assert_lines=tuple(assert_lines),
        pre_cleanup_lines=tuple(pre_cleanup),
        cleanup_lines=tuple(cleanup),
        on_error_off=on_error_off,
        semantic_locus=locus,
    )


def _header(case: CreateProcedureFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE PROCEDURE {case.factor_key}="
        f"{case.factor_value}",
        f"-- FE           : {_FE}",
        "-- ++",
        "-- --------------------------------------------------------",
        f"-- case_id: {case.case_id}",
        f"-- source_md: {_DOC_SOURCE}",
        f"-- factor_md: {_FACTOR_SOURCE}",
        f"-- primary_obligation_id: {case.primary_obligation_id}",
        f"-- expected_outcome: {case.outcome}",
        f"-- expected_sqlstate: {case.expected_sqlstate}",
    ]


def render_create_procedure_factor_case(
    case: CreateProcedureFactorCase
    | CreateProcedureFactorExtensionCase,
    repository_root: Path,
) -> str:
    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("SELECT 1 AS setup_boundary;")
    lines.append("-- 2. 创建完整本地规则和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("SELECT 1 AS pre_target_boundary;")
    lines.append(
        "-- 3. 执行唯一获得覆盖信用的 CREATE PROCEDURE。"
    )
    lines.append(_PRIMARY_BEGIN)
    lines.append(resolved.target_fragment)
    lines.append(_PRIMARY_END)
    lines.append("\\set target_sqlstate :SQLSTATE")
    lines.append("\\echo PGCF_TARGET_SQLSTATE=:target_sqlstate")
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 4. 验证 SQLSTATE、目录状态和数据行为。")
    lines.extend(resolved.assert_lines)
    lines.append("-- 5. 清理全部本编号对象。")
    lines.extend(resolved.cleanup_lines)
    text = "\n".join(lines)
    if not text.endswith("\n"):
        text += "\n"
    return text


def _write_program(
    case: CreateProcedureFactorCase
    | CreateProcedureFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_procedure_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_procedure_factor_programs(
    baseline_plan: CreateProcedureFactorLoopPlan,
    extension_plan: object,
    out_dir: Path,
) -> int:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    count = 0
    for case in baseline_plan.cases:
        _write_program(case, out)
        count += 1
    for case in extension_plan.cases:
        _write_program(case, out)
        count += 1
    return count


def count_primary_create_procedure(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(
            r"(?im)^\s*CREATE\s+(?:OR\s+REPLACE\s+)?PROCEDURE\b",
            region,
        )
    )


def remove_primary_semantic_locus_but_keep_comments(
    sql: str, case: object
) -> str:
    """Mutation helper: remove primary target SQL but keep comment lines."""

    if _PRIMARY_BEGIN not in sql or _PRIMARY_END not in sql:
        return sql
    before_begin, rest = sql.split(_PRIMARY_BEGIN, 1)
    target_and_after, after_end = rest.split(_PRIMARY_END, 1)
    comment_lines = [
        line
        for line in target_and_after.split("\n")
        if line.strip().startswith("--") or not line.strip()
    ]
    return (
        before_begin
        + _PRIMARY_BEGIN
        + "\n".join(comment_lines)
        + _PRIMARY_END
        + after_end
    )


def resolve_create_procedure_factor_witness(
    case: CreateProcedureFactorCase
    | CreateProcedureFactorExtensionCase,
    repository_root: Path,
) -> CreateProcedureFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateProcedureFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


__all__ = [
    "CreateProcedureFactorRenderError",
    "CreateProcedureFactorWitness",
    "count_primary_create_procedure",
    "generate_create_procedure_factor_programs",
    "render_create_procedure_factor_case",
    "resolve_create_procedure_factor_witness",
    "remove_primary_semantic_locus_but_keep_comments",
]
