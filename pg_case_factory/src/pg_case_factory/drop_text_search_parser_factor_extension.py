"""Bounded post-coverage cross-factor extension expander for DROP TEXT SEARCH PARSER.

The marginal factor-value-loop (:mod:`drop_text_search_parser_factor_loop`)
is the required baseline: one program per factor value, 38 local cases
(GRM 1 + SFV 35 + Risk 2).  This module adds the bounded post-coverage
extension phase: cross-factor combinations of the behaviour axes across
the single official synopsis branch (at most one failure-causing value per
case, so attribution stays clean), with ``verification_mode`` crossed and
``cleanup_mode`` crossed so every declared T6 value is exercised.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``derived_extension_required_fields``) and is marked ``is_extension = True``.
The negative factors (``privilege_requirement=non_superuser``,
``object_state=absent`` / ``parser_name_shape=non_existent_name`` when
``if_exists_clause=absent``, ``dependency_context=config_using_parser``
under RESTRICT) are crossed here with at-most-one-failure attribution; the
privilege boundary fires first (42501), then the object-lookup boundary
(42704), then the dependency boundary (2BP01).

The single official synopsis branch is crossed:

* ``branch_drop_ts_parser`` — ``privilege_requirement`` x ``object_state``
  x ``if_exists_clause`` x ``cascade_restrict`` x ``dependency_context`` x
  ``parser_name_shape``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .drop_text_search_parser_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_drop_text_search_parser_factor_loop_plan,
)


class DropTsParserFactorExtensionError(ValueError):
    """Raised when a frozen DROP TEXT SEARCH PARSER extension input drifts."""


@dataclass(frozen=True)
class DropTsParserFactorExtensionCase:
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
class DropTsParserFactorExtensionPlan:
    cases: tuple[DropTsParserFactorExtensionCase, ...]
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

# Dense baseline assignment (all positive values).  The negative factors
# (privilege_requirement=non_superuser, object_state=absent /
# parser_name_shape=non_existent_name, dependency_context=
# config_using_parser) are crossed here with at-most-one-failure attribution.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_ts_parser",
    "grammar_branch": "branch_1",
    "target_action": "drop_text_search_parser",
    "object_state": "exists",
    "expected_status": "success",
    "if_exists_clause": "present",
    "cascade_restrict": "default_restrict",
    "privilege_requirement": "superuser",
    "dependency_status": "no_dependencies",
    "parser_name_shape": "simple_id",
    "privilege_context": "superuser_session",
    "dependency_context": "no_dependencies",
    "error_type": "none",
    "verification_mode": "catalog_query",
    "cleanup_mode": "cascade_cleanup",
}

_BRANCH_GRAMMAR: dict[str, str] = {
    "branch_drop_ts_parser": "branch_1",
}

_BRANCH_FIXED_ACTION: dict[str, str] = {
    "branch_drop_ts_parser": "drop_text_search_parser",
}

# Crossed positive behaviour axes per branch.
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_drop_ts_parser": {
        "privilege_requirement": (
            "non_superuser",
            "superuser",
        ),
        "object_state": ("exists", "absent"),
        "if_exists_clause": ("present", "absent"),
        "cascade_restrict": (
            "default_restrict",
            "explicit_restrict",
            "explicit_cascade",
        ),
        "dependency_context": (
            "no_dependencies",
            "config_using_parser",
        ),
        "parser_name_shape": (
            "simple_id",
            "schema_qualified_id",
            "quoted_id",
            "reserved_word_id",
            "non_existent_name",
        ),
    },
}

# Failure boundaries (in PostgreSQL execution order: privilege -> object
# lookup -> dependency).  The privilege boundary (42501) fires first.  The
# object-lookup boundary (42704) fires when the parser is absent
# (object_state=absent or parser_name_shape=non_existent_name) and IF EXISTS
# is omitted.  The dependency boundary (2BP01) fires when
# dependency_context=config_using_parser under a non-CASCADE drop policy.
_PRIVILEGE_NEGATIVE = ("privilege_requirement", "non_superuser")
_PARSER_MISSING_OBJECT = ("object_state", "absent")
_PARSER_MISSING_NAME = ("parser_name_shape", "non_existent_name")
_DEPENDENCY_NEGATIVE = ("dependency_context", "config_using_parser")
_RESTRICT_VALUES = frozenset({"default_restrict", "explicit_restrict"})
_IF_EXISTS_OMITTED = "absent"


def _privilege_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("privilege_requirement") == "non_superuser"


def _parser_missing_failure_fires(assignment: dict[str, str]) -> bool:
    """parser-missing fires only when IF EXISTS is omitted."""

    if assignment.get("if_exists_clause") != _IF_EXISTS_OMITTED:
        return False
    return (
        assignment.get("object_state") == "absent"
        or assignment.get("parser_name_shape") == "non_existent_name"
    )


def _dependency_failure_fires(assignment: dict[str, str]) -> bool:
    """config_using_parser fires only under a non-CASCADE drop policy."""

    return (
        assignment.get("dependency_context") == "config_using_parser"
        and assignment.get("cascade_restrict") in _RESTRICT_VALUES
    )


def _failure_unit_count(assignment: dict[str, str]) -> int:
    count = 0
    if _privilege_failure_fires(assignment):
        count += 1
    if _parser_missing_failure_fires(assignment):
        count += 1
    if _dependency_failure_fires(assignment):
        count += 1
    return count


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success.

    The privilege boundary (42501) fires before the object lookup, so it is
    attributed first.  The object-lookup boundary (42704) fires next when
    the parser is absent and IF EXISTS is omitted.  The dependency
    boundary (2BP01) fires last under RESTRICT with dependent configurations.
    """

    if _privilege_failure_fires(assignment):
        return _PRIVILEGE_NEGATIVE
    if _parser_missing_failure_fires(assignment):
        if assignment.get("object_state") == "absent":
            return _PARSER_MISSING_OBJECT
        return _PARSER_MISSING_NAME
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
    cases: tuple[DropTsParserFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"drop-text-search-parser-factor-extension-v1\n"
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
    cases: tuple[DropTsParserFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"DROP TEXT SEARCH PARSER extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "drop_text_search_parser_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "DROP TEXT SEARCH PARSER",
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


def build_drop_text_search_parser_factor_extension_plan(
    repository_root: Path,
) -> DropTsParserFactorExtensionPlan:
    """Build the bounded DROP TEXT SEARCH PARSER post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_drop_text_search_parser_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[DropTsParserFactorExtensionCase] = []
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
                    DropTsParserFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"DROPTEXTSEARCHPARSER{ordinal:05d}",
                        sql_filename=(
                            f"DROPTEXTSEARCHPARSER{ordinal:05d}.sql"
                        ),
                        object_prefix=(
                            f"droptextsearchparser_{ordinal:05d}_"
                        ),
                        derivation_id=(
                            f"DROPTEXTSEARCHPARSER-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "drop_text_search_parser_required_baseline_factor_space"
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
    return DropTsParserFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "DropTsParserFactorExtensionError",
    "DropTsParserFactorExtensionCase",
    "DropTsParserFactorExtensionPlan",
    "build_drop_text_search_parser_factor_extension_plan",
    "_present_failure_pair",
    "_failure_unit_count",
]
