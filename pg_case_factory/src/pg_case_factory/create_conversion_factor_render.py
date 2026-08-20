"""Render complete PostgreSQL 18.4 CREATE CONVERSION factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CREATE CONVERSION is a DDL statement: the target is a
``pg_catalog.pg_conversion`` catalog row, not a ``pg_class`` relation.
All catalog oracles schema-qualify ``pg_catalog.pg_conversion``
(exempt from the file-prefix style gate).  No case creates a TABLE, so
the bookend (DROP TABLE IF EXISTS) is never emitted.
Every catalog SELECT carries a top-level ``ORDER BY count(*)``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_conversion_factor_extension import (
    CreateConversionFactorExtensionCase,
    _present_failure_pair,
)
from .create_conversion_factor_loop import (
    CreateConversionFactorCase,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/conversion/"
    "create_conversion.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/conversion/"
    "create_conversion.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_CONV_PROC_SIG = (
    "(integer, integer, cstring, internal, integer, boolean) "
    "RETURNS integer"
)
_INVALID_FUNC_BODY = "$$BEGIN RETURN 'x'; END$$"


class CreateConversionFactorRenderError(ValueError):
    """Raised when a CREATE CONVERSION case cannot be rendered."""


@dataclass(frozen=True)
class CreateConversionFactorWitness:
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


def _synthetic_case(
    ext: CreateConversionFactorExtensionCase,
) -> CreateConversionFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get(
            "target_action", "create_conversion"
        )
    return CreateConversionFactorCase(
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
    case: CreateConversionFactorCase
    | CreateConversionFactorExtensionCase,
) -> CreateConversionFactorCase:
    if isinstance(case, CreateConversionFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateConversionFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _schema_missing(a: dict[str, str]) -> bool:
    return a.get("schema_existence", "schema_exists") == "schema_not_exists"


def _schema_name(a: dict[str, str], p: str) -> str:
    if _schema_missing(a):
        return f"{p}noschema"
    return f"{p}schema"


def _conversion_name(a: dict[str, str], p: str) -> str:
    """The conversion identifier in CREATE CONVERSION."""

    shape = a.get("conversion_name_shape", "simple_id")
    schema = _schema_name(a, p)
    if shape == "quoted_id":
        return f'"{p}Mixed Conv"'
    if shape == "schema_qualified":
        return f"{schema}.{p}conv"
    if shape == "reserved_word_as_name":
        return f"{p}language"
    if shape == "duplicate_name":
        return f"{p}dupconv"
    return f"{p}conv"


def _conversion_name_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    shape = a.get("conversion_name_shape", "simple_id")
    if shape == "quoted_id":
        return f"{p}Mixed Conv"
    if shape == "schema_qualified":
        return f"{p}conv"
    if shape == "reserved_word_as_name":
        return f"{p}language"
    if shape == "duplicate_name":
        return f"{p}dupconv"
    return f"{p}conv"


def _function_name(a: dict[str, str], p: str) -> str:
    """The function identifier in CREATE CONVERSION."""

    shape = a.get("function_name_shape", "simple_id")
    schema = _schema_name(a, p)
    if shape == "schema_qualified":
        return f"{schema}.{p}func"
    if shape == "nonexistent_name":
        return f"{p}nofunc"
    return f"{p}func"


def _source_encoding_name(a: dict[str, str]) -> str:
    """The source encoding name in CREATE CONVERSION."""

    shape = a.get("encoding_name_shape", "valid_encoding_name")
    if shape == "nonexistent_encoding_name":
        return "FAKEENC"
    if shape == "sql_ascii_encoding_name":
        return "SQL_ASCII"
    return a.get("source_encoding", "UTF8")


def _dest_encoding_name(a: dict[str, str]) -> str:
    """The dest encoding name in CREATE CONVERSION."""

    shape = a.get("encoding_name_shape", "valid_encoding_name")
    if shape == "nonexistent_encoding_name":
        return "FAKEENC"
    if shape == "sql_ascii_encoding_name":
        return "SQL_ASCII"
    return a.get("dest_encoding", "LATIN1")


def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target CREATE CONVERSION runs."""

    level = a.get("privilege_level", "superuser")
    if level == "schema_owner_with_create":
        return f"{p}owner"
    if level == "non_owner_no_create":
        return f"{p}nopriv"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    level = a.get("privilege_level", "superuser")
    if level == "schema_owner_with_create":
        roles.append(f"{p}owner")
    if level == "non_owner_no_create":
        roles.append(f"{p}nopriv")
    return tuple(roles)


def _needs_schema(a: dict[str, str]) -> bool:
    if _schema_missing(a):
        return False
    if a.get("privilege_level", "superuser") != "superuser":
        return True
    shape = a.get("conversion_name_shape", "simple_id")
    fshape = a.get("function_name_shape", "simple_id")
    return shape == "schema_qualified" or fshape == "schema_qualified"


def _needs_function(a: dict[str, str]) -> bool:
    state = a.get(
        "conversion_function_state",
        "function_exists_valid_signature",
    )
    fshape = a.get("function_name_shape", "simple_id")
    if fshape == "nonexistent_name":
        return False
    return state != "function_not_exists"


def _function_is_valid(a: dict[str, str]) -> bool:
    state = a.get(
        "conversion_function_state",
        "function_exists_valid_signature",
    )
    return state == "function_exists_valid_signature"


def _needs_existing_conversion(a: dict[str, str]) -> bool:
    state = a.get("object_state", "not_exists")
    return state == "exists"


def _needs_existing_default(a: dict[str, str]) -> bool:
    state = a.get("object_state", "not_exists")
    return state == "same_encoding_pair_default_exists"


def _is_default_branch(a: dict[str, str]) -> bool:
    return a.get("target_action", "create_conversion") == (
        "create_default_conversion"
    )


def _probe_select(
    case: CreateConversionFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only error_assertion."""

    mode = a.get("verification_mode", "catalog_query_pg_conversion")
    if mode == "error_assertion":
        return None

    conv_lit = _conversion_name_literal(a, p)
    success = case.outcome == "success"
    cmp_op = ">" if success else "="
    return (
        f"SELECT count(*) {cmp_op} 0 AS conversion_state "
        f"FROM pg_catalog.pg_conversion "
        f"WHERE conname = '{conv_lit}' "
        f"ORDER BY count(*);"
    )


def _tables_to_drop(
    case: CreateConversionFactorCase,
) -> list[str]:
    """Fixture tables the case CREATEs.

    CREATE CONVERSION is a DDL statement that never creates a TABLE.
    The bookend (DROP TABLE IF EXISTS) is therefore never emitted.
    """
    return []


def _build_target(
    a: dict[str, str], p: str, conv: str
) -> str:
    """The primary CREATE CONVERSION statement for the active branch."""

    default = "DEFAULT " if _is_default_branch(a) else ""
    src = _source_encoding_name(a)
    dst = _dest_encoding_name(a)
    func = _function_name(a, p)
    return (
        f"CREATE {default}CONVERSION {conv} "
        f"FOR '{src}' TO '{dst}' FROM {func};"
    )


def _resolve_case(
    case: CreateConversionFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    schema = _schema_name(a, p)
    conv = _conversion_name(a, p)
    func = _function_name(a, p)
    role = _effective_role(a, p)
    roles = _role_names(a, p)

    setup: list[str] = []
    locus = "target.create_conversion"

    if _needs_schema(a):
        setup.append(f"CREATE SCHEMA IF NOT EXISTS {schema};")
        locus = "fixture.schema"

    if _needs_function(a):
        if _function_is_valid(a):
            setup.append(
                f"CREATE FUNCTION {func} {_CONV_PROC_SIG} "
                f"LANGUAGE internal AS 'ascii_to_mic';"
            )
        else:
            setup.append(
                f"CREATE FUNCTION {func}(text) RETURNS text "
                f"LANGUAGE plpgsql AS {_INVALID_FUNC_BODY};"
            )
        locus = "fixture.function"

    if _needs_existing_conversion(a):
        setup.append(
            f"CREATE CONVERSION {conv} "
            f"FOR '{_source_encoding_name(a)}' "
            f"TO '{_dest_encoding_name(a)}' FROM {func};"
        )
        locus = "fixture.existing_conversion"

    if _needs_existing_default(a):
        setup.append(
            f"CREATE DEFAULT CONVERSION {p}existingdef "
            f"FOR '{_source_encoding_name(a)}' "
            f"TO '{_dest_encoding_name(a)}' FROM {func};"
        )
        locus = "fixture.existing_default"

    for role_name in roles:
        if role_name == f"{p}owner":
            setup.append(
                f"CREATE ROLE {p}owner LOGIN NOSUPERUSER;"
            )
            if _needs_schema(a):
                setup.append(
                    f"GRANT CREATE ON SCHEMA {schema} "
                    f"TO {p}owner;"
                )
            setup.append(
                f"GRANT USAGE ON SCHEMA {schema} TO {p}owner;"
            )
        elif role_name == f"{p}nopriv":
            setup.append(
                f"CREATE ROLE {p}nopriv LOGIN NOSUPERUSER;"
            )
            if _needs_schema(a):
                setup.append(
                    f"GRANT USAGE ON SCHEMA {schema} "
                    f"TO {p}nopriv;"
                )

    if a.get("function_privilege", "has_execute") == "no_execute":
        setup.append(
            f"REVOKE EXECUTE ON FUNCTION {func} "
            f"FROM PUBLIC;"
        )

    if role:
        setup.append(f"SET ROLE {role};")
        locus = "fixture.privilege"

    target = _build_target(a, p, conv)

    assert_lines: list[str] = []
    if role:
        assert_lines.append("RESET ROLE;")
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    probe = _probe_select(case, a, p)
    if probe is not None:
        assert_lines.append(probe)

    conversions_to_drop: list[str] = []
    if case.outcome == "success":
        conversions_to_drop.append(conv)
    if _needs_existing_conversion(a):
        conversions_to_drop.append(conv)
    if _needs_existing_default(a):
        conversions_to_drop.append(f"{p}existingdef")

    role_drops = [
        statement
        for role_name in roles
        for statement in (
            f"DROP OWNED BY {role_name} CASCADE;",
            f"DROP ROLE IF EXISTS {role_name};",
        )
    ]

    conv_drops = [
        f"DROP CONVERSION IF EXISTS {name} CASCADE;"
        for name in dict.fromkeys(conversions_to_drop)
    ]
    func_drops: list[str] = []
    if _needs_function(a):
        func_drops.append(
            f"DROP FUNCTION IF EXISTS {func} CASCADE;"
        )
    schema_drops: list[str] = []
    if _needs_schema(a):
        schema_drops.append(
            f"DROP SCHEMA IF EXISTS {schema} CASCADE;"
        )

    pre_cleanup: list[str] = []
    pre_cleanup.extend(conv_drops)
    pre_cleanup.extend(func_drops)
    pre_cleanup.extend(schema_drops)
    pre_cleanup.extend(role_drops)
    if not pre_cleanup:
        pre_cleanup.append(
            "SELECT 1 AS residual_check_no_objects;"
        )

    cleanup: list[str] = []
    if role:
        cleanup.append("RESET ROLE;")
    cleanup.extend(conv_drops)
    cleanup.extend(func_drops)
    cleanup.extend(schema_drops)
    cleanup.extend(role_drops)
    if not cleanup:
        cleanup.append(
            "SELECT 1 AS residual_check_no_objects;"
        )

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


def resolve_create_conversion_factor_witness(
    case: CreateConversionFactorCase
    | CreateConversionFactorExtensionCase,
    repository_root: Path,
) -> CreateConversionFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateConversionFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_create_conversion(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(
            r"(?im)^\s*CREATE\s+(?:DEFAULT\s+)?CONVERSION\b",
            region,
        )
    )


def _header(case: CreateConversionFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE CONVERSION {case.factor_key}="
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


def render_create_conversion_factor_case(
    case: CreateConversionFactorCase
    | CreateConversionFactorExtensionCase,
    repository_root: Path,
) -> str:
    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地规则和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 CREATE CONVERSION。")
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
    case: CreateConversionFactorCase
    | CreateConversionFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_conversion_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_conversion_factor_programs(
    baseline_plan: CreateConversionFactorCase,
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


__all__ = [
    "CreateConversionFactorRenderError",
    "CreateConversionFactorWitness",
    "count_primary_create_conversion",
    "generate_create_conversion_factor_programs",
    "render_create_conversion_factor_case",
    "resolve_create_conversion_factor_witness",
]
