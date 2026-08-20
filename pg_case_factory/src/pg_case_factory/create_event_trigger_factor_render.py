"""Render complete PostgreSQL 18.4 CREATE EVENT TRIGGER factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CREATE EVENT TRIGGER is an event-DDL statement: the target is a
``pg_catalog.pg_event_trigger`` catalog row backed by a handler
``pg_proc`` function, not a ``pg_class`` relation.  All catalog oracles
schema-qualify ``pg_catalog.pg_event_trigger`` (exempt from the
file-prefix style gate).  No case creates a TABLE, so the bookend
(DROP TABLE IF EXISTS) is never emitted (``_tables_to_drop`` always
returns ``[]``); the table-less scripts use ``SELECT 1 AS
residual_check_no_objects;`` when no fixture objects remain.  Every
catalog SELECT carries a top-level ``ORDER BY`` so the
catalog-observability gate passes.  CREATE EVENT TRIGGER does NOT
support ``OR REPLACE``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_event_trigger_factor_extension import (
    CreateEventTriggerFactorExtensionCase,
    _present_failure_pair,
)
from .create_event_trigger_factor_loop import (
    CreateEventTriggerFactorCase,
    CreateEventTriggerFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/event_trigger/"
    "create_event_trigger.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/event_trigger/"
    "create_event_trigger.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class CreateEventTriggerFactorRenderError(ValueError):
    """Raised when a CREATE EVENT TRIGGER case cannot be rendered."""


@dataclass(frozen=True)
class CreateEventTriggerFactorWitness:
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
    ext: CreateEventTriggerFactorExtensionCase,
) -> CreateEventTriggerFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get(
            "target_action", "create_event_trigger"
        )
    return CreateEventTriggerFactorCase(
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
    case: CreateEventTriggerFactorCase
    | CreateEventTriggerFactorExtensionCase,
) -> CreateEventTriggerFactorCase:
    if isinstance(case, CreateEventTriggerFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateEventTriggerFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _trigger_name(a: dict[str, str], p: str) -> str:
    """Trigger name; quoted/reserved forms live in the target only."""

    shape = a.get("trigger_name_shape", "simple_id")
    if shape == "quoted_id":
        return f'"{p}trig"'
    if shape == "reserved_word_as_name":
        return '"user"'
    return f"{p}trig"


def _trigger_name_plain(name: str) -> str:
    """Unquoted form for string-literal catalog probes."""

    return name.strip('"')


def _function_name(a: dict[str, str], p: str) -> str:
    """Handler function name; quoted/dotted forms in target + fixtures."""

    shape = a.get("function_name_shape", "simple_id")
    if shape == "schema_qualified":
        return f"public.{p}evtfn"
    if shape == "nonexistent_name":
        return f"{p}nonexistfn"
    return f"{p}evtfn"


def _function_created(a: dict[str, str]) -> bool:
    """Whether the case CREATEs the handler function fixture."""

    tfs = a.get(
        "trigger_function_state",
        "function_exists_valid_signature",
    )
    return tfs != "function_not_exists"


def _function_return(a: dict[str, str]) -> str:
    tfs = a.get(
        "trigger_function_state",
        "function_exists_valid_signature",
    )
    if tfs == "function_exists_wrong_return_type":
        return "text"
    return "event_trigger"


def _function_params(a: dict[str, str]) -> str:
    tfs = a.get(
        "trigger_function_state",
        "function_exists_valid_signature",
    )
    if tfs == "function_exists_with_parameters":
        return "arg integer"
    return ""


def _event_clause(a: dict[str, str]) -> str:
    if a.get("invalid_event_type") == "invalid_event_type":
        return "ddl_command_invalid"
    return a.get("event_type", "ddl_command_start")


def _filter_tags(a: dict[str, str]) -> str:
    fvs = a.get("filter_value_shape", "single_command_tag")
    if fvs == "representative_tags_alter_table":
        return "'ALTER TABLE'"
    if fvs == "representative_tags_create_table":
        return "'CREATE TABLE'"
    if fvs == "multiple_command_tags":
        return "'DROP FUNCTION', 'ALTER TABLE'"
    return "'DROP FUNCTION'"


def _when_clause(a: dict[str, str]) -> str:
    wfc = a.get("when_filter_clause", "omitted")
    if wfc == "omitted":
        return ""
    var = "TAG"
    if a.get("invalid_filter_variable") == "unsupported_variable":
        var = "FOO"
    tags = _filter_tags(a)
    if wfc == "single_tag_in_condition":
        return f"WHEN {var} IN ({tags})"
    if wfc == "multiple_tag_in_values":
        if "," not in tags:
            tags = f"{tags}, 'CREATE TABLE'"
        return f"WHEN {var} IN ({tags})"
    if wfc == "and_connected_multiple_conditions":
        first = tags.split(",")[0].strip()
        return (
            f"WHEN {var} IN ({first}) "
            f"AND {var} IN ('CREATE TABLE')"
        )
    return ""


def _needs_role(a: dict[str, str]) -> bool:
    return a.get("privilege_level", "superuser") == "non_superuser"


def _pre_create_trigger(a: dict[str, str]) -> bool:
    return (
        a.get("object_state", "not_exists") == "exists"
        or a.get("duplicate_trigger_name", "no_conflict")
        == "same_name_conflict"
    )


def _probe_select(
    case: CreateEventTriggerFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only error_assertion."""

    mode = a.get(
        "verification_mode", "catalog_query_pg_event_trigger"
    )
    if mode == "error_assertion":
        return None

    name = _trigger_name(a, p)
    plain = _trigger_name_plain(name)
    if mode == "trigger_firing_test":
        return (
            "SELECT evtenabled FROM pg_catalog.pg_event_trigger "
            f"WHERE evtname = '{plain}' "
            "ORDER BY evtenabled;"
        )
    present = (
        case.outcome == "success"
        or a.get("object_state", "not_exists") == "exists"
        or a.get("duplicate_trigger_name", "no_conflict")
        == "same_name_conflict"
    )
    cmp_op = ">" if present else "="
    return (
        f"SELECT count(*) {cmp_op} 0 AS trigger_state "
        "FROM pg_catalog.pg_event_trigger "
        f"WHERE evtname = '{plain}' "
        "ORDER BY count(*);"
    )


def _tables_to_drop(
    case: CreateEventTriggerFactorCase,
) -> list[str]:
    """Fixture tables the case CREATEs.

    CREATE EVENT TRIGGER is an event-DDL statement: it never creates a
    TABLE.  The bookend (DROP TABLE IF EXISTS) is therefore never
    emitted.
    """
    return []


def _resolve_case(
    case: CreateEventTriggerFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix

    setup: list[str] = []
    locus = "target.create_event_trigger"

    fn = _function_name(a, p)
    tfs = a.get(
        "trigger_function_state",
        "function_exists_valid_signature",
    )

    # --- handler function fixture ------------------------------------
    if _function_created(a):
        ret = _function_return(a)
        params = _function_params(a)
        setup.append(
            f"CREATE FUNCTION {fn}({params}) RETURNS {ret} "
            "LANGUAGE plpgsql AS $$ BEGIN END; $$;"
        )
        locus = "fixture.handler_function"

    # --- pre-create the trigger (object_state=exists / duplicate) ----
    if _pre_create_trigger(a):
        name = _trigger_name(a, p)
        event = _event_clause(a)
        kw = a.get("execute_keyword", "FUNCTION")
        setup.append(
            f"CREATE EVENT TRIGGER {name} ON {event} "
            f"EXECUTE {kw} {fn}();"
        )
        locus = "fixture.pre_existing_trigger"

    # --- non-superuser role for privilege-failure cases ---------------
    if _needs_role(a):
        setup.append(
            f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;"
        )
        setup.append(f"SET ROLE {p}actor;")
        locus = "fixture.privilege_state"

    # --- the primary target statement --------------------------------
    name = _trigger_name(a, p)
    event = _event_clause(a)
    when = _when_clause(a)
    kw = a.get("execute_keyword", "FUNCTION")
    parts = [
        f"CREATE EVENT TRIGGER {name}",
        f"ON {event}",
    ]
    if when:
        parts.append(when)
    parts.append(f"EXECUTE {kw} {fn}()")
    target = " ".join(parts) + ";"

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
    name = _trigger_name(a, p)
    cm = a.get("cleanup_mode", "drop_event_trigger")
    cascade = " CASCADE" if cm == "cascade_cleanup" else ""
    trigger_drops = [f"DROP EVENT TRIGGER IF EXISTS {name}{cascade};"]
    func_drops: list[str] = []
    if _function_created(a):
        func_drops.append(f"DROP FUNCTION IF EXISTS {fn};")
    role_drops: list[str] = []
    if _needs_role(a):
        role_drops.extend(
            [
                f"DROP OWNED BY {p}actor CASCADE;",
                f"DROP ROLE IF EXISTS {p}actor;",
            ]
        )

    # pre-cleanup: trigger, function, role (all IF EXISTS)
    pre_cleanup: list[str] = []
    pre_cleanup.extend(trigger_drops)
    pre_cleanup.extend(func_drops)
    pre_cleanup.extend(role_drops)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # cleanup: RESET ROLE, trigger, function, role
    cleanup: list[str] = []
    if _needs_role(a):
        cleanup.append("RESET ROLE;")
    cleanup.extend(trigger_drops)
    cleanup.extend(func_drops)
    cleanup.extend(role_drops)
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


def resolve_create_event_trigger_factor_witness(
    case: CreateEventTriggerFactorCase
    | CreateEventTriggerFactorExtensionCase,
    repository_root: Path,
) -> CreateEventTriggerFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateEventTriggerFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_create_event_trigger(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(
            r"(?im)^CREATE\s+EVENT\s+TRIGGER\b", region
        )
    )


def _header(case: CreateEventTriggerFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE EVENT TRIGGER "
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


def render_create_event_trigger_factor_case(
    case: CreateEventTriggerFactorCase
    | CreateEventTriggerFactorExtensionCase,
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
    lines.append(
        "-- 3. 执行唯一获得覆盖信用的 CREATE EVENT TRIGGER。"
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
    case: CreateEventTriggerFactorCase
    | CreateEventTriggerFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_event_trigger_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_event_trigger_factor_programs(
    baseline_plan: CreateEventTriggerFactorLoopPlan,
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
    "CreateEventTriggerFactorRenderError",
    "CreateEventTriggerFactorWitness",
    "count_primary_create_event_trigger",
    "generate_create_event_trigger_factor_programs",
    "render_create_event_trigger_factor_case",
    "resolve_create_event_trigger_factor_witness",
]
