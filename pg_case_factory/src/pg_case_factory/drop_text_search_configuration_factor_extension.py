"""Bounded post-coverage cross-factor extension expander for DROP TEXT SEARCH CONFIGURATION.

The marginal factor-value-loop (:mod:`drop_text_search_configuration_factor_loop`)
is the required baseline: one program per factor value, 38 local cases (GRM 1 +
SFV 35 + RISK 2).  This module adds the bounded post-coverage extension phase:
cross-factor combinations of the behaviour axes across the single official
synopsis branch (at most one failure-causing value per case, so attribution
stays clean), with ``verification_mode`` crossed and ``cleanup_mode`` crossed
so every declared T6 value is exercised.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``derived_extension_required_fields``) and is marked ``is_extension = True``.
The negative factors (``authorization_path=non_owner``,
``object_state=absent`` / ``config_name_shape=non_existent_name`` when
``if_exists_clause=absent``, ``dependency_status=has_dependencies`` under a
RESTRICT policy) are crossed here with at-most-one-failure attribution; the
privilege boundary fires first (42501), then the configuration-lookup
boundary (42704), then the dependency boundary (2BP01).

The single official synopsis branch is crossed:

* ``branch_drop_ts_config`` — ``authorization_path`` x ``object_state`` x
  ``if_exists_clause`` x ``cascade_restrict`` x ``dependency_status`` x
  ``config_name_shape``.  ``privilege_context``, ``dependency_context``,
  ``error_type``, and ``expected_status`` are derived from the active
  privilege / dependency / object-missing state so every shipped value stays
  coherent and witnessed.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .drop_text_search_configuration_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_drop_text_search_configuration_factor_loop_plan,
)


class DropTextSearchConfigurationFactorExtensionError(ValueError):
    """Raised when a frozen DROP TEXT SEARCH CONFIGURATION extension input drifts."""


@dataclass(frozen=True)
class DropTextSearchConfigurationFactorExtensionCase:
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
class DropTextSearchConfigurationFactorExtensionPlan:
    cases: tuple[DropTextSearchConfigurationFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 38
_CAP = 20000

_VERIFICATION_MODES = (
    "catalog_query",
    "error_assertion",
    "notice_assertion",
)
_CLEANUP_MODES = (
    "cascade_cleanup",
    "manual_dependency_cleanup",
)

# Dense baseline assignment (all positive values).  The negative factors
# (authorization_path=non_owner, object_state=absent /
# config_name_shape=non_existent_name, dependency_status=has_dependencies)
# are crossed here with at-most-one-failure attribution.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_ts_config",
    "grammar_branch": "branch_1",
    "target_action": "drop_text_search_configuration",
    "object_state": "exists",
    "expected_status": "success",
    "if_exists_clause": "present",
    "cascade_restrict": "default_restrict",
    "authorization_path": "owner",
    "dependency_status": "no_dependencies",
    "config_name_shape": "simple_id",
    "privilege_context": "owner_session",
    "dependency_context": "no_dependencies",
    "error_type": "none",
    "verification_mode": "catalog_query",
    "cleanup_mode": "cascade_cleanup",
}

_BRANCH_GRAMMAR: dict[str, str] = {
    "branch_drop_ts_config": "branch_1",
}

_BRANCH_FIXED_ACTION: dict[str, str] = {
    "branch_drop_ts_config": "drop_text_search_configuration",
}

# Crossed positive behaviour axes per branch.  statement_branch is held at the
# bare branch (the IF EXISTS grammar is exercised via if_exists_clause and is
# fully covered by the baseline); privilege_context / dependency_context /
# error_type / expected_status are derived so they stay coherent.
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_drop_ts_config": {
        "authorization_path": ("non_owner", "owner", "superuser"),
        "object_state": ("exists", "absent"),
        "if_exists_clause": ("present", "absent"),
        "cascade_restrict": (
            "default_restrict",
            "explicit_cascade",
            "explicit_restrict",
        ),
        "dependency_status": ("no_dependencies", "has_dependencies"),
        "config_name_shape": (
            "simple_id",
            "schema_qualified_id",
            "quoted_id",
            "reserved_word_id",
            "non_existent_name",
        ),
    },
}

# Failure boundaries (in PostgreSQL execution order: privilege ->
# configuration lookup -> dependency).  The privilege boundary (42501) fires
# first.  The configuration-lookup boundary (42704) fires when the target
# configuration is absent (object_state=absent or config_name_shape=
# non_existent_name) AND IF EXISTS is omitted.  The dependency boundary
# (2BP01) fires only when the configuration EXISTS (a dependent object can
# only block a drop of an existing configuration) under a non-CASCADE policy
# with dependencies.
_PRIVILEGE_NEGATIVE = ("authorization_path", "non_owner")
_CONFIG_MISSING_OBJECT = ("object_state", "absent")
_CONFIG_MISSING_NAME = ("config_name_shape", "non_existent_name")
_DEPENDENCY_NEGATIVE = ("dependency_status", "has_dependencies")
_RESTRICT_VALUES = frozenset({"default_restrict", "explicit_restrict"})
_IF_EXISTS_OMITTED = "absent"


def _config_exists(assignment: dict[str, str]) -> bool:
    return (
        assignment.get("object_state") == "exists"
        and assignment.get("config_name_shape") != "non_existent_name"
    )


def _privilege_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("authorization_path") == "non_owner"


def _config_missing_failure_fires(assignment: dict[str, str]) -> bool:
    """config-missing fires only when IF EXISTS is omitted."""

    if assignment.get("if_exists_clause") != _IF_EXISTS_OMITTED:
        return False
    return (
        assignment.get("object_state") == "absent"
        or assignment.get("config_name_shape") == "non_existent_name"
    )


def _dependency_failure_fires(assignment: dict[str, str]) -> bool:
    """has_dependencies fires only under a non-CASCADE drop on an existing config."""

    if not _config_exists(assignment):
        return False
    return (
        assignment.get("dependency_status") == "has_dependencies"
        and assignment.get("cascade_restrict") in _RESTRICT_VALUES
    )


def _failure_unit_count(assignment: dict[str, str]) -> int:
    count = 0
    if _privilege_failure_fires(assignment):
        count += 1
    if _config_missing_failure_fires(assignment):
        count += 1
    if _dependency_failure_fires(assignment):
        count += 1
    return count


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success.

    The privilege boundary (42501) fires before the object lookup, so it is
    attributed first.  The configuration-lookup boundary (42704) fires next
    when the configuration is absent and IF EXISTS is omitted.  The dependency
    boundary (2BP01) fires last under RESTRICT with dependencies on an
    existing configuration.
    """

    if _privilege_failure_fires(assignment):
        return _PRIVILEGE_NEGATIVE
    if _config_missing_failure_fires(assignment):
        if assignment.get("object_state") == "absent":
            return _CONFIG_MISSING_OBJECT
        return _CONFIG_MISSING_NAME
    if _dependency_failure_fires(assignment):
        return _DEPENDENCY_NEGATIVE
    return None


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    return _failure_unit_count(assignment) <= 1


def _privilege_context_for(authorization_path: str) -> str:
    return {
        "non_owner": "non_owner_session",
        "owner": "owner_session",
        "superuser": "superuser_session",
    }[authorization_path]


def _dependency_context_for(dependency_status: str) -> str:
    return {
        "no_dependencies": "no_dependencies",
        "has_dependencies": "config_used_by_other_object",
    }[dependency_status]


def _error_type_for(assignment: dict[str, str]) -> str:
    pair = _present_failure_pair(assignment)
    if pair is None:
        return "none"
    if pair == _PRIVILEGE_NEGATIVE:
        return "insufficient_privilege"
    if pair == _DEPENDENCY_NEGATIVE:
        return "dependent_object_exists"
    return "non_existent_without_if_exists"


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
            assignment["privilege_context"] = _privilege_context_for(
                assignment["authorization_path"]
            )
            assignment["dependency_context"] = _dependency_context_for(
                assignment["dependency_status"]
            )
            if not _is_valid_combination(assignment):
                continue
            assignment["error_type"] = _error_type_for(assignment)
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
    cases: tuple[DropTextSearchConfigurationFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"drop-text-search-configuration-factor-extension-v1\n"
    )
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
    cases: tuple[DropTextSearchConfigurationFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"DROP TEXT SEARCH CONFIGURATION extension "
                    f"{case.ordinal:05d}: {case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": (
                        "drop_text_search_configuration_factor_extension"
                    ),
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "DROP TEXT SEARCH CONFIGURATION",
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


def build_drop_text_search_configuration_factor_extension_plan(
    repository_root: Path,
) -> DropTextSearchConfigurationFactorExtensionPlan:
    """Build the bounded DROP TEXT SEARCH CONFIGURATION post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_drop_text_search_configuration_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[DropTextSearchConfigurationFactorExtensionCase] = []
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
                    DropTextSearchConfigurationFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"DROPTEXTSEARCHCONFIGURATION{ordinal:05d}",
                        sql_filename=(
                            f"DROPTEXTSEARCHCONFIGURATION{ordinal:05d}.sql"
                        ),
                        object_prefix=(
                            f"droptextsearchconfiguration_{ordinal:05d}_"
                        ),
                        derivation_id=(
                            f"DROPTEXTSEARCHCONFIGURATION-EXT|{ordinal:05d}"
                            f"|{action}|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "drop_text_search_configuration_required_baseline_factor_space"
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
    return DropTextSearchConfigurationFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "DropTextSearchConfigurationFactorExtensionError",
    "DropTextSearchConfigurationFactorExtensionCase",
    "DropTextSearchConfigurationFactorExtensionPlan",
    "build_drop_text_search_configuration_factor_extension_plan",
    "_present_failure_pair",
    "_failure_unit_count",
]
