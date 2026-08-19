"""Bounded Option-A post-coverage extension expander for ALTER OPERATOR FAMILY.

Crosses the positive behaviour axes of each synopsis branch with at most one
failure-causing value per case (clean attribution), then crosses the result
with the verification-mode (T6) and cleanup-mode (T6) axes.  The marginal
baseline (59 cases) already witnesses every factor value once; this expander
witnesses the *combinations* that a single-factor marginal sweep cannot.

``ALTER OPERATOR FAMILY`` is the element-membership sibling of ``ALTER OPERATOR
CLASS``: the ``ADD`` / ``DROP`` branches manipulate operator/function members
of a family, so the element-shape axes (``add_element_type``,
``drop_element_type``, ``element_op_type``, ``dependency_state``,
``index_method_compatibility``) are crossed on those two branches.  The
``RENAME`` / ``OWNER`` / ``SET SCHEMA`` branches reuse the rename-conflict,
owner-transfer (SESSION_USER no-op salvage) and schema-migration crosses from
``alter_operator_class`` / ``alter_large_object``.

The owner-transfer branch (``branch_owner``) reuses the SESSION_USER no-op
transfer salvage: under a non-owner session, ``OWNER TO SESSION_USER`` is a
permitted no-op transfer (PG 18.4), so the privilege boundary does not fire for
the ``session_user`` owner shape.  ``index_method_compatibility`` and
``element_op_type`` are success-variant axes (PG accepts the element membership
at ALTER time without deep semantic validation); the DB doublerun fork
calibrates if a variant surfaces a real rejection.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json


class AlterOperatorFamilyFactorExtensionError(ValueError):
    """Raised when a frozen ALTER OPERATOR FAMILY extension input drifts."""


@dataclass(frozen=True)
class AlterOperatorFamilyFactorExtensionCase:
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
    is_extension: bool


@dataclass(frozen=True)
class AlterOperatorFamilyFactorExtensionPlan:
    cases: tuple[AlterOperatorFamilyFactorExtensionCase, ...]
    extension_multiset_sha256: str


_BASELINE_COUNT = 59
_CAP = 20000

_VERIFICATION_MODES = ("catalog_query", "effect_query", "error_assertion")
_CLEANUP_MODES = ("drop_objects", "reset_state")

_PRIVILEGE_CLUSTER_VALUES = frozenset({"non_owner", "insufficient_privilege"})

_BRANCH_FIXED_ACTION: dict[str, str] = {
    "branch_add": "add_elements",
    "branch_drop": "drop_elements",
    "branch_rename": "rename",
    "branch_owner": "owner_change",
    "branch_set_schema": "set_schema",
}

_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_add",
    "grammar_branch": "branch_add",
    "target_action": "add_elements",
    "alter_action_type": "add_elements",
    "target_object_state": "exists",
    "expected_status": "success",
    "add_element_type": "add_operator_for_search",
    "drop_element_type": "drop_operator",
    "element_op_type": "integer",
    "dependency_state": "ready",
    "index_method_compatibility": "compatible",
    "index_method_shape": "btree",
    "new_owner_shape": "plain_role",
    "privilege_context": "superuser",
    "ownership_boundary": "superuser",
    "name_shape": "plain_identifier",
    "rename_conflict": "new_name_available",
    "schema_migration_state": "target_schema_exists",
    "invalid_combination": "none",
    "verification_mode": "catalog_query",
    "cleanup_mode": "drop_objects",
}

# Per-branch behaviour axes.  Only axes that carry at least one failure value
# (or a meaningfully varying positive value) are crossed; statement-wide
# modifiers absent from a branch are held at their baseline default.  The
# ownership_boundary axis is crossed only on the owner-transfer branch (it is
# the privilege locus there); add/drop/rename/schema rely on privilege_context.
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_add": {
        "add_element_type": (
            "add_operator_for_search",
            "add_operator_for_order_by",
            "add_function",
        ),
        "element_op_type": ("integer", "text", "custom_type", "none_prefix_operator"),
        "dependency_state": (
            "ready",
            "missing_operator",
            "missing_function",
            "missing_family",
        ),
        "index_method_compatibility": ("compatible", "incompatible"),
        "target_object_state": ("exists", "missing"),
        "privilege_context": (
            "superuser",
            "owner",
            "non_owner",
            "insufficient_privilege",
        ),
    },
    "branch_drop": {
        "drop_element_type": ("drop_operator", "drop_function"),
        "element_op_type": ("integer", "text", "custom_type", "none_prefix_operator"),
        "dependency_state": (
            "ready",
            "missing_operator",
            "missing_function",
            "missing_family",
        ),
        "index_method_compatibility": ("compatible", "incompatible"),
        "target_object_state": ("exists", "missing"),
        "privilege_context": (
            "superuser",
            "owner",
            "non_owner",
            "insufficient_privilege",
        ),
    },
    "branch_owner": {
        "new_owner_shape": (
            "plain_role",
            "current_role",
            "current_user",
            "session_user",
            "missing_role",
        ),
        "target_object_state": ("exists", "missing"),
        "privilege_context": (
            "superuser",
            "owner",
            "non_owner",
            "insufficient_privilege",
        ),
        "ownership_boundary": ("superuser", "owner", "non_owner"),
        "name_shape": ("plain_identifier", "schema_qualified", "quoted_identifier"),
    },
    "branch_rename": {
        "rename_conflict": ("new_name_available", "new_name_conflict"),
        "target_object_state": ("exists", "missing"),
        "privilege_context": (
            "superuser",
            "owner",
            "non_owner",
            "insufficient_privilege",
        ),
        "name_shape": ("plain_identifier", "schema_qualified", "quoted_identifier"),
    },
    "branch_set_schema": {
        "schema_migration_state": (
            "target_schema_exists",
            "target_schema_missing",
            "target_schema_conflict",
        ),
        "target_object_state": ("exists", "missing"),
        "privilege_context": (
            "superuser",
            "owner",
            "non_owner",
            "insufficient_privilege",
        ),
        "name_shape": ("plain_identifier", "schema_qualified", "quoted_identifier"),
    },
}

# (factor, value) pairs that, when active, reach a PG 18.4 rejection.
# ``index_method_compatibility`` and ``element_op_type`` are intentionally
# absent: they are success-variant axes (PG accepts the element at ALTER time).
_CROSSED_BEHAVIOUR_NEGATIVES: frozenset[tuple[str, str]] = frozenset(
    {
        ("target_object_state", "missing"),
        ("dependency_state", "missing_operator"),
        ("dependency_state", "missing_function"),
        ("dependency_state", "missing_family"),
        ("new_owner_shape", "missing_role"),
        ("rename_conflict", "new_name_conflict"),
        ("schema_migration_state", "target_schema_missing"),
        ("schema_migration_state", "target_schema_conflict"),
        ("invalid_combination", "syntax_valid_semantic_error"),
        ("invalid_combination", "object_type_mismatch"),
    }
)

_SQLSTATE_BY_REASON: dict[str, tuple[str, str]] = {
    "operator_family_does_not_exist": ("42704", "operator_family_does_not_exist"),
    "missing_operator_element": ("42883", "missing_operator_element"),
    "missing_function_element": ("42883", "missing_function_element"),
    "missing_owner_role": ("42704", "missing_owner_role"),
    "operator_family_name_conflict": ("42710", "operator_family_name_conflict"),
    "missing_target_schema": ("3F000", "missing_target_schema"),
    "operator_family_schema_conflict": ("42710", "operator_family_schema_conflict"),
    "invalid_operator_family_alter_combination": (
        "42601",
        "invalid_operator_family_alter_combination",
    ),
    "wrong_object_type": ("42809", "wrong_object_type"),
    "insufficient_operator_family_privilege": (
        "42501",
        "insufficient_operator_family_privilege",
    ),
}


def _privilege_boundary_fires(assignment: dict[str, str]) -> bool:
    """SESSION USER owner target is a permitted no-op transfer (PG 18.4)."""

    return assignment.get("new_owner_shape") != "session_user"


def _privilege_cluster_fires(
    branch: str,
    assignment: dict[str, str],
) -> bool:
    if assignment.get("privilege_context") not in _PRIVILEGE_CLUSTER_VALUES:
        return False
    if branch == "branch_owner":
        return _privilege_boundary_fires(assignment)
    return True


def _ownership_fires(assignment: dict[str, str]) -> bool:
    # SESSION USER owner target is a permitted no-op transfer for non-owners,
    # so the ownership boundary is subsumed (does not fire) in that case.
    if assignment.get("new_owner_shape") == "session_user":
        return False
    return assignment.get("ownership_boundary") == "non_owner"


def _active_negatives(assignment: dict[str, str]) -> list[tuple[str, str]]:
    active: list[tuple[str, str]] = []
    for factor, value in assignment.items():
        if (factor, value) not in _CROSSED_BEHAVIOUR_NEGATIVES:
            continue
        active.append((factor, value))
    return active


def _failure_unit_count(branch: str, assignment: dict[str, str]) -> int:
    units = 0
    if _privilege_cluster_fires(branch, assignment):
        units += 1
    if branch == "branch_owner" and _ownership_fires(assignment):
        units += 1
    units += len(_active_negatives(assignment))
    return units


def _present_failure_pair(
    branch: str,
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    # 1. Privilege wall (owner-transfer boundary, when it fires).
    if _privilege_cluster_fires(branch, assignment):
        return _SQLSTATE_BY_REASON["insufficient_operator_family_privilege"]
    if branch == "branch_owner" and _ownership_fires(assignment):
        return _SQLSTATE_BY_REASON["insufficient_operator_family_privilege"]
    # 2. Object-type / syntax-semantic negatives.
    invalid = assignment.get("invalid_combination", "none")
    if invalid == "object_type_mismatch":
        return _SQLSTATE_BY_REASON["wrong_object_type"]
    if invalid == "syntax_valid_semantic_error":
        return _SQLSTATE_BY_REASON["invalid_operator_family_alter_combination"]
    # 3. Family-absence negatives (missing family or missing_family dependency).
    if assignment.get("dependency_state") == "missing_family":
        return _SQLSTATE_BY_REASON["operator_family_does_not_exist"]
    if assignment.get("target_object_state") == "missing":
        return _SQLSTATE_BY_REASON["operator_family_does_not_exist"]
    # 4. Element-absence negatives (ADD/DROP of a missing operator/function).
    if assignment.get("dependency_state") == "missing_operator":
        return _SQLSTATE_BY_REASON["missing_operator_element"]
    if assignment.get("dependency_state") == "missing_function":
        return _SQLSTATE_BY_REASON["missing_function_element"]
    # 5. Remaining rename / schema negatives.
    if assignment.get("rename_conflict") == "new_name_conflict":
        return _SQLSTATE_BY_REASON["operator_family_name_conflict"]
    schema = assignment.get("schema_migration_state")
    if schema == "target_schema_missing":
        return _SQLSTATE_BY_REASON["missing_target_schema"]
    if schema == "target_schema_conflict":
        return _SQLSTATE_BY_REASON["operator_family_schema_conflict"]
    if assignment.get("new_owner_shape") == "missing_role":
        return _SQLSTATE_BY_REASON["missing_owner_role"]
    return None


def _is_valid_combination(branch: str, assignment: dict[str, str]) -> bool:
    # At most one failure-causing unit per case (clean attribution).
    if _failure_unit_count(branch, assignment) > 1:
        return False
    # A missing family has nothing to add/drop/rename/re-own; the
    # family-absence negative crosses only against the success baseline for
    # negatives that presume a present family.
    family_missing = (
        assignment.get("target_object_state") == "missing"
        or assignment.get("dependency_state") == "missing_family"
    )
    if family_missing:
        if assignment.get("rename_conflict") == "new_name_conflict":
            return False
        schema = assignment.get("schema_migration_state")
        if schema in ("target_schema_missing", "target_schema_conflict"):
            return False
        if assignment.get("dependency_state") in ("missing_operator", "missing_function"):
            return False
    return True


def _outcome_for(
    branch: str,
    assignment: dict[str, str],
) -> tuple[str, str, str | None]:
    pair = _present_failure_pair(branch, assignment)
    if pair is None:
        return ("success", "00000", None)
    sqlstate, reason = pair
    return ("expected_failure", sqlstate, reason)


def _branch_assignments(
    branch: str,
    axis_assignment: dict[str, str],
) -> dict[str, str]:
    assignment = dict(_BASELINE_DEFAULTS)
    action = _BRANCH_FIXED_ACTION[branch]
    assignment["statement_branch"] = branch
    assignment["grammar_branch"] = branch
    assignment["target_action"] = action
    assignment["alter_action_type"] = action
    assignment.update(axis_assignment)
    return assignment


def _behavior_combinations(
    branch: str,
) -> list[dict[str, str]]:
    axes = _BRANCH_AXES[branch]
    keys = tuple(axes.keys())
    combinations: list[dict[str, str]] = []
    for values in itertools.product(*(axes[k] for k in keys)):
        axis_assignment = dict(zip(keys, values))
        assignment = _branch_assignments(branch, axis_assignment)
        if not _is_valid_combination(branch, assignment):
            continue
        outcome, sqlstate, reason = _outcome_for(branch, assignment)
        if outcome != "success" and sqlstate == "00000":
            continue
        assignment["expected_status"] = outcome
        combinations.append(assignment)
    combinations.sort(key=lambda a: tuple(sorted(a.items())))
    return combinations


def _extension_multiset_sha256(
    cases: tuple[AlterOperatorFamilyFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"alter-operator-family-factor-extension-v1\n")
    for case in cases:
        digest.update(
            json.dumps(
                {
                    "derivation_id": case.derivation_id,
                    "factor_assignment": list(case.factor_assignment),
                    "outcome": case.outcome,
                    "expected_sqlstate": case.expected_sqlstate,
                    "expected_failure_reason": case.expected_failure_reason,
                    "consumer_action_id": case.consumer_action_id,
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        digest.update(b"\n")
    return digest.hexdigest()


def build_alter_operator_family_factor_extension_plan(
    repository_root,  # noqa: ARG001 - reserved for API parity
) -> AlterOperatorFamilyFactorExtensionPlan:
    """Build the bounded post-coverage extension plan (Option A)."""

    cases: list[AlterOperatorFamilyFactorExtensionCase] = []
    truncated = False
    for branch in (
        "branch_add",
        "branch_drop",
        "branch_rename",
        "branch_owner",
        "branch_set_schema",
    ):
        action = _BRANCH_FIXED_ACTION[branch]
        for assignment in _behavior_combinations(branch):
            for verification in _VERIFICATION_MODES:
                for cleanup in _CLEANUP_MODES:
                    if len(cases) >= _CAP:
                        truncated = True
                        break
                    case_assignment = dict(assignment)
                    case_assignment["verification_mode"] = verification
                    case_assignment["cleanup_mode"] = cleanup
                    outcome, sqlstate, reason = _outcome_for(
                        branch, case_assignment
                    )
                    ordinal = len(cases) + 1 + _BASELINE_COUNT
                    derivation_id = (
                        f"AOF-EXT|{ordinal:05d}|{action}|"
                        f"{verification}|{cleanup}"
                    )
                    cases.append(
                        AlterOperatorFamilyFactorExtensionCase(
                            ordinal=ordinal,
                            case_id=f"ALTEROPERATORFAMILY{ordinal:05d}",
                            sql_filename=f"ALTEROPERATORFAMILY{ordinal:05d}.sql",
                            object_prefix=f"alteroperatorfamily_{ordinal:05d}_",
                            derivation_id=derivation_id,
                            derived_from_combination_group=branch,
                            derivation_reason=(
                                f"bounded_cross_{branch}_"
                                f"{verification}_{cleanup}"
                            ),
                            factor_assignment=tuple(
                                sorted(case_assignment.items())
                            ),
                            consumer_action_id=action,
                            outcome=outcome,
                            expected_sqlstate=sqlstate,
                            expected_failure_reason=reason,
                            is_extension=True,
                        )
                    )
                if truncated:
                    break
            if truncated:
                break
        if truncated:
            break
    if truncated:
        raise AlterOperatorFamilyFactorExtensionError(
            "extension cap truncation occurred (review axes)"
        )
    plan = AlterOperatorFamilyFactorExtensionPlan(
        cases=tuple(cases),
        extension_multiset_sha256=_extension_multiset_sha256(tuple(cases)),
    )
    return plan


__all__ = [
    "AlterOperatorFamilyFactorExtensionError",
    "AlterOperatorFamilyFactorExtensionCase",
    "AlterOperatorFamilyFactorExtensionPlan",
    "build_alter_operator_family_factor_extension_plan",
    "_extension_multiset_sha256",
]
