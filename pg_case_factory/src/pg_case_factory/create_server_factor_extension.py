"""Bounded post-coverage cross-factor extension expander for CREATE SERVER.

The marginal factor-value-loop
(:mod:`create_server_factor_loop`) is the required baseline: one
program per factor value, 43 local cases (GRM 2 + SFV 41).  This
module adds the bounded post-coverage extension phase allowed by
``create_server.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive T1-T4 behaviour axes across the two
grammar branches (``branch_create_server`` /
``branch_create_server_if_not_exists``), with at most one
failure-causing value per case so attribution stays clean, and
``verification_mode`` / ``cleanup_mode`` crossed so every declared T6
value is exercised.

CREATE SERVER requires superuser privilege, so
``executor_privilege=non_superuser`` is an unconditional failure
(SQLSTATE 42501).  ``fdw_dependency=nonexistent_fdw`` is an
unconditional failure (SQLSTATE 42704).  The duplicate-name failures
(``server_identity=exists`` / ``quoted_duplicate``) are conditional:
they are failures only when ``IF NOT EXISTS`` is absent (the
``without_if_not_exists`` branch).  With ``IF NOT EXISTS`` the same
``server_identity`` values produce a no-op (notice), so the outcome
is success.

The T5 single-value factors (duplicate_server_name,
privilege_insufficient, nonexistent_fdw, fdw_validator_rejection)
overlap with their T1-T4 counterparts.  Overlapping T5 values are
derived in :func:`_derive_t5_factors`, not crossed, so counting both
would double-count a single failure and break at-most-one attribution.

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

from .create_server_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_create_server_factor_loop_plan,
)


class CreateServerFactorExtensionError(ValueError):
    """Raised when a frozen CREATE SERVER extension input drifts."""


@dataclass(frozen=True)
class CreateServerFactorExtensionCase:
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
class CreateServerFactorExtensionPlan:
    cases: tuple[CreateServerFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 43
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_foreign_server_catalog",
    "error_assertion",
)
_CLEANUP_MODES = (
    "drop_server",
    "drop_fdw_then_drop_server",
)

# Failure pairs that are ALWAYS failures regardless of other factors.
_ALWAYS_FAILURES = frozenset(
    {
        ("fdw_dependency", "nonexistent_fdw"),
        ("executor_privilege", "non_superuser"),
    }
)

# Duplicate-name failures are conditional: they are failures only when
# IF NOT EXISTS is absent (without_if_not_exists branch).
_DUPLICATE_FAILURES = frozenset(
    {
        ("server_identity", "exists"),
        ("server_identity", "quoted_duplicate"),
    }
)

# General axes crossed for the two branches.
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "server_identity": (
        "not_exists",
        "exists",
        "reserved_word_name",
        "quoted_duplicate",
    ),
    "if_not_exists_clause": (
        "without_if_not_exists",
        "with_if_not_exists",
    ),
    "type_version_clause": (
        "omitted",
        "type_only",
        "version_only",
        "both_type_and_version",
    ),
    "options_clause": (
        "omitted",
        "single_option",
        "multiple_options",
    ),
    "fdw_dependency": (
        "existing_fdw",
        "nonexistent_fdw",
    ),
    "server_name_shape": (
        "simple_name",
        "quoted_name",
        "reserved_word_name",
        "non_existing_name",
    ),
    "option_value_shape": (
        "valid_option_value",
        "empty_option_value",
    ),
    "executor_privilege": (
        "superuser",
        "non_superuser",
    ),
}

# Dense positive baseline (all success values).
_BASELINE: dict[str, str] = {
    "statement_branch": "branch_create_server",
    "grammar_branch": "branch_create_server",
    "target_action": "create_server",
    "server_identity": "not_exists",
    "expected_status": "success",
    "if_not_exists_clause": "without_if_not_exists",
    "type_version_clause": "omitted",
    "options_clause": "omitted",
    "fdw_dependency": "existing_fdw",
    "server_name_shape": "simple_name",
    "fdw_name_shape": "existing_fdw_name",
    "option_value_shape": "valid_option_value",
    "executor_privilege": "superuser",
    "fdw_existence": "fdw_exists",
    "duplicate_server_name": "none",
    "privilege_insufficient": "superuser_creating_server",
    "nonexistent_fdw": "fdw_does_exist",
    "fdw_validator_rejection": "none",
    "verification_mode": "pg_foreign_server_catalog",
    "cleanup_mode": "drop_server",
}


def _failure_unit_count(assignment: dict[str, str]) -> int:
    """Count failure-causing values with conditional duplicate logic."""

    count = sum(
        1
        for factor, value in _ALWAYS_FAILURES
        if assignment.get(factor) == value
    )
    ifne = assignment.get(
        "if_not_exists_clause", "without_if_not_exists"
    )
    if ifne == "without_if_not_exists":
        count += sum(
            1
            for factor, value in _DUPLICATE_FAILURES
            if assignment.get(factor) == value
        )
    return count


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single failure pair, or None for success."""

    for neg_factor, neg_value in _ALWAYS_FAILURES:
        if assignment.get(neg_factor) == neg_value:
            return (neg_factor, neg_value)
    ifne = assignment.get(
        "if_not_exists_clause", "without_if_not_exists"
    )
    if ifne == "without_if_not_exists":
        for neg_factor, neg_value in _DUPLICATE_FAILURES:
            if assignment.get(neg_factor) == neg_value:
                return (neg_factor, neg_value)
    return None


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    """Applicability + consistency + at-most-one-failure attribution."""

    si = assignment.get("server_identity", "not_exists")
    sns = assignment.get("server_name_shape", "simple_name")

    # Rule 1: server_identity / server_name_shape consistency.
    if si == "reserved_word_name" and sns != "reserved_word_name":
        return False
    if si == "quoted_duplicate" and sns != "quoted_name":
        return False

    # Rule 2: at-most-one-failure attribution.
    return _failure_unit_count(assignment) <= 1


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive overlapping T5/T4 factors and expected_status."""

    si = a.get("server_identity", "not_exists")
    fd = a.get("fdw_dependency", "existing_fdw")
    ep = a.get("executor_privilege", "superuser")
    ifne = a.get("if_not_exists_clause", "without_if_not_exists")

    # duplicate_server_name cluster
    if si in ("exists", "quoted_duplicate"):
        a["duplicate_server_name"] = "same_name_exists"
    else:
        a["duplicate_server_name"] = "none"

    # nonexistent_fdw / fdw_existence / fdw_name_shape cluster
    if fd == "nonexistent_fdw":
        a["fdw_existence"] = "fdw_not_exists"
        a["fdw_name_shape"] = "nonexistent_fdw_name"
        a["nonexistent_fdw"] = "fdw_does_not_exist"
    else:
        a["fdw_existence"] = "fdw_exists"
        a["fdw_name_shape"] = "existing_fdw_name"
        a["nonexistent_fdw"] = "fdw_does_exist"

    # privilege_insufficient cluster
    if ep == "non_superuser":
        a["privilege_insufficient"] = "non_superuser_creating_server"
    else:
        a["privilege_insufficient"] = "superuser_creating_server"

    # fdw_validator_rejection always none in extension
    a["fdw_validator_rejection"] = "none"

    # statement_branch / grammar_branch / target_action from ifne
    if ifne == "with_if_not_exists":
        a["statement_branch"] = "branch_create_server_if_not_exists"
        a["grammar_branch"] = "branch_create_server_if_not_exists"
        a["target_action"] = "create_server_if_not_exists"
    else:
        a["statement_branch"] = "branch_create_server"
        a["grammar_branch"] = "branch_create_server"
        a["target_action"] = "create_server"

    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments (T6 at baseline) passing the filter."""

    combos: list[dict[str, str]] = []
    names = list(_GENERAL_AXES)
    for values in itertools.product(
        *[list(_GENERAL_AXES[n]) for n in names]
    ):
        assignment: dict[str, str] = dict(_BASELINE)
        for name, value in zip(names, values):
            assignment[name] = value
        _derive_t5_factors(assignment)
        if not _is_valid_combination(assignment):
            continue
        if len(assignment) != len(set(assignment)):
            raise CreateServerFactorExtensionError(
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
    cases: tuple[CreateServerFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-server-factor-extension-v1\n"
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
    cases: tuple[CreateServerFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"CREATE SERVER extension {case.ordinal:05d}: "
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
                        "create_server_factor_extension"
                    ),
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "CREATE SERVER",
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


def build_create_server_factor_extension_plan(
    repository_root: Path,
) -> CreateServerFactorExtensionPlan:
    """Build the bounded CREATE SERVER post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_create_server_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[CreateServerFactorExtensionCase] = []
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
                    CreateServerFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"CREATESERVER{ordinal:05d}",
                        sql_filename=(
                            f"CREATESERVER{ordinal:05d}.sql"
                        ),
                        object_prefix=(
                            f"createserver_{ordinal:05d}_"
                        ),
                        derivation_id=(
                            f"CSRV-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "create_server_declared_"
                            "factor_baseline"
                        ),
                        derivation_reason=(
                            "cross-factor extension: "
                            f"target_action="
                            f"{assignment['target_action']} "
                            f"server_identity="
                            f"{assignment['server_identity']} "
                            f"if_not_exists_clause="
                            f"{assignment['if_not_exists_clause']} "
                            f"type_version_clause="
                            f"{assignment['type_version_clause']} "
                            f"options_clause="
                            f"{assignment['options_clause']} "
                            f"fdw_dependency="
                            f"{assignment['fdw_dependency']} "
                            f"server_name_shape="
                            f"{assignment['server_name_shape']} "
                            f"option_value_shape="
                            f"{assignment['option_value_shape']} "
                            f"executor_privilege="
                            f"{assignment['executor_privilege']} "
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
    return CreateServerFactorExtensionPlan(
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
    "CreateServerFactorExtensionError",
    "CreateServerFactorExtensionCase",
    "CreateServerFactorExtensionPlan",
    "build_create_server_factor_extension_plan",
]
