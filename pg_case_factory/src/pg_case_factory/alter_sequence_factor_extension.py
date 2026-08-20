"""Bounded post-coverage cross-factor extension expander for ALTER SEQUENCE.

The marginal factor-value-loop (:mod:`alter_sequence_factor_loop`) is the
required baseline: one program per factor value, 79 local cases
(GRM 8 + SFV 69 + RISK 2).  This module adds the bounded post-coverage
extension phase allowed by ``alter_sequence.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor combinations
of the positive T1-T4 behaviour axes (at most one failure-causing value per
case, so attribution stays clean), with ``verification_mode`` crossed and
``cleanup_mode`` crossed so every declared T6 value is exercised.

SESSION_USER owner-transfer escape: ``OWNER TO SESSION_USER`` is a
provisional permitted no-op transfer that escapes both the privilege cluster
(non_owner) and the SET-ROLE membership wall.  Under a non-superuser
sequence owner, OWNER TO with an explicit role fails 42501 (requires SET
ROLE membership); only ``SESSION_USER`` escapes (the membership wall is
excluded for it).  The DB phase must verify whether the escape truly holds
for sequence ownership semantics (which differ from publication ownership).
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .alter_sequence_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_alter_sequence_factor_loop_plan,
)


class AlterSequenceFactorExtensionError(ValueError):
    """Raised when a frozen ALTER SEQUENCE extension input drifts."""


@dataclass(frozen=True)
class AlterSequenceFactorExtensionCase:
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
class AlterSequenceFactorExtensionPlan:
    cases: tuple[AlterSequenceFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 79
# Safety backstop only; the natural at-most-one-failure cross is expected to
# stay well under this cap so no coverage-losing truncation occurs.
_CAP = 50000

_VERIFICATION_MODES = (
    "pg_class_catalog_query",
    "sequence_inspection_query",
    "nextval_call",
    "currval_call",
)
_CLEANUP_MODES = (
    "DROP_SEQUENCE",
    "DROP_SEQUENCE_IF_EXISTS",
    "DROP_SEQUENCE_CASCADE",
)

_BRANCH_ALTER_PARAMETERS = "branch_alter_parameters"
_BRANCH_SET_LOGGED_UNLOGGED = "branch_set_logged_unlogged"
_BRANCH_OWNER = "branch_owner"
_BRANCH_RENAME = "branch_rename"
_BRANCH_SET_SCHEMA = "branch_set_schema"

# Privilege cluster: the non_owner privilege level models the
# must_be_owner_of_sequence (42501) boundary and is counted as a single
# attributable failure unit.
_PRIVILEGE_CLUSTER_VALUES = frozenset({"non_owner"})
# SESSION_USER is a provisional no-op transfer that escapes both the
# privilege cluster and the membership wall.  CURRENT_ROLE / CURRENT_USER
# are self-transfers (00000, no wall).  Only an explicit role name requires
# SET ROLE membership (42501 if cannot SET ROLE).
_SESSION_USER_ESCAPE = "SESSION_USER"
_OWNER_TARGET_REQUIRES_MEMBERSHIP = frozenset({"new_owner_role"})

# Dense baseline assignment (all positive T1-T4 + T6 + GRM-axis baselines).
# The T5 single-value negative factors are held at their canonical default
# and are never crossed here, so the at-most-one-failure attribution stays
# clean.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_ALTER_PARAMETERS,
    "grammar_branch": _BRANCH_ALTER_PARAMETERS,
    "target_action": "alter_parameters",
    "object_state": "exists",
    "expected_status": "success",
    "if_exists_clause": "absent",
    "alter_parameter_type": "change_data_type",
    "logged_unlogged_clause": "LOGGED",
    "role_specification": "new_owner_role",
    "sequence_name_shape": "simple",
    "new_data_type": "smallint",
    "new_owner_shape": "existing_role",
    "new_schema_name": "existing_schema",
    "privilege_level": "superuser",
    "owned_by_table_dependency": "same_owner_same_schema",
    "schema_privilege": "has_CREATE",
    "owner_change_privilege": "can_SET_ROLE",
    "new_owner_schema_privilege": "has_CREATE",
    "non_existent_sequence": "target_not_exists_no_if_exists",
    "insufficient_privilege": "non_owner",
    "data_type_incompatible_values": "values_exceed_new_type_range",
    "logged_unlogged_on_temporary": "logged_unlogged_on_temp_illegal",
    "owned_by_different_owner": "table_different_owner",
    "owned_by_different_schema": "table_different_schema",
    "restart_value_out_of_range": "restart_exceeds_bounds",
    "verification_mode": "pg_class_catalog_query",
    "cleanup_mode": "DROP_SEQUENCE",
    "increment_by_keyword": "absent",
    "start_with_keyword": "absent",
    "restart_with_keyword": "absent",
    "cycle_no_keyword": "absent",
}

# Official synopsis branch -> grammar_branch id used by the renderer.
_BRANCH_GRAMMAR = {
    _BRANCH_ALTER_PARAMETERS: _BRANCH_ALTER_PARAMETERS,
    _BRANCH_SET_LOGGED_UNLOGGED: _BRANCH_SET_LOGGED_UNLOGGED,
    _BRANCH_OWNER: _BRANCH_OWNER,
    _BRANCH_RENAME: _BRANCH_RENAME,
    _BRANCH_SET_SCHEMA: _BRANCH_SET_SCHEMA,
}

# Fixed consumer action for every branch.
_BRANCH_FIXED_ACTION = {
    _BRANCH_ALTER_PARAMETERS: "alter_parameters",
    _BRANCH_SET_LOGGED_UNLOGGED: "set_logged_unlogged",
    _BRANCH_OWNER: "owner",
    _BRANCH_RENAME: "rename",
    _BRANCH_SET_SCHEMA: "set_schema",
}

# Crossed positive behaviour axes per branch.
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    _BRANCH_ALTER_PARAMETERS: {
        "alter_parameter_type": (
            "change_data_type", "change_increment", "change_minmax",
            "change_start", "restart_with", "change_cache",
            "change_cycle", "change_owned_by", "none_parameter",
        ),
        "if_exists_clause": ("absent", "present"),
        "sequence_name_shape": (
            "simple", "quoted", "reserved_word", "schema_qualified",
        ),
        "new_data_type": ("smallint", "integer", "bigint"),
        "privilege_level": ("superuser", "sequence_owner", "non_owner"),
        "owned_by_table_dependency": (
            "same_owner_same_schema", "different_owner", "different_schema",
        ),
    },
    _BRANCH_SET_LOGGED_UNLOGGED: {
        "logged_unlogged_clause": ("LOGGED", "UNLOGGED"),
        "if_exists_clause": ("absent", "present"),
        "sequence_name_shape": (
            "simple", "quoted", "reserved_word", "schema_qualified",
        ),
        "privilege_level": ("superuser", "sequence_owner", "non_owner"),
    },
    _BRANCH_OWNER: {
        "role_specification": (
            "new_owner_role", "CURRENT_ROLE", "CURRENT_USER", "SESSION_USER",
        ),
        "if_exists_clause": ("absent", "present"),
        "sequence_name_shape": (
            "simple", "quoted", "reserved_word", "schema_qualified",
        ),
        "new_owner_shape": ("existing_role", "non_existing_role"),
        "privilege_level": ("superuser", "sequence_owner", "non_owner"),
        "owner_change_privilege": ("can_SET_ROLE", "cannot_SET_ROLE"),
    },
    _BRANCH_RENAME: {
        "if_exists_clause": ("absent", "present"),
        "sequence_name_shape": (
            "simple", "quoted", "reserved_word", "schema_qualified",
        ),
        "privilege_level": ("superuser", "sequence_owner", "non_owner"),
    },
    _BRANCH_SET_SCHEMA: {
        "if_exists_clause": ("absent", "present"),
        "sequence_name_shape": (
            "simple", "quoted", "reserved_word", "schema_qualified",
        ),
        "new_schema_name": ("existing_schema", "non_existing_schema"),
        "privilege_level": ("superuser", "sequence_owner", "non_owner"),
        "schema_privilege": ("has_CREATE", "no_CREATE"),
    },
}

# Crossed behaviour-negative (factor, value) pairs.  The privilege cluster
# (privilege_level=non_owner) is counted as a single unit via
# _PRIVILEGE_CLUSTER_VALUES and is therefore not duplicated here.
_CROSSED_BEHAVIOUR_NEGATIVES = frozenset(
    {
        ("new_owner_shape", "non_existing_role"),
        ("new_schema_name", "non_existing_schema"),
        ("owned_by_table_dependency", "different_owner"),
        ("owned_by_table_dependency", "different_schema"),
    }
)


def _owner_privilege_failure(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """The SET-ROLE membership wall firing here, else None.

    Under ``sequence_owner`` (a non-superuser owner), OWNER TO with an
    explicit role requires SET ROLE membership and surfaces 42501.
    SESSION_USER is a provisional no-op escape and does NOT fire this wall.
    CURRENT_ROLE / CURRENT_USER resolve to the owner itself, so they are
    self-transfers (00000, no wall).  Only ``new_owner_role`` is in
    _OWNER_TARGET_REQUIRES_MEMBERSHIP.
    """

    if assignment.get("privilege_level") != "sequence_owner":
        return None
    target_action = assignment.get("target_action")
    if (
        target_action == "owner"
        and assignment.get("owner_change_privilege") == "cannot_SET_ROLE"
        and assignment.get("role_specification")
        in _OWNER_TARGET_REQUIRES_MEMBERSHIP
    ):
        return ("role_specification", "membership_required_under_owner")
    return None


def _privilege_cluster_fires(assignment: dict[str, str]) -> bool:
    """The privilege wall firing for non-owners, EXCEPT SESSION_USER.

    SESSION_USER is a provisional no-op transfer, so the privilege boundary
    does not fire when ``role_specification = SESSION_USER``.  In branches
    other than branch_owner, ``role_specification`` holds its baseline value
    (``new_owner_role``), so the escape only applies to the owner-transfer
    branch where it is crossed.
    """

    level = assignment.get("privilege_level")
    if level not in _PRIVILEGE_CLUSTER_VALUES:
        return False
    if assignment.get("role_specification") == _SESSION_USER_ESCAPE:
        return False
    return True


def _applicable_negative(
    factor: str, value: str, assignment: dict[str, str]
) -> bool:
    """Whether a crossed behaviour-negative is structurally in scope."""

    if assignment.get(factor) != value:
        return False
    branch = assignment.get("grammar_branch")
    if factor == "new_owner_shape":
        return branch == _BRANCH_OWNER
    if factor == "new_schema_name":
        return branch == _BRANCH_SET_SCHEMA
    if factor == "owned_by_table_dependency":
        return (
            branch == _BRANCH_ALTER_PARAMETERS
            and assignment.get("alter_parameter_type") == "change_owned_by"
        )
    return True


def _failure_unit_count(assignment: dict[str, str]) -> int:
    """Privilege cluster (1) + owner-privilege wall (1) + behaviour negatives.

    The privilege cluster (non_owner) and the owner-privilege wall
    (sequence_owner + role-membership) are mutually exclusive -- a case has
    exactly one privilege_level -- so the two never double-count.
    """

    cluster = 1 if _privilege_cluster_fires(assignment) else 0
    owner_priv = 1 if _owner_privilege_failure(assignment) else 0
    negatives = sum(
        1
        for factor, value in _CROSSED_BEHAVIOUR_NEGATIVES
        if _applicable_negative(factor, value, assignment)
    )
    return cluster + owner_priv + negatives


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success.

    Precedence: owner-privilege wall (42501) > privilege cluster (42501) >
    crossed behaviour negatives (42704 / 3F000 / 42501).
    """

    pair = _owner_privilege_failure(assignment)
    if pair is not None:
        return pair
    if _privilege_cluster_fires(assignment):
        level = assignment.get("privilege_level")
        return ("privilege_level", level)
    for neg_factor, neg_value in _CROSSED_BEHAVIOUR_NEGATIVES:
        if _applicable_negative(neg_factor, neg_value, assignment):
            return (neg_factor, neg_value)
    return None


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    """Structural validity + at-most-one-failure attribution."""

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
    """Derive (outcome, expected_sqlstate, expected_failure_reason)."""

    pair = _present_failure_pair(assignment)
    if pair is None:
        return "success", "00000", None
    sqlstate, reason = _SFV_FAILURE_SQLSTATE[pair]
    return "expected_failure", sqlstate, reason


def _extension_multiset_sha256(
    cases: tuple[AlterSequenceFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"alter-sequence-factor-extension-v1\n")
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
    cases: tuple[AlterSequenceFactorExtensionCase, ...],
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
                    f"ALTER SEQUENCE extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "alter_sequence_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "ALTER SEQUENCE",
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


def build_alter_sequence_factor_extension_plan(
    repository_root: Path,
) -> AlterSequenceFactorExtensionPlan:
    """Build the bounded ALTER SEQUENCE post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_alter_sequence_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[AlterSequenceFactorExtensionCase] = []
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
                    AlterSequenceFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"ALTERSEQUENCE{ordinal:05d}",
                        sql_filename=f"ALTERSEQUENCE{ordinal:05d}.sql",
                        object_prefix=f"altersequence_{ordinal:05d}_",
                        derivation_id=(
                            f"ALTSEQ-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "alter_sequence_required_baseline_factor_space"
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
    return AlterSequenceFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "AlterSequenceFactorExtensionError",
    "AlterSequenceFactorExtensionCase",
    "AlterSequenceFactorExtensionPlan",
    "build_alter_sequence_factor_extension_plan",
]
