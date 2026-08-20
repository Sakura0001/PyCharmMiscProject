"""Render complete PostgreSQL 18.4 SECURITY LABEL factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

SECURITY LABEL is a DDL-utility statement that attaches a security
label to a database object.  Some object types (table, column,
materialized view, view) require a TABLE fixture, so the bookend
(DROP TABLE IF EXISTS) applies.  All catalog oracles schema-qualify
``pg_catalog`` (exempt from the file-prefix style gate).  Every catalog
SELECT carries a top-level ``ORDER BY`` and ends ``ORDER BY count(*)
LIMIT 1``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .security_label_factor_extension import (
    SecurityLabelFactorExtensionCase,
    _present_failure_pair,
)
from .security_label_factor_loop import (
    SecurityLabelFactorCase,
    SecurityLabelFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/security_label/"
    "security_label.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/security_label/"
    "security_label.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-21"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

# Objects stored in pg_shseclabel (shared cluster-wide catalog).
_SHARED_OBJECT_TYPES = frozenset(
    {"database", "role", "tablespace", "subscription"}
)


class SecurityLabelFactorRenderError(ValueError):
    """Raised when a SECURITY LABEL case cannot be rendered."""


@dataclass(frozen=True)
class SecurityLabelFactorWitness:
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


# Fixture table: object_type -> (setup_lines, target_fmt, cleanup_lines,
# tables_to_drop_for_bookend).  {p} = object_prefix; {{provider_clause}}
# and {{label}} are substituted later by _build_target.
_FIXTURES: dict[str, tuple[tuple[str, ...], str, tuple[str, ...], tuple[str, ...]]] = {
    "table": (
        ("CREATE TABLE {p}tbl (id int);",),
        "SECURITY LABEL {{provider_clause}}ON TABLE {p}tbl IS {{label}};",
        ("DROP TABLE IF EXISTS {p}tbl;",),
        ("{p}tbl",),
    ),
    "column": (
        ("CREATE TABLE {p}tbl (id int);",),
        "SECURITY LABEL {{provider_clause}}ON COLUMN {p}tbl.id IS {{label}};",
        ("DROP TABLE IF EXISTS {p}tbl;",),
        ("{p}tbl",),
    ),
    "aggregate": (
        (
            "CREATE AGGREGATE {p}agg(int) "
            "(SFUNC = int4_sum, STYPE = bigint, INITCOND = '0');",
        ),
        "SECURITY LABEL {{provider_clause}}ON AGGREGATE {p}agg(int) IS {{label}};",
        ("DROP AGGREGATE IF EXISTS {p}agg(int);",),
        (),
    ),
    "database": (
        (),
        "SECURITY LABEL {{provider_clause}}ON DATABASE {p}db IS {{label}};",
        (),
        (),
    ),
    "domain": (
        ("CREATE DOMAIN {p}dom AS int;",),
        "SECURITY LABEL {{provider_clause}}ON DOMAIN {p}dom IS {{label}};",
        ("DROP DOMAIN IF EXISTS {p}dom;",),
        (),
    ),
    "event_trigger": (
        (
            "CREATE FUNCTION {p}etfn() RETURNS event_trigger "
            "AS $$BEGIN NULL; END;$$ LANGUAGE plpgsql;",
            "CREATE EVENT TRIGGER {p}et ON ddl_command_start "
            "EXECUTE FUNCTION {p}etfn();",
        ),
        "SECURITY LABEL {{provider_clause}}ON EVENT TRIGGER {p}et IS {{label}};",
        (
            "DROP EVENT TRIGGER IF EXISTS {p}et;",
            "DROP FUNCTION IF EXISTS {p}etfn();",
        ),
        (),
    ),
    "foreign_table": (
        (
            "CREATE FOREIGN DATA WRAPPER {p}fdw;",
            "CREATE SERVER {p}srv FOREIGN DATA WRAPPER {p}fdw;",
            "CREATE FOREIGN TABLE {p}ft (id int) SERVER {p}srv;",
        ),
        "SECURITY LABEL {{provider_clause}}ON FOREIGN TABLE {p}ft IS {{label}};",
        (
            "DROP FOREIGN TABLE IF EXISTS {p}ft;",
            "DROP SERVER IF EXISTS {p}srv;",
            "DROP FOREIGN DATA WRAPPER IF EXISTS {p}fdw;",
        ),
        (),
    ),
    "function": (
        (
            "CREATE FUNCTION {p}fn() RETURNS int "
            "AS $$SELECT 1;$$ LANGUAGE sql;",
        ),
        "SECURITY LABEL {{provider_clause}}ON FUNCTION {p}fn() IS {{label}};",
        ("DROP FUNCTION IF EXISTS {p}fn();",),
        (),
    ),
    "large_object": (
        ("SELECT lo_create(16399) AS large_object_created;",),
        "SECURITY LABEL {{provider_clause}}ON LARGE OBJECT 16399 IS {{label}};",
        ("SELECT lo_unlink(16399);",),
        (),
    ),
    "materialized_view": (
        (
            "CREATE TABLE {p}tbl (id int);",
            "CREATE MATERIALIZED VIEW {p}mv AS SELECT * FROM {p}tbl;",
        ),
        "SECURITY LABEL {{provider_clause}}ON MATERIALIZED VIEW {p}mv IS {{label}};",
        (
            "DROP MATERIALIZED VIEW IF EXISTS {p}mv;",
            "DROP TABLE IF EXISTS {p}tbl;",
        ),
        ("{p}tbl",),
    ),
    "language": (
        (),
        "SECURITY LABEL {{provider_clause}}ON LANGUAGE plpgsql IS {{label}};",
        (),
        (),
    ),
    "procedure": (
        (
            "CREATE PROCEDURE {p}proc() "
            "AS $$BEGIN NULL; END;$$ LANGUAGE plpgsql;",
        ),
        "SECURITY LABEL {{provider_clause}}ON PROCEDURE {p}proc() IS {{label}};",
        ("DROP PROCEDURE IF EXISTS {p}proc();",),
        (),
    ),
    "publication": (
        ("CREATE PUBLICATION {p}pub;",),
        "SECURITY LABEL {{provider_clause}}ON PUBLICATION {p}pub IS {{label}};",
        ("DROP PUBLICATION IF EXISTS {p}pub;",),
        (),
    ),
    "role": (
        ("CREATE ROLE {p}role;",),
        "SECURITY LABEL {{provider_clause}}ON ROLE {p}role IS {{label}};",
        ("DROP ROLE IF EXISTS {p}role;",),
        (),
    ),
    "routine": (
        (
            "CREATE FUNCTION {p}fn() RETURNS int "
            "AS $$SELECT 1;$$ LANGUAGE sql;",
        ),
        "SECURITY LABEL {{provider_clause}}ON ROUTINE {p}fn() IS {{label}};",
        ("DROP FUNCTION IF EXISTS {p}fn();",),
        (),
    ),
    "schema": (
        ("CREATE SCHEMA {p}sch;",),
        "SECURITY LABEL {{provider_clause}}ON SCHEMA {p}sch IS {{label}};",
        ("DROP SCHEMA IF EXISTS {p}sch CASCADE;",),
        (),
    ),
    "sequence": (
        ("CREATE SEQUENCE {p}seq;",),
        "SECURITY LABEL {{provider_clause}}ON SEQUENCE {p}seq IS {{label}};",
        ("DROP SEQUENCE IF EXISTS {p}seq;",),
        (),
    ),
    "subscription": (
        (),
        "SECURITY LABEL {{provider_clause}}ON SUBSCRIPTION {p}sub IS {{label}};",
        (),
        (),
    ),
    "tablespace": (
        (),
        "SECURITY LABEL {{provider_clause}}ON TABLESPACE {p}ts IS {{label}};",
        (),
        (),
    ),
    "type": (
        ("CREATE TYPE {p}typ AS (x int);",),
        "SECURITY LABEL {{provider_clause}}ON TYPE {p}typ IS {{label}};",
        ("DROP TYPE IF EXISTS {p}typ;",),
        (),
    ),
    "view": (
        (
            "CREATE TABLE {p}tbl (id int);",
            "CREATE VIEW {p}vw AS SELECT * FROM {p}tbl;",
        ),
        "SECURITY LABEL {{provider_clause}}ON VIEW {p}vw IS {{label}};",
        (
            "DROP VIEW IF EXISTS {p}vw;",
            "DROP TABLE IF EXISTS {p}tbl;",
        ),
        ("{p}tbl",),
    ),
}


def _fixture_spec(
    ot: str, p: str
) -> tuple[tuple[str, ...], str, tuple[str, ...], tuple[str, ...]]:
    spec = _FIXTURES.get(ot, _FIXTURES["table"])
    setup = tuple(s.format(p=p) for s in spec[0])
    target = spec[1].format(p=p)
    cleanup = tuple(c.format(p=p) for c in spec[2])
    tables = tuple(t.format(p=p) for t in spec[3])
    return setup, target, cleanup, tables


def _synthetic_case(
    ext: SecurityLabelFactorExtensionCase,
) -> SecurityLabelFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "object_type"
        factor_value = assignment.get("object_type", "table")
    return SecurityLabelFactorCase(
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
    case: SecurityLabelFactorCase | SecurityLabelFactorExtensionCase,
) -> SecurityLabelFactorCase:
    if isinstance(case, SecurityLabelFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: SecurityLabelFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _label_text(a: dict[str, str]) -> str:
    """The IS clause value for SECURITY LABEL."""

    if a.get("label_value") == "null_removes_label":
        return "NULL"
    shape = a.get("label_string_shape", "valid_label")
    if shape == "empty_string":
        return "''"
    if shape == "special_characters_label":
        return "'a:b:c@special'"
    return "'classification'"


def _label_text_for_query(a: dict[str, str]) -> str:
    text = _label_text(a)
    if text == "NULL":
        return ""
    return text.strip("'")


def _provider_name(a: dict[str, str]) -> str:
    pn = a.get("provider_name_shape", "registered_provider")
    if pn == "unregistered_provider":
        return "no_such_provider"
    return "seclabel"


def _provider_clause(a: dict[str, str]) -> str:
    if a.get("provider_name_shape") == "unregistered_provider":
        return "FOR no_such_provider "
    if a.get("for_provider_clause") == "explicit_provider":
        return f"FOR {_provider_name(a)} "
    return ""


def _object_missing(a: dict[str, str]) -> bool:
    return (
        a.get("object_existence") == "object_not_exists"
        or a.get("nonexistent_object") == "target_object_does_not_exist"
        or a.get("prerequisite_object") == "object_not_exists"
        or a.get("object_name_shape") == "non_existing_name"
    )


def _non_owner(a: dict[str, str]) -> bool:
    return (
        a.get("executor_privilege") in
        {"non_owner", "non_superuser_no_provider_privilege"}
        or a.get("privilege_insufficient")
        == "non_superuser_without_provider_privilege"
    )


def _wrong_column(a: dict[str, str]) -> bool:
    return a.get("column_name_shape") == "nonexistent_column"


def _verify_query(
    ot: str, p: str, a: dict[str, str]
) -> str:
    """Catalog-audit oracle for SECURITY LABEL verification."""

    mode = a.get("verification_mode", "pg_seclabel_catalog_query")
    if mode == "error_assertion":
        return (
            "SELECT 1 AS error_assertion_executed "
            "ORDER BY error_assertion_executed;"
        )
    table = (
        "pg_catalog.pg_shseclabels"
        if ot in _SHARED_OBJECT_TYPES
        else "pg_catalog.pg_seclabels"
    )
    provider = _provider_name(a)
    label_for_query = _label_text_for_query(a)
    return (
        f"SELECT count(*) AS label_count "
        f"FROM {table} "
        f"WHERE provider = '{provider}' "
        f"AND label = '{label_for_query}' "
        f"ORDER BY count(*) LIMIT 1;"
    )


def _tables_to_drop(
    a: dict[str, str], p: str
) -> list[str]:
    """Fixture tables the case CREATEs (for bookend gate)."""

    if _object_missing(a):
        return []
    ot = a.get("object_type", "table")
    _, _, _, tables = _fixture_spec(ot, p)
    return list(tables)


def _build_target(
    a: dict[str, str], p: str
) -> str:
    """The primary SECURITY LABEL statement for the active object_type."""

    ot = a.get("object_type", "table")
    pc = _provider_clause(a)
    label = _label_text(a)

    if _object_missing(a):
        return f"SECURITY LABEL {pc}ON TABLE {p}no_such_tbl IS {label};"
    if _wrong_column(a):
        return f"SECURITY LABEL {pc}ON COLUMN id IS {label};"

    _, target_fmt, _, _ = _fixture_spec(ot, p)
    return target_fmt.format(provider_clause=pc, label=label)


def _remove_label_stmt(
    a: dict[str, str], p: str
) -> str | None:
    """The SECURITY LABEL ... IS NULL cleanup statement, if applicable."""

    if _object_missing(a) or _wrong_column(a):
        return None
    if a.get("cleanup_mode") != "security_label_is_null":
        return None
    ot = a.get("object_type", "table")
    pc = _provider_clause(a)
    _, target_fmt, _, _ = _fixture_spec(ot, p)
    return target_fmt.format(provider_clause=pc, label="NULL")


def _resolve_case(
    case: SecurityLabelFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    ot = a.get("object_type", "table")
    missing = _object_missing(a)
    non_owner = _non_owner(a)
    wrong_col = _wrong_column(a)

    setup: list[str] = []
    locus = "target.security_label"

    # --- non-owner role fixture ----------------------------------
    if non_owner:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- the target object fixture -------------------------------
    if not missing and not wrong_col:
        spec_setup, _, _, _ = _fixture_spec(ot, p)
        setup.extend(spec_setup)
        locus = f"fixture.{ot}"
    elif missing:
        setup.append("SELECT 1 AS target_object_intentionally_absent;")
        locus = "fixture.object_missing"
    else:
        spec_setup, _, _, _ = _fixture_spec(ot, p)
        setup.extend(spec_setup)
        locus = "fixture.wrong_column"

    # --- arm the non-owner role ---------------------------------
    if non_owner:
        setup.append(f"SET ROLE {p}actor;")

    # --- the primary target statement ---------------------------
    target = _build_target(a, p)

    # --- oracle / SQLSTATE assertion ----------------------------
    assert_lines: list[str] = []
    if non_owner:
        assert_lines.append("RESET ROLE;")
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    assert_lines.append(_verify_query(ot, p, a))

    # --- fixture cleanup spec ------------------------------------
    tables = _tables_to_drop(a, p)
    _, _, spec_cleanup, _ = (
        _fixture_spec(ot, p) if not missing else ((), "", (), ())
    )

    # --- pre-cleanup construction --------------------------------
    pre_cleanup: list[str] = []
    if tables:
        tbl_list = ", ".join(tables)
        pre_cleanup.append(f"DROP TABLE IF EXISTS {tbl_list} CASCADE;")
        for item in spec_cleanup:
            if not item.startswith("DROP TABLE"):
                pre_cleanup.append(item)
    else:
        pre_cleanup.extend(spec_cleanup)
    if non_owner:
        pre_cleanup.extend(
            [
                f"DROP OWNED BY {p}actor CASCADE;",
                f"DROP ROLE IF EXISTS {p}actor;",
            ]
        )
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # --- cleanup construction ------------------------------------
    # For table-creating cases, DROP TABLE must be the LAST ; stmt.
    cleanup_list: list[str] = []
    remove_label = _remove_label_stmt(a, p)
    if remove_label is not None:
        cleanup_list.append(remove_label)
    if non_owner:
        cleanup_list.extend(
            [
                f"DROP OWNED BY {p}actor CASCADE;",
                f"DROP ROLE IF EXISTS {p}actor;",
            ]
        )
    if tables:
        for item in spec_cleanup:
            if not item.startswith("DROP TABLE"):
                cleanup_list.append(item)
        tbl_list = ", ".join(tables)
        cleanup_list.append(f"DROP TABLE IF EXISTS {tbl_list};")
    else:
        cleanup_list.extend(spec_cleanup)
    if not cleanup_list:
        cleanup_list.append("SELECT 1 AS residual_check_no_objects;")

    on_error_off = case.outcome == "expected_failure"
    return _CasePlan(
        target_fragment=target,
        setup_lines=tuple(setup),
        assert_lines=tuple(assert_lines),
        pre_cleanup_lines=tuple(pre_cleanup),
        cleanup_lines=tuple(cleanup_list),
        on_error_off=on_error_off,
        semantic_locus=locus,
    )


def resolve_security_label_factor_witness(
    case: SecurityLabelFactorCase | SecurityLabelFactorExtensionCase,
    repository_root: Path,
) -> SecurityLabelFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return SecurityLabelFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_security_label(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*SECURITY\s+LABEL\b", region)
    )


def _header(case: SecurityLabelFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : SECURITY LABEL ON {case.factor_key}="
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


def render_security_label_factor_case(
    case: SecurityLabelFactorCase | SecurityLabelFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 SECURITY LABEL。")
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
    case: SecurityLabelFactorCase | SecurityLabelFactorExtensionCase,
    out: Path,
) -> None:
    text = render_security_label_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_security_label_factor_programs(
    baseline_plan: SecurityLabelFactorLoopPlan,
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
    "SecurityLabelFactorRenderError",
    "SecurityLabelFactorWitness",
    "count_primary_security_label",
    "generate_security_label_factor_programs",
    "render_security_label_factor_case",
    "resolve_security_label_factor_witness",
]
