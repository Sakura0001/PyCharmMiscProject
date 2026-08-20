"""Render complete PostgreSQL 18.4 CREATE TABLE factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CREATE TABLE creates a relation (``pg_class.relkind = 'r'``).  The
bookend gate applies directly: the FIRST and LAST executable
``;``-statements are each ``DROP TABLE IF EXISTS <all created tables>``
and the script creates >=1 table.  All catalog oracles schema-qualify
``pg_catalog.*`` or ``information_schema.*`` (exempt from the
file-prefix style gate) and carry a top-level ``ORDER BY``.  Table
names are always plain unquoted lowercase identifiers so the bookend
``_normalize_identifier`` and the style gate both pass cleanly.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_table_factor_extension import (
    CreateTableFactorExtensionCase,
    _present_failure_pair,
)
from .create_table_factor_loop import (
    CreateTableFactorCase,
    CreateTableFactorLoopPlan,
)


_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/table/"
    "create_table.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/table/"
    "create_table.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class CreateTableFactorRenderError(ValueError):
    """Raised when a CREATE TABLE case cannot be rendered."""


@dataclass(frozen=True)
class CreateTableFactorWitness:
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
    ext: CreateTableFactorExtensionCase,
) -> CreateTableFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "table_type"
        factor_value = assignment.get("table_type", "permanent")
    return CreateTableFactorCase(
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
    case: CreateTableFactorCase | CreateTableFactorExtensionCase,
) -> CreateTableFactorCase:
    if isinstance(case, CreateTableFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateTableFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _is_failure(a: dict[str, str]) -> bool:
    return a.get("expected_status") == "failure"


_TABLE_TYPE_PREFIX = {
    "permanent": "",
    "temp_short": "TEMP ",
    "temporary_global": "GLOBAL TEMPORARY ",
    "temporary_local": "LOCAL TEMPORARY ",
    "unlogged": "UNLOGGED ",
}

_ON_COMMIT_CLAUSE = {
    "DELETE_ROWS": "ON COMMIT DELETE ROWS",
    "DROP": "ON COMMIT DROP",
    "PRESERVE_ROWS": "ON COMMIT PRESERVE ROWS",
    "absent": "",
}

_PARTITION_BY = {
    "RANGE": "PARTITION BY RANGE ({p}col)",
    "LIST": "PARTITION BY LIST ({p}col)",
    "HASH": "PARTITION BY HASH ({p}col)",
    "not_partitioned": "",
}


def _table_type_prefix(a: dict[str, str]) -> str:
    return _TABLE_TYPE_PREFIX.get(
        a.get("table_type", "permanent"), ""
    )


def _on_commit_clause(a: dict[str, str]) -> str:
    return _ON_COMMIT_CLAUSE.get(a.get("on_commit_clause", "absent"), "")


def _partition_clause(a: dict[str, str], p: str) -> str:
    spec = a.get("partition_clause", "not_partitioned")
    template = _PARTITION_BY.get(spec, "")
    return template.replace("{p}", p) if template else ""


def _if_not_exists(a: dict[str, str]) -> str:
    return "IF NOT EXISTS " if a.get("if_not_exists_clause") == (
        "present"
    ) else ""


def _column_name(a: dict[str, str], p: str) -> str:
    shape = a.get("column_name_shape", "simple")
    if shape == "duplicate_in_table":
        return f"{p}col"
    return f"{p}col"


def _data_type_sql(a: dict[str, str]) -> str:
    idt = a.get("invalid_data_type", "none")
    if idt == "unknown_type_name":
        return "nonexistent_type_xyz"
    if idt == "wrong_array_syntax":
        return "integer["
    dtype = a.get("data_type", "integer")
    return _SQL_TYPE_MAP.get(dtype, "integer")


_SQL_TYPE_MAP = {
    "aclitem": "aclitem", "bigint": "bigint", "bigserial": "bigserial",
    "bit": "bit", "bit_varying": "bit varying",
    "boolean": "boolean", "box": "box", "bytea": "bytea",
    "character": "character(10)", "character_varying": "character varying(100)",
    "cid": "cid", "cidr": "cidr", "circle": "circle",
    "composite_type": "{p}composite",
    "date": "date", "daterange": "daterange", "decimal": "decimal(10,2)",
    "double_precision": "double precision", "enum_type": "{p}enum",
    "inet": "inet", "int4range": "int4range", "int8range": "int8range",
    "integer": "integer", "integer_array": "integer[]",
    "interval": "interval", "json": "json", "jsonb": "jsonb",
    "jsonb_array": "jsonb[]", "line": "line", "lseg": "lseg",
    "macaddr": "macaddr", "macaddr8": "macaddr8", "money": "money",
    "name": "name", "numeric": "numeric(10,2)",
    "numeric_array": "numeric[]", "numrange": "numrange", "oid": "oid",
    "path": "path", "pg_lsn": "pg_lsn", "pg_snapshot": "pg_snapshot",
    "point": "point", "polygon": "polygon", "real": "real",
    "regclass": "regclass", "regnamespace": "regnamespace",
    "regproc": "regproc", "regrole": "regrole", "regtype": "regtype",
    "serial": "serial", "smallint": "smallint",
    "smallserial": "smallserial", "text": "text", "text_array": "text[]",
    "tid": "tid", "time": "time", "time_with_time_zone": "time with time zone",
    "timestamp": "timestamp", "timestamp_array": "timestamp[]",
    "timestamp_with_time_zone": "timestamp with time zone",
    "tsquery": "tsquery", "tsrange": "tsrange",
    "tstzrange": "tstzrange", "tsvector": "tsvector",
    "uuid": "uuid", "varchar_array": "varchar[]",
    "xid": "xid", "xid8": "xid8", "xml": "xml",
}


def _default_clause(a: dict[str, str]) -> str:
    shape = a.get("default_value_shape", "without_DEFAULT")
    if shape == "with_DEFAULT_literal":
        return " DEFAULT 0"
    if shape == "with_DEFAULT_expression":
        return " DEFAULT 1 + 1"
    return ""


def _collation_clause(a: dict[str, str]) -> str:
    if a.get("collation_clause") == "with_COLLATION":
        return ' COLLATE "C"'
    return ""


def _generated_clause(a: dict[str, str], p: str) -> str:
    gc = a.get("generated_clause", "none")
    if gc == "GENERATED_ALWAYS_AS_STORED":
        return f", {p}gen integer GENERATED ALWAYS AS ({p}col * 2) STORED"
    if gc == "GENERATED_ALWAYS_AS_VIRTUAL":
        return f", {p}gen integer GENERATED ALWAYS AS ({p}col * 2) VIRTUAL"
    if gc == "GENERATED_ALWAYS_AS_IDENTITY":
        return f" GENERATED ALWAYS AS IDENTITY"
    if gc == "GENERATED_BY_DEFAULT_AS_IDENTITY":
        return f" GENERATED BY DEFAULT AS IDENTITY"
    return ""


def _constraint_column_def(
    a: dict[str, str], p: str
) -> str:
    """Build the column definition(s) for the regular/typed form."""

    col = _column_name(a, p)
    dtype = _data_type_sql(a).replace("{p}", p)
    default = _default_clause(a)
    collation = _collation_clause(a)
    generated = _generated_clause(a, p)
    ctype = a.get("constraint_type", "NOT_NULL")
    cv = a.get("constraint_violation_in_definition", "none")

    if cv == "CHECK_expression_invalid":
        return f"{col} {dtype}{default}{collation}, CHECK ({col} > {p}badcol)"
    if cv == "FK_references_nonexistent_table":
        return (
            f"{col} {dtype}{default}{collation}, "
            f"FOREIGN KEY ({col}) REFERENCES {p}noreftab({col})"
        )
    if cv == "PK_with_nullable_column":
        return f"{col} {dtype} NULL, PRIMARY KEY ({col})"

    parts = f"{col} {dtype}{default}{collation}"
    if ctype == "NOT_NULL":
        parts += " NOT NULL"
    elif ctype == "NOT_NULL_NO_INHERIT":
        parts += " NOT NULL NO INHERIT"
    elif ctype == "GENERATED_IDENTITY":
        parts += generated
    elif ctype == "GENERATED_ALWAYS_VIRTUAL":
        parts = f"{col} {dtype}, {p}gen integer GENERATED ALWAYS AS ({col}) VIRTUAL"
    elif ctype == "NOT_ENFORCED":
        parts += " NOT NULL NOT ENFORCED"
    elif ctype == "TABLE_NOT_NULL":
        return f"{col} {dtype}, NOT NULL {col} NO INHERIT"
    elif ctype == "UNIQUE_WITHOUT_OVERLAPS":
        return f"{col} {dtype}, UNIQUE ({col}) WITHOUT OVERLAPS"
    elif ctype == "PRIMARY_KEY_WITHOUT_OVERLAPS":
        return f"{col} {dtype}, PRIMARY KEY ({col}) WITHOUT OVERLAPS"
    elif ctype == "PERIOD_FOREIGN_KEY":
        return (
            f"{col} {dtype}, {p}ref integer, "
            f"FOREIGN KEY ({col}, {p}ref) REFERENCES {p}reftab({col}, {p}ref)"
        )
    parts += generated
    col_def = parts
    extras = ""
    if ctype == "PRIMARY_KEY":
        extras = f", PRIMARY KEY ({col})"
    elif ctype == "UNIQUE":
        extras = f", UNIQUE ({col})"
    elif ctype == "CHECK":
        extras = f", CHECK ({col} > 0)"
    elif ctype == "DEFAULT":
        col_def = f"{col} {dtype} DEFAULT 0"
    elif ctype == "FOREIGN_KEY":
        extras = f", FOREIGN KEY ({col}) REFERENCES {p}reftab({col})"
    elif ctype == "EXCLUDE":
        extras = f", EXCLUDE USING btree ({col} WITH =)"
    elif ctype == "GENERATED_ALWAYS_STORED":
        extras = f", {p}gen integer GENERATED ALWAYS AS ({col} * 2) STORED"
    if a.get("column_definition_count") == "multiple_columns":
        extras += f", {p}col2 integer"
    return col_def + extras


def _column_list(
    a: dict[str, str], p: str, consumer: str
) -> str:
    """The column-definition list inside parentheses."""

    if consumer == "create_typed":
        return f"{p}col WITH OPTIONS NOT NULL"
    if consumer == "create_partition":
        parts = f"{_column_name(a, p)} {_data_type_sql(a).replace('{p}', p)}"
        if a.get("column_definition_count") == "multiple_columns":
            parts += f", {p}col2 integer"
        return parts
    if a.get("like_clause") == "LIKE_no_options":
        return f"LIKE {p}source"
    if a.get("like_clause") == "LIKE_with_options":
        return f"LIKE {p}source INCLUDING ALL"
    return _constraint_column_def(a, p)


def _partition_bound(a: dict[str, str]) -> str:
    pbi = a.get("partition_bound_invalid", "none")
    if pbi == "bound_out_of_range":
        return "FOR VALUES FROM (999) TO (1)"
    if pbi == "bound_type_mismatch":
        return "FOR VALUES IN ('wrong_type')"
    return "FOR VALUES FROM (1) TO (100)"


def _build_target(
    a: dict[str, str], p: str, consumer: str
) -> str:
    """The primary CREATE TABLE statement."""

    prefix = _table_type_prefix(a)
    ifne = _if_not_exists(a)
    tns = a.get("table_name_shape", "simple")
    if tns == "schema_qualified":
        name = f"{p}schema.{p}t"
    else:
        name = f"{p}t"
    parts: list[str] = [f"CREATE {prefix}TABLE {ifne}{name}"]

    if consumer == "create_typed":
        parts.append(f"OF {p}type")
        cols = _column_list(a, p, consumer)
        if cols:
            parts.append(f"({cols})")
    elif consumer == "create_partition":
        parent = f"{p}noparent" if a.get(
            "parent_table_dependency"
        ) == "parent_table_not_exists" else f"{p}parent"
        parts.append(f"PARTITION OF {parent}")
        cols = _column_list(a, p, consumer)
        if cols:
            parts.append(f"({cols})")
        parts.append(_partition_bound(a))
    else:
        cols = _column_list(a, p, consumer)
        parts.append(f"({cols})")
        inh = a.get("inheritance_clause", "no_inheritance")
        if inh == "INHERITS":
            parts.append(f"INHERITS ({p}parent1)")

    pc = _partition_clause(a, p)
    if pc:
        parts.append(pc)
    oc = _on_commit_clause(a)
    if oc:
        parts.append(oc)
    tsd = a.get("tablespace_dependency", "default_tablespace")
    if tsd == "specified_tablespace_exists":
        parts.append(f"TABLESPACE {p}ts")
    elif tsd == "specified_tablespace_not_exists":
        parts.append(f"TABLESPACE {p}nots")
    return " ".join(parts) + ";"


def _primary_table_name(a: dict[str, str], p: str) -> str:
    """The primary table name as it appears in CREATE TABLE."""

    if a.get("table_name_shape") == "schema_qualified":
        return f"{p}schema.{p}t"
    return f"{p}t"


def _fixture_table_names(
    a: dict[str, str], p: str, consumer: str
) -> list[str]:
    """All fixture table names created in setup (for bookend drop)."""

    tables: list[str] = []
    if consumer == "create_typed":
        pass
    elif consumer == "create_partition":
        if a.get("parent_table_dependency") != "parent_table_not_exists":
            tables.append(f"{p}parent")
    if a.get("inheritance_clause") == "INHERITS":
        tables.append(f"{p}parent1")
    if a.get("like_clause") in ("LIKE_no_options", "LIKE_with_options"):
        tables.append(f"{p}source")
    ctype = a.get("constraint_type", "NOT_NULL")
    if ctype in ("FOREIGN_KEY", "PERIOD_FOREIGN_KEY"):
        tables.append(f"{p}reftab")
    cv = a.get("constraint_violation_in_definition", "none")
    if cv == "FK_references_nonexistent_table":
        pass
    return tables


def _all_tables(
    a: dict[str, str], p: str, consumer: str
) -> list[str]:
    """All created table names (primary + fixtures) for the bookend."""
    tables = [_primary_table_name(a, p)]
    tables.extend(_fixture_table_names(a, p, consumer))
    return list(dict.fromkeys(tables))


def _build_setup(
    a: dict[str, str], p: str, consumer: str
) -> tuple[list[str], str]:
    lines: list[str] = []
    locus = "target.create_table"

    schema_dep = a.get("schema_dependency", "schema_exists")
    if schema_dep == "schema_exists" and a.get(
        "table_name_shape"
    ) == "schema_qualified":
        lines.append(f"CREATE SCHEMA IF NOT EXISTS {p}schema;")
        locus = "fixture.schema"

    if consumer == "create_typed":
        if a.get("type_dependency") == "composite_type_not_exists":
            pass
        else:
            lines.append(f"CREATE TYPE {p}type AS ({p}val integer);")
            locus = "fixture.composite_type"
    elif consumer == "create_partition":
        ptd = a.get("parent_table_dependency", "parent_table_exists")
        if ptd != "parent_table_not_exists":
            strat = "RANGE" if ptd != "parent_table_not_partitioned" else (
                "RANGE"
            )
            lines.append(
                f"CREATE TABLE {p}parent ({p}col integer) "
                f"PARTITION BY {strat} ({p}col);"
            )
            locus = "fixture.partition_parent"

    if a.get("inheritance_clause") == "INHERITS":
        lines.append(f"CREATE TABLE {p}parent1 ({p}col integer);")
        locus = "fixture.inherits_parent"
    if a.get("like_clause") in ("LIKE_no_options", "LIKE_with_options"):
        lines.append(f"CREATE TABLE {p}source ({p}col integer);")
        locus = "fixture.like_source"
    ctype = a.get("constraint_type", "NOT_NULL")
    if ctype in ("FOREIGN_KEY", "PERIOD_FOREIGN_KEY"):
        lines.append(f"CREATE TABLE {p}reftab ({p}col integer PRIMARY KEY);")
        locus = "fixture.referenced_table"

    os_val = a.get("object_state", "not_exists")
    tns = a.get("table_name_shape", "simple")
    dt = a.get("duplicate_table_name", "with_IF_NOT_EXISTS_noop")
    ttsc = a.get("temporary_table_scope_conflict", "none")
    if (
        os_val == "already_exists" or tns == "duplicate"
        or dt == "without_IF_NOT_EXISTS_error"
        or ttsc == "temp_table_same_name_permanent"
    ):
        prefix = _table_type_prefix(a)
        name = _primary_table_name(a, p)
        lines.append(f"CREATE {prefix}TABLE {name} ({p}col integer);")
        locus = "fixture.duplicate_table"

    tsd = a.get("tablespace_dependency", "default_tablespace")
    if tsd == "specified_tablespace_exists":
        lines.append(f"CREATE TABLESPACE {p}ts LOCATION '/tmp';")
        locus = "fixture.tablespace"

    return lines, locus


def _probe_select(
    a: dict[str, str], p: str
) -> str:
    """Catalog-audit oracle with top-level ORDER BY."""

    mode = a.get("verification_mode", "pg_class_catalog_query")
    table_name = f"{p}t"
    if mode == "information_schema_tables":
        return (
            "SELECT count(*) AS table_count "
            "FROM information_schema.tables "
            f"WHERE table_name = '{table_name}' "
            "ORDER BY count(*)"
            ";"
        )
    if mode == "information_schema_columns":
        return (
            "SELECT count(*) AS column_count "
            "FROM information_schema.columns "
            f"WHERE table_name = '{table_name}' "
            "ORDER BY count(*)"
            ";"
        )
    if mode == "SELECT_count":
        return (
            "SELECT count(*) AS exists_check "
            "FROM pg_catalog.pg_class "
            f"WHERE relname = '{table_name}' "
            "ORDER BY count(*)"
            ";"
        )
    if mode == "pg_attribute_query":
        return (
            "SELECT count(*) AS attr_count "
            "FROM pg_catalog.pg_attribute "
            f"WHERE attrelid = '{table_name}'::regclass "
            "ORDER BY count(*)"
            ";"
        )
    return (
        "SELECT count(*) AS table_count "
        "FROM pg_catalog.pg_class "
        f"WHERE relname = '{table_name}' "
        "ORDER BY count(*)"
        ";"
    )


def _build_pre_cleanup(
    a: dict[str, str], p: str, consumer: str
) -> tuple[str, ...]:
    tables = _all_tables(a, p, consumer)
    lines: list[str] = []
    if tables:
        lines.append(
            f"DROP TABLE IF EXISTS {', '.join(tables)} CASCADE;"
        )
    tsd = a.get("tablespace_dependency", "default_tablespace")
    if tsd == "specified_tablespace_exists":
        lines.append(f"DROP TABLESPACE IF EXISTS {p}ts;")
    if consumer == "create_typed":
        lines.append(f"DROP TYPE IF EXISTS {p}type CASCADE;")
    return tuple(lines)


def _build_cleanup(
    a: dict[str, str], p: str, consumer: str
) -> tuple[str, ...]:
    cleanup_mode = a.get("cleanup_mode", "DROP_TABLE")
    lines: list[str] = []
    if consumer == "create_typed":
        lines.append(f"DROP TYPE IF EXISTS {p}type CASCADE;")
    tsd = a.get("tablespace_dependency", "default_tablespace")
    if tsd == "specified_tablespace_exists":
        lines.append(f"DROP TABLESPACE IF EXISTS {p}ts;")
    tables = _all_tables(a, p, consumer)
    if cleanup_mode == "DROP_TABLE_IF_EXISTS":
        lines.append(
            f"DROP TABLE IF EXISTS {', '.join(tables)};"
        )
    elif cleanup_mode == "DROP_TABLE_CASCADE":
        lines.append(
            f"DROP TABLE IF EXISTS {', '.join(tables)} CASCADE;"
        )
    elif cleanup_mode == "DROP_TABLE_CASCADE_RESTRICT":
        lines.append(
            f"DROP TABLE IF EXISTS {', '.join(tables)} RESTRICT;"
        )
    else:
        lines.append(
            f"DROP TABLE IF EXISTS {', '.join(tables)} CASCADE;"
        )
    return tuple(lines)


def _build_assert(
    case: CreateTableFactorCase,
    a: dict[str, str],
    p: str,
) -> tuple[str, ...]:
    lines: list[str] = []
    lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    lines.append(_probe_select(a, p))
    return tuple(lines)


def _resolve_case(case: CreateTableFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    consumer = case.consumer_action_id
    setup, locus = _build_setup(a, p, consumer)
    target = _build_target(a, p, consumer)
    assert_lines = _build_assert(case, a, p)
    pre_cleanup = _build_pre_cleanup(a, p, consumer)
    cleanup = _build_cleanup(a, p, consumer)
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


def _header(case: CreateTableFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE TABLE {case.factor_key}="
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


def render_create_table_factor_case(
    case: CreateTableFactorCase | CreateTableFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 CREATE TABLE。")
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
    case: CreateTableFactorCase | CreateTableFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_table_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_table_factor_programs(
    baseline_plan: CreateTableFactorLoopPlan,
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


def count_primary_create_table(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(
            r"(?im)^CREATE\s+(?:(?:GLOBAL|LOCAL)\s+)?"
            r"(?:TEMP(?:ORARY)?\s+)?(?:UNLOGGED\s+)?"
            r"TABLE(?:\s|;|$)",
            region,
        )
    )


def resolve_create_table_factor_witness(
    case: CreateTableFactorCase | CreateTableFactorExtensionCase,
    repository_root: Path,
) -> CreateTableFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateTableFactorWitness(
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
    "CreateTableFactorRenderError",
    "CreateTableFactorWitness",
    "count_primary_create_table",
    "generate_create_table_factor_programs",
    "render_create_table_factor_case",
    "resolve_create_table_factor_witness",
]
