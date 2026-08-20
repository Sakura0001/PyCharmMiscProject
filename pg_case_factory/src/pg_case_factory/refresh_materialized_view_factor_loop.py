"""Factor-value-loop obligation ledger for PostgreSQL 18.4 REFRESH MATERIALIZED VIEW.

``REFRESH MATERIALIZED VIEW`` has a single syntax branch
(``statement_branch=branch_1``).  Every one of the 38 declared factor
values is a single ``SFV`` obligation (no ``GRM`` block, no ``INV``
block, no ``RISK``): one local program per obligation, so the baseline
case count equals 38 with zero delegated rows.

REFRESH operates on a ``pg_class`` materialized-view relation
(``relkind='m'``).  Success-path cases CREATE a fixture source table and
a fixture materialized view as setup, so the bookend contract (DROP
TABLE IF EXISTS first/last) applies to those cases.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class RefreshMaterializedViewFactorLoopError(ValueError):
    """Raised when a frozen REFRESH MATERIALIZED VIEW obligation drifts."""


@dataclass(frozen=True)
class RefreshMaterializedViewFactorObligation:
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
class RefreshMaterializedViewFactorCase:
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
class RefreshMaterializedViewFactorLoopPlan:
    obligations: tuple[RefreshMaterializedViewFactorObligation, ...]
    cases: tuple[RefreshMaterializedViewFactorCase, ...]
    delegated: tuple[RefreshMaterializedViewFactorObligation, ...]
    obligation_multiset_sha256: str


_REPRESENTATIVE_BRANCH = "refresh_materialized_view_branch_1"

_STATEMENT_BRANCH_CONSUMER = {
    "branch_1": "refresh_materialized_view_branch_1",
}

# Every factor resolves to the single branch consumer.
_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_BRANCH,
    "target_object_state": _REPRESENTATIVE_BRANCH,
    "expected_status": _REPRESENTATIVE_BRANCH,
    "concurrently_clause": _REPRESENTATIVE_BRANCH,
    "data_clause": _REPRESENTATIVE_BRANCH,
    "unique_index_state": _REPRESENTATIVE_BRANCH,
    "privilege_context": _REPRESENTATIVE_BRANCH,
    "name_shape": _REPRESENTATIVE_BRANCH,
    "dependency_state": _REPRESENTATIVE_BRANCH,
    "concurrently_restriction": _REPRESENTATIVE_BRANCH,
    "invalid_combination": _REPRESENTATIVE_BRANCH,
    "constraint_boundary": _REPRESENTATIVE_BRANCH,
    "verification_mode": _REPRESENTATIVE_BRANCH,
    "cleanup_mode": _REPRESENTATIVE_BRANCH,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates - the DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("target_object_state", "missing"),
        ("dependency_state", "missing_dependency"),
        ("privilege_context", "insufficient_privilege"),
        ("concurrently_restriction", "no_unique_index"),
        ("concurrently_restriction", "unpopulated_view"),
        ("concurrently_restriction", "with_no_data_conflict"),
        ("invalid_combination", "concurrently_with_no_data"),
        ("invalid_combination", "concurrently_without_unique_index"),
        ("constraint_boundary", "concurrent_refresh_lock"),
        ("constraint_boundary", "security_restricted_query"),
    }
)

_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "refresh_expected_failure_marker_provisional",
    ),
    ("target_object_state", "missing"): (
        "42704",
        "materialized_view_does_not_exist_provisional",
    ),
    ("dependency_state", "missing_dependency"): (
        "42704",
        "refresh_query_dependency_missing_provisional",
    ),
    ("privilege_context", "insufficient_privilege"): (
        "42501",
        "must_be_owner_of_materialized_view_provisional",
    ),
    ("concurrently_restriction", "no_unique_index"): (
        "0A000",
        "concurrently_requires_unique_index_provisional",
    ),
    ("concurrently_restriction", "unpopulated_view"): (
        "55000",
        "concurrently_requires_populated_view_provisional",
    ),
    ("concurrently_restriction", "with_no_data_conflict"): (
        "42601",
        "concurrently_cannot_be_used_with_no_data_provisional",
    ),
    ("invalid_combination", "concurrently_with_no_data"): (
        "42601",
        "concurrently_cannot_be_used_with_no_data_provisional",
    ),
    ("invalid_combination", "concurrently_without_unique_index"): (
        "0A000",
        "concurrently_requires_unique_index_provisional",
    ),
    ("constraint_boundary", "concurrent_refresh_lock"): (
        "55006",
        "concurrent_refresh_already_running_provisional",
    ),
    ("constraint_boundary", "security_restricted_query"): (
        "42501",
        "security_restricted_query_not_allowed_provisional",
    ),
}


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise RefreshMaterializedViewFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise RefreshMaterializedViewFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[RefreshMaterializedViewFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("refresh_materialized_view")
    if len(catalog_rows) != 38:
        raise RefreshMaterializedViewFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[RefreshMaterializedViewFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            RefreshMaterializedViewFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"REFRESHMATERIALIZEDVIEW-SFV|{row.row_id}|{consumer}"
                ),
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
    rows: tuple[RefreshMaterializedViewFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"refreshmaterializedview-factor-obligations-v1\n"
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


# Dense baseline defaults (all positive success values).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_1",
    "target_object_state": "exists_populated",
    "expected_status": "success",
    "concurrently_clause": "absent",
    "data_clause": "with_data",
    "unique_index_state": "has_unique_index",
    "privilege_context": "owner",
    "name_shape": "plain_identifier",
    "dependency_state": "ready",
    "concurrently_restriction": "all_conditions_met",
    "invalid_combination": "none",
    "constraint_boundary": "none",
    "verification_mode": "catalog_query",
    "cleanup_mode": "drop_objects",
}


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive T4/T5 boundary factors and expected_status from T1-T3 values.

    The three CONCURRENTLY restriction clusters overlap their T2/T1
    counterparts and are derived here so a single failure is not
    double-counted across concurrently_restriction / invalid_combination.
    """

    cr = a.get("concurrently_restriction", "all_conditions_met")
    ic = a.get("invalid_combination", "none")

    if cr == "no_unique_index" or ic == "concurrently_without_unique_index":
        a["concurrently_clause"] = "present"
        a["unique_index_state"] = "no_unique_index"
        a["concurrently_restriction"] = "no_unique_index"
        a["invalid_combination"] = "concurrently_without_unique_index"
    elif cr == "unpopulated_view":
        a["concurrently_clause"] = "present"
        a["target_object_state"] = "exists_unpopulated"
        a["concurrently_restriction"] = "unpopulated_view"
    elif cr == "with_no_data_conflict" or ic == "concurrently_with_no_data":
        a["concurrently_clause"] = "present"
        a["data_clause"] = "with_no_data"
        a["concurrently_restriction"] = "with_no_data_conflict"
        a["invalid_combination"] = "concurrently_with_no_data"

    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _baseline_assignments(
    obligation: RefreshMaterializedViewFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    if len(assignments) != len(set(assignments)):
        raise RefreshMaterializedViewFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: RefreshMaterializedViewFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise RefreshMaterializedViewFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_refresh_materialized_view_factor_loop_plan(
    repository_root: Path,
) -> RefreshMaterializedViewFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_refresh_materialized_view_factor_loop_obligations(
        root
    )
    cases: list[RefreshMaterializedViewFactorCase] = []
    delegated: list[RefreshMaterializedViewFactorObligation] = []
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
            RefreshMaterializedViewFactorCase(
                ordinal=ordinal,
                case_id=f"REFRESHMATERIALIZEDVIEW{ordinal:06d}",
                sql_filename=f"REFRESHMATERIALIZEDVIEW{ordinal:06d}.sql",
                object_prefix=(
                    f"refreshmaterializedview_{ordinal:06d}_"
                ),
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
    plan = RefreshMaterializedViewFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 38 or len(plan.delegated) != 0:
        raise RefreshMaterializedViewFactorLoopError(
            "factor loop plan count drift"
        )
    if len({row.primary_obligation_id for row in plan.cases}) != 38:
        raise RefreshMaterializedViewFactorLoopError(
            "local obligation mapping drift"
        )
    if len({row.sql_filename for row in plan.cases}) != 38:
        raise RefreshMaterializedViewFactorLoopError(
            "duplicate SQL filename"
        )
    return plan


def compile_refresh_materialized_view_factor_loop_obligations(
    repository_root: Path,
) -> tuple[RefreshMaterializedViewFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = _compile_canonical_obligations(root)
    rows = tuple(
        RefreshMaterializedViewFactorObligation(
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
    if len(rows) != 38:
        raise RefreshMaterializedViewFactorLoopError(
            "obligation count drift"
        )
    if len({row.obligation_id for row in rows}) != len(rows):
        raise RefreshMaterializedViewFactorLoopError(
            "duplicate obligation id"
        )
    expected_kind_counts = {"SFV": 38}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise RefreshMaterializedViewFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise RefreshMaterializedViewFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"} for row in rows
    ) != 38:
        raise RefreshMaterializedViewFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise RefreshMaterializedViewFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "RefreshMaterializedViewFactorLoopError",
    "RefreshMaterializedViewFactorObligation",
    "RefreshMaterializedViewFactorCase",
    "RefreshMaterializedViewFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_refresh_materialized_view_factor_loop_obligations",
    "build_refresh_materialized_view_factor_loop_plan",
    "_obligation_multiset_sha256",
]
