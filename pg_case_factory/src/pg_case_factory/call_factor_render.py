"""Render complete PostgreSQL 18.4 CALL factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CALL is a DML routine-invocation statement: the target is a PROCEDURE
object in ``pg_catalog.pg_proc``, not a ``pg_class`` relation.  All
catalog oracles schema-qualify ``pg_catalog.pg_proc`` (exempt from the
file-prefix style gate).  Success cases CREATE a fixture TABLE
(``{p}tbl``) for the called procedure to observe/mutate, so the bookend
gate (DROP TABLE IF EXISTS first + last ``;``-stmt) applies.  Failure
cases that do not create a table (e.g. ``target_relation_state=missing``)
have the bookend gate N/A.  Every catalog SELECT carries a top-level
``ORDER BY count(*)`` so the catalog-observability gate passes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .cleanup_bookend import DropSpec, build_cleanup, build_pre_cleanup
from .call_factor_extension import (
    CallFactorExtensionCase,
    _present_failure_pair,
)
from .call_factor_loop import (
    CallFactorCase,
    CallFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/dml/routine/"
    "call.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/dml/routine/"
    "call.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class CallFactorRenderError(ValueError):
    """Raised when a CALL case cannot be rendered."""


@dataclass(frozen=True)
class CallFactorWitness:
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
    ext: CallFactorExtensionCase,
) -> CallFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get("target_action", "call")
    return CallFactorCase(
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
    case: CallFactorCase | CallFactorExtensionCase,
) -> CallFactorCase:
    if isinstance(case, CallFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: CallFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _target_missing(a: dict[str, str]) -> bool:
    return a.get("target_relation_state") == "missing"


def _target_wrong(a: dict[str, str]) -> bool:
    return a.get("target_relation_state") == "wrong_object_type"


def _procedure_name(a: dict[str, str], p: str) -> str:
    """The procedure identifier in CALL and fixture statements."""

    shape = a.get("name_shape", "plain_identifier")
    if shape == "schema_qualified":
        return f"public.{p}proc"
    if shape == "quoted_identifier":
        return f'"{p}Proc"'
    # plain_identifier and alias_used both use a plain name.
    return f"{p}proc"


def _procedure_name_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    shape = a.get("name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f"{p}Proc"
    return f"{p}proc"


def _table_name(p: str) -> str:
    """The fixture table name (always plain, prefix-compliant)."""
    return f"{p}tbl"


def _argument_sql(a: dict[str, str], p: str) -> str:
    """The argument expression list inside CALL name( ... )."""

    doqs = a.get("data_or_query_shape", "explicit_values")
    es = a.get("expression_shape", "literal")
    tbl = _table_name(p)

    if doqs == "minimal":
        return ""

    if doqs == "cte_source":
        return f"(SELECT val FROM {p}cte)"

    if doqs == "query_source":
        return f"(SELECT val FROM {tbl} LIMIT 1)"

    # explicit_values: argument shape governed by expression_shape.
    if es == "literal":
        return "42"
    if es == "column_reference":
        return f"(SELECT val FROM {tbl} LIMIT 1)"
    if es == "function_call":
        return "abs(1)"
    if es == "subquery_expression":
        return "(SELECT 1)"
    return "42"


def _with_prefix(a: dict[str, str], p: str) -> str:
    """The WITH clause prefix for the CALL statement."""

    doqs = a.get("data_or_query_shape", "explicit_values")
    wc = a.get("with_clause", "absent")

    if doqs == "cte_source" or wc != "absent":
        if wc == "recursive":
            return (
                f"WITH RECURSIVE {p}cte AS ("
                f"SELECT 42 AS val "
                f"UNION ALL "
                f"SELECT val + 1 FROM {p}cte WHERE val < 50)\n"
            )
        return f"WITH {p}cte AS (SELECT 42 AS val)\n"
    return ""


def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target CALL runs."""

    pc = a.get("privilege_context", "owner")
    if pc == "insufficient_privilege":
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    pc = a.get("privilege_context", "owner")
    if pc == "insufficient_privilege":
        roles.append(f"{p}actor")
    return tuple(roles)


def _probe_select(
    case: CallFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog/effect oracle, or None for sqlstate-only error_assertion."""

    mode = a.get("verification_mode", "effect_query")
    if mode == "error_assertion":
        return None

    proc_lit = _procedure_name_literal(a, p)
    tbl = _table_name(p)
    missing = _target_missing(a)
    wrong = _target_wrong(a)

    if mode == "catalog_query":
        cmp_op = "=" if (missing or wrong) else ">"
        return (
            f"SELECT count(*) {cmp_op} 0 AS procedure_state "
            f"FROM pg_catalog.pg_proc "
            f"WHERE proname = '{proc_lit}' "
            f"ORDER BY count(*);"
        )

    # effect_query and returned_rows both probe the fixture table.
    cmp_op = "=" if (missing or wrong) else ">"
    label = "returned_rows_state" if mode == "returned_rows" else "effect_state"
    return (
        f"SELECT count(*) {cmp_op} 0 AS {label} "
        f"FROM {tbl} "
        f"ORDER BY count(*);"
    )


def _tables_to_drop(
    case: CallFactorCase,
) -> list[str]:
    """Fixture tables the case CREATEs.

    CALL success and most failure cases CREATE a fixture TABLE for the
    called procedure to observe/mutate, so the bookend (DROP TABLE IF
    EXISTS first + last) applies.  Cases where target_relation_state=
    missing still create the table for pre-cleanup bookend consistency.
    """
    a = _baseline(case)
    p = case.object_prefix
    return [_table_name(p)]


def _resolve_case(
    case: CallFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    missing = _target_missing(a)
    wrong = _target_wrong(a)
    tbl = _table_name(p)

    setup: list[str] = []
    locus = "target.call"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    proc = _procedure_name(a, p)

    # --- role fixtures -----------------------------------------------
    if effective == f"{p}actor":
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- the fixture table -------------------------------------------
    cb = a.get("constraint_boundary", "none")
    if cb == "constraint_violation":
        setup.append(
            f"CREATE TABLE {tbl} (val int UNIQUE);"
        )
        setup.append(f"INSERT INTO {tbl} (val) VALUES (42);")
        locus = "fixture.constraint_boundary"
    else:
        setup.append(f"CREATE TABLE {tbl} (val int);")
        locus = "fixture.table"

    # --- the target procedure / function fixture ---------------------
    if missing:
        setup.append(
            "SELECT 1 AS target_procedure_intentionally_absent;"
        )
        locus = "fixture.procedure_missing"
    elif wrong:
        setup.append(
            f"CREATE FUNCTION {proc}(int) RETURNS int "
            f"AS $$ SELECT $1 $$ LANGUAGE sql;"
        )
        locus = "fixture.wrong_object_type"
    else:
        ds = a.get("dependency_state", "ready")
        if ds == "missing_dependency":
            setup.append(
                f"CREATE PROCEDURE {proc}"
                f"(arg1 int DEFAULT 0) "
                f"LANGUAGE plpgsql AS $$ "
                f"BEGIN "
                f"INSERT INTO {p}no_such_tbl (val) VALUES (arg1); "
                f"END; $$;"
            )
            locus = "fixture.missing_dependency"
        else:
            setup.append(
                f"CREATE PROCEDURE {proc}"
                f"(arg1 int DEFAULT 0) "
                f"LANGUAGE plpgsql AS $$ "
                f"BEGIN "
                f"INSERT INTO {tbl} (val) VALUES (arg1); "
                f"END; $$;"
            )
            locus = "fixture.procedure"

    # --- arm the effective role --------------------------------------
    if effective:
        setup.append(f"SET ROLE {effective};")

    # --- the primary target statement --------------------------------
    target = _build_target(a, p, proc)

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

    # --- cleanup construction (shared idempotent bookends) -----------
    # Migrated to cleanup_bookend so every DROP carries IF EXISTS and
    # DROP OWNED BY is unreachable in pre-cleanup: the role fixture is
    # created by setup, so on a fresh database the role does not exist
    # yet at pre-cleanup time and DROP OWNED BY would crash
    # (ON_ERROR_STOP=1) before the target statement reaches execution.
    # Pre-cleanup drops roles via DROP ROLE IF EXISTS only; the post-target
    # cleanup runs DROP OWNED BY then DROP ROLE IF EXISTS once setup has
    # created the role.  The DROP TABLE IF EXISTS anchor is first in
    # pre-cleanup and last in cleanup, satisfying the table-bookend gate.
    specs: list[DropSpec] = []
    if not missing and not wrong:
        specs.append(DropSpec("PROCEDURE", proc))
    elif wrong:
        specs.append(DropSpec("FUNCTION", proc))
    table_names = [tbl]
    role_list = list(roles)
    pre_bookend = build_pre_cleanup(
        tables=table_names,
        specs=tuple(specs),
        roles=role_list,
    )
    cln_bookend = build_cleanup(
        tables=table_names,
        specs=tuple(specs),
        roles=role_list,
        drop_owned=bool(role_list),
        reset_role=bool(effective),
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


def _build_target(
    a: dict[str, str], p: str, proc: str
) -> str:
    """The primary CALL statement."""

    with_prefix = _with_prefix(a, p)
    arg = _argument_sql(a, p)
    return f"{with_prefix}CALL {proc}({arg});"


def resolve_call_factor_witness(
    case: CallFactorCase | CallFactorExtensionCase,
    repository_root: Path,
) -> CallFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CallFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_call(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    # The WITH-clause prefix (cte_source / recursive factors) is newline-
    # terminated, so the primary CALL always starts at line start
    # (``CALL proc(...)``), matching the content-gate regex ``^CALL``.
    # Case-sensitive: the keyword is always uppercase in generated SQL;
    # lowercase ``call`` in prefixed procedure names has no trailing
    # word boundary (followed by ``_``) so it never matches.
    return len(re.findall(r"\bCALL\b", region))


def _header(case: CallFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CALL {case.factor_key}="
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


def render_call_factor_case(
    case: CallFactorCase | CallFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 CALL。")
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
    case: CallFactorCase | CallFactorExtensionCase,
    out: Path,
) -> None:
    text = render_call_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_call_factor_programs(
    baseline_plan: CallFactorLoopPlan,
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
    "CallFactorRenderError",
    "CallFactorWitness",
    "count_primary_call",
    "generate_call_factor_programs",
    "render_call_factor_case",
    "resolve_call_factor_witness",
]
