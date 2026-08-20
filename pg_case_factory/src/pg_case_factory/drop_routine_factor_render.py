"""Render complete PostgreSQL 18.4 DROP ROUTINE factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.
The file is assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (re-render + compare) can never diverge from
the bytes actually written.

Oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_proc WHERE proname = ...
ORDER BY count(*) LIMIT 1`` never nests a ``FROM`` inside an ``EXISTS``
subquery.  ``proname`` is the real PG18 ``pg_proc`` name column; for a
generic DROP ROUTINE a ``proname`` match (any ``prokind``) is correct.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .drop_routine_factor_extension import (
    DropRoutineFactorExtensionCase,
)
from .drop_routine_factor_loop import (
    DropRoutineFactorCase,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/routine/drop_routine.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/routine/"
    "drop_routine.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_NEUTRAL_SUCCESS = ("routine_existence", "routine_exists")

_ABSENT_BASELINE: frozenset[tuple[str, str]] = frozenset(
    {
        ("expected_status", "failure"),
        ("nonexistent_routine", "routine_does_not_exist"),
        ("routine_existence", "routine_not_exists"),
        ("routine_name_shape", "non_existing_name"),
    }
)

_DEPENDENT_BASELINE: frozenset[tuple[str, str]] = frozenset(
    {
        ("dependent_objects", "has_dependent_trigger"),
        ("dependent_objects", "has_dependent_view"),
        ("dependent_objects", "has_dependent_routine"),
        ("dependent_object_conflict", "restrict_with_dependent_fails"),
        ("dependent_object_conflict", "cascade_with_dependent_succeeds"),
    }
)

_OVERLOAD_BASELINE: frozenset[tuple[str, str]] = frozenset(
    {
        ("arg_signature_disambiguation", "overloaded_requires_signature"),
        ("arg_signature_disambiguation", "single_arg_with_signature"),
        ("arg_signature_disambiguation", "signature_mismatch"),
        ("overloaded_routine_ambiguity", "ambiguous_without_signature"),
        ("overloaded_routine_ambiguity", "resolved_with_signature"),
        ("wrong_argument_types", "signature_does_not_match_any_routine"),
    }
)

_MULTI_BASELINE: frozenset[tuple[str, str]] = frozenset(
    {
        ("multi_target", "multi_target_all_exist"),
        ("multi_target", "multi_target_some_not_exist"),
    }
)

_ARGSHAPE_SPEC: dict[str, str] = {
    "no_args": "",
    "single_arg": "(integer)",
    "multiple_args": "(integer, text)",
    "with_argmode": "(IN integer)",
    "with_argname": "(a integer)",
    "empty_arg_list": "()",
}

_OVERLOAD_ARG_SPEC: dict[str, str] = {
    "no_args_no_ambiguity": "",
    "single_arg_with_signature": "(integer)",
    "overloaded_requires_signature": "(integer)",
    "signature_mismatch": "(integer)",
    "ambiguous_without_signature": "",
    "resolved_with_signature": "(integer)",
    "signature_does_not_match_any_routine": "(integer)",
}


def _synthetic_case(
    ext: DropRoutineFactorExtensionCase,
) -> DropRoutineFactorCase:
    from .drop_routine_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropRoutineFactorCase(
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
    case: DropRoutineFactorCase | DropRoutineFactorExtensionCase,
) -> DropRoutineFactorCase:
    if isinstance(case, DropRoutineFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropRoutineFactorRenderError(ValueError):
    """Raised when a DROP ROUTINE case cannot be rendered."""


@dataclass(frozen=True)
class DropRoutineFactorWitness:
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


def _baseline(case: DropRoutineFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _ref(a: dict[str, str], p: str) -> str:
    shape = a.get("routine_name_shape", "simple_name")
    if shape == "quoted_name":
        return f'"{p}QuotedR"'
    if shape == "schema_qualified_name":
        return f"public.{p}r"
    if shape == "non_existing_name":
        return f"{p}nonexistent_r"
    return f"{p}r"


def _probe_name(a: dict[str, str], p: str) -> str:
    shape = a.get("routine_name_shape", "simple_name")
    if shape == "quoted_name":
        return f"{p}QuotedR"
    if shape == "non_existing_name":
        return f"{p}nonexistent_r"
    return f"{p}r"


def _routine_kind(a: dict[str, str]) -> str:
    return a.get("routine_type", "function")


def _is_overload_primary(case: DropRoutineFactorCase) -> bool:
    return (case.factor_key, case.factor_value) in _OVERLOAD_BASELINE


def _arg_spec(case: DropRoutineFactorCase, a: dict[str, str]) -> str:
    if case.kind == "EXT":
        return ""
    primary = (case.factor_key, case.factor_value)
    if primary in _OVERLOAD_BASELINE:
        return _OVERLOAD_ARG_SPEC[case.factor_value]
    if case.factor_key == "arg_signature_shape":
        return _ARGSHAPE_SPEC.get(case.factor_value, "")
    if _routine_kind(a) == "aggregate":
        return "(integer)"
    return _ARGSHAPE_SPEC.get(a.get("arg_signature_shape", "no_args"), "")


def _create_arg_spec(case: DropRoutineFactorCase, a: dict[str, str]) -> str:
    """Arg list for the fixture CREATE; aggregate always needs an arg."""

    if _routine_kind(a) == "aggregate":
        return "(integer)"
    return _arg_spec(case, a)


def _create_routine_stmt(
    kind: str, ref: str, argspec: str, trigger: bool = False
) -> str:
    if trigger:
        return (
            f"CREATE FUNCTION {ref}() RETURNS trigger "
            "AS $$ BEGIN RETURN NULL; END; $$ LANGUAGE plpgsql;"
        )
    if kind == "procedure":
        return (
            f"CREATE PROCEDURE {ref}{argspec} "
            "AS $$ BEGIN NULL; END; $$ LANGUAGE plpgsql;"
        )
    if kind == "aggregate":
        return (
            f"CREATE AGGREGATE {ref}(integer) "
            "(SFUNC = sum, STYPE = integer, INITCOND = '0');"
        )
    return (
        f"CREATE FUNCTION {ref}{argspec} RETURNS integer "
        "AS $$ BEGIN RETURN 1; END; $$ LANGUAGE plpgsql;"
    )


def _fixture_kind(
    case: DropRoutineFactorCase, a: dict[str, str]
) -> str:
    if case.kind == "RISK":
        return "routine"
    if a.get("routine_existence") == "routine_not_exists":
        return "none"
    if a.get("routine_name_shape") == "non_existing_name":
        return "none"
    if case.kind == "EXT":
        if a.get("dependent_objects") == "has_dependent_routine":
            return "dep_routine"
        return "routine"
    primary = (case.factor_key, case.factor_value)
    if primary in _ABSENT_BASELINE:
        return "none"
    if primary == ("dependent_objects", "has_dependent_trigger"):
        return "trigger"
    if primary == ("dependent_objects", "has_dependent_view"):
        return "view"
    if primary in _DEPENDENT_BASELINE:
        return "dep_routine"
    if primary in _OVERLOAD_BASELINE:
        return "overload"
    if primary in _MULTI_BASELINE:
        return "multi"
    return "routine"


def _needs_table(case: DropRoutineFactorCase, a: dict[str, str]) -> bool:
    return _fixture_kind(case, a) == "trigger"


def _if_exists_present(a: dict[str, str]) -> bool:
    return a.get("if_exists_clause") == "with_if_exists"


def _cascade_clause(a: dict[str, str]) -> str:
    c = a.get("cascade_restrict_clause", "no_clause_default_restrict")
    if c == "cascade":
        return "CASCADE"
    if c == "restrict":
        return "RESTRICT"
    return ""


def _privilege_mode(
    case: DropRoutineFactorCase, a: dict[str, str]
) -> str:
    if case.kind == "EXT":
        pc = a.get("privilege_context", "superuser")
        if pc == "non_owner_no_privilege":
            return "non_owner"
        if pc == "owner_of_routine":
            return "owner"
        return "none"
    if case.kind == "RISK":
        return "none"
    fk, fv = case.factor_key, case.factor_value
    if (fk, fv) in {
        ("privilege_insufficient", "non_owner_dropping_routine"),
        ("privilege_context", "non_owner_no_privilege"),
        ("executor_privilege", "non_owner_no_privilege"),
    }:
        return "non_owner"
    if (fk, fv) in {
        ("privilege_context", "owner_of_routine"),
        ("executor_privilege", "owner"),
    }:
        return "owner"
    return "none"


def _dependent_create_stmts(
    kind: str, ref: str, p: str
) -> list[str]:
    if kind == "procedure":
        return [
            f"CREATE FUNCTION {p}dep() RETURNS integer "
            f"AS $$ BEGIN CALL {ref}(); RETURN 1; END; $$ LANGUAGE plpgsql;"
        ]
    if kind == "aggregate":
        return [
            f"CREATE FUNCTION {p}dep() RETURNS integer "
            f"AS $$ BEGIN RETURN (SELECT {ref}(c) FROM "
            f"(SELECT 1 AS c) s); END; $$ LANGUAGE plpgsql;"
        ]
    return [
        f"CREATE FUNCTION {p}dep() RETURNS integer "
        f"AS $$ BEGIN RETURN {ref}(); END; $$ LANGUAGE plpgsql;"
    ]


def _fixture_stmts(
    case: DropRoutineFactorCase, a: dict[str, str], p: str
) -> list[str]:
    kind = _fixture_kind(case, a)
    ref = _ref(a, p)
    rkind = _routine_kind(a)
    stmts: list[str] = []
    if kind == "none":
        stmts.append("SELECT 1 AS target_routine_intentionally_absent;")
        return stmts
    if kind == "trigger":
        stmts.append(_create_routine_stmt("function", ref, "", trigger=True))
        stmts.append(f"CREATE TABLE {p}t (c integer);")
        stmts.append(
            f"CREATE TRIGGER {p}trig BEFORE INSERT ON {p}t "
            f"FOR EACH ROW EXECUTE FUNCTION {ref}();"
        )
        return stmts
    if kind == "overload":
        fv = case.factor_value
        if fv in {
            "overloaded_requires_signature",
            "resolved_with_signature",
            "ambiguous_without_signature",
        }:
            stmts.append(_create_routine_stmt("function", ref, ""))
            stmts.append(_create_routine_stmt("function", ref, "(integer)"))
        elif fv == "single_arg_with_signature":
            stmts.append(_create_routine_stmt("function", ref, "(integer)"))
        else:
            stmts.append(_create_routine_stmt("function", ref, ""))
        return stmts
    if kind == "multi":
        if case.factor_value == "multi_target_all_exist":
            stmts.append(_create_routine_stmt(rkind, ref, _create_arg_spec(case, a)))
            stmts.append(_create_routine_stmt(rkind, f"{p}r2", _create_arg_spec(case, a)))
        else:
            stmts.append(_create_routine_stmt(rkind, ref, _create_arg_spec(case, a)))
        return stmts
    if kind == "dep_routine":
        stmts.append(_create_routine_stmt(rkind, ref, _create_arg_spec(case, a)))
        stmts.extend(_dependent_create_stmts(rkind, ref, p))
        return stmts
    if kind == "view":
        stmts.append(_create_routine_stmt(rkind, ref, _create_arg_spec(case, a)))
        if rkind == "aggregate":
            stmts.append(
                f"CREATE VIEW {p}v AS SELECT {ref}(c) FROM (SELECT 1 AS c) s;"
            )
        else:
            stmts.append(f"CREATE VIEW {p}v AS SELECT {ref}();")
        return stmts
    stmts.append(_create_routine_stmt(rkind, ref, _create_arg_spec(case, a)))
    return stmts


def _drop_target(
    case: DropRoutineFactorCase, a: dict[str, str], p: str
) -> str:
    ref = _ref(a, p)
    ifexists = "IF EXISTS " if _if_exists_present(a) else ""
    cascade = _cascade_clause(a)
    argspec = _arg_spec(case, a)
    mt = a.get("multi_target", "single_target")
    if mt == "multi_target_all_exist":
        target = f"DROP ROUTINE {ifexists}{ref}{argspec}, {p}r2{argspec}"
    elif mt == "multi_target_some_not_exist":
        target = f"DROP ROUTINE {ifexists}{ref}{argspec}, {p}nonexistent{argspec}"
    else:
        target = f"DROP ROUTINE {ifexists}{ref}{argspec}"
    if cascade:
        target += f" {cascade}"
    return target + ";"


def _routine_absent_after(
    case: DropRoutineFactorCase, a: dict[str, str]
) -> bool:
    if case.kind == "RISK":
        return case.factor_value == "commit"
    if _fixture_kind(case, a) == "none":
        return True
    return case.outcome == "success"


def _probe_select(
    case: DropRoutineFactorCase, a: dict[str, str], p: str
) -> str:
    name = _probe_name(a, p)
    absent = _routine_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "routine_absent" if absent else "routine_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_proc "
        f"WHERE proname = '{name}' ORDER BY count(*) LIMIT 1;"
    )


def _role_names(p: str, mode: str) -> tuple[str, ...]:
    return (f"{p}actor",) if mode in ("owner", "non_owner") else ()


def _resolve_case(case: DropRoutineFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    fkind = _fixture_kind(case, a)
    ref = _ref(a, p)
    rkind = _routine_kind(a)
    needs_table = _needs_table(case, a)
    mode = _privilege_mode(case, a)

    setup: list[str] = []
    locus = "target.routine"

    if needs_table:
        setup.append("SELECT 1 AS setup_boundary;")
    if mode in ("owner", "non_owner"):
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"
    if mode == "owner":
        setup.append(f"SET ROLE {p}actor;")
    setup.extend(_fixture_stmts(case, a, p))
    if fkind not in ("none",) and fkind != "none":
        locus = "fixture.object_state"
    if mode == "non_owner":
        setup.append(f"SET ROLE {p}actor;")
    if case.kind == "RISK":
        setup.append("BEGIN;")
        locus = "target.transaction_boundary"

    target = _drop_target(case, a, p)

    assert_lines: list[str] = []
    if mode in ("owner", "non_owner"):
        assert_lines.append("RESET ROLE;")
    if case.kind == "RISK":
        assert_lines.append(
            "COMMIT;" if case.factor_value == "commit" else "ROLLBACK;"
        )
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    assert_lines.append(_probe_select(case, a, p))

    routine_drop = f"DROP ROUTINE IF EXISTS {ref} CASCADE;"
    dep_routine_drop = f"DROP FUNCTION IF EXISTS {p}dep CASCADE;"
    dep_view_drop = f"DROP VIEW IF EXISTS {p}v;"
    dep_trigger_drop = f"DROP TRIGGER IF EXISTS {p}trig ON {p}t;"
    table_drop = f"DROP TABLE IF EXISTS {p}t CASCADE;"
    roles = _role_names(p, mode)
    role_drops = [
        stmt
        for role in roles
        for stmt in (f"DROP OWNED BY {role};", f"DROP ROLE IF EXISTS {role};")
    ]

    needs_dep_routine = fkind == "dep_routine"
    needs_view = fkind == "view"
    needs_trigger = fkind == "trigger"

    dep_drops: list[str] = []
    if needs_table:
        dep_drops.append(table_drop)

    pre_cleanup: list[str] = []
    pre_cleanup.extend(dep_drops)
    if needs_trigger:
        pre_cleanup.append(dep_trigger_drop)
    if needs_view:
        pre_cleanup.append(dep_view_drop)
    if needs_dep_routine:
        pre_cleanup.append(dep_routine_drop)
    pre_cleanup.append(routine_drop)
    pre_cleanup.extend(role_drops)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    cleanup: list[str] = []
    if mode in ("owner", "non_owner"):
        cleanup.append("RESET ROLE;")
    if needs_trigger:
        cleanup.append(dep_trigger_drop)
    if needs_view:
        cleanup.append(dep_view_drop)
    if needs_dep_routine:
        cleanup.append(dep_routine_drop)
    cleanup.append(routine_drop)
    cleanup.extend(role_drops)
    cleanup.extend(dep_drops)
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


def resolve_drop_routine_factor_witness(
    case: DropRoutineFactorCase | DropRoutineFactorExtensionCase,
    repository_root: Path,
) -> DropRoutineFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropRoutineFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_routine(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(re.findall(r"(?im)^DROP\s+ROUTINE\b", region))


def _header(case: DropRoutineFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP ROUTINE {case.factor_key}={case.factor_value}",
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


def render_drop_routine_factor_case(
    case: DropRoutineFactorCase | DropRoutineFactorExtensionCase,
    repository_root: Path,
) -> str:
    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地 routine 和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP ROUTINE。")
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
    if not text.endswith(";"):
        text += ";"
    return text + "\n"


def generate_drop_routine_factor_programs(
    baseline_plan: object,
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


def _write_program(
    case: DropRoutineFactorCase | DropRoutineFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_routine_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropRoutineFactorRenderError",
    "DropRoutineFactorWitness",
    "count_primary_drop_routine",
    "generate_drop_routine_factor_programs",
    "render_drop_routine_factor_case",
    "resolve_drop_routine_factor_witness",
]
