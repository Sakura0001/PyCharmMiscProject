"""Bounded post-coverage cross-factor extension expander for DROP TABLE.

The marginal factor-value-loop (:mod:`drop_table_factor_loop`) is the required
baseline: one program per factor value, 50 local cases (GRM 1 + SFV 47 +
Risk 2).  This module adds the bounded post-coverage extension phase:
cross-factor combinations of the behaviour axes across the single official
synopsis branch (at most one failure-causing value per case, so attribution
stays clean), with ``verification_mode`` crossed and ``cleanup_mode``
crossed so every declared T6 value is exercised.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``derived_extension_required_fields``) and is marked ``is_extension = True``.
The negative factors (``privilege_level=non_owner``,
``object_state=not_exists`` when ``if_exists_clause=absent``,
``dependency_state=has_views`` / ``has_fk_references`` under RESTRICT) are
crossed here with at-most-one-failure attribution; the privilege boundary
fires first (42501), then the table-lookup boundary (42P01), then the
dependency boundary (2BP01).

The single official synopsis branch is crossed:

* ``branch_drop_table`` — ``object_state`` x ``privilege_level`` x
  ``dependency_state`` x ``if_exists_clause`` x ``cascade_restrict``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .drop_table_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_drop_table_factor_loop_plan,
)


class DropTableFactorExtensionError(ValueError):
    """Raised when a frozen DROP TABLE extension input drifts."""


@dataclass(frozen=True)
class DropTableFactorExtensionCase:
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
class DropTableFactorExtensionPlan:
    cases: tuple[DropTableFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 50
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_class_query",
    "error_assertion",
    "notice_assertion",
    "effect_query",
)
_CLEANUP_MODES = (
    "cascade_cleanup",
    "manual_cleanup",
    "rollback",
)

# Dense baseline assignment (all positive values).  The negative factors
# (privilege_level=non_owner, object_state=not_exists, dependency_state=
# has_views/has_fk_references) are crossed here with at-most-one-failure
# attribution.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_table",
    "grammar_branch": "branch_1",
    "target_action": "drop_table",
    "object_state": "exists_permanent",
    "expected_status": "success",
    "if_exists_clause": "absent",
    "cascade_restrict": "none",
    "table_type_permanence": "permanent",
    "table_name_shape": "simple",
    "multi_table_drop": "single_table",
    "privilege_level": "owner",
    "dependency_state": "no_dependents",
    "error_boundary": "none",
    "verification_mode": "pg_class_query",
    "cleanup_mode": "cascade_cleanup",
}

_BRANCH_GRAMMAR: dict[str, str] = {
    "branch_drop_table": "branch_1",
}

_BRANCH_FIXED_ACTION: dict[str, str] = {
    "branch_drop_table": "drop_table",
}

# Crossed positive behaviour axes per branch.
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_drop_table": {
        "object_state": (
            "exists_permanent",
            "not_exists",
            "exists_temporary",
            "exists_unlogged",
        ),
        "privilege_level": (
            "owner",
            "superuser",
            "schema_owner",
            "non_owner",
        ),
        "dependency_state": (
            "no_dependents",
            "has_views",
            "has_fk_references",
            "has_triggers",
            "has_indexes",
            "has_policies",
            "has_rules",
        ),
        "if_exists_clause": ("absent", "present"),
        "cascade_restrict": ("none", "cascade", "restrict"),
    },
}

# Failure boundaries (in PostgreSQL execution order: privilege -> table
# lookup -> dependency).  The privilege boundary (42501) fires first.
# The table-lookup boundary (42P01) fires when the target table is absent
# and IF EXISTS is omitted.  The dependency boundary (2BP01) fires when
# dependent views or FK constraints exist under RESTRICT (or default
# RESTRICT).  Note: has_triggers, has_indexes, has_policies, and has_rules
# are auto-removed by DROP TABLE and do NOT fire under RESTRICT.
_PRIVILEGE_NEGATIVE = ("privilege_level", "non_owner")
_TABLE_MISSING_NEGATIVE = ("object_state", "not_exists")
_DEPENDENCY_NEGATIVES = frozenset(
    {
        ("dependency_state", "has_views"),
        ("dependency_state", "has_fk_references"),
    }
)
_RESTRICT_VALUES = frozenset({"none", "restrict"})
_IF_EXISTS_OMITTED = "absent"


def _privilege_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("privilege_level") == "non_owner"


def _table_missing_failure_fires(assignment: dict[str, str]) -> bool:
    """table-missing fires only when IF EXISTS is omitted."""

    if assignment.get("if_exists_clause") != _IF_EXISTS_OMITTED:
        return False
    return assignment.get("object_state") == "not_exists"


def _dependency_failure_fires(assignment: dict[str, str]) -> bool:
    """has_views/has_fk_references fire only under a non-CASCADE drop policy."""

    dep = assignment.get("dependency_state")
    if dep is None:
        return False
    pair = ("dependency_state", dep)
    if pair not in _DEPENDENCY_NEGATIVES:
        return False
    return assignment.get("cascade_restrict") in _RESTRICT_VALUES


def _failure_unit_count(assignment: dict[str, str]) -> int:
    count = 0
    if _privilege_failure_fires(assignment):
        count += 1
    if _table_missing_failure_fires(assignment):
        count += 1
    if _dependency_failure_fires(assignment):
        count += 1
    return count


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success.

    The privilege boundary (42501) fires before the object lookup, so it is
    attributed first.  The table-lookup boundary (42P01) fires next when the
    target table is absent and IF EXISTS is omitted.  The dependency
    boundary (2BP01) fires last under RESTRICT with dependent views or FK
    constraints.
    """

    if _privilege_failure_fires(assignment):
        return _PRIVILEGE_NEGATIVE
    if _table_missing_failure_fires(assignment):
        return _TABLE_MISSING_NEGATIVE
    if _dependency_failure_fires(assignment):
        return ("dependency_state", assignment["dependency_state"])
    return None


def _is_valid_combination(assignment: dict[str, str]) -> bool:
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
    pair = _present_failure_pair(assignment)
    if pair is None:
        return "success", "00000", None
    sqlstate, reason = _SFV_FAILURE_SQLSTATE[pair]
    return "expected_failure", sqlstate, reason


def _extension_multiset_sha256(
    cases: tuple[DropTableFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"drop-table-factor-extension-v1\n")
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
    cases: tuple[DropTableFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"DROP TABLE extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "drop_table_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "DROP TABLE",
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


def build_drop_table_factor_extension_plan(
    repository_root: Path,
) -> DropTableFactorExtensionPlan:
    """Build the bounded DROP TABLE post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_drop_table_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[DropTableFactorExtensionCase] = []
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
                    DropTableFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"DROPTABLE{ordinal:05d}",
                        sql_filename=f"DROPTABLE{ordinal:05d}.sql",
                        object_prefix=f"droptable_{ordinal:05d}_",
                        derivation_id=(
                            f"DROPTABLE-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "drop_table_required_baseline_factor_space"
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
    return DropTableFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "DropTableFactorExtensionError",
    "DropTableFactorExtensionCase",
    "DropTableFactorExtensionPlan",
    "build_drop_table_factor_extension_plan",
    "_present_failure_pair",
    "_failure_unit_count",
]
