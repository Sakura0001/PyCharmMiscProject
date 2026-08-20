"""Bounded post-coverage cross-factor extension expander for ALTER VIEW.

The marginal factor-value-loop (:mod:`alter_view_factor_loop`) is the
required baseline: one program per factor value, 71 local cases
(GRM 8 + SFV 63).  This module adds the bounded post-coverage extension
phase allowed by ``alter_view.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive T1-T4 behaviour axes across all 8 grammar
branches, with at most one failure-causing value per case so attribution
stays clean, and ``verification_mode`` crossed so every declared T6 value
is exercised.

ALTER VIEW operates on existing plain views; ``privilege_level=non_owner_
no_privilege`` is an unconditional failure on every branch.  The
``object_state=not_exists`` boundary is a failure only when
``if_exists_clause=absent``; with ``if_exists_clause=present`` it is a
no-op success (PG skips the missing view).  The no-op suppresses every
other failure attribution.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``post_coverage_extension_policy.required_fields``) and is marked
``is_extension``.  Filtering happens BEFORE counting (``raw += 1``), so
``raw_combination_count == len(cases)`` and ``dropped_count == 0``
(no over-pruning).
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .alter_view_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_alter_view_factor_loop_plan,
)


class AlterViewFactorExtensionError(ValueError):
    """Raised when a frozen ALTER VIEW extension input drifts."""


@dataclass(frozen=True)
class AlterViewFactorExtensionCase:
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
class AlterViewFactorExtensionPlan:
    cases: tuple[AlterViewFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 71
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_class_query",
    "pg_views_query",
    "information_schema_views",
    "select_from_view",
    "error_assertion",
)
_CLEANUP_MODES = (
    "drop_view_if_exists",
    "drop_view_cascade",
    "revert_alter",
)

# General axes crossed for ALL 8 branches.
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "object_state": (
        "exists",
        "not_exists",
    ),
    "if_exists_clause": (
        "absent",
        "present",
    ),
    "privilege_level": (
        "owner",
        "superuser",
        "non_owner_with_privilege",
        "non_owner_no_privilege",
    ),
}

# Dense positive baseline (all success values).  statement_branch /
# target_action / grammar_branch are overridden per branch.
_BASELINE: dict[str, str] = {
    "object_state": "exists",
    "expected_status": "success",
    "if_exists_clause": "absent",
    "view_name_shape": "simple",
    "column_name_shape": "simple",
    "new_name_shape": "simple",
    "new_schema_shape": "schema_exists",
    "owner_target_shape": "role_name",
    "view_option_shape": "check_option_local",
    "privilege_level": "owner",
    "dependency_state": "base_table_exists",
    "error_boundary": "none",
    "verification_mode": "pg_class_query",
    "cleanup_mode": "drop_view_if_exists",
}

# Branch -> (statement_branch, target_action, branch-specific axes).
_BRANCH_CONFIG: tuple[
    tuple[str, str, dict[str, tuple[str, ...]]], ...
] = (
    (
        "branch_set_default",
        "set_default",
        {
            "column_name_shape": (
                "simple",
                "quoted",
                "with_column_keyword",
                "without_column_keyword",
            ),
        },
    ),
    (
        "branch_drop_default",
        "drop_default",
        {
            "column_name_shape": (
                "simple",
                "quoted",
                "with_column_keyword",
                "without_column_keyword",
            ),
        },
    ),
    (
        "branch_owner_to",
        "owner_to",
        {
            "owner_target_shape": (
                "role_name",
                "current_role",
                "current_user",
                "session_user",
                "non_existent_role",
            ),
        },
    ),
    (
        "branch_rename_column",
        "rename_column",
        {
            "column_name_shape": (
                "simple",
                "quoted",
                "with_column_keyword",
                "without_column_keyword",
            ),
        },
    ),
    (
        "branch_rename_view",
        "rename",
        {
            "new_name_shape": (
                "simple",
                "quoted",
                "reserved_word",
                "same_as_existing",
            ),
        },
    ),
    (
        "branch_set_schema",
        "set_schema",
        {
            "new_schema_shape": (
                "schema_exists",
                "schema_not_exists",
                "pg_catalog_reserved",
            ),
        },
    ),
    (
        "branch_set_option",
        "set_option",
        {
            "view_option_shape": (
                "check_option_local",
                "check_option_cascaded",
                "security_barrier_true",
                "security_barrier_false",
                "security_invoker_true",
                "security_invoker_false",
                "multiple_options",
            ),
        },
    ),
    (
        "branch_reset_option",
        "reset_option",
        {
            "view_option_shape": (
                "check_option_local",
                "check_option_cascaded",
                "security_barrier_true",
                "security_barrier_false",
                "security_invoker_true",
                "security_invoker_false",
                "multiple_options",
            ),
        },
    ),
)

# Crossed behaviour-negative (factor, value) pairs — one representative
# per failure scenario.  object_state=not_exists is NOT listed here: it is
# a failure only when if_exists_clause=absent (a conditional failure handled
# in :func:`_active_failures`), so listing it unconditionally would
# double-count the no-op success cases.
_CROSSED_NEGATIVES = frozenset(
    {
        ("privilege_level", "non_owner_no_privilege"),
        ("owner_target_shape", "non_existent_role"),
        ("new_schema_shape", "schema_not_exists"),
        ("new_schema_shape", "pg_catalog_reserved"),
        ("new_name_shape", "same_as_existing"),
    }
)


def _active_failures(
    assignment: dict[str, str],
) -> list[tuple[str, str]]:
    """Failure pairs active in this assignment (object_state is conditional)."""

    pairs: list[tuple[str, str]] = []
    os_ = assignment.get("object_state", "exists")
    ie = assignment.get("if_exists_clause", "absent")
    if os_ == "not_exists" and ie == "absent":
        pairs.append(("object_state", "not_exists"))
    for factor, value in _CROSSED_NEGATIVES:
        if assignment.get(factor) == value:
            pairs.append((factor, value))
    return pairs


def _is_noop(assignment: dict[str, str]) -> bool:
    """ALTER VIEW IF EXISTS on a missing view is a no-op success."""

    os_ = assignment.get("object_state", "exists")
    ie = assignment.get("if_exists_clause", "absent")
    return os_ == "not_exists" and ie == "present"


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    """Applicability + at-most-one-failure attribution."""

    if _is_noop(assignment):
        return True
    return len(_active_failures(assignment)) <= 1


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    if _is_noop(assignment):
        return None
    pairs = _active_failures(assignment)
    return pairs[0] if pairs else None


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values."""

    os_ = a.get("object_state", "exists")
    ie = a.get("if_exists_clause", "absent")
    pl = a.get("privilege_level", "owner")
    ot = a.get("owner_target_shape", "role_name")
    nss = a.get("new_schema_shape", "schema_exists")

    if os_ == "not_exists":
        a["view_name_shape"] = "non_existent"
        a["error_boundary"] = (
            "view_not_exists_without_if_exists"
            if ie == "absent"
            else "none"
        )
    else:
        a["view_name_shape"] = a.get("view_name_shape", "simple")

    if pl == "non_owner_no_privilege":
        a["error_boundary"] = "insufficient_privilege"
    if ot == "non_existent_role":
        a["error_boundary"] = "non_existent_role"
    if nss == "schema_not_exists":
        a["error_boundary"] = "non_existent_schema"
    elif nss == "pg_catalog_reserved":
        a["error_boundary"] = "non_existent_schema"

    pair = _present_failure_pair(a)
    a["expected_status"] = "failure" if pair is not None else "success"


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
            for name, value in zip(names, values):
                assignment[name] = value
            _derive_t5_factors(assignment)
            if not _is_valid_combination(assignment):
                continue
            if len(assignment) != len(set(assignment)):
                raise AlterViewFactorExtensionError(
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
    cases: tuple[AlterViewFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"alter-view-factor-extension-v1\n")
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
    cases: tuple[AlterViewFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"ALTER VIEW extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "alter_view_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "ALTER VIEW",
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


def build_alter_view_factor_extension_plan(
    repository_root: Path,
) -> AlterViewFactorExtensionPlan:
    """Build the bounded ALTER VIEW post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_alter_view_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[AlterViewFactorExtensionCase] = []
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
                    AlterViewFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"ALTERVIEW{ordinal:05d}",
                        sql_filename=f"ALTERVIEW{ordinal:05d}.sql",
                        object_prefix=f"alterview_{ordinal:05d}_",
                        derivation_id=(
                            f"AVIEW-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "alter_view_required_factor_value_matrix"
                        ),
                        derivation_reason=(
                            "cross-factor extension: "
                            f"target_action="
                            f"{assignment['target_action']} "
                            f"x object_state="
                            f"{assignment['object_state']} "
                            f"x if_exists_clause="
                            f"{assignment['if_exists_clause']} "
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
    return AlterViewFactorExtensionPlan(
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
    "AlterViewFactorExtensionError",
    "AlterViewFactorExtensionCase",
    "AlterViewFactorExtensionPlan",
    "build_alter_view_factor_extension_plan",
]
