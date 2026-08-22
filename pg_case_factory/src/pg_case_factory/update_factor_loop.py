"""Factor-value-loop obligation ledger for PostgreSQL 18.4 UPDATE.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``UPDATE``.  UPDATE is a PostgreSQL DML row-mutation statement with a
single official synopsis branch::

    [ WITH [ RECURSIVE ] with_query [, ...] ]
    UPDATE [ ONLY ] table_name [ * ] [ [ AS ] alias ]
        SET { column_name = { expression | DEFAULT } |
              ( column_name [, ...] ) = [ ROW ] ( { expression | DEFAULT } [, ...] ) |
              ( column_name [, ...] ) = ( sub-SELECT )
            } [, ...]
        [ FROM from_item [, ...] ]
        [ WHERE condition | WHERE CURRENT OF cursor_name ]
        [ RETURNING { * | output_expression [ [ AS ] output_name ] } [, ...] ]

It mutates a ``pg_class`` relation of kind ``r`` (a base table), so
``target_relation_coverage`` is applicable and the target state
(exists / missing / wrong_object_type) refers to the updated relation.

The 15 canonical factors and their values are frozen in the shipped
combination matrix ``update.yaml`` (the source of truth);
``factor_value_count`` (the sum of ``len(values)`` across all 15
factors) equals 49.  The ``GRM`` target action is synthesised from the
official synopsis branch and is NOT counted in ``factor_value_count``.
All 49 factor-value pairs — including ``statement_branch=branch_1`` —
are read from the shipped applicability catalog and become ``SFV``
obligations.  Hence ``GRM`` 1 + ``SFV`` 49 = 50 local obligations,
each materialised as exactly one regress program.

Each local obligation becomes exactly one regress program.  Because
UPDATE is a transactional DML statement and the inventory declares no
``transaction_outcome`` factor, there are no ``RISK`` obligations.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json

from .applicability import load_shipped_applicability_universe


class UpdateFactorLoopError(ValueError):
    """Raised when a frozen UPDATE obligation input drifts."""


@dataclass(frozen=True)
class UpdateGrammarAction:
    """One official target action form of the UPDATE synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class UpdateFactorObligation:
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
class UpdateFactorCase:
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
class UpdateFactorLoopPlan:
    obligations: tuple[UpdateFactorObligation, ...]
    cases: tuple[UpdateFactorCase, ...]
    delegated: tuple[UpdateFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-update.html).
_BRANCH_1 = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-update"
_STATEMENT_REF = "references/statements/dml/table/update.md"

# The single consumer action for all UPDATE factors.  Since UPDATE has
# only one branch, every factor's consumer is "update".
_REPRESENTATIVE_ACTION = "update"

_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "target_relation_state": _REPRESENTATIVE_ACTION,
    "data_or_query_shape": _REPRESENTATIVE_ACTION,
    "condition_shape": _REPRESENTATIVE_ACTION,
    "result_shape": _REPRESENTATIVE_ACTION,
    "with_clause": _REPRESENTATIVE_ACTION,
    "name_shape": _REPRESENTATIVE_ACTION,
    "expression_shape": _REPRESENTATIVE_ACTION,
    "dependency_state": _REPRESENTATIVE_ACTION,
    "privilege_context": _REPRESENTATIVE_ACTION,
    "invalid_combination": _REPRESENTATIVE_ACTION,
    "constraint_boundary": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target
# check and are rejected (provisional sqlstates -- DB phase verifies on
# PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("target_relation_state", "missing"),
        ("target_relation_state", "wrong_object_type"),
        ("dependency_state", "missing_dependency"),
        ("privilege_context", "insufficient_privilege"),
        ("invalid_combination", "syntax_valid_semantic_error"),
        ("invalid_combination", "object_type_mismatch"),
        ("constraint_boundary", "constraint_violation"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure
# value.  UPDATE targets a ``pg_class`` relation, so a missing target
# yields ``42P01`` (undefined_table) rather than a routine sqlstate.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42P01",
        "missing_target_relation_provisional",
    ),
    ("target_relation_state", "missing"): (
        "42P01",
        "missing_target_relation_provisional",
    ),
    ("target_relation_state", "wrong_object_type"): (
        "42809",
        "wrong_object_type_provisional",
    ),
    ("dependency_state", "missing_dependency"): (
        "42P01",
        "missing_dependency_provisional",
    ),
    ("privilege_context", "insufficient_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("invalid_combination", "syntax_valid_semantic_error"): (
        "42703",
        "syntax_valid_semantic_error_provisional",
    ),
    ("invalid_combination", "object_type_mismatch"): (
        "42809",
        "wrong_object_type_provisional",
    ),
    ("constraint_boundary", "constraint_violation"): (
        "23503",
        "foreign_key_violation_provisional",
    ),
}

# Canonical factor -> (tier, values) hardcoded verbatim from
# update.yaml ``factor_contract.factors``.  The sum of len(values) is
# exactly 49 (the frozen factor_value_count).
_CANONICAL_FACTORS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("statement_branch", "T1", ("branch_1",)),
    ("expected_status", "T1", ("success", "failure")),
    (
        "target_relation_state",
        "T1",
        ("exists", "missing", "wrong_object_type"),
    ),
    (
        "data_or_query_shape",
        "T1",
        ("minimal", "explicit_values", "query_source", "cte_source"),
    ),
    (
        "condition_shape",
        "T2",
        (
            "none",
            "simple_predicate",
            "join_or_match_condition",
            "cursor_or_conflict_target",
        ),
    ),
    (
        "result_shape",
        "T2",
        (
            "none",
            "returning_star",
            "returning_expression",
            "rowset_projection",
            "returning_old_new_aliases",
        ),
    ),
    ("with_clause", "T2", ("absent", "non_recursive", "recursive")),
    (
        "name_shape",
        "T3",
        (
            "plain_identifier",
            "schema_qualified",
            "quoted_identifier",
            "alias_used",
        ),
    ),
    (
        "expression_shape",
        "T3",
        ("literal", "column_reference", "function_call", "subquery_expression"),
    ),
    ("dependency_state", "T4", ("ready", "missing_dependency")),
    (
        "privilege_context",
        "T4",
        ("owner", "granted_role", "insufficient_privilege"),
    ),
    (
        "invalid_combination",
        "T5",
        ("none", "syntax_valid_semantic_error", "object_type_mismatch"),
    ),
    (
        "constraint_boundary",
        "T5",
        (
            "none",
            "constraint_satisfied",
            "constraint_violation",
            "empty_input",
        ),
    ),
    (
        "verification_mode",
        "T6",
        ("catalog_query", "effect_query", "returned_rows", "error_assertion"),
    ),
    ("cleanup_mode", "T6", ("rollback", "drop_objects", "reset_state")),
)


def _factor_value_count() -> int:
    return sum(len(values) for _, _, values in _CANONICAL_FACTORS)


def _load_grammar_actions() -> tuple[UpdateGrammarAction, ...]:
    """Freeze every UPDATE synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "update",
            _BRANCH_1,
            (
                "UPDATE [ ONLY ] table_name [ * ] [ [ AS ] alias ] "
                "SET column_name = { expression | DEFAULT } [, ...] "
                "[ FROM from_item [, ...] ] "
                "[ WHERE condition | WHERE CURRENT OF cursor_name ] "
                "[ RETURNING { * | output_expression } [, ...] ]"
            ),
            "synopsis-update",
        ),
    )
    actions = [
        UpdateGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise UpdateFactorLoopError("update action count drift")
    return tuple(actions)


def _canonical_consumer(row) -> str:
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise UpdateFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> list[UpdateFactorObligation]:
    rows: list[UpdateFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            UpdateFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"UPDATE-GRM|{action.grammar_branch_id}|"
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
        raise UpdateFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root,  # noqa: ANN001  (Path)
) -> list[UpdateFactorObligation]:
    """Compile the 49 SFV obligations from the shipped applicability catalog."""

    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("update")
    if len(catalog_rows) != 49:
        raise UpdateFactorLoopError("canonical obligation count drift")
    rows: list[UpdateFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            UpdateFactorObligation(
                ordinal=0,
                obligation_id=f"UPDATE-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[UpdateFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"update-factor-obligations-v1\n")
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


# Dense baseline defaults (all positive T1-T4 + T6 factor values).
# condition_shape defaults to simple_predicate (not none) so that
# data_or_query_shape and expression_shape are observable in the SET
# clause, mirroring how CALL defaulted data_or_query_shape to
# explicit_values so expression_shape was observable in the argument list.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_1,
    "expected_status": "success",
    "target_relation_state": "exists",
    "data_or_query_shape": "explicit_values",
    "condition_shape": "simple_predicate",
    "result_shape": "none",
    "with_clause": "absent",
    "name_shape": "plain_identifier",
    "expression_shape": "literal",
    "dependency_state": "ready",
    "privilege_context": "owner",
    "invalid_combination": "none",
    "constraint_boundary": "none",
    "verification_mode": "effect_query",
    "cleanup_mode": "rollback",
}


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive related factors and ensure baseline self-consistency.

    The T5 negative-axis factors (invalid_combination,
    constraint_boundary) describe the same scenario as their T1-T4
    counterparts.  When the primary factor is a T1-T4 value, the
    corresponding T5 value is derived; when the primary is a T5 value,
    the T1-T4 counterpart is derived.  expected_status=failure is a
    marker that requires a concrete failure cause.
    """

    trs = a.get("target_relation_state", "exists")
    ds = a.get("dependency_state", "ready")
    ic = a.get("invalid_combination", "none")
    es = a.get("expected_status", "success")

    if trs == "missing" or ds == "missing_dependency":
        a["target_relation_state"] = "missing"
        a["dependency_state"] = "missing_dependency"

    if trs == "wrong_object_type" or ic == "object_type_mismatch":
        a["target_relation_state"] = "wrong_object_type"
        a["invalid_combination"] = "object_type_mismatch"

    if es == "failure":
        has_concrete = any(
            a.get(f) == v
            for f, v in _SFV_FAILURE_VALUES
            if f != "expected_status"
        )
        if not has_concrete:
            a["target_relation_state"] = "missing"
            a["dependency_state"] = "missing_dependency"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: UpdateFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["statement_branch"] = _BRANCH_1
    assignments["target_action"] = obligation.consumer_action_id
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    failures = _count_baseline_failures(assignments)
    assignments["expected_status"] = (
        "failure" if failures > 0 else "success"
    )
    if len(assignments) != len(set(assignments)):
        raise UpdateFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: UpdateFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise UpdateFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_update_factor_loop_plan(
    repository_root,  # noqa: ANN001  (Path; kept for API parity)
) -> UpdateFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    obligations = compile_update_factor_loop_obligations(repository_root)
    cases: list[UpdateFactorCase] = []
    delegated: list[UpdateFactorObligation] = []
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
            UpdateFactorCase(
                ordinal=ordinal,
                case_id=f"UPDATE{ordinal:05d}",
                sql_filename=f"UPDATE{ordinal:05d}.sql",
                object_prefix=f"update_{ordinal:05d}_",
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
    plan = UpdateFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 50 or len(plan.delegated) != 0:
        raise UpdateFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 50:
        raise UpdateFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 50:
        raise UpdateFactorLoopError("duplicate SQL filename")
    return plan


def compile_update_factor_loop_obligations(
    repository_root,  # noqa: ANN001  (Path; kept for API parity)
) -> tuple[UpdateFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    from pathlib import Path

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        UpdateFactorObligation(
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
    if len(rows) != 50:
        raise UpdateFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise UpdateFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 49}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise UpdateFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise UpdateFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 50:
        raise UpdateFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise UpdateFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "UpdateFactorLoopError",
    "UpdateGrammarAction",
    "UpdateFactorObligation",
    "UpdateFactorCase",
    "UpdateFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_update_factor_loop_obligations",
    "build_update_factor_loop_plan",
    "_obligation_multiset_sha256",
]
