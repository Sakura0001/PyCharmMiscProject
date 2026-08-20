"""Bounded post-coverage cross-factor extension expander for ALTER SYSTEM.

The marginal factor-value-loop (:mod:`alter_system_factor_loop`) is the
required baseline: one program per factor value, 55 local cases
(GRM 4 + SFV 49 + RISK 2).  This module adds the bounded post-coverage
extension phase allowed by ``alter_system.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive T1-T4 behaviour axes for BOTH statement
groups (SET and RESET), with at most one failure-causing value per case so
attribution stays clean, and ``verification_mode`` crossed with
``cleanup_mode`` so every declared T6 value is exercised.

ALTER SYSTEM's SET group carries a value (``SET param = value``) while the
RESET group carries none (``RESET param`` / ``RESET ALL``).  The crossed
axes therefore differ per group: the SET group crosses ``value_shape`` and
derives ``set_value_behavior`` from it; the RESET group crosses
``reset_behavior`` instead.  ``parameter_validity`` (T4) is DERIVED from
the T3 values (``parameter_name_shape`` and ``value_shape``), mirroring
the alter_schema pattern where the T5 boundary factor is derived from the
crossed T3/T4 axes: this keeps the at-most-one attribution clean and avoids
the 3/4 failure density that crossing ``parameter_validity`` directly
would introduce.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``derived_extension_required_fields``) and is marked ``is_extension``.
Filtering happens BEFORE counting (``raw += 1``), so
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

from .alter_system_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_alter_system_factor_loop_plan,
)


class AlterSystemFactorExtensionError(ValueError):
    """Raised when a frozen ALTER SYSTEM extension input drifts."""


@dataclass(frozen=True)
class AlterSystemFactorExtensionCase:
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
class AlterSystemFactorExtensionPlan:
    cases: tuple[AlterSystemFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 55
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_settings_query",
    "pg_file_settings_query",
    "show_command",
    "error_assertion",
)
_CLEANUP_MODES = (
    "alter_system_reset_parameter",
    "alter_system_reset_all",
)

# Dense positive baselines per group.  The T5 single-value-negative factors
# (privilege_insufficient, nonexistent_parameter, invalid_parameter_value,
# superuser_only_parameter_by_non_superuser) are NOT baselined here;
# :func:`_derive_t5_factors` adds them at their declared values.
_SET_BASELINE: dict[str, str] = {
    "statement_branch": "branch_set",
    "grammar_branch": "branch_set",
    "target_action": "set",
    "expected_status": "success",
    "configuration_parameter_type": "user_settable_parameter",
    "set_value_behavior": "single_value",
    "reset_behavior": "reset_specific_parameter",
    "parameter_effect_scope": "immediate_effect",
    "parameter_name_shape": "valid_parameter_name",
    "value_shape": "valid_string_value",
    "executor_privilege": "superuser",
    "parameter_validity": "valid_parameter_and_value",
    "restart_required_parameter": "parameter_change_requires_restart",
    "reset_nonexistent_parameter_entry": (
        "reset_parameter_not_in_auto_conf_no_op"
    ),
    "verification_mode": "pg_settings_query",
    "cleanup_mode": "alter_system_reset_parameter",
}

_RESET_BASELINE: dict[str, str] = {
    "statement_branch": "branch_reset",
    "grammar_branch": "branch_reset",
    "target_action": "reset",
    "expected_status": "success",
    "configuration_parameter_type": "user_settable_parameter",
    "set_value_behavior": "single_value",
    "reset_behavior": "reset_specific_parameter",
    "parameter_effect_scope": "immediate_effect",
    "parameter_name_shape": "valid_parameter_name",
    "value_shape": "valid_string_value",
    "executor_privilege": "superuser",
    "parameter_validity": "valid_parameter_and_value",
    "restart_required_parameter": "parameter_change_requires_restart",
    "reset_nonexistent_parameter_entry": (
        "reset_parameter_not_in_auto_conf_no_op"
    ),
    "verification_mode": "pg_settings_query",
    "cleanup_mode": "alter_system_reset_parameter",
}

# Crossed axes per group (T2 + T3 + T4).  Each axis includes both positive
# and negative (failure-causing) values; the at-most-one-failure rule
# ensures clean attribution.  parameter_validity (T4) is DERIVED, not
# crossed, to avoid its 3/4 failure density inflating the failure count.
_SET_AXES: dict[str, tuple[str, ...]] = {
    "configuration_parameter_type": (
        "superuser_only_parameter",
        "user_settable_parameter",
        "postmaster_restart_required",
        "sighup_reload_required",
        "backend_session_parameter",
    ),
    "parameter_effect_scope": (
        "immediate_effect",
        "requires_reload",
        "requires_restart",
    ),
    "parameter_name_shape": (
        "valid_parameter_name",
        "custom_parameter_name_with_dot",
        "quoted_parameter_name",
        "nonexistent_parameter_name",
    ),
    "value_shape": (
        "valid_string_value",
        "valid_integer_value",
        "valid_boolean_value",
        "multiple_comma_separated_values",
        "default_keyword",
        "invalid_value_type",
    ),
    "executor_privilege": ("superuser", "non_superuser"),
}

# RESET has no value_shape (RESET takes no value).
_RESET_AXES: dict[str, tuple[str, ...]] = {
    "configuration_parameter_type": (
        "superuser_only_parameter",
        "user_settable_parameter",
        "postmaster_restart_required",
        "sighup_reload_required",
        "backend_session_parameter",
    ),
    "parameter_effect_scope": (
        "immediate_effect",
        "requires_reload",
        "requires_restart",
    ),
    "parameter_name_shape": (
        "valid_parameter_name",
        "custom_parameter_name_with_dot",
        "quoted_parameter_name",
        "nonexistent_parameter_name",
    ),
    "executor_privilege": ("superuser", "non_superuser"),
    "reset_behavior": (
        "reset_specific_parameter",
        "reset_all_parameters",
    ),
}

# Crossed behaviour-negative (factor, value) pairs across both groups.
_CROSSED_NEGATIVES = frozenset(
    {
        ("parameter_name_shape", "nonexistent_parameter_name"),
        ("value_shape", "invalid_value_type"),
        ("executor_privilege", "non_superuser"),
    }
)

_GROUP_CONFIG = (
    ("set", _SET_AXES, _SET_BASELINE),
    ("reset", _RESET_AXES, _RESET_BASELINE),
)

# value_shape -> set_value_behavior (SET group derivation).
_VALUE_SHAPE_TO_SET_BEHAVIOR = {
    "valid_string_value": "single_value",
    "valid_integer_value": "single_value",
    "valid_boolean_value": "single_value",
    "multiple_comma_separated_values": "multiple_values",
    "default_keyword": "set_to_default",
    "invalid_value_type": "single_value",
}

# parameter_effect_scope -> restart_required_parameter derivation.
_EFFECT_SCOPE_TO_RESTART = {
    "requires_restart": "parameter_change_requires_restart",
    "requires_reload": "parameter_change_requires_reload",
    "immediate_effect": "parameter_change_requires_restart",
}

# reset_behavior -> statement_branch (RESET group derivation).
_RESET_BEHAVIOR_TO_BRANCH = {
    "reset_specific_parameter": "branch_reset",
    "reset_all_parameters": "branch_reset_all",
}


def _failure_unit_count(assignment: dict[str, str]) -> int:
    return sum(
        1
        for factor, value in _CROSSED_NEGATIVES
        if assignment.get(factor) == value
    )


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    for neg_factor, neg_value in _CROSSED_NEGATIVES:
        if assignment.get(neg_factor) == neg_value:
            return (neg_factor, neg_value)
    return None


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    """Applicability + consistency + at-most-one-failure attribution."""

    branch = assignment.get("target_action")
    if branch not in ("set", "reset"):
        return False
    return _failure_unit_count(assignment) <= 1


def _derive_parameter_validity(a: dict[str, str]) -> None:
    """Derive parameter_validity (T4) from T3 values.

    parameter_name_shape=nonexistent -> parameter_validity=nonexistent.
    value_shape=invalid_value_type -> parameter_validity=valid_invalid_value.
    Otherwise -> parameter_validity=valid_parameter_and_value.
    """

    if a.get("parameter_name_shape") == "nonexistent_parameter_name":
        a["parameter_validity"] = "nonexistent_parameter"
    elif a.get("value_shape") == "invalid_value_type":
        a["parameter_validity"] = "valid_parameter_invalid_value"
    else:
        a["parameter_validity"] = "valid_parameter_and_value"


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T3/T4 values.

    The T5 single-value-negative factors carry only their declared (negative)
    value, so they are set to that declared value and fire only when the
    corresponding T3/T4 is also negative.  The extension's failure count uses
    T3/T4 crossed negatives only (:func:`_failure_unit_count`), so the
    always-on T5 values do not inflate the count.
    """

    a["privilege_insufficient"] = "non_superuser_using_alter_system"
    a["nonexistent_parameter"] = "parameter_does_not_exist"
    a["invalid_parameter_value"] = "wrong_type_value"
    a["superuser_only_parameter_by_non_superuser"] = (
        "cannot_set_superuser_only_parameter"
    )
    a["reset_nonexistent_parameter_entry"] = (
        "reset_parameter_not_in_auto_conf_no_op"
    )

    # set_value behavior derived from value_shape (SET group only).
    vs = a.get("value_shape", "valid_string_value")
    a["set_value_behavior"] = _VALUE_SHAPE_TO_SET_BEHAVIOR.get(
        vs, "single_value"
    )
    if a.get("target_action") == "set":
        if a["set_value_behavior"] == "set_to_default":
            a["statement_branch"] = "branch_set_default"
            a["grammar_branch"] = "branch_set_default"
        else:
            a["statement_branch"] = "branch_set"
            a["grammar_branch"] = "branch_set"

    # restart_required_parameter derived from parameter_effect_scope.
    es = a.get("parameter_effect_scope", "immediate_effect")
    a["restart_required_parameter"] = _EFFECT_SCOPE_TO_RESTART.get(
        es, "parameter_change_requires_restart"
    )

    # statement_branch derived from reset_behavior (RESET group only).
    if a.get("target_action") == "reset":
        rb = a.get("reset_behavior", "reset_specific_parameter")
        a["statement_branch"] = _RESET_BEHAVIOR_TO_BRANCH.get(
            rb, "branch_reset"
        )
        a["grammar_branch"] = a["statement_branch"]

    _derive_parameter_validity(a)

    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments (T6 at baseline) passing the filter."""

    combos: list[dict[str, str]] = []
    for _group, axes, baseline in _GROUP_CONFIG:
        names = list(axes)
        for values in itertools.product(*[axes[n] for n in names]):
            assignment: dict[str, str] = dict(baseline)
            for name, value in zip(names, values):
                assignment[name] = value
            _derive_t5_factors(assignment)
            if not _is_valid_combination(assignment):
                continue
            if len(assignment) != len(set(assignment)):
                raise AlterSystemFactorExtensionError(
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
    cases: tuple[AlterSystemFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"alter-system-factor-extension-v1\n")
    for case in cases:
        digest.update(
            json.dumps(
                {
                    "derivation_id": case.derivation_id,
                    "factor_assignment": list(case.factor_assignment),
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
    cases: tuple[AlterSystemFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"ALTER SYSTEM extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "alter_system_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "ALTER SYSTEM",
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


def build_alter_system_factor_extension_plan(
    repository_root: Path,
) -> AlterSystemFactorExtensionPlan:
    """Build the bounded ALTER SYSTEM post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_alter_system_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[AlterSystemFactorExtensionCase] = []
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
                cases.append(
                    AlterSystemFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"ALTERSYSTEM{ordinal:05d}",
                        sql_filename=f"ALTERSYSTEM{ordinal:05d}.sql",
                        object_prefix=f"alter_system_{ordinal:05d}_",
                        derivation_id=(
                            f"ASYS-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "alter_system_required_factor_value_matrix"
                        ),
                        derivation_reason=(
                            f"cross-factor extension: "
                            f"target_action="
                            f"{assignment['target_action']} "
                            f"x parameter_name_shape="
                            f"{assignment['parameter_name_shape']} "
                            f"x executor_privilege="
                            f"{assignment['executor_privilege']} "
                            f"x verification_mode={verification} "
                            f"x cleanup_mode={cleanup}"
                        ),
                        factor_assignment=tuple(
                            sorted(assignment.items())
                        ),
                        consumer_action_id=assignment["target_action"],
                        outcome=outcome,
                        expected_sqlstate=sqlstate,
                        expected_failure_reason=reason,
                        is_extension=True,
                    )
                )
    dropped = max(0, raw - _CAP)
    cases_tuple = tuple(cases)
    return AlterSystemFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "AlterSystemFactorExtensionError",
    "AlterSystemFactorExtensionCase",
    "AlterSystemFactorExtensionPlan",
    "build_alter_system_factor_extension_plan",
]
