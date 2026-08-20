"""Factor-value-loop obligation ledger for PostgreSQL 18.4 PREPARE.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``PREPARE`` (prepare a statement for execution).  The statement has a
single official synopsis branch: ``PREPARE name [ ( data_type [, ...] ) ]
AS statement`` with parameter and body forms.  The statement operates on
session-scoped prepared statements catalogued in
``pg_catalog.pg_prepared_statements`` (not a ``pg_class`` relation), so
column/table/relation coverage is ``not_applicable`` and there is no
``INV`` block.

PREPARE fixtures may ``CREATE TABLE`` (to ``PREPARE`` a
``SELECT``/``INSERT`` against), so the render emits a ``DROP TABLE IF
EXISTS`` bookend covering the full table vocabulary.  Cleanup uses
``DEALLOCATE ALL`` plus ``DROP TABLE``/``DROP SCHEMA``.

Each local obligation becomes exactly one regress program.  The 41
canonical ``SFV`` rows are loaded from the shipped applicability universe.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class PrepareFactorLoopError(ValueError):
    """Raised when a frozen PREPARE obligation input drifts."""


@dataclass(frozen=True)
class PrepareGrammarAction:
    """One official target action form of the PREPARE synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class PrepareFactorObligation:
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
class PrepareFactorCase:
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
class PrepareFactorLoopPlan:
    obligations: tuple[PrepareFactorObligation, ...]
    cases: tuple[PrepareFactorCase, ...]
    delegated: tuple[PrepareFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-prepare.html).
_BRANCH_DEFINE = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-prepare"

_REPRESENTATIVE_ACTION = "prepare_statement"


def _canonical_consumer(row) -> str:
    """Map a canonical factor value to its target consumer action."""

    if row.factor == "expected_status":
        if row.value == "failure":
            return "prepare_failure"
        return "prepare_statement"
    if row.factor == "prepared_state":
        if row.value == "missing":
            return "prepare_missing"
        if row.value == "deallocated":
            return "prepare_already_deallocated"
        if row.value == "duplicate_name":
            return "prepare_duplicate"
        return "prepare_statement"
    if row.factor == "prepared_name_shape":
        if row.value == "all_prepared_statements":
            return "prepare_all"
        if row.value == "missing_name":
            return "prepare_missing_name"
        if row.value == "quoted_identifier":
            return "prepare_quoted"
        return "prepare_statement"
    if row.factor == "argument_shape":
        if row.value == "too_few_arguments":
            return "prepare_too_few_args"
        if row.value == "too_many_arguments":
            return "prepare_too_many_args"
        if row.value == "wrong_type_arguments":
            return "prepare_wrong_type_args"
        return "prepare_statement"
    if row.factor == "lifecycle_boundary":
        if row.value == "execute_after_deallocate":
            return "prepare_execute_after"
        if row.value == "deallocate_all":
            return "prepare_all_boundary"
        return "prepare_statement"
    if row.factor == "invalid_combination":
        if row.value == "syntax_valid_semantic_error":
            return "prepare_semantic_error"
        if row.value == "object_type_mismatch":
            return "prepare_type_mismatch"
        return "prepare_statement"
    if row.factor == "dependency_state":
        if row.value == "missing_dependency":
            return "prepare_missing_dependency"
        return "prepare_statement"
    return _REPRESENTATIVE_ACTION


# Canonical (factor, value) pairs that the declared matrix marks as
# failure (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset({("expected_status", "failure")})

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
# Extra entries (beyond _SFV_FAILURE_VALUES) are consumed by the extension
# module's crossed-negative attribution; the baseline only looks up the
# expected_status=failure entry.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "26000",
        "prepare_declared_failure_provisional",
    ),
    ("prepared_state", "missing"): (
        "26000",
        "prepare_missing_statement_provisional",
    ),
    ("prepared_state", "deallocated"): (
        "26000",
        "prepare_already_deallocated_provisional",
    ),
    ("argument_shape", "too_few_arguments"): (
        "22023",
        "too_few_arguments_provisional",
    ),
    ("argument_shape", "too_many_arguments"): (
        "22023",
        "too_many_arguments_provisional",
    ),
    ("argument_shape", "wrong_type_arguments"): (
        "42804",
        "wrong_type_arguments_provisional",
    ),
    ("dependency_state", "missing_dependency"): (
        "42P01",
        "missing_dependency_provisional",
    ),
    ("invalid_combination", "syntax_valid_semantic_error"): (
        "42601",
        "semantic_error_provisional",
    ),
    ("invalid_combination", "object_type_mismatch"): (
        "42809",
        "object_type_mismatch_provisional",
    ),
    ("lifecycle_boundary", "execute_after_deallocate"): (
        "26000",
        "execute_after_deallocate_provisional",
    ),
}


def _load_grammar_actions() -> tuple[PrepareGrammarAction, ...]:
    """Freeze every PREPARE synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "prepare_statement",
            _BRANCH_DEFINE,
            "PREPARE name [ ( data_type [, ...] ) ] AS statement",
            "synopsis-prepare-statement",
        ),
    )
    actions = [
        PrepareGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise PrepareFactorLoopError(
            "prepare action count drift"
        )
    return tuple(actions)


def _compile_grammar_obligations() -> (
    list[PrepareFactorObligation]
):
    rows: list[PrepareFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            PrepareFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"PREPARE-GRM|{action.grammar_branch_id}|"
                    f"{action.action_id}|target_form|"
                    f"{action.action_id}"
                ),
                kind="GRM",
                factor_key="target_form",
                value=action.action_id,
                consumer_action_id=action.action_id,
                disposition="covered",
                source_locator=action.source_locator,
            )
        )
    if len(rows) != 1:
        raise PrepareFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[PrepareFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("prepare")
    if len(catalog_rows) != 41:
        raise PrepareFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[PrepareFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            PrepareFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"PREPARE-SFV|{row.row_id}|{consumer}"
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
    rows: tuple[PrepareFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"prepare-factor-obligations-v1\n"
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


# Dense baseline defaults (all positive factor values).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_1",
    "expected_status": "success",
    "prepared_state": "exists",
    "parameter_shape": "none",
    "prepared_statement_body": "select_statement",
    "prepared_name_shape": "plain_identifier",
    "argument_shape": "none",
    "dependency_state": "ready",
    "transaction_context": "outside_transaction",
    "invalid_combination": "none",
    "lifecycle_boundary": "prepare_execute_deallocate",
    "verification_mode": "catalog_query",
    "cleanup_mode": "rollback",
}


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive expected_status from the failure count."""

    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _baseline_assignments(
    obligation: PrepareFactorObligation,
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
        raise PrepareFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: PrepareFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise PrepareFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_prepare_factor_loop_plan(
    repository_root: Path,
) -> PrepareFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_prepare_factor_loop_obligations(root)
    cases: list[PrepareFactorCase] = []
    delegated: list[PrepareFactorObligation] = []
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
            PrepareFactorCase(
                ordinal=ordinal,
                case_id=f"PREPARE{ordinal:05d}",
                sql_filename=f"PREPARE{ordinal:05d}.sql",
                object_prefix=f"prepare_{ordinal:05d}_",
                primary_obligation_id=obligation.obligation_id,
                kind=obligation.kind,
                factor_key=obligation.factor_key,
                factor_value=obligation.value,
                consumer_action_id=obligation.consumer_action_id,
                outcome=outcome,
                expected_sqlstate=sqlstate,
                expected_failure_reason=failure_reason,
                baseline_assignments=_baseline_assignments(
                    obligation
                ),
                execution_profile="serial_sql",
            )
        )
    plan = PrepareFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 42 or len(plan.delegated) != 0:
        raise PrepareFactorLoopError(
            "factor loop plan count drift"
        )
    if (
        len({row.primary_obligation_id for row in plan.cases})
        != 42
    ):
        raise PrepareFactorLoopError(
            "local obligation mapping drift"
        )
    if (
        len({row.sql_filename for row in plan.cases}) != 42
    ):
        raise PrepareFactorLoopError(
            "duplicate SQL filename"
        )
    return plan


def compile_prepare_factor_loop_obligations(
    repository_root: Path,
) -> tuple[PrepareFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        PrepareFactorObligation(
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
    if len(rows) != 42:
        raise PrepareFactorLoopError(
            "obligation count drift"
        )
    if len({row.obligation_id for row in rows}) != len(rows):
        raise PrepareFactorLoopError(
            "duplicate obligation id"
        )
    expected_kind_counts = {"GRM": 1, "SFV": 41}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise PrepareFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise PrepareFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 42:
        raise PrepareFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise PrepareFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "PrepareFactorLoopError",
    "PrepareGrammarAction",
    "PrepareFactorObligation",
    "PrepareFactorCase",
    "PrepareFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_prepare_factor_loop_obligations",
    "build_prepare_factor_loop_plan",
    "_obligation_multiset_sha256",
    "_BASELINE_DEFAULTS",
]
