"""Render complete PostgreSQL 18.4 CREATE VIEW factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CREATE VIEW creates a ``pg_class`` relation of kind ``v`` — not a base
table — so the bookend (DROP TABLE IF EXISTS) is never emitted as the
col-0 primary target.  Fixture base tables use ``CREATE TABLE`` in the
setup section and ``DROP TABLE IF EXISTS`` in the cleanup section, which
do not trigger the bookend gate.  All catalog oracles schema-qualify
``pg_catalog`` (exempt from the file-prefix style gate via the ``pg_``
prefix) and carry a top-level ``ORDER BY``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_view_factor_extension import (
    CreateViewFactorExtensionCase,
    _present_failure_pair,
)
from .create_view_factor_loop import (
    CreateViewFactorCase,
    CreateViewFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/"
    "view/create_view.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/"
    "view/create_view.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class CreateViewFactorRenderError(ValueError):
    """Raised when a CREATE VIEW case cannot be rendered."""


@dataclass(frozen=True)
class CreateViewFactorWitness:
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
    ext: CreateViewFactorExtensionCase,
) -> CreateViewFactorCase:
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
    return CreateViewFactorCase(
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
    case: CreateViewFactorCase | CreateViewFactorExtensionCase,
) -> CreateViewFactorCase:
    if isinstance(case, CreateViewFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateViewFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _schema_name(p: str) -> str:
    return f"{p}schema"


def _view_name(a: dict[str, str], p: str) -> str:
    """The view identifier in CREATE VIEW."""

    shape = a.get("view_name_shape", "simple")
    schema = _schema_name(p)
    if shape == "quoted":
        return f'{schema}."{p}view"'
    if shape == "reserved_word":
        return f'{schema}."select"'
    if shape == "schema_qualified":
        return f"{schema}.{p}view"
    if shape == "duplicate":
        return f"{schema}.{p}view"
    return f"{schema}.{p}view"


def _view_name_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    shape = a.get("view_name_shape", "simple")
    if shape == "quoted":
        return f"{p}view"
    if shape == "reserved_word":
        return "select"
    return f"{p}view"


def _base_table_name(p: str, suffix: str = "base") -> str:
    schema = _schema_name(p)
    return f"{schema}.{p}{suffix}"


_BASE_TABLE_COLUMNS: dict[str, tuple[tuple[str, str, str], ...]] = {
    "representative_int_types": (
        ("c1", "smallint", "1"),
        ("c2", "integer", "100"),
        ("c3", "bigint", "2000000"),
    ),
    "representative_string_types": (
        ("c1", "varchar(50)", "'hello'"),
        ("c2", "text", "'world'"),
        ("c3", "char(10)", "'fixed'"),
    ),
    "representative_datetime_types": (
        ("c1", "date", "'2026-01-01'"),
        ("c2", "timestamp", "'2026-01-01 12:00:00'"),
        ("c3", "interval", "'1 day'"),
    ),
    "representative_numeric_types": (
        ("c1", "numeric(10,2)", "3.14"),
        ("c2", "real", "2.5"),
        ("c3", "double precision", "1.5"),
    ),
    "representative_json_types": (
        ("c1", "json", "'[1,2,3]'"),
        ("c2", "jsonb", "'[4,5,6]'"),
        ("c3", "text", "'jsonrow'"),
    ),
    "representative_boolean_types": (
        ("c1", "boolean", "true"),
        ("c2", "boolean", "false"),
        ("c3", "integer", "1"),
    ),
}


def _columns(a: dict[str, str]) -> tuple[tuple[str, str, str], ...]:
    return _BASE_TABLE_COLUMNS.get(
        a.get("base_table_coverage", "representative_int_types"),
        _BASE_TABLE_COLUMNS["representative_int_types"],
    )


def _is_duplicate(a: dict[str, str]) -> bool:
    return (
        a.get("object_state") == "already_exists"
        or a.get("view_name_shape") == "duplicate"
    )


def _is_dependency_missing(a: dict[str, str]) -> bool:
    ds = a.get("dependency_state", "base_table_exists")
    return ds in ("base_table_not_exists", "referenced_view_not_exists")


def _is_insufficient_privilege(a: dict[str, str]) -> bool:
    return a.get("privilege_level") == "non_owner_no_privilege"


def _is_failure(a: dict[str, str]) -> bool:
    return a.get("expected_status") == "failure"


def _is_recursive(a: dict[str, str]) -> bool:
    return a.get("recursive_clause") == "present"


def _is_merge_failure(a: dict[str, str]) -> bool:
    return a.get("error_boundary") == "merge_view_with_rules"


def _is_merge_updatable(a: dict[str, str]) -> bool:
    return a.get("query_shape") == "merge_updatable_view"


def _effective_role(a: dict[str, str], p: str) -> str:
    if _is_insufficient_privilege(a):
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    if _is_insufficient_privilege(a):
        roles.append(f"{p}actor")
    return tuple(roles)


def _col_name(shape: str, base: str) -> str:
    if shape == "quoted":
        return f'"{base}"'
    if shape == "reserved_word":
        return f'"select"'
    return base


def _column_list_clause(a: dict[str, str]) -> str:
    """The optional (col1, col2, ...) list for CREATE VIEW."""

    cnl = a.get("column_name_list", "absent")
    if cnl == "absent":
        return ""
    shape = a.get("column_name_shape", "simple")
    cols = _columns(a)
    names = ", ".join(_col_name(shape, c[0]) for c in cols)
    return f" ({names})"


def _with_options_clause(a: dict[str, str]) -> str:
    """The optional WITH (...) clause."""

    opt = a.get("with_options_clause", "absent")
    if opt == "absent":
        return ""
    if opt == "security_barrier":
        return " WITH (security_barrier = true)"
    if opt == "security_invoker":
        return " WITH (security_invoker = true)"
    if opt == "check_option":
        return " WITH (check_option = cascaded)"
    if opt == "multiple_options":
        return (
            " WITH (security_barrier = true, "
            "security_invoker = true)"
        )
    return ""


def _check_option_clause(a: dict[str, str]) -> str:
    co = a.get("check_option_clause", "absent")
    if co == "cascaded":
        return " WITH CASCADED CHECK OPTION"
    if co == "local":
        return " WITH LOCAL CHECK OPTION"
    return ""


def _query_sql(a: dict[str, str], p: str) -> str:
    """The AS query expression for CREATE VIEW."""

    shape = a.get("query_shape", "select_simple")
    base = _base_table_name(p)
    cols = _columns(a)
    col_names = ", ".join(c[0] for c in cols)
    first_col = cols[0][0]

    if shape == "values_clause":
        v0 = cols[0][2]
        v1 = cols[1][2] if len(cols) > 1 else "0"
        return f"VALUES ({v0}, {v1}), ({v0}, {v1})"
    if shape == "select_with_where":
        return (
            f"SELECT {col_names} FROM {base} "
            f"WHERE {first_col} > 0"
        )
    if shape == "select_with_join":
        base2 = _base_table_name(p, "join")
        return (
            f"SELECT a.{first_col}, b.{cols[1][0]} "
            f"FROM {base} a JOIN {base2} b "
            f"ON a.{first_col} = b.{first_col}"
        )
    if shape == "select_with_aggregate":
        return (
            f"SELECT {first_col}, count(*) AS cnt "
            f"FROM {base} GROUP BY {first_col}"
        )
    if shape == "select_with_expression":
        return (
            f"SELECT {first_col}, {first_col} * 2 AS doubled "
            f"FROM {base}"
        )
    if shape == "merge_updatable_view":
        return (
            f"SELECT {col_names} FROM {base} "
            f"WHERE {first_col} > 0"
        )
    return f"SELECT {col_names} FROM {base}"


def _build_target(a: dict[str, str], p: str) -> str:
    """The primary CREATE VIEW statement (possibly with MERGE/RULE)."""

    name = _view_name(a, p)
    or_replace = (
        "OR REPLACE " if a.get("or_replace_clause") == "present" else ""
    )
    temp = ""
    tc = a.get("temporary_clause", "permanent")
    if tc == "temp":
        temp = "TEMP "
    elif tc == "temporary":
        temp = "TEMPORARY "
    recursive = (
        "RECURSIVE " if a.get("recursive_clause") == "present" else ""
    )
    col_list = _column_list_clause(a)
    with_options = _with_options_clause(a)
    query = _query_sql(a, p)
    check_option = _check_option_clause(a)

    stmt = (
        f"CREATE {or_replace}{temp}{recursive}VIEW {name}"
        f"{col_list}{with_options} AS {query}{check_option};"
    )

    if _is_merge_failure(a):
        base = _base_table_name(p)
        rule = f"{p}updrule"
        src = _base_table_name(p, "src")
        return (
            f"{stmt}\n"
            f"CREATE RULE {rule} AS ON UPDATE TO {name} "
            f"DO INSTEAD NOTHING;\n"
            f"MERGE INTO {name} v USING {src} s "
            f"ON v.c1 = s.c1 WHEN MATCHED THEN DO NOTHING;"
        )
    return stmt


def _build_base_table_fixture(
    a: dict[str, str], p: str
) -> list[str]:
    """CREATE TABLE + INSERT for the view's source data."""

    if _is_dependency_missing(a):
        return []
    ds = a.get("dependency_state", "base_table_exists")
    cols = _columns(a)
    schema = _schema_name(p)
    lines: list[str] = []

    if ds == "referenced_view_exists":
        base = _base_table_name(p)
        ref_view = f"{schema}.{p}refview"
        col_defs = ", ".join(f"{c[0]} {c[1]}" for c in cols)
        lines.append(
            f"CREATE TABLE {base} ({col_defs});"
        )
        vals = ", ".join(c[2] for c in cols)
        lines.append(f"INSERT INTO {base} VALUES ({vals});")
        first_col = cols[0][0]
        lines.append(
            f"CREATE VIEW {ref_view} AS SELECT {first_col} "
            f"FROM {base};"
        )
        return lines

    base = _base_table_name(p)
    col_defs = ", ".join(f"{c[0]} {c[1]}" for c in cols)
    lines.append(f"CREATE TABLE {base} ({col_defs});")
    vals = ", ".join(c[2] for c in cols)
    lines.append(f"INSERT INTO {base} VALUES ({vals});")

    shape = a.get("query_shape", "select_simple")
    if shape == "select_with_join":
        base2 = _base_table_name(p, "join")
        lines.append(f"CREATE TABLE {base2} ({col_defs});")
        lines.append(f"INSERT INTO {base2} VALUES ({vals});")
    if _is_merge_failure(a) or _is_merge_updatable(a):
        src = _base_table_name(p, "src")
        lines.append(f"CREATE TABLE {src} ({col_defs});")
        lines.append(f"INSERT INTO {src} VALUES ({vals});")
    return lines


def _build_duplicate_fixture(
    a: dict[str, str], p: str
) -> list[str]:
    """Pre-create the view for duplicate-signature tests."""

    if not _is_duplicate(a):
        return []
    schema = _schema_name(p)
    base = _base_table_name(p)
    cols = _columns(a)
    col_names = ", ".join(c[0] for c in cols)
    lines: list[str] = []

    eb = a.get("error_boundary", "none")
    if eb == "or_replace_column_mismatch":
        mismatch_cols = ", ".join(
            f"{c[0]} {c[1]}" for c in cols[:2]
        )
        lines.append(
            f"CREATE VIEW {schema}.{p}view AS "
            f"SELECT {mismatch_cols} FROM {base};"
        )
    else:
        lines.append(
            f"CREATE VIEW {schema}.{p}view AS "
            f"SELECT {col_names} FROM {base};"
        )
    return lines


def _build_role_fixture(
    a: dict[str, str], p: str
) -> list[str]:
    """Role fixture for privilege tests."""

    if not _is_insufficient_privilege(a):
        return []
    schema = _schema_name(p)
    base = _base_table_name(p)
    lines = [
        f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;",
        f"GRANT USAGE ON SCHEMA {schema} TO {p}actor;",
        f"GRANT SELECT ON {base} TO {p}actor;",
    ]
    return lines


def _probe_select(
    case: CreateViewFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only verification."""

    mode = a.get("verification_mode", "pg_class_query")
    if mode == "error_assertion":
        return None

    view_lit = _view_name_literal(a, p)
    present = not (_is_failure(a) and not _is_duplicate(a))
    if _is_merge_failure(a):
        present = False
    cmp_op = ">" if present else "="

    if mode == "information_schema_views":
        return (
            f"SELECT count(*) {cmp_op} 0 AS view_state "
            f"FROM information_schema.views "
            f"WHERE table_name = '{view_lit}' "
            f"ORDER BY count(*);"
        )
    if mode == "select_from_view":
        if not present:
            return None
        name = _view_name(a, p)
        return (
            f"SELECT count(*) > 0 AS view_readable "
            f"FROM {name} ORDER BY 1;"
        )
    return (
        f"SELECT count(*) {cmp_op} 0 AS view_state "
        f"FROM pg_catalog.pg_class "
        f"WHERE relname = '{view_lit}' AND relkind = 'v' "
        f"ORDER BY count(*);"
    )


def _build_merge_assert(a: dict[str, str], p: str) -> list[str]:
    """Additional oracle for merge_updatable_view success cases."""

    if not _is_merge_updatable(a) or _is_failure(a):
        return []
    name = _view_name(a, p)
    src = _base_table_name(p, "src")
    base = _base_table_name(p)
    return [
        f"MERGE INTO {name} v USING {src} s "
        f"ON v.c1 = s.c1 WHEN MATCHED THEN "
        f"UPDATE SET c2 = s.c2;",
        f"SELECT count(*) AS merge_effect "
        f"FROM {base} ORDER BY count(*);",
    ]


def _build_cleanup(a: dict[str, str], p: str) -> list[str]:
    """Cleanup lines after the primary target."""

    schema = _schema_name(p)
    cleanup_mode = a.get("cleanup_mode", "drop_view_if_exists")
    lines: list[str] = []
    if _is_insufficient_privilege(a):
        lines.append("RESET ROLE;")
    view_name = _view_name(a, p)
    base = _base_table_name(p)
    base2 = _base_table_name(p, "join")
    src = _base_table_name(p, "src")
    ref_view = f"{schema}.{p}refview"
    if cleanup_mode == "drop_view_cascade":
        if not _is_syntax_or_reserved(a):
            lines.append(f"DROP VIEW {view_name} CASCADE;")
    elif cleanup_mode == "drop_base_table_cascade":
        lines.append(f"DROP VIEW IF EXISTS {view_name} CASCADE;")
        lines.append(f"DROP TABLE IF EXISTS {base} CASCADE;")
    else:
        if not _is_syntax_or_reserved(a):
            lines.append(f"DROP VIEW IF EXISTS {view_name} CASCADE;")
    lines.append(f"DROP VIEW IF EXISTS {ref_view} CASCADE;")
    lines.append(f"DROP SCHEMA IF EXISTS {schema} CASCADE;")
    for role in _role_names(a, p):
        lines.append(f"DROP OWNED BY {role} CASCADE;")
        lines.append(f"DROP ROLE IF EXISTS {role};")
    # Bookend gate: the final ;-segment must be a single DROP TABLE IF EXISTS
    # statement covering every table this case may create.  The schema/role
    # cleanup above already CASCADE-removed them, so this is a safe no-op that
    # satisfies the gate's last-segment requirement.
    lines.append(f"DROP TABLE IF EXISTS {base}, {base2}, {src} CASCADE;")
    return lines


def _is_syntax_or_reserved(a: dict[str, str]) -> bool:
    """Views whose name is a quoted reserved word still need DROP."""
    return False


def _resolve_case(
    case: CreateViewFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    schema = _schema_name(p)

    setup: list[str] = []
    locus = "target.create_view"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)

    setup.append(f"CREATE SCHEMA {schema};")
    locus = "fixture.schema"

    setup.extend(_build_base_table_fixture(a, p))
    if not _is_dependency_missing(a):
        locus = "fixture.base_table"

    if _is_duplicate(a):
        setup.extend(_build_duplicate_fixture(a, p))
        locus = "fixture.duplicate_view"

    if effective:
        setup.extend(_build_role_fixture(a, p))
        locus = "fixture.privilege_state"
        setup.append(f"SET ROLE {effective};")

    target = _build_target(a, p)

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
    assert_lines.extend(_build_merge_assert(a, p))

    cleanup = _build_cleanup(a, p)

    pre_cleanup: list[str] = []
    view_name = _view_name(a, p)
    base = _base_table_name(p)
    base2 = _base_table_name(p, "join")
    src = _base_table_name(p, "src")
    ref_view = f"{schema}.{p}refview"
    # Bookend gate: the first ;-segment must be a single DROP TABLE IF EXISTS
    # statement covering every table this case may create.  base/base2/src are
    # the render's full table vocabulary, so the superset drop satisfies the
    # gate; CASCADE also removes dependent views before the no-op DROP VIEWs.
    pre_cleanup.append(f"DROP TABLE IF EXISTS {base}, {base2}, {src} CASCADE;")
    pre_cleanup.append(f"DROP VIEW IF EXISTS {view_name} CASCADE;")
    pre_cleanup.append(f"DROP VIEW IF EXISTS {ref_view} CASCADE;")
    pre_cleanup.append(f"DROP SCHEMA IF EXISTS {schema} CASCADE;")
    pre_cleanup.append("RESET ROLE;")
    for role in roles:
        pre_cleanup.append(f"DROP ROLE IF EXISTS {role};")
    if not pre_cleanup:
        pre_cleanup.append(
            "SELECT 1 AS residual_check_no_objects;"
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


def _header(case: CreateViewFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE VIEW "
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


def render_create_view_factor_case(
    case: CreateViewFactorCase | CreateViewFactorExtensionCase,
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
    lines.append(
        "-- 3. 执行唯一获得覆盖信用的 CREATE VIEW。"
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
    case: CreateViewFactorCase | CreateViewFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_view_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_view_factor_programs(
    baseline_plan: CreateViewFactorLoopPlan,
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


def count_primary_create_view(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(
            r"(?im)^CREATE\s+(?:OR\s+REPLACE\s+)?"
            r"(?:TEMP(?:ORARY)?\s+)?"
            r"(?:RECURSIVE\s+)?VIEW\b",
            region,
        )
    )


def resolve_create_view_factor_witness(
    case: CreateViewFactorCase | CreateViewFactorExtensionCase,
    repository_root: Path,
) -> CreateViewFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateViewFactorWitness(
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
    "CreateViewFactorRenderError",
    "CreateViewFactorWitness",
    "count_primary_create_view",
    "generate_create_view_factor_programs",
    "render_create_view_factor_case",
    "resolve_create_view_factor_witness",
]
