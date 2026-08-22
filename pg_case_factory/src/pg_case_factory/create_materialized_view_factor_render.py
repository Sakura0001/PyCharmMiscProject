"""Render complete PostgreSQL 18.4 CREATE MATERIALIZED VIEW factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the byte-level
witness validator (which re-renders and compares) can never diverge from
the bytes actually written.

CREATE MATERIALIZED VIEW is a relation-creating DDL statement: the target
is a ``pg_class`` row with ``relkind='m'`` (also visible in
``pg_catalog.pg_matviews``).  All catalog oracles schema-qualify
``pg_catalog.pg_matviews`` (exempt from the file-prefix style gate) and
carry a top-level ``ORDER BY count(*)``.  No case ever emits a
``CREATE TABLE`` statement (fixture sources and conflicting relations are
``CREATE VIEW``), so the shared bookend (DROP TABLE IF EXISTS) never
applies — ``_tables_to_drop`` always returns ``[]`` (bookend N/A).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .cleanup_bookend import DropSpec, build_cleanup, build_pre_cleanup
from .create_materialized_view_factor_extension import (
    CreateMaterializedViewFactorExtensionCase,
    _present_failure_pair,
)
from .create_materialized_view_factor_loop import (
    CreateMaterializedViewFactorCase,
    CreateMaterializedViewFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/materialized_view/"
    "create_materialized_view.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/materialized_view/"
    "create_materialized_view.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_DEFAULT_SCHEMA = "public"


class CreateMaterializedViewFactorRenderError(ValueError):
    """Raised when a CREATE MATERIALIZED VIEW case cannot be rendered."""


@dataclass(frozen=True)
class CreateMaterializedViewFactorWitness:
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
    ext: CreateMaterializedViewFactorExtensionCase,
) -> CreateMaterializedViewFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get(
            "target_action", "create_matview"
        )
    return CreateMaterializedViewFactorCase(
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
    case: CreateMaterializedViewFactorCase
    | CreateMaterializedViewFactorExtensionCase,
) -> CreateMaterializedViewFactorCase:
    if isinstance(
        case, CreateMaterializedViewFactorExtensionCase
    ):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateMaterializedViewFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _base_name(p: str) -> str:
    return f"{p}mv"


def _qualify(name_shape: str, base: str) -> str:
    if name_shape == "schema_qualified":
        return f"{_DEFAULT_SCHEMA}.{base}"
    if name_shape == "quoted_identifier":
        return f'"{base}"'
    return base


def _name_shape(a: dict[str, str]) -> str:
    return a.get("name_shape", "plain_identifier")


def _mv_qualified(a: dict[str, str], p: str) -> str:
    return _qualify(_name_shape(a), _base_name(p))


def _if_not_exists_sql(a: dict[str, str]) -> str:
    return (
        "IF NOT EXISTS " if a.get("if_not_exists_clause") == "present" else ""
    )


def _needs_source_view(a: dict[str, str]) -> bool:
    """Whether the case needs a fixture source VIEW for its query."""

    if a.get("dependency_state") == "missing_dependency":
        return False
    if a.get("query_source_state") == "source_table_missing":
        return False
    return a.get("query_shape") == "select_from_table"


def _needs_conflict_view(a: dict[str, str]) -> bool:
    return a.get("target_object_state") == "exists_conflict"


def _needs_pre_matview(a: dict[str, str]) -> bool:
    return a.get("target_object_state") == "exists"


def _needs_role(a: dict[str, str]) -> bool:
    return a.get("privilege_context") == "insufficient_privilege"


def _needs_sec_function(a: dict[str, str]) -> bool:
    return (
        a.get("constraint_boundary") == "security_restricted_operation"
    )


def _is_failure(a: dict[str, str]) -> bool:
    return a.get("expected_status") == "failure"


def _query_sql(a: dict[str, str], p: str) -> str:
    """The AS-query fragment for the materialized view."""

    qshape = a.get("query_shape", "minimal_query")
    ctype = a.get("column_type_coverage", "representative_types")
    # Failure overrides: a missing dependency / missing source makes the
    # query reference a non-existent relation regardless of query_shape.
    if a.get("dependency_state") == "missing_dependency":
        return f"SELECT * FROM {p}nodep"
    if a.get("query_source_state") == "source_table_missing":
        return f"SELECT * FROM {p}nosrc"
    if _needs_sec_function(a):
        return f"SELECT {p}secfn() AS c1"
    if qshape == "explicit_values":
        if ctype == "representative_types":
            return "SELECT 1::int AS c1, 'x'::text AS c2"
        return "SELECT 1 AS c1, 2 AS c2"
    if qshape == "select_from_table":
        return f"SELECT c1, c2 FROM {p}src"
    if qshape == "cte_source":
        return (
            f"WITH {p}cte AS (SELECT 1 AS c1, 2 AS c2) "
            f"SELECT c1, c2 FROM {p}cte"
        )
    return "SELECT 1"


def _column_count(a: dict[str, str]) -> int:
    qshape = a.get("query_shape", "minimal_query")
    if qshape == "minimal_query" and not _needs_sec_function(a):
        return 1
    return 2


def _column_list_sql(a: dict[str, str]) -> str:
    if a.get("column_list_clause") != "present":
        return ""
    count = _column_count(a)
    names = ", ".join(f"c{i + 1}" for i in range(count))
    return f"({names})"


def _using_sql(a: dict[str, str]) -> str:
    if a.get("using_clause") != "present":
        return ""
    return "USING heap"


def _storage_parameter_sql(a: dict[str, str]) -> str:
    if a.get("storage_parameter_clause") != "present":
        return ""
    return "WITH (autovacuum_enabled=true)"


def _tablespace_sql(a: dict[str, str]) -> str:
    if a.get("tablespace_clause") != "present":
        return ""
    return "TABLESPACE pg_default"


def _data_clause_sql(a: dict[str, str]) -> str:
    if a.get("data_clause") == "with_no_data":
        return "WITH NO DATA"
    return "WITH DATA"


def _probe_select(
    case: CreateMaterializedViewFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit or effect oracle, or None for error_assertion."""

    mode = a.get("verification_mode", "catalog_query")
    if mode == "error_assertion":
        return None
    base = _base_name(p)
    # A failure case leaves no scannable matview (except exists/exists_conflict
    # where a pre-existing relation remains, but it is not the new matview).
    absent = _is_failure(a)
    if mode == "returned_rows":
        if absent or a.get("data_clause") == "with_no_data":
            # An unscannable (WITH NO DATA) or absent matview cannot be
            # scanned; assert the catalog state instead.
            cmp_op = "=" if absent else "> 0"
            alias = "returned_rows_absent" if absent else "mv_not_populated"
            extra = " AND NOT ispopulated" if not absent else ""
            return (
                f"SELECT count(*) {cmp_op} AS {alias} "
                "FROM pg_catalog.pg_matviews "
                f"WHERE matviewname = '{base}'{extra} "
                "ORDER BY count(*) LIMIT 1;"
            )
        return (
            f"SELECT count(*) AS returned_rows FROM {base} "
            "ORDER BY count(*) LIMIT 1;"
        )
    if mode == "effect_query":
        if absent:
            return (
                f"SELECT count(*) = 0 AS mv_not_populated "
                "FROM pg_catalog.pg_matviews "
                f"WHERE matviewname = '{base}' "
                "ORDER BY count(*) LIMIT 1;"
            )
        populated = a.get("data_clause") != "with_no_data"
        cmp = "> 0" if populated else "= 0"
        extra = " AND ispopulated" if populated else " AND NOT ispopulated"
        return (
            f"SELECT count(*) {cmp} AS mv_populated "
            "FROM pg_catalog.pg_matviews "
            f"WHERE matviewname = '{base}'{extra} "
            "ORDER BY count(*) LIMIT 1;"
        )
    # catalog_query
    cmp_op = "= 0" if absent else "> 0"
    alias = "mv_absent" if absent else "mv_present"
    return (
        f"SELECT count(*) {cmp_op} AS {alias} "
        "FROM pg_catalog.pg_matviews "
        f"WHERE matviewname = '{base}' "
        "ORDER BY count(*) LIMIT 1;"
    )


def _tables_to_drop(
    case: CreateMaterializedViewFactorCase,
) -> list[str]:
    """Fixture tables the case CREATEs.

    CREATE MATERIALIZED VIEW never emits ``CREATE TABLE`` (fixture sources
    and conflicting relations are ``CREATE VIEW``), so the bookend
    (DROP TABLE IF EXISTS) is never emitted.
    """
    return []


def _resolve_case(
    case: CreateMaterializedViewFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix

    setup: list[str] = []
    locus = "target.materialized_view"

    # --- role fixture (insufficient_privilege) -----------------------
    if _needs_role(a):
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- security-definer function fixture ----------------------------
    if _needs_sec_function(a):
        setup.append(
            f"CREATE FUNCTION {p}secfn() RETURNS int "
            "LANGUAGE plpgsql SECURITY DEFINER AS "
            "$$ BEGIN RETURN 1; END $$;"
        )
        locus = "fixture.security_restricted_operation"

    # --- source VIEW fixture (select_from_table + source exists) -----
    if _needs_source_view(a):
        setup.append(
            f"CREATE VIEW {p}src AS SELECT 1::int AS c1, 'x'::text AS c2;"
        )
        locus = "fixture.source_view"

    # --- conflicting VIEW fixture (exists_conflict) ------------------
    if _needs_conflict_view(a):
        setup.append(f"CREATE VIEW {_base_name(p)} AS SELECT 1 AS c1;")
        locus = "fixture.conflicting_relation"

    # --- pre-existing matview fixture (exists) ------------------------
    if _needs_pre_matview(a):
        setup.append(
            f"CREATE MATERIALIZED VIEW {_base_name(p)} AS SELECT 1 AS c1;"
        )
        locus = "fixture.pre_existing_matview"

    # --- arm the effective role --------------------------------------
    if _needs_role(a):
        setup.append(f"SET ROLE {p}actor;")
        locus = "fixture.privilege_state"

    # --- the primary target statement --------------------------------
    name = _mv_qualified(a, p)
    parts = [
        f"CREATE MATERIALIZED VIEW {_if_not_exists_sql(a)}{name}",
    ]
    col_list = _column_list_sql(a)
    if col_list:
        parts.append(col_list)
    using = _using_sql(a)
    if using:
        parts.append(using)
    storage = _storage_parameter_sql(a)
    if storage:
        parts.append(storage)
    tablespace = _tablespace_sql(a)
    if tablespace:
        parts.append(tablespace)
    parts.append(f"AS {_query_sql(a, p)}")
    parts.append(_data_clause_sql(a))
    target = " ".join(parts) + ";"

    # --- oracle / SQLSTATE assertion ---------------------------------
    assert_lines: list[str] = []
    if _needs_role(a):
        assert_lines.append("RESET ROLE;")
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    probe = _probe_select(case, a, p)
    if probe is not None:
        assert_lines.append(probe)

    # --- cleanup construction (shared idempotent bookends) -----------
    # Migrated to cleanup_bookend so every DROP carries IF EXISTS and
    # DROP OWNED BY is unreachable in pre-cleanup: the {p}actor role is
    # created by setup, so on a fresh database the role does not exist yet
    # at pre-cleanup time and DROP OWNED BY would crash (ON_ERROR_STOP=1)
    # before the target statement reaches execution.  Pre-cleanup drops
    # roles via DROP ROLE IF EXISTS only; the post-target cleanup runs
    # DROP OWNED BY then DROP ROLE IF EXISTS once setup has created the
    # role.  This package never emits CREATE TABLE (fixture sources and
    # conflicting relations are CREATE VIEW), so no DROP TABLE anchor is
    # emitted (table-bookend gate is table-less-exempt here).
    specs: list[DropSpec] = [DropSpec("MATERIALIZED VIEW", name)]
    if _needs_conflict_view(a):
        specs.append(DropSpec("VIEW", _base_name(p)))
    if _needs_source_view(a):
        specs.append(DropSpec("VIEW", f"{p}src"))
    if _needs_sec_function(a):
        specs.append(DropSpec("FUNCTION", f"{p}secfn", args="()"))

    role_list = [f"{p}actor"] if _needs_role(a) else []
    pre_bookend = build_pre_cleanup(
        specs=tuple(specs),
        roles=role_list,
    )
    cln_bookend = build_cleanup(
        specs=tuple(specs),
        roles=role_list,
        drop_owned=bool(role_list),
        reset_role=bool(role_list),
    )
    pre_cleanup = list(pre_bookend.statements)
    cleanup = list(cln_bookend.statements)

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


def resolve_create_materialized_view_factor_witness(
    case: CreateMaterializedViewFactorCase
    | CreateMaterializedViewFactorExtensionCase,
    repository_root: Path,
) -> CreateMaterializedViewFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateMaterializedViewFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_create_materialized_view(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(
            r"(?im)^\s*CREATE\s+MATERIALIZED\s+VIEW\b", region
        )
    )


def _header(case: CreateMaterializedViewFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE MATERIALIZED VIEW "
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


def render_create_materialized_view_factor_case(
    case: CreateMaterializedViewFactorCase
    | CreateMaterializedViewFactorExtensionCase,
    repository_root: Path,
) -> str:
    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    # Boundary SELECT so the CREATE MATERIALIZED VIEW starts its own
    # ';'-segment at column 0 (the \set meta-command has no terminator).
    lines.append("SELECT 1 AS setup_boundary;")
    lines.append("-- 2. 创建完整本地规则和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 CREATE MATERIALIZED VIEW。")
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
    case: CreateMaterializedViewFactorCase
    | CreateMaterializedViewFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_materialized_view_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_materialized_view_factor_programs(
    baseline_plan: CreateMaterializedViewFactorLoopPlan,
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
    "CreateMaterializedViewFactorRenderError",
    "CreateMaterializedViewFactorWitness",
    "count_primary_create_materialized_view",
    "generate_create_materialized_view_factor_programs",
    "render_create_materialized_view_factor_case",
    "resolve_create_materialized_view_factor_witness",
]
