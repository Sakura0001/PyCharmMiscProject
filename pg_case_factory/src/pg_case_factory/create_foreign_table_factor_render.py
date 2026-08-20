"""Render complete PostgreSQL 18.4 CREATE FOREIGN TABLE factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CREATE FOREIGN TABLE creates a ``pg_class`` relation with
``relkind = 'f'``.  The shared bookend gate's ``CREATE TABLE`` pattern
deliberately does not match ``CREATE FOREIGN TABLE`` (``FOREIGN`` sits
between ``CREATE`` and ``TABLE``), so scripts that create only foreign
tables are table-less and bookend-exempt.  Cases that fixture a regular
parent/source table (partition parent, ``INHERITS`` parent, ``LIKE``
source) do create a ``CREATE TABLE`` and therefore carry the
``DROP TABLE IF EXISTS`` bookend.  CREATE FOREIGN TABLE does not
support ``OR REPLACE``.  All catalog oracles schema-qualify
``pg_catalog.pg_class`` (exempt from the file-prefix style gate) and
carry a top-level ``ORDER BY count(*)``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_foreign_table_factor_extension import (
    CreateForeignTableFactorExtensionCase,
    _present_failure_pair,
)
from .create_foreign_table_factor_loop import (
    CreateForeignTableFactorCase,
    CreateForeignTableFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/foreign_table/"
    "create_foreign_table.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/foreign_table/"
    "create_foreign_table.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class CreateForeignTableFactorRenderError(ValueError):
    """Raised when a CREATE FOREIGN TABLE case cannot be rendered."""


@dataclass(frozen=True)
class CreateForeignTableFactorWitness:
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


# ------------------------------------------------------------------
# Case adaptation
# ------------------------------------------------------------------


def _synthetic_case(
    ext: CreateForeignTableFactorExtensionCase,
) -> CreateForeignTableFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_form"
        factor_value = ext.consumer_action_id
    return CreateForeignTableFactorCase(
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
    case: CreateForeignTableFactorCase
    | CreateForeignTableFactorExtensionCase,
) -> CreateForeignTableFactorCase:
    if isinstance(
        case, CreateForeignTableFactorExtensionCase
    ):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateForeignTableFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


# ------------------------------------------------------------------
# Name builders
# ------------------------------------------------------------------


def _table_name(a: dict[str, str], p: str) -> str:
    """The foreign table identifier in CREATE FOREIGN TABLE."""

    shape = a.get("table_name_shape", "simple_id")
    if shape == "schema_qualified":
        se = a.get("schema_existence", "schema_exists")
        schema = f"{p}schema" if se == "schema_exists" else f"{p}noschema"
        return f"{schema}.{p}ft"
    if shape == "quoted_id":
        return f'"{p}Mixed Ft"'
    if shape == "reserved_word_name":
        return f'"{p}user"'
    # simple_id, duplicate_name
    return f"{p}ft"


def _table_name_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    shape = a.get("table_name_shape", "simple_id")
    if shape == "quoted_id":
        return f"{p}Mixed Ft"
    if shape == "reserved_word_name":
        return f"{p}user"
    return f"{p}ft"


def _server_name(a: dict[str, str], p: str) -> str:
    if a.get("server_existence") == "server_not_exists":
        return f"{p}noserver"
    return f"{p}server"


def _fdw_name(p: str) -> str:
    return f"{p}fdw"


def _column_name(a: dict[str, str], p: str) -> str:
    shape = a.get("column_name_shape", "simple_id")
    if shape == "quoted_id":
        return f'"{p}Mixed Col"'
    if shape == "reserved_word_name":
        return f'"{p}check"'
    return f"{p}col"


_SQL_TYPE = {
    "integer": "integer",
    "bigint": "bigint",
    "text": "text",
    "varchar": "character varying(100)",
    "numeric": "numeric(10,2)",
    "boolean": "boolean",
    "date": "date",
    "timestamp": "timestamp",
    "jsonb": "jsonb",
    "uuid": "uuid",
    "float8": "double precision",
}


def _column_def(a: dict[str, str], p: str) -> str:
    """One column definition for the regular form."""

    col = _column_name(a, p)
    dtype = _SQL_TYPE.get(
        a.get("column_data_type", "integer"), "integer"
    )
    collation = ""
    if a.get("collation_name_shape") == "specified":
        collation = ' COLLATE "C"'
    constraint = _column_constraint(a, p, col)
    return f"{col} {dtype}{collation}{constraint}"


def _column_constraint(
    a: dict[str, str], p: str, col: str
) -> str:
    ce = a.get("constraint_not_enforced", "no_constraints")
    cn = a.get("constraint_name_shape", "omitted")
    name = f"CONSTRAINT {p}nn " if cn == "simple_id" else ""
    if ce == "with_not_null":
        return f" {name}NOT NULL"
    if ce == "with_check":
        return f" {name}CHECK ({col} IS NOT NULL)"
    if cn == "simple_id":
        return f" CONSTRAINT {p}nn NOT NULL"
    return ""


def _column_list(
    a: dict[str, str], consumer: str
) -> str:
    """The column-definition list inside parentheses."""

    p = a.get("__prefix", "")
    if consumer == "pg18_like_source":
        return f"LIKE {p}source INCLUDING ALL"
    if consumer == "pg18_virtual_generated":
        return (
            f"{p}col integer GENERATED ALWAYS AS (1) "
            "VIRTUAL NOT ENFORCED"
        )
    if consumer == "pg18_table_not_null":
        return f"{p}col integer, NOT NULL {p}col NO INHERIT"
    # create_regular, create_partition
    count = a.get("column_count", "single_column")
    if count == "zero_columns":
        return ""
    first = _column_def(a, p)
    if count == "multiple_columns":
        return f"{first}, {p}col2 integer"
    return first


def _inherits_clause(a: dict[str, str], p: str) -> str:
    clause = a.get("inherits_clause", "omitted")
    if clause == "single_parent":
        return f" INHERITS ({p}parent1)"
    if clause == "multiple_parents":
        return f" INHERITS ({p}parent1, {p}parent2)"
    return ""


_PARTITION_SPEC = {
    "for_values_in": ("LIST", "FOR VALUES IN (1)"),
    "for_values_from_to": ("RANGE", "FOR VALUES FROM (1) TO (10)"),
    "for_values_with": ("HASH", "FOR VALUES WITH (MODULUS 4, REMAINDER 0)"),
    "default_partition": ("LIST", "DEFAULT"),
}


def _partition_bound(a: dict[str, str]) -> str:
    spec = a.get("partition_bound_spec", "for_values_in")
    return _PARTITION_SPEC.get(spec, _PARTITION_SPEC["for_values_in"])[1]


def _parent_name(a: dict[str, str], p: str) -> str:
    if a.get("parent_table_existence") == "parent_not_exists":
        return f"{p}noparent"
    return f"{p}parent"


# ------------------------------------------------------------------
# Fixture helpers
# ------------------------------------------------------------------


def _needs_server(a: dict[str, str]) -> bool:
    return a.get("server_existence") != "server_not_exists"


def _needs_schema(a: dict[str, str]) -> bool:
    shape = a.get("table_name_shape")
    se = a.get("schema_existence")
    return shape == "schema_qualified" and se == "schema_exists"


def _can_drop_ft(a: dict[str, str]) -> bool:
    """Whether DROP FOREIGN TABLE is safe (schema must exist)."""

    return a.get("schema_existence") != "schema_not_exists"


def _effective_role(a: dict[str, str], p: str) -> str:
    pl = a.get("privilege_level", "usage_on_server_and_types")
    if pl in ("no_server_usage", "no_type_usage"):
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    if _effective_role(a, p):
        return (f"{p}actor",)
    return ()


def _fixture_table_names(
    a: dict[str, str], p: str, consumer: str
) -> list[str]:
    """Regular tables created as fixtures (for bookend + drop)."""

    tables: list[str] = []
    if consumer == "create_regular":
        clause = a.get("inherits_clause", "omitted")
        if clause == "single_parent":
            tables.append(f"{p}parent1")
        elif clause == "multiple_parents":
            tables.extend([f"{p}parent1", f"{p}parent2"])
    elif consumer == "create_partition":
        if a.get("parent_table_existence") != "parent_not_exists":
            tables.append(f"{p}parent")
    elif consumer == "pg18_like_source":
        tables.append(f"{p}source")
    return tables


def _drop_table_stmt(names: list[str]) -> str:
    return f"DROP TABLE IF EXISTS {', '.join(names)} CASCADE;"


# ------------------------------------------------------------------
# Target builder
# ------------------------------------------------------------------


def _build_target(
    a: dict[str, str], p: str, consumer: str
) -> str:
    """The primary CREATE FOREIGN TABLE statement."""

    ifne = ""
    if a.get("if_not_exists_clause") == "specified":
        ifne = "IF NOT EXISTS "
    name = _table_name(a, p)
    server = _server_name(a, p)

    if consumer == "create_partition":
        parent = _parent_name(a, p)
        bound = _partition_bound(a)
        return (
            f"CREATE FOREIGN TABLE {ifne}{name} "
            f"PARTITION OF {parent} {bound} "
            f"SERVER {server};"
        )
    cols = _column_list(a, consumer)
    inherits = _inherits_clause(a, p)
    return (
        f"CREATE FOREIGN TABLE {ifne}{name} ({cols})"
        f"{inherits} SERVER {server};"
    )


# ------------------------------------------------------------------
# Catalog oracle
# ------------------------------------------------------------------


def _probe_select(
    case: CreateForeignTableFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only error_assertion."""

    mode = a.get("verification_mode", "pg_class_catalog_query")
    if mode == "error_assertion":
        return None

    table_lit = _table_name_literal(a, p)
    os_val = a.get("object_state", "not_exists")
    if case.outcome == "success":
        present = True
    elif os_val == "already_exists":
        present = True
    else:
        present = False
    cmp_op = ">" if present else "="
    return (
        f"SELECT count(*) {cmp_op} 0 AS ft_state "
        "FROM pg_catalog.pg_class "
        f"WHERE relname = '{table_lit}' AND relkind = 'f' "
        "ORDER BY count(*);"
    )


# ------------------------------------------------------------------
# Case resolution
# ------------------------------------------------------------------


def _setup_lines(
    a: dict[str, str], p: str, consumer: str
) -> tuple[str, ...]:
    """Fixture setup statements (after ON_ERROR_STOP on)."""

    lines: list[str] = []
    locus = "target.create_foreign_table"

    if _needs_server(a):
        lines.append(f"CREATE FOREIGN DATA WRAPPER {p}fdw;")
        lines.append(
            f"CREATE SERVER {p}server FOREIGN DATA WRAPPER {p}fdw;"
        )
        locus = "fixture.server"
    if _needs_schema(a):
        lines.append(f"CREATE SCHEMA IF NOT EXISTS {p}schema;")
        locus = "fixture.schema"

    # Fixture tables (parent / source / INHERITS parents)
    if consumer == "create_regular":
        clause = a.get("inherits_clause", "omitted")
        if clause == "single_parent":
            lines.append(
                f"CREATE TABLE {p}parent1 ({p}col integer);"
            )
            locus = "fixture.inherits_parent"
        elif clause == "multiple_parents":
            lines.append(
                f"CREATE TABLE {p}parent1 ({p}col integer);"
            )
            lines.append(
                f"CREATE TABLE {p}parent2 ({p}col integer);"
            )
            locus = "fixture.inherits_parents"
    elif consumer == "create_partition":
        if a.get("parent_table_existence") != "parent_not_exists":
            strat = _PARTITION_SPEC.get(
                a.get("partition_bound_spec", "for_values_in"),
                _PARTITION_SPEC["for_values_in"],
            )[0]
            lines.append(
                f"CREATE TABLE {p}parent ({p}key integer) "
                f"PARTITION BY {strat} ({p}key);"
            )
            if a.get("parent_has_unique_index") == "parent_has_unique":
                lines.append(
                    f"CREATE UNIQUE INDEX {p}uidx "
                    f"ON {p}parent ({p}key);"
                )
                locus = "fixture.parent_unique_index"
            else:
                locus = "fixture.partition_parent"
    elif consumer == "pg18_like_source":
        lines.append(f"CREATE TABLE {p}source ({p}col integer);")
        locus = "fixture.like_source"

    # Pre-existing object for already_exists / type_name_conflict
    os_val = a.get("object_state", "not_exists")
    ft_name = _table_name(a, p)
    if os_val == "already_exists":
        server = _server_name(a, p)
        if _needs_server(a):
            lines.append(
                f"CREATE FOREIGN TABLE {ft_name} () "
                f"SERVER {server};"
            )
        locus = "fixture.duplicate_foreign_table"
    elif os_val == "type_name_conflict":
        lines.append(
            f"CREATE TYPE {ft_name} AS ({p}val integer);"
        )
        locus = "fixture.type_name_conflict"

    # Role fixture
    role = _effective_role(a, p)
    if role:
        lines.append(
            f"CREATE ROLE {role} LOGIN NOSUPERUSER;"
        )
        if _needs_server(a):
            lines.append(
                f"GRANT USAGE ON FOREIGN DATA WRAPPER {p}fdw "
                f"TO {role};"
            )
            lines.append(
                f"GRANT USAGE ON FOREIGN SERVER {p}server "
                f"TO {role};"
            )
        lines.append(f"SET ROLE {role};")
        locus = "fixture.privilege"

    return tuple(lines), locus  # type: ignore[return-value]


def _resolve_case(
    case: CreateForeignTableFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    a["__prefix"] = p
    consumer = case.consumer_action_id
    setup, locus = _setup_lines(a, p, consumer)

    target = _build_target(a, p, consumer)

    # Assert lines
    assert_lines: list[str] = []
    role = _effective_role(a, p)
    if role:
        assert_lines.append("RESET ROLE;")
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    probe = _probe_select(case, a, p)
    if probe is not None:
        assert_lines.append(probe)

    # Object drops
    ft_name = _table_name(a, p)
    roles = _role_names(a, p)
    fixture_tables = _fixture_table_names(a, p, consumer)

    ft_drops: list[str] = []
    if _can_drop_ft(a):
        ft_drops.append(
            f"DROP FOREIGN TABLE IF EXISTS {ft_name} CASCADE;"
        )
    schema_drops: list[str] = []
    if _needs_schema(a):
        schema_drops.append(
            f"DROP SCHEMA IF EXISTS {p}schema CASCADE;"
        )
    server_drops: list[str] = []
    if _needs_server(a):
        server_drops.append(
            f"DROP SERVER IF EXISTS {p}server CASCADE;"
        )
        server_drops.append(
            f"DROP FOREIGN DATA WRAPPER IF EXISTS {p}fdw CASCADE;"
        )
    type_drops: list[str] = []
    if a.get("object_state") == "type_name_conflict":
        type_drops.append(
            f"DROP TYPE IF EXISTS {ft_name} CASCADE;"
        )
    role_drops: list[str] = []
    for r in roles:
        role_drops.append(f"DROP OWNED BY {r} CASCADE;")
        role_drops.append(f"DROP ROLE IF EXISTS {r};")

    # Pre-cleanup: table drops first (bookend), then others
    pre: list[str] = []
    if fixture_tables:
        pre.append(_drop_table_stmt(fixture_tables))
    pre.extend(ft_drops)
    pre.extend(schema_drops)
    pre.extend(server_drops)
    pre.extend(type_drops)
    pre.extend(role_drops)
    if not pre:
        pre.append("SELECT 1 AS residual_check_no_objects;")

    # Cleanup: others first, table drops last (bookend)
    post: list[str] = []
    if role:
        post.append("RESET ROLE;")
    post.extend(ft_drops)
    post.extend(type_drops)
    post.extend(schema_drops)
    post.extend(server_drops)
    post.extend(role_drops)
    if fixture_tables:
        post.append(_drop_table_stmt(fixture_tables))
    elif not post:
        post.append("SELECT 1 AS residual_check_no_objects;")

    on_error_off = case.outcome == "expected_failure"
    return _CasePlan(
        target_fragment=target,
        setup_lines=setup,
        assert_lines=tuple(assert_lines),
        pre_cleanup_lines=tuple(pre),
        cleanup_lines=tuple(post),
        on_error_off=on_error_off,
        semantic_locus=locus,
    )


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------


def count_primary_create_foreign_table(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(
            r"(?im)^CREATE\s+FOREIGN\s+TABLE(?:\s|;|$)",
            region,
        )
    )


def _header(
    case: CreateForeignTableFactorCase,
) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE FOREIGN TABLE {case.factor_key}="
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


def render_create_foreign_table_factor_case(
    case: CreateForeignTableFactorCase
    | CreateForeignTableFactorExtensionCase,
    repository_root: Path,
) -> str:
    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地规则和因子专用夹具。")
    lines.append("SELECT 1 AS setup_boundary;")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 CREATE FOREIGN TABLE。")
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
    case: CreateForeignTableFactorCase
    | CreateForeignTableFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_foreign_table_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_foreign_table_factor_programs(
    baseline_plan: CreateForeignTableFactorLoopPlan,
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


def resolve_create_foreign_table_factor_witness(
    case: CreateForeignTableFactorCase
    | CreateForeignTableFactorExtensionCase,
    repository_root: Path,
) -> CreateForeignTableFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateForeignTableFactorWitness(
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
    "CreateForeignTableFactorRenderError",
    "CreateForeignTableFactorWitness",
    "count_primary_create_foreign_table",
    "generate_create_foreign_table_factor_programs",
    "render_create_foreign_table_factor_case",
    "resolve_create_foreign_table_factor_witness",
]
