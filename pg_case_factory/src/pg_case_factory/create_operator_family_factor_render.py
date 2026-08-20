"""Render complete PostgreSQL 18.4 CREATE OPERATOR FAMILY factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CREATE OPERATOR FAMILY is a catalog-row DDL statement: the target is a
``pg_catalog.pg_opfamily`` catalog row, not a ``pg_class`` relation.
All catalog oracles schema-qualify ``pg_catalog.pg_opfamily`` (exempt
from the file-prefix style gate).  No case creates a TABLE, so the
bookend (DROP TABLE IF EXISTS) is never emitted.  Every catalog SELECT
carries a top-level ``ORDER BY count(*)`` so the catalog-observability
gate passes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_operator_family_factor_extension import (
    CreateOperatorFamilyFactorExtensionCase,
    _present_failure_pair,
)
from .create_operator_family_factor_loop import (
    CreateOperatorFamilyFactorCase,
    CreateOperatorFamilyFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/operator_family/"
    "create_operator_family.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/operator_family/"
    "create_operator_family.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_INVALID_METHOD = "pgcf_nosucham"
_BOGUS_SCHEMA = "pgcf_noschema"


class CreateOperatorFamilyFactorRenderError(ValueError):
    """Raised when a CREATE OPERATOR FAMILY case cannot be rendered."""


@dataclass(frozen=True)
class CreateOperatorFamilyFactorWitness:
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
    ext: CreateOperatorFamilyFactorExtensionCase,
) -> CreateOperatorFamilyFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_form"
        factor_value = assignment.get(
            "target_form", ext.consumer_action_id
        )
    return CreateOperatorFamilyFactorCase(
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
    case: CreateOperatorFamilyFactorCase
    | CreateOperatorFamilyFactorExtensionCase,
) -> CreateOperatorFamilyFactorCase:
    if isinstance(case, CreateOperatorFamilyFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateOperatorFamilyFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _is_privilege_failure(a: dict[str, str]) -> bool:
    return a.get("privilege_context") == "insufficient_privilege"


def _is_duplicate(a: dict[str, str]) -> bool:
    return a.get("target_object_state") in ("exists", "exists_conflict")


def _is_failure(a: dict[str, str]) -> bool:
    return a.get("expected_status") == "failure"


def _present(a: dict[str, str]) -> bool:
    """Whether the operator family exists after the target statement."""

    if not _is_failure(a):
        return True
    if _is_duplicate(a):
        return True
    return False


def _index_method(a: dict[str, str]) -> str:
    """The USING index_method token in CREATE OPERATOR FAMILY."""

    if a.get("invalid_combination") == "syntax_valid_semantic_error":
        return _INVALID_METHOD
    return a.get("index_method_shape", "btree")


def _opfamily_name(a: dict[str, str], p: str) -> str:
    """The operator family identifier in CREATE/DROP statements."""

    if a.get("dependency_state") == "missing_dependency":
        return f"{_BOGUS_SCHEMA}.{p}opfam"
    shape = a.get("name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f'"{p}QOpfam"'
    if shape == "schema_qualified":
        return f"public.{p}opfam"
    return f"{p}opfam"


def _opfamily_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    if a.get("dependency_state") == "missing_dependency":
        return f"{p}opfam"
    shape = a.get("name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f"{p}QOpfam"
    return f"{p}opfam"


def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target runs."""

    if _is_privilege_failure(a):
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    if _is_privilege_failure(a):
        roles.append(f"{p}actor")
    return tuple(roles)


def _build_target(
    a: dict[str, str], p: str
) -> str:
    """The primary CREATE OPERATOR FAMILY statement."""

    name = _opfamily_name(a, p)
    method = _index_method(a)
    return f"CREATE OPERATOR FAMILY {name} USING {method};"


def _probe_select(
    case: CreateOperatorFamilyFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only verification."""

    mode = a.get("verification_mode", "catalog_query")
    literal = _opfamily_literal(a, p)

    if mode == "error_assertion":
        return None

    cmp_op = ">" if _present(a) else "="
    if mode == "effect_query":
        return (
            f"SELECT count(*) {cmp_op} 0 AS opfamily_effect "
            f"FROM pg_catalog.pg_opfamily opf "
            f"JOIN pg_catalog.pg_am am ON opf.opfmethod = am.oid "
            f"WHERE opf.opfname = '{literal}' "
            f"ORDER BY count(*);"
        )
    # catalog_query
    return (
        f"SELECT count(*) {cmp_op} 0 AS opfamily_state "
        f"FROM pg_catalog.pg_opfamily "
        f"WHERE opfname = '{literal}' "
        f"ORDER BY count(*);"
    )


def _resolve_case(
    case: CreateOperatorFamilyFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix

    setup: list[str] = []
    locus = "target.create_operator_family"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    name = _opfamily_name(a, p)
    method = _index_method(a)

    # --- role fixtures -----------------------------------------------
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- duplicate operator family fixture ----------------------------
    if _is_duplicate(a):
        setup.append(
            f"CREATE OPERATOR FAMILY {name} USING {method};"
        )
        locus = "fixture.duplicate_operator_family"

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
    opfamilies_to_drop: list[str] = [name]

    cleanup_mode = a.get("cleanup_mode", "drop_objects")
    if cleanup_mode == "reset_state":
        opf_drops = [
            f"DROP OPERATOR FAMILY IF EXISTS {n} CASCADE;"
            for n in opfamilies_to_drop
        ]
        cleanup_block: list[str] = []
        if effective:
            cleanup_block.append("RESET ROLE;")
        cleanup_block.extend(opf_drops)
    else:
        opf_drops = [
            f"DROP OPERATOR FAMILY IF EXISTS {n} CASCADE;"
            for n in opfamilies_to_drop
        ]
        cleanup_block = list(opf_drops)

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
        f"DROP OPERATOR FAMILY IF EXISTS {name} CASCADE;"
    )
    pre_cleanup.append("RESET ROLE;")
    for role in roles:
        pre_cleanup.append(f"DROP ROLE IF EXISTS {role};")

    # cleanup: RESET ROLE, opfamilies, roles
    cleanup: list[str] = list(cleanup_block)
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


def _header(case: CreateOperatorFamilyFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE OPERATOR FAMILY {case.factor_key}="
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


def render_create_operator_family_factor_case(
    case: CreateOperatorFamilyFactorCase
    | CreateOperatorFamilyFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 CREATE OPERATOR FAMILY。")
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
    case: CreateOperatorFamilyFactorCase
    | CreateOperatorFamilyFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_operator_family_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_operator_family_factor_programs(
    baseline_plan: CreateOperatorFamilyFactorLoopPlan,
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


def count_primary_create_operator_family(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*CREATE\s+OPERATOR\s+FAMILY\b", region)
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


def resolve_create_operator_family_factor_witness(
    case: CreateOperatorFamilyFactorCase
    | CreateOperatorFamilyFactorExtensionCase,
    repository_root: Path,
) -> CreateOperatorFamilyFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateOperatorFamilyFactorWitness(
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
    "CreateOperatorFamilyFactorRenderError",
    "CreateOperatorFamilyFactorWitness",
    "count_primary_create_operator_family",
    "generate_create_operator_family_factor_programs",
    "render_create_operator_family_factor_case",
    "resolve_create_operator_family_factor_witness",
    "remove_primary_semantic_locus_but_keep_comments",
]
