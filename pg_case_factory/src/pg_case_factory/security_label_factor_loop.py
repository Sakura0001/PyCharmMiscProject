"""Compile the marginal ``SFV`` obligation ledger for SECURITY LABEL.

SECURITY LABEL is a DDL-utility statement that attaches a security label
to a database object.  There are no separate ``GRM`` obligations because
``statement_branch`` (the 21 ON-object grammar branches) and
``object_type`` are themselves T1/T2 factors in the shipped applicability
universe, so every grammar branch is already carried as an ``SFV`` row.
No obligations are delegated.  No ``RISK`` obligations are synthesized
(the shipped rows carry none).

All 86 canonical ``SFV`` rows are loaded from the shipped applicability
universe (``load_shipped_applicability_universe``) and mapped 1:1 to
obligations and cases.  UNIVERSAL INVARIANT:
``catalog_rows == fvc == factor_value_count == 86``.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class SecurityLabelFactorLoopError(ValueError):
    """Raised when the SECURITY LABEL obligation ledger drifts."""


@dataclass(frozen=True)
class SecurityLabelFactorObligation:
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
class SecurityLabelFactorCase:
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
class SecurityLabelFactorLoopPlan:
    obligations: tuple[SecurityLabelFactorObligation, ...]
    cases: tuple[SecurityLabelFactorCase, ...]
    delegated: tuple[SecurityLabelFactorObligation, ...]
    obligation_multiset_sha256: str


_REPRESENTATIVE = "table"

# Map each statement_branch value to the object_type it targets so the
# rendered case uses the matching fixture.
_BRANCH_TO_OBJECT_TYPE: dict[str, str] = {
    "branch_on_table": "table",
    "branch_on_column": "column",
    "branch_on_aggregate": "aggregate",
    "branch_on_database": "database",
    "branch_on_domain": "domain",
    "branch_on_event_trigger": "event_trigger",
    "branch_on_foreign_table": "foreign_table",
    "branch_on_function": "function",
    "branch_on_large_object": "large_object",
    "branch_on_materialized_view": "materialized_view",
    "branch_on_language": "language",
    "branch_on_procedure": "procedure",
    "branch_on_publication": "publication",
    "branch_on_role": "role",
    "branch_on_routine": "routine",
    "branch_on_schema": "schema",
    "branch_on_sequence": "sequence",
    "branch_on_subscription": "subscription",
    "branch_on_tablespace": "tablespace",
    "branch_on_type": "type",
    "branch_on_view": "view",
}

# Factor -> default consumer action (an object_type fixture key).
_SFV_FACTOR_CONSUMER: dict[str, str] = {
    "object_type": _REPRESENTATIVE,
    "statement_branch": _REPRESENTATIVE,
    "expected_status": _REPRESENTATIVE,
    "object_existence": _REPRESENTATIVE,
    "for_provider_clause": _REPRESENTATIVE,
    "label_value": _REPRESENTATIVE,
    "aggregate_signature": "aggregate",
    "routine_signature": "function",
    "object_name_shape": _REPRESENTATIVE,
    "provider_name_shape": _REPRESENTATIVE,
    "column_name_shape": "column",
    "label_string_shape": _REPRESENTATIVE,
    "executor_privilege": _REPRESENTATIVE,
    "provider_registration": _REPRESENTATIVE,
    "prerequisite_object": _REPRESENTATIVE,
    "nonexistent_object": _REPRESENTATIVE,
    "privilege_insufficient": _REPRESENTATIVE,
    "unregistered_provider": _REPRESENTATIVE,
    "invalid_label_for_provider": _REPRESENTATIVE,
    "duplicate_label_same_provider": _REPRESENTATIVE,
    "verification_mode": _REPRESENTATIVE,
    "cleanup_mode": _REPRESENTATIVE,
}

# Value-dependent consumer overrides.
_FACTOR_VALUE_CONSUMER: dict[tuple[str, str], str] = {
    ("executor_privilege", "object_owner"): "table",
    ("executor_privilege", "non_owner"): "table",
    ("executor_privilege", "superuser"): "table",
    ("executor_privilege", "non_superuser_no_provider_privilege"): "table",
}
for _branch_value, _object_type in _BRANCH_TO_OBJECT_TYPE.items():
    _FACTOR_VALUE_CONSUMER[("statement_branch", _branch_value)] = _object_type
del _branch_value, _object_type

# Canonical (factor, value) pairs that reach the PG target check and are
# rejected (provisional sqlstates — the DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_existence", "object_not_exists"),
        ("nonexistent_object", "target_object_does_not_exist"),
        ("privilege_insufficient", "non_superuser_without_provider_privilege"),
        ("unregistered_provider", "provider_not_registered_failure"),
        ("provider_registration", "provider_not_registered"),
        ("provider_name_shape", "unregistered_provider"),
        ("invalid_label_for_provider", "provider_rejects_label"),
        ("executor_privilege", "non_owner"),
        ("executor_privilege", "non_superuser_no_provider_privilege"),
        ("column_name_shape", "nonexistent_column"),
        ("object_name_shape", "non_existing_name"),
        ("prerequisite_object", "object_not_exists"),
    }
)

_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "object_does_not_exist_provisional",
    ),
    ("object_existence", "object_not_exists"): (
        "42704",
        "object_does_not_exist_provisional",
    ),
    ("nonexistent_object", "target_object_does_not_exist"): (
        "42704",
        "object_does_not_exist_provisional",
    ),
    ("privilege_insufficient", "non_superuser_without_provider_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("unregistered_provider", "provider_not_registered_failure"): (
        "42704",
        "provider_not_installed_provisional",
    ),
    ("provider_registration", "provider_not_registered"): (
        "42704",
        "provider_not_installed_provisional",
    ),
    ("provider_name_shape", "unregistered_provider"): (
        "42704",
        "provider_not_installed_provisional",
    ),
    ("invalid_label_for_provider", "provider_rejects_label"): (
        "22023",
        "provider_rejected_label_provisional",
    ),
    ("executor_privilege", "non_owner"): (
        "42501",
        "security_label_requires_object_ownership",
    ),
    ("executor_privilege", "non_superuser_no_provider_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("column_name_shape", "nonexistent_column"): (
        "42704",
        "object_does_not_exist_provisional",
    ),
    ("object_name_shape", "non_existing_name"): (
        "42704",
        "object_does_not_exist_provisional",
    ),
    ("prerequisite_object", "object_not_exists"): (
        "42704",
        "object_does_not_exist_provisional",
    ),
}


def _canonical_consumer(row) -> str:
    key = (row.factor, row.value)
    if key in _FACTOR_VALUE_CONSUMER:
        return _FACTOR_VALUE_CONSUMER[key]
    if row.factor == "object_type":
        return row.value
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise SecurityLabelFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[SecurityLabelFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("security_label")
    if len(catalog_rows) != 86:
        raise SecurityLabelFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[SecurityLabelFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            SecurityLabelFactorObligation(
                ordinal=0,
                obligation_id=f"SECURITYLABEL-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[SecurityLabelFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"security-label-factor-obligations-v1\n"
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


# Dense baseline defaults (all positive success values).  The T5
# exception factors use a positive sentinel that is NOT in the shipped
# failure rows (mirrors comment's object_exists / owner_success pattern).
_BASELINE_DEFAULTS: dict[str, str] = {
    "object_type": "table",
    "statement_branch": "branch_on_table",
    "expected_status": "success",
    "object_existence": "object_exists",
    "for_provider_clause": "omitted_default_provider",
    "label_value": "string_literal",
    "aggregate_signature": "star_wildcard",
    "routine_signature": "no_args",
    "object_name_shape": "simple_name",
    "provider_name_shape": "registered_provider",
    "column_name_shape": "simple_name",
    "label_string_shape": "valid_label",
    "executor_privilege": "superuser",
    "provider_registration": "provider_registered",
    "prerequisite_object": "object_exists",
    "nonexistent_object": "target_object_exists",
    "privilege_insufficient": "sufficient_privilege",
    "unregistered_provider": "provider_registered",
    "invalid_label_for_provider": "provider_accepts_label",
    "duplicate_label_same_provider": "replaces_existing_label",
    "verification_mode": "pg_seclabel_catalog_query",
    "cleanup_mode": "security_label_is_null",
}


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive overlapping failure-consistent values + expected_status."""

    # Group 1: object-existence family.
    if (
        a.get("object_existence") == "object_not_exists"
        or a.get("nonexistent_object") == "target_object_does_not_exist"
        or a.get("prerequisite_object") == "object_not_exists"
        or a.get("object_name_shape") == "non_existing_name"
    ):
        a["object_existence"] = "object_not_exists"
        a["nonexistent_object"] = "target_object_does_not_exist"
        a["prerequisite_object"] = "object_not_exists"
        a["object_name_shape"] = "non_existing_name"

    # Group 2: provider-registration family.
    if (
        a.get("provider_registration") == "provider_not_registered"
        or a.get("provider_name_shape") == "unregistered_provider"
        or a.get("unregistered_provider") == "provider_not_registered_failure"
    ):
        a["provider_registration"] = "provider_not_registered"
        a["provider_name_shape"] = "unregistered_provider"
        a["unregistered_provider"] = "provider_not_registered_failure"

    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _baseline_assignments(
    obligation: SecurityLabelFactorObligation,
) -> tuple[tuple[str, str], ...]:
    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["object_type"] = obligation.consumer_action_id
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    if len(assignments) != len(set(assignments)):
        raise SecurityLabelFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: SecurityLabelFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise SecurityLabelFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_security_label_factor_loop_plan(
    repository_root: Path,
) -> SecurityLabelFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_security_label_factor_loop_obligations(root)
    cases: list[SecurityLabelFactorCase] = []
    delegated: list[SecurityLabelFactorObligation] = []
    for obligation in obligations:
        if obligation.disposition == "delegated":
            delegated.append(obligation)
            continue
        ordinal = len(cases) + 1
        if obligation.disposition == "expected_failure":
            sqlstate, failure_reason = _expected_failure_details(
                obligation
            )
            outcome = "expected_failure"
        else:
            outcome = "success"
            sqlstate = "00000"
            failure_reason = None
        cases.append(
            SecurityLabelFactorCase(
                ordinal=ordinal,
                case_id=f"SECURITYLABEL{ordinal:05d}",
                sql_filename=f"SECURITYLABEL{ordinal:05d}.sql",
                object_prefix=f"securitylabel_{ordinal:05d}_",
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
    plan = SecurityLabelFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 86 or len(plan.delegated) != 0:
        raise SecurityLabelFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 86:
        raise SecurityLabelFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 86:
        raise SecurityLabelFactorLoopError("duplicate SQL filename")
    return plan


def compile_security_label_factor_loop_obligations(
    repository_root: Path,
) -> tuple[SecurityLabelFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = _compile_canonical_obligations(root)
    rows = tuple(
        SecurityLabelFactorObligation(
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
    if len(rows) != 86:
        raise SecurityLabelFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise SecurityLabelFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"SFV": 86}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise SecurityLabelFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise SecurityLabelFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 86:
        raise SecurityLabelFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise SecurityLabelFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "SecurityLabelFactorLoopError",
    "SecurityLabelFactorObligation",
    "SecurityLabelFactorCase",
    "SecurityLabelFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_security_label_factor_loop_obligations",
    "build_security_label_factor_loop_plan",
    "_obligation_multiset_sha256",
]
