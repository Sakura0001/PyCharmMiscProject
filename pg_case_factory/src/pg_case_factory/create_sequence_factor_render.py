"""Render complete PostgreSQL 18.4 CREATE SEQUENCE factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file.  Most scripts are table-less-exempt; only ``owned_by_column`` and
``same_name_table`` scripts emit ``CREATE TABLE`` (per-script ``DROP
TABLE`` bookend).  All catalog oracles use ``pg_catalog`` /
``information_schema`` (exempt) with top-level ``ORDER BY``.

TEMP / TEMPORARY / UNLOGGED sequences ARE emitted — the parent col-0
regex must be relaxed to
``(?m)^CREATE\\s+(?:(?:TEMP(?:ORARY)?|UNLOGGED)\\s+)*SEQUENCE(?:\\s|;|$)``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_sequence_factor_extension import (
    CreateSequenceFactorExtensionCase,
    _present_failure_pair,
)
from .create_sequence_factor_loop import (
    CreateSequenceFactorCase,
    CreateSequenceFactorLoopPlan,
    _failure_conditions,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/sequence/"
    "create_sequence.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/sequence/"
    "create_sequence.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class CreateSequenceFactorRenderError(ValueError):
    """Raised when a CREATE SEQUENCE case cannot be rendered."""


@dataclass(frozen=True)
class CreateSequenceFactorWitness:
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
    is_table_creating: bool


def _synthetic_case(
    ext: CreateSequenceFactorExtensionCase,
) -> CreateSequenceFactorCase:
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
    return CreateSequenceFactorCase(
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
    case: CreateSequenceFactorCase
    | CreateSequenceFactorExtensionCase,
) -> CreateSequenceFactorCase:
    if isinstance(case, CreateSequenceFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateSequenceFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


# ---- name / fixture helpers ----


def _is_temp(a: dict[str, str]) -> bool:
    return a.get("sequence_type") in ("temporary", "temporary_short")


def _is_unlogged(a: dict[str, str]) -> bool:
    return a.get("sequence_type") == "unlogged"


def _uses_schema(a: dict[str, str]) -> bool:
    """Whether a custom schema fixture is needed."""

    nsh = a.get("sequence_name_shape", "simple")
    sd = a.get("schema_dependency", "schema_exists")
    if nsh == "schema_qualified" or sd in (
        "schema_not_exists",
        "pg_catalog_reserved",
    ):
        return True
    if _is_temp(a):
        return False
    obc = a.get("owned_by_clause", "absent_default")
    if obc == "owned_by_column":
        return False
    snc = a.get("same_name_conflict", "no_conflict")
    if snc == "same_name_table":
        return False
    return True


def _schema_name(a: dict[str, str], p: str) -> str:
    return f"{p}schema"


def _seq_name(a: dict[str, str], p: str) -> str:
    """The sequence identifier in CREATE SEQUENCE."""

    nsh = a.get("sequence_name_shape", "simple")
    sd = a.get("schema_dependency", "schema_exists")
    base = f"{p}seq"
    if sd == "pg_catalog_reserved":
        return f"pg_catalog.{base}"
    if sd == "schema_not_exists":
        return f"{p}norelsch.{base}"
    if nsh == "schema_qualified":
        return f"{_schema_name(a, p)}.{base}"
    if nsh == "quoted":
        return f'"{base}"'
    if nsh == "reserved_word":
        return '"select"'
    return base


def _seq_relname(a: dict[str, str], p: str) -> str:
    """The relname (unqualified) used in catalog queries."""

    nsh = a.get("sequence_name_shape", "simple")
    if nsh == "reserved_word":
        return "select"
    return f"{p}seq"


def _table_name(a: dict[str, str], p: str) -> str:
    return f"{p}tbl"


def _uses_table(a: dict[str, str]) -> bool:
    obc = a.get("owned_by_clause", "absent_default")
    snc = a.get("same_name_conflict", "no_conflict")
    otd = a.get("owned_by_table_dependency", "table_column_exists")
    if obc == "owned_by_column" and otd == "table_column_exists":
        return True
    if snc == "same_name_table":
        return True
    return False


def _uses_role(a: dict[str, str]) -> bool:
    pl = a.get("privilege_level", "sequence_creator")
    ip = a.get("insufficient_privilege", "has_create_privilege")
    return pl == "non_creator_no_privilege" or ip == "no_CREATE_privilege"


def _uses_view(a: dict[str, str]) -> bool:
    return a.get("same_name_conflict") == "same_name_view"


def _uses_duplicate_fixture(a: dict[str, str]) -> bool:
    tos = a.get("object_state", "not_exists")
    dsn = a.get("duplicate_sequence_name", "no_duplicate")
    return tos == "already_exists" or dsn in (
        "with_IF_NOT_EXISTS_noop",
        "without_IF_NOT_EXISTS_error",
    )


def _is_failure(a: dict[str, str]) -> bool:
    return a.get("expected_status") == "failure"


def _sequence_present(a: dict[str, str]) -> bool:
    """Whether the sequence exists after the target statement."""

    if not _is_failure(a):
        return True
    if _uses_duplicate_fixture(a):
        return True
    return False


# ---- target builder ----


def _type_prefix(a: dict[str, str]) -> str:
    st = a.get("sequence_type", "permanent")
    if st == "temporary":
        return "TEMPORARY "
    if st == "temporary_short":
        return "TEMP "
    if st == "unlogged":
        return "UNLOGGED "
    return ""


def _if_not_exists_kw(a: dict[str, str]) -> str:
    if a.get("if_not_exists_clause", "absent") == "present":
        return "IF NOT EXISTS "
    return ""


def _as_clause(a: dict[str, str]) -> str:
    adt = a.get("as_data_type", "absent_default")
    return "" if adt == "absent_default" else f"AS {adt} "


def _increment_clause(a: dict[str, str]) -> str:
    if a.get("increment_zero") == "zero_increment":
        return "INCREMENT BY 0 "
    if a.get("increment_direction", "ascending") == "descending":
        return "INCREMENT BY -1 "
    return ""


def _minmax_clause(a: dict[str, str]) -> str:
    setting = a.get("minvalue_maxvalue_setting", "absent_defaults")
    if a.get("minvalue_greater_than_maxvalue") == "min_greater_than_max":
        return "MINVALUE 100 MAXVALUE 10 "
    if a.get("incompatible_data_type_values") == "smallint_overflow":
        return "MINVALUE 1 MAXVALUE 100000 "
    if setting == "explicit_values":
        return "MINVALUE 1 MAXVALUE 1000 "
    if setting == "NO_MINVALUE_NO_MAXVALUE":
        return "NO MINVALUE NO MAXVALUE "
    return ""


def _start_clause(a: dict[str, str]) -> str:
    svs = a.get("start_value_setting", "absent_default")
    sor = a.get("start_out_of_range", "start_in_range")
    if sor == "start_above_maxvalue":
        return "START WITH 99999 "
    if sor == "start_below_minvalue":
        return "START WITH -99999 "
    if svs == "explicit_start":
        return "START WITH 5 "
    return ""


def _cache_clause(a: dict[str, str]) -> str:
    cv = a.get("cache_value", "absent_default")
    if cv == "cache_1":
        return "CACHE 1 "
    if cv == "cache_10":
        return "CACHE 10 "
    return ""


def _cycle_clause(a: dict[str, str]) -> str:
    cc = a.get("cycle_clause", "absent_default")
    if cc == "CYCLE":
        return "CYCLE "
    if cc == "NO_CYCLE":
        return "NO CYCLE "
    return ""


def _owned_by_clause(a: dict[str, str], p: str) -> str:
    obc = a.get("owned_by_clause", "absent_default")
    if obc == "owned_by_none":
        return "OWNED BY NONE "
    if obc == "owned_by_column":
        tbl = _table_name(a, p)
        return f"OWNED BY {tbl}.id "
    return ""


def _build_target(a: dict[str, str], p: str) -> str:
    """The primary CREATE SEQUENCE statement."""

    prefix = _type_prefix(a)
    ine = _if_not_exists_kw(a)
    name = _seq_name(a, p)
    parts = [
        f"CREATE {prefix}SEQUENCE {ine}{name}",
    ]
    option_str = (
        _as_clause(a) + _increment_clause(a) + _minmax_clause(a)
        + _start_clause(a) + _cache_clause(a) + _cycle_clause(a)
        + _owned_by_clause(a, p)
    ).strip()
    line = f"CREATE {prefix}SEQUENCE {ine}{name}"
    if option_str:
        line += f" {option_str}"
    line += ";"
    return line


# ---- verification oracle ----


def _probe_select(
    a: dict[str, str], p: str
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only verification."""

    mode = a.get("verification_mode", "pg_class_catalog_query")
    relname = _seq_relname(a, p)
    schema = _schema_name(a, p)
    present = _sequence_present(a)

    if mode == "error_assertion":
        return None

    if mode == "nextval_call":
        if present:
            full = _seq_name(a, p)
            return (
                f"SELECT nextval('{full}') "
                f"AS nextval_check ORDER BY 1;"
            )
        return None

    if mode == "sequence_inspection_query":
        if present:
            cmp_op = ">"
            cond = ""
        else:
            cmp_op = "="
            cond = ""
        return (
            f"SELECT count(*) {cmp_op} 0 AS seq_state "
            f"FROM information_schema.sequences "
            f"WHERE sequence_name = '{relname}' "
            f"{cond}"
            f"ORDER BY count(*);"
        ).replace("  ", " ").replace("' \n", "'\n")

    # pg_class_catalog_query (default)
    if present:
        cmp_op = ">"
    else:
        cmp_op = "="
    uses_sch = _uses_schema(a)
    if uses_sch:
        nsh = a.get("sequence_name_shape", "simple")
        sd = a.get("schema_dependency", "schema_exists")
        if sd == "pg_catalog_reserved":
            sch_filter = (
                f"AND relnamespace = "
                f"'pg_catalog'::regnamespace "
            )
        elif sd == "schema_not_exists":
            sch_filter = ""
        elif nsh == "schema_qualified":
            sch_filter = (
                f"AND relnamespace = "
                f"'{schema}'::regnamespace "
            )
        else:
            sch_filter = (
                f"AND relnamespace = "
                f"'{schema}'::regnamespace "
            )
    else:
        sch_filter = ""
    return (
        f"SELECT count(*) {cmp_op} 0 AS seq_state "
        f"FROM pg_catalog.pg_class "
        f"WHERE relname = '{relname}' "
        f"AND relkind = 'S' "
        f"{sch_filter}"
        f"ORDER BY count(*);"
    ).replace("  ", " ")


# ---- setup / cleanup builders ----


def _build_setup(
    a: dict[str, str], p: str
) -> tuple[list[str], str]:
    """Build fixture setup lines; return (lines, semantic_locus)."""

    setup: list[str] = []
    locus = "target.create_sequence"
    schema = _schema_name(a, p)
    tbl = _table_name(a, p)
    uses_sch = _uses_schema(a)
    uses_tbl = _uses_table(a)
    uses_view = _uses_view(a)
    uses_role = _uses_role(a)
    uses_dup = _uses_duplicate_fixture(a)
    snc = a.get("same_name_conflict", "no_conflict")

    # --- schema fixture ---
    if uses_sch:
        setup.append(f"CREATE SCHEMA {schema};")
        locus = "fixture.schema"

    # --- table fixture (owned_by_column success or same_name_table) ---
    if uses_tbl:
        if _is_temp(a):
            setup.append(
                f"CREATE TEMP TABLE {tbl} (id bigint);"
            )
        else:
            setup.append(
                f"CREATE TABLE {tbl} (id bigint);"
            )
        locus = "fixture.owned_by_table"

    # --- view fixture (same_name_view) ---
    if uses_view:
        vname = _seq_relname(a, p)
        setup.append(f'CREATE VIEW "{vname}" AS SELECT 1 AS id;')
        locus = "fixture.same_name_view"

    # --- duplicate sequence fixture ---
    if uses_dup:
        full = _seq_name(a, p)
        if _is_temp(a):
            setup.append(
                f"CREATE TEMP SEQUENCE {full};"
            )
        else:
            setup.append(
                f"CREATE SEQUENCE {full};"
            )
        locus = "fixture.duplicate_sequence"

    # --- same_name_table fixture (pre-create table with seq name) ---
    if snc == "same_name_table":
        vname = _seq_relname(a, p)
        setup.append(
            f'CREATE TABLE "{vname}" (id bigint);'
        )
        locus = "fixture.same_name_table"

    # --- role fixture for privilege tests ---
    if uses_role:
        setup.append(
            f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;"
        )
        if uses_sch:
            setup.append(
                f"GRANT USAGE ON SCHEMA {schema} TO {p}actor;"
            )
        locus = "fixture.privilege_state"

    if uses_role:
        setup.append(f"SET ROLE {p}actor;")

    return setup, locus


def _build_cleanup(
    a: dict[str, str], p: str
) -> list[str]:
    """Build cleanup lines (order matters for bookend)."""

    schema = _schema_name(a, p)
    tbl = _table_name(a, p)
    full = _seq_name(a, p)
    uses_sch = _uses_schema(a)
    uses_tbl = _uses_table(a)
    uses_view = _uses_view(a)
    uses_role = _uses_role(a)
    snc = a.get("same_name_conflict", "no_conflict")
    cleanup_mode = a.get("cleanup_mode", "DROP_SEQUENCE_IF_EXISTS")

    cleanup: list[str] = []
    if uses_role:
        cleanup.append("RESET ROLE;")

    drop_kw = "DROP SEQUENCE"
    if cleanup_mode == "DROP_SEQUENCE_CASCADE":
        drop_kw = "DROP SEQUENCE"
    elif cleanup_mode == "DROP_SEQUENCE_IF_EXISTS":
        drop_kw = "DROP SEQUENCE IF EXISTS"

    # Drop the sequence (may not exist if CREATE failed)
    cleanup.append(f"{drop_kw} {full} CASCADE;")

    # Drop view fixture
    if uses_view:
        vname = _seq_relname(a, p)
        cleanup.append(f'DROP VIEW IF EXISTS "{vname}" CASCADE;')

    # Drop duplicate fixture sequence (the pre-created one)
    if _uses_duplicate_fixture(a):
        cleanup.append(f"{drop_kw} {full} CASCADE;")

    # Drop same_name_table fixture
    if snc == "same_name_table":
        vname = _seq_relname(a, p)
        cleanup.append(f'DROP TABLE IF EXISTS "{vname}" CASCADE;')

    # Drop schema (before final DROP TABLE for table-creating scripts)
    if uses_sch:
        sd = a.get("schema_dependency", "schema_exists")
        if sd != "pg_catalog_reserved":
            cleanup.append(
                f"DROP SCHEMA IF EXISTS {schema} CASCADE;"
            )

    # Drop role (before final DROP TABLE)
    if uses_role:
        cleanup.append(f"DROP OWNED BY {p}actor CASCADE;")
        cleanup.append(f"DROP ROLE IF EXISTS {p}actor;")

    # Final DROP TABLE (bookend: must be LAST for table-creating scripts)
    if uses_tbl:
        cleanup.append(f"DROP TABLE IF EXISTS {tbl} CASCADE;")

    return cleanup


def _build_pre_cleanup(
    a: dict[str, str], p: str
) -> list[str]:
    """Build pre-cleanup lines (first must be DROP TABLE if table-creating)."""

    schema = _schema_name(a, p)
    tbl = _table_name(a, p)
    uses_sch = _uses_schema(a)
    uses_tbl = _uses_table(a)
    uses_role = _uses_role(a)
    uses_view = _uses_view(a)
    uses_dup = _uses_duplicate_fixture(a)
    snc = a.get("same_name_conflict", "no_conflict")

    pre: list[str] = []

    # For table-creating scripts, DROP TABLE must be FIRST
    if uses_tbl:
        pre.append(f"DROP TABLE IF EXISTS {tbl} CASCADE;")
    if snc == "same_name_table":
        vname = _seq_relname(a, p)
        pre.append(f'DROP TABLE IF EXISTS "{vname}" CASCADE;')

    # Drop sequence (duplicate fixtures etc.)
    full = _seq_name(a, p)
    pre.append(f"DROP SEQUENCE IF EXISTS {full} CASCADE;")

    # Drop view
    if uses_view:
        vname = _seq_relname(a, p)
        pre.append(f'DROP VIEW IF EXISTS "{vname}" CASCADE;')

    # Drop schema
    if uses_sch:
        sd = a.get("schema_dependency", "schema_exists")
        if sd != "pg_catalog_reserved":
            pre.append(f"DROP SCHEMA IF EXISTS {schema} CASCADE;")

    pre.append("RESET ROLE;")
    if uses_role:
        pre.append(f"DROP ROLE IF EXISTS {p}actor;")

    return pre


def _resolve_case(
    case: CreateSequenceFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix

    setup, locus = _build_setup(a, p)
    target = _build_target(a, p)

    assert_lines: list[str] = []
    uses_role = _uses_role(a)
    if uses_role:
        assert_lines.append("RESET ROLE;")
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    probe = _probe_select(a, p)
    if probe is not None:
        assert_lines.append(probe)

    cleanup = _build_cleanup(a, p)
    pre_cleanup = _build_pre_cleanup(a, p)

    on_error_off = case.outcome == "expected_failure"
    is_table_creating = _uses_table(a) or a.get(
        "same_name_conflict"
    ) == "same_name_table"
    return _CasePlan(
        target_fragment=target,
        setup_lines=tuple(setup),
        assert_lines=tuple(assert_lines),
        pre_cleanup_lines=tuple(pre_cleanup),
        cleanup_lines=tuple(cleanup),
        on_error_off=on_error_off,
        semantic_locus=locus,
        is_table_creating=is_table_creating,
    )


def _header(case: CreateSequenceFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE SEQUENCE {case.factor_key}="
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


def render_create_sequence_factor_case(
    case: CreateSequenceFactorCase
    | CreateSequenceFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 CREATE SEQUENCE。")
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
    case: CreateSequenceFactorCase
    | CreateSequenceFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_sequence_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_sequence_factor_programs(
    baseline_plan: CreateSequenceFactorLoopPlan,
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


def count_primary_create_sequence(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(
            r"(?im)^\s*CREATE\s+"
            r"(?:(?:TEMP(?:ORARY)?|UNLOGGED)\s+)*"
            r"SEQUENCE\b",
            region,
        )
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


def resolve_create_sequence_factor_witness(
    case: CreateSequenceFactorCase
    | CreateSequenceFactorExtensionCase,
    repository_root: Path,
) -> CreateSequenceFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateSequenceFactorWitness(
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
    "CreateSequenceFactorRenderError",
    "CreateSequenceFactorWitness",
    "count_primary_create_sequence",
    "generate_create_sequence_factor_programs",
    "render_create_sequence_factor_case",
    "resolve_create_sequence_factor_witness",
    "remove_primary_semantic_locus_but_keep_comments",
]
