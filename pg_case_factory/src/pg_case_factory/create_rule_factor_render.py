"""Render complete PostgreSQL 18.4 CREATE RULE factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CREATE RULE operates ON a relation (table or view).  Success-path cases
CREATE the fixture table as setup, so the bookend contract applies:
the FIRST and LAST executable ``;``-statements are each
``DROP TABLE IF EXISTS <all created tables>`` when the case creates one
or more tables.

All catalog oracles schema-qualify ``pg_catalog.*`` (exempt from the
file-prefix style gate) and carry a top-level ``ORDER BY`` so the
catalog-observability gate passes.  Quoted / dotted / reserved rule or
table identifiers appear ONLY in the fenced CREATE RULE target
(which the style gate does not parse); fixtures and catalog queries
always use the plain prefix-derived unqualified name.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .cleanup_bookend import (
    OnDropSpec,
    build_cleanup,
    build_pre_cleanup,
)
from .create_rule_factor_extension import (
    CreateRuleFactorExtensionCase,
    _present_failure_pair,
)
from .create_rule_factor_loop import (
    CreateRuleFactorCase,
    CreateRuleFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/rule/"
    "create_rule.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/rule/"
    "create_rule.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class CreateRuleFactorRenderError(ValueError):
    """Raised when a CREATE RULE case cannot be rendered."""


@dataclass(frozen=True)
class CreateRuleFactorWitness:
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
    ext: CreateRuleFactorExtensionCase,
) -> CreateRuleFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "statement_branch"
        factor_value = "branch_create_rule"
    return CreateRuleFactorCase(
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
    case: CreateRuleFactorCase | CreateRuleFactorExtensionCase,
) -> CreateRuleFactorCase:
    if isinstance(case, CreateRuleFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateRuleFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _is_failure(a: dict[str, str]) -> bool:
    return a.get("expected_status") == "failure"


def _is_duplicate(a: dict[str, str]) -> bool:
    return (
        a.get("object_state") == "exists_same_table_same_event"
        and a.get("or_replace", "absent") == "absent"
    )


def _is_nonexistent_table(a: dict[str, str]) -> bool:
    return a.get("nonexistent_table") == "table_missing"


def _present(a: dict[str, str]) -> bool:
    """Whether the rule exists after the target statement."""

    if not _is_failure(a):
        return True
    if _is_duplicate(a):
        return True
    return False


def _table_plain(a: dict[str, str], p: str) -> str:
    """Plain table or view name for fixtures and cleanup."""
    return f"{p}v" if a.get("table_type") == "view" else f"{p}t"


def _table_ref(a: dict[str, str], p: str) -> str:
    """Table reference in the fenced CREATE RULE target."""
    tns = a.get("table_name_shape", "simple_id")
    base = _table_plain(a, p)
    if tns == "quoted_id":
        return f'"{base}"'
    if tns == "schema_qualified":
        return f"public.{base}"
    if tns == "nonexistent_table":
        return f"{p}nosuch"
    return base


def _rule_name(a: dict[str, str], p: str) -> str:
    """Rule name in the fenced CREATE RULE target."""
    shape = a.get("rule_name_shape", "simple_id")
    if shape == "_RETURN_special_name":
        return "_RETURN"
    if shape == "quoted_id":
        return f'"{p}r"'
    if shape == "reserved_word_as_name":
        return f'"{p}select"'
    return f"{p}r"


def _rule_name_plain(a: dict[str, str], p: str) -> str:
    """Always-plain rule name for cleanup and oracle queries."""
    return f"{p}r"


def _where_clause(a: dict[str, str]) -> str:
    wc = a.get("where_condition", "omitted")
    if wc == "simple_boolean_condition":
        return "WHERE id > 0"
    if wc == "complex_condition":
        return "WHERE id > 0 AND val IS NOT NULL"
    if wc == "new_old_reference_condition":
        et = a.get("event_type", "INSERT")
        if et == "DELETE":
            return "WHERE OLD.id > 0"
        return "WHERE NEW.id > 0"
    return ""


def _command_sql(a: dict[str, str], p: str) -> str:
    cc = a.get("command_content", "INSERT_command")
    t = f"{p}t"
    if cc == "INSERT_command":
        cmd = f"INSERT INTO {t} VALUES (1, 'x')"
        if a.get("on_conflict_incompatibility") == (
            "on_conflict_insert_rule_conflict"
        ):
            cmd += " ON CONFLICT DO NOTHING"
        return cmd
    if cc == "UPDATE_command":
        return f"UPDATE {t} SET val = 'y'"
    if cc == "DELETE_command":
        return f"DELETE FROM {t}"
    if cc == "SELECT_command":
        return f"SELECT id, val FROM {t}"
    if cc == "NOTIFY_command":
        return f"NOTIFY {p}ch"
    return "SELECT 1"


def _do_clause(a: dict[str, str], p: str) -> str:
    ra = a.get("rule_action", "INSTEAD")
    ct = a.get("command_type", "single_command")
    if ra == "NOTHING" or ct == "NOTHING":
        return "DO NOTHING"
    cmd = _command_sql(a, p)
    if ct == "multiple_commands":
        cmd = f"({cmd}; {cmd})"
    if ra == "INSTEAD":
        return f"DO INSTEAD {cmd}"
    if ra == "ALSO":
        return f"DO ALSO {cmd}"
    return f"DO {cmd}"


def _build_target(a: dict[str, str], p: str) -> str:
    """The primary CREATE [OR REPLACE] RULE statement."""
    orr = a.get("or_replace", "absent")
    replace = "OR REPLACE " if orr == "present" else ""
    name = _rule_name(a, p)
    event = a.get("event_type", "INSERT")
    table = _table_ref(a, p)
    where = _where_clause(a)
    do = _do_clause(a, p)
    parts = [f"CREATE {replace}RULE {name} AS ON {event} TO {table}"]
    if where:
        parts.append(where)
    parts.append(do)
    return " ".join(parts) + ";"


def _tables_to_drop(a: dict[str, str], p: str) -> list[str]:
    tables = [f"{p}t"]
    if a.get("object_state") == "exists_different_table":
        tables.append(f"{p}other")
    return tables


def _build_setup(
    a: dict[str, str], p: str
) -> tuple[list[str], str]:
    lines: list[str] = []
    locus = "fixture.table"
    lines.append(f"CREATE TABLE {p}t (id integer, val text);")

    if a.get("table_type") == "view":
        lines.append(
            f"CREATE VIEW {p}v AS SELECT id, val FROM {p}t;"
        )
        locus = "fixture.view"

    if a.get("object_state") == "exists_different_table":
        lines.append(f"CREATE TABLE {p}other (id integer, val text);")
        event = a.get("event_type", "INSERT")
        rname = _rule_name(a, p)
        lines.append(
            f"CREATE RULE {rname} AS ON {event} "
            f"TO {p}other DO INSTEAD NOTHING;"
        )
        locus = "fixture.different_table_rule"

    if a.get("object_state") == "exists_same_table_same_event":
        event = a.get("event_type", "INSERT")
        rname = _rule_name(a, p)
        table = _table_plain(a, p)
        lines.append(
            f"CREATE RULE {rname} AS ON {event} "
            f"TO {table} DO INSTEAD NOTHING;"
        )
        locus = "fixture.duplicate_rule"

    if a.get("privilege_denied") == "non_owner_denied":
        lines.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        lines.append(f"SET ROLE {p}actor;")
        locus = "fixture.permission_state"

    return lines, locus


def _build_bookends(
    a: dict[str, str], p: str
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Idempotent pre-cleanup + cleanup via the shared cleanup_bookend helper.

    The RULE drop is shape A (``ON <table>``) and is routed to build_cleanup
    ONLY: in pre_cleanup the host table drops first via ``DROP TABLE
    CASCADE``, removing the rule's container relation, so a later ``DROP RULE
    ON <gone-relation>`` would error regardless of ``IF EXISTS``.  The fixture
    VIEW ``{p}v`` is never dropped explicitly -- ``DROP TABLE {p}t CASCADE``
    removes it as a dependent, which also sidesteps the helper's
    specs-before-complex_specs ordering hazard (the rule attaches to ``{p}v``
    when ``table_type==view``, so an explicit ``DROP VIEW`` in ``specs`` would
    drop the host before the rule drop).  The conditional ``DROP RULE`` is
    kept only for structural absence (``nonexistent_table``): the container
    was never created, so ``DROP RULE ON <missing-relation>`` is unsafe even
    with ``IF EXISTS``; everywhere else the drop is unconditional (idempotent
    no-op over a relation that exists).
    """
    tables = tuple(_tables_to_drop(a, p))
    complex_specs: tuple[OnDropSpec, ...] = ()
    if not _is_nonexistent_table(a):
        rule = _rule_name_plain(a, p)
        host = _table_plain(a, p)
        on_specs = [OnDropSpec("RULE", rule, host)]
        if a.get("object_state") == "exists_different_table":
            on_specs.append(OnDropSpec("RULE", rule, f"{p}other"))
        complex_specs = tuple(on_specs)
    roles = (
        (f"{p}actor",)
        if a.get("privilege_denied") == "non_owner_denied"
        else ()
    )
    pre_cleanup = build_pre_cleanup(tables=tables, roles=roles)
    cleanup = build_cleanup(
        tables=tables,
        complex_specs=complex_specs,
        roles=roles,
        drop_owned=bool(roles),
        reset_role=bool(roles),
    )
    return pre_cleanup.statements, cleanup.statements


def _probe_select(
    case: CreateRuleFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only verification."""

    mode = a.get("verification_mode", "catalog_query_pg_rewrite")

    if not _present(a):
        if mode == "error_assertion":
            return None
        if mode == "rule_behavior_test":
            return None
        table = _table_plain(a, p)
        return (
            "SELECT count(*) AS rule_count "
            "FROM pg_catalog.pg_rewrite r "
            "JOIN pg_catalog.pg_class c ON c.oid = r.ev_class "
            f"WHERE c.relname = '{table}' "
            "ORDER BY count(*)"
            ";"
        )

    if mode == "error_assertion":
        return None
    if mode == "rule_behavior_test":
        et = a.get("event_type", "INSERT")
        if et == "SELECT" and a.get("table_type") == "view":
            return (
                f"SELECT count(*) AS behavior_row_count "
                f"FROM {p}v "
                f"ORDER BY count(*)"
                f";"
            )
        return (
            f"INSERT INTO {p}t (id, val) VALUES (1, 'x');\n"
            f"SELECT count(*) AS behavior_row_count "
            f"FROM {p}t "
            f"ORDER BY count(*)"
            f";"
        )
    table = _table_plain(a, p)
    return (
        "SELECT count(*) AS rule_count "
        "FROM pg_catalog.pg_rewrite r "
        "JOIN pg_catalog.pg_class c ON c.oid = r.ev_class "
        f"WHERE c.relname = '{table}' "
        "ORDER BY count(*)"
        ";"
    )


def _build_assert(
    case: CreateRuleFactorCase,
    a: dict[str, str],
    p: str,
) -> tuple[str, ...]:
    lines: list[str] = []
    if a.get("privilege_denied") == "non_owner_denied":
        lines.append("RESET ROLE;")
    lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    probe = _probe_select(case, a, p)
    if probe is not None:
        lines.append(probe)
    return tuple(lines)


def _resolve_case(case: CreateRuleFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    setup, locus = _build_setup(a, p)
    target = _build_target(a, p)
    assert_lines = _build_assert(case, a, p)
    pre_cleanup, cleanup = _build_bookends(a, p)
    on_error_off = case.outcome == "expected_failure"
    return _CasePlan(
        target_fragment=target,
        setup_lines=tuple(setup),
        assert_lines=assert_lines,
        pre_cleanup_lines=pre_cleanup,
        cleanup_lines=cleanup,
        on_error_off=on_error_off,
        semantic_locus=locus,
    )


def _header(case: CreateRuleFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE RULE {case.factor_key}="
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


def render_create_rule_factor_case(
    case: CreateRuleFactorCase
    | CreateRuleFactorExtensionCase,
    repository_root: Path,
) -> str:
    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("SELECT 1 AS setup_boundary;")
    lines.append("-- 2. 创建完整本地表和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("SELECT 1 AS pre_target_boundary;")
    lines.append(
        "-- 3. 执行唯一获得覆盖信用的 CREATE RULE。"
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
    case: CreateRuleFactorCase
    | CreateRuleFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_rule_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_rule_factor_programs(
    baseline_plan: CreateRuleFactorLoopPlan,
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


def count_primary_create_rule(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(
            r"(?im)^\s*CREATE\s+(?:OR\s+REPLACE\s+)?RULE\b",
            region,
        )
    )


def remove_primary_semantic_locus_but_keep_comments(
    sql: str,
    case: object,
) -> str:
    """Mutation helper proving that trace comments alone receive no credit."""

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


def resolve_create_rule_factor_witness(
    case: CreateRuleFactorCase
    | CreateRuleFactorExtensionCase,
    repository_root: Path,
) -> CreateRuleFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateRuleFactorWitness(
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
    "CreateRuleFactorRenderError",
    "CreateRuleFactorWitness",
    "count_primary_create_rule",
    "generate_create_rule_factor_programs",
    "render_create_rule_factor_case",
    "resolve_create_rule_factor_witness",
    "remove_primary_semantic_locus_but_keep_comments",
]
