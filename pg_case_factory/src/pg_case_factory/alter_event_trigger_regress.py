"""PostgreSQL 18 ALTER EVENT TRIGGER conditional-product regress design."""

from __future__ import annotations

import itertools
from typing import Any, Mapping

from .remaining_statement_regress import (
    FactorValueDecision,
    RemainingStatementRegressError,
    StatementRegressCase,
    StatementRegressPlan,
    _header,
)
from .statement_factor_cycle import StatementCycleEntry, StatementFactorCycleSnapshot


_STATE_BRANCHES = ("disable", "enable", "enable_replica", "enable_always")
_BRANCHES = _STATE_BRANCHES + ("owner", "rename")
_CURRENT_STATES = ("enabled", "disabled", "enabled_replica", "enabled_always")
_SESSION_ROLES = ("origin", "replica", "local")
_NAME_SHAPES = ("simple_id", "quoted_id")
_VERIFY = ("catalog_query_pg_event_trigger", "catalog_query_evtenabled_field", "error_assertion")
_CLEANUP = ("drop_event_trigger", "drop_function", "cascade_cleanup")


def _spec(
    group: str,
    branch: str,
    *,
    outcome: str = "success",
    sqlstate: str = "00000",
    **axes: str,
) -> dict[str, Any]:
    return {
        "group": group,
        "outcome": outcome,
        "axes": {
            "branch": branch,
            "expected_sqlstate": sqlstate,
            "actor": "superuser",
            "trigger_name_shape": "simple_id",
            "current_state": "enabled",
            "session_role": "origin",
            "function_state": "function_exists",
            **axes,
        },
    }


def _build_specs() -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for branch, state, role, shape in itertools.product(
        _STATE_BRANCHES, _CURRENT_STATES, _SESSION_ROLES, _NAME_SHAPES
    ):
        specs.append(_spec(
            "state_transition_product", branch,
            current_state=state, session_role=role, trigger_name_shape=shape,
        ))
    for shape, (target, owner_shape, state) in itertools.product(
        _NAME_SHAPES,
        (
            ("existing_role", "simple_id", "exists"),
            ("existing_role", "quoted_id", "exists"),
            ("CURRENT_ROLE", "special_token", "exists"),
            ("CURRENT_USER", "special_token", "exists"),
            ("SESSION_USER", "special_token", "exists"),
            ("nonexistent_role", "simple_id", "missing"),
            ("nonexistent_role", "quoted_id", "missing"),
        ),
    ):
        missing = state == "missing"
        specs.append(_spec(
            "owner_target_product", "owner",
            outcome="expected_failure" if missing else "success",
            sqlstate="42704" if missing else "00000",
            trigger_name_shape=shape, owner_target=target,
            new_owner_shape=owner_shape, owner_state=state,
        ))
    for shape, new_shape, target_state in itertools.product(
        _NAME_SHAPES, ("simple_id", "quoted_id", "reserved_word_as_name"),
        ("unique", "conflict"),
    ):
        conflict = target_state == "conflict"
        specs.append(_spec(
            "rename_state_product", "rename",
            outcome="expected_failure" if conflict else "success",
            sqlstate="42710" if conflict else "00000",
            trigger_name_shape=shape, new_name_shape=new_shape,
            rename_state=target_state,
        ))
    for branch in _BRANCHES:
        specs.append(_spec(
            "missing_trigger_product", branch, outcome="expected_failure", sqlstate="42704",
            object_state="not_exists", trigger_name_shape="nonexistent_name",
            owner_target="CURRENT_USER", new_name_shape="simple_id",
        ))
    for branch, actor in itertools.product(_BRANCHES, ("superuser", "non_superuser")):
        denied = actor == "non_superuser"
        specs.append(_spec(
            "privilege_truth_product", branch,
            outcome="expected_failure" if denied else "success",
            sqlstate="42501" if denied else "00000", actor=actor,
            owner_target="CURRENT_USER", new_name_shape="simple_id",
        ))
    specs.append(_spec(
        "trigger_function_state_product", "disable",
        outcome="expected_failure", sqlstate="42704",
        object_state="not_exists", function_state="function_not_exists",
        trigger_name_shape="nonexistent_name",
    ))
    for branch in _BRANCHES:
        specs.append(_spec(
            "transactional_rollback_product", branch, transaction="rollback",
            owner_target="CURRENT_USER", new_name_shape="simple_id",
        ))
    for boundary, branch, sqlstate in (
        ("empty_name", "disable", "42601"),
        ("qualified_source", "disable", "42601"),
        ("three_part_source", "disable", "42601"),
        ("unknown_state", "enable", "42601"),
        ("duplicate_enable_modifier", "enable", "42601"),
        ("missing_owner", "owner", "42601"),
        ("qualified_owner", "owner", "42601"),
        ("owner_public", "owner", "42704"),
        ("owner_none", "owner", "42939"),
        ("missing_rename_target", "rename", "42601"),
        ("qualified_rename_target", "rename", "42601"),
        ("unquoted_reserved_target", "rename", "42601"),
    ):
        specs.append(_spec(
            "parser_boundary_product", branch, outcome="expected_failure", sqlstate=sqlstate,
            parser_boundary=boundary,
            new_name_shape="invalid_name" if "rename" in boundary or "reserved" in boundary else "simple_id",
            new_owner_shape="special_token" if branch == "owner" else "simple_id",
        ))
    return specs


def _tokens(axes: Mapping[str, str], outcome: str, ordinal: int) -> tuple[str, ...]:
    branch = axes["branch"]
    missing = axes.get("object_state") == "not_exists"
    actor = axes.get("actor", "superuser")
    values: dict[str, str] = {
        "statement_branch": f"branch_{branch}",
        "object_state": "not_exists" if missing else "exists",
        "expected_status": "failure" if outcome == "expected_failure" else "success",
        "privilege_level": actor,
        "trigger_current_state": axes.get("current_state", "enabled"),
        "trigger_name_shape": axes.get("trigger_name_shape", "simple_id"),
        "session_replication_role": axes.get("session_role", "origin"),
        "trigger_function_state": axes.get("function_state", "function_exists"),
        "trigger_not_exist": "trigger_not_exists" if missing else "trigger_exists",
        "privilege_denied_non_superuser": "non_superuser_failure" if actor == "non_superuser" else "superuser_success",
        "alter_nonexistent_trigger": "trigger_not_exists" if missing else "trigger_exists",
        "verification_mode": _VERIFY[(ordinal - 1) % 3],
        "cleanup_mode": _CLEANUP[(ordinal - 1) % 3],
    }
    if branch in {"enable", "enable_replica", "enable_always"}:
        values["enable_mode"] = {
            "enable": "ENABLE", "enable_replica": "ENABLE REPLICA", "enable_always": "ENABLE ALWAYS"
        }[branch]
    if branch == "owner":
        owner_state = axes.get("owner_state", "exists")
        values.update(
            new_owner_target=axes.get("owner_target", "CURRENT_USER"),
            new_owner_shape=axes.get("new_owner_shape", "special_token"),
            owner_not_exist="role_not_exists" if owner_state == "missing" else "role_exists",
        )
    if branch == "rename":
        conflict = axes.get("rename_state") == "conflict"
        values.update(
            rename_conflict="new_name_exists" if conflict else "new_name_unique",
            new_name_shape=axes.get("new_name_shape", "simple_id"),
            rename_target_conflict="name_already_exists" if conflict else "no_conflict",
        )
    return tuple(f"{key}={value}" for key, value in values.items())


def _build_cases() -> tuple[StatementRegressCase, ...]:
    cases: list[StatementRegressCase] = []
    for ordinal, spec in enumerate(_build_specs(), start=1):
        axes = dict(spec["axes"])
        case_id = f"ALTEREVENTTRIGGER{ordinal:05d}"
        cases.append(StatementRegressCase(
            ordinal=ordinal, case_id=case_id, sql_filename=f"{case_id}.sql",
            object_prefix=f"altereventtrigger_{ordinal:05d}_",
            case_group=str(spec["group"]),
            case_type="expected_failure" if spec["outcome"] == "expected_failure" else "success",
            outcome=str(spec["outcome"]), execution_profile="same_session_multiphase",
            derived_axes=axes, factor_values=_tokens(axes, str(spec["outcome"]), ordinal),
            combination_strategy="full branch-applicable conditional product; no table/type axes",
            description="ALTER EVENT TRIGGER conditional product: " + ", ".join(f"{k}={v}" for k, v in sorted(axes.items())),
            expected_anchor=f"SQLSTATE {axes['expected_sqlstate']}; pg_event_trigger state/owner/name and firing oracle",
        ))
    return tuple(cases)


def _factor_decisions(entry: StatementCycleEntry, cases: tuple[StatementRegressCase, ...]) -> tuple[FactorValueDecision, ...]:
    by_id = {case.case_id: case for case in cases}
    rows: list[FactorValueDecision] = []
    for factor in entry.factors:
        for value, row_id in zip(factor.values, factor.row_ids):
            token = f"{factor.name}={value}"
            witnesses = tuple(case.case_id for case in cases if token in case.factor_values)
            if not witnesses:
                raise RemainingStatementRegressError(f"ALTER EVENT TRIGGER missing witness for {token}")
            failures = all(by_id[case_id].outcome == "expected_failure" for case_id in witnesses)
            rows.append(FactorValueDecision(
                row_id=row_id, factor=factor.name, value=value,
                disposition="expected_failure" if failures else "covered",
                reason="isolated PostgreSQL rejection" if failures else None,
                case_ids=witnesses,
            ))
    return tuple(rows)


def build_alter_event_trigger_plan(
    snapshot: StatementFactorCycleSnapshot, entry: StatementCycleEntry
) -> StatementRegressPlan:
    cases = _build_cases()
    if len(cases) != 159:
        raise RemainingStatementRegressError(f"ALTER EVENT TRIGGER expected 159 cases, found {len(cases)}")
    return StatementRegressPlan(
        statement_key="alter_event_trigger", file_prefix="ALTEREVENTTRIGGER",
        cycle_fingerprint=snapshot.fingerprint, matrix_path=entry.matrix_path.as_posix(),
        matrix_sha256=entry.matrix_sha256, reference_path=entry.reference_path.as_posix(),
        reference_sha256=entry.reference_sha256,
        universe_semantic_sha256=snapshot.universe_semantic_sha256,
        official_source=entry.official_source, cases=cases,
        factor_decisions=_factor_decisions(entry, cases),
    )


def _qi(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _lit(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _names(case: StatementRegressCase) -> dict[str, str]:
    p = case.object_prefix
    quoted = case.derived_axes.get("trigger_name_shape") == "quoted_id"
    raw = p + ("Event Trigger" if quoted else "event_trigger")
    new_shape = case.derived_axes.get("new_name_shape")
    new_raw = "select" if new_shape == "reserved_word_as_name" else p + ("New Trigger" if new_shape == "quoted_id" else "new_trigger")
    owner_quoted = case.derived_axes.get("new_owner_shape") == "quoted_id"
    owner_raw = p + ("New Owner" if owner_quoted else "new_owner")
    return {
        "prefix": p, "trigger_raw": raw, "trigger": _qi(raw) if quoted else raw,
        "missing_trigger": p + "missing_trigger",
        "new_raw": new_raw, "new": _qi(new_raw) if new_shape in {"quoted_id", "reserved_word_as_name"} else new_raw,
        "conflict": p + "conflict_trigger", "function": p + "event_function",
        "probe_schema": p + "probe_schema", "intruder": p + "intruder",
        "owner_raw": owner_raw, "owner": _qi(owner_raw) if owner_quoted else owner_raw,
        "guc": "pgcf." + p + "fired",
    }


def _source(case: StatementRegressCase, n: Mapping[str, str]) -> str:
    return n["missing_trigger"] if case.derived_axes.get("object_state") == "not_exists" else n["trigger"]


def _target(case: StatementRegressCase, n: Mapping[str, str]) -> str:
    a = case.derived_axes
    source = _source(case, n)
    boundary = a.get("parser_boundary")
    if boundary:
        return {
            "empty_name": "ALTER EVENT TRIGGER DISABLE;",
            "qualified_source": f"ALTER EVENT TRIGGER public.{n['trigger']} DISABLE;",
            "three_part_source": f"ALTER EVENT TRIGGER db.public.{n['trigger']} DISABLE;",
            "unknown_state": f"ALTER EVENT TRIGGER {source} ENABLE LOCAL;",
            "duplicate_enable_modifier": f"ALTER EVENT TRIGGER {source} ENABLE REPLICA ALWAYS;",
            "missing_owner": f"ALTER EVENT TRIGGER {source} OWNER TO;",
            "qualified_owner": f"ALTER EVENT TRIGGER {source} OWNER TO public.some_role;",
            "owner_public": f"ALTER EVENT TRIGGER {source} OWNER TO PUBLIC;",
            "owner_none": f"ALTER EVENT TRIGGER {source} OWNER TO none;",
            "missing_rename_target": f"ALTER EVENT TRIGGER {source} RENAME TO;",
            "qualified_rename_target": f"ALTER EVENT TRIGGER {source} RENAME TO public.new_name;",
            "unquoted_reserved_target": f"ALTER EVENT TRIGGER {source} RENAME TO SELECT;",
        }[boundary]
    if a["branch"] == "disable":
        return f"ALTER EVENT TRIGGER {source} DISABLE;"
    if a["branch"] == "enable":
        return f"ALTER EVENT TRIGGER {source} ENABLE;"
    if a["branch"] == "enable_replica":
        return f"ALTER EVENT TRIGGER {source} ENABLE REPLICA;"
    if a["branch"] == "enable_always":
        return f"ALTER EVENT TRIGGER {source} ENABLE ALWAYS;"
    if a["branch"] == "owner":
        target = a.get("owner_target", "CURRENT_USER")
        if target == "existing_role":
            target = n["owner"]
        elif target == "nonexistent_role":
            target = n["owner"] + "_missing"
        return f"ALTER EVENT TRIGGER {source} OWNER TO {target};"
    target = n["conflict"] if a.get("rename_state") == "conflict" else n["new"]
    return f"ALTER EVENT TRIGGER {source} RENAME TO {target};"


def _state_setup(state: str, trigger: str) -> list[str]:
    if state == "enabled":
        return []
    command = {
        "disabled": "DISABLE", "enabled_replica": "ENABLE REPLICA", "enabled_always": "ENABLE ALWAYS"
    }[state]
    return ["-- setup-only ALTER EVENT TRIGGER; coverage_credit=false", f"ALTER EVENT TRIGGER {trigger} {command};"]


def _fixture(case: StatementRegressCase, n: Mapping[str, str]) -> list[str]:
    a = case.derived_axes
    lines = [
        "SET client_min_messages TO warning;", "SET session_replication_role TO origin;",
        f"CREATE ROLE {n['intruder']};",
    ]
    if a.get("owner_state") != "missing":
        lines.append(f"CREATE ROLE {n['owner']};")
    lines.extend([
        f"CREATE FUNCTION public.{n['function']}() RETURNS event_trigger",
        "LANGUAGE plpgsql",
        f"AS $body$ BEGIN PERFORM pg_catalog.set_config({_lit(n['guc'])}, '1', false); END $body$;",
    ])
    if a.get("object_state") != "not_exists":
        lines.append(
            f"CREATE EVENT TRIGGER {n['trigger']} ON ddl_command_end WHEN TAG IN ('CREATE SCHEMA') "
            f"EXECUTE FUNCTION public.{n['function']}();"
        )
        lines.extend(_state_setup(a.get("current_state", "enabled"), n["trigger"]))
    if a.get("rename_state") == "conflict":
        lines.append(
            f"CREATE EVENT TRIGGER {n['conflict']} ON ddl_command_end WHEN TAG IN ('CREATE SCHEMA') "
            f"EXECUTE FUNCTION public.{n['function']}();"
        )
    if a.get("function_state") == "function_not_exists":
        lines.append(f"DROP FUNCTION public.{n['function']}() CASCADE;")
    return lines


def _capture(n: Mapping[str, str]) -> list[str]:
    return [
        "SELECT",
        f"    COALESCE((SELECT oid::text FROM pg_catalog.pg_event_trigger WHERE evtname={_lit(n['trigger_raw'])}), '0') AS before_trigger_oid,",
        f"    COALESCE((SELECT evtenabled::text FROM pg_catalog.pg_event_trigger WHERE evtname={_lit(n['trigger_raw'])}), '<MISSING>') AS before_trigger_state,",
        f"    COALESCE((SELECT evtname FROM pg_catalog.pg_event_trigger WHERE evtname={_lit(n['trigger_raw'])}), '<MISSING>') AS before_trigger_name,",
        f"    COALESCE((SELECT evtowner::text FROM pg_catalog.pg_event_trigger WHERE evtname={_lit(n['trigger_raw'])}), '<MISSING>') AS before_trigger_owner",
        "FROM (VALUES (true)) AS capture_anchor(dummy)",
        "ORDER BY before_trigger_oid;", r"\gset",
    ]


def _oracle(case: StatementRegressCase, n: Mapping[str, str]) -> list[str]:
    a = case.derived_axes
    if case.outcome == "expected_failure" or a.get("transaction") == "rollback":
        return [
            "SELECT COALESCE(pg_catalog.bool_and(",
            "    e.evtenabled::text = :'before_trigger_state'",
            "    AND e.evtname = :'before_trigger_name'",
            "    AND e.evtowner::text = :'before_trigger_owner'",
            "), true) AS failed_or_rolled_back_state_unchanged",
            "FROM pg_catalog.pg_event_trigger AS e",
            "WHERE :'before_trigger_oid' <> '0' AND e.oid=:'before_trigger_oid'::oid",
            "ORDER BY failed_or_rolled_back_state_unchanged;",
        ]
    if a["branch"] in _STATE_BRANCHES:
        expected_state = {"disable": "D", "enable": "O", "enable_replica": "R", "enable_always": "A"}[a["branch"]]
        should_fire = a["branch"] == "enable_always" or (
            a["branch"] == "enable" and a["session_role"] in {"origin", "local"}
        ) or (a["branch"] == "enable_replica" and a["session_role"] == "replica")
        return [
            f"SELECT e.evtenabled = {_lit(expected_state)}::\"char\" AS evtenabled_matches",
            "FROM pg_catalog.pg_event_trigger AS e WHERE e.oid=:'before_trigger_oid'::oid",
            "ORDER BY evtenabled_matches;",
            f"SELECT pg_catalog.set_config({_lit(n['guc'])}, '0', false) = '0' AS firing_probe_reset;",
            f"SET session_replication_role TO {a['session_role']};",
            f"CREATE SCHEMA {n['probe_schema']};",
            "SET session_replication_role TO origin;",
            f"SELECT pg_catalog.current_setting({_lit(n['guc'])}) = {_lit('1' if should_fire else '0')} AS event_trigger_fired_matches",
            "FROM (VALUES (true)) AS firing_anchor(dummy)",
            "ORDER BY event_trigger_fired_matches;",
        ]
    if a["branch"] == "owner":
        return [
            "SELECT pg_catalog.pg_get_userbyid(e.evtowner) IS NOT NULL AS event_trigger_owner_observed",
            "FROM pg_catalog.pg_event_trigger AS e WHERE e.oid=:'before_trigger_oid'::oid",
            "ORDER BY event_trigger_owner_observed;",
        ]
    return [
        "SELECT e.evtname <> '' AS event_trigger_name_observed",
        "FROM pg_catalog.pg_event_trigger AS e WHERE e.oid=:'before_trigger_oid'::oid",
        "ORDER BY event_trigger_name_observed;",
    ]


def _cleanup(n: Mapping[str, str]) -> list[str]:
    return [
        "RESET ROLE;", "SET session_replication_role TO origin;",
        f"DROP SCHEMA IF EXISTS {n['probe_schema']} CASCADE;",
        f"DROP EVENT TRIGGER IF EXISTS {n['trigger']};",
        f"DROP EVENT TRIGGER IF EXISTS {n['new']};",
        f"DROP EVENT TRIGGER IF EXISTS {n['conflict']};",
        f"DROP FUNCTION IF EXISTS public.{n['function']}() CASCADE;",
        f"DROP ROLE IF EXISTS {n['owner']};", f"DROP ROLE IF EXISTS {n['intruder']};",
        "SELECT",
        f"    NOT EXISTS (SELECT 1 FROM pg_catalog.pg_event_trigger WHERE evtname IN ({_lit(n['trigger_raw'])}, {_lit(n['new_raw'])}, {_lit(n['conflict'])}))",
        f"    AND NOT EXISTS (SELECT 1 FROM pg_catalog.pg_proc WHERE proname={_lit(n['function'])})",
        f"    AND NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname IN ({_lit(n['owner_raw'])}, {_lit(n['intruder'])})) AS cleanup_complete",
        "FROM (VALUES (true)) AS cleanup_anchor(dummy)",
        "ORDER BY cleanup_complete;",
    ]


def render_alter_event_trigger_case(plan: StatementRegressPlan, case: StatementRegressCase) -> str:
    n = _names(case)
    lines = _header(plan, case) + [
        "", "-- 1. Header and immutable trace metadata are complete above.",
        "", "-- 2. Session settings are explicit and reset during cleanup.",
        "", "-- 3. Idempotent pre-cleanup.", *_cleanup(n),
        "", "-- 4. Event-trigger function, roles, and trigger fixture.", *_fixture(case, n),
        "", "-- 5. Function and target existence states are isolated above.",
        "SELECT true AS fixture_ready FROM (VALUES (true)) AS fixture_anchor(dummy) ORDER BY fixture_ready;",
        "", "-- 6. Capture the exact pg_event_trigger state.", *_capture(n),
        "", "-- 7. Select the superuser or deliberate non-superuser executor.",
    ]
    if case.derived_axes.get("actor") == "non_superuser":
        lines.append(f"SET ROLE {n['intruder']};")
    lines.extend(["", "-- 8. Primary target statement (exactly one coverage-credit operation)."])
    if case.derived_axes.get("transaction") == "rollback":
        lines.append("BEGIN;")
    lines.extend([
        r"\set ON_ERROR_STOP off", _target(case, n), r"\set alter_event_trigger_sqlstate :SQLSTATE", r"\set ON_ERROR_STOP on",
        "", "-- 9. SQLSTATE and primary-result oracle.",
        f"SELECT :'alter_event_trigger_sqlstate' = {_lit(case.derived_axes['expected_sqlstate'])} AS expected_SQLSTATE;",
    ])
    if case.derived_axes.get("transaction") == "rollback":
        lines.append("ROLLBACK;")
    lines.extend([
        "RESET ROLE;", "", "-- 10. Catalog and actual firing-semantics verification.", *_oracle(case, n),
        "", "-- 11. Drop trigger, function, probe schema, and roles.", *_cleanup(n),
        "", "-- 12. Cleanup oracle is the final executable query above.",
    ])
    return "\n".join(lines).rstrip() + "\n"


__all__ = ["build_alter_event_trigger_plan", "render_alter_event_trigger_case"]
