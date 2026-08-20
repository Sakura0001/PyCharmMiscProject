"""Bounded post-coverage extension plan for CREATE POLICY factor regress.

The baseline :mod:`create_policy_factor_loop` assigns one local SQL
program to every ``SFV``/``GRM`` obligation (marginal 1:1).  This module
crosses the main-axis factor values with verification/cleanup axes under
an at-most-one-failure attribution policy, producing a bounded set of
additional regress programs that exercise pairwise factor interactions.

CREATE POLICY is a table-level DDL statement — it requires a fixture
TABLE that must be created and RLS-enabled.  The bookend (DROP TABLE
IF EXISTS) is always emitted.  The ``pg_catalog.pg_policy`` catalog
row is the semantic witness target.

The extension is deterministic: given the same repository root, it
always produces the same frozen multiset SHA-256 and the same
contiguous case ordinals starting at ``_BASELINE_COUNT + 1``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

from .create_policy_factor_loop import (
    _BASELINE_DEFAULTS,
    _PG18_COMMAND_MAP,
    _SFV_FAILURE_SQLSTATE,
    _SFV_FAILURE_VALUES,
)


class CreatePolicyFactorExtensionError(ValueError):
    """Raised when CREATE POLICY extension input drifts."""


@dataclass(frozen=True)
class CreatePolicyFactorExtensionCase:
    ordinal: int
    case_id: str
    sql_filename: str
    object_prefix: str
    derivation_id: str
    derived_from_combination_group: str
    derivation_reason: str
    factor_assignment: tuple[tuple[str, str], ...]
    consumer_action_id: str
    outcome: str
    expected_sqlstate: str
    expected_failure_reason: str | None
    is_extension: bool = True


@dataclass(frozen=True)
class CreatePolicyFactorExtensionPlan:
    cases: tuple[CreatePolicyFactorExtensionCase, ...]
    extension_multiset_sha256: str
    raw_combination_count: int
    dropped_combination_count: int


_BASELINE_COUNT = 81
_CAP = 20000

_VERIFICATION_MODES = (
    "catalog_query_pg_policy",
    "rls_behavior_test",
    "error_assertion",
)
_CLEANUP_MODES = (
    "drop_policy",
    "disable_rls_and_drop_policy",
    "drop_table",
)

_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "policy_type": ("permissive", "restrictive"),
    "command_type": ("ALL", "SELECT", "INSERT", "UPDATE", "DELETE"),
    "object_state": (
        "not_exists",
        "exists_same_table",
        "exists_different_table",
    ),
    "privilege_level": ("superuser", "table_owner", "non_owner"),
}

_EXPRESSION_AXES: dict[str, tuple[str, ...]] = {
    "expression_compatibility": (
        "compatible_pairing",
        "select_with_check_incompatible",
        "insert_with_using_incompatible",
        "delete_with_check_incompatible",
    ),
}

_CROSSED_NEGATIVES = frozenset(
    {
        ("object_state", "exists_same_table"),
        ("privilege_level", "non_owner"),
        ("expression_compatibility", "select_with_check_incompatible"),
        ("expression_compatibility", "insert_with_using_incompatible"),
        ("expression_compatibility", "delete_with_check_incompatible"),
    }
)

_COMBINATION_GROUP = "create_policy_required_factor_value_matrix"

_CONSUMER_ACTION = "create_policy"

# Which expression_compatibility values are valid for each command_type.
_COMPAT_BY_COMMAND: dict[str, frozenset[str]] = {
    "ALL": frozenset({"compatible_pairing"}),
    "SELECT": frozenset(
        {"compatible_pairing", "select_with_check_incompatible"}
    ),
    "INSERT": frozenset(
        {"compatible_pairing", "insert_with_using_incompatible"}
    ),
    "UPDATE": frozenset({"compatible_pairing"}),
    "DELETE": frozenset(
        {"compatible_pairing", "delete_with_check_incompatible"}
    ),
}


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    """Consistency + at-most-one-failure attribution."""

    ct = assignment.get("command_type", "ALL")
    ec = assignment.get(
        "expression_compatibility", "compatible_pairing"
    )
    if ec not in _COMPAT_BY_COMMAND.get(ct, frozenset()):
        return False

    failures = [
        pair
        for pair in _CROSSED_NEGATIVES
        if assignment.get(pair[0]) == pair[1]
    ]
    return len(failures) <= 1


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors from T1-T4 values in extension."""

    os = a.get("object_state", "not_exists")
    if os == "exists_same_table":
        a["duplicate_policy_name"] = "same_table_same_name"
        a["policy_name_shape"] = "duplicate_name_same_table"
    elif os == "exists_different_table":
        a["duplicate_policy_name"] = "no_conflict"
        a["policy_name_shape"] = "duplicate_name_different_table"
    else:
        a["duplicate_policy_name"] = "no_conflict"

    te = a.get("table_existence", "table_exists")
    if te == "table_not_exists":
        a["nonexistent_table"] = "table_missing"
        a["table_name_shape"] = "nonexistent_table"
    else:
        a["nonexistent_table"] = "table_exists"

    rls = a.get("rls_enabled", "rls_enabled")
    if rls == "rls_not_enabled":
        a["rls_not_enabled"] = "rls_not_enabled"
    else:
        a["rls_not_enabled"] = "rls_enabled"

    pl = a.get("privilege_level", "superuser")
    if pl == "non_owner":
        a["privilege_denied"] = "non_owner_denied"
    elif pl == "table_owner":
        a["privilege_denied"] = "owner_execution"
    else:
        a["privilege_denied"] = "superuser_execution"

    ec = a.get("expression_compatibility", "compatible_pairing")
    if ec == "select_with_check_incompatible":
        a["select_with_check_conflict"] = "incompatible_with_check"
    else:
        a["select_with_check_conflict"] = "compatible_no_with_check"

    if ec == "insert_with_using_incompatible":
        a["insert_with_using_conflict"] = "incompatible_using"
    else:
        a["insert_with_using_conflict"] = "compatible_no_using"

    orp = a.get("only_restrictive_policy", "has_permissive_policy")
    if orp == "only_restrictive_no_permissive":
        a["policy_type"] = "restrictive"


def _derive_expressions(a: dict[str, str]) -> None:
    """Derive using_expression and with_check_expression from
    expression_compatibility and command_type."""

    ct = a.get("command_type", "ALL")
    ec = a.get("expression_compatibility", "compatible_pairing")

    if ec == "select_with_check_incompatible":
        a["using_expression"] = "omitted"
        a["with_check_expression"] = "simple_boolean_expr"
    elif ec == "insert_with_using_incompatible":
        a["using_expression"] = "simple_boolean_expr"
        a["with_check_expression"] = "omitted"
    elif ec == "delete_with_check_incompatible":
        a["using_expression"] = "simple_boolean_expr"
        a["with_check_expression"] = "simple_boolean_expr"
    else:
        # compatible_pairing
        if ct in {"ALL", "UPDATE"}:
            a["using_expression"] = "simple_boolean_expr"
            a["with_check_expression"] = "simple_boolean_expr"
        elif ct in {"SELECT", "DELETE"}:
            a["using_expression"] = "simple_boolean_expr"
            a["with_check_expression"] = "omitted"
        elif ct == "INSERT":
            a["using_expression"] = "omitted"
            a["with_check_expression"] = "simple_boolean_expr"


def _failure_conditions(a: dict[str, str]) -> list[str]:
    """Return list of active failure condition names."""

    conditions: list[str] = []
    os = a.get("object_state", "not_exists")
    if os == "exists_same_table":
        conditions.append("duplicate")
    pl = a.get("privilege_level", "superuser")
    if pl == "non_owner":
        conditions.append("insufficient_privilege")
    ec = a.get("expression_compatibility", "compatible_pairing")
    if ec != "compatible_pairing":
        conditions.append("incompatible_expression")
    return conditions


_FAILURE_SQLSTATE = {
    "duplicate": ("42710", "duplicate_policy_provisional"),
    "insufficient_privilege": (
        "42501",
        "insufficient_privilege_provisional",
    ),
    "incompatible_expression": (
        "42601",
        "syntax_error_provisional",
    ),
}


def _behavior_combinations() -> list[dict[str, str]]:
    """Cartesian product of general + expression axes, filtered."""

    general_items = list(_GENERAL_AXES.items())
    expr_items = list(_EXPRESSION_AXES.items())

    all_keys = [k for k, _ in general_items] + [
        k for k, _ in expr_items
    ]
    all_value_lists = (
        [v for _, v in general_items]
        + [v for _, v in expr_items]
    )

    combos: list[dict[str, str]] = []
    for values in itertools.product(*all_value_lists):
        assignment = dict(zip(all_keys, values))
        if _is_valid_combination(assignment):
            combos.append(assignment)
    return combos


def _full_assignment(
    behavior: dict[str, str],
    verification: str,
    cleanup: str,
) -> dict[str, str]:
    a: dict[str, str] = dict(_BASELINE_DEFAULTS)
    a["statement_branch"] = "branch_create_policy"
    for key, value in behavior.items():
        a[key] = value
    a["verification_mode"] = verification
    a["cleanup_mode"] = cleanup
    _derive_t5_factors(a)
    _derive_expressions(a)
    failures = _failure_conditions(a)
    a["expected_status"] = "failure" if failures else "success"
    return a


def _present_failure_pair(
    a: dict[str, str],
) -> tuple[str, str] | None:
    """Return the (factor, value) pair representing the active failure."""

    os = a.get("object_state", "not_exists")
    if os == "exists_same_table":
        return ("object_state", "exists_same_table")
    pl = a.get("privilege_level", "superuser")
    if pl == "non_owner":
        return ("privilege_level", "non_owner")
    ec = a.get("expression_compatibility", "compatible_pairing")
    if ec != "compatible_pairing":
        return ("expression_compatibility", ec)
    return None


def _extension_multiset_sha256(
    cases: tuple[CreatePolicyFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-policy-factor-extension-v1\n"
    )
    for case in cases:
        digest.update(
            json.dumps(
                {
                    "ordinal": case.ordinal,
                    "case_id": case.case_id,
                    "derivation_id": case.derivation_id,
                    "derived_from_combination_group": (
                        case.derived_from_combination_group
                    ),
                    "derivation_reason": case.derivation_reason,
                    "factor_assignment": [
                        list(item) for item in case.factor_assignment
                    ],
                    "consumer_action_id": case.consumer_action_id,
                    "outcome": case.outcome,
                    "expected_sqlstate": case.expected_sqlstate,
                    "expected_failure_reason": (
                        case.expected_failure_reason
                    ),
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        digest.update(b"\n")
    return digest.hexdigest()


def build_create_policy_factor_extension_plan(
    repository_root: Path,
) -> CreatePolicyFactorExtensionPlan:
    """Build the bounded post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    # Confirm the universe is loadable (same as baseline check).
    from .applicability import load_shipped_applicability_universe

    catalog_rows = load_shipped_applicability_universe(
        root
    ).rows_for_statement("create_policy")
    if len(catalog_rows) != 80:
        raise CreatePolicyFactorExtensionError(
            "catalog row count drift"
        )

    cases: list[CreatePolicyFactorExtensionCase] = []
    raw_count = 0
    ordinal = _BASELINE_COUNT

    behavior_combos = _behavior_combinations()
    for behavior in behavior_combos:
        for verification in _VERIFICATION_MODES:
            for cleanup in _CLEANUP_MODES:
                raw_count += 1
                full = _full_assignment(
                    behavior, verification, cleanup
                )
                failures = _failure_conditions(full)
                if len(failures) > 1:
                    continue
                if failures:
                    condition = failures[0]
                    sqlstate, reason = _FAILURE_SQLSTATE[condition]
                    outcome = "expected_failure"
                else:
                    sqlstate = "00000"
                    reason = None
                    outcome = "success"
                ordinal += 1
                sorted_assignment = tuple(sorted(full.items()))
                derivation_id = (
                    f"CPOL-EXT|{ordinal:05d}|"
                    f"{verification}|{cleanup}"
                )
                cases.append(
                    CreatePolicyFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"CREATEPOLICY{ordinal:05d}",
                        sql_filename=f"CREATEPOLICY{ordinal:05d}.sql",
                        object_prefix=f"createpolicy_{ordinal:05d}_",
                        derivation_id=derivation_id,
                        derived_from_combination_group=_COMBINATION_GROUP,
                        derivation_reason=(
                            f"CREATE POLICY extension: "
                            f"policy_type={behavior.get('policy_type')}, "
                            f"command_type={behavior.get('command_type')}, "
                            f"object_state={behavior.get('object_state')}, "
                            f"privilege_level={behavior.get('privilege_level')}, "
                            f"expression_compatibility={behavior.get('expression_compatibility')}, "
                            f"verification={verification}, "
                            f"cleanup={cleanup}"
                        ),
                        factor_assignment=sorted_assignment,
                        consumer_action_id=_CONSUMER_ACTION,
                        outcome=outcome,
                        expected_sqlstate=sqlstate,
                        expected_failure_reason=reason,
                    )
                )

    dropped = max(0, raw_count - _CAP)
    if dropped > 0:
        cases = cases[: _CAP]

    plan = CreatePolicyFactorExtensionPlan(
        cases=tuple(cases),
        extension_multiset_sha256=_extension_multiset_sha256(
            tuple(cases)
        ),
        raw_combination_count=raw_count,
        dropped_combination_count=dropped,
    )

    expected_min = 1000 - _BASELINE_COUNT
    if len(plan.cases) < expected_min:
        raise CreatePolicyFactorExtensionError(
            f"extension case count below threshold: {len(plan.cases)}"
        )
    if len(plan.cases) > _CAP:
        raise CreatePolicyFactorExtensionError(
            "extension case count exceeds cap"
        )
    ordinals = [case.ordinal for case in plan.cases]
    if ordinals != list(
        range(
            _BASELINE_COUNT + 1,
            _BASELINE_COUNT + 1 + len(plan.cases),
        )
    ):
        raise CreatePolicyFactorExtensionError(
            "extension ordinal gap"
        )
    if len({case.case_id for case in plan.cases}) != len(plan.cases):
        raise CreatePolicyFactorExtensionError(
            "duplicate extension case_id"
        )
    if len({case.sql_filename for case in plan.cases}) != len(
        plan.cases
    ):
        raise CreatePolicyFactorExtensionError(
            "duplicate extension sql_filename"
        )
    if not all(
        case.outcome == "success"
        or case.outcome == "expected_failure"
        for case in plan.cases
    ):
        raise CreatePolicyFactorExtensionError(
            "unknown extension outcome"
        )
    if not all(
        case.derivation_id.startswith("CPOL-EXT|")
        for case in plan.cases
    ):
        raise CreatePolicyFactorExtensionError(
            "extension derivation_id prefix drift"
        )
    return plan


__all__ = [
    "CreatePolicyFactorExtensionError",
    "CreatePolicyFactorExtensionCase",
    "CreatePolicyFactorExtensionPlan",
    "build_create_policy_factor_extension_plan",
    "_BASELINE_COUNT",
    "_CAP",
    "_VERIFICATION_MODES",
    "_CLEANUP_MODES",
    "_CROSSED_NEGATIVES",
    "_present_failure_pair",
    "_extension_multiset_sha256",
]
