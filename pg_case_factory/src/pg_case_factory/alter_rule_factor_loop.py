"""Factor-value-loop obligation ledger for PostgreSQL 18.4 ALTER RULE.

This module compiles the marginal GRM/SFV/RISK obligation ledger for
``ALTER RULE``.  ALTER RULE supports only ``RENAME TO`` (single grammar
branch); there is no ``INV`` block because ``alter_rule.yaml`` marks
``column_type_coverage`` conditional and rule behaviour does not vary
with column types.  Each local obligation becomes exactly one regress
program; there are no delegated handoffs because every reachable
negative boundary is a real ``ALTER RULE`` error that belongs to this
statement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .alter_rule_regress import (
    AlterRuleRegressError,
    load_alter_rule_grammar_actions,
    load_alter_rule_grammar_axes,
)
from .applicability import load_shipped_applicability_universe


class AlterRuleFactorLoopError(ValueError):
    """Raised when a frozen ALTER RULE obligation input drifts."""


@dataclass(frozen=True)
class AlterRuleFactorObligation:
    ordinal: int
    obligation_id: str
    kind: str
    factor_key: str
    value: str
    consumer_action_id: str
    disposition: str
    source_locator: str
    delegated_statement_key: str | None = None


@dataclass(frozen=True)
class AlterRuleFactorCase:
    ordinal: int
    case_id: str
    sql_filename: str
    object_prefix: str
    primary_obligation_id: str
    kind: str
    factor_key: str
    factor_value: str
    consumer_action_id: str
    outcome: str
    expected_sqlstate: str
    expected_failure_reason: str | None
    baseline_assignments: tuple[tuple[str, str], ...]
    execution_profile: str


@dataclass(frozen=True)
class AlterRuleFactorLoopPlan:
    obligations: tuple[AlterRuleFactorObligation, ...]
    cases: tuple[AlterRuleFactorCase, ...]
    delegated: tuple[AlterRuleFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch.
_BRANCH_RENAME = "branch_rename"

# The single consumer action for every factor value.
_REPRESENTATIVE_ACTION = "rename"

# Canonical factor -> the action where the value is observable.  ALTER RULE
# has only one branch, so every factor resolves to "rename".
_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "alter_action": _REPRESENTATIVE_ACTION,
    "table_type": _REPRESENTATIVE_ACTION,
    "rule_name_shape": _REPRESENTATIVE_ACTION,
    "table_name_shape": _REPRESENTATIVE_ACTION,
    "new_name_shape": _REPRESENTATIVE_ACTION,
    "privilege_level": _REPRESENTATIVE_ACTION,
    "table_existence": _REPRESENTATIVE_ACTION,
    "nonexistent_rule": _REPRESENTATIVE_ACTION,
    "nonexistent_table": _REPRESENTATIVE_ACTION,
    "privilege_denied": _REPRESENTATIVE_ACTION,
    "duplicate_new_name": _REPRESENTATIVE_ACTION,
    "on_select_return_rename": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "not_exists"),
        ("rule_name_shape", "nonexistent_name"),
        ("table_name_shape", "nonexistent_table"),
        ("table_existence", "table_not_exists"),
        ("nonexistent_rule", "rule_missing"),
        ("nonexistent_table", "table_missing"),
        ("privilege_level", "non_owner"),
        ("privilege_denied", "non_owner_denied"),
        ("new_name_shape", "duplicate_name_same_table"),
        ("duplicate_new_name", "same_table_same_event_conflict"),
        ("new_name_shape", "invalid_name"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
# These are provisional pending DB-phase calibration on PG 18.4.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42P01",
        "expected_status_failure_rule_not_found",
    ),
    ("object_state", "not_exists"): ("42P01", "rule_does_not_exist"),
    ("rule_name_shape", "nonexistent_name"): (
        "42P01",
        "rule_does_not_exist",
    ),
    ("table_name_shape", "nonexistent_table"): (
        "42P01",
        "relation_does_not_exist",
    ),
    ("table_existence", "table_not_exists"): (
        "42P01",
        "relation_does_not_exist",
    ),
    ("nonexistent_rule", "rule_missing"): (
        "42P01",
        "rule_does_not_exist",
    ),
    ("nonexistent_table", "table_missing"): (
        "42P01",
        "relation_does_not_exist",
    ),
    ("privilege_level", "non_owner"): (
        "42501",
        "must_be_owner_of_table",
    ),
    ("privilege_denied", "non_owner_denied"): (
        "42501",
        "permission_denied_for_table",
    ),
    ("new_name_shape", "duplicate_name_same_table"): (
        "42710",
        "duplicate_rule",
    ),
    ("duplicate_new_name", "same_table_same_event_conflict"): (
        "42710",
        "duplicate_rule",
    ),
    ("new_name_shape", "invalid_name"): (
        "42601",
        "syntax_error_invalid_identifier",
    ),
}

# The _RETURN rename is a SUCCESS with a behavior assertion (the view
# breaks).  It is NOT a failure — the rename succeeds (00000) but the
# follow-up SELECT on the view fails.
_EXPECTED_BEHAVIOR_VALUES = frozenset(
    {
        ("on_select_return_rename", "_RETURN_rename_breaks_view"),
    }
)


def _canonical_consumer(row) -> str:
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise AlterRuleFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> list[AlterRuleFactorObligation]:
    rows: list[AlterRuleFactorObligation] = []
    for action in load_alter_rule_grammar_actions():
        rows.append(
            AlterRuleFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"AR-GRM|{action.grammar_branch_id}|"
                    f"{action.action_id}|target_action|{action.action_id}"
                ),
                kind="GRM",
                factor_key="target_action",
                value=action.action_id,
                consumer_action_id=action.action_id,
                disposition="covered",
                source_locator=action.source_locator,
            )
        )
    for axis in load_alter_rule_grammar_axes():
        factor_key = (
            f"outer:{axis.axis_id}"
            if axis.action_id == "__outer_action__"
            else f"local:{axis.axis_id}"
        )
        consumer = (
            _REPRESENTATIVE_ACTION
            if axis.action_id == "__outer_action__"
            else axis.action_id
        )
        for value in axis.values:
            rows.append(
                AlterRuleFactorObligation(
                    ordinal=0,
                    obligation_id=(
                        f"AR-GRM|{axis.grammar_branch_id}|"
                        f"{axis.action_id}|{axis.axis_id}|{value}"
                    ),
                    kind="GRM",
                    factor_key=factor_key,
                    value=value,
                    consumer_action_id=consumer,
                    disposition="covered",
                    source_locator=axis.source_locator,
                )
            )
    if len(rows) != 1:
        raise AlterRuleFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[AlterRuleFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("alter_rule")
    if len(catalog_rows) != 43:
        raise AlterRuleFactorLoopError("canonical obligation count drift")
    rows: list[AlterRuleFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        is_behavior = (row.factor, row.value) in _EXPECTED_BEHAVIOR_VALUES
        rows.append(
            AlterRuleFactorObligation(
                ordinal=0,
                obligation_id=f"AR-SFV|{row.row_id}|{consumer}",
                kind="SFV",
                factor_key=row.factor,
                value=row.value,
                consumer_action_id=consumer,
                disposition=(
                    "expected_failure"
                    if is_failure
                    else "covered"
                ),
                source_locator=f"{row.source_reference}#{row.row_id}",
            )
        )
    return rows


def _compile_risk_obligations() -> list[AlterRuleFactorObligation]:
    return [
        AlterRuleFactorObligation(
            ordinal=0,
            obligation_id=f"AR-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-alterrule:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[AlterRuleFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"alter-rule-factor-obligations-v1\n")
    for row in rows:
        digest.update(
            json.dumps(
                {
                    "obligation_id": row.obligation_id,
                    "kind": row.kind,
                    "factor_key": row.factor_key,
                    "value": row.value,
                    "consumer_action_id": row.consumer_action_id,
                    "disposition": row.disposition,
                    "delegated_statement_key": row.delegated_statement_key,
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        digest.update(b"\n")
    return digest.hexdigest()


def _renderer_factor_key(factor_key: str) -> str:
    """Map an obligation factor key to the renderer's flat factor namespace."""

    if factor_key.startswith("outer:") or factor_key.startswith("local:"):
        return factor_key.split(":", 1)[1]
    return factor_key


# Dense baseline defaults (all positive T1-T6 factor values).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_rename",
    "grammar_branch": "branch_rename",
    "alter_action": "rename",
    "object_state": "exists",
    "expected_status": "success",
    "table_type": "table",
    "rule_name_shape": "simple_id",
    "table_name_shape": "simple_id",
    "new_name_shape": "simple_id",
    "privilege_level": "superuser",
    "table_existence": "table_exists",
    "nonexistent_rule": "rule_exists",
    "nonexistent_table": "table_exists",
    "privilege_denied": "owner_execution",
    "duplicate_new_name": "no_conflict",
    "on_select_return_rename": "normal_rule_rename",
    "verification_mode": "catalog_query_pg_rewrite",
    "cleanup_mode": "revert_rename",
}


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive T3↔T4↔T5 overlapping factor values in-place.

    The T5 boundary factors describe the same scenario as their T3/T4
    counterparts.  When the primary factor is a T3/T4 value, the
    corresponding T5 value is derived.  When the primary is a T5 value,
    the T3/T4 counterpart is derived.  This keeps the baseline assignment
    self-consistent so the render produces SQL that actually reaches the
    intended boundary.
    """

    rns = a.get("rule_name_shape", "simple_id")
    tns = a.get("table_name_shape", "simple_id")
    nns = a.get("new_name_shape", "simple_id")
    pl = a.get("privilege_level", "superuser")
    os_ = a.get("object_state", "exists")
    te = a.get("table_existence", "table_exists")
    nr = a.get("nonexistent_rule", "rule_exists")
    nt = a.get("nonexistent_table", "table_exists")
    pd = a.get("privilege_denied", "owner_execution")
    dn = a.get("duplicate_new_name", "no_conflict")
    otr = a.get("on_select_return_rename", "normal_rule_rename")

    # rule_name_shape <-> nonexistent_rule / object_state
    if rns == "nonexistent_name":
        a["nonexistent_rule"] = "rule_missing"
        a["object_state"] = "not_exists"
    elif nr == "rule_missing":
        a["rule_name_shape"] = "nonexistent_name"
        a["object_state"] = "not_exists"
    elif os_ == "not_exists":
        a["rule_name_shape"] = "nonexistent_name"
        a["nonexistent_rule"] = "rule_missing"

    # table_name_shape <-> nonexistent_table / table_existence
    if tns == "nonexistent_table":
        a["nonexistent_table"] = "table_missing"
        a["table_existence"] = "table_not_exists"
    elif nt == "table_missing":
        a["table_name_shape"] = "nonexistent_table"
        a["table_existence"] = "table_not_exists"
    elif te == "table_not_exists":
        a["table_name_shape"] = "nonexistent_table"
        a["nonexistent_table"] = "table_missing"

    # new_name_shape <-> duplicate_new_name
    if nns == "duplicate_name_same_table":
        a["duplicate_new_name"] = "same_table_same_event_conflict"
    elif dn == "same_table_same_event_conflict":
        a["new_name_shape"] = "duplicate_name_same_table"

    # privilege_level <-> privilege_denied
    if pl == "non_owner":
        a["privilege_denied"] = "non_owner_denied"
    elif pl == "table_owner":
        a["privilege_denied"] = "owner_execution"
    elif pd == "non_owner_denied":
        a["privilege_level"] = "non_owner"
    elif pd == "owner_execution":
        a["privilege_level"] = "table_owner"

    # on_select_return_rename <-> rule_name_shape + table_type
    tt = a.get("table_type", "table")
    if rns == "_RETURN_special" and tt == "view":
        a["on_select_return_rename"] = "_RETURN_rename_breaks_view"
    elif otr == "_RETURN_rename_breaks_view":
        a["rule_name_shape"] = "_RETURN_special"
        a["table_type"] = "view"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: AlterRuleFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    key = _renderer_factor_key(obligation.factor_key)
    assignments[key] = obligation.value
    _derive_overlapping_factors(assignments)
    failures = _count_baseline_failures(assignments)
    assignments["expected_status"] = "failure" if failures > 0 else "success"
    if len(assignments) != len(set(assignments)):
        raise AlterRuleFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: AlterRuleFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise AlterRuleFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_alter_rule_factor_loop_plan(
    repository_root: Path,
) -> AlterRuleFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_alter_rule_factor_loop_obligations(root)
    cases: list[AlterRuleFactorCase] = []
    delegated: list[AlterRuleFactorObligation] = []
    for obligation in obligations:
        if obligation.disposition == "delegated":
            delegated.append(obligation)
            continue
        ordinal = len(cases) + 1
        if obligation.disposition == "expected_failure":
            sqlstate, failure_reason = _expected_failure_details(obligation)
            outcome = "expected_failure"
        else:
            outcome = "success"
            sqlstate = "00000"
            failure_reason = None
        cases.append(
            AlterRuleFactorCase(
                ordinal=ordinal,
                case_id=f"ALTERRULE{ordinal:05d}",
                sql_filename=f"ALTERRULE{ordinal:05d}.sql",
                object_prefix=f"alterrule_{ordinal:05d}_",
                primary_obligation_id=obligation.obligation_id,
                kind=obligation.kind,
                factor_key=_renderer_factor_key(obligation.factor_key),
                factor_value=obligation.value,
                consumer_action_id=obligation.consumer_action_id,
                outcome=outcome,
                expected_sqlstate=sqlstate,
                expected_failure_reason=failure_reason,
                baseline_assignments=_baseline_assignments(obligation),
                execution_profile="serial_sql",
            )
        )
    plan = AlterRuleFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 46 or len(plan.delegated) != 0:
        raise AlterRuleFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 46:
        raise AlterRuleFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 46:
        raise AlterRuleFactorLoopError("duplicate SQL filename")
    return plan


def compile_alter_rule_factor_loop_obligations(
    repository_root: Path,
) -> tuple[AlterRuleFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        AlterRuleFactorObligation(
            ordinal=ordinal,
            obligation_id=row.obligation_id,
            kind=row.kind,
            factor_key=row.factor_key,
            value=row.value,
            consumer_action_id=row.consumer_action_id,
            disposition=row.disposition,
            source_locator=row.source_locator,
            delegated_statement_key=row.delegated_statement_key,
        )
        for ordinal, row in enumerate(unordered_rows, start=1)
    )
    if len(rows) != 46:
        raise AlterRuleFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise AlterRuleFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 43, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise AlterRuleFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise AlterRuleFactorLoopError("delegated obligation count drift")
    if sum(row.disposition in {"covered", "expected_failure"} for row in rows) != 46:
        raise AlterRuleFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(row.disposition not in allowed_dispositions for row in rows):
        raise AlterRuleFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "AlterRuleFactorLoopError",
    "AlterRuleFactorObligation",
    "AlterRuleFactorCase",
    "AlterRuleFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "_EXPECTED_BEHAVIOR_VALUES",
    "compile_alter_rule_factor_loop_obligations",
    "build_alter_rule_factor_loop_plan",
    "_obligation_multiset_sha256",
]
