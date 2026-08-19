"""Render complete PostgreSQL 18.4 ALTER POLICY factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file
assembled from a single :func:`_resolve_case` plan, so the byte-level witness
validator (which re-renders and compares) can never diverge from the bytes
actually written.

ALTER POLICY is a table-attached RLS DDL: it alters a policy ON a table (it
does not alter the table itself).  The fixture therefore creates a TABLE
plus a POLICY on it (for success / privilege / role failures); a
missing-table case omits the table (42P01); a missing-policy case creates
the table but not the policy (42704).  ``rls_not_enabled`` is NOT a failure
(the policy definition can be altered with RLS off), so the RLS state is a
fixture line, not an error axis.

The privilege boundary (``privilege_level = non_owner`` → 42501) has no
SESSION_USER no-op-transfer carve-out (ALTER POLICY has no ``OWNER TO``
clause): the boundary fires simply for a non-owner, armed via ``SET ROLE``
to a non-superuser actor role.  ``table_owner`` exercises the non-superuser
owner path (a separate owner role owns the table + ``SET ROLE`` to it).

All fixture decisions are read from the frozen *assignment* dict, so
extension cases — whose primary is a synthetic attribution pair — render
identically to a baseline case carrying the same factor assignment.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .alter_policy_factor_extension import (
    AlterPolicyFactorExtensionCase,
    _present_failure_pair,
)
from .alter_policy_factor_loop import (
    AlterPolicyFactorCase,
    AlterPolicyFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/policy/"
    "alter_policy.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/policy/"
    "alter_policy.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_DEFAULT_SCHEMA = "public"


def _synthetic_case(
    ext: AlterPolicyFactorExtensionCase,
) -> AlterPolicyFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    elif ext.consumer_action_id == "rename" and ext.outcome == "success":
        factor_key = "new_name_shape"
        factor_value = assignment["new_name_shape"]
    else:
        factor_key = "alter_action"
        factor_value = assignment["alter_action"]
    return AlterPolicyFactorCase(
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
    case: AlterPolicyFactorCase | AlterPolicyFactorExtensionCase,
) -> AlterPolicyFactorCase:
    if isinstance(case, AlterPolicyFactorExtensionCase):
        return _synthetic_case(case)
    return case


class AlterPolicyFactorRenderError(ValueError):
    """Raised when an ALTER POLICY case cannot be rendered."""


@dataclass(frozen=True)
class AlterPolicyFactorWitness:
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


def _baseline(case: AlterPolicyFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _base_table(p: str) -> str:
    return f"{p}tbl"


def _base_policy(p: str) -> str:
    return f"{p}pol"


def _new_policy_name(p: str) -> str:
    return f"{p}pol_new"


def _dup_policy_name(p: str) -> str:
    return f"{p}pol_dup"


def _actor_role(p: str) -> str:
    return f"{p}actor"


def _owner_role(p: str) -> str:
    return f"{p}owner"


def _extra_role(p: str, n: int) -> str:
    return f"{p}role{n}"


def _policy_ref(a: dict[str, str], p: str) -> str:
    """The policy name inside ALTER POLICY."""

    shape = a.get("policy_name_shape", "simple_id")
    if shape == "quoted_id":
        return f'"{_base_policy(p)}"'
    if shape == "existing_name":
        return f"{p}pol_ex"
    if shape == "nonexistent_name":
        return f"{p}no_such_policy"
    return _base_policy(p)


def _policy_fixture_name(a: dict[str, str], p: str) -> str:
    """The concrete policy name the fixture CREATEs (plain identifier)."""

    shape = a.get("policy_name_shape", "simple_id")
    if shape == "existing_name":
        return f"{p}pol_ex"
    if shape == "nonexistent_name":
        return _base_policy(p)  # created for the duplicate-name partner only
    return _base_policy(p)


def _table_ref(a: dict[str, str], p: str) -> str:
    """The table name inside ALTER POLICY ... ON."""

    shape = a.get("table_name_shape", "simple_id")
    if shape == "quoted_id":
        return f'"{_base_table(p)}"'
    if shape == "schema_qualified":
        return f"{_DEFAULT_SCHEMA}.{_base_table(p)}"
    if shape == "nonexistent_table":
        return f"{p}no_such_table"
    return _base_table(p)


def _new_name_ref(a: dict[str, str], p: str) -> str:
    """The RENAME TO target name (may be invalid/duplicate)."""

    shape = a.get("new_name_shape", "simple_id")
    if shape == "quoted_id":
        return f'"{_new_policy_name(p)}"'
    if shape == "duplicate_name":
        return _dup_policy_name(p)
    if shape == "invalid_name":
        # An unquoted identifier containing a hyphen tokenises as
        # <id> - <id>, surfacing 42601 (syntax_error).
        return f"{p}pol-bad"
    return _new_policy_name(p)


def _role_target_clause(a: dict[str, str], p: str) -> str:
    """The TO clause role list for modify_roles."""

    value = a.get("role_target", "single_role")
    if value == "CURRENT_ROLE":
        return "CURRENT_ROLE"
    if value == "CURRENT_USER":
        return "CURRENT_USER"
    if value == "PUBLIC":
        return "PUBLIC"
    if value == "SESSION_USER":
        return "SESSION_USER"
    if value == "multiple_roles":
        return f"{_extra_role(p, 1)}, {_extra_role(p, 2)}"
    return _extra_role(p, 1)  # single_role


def _table_present(a: dict[str, str]) -> bool:
    """Whether the fixture creates the target table."""

    if a.get("table_name_shape") == "nonexistent_table":
        return False
    if a.get("table_existence") == "table_not_exists":
        return False
    if a.get("nonexistent_table") == "table_missing":
        return False
    return True


def _policy_present(case: AlterPolicyFactorCase, a: dict[str, str]) -> bool:
    """Whether the fixture creates the target policy (probe asserts presence)."""

    if case.kind == "RISK":
        return True
    if a.get("object_state") == "not_exists":
        return False
    if not _table_present(a):
        return False
    if a.get("policy_name_shape") == "nonexistent_name":
        return False
    if a.get("policy_existence") == "policy_not_exists":
        return False
    if a.get("nonexistent_policy") == "policy_missing":
        return False
    return True


def _effective_role(
    case: AlterPolicyFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target ALTER POLICY runs."""

    level = a.get("privilege_level", "superuser")
    if level == "non_owner":
        return _actor_role(p)
    if level == "table_owner":
        return _owner_role(p)
    return ""


def _rls_enable_line(a: dict[str, str], p: str) -> str | None:
    """Fixture line enabling RLS when rls_enabled = rls_enabled."""

    if a.get("rls_enabled") == "rls_enabled" and _table_present(a):
        return f"ALTER TABLE {_table_ref(a, p)} ENABLE ROW LEVEL SECURITY;"
    return None


def _action_target_sql(
    case: AlterPolicyFactorCase, a: dict[str, str], p: str
) -> str:
    """The ALTER POLICY statement for the case's consumer action."""

    pol = _policy_ref(a, p)
    tbl = _table_ref(a, p)
    action = case.consumer_action_id
    if action == "rename":
        return f"ALTER POLICY {pol} ON {tbl} RENAME TO {_new_name_ref(a, p)};"
    # modify branch: each action always renders its signature clause so the
    # action + its sub-axis are byte-observable (omitted restates the
    # original expression; new sets a fresh one).
    if action == "modify_roles":
        return f"ALTER POLICY {pol} ON {tbl} TO {_role_target_clause(a, p)};"
    if action == "modify_using":
        using = "true" if a.get("using_expression") == "new_expression" else "false"
        return f"ALTER POLICY {pol} ON {tbl} USING ({using});"
    if action == "modify_with_check":
        check = "true" if a.get("with_check_expression") == "new_expression" else "false"
        return f"ALTER POLICY {pol} ON {tbl} WITH CHECK ({check});"
    if action == "modify_combined":
        return (
            f"ALTER POLICY {pol} ON {tbl} TO PUBLIC "
            "USING (true) WITH CHECK (true);"
        )
    raise AlterPolicyFactorRenderError(f"unknown consumer action: {action}")


def _probe_policy_name(
    case: AlterPolicyFactorCase, a: dict[str, str], p: str
) -> str:
    """The policy name the catalog oracle queries.

    A successful RENAME moves the policy to its new name, so the presence
    oracle must query the new name.  An absent-target case (no table / no
    policy / object_state=not_exists) must query the *targeted* name (which
    is missing) to assert its absence, not the fixture-partner name.
    """

    if case.consumer_action_id == "rename" and case.outcome == "success":
        return _new_policy_name(p)
    if not _policy_present(case, a):
        return _policy_ref(a, p)
    return _policy_fixture_name(a, p)


def _probe_select(
    case: AlterPolicyFactorCase, a: dict[str, str], p: str
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only error_assertion."""

    mode = a.get("verification_mode", "catalog_query_pg_policy")
    if mode == "error_assertion":
        return None
    present = _policy_present(case, a)
    name = _probe_policy_name(case, a, p)
    comparator = "> 0" if present else "= 0"
    if mode == "rls_behavior_test":
        alias = "rls_behavior_policy_present" if present else "rls_behavior_policy_absent"
    else:
        alias = "catalog_policy_present" if present else "catalog_policy_absent"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_policy "
        f"WHERE polname = '{name}' "
        "ORDER BY count(*) LIMIT 1;"
    )


def _role_fixtures(
    case: AlterPolicyFactorCase, a: dict[str, str], p: str
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return (create_role_lines, drop_role_lines) for the case."""

    creates: list[str] = []
    drops: list[str] = []
    level = a.get("privilege_level", "superuser")
    if level == "non_owner":
        creates.append(f"CREATE ROLE {_actor_role(p)} LOGIN NOSUPERUSER;")
        drops.append(f"DROP ROLE IF EXISTS {_actor_role(p)};")
    elif level == "table_owner":
        creates.append(f"CREATE ROLE {_owner_role(p)} LOGIN NOSUPERUSER;")
        drops.append(f"DROP ROLE IF EXISTS {_owner_role(p)};")
    action = case.consumer_action_id
    if action == "modify_roles":
        value = a.get("role_target", "single_role")
        if value == "multiple_roles":
            for n in (1, 2):
                creates.append(f"CREATE ROLE {_extra_role(p, n)} LOGIN;")
                drops.append(f"DROP ROLE IF EXISTS {_extra_role(p, n)};")
        elif value not in ("CURRENT_ROLE", "CURRENT_USER", "PUBLIC", "SESSION_USER"):
            creates.append(f"CREATE ROLE {_extra_role(p, 1)} LOGIN;")
            drops.append(f"DROP ROLE IF EXISTS {_extra_role(p, 1)};")
    return tuple(creates), tuple(drops)


def _resolve_case(case: AlterPolicyFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    action = case.consumer_action_id
    table_present = _table_present(a)
    policy_present = _policy_present(case, a)

    setup: list[str] = []
    locus = "target.policy"

    role_creates, role_drops = _role_fixtures(case, a, p)

    # --- role fixtures -------------------------------------------------
    setup.extend(role_creates)

    # --- the target table + policy fixture ----------------------------
    if not table_present:
        setup.append("SELECT 1 AS target_table_intentionally_absent;")
        locus = "fixture.object_state"
    else:
        setup.append(f"CREATE TABLE {_table_ref(a, p)} AS SELECT 1 AS c;")
        if level_owner := (
            a.get("privilege_level") == "table_owner"
        ):
            setup.append(
                f"ALTER TABLE {_table_ref(a, p)} OWNER TO {_owner_role(p)};"
            )
        if policy_present:
            pol_name = _policy_fixture_name(a, p)
            # The original policy carries USING (false) WITH CHECK (false)
            # so the modify_using / modify_with_check "omitted = restate
            # original" path keeps the original expression verbatim.
            setup.append(
                f"CREATE POLICY {pol_name} ON {_table_ref(a, p)} "
                "FOR SELECT TO PUBLIC USING (false) WITH CHECK (false);"
            )
            if action == "rename" and a.get("new_name_shape") == "duplicate_name":
                setup.append(
                    f"CREATE POLICY {_dup_policy_name(p)} "
                    f"ON {_table_ref(a, p)} FOR SELECT TO PUBLIC "
                    "USING (false) WITH CHECK (false);"
                )
        rls_line = _rls_enable_line(a, p)
        if rls_line is not None:
            setup.append(rls_line)
        if level_owner:
            setup.append(f"SET ROLE {_owner_role(p)};")
            locus = "fixture.privilege_state"

    # --- arm the effective role (superuser is the default) -------------
    effective = _effective_role(case, a, p)
    if effective and effective != _owner_role(p):
        setup.append(f"SET ROLE {effective};")
        locus = "fixture.privilege_state"

    # --- the primary target statement ---------------------------------
    target = _action_target_sql(case, a, p)

    if case.kind == "RISK":
        setup.append("BEGIN;")
        locus = "target.transaction_boundary"

    # --- oracle / SQLSTATE assertion ------------------------------------
    assert_lines: list[str] = []
    if effective or a.get("privilege_level") == "table_owner":
        assert_lines.append("RESET ROLE;")
    if case.kind == "RISK":
        assert_lines.append(
            "COMMIT;" if case.factor_value == "commit" else "ROLLBACK;"
        )
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    probe = _probe_select(case, a, p)
    if probe is not None:
        assert_lines.append(probe)

    # --- cleanup construction ------------------------------------------
    drop_mode = a.get("cleanup_mode", "drop_policy")
    cleanup: list[str] = []
    if table_present:
        if drop_mode == "disable_rls_and_drop_policy":
            cleanup.append(
                f"ALTER TABLE IF EXISTS {_table_ref(a, p)} "
                "DISABLE ROW LEVEL SECURITY;"
            )
        if drop_mode in ("drop_policy", "revert_rename", "disable_rls_and_drop_policy"):
            cleanup.append(
                f"DROP POLICY IF EXISTS {_policy_fixture_name(a, p)} "
                f"ON {_table_ref(a, p)};"
            )
        if drop_mode == "revert_rename" and action == "rename" and case.outcome == "success":
            cleanup.append(
                f"ALTER POLICY IF EXISTS {_new_policy_name(p)} "
                f"ON {_table_ref(a, p)} RENAME TO {_policy_fixture_name(a, p)};"
            )
            cleanup.append(
                f"DROP POLICY IF EXISTS {_new_policy_name(p)} "
                f"ON {_table_ref(a, p)};"
            )
        if drop_mode == "revert_rename" and a.get("new_name_shape") == "duplicate_name":
            cleanup.append(
                f"DROP POLICY IF EXISTS {_dup_policy_name(p)} "
                f"ON {_table_ref(a, p)};"
            )
    if drop_mode == "drop_table" or not table_present:
        cleanup.append(f"DROP TABLE IF EXISTS {_table_ref(a, p)} CASCADE;")
    else:
        cleanup.append(f"DROP TABLE IF EXISTS {_table_ref(a, p)} CASCADE;")
    cleanup.extend(role_drops)
    if not cleanup:
        cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # --- pre-cleanup (section 1, re-runnable) -------------------------
    pre_cleanup: list[str] = [f"DROP TABLE IF EXISTS {_table_ref(a, p)} CASCADE;"]
    pre_cleanup.extend(role_drops)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

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


def resolve_alter_policy_factor_witness(
    case: AlterPolicyFactorCase | AlterPolicyFactorExtensionCase,
    repository_root: Path,
) -> AlterPolicyFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return AlterPolicyFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_alter_policy(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(re.findall(r"(?im)^\s*ALTER\s+POLICY\b", region))


def _header(case: AlterPolicyFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : ALTER POLICY {case.factor_key}={case.factor_value}",
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


def render_alter_policy_factor_case(
    case: AlterPolicyFactorCase | AlterPolicyFactorExtensionCase,
    repository_root: Path,
) -> str:
    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地表和策略以及因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信心的 ALTER POLICY。")
    lines.append(_PRIMARY_BEGIN)
    lines.append(resolved.target_fragment)
    lines.append(_PRIMARY_END)
    lines.append("\\set target_sqlstate :SQLSTATE")
    lines.append("\\echo PGCF_TARGET_SQLSTATE=:target_sqlstate")
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 4. 验证 SQLSTATE、目录状态和行级安全策略行为。")
    lines.extend(resolved.assert_lines)
    lines.append("-- 5. 清理全部本编号对象。")
    lines.extend(resolved.cleanup_lines)
    text = "\n".join(lines)
    if not text.endswith("\n"):
        text += "\n"
    return text


def generate_alter_policy_factor_programs(
    baseline_plan: AlterPolicyFactorLoopPlan,
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


def _write_program(
    case: AlterPolicyFactorCase | AlterPolicyFactorExtensionCase,
    out: Path,
) -> None:
    text = render_alter_policy_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "AlterPolicyFactorRenderError",
    "AlterPolicyFactorWitness",
    "count_primary_alter_policy",
    "generate_alter_policy_factor_programs",
    "render_alter_policy_factor_case",
    "resolve_alter_policy_factor_witness",
]
