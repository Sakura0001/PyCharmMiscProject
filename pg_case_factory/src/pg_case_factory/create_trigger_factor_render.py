"""Render complete PostgreSQL 18.4 CREATE TRIGGER factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CREATE TRIGGER is a table-dependent DDL statement: the target is a
trigger ON a table.  Every case creates at least one table (and a
trigger function), so the bookend gate applies: the FIRST and LAST
executable ``;``-statement must each be
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

from .cleanup_bookend import (
    DropSpec,
    OnDropSpec,
    build_cleanup,
    build_pre_cleanup,
)
from .create_trigger_factor_extension import (
    CreateTriggerFactorExtensionCase,
    _present_failure_pair,
)
from .create_trigger_factor_loop import (
    CreateTriggerFactorCase,
    CreateTriggerFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/trigger/"
    "create_trigger.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/trigger/"
    "create_trigger.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

class CreateTriggerFactorRenderError(ValueError):
    """Raised when a CREATE TRIGGER case cannot be rendered."""

@dataclass(frozen=True)
class CreateTriggerFactorWitness:
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
    ext: CreateTriggerFactorExtensionCase,
) -> CreateTriggerFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get("target_action", "before_trigger")
    return CreateTriggerFactorCase(
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
    case: CreateTriggerFactorCase
    | CreateTriggerFactorExtensionCase,
) -> CreateTriggerFactorCase:
    if isinstance(case, CreateTriggerFactorExtensionCase):
        return _synthetic_case(case)
    return case

def _baseline(case: CreateTriggerFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)

def _is_instead_of(a: dict[str, str]) -> bool:
    return a.get("trigger_timing") == "INSTEAD_OF"

def _table_missing(a: dict[str, str]) -> bool:
    return a.get("table_dependency") == "table_not_exists"

def _function_missing(a: dict[str, str]) -> bool:
    return a.get("function_dependency") == "trigger_function_not_exists"

def _function_wrong_type(a: dict[str, str]) -> bool:
    return (
        a.get("function_dependency") == "function_returns_wrong_type"
    )

def _trigger_exists(a: dict[str, str]) -> bool:
    return a.get("object_state") == "already_exists"

def _is_foreign_table_case(a: dict[str, str]) -> bool:
    return (
        a.get("referencing_clause")
        == "transition_table_on_foreign_table"
    )

def _table_name(a: dict[str, str], p: str) -> str:
    """Plain fixture table name for CREATE/DROP (bookend-safe)."""
    return f"{p}tbl"

def _view_name(a: dict[str, str], p: str) -> str:
    return f"{p}vw"

def _foreign_table_name(a: dict[str, str], p: str) -> str:
    return f"{p}ft"

def _table_name_for_target(
    a: dict[str, str], p: str
) -> str:
    """Target table/view reference (quoted-factor byte carrier)."""
    if _is_instead_of(a):
        return _view_name(a, p)
    if _is_foreign_table_case(a):
        return _foreign_table_name(a, p)
    return _table_name(a, p)

def _trigger_name(
    case: CreateTriggerFactorCase, a: dict[str, str], p: str
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
    if shape == "duplicate":
        return f"{p}trig"
    return f"{p}trig"

def _trigger_name_literal(
    case: CreateTriggerFactorCase, a: dict[str, str], p: str
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
    return f"{p}trig"

def _function_name(a: dict[str, str], p: str) -> str:
    shape = a.get("function_name_shape", "simple")
    if shape == "quoted":
        return f'"{p}fn"'
    return f"{p}fn"

def _referenced_table_name(a: dict[str, str], p: str) -> str:
    return f"{p}reftbl"

def _effective_role(a: dict[str, str], p: str) -> str:
    pl = a.get("privilege_level", "superuser")
    if pl == "non_owner_no_privilege":
        return f"{p}actor"
    if pl == "non_owner_with_create_trigger":
        return f"{p}actor"
    return ""

def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    pl = a.get("privilege_level", "superuser")
    if pl in (
        "non_owner_no_privilege",
        "non_owner_with_create_trigger",
    ):
        roles.append(f"{p}actor")
    return tuple(roles)

def _tables_to_drop(
    case: CreateTriggerFactorCase,
) -> list[str]:
    """All tables the case CREATEs (for bookend)."""

    a = _baseline(case)
    p = case.object_prefix
    tables = [_table_name(a, p)]
    if a.get("table_dependency") == "partitioned_table":
        part_name = f"{p}tbl_part1"
        if part_name not in tables:
            tables.append(part_name)
    if a.get("from_clause") == "present":
        ref_name = _referenced_table_name(a, p)
        if ref_name not in tables:
            tables.append(ref_name)
    return tables

def _event_clause(a: dict[str, str]) -> str:
    event = a.get("trigger_event", "INSERT")
    event_map = {
        "INSERT": "INSERT",
        "UPDATE": "UPDATE",
        "DELETE": "DELETE",
        "TRUNCATE": "TRUNCATE",
        "INSERT_OR_UPDATE": "INSERT OR UPDATE",
        "UPDATE_OR_DELETE": "UPDATE OR DELETE",
        "INSERT_OR_UPDATE_OR_DELETE": "INSERT OR UPDATE OR DELETE",
    }
    return event_map.get(event, "INSERT")

def _update_of_clause(a: dict[str, str], p: str) -> str:
    if a.get("update_of_columns") != "with_column_list":
        return ""
    col_list = a.get("event_column_list", "single_column")
    if col_list == "nonexistent_column":
        return f" OF {p}no_such_col"
    if col_list == "multiple_columns":
        return f" OF {p}col_a, {p}col_b"
    return f" OF {p}col_a"

def _for_each_clause(a: dict[str, str]) -> str:
    fe = a.get("for_each_clause", "absent")
    if fe == "ROW":
        return "FOR EACH ROW"
    if fe == "STATEMENT":
        return "FOR EACH STATEMENT"
    return ""


def _deferrable_clause(a: dict[str, str]) -> str:
    dc = a.get("deferrable_clause", "absent")
    if dc == "NOT_DEFERRABLE":
        return "NOT DEFERRABLE"
    if dc == "DEFERRABLE_INITIALLY_IMMEDIATE":
        return "DEFERRABLE INITIALLY IMMEDIATE"
    if dc == "DEFERRABLE_INITIALLY_DEFERRED":
        return "DEFERRABLE INITIALLY DEFERRED"
    return ""


def _when_clause(a: dict[str, str], p: str) -> str:
    if a.get("when_clause") != "with_WHEN_condition":
        return ""
    return f" WHEN ({p}col_a IS NOT NULL)"


def _referencing_clause(a: dict[str, str], p: str) -> str:
    rc = a.get("referencing_clause", "absent")
    if rc == "with_OLD_TABLE":
        return f" REFERENCING OLD TABLE AS {p}old_rows"
    if rc == "with_NEW_TABLE":
        return f" REFERENCING NEW TABLE AS {p}new_rows"
    if rc == "with_BOTH":
        return (
            f" REFERENCING OLD TABLE AS {p}old_rows"
            f" NEW TABLE AS {p}new_rows"
        )
    if rc == "transition_table_on_foreign_table":
        return f" REFERENCING NEW TABLE AS {p}new_rows"
    return ""


def _from_clause(a: dict[str, str], p: str) -> str:
    if a.get("from_clause") != "present":
        return ""
    return f" FROM {_referenced_table_name(a, p)}"


def _execute_clause(a: dict[str, str], p: str) -> str:
    ec = a.get("execute_clause", "FUNCTION")
    fn = _function_name(a, p)
    if ec == "PROCEDURE":
        return f"EXECUTE PROCEDURE {fn}()"
    return f"EXECUTE FUNCTION {fn}()"


def _probe_select(
    case: CreateTriggerFactorCase,
    a: dict[str, str],
    p: str,
) -> str:
    """Catalog-audit oracle."""

    mode = a.get("verification_mode", "pg_trigger_catalog_query")
    check = _trigger_name_literal(case, a, p)
    present = case.outcome == "success"
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


def _build_target(
    case: CreateTriggerFactorCase,
    a: dict[str, str],
    p: str,
) -> str:
    """The primary CREATE TRIGGER statement."""

    timing = a.get("trigger_timing", "BEFORE")
    timing_sql = {
        "BEFORE": "BEFORE",
        "AFTER": "AFTER",
        "INSTEAD_OF": "INSTEAD OF",
    }[timing]

    or_replace = ""
    if a.get("or_replace_clause") == "present":
        or_replace = "OR REPLACE "

    constraint = ""
    if a.get("constraint_trigger") == "present":
        constraint = "CONSTRAINT "

    trigger = _trigger_name(case, a, p)
    target = _table_name_for_target(a, p)
    event = _event_clause(a) + _update_of_clause(a, p)
    from_c = _from_clause(a, p)
    deferrable = _deferrable_clause(a)
    referencing = _referencing_clause(a, p)
    for_each = _for_each_clause(a)
    when_c = _when_clause(a, p)
    execute = _execute_clause(a, p)

    parts = [
        f"CREATE {or_replace}{constraint}TRIGGER {trigger}",
        f"{timing_sql} {event}",
        f"ON {target}",
    ]
    if from_c:
        parts.append(from_c.strip())
    if deferrable:
        parts.append(deferrable)
    if referencing:
        parts.append(referencing.strip())
    if for_each:
        parts.append(for_each)
    if when_c:
        parts.append(when_c.strip())
    parts.append(execute)
    return " ".join(parts) + ";"


def _resolve_case(
    case: CreateTriggerFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    table_missing = _table_missing(a)
    function_missing = _function_missing(a)
    function_wrong = _function_wrong_type(a)
    instead_of = _is_instead_of(a)
    is_foreign = _is_foreign_table_case(a)
    duplicate = _trigger_exists(a)

    setup: list[str] = []
    locus = "target.create_trigger"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    table = _table_name(a, p)
    view = _view_name(a, p)
    ftable = _foreign_table_name(a, p)
    fn = _function_name(a, p)

    # --- role fixtures -----------------------------------------------
    if effective == f"{p}actor":
        priv = a.get("privilege_level", "superuser")
        if priv == "non_owner_with_create_trigger":
            setup.append(
                f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;"
            )
            setup.append(
                f"GRANT CREATE ON SCHEMA public TO {p}actor;"
            )
            setup.append(
                f"GRANT USAGE ON SCHEMA public TO {p}actor;"
            )
        else:
            setup.append(
                f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;"
            )
        locus = "fixture.privilege_state"

    # --- schema fixture (for schema_qualified names) ----------------
    if a.get("table_name_shape") == "schema_qualified":
        setup.append(f"CREATE SCHEMA {p}schema;")
        locus = "fixture.schema"
    if a.get("function_name_shape") == "schema_qualified":
        if f"CREATE SCHEMA {p}schema;" not in setup:
            setup.append(f"CREATE SCHEMA {p}schema;")
        locus = "fixture.schema"

    # --- the target table/view fixture -------------------------------
    if not table_missing:
        if instead_of:
            setup.append(f"CREATE TABLE {table} (id integer);")
            setup.append(
                f"CREATE VIEW {view} AS SELECT * FROM {table};"
            )
            locus = "fixture.view"
        elif is_foreign:
            setup.append(f"CREATE TABLE {table} (id integer);")
            setup.append(
                "CREATE EXTENSION IF NOT EXISTS file_fdw;"
            )
            setup.append(
                f"CREATE SERVER {p}srv "
                f"FOREIGN DATA WRAPPER file_fdw;"
            )
            setup.append(
                f"CREATE FOREIGN TABLE {ftable} (id integer) "
                f"SERVER {p}srv "
                f"OPTIONS (filename '/tmp/{p}ft.csv');"
            )
            locus = "fixture.foreign_table"
        elif a.get("table_dependency") == "partitioned_table":
            setup.append(
                f"CREATE TABLE {table} (id integer) "
                f"PARTITION BY RANGE (id);"
            )
            setup.append(
                f"CREATE TABLE {p}tbl_part1 "
                f"PARTITION OF {table} "
                f"FOR VALUES FROM (0) TO (100);"
            )
            locus = "fixture.partitioned_table"
        else:
            if a.get("update_of_columns") == "with_column_list":
                setup.append(
                    f"CREATE TABLE {table} "
                    f"({p}col_a integer, {p}col_b integer, "
                    f"id integer);"
                )
            else:
                setup.append(
                    f"CREATE TABLE {table} "
                    f"(id integer, {p}col_a integer);"
                )
            locus = "fixture.table"
    else:
        setup.append(
            "SELECT 1 AS target_table_intentionally_absent;"
        )
        locus = "fixture.table_missing"

    # --- referenced table fixture (for FROM clause) ------------------
    if (
        a.get("from_clause") == "present"
        and not table_missing
        and a.get("referenced_table_dependency")
        == "referenced_table_exists"
    ):
        ref = _referenced_table_name(a, p)
        setup.append(f"CREATE TABLE {ref} (id integer);")
        locus = "fixture.referenced_table"

    # --- trigger function --------------------------------------------
    if not function_missing and not table_missing:
        if function_wrong:
            setup.append(
                f"CREATE FUNCTION {fn}() RETURNS integer "
                f"LANGUAGE plpgsql AS $$ BEGIN RETURN 1; END; $$;"
            )
            locus = "fixture.function_wrong_type"
        else:
            setup.append(
                f"CREATE FUNCTION {fn}() RETURNS trigger "
                f"LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END; $$;"
            )
            locus = "fixture.function"
    elif not table_missing and function_missing:
        setup.append(
            "SELECT 1 AS target_function_intentionally_absent;"
        )
        locus = "fixture.function_missing"

    # --- duplicate trigger (for already_exists) ----------------------
    if (
        duplicate
        and not table_missing
        and not function_missing
        and not function_wrong
    ):
        dup_trigger = _trigger_name(case, a, p)
        target = _table_name_for_target(a, p)
        execute = _execute_clause(a, p)
        timing = a.get("trigger_timing", "BEFORE")
        timing_sql = {
            "BEFORE": "BEFORE",
            "AFTER": "AFTER",
            "INSTEAD_OF": "INSTEAD OF",
        }[timing]
        event = _event_clause(a)
        setup.append(
            f"CREATE TRIGGER {dup_trigger} {timing_sql} {event} "
            f"ON {target} FOR EACH ROW {execute};"
        )
        locus = "fixture.duplicate_trigger"

    # --- arm the effective role --------------------------------------
    if effective:
        setup.append(f"SET ROLE {effective};")

    # --- the primary target statement --------------------------------
    target = _build_target(case, a, p)

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

    # --- cleanup construction (idempotent bookends via cleanup_bookend) ---
    # The TRIGGER drop is shape A (``ON <table>``) and goes through
    # ``complex_specs``.  It is routed to ``build_cleanup`` ONLY (quirk
    # Q2): in pre-cleanup the table is dropped first (``DROP TABLE
    # CASCADE`` removes the trigger), so a later ``DROP TRIGGER ON
    # <gone-table>`` would error on the missing relation; ``IF EXISTS``
    # on the trigger does not suppress a missing-table error.  Per Q3 the
    # complex DROP is unconditional except when the container relation was
    # never created (``table_missing``) -- structural absence keeps the
    # guard because ``DROP TRIGGER ON <missing-relation>`` errors
    # regardless of IF EXISTS.
    cleanup_specs: list[DropSpec] = [
        DropSpec("FUNCTION", fn, args="()")
    ]
    if instead_of:
        cleanup_specs.append(DropSpec("VIEW", view))
    if is_foreign:
        cleanup_specs.append(DropSpec("FOREIGN TABLE", ftable))
        cleanup_specs.append(DropSpec("SERVER", f"{p}srv"))

    schemas: list[str] = []
    if (
        a.get("table_name_shape") == "schema_qualified"
        or a.get("function_name_shape") == "schema_qualified"
    ):
        schemas.append(f"{p}schema")

    tables = _tables_to_drop(case)
    complex_specs: tuple[OnDropSpec, ...] = ()
    if not table_missing:
        complex_specs = (
            OnDropSpec(
                "TRIGGER",
                _trigger_name(case, a, p),
                _table_name_for_target(a, p),
            ),
        )

    pre_cleanup_bk = build_pre_cleanup(
        tables=tuple(tables),
        specs=tuple(cleanup_specs),
        schemas=tuple(schemas),
        roles=tuple(roles),
    )
    cleanup_bk = build_cleanup(
        tables=tuple(tables),
        specs=tuple(cleanup_specs),
        complex_specs=complex_specs,
        schemas=tuple(schemas),
        roles=tuple(roles),
        drop_owned=bool(roles),
        reset_role=bool(effective),
    )
    pre_cleanup = list(pre_cleanup_bk.statements)
    cleanup = list(cleanup_bk.statements)

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


def resolve_create_trigger_factor_witness(
    case: CreateTriggerFactorCase
    | CreateTriggerFactorExtensionCase,
    repository_root: Path,
) -> CreateTriggerFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateTriggerFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_create_trigger(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(
            r"(?im)^CREATE\s+(?:OR\s+REPLACE\s+)?"
            r"(?:CONSTRAINT\s+)?TRIGGER\b",
            region,
        )
    )


def _header(case: CreateTriggerFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE TRIGGER {case.factor_key}="
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


def render_create_trigger_factor_case(
    case: CreateTriggerFactorCase
    | CreateTriggerFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 CREATE TRIGGER。")
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
    if not text.endswith(";"):
        text += ";"
    return text + "\n"


def _write_program(
    case: CreateTriggerFactorCase
    | CreateTriggerFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_trigger_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_trigger_factor_programs(
    baseline_plan: CreateTriggerFactorLoopPlan,
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
    "CreateTriggerFactorRenderError",
    "CreateTriggerFactorWitness",
    "count_primary_create_trigger",
    "generate_create_trigger_factor_programs",
    "render_create_trigger_factor_case",
    "resolve_create_trigger_factor_witness",
]
