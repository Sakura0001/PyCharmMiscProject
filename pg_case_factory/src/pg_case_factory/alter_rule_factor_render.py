"""Render complete PostgreSQL 18.4 ALTER RULE factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.
The file is assembled from a single :func:`_resolve_case` plan so that the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

BOOKEND: ``ALTER RULE`` with ``table_type=table`` creates a host TABLE, so
``contains_create_table_statement`` is True — the first and last ``;``-
statement must each be ``DROP TABLE IF EXISTS`` naming every created table.
The fixture CREATE TABLE and both bookend DROP TABLE statements use the
audit-normalizable :func:`_table_fixture_name` (a plain or schema-qualified
name); the ALTER RULE target keeps the shape-appropriate :func:`_host_name`
(a quoted lowercase identifier resolves to the same table), so the
``quoted_id`` factor stays byte-observable without breaking the table audit.
For ``table_type=view`` (no CREATE TABLE), the bookend gate is False and
cleanup DROPs the VIEW instead.  For ``table_name_shape=nonexistent_table``
(no table created at all), the bookend is also False.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Sequence

from .alter_rule_factor_extension import (
    AlterRuleFactorExtensionCase,
    _present_failure_pair,
)
from .alter_rule_factor_loop import (
    AlterRuleFactorCase,
    AlterRuleFactorLoopPlan,
    _EXPECTED_BEHAVIOR_VALUES,
)
from .cleanup_bookend import (
    CleanupBookend,
    DropSpec,
    OnDropSpec,
    build_cleanup,
    build_pre_cleanup,
)


_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/rule/"
    "alter_rule.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/rule/"
    "alter_rule.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_RENAME = "branch_rename"

# The placeholder the shared bookend emits when a region would otherwise be
# empty; mirrored from cleanup_bookend._RESIDUAL_SELECT so splicing a real
# statement lets us drop the placeholder without importing a private name.
_RESIDUAL_SELECT = "SELECT 1 AS residual_check_no_objects;"


def _splice_bookend(
    bookend: CleanupBookend,
    lead: Sequence[str] = (),
    tail: Sequence[str] = (),
) -> tuple[str, ...]:
    """Splice non-DROP lead/tail statements into a cleanup bookend.

    ``lead`` (e.g. an ``ALTER RULE ... RENAME TO`` that reverts the target's
    rename) is inserted right after ``RESET ROLE`` (or just after the begin
    marker); ``tail`` (e.g. a ``DROP VIEW`` that must follow the rule drops
    and the role teardown) before the end marker.  A lone residual ``SELECT``
    is dropped because the splice makes the region non-empty.  A no-op when
    both are empty (the helper's output is returned untouched).
    """
    if not lead and not tail:
        return bookend.statements
    stmts = [s for s in bookend.statements if s != _RESIDUAL_SELECT]
    # stmts[0] is CLEANUP_BEGIN, stmts[-1] is CLEANUP_END (helper contract).
    inner = stmts[1:-1]
    lead_at = 1 if inner and inner[0] == "RESET ROLE;" else 0
    new_inner = inner[:lead_at] + list(lead) + inner[lead_at:] + list(tail)
    return (stmts[0], *new_inner, stmts[-1])


def _synthetic_case(
    ext: AlterRuleFactorExtensionCase,
) -> AlterRuleFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    elif ext.outcome == "success":
        rns = assignment.get("rule_name_shape", "simple_id")
        if rns == "_RETURN_special":
            factor_key = "on_select_return_rename"
            factor_value = "_RETURN_rename_breaks_view"
        else:
            factor_key = "rule_name_shape"
            factor_value = rns
    else:
        factor_key = "rule_name_shape"
        factor_value = assignment.get("rule_name_shape", "simple_id")
    return AlterRuleFactorCase(
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
    case: AlterRuleFactorCase | AlterRuleFactorExtensionCase,
) -> AlterRuleFactorCase:
    if isinstance(case, AlterRuleFactorExtensionCase):
        return _synthetic_case(case)
    return case


class AlterRuleFactorRenderError(ValueError):
    """Raised when an ALTER RULE case cannot be rendered."""


@dataclass(frozen=True)
class AlterRuleFactorWitness:
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


def _baseline(case: AlterRuleFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _table_type(a: dict[str, str]) -> str:
    return a.get("table_type", "table")


def _is_view(a: dict[str, str]) -> bool:
    return _table_type(a) == "view"


def _table_missing(a: dict[str, str]) -> bool:
    return a.get("table_name_shape") == "nonexistent_table"


def _rule_missing(a: dict[str, str]) -> bool:
    return a.get("rule_name_shape") == "nonexistent_name"


def _host_name(
    case: AlterRuleFactorCase, a: dict[str, str], p: str
) -> str:
    """The host relation name used inside ALTER RULE and fixtures."""

    shape = a.get("table_name_shape", "simple_id")
    base = f"{p}vhost" if _is_view(a) else f"{p}host"
    if shape == "quoted_id":
        return f'"{base}"'
    if shape == "schema_qualified":
        return f"public.{base}"
    if shape == "nonexistent_table":
        return f"{p}no_such_table" if not _is_view(a) else f"{p}no_such_view"
    return base


def _table_fixture_name(
    case: AlterRuleFactorCase, a: dict[str, str], p: str
) -> str:
    """The bookend-audit-normalizable name for fixture CREATE/DROP.

    The shared ``audit_complete_table_script`` normalizes table identifiers
    with a plain ``[A-Za-z_][A-Za-z0-9_$]*`` grammar that rejects quoted
    names (and stops at the space inside a quoted name), so the fixture
    CREATE TABLE and the bookend DROP TABLE statements emit a plain (or
    schema-qualified) name.  The ALTER RULE target still uses the
    shape-appropriate :func:`_host_name` form — a quoted lowercase identifier
    resolves to the same table as the plain fixture name — so the
    ``quoted_id`` factor stays byte-observable in the target without
    breaking the table audit.
    """

    shape = a.get("table_name_shape", "simple_id")
    base = f"{p}vhost" if _is_view(a) else f"{p}host"
    if shape == "schema_qualified":
        return f"public.{base}"
    if shape == "nonexistent_table":
        return f"{p}no_such_table" if not _is_view(a) else f"{p}no_such_view"
    return base


def _host_base(
    case: AlterRuleFactorCase, a: dict[str, str], p: str
) -> str:
    """The unqualified host name for catalog oracles."""

    shape = a.get("table_name_shape", "simple_id")
    if shape == "quoted_id":
        return f"{p}vhost" if _is_view(a) else f"{p}host"
    if shape == "schema_qualified":
        return f"{p}vhost" if _is_view(a) else f"{p}host"
    if shape == "nonexistent_table":
        return f"{p}no_such_table" if not _is_view(a) else f"{p}no_such_view"
    return f"{p}vhost" if _is_view(a) else f"{p}host"


def _rule_name(
    case: AlterRuleFactorCase, a: dict[str, str], p: str
) -> str:
    """The rule name used inside ALTER RULE."""

    shape = a.get("rule_name_shape", "simple_id")
    if shape == "quoted_id":
        return f'"{p}Mixed Rule"'
    if shape == "_RETURN_special":
        return "_RETURN"
    if shape == "nonexistent_name":
        return f"{p}nonexistent_rule"
    if shape == "existing_name":
        return f"{p}existing_rule"
    return f"{p}rule"


def _new_name(
    case: AlterRuleFactorCase, a: dict[str, str], p: str
) -> str:
    """The new name in RENAME TO."""

    shape = a.get("new_name_shape", "simple_id")
    if shape == "quoted_id":
        return f'"{p}Mixed Name"'
    if shape == "duplicate_name_same_table":
        return f"{p}dup_rule"
    if shape == "invalid_name":
        return "123invalid"
    return f"{p}renamed"


def _effective_role(
    case: AlterRuleFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target ALTER RULE runs."""

    level = a.get("privilege_level", "superuser")
    if level == "table_owner":
        return f"{p}owner"
    if level == "non_owner":
        return f"{p}actor"
    return ""  # superuser


def _role_names(
    case: AlterRuleFactorCase, a: dict[str, str], p: str
) -> tuple[str, ...]:
    """Roles to tear down, ordered members/grantees before the owner role."""

    roles: list[str] = []
    level = a.get("privilege_level", "superuser")
    if level == "non_owner":
        roles.append(f"{p}actor")
    if level in ("table_owner", "non_owner"):
        roles.append(f"{p}owner")
    return tuple(roles)


def _probe_relname(
    case: AlterRuleFactorCase, a: dict[str, str], p: str
) -> str:
    """The relation name the catalog-audit oracle queries."""

    return _host_base(case, a, p)


def _is_return_behavior(a: dict[str, str]) -> bool:
    return (
        a.get("on_select_return_rename") == "_RETURN_rename_breaks_view"
    )


def _probe_select(
    case: AlterRuleFactorCase, a: dict[str, str], p: str
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only error_assertion."""

    mode = a.get("verification_mode", "catalog_query_pg_rewrite")
    relname = _probe_relname(case, a, p)
    new_name = _new_name(case, a, p).strip('"')
    if _is_return_behavior(a):
        return (
            "SELECT count(*) = 0 AS return_rule_renamed "
            "FROM pg_catalog.pg_rewrite AS r "
            "JOIN pg_catalog.pg_class AS c ON r.ev_class = c.oid "
            f"WHERE r.rulename = '_RETURN' AND c.relname = '{relname}' "
            "ORDER BY count(*) LIMIT 1;"
        )
    if mode == "error_assertion":
        return None
    absent = _rule_missing(a) or _table_missing(a)
    if absent:
        return (
            f"SELECT count(*) = 0 AS rule_absent "
            "FROM pg_catalog.pg_rewrite AS r "
            "JOIN pg_catalog.pg_class AS c ON r.ev_class = c.oid "
            f"WHERE r.rulename = '{new_name}' AND c.relname = '{relname}' "
            "ORDER BY count(*) LIMIT 1;"
        )
    return (
        f"SELECT count(*) > 0 AS rule_renamed "
        "FROM pg_catalog.pg_rewrite AS r "
        "JOIN pg_catalog.pg_class AS c ON r.ev_class = c.oid "
        f"WHERE r.rulename = '{new_name}' AND c.relname = '{relname}' "
        "ORDER BY count(*) LIMIT 1;"
    )


def _resolve_case(case: AlterRuleFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    is_view = _is_view(a)
    table_missing = _table_missing(a)
    rule_missing = _rule_missing(a)

    setup: list[str] = []
    locus = "target.rule_rename"

    effective = _effective_role(case, a, p)
    roles = _role_names(case, a, p)
    host = _host_name(case, a, p)
    fixture_name = _table_fixture_name(case, a, p)
    rule = _rule_name(case, a, p)
    new = _new_name(case, a, p)

    # --- role fixtures -------------------------------------------------
    if effective == f"{p}owner":
        setup.append(f"CREATE ROLE {p}owner LOGIN;")
        setup.append("GRANT CREATE ON SCHEMA public TO " + f"{p}owner;")
        setup.append(f"SET ROLE {p}owner;")
        locus = "fixture.privilege_state"
    elif effective == f"{p}actor":
        setup.append(f"CREATE ROLE {p}owner LOGIN;")
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        setup.append("GRANT CREATE ON SCHEMA public TO " + f"{p}owner;")
        setup.append(f"GRANT USAGE ON SCHEMA public TO {p}actor;")
        setup.append(f"SET ROLE {p}owner;")
        locus = "fixture.privilege_state"

    # --- the target relation fixture ----------------------------------
    if table_missing:
        setup.append(
            "SELECT 1 AS target_host_intentionally_absent;"
        )
        locus = "fixture.table_missing"
    elif is_view:
        setup.append(
            f"CREATE VIEW {host} AS SELECT 1 AS {p}col;"
        )
        locus = "fixture.view"
    else:
        setup.append(
            f"CREATE TABLE {fixture_name} ({p}col integer);"
        )
        locus = "fixture.table"

    # --- CREATE RULE (not for _RETURN_special or rule_missing) ----------
    rns = a.get("rule_name_shape", "simple_id")
    if rns != "_RETURN_special" and not rule_missing and not table_missing:
        setup.append(
            f"CREATE RULE {rule} AS ON INSERT TO {host} "
            "DO INSTEAD NOTHING;"
        )

    # --- duplicate-name fixture ----------------------------------------
    if a.get("new_name_shape") == "duplicate_name_same_table":
        dup = _new_name(case, a, p)
        setup.append(
            f"CREATE RULE {dup} AS ON INSERT TO {host} "
            "DO INSTEAD NOTHING;"
        )

    # --- arm the effective non-owner role ------------------------------
    if effective == f"{p}actor":
        setup.append("RESET ROLE;")
        setup.append(f"SET ROLE {p}actor;")

    # --- the primary target statement ---------------------------------
    target = f"ALTER RULE {rule} ON {host} RENAME TO {new};"

    if case.kind == "RISK":
        setup.append("BEGIN;")
        locus = "target.transaction_boundary"

    # --- oracle / SQLSTATE assertion ------------------------------------
    assert_lines: list[str] = []
    if effective:
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

    # --- cleanup construction (idempotent bookends via cleanup_bookend) ---
    # The RULE drop is shape A (ON <relation>) and goes through complex_specs.
    # It is routed to build_cleanup ONLY: in pre-cleanup the host relation
    # drops first (CASCADE removes the rule), so a later DROP RULE ON an
    # already-gone relation errors even with IF EXISTS (Q2).
    drop_mode = a.get("cleanup_mode", "revert_rename")

    # revert_rename renames the rule back; this is a non-DROP cleanup action
    # the helper cannot express, so it is spliced in as a lead statement
    # right after RESET ROLE.
    lead: list[str] = []
    if (
        drop_mode == "revert_rename"
        and case.outcome == "success"
        and not _is_return_behavior(a)
    ):
        lead.append(f"ALTER RULE {new} ON {host} RENAME TO {rule};")

    # shape-A DROP RULE statements (drop_rule mode only).  The original
    # conditions are preserved verbatim: the ``new`` drop is success-gated
    # because the invalid_name factor yields an identifier OnDropSpec cannot
    # validate; the ``rule`` drop stays gated on the container existing
    # (table_missing is structural absence — DROP RULE ON a missing relation
    # errors even with IF EXISTS, so that condition is kept per Q3).
    complex_drops: list[OnDropSpec] = []
    if drop_mode == "drop_rule":
        if case.outcome == "success":
            complex_drops.append(OnDropSpec("RULE", new, host))
        if not rule_missing and not table_missing:
            complex_drops.append(OnDropSpec("RULE", rule, host))
            if a.get("new_name_shape") == "duplicate_name_same_table":
                complex_drops.append(OnDropSpec("RULE", new, host))

    # Host relation teardown.  Tables go through ``tables=`` (DROP TABLE is
    # the bookend anchor: first in pre-cleanup, last in cleanup).  Views
    # cannot use ``tables=`` (the helper emits DROP TABLE) and the helper's
    # ``specs`` slot precedes ``complex_specs`` — which would drop the view
    # before the rules — so the view drop is spliced in last (tail).
    if is_view:
        pre_tables: tuple[str, ...] = ()
        pre_specs: tuple[DropSpec, ...] = (DropSpec("VIEW", host),)
        cln_tables: tuple[str, ...] = ()
        tail = [f"DROP VIEW IF EXISTS {host} CASCADE;"]
    else:
        pre_tables = (fixture_name,)
        pre_specs = ()
        cln_tables = (fixture_name,)
        tail = []

    pre_cleanup_bk = build_pre_cleanup(
        tables=pre_tables,
        specs=pre_specs,
        roles=roles,
    )
    cleanup_bk = build_cleanup(
        tables=cln_tables,
        complex_specs=tuple(complex_drops),
        roles=roles,
        drop_owned=bool(roles),
        reset_role=bool(effective),
    )
    pre_cleanup = list(pre_cleanup_bk.statements)
    cleanup = list(_splice_bookend(cleanup_bk, lead, tail))

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


def resolve_alter_rule_factor_witness(
    case: AlterRuleFactorCase | AlterRuleFactorExtensionCase,
    repository_root: Path,
) -> AlterRuleFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return AlterRuleFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_alter_rule(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(re.findall(r"(?im)^\s*ALTER\s+RULE\b", region))


def _header(case: AlterRuleFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : ALTER RULE {case.factor_key}={case.factor_value}",
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


def render_alter_rule_factor_case(
    case: AlterRuleFactorCase | AlterRuleFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 ALTER RULE。")
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


def generate_alter_rule_factor_programs(
    baseline_plan: AlterRuleFactorLoopPlan,
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
    case: AlterRuleFactorCase | AlterRuleFactorExtensionCase,
    out: Path,
) -> None:
    text = render_alter_rule_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "AlterRuleFactorRenderError",
    "AlterRuleFactorWitness",
    "count_primary_alter_rule",
    "generate_alter_rule_factor_programs",
    "render_alter_rule_factor_case",
    "resolve_alter_rule_factor_witness",
]
