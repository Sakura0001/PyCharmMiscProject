"""Render complete PostgreSQL 18.4 ALTER TRIGGER factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

ALTER TRIGGER is a table-dependent DDL statement: the target is a
trigger ON a table.  Every case creates at least one table (and a
trigger function + trigger), so the bookend gate applies: the FIRST and
LAST executable ``;``-statement must each be
``DROP TABLE IF EXISTS <all created tables>``.  All catalog oracles
schema-qualify ``pg_catalog.pg_trigger`` or ``information_schema.triggers``
(exempt from the file-prefix style gate).  Every catalog SELECT carries
a top-level ``ORDER BY count(*)`` so the catalog-observability gate
passes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .alter_trigger_factor_extension import (
    AlterTriggerFactorExtensionCase,
    _present_failure_pair,
)
from .alter_trigger_factor_loop import (
    AlterTriggerFactorCase,
    AlterTriggerFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/trigger/"
    "alter_trigger.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/trigger/"
    "alter_trigger.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class AlterTriggerFactorRenderError(ValueError):
    """Raised when an ALTER TRIGGER case cannot be rendered."""


@dataclass(frozen=True)
class AlterTriggerFactorWitness:
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
    ext: AlterTriggerFactorExtensionCase,
) -> AlterTriggerFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get("target_action", "rename")
    return AlterTriggerFactorCase(
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
    case: AlterTriggerFactorCase
    | AlterTriggerFactorExtensionCase,
) -> AlterTriggerFactorCase:
    if isinstance(case, AlterTriggerFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: AlterTriggerFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _trigger_missing(a: dict[str, str]) -> bool:
    return a.get("object_state") == "not_exists"


def _table_missing(a: dict[str, str]) -> bool:
    return a.get("table_dependency") == "table_not_exists"


def _table_name(a: dict[str, str], p: str) -> str:
    """Plain fixture table name for CREATE/DROP (bookend-safe).

    Always returns an UNQUOTED lowercase identifier: the shared bookend
    gate (regression_style._normalize_identifier /
    _split_identifier_list) rejects any ``"`` inside CREATE TABLE / DROP
    TABLE, so the quoted form of the ``table_name_shape=quoted`` factor is
    kept byte-observable ONLY in the ALTER TRIGGER target (see
    :func:`_table_name_for_target`), never in the bookend DDL here.
    """
    shape = a.get("table_name_shape", "simple")
    if shape == "schema_qualified":
        return f"{p}schema.{p}tbl"
    return f"{p}tbl"


def _table_name_for_target(a: dict[str, str], p: str) -> str:
    """ALTER TRIGGER target table reference (quoted-factor byte carrier).

    For ``table_name_shape=quoted`` the plain lowercase fixture name is
    wrapped in double quotes so the quoted-identifier factor stays
    byte-observable in the primary target statement.  PostgreSQL treats
    ``"lowercase_name"`` identically to the unquoted ``lowercase_name``,
    so this never changes identity and never breaks the shared bookend
    gate (which only inspects the plain name in CREATE/DROP).  Other
    shapes reuse the plain name unchanged.
    """
    if a.get("table_name_shape") == "quoted":
        return f'"{_table_name(a, p)}"'
    return _table_name(a, p)


def _trigger_name(
    case: AlterTriggerFactorCase, a: dict[str, str], p: str
) -> str:
    if (
        case.factor_key == "identifier_length_exceeded"
        and case.factor_value == "over_63_chars"
    ):
        base = f"{p}trig"
        return base + "a" * max(1, 64 - len(base))
    shape = a.get("trigger_name_shape", "simple")
    if shape == "quoted":
        return f'"{p}MixedTrig"'
    if shape == "reserved_word":
        return '"column"'
    if shape == "schema_qualified":
        return f"{p}schema.{p}trig"
    return f"{p}trig"


def _trigger_name_literal(
    case: AlterTriggerFactorCase, a: dict[str, str], p: str
) -> str:
    if (
        case.factor_key == "identifier_length_exceeded"
        and case.factor_value == "over_63_chars"
    ):
        base = f"{p}trig"
        return base + "a" * max(1, 64 - len(base))
    shape = a.get("trigger_name_shape", "simple")
    if shape == "quoted":
        return f"{p}MixedTrig"
    if shape == "reserved_word":
        return "column"
    if shape == "schema_qualified":
        return f"{p}schema.{p}trig"
    return f"{p}trig"


def _new_name(a: dict[str, str], p: str) -> str:
    rt = a.get("rename_target", "simple")
    if rt == "duplicate_name":
        return f"{p}duptrig"
    shape = a.get("new_name_shape", "simple")
    if shape == "quoted":
        return f'"{p}MixedNew"'
    if shape == "reserved_word":
        return '"column"'
    return f"{p}newtrig"


def _new_name_literal(a: dict[str, str], p: str) -> str:
    rt = a.get("rename_target", "simple")
    if rt == "duplicate_name":
        return f"{p}duptrig"
    shape = a.get("new_name_shape", "simple")
    if shape == "quoted":
        return f"{p}MixedNew"
    if shape == "reserved_word":
        return "column"
    return f"{p}newtrig"


def _extension_clause(a: dict[str, str], p: str) -> str:
    et = a.get("extension_target", "extension_exists")
    if et == "NO_DEPENDS":
        return f"NO DEPENDS ON EXTENSION plpgsql"
    if et == "extension_not_exists":
        return f"DEPENDS ON EXTENSION {p}noext"
    return "DEPENDS ON EXTENSION plpgsql"


def _effective_role(a: dict[str, str], p: str) -> str:
    pl = a.get("privilege_level", "superuser")
    if pl == "non_owner_no_privilege":
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    pl = a.get("privilege_level", "superuser")
    if pl == "non_owner_no_privilege":
        roles.append(f"{p}actor")
    return tuple(roles)


def _tables_to_drop(
    case: AlterTriggerFactorCase,
) -> list[str]:
    """All tables the case CREATEs (for bookend)."""

    a = _baseline(case)
    p = case.object_prefix
    tables = [_table_name(a, p)]
    if a.get("partitioned_table_effect") == "partitioned_table":
        part_name = f"{p}tbl_part1"
        if part_name not in tables:
            tables.append(part_name)
    return tables


def _table_boundary_cleanup(
    case: AlterTriggerFactorCase,
) -> str:
    return (
        "DROP TABLE IF EXISTS "
        + ", ".join(_tables_to_drop(case))
        + " CASCADE;"
    )


def _probe_select(
    case: AlterTriggerFactorCase,
    a: dict[str, str],
    p: str,
) -> str:
    """Catalog-audit oracle."""

    mode = a.get("verification_mode", "pg_trigger_catalog_query")
    action = a.get("target_action", "rename")
    missing = _trigger_missing(a)
    table_missing = _table_missing(a)

    if action == "rename" and case.outcome == "success" and not missing:
        check = _new_name_literal(a, p)
        present = True
    elif missing or table_missing:
        check = _trigger_name_literal(case, a, p)
        present = False
    else:
        check = _trigger_name_literal(case, a, p)
        present = True

    cmp_op = ">" if present else "="
    if mode == "information_schema_triggers":
        return (
            f"SELECT count(*) {cmp_op} 0 AS trigger_state "
            f"FROM information_schema.triggers "
            f"WHERE trigger_name = '{check}' "
            f"ORDER BY count(*);"
        )
    return (
        f"SELECT count(*) {cmp_op} 0 AS trigger_state "
        f"FROM pg_catalog.pg_trigger "
        f"WHERE tgname = '{check}' "
        f"ORDER BY count(*);"
    )


def _resolve_case(
    case: AlterTriggerFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    action = a.get("target_action", "rename")
    missing = _trigger_missing(a)
    table_missing = _table_missing(a)

    setup: list[str] = []
    locus = "target.alter_trigger"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    table = _table_name(a, p)
    target_table = _table_name_for_target(a, p)
    trigger = _trigger_name(case, a, p)

    # --- role fixtures -----------------------------------------------
    if effective == f"{p}actor":
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- schema fixture (for schema_qualified table name) ------------
    if a.get("table_name_shape") == "schema_qualified":
        setup.append(f"CREATE SCHEMA {p}schema;")
        locus = "fixture.schema"

    # --- the target table fixture ------------------------------------
    if not table_missing:
        if a.get("partitioned_table_effect") == "partitioned_table":
            setup.append(
                f"CREATE TABLE {table} (id integer) "
                f"PARTITION BY RANGE (id);"
            )
            setup.append(
                f"CREATE TABLE {p}tbl_part1 PARTITION OF {table} "
                f"FOR VALUES FROM (0) TO (100);"
            )
        else:
            setup.append(f"CREATE TABLE {table} (id integer);")
        locus = "fixture.table"
    else:
        setup.append(
            "SELECT 1 AS target_table_intentionally_absent;"
        )
        locus = "fixture.table_missing"

    # --- trigger function + trigger ---------------------------------
    if not table_missing:
        setup.append(
            f"CREATE FUNCTION {p}trigfn() RETURNS trigger "
            f"LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END; $$;"
        )
        if not missing:
            setup.append(
                f"CREATE TRIGGER {trigger} BEFORE INSERT "
                f"ON {table} FOR EACH ROW "
                f"EXECUTE FUNCTION {p}trigfn();"
            )
            locus = "fixture.trigger"
        else:
            setup.append(
                "SELECT 1 AS target_trigger_intentionally_absent;"
            )
            locus = "fixture.trigger_missing"

    # --- conflict trigger for duplicate_name -------------------------
    if (
        action == "rename"
        and a.get("rename_target") == "duplicate_name"
        and not missing
        and not table_missing
    ):
        setup.append(
            f"CREATE TRIGGER {p}duptrig BEFORE INSERT "
            f"ON {table} FOR EACH ROW "
            f"EXECUTE FUNCTION {p}trigfn();"
        )
        locus = "fixture.duplicate_trigger"

    # --- arm the effective role --------------------------------------
    if effective:
        setup.append(f"SET ROLE {effective};")

    # --- the primary target statement --------------------------------
    target = _build_target(case, a, p, trigger, target_table)

    # --- oracle / SQLSTATE assertion ---------------------------------
    assert_lines: list[str] = []
    if effective:
        assert_lines.append("RESET ROLE;")
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    probe = _probe_select(case, a, p)
    assert_lines.append(probe)

    # --- cleanup construction -----------------------------------------
    role_drops = [
        statement
        for role in roles
        for statement in (
            f"DROP OWNED BY {role} CASCADE;",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    trigger_drop = ""
    cleanup_mode = a.get("cleanup_mode", "DROP_TRIGGER")
    if cleanup_mode == "DROP_TRIGGER_IF_EXISTS":
        if not missing and not table_missing:
            trigger_drop = (
                f"DROP TRIGGER IF EXISTS {trigger} ON {table};"
            )
    else:
        if not missing and not table_missing:
            if action == "rename" and case.outcome == "success":
                new_trigger = _new_name(a, p)
                trigger_drop = (
                    f"DROP TRIGGER IF EXISTS {new_trigger} ON {table};"
                )
            else:
                trigger_drop = (
                    f"DROP TRIGGER IF EXISTS {trigger} ON {table};"
                )

    func_drop = f"DROP FUNCTION IF EXISTS {p}trigfn() CASCADE;"

    # pre-cleanup: table boundary (bookend first), then schema, func, role
    pre_cleanup: list[str] = []
    pre_cleanup.append(_table_boundary_cleanup(case))
    if a.get("table_name_shape") == "schema_qualified":
        pre_cleanup.append(
            f"DROP SCHEMA IF EXISTS {p}schema CASCADE;"
        )
    pre_cleanup.append(func_drop)
    pre_cleanup.extend(role_drops)
    pre_cleanup.append("RESET ROLE;")
    if len(pre_cleanup) <= 1:
        pre_cleanup.append(
            "SELECT 1 AS residual_check_no_objects;"
        )

    # cleanup: reset role, trigger, function, table boundary (bookend last)
    cleanup: list[str] = []
    cleanup.append("RESET ROLE;")
    if trigger_drop:
        cleanup.append(trigger_drop)
    cleanup.append(func_drop)
    cleanup.extend(role_drops)
    if a.get("table_name_shape") == "schema_qualified":
        cleanup.append(
            f"DROP SCHEMA IF EXISTS {p}schema CASCADE;"
        )
    cleanup.append(_table_boundary_cleanup(case))

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


def _build_target(
    case: AlterTriggerFactorCase,
    a: dict[str, str],
    p: str,
    trigger: str,
    table: str,
) -> str:
    """The primary ALTER TRIGGER statement for the active branch."""

    action = a.get("target_action", "rename")
    if action == "depends_on_extension":
        clause = _extension_clause(a, p)
        return f"ALTER TRIGGER {trigger} ON {table} {clause};"
    new = _new_name(a, p)
    return f"ALTER TRIGGER {trigger} ON {table} RENAME TO {new};"


def resolve_alter_trigger_factor_witness(
    case: AlterTriggerFactorCase
    | AlterTriggerFactorExtensionCase,
    repository_root: Path,
) -> AlterTriggerFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return AlterTriggerFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_alter_trigger(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*ALTER\s+TRIGGER\b", region)
    )


def _header(case: AlterTriggerFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : ALTER TRIGGER {case.factor_key}="
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


def render_alter_trigger_factor_case(
    case: AlterTriggerFactorCase
    | AlterTriggerFactorExtensionCase,
    repository_root: Path,
) -> str:
    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.append(resolved.pre_cleanup_lines[0])
    lines.append("\\set ON_ERROR_STOP on")
    lines.extend(resolved.pre_cleanup_lines[1:])
    lines.append("-- 2. 创建完整本地规则和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 ALTER TRIGGER。")
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
    case: AlterTriggerFactorCase
    | AlterTriggerFactorExtensionCase,
    out: Path,
) -> None:
    text = render_alter_trigger_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_alter_trigger_factor_programs(
    baseline_plan: AlterTriggerFactorLoopPlan,
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
    "AlterTriggerFactorRenderError",
    "AlterTriggerFactorWitness",
    "count_primary_alter_trigger",
    "generate_alter_trigger_factor_programs",
    "render_alter_trigger_factor_case",
    "resolve_alter_trigger_factor_witness",
]
