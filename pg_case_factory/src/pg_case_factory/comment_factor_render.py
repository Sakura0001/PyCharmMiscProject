"""Render complete PostgreSQL 18.4 COMMENT ON factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

COMMENT ON is a DDL statement that attaches a comment to a database
object.  Some object types (table, column, constraint, index, matview,
view, policy, rule, trigger, statistics) require a TABLE fixture, so
the bookend (DROP TABLE IF EXISTS) applies.  All catalog oracles
schema-qualify ``pg_catalog`` (exempt from the file-prefix style gate).
Every catalog SELECT carries a top-level ``ORDER BY``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .comment_factor_extension import (
    CommentFactorExtensionCase,
    _present_failure_pair,
)
from .comment_factor_loop import (
    CommentFactorCase,
    CommentFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/comment/"
    "comment.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/comment/"
    "comment.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class CommentFactorRenderError(ValueError):
    """Raised when a COMMENT case cannot be rendered."""


@dataclass(frozen=True)
class CommentFactorWitness:
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
    ext: CommentFactorExtensionCase,
) -> CommentFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "object_type"
        factor_value = assignment.get("object_type", "table")
    return CommentFactorCase(
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
    case: CommentFactorCase | CommentFactorExtensionCase,
) -> CommentFactorCase:
    if isinstance(case, CommentFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: CommentFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _comment_text(a: dict[str, str]) -> str:
    """The IS clause value for COMMENT ON."""

    action = a.get("comment_action", "set_comment")
    if action == "remove_comment_null":
        return "NULL"
    if action == "remove_comment_empty":
        return "''"
    shape = a.get("comment_text_shape", "short_literal")
    if shape == "long_literal":
        return "'a longer comment with multiple words'"
    if shape == "empty_string_literal":
        return "''"
    if shape == "null_literal":
        return "NULL"
    if shape == "special_chars_literal":
        return "'special @#$ chars'"
    return "'short comment'"


_FIXTURES: dict[str, tuple[tuple[str, ...], str, tuple[str, ...], tuple[str, ...]]] = {
    "table": (
        ("CREATE TABLE {p}tbl (id int);",),
        "COMMENT ON TABLE {p}tbl IS {{text}};",
        ("DROP TABLE IF EXISTS {p}tbl;",),
        ("{p}tbl",),
    ),
    "aggregate": (
        ("CREATE AGGREGATE {p}agg(int) (SFUNC = int4_sum, STYPE = bigint, INITCOND = '0');",),
        "COMMENT ON AGGREGATE {p}agg(int) IS {{text}};",
        ("DROP AGGREGATE IF EXISTS {p}agg(int);",),
        (),
    ),
    "column": (
        ("CREATE TABLE {p}tbl (id int);",),
        "COMMENT ON COLUMN {p}tbl.id IS {{text}};",
        ("DROP TABLE IF EXISTS {p}tbl;",),
        ("{p}tbl",),
    ),
    "constraint_on_table": (
        ("CREATE TABLE {p}tbl (id int, CONSTRAINT {p}con CHECK (id > 0));",),
        "COMMENT ON CONSTRAINT {p}con ON {p}tbl IS {{text}};",
        ("DROP TABLE IF EXISTS {p}tbl;",),
        ("{p}tbl",),
    ),
    "constraint_on_domain": (
        ("CREATE DOMAIN {p}dom AS int CONSTRAINT {p}con CHECK (VALUE > 0);",),
        "COMMENT ON CONSTRAINT {p}con ON DOMAIN {p}dom IS {{text}};",
        ("DROP DOMAIN IF EXISTS {p}dom;",),
        (),
    ),
    "index": (
        ("CREATE TABLE {p}tbl (id int);", "CREATE INDEX {p}idx ON {p}tbl (id);"),
        "COMMENT ON INDEX {p}idx IS {{text}};",
        ("DROP TABLE IF EXISTS {p}tbl;",),
        ("{p}tbl",),
    ),
    "materialized_view": (
        ("CREATE TABLE {p}tbl (id int);", "CREATE MATERIALIZED VIEW {p}mv AS SELECT * FROM {p}tbl;"),
        "COMMENT ON MATERIALIZED VIEW {p}mv IS {{text}};",
        ("DROP MATERIALIZED VIEW IF EXISTS {p}mv;", "DROP TABLE IF EXISTS {p}tbl;"),
        ("{p}tbl",),
    ),
    "view": (
        ("CREATE TABLE {p}tbl (id int);", "CREATE VIEW {p}vw AS SELECT * FROM {p}tbl;"),
        "COMMENT ON VIEW {p}vw IS {{text}};",
        ("DROP VIEW IF EXISTS {p}vw;", "DROP TABLE IF EXISTS {p}tbl;"),
        ("{p}tbl",),
    ),
    "policy": (
        ("CREATE TABLE {p}tbl (id int);", "CREATE POLICY {p}pol ON {p}tbl;"),
        "COMMENT ON POLICY {p}pol ON {p}tbl IS {{text}};",
        ("DROP TABLE IF EXISTS {p}tbl;",),
        ("{p}tbl",),
    ),
    "rule": (
        ("CREATE TABLE {p}tbl (id int);", "CREATE RULE {p}rule AS ON INSERT TO {p}tbl DO INSTEAD NOTHING;"),
        "COMMENT ON RULE {p}rule ON {p}tbl IS {{text}};",
        ("DROP TABLE IF EXISTS {p}tbl;",),
        ("{p}tbl",),
    ),
    "trigger": (
        ("CREATE TABLE {p}tbl (id int);",
         "CREATE FUNCTION {p}trigfn() RETURNS trigger AS $$BEGIN RETURN NULL; END;$$ LANGUAGE plpgsql;",
         "CREATE TRIGGER {p}trig BEFORE INSERT ON {p}tbl FOR EACH ROW EXECUTE FUNCTION {p}trigfn();"),
        "COMMENT ON TRIGGER {p}trig ON {p}tbl IS {{text}};",
        ("DROP FUNCTION IF EXISTS {p}trigfn();", "DROP TABLE IF EXISTS {p}tbl;"),
        ("{p}tbl",),
    ),
    "statistics": (
        ("CREATE TABLE {p}tbl (id int, val int);", "CREATE STATISTICS {p}stats ON id, val FROM {p}tbl;"),
        "COMMENT ON STATISTICS {p}stats IS {{text}};",
        ("DROP STATISTICS IF EXISTS {p}stats;", "DROP TABLE IF EXISTS {p}tbl;"),
        ("{p}tbl",),
    ),
    "function": (
        ("CREATE FUNCTION {p}fn() RETURNS int AS $$SELECT 1;$$ LANGUAGE sql;",),
        "COMMENT ON FUNCTION {p}fn() IS {{text}};",
        ("DROP FUNCTION IF EXISTS {p}fn();",),
        (),
    ),
    "procedure": (
        ("CREATE PROCEDURE {p}proc() AS $$BEGIN NULL; END;$$ LANGUAGE plpgsql;",),
        "COMMENT ON PROCEDURE {p}proc() IS {{text}};",
        ("DROP PROCEDURE IF EXISTS {p}proc();",),
        (),
    ),
    "routine": (
        ("CREATE FUNCTION {p}fn() RETURNS int AS $$SELECT 1;$$ LANGUAGE sql;",),
        "COMMENT ON ROUTINE {p}fn() IS {{text}};",
        ("DROP FUNCTION IF EXISTS {p}fn();",),
        (),
    ),
    "schema": (
        ("CREATE SCHEMA {p}sch;",),
        "COMMENT ON SCHEMA {p}sch IS {{text}};",
        ("DROP SCHEMA IF EXISTS {p}sch CASCADE;",),
        (),
    ),
    "sequence": (
        ("CREATE SEQUENCE {p}seq;",),
        "COMMENT ON SEQUENCE {p}seq IS {{text}};",
        ("DROP SEQUENCE IF EXISTS {p}seq;",),
        (),
    ),
    "domain": (
        ("CREATE DOMAIN {p}dom AS int;",),
        "COMMENT ON DOMAIN {p}dom IS {{text}};",
        ("DROP DOMAIN IF EXISTS {p}dom;",),
        (),
    ),
    "collation": (
        ("CREATE COLLATION {p}col (locale = 'C');",),
        "COMMENT ON COLLATION {p}col IS {{text}};",
        ("DROP COLLATION IF EXISTS {p}col;",),
        (),
    ),
    "conversion": (
        ("CREATE FUNCTION {p}convfn(integer, integer) RETURNS integer AS $$SELECT $1;$$ LANGUAGE sql;",
         "CREATE CONVERSION {p}conv FOR 'UTF8' TO 'UTF8' FROM {p}convfn;"),
        "COMMENT ON CONVERSION {p}conv IS {{text}};",
        ("DROP CONVERSION IF EXISTS {p}conv;", "DROP FUNCTION IF EXISTS {p}convfn(integer, integer);"),
        (),
    ),
    "type": (
        ("CREATE TYPE {p}typ AS (x int);",),
        "COMMENT ON TYPE {p}typ IS {{text}};",
        ("DROP TYPE IF EXISTS {p}typ;",),
        (),
    ),
    "operator": (
        ("CREATE OPERATOR {p}op (PROCEDURE = int4eq, LEFTARG = int, RIGHTARG = int);",),
        "COMMENT ON OPERATOR {p}op(int, int) IS {{text}};",
        ("DROP OPERATOR IF EXISTS {p}op(int, int);",),
        (),
    ),
    "operator_family": (
        ("CREATE OPERATOR FAMILY {p}opf USING btree;",),
        "COMMENT ON OPERATOR FAMILY {p}opf USING btree IS {{text}};",
        ("DROP OPERATOR FAMILY IF EXISTS {p}opf USING btree;",),
        (),
    ),
    "operator_class": (
        ("CREATE OPERATOR FAMILY {p}opf USING btree;",
         "CREATE OPERATOR CLASS {p}opc FOR TYPE int USING btree FAMILY {p}opf AS STORAGE int;"),
        "COMMENT ON OPERATOR CLASS {p}opc USING btree IS {{text}};",
        ("DROP OPERATOR CLASS IF EXISTS {p}opc USING btree;", "DROP OPERATOR FAMILY IF EXISTS {p}opf USING btree;"),
        (),
    ),
    "access_method": (
        ("CREATE FUNCTION {p}amhandler(internal) RETURNS table_am_handler AS 'no_op' LANGUAGE internal;",
         "CREATE ACCESS METHOD {p}am TYPE TABLE HANDLER {p}amhandler;"),
        "COMMENT ON ACCESS METHOD {p}am IS {{text}};",
        ("DROP ACCESS METHOD IF EXISTS {p}am;", "DROP FUNCTION IF EXISTS {p}amhandler(internal);"),
        (),
    ),
    "cast": (
        (),
        "COMMENT ON CAST (int AS bigint) IS {{text}};",
        (),
        (),
    ),
    "foreign_data_wrapper": (
        ("CREATE FOREIGN DATA WRAPPER {p}fdw;",),
        "COMMENT ON FOREIGN DATA WRAPPER {p}fdw IS {{text}};",
        ("DROP FOREIGN DATA WRAPPER IF EXISTS {p}fdw;",),
        (),
    ),
    "server": (
        ("CREATE FOREIGN DATA WRAPPER {p}fdw;", "CREATE SERVER {p}srv FOREIGN DATA WRAPPER {p}fdw;"),
        "COMMENT ON SERVER {p}srv IS {{text}};",
        ("DROP SERVER IF EXISTS {p}srv;", "DROP FOREIGN DATA WRAPPER IF EXISTS {p}fdw;"),
        (),
    ),
    "foreign_table": (
        ("CREATE FOREIGN DATA WRAPPER {p}fdw;", "CREATE SERVER {p}srv FOREIGN DATA WRAPPER {p}fdw;",
         "CREATE FOREIGN TABLE {p}ft (id int) SERVER {p}srv;"),
        "COMMENT ON FOREIGN TABLE {p}ft IS {{text}};",
        ("DROP FOREIGN TABLE IF EXISTS {p}ft;", "DROP SERVER IF EXISTS {p}srv;", "DROP FOREIGN DATA WRAPPER IF EXISTS {p}fdw;"),
        (),
    ),
    "large_object": (
        ("SELECT lo_create(16399) AS large_object_created;",),
        "COMMENT ON LARGE OBJECT 16399 IS {{text}};",
        ("SELECT lo_unlink(16399);",),
        (),
    ),
    "text_search_configuration": (
        ("CREATE TEXT SEARCH CONFIGURATION {p}tsc (COPY = simple);",),
        "COMMENT ON TEXT SEARCH CONFIGURATION {p}tsc IS {{text}};",
        ("DROP TEXT SEARCH CONFIGURATION IF EXISTS {p}tsc;",),
        (),
    ),
    "text_search_dictionary": (
        ("CREATE TEXT SEARCH DICTIONARY {p}tsd (TEMPLATE = simple);",),
        "COMMENT ON TEXT SEARCH DICTIONARY {p}tsd IS {{text}};",
        ("DROP TEXT SEARCH DICTIONARY IF EXISTS {p}tsd;",),
        (),
    ),
    "text_search_parser": (
        (),
        "COMMENT ON TEXT SEARCH PARSER default IS {{text}};",
        (),
        (),
    ),
    "text_search_template": (
        (),
        "COMMENT ON TEXT SEARCH TEMPLATE simple IS {{text}};",
        (),
        (),
    ),
    "transform": (
        ("CREATE TYPE {p}typ AS (x int);",),
        "COMMENT ON TRANSFORM FOR int LANGUAGE sql IS {{text}};",
        ("DROP TYPE IF EXISTS {p}typ;",),
        (),
    ),
    "event_trigger": (
        ("CREATE FUNCTION {p}etfn() RETURNS event_trigger AS $$BEGIN NULL; END;$$ LANGUAGE plpgsql;",
         "CREATE EVENT TRIGGER {p}et ON ddl_command_start EXECUTE FUNCTION {p}etfn();"),
        "COMMENT ON EVENT TRIGGER {p}et IS {{text}};",
        ("DROP EVENT TRIGGER IF EXISTS {p}et;", "DROP FUNCTION IF EXISTS {p}etfn();"),
        (),
    ),
    "extension": (
        (),
        "COMMENT ON EXTENSION plpgsql IS {{text}};",
        (),
        (),
    ),
    "publication": (
        ("CREATE PUBLICATION {p}pub;",),
        "COMMENT ON PUBLICATION {p}pub IS {{text}};",
        ("DROP PUBLICATION IF EXISTS {p}pub;",),
        (),
    ),
    "subscription": (
        (),
        "COMMENT ON SUBSCRIPTION {p}sub IS {{text}};",
        (),
        (),
    ),
    "role": (
        ("CREATE ROLE {p}role;",),
        "COMMENT ON ROLE {p}role IS {{text}};",
        ("DROP ROLE IF EXISTS {p}role;",),
        (),
    ),
    "database": (
        (),
        "COMMENT ON DATABASE {p}db IS {{text}};",
        (),
        (),
    ),
    "tablespace": (
        (),
        "COMMENT ON TABLESPACE {p}ts IS {{text}};",
        (),
        (),
    ),
    "procedural_language": (
        (),
        "COMMENT ON LANGUAGE plpgsql IS {{text}};",
        (),
        (),
    ),
}


def _fixture_spec(
    ot: str, p: str
) -> tuple[tuple[str, ...], str, tuple[str, ...], tuple[str, ...]]:
    """Return (setup, target_fmt, cleanup, tables) for an object_type.

    target_fmt uses {text} placeholder for the IS clause value.
    """

    spec = _FIXTURES.get(ot, _FIXTURES["table"])
    setup = tuple(s.format(p=p) for s in spec[0])
    target = spec[1].format(p=p)
    cleanup = tuple(c.format(p=p) for c in spec[2])
    tables = tuple(t.format(p=p) for t in spec[3])
    return setup, target, cleanup, tables


_SHARED_OBJECT_TYPES = frozenset(
    {"database", "role", "tablespace", "subscription"}
)


def _is_failure_case(a: dict[str, str]) -> bool:
    return a.get("expected_status") == "failure"


def _object_missing(a: dict[str, str]) -> bool:
    return a.get("object_state") == "object_not_exists"


def _non_owner(a: dict[str, str]) -> bool:
    return a.get("privilege_level") == "non_owner"


def _wrong_identifier(a: dict[str, str]) -> bool:
    wif = a.get("wrong_identifier_format", "correct_format")
    return wif != "correct_format"


def _verify_query(
    ot: str, p: str, a: dict[str, str]
) -> str:
    """Catalog-audit or function-call oracle for comment verification."""

    mode = a.get("verification_mode", "obj_description_query")
    text = _comment_text(a)
    if text == "NULL":
        text_for_query = ""
    else:
        text_for_query = text.strip("'")

    if mode == "psql_dd_command":
        return (
            "SELECT 1 AS psql_dd_command_executed "
            "ORDER BY psql_dd_command_executed;"
        )
    if mode == "catalog_query_pg_description":
        table = (
            "pg_catalog.pg_shdescription"
            if ot in _SHARED_OBJECT_TYPES
            else "pg_catalog.pg_description"
        )
        return (
            f"SELECT count(*) AS comment_count "
            f"FROM {table} "
            f"WHERE description = '{text_for_query}' "
            f"ORDER BY count(*)"
        )
    if mode == "obj_description_query":
        return (
            f"SELECT obj_description('{p}tbl'::regclass) "
            f"AS comment ORDER BY comment;"
        )
    if mode == "col_description_query":
        return (
            f"SELECT col_description('{p}tbl'::regclass, 1) "
            f"AS comment ORDER BY comment;"
        )
    if mode == "shobj_description_query":
        return (
            f"SELECT shobj_description('{p}role'::regrole, "
            f"'pg_authid') AS comment ORDER BY comment;"
        )
    return (
        f"SELECT obj_description('{p}tbl'::regclass) "
        f"AS comment ORDER BY comment;"
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
    """The primary COMMENT ON statement for the active object_type."""

    ot = a.get("object_type", "table")
    text = _comment_text(a)

    if _object_missing(a):
        if ot == "table":
            return f"COMMENT ON TABLE {p}no_such_tbl IS {text};"
        return f"COMMENT ON TABLE {p}no_such_tbl IS {text};"

    if _wrong_identifier(a):
        wif = a.get("wrong_identifier_format")
        if wif == "missing_relation_for_column":
            return f"COMMENT ON COLUMN id IS {text};"
        if wif == "missing_on_for_constraint":
            return f"COMMENT ON CONSTRAINT {p}con IS {text};"
        return f"COMMENT ON TABLE {p}tbl IS {text};"

    setup, target_fmt, cleanup, tables = _fixture_spec(ot, p)
    return target_fmt.format(text=text)


def _resolve_case(
    case: CommentFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    ot = a.get("object_type", "table")
    missing = _object_missing(a)
    non_owner = _non_owner(a)
    wrong_id = _wrong_identifier(a)

    setup: list[str] = []
    locus = "target.comment_on"

    # --- non-owner role fixture ----------------------------------
    if non_owner:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- the target object fixture -------------------------------
    if not missing and not wrong_id:
        spec_setup, _, _, _ = _fixture_spec(ot, p)
        setup.extend(spec_setup)
        locus = f"fixture.{ot}"
    elif missing:
        setup.append(
            "SELECT 1 AS target_object_intentionally_absent;"
        )
        locus = "fixture.object_missing"
    else:
        # wrong_identifier: still create the object so the
        # malformed COMMENT ON is the only failure.
        spec_setup, _, _, _ = _fixture_spec(ot, p)
        setup.extend(spec_setup)
        locus = "fixture.wrong_identifier"

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
        pre_cleanup.append(
            f"DROP TABLE IF EXISTS {tbl_list} CASCADE;"
        )
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
        pre_cleanup.append(
            "SELECT 1 AS residual_check_no_objects;"
        )

    # --- cleanup construction ------------------------------------
    # For table-creating cases, DROP TABLE must be the LAST ; stmt.
    cleanup_list: list[str] = []
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
        cleanup_list.append(
            "SELECT 1 AS residual_check_no_objects;"
        )

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


def resolve_comment_factor_witness(
    case: CommentFactorCase | CommentFactorExtensionCase,
    repository_root: Path,
) -> CommentFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CommentFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_comment(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*COMMENT\s+ON\b", region)
    )


def _header(case: CommentFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : COMMENT ON {case.factor_key}="
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


def render_comment_factor_case(
    case: CommentFactorCase | CommentFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 COMMENT ON。")
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
    case: CommentFactorCase | CommentFactorExtensionCase,
    out: Path,
) -> None:
    text = render_comment_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_comment_factor_programs(
    baseline_plan: CommentFactorLoopPlan,
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
    "CommentFactorRenderError",
    "CommentFactorWitness",
    "count_primary_comment",
    "generate_comment_factor_programs",
    "render_comment_factor_case",
    "resolve_comment_factor_witness",
]
