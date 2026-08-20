"""Bounded post-coverage cross-factor extension expander for DROP TEXT SEARCH TEMPLATE.

The marginal factor-value-loop (:mod:`drop_text_search_template_factor_loop`)
is the required baseline: one program per factor value, 36 local cases (GRM 1
+ SFV 33 + Risk 2).  This module adds the bounded post-coverage extension
phase: cross-factor combinations of the behaviour axes across the single
official synopsis branch (at most one failure-causing value per case, so
attribution stays clean), with ``verification_mode`` crossed and
``cleanup_mode`` crossed so every declared T6 value is exercised.

The negative factors (``privilege_requirement=non_superuser`` /
``privilege_context=non_superuser_session``, ``object_state=absent`` /
``template_name_shape=non_existent_name`` when ``if_exists_clause=absent``,
``dependency_context=dict_using_template`` / ``dependency_status=
has_dict_dependencies`` under RESTRICT) are crossed here with
at-most-one-failure attribution; the privilege boundary fires first (42501),
then the template-lookup boundary (42704), then the dependency boundary
(2BP01).
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .drop_text_search_template_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_drop_text_search_template_factor_loop_plan,
)


class DropTextSearchTemplateFactorExtensionError(ValueError):
    """Raised when a frozen DROP TEXT SEARCH TEMPLATE extension input drifts."""


@dataclass(frozen=True)
class DropTextSearchTemplateFactorExtensionCase:
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
class DropTextSearchTemplateFactorExtensionPlan:
    cases: tuple[DropTextSearchTemplateFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 36
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

# Dense baseline assignment (all positive values).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_ts_template",
    "grammar_branch": "branch_1",
    "target_action": "drop_text_search_template",
    "object_state": "exists",
    "expected_status": "success",
    "if_exists_clause": "present",
    "cascade_restrict": "default_restrict",
    "privilege_requirement": "superuser",
    "privilege_context": "superuser_session",
    "dependency_status": "no_dependencies",
    "dependency_context": "no_dependencies",
    "template_name_shape": "simple_id",
    "error_type": "none",
    "verification_mode": "catalog_query",
    "cleanup_mode": "cascade_cleanup",
}

_BRANCH_GRAMMAR: dict[str, str] = {
    "branch_drop_ts_template": "branch_1",
}

_BRANCH_FIXED_ACTION: dict[str, str] = {
    "branch_drop_ts_template": "drop_text_search_template",
}

# Crossed positive behaviour axes per branch.
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_drop_ts_template": {
        "privilege_requirement": ("non_superuser", "superuser"),
        "privilege_context": (
            "non_superuser_session",
            "superuser_session",
        ),
        "object_state": ("absent", "exists"),
        "if_exists_clause": ("absent", "present"),
        "cascade_restrict": (
            "default_restrict",
            "explicit_restrict",
            "explicit_cascade",
        ),
        "dependency_context": ("dict_using_template", "no_dependencies"),
        "dependency_status": (
            "has_dict_dependencies",
            "no_dependencies",
        ),
        "template_name_shape": (
            "non_existent_name",
            "quoted_id",
            "reserved_word_id",
            "schema_qualified_id",
            "simple_id",
        ),
    },
}

# Failure boundaries (in PostgreSQL execution order: privilege -> template
# lookup -> dependency).  The privilege boundary (42501) fires first.  The
# template-lookup boundary (42704) fires when the template is absent
# (object_state=absent or template_name_shape=non_existent_name) and IF EXISTS
# is omitted.  The dependency boundary (2BP01) fires when a dictionary
# dependency exists and RESTRICT (or default RESTRICT) is used AND the
# template exists (the dependency can only exist if the template was created).
_PRIVILEGE_NEGATIVE = ("privilege_requirement", "non_superuser")
_OBJECT_MISSING_NEGATIVE = ("object_state", "absent")
_NAME_MISSING_NEGATIVE = ("template_name_shape", "non_existent_name")
_DEPENDENCY_NEGATIVE = ("dependency_context", "dict_using_template")
_RESTRICT_VALUES = frozenset({"default_restrict", "explicit_restrict"})
_IF_EXISTS_OMITTED = "absent"


def _template_exists(assignment: dict[str, str]) -> bool:
    return (
        assignment.get("object_state") == "exists"
        and assignment.get("template_name_shape") != "non_existent_name"
    )


def _privilege_failure_fires(assignment: dict[str, str]) -> bool:
    return (
        assignment.get("privilege_requirement") == "non_superuser"
        or assignment.get("privilege_context") == "non_superuser_session"
    )


def _object_missing_failure_fires(assignment: dict[str, str]) -> bool:
    return (
        assignment.get("object_state") == "absent"
        and assignment.get("if_exists_clause") == _IF_EXISTS_OMITTED
    )


def _name_missing_failure_fires(assignment: dict[str, str]) -> bool:
    return (
        assignment.get("template_name_shape") == "non_existent_name"
        and assignment.get("if_exists_clause") == _IF_EXISTS_OMITTED
    )


def _dependency_failure_fires(assignment: dict[str, str]) -> bool:
    dep = (
        assignment.get("dependency_context") == "dict_using_template"
        or assignment.get("dependency_status") == "has_dict_dependencies"
    )
    return (
        dep
        and _template_exists(assignment)
        and assignment.get("cascade_restrict") in _RESTRICT_VALUES
    )


def _failure_unit_count(assignment: dict[str, str]) -> int:
    count = 0
    if _privilege_failure_fires(assignment):
        count += 1
    if _object_missing_failure_fires(assignment):
        count += 1
    if _name_missing_failure_fires(assignment):
        count += 1
    if _dependency_failure_fires(assignment):
        count += 1
    return count


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success."""

    if _privilege_failure_fires(assignment):
        if assignment.get("privilege_requirement") == "non_superuser":
            return _PRIVILEGE_NEGATIVE
        return ("privilege_context", "non_superuser_session")
    if _object_missing_failure_fires(assignment):
        return _OBJECT_MISSING_NEGATIVE
    if _name_missing_failure_fires(assignment):
        return _NAME_MISSING_NEGATIVE
    if _dependency_failure_fires(assignment):
        if assignment.get("dependency_context") == "dict_using_template":
            return _DEPENDENCY_NEGATIVE
        return ("dependency_status", "has_dict_dependencies")
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
    cases: tuple[DropTextSearchTemplateFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"drop-text-search-template-factor-extension-v1\n"
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
    cases: tuple[DropTextSearchTemplateFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"DROP TEXT SEARCH TEMPLATE extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "drop_text_search_template_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "DROP TEXT SEARCH TEMPLATE",
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


def build_drop_text_search_template_factor_extension_plan(
    repository_root: Path,
) -> DropTextSearchTemplateFactorExtensionPlan:
    """Build the bounded DROP TEXT SEARCH TEMPLATE post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_drop_text_search_template_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[DropTextSearchTemplateFactorExtensionCase] = []
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
                    DropTextSearchTemplateFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"DROPTEXTSEARCHTEMPLATE{ordinal:05d}",
                        sql_filename=f"DROPTEXTSEARCHTEMPLATE{ordinal:05d}.sql",
                        object_prefix=f"droptextsearchtemplate_{ordinal:05d}_",
                        derivation_id=(
                            f"DROPTEXTSEARCHTEMPLATE-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "drop_text_search_template_required_baseline_factor_space"
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
    return DropTextSearchTemplateFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "DropTextSearchTemplateFactorExtensionError",
    "DropTextSearchTemplateFactorExtensionCase",
    "DropTextSearchTemplateFactorExtensionPlan",
    "build_drop_text_search_template_factor_extension_plan",
    "_present_failure_pair",
    "_failure_unit_count",
]
