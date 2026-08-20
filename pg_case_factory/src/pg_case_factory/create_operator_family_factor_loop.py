"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE OPERATOR FAMILY.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE OPERATOR FAMILY``.  CREATE OPERATOR FAMILY is a PostgreSQL
schema-level DDL statement with a single official synopsis branch:
``CREATE OPERATOR FAMILY name USING index_method``.  There is no ``IF NOT
EXISTS`` clause and no ``OR REPLACE`` form.

The statement touches the ``pg_catalog.pg_opfamily`` catalog row (not a
``pg_class`` relation), so column/table/relation coverage is
``not_applicable`` and there is no ``INV`` block.  CREATE OPERATOR FAMILY
does not create tables, so the bookend (DROP TABLE IF EXISTS) is never
emitted.

Each local obligation becomes exactly one regress program.  The 30
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


class CreateOperatorFamilyFactorLoopError(ValueError):
    """Raised when a frozen CREATE OPERATOR FAMILY obligation input drifts."""


@dataclass(frozen=True)
class CreateOperatorFamilyGrammarAction:
    """One official target action form of the CREATE OPERATOR FAMILY synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateOperatorFamilyFactorObligation:
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
class CreateOperatorFamilyFactorCase:
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
class CreateOperatorFamilyFactorLoopPlan:
    obligations: tuple[CreateOperatorFamilyFactorObligation, ...]
    cases: tuple[CreateOperatorFamilyFactorCase, ...]
    delegated: tuple[CreateOperatorFamilyFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-createopfamily.html).
_BRANCH_1 = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createopfamily"

# The single representative define action used as the baseline consumer
# for every canonical factor (CREATE OPERATOR FAMILY has one synopsis form).
_REPRESENTATIVE_ACTION = "create_opfamily"


def _canonical_consumer(row) -> str:
    """CREATE OPERATOR FAMILY has one synopsis form -> one consumer action."""

    if row.factor == "statement_branch":
        if row.value != "branch_1":
            raise CreateOperatorFamilyFactorLoopError(
                f"unknown statement branch value: {row.value}"
            )
        return _REPRESENTATIVE_ACTION
    return _REPRESENTATIVE_ACTION


# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("target_object_state", "exists"),
        ("target_object_state", "exists_conflict"),
        ("privilege_context", "insufficient_privilege"),
        ("dependency_state", "missing_dependency"),
        ("invalid_combination", "syntax_valid_semantic_error"),
        ("ownership_boundary", "non_privileged"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42710",
        "duplicate_operator_family_provisional",
    ),
    ("target_object_state", "exists"): (
        "42710",
        "duplicate_operator_family_provisional",
    ),
    ("target_object_state", "exists_conflict"): (
        "42710",
        "duplicate_operator_family_provisional",
    ),
    ("privilege_context", "insufficient_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("ownership_boundary", "non_privileged"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("dependency_state", "missing_dependency"): (
        "3F000",
        "invalid_schema_name_provisional",
    ),
    ("invalid_combination", "syntax_valid_semantic_error"): (
        "42704",
        "undefined_access_method_provisional",
    ),
}


def _load_grammar_actions() -> (
    tuple[CreateOperatorFamilyGrammarAction, ...]
):
    """Freeze every CREATE OPERATOR FAMILY synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "create_opfamily",
            _BRANCH_1,
            "CREATE OPERATOR FAMILY name USING index_method",
            "synopsis-create-opfamily",
        ),
    )
    actions = [
        CreateOperatorFamilyGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise CreateOperatorFamilyFactorLoopError(
            "create operator family action count drift"
        )
    return tuple(actions)


def _compile_grammar_obligations() -> (
    list[CreateOperatorFamilyFactorObligation]
):
    rows: list[CreateOperatorFamilyFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateOperatorFamilyFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"COF-GRM|{action.grammar_branch_id}|"
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
        raise CreateOperatorFamilyFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateOperatorFamilyFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_operator_family")
    if len(catalog_rows) != 30:
        raise CreateOperatorFamilyFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[CreateOperatorFamilyFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateOperatorFamilyFactorObligation(
                ordinal=0,
                obligation_id=f"COF-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreateOperatorFamilyFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-operator-family-factor-obligations-v1\n"
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


# Branch action -> grammar branch id used by the renderer.
_ACTION_BRANCH = {
    "create_opfamily": _BRANCH_1,
}

# Dense baseline defaults (all positive factor values).  Boundary factors
# are derived in :func:`_derive_overlapping_factors`.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_1,
    "target_object_state": "absent",
    "expected_status": "success",
    "privilege_context": "superuser",
    "name_shape": "plain_identifier",
    "dependency_state": "ready",
    "index_method_shape": "btree",
    "invalid_combination": "none",
    "ownership_boundary": "superuser",
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
    """Derive boundary factors and expected_status from primary values.

    CREATE OPERATOR FAMILY has no ``IF NOT EXISTS`` clause, so a pre-existing
    target object is always a duplicate (``42710``).  ``expected_status =
    failure`` resolves to the representative duplicate scenario.
    ``privilege_context`` and ``ownership_boundary`` describe the same
    privilege boundary and are kept in sync.
    """

    # --- expected_status=failure -> representative duplicate ---
    es = a.get("expected_status", "success")
    if es == "failure":
        a["target_object_state"] = "exists"

    # --- target_object_state=exists/exists_conflict -> expected_status ---
    tos = a.get("target_object_state", "absent")
    if tos in ("exists", "exists_conflict"):
        a["expected_status"] = "failure"

    # --- privilege_context <-> ownership_boundary ---
    priv = a.get("privilege_context", "superuser")
    if priv == "insufficient_privilege":
        a["ownership_boundary"] = "non_privileged"
    own = a.get("ownership_boundary", "superuser")
    if own == "non_privileged":
        a["privilege_context"] = "insufficient_privilege"

    # --- Derive expected_status from failure count ---
    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _baseline_assignments(
    obligation: CreateOperatorFamilyFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["statement_branch"] = _ACTION_BRANCH[
        obligation.consumer_action_id
    ]
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    failures = _count_baseline_failures(assignments)
    assignments["expected_status"] = (
        "failure" if failures > 0 else "success"
    )
    if len(assignments) != len(set(assignments)):
        raise CreateOperatorFamilyFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateOperatorFamilyFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateOperatorFamilyFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_operator_family_factor_loop_plan(
    repository_root: Path,
) -> CreateOperatorFamilyFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_operator_family_factor_loop_obligations(root)
    cases: list[CreateOperatorFamilyFactorCase] = []
    delegated: list[CreateOperatorFamilyFactorObligation] = []
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
            CreateOperatorFamilyFactorCase(
                ordinal=ordinal,
                case_id=f"CREATEOPERATORFAMILY{ordinal:05d}",
                sql_filename=f"CREATEOPERATORFAMILY{ordinal:05d}.sql",
                object_prefix=f"createoperatorfamily_{ordinal:05d}_",
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
    plan = CreateOperatorFamilyFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 31 or len(plan.delegated) != 0:
        raise CreateOperatorFamilyFactorLoopError(
            "factor loop plan count drift"
        )
    if len({row.primary_obligation_id for row in plan.cases}) != 31:
        raise CreateOperatorFamilyFactorLoopError(
            "local obligation mapping drift"
        )
    if len({row.sql_filename for row in plan.cases}) != 31:
        raise CreateOperatorFamilyFactorLoopError("duplicate SQL filename")
    return plan


def compile_create_operator_family_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateOperatorFamilyFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateOperatorFamilyFactorObligation(
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
    if len(rows) != 31:
        raise CreateOperatorFamilyFactorLoopError(
            "obligation count drift"
        )
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateOperatorFamilyFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 30}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateOperatorFamilyFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateOperatorFamilyFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 31:
        raise CreateOperatorFamilyFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreateOperatorFamilyFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "CreateOperatorFamilyFactorLoopError",
    "CreateOperatorFamilyGrammarAction",
    "CreateOperatorFamilyFactorObligation",
    "CreateOperatorFamilyFactorCase",
    "CreateOperatorFamilyFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_create_operator_family_factor_loop_obligations",
    "build_create_operator_family_factor_loop_plan",
    "_obligation_multiset_sha256",
]
