"""Factor-value-loop obligation ledger for PostgreSQL 18.4 DROP ROUTINE.

``DROP ROUTINE`` is the GENERIC routine-removal statement: it resolves
functions, procedures, AND aggregates (unlike the kind-specific DROP
FUNCTION / DROP PROCEDURE / DROP AGGREGATE aliases).  The baseline
ledger covers every shipped applicability factor value one-to-one (60
SFV rows), plus one grammar action (GRM) and a RISK transactional pair.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class DropRoutineFactorLoopError(ValueError):
    """Raised when a frozen DROP ROUTINE obligation input drifts."""


@dataclass(frozen=True)
class DropRoutineFactorObligation:
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
class DropRoutineFactorCase:
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
class DropRoutineFactorLoopPlan:
    obligations: tuple[DropRoutineFactorObligation, ...]
    cases: tuple[DropRoutineFactorCase, ...]
    delegated: tuple[DropRoutineFactorObligation, ...]
    obligation_multiset_sha256: str


_BRANCH_1 = "branch_1"
_DOC_SOURCE = "postgresql-18.4-doc:sql-droproutine"

@dataclass(frozen=True)
class _GrammarAction:
    action_id: str
    grammar_branch_id: str
    source_locator: str


_GRAMMAR_ACTIONS: tuple[_GrammarAction, ...] = (
    _GrammarAction(
        action_id="drop_routine",
        grammar_branch_id=_BRANCH_1,
        source_locator=f"{_DOC_SOURCE}:synopsis",
    ),
)

_REPRESENTATIVE_ACTION = "drop_routine"

_SFV_FACTOR_CONSUMER: dict[str, str] = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "routine_existence": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "if_exists_clause": _REPRESENTATIVE_ACTION,
    "cascade_restrict_clause": _REPRESENTATIVE_ACTION,
    "routine_type": _REPRESENTATIVE_ACTION,
    "arg_signature_disambiguation": _REPRESENTATIVE_ACTION,
    "privilege_context": _REPRESENTATIVE_ACTION,
    "multi_target": _REPRESENTATIVE_ACTION,
    "routine_name_shape": _REPRESENTATIVE_ACTION,
    "arg_signature_shape": _REPRESENTATIVE_ACTION,
    "executor_privilege": _REPRESENTATIVE_ACTION,
    "dependent_objects": _REPRESENTATIVE_ACTION,
    "nonexistent_routine": _REPRESENTATIVE_ACTION,
    "privilege_insufficient": _REPRESENTATIVE_ACTION,
    "dependent_object_conflict": _REPRESENTATIVE_ACTION,
    "overloaded_routine_ambiguity": _REPRESENTATIVE_ACTION,
    "wrong_argument_types": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

_STATEMENT_BRANCH_CONSUMER: dict[str, str] = {
    "branch_drop_routine": "drop_routine",
    "branch_drop_routine_if_exists": "drop_routine",
    "branch_drop_routine_cascade": "drop_routine",
    "branch_drop_routine_restrict": "drop_routine",
}

# Inherently-failing single-boundary (factor, value) pairs.  Each gets a
# provisional PG 18.4 SQLSTATE; cross-factor failures live in EXTENSION.
_SFV_FAILURE_VALUES: frozenset[tuple[str, str]] = frozenset(
    {
        ("expected_status", "failure"),
        ("nonexistent_routine", "routine_does_not_exist"),
        ("routine_existence", "routine_not_exists"),
        ("privilege_insufficient", "non_owner_dropping_routine"),
        ("privilege_context", "non_owner_no_privilege"),
        ("executor_privilege", "non_owner_no_privilege"),
        ("dependent_objects", "has_dependent_trigger"),
        ("dependent_objects", "has_dependent_view"),
        ("dependent_objects", "has_dependent_routine"),
        ("dependent_object_conflict", "restrict_with_dependent_fails"),
        ("overloaded_routine_ambiguity", "ambiguous_without_signature"),
        ("wrong_argument_types", "signature_does_not_match_any_routine"),
        ("arg_signature_disambiguation", "signature_mismatch"),
        ("routine_name_shape", "non_existing_name"),
    }
)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise DropRoutineFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise DropRoutineFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _consumer_branch_map() -> dict[str, str]:
    return {action.action_id: action.grammar_branch_id for action in _GRAMMAR_ACTIONS}


def _renderer_factor_key(factor_key: str) -> str:
    if factor_key.startswith("outer:") or factor_key.startswith("local:"):
        return factor_key.split(":", 1)[1]
    return factor_key


def _compile_grammar_obligations() -> list[DropRoutineFactorObligation]:
    rows: list[DropRoutineFactorObligation] = []
    for action in _GRAMMAR_ACTIONS:
        rows.append(
            DropRoutineFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPROUTINE-GRM|{action.grammar_branch_id}|"
                    f"{action.action_id}|target_action|{action.action_id}"
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
        raise DropRoutineFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[DropRoutineFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("drop_routine")
    if len(catalog_rows) != 60:
        raise DropRoutineFactorLoopError("canonical obligation count drift")
    rows: list[DropRoutineFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            DropRoutineFactorObligation(
                ordinal=0,
                obligation_id=f"DROPROUTINE-SFV|{row.row_id}|{consumer}",
                kind="SFV",
                factor_key=row.factor,
                value=row.value,
                consumer_action_id=consumer,
                disposition=(
                    "expected_failure"
                    if (row.factor, row.value) in _SFV_FAILURE_VALUES
                    else "covered"
                ),
                source_locator=f"{row.source_reference}#{row.row_id}",
            )
        )
    return rows


def _compile_risk_obligations() -> list[DropRoutineFactorObligation]:
    return [
        DropRoutineFactorObligation(
            ordinal=0,
            obligation_id=f"DROPROUTINE-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator="postgresql-18.4-doc:sql-droproutine:transactional-ddl",
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[DropRoutineFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"drop-routine-factor-obligations-v1\n")
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
                    "delegated_statement_key": row.delegated_statement_key,
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        digest.update(b"\n")
    return digest.hexdigest()


# Provisional PG 18.4 SQLSTATE attribution for each reachable expected-failure
# value.  The frozen counts + sha256s in the companion tests are the spec.
# The no-DB tickoff does NOT execute probe SQL; these SQLSTATEs are verified
# in a later DB phase.  Superset of _SFV_FAILURE_VALUES for extension reuse.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): ("42704", "drop_routine_declared_failure"),
    ("nonexistent_routine", "routine_does_not_exist"): (
        "42704",
        "undefined_routine_absent",
    ),
    ("routine_existence", "routine_not_exists"): (
        "42704",
        "undefined_routine_absent",
    ),
    ("routine_name_shape", "non_existing_name"): (
        "42704",
        "undefined_routine_name",
    ),
    ("privilege_insufficient", "non_owner_dropping_routine"): (
        "42501",
        "insufficient_routine_privilege",
    ),
    ("privilege_context", "non_owner_no_privilege"): (
        "42501",
        "insufficient_routine_privilege",
    ),
    ("executor_privilege", "non_owner_no_privilege"): (
        "42501",
        "insufficient_routine_privilege",
    ),
    ("dependent_objects", "has_dependent_trigger"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
    ("dependent_objects", "has_dependent_view"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
    ("dependent_objects", "has_dependent_routine"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
    ("dependent_object_conflict", "restrict_with_dependent_fails"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
    ("overloaded_routine_ambiguity", "ambiguous_without_signature"): (
        "42725",
        "routine_ambiguous_without_signature",
    ),
    ("wrong_argument_types", "signature_does_not_match_any_routine"): (
        "42883",
        "undefined_function_signature_mismatch",
    ),
    ("arg_signature_disambiguation", "signature_mismatch"): (
        "42883",
        "undefined_function_signature_mismatch",
    ),
}


def _expected_failure_details(
    obligation: DropRoutineFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise DropRoutineFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_routine",
    "grammar_branch": "branch_1",
    "target_action": "drop_routine",
    "routine_existence": "routine_exists",
    "expected_status": "success",
    "if_exists_clause": "without_if_exists",
    "cascade_restrict_clause": "no_clause_default_restrict",
    "routine_type": "function",
    "arg_signature_disambiguation": "no_args_no_ambiguity",
    "privilege_context": "superuser",
    "multi_target": "single_target",
    "routine_name_shape": "simple_name",
    "arg_signature_shape": "no_args",
    "executor_privilege": "superuser",
    "dependent_objects": "no_dependent_objects",
    "nonexistent_routine": "routine_does_not_exist",
    "privilege_insufficient": "non_owner_dropping_routine",
    "dependent_object_conflict": "restrict_with_dependent_fails",
    "overloaded_routine_ambiguity": "ambiguous_without_signature",
    "wrong_argument_types": "signature_does_not_match_any_routine",
    "verification_mode": "pg_proc_catalog",
    "cleanup_mode": "drop_routine",
}


def _baseline_assignments(
    obligation: DropRoutineFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides."""

    branch = _consumer_branch_map()[obligation.consumer_action_id]
    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["grammar_branch"] = branch
    assignments["target_action"] = obligation.consumer_action_id
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value
    # Reconcile routine_existence with routine_type so the fixture kind is
    # consistent: the ``routine_exists_as_*`` values pin the routine kind.
    existence = assignments.get("routine_existence", "routine_exists")
    if existence == "routine_exists_as_function":
        assignments["routine_type"] = "function"
    elif existence == "routine_exists_as_procedure":
        assignments["routine_type"] = "procedure"
    elif existence == "routine_exists_as_aggregate":
        assignments["routine_type"] = "aggregate"
    # Reconcile statement_branch with the clause factors: the branch label
    # pins IF EXISTS and CASCADE/RESTRICT unless a clause factor is itself
    # the primary (the primary override above already won by this point).
    sb = assignments.get("statement_branch", "branch_drop_routine")
    if sb == "branch_drop_routine_if_exists":
        assignments["if_exists_clause"] = "with_if_exists"
    elif sb == "branch_drop_routine_cascade":
        assignments["cascade_restrict_clause"] = "cascade"
    elif sb == "branch_drop_routine_restrict":
        assignments["cascade_restrict_clause"] = "restrict"
    if len(assignments) != len(set(assignments)):
        raise DropRoutineFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_drop_routine_factor_loop_plan(
    repository_root: Path,
) -> DropRoutineFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_drop_routine_factor_loop_obligations(root)
    cases: list[DropRoutineFactorCase] = []
    delegated: list[DropRoutineFactorObligation] = []
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
            DropRoutineFactorCase(
                ordinal=ordinal,
                case_id=f"DROPROUTINE{ordinal:05d}",
                sql_filename=f"DROPROUTINE{ordinal:05d}.sql",
                object_prefix=f"droproutine_{ordinal:05d}_",
                primary_obligation_id=obligation.obligation_id,
                kind=obligation.kind,
                factor_key=_renderer_factor_key(obligation.factor_key),
                factor_value=obligation.value,
                consumer_action_id=obligation.consumer_action_id,
                outcome=outcome,
                expected_sqlstate=sqlstate,
                expected_failure_reason=failure_reason,
                baseline_assignments=_baseline_assignments(obligation),
                execution_profile="serial_sql",
            )
        )
    plan = DropRoutineFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 63 or len(plan.delegated) != 0:
        raise DropRoutineFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 63:
        raise DropRoutineFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 63:
        raise DropRoutineFactorLoopError("duplicate SQL filename")
    return plan


_PLAN_CACHE: dict[Path, DropRoutineFactorLoopPlan] = {}


def _build_drop_routine_factor_plan_lazily(
    repository_root: Path,
) -> DropRoutineFactorLoopPlan:
    root = Path(repository_root).resolve(strict=True)
    if root not in _PLAN_CACHE:
        _PLAN_CACHE[root] = build_drop_routine_factor_loop_plan(root)
    return _PLAN_CACHE[root]


def compile_drop_routine_factor_loop_obligations(
    repository_root: Path,
) -> tuple[DropRoutineFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        DropRoutineFactorObligation(
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
    if len(rows) != 63:
        raise DropRoutineFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise DropRoutineFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 60, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise DropRoutineFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise DropRoutineFactorLoopError("delegated obligation count drift")
    if sum(row.disposition in {"covered", "expected_failure"} for row in rows) != 63:
        raise DropRoutineFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(row.disposition not in allowed_dispositions for row in rows):
        raise DropRoutineFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "DropRoutineFactorLoopError",
    "DropRoutineFactorObligation",
    "DropRoutineFactorCase",
    "DropRoutineFactorLoopPlan",
    "compile_drop_routine_factor_loop_obligations",
    "build_drop_routine_factor_loop_plan",
    "_obligation_multiset_sha256",
    "_build_drop_routine_factor_plan_lazily",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
]
