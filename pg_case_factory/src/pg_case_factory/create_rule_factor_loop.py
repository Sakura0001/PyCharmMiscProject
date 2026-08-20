"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE RULE.

This module compiles the marginal ``SFV`` obligation ledger for
``CREATE [ OR REPLACE ] RULE``.  CREATE RULE is a PostgreSQL DDL
statement whose official synopsis is::

    CREATE [ OR REPLACE ] RULE name AS ON event TO table_name
        [ WHERE condition ] DO [ INSTEAD ] { NOTHING | command | ( command_list ) }

The statement defines a ``pg_catalog.pg_rewrite`` catalog row attached to
a relation (table or view).  CREATE RULE is table-creating: the render
emits ``CREATE TABLE`` fixture(s) for the rule target, so the bookend
(DROP TABLE IF EXISTS) applies.  The statement supports ``OR REPLACE``;
the renderer emits both ``CREATE RULE`` and ``CREATE OR REPLACE RULE``
variants.

Each local obligation becomes exactly one regress program.  The 72
canonical ``SFV`` rows are loaded from the shipped applicability universe
(``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CreateRuleFactorLoopError(ValueError):
    """Raised when a frozen CREATE RULE obligation input drifts."""


@dataclass(frozen=True)
class CreateRuleFactorObligation:
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
class CreateRuleFactorCase:
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
class CreateRuleFactorLoopPlan:
    obligations: tuple[CreateRuleFactorObligation, ...]
    cases: tuple[CreateRuleFactorCase, ...]
    delegated: tuple[CreateRuleFactorObligation, ...]
    obligation_multiset_sha256: str


_DOC_SOURCE = "postgresql-18.4-doc:sql-createrule"
_REPRESENTATIVE_ACTION = "create_rule"


def _canonical_consumer(row) -> str:
    return _REPRESENTATIVE_ACTION


# Unconditional failure (factor, value) pairs.  The conditional duplicate
# failure (object_state=exists_same_table_same_event + or_replace=absent)
# is NOT listed here -- it is resolved via the derivation logic so that
# the OR REPLACE variant (or_replace=present, a success) is not falsely
# counted as a failure.
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("circular_rule", "circular_select_rule_error"),
        ("conditional_rule_on_view", "only_conditional_rules_on_view"),
        ("duplicate_rule", "same_table_same_event_same_name"),
        ("new_old_in_invalid_event", "new_in_delete_invalid"),
        ("new_old_in_invalid_event", "old_in_insert_invalid"),
        ("nonexistent_table", "table_missing"),
        ("on_conflict_incompatibility", "on_conflict_insert_rule_conflict"),
        ("on_select_rule_constraints", "on_select_conditional_invalid"),
        ("on_select_rule_constraints", "on_select_multi_command_invalid"),
        ("on_select_rule_constraints", "on_select_not_INSTEAD_invalid"),
        ("on_select_rule_constraints", "on_select_not_RETURN_name"),
        ("on_select_rule_constraints", "on_select_on_table_invalid"),
        ("privilege_denied", "non_owner_denied"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42710",
        "duplicate_rule_provisional",
    ),
    ("object_state", "exists_same_table_same_event"): (
        "42710",
        "duplicate_rule_provisional",
    ),
    ("circular_rule", "circular_select_rule_error"): (
        "42P17",
        "invalid_rule_definition_provisional",
    ),
    ("conditional_rule_on_view", "only_conditional_rules_on_view"): (
        "42P17",
        "invalid_rule_definition_provisional",
    ),
    ("duplicate_rule", "same_table_same_event_same_name"): (
        "42710",
        "duplicate_rule_provisional",
    ),
    ("new_old_in_invalid_event", "new_in_delete_invalid"): (
        "42P17",
        "invalid_rule_definition_provisional",
    ),
    ("new_old_in_invalid_event", "old_in_insert_invalid"): (
        "42P17",
        "invalid_rule_definition_provisional",
    ),
    ("nonexistent_table", "table_missing"): (
        "42P01",
        "undefined_table_provisional",
    ),
    ("on_conflict_incompatibility", "on_conflict_insert_rule_conflict"): (
        "42P17",
        "invalid_rule_definition_provisional",
    ),
    ("on_select_rule_constraints", "on_select_conditional_invalid"): (
        "42P17",
        "invalid_rule_definition_provisional",
    ),
    ("on_select_rule_constraints", "on_select_multi_command_invalid"): (
        "42P17",
        "invalid_rule_definition_provisional",
    ),
    ("on_select_rule_constraints", "on_select_not_INSTEAD_invalid"): (
        "42P17",
        "invalid_rule_definition_provisional",
    ),
    ("on_select_rule_constraints", "on_select_not_RETURN_name"): (
        "42P17",
        "invalid_rule_definition_provisional",
    ),
    ("on_select_rule_constraints", "on_select_on_table_invalid"): (
        "42P17",
        "invalid_rule_definition_provisional",
    ),
    ("privilege_denied", "non_owner_denied"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
}


def _obligation_is_failure(factor: str, value: str) -> bool:
    if (factor, value) in _SFV_FAILURE_VALUES:
        return True
    if factor == "object_state" and value == "exists_same_table_same_event":
        return True
    return False


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateRuleFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_rule")
    if len(catalog_rows) != 72:
        raise CreateRuleFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[CreateRuleFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = _obligation_is_failure(row.factor, row.value)
        rows.append(
            CreateRuleFactorObligation(
                ordinal=0,
                obligation_id=f"CRULE-SFV|{row.row_id}|{consumer}",
                kind="SFV",
                factor_key=row.factor,
                value=row.value,
                consumer_action_id=consumer,
                disposition=(
                    "expected_failure" if is_failure else "covered"
                ),
                source_locator=f"{row.source_reference}#{row.row_id}",
            )
        )
    return rows


def _obligation_multiset_sha256(
    rows: tuple[CreateRuleFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-rule-factor-obligations-v1\n"
    )
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
                    "delegated_statement_key": (
                        row.delegated_statement_key
                    ),
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        digest.update(b"\n")
    return digest.hexdigest()


# Dense baseline defaults (all positive T1-T4 + T6 factor values).  The T5
# single-value boundary factors are derived in
# :func:`_derive_overlapping_factors` so that the success path is never
# falsely attributed a failure.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_create_rule",
    "event_type": "INSERT",
    "expected_status": "success",
    "object_state": "not_exists",
    "rule_action": "INSTEAD",
    "command_content": "INSERT_command",
    "command_type": "single_command",
    "or_replace": "absent",
    "where_condition": "omitted",
    "rule_name_shape": "simple_id",
    "table_name_shape": "simple_id",
    "privilege_level": "superuser",
    "table_existence": "table_exists",
    "table_type": "table",
    "circular_rule": "no_circular_dependency",
    "conditional_rule_on_view": "unconditional_instead_present",
    "duplicate_rule": "no_conflict",
    "new_old_in_invalid_event": "valid_new_old_reference",
    "nonexistent_table": "table_exists",
    "on_conflict_incompatibility": "no_on_conflict_issue",
    "on_select_rule_constraints": "valid_on_select_on_view",
    "privilege_denied": "superuser_execution",
    "cleanup_mode": "drop_rule",
    "verification_mode": "catalog_query_pg_rewrite",
}


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values.

    The T5 single-value factors describe the same scenario as their T1-T4
    counterparts.  When the primary factor is a T1-T4 value, the
    corresponding T5 value is derived; when the primary is a T5 value,
    the T1-T4 counterpart is derived.
    """

    # --- duplicate_rule / object_state / or_replace cluster -----------
    dr = a.get("duplicate_rule", "no_conflict")
    if dr == "same_table_same_event_same_name":
        a["object_state"] = "exists_same_table_same_event"
        a["or_replace"] = "absent"
    os_ = a.get("object_state", "not_exists")
    orr = a.get("or_replace", "absent")
    if os_ == "exists_same_table_same_event" and orr == "absent":
        a["duplicate_rule"] = "same_table_same_event_same_name"
    elif os_ == "exists_same_table_same_event" and orr == "present":
        a["duplicate_rule"] = "no_conflict"
    elif os_ == "not_exists":
        a["duplicate_rule"] = "no_conflict"

    # --- nonexistent_table / table_existence / table_name_shape -------
    nt = a.get("nonexistent_table", "table_exists")
    te = a.get("table_existence", "table_exists")
    tns = a.get("table_name_shape", "simple_id")
    if nt == "table_missing":
        a["table_existence"] = "table_not_exists"
        a["table_name_shape"] = "nonexistent_table"
    elif te == "table_not_exists" or tns == "nonexistent_table":
        a["nonexistent_table"] = "table_missing"
        a["table_existence"] = "table_not_exists"
        a["table_name_shape"] = "nonexistent_table"

    # --- privilege_denied / privilege_level cluster -------------------
    pd = a.get("privilege_denied", "superuser_execution")
    pl = a.get("privilege_level", "superuser")
    if pd == "non_owner_denied":
        a["privilege_level"] = "non_owner"
    elif pd == "owner_execution":
        a["privilege_level"] = "table_owner"
    elif pd == "superuser_execution":
        a["privilege_level"] = "superuser"
    if pl == "non_owner" and pd != "non_owner_denied":
        a["privilege_denied"] = "non_owner_denied"
    elif pl == "table_owner" and pd not in (
        "owner_execution",
        "non_owner_denied",
    ):
        a["privilege_denied"] = "owner_execution"

    # --- on_select_rule_constraints cluster ---------------------------
    osr = a.get("on_select_rule_constraints", "valid_on_select_on_view")
    if osr != "valid_on_select_on_view":
        a["event_type"] = "SELECT"
        a["rule_name_shape"] = "_RETURN_special_name"
        a["rule_action"] = "INSTEAD"
        if "on_table" in osr:
            a["table_type"] = "table"
        else:
            a["table_type"] = "view"
        if osr == "on_select_conditional_invalid":
            a["where_condition"] = "simple_boolean_condition"
        elif osr == "on_select_multi_command_invalid":
            a["command_type"] = "multiple_commands"

    # --- circular_rule cluster -----------------------------------------
    cr = a.get("circular_rule", "no_circular_dependency")
    if cr == "circular_select_rule_error":
        a["event_type"] = "SELECT"
        a["table_type"] = "view"
        a["rule_name_shape"] = "_RETURN_special_name"
        a["rule_action"] = "INSTEAD"

    # --- conditional_rule_on_view cluster ------------------------------
    crv = a.get(
        "conditional_rule_on_view", "unconditional_instead_present"
    )
    if crv == "only_conditional_rules_on_view":
        a["event_type"] = "SELECT"
        a["table_type"] = "view"
        a["where_condition"] = "simple_boolean_condition"

    # --- new_old_in_invalid_event cluster ------------------------------
    noi = a.get("new_old_in_invalid_event", "valid_new_old_reference")
    if noi == "new_in_delete_invalid":
        a["event_type"] = "DELETE"
        a["where_condition"] = "new_old_reference_condition"
    elif noi == "old_in_insert_invalid":
        a["event_type"] = "INSERT"
        a["where_condition"] = "new_old_reference_condition"

    # --- on_conflict_incompatibility cluster ---------------------------
    oci = a.get("on_conflict_incompatibility", "no_on_conflict_issue")
    if oci == "on_conflict_insert_rule_conflict":
        a["event_type"] = "INSERT"

    # --- expected_status=failure -> representative failure -------------
    es = a.get("expected_status", "success")
    if es == "failure":
        a["object_state"] = "exists_same_table_same_event"
        a["or_replace"] = "absent"
        a["duplicate_rule"] = "same_table_same_event_same_name"

    # --- Derive expected_status from failure count --------------------
    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _baseline_assignments(
    obligation: CreateRuleFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    failures = _count_baseline_failures(assignments)
    assignments["expected_status"] = (
        "failure" if failures > 0 else "success"
    )
    if len(assignments) != len(set(assignments)):
        raise CreateRuleFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateRuleFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateRuleFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_rule_factor_loop_plan(
    repository_root: Path,
) -> CreateRuleFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_rule_factor_loop_obligations(root)
    cases: list[CreateRuleFactorCase] = []
    delegated: list[CreateRuleFactorObligation] = []
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
            CreateRuleFactorCase(
                ordinal=ordinal,
                case_id=f"CREATERULE{ordinal:05d}",
                sql_filename=f"CREATERULE{ordinal:05d}.sql",
                object_prefix=f"createrule_{ordinal:05d}_",
                primary_obligation_id=obligation.obligation_id,
                kind=obligation.kind,
                factor_key=obligation.factor_key,
                factor_value=obligation.value,
                consumer_action_id=obligation.consumer_action_id,
                outcome=outcome,
                expected_sqlstate=sqlstate,
                expected_failure_reason=failure_reason,
                baseline_assignments=_baseline_assignments(obligation),
                execution_profile="serial_sql",
            )
        )
    plan = CreateRuleFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 72 or len(plan.delegated) != 0:
        raise CreateRuleFactorLoopError(
            "factor loop plan count drift"
        )
    if len({row.primary_obligation_id for row in plan.cases}) != 72:
        raise CreateRuleFactorLoopError(
            "local obligation mapping drift"
        )
    if len({row.sql_filename for row in plan.cases}) != 72:
        raise CreateRuleFactorLoopError("duplicate SQL filename")
    return plan


def compile_create_rule_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateRuleFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = _compile_canonical_obligations(root)
    rows = tuple(
        CreateRuleFactorObligation(
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
    if len(rows) != 72:
        raise CreateRuleFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateRuleFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"SFV": 72}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateRuleFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateRuleFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 72:
        raise CreateRuleFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreateRuleFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "CreateRuleFactorLoopError",
    "CreateRuleFactorObligation",
    "CreateRuleFactorCase",
    "CreateRuleFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "_BASELINE_DEFAULTS",
    "compile_create_rule_factor_loop_obligations",
    "build_create_rule_factor_loop_plan",
    "_obligation_multiset_sha256",
]
