"""Bounded post-coverage cross-factor extension expander for DROP RULE.

The marginal factor-value-loop (:mod:`drop_rule_factor_loop`) is the required
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
``object_state=absent`` / ``rule_name_shape=nonexistent_name`` when
``if_exists_clause=absent``, ``dependency_context=has_dependent_objects``
under RESTRICT) are crossed here with at-most-one-failure attribution; the
privilege boundary fires first (42501), then the table-lookup boundary
(42P01), then the rule-lookup boundary (42704), then the dependency
boundary (2BP01).

The single official synopsis branch is crossed:

* ``branch_drop_rule`` — ``privilege_level`` x ``table_existence`` x
  ``object_state`` x ``if_exists_clause`` x ``cascade_restrict`` x
  ``dependency_context`` x ``target_rule_type`` x ``rule_name_shape``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .drop_rule_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_drop_rule_factor_loop_plan,
)


class DropRuleFactorExtensionError(ValueError):
    """Raised when a frozen DROP RULE extension input drifts."""


@dataclass(frozen=True)
class DropRuleFactorExtensionCase:
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
class DropRuleFactorExtensionPlan:
    cases: tuple[DropRuleFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 50
_CAP = 20000

_VERIFICATION_MODES = (
    "catalog_query_pg_rewrite",
    "error_assertion",
    "notice_assertion",
)
_CLEANUP_MODES = (
    "drop_rule",
    "drop_view_after_return_drop",
    "drop_table",
    "cascade_cleanup",
)

# Dense baseline assignment (all positive values).  The negative factors
# (privilege_level=non_owner, object_state=absent / rule_name_shape=
# nonexistent_name, dependency_context=has_dependent_objects) are crossed
# here with at-most-one-failure attribution.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_rule",
    "grammar_branch": "branch_1",
    "target_action": "drop_rule",
    "object_state": "exists",
    "expected_status": "success",
    "if_exists_clause": "present",
    "cascade_restrict": "omitted_default_restrict",
    "target_rule_type": "normal_rule",
    "rule_name_shape": "simple_id",
    "table_name_shape": "simple_id",
    "privilege_level": "superuser",
    "table_existence": "table_exists",
    "dependency_context": "no_dependencies",
    "nonexistent_rule": "rule_exists",
    "nonexistent_table": "table_exists",
    "privilege_denied": "owner_execution",
    "has_dependents_restrict": "no_dependents_safe",
    "on_select_return_drop": "normal_rule_drop",
    "verification_mode": "catalog_query_pg_rewrite",
    "cleanup_mode": "drop_rule",
}

_BRANCH_GRAMMAR: dict[str, str] = {
    "branch_drop_rule": "branch_1",
}

_BRANCH_FIXED_ACTION: dict[str, str] = {
    "branch_drop_rule": "drop_rule",
}

# Crossed positive behaviour axes per branch.
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_drop_rule": {
        "privilege_level": (
            "non_owner",
            "superuser",
            "table_owner",
        ),
        "table_existence": ("table_exists", "table_not_exists"),
        "object_state": ("exists", "absent"),
        "if_exists_clause": ("present", "absent"),
        "cascade_restrict": (
            "cascade",
            "omitted_default_restrict",
            "restrict",
        ),
        "dependency_context": ("no_dependencies", "has_dependent_objects"),
        "target_rule_type": ("normal_rule", "on_select_return_rule"),
        "rule_name_shape": (
            "simple_id",
            "quoted_id",
            "_RETURN_special",
            "nonexistent_name",
            "existing_name",
        ),
    },
}

# Failure boundaries (in PostgreSQL execution order: privilege -> table
# lookup -> rule lookup -> dependency).  The privilege boundary (42501)
# fires first.  The table-lookup boundary (42P01) fires when the host
# relation is absent.  The rule-lookup boundary (42704) fires when the rule
# is absent (object_state=absent or rule_name_shape=nonexistent_name) and IF
# EXISTS is omitted.  The dependency boundary (2BP01) fires when RESTRICT
# (or default RESTRICT) is used with dependents.
_PRIVILEGE_NEGATIVE = ("privilege_level", "non_owner")
_TABLE_MISSING_NEGATIVE = ("table_existence", "table_not_exists")
_RULE_MISSING_OBJECT = ("object_state", "absent")
_RULE_MISSING_NAME = ("rule_name_shape", "nonexistent_name")
_DEPENDENCY_NEGATIVE = ("dependency_context", "has_dependent_objects")
_RESTRICT_VALUES = frozenset({"omitted_default_restrict", "restrict"})
_IF_EXISTS_OMITTED = "absent"


def _privilege_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("privilege_level") == "non_owner"


def _table_missing_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("table_existence") == "table_not_exists"


def _rule_missing_failure_fires(assignment: dict[str, str]) -> bool:
    """rule-missing fires only when IF EXISTS is omitted."""

    if assignment.get("if_exists_clause") != _IF_EXISTS_OMITTED:
        return False
    return (
        assignment.get("object_state") == "absent"
        or assignment.get("rule_name_shape") == "nonexistent_name"
    )


def _dependency_failure_fires(assignment: dict[str, str]) -> bool:
    """has_dependent_objects fires only under a non-CASCADE drop policy."""

    return (
        assignment.get("dependency_context") == "has_dependent_objects"
        and assignment.get("cascade_restrict") in _RESTRICT_VALUES
    )


def _failure_unit_count(assignment: dict[str, str]) -> int:
    count = 0
    if _privilege_failure_fires(assignment):
        count += 1
    if _table_missing_failure_fires(assignment):
        count += 1
    if _rule_missing_failure_fires(assignment):
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
    host relation is absent.  The rule-lookup boundary (42704) fires next
    when the rule is absent and IF EXISTS is omitted.  The dependency
    boundary (2BP01) fires last under RESTRICT with dependencies.
    """

    if _privilege_failure_fires(assignment):
        return _PRIVILEGE_NEGATIVE
    if _table_missing_failure_fires(assignment):
        return _TABLE_MISSING_NEGATIVE
    if _rule_missing_failure_fires(assignment):
        if assignment.get("object_state") == "absent":
            return _RULE_MISSING_OBJECT
        return _RULE_MISSING_NAME
    if _dependency_failure_fires(assignment):
        return _DEPENDENCY_NEGATIVE
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
    cases: tuple[DropRuleFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"drop-rule-factor-extension-v1\n")
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
    cases: tuple[DropRuleFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"DROP RULE extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "drop_rule_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "DROP RULE",
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


def build_drop_rule_factor_extension_plan(
    repository_root: Path,
) -> DropRuleFactorExtensionPlan:
    """Build the bounded DROP RULE post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_drop_rule_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[DropRuleFactorExtensionCase] = []
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
                    DropRuleFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"DROPRULE{ordinal:05d}",
                        sql_filename=f"DROPRULE{ordinal:05d}.sql",
                        object_prefix=f"droprule_{ordinal:05d}_",
                        derivation_id=(
                            f"DROPRULE-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "drop_rule_required_baseline_factor_space"
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
    return DropRuleFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "DropRuleFactorExtensionError",
    "DropRuleFactorExtensionCase",
    "DropRuleFactorExtensionPlan",
    "build_drop_rule_factor_extension_plan",
    "_present_failure_pair",
    "_failure_unit_count",
]
