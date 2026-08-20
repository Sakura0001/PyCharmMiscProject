"""Bounded post-coverage cross-factor extension expander for DROP SCHEMA.

The marginal factor-value-loop (:mod:`drop_schema_factor_loop`) is the
required baseline: one program per factor value, 43 local cases
(GRM 1 + SFV 40 + Risk 2).  This module adds the bounded post-coverage
extension phase: cross-factor combinations of the behaviour axes (at most one
failure-causing value per case, so attribution stays clean), with
``verification_mode`` crossed and ``cleanup_mode`` crossed so every declared T6
value is exercised.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record and is marked ``is_extension = True``.
The negative factors (``privilege_level=non_owner``; ``object_state=not_exists``
when ``if_exists_clause=absent``; ``object_state=exists_with_objects`` under a
non-CASCADE drop policy) are crossed here with at-most-one-failure attribution;
the privilege boundary fires first (42501), then the not-exist boundary (42704),
then the contains-without-cascade boundary (2BP01).
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .drop_schema_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_drop_schema_factor_loop_plan,
)


class DropSchemaFactorExtensionError(ValueError):
    """Raised when a frozen DROP SCHEMA extension input drifts."""


@dataclass(frozen=True)
class DropSchemaFactorExtensionCase:
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
class DropSchemaFactorExtensionPlan:
    cases: tuple[DropSchemaFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 43
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_namespace_query",
    "information_schema_schemata",
    "error_assertion",
    "notice_assertion",
)
_CLEANUP_MODES = (
    "no_cleanup_needed",
    "manual_cleanup",
    "rollback",
)

# Dense baseline assignment (all positive values).  The negative factors
# (privilege_level=non_owner; object_state=not_exists with if_exists_clause=
# absent; object_state=exists_with_objects under RESTRICT) are crossed here
# with at-most-one-failure attribution.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_schema",
    "grammar_branch": "branch_1",
    "target_action": "drop_schema",
    "object_state": "exists_empty",
    "expected_status": "success",
    "if_exists_clause": "absent",
    "cascade_restrict": "none",
    "multi_schema_drop": "single_schema",
    "schema_name_shape": "simple",
    "privilege_level": "superuser",
    "contained_objects_state": "empty_schema",
    "cross_schema_dependency": "no_cross_dependency",
    "error_boundary": "none",
    "verification_mode": "pg_namespace_query",
    "cleanup_mode": "no_cleanup_needed",
}

_BRANCH_GRAMMAR: dict[str, str] = {
    "branch_drop_schema": "branch_1",
    "branch_drop_schema_if_exists": "branch_1",
}
_BRANCH_FIXED_ACTION: dict[str, str] = {
    "branch_drop_schema": "drop_schema",
    "branch_drop_schema_if_exists": "drop_schema",
}

# Crossed positive behaviour axes.  Held constant: multi_schema_drop,
# schema_name_shape, cross_schema_dependency (these are witnessed in the
# baseline 1:1 marginal and would explode the cross without adding clean
# attribution).
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_drop_schema": {
        "privilege_level": ("owner", "superuser", "non_owner"),
        "object_state": (
            "exists_empty",
            "exists_with_objects",
            "not_exists",
        ),
        "if_exists_clause": ("absent", "present"),
        "cascade_restrict": ("none", "cascade", "restrict"),
        "contained_objects_state": (
            "empty_schema",
            "has_tables",
            "has_views",
            "has_functions",
            "has_multiple_object_types",
        ),
    },
}

# Failure boundaries (in PostgreSQL execution order: privilege -> lookup ->
# dependency).  The privilege boundary (42501) fires first.  The not-exist
# boundary (42704) fires when the schema is absent and IF EXISTS is omitted.
# The contains-without-cascade boundary (2BP01) fires when a schema holding
# objects is dropped under RESTRICT (explicit or the omitted default).
_PRIVILEGE_NEGATIVE = ("privilege_level", "non_owner")
_NOT_EXIST_NEGATIVE = ("object_state", "not_exists")
_CONTAINS_NEGATIVE = ("object_state", "exists_with_objects")
_RESTRICT_VALUES = frozenset({"none", "restrict"})
_IF_EXISTS_OMITTED = "absent"


def _privilege_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("privilege_level") == "non_owner"


def _not_exist_failure_fires(assignment: dict[str, str]) -> bool:
    """not_exists fires only when IF EXISTS is omitted."""

    return (
        assignment.get("object_state") == "not_exists"
        and assignment.get("if_exists_clause") == _IF_EXISTS_OMITTED
    )


def _contains_failure_fires(assignment: dict[str, str]) -> bool:
    """exists_with_objects fires only under a non-CASCADE drop policy."""

    return (
        assignment.get("object_state") == "exists_with_objects"
        and assignment.get("cascade_restrict") in _RESTRICT_VALUES
    )


def _failure_unit_count(assignment: dict[str, str]) -> int:
    count = 0
    if _privilege_failure_fires(assignment):
        count += 1
    if _not_exist_failure_fires(assignment):
        count += 1
    if _contains_failure_fires(assignment):
        count += 1
    return count


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success.

    The privilege boundary (42501) fires before the object lookup.  The
    not-exist boundary (42704) fires next when the schema is absent and IF
    EXISTS is omitted.  The contains-without-cascade boundary (2BP01) fires
    last under RESTRICT with contained objects.
    """

    if _privilege_failure_fires(assignment):
        return _PRIVILEGE_NEGATIVE
    if _not_exist_failure_fires(assignment):
        return _NOT_EXIST_NEGATIVE
    if _contains_failure_fires(assignment):
        return _CONTAINS_NEGATIVE
    return None


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    # Consistency: a not-exists or empty schema cannot hold contained objects
    # or carry a cross-schema dependency.
    object_state = assignment.get("object_state")
    contained = assignment.get("contained_objects_state")
    if object_state in ("not_exists", "exists_empty"):
        if contained != "empty_schema":
            return False
    if object_state == "exists_with_objects":
        if contained == "empty_schema":
            return False
    return _failure_unit_count(assignment) <= 1


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments passing the consistency + failure filter."""

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
    cases: tuple[DropSchemaFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"drop-schema-factor-extension-v1\n")
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
    cases: tuple[DropSchemaFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"DROP SCHEMA extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "drop_schema_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "DROP SCHEMA",
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


def build_drop_schema_factor_extension_plan(
    repository_root: Path,
) -> DropSchemaFactorExtensionPlan:
    """Build the bounded DROP SCHEMA post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_drop_schema_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[DropSchemaFactorExtensionCase] = []
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
                    DropSchemaFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"DROPSCHEMA{ordinal:05d}",
                        sql_filename=f"DROPSCHEMA{ordinal:05d}.sql",
                        object_prefix=f"dropschema_{ordinal:05d}_",
                        derivation_id=(
                            f"DROPSCHEMA-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "drop_schema_required_baseline_factor_space"
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
    return DropSchemaFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "DropSchemaFactorExtensionError",
    "DropSchemaFactorExtensionCase",
    "DropSchemaFactorExtensionPlan",
    "build_drop_schema_factor_extension_plan",
    "_present_failure_pair",
    "_failure_unit_count",
]
