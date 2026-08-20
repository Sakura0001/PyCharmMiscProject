"""Render complete PostgreSQL 18.4 CREATE SERVER factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CREATE SERVER is a DDL statement: the target is a
``pg_catalog.pg_foreign_server`` catalog row, NOT a ``pg_class``
relation.  All catalog oracles schema-qualify
``pg_catalog.pg_foreign_server`` (exempt from the file-prefix style
gate — it starts with ``pg_``).  The statement does NOT create
fixture tables, so the bookend gate is EXEMPT: the placeholder
``SELECT 1 AS residual_check_no_objects;`` is used when no
pre-cleanup/cleanup objects exist.  Every catalog SELECT carries a
top-level ``ORDER BY count(*)``.

CREATE SERVER does NOT support ``OR REPLACE`` — the official
PostgreSQL 18 synopsis is ``CREATE SERVER [ IF NOT EXISTS ]
server_name ...`` with no optional ``OR REPLACE`` clause.

The setup fixture creates a ``CREATE FOREIGN DATA WRAPPER`` before the
primary CREATE SERVER (that is a different statement, but as a fixture
it is fine; the PRIMARY target line is the CREATE SERVER).  Cleanup
emits ``DROP SERVER IF EXISTS ... CASCADE`` and
``DROP FOREIGN DATA WRAPPER IF EXISTS ... CASCADE``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_server_factor_extension import (
    CreateServerFactorExtensionCase,
    _present_failure_pair,
)
from .create_server_factor_loop import (
    CreateServerFactorCase,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/"
    "server/create_server.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/"
    "server/create_server.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class CreateServerFactorRenderError(ValueError):
    """Raised when a CREATE SERVER case cannot be rendered."""


@dataclass(frozen=True)
class CreateServerFactorWitness:
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
    ext: CreateServerFactorExtensionCase,
) -> CreateServerFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get(
            "target_action", "create_server"
        )
    return CreateServerFactorCase(
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
    case: CreateServerFactorCase
    | CreateServerFactorExtensionCase,
) -> CreateServerFactorCase:
    if isinstance(case, CreateServerFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateServerFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _server_name(a: dict[str, str], p: str) -> str:
    """The server identifier in CREATE SERVER."""

    shape = a.get("server_name_shape", "simple_name")
    if shape == "quoted_name":
        return f'"{p}Mixed Srv"'
    if shape == "reserved_word_name":
        return f'"{p}select"'
    return f"{p}srv"


def _server_name_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    shape = a.get("server_name_shape", "simple_name")
    if shape == "quoted_name":
        return f"{p}Mixed Srv"
    if shape == "reserved_word_name":
        return f"{p}select"
    return f"{p}srv"


def _fdw_name(a: dict[str, str], p: str) -> str:
    """The FDW identifier in CREATE SERVER."""

    shape = a.get("fdw_name_shape", "existing_fdw_name")
    if shape == "nonexistent_fdw_name":
        return f"{p}missing_fdw"
    return f"{p}fdw"


def _fdw_name_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for FDW oracle queries."""

    shape = a.get("fdw_name_shape", "existing_fdw_name")
    if shape == "nonexistent_fdw_name":
        return f"{p}missing_fdw"
    return f"{p}fdw"


def _if_not_exists_sql(a: dict[str, str]) -> str:
    """The IF NOT EXISTS clause fragment."""

    ifne = a.get("if_not_exists_clause", "without_if_not_exists")
    if ifne == "with_if_not_exists":
        return "IF NOT EXISTS"
    return ""


def _type_version_sql(a: dict[str, str], p: str) -> str:
    """The TYPE / VERSION clause fragment."""

    tv = a.get("type_version_clause", "omitted")
    if tv == "type_only":
        return f"TYPE '{p}srvtype'"
    if tv == "version_only":
        return f"VERSION '{p}srvver'"
    if tv == "both_type_and_version":
        return f"TYPE '{p}srvtype' VERSION '{p}srvver'"
    return ""


def _options_sql(a: dict[str, str], p: str) -> str:
    """The OPTIONS clause fragment."""

    oc = a.get("options_clause", "omitted")
    ov = a.get("option_value_shape", "valid_option_value")
    fvr = a.get("fdw_validator_rejection", "none")
    if oc == "omitted":
        return ""
    if fvr == "validator_rejects_invalid_option":
        return f"OPTIONS ('{p}bad_opt' 'val')"
    val = "" if ov == "empty_option_value" else f"{p}optval"
    if oc == "single_option":
        return f"OPTIONS ('{p}opt1' '{val}')"
    if oc == "multiple_options":
        return (
            f"OPTIONS ('{p}opt1' '{val}', "
            f"'{p}opt2' '{val}')"
        )
    return ""


def _is_duplicate(a: dict[str, str]) -> bool:
    return a.get("server_identity") in ("exists", "quoted_duplicate")


def _fdw_exists(a: dict[str, str]) -> bool:
    return a.get("fdw_dependency") == "existing_fdw"


def _is_validator_rejection(a: dict[str, str]) -> bool:
    return (
        a.get("fdw_validator_rejection")
        == "validator_rejects_invalid_option"
    )


def _is_non_superuser(a: dict[str, str]) -> bool:
    return a.get("executor_privilege") == "non_superuser"


def _effective_role(a: dict[str, str], p: str) -> str:
    if _is_non_superuser(a):
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    if _is_non_superuser(a):
        roles.append(f"{p}actor")
    return tuple(roles)


def _probe_select(
    case: CreateServerFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for error_assertion."""

    mode = a.get("verification_mode", "pg_foreign_server_catalog")
    if mode == "error_assertion":
        return None

    server_lit = _server_name_literal(a, p)
    si = a.get("server_identity", "not_exists")
    # For duplicate cases, the pre-existing server is in the catalog
    # regardless of outcome.  For other success cases, the server was
    # created.  For other failure cases, the server was NOT created.
    if si in ("exists", "quoted_duplicate"):
        cmp_op = ">"
    elif case.outcome == "success":
        cmp_op = ">"
    else:
        cmp_op = "="
    return (
        f"SELECT count(*) {cmp_op} 0 AS server_state "
        f"FROM pg_catalog.pg_foreign_server "
        f"WHERE srvname = '{server_lit}' "
        f"ORDER BY count(*);"
    )


def _build_target(a: dict[str, str], p: str) -> str:
    """The primary CREATE SERVER statement."""

    server = _server_name(a, p)
    fdw = _fdw_name(a, p)
    parts = ["CREATE SERVER"]
    ifne = _if_not_exists_sql(a)
    if ifne:
        parts.append(ifne)
    parts.append(server)
    tv = _type_version_sql(a, p)
    if tv:
        parts.append(tv)
    parts.append("FOREIGN DATA WRAPPER")
    parts.append(fdw)
    options = _options_sql(a, p)
    if options:
        parts.append(options)
    return " ".join(parts) + ";"


def _resolve_case(case: CreateServerFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix

    setup: list[str] = []
    locus = "target.create_server"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    server = _server_name(a, p)
    fdw = _fdw_name(a, p)

    # --- role fixtures -----------------------------------------------
    if effective == f"{p}actor":
        setup.append(
            f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;"
        )
        locus = "fixture.privilege_state"

    # --- validator function fixture (fdw_validator_rejection) -------
    if _is_validator_rejection(a):
        validator = f"{p}validator"
        setup.append(
            f"CREATE FUNCTION {validator}(text[], oid) "
            f"RETURNS void "
            f"LANGUAGE plpgsql AS $$ "
            f"BEGIN RAISE EXCEPTION 'invalid option'; "
            f"END; $$;"
        )
        locus = "fixture.validator_function"

    # --- FDW fixture -------------------------------------------------
    if _fdw_exists(a):
        if _is_validator_rejection(a):
            validator = f"{p}validator"
            setup.append(
                f"CREATE FOREIGN DATA WRAPPER {fdw} "
                f"VALIDATOR {validator};"
            )
        else:
            setup.append(
                f"CREATE FOREIGN DATA WRAPPER {fdw};"
            )
        locus = "fixture.fdw"

    # --- pre-existing server for duplicate --------------------------
    if _is_duplicate(a):
        setup.append(
            f"CREATE SERVER {server} "
            f"FOREIGN DATA WRAPPER {fdw};"
        )
        locus = "fixture.duplicate_server"

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
    server_drops: list[str] = [
        f"DROP SERVER IF EXISTS {server} CASCADE;"
    ]
    fdw_drops: list[str] = [
        f"DROP FOREIGN DATA WRAPPER IF EXISTS {fdw} CASCADE;"
    ]
    validator_drops: list[str] = []
    if _is_validator_rejection(a):
        validator_drops.append(
            f"DROP FUNCTION IF EXISTS {p}validator(text[], oid);"
        )

    role_drops = [
        statement
        for role in roles
        for statement in (
            f"DROP OWNED BY {role} CASCADE;",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    # pre_cleanup: server, FDW, functions, roles
    pre_cleanup: list[str] = []
    pre_cleanup.extend(server_drops)
    pre_cleanup.extend(fdw_drops)
    pre_cleanup.extend(validator_drops)
    pre_cleanup.extend(role_drops)
    if not pre_cleanup:
        pre_cleanup.append(
            "SELECT 1 AS residual_check_no_objects;"
        )

    # cleanup: RESET ROLE, server, FDW, functions, roles
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(server_drops)
    cleanup.extend(fdw_drops)
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


def resolve_create_server_factor_witness(
    case: CreateServerFactorCase
    | CreateServerFactorExtensionCase,
    repository_root: Path,
) -> CreateServerFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateServerFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_create_server(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(
            r"(?im)^CREATE\s+SERVER\b",
            region,
        )
    )


def _header(case: CreateServerFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE SERVER "
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


def render_create_server_factor_case(
    case: CreateServerFactorCase
    | CreateServerFactorExtensionCase,
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
        "-- 3. 执行唯一获得覆盖信用的 CREATE SERVER。"
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
    case: CreateServerFactorCase
    | CreateServerFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_server_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_server_factor_programs(
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
    "CreateServerFactorRenderError",
    "CreateServerFactorWitness",
    "count_primary_create_server",
    "generate_create_server_factor_programs",
    "render_create_server_factor_case",
    "resolve_create_server_factor_witness",
]
