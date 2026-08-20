"""Render complete PostgreSQL 18.4 CREATE PUBLICATION factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CREATE PUBLICATION is a catalog-row DDL statement: the target is a
``pg_catalog.pg_publication`` catalog row, not a ``pg_class`` relation.
All catalog oracles schema-qualify ``pg_catalog.pg_publication`` and
``pg_catalog.pg_publication_tables`` (exempt from the file-prefix style
gate).  Cases that fixture a backing TABLE emit the bookend
(``DROP TABLE IF EXISTS ... CASCADE;``) as the first and last
executable ``;``-statement so the shared ``audit_complete_table_script``
bookend gate sees every created table; table-less cases create no TABLE
and are exempt.  Every catalog SELECT carries a top-level
``ORDER BY count(*)`` so the catalog-observability gate passes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_publication_factor_extension import (
    CreatePublicationFactorExtensionCase,
    _present_failure_pair,
)
from .create_publication_factor_loop import (
    CreatePublicationFactorCase,
    CreatePublicationFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/publication/"
    "create_publication.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/publication/"
    "create_publication.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class CreatePublicationFactorRenderError(ValueError):
    """Raised when a CREATE PUBLICATION case cannot be rendered."""


@dataclass(frozen=True)
class CreatePublicationFactorWitness:
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
    ext: CreatePublicationFactorExtensionCase,
) -> CreatePublicationFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_form"
        factor_value = assignment.get(
            "target_form", ext.consumer_action_id
        )
    return CreatePublicationFactorCase(
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
    case: CreatePublicationFactorCase
    | CreatePublicationFactorExtensionCase,
) -> CreatePublicationFactorCase:
    if isinstance(case, CreatePublicationFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: CreatePublicationFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _publication_name(a: dict[str, str], p: str) -> str:
    """The publication identifier in CREATE PUBLICATION and fixtures."""

    shape = a.get("publication_name_shape", "simple_name")
    if shape == "quoted_name":
        return f'"{p}QPub"'
    if shape == "schema_qualified_name":
        return f'"{p}.pub"'
    if shape == "reserved_word_name":
        return '"all"'
    return f"{p}pub"


def _publication_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    shape = a.get("publication_name_shape", "simple_name")
    if shape == "quoted_name":
        return f"{p}QPub"
    if shape == "schema_qualified_name":
        return f"{p}.pub"
    if shape == "reserved_word_name":
        return "all"
    return f"{p}pub"


def _table_name(a: dict[str, str], p: str) -> str:
    """The table identifier used in FOR TABLE and fixtures."""

    shape = a.get("table_name_shape", "simple_name")
    if shape == "quoted_name":
        return f'"{p}QTab"'
    if shape == "schema_qualified_name":
        return f"public.{p}tab"
    if shape == "nonexistent_table":
        return f"{p}notab"
    return f"{p}tab"


def _schema_name(a: dict[str, str], p: str) -> str:
    """The schema identifier used in FOR TABLES IN SCHEMA and fixtures."""

    shape = a.get("schema_name_shape", "simple_name")
    if shape == "quoted_name":
        return f'"{p}QSch"'
    if shape == "current_schema_keyword":
        return "CURRENT_SCHEMA"
    if shape == "nonexistent_schema":
        return f"{p}nosch"
    return f"{p}sch"


def _is_duplicate(a: dict[str, str]) -> bool:
    pi = a.get("publication_identity", "not_exists")
    return pi in ("exists", "quoted_duplicate")


def _is_failure(a: dict[str, str]) -> bool:
    return a.get("expected_status") == "failure"


def _is_present(a: dict[str, str]) -> bool:
    """Whether the publication exists after the target statement."""

    if not _is_failure(a):
        return True
    if _is_duplicate(a):
        return True
    return False


def _build_with_clause(a: dict[str, str]) -> str:
    wpc = a.get("with_parameter_clause", "omitted")
    if wpc == "publish_insert_only":
        return " WITH (publish = 'insert')"
    if wpc == "publish_all_operations":
        return " WITH (publish = 'insert, update, delete, truncate')"
    if wpc == "publish_via_partition_root":
        return " WITH (publish_via_partition_root = true)"
    if wpc == "multiple_parameters":
        return (
            " WITH (publish = 'insert, update', "
            "publish_via_partition_root = true)"
        )
    return ""


def _column_list(a: dict[str, str]) -> str:
    cf = a.get("column_filter", "no_column_filter")
    cns = a.get("column_name_shape", "simple_name")

    if cns == "nonexistent_column":
        return "(badcol)"
    if cf == "no_column_filter":
        return ""
    if cns == "quoted_name":
        if cf == "single_column_filter":
            return '("id")'
        return '("id", "data")'
    if cf == "single_column_filter":
        return "(id)"
    if cf == "multiple_column_filter":
        return "(id, data)"
    return ""


def _where_clause(a: dict[str, str]) -> str:
    iwe = a.get("invalid_where_expression", "none")
    if iwe == "non_boolean_expression":
        return " WHERE (1)"
    wc = a.get("where_clause", "no_where")
    if wc == "simple_where_condition":
        return " WHERE (id > 0)"
    if wc == "complex_where_expression":
        return " WHERE (id > 0 AND id < 100)"
    return ""


def _build_for_clause(a: dict[str, str], p: str) -> str:
    """The FOR clause portion (without CREATE PUBLICATION prefix)."""

    cfc = a.get("conflicting_for_clause", "none")
    if cfc == "for_all_tables_with_for_table_conflict":
        return f"FOR ALL TABLES FOR TABLE {p}tab"

    fcs = a.get("for_clause_shape", "for_all_tables")
    only = "ONLY " if a.get("only_keyword") == "with_only" else ""
    tname = _table_name(a, p)
    cols = _column_list(a)
    where = _where_clause(a)

    if fcs == "for_all_tables":
        return "FOR ALL TABLES"
    if fcs == "no_for_clause":
        return ""
    if fcs == "for_table_multiple":
        return f"FOR TABLE {only}{tname}{cols}{where}, {p}tab2"
    if fcs == "for_mixed_table_and_schema":
        return (
            f"FOR TABLE {only}{tname}{cols}{where}, "
            f"TABLES IN SCHEMA {p}sch"
        )
    if fcs in (
        "for_tables_in_schema",
        "for_tables_in_schema_current_schema",
    ):
        sname = _schema_name(a, p)
        return f"FOR TABLES IN SCHEMA {sname}"
    # for_table_single (default for for_table branch)
    return f"FOR TABLE {only}{tname}{cols}{where}"


def _build_target(
    a: dict[str, str], p: str
) -> str:
    """The primary CREATE PUBLICATION statement."""

    name = _publication_name(a, p)
    for_clause = _build_for_clause(a, p)
    with_clause = _build_with_clause(a)

    target = f"CREATE PUBLICATION {name}"
    if for_clause:
        target += f" {for_clause}"
    if with_clause:
        target += with_clause
    return f"{target};"


def _effective_role(a: dict[str, str], p: str) -> str:
    priv = a.get("executor_privilege", "superuser")
    if priv == "non_superuser":
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    priv = a.get("executor_privilege", "superuser")
    if priv == "non_superuser":
        roles.append(f"{p}actor")
    return tuple(roles)


def _needs_table(a: dict[str, str]) -> bool:
    fcs = a.get("for_clause_shape", "for_all_tables")
    cfc = a.get("conflicting_for_clause", "none")
    return (
        fcs in (
            "for_table_single",
            "for_table_multiple",
            "for_mixed_table_and_schema",
        )
        or cfc == "for_all_tables_with_for_table_conflict"
    )


def _needs_schema(a: dict[str, str]) -> bool:
    fcs = a.get("for_clause_shape", "for_all_tables")
    return fcs in (
        "for_tables_in_schema",
        "for_tables_in_schema_current_schema",
        "for_mixed_table_and_schema",
    )


def _probe_select(
    case: CreatePublicationFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only verification."""

    mode = a.get("verification_mode", "pg_publication_catalog")
    literal = _publication_literal(a, p)

    if mode == "error_assertion":
        return None

    if _is_present(a):
        cmp_op = ">"
    else:
        cmp_op = "="

    if mode == "pg_publication_tables_catalog":
        return (
            f"SELECT count(*) {cmp_op} 0 AS pub_tables_state "
            f"FROM pg_catalog.pg_publication_tables "
            f"WHERE pubname = '{literal}' "
            f"ORDER BY count(*);"
        )

    return (
        f"SELECT count(*) {cmp_op} 0 AS pub_state "
        f"FROM pg_catalog.pg_publication "
        f"WHERE pubname = '{literal}' "
        f"ORDER BY count(*);"
    )


def _resolve_case(
    case: CreatePublicationFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix

    setup: list[str] = []
    locus = "target.create_publication"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    name = _publication_name(a, p)

    # --- role fixtures -----------------------------------------------
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- duplicate publication fixture --------------------------------
    if _is_duplicate(a):
        setup.append(f"CREATE PUBLICATION {name};")
        locus = "fixture.duplicate_publication"

    # --- table fixtures ----------------------------------------------
    # created_tables mirrors every TABLE the setup block CREATEs so the
    # bookend gate (statements[0]/statements[-1] must be a combined
    # DROP TABLE IF EXISTS ... CASCADE; naming every created table) can
    # be satisfied; mirrors create_policy_factor_render.
    created_tables: list[str] = []
    if _needs_table(a):
        tns = a.get("table_name_shape", "simple_name")
        td = a.get("table_dependency", "table_exists")
        fcs = a.get("for_clause_shape", "for_all_tables")
        cfc = a.get("conflicting_for_clause", "none")

        create_table = (
            tns != "nonexistent_table"
            and td != "table_not_exists"
        )

        if create_table:
            tname = _table_name(a, p)
            created_tables.append(tname)
            if td == "partition_table":
                setup.append(
                    f"CREATE TABLE {tname} (id integer, data text) "
                    f"PARTITION BY RANGE (id);"
                )
                setup.append(
                    f"CREATE TABLE {p}tabpart1 PARTITION OF {tname} "
                    f"FOR VALUES FROM (0) TO (100);"
                )
                created_tables.append(f"{p}tabpart1")
                locus = "fixture.partition_table"
            else:
                setup.append(
                    f"CREATE TABLE {tname} (id integer, data text);"
                )
                locus = "fixture.source_table"

            if fcs == "for_table_multiple":
                setup.append(
                    f"CREATE TABLE {p}tab2 (id integer, data text);"
                )
                created_tables.append(f"{p}tab2")

        if cfc == "for_all_tables_with_for_table_conflict":
            setup.append(
                f"CREATE TABLE {p}tab (id integer, data text);"
            )
            created_tables.append(f"{p}tab")
            locus = "fixture.conflict_table"

    created_tables = list(dict.fromkeys(created_tables))

    # --- schema fixtures ---------------------------------------------
    if _needs_schema(a):
        sns = a.get("schema_name_shape", "simple_name")
        sd = a.get("schema_dependency", "schema_exists")

        create_schema = (
            sns != "nonexistent_schema"
            and sns != "current_schema_keyword"
            and sd != "schema_not_exists"
        )

        if create_schema:
            sname = _schema_name(a, p)
            setup.append(f"CREATE SCHEMA {sname};")
            locus = "fixture.source_schema"

        if fcs_is_mixed := (
            a.get("for_clause_shape") == "for_mixed_table_and_schema"
        ):
            setup.append(f"CREATE SCHEMA {p}sch;")

    # --- arm the effective role --------------------------------------
    if effective:
        setup.append(f"SET ROLE {effective};")

    # --- the primary target statement --------------------------------
    target = _build_target(a, p)

    # --- oracle / SQLSTATE assertion ---------------------------------
    assert_lines: list[str] = []
    if effective:
        assert_lines.append("RESET ROLE;")
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    probe = _probe_select(case, a, p)
    if probe is not None:
        assert_lines.append(probe)

    # --- cleanup construction -----------------------------------------
    pub_drops: list[str] = []
    cleanup_mode = a.get("cleanup_mode", "drop_publication")
    if cleanup_mode == "DROP_PUBLICATION_IF_EXISTS":
        pub_drops = [f"DROP PUBLICATION IF EXISTS {name};"]
    else:
        pub_drops = [f"DROP PUBLICATION {name};"]

    schema_drops: list[str] = []
    if _needs_schema(a):
        sns = a.get("schema_name_shape", "simple_name")
        sd = a.get("schema_dependency", "schema_exists")
        schemas: list[str] = []
        if sns not in ("nonexistent_schema", "current_schema_keyword"):
            if sd != "schema_not_exists":
                schemas.append(_schema_name(a, p))
        if a.get("for_clause_shape") == "for_mixed_table_and_schema":
            schemas.append(f"{p}sch")
        for s in schemas:
            schema_drops.append(f"DROP SCHEMA IF EXISTS {s} CASCADE;")

    role_drops = [
        stmt
        for role in roles
        for stmt in (
            f"DROP OWNED BY {role} CASCADE;",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    # pre-cleanup: always use IF EXISTS (safe).  When this script CREATEs
    # fixture tables, the combined DROP TABLE IF EXISTS ... CASCADE; is
    # emitted FIRST so the shared bookend gate (which only inspects
    # statements[0]) sees every created table in a single ;-segment.
    pre_cleanup: list[str] = []
    if created_tables:
        pre_cleanup.append(
            f"DROP TABLE IF EXISTS {', '.join(created_tables)} CASCADE;"
        )
    pre_cleanup.append(f"DROP PUBLICATION IF EXISTS {name};")
    pre_cleanup.append(f"DROP PUBLICATION IF EXISTS {p}pub;")
    pre_cleanup.append(f'DROP PUBLICATION IF EXISTS "{p}QPub";')
    pre_cleanup.append(f'DROP PUBLICATION IF EXISTS "{p}.pub";')
    pre_cleanup.append('DROP PUBLICATION IF EXISTS "all";')
    pre_cleanup.append(f"DROP TABLE IF EXISTS {p}tab CASCADE;")
    pre_cleanup.append(f"DROP TABLE IF EXISTS {p}tab2 CASCADE;")
    pre_cleanup.append(f"DROP TABLE IF EXISTS {p}tabpart1 CASCADE;")
    pre_cleanup.append(f"DROP TABLE IF EXISTS {p}notab CASCADE;")
    pre_cleanup.append(f"DROP SCHEMA IF EXISTS {p}sch CASCADE;")
    pre_cleanup.append(f"DROP SCHEMA IF EXISTS {p}nosch CASCADE;")
    pre_cleanup.append("RESET ROLE;")
    for role in roles:
        pre_cleanup.append(f"DROP ROLE IF EXISTS {role};")

    # cleanup: RESET ROLE, publication, schemas, roles; then the combined
    # DROP TABLE IF EXISTS ... CASCADE; LAST (reverse creation order) so
    # the shared bookend gate (which only inspects statements[-1]) sees
    # every created table in a single ;-segment.
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(pub_drops)
    cleanup.extend(schema_drops)
    cleanup.extend(role_drops)
    if created_tables:
        cleanup.append(
            f"DROP TABLE IF EXISTS {', '.join(reversed(created_tables))} CASCADE;"
        )

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


def _header(case: CreatePublicationFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE PUBLICATION {case.factor_key}="
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


def render_create_publication_factor_case(
    case: CreatePublicationFactorCase
    | CreatePublicationFactorExtensionCase,
    repository_root: Path,
) -> str:
    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("SELECT 1 AS setup_boundary;")
    lines.append("-- 2. 创建完整本地规则和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("SELECT 1 AS pre_target_boundary;")
    lines.append("-- 3. 执行唯一获得覆盖信用的 CREATE PUBLICATION。")
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
    case: CreatePublicationFactorCase
    | CreatePublicationFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_publication_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_publication_factor_programs(
    baseline_plan: CreatePublicationFactorLoopPlan,
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


def count_primary_create_publication(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*CREATE\s+PUBLICATION\b", region)
    )


def remove_primary_semantic_locus_but_keep_comments(
    sql: str, case: object
) -> str:
    """Mutation helper: remove primary target SQL but keep comment lines."""

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


def resolve_create_publication_factor_witness(
    case: CreatePublicationFactorCase
    | CreatePublicationFactorExtensionCase,
    repository_root: Path,
) -> CreatePublicationFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreatePublicationFactorWitness(
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
    "CreatePublicationFactorRenderError",
    "CreatePublicationFactorWitness",
    "count_primary_create_publication",
    "generate_create_publication_factor_programs",
    "render_create_publication_factor_case",
    "resolve_create_publication_factor_witness",
    "remove_primary_semantic_locus_but_keep_comments",
]
