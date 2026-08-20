"""Bounded post-coverage cross-factor extension expander for CREATE EXTENSION.

The marginal factor-value-loop (:mod:`create_extension_factor_loop`)
is the required baseline: one program per factor value, 63 local cases
(GRM 1 + SFV 62).  This module adds the bounded post-coverage
extension phase allowed by ``create_extension.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive T1-T4 behaviour axes across the two
statement branches (``branch_create_extension`` and
``branch_create_extension_if_not_exists``), with at most one
failure-causing value per case so attribution stays clean, and
``verification_mode`` / ``cleanup_mode`` crossed so every declared T6
value is exercised.

CREATE EXTENSION requires superuser privilege for untrusted extensions;
trusted extensions can be installed by users with CREATE privilege.  The
T5 single-value factors (duplicate_extension_name,
nonexistent_extension_script, nonexistent_schema,
control_file_schema_conflict, insufficient_privilege, invalid_version,
if_not_exists_no_op) overlap with their T1-T4 counterparts.  Overlapping
T5 values are derived in :func:`_derive_t5_factors`, not crossed, so
counting both would double-count a single failure and break
at-most-one attribution.

The extension phase never replaces a required-baseline obligation.
Each extension case carries a derivation record (per yaml
``post_coverage_extension_policy.required_fields``) and is marked
``is_extension``.  Filtering happens BEFORE counting (``raw += 1``),
so ``raw_combination_count == len(cases)`` and ``dropped_count == 0``
(no over-pruning).
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .create_extension_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_create_extension_factor_loop_plan,
)


class CreateExtensionFactorExtensionError(ValueError):
    """Raised when a frozen CREATE EXTENSION extension input drifts."""


@dataclass(frozen=True)
class CreateExtensionFactorExtensionCase:
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
class CreateExtensionFactorExtensionPlan:
    cases: tuple[CreateExtensionFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 63
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_available_extensions_query",
    "pg_extension_catalog_query",
    "error_assertion",
)
_CLEANUP_MODES = (
    "drop_extension",
    "drop_extension_cascade",
    "schema_cleanup",
)

# General axes crossed for both branches.
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "object_state": (
        "not_exists",
        "already_exists",
    ),
    "schema_clause": (
        "omitted",
        "specified_schema",
        "control_file_schema_conflict",
    ),
    "version_clause": (
        "omitted",
        "specified_version",
        "invalid_version",
    ),
    "cascade_clause": (
        "omitted",
        "specified",
    ),
    "extension_trust_level": (
        "trusted",
        "untrusted",
    ),
    "extension_name_shape": (
        "simple_id",
        "quoted_id",
        "reserved_word_name",
        "nonexistent_extension",
        "duplicate_name",
    ),
    "privilege_level": (
        "superuser",
        "create_privilege_user",
        "non_superuser_no_create",
    ),
    "control_file_presence": (
        "installed_on_system",
        "not_installed_on_system",
    ),
}

# Branch -> (statement_branch, target_action, branch-specific axes).
_BRANCH_CONFIG: tuple[
    tuple[str, str, dict[str, tuple[str, ...]]], ...
] = (
    (
        "branch_create_extension",
        "create_extension",
        _GENERAL_AXES,
    ),
    (
        "branch_create_extension_if_not_exists",
        "create_extension",
        _GENERAL_AXES,
    ),
)

# Dense positive baseline (all success values).
_BASELINE: dict[str, str] = {
    "statement_branch": "branch_create_extension",
    "grammar_branch": "branch_create_extension",
    "target_action": "create_extension",
    "object_state": "not_exists",
    "expected_status": "success",
    "if_not_exists_clause": "omitted",
    "schema_clause": "omitted",
    "version_clause": "omitted",
    "cascade_clause": "omitted",
    "extension_trust_level": "trusted",
    "extension_name_shape": "simple_id",
    "schema_name_shape": "simple_id",
    "version_string_shape": "identifier_form",
    "privilege_level": "superuser",
    "schema_existence": "schema_exists",
    "dependency_extension_state": "already_installed",
    "control_file_presence": "installed_on_system",
    "verification_mode": "pg_extension_catalog_query",
    "cleanup_mode": "drop_extension",
}

# Crossed behaviour-negative (factor, value) pairs -- one representative
# per failure scenario.  Overlapping T5 values are NOT listed here
# (they are derived in :func:`_derive_t5_factors`) so counting both
# would double-count a single failure and break at-most-one
# attribution.
_CROSSED_NEGATIVES = frozenset(
    {
        ("object_state", "already_exists"),
        ("schema_clause", "control_file_schema_conflict"),
        ("version_clause", "invalid_version"),
        ("extension_name_shape", "nonexistent_extension"),
        ("extension_name_shape", "duplicate_name"),
        ("privilege_level", "non_superuser_no_create"),
        ("control_file_presence", "not_installed_on_system"),
    }
)


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

    os_ = assignment.get("object_state", "not_exists")
    ens = assignment.get("extension_name_shape", "simple_id")
    cfp = assignment.get(
        "control_file_presence", "installed_on_system"
    )

    # Rule 1: object_state / extension_name_shape consistency.
    if os_ == "already_exists" and ens != "duplicate_name":
        return False
    if os_ == "not_exists" and ens == "duplicate_name":
        return False

    # Rule 2: extension_name_shape / control_file_presence consistency.
    if ens == "nonexistent_extension" and cfp != "not_installed_on_system":
        return False
    if (
        ens != "nonexistent_extension"
        and cfp == "not_installed_on_system"
    ):
        return False

    # Rule 3: at-most-one-failure attribution.
    return _failure_unit_count(assignment) <= 1


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive overlapping T5 factors and expected_status from T1-T4 values."""

    os_ = a.get("object_state", "not_exists")
    ens = a.get("extension_name_shape", "simple_id")
    cfp = a.get("control_file_presence", "installed_on_system")
    sc = a.get("schema_clause", "omitted")
    cas = a.get("cascade_clause", "omitted")
    pl = a.get("privilege_level", "superuser")
    etl = a.get("extension_trust_level", "trusted")
    vc = a.get("version_clause", "omitted")
    ine = a.get("if_not_exists_clause", "omitted")

    # 1. object_state / duplicate_extension_name
    if os_ == "already_exists" or ens == "duplicate_name":
        a["object_state"] = "already_exists"
        a["duplicate_extension_name"] = "same_name_conflict"
    else:
        a["duplicate_extension_name"] = "no_conflict"

    # 2. control_file_presence / nonexistent_extension_script
    if cfp == "not_installed_on_system" or ens == "nonexistent_extension":
        a["control_file_presence"] = "not_installed_on_system"
        a["nonexistent_extension_script"] = "script_missing"
    else:
        a["nonexistent_extension_script"] = "script_exists"

    # 3. schema_existence / nonexistent_schema
    a["schema_existence"] = "schema_exists"
    a["nonexistent_schema"] = "schema_exists"

    # 4. schema_clause / control_file_schema_conflict
    if sc == "control_file_schema_conflict":
        if cas == "specified":
            a["control_file_schema_conflict"] = (
                "conflict_with_cascade_ignored"
            )
        else:
            a["control_file_schema_conflict"] = (
                "conflict_without_cascade"
            )
    else:
        a["control_file_schema_conflict"] = "no_conflict"

    # 5. privilege_level / insufficient_privilege
    if pl == "non_superuser_no_create":
        a["insufficient_privilege"] = "no_create_privilege_trusted"
    elif etl == "untrusted" and pl != "superuser":
        a["insufficient_privilege"] = (
            "non_superuser_untrusted_extension"
        )
    else:
        a["insufficient_privilege"] = "sufficient_privilege"

    # 6. version_clause / invalid_version
    if vc == "invalid_version":
        a["invalid_version"] = "nonexistent_version"
        a["version_string_shape"] = "invalid_version_string"
    else:
        a["invalid_version"] = "valid_version"

    # 7. if_not_exists_no_op
    if ine == "specified" and a.get("object_state") == "already_exists":
        a["if_not_exists_no_op"] = "no_op_notice"
    else:
        a["if_not_exists_no_op"] = "new_install"

    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments (T6 at baseline) passing the filter."""

    combos: list[dict[str, str]] = []
    for branch, action, axes in _BRANCH_CONFIG:
        names = list(axes)
        for values in itertools.product(
            *[axes[n] for n in names]
        ):
            assignment: dict[str, str] = dict(_BASELINE)
            assignment["statement_branch"] = branch
            assignment["grammar_branch"] = branch
            assignment["target_action"] = action
            for name, value in zip(names, values):
                assignment[name] = value
            _derive_t5_factors(assignment)
            if not _is_valid_combination(assignment):
                continue
            if len(assignment) != len(set(assignment)):
                raise CreateExtensionFactorExtensionError(
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
    cases: tuple[CreateExtensionFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-extension-factor-extension-v1\n"
    )
    for case in cases:
        digest.update(
            json.dumps(
                {
                    "derivation_id": case.derivation_id,
                    "factor_assignment": list(
                        case.factor_assignment
                    ),
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
    cases: tuple[CreateExtensionFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"CREATE EXTENSION extension "
                    f"{case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": (
                        "create_extension_factor_extension"
                    ),
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "CREATE EXTENSION",
                    "primary_fence": (
                        "primary-target-begin/end"
                    ),
                    "consumer_action_id": case.consumer_action_id,
                },
                "verification": {
                    "verification_mode": assignment[
                        "verification_mode"
                    ],
                    "expected_sqlstate": case.expected_sqlstate,
                },
                "cleanup": {
                    "cleanup_mode": assignment["cleanup_mode"],
                },
            }
        )
    return yaml.safe_dump(
        entries, sort_keys=False, allow_unicode=True
    )


def build_create_extension_factor_extension_plan(
    repository_root: Path,
) -> CreateExtensionFactorExtensionPlan:
    """Build the bounded CREATE EXTENSION post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_create_extension_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[CreateExtensionFactorExtensionCase] = []
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
                outcome, sqlstate, reason = _outcome_for(
                    assignment
                )
                ordinal += 1
                cases.append(
                    CreateExtensionFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=(
                            f"CREATEEXTENSION{ordinal:05d}"
                        ),
                        sql_filename=(
                            f"CREATEEXTENSION{ordinal:05d}.sql"
                        ),
                        object_prefix=(
                            f"createextension_{ordinal:05d}_"
                        ),
                        derivation_id=(
                            f"CE-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "create_extension_declared_"
                            "factor_baseline"
                        ),
                        derivation_reason=(
                            "cross-factor extension: "
                            f"target_action="
                            f"{assignment['target_action']} "
                            f"object_state="
                            f"{assignment['object_state']} "
                            f"schema_clause="
                            f"{assignment['schema_clause']} "
                            f"version_clause="
                            f"{assignment['version_clause']} "
                            f"cascade_clause="
                            f"{assignment['cascade_clause']} "
                            f"extension_trust_level="
                            f"{assignment['extension_trust_level']} "
                            f"extension_name_shape="
                            f"{assignment['extension_name_shape']} "
                            f"privilege_level="
                            f"{assignment['privilege_level']} "
                            f"control_file_presence="
                            f"{assignment['control_file_presence']} "
                            f"verification_mode="
                            f"{verification} "
                            f"cleanup_mode={cleanup}"
                        ),
                        factor_assignment=tuple(
                            sorted(assignment.items())
                        ),
                        consumer_action_id=assignment[
                            "target_action"
                        ],
                        outcome=outcome,
                        expected_sqlstate=sqlstate,
                        expected_failure_reason=reason,
                        is_extension=True,
                    )
                )
    dropped = max(0, raw - _CAP)
    cases_tuple = tuple(cases)
    return CreateExtensionFactorExtensionPlan(
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
    "CreateExtensionFactorExtensionError",
    "CreateExtensionFactorExtensionCase",
    "CreateExtensionFactorExtensionPlan",
    "build_create_extension_factor_extension_plan",
]
