"""Render complete PostgreSQL 18.4 ALTER TABLE factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.
The file is assembled from a single :func:`_resolve_case` plan so that the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .alter_table_factor_extension import (
    AlterTableFactorExtensionCase,
)
from .alter_table_factor_loop import (
    AlterTableFactorCase,
)


_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/table/"
    "alter_table.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/table/"
    "alter_table.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1_ACTION = "branch_1_action"
_BRANCH_2_RENAME_COLUMN = "branch_2_rename_column"
_BRANCH_3_RENAME_CONSTRAINT = "branch_3_rename_constraint"
_BRANCH_4_RENAME_TABLE = "branch_4_rename_table"
_BRANCH_5_SET_SCHEMA = "branch_5_set_schema"
_BRANCH_6_SET_TABLESPACE_BATCH = "branch_6_set_tablespace_batch"
_BRANCH_7_ATTACH_PARTITION = "branch_7_attach_partition"
_BRANCH_8_DETACH_PARTITION = "branch_8_detach_partition"


def _synthetic_case(
    ext: AlterTableFactorExtensionCase,
) -> AlterTableFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .alter_table_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "object_state"
        factor_value = assignment.get("object_state", "exists_normal")
    return AlterTableFactorCase(
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
        execution_profile="serial_sql",
    )


def _as_render_case(
    case: AlterTableFactorCase | AlterTableFactorExtensionCase,
) -> AlterTableFactorCase:
    if isinstance(case, AlterTableFactorExtensionCase):
        return _synthetic_case(case)
    return case


class AlterTableFactorRenderError(ValueError):
    """Raised when an ALTER TABLE case cannot be rendered."""


@dataclass(frozen=True)
class AlterTableFactorWitness:
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


@dataclass(frozen=True)
class _FixtureState:
    needs_table: bool
    needs_parent: bool
    needs_index: bool
    needs_role: bool
    needs_new_owner_role: bool
    needs_schema: bool
    needs_constraint: bool
    effective: str
    table_name: str
    fixture_table: str
    parent_name: str
    index_name: str
    constraint_name: str
    schema_name: str
    is_session_user_escape: bool


def _baseline(case: AlterTableFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _table_name(a: dict[str, str], p: str) -> str:
    """Table name in the target ALTER (shape-appropriate)."""

    shape = a.get("table_name_shape", "simple")
    if shape == "quoted":
        return f'"{p}Mixed Table"'
    if shape == "reserved_word":
        return f'"{p}select"'
    if shape == "schema_qualified":
        return f"{p}sch.{p}tbl"
    if shape == "nonexistent":
        return f"{p}no_such_table"
    return f"{p}tbl"


def _table_fixture_name(a: dict[str, str], p: str) -> str:
    """Audit-normalizable name for fixture CREATE/DROP (plain or schema-qualified)."""

    shape = a.get("table_name_shape", "simple")
    base = f"{p}tbl"
    if shape == "schema_qualified":
        return f"public.{base}"
    if shape == "nonexistent":
        return f"{p}no_such_table"
    return base


def _probe_name(a: dict[str, str], p: str) -> str:
    """Name to probe in verification (strip quotes for catalog match)."""

    return _table_name(a, p).strip('"').split(".")[-1]


def _owner_target(a: dict[str, str], p: str) -> str:
    """OWNER TO target role expression."""

    dep = a.get("role_dependency", "owner_role_exists")
    if dep == "current_role_variants":
        return "SESSION_USER"
    if dep == "owner_role_not_exists":
        return f"{p}no_such_role"
    return f"{p}new_owner"


def _column_name(a: dict[str, str], p: str) -> str:
    shape = a.get("column_name_shape", "simple")
    if shape == "quoted":
        return f'"{p}Mixed Col"'
    if shape == "reserved_word":
        return f'"{p}user"'
    if shape == "nonexistent":
        return f"{p}no_such_col"
    return f"{p}col"


def _constraint_name(a: dict[str, str], p: str) -> str:
    shape = a.get("constraint_name_shape", "simple")
    if shape == "quoted":
        return f'"{p}Mixed Con"'
    if shape == "nonexistent":
        return f"{p}no_such_con"
    return f"{p}con"


def _new_name(a: dict[str, str], p: str) -> str:
    shape = a.get("new_name_shape", "simple")
    if shape == "quoted":
        return f'"{p}Mixed New"'
    if shape == "reserved_word":
        return f'"{p}from"'
    if shape == "duplicate":
        return f"{p}tbl"
    return f"{p}renamed"


def _data_type_sql(a: dict[str, str]) -> str:
    dt = a.get("data_type", "integer")
    mapping = {
        "character_varying": "character varying",
        "double_precision": "double precision",
        "time_with_time_zone": "time with time zone",
        "timestamp_with_time_zone": "timestamp with time zone",
        "bit_varying": "bit varying",
        "integer_array": "integer[]",
        "text_array": "text[]",
        "int4range": "int4range",
        "composite_type": "integer",
        "enum_type": "integer",
    }
    return mapping.get(dt, dt)


def _is_non_existent(case: AlterTableFactorCase, a: dict[str, str]) -> bool:
    if case.kind != "EXT" and a.get("expected_status") == "failure":
        ne = a.get("nonexistent_table")
        return ne == "without_IF_EXISTS_error"
    if a.get("object_state") == "not_exists":
        return True
    if a.get("table_name_shape") == "nonexistent":
        return True
    return False


def _privilege_denied(
    case: AlterTableFactorCase, a: dict[str, str]
) -> bool:
    if case.kind != "EXT" and a.get("expected_status") == "failure":
        return False
    return a.get("privilege_level") == "non_owner_no_privilege"


def _effective_role(
    case: AlterTableFactorCase, a: dict[str, str], p: str
) -> str:
    if _privilege_denied(case, a):
        return f"{p}actor"
    if a.get("privilege_level") == "table_owner":
        return f"{p}owner"
    return ""


def _needs_table(a: dict[str, str]) -> bool:
    return a.get("object_state", "exists_normal") != "not_exists"


def _needs_role(a: dict[str, str]) -> bool:
    return a.get("privilege_level") in ("table_owner", "non_owner_no_privilege")


def _needs_new_owner_role(a: dict[str, str], p: str) -> bool:
    target_action = a.get("target_action", "")
    if target_action != "owner_to":
        return False
    dep = a.get("role_dependency", "owner_role_exists")
    return dep == "owner_role_exists"


def _needs_schema(a: dict[str, str]) -> bool:
    return a.get("schema_dependency") == "schema_not_exists"


def _needs_parent(a: dict[str, str]) -> bool:
    dep = a.get("parent_table_dependency", "parent_partitioned_exists")
    return dep in ("parent_partitioned_exists", "parent_not_partitioned")


def _needs_index(a: dict[str, str]) -> bool:
    action = a.get("target_action", "")
    return action in ("cluster_on", "add_table_constraint_using_index")


def _needs_constraint(a: dict[str, str]) -> bool:
    action = a.get("target_action", "")
    return action in ("drop_constraint", "validate_constraint", "alter_constraint")


def _compute_state(case: AlterTableFactorCase) -> _FixtureState:
    a = _baseline(case)
    p = case.object_prefix
    effective = _effective_role(case, a, p)
    is_escape = (
        a.get("target_action") == "owner_to"
        and a.get("role_dependency") == "current_role_variants"
        and effective == f"{p}actor"
    )
    needs_tbl = _needs_table(a) and a.get("table_name_shape") != "nonexistent"
    return _FixtureState(
        needs_table=needs_tbl,
        needs_parent=_needs_parent(a),
        needs_index=_needs_index(a),
        needs_role=_needs_role(a),
        needs_new_owner_role=_needs_new_owner_role(a, p),
        needs_schema=_needs_schema(a),
        needs_constraint=_needs_constraint(a),
        effective=effective,
        table_name=_table_name(a, p),
        fixture_table=_table_fixture_name(a, p),
        parent_name=f"{p}parent",
        index_name=f"{p}idx",
        constraint_name=_constraint_name(a, p),
        schema_name=f"{p}new_sch",
        is_session_user_escape=is_escape,
    )


def _if_exists_clause(a: dict[str, str]) -> str:
    if a.get("if_exists_clause") == "present":
        return "IF EXISTS "
    return ""


def _action_clause(
    case: AlterTableFactorCase, a: dict[str, str], p: str
) -> str:
    """Render the ALTER TABLE action clause for the consumer action."""

    action = case.consumer_action_id
    col = _column_name(a, p)
    con = _constraint_name(a, p)
    idx = f"{p}idx"
    parent = f"{p}parent"
    dt = _data_type_sql(a)
    col_kw = "COLUMN " if a.get("add_column_keyword") == "present" else ""
    drop_kw = "COLUMN " if a.get("drop_column_keyword") == "present" else ""
    alt_kw = "COLUMN " if a.get("alter_column_keyword") == "present" else ""
    set_data = "SET DATA " if a.get("set_data_keyword") == "present" else ""
    clauses = {
        "add_column": f"ADD {col_kw}{col} {dt}",
        "add_virtual_generated_column": f"ADD COLUMN {col} integer GENERATED ALWAYS AS ({col} + 1) VIRTUAL",
        "add_temporal_constraint": f"ADD CONSTRAINT {con} UNIQUE ({col} WITHOUT OVERLAPS)",
        "drop_column": f"DROP {drop_kw}{col}",
        "alter_column_type": f"ALTER {alt_kw}{col} {set_data}TYPE {dt}",
        "alter_column_set_default": f"ALTER COLUMN {col} SET DEFAULT 0",
        "alter_column_drop_default": f"ALTER COLUMN {col} DROP DEFAULT",
        "alter_column_set_drop_not_null": f"ALTER COLUMN {col} SET NOT NULL",
        "alter_column_drop_expression": f"ALTER COLUMN {col} DROP EXPRESSION",
        "alter_column_set_expression": f"ALTER COLUMN {col} SET EXPRESSION AS ({col} + 1)",
        "alter_column_add_generated_identity": f"ALTER COLUMN {col} ADD GENERATED ALWAYS AS IDENTITY",
        "alter_column_set_generated_restart": f"ALTER COLUMN {col} SET GENERATED ALWAYS",
        "alter_column_drop_identity": f"ALTER COLUMN {col} DROP IDENTITY",
        "alter_column_set_statistics": f"ALTER COLUMN {col} SET STATISTICS 100",
        "alter_column_set_statistics_default": f"ALTER COLUMN {col} SET STATISTICS DEFAULT",
        "alter_column_set_attribute_option": f"ALTER COLUMN {col} SET (n_distinct = 1)",
        "alter_column_reset_attribute_option": f"ALTER COLUMN {col} RESET (n_distinct)",
        "alter_column_set_storage": f"ALTER COLUMN {col} SET STORAGE PLAIN",
        "alter_column_set_compression": f"ALTER COLUMN {col} SET COMPRESSION pglz",
        "add_table_constraint": f"ADD CONSTRAINT {con} CHECK ({col} > 0)",
        "add_table_constraint_using_index": f"ADD CONSTRAINT {con} UNIQUE USING INDEX {idx}",
        "alter_constraint": f"ALTER CONSTRAINT {con} DEFERRABLE",
        "alter_constraint_enforced": f"ALTER CONSTRAINT {con} NOT ENFORCED",
        "alter_constraint_inherit": f"ALTER CONSTRAINT {con} NO INHERIT",
        "validate_constraint": f"VALIDATE CONSTRAINT {con}",
        "drop_constraint": f"DROP CONSTRAINT {con}",
        "disable_trigger": "DISABLE TRIGGER ALL",
        "enable_trigger": "ENABLE TRIGGER ALL",
        "enable_replica_trigger": f"ENABLE REPLICA TRIGGER {p}trig",
        "enable_always_trigger": f"ENABLE ALWAYS TRIGGER {p}trig",
        "disable_rule": f"DISABLE RULE {p}rule",
        "enable_rule": f"ENABLE RULE {p}rule",
        "enable_replica_rule": f"ENABLE REPLICA RULE {p}rule",
        "enable_always_rule": f"ENABLE ALWAYS RULE {p}rule",
        "disable_row_level_security": "DISABLE ROW LEVEL SECURITY",
        "enable_row_level_security": "ENABLE ROW LEVEL SECURITY",
        "force_row_level_security": "FORCE ROW LEVEL SECURITY",
        "no_force_row_level_security": "NO FORCE ROW LEVEL SECURITY",
        "cluster_on": f"CLUSTER ON {idx}",
        "set_without_cluster": "SET WITHOUT CLUSTER",
        "set_without_oids": "SET WITHOUT OIDS",
        "set_access_method": "SET ACCESS METHOD heap",
        "set_access_method_default": "SET ACCESS METHOD DEFAULT",
        "set_tablespace": "SET TABLESPACE pg_default",
        "set_logged_unlogged": "SET LOGGED",
        "set_storage_parameter": "SET (fillfactor = 50)",
        "reset_storage_parameter": "RESET (fillfactor)",
        "inherit": f"INHERIT {parent}",
        "no_inherit": f"NO INHERIT {parent}",
        "of_type": f"OF {p}comp_type",
        "not_of": "NOT OF",
        "owner_to": f"OWNER TO {_owner_target(a, p)}",
        "replica_identity": "REPLICA IDENTITY DEFAULT",
    }
    try:
        return clauses[action]
    except KeyError as exc:
        raise AlterTableFactorRenderError(
            f"no action clause for {action}"
        ) from exc


def _build_target(
    case: AlterTableFactorCase, st: _FixtureState
) -> str:
    a = _baseline(case)
    p = case.object_prefix
    branch = a["grammar_branch"]
    ref = _table_name(a, p)
    ie = _if_exists_clause(a)
    only = "ONLY " if a.get("only_clause") == "present" else ""
    if branch == _BRANCH_1_ACTION:
        action = _action_clause(case, a, p)
        return f"ALTER TABLE {ie}{only}{ref} {action};"
    if branch == _BRANCH_2_RENAME_COLUMN:
        col = _column_name(a, p)
        new = _new_name(a, p)
        return f"ALTER TABLE {ie}{ref} RENAME COLUMN {col} TO {new};"
    if branch == _BRANCH_3_RENAME_CONSTRAINT:
        con = _constraint_name(a, p)
        new = _new_name(a, p)
        return f"ALTER TABLE {ie}{ref} RENAME CONSTRAINT {con} TO {new};"
    if branch == _BRANCH_4_RENAME_TABLE:
        new = _new_name(a, p)
        return f"ALTER TABLE {ie}{ref} RENAME TO {new};"
    if branch == _BRANCH_5_SET_SCHEMA:
        sch = a.get("schema_dependency") == "schema_not_exists" and f"{p}no_such_sch" or f"{p}new_sch"
        return f"ALTER TABLE {ie}{ref} SET SCHEMA {sch};"
    if branch == _BRANCH_6_SET_TABLESPACE_BATCH:
        ts = f"{p}no_such_ts" if a.get("tablespace_dependency") == "specified_tablespace_not_exists" else "pg_default"
        return f"ALTER TABLE {ie}{ref} SET TABLESPACE {ts};"
    if branch == _BRANCH_7_ATTACH_PARTITION:
        return f"ALTER TABLE {ie}{ref} ATTACH PARTITION {p}part FOR VALUES FROM (1) TO (100);"
    if branch == _BRANCH_8_DETACH_PARTITION:
        return f"ALTER TABLE {ie}{ref} DETACH PARTITION {p}part;"
    raise AlterTableFactorRenderError(f"unknown branch {branch}")


def _probe_select(
    case: AlterTableFactorCase, a: dict[str, str], p: str
) -> tuple[str, ...]:
    mode = a.get("verification_mode", "pg_class_catalog_query")
    if case.factor_key == "verification_mode":
        mode = case.factor_value
    name = _probe_name(a, p)
    if mode == "pg_attribute_query":
        return (
            "SELECT a.attname, a.attnum "
            "FROM pg_catalog.pg_attribute AS a "
            f"WHERE a.attrelid = '{name}'::regclass AND a.attnum > 0 "
            "ORDER BY a.attname;",
        )
    if mode == "pg_constraint_query":
        return (
            "SELECT c.conname, c.contype "
            "FROM pg_catalog.pg_constraint AS c "
            f"WHERE c.conrelid = '{name}'::regclass "
            "ORDER BY c.conname;",
        )
    if mode == "information_schema_query":
        return (
            "SELECT column_name, data_type "
            "FROM information_schema.columns "
            f"WHERE table_name = '{name}' "
            "ORDER BY column_name;",
        )
    if mode == "SELECT_inspection":
        return (f"SELECT count(*) AS row_count FROM {name} ORDER BY count(*);",)
    return (
        f"SELECT count(*) AS table_exists FROM pg_catalog.pg_class "
        f"WHERE relname = '{name}' AND relkind = 'r' "
        f"ORDER BY count(*);",
    )


def _build_setup(
    case: AlterTableFactorCase, st: _FixtureState,
) -> tuple[list[str], str]:
    a = _baseline(case)
    p = case.object_prefix
    setup: list[str] = []
    locus = "target.table"
    if st.needs_schema:
        setup.append(f"CREATE SCHEMA IF NOT EXISTS {st.schema_name};")
    if a.get("table_name_shape") == "schema_qualified":
        setup.append(f"CREATE SCHEMA IF NOT EXISTS {p}sch;")
    if st.needs_new_owner_role:
        setup.append(f"CREATE ROLE {p}new_owner LOGIN;")
    effective = st.effective
    if effective:
        setup.append(f"CREATE ROLE {p}owner LOGIN;")
        if _privilege_denied(case, a):
            setup.append(f"CREATE ROLE {p}actor LOGIN;")
        setup.append(f"GRANT USAGE ON SCHEMA public TO {p}owner;")
        if _privilege_denied(case, a):
            setup.append(f"GRANT USAGE ON SCHEMA public TO {p}actor;")
        locus = "fixture.privilege_state"
    if st.needs_table:
        ft = st.fixture_table
        setup.append(
            f"CREATE TABLE {ft} ({p}id integer PRIMARY KEY, "
            f"{p}col integer, {p}txt text);"
        )
        if st.needs_constraint:
            setup.append(
                f"ALTER TABLE {ft} ADD CONSTRAINT {st.constraint_name} "
                f"CHECK ({p}col > 0);"
            )
        if st.needs_index:
            setup.append(
                f"CREATE INDEX {st.index_name} ON {ft} ({p}col);"
            )
        if st.needs_parent:
            setup.append(
                f"CREATE TABLE {st.parent_name} ({p}id integer PRIMARY KEY, "
                f"{p}col integer);"
            )
    if effective and not st.is_session_user_escape:
        if st.needs_table:
            setup.append(
                f"ALTER TABLE {st.fixture_table} OWNER TO {p}owner;"
            )
        setup.append(f"SET ROLE {effective};")
    elif effective and st.is_session_user_escape:
        setup.append(f"SET ROLE {effective};")
    if case.kind == "RISK":
        setup.append("BEGIN;")
        locus = "target.transaction_boundary"
    if not setup:
        setup.append("SELECT 1 AS no_fixture_required;")
    return setup, locus


def _build_assert(case: AlterTableFactorCase) -> tuple[str, ...]:
    a = _baseline(case)
    p = case.object_prefix
    lines: list[str] = []
    if case.kind == "RISK":
        lines.append(
            "COMMIT;" if case.factor_value == "commit"
            else "ROLLBACK;"
        )
    lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    lines.extend(_probe_select(case, a, p))
    return tuple(lines)


def _tables_to_drop(
    case: AlterTableFactorCase, st: _FixtureState
) -> list[str]:
    p = case.object_prefix
    tables: list[str] = []
    if st.needs_table:
        tables.append(st.fixture_table)
    if st.needs_parent:
        tables.append(st.parent_name)
    return tables


def _roles_to_drop(
    case: AlterTableFactorCase, a: dict[str, str], p: str
) -> list[str]:
    roles: list[str] = []
    if _effective_role(case, a, p):
        roles.append(f"{p}owner")
        if _privilege_denied(case, a):
            roles.append(f"{p}actor")
    if _needs_new_owner_role(a, p):
        roles.append(f"{p}new_owner")
    return roles


def _schemas_to_drop(
    case: AlterTableFactorCase, st: _FixtureState
) -> list[str]:
    p = case.object_prefix
    a = _baseline(case)
    schemas: list[str] = []
    if st.needs_schema:
        schemas.append(st.schema_name)
    if a.get("table_name_shape") == "schema_qualified":
        schemas.append(f"{p}sch")
    return schemas


def _build_pre_cleanup(
    case: AlterTableFactorCase, st: _FixtureState
) -> tuple[str, ...]:
    a = _baseline(case)
    p = case.object_prefix
    tables = _tables_to_drop(case, st)
    schemas = _schemas_to_drop(case, st)
    lines: list[str] = []
    if tables:
        lines.append(f"DROP TABLE IF EXISTS {', '.join(tables)} CASCADE;")
    for s in schemas:
        lines.append(f"DROP SCHEMA IF EXISTS {s} CASCADE;")
    for role in _roles_to_drop(case, a, p):
        lines.append(f"DROP ROLE IF EXISTS {role};")
    if not lines:
        lines.append("SELECT 1 AS residual_check_no_objects;")
    return tuple(lines)


def _build_cleanup(
    case: AlterTableFactorCase, st: _FixtureState
) -> tuple[str, ...]:
    a = _baseline(case)
    p = case.object_prefix
    tables = _tables_to_drop(case, st)
    schemas = _schemas_to_drop(case, st)
    lines: list[str] = []
    if st.effective:
        lines.append("RESET ROLE;")
    for s in schemas:
        lines.append(f"DROP SCHEMA IF EXISTS {s} CASCADE;")
    for role in _roles_to_drop(case, a, p):
        lines.append(f"DROP OWNED BY {role};")
        lines.append(f"DROP ROLE IF EXISTS {role};")
    if tables:
        lines.append(f"DROP TABLE IF EXISTS {', '.join(tables)} CASCADE;")
    if not lines:
        lines.append("SELECT 1 AS residual_check_no_objects;")
    return tuple(lines)


def _resolve_case(case: AlterTableFactorCase) -> _CasePlan:
    st = _compute_state(case)
    setup, locus = _build_setup(case, st)
    target = _build_target(case, st)
    assert_lines = _build_assert(case)
    pre_cleanup = _build_pre_cleanup(case, st)
    cleanup = _build_cleanup(case, st)
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


def resolve_alter_table_factor_witness(
    case: AlterTableFactorCase | AlterTableFactorExtensionCase,
    repository_root: Path,
) -> AlterTableFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return AlterTableFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_alter_table(sql: str) -> int:
    """Count the single credited ALTER TABLE inside the fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(re.findall(r"(?im)^\s*ALTER\s+TABLE\b", region))


def _header(case: AlterTableFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : ALTER TABLE "
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


def render_alter_table_factor_case(
    case: AlterTableFactorCase | AlterTableFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic ALTER TABLE regress program."""

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地表和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。")
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


def generate_alter_table_factor_programs(
    baseline_plan: object,
    extension_plan: object,
    out_dir: Path,
) -> int:
    """Write every baseline + extension program; return the file count."""

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    count = 0
    for case in baseline_plan.cases:
        text = render_alter_table_factor_case(case, Path("."))
        (out / case.sql_filename).write_text(text, encoding="utf-8")
        count += 1
    for case in extension_plan.cases:
        text = render_alter_table_factor_case(case, Path("."))
        (out / case.sql_filename).write_text(text, encoding="utf-8")
        count += 1
    return count


__all__ = [
    "AlterTableFactorRenderError",
    "AlterTableFactorWitness",
    "render_alter_table_factor_case",
    "resolve_alter_table_factor_witness",
    "count_primary_alter_table",
    "generate_alter_table_factor_programs",
]
