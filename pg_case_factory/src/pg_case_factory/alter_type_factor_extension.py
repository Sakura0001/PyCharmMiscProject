"""Bounded post-coverage cross-factor extension expander for ALTER TYPE.

The marginal factor-value-loop (:mod:`alter_type_factor_loop`) is the
required baseline: one program per factor value, 94 local cases
(GRM 10 + SFV 84).  This module adds the bounded post-coverage extension
phase allowed by ``alter_type.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive T1-T4 behaviour axes across all 10 grammar
branches, with at most one failure-causing value per case so attribution
stays clean, and ``verification_mode``/``cleanup_mode`` crossed so every
declared T6 value is exercised.

ALTER TYPE requires ownership (or superuser for SET property).  The
storage-boundary T5 factors (storage_plain_to_other_requires_superuser,
storage_other_to_plain_never_allowed) are conditional on privilege, so
they are exercised in the baseline only and are not crossed here.  The
restrict-with-typed-tables failure is a two-factor boundary
(cascade_restrict=restrict AND typed_table_dependency=has_typed_tables)
and is attributed as a single failure unit.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record and is marked ``is_extension``.
Filtering happens BEFORE counting (``raw += 1``), so
``raw_combination_count == len(cases)`` and ``dropped_count == 0`` when
the cap is not reached.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .alter_type_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_alter_type_factor_loop_plan,
)


class AlterTypeFactorExtensionError(ValueError):
    """Raised when a frozen ALTER TYPE extension input drifts."""


@dataclass(frozen=True)
class AlterTypeFactorExtensionCase:
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
class AlterTypeFactorExtensionPlan:
    cases: tuple[AlterTypeFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 94
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_type_catalog_query",
    "pg_attribute_query",
    "information_schema_user_defined_types",
    "enum_value_query",
)
_CLEANUP_MODES = (
    "DROP_TYPE",
    "DROP_TYPE_IF_EXISTS",
    "DROP_TYPE_CASCADE",
)

# General axes crossed for ALL 10 branches.
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "object_state": (
        "exists",
        "not_exists",
    ),
    "privilege_level": ("superuser", "type_owner", "non_owner"),
}

_NEW_ATTRIBUTE_TYPES = (
    "integer",
    "text",
    "varchar",
    "numeric",
    "boolean",
    "date",
    "timestamp",
    "jsonb",
)
_TYPE_NAME_SHAPES = ("simple", "quoted", "reserved_word", "schema_qualified")
_ATTRIBUTE_NAME_SHAPES = ("simple", "quoted", "reserved_word")

# Dense positive baseline (all success values).  statement_branch /
# target_action are overridden per branch.
_BASELINE: dict[str, str] = {
    "object_state": "exists",
    "expected_status": "success",
    "type_category": "composite",
    "cascade_restrict": "none",
    "if_exists_clause": "absent",
    "if_not_exists_clause": "absent",
    "enum_position_clause": "absent",
    "role_specification": "new_owner_role",
    "type_name_shape": "simple",
    "attribute_name_shape": "simple",
    "new_attribute_type": "integer",
    "new_enum_value_shape": "simple_value",
    "privilege_level": "type_owner",
    "typed_table_dependency": "no_typed_tables",
    "attribute_usage_privilege": "has_USAGE",
    "owner_change_privilege": "can_SET_ROLE",
    "schema_privilege": "has_CREATE",
    "new_owner_schema_privilege": "has_CREATE",
    "enum_transaction_state": "outside_transaction",
    "verification_mode": "pg_type_catalog_query",
    "cleanup_mode": "DROP_TYPE_IF_EXISTS",
}

# Branch -> (statement_branch, target_action, branch-specific axes).
_BRANCH_CONFIG: tuple[
    tuple[str, str, dict[str, tuple[str, ...]]], ...
] = (
    (
        "branch_owner",
        "owner_to",
        {
            "role_specification": (
                "new_owner_role",
                "CURRENT_ROLE",
                "CURRENT_USER",
                "SESSION_USER",
            ),
            "owner_change_privilege": ("can_SET_ROLE", "cannot_SET_ROLE"),
            "new_owner_schema_privilege": ("has_CREATE", "no_CREATE"),
            "type_name_shape": _TYPE_NAME_SHAPES,
        },
    ),
    (
        "branch_rename",
        "rename",
        {
            "type_name_shape": _TYPE_NAME_SHAPES,
        },
    ),
    (
        "branch_set_schema",
        "set_schema",
        {
            "schema_privilege": ("has_CREATE", "no_CREATE"),
            "type_name_shape": _TYPE_NAME_SHAPES,
        },
    ),
    (
        "branch_rename_attribute",
        "rename_attribute",
        {
            "cascade_restrict": ("none", "cascade", "restrict"),
            "attribute_name_shape": _ATTRIBUTE_NAME_SHAPES,
        },
    ),
    (
        "branch_add_attribute",
        "add_attribute",
        {
            "cascade_restrict": ("none", "cascade", "restrict"),
            "new_attribute_type": _NEW_ATTRIBUTE_TYPES,
            "typed_table_dependency": (
                "no_typed_tables",
                "has_typed_tables",
            ),
        },
    ),
    (
        "branch_drop_attribute",
        "drop_attribute",
        {
            "cascade_restrict": ("none", "cascade", "restrict"),
            "if_exists_clause": ("absent", "present"),
            "attribute_name_shape": _ATTRIBUTE_NAME_SHAPES,
        },
    ),
    (
        "branch_alter_attribute_type",
        "alter_attribute_type",
        {
            "cascade_restrict": ("none", "cascade", "restrict"),
            "new_attribute_type": _NEW_ATTRIBUTE_TYPES,
            "typed_table_dependency": (
                "no_typed_tables",
                "has_typed_tables",
            ),
        },
    ),
    (
        "branch_add_value",
        "add_value",
        {
            "if_not_exists_clause": ("absent", "present"),
            "enum_position_clause": ("absent", "BEFORE", "AFTER"),
            "new_enum_value_shape": (
                "simple_value",
                "quoted_value",
                "long_value",
            ),
        },
    ),
    (
        "branch_rename_value",
        "rename_value",
        {
            "new_enum_value_shape": (
                "simple_value",
                "quoted_value",
                "long_value",
            ),
        },
    ),
    (
        "branch_set_property",
        "set_property",
        {
            "insufficient_privilege": (
                "non_owner",
                "non_superuser_set_property",
            ),
        },
    ),
)

# Crossed behaviour-negative (factor, value) pairs — one representative
# per failure scenario.  The two-factor restrict-with-typed-tables
# boundary is handled separately in :func:`_restrict_typed_failure`.
_CROSSED_NEGATIVES = frozenset(
    {
        ("object_state", "not_exists"),
        ("privilege_level", "non_owner"),
        ("owner_change_privilege", "cannot_SET_ROLE"),
        ("new_owner_schema_privilege", "no_CREATE"),
        ("schema_privilege", "no_CREATE"),
        ("insufficient_privilege", "non_superuser_set_property"),
    }
)


def _restrict_typed_failure(a: dict[str, str]) -> bool:
    return (
        a.get("cascade_restrict") == "restrict"
        and a.get("typed_table_dependency") == "has_typed_tables"
    )


def _failure_unit_count(assignment: dict[str, str]) -> int:
    count = sum(
        1
        for factor, value in _CROSSED_NEGATIVES
        if assignment.get(factor) == value
    )
    if _restrict_typed_failure(assignment):
        count += 1
    return count


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    for neg_factor, neg_value in _CROSSED_NEGATIVES:
        if assignment.get(neg_factor) == neg_value:
            return (neg_factor, neg_value)
    if _restrict_typed_failure(assignment):
        return ("restrict_with_typed_tables", "restrict_refuses_typed_tables")
    return None


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    """Applicability + consistency + at-most-one-failure attribution."""

    # object_state=not_exists is incompatible with a present type fixture;
    # it is a standalone failure and must not be combined with branch
    # failures.
    if _failure_unit_count(assignment) > 1:
        return False

    # owner_change_privilege=cannot_SET_ROLE must not co-occur with
    # new_owner_schema_privilege=no_CREATE (two distinct owner failures).
    if (
        assignment.get("owner_change_privilege") == "cannot_SET_ROLE"
        and assignment.get("new_owner_schema_privilege") == "no_CREATE"
    ):
        return False

    # enum value conflict boundary requires the add_value branch and an
    # existing value; only meaningful when armed there.
    return True


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values."""

    os_state = a.get("object_state", "exists")
    if os_state == "not_exists":
        a["non_existent_type"] = "target_not_exists"

    pl = a.get("privilege_level", "type_owner")
    ip = a.get("insufficient_privilege", "")
    if pl == "non_owner" and ip == "":
        a["insufficient_privilege"] = "non_owner"
    elif ip == "non_superuser_set_property":
        a["privilege_level"] = "non_owner"

    aup = a.get("attribute_usage_privilege", "has_USAGE")
    if aup == "no_USAGE":
        a["insufficient_privilege"] = "no_USAGE_on_attribute_type"

    if _restrict_typed_failure(a):
        a["restrict_with_typed_tables"] = "restrict_refuses_typed_tables"
    elif (
        a.get("cascade_restrict") == "cascade"
        and a.get("typed_table_dependency") == "has_typed_tables"
    ):
        a["cascade_with_typed_tables"] = "cascade_propagates_to_typed_tables"

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
            assignment["target_action"] = action
            if action in ("add_value", "rename_value"):
                assignment["type_category"] = "enum"
            elif action in ("add_attribute", "drop_attribute",
                            "alter_attribute_type", "rename_attribute"):
                assignment["type_category"] = "composite"
            elif action == "set_property":
                assignment["type_category"] = "base"
            for name, value in zip(names, values):
                assignment[name] = value
            _derive_t5_factors(assignment)
            if not _is_valid_combination(assignment):
                continue
            if len(assignment) != len(set(assignment)):
                raise AlterTypeFactorExtensionError(
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
    cases: tuple[AlterTypeFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"alter-type-factor-extension-v1\n"
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
    cases: tuple[AlterTypeFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"ALTER TYPE extension {case.ordinal:05d}: "
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
                        "alter_type_factor_extension"
                    ),
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "ALTER TYPE",
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


def build_alter_type_factor_extension_plan(
    repository_root: Path,
) -> AlterTypeFactorExtensionPlan:
    """Build the bounded ALTER TYPE post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_alter_type_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[AlterTypeFactorExtensionCase] = []
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
                cases.append(
                    AlterTypeFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"ALTERTYPE{ordinal:05d}",
                        sql_filename=(
                            f"ALTERTYPE{ordinal:05d}.sql"
                        ),
                        object_prefix=(
                            f"altertype_{ordinal:05d}_"
                        ),
                        derivation_id=(
                            f"ATYPE-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "alter_type_required_factor_value_matrix"
                        ),
                        derivation_reason=(
                            "cross-factor extension: "
                            f"target_action="
                            f"{assignment['target_action']} "
                            f"x object_state="
                            f"{assignment['object_state']} "
                            f"x privilege_level="
                            f"{assignment['privilege_level']} "
                            f"x verification_mode={verification} "
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
    return AlterTypeFactorExtensionPlan(
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
    "AlterTypeFactorExtensionError",
    "AlterTypeFactorExtensionCase",
    "AlterTypeFactorExtensionPlan",
    "build_alter_type_factor_extension_plan",
]
