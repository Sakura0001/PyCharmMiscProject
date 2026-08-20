"""Factor-value-loop obligation ledger for PostgreSQL 18.4 ANALYZE.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``ANALYZE``.  ANALYZE is a PostgreSQL utility statement with a single
official synopsis branch (``branch_1``): ``ANALYZE [ ( option [, ...] ) ]
[ table_and_columns [, ...] ]``.  The statement collects statistics about
a database and touches the ``pg_catalog.pg_statistic`` catalog rows (not
a ``pg_class`` relation), so column/table/relation coverage is
``not_applicable`` and there is no ``INV`` block.

Each local obligation becomes exactly one regress program.  ANALYZE is a
metadata/IO-oriented statement: it can run inside a transaction block
(unlike VACUUM), so ``environment_context=transaction_block`` is a success
path.  The inventory declares 13 factors / 47 factor values; together
with the single GRM synopsis obligation the ledger has 48 local cases.

The grammar ledger is self-contained (there is no separate
``analyze_regress`` module): the 1 synopsis action is frozen inline.  The
47 canonical ``SFV`` rows are loaded from the shipped applicability
universe (``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class AnalyzeFactorLoopError(ValueError):
    """Raised when a frozen ANALYZE obligation input drifts."""


@dataclass(frozen=True)
class AnalyzeGrammarAction:
    """One official target action form of the ANALYZE synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class AnalyzeFactorObligation:
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
class AnalyzeFactorCase:
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
class AnalyzeFactorLoopPlan:
    obligations: tuple[AnalyzeFactorObligation, ...]
    cases: tuple[AnalyzeFactorCase, ...]
    delegated: tuple[AnalyzeFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-analyze.html).
_BRANCH_1 = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-analyze"

# ANALYZE has a single synopsis action; every factor value is observable
# through it.
_REPRESENTATIVE_ACTION = "analyze"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_1: "analyze",
}

# Canonical factor -> the action where the value is observable.  ANALYZE
# has one branch, so every factor is observable through ``analyze``.
_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "target_state": _REPRESENTATIVE_ACTION,
    "option_shape": _REPRESENTATIVE_ACTION,
    "execution_mode": _REPRESENTATIVE_ACTION,
    "target_name_shape": _REPRESENTATIVE_ACTION,
    "input_output_shape": _REPRESENTATIVE_ACTION,
    "environment_context": _REPRESENTATIVE_ACTION,
    "privilege_context": _REPRESENTATIVE_ACTION,
    "invalid_combination": _REPRESENTATIVE_ACTION,
    "resource_boundary": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("target_state", "target_missing"),
        ("target_state", "wrong_object_type"),
        ("privilege_context", "insufficient_privilege"),
        ("invalid_combination", "object_type_mismatch"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42P01",
        "analyze_declared_failure_provisional",
    ),
    ("target_state", "target_missing"): (
        "42P01",
        "undefined_table_provisional",
    ),
    ("target_state", "wrong_object_type"): (
        "42809",
        "wrong_object_type_provisional",
    ),
    ("privilege_context", "insufficient_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("invalid_combination", "object_type_mismatch"): (
        "42809",
        "wrong_object_type_provisional",
    ),
}


def _load_grammar_actions() -> tuple[AnalyzeGrammarAction, ...]:
    """Freeze every ANALYZE synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "analyze",
            _BRANCH_1,
            (
                "ANALYZE [ ( option [, ...] ) ] [ table_and_columns "
                "[, ...] ]"
            ),
            "synopsis-branch-1",
        ),
    )
    actions = [
        AnalyzeGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise AnalyzeFactorLoopError("analyze action count drift")
    return tuple(actions)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise AnalyzeFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise AnalyzeFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> list[AnalyzeFactorObligation]:
    rows: list[AnalyzeFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            AnalyzeFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"ANALYZE-GRM|{action.grammar_branch_id}|"
                    f"{action.action_id}|target_action|"
                    f"{action.action_id}"
                ),
                kind="GRM",
                factor_key="target_action",
                value=action.action_id,
                consumer_action_id=action.action_id,
                disposition="covered",
                source_locator=action.source_locator,
            )
        )
    if len(rows) != 1:
        raise AnalyzeFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[AnalyzeFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("analyze")
    if len(catalog_rows) != 47:
        raise AnalyzeFactorLoopError("canonical obligation count drift")
    rows: list[AnalyzeFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            AnalyzeFactorObligation(
                ordinal=0,
                obligation_id=f"ANALYZE-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[AnalyzeFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"analyze-factor-obligations-v1\n")
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


# Branch action -> grammar branch id used by the renderer.
_ACTION_BRANCH = {
    "analyze": _BRANCH_1,
}

# Dense baseline defaults (all positive factor values).  T5 boundary
# factors (invalid_combination, resource_boundary) that are NOT declared
# as failures are set to their success values here.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_1,
    "grammar_branch": _BRANCH_1,
    "target_action": "analyze",
    "expected_status": "success",
    "target_state": "target_exists",
    "option_shape": "minimal",
    "execution_mode": "metadata_only",
    "target_name_shape": "plain_identifier",
    "input_output_shape": "none",
    "environment_context": "normal_session",
    "privilege_context": "owner",
    "invalid_combination": "none",
    "resource_boundary": "small_relation",
    "verification_mode": "catalog_query",
    "cleanup_mode": "rollback",
}


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive expected_status and failure-trigger factors.

    When ``expected_status=failure`` or
    ``invalid_combination=object_type_mismatch`` is the primary factor,
    a real failure trigger (target_state) is attached so the rendered
    SQL actually reaches a PostgreSQL error check.  ``expected_status``
    is then derived from the failure count.
    """

    # expected_status=failure needs a real failure trigger.
    if a.get("expected_status") == "failure":
        a["target_state"] = "target_missing"
        a["target_name_shape"] = "plain_identifier"

    # invalid_combination=object_type_mismatch needs wrong_object_type.
    if a.get("invalid_combination") == "object_type_mismatch":
        a["target_state"] = "wrong_object_type"
        a["target_name_shape"] = "plain_identifier"

    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: AnalyzeFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["grammar_branch"] = _ACTION_BRANCH[
        obligation.consumer_action_id
    ]
    assignments["target_action"] = obligation.consumer_action_id
    assignments["statement_branch"] = _ACTION_BRANCH[
        obligation.consumer_action_id
    ]
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    if len(assignments) != len(set(assignments)):
        raise AnalyzeFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: AnalyzeFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise AnalyzeFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_analyze_factor_loop_plan(
    repository_root: Path,
) -> AnalyzeFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_analyze_factor_loop_obligations(root)
    cases: list[AnalyzeFactorCase] = []
    delegated: list[AnalyzeFactorObligation] = []
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
            AnalyzeFactorCase(
                ordinal=ordinal,
                case_id=f"ANALYZE{ordinal:05d}",
                sql_filename=f"ANALYZE{ordinal:05d}.sql",
                object_prefix=f"analyze_{ordinal:05d}_",
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
    plan = AnalyzeFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 48 or len(plan.delegated) != 0:
        raise AnalyzeFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 48:
        raise AnalyzeFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 48:
        raise AnalyzeFactorLoopError("duplicate SQL filename")
    return plan


def compile_analyze_factor_loop_obligations(
    repository_root: Path,
) -> tuple[AnalyzeFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        AnalyzeFactorObligation(
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
    if len(rows) != 48:
        raise AnalyzeFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise AnalyzeFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 47}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise AnalyzeFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise AnalyzeFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 48:
        raise AnalyzeFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise AnalyzeFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "AnalyzeFactorLoopError",
    "AnalyzeGrammarAction",
    "AnalyzeFactorObligation",
    "AnalyzeFactorCase",
    "AnalyzeFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_analyze_factor_loop_obligations",
    "build_analyze_factor_loop_plan",
    "_obligation_multiset_sha256",
]
