"""Bounded post-coverage extension plan for SECURITY LABEL.

After the 86-case canonical baseline passes, a bounded set of cross-factor
combinations is derived from the positive T1-T4 axes (``for_provider_clause``
x ``label_value`` x ``label_string_shape`` x ``object_existence``) crossed
with every declared ``verification_mode`` and ``cleanup_mode`` value.  At
most one failure-causing value is permitted per case so each failure remains
attributable.  The total (baseline + extension) is bounded by ``_CAP``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

from .security_label_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_security_label_factor_loop_plan,
)


class SecurityLabelFactorExtensionError(ValueError):
    """Raised when the SECURITY LABEL extension plan cannot be built."""


@dataclass(frozen=True)
class SecurityLabelFactorExtensionCase:
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
class SecurityLabelFactorExtensionPlan:
    cases: tuple[SecurityLabelFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 86
_CAP = 20000

_VERIFICATION_MODES = ("pg_seclabel_catalog_query", "error_assertion")
_CLEANUP_MODES = ("security_label_is_null", "drop_object")

_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "for_provider_clause": (
        "omitted_default_provider",
        "explicit_provider",
    ),
    "label_value": ("string_literal", "null_removes_label"),
    "label_string_shape": (
        "valid_label",
        "empty_string",
        "special_characters_label",
    ),
    "object_existence": ("object_exists", "object_not_exists"),
}

_CROSSED_NEGATIVES = frozenset(
    {
        ("object_existence", "object_not_exists"),
    }
)

_BASELINE: dict[str, str] = {
    "object_type": "table",
    "statement_branch": "branch_on_table",
    "expected_status": "success",
    "object_existence": "object_exists",
    "for_provider_clause": "omitted_default_provider",
    "label_value": "string_literal",
    "aggregate_signature": "star_wildcard",
    "routine_signature": "no_args",
    "object_name_shape": "simple_name",
    "provider_name_shape": "registered_provider",
    "column_name_shape": "simple_name",
    "label_string_shape": "valid_label",
    "executor_privilege": "superuser",
    "provider_registration": "provider_registered",
    "prerequisite_object": "object_exists",
    "nonexistent_object": "target_object_exists",
    "privilege_insufficient": "sufficient_privilege",
    "unregistered_provider": "provider_registered",
    "invalid_label_for_provider": "provider_accepts_label",
    "duplicate_label_same_provider": "replaces_existing_label",
    "verification_mode": "pg_seclabel_catalog_query",
    "cleanup_mode": "security_label_is_null",
}


def _failure_unit_count(assignment: dict[str, str]) -> int:
    return sum(
        1
        for pair in _CROSSED_NEGATIVES
        if assignment.get(pair[0]) == pair[1]
    )


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    for factor, value in _CROSSED_NEGATIVES:
        if assignment.get(factor) == value:
            return (factor, value)
    return None


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    return _failure_unit_count(assignment) <= 1


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    if a.get("object_existence") == "object_not_exists":
        a["object_existence"] = "object_not_exists"
        a["nonexistent_object"] = "target_object_does_not_exist"
        a["prerequisite_object"] = "object_not_exists"
        a["object_name_shape"] = "non_existing_name"
    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _behavior_combinations() -> list[dict[str, str]]:
    keys = list(_GENERAL_AXES.keys())
    combos: list[dict[str, str]] = []
    for values in itertools.product(*(_GENERAL_AXES[k] for k in keys)):
        assignment = dict(_BASELINE)
        for k, v in zip(keys, values):
            assignment[k] = v
        _derive_overlapping_factors(assignment)
        if not _is_valid_combination(assignment):
            continue
        combos.append(assignment)
    combos.sort(key=lambda a: tuple(sorted(a.items())))
    return combos


def _outcome_for(
    assignment: dict[str, str],
) -> tuple[str, str, str | None]:
    pair = _present_failure_pair(assignment)
    if pair is None:
        return ("success", "00000", None)
    sqlstate, reason = _SFV_FAILURE_SQLSTATE[pair]
    return ("expected_failure", sqlstate, reason)


def _extension_multiset_sha256(
    cases: tuple[SecurityLabelFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"security-label-factor-extension-v1\n"
    )
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
    cases: tuple[SecurityLabelFactorExtensionCase, ...],
) -> str:
    import yaml

    records = [
        {
            "id": case.derivation_id,
            "derived_from_combination_group": (
                case.derived_from_combination_group
            ),
            "derivation_reason": case.derivation_reason,
            "factor_assignment": [
                {"factor": k, "value": v}
                for k, v in case.factor_assignment
            ],
            "expected_status_policy": case.outcome,
        }
        for case in cases
    ]
    return yaml.safe_dump(
        {"derived_extension_combinations": records},
        sort_keys=True,
        allow_unicode=True,
    )


def build_security_label_factor_extension_plan(
    repository_root: Path,
) -> SecurityLabelFactorExtensionPlan:
    """Build the bounded SECURITY LABEL post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_security_label_factor_loop_plan(root)  # sanity-check baseline
    behaviors = _behavior_combinations()
    cases: list[SecurityLabelFactorExtensionCase] = []
    ordinal = _BASELINE_COUNT
    raw = 0
    for behavior in behaviors:
        for verification in _VERIFICATION_MODES:
            for cleanup in _CLEANUP_MODES:
                raw += 1
                if len(cases) >= _CAP:
                    continue
                assignment = dict(behavior)
                assignment["verification_mode"] = verification
                assignment["cleanup_mode"] = cleanup
                _derive_overlapping_factors(assignment)
                outcome, sqlstate, reason = _outcome_for(assignment)
                ordinal += 1
                cases.append(
                    SecurityLabelFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"SECURITYLABEL{ordinal:05d}",
                        sql_filename=f"SECURITYLABEL{ordinal:05d}.sql",
                        object_prefix=f"securitylabel_{ordinal:05d}_",
                        derivation_id=(
                            f"SECURITYLABEL-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "security_label_required_factor_value_matrix"
                        ),
                        derivation_reason=(
                            "cross-factor extension: "
                            f"for_provider_clause="
                            f"{assignment['for_provider_clause']} "
                            f"x label_value={assignment['label_value']} "
                            f"x label_string_shape="
                            f"{assignment['label_string_shape']} "
                            f"x object_existence="
                            f"{assignment['object_existence']} "
                            f"x verification_mode={verification} "
                            f"x cleanup_mode={cleanup}"
                        ),
                        factor_assignment=tuple(
                            sorted(assignment.items())
                        ),
                        consumer_action_id=assignment.get(
                            "object_type", "table"
                        ),
                        outcome=outcome,
                        expected_sqlstate=sqlstate,
                        expected_failure_reason=reason,
                        is_extension=True,
                    )
                )
    dropped = max(0, raw - _CAP)
    cases_tuple = tuple(cases)
    return SecurityLabelFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(
            cases_tuple
        ),
        derived_combinations_yaml=_derived_combinations_yaml(
            cases_tuple
        ),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "SecurityLabelFactorExtensionError",
    "SecurityLabelFactorExtensionCase",
    "SecurityLabelFactorExtensionPlan",
    "_BASELINE_COUNT",
    "_CAP",
    "_VERIFICATION_MODES",
    "_CLEANUP_MODES",
    "build_security_label_factor_extension_plan",
]
