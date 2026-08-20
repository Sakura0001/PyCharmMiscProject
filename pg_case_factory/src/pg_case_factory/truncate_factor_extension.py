"""Bounded post-coverage cross-factor extension expander for TRUNCATE.

The marginal factor-value-loop (:mod:`truncate_factor_loop`) is the
required baseline: one program per factor value, 53 local cases (GRM 1
+ SFV 52).  This module adds the bounded post-coverage extension phase
allowed by ``truncate.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive T1-T4 behaviour axes across the four
``statement_branch`` grammar branches, with at most one failure-causing
value per case so attribution stays clean, and ``verification`` x
``cleanup`` crossed so every declared T6 value is exercised.

TRUNCATE acts on a ``pg_class`` base-table relation; the
failure-causing values are: ``object_state=table_does_not_exist`` and
``privilege_level=insufficient_privilege``.  The T5 single-value
factors (non_existent_table, insufficient_privilege,
fk_references_without_cascade) are derived from their T1-T4
counterparts, not crossed as axes.

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

from .truncate_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_truncate_factor_loop_plan,
)


class TruncateFactorExtensionError(ValueError):
    """Raised when a frozen TRUNCATE extension input drifts."""


@dataclass(frozen=True)
class TruncateFactorExtensionCase:
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
class TruncateFactorExtensionPlan:
    cases: tuple[TruncateFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 53
_CAP = 20000

_VERIFICATION_MODES = (
    "error_assertion",
    "pg_class_relpages",
    "select_count_zero",
    "sequence_reset_check",
)
_CLEANUP_MODES = (
    "drop_objects",
    "reinsert_data",
    "restart_identity_resets_sequences",
    "rollback",
)

# General axes crossed per branch.  These are the behaviour axes with
# more than one value that are not markers (expected_status), not T5
# (derived), and not T6 (crossed separately).
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "object_state": (
        "empty_table",
        "non_empty_table",
        "table_does_not_exist",
        "table_exists",
    ),
    "cascade_restrict": ("cascade", "none", "restrict"),
    "multi_table": ("multiple", "single"),
    "privilege_level": (
        "insufficient_privilege",
        "owner",
        "superuser",
        "truncate_privilege",
    ),
}

# Dense positive baseline (all success values).  statement_branch /
# target_action are overridden per branch.  cascade_restrict defaults
# to "cascade" so fk_dependency=referenced_by_other_tables (at
# baseline) does not cause an unattributed failure.
_BASELINE: dict[str, str] = {
    "statement_branch": "truncate_table",
    "expected_status": "success",
    "object_state": "table_exists",
    "cascade_restrict": "cascade",
    "identity_option": "none",
    "only_clause": "without_only",
    "multi_table": "single",
    "table_name_shape": "simple",
    "fk_dependency": "no_fk_references",
    "privilege_level": "owner",
    "fk_references_without_cascade": "none",
    "insufficient_privilege": "none",
    "non_existent_table": "none",
    "partitioned_table_behavior": "none",
    "temporary_table_truncation": "none",
    "verification": "select_count_zero",
    "cleanup": "rollback",
}

# Branch -> (statement_branch, target_action, branch-specific axes).
# The four statement_branch values are the grammar branches; each
# carries the same general axes.
_BRANCH_CONFIG: tuple[
    tuple[str, str, dict[str, tuple[str, ...]]], ...
] = (
    ("truncate_table", "truncate", {}),
    ("truncate_table_continue_identity", "truncate", {}),
    ("truncate_table_only", "truncate", {}),
    ("truncate_table_restart_identity", "truncate", {}),
)

# statement_branch -> (only_clause, identity_option) correlation.
_BRANCH_OPTIONS: dict[str, tuple[str, str]] = {
    "truncate_table": ("without_only", "none"),
    "truncate_table_continue_identity": (
        "without_only",
        "continue_identity",
    ),
    "truncate_table_only": ("only", "none"),
    "truncate_table_restart_identity": (
        "without_only",
        "restart_identity",
    ),
}

# Crossed behaviour-negative (factor, value) pairs -- one
# representative per failure scenario.  Overlapping T5 values are NOT
# listed here (they are derived in :func:`_derive_t5_factors`) so
# counting both would double-count a single failure and break
# at-most-one attribution.
_CROSSED_NEGATIVES = frozenset(
    {
        ("object_state", "table_does_not_exist"),
        ("privilege_level", "insufficient_privilege"),
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

    return _failure_unit_count(assignment) <= 1


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values."""

    sb = a.get("statement_branch", "truncate_table")
    if sb in _BRANCH_OPTIONS:
        a["only_clause"], a["identity_option"] = _BRANCH_OPTIONS[sb]

    os_state = a.get("object_state", "table_exists")
    pl = a.get("privilege_level", "owner")
    fk_dep = a.get("fk_dependency", "no_fk_references")
    cr = a.get("cascade_restrict", "cascade")

    if os_state == "table_does_not_exist":
        a["non_existent_table"] = "truncate_non_existent_table"
        a["table_name_shape"] = "non_existent"
    else:
        a["non_existent_table"] = "none"

    if pl == "insufficient_privilege":
        a["insufficient_privilege"] = "no_truncate_privilege"
    else:
        a["insufficient_privilege"] = "none"

    if (
        fk_dep == "referenced_by_other_tables"
        and cr in ("none", "restrict")
    ):
        a["fk_references_without_cascade"] = "has_fk_ref_no_cascade"
    else:
        a["fk_references_without_cascade"] = "none"

    a["partitioned_table_behavior"] = "none"
    a["temporary_table_truncation"] = "none"

    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments (T6 at baseline) passing the filter."""

    combos: list[dict[str, str]] = []
    for branch, action, axes in _BRANCH_CONFIG:
        all_axes = dict(_GENERAL_AXES)
        all_axes.update(axes)
        names = list(all_axes)
        for values in itertools.product(
            *[all_axes[n] for n in names]
        ):
            assignment: dict[str, str] = dict(_BASELINE)
            assignment["statement_branch"] = branch
            assignment["target_action"] = action
            for name, value in zip(names, values):
                assignment[name] = value
            _derive_t5_factors(assignment)
            if not _is_valid_combination(assignment):
                continue
            if len(assignment) != len(set(assignment)):
                raise TruncateFactorExtensionError(
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
    cases: tuple[TruncateFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"truncate-factor-extension-v1\n")
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
    cases: tuple[TruncateFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"TRUNCATE extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "truncate_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "TRUNCATE",
                    "primary_fence": (
                        "primary-target-begin/end"
                    ),
                    "consumer_action_id": case.consumer_action_id,
                },
                "verification": {
                    "verification": assignment["verification"],
                    "expected_sqlstate": case.expected_sqlstate,
                },
                "cleanup": {
                    "cleanup": assignment["cleanup"],
                },
            }
        )
    return yaml.safe_dump(
        entries, sort_keys=False, allow_unicode=True
    )


def build_truncate_factor_extension_plan(
    repository_root: Path,
) -> TruncateFactorExtensionPlan:
    """Build the bounded TRUNCATE post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_truncate_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[TruncateFactorExtensionCase] = []
    ordinal = _BASELINE_COUNT
    raw = 0
    for behavior in behaviors:
        for verification in _VERIFICATION_MODES:
            for cleanup in _CLEANUP_MODES:
                raw += 1
                if len(cases) >= _CAP:
                    continue
                assignment: dict[str, str] = dict(behavior)
                assignment["verification"] = verification
                assignment["cleanup"] = cleanup
                outcome, sqlstate, reason = _outcome_for(
                    assignment
                )
                ordinal += 1
                cases.append(
                    TruncateFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"TRUNCATE{ordinal:05d}",
                        sql_filename=f"TRUNCATE{ordinal:05d}.sql",
                        object_prefix=f"truncate_{ordinal:05d}_",
                        derivation_id=(
                            f"TRUNCATE-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "truncate_required_factor_value_matrix"
                        ),
                        derivation_reason=(
                            "cross-factor extension: "
                            f"statement_branch="
                            f"{assignment['statement_branch']} "
                            f"object_state="
                            f"{assignment['object_state']} "
                            f"cascade_restrict="
                            f"{assignment['cascade_restrict']} "
                            f"multi_table="
                            f"{assignment['multi_table']} "
                            f"privilege_level="
                            f"{assignment['privilege_level']} "
                            f"verification={verification} "
                            f"cleanup={cleanup}"
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
    return TruncateFactorExtensionPlan(
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
    "TruncateFactorExtensionError",
    "TruncateFactorExtensionCase",
    "TruncateFactorExtensionPlan",
    "build_truncate_factor_extension_plan",
]
