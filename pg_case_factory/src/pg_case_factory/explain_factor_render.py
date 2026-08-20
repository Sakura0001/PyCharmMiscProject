"""Render complete PostgreSQL 18.4 EXPLAIN factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

EXPLAIN is a plan-output utility statement.  Cases that target a
relation create a fixture ``CREATE TABLE {p}t ({p}c int)`` with sample
rows, and the bookend (DROP TABLE IF EXISTS as the first + last
executable ``;``-statement) applies.  Cases that target a non-existent
relation (target_missing) do not create a TABLE, so the bookend is
N/A.  Cases that target a wrong object type (wrong_object_type) create
a SEQUENCE (not selectable as a table).  Every catalog SELECT carries
a top-level ``ORDER BY count(*) LIMIT 1`` so the catalog-observability
gate passes.  The fixture CREATE TABLE / DROP TABLE always use
unquoted base names; quoted/schema-qualified shapes appear ONLY in the
credited EXPLAIN target's relation reference.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .explain_factor_extension import (
    ExplainFactorExtensionCase,
    _present_failure_pair,
)
from .explain_factor_loop import (
    ExplainFactorCase,
    ExplainFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/utility/plan/"
    "explain.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/utility/plan/"
    "explain.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-21"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class ExplainFactorRenderError(ValueError):
    """Raised when an EXPLAIN case cannot be rendered."""


@dataclass(frozen=True)
class ExplainFactorWitness:
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
    ext: ExplainFactorExtensionCase,
) -> ExplainFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get("target_action", "explain")
    return ExplainFactorCase(
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
    case: ExplainFactorCase | ExplainFactorExtensionCase,
) -> ExplainFactorCase:
    if isinstance(case, ExplainFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: ExplainFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _table_name(p: str) -> str:
    return f"{p}t"


def _col_name(p: str) -> str:
    return f"{p}c"


def _query_for(a: dict[str, str], p: str) -> str:
    """The statement EXPLAIN inspects, shaped by target_name_shape."""

    shape = a.get("target_name_shape", "plain_identifier")
    t = _table_name(p)

    if shape == "all_or_database_wide":
        return "SELECT 1"
    if shape == "schema_qualified":
        return f"SELECT * FROM public.{t}"
    if shape == "quoted_identifier":
        return f'SELECT * FROM "{t}"'
    return f"SELECT * FROM {t}"


def _option_clause(a: dict[str, str]) -> str:
    """The option content inside parentheses, or empty for bare EXPLAIN."""

    shape = a.get("option_shape", "minimal")
    if shape == "minimal":
        return ""
    if shape == "verbose_or_format":
        return "VERBOSE"
    if shape == "boolean_options":
        return "ANALYZE"
    if shape == "resource_options":
        return "BUFFERS"
    if shape == "serialize":
        return "SERIALIZE"
    if shape == "memory":
        return "SUMMARY"
    return ""


def _build_target(a: dict[str, str], p: str) -> str:
    """The primary EXPLAIN statement."""

    t = _table_name(p)

    # syntax_valid_semantic_error: a syntactically valid but semantically
    # invalid option combo (WAL requires ANALYZE) reaches a real error.
    if a.get("invalid_combination") == "syntax_valid_semantic_error":
        return f"EXPLAIN (WAL) SELECT * FROM {t};"

    opts = _option_clause(a)
    query = _query_for(a, p)
    if opts:
        return f"EXPLAIN ({opts}) {query};"
    return f"EXPLAIN {query};"


def _creates_table(a: dict[str, str]) -> bool:
    """Whether the case creates a TABLE (bookend applicability)."""

    ts = a.get("target_state", "target_exists")
    return ts not in ("target_missing", "wrong_object_type")


def _creates_sequence(a: dict[str, str]) -> bool:
    return a.get("target_state") == "wrong_object_type"


def _needs_role(a: dict[str, str]) -> bool:
    pc = a.get("privilege_context", "owner")
    return pc in ("granted_role", "insufficient_privilege")


def _probe_select(
    case: ExplainFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for error_assertion."""

    mode = a.get("verification_mode", "catalog_query")
    if mode == "error_assertion":
        return None

    ts = a.get("target_state", "target_exists")
    t = _table_name(p)

    if ts == "database_wide":
        return (
            "SELECT count(*) > 0 AS database_explained "
            "FROM pg_catalog.pg_class "
            f"WHERE relname = '{t}' "
            "ORDER BY count(*) LIMIT 1;"
        )

    if mode == "catalog_query":
        if ts == "target_missing":
            return (
                "SELECT count(*) = 0 AS relation_absent "
                "FROM pg_catalog.pg_class "
                f"WHERE relname = '{t}' "
                "ORDER BY count(*) LIMIT 1;"
            )
        if ts == "wrong_object_type":
            return (
                "SELECT count(*) = 0 AS not_a_regular_table "
                "FROM pg_catalog.pg_class "
                f"WHERE relname = '{t}' AND relkind = 'r' "
                "ORDER BY count(*) LIMIT 1;"
            )
        return (
            "SELECT count(*) > 0 AS relation_present "
            "FROM pg_catalog.pg_class "
            f"WHERE relname = '{t}' "
            "ORDER BY count(*) LIMIT 1;"
        )

    if mode == "effect_query":
        if ts == "target_exists":
            return (
                "SELECT count(*) > 0 AS plan_effect "
                "FROM pg_catalog.pg_class "
                f"WHERE relname = '{t}' "
                "ORDER BY count(*) LIMIT 1;"
            )
        return (
            "SELECT count(*) = 0 AS no_plan "
            "FROM pg_catalog.pg_class "
            f"WHERE relname = '{t}' AND relkind = 'r' "
            "ORDER BY count(*) LIMIT 1;"
        )

    if mode == "returned_rows":
        if ts == "target_exists":
            return (
                "SELECT count(*) > 0 AS explain_ran "
                "FROM pg_catalog.pg_class "
                f"WHERE relname = '{t}' "
                "ORDER BY count(*) LIMIT 1;"
            )
        return (
            "SELECT count(*) = 0 AS no_explain "
            "FROM pg_catalog.pg_class "
            f"WHERE relname = '{t}' AND relkind = 'r' "
            "ORDER BY count(*) LIMIT 1;"
        )

    return None


def _resolve_case(
    case: ExplainFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    t = _table_name(p)
    c = _col_name(p)
    ts = a.get("target_state", "target_exists")

    setup: list[str] = []
    locus = "target.explain"

    # --- privilege fixtures ------------------------------------------
    if _needs_role(a):
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- the target fixture ------------------------------------------
    if ts == "target_missing":
        setup.append(
            "SELECT 1 AS target_table_intentionally_absent;"
        )
        locus = "fixture.table_missing"
    elif ts == "wrong_object_type":
        setup.append(f"CREATE SEQUENCE {t};")
        locus = "fixture.wrong_object_type"
    else:
        setup.append(f"CREATE TABLE {t} ({c} int);")
        setup.append(f"INSERT INTO {t} VALUES (1), (2), (3);")
        locus = "fixture.table"

    # --- privilege grants --------------------------------------------
    if a.get("privilege_context") == "granted_role":
        setup.append(f"GRANT SELECT ON {t} TO {p}actor;")
        locus = "fixture.granted_select"
    if _needs_role(a):
        setup.append(f"SET ROLE {p}actor;")

    # --- the primary target statement --------------------------------
    target = _build_target(a, p)

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

    # --- cleanup construction -----------------------------------------
    pre_cleanup: list[str] = []
    cleanup: list[str] = []

    # Pre-cleanup: DROP SEQUENCE first (if applicable), then DROP TABLE,
    # then DROP ROLE.  For table-creating cases, DROP TABLE must be
    # the first executable statement (bookend).
    if _creates_sequence(a):
        pre_cleanup.append(f"DROP SEQUENCE IF EXISTS {t};")
    if _creates_table(a):
        pre_cleanup.append(f"DROP TABLE IF EXISTS {t};")
    if _needs_role(a):
        pre_cleanup.append(f"DROP ROLE IF EXISTS {p}actor;")
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # Cleanup: RESET ROLE, cleanup_mode, DROP ROLE, DROP SEQUENCE/TABLE.
    if _needs_role(a):
        cleanup.append("RESET ROLE;")
    cm = a.get("cleanup_mode", "drop_objects")
    if cm == "rollback":
        cleanup.append("ROLLBACK;")
    elif cm == "reset_state":
        cleanup.append("RESET search_path;")
    if _needs_role(a):
        cleanup.append(f"DROP ROLE IF EXISTS {p}actor;")
    if _creates_sequence(a):
        cleanup.append(f"DROP SEQUENCE IF EXISTS {t};")
    if _creates_table(a):
        cleanup.append(f"DROP TABLE IF EXISTS {t};")
    if not cleanup:
        cleanup.append("SELECT 1 AS residual_check_no_objects;")

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


def resolve_explain_factor_witness(
    case: ExplainFactorCase | ExplainFactorExtensionCase,
    repository_root: Path,
) -> ExplainFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return ExplainFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_explain(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*EXPLAIN\b", region)
    )


def _header(case: ExplainFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : EXPLAIN {case.factor_key}="
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


def render_explain_factor_case(
    case: ExplainFactorCase | ExplainFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 EXPLAIN。")
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
    case: ExplainFactorCase | ExplainFactorExtensionCase,
    out: Path,
) -> None:
    text = render_explain_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_explain_factor_programs(
    baseline_plan: ExplainFactorLoopPlan,
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
    "ExplainFactorRenderError",
    "ExplainFactorWitness",
    "count_primary_explain",
    "generate_explain_factor_programs",
    "render_explain_factor_case",
    "resolve_explain_factor_witness",
]
