"""Render complete PostgreSQL 18.4 CREATE FOREIGN DATA WRAPPER factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CREATE FOREIGN DATA WRAPPER is a DDL statement: the target is a
``pg_catalog.pg_foreign_data_wrapper`` catalog row, NOT a ``pg_class``
relation.  All catalog oracles schema-qualify
``pg_catalog.pg_foreign_data_wrapper`` (exempt from the file-prefix
style gate — it starts with ``pg_``).  The statement does NOT create
fixture tables, so the bookend gate is EXEMPT: the placeholder
``SELECT 1 AS residual_check_no_objects;`` is used when no
pre-cleanup/cleanup objects exist.  Every catalog SELECT carries a
top-level ``ORDER BY count(*)``.

CREATE FOREIGN DATA WRAPPER does NOT support ``OR REPLACE`` — the
official PostgreSQL 18 synopsis is ``CREATE FOREIGN DATA WRAPPER name
...`` with no optional ``OR REPLACE`` clause.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_foreign_data_wrapper_factor_extension import (
    CreateForeignDataWrapperFactorExtensionCase,
    _present_failure_pair,
)
from .create_foreign_data_wrapper_factor_loop import (
    CreateForeignDataWrapperFactorCase,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/"
    "foreign_data_wrapper/create_foreign_data_wrapper.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/"
    "foreign_data_wrapper/create_foreign_data_wrapper.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class CreateForeignDataWrapperFactorRenderError(ValueError):
    """Raised when a CREATE FOREIGN DATA WRAPPER case cannot be rendered."""


@dataclass(frozen=True)
class CreateForeignDataWrapperFactorWitness:
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
    ext: CreateForeignDataWrapperFactorExtensionCase,
) -> CreateForeignDataWrapperFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get(
            "target_action", "create_foreign_data_wrapper"
        )
    return CreateForeignDataWrapperFactorCase(
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
    case: CreateForeignDataWrapperFactorCase
    | CreateForeignDataWrapperFactorExtensionCase,
) -> CreateForeignDataWrapperFactorCase:
    if isinstance(
        case, CreateForeignDataWrapperFactorExtensionCase
    ):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateForeignDataWrapperFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _fdw_name(a: dict[str, str], p: str) -> str:
    """The FDW identifier in CREATE FOREIGN DATA WRAPPER."""

    shape = a.get("fdw_name_shape", "simple_id")
    if shape == "quoted_id":
        return f'"{p}Mixed Fdw"'
    if shape == "reserved_word_name":
        return f'"{p}select"'
    if shape == "duplicate_name":
        return f"{p}fdw"
    if shape == "nonexistent_name":
        return f"{p}fdw"
    return f"{p}fdw"


def _fdw_name_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    shape = a.get("fdw_name_shape", "simple_id")
    if shape == "quoted_id":
        return f"{p}Mixed Fdw"
    if shape == "reserved_word_name":
        return f"{p}select"
    return f"{p}fdw"


def _handler_name(a: dict[str, str], p: str) -> str:
    """The handler function identifier."""

    shape = a.get("handler_name_shape", "simple_id")
    if shape == "schema_qualified":
        return f"public.{p}handler"
    if shape == "nonexistent_function":
        return f"{p}missing_handler"
    return f"{p}handler"


def _handler_name_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for handler oracle queries."""

    shape = a.get("handler_name_shape", "simple_id")
    if shape == "schema_qualified":
        return f"{p}handler"
    return f"{p}handler"


def _validator_name(a: dict[str, str], p: str) -> str:
    """The validator function identifier."""

    shape = a.get("validator_name_shape", "simple_id")
    if shape == "schema_qualified":
        return f"public.{p}validator"
    if shape == "nonexistent_function":
        return f"{p}missing_validator"
    return f"{p}validator"


def _validator_name_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for validator oracle queries."""

    shape = a.get("validator_name_shape", "simple_id")
    if shape == "schema_qualified":
        return f"{p}validator"
    return f"{p}validator"


def _handler_clause_sql(a: dict[str, str], p: str) -> str:
    """The HANDLER / NO HANDLER clause fragment."""

    hc = a.get("handler_clause", "omitted")
    if hc == "specified_handler_function":
        handler = _handler_name(a, p)
        return f"HANDLER {handler}"
    if hc == "no_handler":
        return "NO HANDLER"
    return ""


def _validator_clause_sql(a: dict[str, str], p: str) -> str:
    """The VALIDATOR / NO VALIDATOR clause fragment."""

    vc = a.get("validator_clause", "omitted")
    if vc == "specified_validator_function":
        validator = _validator_name(a, p)
        return f"VALIDATOR {validator}"
    if vc == "no_validator":
        return "NO VALIDATOR"
    return ""


def _options_clause_sql(a: dict[str, str], p: str) -> str:
    """The OPTIONS clause fragment."""

    oc = a.get("options_clause", "omitted")
    ons = a.get("option_name_shape", "valid_option")
    if oc == "omitted":
        return ""
    if oc == "single_option":
        return f"OPTIONS ('{p}opt1' 'val1')"
    if oc == "multiple_options":
        if ons == "duplicate_option":
            return (
                f"OPTIONS ('{p}dup' 'val1', "
                f"'{p}dup' 'val2')"
            )
        return (
            f"OPTIONS ('{p}opt1' 'val1', "
            f"'{p}opt2' 'val2')"
        )
    return ""


def _is_duplicate(a: dict[str, str]) -> bool:
    return a.get("object_state", "not_exists") == "already_exists"


def _handler_missing(a: dict[str, str]) -> bool:
    return a.get("handler_function_existence") == "function_not_exists"


def _validator_missing(a: dict[str, str]) -> bool:
    return (
        a.get("validator_function_existence") == "function_not_exists"
    )


def _handler_wrong_return(a: dict[str, str]) -> bool:
    return (
        a.get("handler_function_return_type") == "mismatches_fdw_handler"
    )


def _is_non_superuser(a: dict[str, str]) -> bool:
    return a.get("privilege_level") == "non_superuser"


def _effective_role(a: dict[str, str], p: str) -> str:
    if _is_non_superuser(a):
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    if _is_non_superuser(a):
        roles.append(f"{p}actor")
    return tuple(roles)


def _handler_returns_type(a: dict[str, str]) -> str:
    if _handler_wrong_return(a):
        return "text"
    return "fdw_handler"


def _probe_select(
    case: CreateForeignDataWrapperFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for error_assertion."""

    mode = a.get("verification_mode", "pg_foreign_data_wrapper_catalog")
    if mode == "error_assertion":
        return None

    fdw_lit = _fdw_name_literal(a, p)
    present = case.outcome == "success"
    cmp_op = ">" if present else "="
    return (
        f"SELECT count(*) {cmp_op} 0 AS fdw_state "
        f"FROM pg_catalog.pg_foreign_data_wrapper "
        f"WHERE fdwname = '{fdw_lit}' "
        f"ORDER BY count(*);"
    )


def _build_target(
    a: dict[str, str],
    p: str,
) -> str:
    """The primary CREATE FOREIGN DATA WRAPPER statement."""

    fdw = _fdw_name(a, p)
    parts = [f"CREATE FOREIGN DATA WRAPPER {fdw}"]
    handler_clause = _handler_clause_sql(a, p)
    if handler_clause:
        parts.append(handler_clause)
    validator_clause = _validator_clause_sql(a, p)
    if validator_clause:
        parts.append(validator_clause)
    options_clause = _options_clause_sql(a, p)
    if options_clause:
        parts.append(options_clause)
    return " ".join(parts) + ";"


def _resolve_case(
    case: CreateForeignDataWrapperFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix

    setup: list[str] = []
    locus = "target.create_foreign_data_wrapper"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    fdw = _fdw_name(a, p)

    # --- role fixtures -----------------------------------------------
    if effective == f"{p}actor":
        setup.append(
            f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;"
        )
        locus = "fixture.privilege_state"

    # --- handler function fixture ------------------------------------
    handler_clause = a.get("handler_clause", "omitted")
    if (
        handler_clause == "specified_handler_function"
        and not _handler_missing(a)
    ):
        handler = _handler_name(a, p)
        returns = _handler_returns_type(a)
        if returns == "fdw_handler":
            setup.append(
                f"CREATE FUNCTION {handler}() RETURNS fdw_handler "
                f"AS 'MODULE_PATHNAME', 'cfdw_handler' "
                f"LANGUAGE C STRICT;"
            )
        else:
            setup.append(
                f"CREATE FUNCTION {handler}() RETURNS {returns} "
                f"AS 'MODULE_PATHNAME', 'cfdw_handler' "
                f"LANGUAGE C STRICT;"
            )
        locus = "fixture.handler_function"

    # --- validator function fixture ----------------------------------
    validator_clause = a.get("validator_clause", "omitted")
    if (
        validator_clause == "specified_validator_function"
        and not _validator_missing(a)
    ):
        validator = _validator_name(a, p)
        setup.append(
            f"CREATE FUNCTION {validator}(text[], oid) "
            f"RETURNS void "
            f"AS 'MODULE_PATHNAME', 'cfdw_validator' "
            f"LANGUAGE C STRICT;"
        )
        locus = "fixture.validator_function"

    # --- pre-existing FDW for duplicate_name / already_exists ---------
    if _is_duplicate(a):
        setup.append(
            f"CREATE FOREIGN DATA WRAPPER {fdw} NO HANDLER;"
        )
        locus = "fixture.duplicate_fdw"

    # --- arm the effective role --------------------------------------
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
    fdw_drops: list[str] = [
        f"DROP FOREIGN DATA WRAPPER IF EXISTS {fdw} CASCADE;"
    ]

    role_drops = [
        statement
        for role in roles
        for statement in (
            f"DROP OWNED BY {role} CASCADE;",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    handler_drops: list[str] = []
    if (
        handler_clause == "specified_handler_function"
        and not _handler_missing(a)
    ):
        handler = _handler_name(a, p)
        returns = _handler_returns_type(a)
        handler_drops.append(
            f"DROP FUNCTION IF EXISTS {handler}();"
        )

    validator_drops: list[str] = []
    if (
        validator_clause == "specified_validator_function"
        and not _validator_missing(a)
    ):
        validator = _validator_name(a, p)
        validator_drops.append(
            f"DROP FUNCTION IF EXISTS {validator}(text[], oid);"
        )

    # pre-cleanup: FDW first, then functions, then roles
    pre_cleanup: list[str] = []
    pre_cleanup.extend(fdw_drops)
    pre_cleanup.extend(handler_drops)
    pre_cleanup.extend(validator_drops)
    pre_cleanup.extend(role_drops)
    if not pre_cleanup:
        pre_cleanup.append(
            "SELECT 1 AS residual_check_no_objects;"
        )

    # cleanup: RESET ROLE, FDW, functions, roles
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(fdw_drops)
    cleanup.extend(handler_drops)
    cleanup.extend(validator_drops)
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


def resolve_create_foreign_data_wrapper_factor_witness(
    case: CreateForeignDataWrapperFactorCase
    | CreateForeignDataWrapperFactorExtensionCase,
    repository_root: Path,
) -> CreateForeignDataWrapperFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateForeignDataWrapperFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_create_foreign_data_wrapper(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(
            r"(?im)^CREATE\s+FOREIGN\s+DATA\s+WRAPPER\b",
            region,
        )
    )


def _header(case: CreateForeignDataWrapperFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE FOREIGN DATA WRAPPER "
        f"{case.factor_key}={case.factor_value}",
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


def render_create_foreign_data_wrapper_factor_case(
    case: CreateForeignDataWrapperFactorCase
    | CreateForeignDataWrapperFactorExtensionCase,
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
    lines.append(
        "-- 3. 执行唯一获得覆盖信用的 CREATE FOREIGN DATA WRAPPER。"
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
    case: CreateForeignDataWrapperFactorCase
    | CreateForeignDataWrapperFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_foreign_data_wrapper_factor_case(
        case, Path(".")
    )
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_foreign_data_wrapper_factor_programs(
    baseline_plan: object,
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
    "CreateForeignDataWrapperFactorRenderError",
    "CreateForeignDataWrapperFactorWitness",
    "count_primary_create_foreign_data_wrapper",
    "generate_create_foreign_data_wrapper_factor_programs",
    "render_create_foreign_data_wrapper_factor_case",
    "resolve_create_foreign_data_wrapper_factor_witness",
]
