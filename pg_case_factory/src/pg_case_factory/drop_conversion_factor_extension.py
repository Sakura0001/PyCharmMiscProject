"""Bounded post-coverage cross-factor extension expander for DROP CONVERSION.

The marginal factor-value-loop (:mod:`drop_conversion_factor_loop`) is the
required baseline: one program per factor value, 38 local cases
(GRM 1 + SFV 35 + Risk 2).  This module adds the bounded post-coverage
extension phase: cross-factor combinations of the positive behaviour axes
across the single official synopsis branch (at most one failure-causing
value per case, so attribution stays clean), with ``verification_mode``
crossed and ``cleanup_mode`` crossed so every declared T6 value is exercised.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record and is marked ``is_extension = True``.
The negative factors (``privilege_level=non_owner``,
``conversion_not_exist=conversion_not_exists``, ``conversion_name_shape=nonexistent_name``,
``schema_existence=schema_not_exists``) are crossed here with at-most-one-failure
attribution; the privilege boundary fires first (42501), then the schema boundary
(42704 for schema-qualified + schema_not_exists), then the not-exist boundary
(42704 when if_exists_clause=omitted).

The single official synopsis branch is crossed:

* ``branch_drop_conversion`` — ``privilege_level`` x ``conversion_not_exist`` x
  ``if_exists_clause`` x ``schema_existence`` x ``conversion_name_shape``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .drop_conversion_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_drop_conversion_factor_loop_plan,
)


class DropConversionFactorExtensionError(ValueError):
    """Raised when a frozen DROP CONVERSION extension input drifts."""


@dataclass(frozen=True)
class DropConversionFactorExtensionCase:
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
class DropConversionFactorExtensionPlan:
    cases: tuple[DropConversionFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 38
_CAP = 20000

_VERIFICATION_MODES = (
    "catalog_query_pg_conversion",
    "error_assertion",
    "notice_assertion_if_exists",
)
_CLEANUP_MODES = (
    "drop_conversion",
    "drop_schema_cascade",
)

# Dense baseline assignment (all positive values).  The negative factors
# (privilege_level=non_owner, conversion_not_exist=conversion_not_exists,
# conversion_name_shape=nonexistent_name, schema_existence=schema_not_exists)
# are crossed here with at-most-one-failure attribution.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_conversion",
    "grammar_branch": "branch_1",
    "target_action": "drop_conversion",
    "cascade_restrict": "omitted",
    "cascade_semantics_null": "cascade_no_effect",
    "cleanup_mode": "drop_conversion",
    "conversion_name_shape": "simple_id",
    "conversion_not_exist": "conversion_exists",
    "conversion_ownership": "is_owner",
    "expected_status": "success",
    "if_exists_clause": "omitted",
    "nonexistent_name": "valid_name",
    "object_state": "exists",
    "privilege_denied": "owner_success",
    "privilege_level": "superuser",
    "schema_existence": "schema_exists",
    "verification_mode": "catalog_query_pg_conversion",
}

_BRANCH_GRAMMAR: dict[str, str] = {
    "branch_drop_conversion": "branch_1",
}

_BRANCH_FIXED_ACTION: dict[str, str] = {
    "branch_drop_conversion": "drop_conversion",
}

# Crossed positive behaviour axes per branch.  conversion_name_shape includes
# nonexistent_name (a crossed negative owned by the extension).
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_drop_conversion": {
        "privilege_level": (
            "conversion_owner",
            "non_owner",
            "superuser",
        ),
        "conversion_not_exist": (
            "conversion_exists",
            "conversion_not_exists",
        ),
        "if_exists_clause": ("omitted", "specified_if_exists"),
        "schema_existence": ("schema_exists", "schema_not_exists"),
        "conversion_name_shape": (
            "nonexistent_name",
            "quoted_id",
            "schema_qualified",
            "simple_id",
        ),
    },
}

# Crossed behaviour-negative (factor, value) pairs.  The privilege boundary
# (privilege_level=non_owner) fires first (42501).  The schema boundary
# (schema_existence=schema_not_exists) fires only for schema-qualified names.
# The not-exist boundary (conversion_not_exist=conversion_not_exists /
# conversion_name_shape=nonexistent_name) fires only when if_exists_clause=omitted.
_PRIVILEGE_NEGATIVE = ("privilege_level", "non_owner")
_SCHEMA_NEGATIVE = ("schema_existence", "schema_not_exists")
_NAME_NONEXISTENT = ("conversion_name_shape", "nonexistent_name")
_CONV_NOT_EXIST = ("conversion_not_exist", "conversion_not_exists")
_SCHEMA_QUALIFIED = "schema_qualified"
_IF_EXISTS_OMITTED = "omitted"


def _privilege_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("privilege_level") == "non_owner"


def _schema_failure_fires(assignment: dict[str, str]) -> bool:
    """schema_not_exists fires only for schema-qualified names."""

    return (
        assignment.get("schema_existence") == "schema_not_exists"
        and assignment.get("conversion_name_shape") == _SCHEMA_QUALIFIED
    )


def _not_exist_failure_fires(assignment: dict[str, str]) -> bool:
    """conversion_not_exists / nonexistent_name fire only without IF EXISTS."""

    if assignment.get("if_exists_clause") != _IF_EXISTS_OMITTED:
        return False
    if assignment.get("conversion_name_shape") == "nonexistent_name":
        return True
    if assignment.get("conversion_not_exist") == "conversion_not_exists":
        return True
    return False


def _failure_unit_count(assignment: dict[str, str]) -> int:
    count = 0
    if _privilege_failure_fires(assignment):
        count += 1
    if _schema_failure_fires(assignment):
        count += 1
    if _not_exist_failure_fires(assignment):
        count += 1
    return count


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success.

    The privilege boundary (42501) fires before the object lookup, so it is
    attributed first.  The schema boundary (42704) fires next for
    schema-qualified names when the schema is absent.  The not-exist boundary
    (42704) fires last when IF EXISTS is omitted and the conversion is absent.
    """

    if _privilege_failure_fires(assignment):
        return _PRIVILEGE_NEGATIVE
    if _schema_failure_fires(assignment):
        return _SCHEMA_NEGATIVE
    if assignment.get("if_exists_clause") == _IF_EXISTS_OMITTED:
        if assignment.get("conversion_name_shape") == "nonexistent_name":
            return _NAME_NONEXISTENT
        if assignment.get("conversion_not_exist") == "conversion_not_exists":
            return _CONV_NOT_EXIST
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
    cases: tuple[DropConversionFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"drop-conversion-factor-extension-v1\n")
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
    cases: tuple[DropConversionFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"DROP CONVERSION extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "drop_conversion_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "DROP CONVERSION",
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


def build_drop_conversion_factor_extension_plan(
    repository_root: Path,
) -> DropConversionFactorExtensionPlan:
    """Build the bounded DROP CONVERSION post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_drop_conversion_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[DropConversionFactorExtensionCase] = []
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
                    DropConversionFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"DROPCONVERSION{ordinal:05d}",
                        sql_filename=f"DROPCONVERSION{ordinal:05d}.sql",
                        object_prefix=f"dropconversion_{ordinal:05d}_",
                        derivation_id=(
                            f"DROPCONVERSION-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "drop_conversion_required_baseline_factor_space"
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
    return DropConversionFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "DropConversionFactorExtensionError",
    "DropConversionFactorExtensionCase",
    "DropConversionFactorExtensionPlan",
    "build_drop_conversion_factor_extension_plan",
    "_present_failure_pair",
    "_failure_unit_count",
]
