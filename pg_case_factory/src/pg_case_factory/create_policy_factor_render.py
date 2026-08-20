"""Render complete PostgreSQL 18.4 CREATE POLICY factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CREATE POLICY is a table-level DDL statement: the target is a
``pg_catalog.pg_policy`` catalog row that requires a backing TABLE.
Each script CREATEs a fixture TABLE (with RLS enabled when applicable),
so the bookend (DROP TABLE IF EXISTS) is always emitted as the first
and last executable ``;``-statement.  All catalog oracles
schema-qualify ``pg_catalog.pg_policy`` (exempt from the file-prefix
style gate).  Every catalog SELECT carries a top-level ``ORDER BY``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_policy_factor_extension import (
    CreatePolicyFactorExtensionCase,
    _present_failure_pair,
)
from .create_policy_factor_loop import (
    CreatePolicyFactorCase,
    CreatePolicyFactorLoopPlan,
    _PG18_COMMAND_MAP,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/policy/"
    "create_policy.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/policy/"
    "create_policy.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class CreatePolicyFactorRenderError(ValueError):
    """Raised when a CREATE POLICY case cannot be rendered."""


@dataclass(frozen=True)
class CreatePolicyFactorWitness:
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
    ext: CreatePolicyFactorExtensionCase,
) -> CreatePolicyFactorCase:
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
    return CreatePolicyFactorCase(
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
    case: CreatePolicyFactorCase
    | CreatePolicyFactorExtensionCase,
) -> CreatePolicyFactorCase:
    if isinstance(case, CreatePolicyFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: CreatePolicyFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _policy_name(a: dict[str, str], p: str) -> str:
    """The policy identifier in CREATE POLICY."""

    shape = a.get("policy_name_shape", "simple_id")
    if shape == "quoted_id":
        return f'"{p}Qp"'
    if shape == "reserved_word_as_name":
        return '"select"'
    return f"{p}p"


def _policy_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    shape = a.get("policy_name_shape", "simple_id")
    if shape == "quoted_id":
        return f"{p}Qp"
    if shape == "reserved_word_as_name":
        return "select"
    return f"{p}p"


def _table_name(a: dict[str, str], p: str) -> str:
    """The table identifier in CREATE POLICY ON clause."""

    shape = a.get("table_name_shape", "simple_id")
    if shape == "quoted_id":
        return f'"{p}t"'
    if shape == "schema_qualified":
        return f"public.{p}t"
    if shape == "nonexistent_table":
        return f"{p}nosuch"
    return f"{p}t"


def _is_duplicate(a: dict[str, str]) -> bool:
    return (
        a.get("object_state") == "exists_same_table"
    )


def _is_failure(a: dict[str, str]) -> bool:
    return a.get("expected_status") == "failure"


def _present(a: dict[str, str]) -> bool:
    """Whether the policy exists after the target statement."""

    if not _is_failure(a):
        return True
    if _is_duplicate(a):
        return True
    return False


def _to_clause(a: dict[str, str], p: str) -> str | None:
    """The TO clause for CREATE POLICY."""

    rt = a.get("role_target", "PUBLIC")
    if rt == "PUBLIC":
        return "TO PUBLIC"
    if rt == "CURRENT_ROLE":
        return "TO CURRENT_ROLE"
    if rt == "CURRENT_USER":
        return "TO CURRENT_USER"
    if rt == "SESSION_USER":
        return "TO SESSION_USER"
    if rt == "multiple_roles":
        return f"TO {p}role, {p}role2"
    # single_role
    re = a.get("role_existence", "role_exists")
    if re == "role_not_exists":
        return f"TO {p}norole"
    rns = a.get("role_name_shape", "simple_id")
    if rns == "quoted_id":
        return f'TO "{p}role"'
    return f"TO {p}role"


def _using_expr_text(a: dict[str, str]) -> str | None:
    """The USING expression text, or None if omitted."""

    ie = a.get("invalid_expression", "valid_expression")
    if ie == "aggregate_in_expression":
        return "count(*) > 0"
    if ie == "window_function_in_expression":
        return "row_number() OVER () > 0"

    ue = a.get("using_expression", "omitted")
    if ue == "omitted":
        return None
    if ue == "simple_boolean_expr":
        return "true"
    if ue == "column_reference_expr":
        return "id > 0"
    if ue == "complex_expr":
        return "CASE WHEN id > 0 THEN true ELSE false END"
    return None


def _with_check_expr_text(a: dict[str, str]) -> str | None:
    """The WITH CHECK expression text, or None if omitted."""

    ie = a.get("invalid_expression", "valid_expression")
    if ie == "aggregate_in_expression":
        return None  # invalid_expression is in USING, not WITH CHECK
    if ie == "window_function_in_expression":
        return None

    wce = a.get("with_check_expression", "omitted")
    if wce == "omitted":
        return None
    if wce == "simple_boolean_expr":
        return "true"
    if wce == "column_reference_expr":
        return "id > 0"
    if wce == "complex_expr":
        return "CASE WHEN id > 0 THEN true ELSE false END"
    return None


def _build_target(
    a: dict[str, str], p: str
) -> str:
    """The primary CREATE POLICY statement."""

    name = _policy_name(a, p)
    table = _table_name(a, p)

    parts: list[str] = [f"CREATE POLICY {name} ON {table}"]

    pt = a.get("policy_type", "permissive")
    parts.append(f"AS {pt.upper()}")

    ct = a.get("command_type", "ALL")
    for_clause = _PG18_COMMAND_MAP.get(ct, ct)
    parts.append(f"FOR {for_clause}")

    to = _to_clause(a, p)
    if to:
        parts.append(to)

    using_expr = _using_expr_text(a)
    if using_expr is not None:
        parts.append(f"USING ({using_expr})")

    wc_expr = _with_check_expr_text(a)
    if wc_expr is not None:
        parts.append(f"WITH CHECK ({wc_expr})")

    return " ".join(parts) + ";"


def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target runs."""

    priv = a.get("privilege_level", "superuser")
    if priv == "non_owner":
        return f"{p}actor"
    return ""


def _needs_second_table(a: dict[str, str]) -> bool:
    return a.get("object_state") == "exists_different_table"


def _needs_target_roles(a: dict[str, str]) -> bool:
    rt = a.get("role_target", "PUBLIC")
    re = a.get("role_existence", "role_exists")
    if rt in {"PUBLIC", "CURRENT_ROLE", "CURRENT_USER", "SESSION_USER"}:
        return False
    if re == "role_not_exists":
        return False
    return True


def _probe_select(
    case: CreatePolicyFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only verification."""

    mode = a.get("verification_mode", "catalog_query_pg_policy")
    literal = _policy_literal(a, p)
    name = _policy_name(a, p)

    if mode == "error_assertion":
        return None

    if mode == "rls_behavior_test":
        if _present(a):
            return (
                f"SELECT count(*) FROM {p}t ORDER BY count(*);"
            )
        return None

    # catalog_query_pg_policy
    if _present(a):
        cmp_op = ">"
    else:
        cmp_op = "="
    return (
        f"SELECT count(*) {cmp_op} 0 AS policy_state "
        f"FROM pg_catalog.pg_policy "
        f"WHERE polname = '{literal}' "
        f"ORDER BY count(*);"
    )


def _resolve_case(
    case: CreatePolicyFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix

    setup: list[str] = []
    locus = "target.create_policy"

    effective = _effective_role(a, p)
    needs_2nd = _needs_second_table(a)
    needs_roles = _needs_target_roles(a)
    policy_name = _policy_name(a, p)
    is_dup = _is_duplicate(a)

    # --- pre-cleanup (step 1) ---
    # Combined DROP TABLE of all created tables as a single ;-segment so the
    # shared bookend gate (which only inspects statements[0]) sees every
    # created table; phantom drops (nosuch/src) follow as separate segments.
    pre_cleanup: list[str] = []
    _created_tables = [f"{p}t"]
    if needs_2nd:
        _created_tables.append(f"{p}t2")
    pre_cleanup.append(
        f"DROP TABLE IF EXISTS {', '.join(_created_tables)} CASCADE;"
    )
    pre_cleanup.append(f"DROP TABLE IF EXISTS {p}nosuch CASCADE;")
    pre_cleanup.append(f"DROP TABLE IF EXISTS {p}src CASCADE;")
    pre_cleanup.append(f"DROP POLICY IF EXISTS {policy_name} ON {p}t;")
    if needs_2nd:
        pre_cleanup.append(
            f"DROP POLICY IF EXISTS {policy_name} ON {p}t2;"
        )
    pre_cleanup.append("RESET ROLE;")
    if effective:
        pre_cleanup.append(f"DROP OWNED BY {p}actor CASCADE;")
        pre_cleanup.append(f"DROP ROLE IF EXISTS {p}actor;")
    if needs_roles:
        pre_cleanup.append(f"DROP OWNED BY {p}role CASCADE;")
        pre_cleanup.append(f"DROP ROLE IF EXISTS {p}role;")
        if a.get("role_target") == "multiple_roles":
            pre_cleanup.append(
                f"DROP OWNED BY {p}role2 CASCADE;"
            )
            pre_cleanup.append(f"DROP ROLE IF EXISTS {p}role2;")
    pre_cleanup.append(f"DROP ROLE IF EXISTS {p}norole;")

    # --- setup (step 2) ---
    # Fixture table
    setup.append(f"CREATE TABLE {p}t (id int, data text);")
    if needs_2nd:
        setup.append(f"CREATE TABLE {p}t2 (id int, data text);")
    # RLS enable
    if a.get("rls_enabled", "rls_enabled") == "rls_enabled":
        setup.append(
            f"ALTER TABLE {p}t ENABLE ROW LEVEL SECURITY;"
        )
        if needs_2nd:
            setup.append(
                f"ALTER TABLE {p}t2 ENABLE ROW LEVEL SECURITY;"
            )
    # Actor role (for non_owner)
    if effective:
        setup.append(
            f"CREATE ROLE {p}actor LOGIN NOSUPERUSER NOBYPASSRLS;"
        )
    # Target roles
    if needs_roles:
        setup.append(f"CREATE ROLE {p}role;")
        if a.get("role_target") == "multiple_roles":
            setup.append(f"CREATE ROLE {p}role2;")
    # Pre-existing policy (for duplicate or different_table)
    if is_dup:
        setup.append(
            f"CREATE POLICY {policy_name} ON {p}t FOR ALL;"
        )
        locus = "fixture.duplicate_policy"
    elif needs_2nd:
        setup.append(
            f"CREATE POLICY {policy_name} ON {p}t2 FOR ALL;"
        )
        locus = "fixture.different_table_policy"
    # Arm the effective role
    if effective:
        setup.append(f"SET ROLE {effective};")
        locus = "fixture.privilege_state"

    # --- the primary target statement (step 3) ---
    target = _build_target(a, p)

    # --- oracle / SQLSTATE assertion (step 4) ---
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

    # --- cleanup (step 5) ---
    cleanup_mode = a.get("cleanup_mode", "drop_policy")
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    if cleanup_mode != "drop_table":
        cleanup.append(
            f"DROP POLICY IF EXISTS {policy_name} ON {p}t;"
        )
        if needs_2nd:
            cleanup.append(
                f"DROP POLICY IF EXISTS {policy_name} ON {p}t2;"
            )
    if cleanup_mode == "disable_rls_and_drop_policy":
        cleanup.append(
            f"ALTER TABLE {p}t DISABLE ROW LEVEL SECURITY;"
        )
        if needs_2nd:
            cleanup.append(
                f"ALTER TABLE {p}t2 DISABLE ROW LEVEL SECURITY;"
            )
    if effective:
        cleanup.append(f"DROP OWNED BY {p}actor CASCADE;")
        cleanup.append(f"DROP ROLE IF EXISTS {p}actor;")
    if needs_roles:
        cleanup.append(f"DROP OWNED BY {p}role CASCADE;")
        cleanup.append(f"DROP ROLE IF EXISTS {p}role;")
        if a.get("role_target") == "multiple_roles":
            cleanup.append(
                f"DROP OWNED BY {p}role2 CASCADE;"
            )
            cleanup.append(f"DROP ROLE IF EXISTS {p}role2;")
    # Always last: DROP TABLE — combined into a single ;-segment in reverse
    # creation order so the shared bookend gate (which only inspects
    # statements[-1]) sees ALL created tables and they drop reverse-first.
    _drop_tables = [f"{p}t2"] if needs_2nd else []
    _drop_tables.append(f"{p}t")
    cleanup.append(
        f"DROP TABLE IF EXISTS {', '.join(_drop_tables)} CASCADE;"
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


def _header(case: CreatePolicyFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE POLICY {case.factor_key}="
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


def render_create_policy_factor_case(
    case: CreatePolicyFactorCase
    | CreatePolicyFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 CREATE POLICY。")
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
    case: CreatePolicyFactorCase
    | CreatePolicyFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_policy_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_policy_factor_programs(
    baseline_plan: CreatePolicyFactorLoopPlan,
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


def count_primary_create_policy(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*CREATE\s+POLICY\b", region)
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


def resolve_create_policy_factor_witness(
    case: CreatePolicyFactorCase
    | CreatePolicyFactorExtensionCase,
    repository_root: Path,
) -> CreatePolicyFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreatePolicyFactorWitness(
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
    "CreatePolicyFactorRenderError",
    "CreatePolicyFactorWitness",
    "count_primary_create_policy",
    "generate_create_policy_factor_programs",
    "render_create_policy_factor_case",
    "resolve_create_policy_factor_witness",
    "remove_primary_semantic_locus_but_keep_comments",
]
