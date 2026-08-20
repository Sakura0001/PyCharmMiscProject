"""Factor-value-loop obligation ledger for PostgreSQL 18.4 REINDEX.

This module compiles the marginal ``SFV`` obligation ledger for
``REINDEX``.  REINDEX is a PostgreSQL maintenance utility that rebuilds
indexes.  The official synopsis has five top-level forms (``REINDEX
INDEX``, ``REINDEX TABLE``, ``REINDEX SCHEMA``, ``REINDEX DATABASE``,
``REINDEX SYSTEM``), each with optional ``VERBOSE``, parenthesised
options, and ``CONCURRENTLY``, yielding 83 declared factor values.

Like ``CLUSTER``, REINDEX has no ``GRM`` or ``RISK`` blocks: every one
of the 83 declared factor values is a single ``SFV`` obligation.  Each
local obligation becomes exactly one regress program, so the baseline
case count equals the obligation count (83) with zero delegated rows.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class ReindexFactorLoopError(ValueError):
    """Raised when a frozen REINDEX obligation input drifts."""


@dataclass(frozen=True)
class ReindexFactorObligation:
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
class ReindexFactorCase:
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
class ReindexFactorLoopPlan:
    obligations: tuple[ReindexFactorObligation, ...]
    cases: tuple[ReindexFactorCase, ...]
    delegated: tuple[ReindexFactorObligation, ...]
    obligation_multiset_sha256: str


_DOC_SOURCE = "postgresql-18.4-doc:sql-reindex"

_REPRESENTATIVE_BRANCH = "reindex_index"

_STATEMENT_BRANCH_CONSUMER = {
    "reindex_index": "reindex_index",
    "reindex_table": "reindex_table",
    "reindex_schema": "reindex_schema",
    "reindex_database": "reindex_database",
    "reindex_system": "reindex_system",
}

_PERMISSION_INSUFFICIENT_CONSUMER = {
    "non_owner_reindex": "reindex_index",
    "non_superuser_shared_catalog": "reindex_system",
    "none": "reindex_index",
}

_INVALID_COMBINATION_CONSUMER = {
    "concurrently_in_transaction": "reindex_index",
    "concurrently_with_exclusion_constraint": "reindex_index",
    "concurrently_with_system": "reindex_system",
    "database_name_mismatch": "reindex_database",
    "none": "reindex_index",
    "tablespace_on_system_relation": "reindex_system",
}

_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_BRANCH,
    "object_state": _REPRESENTATIVE_BRANCH,
    "expected_status": _REPRESENTATIVE_BRANCH,
    "concurrently_keyword": _REPRESENTATIVE_BRANCH,
    "option_concurrently": _REPRESENTATIVE_BRANCH,
    "option_tablespace": _REPRESENTATIVE_BRANCH,
    "option_verbose": _REPRESENTATIVE_BRANCH,
    "boolean_value": _REPRESENTATIVE_BRANCH,
    "permission": _REPRESENTATIVE_BRANCH,
    "name_shape": _REPRESENTATIVE_BRANCH,
    "index_method": _REPRESENTATIVE_BRANCH,
    "tablespace_dependency": _REPRESENTATIVE_BRANCH,
    "toast_indexes": _REPRESENTATIVE_BRANCH,
    "partition_behavior": _REPRESENTATIVE_BRANCH,
    "invalid_combination": _REPRESENTATIVE_BRANCH,
    "concurrent_failure": _REPRESENTATIVE_BRANCH,
    "syntax_error": _REPRESENTATIVE_BRANCH,
    "permission_insufficient": _REPRESENTATIVE_BRANCH,
    "verification_mode": _REPRESENTATIVE_BRANCH,
    "cleanup_mode": _REPRESENTATIVE_BRANCH,
}

_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("expected_status", "partial_success"),
        ("object_state", "not_exists"),
        ("name_shape", "missing_object"),
        ("permission", "insufficient_privilege"),
        ("permission", "non_owner"),
        ("permission_insufficient", "non_owner_reindex"),
        ("permission_insufficient", "non_superuser_shared_catalog"),
        ("invalid_combination", "concurrently_in_transaction"),
        ("invalid_combination", "concurrently_with_exclusion_constraint"),
        ("invalid_combination", "concurrently_with_system"),
        ("invalid_combination", "database_name_mismatch"),
        ("invalid_combination", "tablespace_on_system_relation"),
        ("syntax_error", "invalid_syntax"),
        ("concurrent_failure", "ccnew_suffix"),
        ("concurrent_failure", "ccold_suffix"),
        ("concurrent_failure", "invalid_index_leftover"),
        ("concurrent_failure", "suffixed_numeric_disambiguator"),
        ("concurrent_failure", "underscore_ccnew_suffix"),
        ("concurrent_failure", "underscore_ccold_suffix"),
    }
)

_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42P01",
        "reindex_failure_provisional",
    ),
    ("expected_status", "partial_success"): (
        "55006",
        "reindex_partial_success_provisional",
    ),
    ("object_state", "not_exists"): (
        "42704",
        "reindex_target_missing_provisional",
    ),
    ("name_shape", "missing_object"): (
        "42704",
        "reindex_target_missing_provisional",
    ),
    ("permission", "insufficient_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("permission", "non_owner"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("permission_insufficient", "non_owner_reindex"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("permission_insufficient", "non_superuser_shared_catalog"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("invalid_combination", "concurrently_in_transaction"): (
        "25001",
        "reindex_concurrently_in_transaction_provisional",
    ),
    ("invalid_combination", "concurrently_with_exclusion_constraint"): (
        "0A000",
        "reindex_concurrently_exclusion_constraint_provisional",
    ),
    ("invalid_combination", "concurrently_with_system"): (
        "0A000",
        "reindex_concurrently_system_provisional",
    ),
    ("invalid_combination", "database_name_mismatch"): (
        "42809",
        "reindex_database_name_mismatch_provisional",
    ),
    ("invalid_combination", "tablespace_on_system_relation"): (
        "0A000",
        "reindex_tablespace_system_relation_provisional",
    ),
    ("syntax_error", "invalid_syntax"): (
        "42601",
        "reindex_syntax_error_provisional",
    ),
    ("concurrent_failure", "ccnew_suffix"): (
        "55006",
        "reindex_concurrent_failure_provisional",
    ),
    ("concurrent_failure", "ccold_suffix"): (
        "55006",
        "reindex_concurrent_failure_provisional",
    ),
    ("concurrent_failure", "invalid_index_leftover"): (
        "55006",
        "reindex_concurrent_failure_provisional",
    ),
    ("concurrent_failure", "suffixed_numeric_disambiguator"): (
        "55006",
        "reindex_concurrent_failure_provisional",
    ),
    ("concurrent_failure", "underscore_ccnew_suffix"): (
        "55006",
        "reindex_concurrent_failure_provisional",
    ),
    ("concurrent_failure", "underscore_ccold_suffix"): (
        "55006",
        "reindex_concurrent_failure_provisional",
    ),
}

_INVALID_COMBINATION_DERIVATION: dict[str, dict[str, str]] = {
    "concurrently_in_transaction": {"concurrently_keyword": "true"},
    "concurrently_with_exclusion_constraint": {
        "concurrently_keyword": "true",
        "index_method": "exclusion_constraint",
    },
    "concurrently_with_system": {
        "statement_branch": "reindex_system",
        "concurrently_keyword": "true",
    },
    "database_name_mismatch": {"statement_branch": "reindex_database"},
    "tablespace_on_system_relation": {
        "statement_branch": "reindex_system",
        "option_tablespace": "present_custom",
    },
    "none": {},
}

_CONCURRENT_FAILURE_DERIVATION: dict[str, dict[str, str]] = {
    "ccnew_suffix": {"concurrently_keyword": "true"},
    "ccold_suffix": {"concurrently_keyword": "true"},
    "invalid_index_leftover": {"concurrently_keyword": "true"},
    "suffixed_numeric_disambiguator": {"concurrently_keyword": "true"},
    "underscore_ccnew_suffix": {"concurrently_keyword": "true"},
    "underscore_ccold_suffix": {"concurrently_keyword": "true"},
    "none": {},
}


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise ReindexFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "permission_insufficient":
        try:
            return _PERMISSION_INSUFFICIENT_CONSUMER[row.value]
        except KeyError as exc:
            raise ReindexFactorLoopError(
                f"unknown permission_insufficient value: {row.value}"
            ) from exc
    if row.factor == "invalid_combination":
        try:
            return _INVALID_COMBINATION_CONSUMER[row.value]
        except KeyError as exc:
            raise ReindexFactorLoopError(
                f"unknown invalid_combination value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise ReindexFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[ReindexFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("reindex")
    if len(catalog_rows) != 83:
        raise ReindexFactorLoopError("canonical obligation count drift")
    rows: list[ReindexFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            ReindexFactorObligation(
                ordinal=0,
                obligation_id=f"REINDEX-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[ReindexFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"reindex-factor-obligations-v1\n")
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


_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "reindex_index",
    "object_state": "exists",
    "expected_status": "success",
    "concurrently_keyword": "false",
    "option_concurrently": "absent",
    "option_tablespace": "absent",
    "option_verbose": "absent",
    "boolean_value": "omitted_default",
    "permission": "owner",
    "name_shape": "plain_identifier",
    "index_method": "btree",
    "tablespace_dependency": "no_tablespace_move",
    "toast_indexes": "not_applicable",
    "partition_behavior": "non_partitioned",
    "invalid_combination": "none",
    "concurrent_failure": "none",
    "syntax_error": "none",
    "permission_insufficient": "none",
    "verification_mode": "catalog_validity_check",
    "cleanup_mode": "drop_invalid_index",
}


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values."""

    ic = a.get("invalid_combination", "none")
    if ic in _INVALID_COMBINATION_DERIVATION:
        a.update(_INVALID_COMBINATION_DERIVATION[ic])

    cf = a.get("concurrent_failure", "none")
    if cf in _CONCURRENT_FAILURE_DERIVATION:
        a.update(_CONCURRENT_FAILURE_DERIVATION[cf])

    pi = a.get("permission_insufficient", "none")
    if pi == "non_superuser_shared_catalog":
        a["permission"] = "non_owner"
        a["statement_branch"] = "reindex_system"

    os_ = a.get("object_state", "exists")
    ns = a.get("name_shape", "plain_identifier")
    if os_ == "not_exists" or ns == "missing_object":
        a["object_state"] = "not_exists"
        a["name_shape"] = "missing_object"

    pl = a.get("permission", "owner")
    if pl in ("insufficient_privilege", "non_owner"):
        a["permission_insufficient"] = "non_owner_reindex"
    elif pi == "non_owner_reindex":
        a["permission"] = "insufficient_privilege"

    current = a.get("expected_status", "success")
    if current != "partial_success":
        failures = _count_baseline_failures(a)
        a["expected_status"] = "failure" if failures > 0 else "success"


def _baseline_assignments(
    obligation: ReindexFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    if len(assignments) != len(set(assignments)):
        raise ReindexFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: ReindexFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise ReindexFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_reindex_factor_loop_plan(
    repository_root: Path,
) -> ReindexFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_reindex_factor_loop_obligations(root)
    cases: list[ReindexFactorCase] = []
    delegated: list[ReindexFactorObligation] = []
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
            ReindexFactorCase(
                ordinal=ordinal,
                case_id=f"REINDEX{ordinal:05d}",
                sql_filename=f"REINDEX{ordinal:05d}.sql",
                object_prefix=f"reindex_{ordinal:05d}_",
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
    plan = ReindexFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 83 or len(plan.delegated) != 0:
        raise ReindexFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 83:
        raise ReindexFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 83:
        raise ReindexFactorLoopError("duplicate SQL filename")
    return plan


def compile_reindex_factor_loop_obligations(
    repository_root: Path,
) -> tuple[ReindexFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = _compile_canonical_obligations(root)
    rows = tuple(
        ReindexFactorObligation(
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
    if len(rows) != 83:
        raise ReindexFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise ReindexFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"SFV": 83}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise ReindexFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise ReindexFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"} for row in rows
    ) != 83:
        raise ReindexFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(row.disposition not in allowed_dispositions for row in rows):
        raise ReindexFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "ReindexFactorLoopError",
    "ReindexFactorObligation",
    "ReindexFactorCase",
    "ReindexFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_reindex_factor_loop_obligations",
    "build_reindex_factor_loop_plan",
    "_obligation_multiset_sha256",
]
