"""Bounded post-coverage cross-factor extension expander for DROP ACCESS METHOD.

The marginal factor-value-loop (:mod:`drop_access_method_factor_loop`) is the
required baseline: one program per factor value, 31 local cases
(GRM 1 + SFV 28 + Risk 2).  This module adds the bounded post-coverage
extension phase allowed by ``drop_access_method.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor combinations
of the positive T1-T4 behaviour axes across the single official synopsis
branch (at most one failure-causing value per case, so attribution stays
clean), with ``verification_mode`` crossed and ``cleanup_mode`` crossed so
every declared T6 value is exercised.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``derived_extension_required_fields``) and is marked ``is_extension = True``.
The T5 negative factors (``nonexistent_am``,
``dependent_objects_exist``, ``insufficient_privilege``, ``expected_status``,
``object_state=not_exists``) are owned one-per-value by the marginal baseline
and are never crossed here, so the at-most-one-failure attribution stays
clean.

The single official synopsis branch is crossed:

* ``branch_1`` — ``am_name_shape`` x ``if_exists_clause`` x
  ``cascade_restrict`` x ``dependency_state`` x ``privilege_level``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .drop_access_method_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_drop_access_method_factor_loop_plan,
)


class DropAccessMethodFactorExtensionError(ValueError):
    """Raised when a frozen DROP ACCESS METHOD extension input drifts."""


@dataclass(frozen=True)
class DropAccessMethodFactorExtensionCase:
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
class DropAccessMethodFactorExtensionPlan:
    cases: tuple[DropAccessMethodFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 31
# Safety backstop only; the natural at-most-one-failure cross is expected to
# stay well under this cap so no coverage-losing truncation occurs.  The exact
# frozen count is asserted in the companion test.
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_am_catalog_query",
    "pg_am_removed_assertion",
)
_CLEANUP_MODES = (
    "DROP_ACCESS_METHOD_CASCADE",
    "DROP_DEPENDENT_OBJECTS_FIRST",
)

# Dense baseline assignment (all positive T1-T4 + T6 baselines).  The T5
# negative factors (nonexistent_am, dependent_objects_exist,
# insufficient_privilege, expected_status, object_state=not_exists) are
# intentionally absent from the cross: they are owned one-per-value by the
# marginal baseline and are never crossed here, so the at-most-one-failure
# attribution stays clean.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_1",
    "grammar_branch": "branch_1",
    "target_action": "drop_access_method",
    "object_state": "already_exists",
    "expected_status": "success",
    "if_exists_clause": "absent",
    "cascade_restrict": "RESTRICT_default",
    "dependency_state": "no_dependencies",
    "am_name_shape": "plain_identifier",
    "privilege_level": "superuser",
    "nonexistent_am": "without_if_exists",
    "dependent_objects_exist": "restrict_with_dependencies",
    "insufficient_privilege": "non_superuser_drop",
    "verification_mode": "pg_am_removed_assertion",
    "cleanup_mode": "DROP_ACCESS_METHOD_CASCADE",
}

# Official synopsis branch -> grammar_branch id used by the renderer.
_BRANCH_GRAMMAR: dict[str, str] = {
    "branch_1": "branch_1",
}

# Fixed consumer action per branch (the synopsis action form).
_BRANCH_FIXED_ACTION: dict[str, str] = {
    "branch_1": "drop_access_method",
}

# Crossed positive behaviour axes per branch.  am_name_shape excludes
# nonexistent_name (a T3 negative owned by the marginal baseline).
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_1": {
        "am_name_shape": (
            "plain_identifier",
            "quoted_identifier",
            "schema_qualified",
        ),
        "if_exists_clause": ("absent", "present"),
        "cascade_restrict": ("RESTRICT_default", "RESTRICT_explicit", "CASCADE"),
        "dependency_state": (
            "no_dependencies",
            "has_dependent_opclass",
            "has_dependent_index",
        ),
        "privilege_level": ("superuser", "non_superuser"),
    },
}

# Crossed behaviour-negative (factor, value) pairs.  The privilege boundary
# (privilege_level=non_superuser) is counted as a single unit.  The dependency
# negatives only fire when cascade_restrict != CASCADE, so they are
# conditional rather than unconditional value matches.
_CROSSED_BEHAVIOUR_NEGATIVES = frozenset(
    {
        ("dependency_state", "has_dependent_opclass"),
        ("dependency_state", "has_dependent_index"),
    }
)
_PRIVILEGE_NEGATIVE = ("privilege_level", "non_superuser")
_RESTRICT_VALUES = frozenset({"RESTRICT_default", "RESTRICT_explicit"})


def _dependency_failure_fires(assignment: dict[str, str]) -> bool:
    """Whether a crossed dependency negative actually fires here.

    ``has_dependent_opclass`` / ``has_dependent_index`` surface
    ``dependent_objects_restricted`` (2BPQ1) only under a non-CASCADE drop
    policy.  Under CASCADE the dependent is removed along with the access
    method, so the drop succeeds and the negative never fires.
    """

    return assignment.get("cascade_restrict") in _RESTRICT_VALUES


def _failure_unit_count(assignment: dict[str, str]) -> int:
    """Privilege boundary (1) + conditional dependency negatives; <= 1."""

    count = 0
    if assignment.get("privilege_level") == "non_superuser":
        count += 1
    if _dependency_failure_fires(assignment):
        for factor, value in _CROSSED_BEHAVIOUR_NEGATIVES:
            if assignment.get(factor) == value:
                count += 1
    return count


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success.

    The privilege boundary (must be superuser, 42501) fires before the
    dependency check, so it is attributed first when present (it shadows any
    co-occurring dependency negative, which the at-most-one rule has already
    excluded from the kept set).
    """

    if assignment.get("privilege_level") == "non_superuser":
        return _PRIVILEGE_NEGATIVE
    if _dependency_failure_fires(assignment):
        for factor, value in _CROSSED_BEHAVIOUR_NEGATIVES:
            if assignment.get(factor) == value:
                return (factor, value)
    return None


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    """At-most-one-failure attribution."""

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
            pair = _present_failure_pair(assignment)
            assignment["expected_status"] = (
                "failure" if pair is not None else "success"
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
    cases: tuple[DropAccessMethodFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"drop-access-method-factor-extension-v1\n")
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
    cases: tuple[DropAccessMethodFactorExtensionCase, ...],
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
                    f"DROP ACCESS METHOD extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "drop_access_method_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "DROP ACCESS METHOD",
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


def build_drop_access_method_factor_extension_plan(
    repository_root: Path,
) -> DropAccessMethodFactorExtensionPlan:
    """Build the bounded DROP ACCESS METHOD post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_drop_access_method_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[DropAccessMethodFactorExtensionCase] = []
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
                    DropAccessMethodFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"DROPACCESSMETHOD{ordinal:05d}",
                        sql_filename=f"DROPACCESSMETHOD{ordinal:05d}.sql",
                        object_prefix=f"dropaccessmethod_{ordinal:05d}_",
                        derivation_id=(
                            f"DAM-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "drop_access_method_required_baseline_factor_space"
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
    return DropAccessMethodFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "DropAccessMethodFactorExtensionError",
    "DropAccessMethodFactorExtensionCase",
    "DropAccessMethodFactorExtensionPlan",
    "build_drop_access_method_factor_extension_plan",
    "_present_failure_pair",
    "_failure_unit_count",
    "_dependency_failure_fires",
]
