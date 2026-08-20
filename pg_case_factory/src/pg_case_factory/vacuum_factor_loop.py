"""Factor-value-loop obligation ledger for PostgreSQL 18.4 VACUUM.

This module compiles the marginal ``SFV`` obligation ledger for
``VACUUM``.  VACUUM is a PostgreSQL utility statement that
garbage-collects and optionally analyzes a database.  The official
synopsis has two top-level forms (``VACUUM [ ( option [, ...] ) ]
[table_and_columns [, ...]]`` and ``VACUUM [ FULL ] [ FREEZE ] [
VERBOSE ] [ ANALYZE ] [ table_and_columns [, ...] ]``); the catalog
declares a single ``statement_branch`` value (``branch_1``), so every
one of the 47 declared factor values is a single ``SFV`` obligation (no
``GRM`` block, no ``INV`` block, no ``RISK``).  Each local obligation
becomes exactly one regress program, so the baseline case count equals
the obligation count (47) with zero delegated rows.

VACUUM operates on an existing ``pg_class`` table relation.  Cases that
exercise a success path CREATE the fixture table as setup, so the
bookend contract (DROP TABLE IF EXISTS first/last) applies to those
cases.  Cases that target a non-existent table create no fixture
table, so the bookend is satisfied vacuously.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class VacuumFactorLoopError(ValueError):
    """Raised when a frozen VACUUM obligation input drifts."""


@dataclass(frozen=True)
class VacuumFactorObligation:
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
class VacuumFactorCase:
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
class VacuumFactorLoopPlan:
    obligations: tuple[VacuumFactorObligation, ...]
    cases: tuple[VacuumFactorCase, ...]
    delegated: tuple[VacuumFactorObligation, ...]
    obligation_multiset_sha256: str


_DOC_SOURCE = "postgresql-18.4-doc:sql-vacuum"

# Representative consumer used as the baseline consumer for canonical
# factor values that are not bound to one specific value-dependent axis.
# VACUUM t (minimal, plain identifier, target exists) is the simplest
# success branch.
_REPRESENTATIVE_CONSUMER = "vacuum_option_minimal"

# statement_branch canonical value -> consumer.
_STATEMENT_BRANCH_CONSUMER = {
    "branch_1": "vacuum_branch_1",
}

# option_shape value -> consumer.
_OPTION_SHAPE_CONSUMER = {
    "minimal": "vacuum_option_minimal",
    "boolean_options": "vacuum_option_boolean",
    "resource_options": "vacuum_option_resource",
    "verbose_or_format": "vacuum_option_verbose",
}

# target_name_shape value -> consumer.
_TARGET_NAME_CONSUMER = {
    "all_or_database_wide": "vacuum_target_all_database",
    "only_relation": "vacuum_target_relation",
    "plain_identifier": "vacuum_target_plain",
    "quoted_identifier": "vacuum_target_quoted",
    "relation_and_descendants": "vacuum_target_descendants",
    "schema_qualified": "vacuum_target_schema_qualified",
}

# target_state value -> consumer.
_TARGET_STATE_CONSUMER = {
    "database_wide": "vacuum_state_database_wide",
    "target_exists": "vacuum_state_exists",
    "target_missing": "vacuum_state_missing",
    "wrong_object_type": "vacuum_state_wrong_type",
}

# environment_context value -> consumer.
_ENVIRONMENT_CONSUMER = {
    "external_resource_required": "vacuum_environment",
    "normal_session": "vacuum_environment",
    "outside_transaction_required": "vacuum_environment",
    "transaction_block": "vacuum_env_transaction_block",
}

# privilege_context value -> consumer.
_PRIVILEGE_CONSUMER = {
    "granted_role": "vacuum_privilege_granted",
    "insufficient_privilege": "vacuum_privilege_denied",
    "owner": "vacuum_privilege_owner",
}

# Canonical factor -> the consumer used when the value is not bound to a
# value-dependent axis.  Factors whose consumer depends on the value
# (statement_branch, option_shape, target_name_shape, target_state,
# environment_context, privilege_context) are resolved in
# :func:`_canonical_consumer`.
_SFV_FACTOR_CONSUMER = {
    "statement_branch": "vacuum_branch_1",
    "input_output_shape": "vacuum_io_shape",
    "verification_mode": "vacuum_verification",
    "cleanup_mode": "vacuum_cleanup",
    "resource_boundary": "vacuum_resource_boundary",
    "execution_mode": "vacuum_execution",
    "invalid_combination": "vacuum_invalid_combo",
    "expected_status": "vacuum_expected_status",
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates - the DB phase verifies on
# PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("target_state", "target_missing"),
        ("target_state", "wrong_object_type"),
        ("privilege_context", "insufficient_privilege"),
        ("environment_context", "transaction_block"),
        ("invalid_combination", "object_type_mismatch"),
        ("invalid_combination", "syntax_valid_semantic_error"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42P01",
        "vacuum_failure_marker_provisional",
    ),
    ("target_state", "target_missing"): (
        "42P01",
        "vacuum_target_missing_provisional",
    ),
    ("target_state", "wrong_object_type"): (
        "42809",
        "vacuum_wrong_object_type_provisional",
    ),
    ("privilege_context", "insufficient_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("environment_context", "transaction_block"): (
        "25001",
        "vacuum_transaction_block_forbidden_provisional",
    ),
    ("invalid_combination", "object_type_mismatch"): (
        "42809",
        "vacuum_object_type_mismatch_provisional",
    ),
    ("invalid_combination", "syntax_valid_semantic_error"): (
        "42703",
        "vacuum_semantic_error_provisional",
    ),
}


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise VacuumFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "option_shape":
        try:
            return _OPTION_SHAPE_CONSUMER[row.value]
        except KeyError as exc:
            raise VacuumFactorLoopError(
                f"unknown option_shape value: {row.value}"
            ) from exc
    if row.factor == "target_name_shape":
        try:
            return _TARGET_NAME_CONSUMER[row.value]
        except KeyError as exc:
            raise VacuumFactorLoopError(
                f"unknown target_name_shape value: {row.value}"
            ) from exc
    if row.factor == "target_state":
        try:
            return _TARGET_STATE_CONSUMER[row.value]
        except KeyError as exc:
            raise VacuumFactorLoopError(
                f"unknown target_state value: {row.value}"
            ) from exc
    if row.factor == "environment_context":
        try:
            return _ENVIRONMENT_CONSUMER[row.value]
        except KeyError as exc:
            raise VacuumFactorLoopError(
                f"unknown environment_context value: {row.value}"
            ) from exc
    if row.factor == "privilege_context":
        try:
            return _PRIVILEGE_CONSUMER[row.value]
        except KeyError as exc:
            raise VacuumFactorLoopError(
                f"unknown privilege_context value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise VacuumFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[VacuumFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("vacuum")
    if len(catalog_rows) != 47:
        raise VacuumFactorLoopError("canonical obligation count drift")
    rows: list[VacuumFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            VacuumFactorObligation(
                ordinal=0,
                obligation_id=f"VACUUM-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[VacuumFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"vacuum-factor-obligations-v1\n")
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
    "option_shape": "minimal",
    "target_name_shape": "plain_identifier",
    "target_state": "target_exists",
    "environment_context": "normal_session",
    "privilege_context": "owner",
    "input_output_shape": "none",
    "verification_mode": "catalog_query",
    "cleanup_mode": "drop_objects",
    "resource_boundary": "small_relation",
    "execution_mode": "executes_statement",
    "invalid_combination": "none",
    "expected_status": "success",
}


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive database-wide coupling and expected_status from failures."""

    ts = a.get("target_state", "target_exists")
    tns = a.get("target_name_shape", "plain_identifier")

    # database-wide coupling: target_state=database_wide and
    # target_name_shape=all_or_database_wide describe the same
    # (no-table, database-wide) scenario; keep them consistent so a
    # single scenario is not double-counted.
    if ts == "database_wide" or tns == "all_or_database_wide":
        a["target_state"] = "database_wide"
        a["target_name_shape"] = "all_or_database_wide"

    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _baseline_assignments(
    obligation: VacuumFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    # Re-derive in case the primary set target_state/target_name_shape
    # to a database-wide value that constrains the other.
    _derive_overlapping_factors(assignments)
    if len(assignments) != len(set(assignments)):
        raise VacuumFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: VacuumFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise VacuumFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_vacuum_factor_loop_plan(
    repository_root: Path,
) -> VacuumFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_vacuum_factor_loop_obligations(root)
    cases: list[VacuumFactorCase] = []
    delegated: list[VacuumFactorObligation] = []
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
            VacuumFactorCase(
                ordinal=ordinal,
                case_id=f"VACUUM{ordinal:05d}",
                sql_filename=f"VACUUM{ordinal:05d}.sql",
                object_prefix=f"vacuum_{ordinal:05d}_",
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
    plan = VacuumFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 47 or len(plan.delegated) != 0:
        raise VacuumFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 47:
        raise VacuumFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 47:
        raise VacuumFactorLoopError("duplicate SQL filename")
    return plan


def compile_vacuum_factor_loop_obligations(
    repository_root: Path,
) -> tuple[VacuumFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = _compile_canonical_obligations(root)
    rows = tuple(
        VacuumFactorObligation(
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
    if len(rows) != 47:
        raise VacuumFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise VacuumFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"SFV": 47}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise VacuumFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise VacuumFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"} for row in rows
    ) != 47:
        raise VacuumFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(row.disposition not in allowed_dispositions for row in rows):
        raise VacuumFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "VacuumFactorLoopError",
    "VacuumFactorObligation",
    "VacuumFactorCase",
    "VacuumFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_vacuum_factor_loop_obligations",
    "build_vacuum_factor_loop_plan",
    "_obligation_multiset_sha256",
]
