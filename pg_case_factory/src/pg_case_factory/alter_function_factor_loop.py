"""Factor-value-loop obligation ledger for PostgreSQL 18.4 ALTER FUNCTION.

This module compiles the marginal GRM/SFV/RISK obligation ledger for
``ALTER FUNCTION``.  It must not enumerate a signature/type cross product:
``alter_function.yaml`` marks column/table/relation coverage
``not_applicable``, so there is no ``INV`` block.  Each local obligation will
become exactly one regress program; there are no delegated handoffs because
every reachable negative boundary is a real ``ALTER FUNCTION`` error that
belongs to this statement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .alter_function_regress import (
    AlterFunctionRegressError,
    load_alter_function_grammar_actions,
    load_alter_function_grammar_axes,
)
from .applicability import load_shipped_applicability_universe


class AlterFunctionFactorLoopError(ValueError):
    """Raised when a frozen ALTER FUNCTION obligation input drifts."""


@dataclass(frozen=True)
class AlterFunctionFactorObligation:
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
class AlterFunctionFactorCase:
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
class AlterFunctionFactorLoopPlan:
    obligations: tuple[AlterFunctionFactorObligation, ...]
    cases: tuple[AlterFunctionFactorCase, ...]
    delegated: tuple[AlterFunctionFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches.
_BRANCH_ACTION_FORM = "branch_action_form"

# A representative branch_1 action used as the baseline consumer for
# signature-level / outer modifiers that are not bound to one sub-clause.
_REPRESENTATIVE_ACTION = "volatile"

# Canonical factor -> the action where the value is observable.  Factors
# whose consumer depends on the value (statement_branch, action_type,
# permission_insufficient) are resolved in :func:`_canonical_consumer`.
_SFV_FACTOR_CONSUMER = {
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "restrict_clause": _REPRESENTATIVE_ACTION,
    "rename_target": "rename",
    "owner_target": "owner",
    "schema_target": "set_schema",
    "extension_target": "depends_on_extension",
    "argtype_specification": _REPRESENTATIVE_ACTION,
    "function_name_shape": _REPRESENTATIVE_ACTION,
    "new_name_shape": "rename",
    "configuration_parameter_shape": "set_parameter",
    "privilege_level": _REPRESENTATIVE_ACTION,
    "schema_dependency": "set_schema",
    "role_dependency": "owner",
    "extension_dependency": "depends_on_extension",
    "target_function_not_exists": _REPRESENTATIVE_ACTION,
    "target_function_different_type": _REPRESENTATIVE_ACTION,
    "conflicting_action": _REPRESENTATIVE_ACTION,
    "identifier_length_exceeded": "rename",
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

_STATEMENT_BRANCH_CONSUMER = {
    "branch_1": _REPRESENTATIVE_ACTION,
    "branch_2": "rename",
    "branch_3": "owner",
    "branch_4": "set_schema",
    "branch_5": "depends_on_extension",
}

_ACTION_TYPE_CONSUMER = {
    "CALLED_ON_NULL_INPUT": "called_on_null_input",
    "RETURNS_NULL_ON_NULL_INPUT": "returns_null_on_null_input",
    "STRICT": "strict",
    "IMMUTABLE": "immutable",
    "STABLE": "stable",
    "VOLATILE": "volatile",
    "LEAKPROOF": "leakproof",
    "NOT_LEAKPROOF": "not_leakproof",
    "SECURITY_INVOKER": "security_invoker",
    "SECURITY_DEFINER": "security_definer",
    "PARALLEL_UNSAFE": "parallel_unsafe",
    "PARALLEL_RESTRICTED": "parallel_restricted",
    "PARALLEL_SAFE": "parallel_safe",
    "COST": "cost",
    "ROWS": "rows",
    "SUPPORT": "support",
    "SET_parameter": "set_parameter",
    "RESET_parameter": "reset_parameter",
    "RESET_ALL": "reset_all",
}

_PERMISSION_INSUFFICIENT_CONSUMER = {
    "no_alter_privilege": _REPRESENTATIVE_ACTION,
    "not_owner_for_OWNER_TO": "owner",
    "not_owner_for_SET_SCHEMA": "set_schema",
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check and
# are rejected (verified against PG 18.4).  ``without_signature`` is a legal
# success for a unique-name function, and ``over_63_chars`` succeeds via
# NAMEDATALEN truncation, so neither is an expected failure.
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "not_exists"),
        ("object_state", "different_signature_exists"),
        ("rename_target", "duplicate_name"),
        ("owner_target", "nonexistent_role"),
        ("schema_target", "schema_not_exists"),
        ("schema_target", "pg_catalog_reserved"),
        ("schema_target", "information_schema_reserved"),
        ("extension_target", "extension_not_exists"),
        ("argtype_specification", "with_partial_signature"),
        ("configuration_parameter_shape", "invalid_parameter"),
        ("privilege_level", "non_owner_no_privilege"),
        ("schema_dependency", "target_schema_not_exists"),
        ("schema_dependency", "reserved_schema"),
        ("role_dependency", "owner_role_not_exists"),
        ("extension_dependency", "extension_not_installed"),
        ("target_function_not_exists", "function_name_not_found"),
        ("target_function_not_exists", "function_signature_not_found"),
        ("target_function_different_type", "same_name_is_aggregate"),
        ("target_function_different_type", "same_name_is_procedure"),
        ("permission_insufficient", "no_alter_privilege"),
        ("permission_insufficient", "not_owner_for_OWNER_TO"),
        ("permission_insufficient", "not_owner_for_SET_SCHEMA"),
        ("conflicting_action", "multiple_conflicting_volatility"),
    }
)


def _axis_consumer(action_id: str) -> str:
    """Resolve the baseline action that witnesses an outer/axis modifier."""

    if action_id == "__outer_action__":
        return _REPRESENTATIVE_ACTION
    return action_id


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterFunctionFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "action_type":
        try:
            return _ACTION_TYPE_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterFunctionFactorLoopError(
                f"unknown action_type value: {row.value}"
            ) from exc
    if row.factor == "permission_insufficient":
        try:
            return _PERMISSION_INSUFFICIENT_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterFunctionFactorLoopError(
                f"unknown permission_insufficient value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise AlterFunctionFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> list[AlterFunctionFactorObligation]:
    rows: list[AlterFunctionFactorObligation] = []
    for action in load_alter_function_grammar_actions():
        rows.append(
            AlterFunctionFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"AF-GRM|{action.grammar_branch_id}|"
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
    for axis in load_alter_function_grammar_axes():
        factor_key = (
            f"outer:{axis.axis_id}"
            if axis.action_id == "__outer_action__"
            else f"local:{axis.axis_id}"
        )
        consumer = _axis_consumer(axis.action_id)
        for value in axis.values:
            rows.append(
                AlterFunctionFactorObligation(
                    ordinal=0,
                    obligation_id=(
                        f"AF-GRM|{axis.grammar_branch_id}|"
                        f"{axis.action_id}|{axis.axis_id}|{value}"
                    ),
                    kind="GRM",
                    factor_key=factor_key,
                    value=value,
                    consumer_action_id=consumer,
                    disposition="covered",
                    source_locator=axis.source_locator,
                )
            )
    if len(rows) != 36:
        raise AlterFunctionFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[AlterFunctionFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("alter_function")
    if len(catalog_rows) != 85:
        raise AlterFunctionFactorLoopError("canonical obligation count drift")
    rows: list[AlterFunctionFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            AlterFunctionFactorObligation(
                ordinal=0,
                obligation_id=f"AF-SFV|{row.row_id}|{consumer}",
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


def _compile_risk_obligations() -> list[AlterFunctionFactorObligation]:
    return [
        AlterFunctionFactorObligation(
            ordinal=0,
            obligation_id=f"AF-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-alterfunction:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[AlterFunctionFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"alter-function-factor-obligations-v1\n")
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


def _consumer_branch_map() -> dict[str, str]:
    return {
        action.action_id: action.grammar_branch_id
        for action in load_alter_function_grammar_actions()
    }


def _renderer_factor_key(factor_key: str) -> str:
    """Map an obligation factor key to the renderer's flat factor namespace."""

    if factor_key.startswith("outer:") or factor_key.startswith("local:"):
        return factor_key.split(":", 1)[1]
    return factor_key


# Verified PG 18.4 SQLSTATE for each reachable expected-failure value.  These
# were probed against an isolated 18.4 instance under the function-owner
# baseline (reserved-schema rejections surface as 42501 under a non-superuser
# owner, not as a superuser-only success).
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42883",
        "expected_status_failure_function_not_found",
    ),
    ("object_state", "not_exists"): ("42883", "function_does_not_exist"),
    ("object_state", "different_signature_exists"): (
        "42883",
        "function_signature_does_not_exist",
    ),
    ("rename_target", "duplicate_name"): (
        "42723",
        "function_already_exists_in_schema",
    ),
    ("owner_target", "nonexistent_role"): ("42704", "role_does_not_exist"),
    ("schema_target", "schema_not_exists"): ("3F000", "schema_does_not_exist"),
    ("schema_target", "pg_catalog_reserved"): (
        "42501",
        "permission_denied_for_reserved_schema",
    ),
    ("schema_target", "information_schema_reserved"): (
        "42501",
        "permission_denied_for_reserved_schema",
    ),
    ("extension_target", "extension_not_exists"): (
        "42704",
        "extension_does_not_exist",
    ),
    ("argtype_specification", "with_partial_signature"): (
        "42883",
        "function_signature_does_not_exist",
    ),
    ("configuration_parameter_shape", "invalid_parameter"): (
        "42704",
        "unrecognized_configuration_parameter",
    ),
    ("privilege_level", "non_owner_no_privilege"): (
        "42501",
        "must_be_owner_of_function",
    ),
    ("schema_dependency", "target_schema_not_exists"): (
        "3F000",
        "schema_does_not_exist",
    ),
    ("schema_dependency", "reserved_schema"): (
        "42501",
        "permission_denied_for_reserved_schema",
    ),
    ("role_dependency", "owner_role_not_exists"): (
        "42704",
        "role_does_not_exist",
    ),
    ("extension_dependency", "extension_not_installed"): (
        "42704",
        "extension_does_not_exist",
    ),
    ("target_function_not_exists", "function_name_not_found"): (
        "42883",
        "function_does_not_exist",
    ),
    ("target_function_not_exists", "function_signature_not_found"): (
        "42883",
        "function_signature_does_not_exist",
    ),
    ("target_function_different_type", "same_name_is_aggregate"): (
        "42809",
        "not_a_function_is_aggregate",
    ),
    ("target_function_different_type", "same_name_is_procedure"): (
        "42809",
        "not_a_function_is_procedure",
    ),
    ("permission_insufficient", "no_alter_privilege"): (
        "42501",
        "must_be_owner_of_function",
    ),
    ("permission_insufficient", "not_owner_for_OWNER_TO"): (
        "42501",
        "must_be_owner_of_function",
    ),
    ("permission_insufficient", "not_owner_for_SET_SCHEMA"): (
        "42501",
        "must_be_owner_of_function",
    ),
    ("conflicting_action", "multiple_conflicting_volatility"): (
        "42601",
        "conflicting_or_redundant_options",
    ),
}


def _expected_failure_details(
    obligation: AlterFunctionFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise AlterFunctionFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def _baseline_assignments(
    obligation: AlterFunctionFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides."""

    branch = _consumer_branch_map()[obligation.consumer_action_id]
    assignments: dict[str, str] = {
        "grammar_branch": branch,
        "target_action": obligation.consumer_action_id,
        "object_state": "exists",
        "privilege_level": "function_owner",
        "function_name_shape": "simple",
        "argtype_specification": "with_full_signature",
        "expected_status": "success",
        "verification_mode": "pg_proc_catalog_query",
        "cleanup_mode": "DROP_FUNCTION_IF_EXISTS",
        # GRM axis baselines (minimal / absent form).
        "restrict_clause": "absent",
        "action_list_cardinality": "one_action",
        "set_assignment_form": "to_value",
        "external_keyword": "omitted",
        "depends_polarity": "depends",
    }
    if branch == "branch_rename":
        assignments["new_name_shape"] = "simple"
    elif branch == "branch_owner":
        assignments["owner_target"] = "new_owner_role"
        assignments["role_dependency"] = "owner_role_exists"
    elif branch == "branch_set_schema":
        assignments["schema_target"] = "schema_exists"
        assignments["schema_dependency"] = "target_schema_exists"
    elif branch == "branch_depends_extension":
        assignments["extension_target"] = "extension_exists"
        assignments["extension_dependency"] = "extension_installed"
    # The primary value overrides exactly one key.
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value
    if len(assignments) != len(set(assignments)):
        raise AlterFunctionFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_alter_function_factor_loop_plan(
    repository_root: Path,
) -> AlterFunctionFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_alter_function_factor_loop_obligations(root)
    cases: list[AlterFunctionFactorCase] = []
    delegated: list[AlterFunctionFactorObligation] = []
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
            AlterFunctionFactorCase(
                ordinal=ordinal,
                case_id=f"ALTERFUNCTION{ordinal:04d}",
                sql_filename=f"ALTERFUNCTION{ordinal:04d}.sql",
                object_prefix=f"alterfunction_{ordinal:04d}_",
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
    plan = AlterFunctionFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 123 or len(plan.delegated) != 0:
        raise AlterFunctionFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 123:
        raise AlterFunctionFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 123:
        raise AlterFunctionFactorLoopError("duplicate SQL filename")
    return plan


def compile_alter_function_factor_loop_obligations(
    repository_root: Path,
) -> tuple[AlterFunctionFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        AlterFunctionFactorObligation(
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
    if len(rows) != 123:
        raise AlterFunctionFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise AlterFunctionFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 36, "SFV": 85, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise AlterFunctionFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise AlterFunctionFactorLoopError("delegated obligation count drift")
    if sum(row.disposition in {"covered", "expected_failure"} for row in rows) != 123:
        raise AlterFunctionFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(row.disposition not in allowed_dispositions for row in rows):
        raise AlterFunctionFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "AlterFunctionFactorLoopError",
    "AlterFunctionFactorObligation",
    "AlterFunctionFactorCase",
    "AlterFunctionFactorLoopPlan",
    "compile_alter_function_factor_loop_obligations",
    "build_alter_function_factor_loop_plan",
    "_obligation_multiset_sha256",
]
