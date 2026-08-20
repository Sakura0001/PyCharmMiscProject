"""Bounded post-coverage cross-factor extension expander for DROP TYPE.

The marginal factor-value-loop (:mod:`drop_type_factor_loop`) is the required
baseline: one program per factor value, 46 local cases (GRM 1 + SFV 43 +
Risk 2).  This module adds the bounded post-coverage extension phase:
cross-factor combinations of the behaviour axes across the single official
synopsis branch (at most one failure-causing value per case, so attribution
stays clean), with ``verification_mode`` crossed and ``cleanup_mode``
crossed so every declared T6 value is exercised.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``derived_extension_required_fields``) and is marked ``is_extension = True``.
The negative factors (``privilege_level=non_owner``, ``object_state=not_exists``
when ``if_exists_clause=absent``, ``dependency_state`` under RESTRICT) are
crossed here with at-most-one-failure attribution; the not-exist boundary
fires first (42704), then the privilege boundary (42501), then the dependency
boundary (2BP01).

The single official synopsis branch is crossed:

* ``branch_drop_type`` — ``privilege_level`` x ``object_state`` x
  ``if_exists_clause`` x ``cascade_restrict`` x ``dependency_state`` x
  ``type_category``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .drop_type_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_drop_type_factor_loop_plan,
)


class DropTypeFactorExtensionError(ValueError):
    """Raised when a frozen DROP TYPE extension input drifts."""


@dataclass(frozen=True)
class DropTypeFactorExtensionCase:
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
class DropTypeFactorExtensionPlan:
    cases: tuple[DropTypeFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 46
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_type_query",
    "information_schema_user_defined_types",
    "error_assertion",
    "notice_assertion",
)
_CLEANUP_MODES = (
    "no_cleanup_needed",
    "manual_cleanup",
    "rollback",
)

# Dense baseline assignment (all positive values).  The negative factors
# (privilege_level=non_owner, object_state=not_exists / if_exists_clause=
# absent, dependency_state under RESTRICT) are crossed here with
# at-most-one-failure attribution.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_type",
    "grammar_branch": "branch_1",
    "target_action": "drop_type",
    "object_state": "exists_composite",
    "expected_status": "success",
    "if_exists_clause": "absent",
    "cascade_restrict": "none",
    "multi_type_drop": "single_type",
    "type_category": "composite",
    "type_name_shape": "simple",
    "privilege_level": "superuser",
    "dependency_state": "no_dependents",
    "error_boundary": "none",
    "verification_mode": "pg_type_query",
    "cleanup_mode": "no_cleanup_needed",
}

_BRANCH_GRAMMAR: dict[str, str] = {
    "branch_drop_type": "branch_1",
}

_BRANCH_FIXED_ACTION: dict[str, str] = {
    "branch_drop_type": "drop_type",
}

# Crossed positive behaviour axes per branch.
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_drop_type": {
        "privilege_level": (
            "non_owner",
            "superuser",
            "owner",
        ),
        "object_state": ("exists_composite", "not_exists"),
        "if_exists_clause": ("present", "absent"),
        "cascade_restrict": (
            "cascade",
            "none",
            "restrict",
        ),
        "dependency_state": (
            "no_dependents",
            "used_in_table_columns",
            "used_in_function_params",
            "used_in_operators",
            "used_in_typed_tables",
        ),
        "type_category": ("composite", "enum", "range", "base"),
    },
}

# Failure boundaries (in PostgreSQL execution order: not-exist lookup ->
# privilege -> dependency).  The not-exist boundary (42704) fires when the
# type is absent and IF EXISTS is omitted.  The privilege boundary (42501)
# fires when the caller is not the type owner.  The dependency boundary
# (2BP01) fires when RESTRICT (or default RESTRICT) is used with dependents.
_PRIVILEGE_NEGATIVE = ("privilege_level", "non_owner")
_NOT_EXIST_NEGATIVE = ("object_state", "not_exists")
_DEPENDENCY_VALUES = frozenset(
    {
        "used_in_table_columns",
        "used_in_function_params",
        "used_in_operators",
        "used_in_typed_tables",
    }
)
_RESTRICT_VALUES = frozenset({"none", "restrict"})
_IF_EXISTS_OMITTED = "absent"


def _privilege_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("privilege_level") == "non_owner"


def _not_exist_failure_fires(assignment: dict[str, str]) -> bool:
    """not-exist fires only when IF EXISTS is omitted."""

    if assignment.get("if_exists_clause") != _IF_EXISTS_OMITTED:
        return False
    return assignment.get("object_state") == "not_exists"


def _dependency_failure_fires(assignment: dict[str, str]) -> bool:
    """has-dependents fires only under a non-CASCADE drop policy."""

    return (
        assignment.get("dependency_state") in _DEPENDENCY_VALUES
        and assignment.get("cascade_restrict") in _RESTRICT_VALUES
    )


def _failure_unit_count(assignment: dict[str, str]) -> int:
    count = 0
    if _not_exist_failure_fires(assignment):
        count += 1
    if _privilege_failure_fires(assignment):
        count += 1
    if _dependency_failure_fires(assignment):
        count += 1
    return count


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success.

    The not-exist boundary (42704) fires first when the type is absent and
    IF EXISTS is omitted.  The privilege boundary (42501) fires next when the
    caller is not the owner.  The dependency boundary (2BP01) fires last
    under RESTRICT with dependents.
    """

    if _not_exist_failure_fires(assignment):
        return _NOT_EXIST_NEGATIVE
    if _privilege_failure_fires(assignment):
        return _PRIVILEGE_NEGATIVE
    if _dependency_failure_fires(assignment):
        return ("dependency_state", assignment["dependency_state"])
    return None


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    if _failure_unit_count(assignment) > 1:
        return False
    # Structural constraint: a dependent fixture (table column, function,
    # operator, typed table) references the target type, so the type must
    # exist.  object_state=not_exists would leave the dependent pointing at a
    # missing type, which breaks the setup before the target ever runs.
    if (
        assignment.get("dependency_state") in _DEPENDENCY_VALUES
        and assignment.get("object_state") == "not_exists"
    ):
        return False
    return True


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
            assignment["error_boundary"] = _error_boundary_for(pair)
            combos.append(assignment)
    return combos


def _error_boundary_for(
    pair: tuple[str, str] | None,
) -> str:
    if pair is None:
        return "none"
    if pair == _NOT_EXIST_NEGATIVE:
        return "non_existent_without_if_exists"
    if pair == _PRIVILEGE_NEGATIVE:
        return "insufficient_privilege"
    return "dependent_objects_without_cascade"


def _outcome_for(
    assignment: dict[str, str],
) -> tuple[str, str, str | None]:
    pair = _present_failure_pair(assignment)
    if pair is None:
        return "success", "00000", None
    sqlstate, reason = _SFV_FAILURE_SQLSTATE[pair]
    return "expected_failure", sqlstate, reason


def _extension_multiset_sha256(
    cases: tuple[DropTypeFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"drop-type-factor-extension-v1\n")
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
    cases: tuple[DropTypeFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"DROP TYPE extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "drop_type_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "DROP TYPE",
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


def build_drop_type_factor_extension_plan(
    repository_root: Path,
) -> DropTypeFactorExtensionPlan:
    """Build the bounded DROP TYPE post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_drop_type_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[DropTypeFactorExtensionCase] = []
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
                    DropTypeFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"DROPTYPE{ordinal:05d}",
                        sql_filename=f"DROPTYPE{ordinal:05d}.sql",
                        object_prefix=f"droptype_{ordinal:05d}_",
                        derivation_id=(
                            f"DROPTYPE-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "drop_type_required_baseline_factor_space"
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
    return DropTypeFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "DropTypeFactorExtensionError",
    "DropTypeFactorExtensionCase",
    "DropTypeFactorExtensionPlan",
    "build_drop_type_factor_extension_plan",
    "_present_failure_pair",
    "_failure_unit_count",
]
