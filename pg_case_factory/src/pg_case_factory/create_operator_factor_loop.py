"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE OPERATOR.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE OPERATOR``.  CREATE OPERATOR is a PostgreSQL schema-level DDL
statement with a single official synopsis branch:
``CREATE OPERATOR name ( {FUNCTION|PROCEDURE} = function_name [, ...] )``.

The statement touches the ``pg_catalog.pg_operator`` catalog row (not a
``pg_class`` relation), so column/table/relation coverage is
``not_applicable`` and there is no ``INV`` block.  CREATE OPERATOR does
not create tables, so the bookend (DROP TABLE IF EXISTS) is never emitted.
Cleanup uses ``DROP OPERATOR IF EXISTS`` plus ``DROP SCHEMA``.

Each local obligation becomes exactly one regress program.  The 55
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


class CreateOperatorFactorLoopError(ValueError):
    """Raised when a frozen CREATE OPERATOR obligation input drifts."""


@dataclass(frozen=True)
class CreateOperatorGrammarAction:
    """One official target action form of the CREATE OPERATOR synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateOperatorFactorObligation:
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
class CreateOperatorFactorCase:
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
class CreateOperatorFactorLoopPlan:
    obligations: tuple[CreateOperatorFactorObligation, ...]
    cases: tuple[CreateOperatorFactorCase, ...]
    delegated: tuple[CreateOperatorFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-createoperator.html).
_BRANCH_DEFINE = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createoperator"

# A representative define action used as the baseline consumer for
# canonical factors not bound to one specific branch.
_REPRESENTATIVE_ACTION = "define_operator"


def _canonical_consumer(row) -> str:
    """Map a canonical factor value to its target consumer action."""
    if row.factor == "statement_branch":
        return "define_operator"
    if row.factor == "operand_type_shape":
        if row.value == "binary_operator":
            return "define_binary"
        return "define_prefix"
    if row.factor == "function_clause":
        if row.value == "function_keyword":
            return "define_function_kw"
        return "define_procedure_kw"
    if row.factor in ("commutator_clause", "negator_clause"):
        if row.value == "present":
            return "define_with_binding"
        return "define_operator"
    if row.factor in ("restrict_clause", "join_clause"):
        if row.value == "present":
            return "define_with_estimator"
        return "define_operator"
    if row.factor in ("hashes_clause", "merges_clause"):
        if row.value == "present":
            return "define_with_behavior"
        return "define_operator"
    if row.factor == "privilege_context":
        if row.value == "insufficient_privilege":
            return "define_insufficient_priv"
        return "define_operator"
    if row.factor == "name_shape":
        if row.value == "schema_qualified":
            return "define_schema_qualified"
        if row.value == "quoted_identifier":
            return "define_quoted_schema"
        return "define_operator"
    if row.factor == "function_name_shape":
        if row.value == "schema_qualified_function":
            return "define_qualified_fn"
        if row.value == "missing_function":
            return "define_missing_fn"
        return "define_operator"
    if row.factor == "operand_data_type":
        return "define_operator"
    if row.factor == "dependency_state":
        if row.value == "missing_function":
            return "define_missing_fn"
        if row.value == "wrong_signature":
            return "define_wrong_sig"
        return "define_operator"
    if row.factor == "operator_type_compatibility":
        if row.value == "incompatible":
            return "define_incompatible"
        return "define_operator"
    if row.factor == "invalid_combination":
        if row.value == "syntax_valid_semantic_error":
            return "define_semantic_error"
        if row.value == "object_type_mismatch":
            return "define_type_mismatch"
        return "define_operator"
    if row.factor == "ownership_boundary":
        if row.value == "non_privileged":
            return "define_insufficient_priv"
        return "define_operator"
    return _REPRESENTATIVE_ACTION


# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("target_object_state", "exists"),
        ("target_object_state", "exists_conflict"),
        ("dependency_state", "missing_function"),
        ("dependency_state", "wrong_signature"),
        ("operator_type_compatibility", "incompatible"),
        ("invalid_combination", "syntax_valid_semantic_error"),
        ("invalid_combination", "object_type_mismatch"),
        ("privilege_context", "insufficient_privilege"),
        ("ownership_boundary", "non_privileged"),
        ("function_name_shape", "missing_function"),
        ("expected_status", "failure"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("target_object_state", "exists"): (
        "42710",
        "duplicate_operator_signature_provisional",
    ),
    ("target_object_state", "exists_conflict"): (
        "42710",
        "duplicate_operator_signature_provisional",
    ),
    ("dependency_state", "missing_function"): (
        "42883",
        "missing_operator_function_provisional",
    ),
    ("function_name_shape", "missing_function"): (
        "42883",
        "missing_operator_function_provisional",
    ),
    ("dependency_state", "wrong_signature"): (
        "42809",
        "wrong_operator_function_signature_provisional",
    ),
    ("operator_type_compatibility", "incompatible"): (
        "42809",
        "incompatible_operand_types_provisional",
    ),
    ("invalid_combination", "syntax_valid_semantic_error"): (
        "42601",
        "invalid_operator_definition_provisional",
    ),
    ("invalid_combination", "object_type_mismatch"): (
        "42809",
        "invalid_operator_definition_provisional",
    ),
    ("privilege_context", "insufficient_privilege"): (
        "42501",
        "insufficient_operator_privilege_provisional",
    ),
    ("ownership_boundary", "non_privileged"): (
        "42501",
        "insufficient_operator_privilege_provisional",
    ),
    ("expected_status", "failure"): (
        "42710",
        "duplicate_operator_signature_provisional",
    ),
}


def _load_grammar_actions() -> (
    tuple[CreateOperatorGrammarAction, ...]
):
    """Freeze every CREATE OPERATOR synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "define_operator",
            _BRANCH_DEFINE,
            "CREATE OPERATOR name (FUNCTION = fn [, LEFTARG = lt] [, RIGHTARG = rt] ...)",
            "synopsis-define-operator",
        ),
    )
    actions = [
        CreateOperatorGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise CreateOperatorFactorLoopError(
            "create operator action count drift"
        )
    return tuple(actions)


def _compile_grammar_obligations() -> (
    list[CreateOperatorFactorObligation]
):
    rows: list[CreateOperatorFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateOperatorFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"COP-GRM|{action.grammar_branch_id}|"
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
        raise CreateOperatorFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateOperatorFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_operator")
    if len(catalog_rows) != 55:
        raise CreateOperatorFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[CreateOperatorFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateOperatorFactorObligation(
                ordinal=0,
                obligation_id=f"COP-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreateOperatorFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-operator-factor-obligations-v1\n"
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
    "statement_branch": _BRANCH_DEFINE,
    "target_object_state": "absent",
    "operand_type_shape": "binary_operator",
    "expected_status": "success",
    "function_clause": "function_keyword",
    "leftarg_clause": "present",
    "rightarg_clause": "present",
    "commutator_clause": "absent",
    "negator_clause": "absent",
    "restrict_clause": "absent",
    "join_clause": "absent",
    "hashes_clause": "absent",
    "merges_clause": "absent",
    "privilege_context": "schema_create_privilege",
    "name_shape": "plain_identifier",
    "function_name_shape": "plain_function",
    "operand_data_type": "integer",
    "dependency_state": "ready",
    "operator_type_compatibility": "compatible",
    "invalid_combination": "none",
    "ownership_boundary": "schema_owner",
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
    """Derive overlapping T1-T5 boundary factors from the primary value.

    operand_type_shape ↔ leftarg_clause:
      binary_operator    → leftarg_clause = present
      prefix_operator    → leftarg_clause = absent_prefix_operator
    privilege_context ↔ ownership_boundary:
      insufficient_privilege → ownership_boundary = non_privileged
      non_privileged          → privilege_context = insufficient_privilege
    function_name_shape ↔ dependency_state:
      missing_function  → dependency_state = missing_function
      (and vice-versa)
    operator_type_compatibility ↔ invalid_combination:
      incompatible → invalid_combination = syntax_valid_semantic_error
      (but keep explicit invalid_combination if set first)
    target_object_state → expected_status:
      exists / exists_conflict → expected_status = failure
    expected_status=failure → representative duplicate failure:
      target_object_state = exists
    """

    # --- operand_type_shape ↔ leftarg_clause ---
    ots = a.get("operand_type_shape", "binary_operator")
    if ots == "binary_operator":
        a["leftarg_clause"] = "present"
    elif ots == "prefix_operator":
        a["leftarg_clause"] = "absent_prefix_operator"
    lac = a.get("leftarg_clause", "present")
    if lac == "absent_prefix_operator":
        a["operand_type_shape"] = "prefix_operator"
    elif lac == "present":
        if a.get("operand_type_shape") == "prefix_operator":
            a["operand_type_shape"] = "binary_operator"

    # --- privilege_context ↔ ownership_boundary ---
    pc = a.get("privilege_context", "schema_create_privilege")
    if pc == "insufficient_privilege":
        a["ownership_boundary"] = "non_privileged"
    ob = a.get("ownership_boundary", "schema_owner")
    if ob == "non_privileged":
        a["privilege_context"] = "insufficient_privilege"

    # --- function_name_shape ↔ dependency_state ---
    fns = a.get("function_name_shape", "plain_function")
    if fns == "missing_function":
        a["dependency_state"] = "missing_function"
    ds = a.get("dependency_state", "ready")
    if ds == "missing_function":
        a["function_name_shape"] = "missing_function"
    if ds == "wrong_signature":
        a["function_name_shape"] = "plain_function"

    # --- operator_type_compatibility ↔ invalid_combination ---
    otc = a.get("operator_type_compatibility", "compatible")
    ic = a.get("invalid_combination", "none")
    if otc == "incompatible" and ic == "none":
        a["invalid_combination"] = "syntax_valid_semantic_error"
    if ic != "none" and otc == "compatible":
        a["operator_type_compatibility"] = "incompatible"

    # --- target_object_state → expected_status ---
    tos = a.get("target_object_state", "absent")
    if tos in ("exists", "exists_conflict"):
        a["expected_status"] = "failure"

    # --- expected_status=failure → representative duplicate ---
    es = a.get("expected_status", "success")
    if es == "failure":
        if tos not in ("exists", "exists_conflict"):
            a["target_object_state"] = "exists"
        a["ownership_boundary"] = "schema_owner"
        a["privilege_context"] = "schema_create_privilege"

    # --- Derive expected_status from failure count ---
    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _baseline_assignments(
    obligation: CreateOperatorFactorObligation,
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
        raise CreateOperatorFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateOperatorFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateOperatorFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_operator_factor_loop_plan(
    repository_root: Path,
) -> CreateOperatorFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_operator_factor_loop_obligations(root)
    cases: list[CreateOperatorFactorCase] = []
    delegated: list[CreateOperatorFactorObligation] = []
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
            CreateOperatorFactorCase(
                ordinal=ordinal,
                case_id=f"CREATEOPERATOR{ordinal:05d}",
                sql_filename=f"CREATEOPERATOR{ordinal:05d}.sql",
                object_prefix=f"createoperator_{ordinal:05d}_",
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
    plan = CreateOperatorFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 56 or len(plan.delegated) != 0:
        raise CreateOperatorFactorLoopError(
            "factor loop plan count drift"
        )
    if len({row.primary_obligation_id for row in plan.cases}) != 56:
        raise CreateOperatorFactorLoopError(
            "local obligation mapping drift"
        )
    if len({row.sql_filename for row in plan.cases}) != 56:
        raise CreateOperatorFactorLoopError("duplicate SQL filename")
    return plan


def compile_create_operator_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateOperatorFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateOperatorFactorObligation(
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
    if len(rows) != 56:
        raise CreateOperatorFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateOperatorFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 55}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateOperatorFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateOperatorFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 56:
        raise CreateOperatorFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreateOperatorFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "CreateOperatorFactorLoopError",
    "CreateOperatorGrammarAction",
    "CreateOperatorFactorObligation",
    "CreateOperatorFactorCase",
    "CreateOperatorFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_create_operator_factor_loop_obligations",
    "build_create_operator_factor_loop_plan",
    "_obligation_multiset_sha256",
]
