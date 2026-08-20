"""Factor-value-loop obligation ledger for PostgreSQL 18.4 LOCK TABLE.

This module compiles the marginal ``SFV`` obligation ledger for
``LOCK TABLE``.  LOCK TABLE is a PostgreSQL utility statement that
obtains a table-level lock on the named relation, held for the duration
of the current transaction.  The official synopsis has a single
top-level form (``LOCK TABLE name [, ...] [ IN mode MODE ] [ NOWAIT ]``),
so the shipped applicability universe declares exactly one
``statement_branch`` value (``branch_1``).

Like ``CLUSTER``, LOCK TABLE has no separate ``target_action`` grammar
axis and no ``GRM`` / ``INV`` / ``RISK`` blocks: every one of the 46
declared factor values is a single ``SFV`` obligation.  Each local
obligation becomes exactly one regress program, so the baseline case
count equals the obligation count (46) with zero delegated rows.

LOCK TABLE operates on a ``pg_class`` table relation.  Cases that
exercise a success path CREATE the fixture table as setup, so the
bookend contract (DROP TABLE IF EXISTS first/last) applies to those
cases.  Failure cases that target a missing or wrong-type relation
create no fixture table and satisfy the bookend vacuously.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class LockFactorLoopError(ValueError):
    """Raised when a frozen LOCK obligation input drifts."""


@dataclass(frozen=True)
class LockFactorObligation:
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
class LockFactorCase:
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
class LockFactorLoopPlan:
    obligations: tuple[LockFactorObligation, ...]
    cases: tuple[LockFactorCase, ...]
    delegated: tuple[LockFactorObligation, ...]
    obligation_multiset_sha256: str


_DOC_SOURCE = "postgresql-18.4-doc:sql-lock"

# Representative branch used as the baseline consumer for canonical factor
# values.  LOCK TABLE has a single declared statement_branch (branch_1).
_REPRESENTATIVE_BRANCH = "branch_1"

# statement_branch canonical value -> consumer (the branch itself).
_STATEMENT_BRANCH_CONSUMER = {
    "branch_1": "branch_1",
}

# Canonical factor -> the branch where the value is observable.  LOCK TABLE
# has only one branch, so every canonical factor resolves to branch_1.
_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_BRANCH,
    "target_state": _REPRESENTATIVE_BRANCH,
    "expected_status": _REPRESENTATIVE_BRANCH,
    "execution_mode": _REPRESENTATIVE_BRANCH,
    "option_shape": _REPRESENTATIVE_BRANCH,
    "input_output_shape": _REPRESENTATIVE_BRANCH,
    "target_name_shape": _REPRESENTATIVE_BRANCH,
    "environment_context": _REPRESENTATIVE_BRANCH,
    "privilege_context": _REPRESENTATIVE_BRANCH,
    "invalid_combination": _REPRESENTATIVE_BRANCH,
    "resource_boundary": _REPRESENTATIVE_BRANCH,
    "cleanup_mode": _REPRESENTATIVE_BRANCH,
    "verification_mode": _REPRESENTATIVE_BRANCH,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates - DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("target_state", "target_missing"),
        ("target_state", "wrong_object_type"),
        ("invalid_combination", "object_type_mismatch"),
        ("invalid_combination", "syntax_valid_semantic_error"),
        ("privilege_context", "insufficient_privilege"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42P01",
        "lock_target_missing_provisional",
    ),
    ("target_state", "target_missing"): (
        "42P01",
        "lock_target_missing_provisional",
    ),
    ("target_state", "wrong_object_type"): (
        "42809",
        "lock_wrong_object_type_provisional",
    ),
    ("invalid_combination", "object_type_mismatch"): (
        "42809",
        "lock_wrong_object_type_provisional",
    ),
    ("invalid_combination", "syntax_valid_semantic_error"): (
        "42809",
        "lock_semantic_error_provisional",
    ),
    ("privilege_context", "insufficient_privilege"): (
        "42501",
        "lock_insufficient_privilege_provisional",
    ),
}


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise LockFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise LockFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[LockFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("lock")
    if len(catalog_rows) != 46:
        raise LockFactorLoopError("canonical obligation count drift")
    rows: list[LockFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            LockFactorObligation(
                ordinal=0,
                obligation_id=f"LOCK-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[LockFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"lock-factor-obligations-v1\n")
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


# Dense baseline defaults (all positive factor values).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_1",
    "target_state": "target_exists",
    "expected_status": "success",
    "execution_mode": "executes_statement",
    "option_shape": "minimal",
    "input_output_shape": "none",
    "target_name_shape": "plain_identifier",
    "environment_context": "normal_session",
    "privilege_context": "owner",
    "invalid_combination": "none",
    "resource_boundary": "small_relation",
    "cleanup_mode": "drop_objects",
    "verification_mode": "catalog_query",
}


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive the wrong-object-type cluster and expected_status."""

    state = a.get("target_state", "target_exists")
    ic = a.get("invalid_combination", "none")
    # wrong-object-type cluster: target_state / invalid_combination
    if state == "wrong_object_type" or ic == "object_type_mismatch":
        a["target_state"] = "wrong_object_type"
        a["invalid_combination"] = "object_type_mismatch"
    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: LockFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    if len(assignments) != len(set(assignments)):
        raise LockFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: LockFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise LockFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_lock_factor_loop_plan(
    repository_root: Path,
) -> LockFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_lock_factor_loop_obligations(root)
    cases: list[LockFactorCase] = []
    delegated: list[LockFactorObligation] = []
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
            LockFactorCase(
                ordinal=ordinal,
                case_id=f"LOCK{ordinal:05d}",
                sql_filename=f"LOCK{ordinal:05d}.sql",
                object_prefix=f"lock_{ordinal:05d}_",
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
    plan = LockFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 46 or len(plan.delegated) != 0:
        raise LockFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 46:
        raise LockFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 46:
        raise LockFactorLoopError("duplicate SQL filename")
    return plan


def compile_lock_factor_loop_obligations(
    repository_root: Path,
) -> tuple[LockFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = _compile_canonical_obligations(root)
    rows = tuple(
        LockFactorObligation(
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
        raise LockFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise LockFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"SFV": 46}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise LockFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise LockFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"} for row in rows
    ) != 46:
        raise LockFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(row.disposition not in allowed_dispositions for row in rows):
        raise LockFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "LockFactorLoopError",
    "LockFactorObligation",
    "LockFactorCase",
    "LockFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_lock_factor_loop_obligations",
    "build_lock_factor_loop_plan",
    "_obligation_multiset_sha256",
]
