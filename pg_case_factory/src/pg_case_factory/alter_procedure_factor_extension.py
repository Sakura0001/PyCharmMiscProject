"""Bounded post-coverage cross-factor extension expander for ALTER PROCEDURE.

The marginal factor-value-loop (:mod:`alter_procedure_factor_loop`) is the
required baseline: one program per factor value, 94 local cases
(GRM 22 + SFV 70 + RISK 2).  This module adds the bounded post-coverage
extension phase allowed by ``alter_procedure.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor combinations
of the positive T1-T4 behaviour axes (at most one failure-causing value per
case, so attribution stays clean), with ``verification_mode`` crossed and
``cleanup_mode`` crossed so every declared T6 value is exercised.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``derived_extension_required_fields``) and is marked ``is_extension = True``.

SESSION_USER owner-transfer no-op: ``OWNER TO SESSION_USER`` is a permitted
no-op transfer (PG 18.4 allows it even for non-owners), so the privilege
boundary does not fire for ``owner_target = SESSION_USER``.  Only
``new_owner_role`` requires role membership under a non-superuser procedure
owner (42501); ``CURRENT_ROLE`` and ``CURRENT_USER`` correctly fail 42501
under a non-owner session (attributed via the privilege cluster).
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .alter_procedure_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_alter_procedure_factor_loop_plan,
)


class AlterProcedureFactorExtensionError(ValueError):
    """Raised when a frozen ALTER PROCEDURE extension input drifts."""


@dataclass(frozen=True)
class AlterProcedureFactorExtensionCase:
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
class AlterProcedureFactorExtensionPlan:
    cases: tuple[AlterProcedureFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 94
# Safety backstop only; the natural at-most-one-failure cross is expected to
# stay well under this cap so no coverage-losing truncation occurs.  The
# exact frozen count is asserted in the companion test.
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_proc_catalog_query",
    "information_schema_routines",
    "pg_get_functiondef",
)
_CLEANUP_MODES = (
    "DROP_PROCEDURE",
    "DROP_PROCEDURE_IF_EXISTS",
    "DROP_PROCEDURE_CASCADE",
)

# Actions whose clause carries a configuration parameter; only these can
# surface the configuration_parameter_shape=invalid_parameter failure.
_CONFIG_ACTIONS = frozenset({"set_parameter", "reset_parameter", "reset_all"})

# Reserved schemas: ALTER PROCEDURE ... SET SCHEMA <reserved> surfaces 42501
# only under a non-superuser owner (gotcha #4).  Pairing them with
# privilege_level=superuser is semantically invalid for the extension.
_RESERVED_SCHEMA_TARGETS = frozenset(
    {"pg_catalog_reserved", "information_schema_reserved"}
)

# Privilege cluster: both non-owner privilege levels model the same
# must_be_owner_of_procedure (42501) boundary and are counted as a single
# attributable failure unit.
_PRIVILEGE_CLUSTER_VALUES = frozenset(
    {"non_owner_with_alter", "non_owner_no_privilege"}
)
# SESSION_USER is a permitted no-op transfer (PG 18.4 allows even for
# non-owners), so it escapes the privilege boundary.  Only new_owner_role
# requires role membership under a non-superuser procedure owner (42501).
_SESSION_USER_ESCAPE = "SESSION_USER"
_OWNER_TARGET_REQUIRES_MEMBERSHIP = frozenset({"new_owner_role"})

# Dense baseline assignment (all positive T1-T4 + T6 + GRM-axis baselines).
# The T5 negative factors are intentionally absent: they are owned
# one-per-value by the marginal baseline and are never crossed here, so the
# at-most-one-failure attribution stays clean.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_1",
    "grammar_branch": "branch_action_form",
    "target_action": "security_invoker",
    "object_state": "exists",
    "expected_status": "success",
    "restrict_clause": "absent",
    "rename_target": "simple",
    "owner_target": "new_owner_role",
    "schema_target": "schema_exists",
    "extension_target": "extension_exists",
    "argtype_specification": "with_full_signature",
    "procedure_name_shape": "simple",
    "new_name_shape": "simple",
    "configuration_parameter_shape": "valid_parameter",
    "privilege_level": "superuser",
    "schema_dependency": "target_schema_exists",
    "role_dependency": "owner_role_exists",
    "extension_dependency": "extension_installed",
    "verification_mode": "pg_proc_catalog_query",
    "cleanup_mode": "DROP_PROCEDURE_IF_EXISTS",
    "action_list_cardinality": "one_action",
    "set_assignment_form": "to_value",
    "external_keyword": "omitted",
    "depends_polarity": "depends",
}

# Official synopsis branch -> grammar_branch id used by the renderer.
_BRANCH_GRAMMAR = {
    "branch_1": "branch_action_form",
    "branch_2": "branch_rename",
    "branch_3": "branch_owner",
    "branch_4": "branch_set_schema",
    "branch_5": "branch_depends_extension",
}

# Fixed consumer action for branches 2-5 (branch_1 takes its crossed
# target_action value as the consumer action id).
_BRANCH_FIXED_ACTION = {
    "branch_2": "rename",
    "branch_3": "owner",
    "branch_4": "set_schema",
    "branch_5": "depends_on_extension",
}

# Crossed positive behaviour axes per branch.  branch_1 crosses all 5 action
# types (the complete procedure action set); configuration_parameter_shape is
# crossed but invalid_parameter is only applicable to the set/reset actions
# (filtered in _is_valid_combination).
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_1": {
        "target_action": (
            "security_invoker",
            "security_definer",
            "set_parameter",
            "reset_parameter",
            "reset_all",
        ),
        "object_state": (
            "exists",
            "not_exists",
            "different_signature_exists",
        ),
        "argtype_specification": (
            "with_full_signature",
            "with_partial_signature",
            "without_signature",
        ),
        "procedure_name_shape": (
            "simple",
            "quoted",
            "reserved_word",
            "schema_qualified",
        ),
        "privilege_level": (
            "superuser",
            "procedure_owner",
            "non_owner_with_alter",
            "non_owner_no_privilege",
        ),
        "restrict_clause": ("present", "absent"),
        "configuration_parameter_shape": (
            "valid_parameter",
            "invalid_parameter",
        ),
    },
    "branch_2": {
        "new_name_shape": ("simple", "quoted", "reserved_word"),
        "rename_target": (
            "simple",
            "quoted",
            "reserved_word",
            "duplicate_name",
        ),
        "object_state": (
            "exists",
            "not_exists",
            "different_signature_exists",
        ),
        "procedure_name_shape": (
            "simple",
            "quoted",
            "reserved_word",
            "schema_qualified",
        ),
        "privilege_level": (
            "superuser",
            "procedure_owner",
            "non_owner_with_alter",
            "non_owner_no_privilege",
        ),
    },
    "branch_3": {
        "owner_target": (
            "new_owner_role",
            "CURRENT_ROLE",
            "CURRENT_USER",
            "SESSION_USER",
            "nonexistent_role",
        ),
        "object_state": (
            "exists",
            "not_exists",
            "different_signature_exists",
        ),
        "procedure_name_shape": (
            "simple",
            "quoted",
            "reserved_word",
            "schema_qualified",
        ),
        "privilege_level": (
            "superuser",
            "procedure_owner",
            "non_owner_with_alter",
            "non_owner_no_privilege",
        ),
        "role_dependency": ("owner_role_exists", "owner_role_not_exists"),
    },
    "branch_4": {
        "schema_target": (
            "schema_exists",
            "schema_not_exists",
            "pg_catalog_reserved",
            "information_schema_reserved",
        ),
        "object_state": (
            "exists",
            "not_exists",
            "different_signature_exists",
        ),
        "procedure_name_shape": (
            "simple",
            "quoted",
            "reserved_word",
            "schema_qualified",
        ),
        "privilege_level": (
            "superuser",
            "procedure_owner",
            "non_owner_with_alter",
            "non_owner_no_privilege",
        ),
        "schema_dependency": (
            "target_schema_exists",
            "target_schema_not_exists",
            "reserved_schema",
        ),
    },
    "branch_5": {
        "extension_target": (
            "extension_exists",
            "extension_not_exists",
            "NO_DEPENDS",
        ),
        "object_state": (
            "exists",
            "not_exists",
            "different_signature_exists",
        ),
        "procedure_name_shape": (
            "simple",
            "quoted",
            "reserved_word",
            "schema_qualified",
        ),
        "privilege_level": (
            "superuser",
            "procedure_owner",
            "non_owner_with_alter",
            "non_owner_no_privilege",
        ),
        "extension_dependency": (
            "extension_installed",
            "extension_not_installed",
        ),
    },
}

# Crossed behaviour-negative (factor, value) pairs.  The privilege cluster
# (privilege_level=non_owner_*) is counted as a single unit via
# _PRIVILEGE_CLUSTER_VALUES and is therefore not duplicated here.
_CROSSED_BEHAVIOUR_NEGATIVES = frozenset(
    {
        ("object_state", "not_exists"),
        ("object_state", "different_signature_exists"),
        ("argtype_specification", "with_partial_signature"),
        ("configuration_parameter_shape", "invalid_parameter"),
        ("rename_target", "duplicate_name"),
        ("owner_target", "nonexistent_role"),
        ("schema_target", "schema_not_exists"),
        ("schema_target", "pg_catalog_reserved"),
        ("schema_target", "information_schema_reserved"),
        ("extension_target", "extension_not_exists"),
        ("schema_dependency", "target_schema_not_exists"),
        ("schema_dependency", "reserved_schema"),
        ("role_dependency", "owner_role_not_exists"),
        ("extension_dependency", "extension_not_installed"),
    }
)


def _owner_privilege_failure(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """The role-membership wall (factor, value) pair firing here, else None.

    Under ``procedure_owner`` (a non-superuser owner), OWNER TO new_owner_role
    requires the issuer to be a member of that role, surfacing 42501 before the
    action takes effect.  SESSION_USER is a permitted no-op transfer and does
    NOT fire this wall.  Only ``procedure_owner`` is reachable: the non_owner
    cluster already attributes 42501 (must_be_owner) and superuser passes the
    membership check, so neither adds this unit.  Co-occurrence with a
    behaviour-negative is excluded by the at-most-one rule (the shadowed
    negative is never reached), so the kept cases carry this as the sole
    failure unit.
    """

    if assignment.get("privilege_level") != "procedure_owner":
        return None
    # owner_target is crossed only in branch_3; in the other branches it holds
    # its baseline value, so scoping the membership check on target_action
    # ("owner") keeps it from firing on unrelated branches where owner_target
    # is merely the inert baseline default.
    target_action = assignment.get("target_action")
    if (
        target_action == "owner"
        and assignment.get("owner_target") in _OWNER_TARGET_REQUIRES_MEMBERSHIP
    ):
        return ("owner_target", "membership_required_under_procedure_owner")
    return None


def _privilege_cluster_fires(assignment: dict[str, str]) -> bool:
    """The privilege wall firing for non-owners, EXCEPT SESSION_USER.

    SESSION_USER is a permitted no-op transfer (PG 18.4 allows even for
    non-owners), so the privilege boundary does not fire when
    ``owner_target = SESSION_USER``.  In branches other than branch_3,
    ``owner_target`` holds its baseline value (``new_owner_role``), so the
    escape only applies to the owner-transfer branch where it is crossed.
    """

    level = assignment.get("privilege_level")
    if level not in _PRIVILEGE_CLUSTER_VALUES:
        return False
    if assignment.get("owner_target") == _SESSION_USER_ESCAPE:
        return False
    return True


def _failure_unit_count(assignment: dict[str, str]) -> int:
    """Privilege cluster (1) + owner-privilege wall (1) + behaviour negatives.

    The privilege cluster (non_owner_*) and the owner-privilege wall
    (procedure_owner + role-membership) are mutually exclusive -- a case has
    exactly one privilege_level -- so the two never double-count.
    """

    cluster = 1 if _privilege_cluster_fires(assignment) else 0
    owner_priv = 1 if _owner_privilege_failure(assignment) else 0
    negatives = sum(
        1
        for factor, value in _CROSSED_BEHAVIOUR_NEGATIVES
        if assignment.get(factor) == value
    )
    return cluster + owner_priv + negatives


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success.

    The owner-privilege wall (role-membership) fires before the action takes
    effect, so it is attributed first when present (it shadows any
    co-occurring behaviour-negative, which the at-most-one rule has already
    excluded from the kept set).
    """

    pair = _owner_privilege_failure(assignment)
    if pair is not None:
        return pair
    if _privilege_cluster_fires(assignment):
        level = assignment.get("privilege_level")
        return ("privilege_level", level)
    for neg_factor, neg_value in _CROSSED_BEHAVIOUR_NEGATIVES:
        if assignment.get(neg_factor) == neg_value:
            return (neg_factor, neg_value)
    return None


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    """Branch-local applicability + at-most-one-failure attribution."""

    # configuration_parameter_shape=invalid_parameter is only reachable via a
    # SET/RESET action; pair it with any other action and the invalid GUC
    # never reaches the target check.
    if assignment.get("configuration_parameter_shape") == "invalid_parameter":
        if assignment.get("target_action") not in _CONFIG_ACTIONS:
            return False
    # Reserved-schema SET SCHEMA surfaces 42501 only under a non-superuser
    # owner (gotcha #4); the superuser pairing is semantically invalid.
    reserved_schema = (
        assignment.get("schema_target") in _RESERVED_SCHEMA_TARGETS
        or assignment.get("schema_dependency") == "reserved_schema"
    )
    if reserved_schema and assignment.get("privilege_level") == "superuser":
        return False
    return _failure_unit_count(assignment) <= 1


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments (T6 at baseline) passing the filter."""

    combos: list[dict[str, str]] = []
    for branch, axes in _BRANCH_AXES.items():
        names = list(axes)
        for values in itertools.product(*(axes[name] for name in names)):
            assignment: dict[str, str] = dict(_BASELINE_DEFAULTS)
            assignment["statement_branch"] = branch
            assignment["grammar_branch"] = _BRANCH_GRAMMAR[branch]
            if branch != "branch_1":
                assignment["target_action"] = _BRANCH_FIXED_ACTION[branch]
            for name, value in zip(names, values):
                assignment[name] = value
            if not _is_valid_combination(assignment):
                continue
            unit = _failure_unit_count(assignment)
            assignment["expected_status"] = (
                "failure" if unit == 1 else "success"
            )
            combos.append(assignment)
    return combos


def _outcome_for(
    assignment: dict[str, str],
) -> tuple[str, str, str | None]:
    """Derive (outcome, expected_sqlstate, expected_failure_reason).

    The role-membership wall (OWNER TO new_owner_role under procedure_owner) is
    surfaced by ``_present_failure_pair`` as the sentinel
    ``("owner_target", "membership_required_under_procedure_owner")`` pair,
    which ``_SFV_FAILURE_SQLSTATE`` maps to 42501.  Every other case is derived
    from its single attributable behaviour-negative pair.
    """

    pair = _present_failure_pair(assignment)
    if pair is None:
        return "success", "00000", None
    sqlstate, reason = _SFV_FAILURE_SQLSTATE[pair]
    return "expected_failure", sqlstate, reason


def _extension_multiset_sha256(
    cases: tuple[AlterProcedureFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"alter-procedure-factor-extension-v1\n")
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


def _derived_combinations_yaml(
    cases: tuple[AlterProcedureFactorExtensionCase, ...],
) -> str:
    """Emit the derived-extension ledger with the yaml required fields."""

    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"ALTER PROCEDURE extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "alter_procedure_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "ALTER PROCEDURE",
                    "primary_fence": "primary-target-begin/end",
                    "consumer_action_id": case.consumer_action_id,
                },
                "verification": {
                    "verification_mode": assignment["verification_mode"],
                    "expected_sqlstate": case.expected_sqlstate,
                },
                "cleanup": {
                    "cleanup_mode": assignment["cleanup_mode"],
                },
            }
        )
    return yaml.safe_dump(entries, sort_keys=False, allow_unicode=True)


def build_alter_procedure_factor_extension_plan(
    repository_root: Path,
) -> AlterProcedureFactorExtensionPlan:
    """Build the bounded ALTER PROCEDURE post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_alter_procedure_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    # Stable sort so any cap truncation is deterministic and interleaves
    # branches rather than favouring the first branch.
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[AlterProcedureFactorExtensionCase] = []
    ordinal = _BASELINE_COUNT
    raw = 0
    for behavior in behaviors:
        for verification in _VERIFICATION_MODES:
            for cleanup in _CLEANUP_MODES:
                raw += 1
                if len(cases) >= _CAP:
                    continue
                assignment: dict[str, str] = dict(behavior)
                assignment["verification_mode"] = verification
                assignment["cleanup_mode"] = cleanup
                outcome, sqlstate, reason = _outcome_for(assignment)
                ordinal += 1
                action = assignment["target_action"]
                cases.append(
                    AlterProcedureFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"ALTERPROCEDURE{ordinal:05d}",
                        sql_filename=f"ALTERPROCEDURE{ordinal:05d}.sql",
                        object_prefix=f"alterprocedure_{ordinal:05d}_",
                        derivation_id=(
                            f"AP-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "alter_procedure_required_baseline_factor_space"
                        ),
                        derivation_reason=(
                            f"cross-factor extension: statement_branch="
                            f"{assignment['statement_branch']} "
                            f"x verification_mode={verification} "
                            f"x cleanup_mode={cleanup}"
                        ),
                        factor_assignment=tuple(sorted(assignment.items())),
                        consumer_action_id=action,
                        outcome=outcome,
                        expected_sqlstate=sqlstate,
                        expected_failure_reason=reason,
                        is_extension=True,
                    )
                )
    dropped = max(0, raw - _CAP)
    cases_tuple = tuple(cases)
    return AlterProcedureFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "AlterProcedureFactorExtensionError",
    "AlterProcedureFactorExtensionCase",
    "AlterProcedureFactorExtensionPlan",
    "build_alter_procedure_factor_extension_plan",
]
