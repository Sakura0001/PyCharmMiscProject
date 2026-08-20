"""Bounded post-coverage cross-factor extension expander for ALTER USER.

The marginal factor-value-loop (:mod:`alter_user_factor_loop`) is the
required baseline: one program per factor value, 75 local cases (GRM 6
+ SFV 69).  This module adds the bounded post-coverage extension phase
allowed by ``alter_user.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive T1-T4 behaviour axes across all 6 grammar
branches, with at most one failure-causing value per case so attribution
stays clean, and ``verification_mode`` / ``cleanup_mode`` crossed so
every declared T6 value is exercised.

ALTER USER requires CREATEROLE privilege for option/rename forms and
role ownership for SET/RESET forms, so ``privilege_level=non_createrole``
and ``privilege_level=non_owner`` are unconditional failures.  The T5
single-value factors (nonexistent_role, duplicate_new_name,
nonexistent_database, insufficient_privilege,
superuser_modification_by_non_superuser) are derived from their T1-T4
counterparts, not crossed as axes.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record and is marked ``is_extension``.
Filtering happens BEFORE counting, so ``raw_combination_count ==
len(cases)`` and ``dropped_count == 0``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .alter_user_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_alter_user_factor_loop_plan,
)


class AlterUserFactorExtensionError(ValueError):
    """Raised when a frozen ALTER USER extension input drifts."""


@dataclass(frozen=True)
class AlterUserFactorExtensionCase:
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
class AlterUserFactorExtensionPlan:
    cases: tuple[AlterUserFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 75
_CAP = 20000

_VERIFICATION_MODES = (
    "catalog_query_pg_roles",
    "config_parameter_query",
    "error_assertion",
)
_CLEANUP_MODES = (
    "revert_option",
    "revert_rename",
    "reset_config",
    "drop_role",
)

# General axes crossed for ALL 6 branches.
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "object_state": ("exists", "not_exists"),
    "role_name_shape": ("simple_id", "quoted_id", "nonexistent_name"),
    "privilege_level": (
        "createrole",
        "superuser",
        "role_owner",
        "non_owner",
        "non_createrole",
    ),
}

# Dense positive baseline (all success values).  statement_branch /
# target_action / grammar_branch / alter_action are overridden per branch.
_BASELINE: dict[str, str] = {
    "object_state": "exists",
    "expected_status": "success",
    "role_specification": "named_role",
    "in_database_clause": "omitted",
    "option_type": "superuser_toggle",
    "role_name_shape": "simple_id",
    "new_name_shape": "simple_id",
    "database_name_shape": "simple_id",
    "config_param_shape": "valid_param",
    "privilege_level": "createrole",
    "database_existence": "database_exists",
    "nonexistent_role": "role_exists",
    "duplicate_new_name": "no_conflict",
    "nonexistent_database": "database_exists",
    "insufficient_privilege": "has_privilege",
    "superuser_modification_by_non_superuser": "superuser_execution",
    "verification_mode": "catalog_query_pg_roles",
    "cleanup_mode": "revert_option",
}

# Branch -> (statement_branch, target_action, branch-specific axes).
_BRANCH_CONFIG: tuple[
    tuple[str, str, dict[str, tuple[str, ...]]], ...
] = (
    (
        "branch_option",
        "option_modify",
        {
            "option_type": (
                "superuser_toggle",
                "createdb_toggle",
                "createrole_toggle",
                "inherit_toggle",
                "login_toggle",
                "replication_toggle",
                "bypassrls_toggle",
                "connection_limit",
                "password",
                "password_null",
                "valid_until",
            ),
        },
    ),
    (
        "branch_rename",
        "rename",
        {
            "new_name_shape": (
                "simple_id",
                "quoted_id",
                "duplicate_name",
            ),
        },
    ),
    (
        "branch_set_config",
        "set_config",
        {
            "in_database_clause": ("omitted", "specified"),
            "config_param_shape": ("valid_param", "invalid_param"),
            "database_name_shape": (
                "simple_id",
                "nonexistent_name",
            ),
        },
    ),
    (
        "branch_set_from_current",
        "set_from_current",
        {
            "in_database_clause": ("omitted", "specified"),
            "config_param_shape": ("valid_param", "invalid_param"),
        },
    ),
    (
        "branch_reset_config",
        "reset_config",
        {
            "in_database_clause": ("omitted", "specified"),
        },
    ),
    (
        "branch_reset_all",
        "reset_all",
        {
            "in_database_clause": ("omitted", "specified"),
        },
    ),
)

# Crossed behaviour-negative (factor, value) pairs -- one representative
# per failure scenario.  Overlapping T5 values are NOT listed here (they
# are derived in :func:`_derive_t5_factors`) so counting both would
# double-count a single failure and break at-most-one attribution.
_CROSSED_NEGATIVES = frozenset(
    {
        ("object_state", "not_exists"),
        ("privilege_level", "non_createrole"),
        ("privilege_level", "non_owner"),
        ("new_name_shape", "duplicate_name"),
        ("database_name_shape", "nonexistent_name"),
        ("config_param_shape", "invalid_param"),
    }
)


def _failure_unit_count(assignment: dict[str, str]) -> int:
    return sum(
        1
        for factor, value in _CROSSED_NEGATIVES
        if assignment.get(factor) == value
    )


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    for neg_factor, neg_value in _CROSSED_NEGATIVES:
        if assignment.get(neg_factor) == neg_value:
            return (neg_factor, neg_value)
    return None


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    """Applicability + consistency + at-most-one-failure attribution."""

    os_ = assignment.get("object_state", "exists")
    rns = assignment.get("role_name_shape", "simple_id")
    # object_state=not_exists iff role_name_shape=nonexistent_name
    if os_ == "not_exists" and rns != "nonexistent_name":
        return False
    if os_ != "not_exists" and rns == "nonexistent_name":
        return False

    # role_owner privilege requires the role to exist
    pl = assignment.get("privilege_level", "createrole")
    if os_ == "not_exists" and pl == "role_owner":
        return False

    # database_name_shape only meaningful when in_database=specified
    idc = assignment.get("in_database_clause")
    dns = assignment.get("database_name_shape")
    if idc == "omitted" and dns == "nonexistent_name":
        return False

    return _failure_unit_count(assignment) <= 1


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values."""

    os_ = a.get("object_state", "exists")
    rns = a.get("role_name_shape", "simple_id")
    pl = a.get("privilege_level", "createrole")
    nns = a.get("new_name_shape", "simple_id")
    dns = a.get("database_name_shape", "simple_id")
    ot = a.get("option_type", "superuser_toggle")
    action = a.get("target_action", "option_modify")

    # nonexistent_role
    if os_ == "not_exists" or rns == "nonexistent_name":
        a["nonexistent_role"] = "role_missing"
    else:
        a["nonexistent_role"] = "role_exists"

    # duplicate_new_name
    if nns == "duplicate_name":
        a["duplicate_new_name"] = "same_name_conflict"
    else:
        a["duplicate_new_name"] = "no_conflict"

    # nonexistent_database / database_existence
    if dns == "nonexistent_name":
        a["nonexistent_database"] = "database_missing"
        a["database_existence"] = "database_not_exists"
    else:
        a["nonexistent_database"] = "database_exists"
        a["database_existence"] = "database_exists"

    # insufficient_privilege
    if pl == "non_createrole":
        a["insufficient_privilege"] = "lacks_createrole"
    elif pl == "non_owner":
        a["insufficient_privilege"] = "lacks_role_ownership"
    else:
        a["insufficient_privilege"] = "has_privilege"

    # superuser_modification_by_non_superuser
    if (
        pl in ("non_createrole", "non_owner")
        and ot == "superuser_toggle"
        and action == "option_modify"
    ):
        a["superuser_modification_by_non_superuser"] = (
            "non_superuser_attempting_superuser_toggle"
        )
    else:
        a["superuser_modification_by_non_superuser"] = (
            "superuser_execution"
        )

    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments (T6 at baseline) passing the filter."""

    combos: list[dict[str, str]] = []
    for branch, action, axes in _BRANCH_CONFIG:
        all_axes = dict(_GENERAL_AXES)
        all_axes.update(axes)
        names = list(all_axes)
        for values in itertools.product(
            *[all_axes[n] for n in names]
        ):
            assignment: dict[str, str] = dict(_BASELINE)
            assignment["statement_branch"] = branch
            assignment["grammar_branch"] = branch
            assignment["target_action"] = action
            assignment["alter_action"] = action
            for name, value in zip(names, values):
                assignment[name] = value
            _derive_t5_factors(assignment)
            if not _is_valid_combination(assignment):
                continue
            if len(assignment) != len(set(assignment)):
                raise AlterUserFactorExtensionError(
                    "duplicate factor key in extension assignment"
                )
            combos.append(assignment)
    return combos


def _outcome_for(
    assignment: dict[str, str],
) -> tuple[str, str, str | None]:
    pair = _present_failure_pair(assignment)
    if pair is None:
        return "success", "00000", None
    sqlstate, reason = _SFV_FAILURE_SQLSTATE[pair]
    return "expected_failure", sqlstate, reason


def _extension_multiset_sha256(
    cases: tuple[AlterUserFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"alter-user-factor-extension-v1\n"
    )
    for case in cases:
        digest.update(
            json.dumps(
                {
                    "derivation_id": case.derivation_id,
                    "factor_assignment": list(
                        case.factor_assignment
                    ),
                    "outcome": case.outcome,
                    "expected_sqlstate": case.expected_sqlstate,
                    "expected_failure_reason": (
                        case.expected_failure_reason
                    ),
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
    cases: tuple[AlterUserFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"ALTER USER extension "
                    f"{case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": (
                        "alter_user_factor_extension"
                    ),
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "ALTER USER",
                    "primary_fence": (
                        "primary-target-begin/end"
                    ),
                    "consumer_action_id": case.consumer_action_id,
                },
                "verification": {
                    "verification_mode": assignment[
                        "verification_mode"
                    ],
                    "expected_sqlstate": case.expected_sqlstate,
                },
                "cleanup": {
                    "cleanup_mode": assignment["cleanup_mode"],
                },
            }
        )
    return yaml.safe_dump(
        entries, sort_keys=False, allow_unicode=True
    )


def build_alter_user_factor_extension_plan(
    repository_root: Path,
) -> AlterUserFactorExtensionPlan:
    """Build the bounded ALTER USER post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_alter_user_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[AlterUserFactorExtensionCase] = []
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
                outcome, sqlstate, reason = _outcome_for(
                    assignment
                )
                ordinal += 1
                cases.append(
                    AlterUserFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=(
                            f"ALTERUSER{ordinal:05d}"
                        ),
                        sql_filename=(
                            f"ALTERUSER{ordinal:05d}.sql"
                        ),
                        object_prefix=(
                            f"alteruser_{ordinal:05d}_"
                        ),
                        derivation_id=(
                            f"AUSR-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "alter_user_required_factor_"
                            "value_matrix"
                        ),
                        derivation_reason=(
                            "cross-factor extension: "
                            f"target_action="
                            f"{assignment['target_action']} "
                            f"x object_state="
                            f"{assignment['object_state']} "
                            f"x privilege_level="
                            f"{assignment['privilege_level']} "
                            f"x verification_mode="
                            f"{verification} "
                            f"x cleanup_mode={cleanup}"
                        ),
                        factor_assignment=tuple(
                            sorted(assignment.items())
                        ),
                        consumer_action_id=assignment[
                            "target_action"
                        ],
                        outcome=outcome,
                        expected_sqlstate=sqlstate,
                        expected_failure_reason=reason,
                        is_extension=True,
                    )
                )
    dropped = max(0, raw - _CAP)
    cases_tuple = tuple(cases)
    return AlterUserFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(
            cases_tuple
        ),
        derived_combinations_yaml=_derived_combinations_yaml(
            cases_tuple
        ),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "AlterUserFactorExtensionError",
    "AlterUserFactorExtensionCase",
    "AlterUserFactorExtensionPlan",
    "build_alter_user_factor_extension_plan",
]
