"""Bounded post-coverage cross-factor extension expander for ALTER STATISTICS.

The marginal factor-value-loop (:mod:`alter_statistics_factor_loop`) is the
required baseline: one program per factor value, 56 local cases
(GRM 4 + SFV 50 + RISK 2).  This module adds the bounded post-coverage
extension phase allowed by ``alter_statistics.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor combinations
of the positive T1-T4 behaviour axes for ALL FOUR grammar branches (set
statistics, rename, owner to, set schema), with at most one failure-causing
value per case so attribution stays clean, and ``verification_mode``
crossed with ``cleanup_mode`` crossed so every declared T6 value is
exercised.

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

from .alter_statistics_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_alter_statistics_factor_loop_plan,
)


class AlterStatisticsFactorExtensionError(ValueError):
    """Raised when a frozen ALTER STATISTICS extension input drifts."""


@dataclass(frozen=True)
class AlterStatisticsFactorExtensionCase:
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
class AlterStatisticsFactorExtensionPlan:
    cases: tuple[AlterStatisticsFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 56
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_statistic_ext_catalog",
    "error_assertion",
    "stxstattarget_query",
)
_CLEANUP_MODES = (
    "DROP_STATISTICS",
    "DROP_STATISTICS_IF_EXISTS",
    "DROP_STATISTICS_CASCADE",
)

# Dense positive baselines per branch.  The T5 single-value-negative factors
# are NOT baselined here; :func:`_derive_t5_factors` adds them at their
# declared values (always armed, firing only when the matching T1/T3 goes
# negative).
_SET_STATISTICS_BASELINE: dict[str, str] = {
    "statement_branch": "branch_set_statistics",
    "grammar_branch": "branch_set_statistics",
    "target_action": "set_statistics",
    "statistics_state": "exists",
    "expected_status": "success",
    "statistics_target_value": "zero",
    "statistics_name_shape": "simple_name",
    "target_value_shape": "integer_value",
    "executor_privilege": "superuser",
    "table_dependency": "underlying_table_exists",
    "new_name_shape": "simple_name",
    "new_schema_shape": "existing_schema",
    "new_owner_shape": "existing_role",
    "owner_to_shape": "explicit_role_name",
    "rename_behavior": "rename_to_new_name",
    "set_schema_behavior": "existing_schema",
    "verification_mode": "pg_statistic_ext_catalog",
    "cleanup_mode": "drop_statistics",
}

_RENAME_BASELINE: dict[str, str] = {
    "statement_branch": "branch_rename",
    "grammar_branch": "branch_rename",
    "target_action": "rename",
    "statistics_state": "exists",
    "expected_status": "success",
    "statistics_target_value": "zero",
    "statistics_name_shape": "simple_name",
    "target_value_shape": "integer_value",
    "executor_privilege": "superuser",
    "table_dependency": "underlying_table_exists",
    "new_name_shape": "simple_name",
    "new_schema_shape": "existing_schema",
    "new_owner_shape": "existing_role",
    "owner_to_shape": "explicit_role_name",
    "rename_behavior": "rename_to_new_name",
    "set_schema_behavior": "existing_schema",
    "verification_mode": "pg_statistic_ext_catalog",
    "cleanup_mode": "drop_statistics",
}

_OWNER_BASELINE: dict[str, str] = {
    "statement_branch": "branch_owner_to",
    "grammar_branch": "branch_owner_to",
    "target_action": "owner_to",
    "statistics_state": "exists",
    "expected_status": "success",
    "statistics_target_value": "zero",
    "statistics_name_shape": "simple_name",
    "target_value_shape": "integer_value",
    "executor_privilege": "superuser",
    "table_dependency": "underlying_table_exists",
    "new_name_shape": "simple_name",
    "new_schema_shape": "existing_schema",
    "new_owner_shape": "existing_role",
    "owner_to_shape": "explicit_role_name",
    "rename_behavior": "rename_to_new_name",
    "set_schema_behavior": "existing_schema",
    "verification_mode": "pg_statistic_ext_catalog",
    "cleanup_mode": "drop_statistics",
}

_SET_SCHEMA_BASELINE: dict[str, str] = {
    "statement_branch": "branch_set_schema",
    "grammar_branch": "branch_set_schema",
    "target_action": "set_schema",
    "statistics_state": "exists",
    "expected_status": "success",
    "statistics_target_value": "zero",
    "statistics_name_shape": "simple_name",
    "target_value_shape": "integer_value",
    "executor_privilege": "superuser",
    "table_dependency": "underlying_table_exists",
    "new_name_shape": "simple_name",
    "new_schema_shape": "existing_schema",
    "new_owner_shape": "existing_role",
    "owner_to_shape": "explicit_role_name",
    "rename_behavior": "rename_to_new_name",
    "set_schema_behavior": "existing_schema",
    "verification_mode": "pg_statistic_ext_catalog",
    "cleanup_mode": "drop_statistics",
}

# Common axes crossed on every branch.  statistics_state and
# statistics_name_shape are tied (cluster A): non_existent_name only appears
# with non_existent, so they are crossed as one paired axis to avoid
# double-counting a single failure.
_STATE_NAME_PAIRS = (
    ("exists", "simple_name"),
    ("exists", "schema_qualified_name"),
    ("exists", "quoted_name"),
    ("non_existent", "non_existent_name"),
)
_PRIVILEGE_AXES: dict[str, tuple[str, ...]] = {
    "executor_privilege": (
        "superuser",
        "table_owner",
        "non_owner_no_privilege",
    ),
}

# Per-branch crossed axes (T2 + T3).  Each axis includes both positive and
# negative (failure-causing) values; the at-most-one-failure rule ensures
# clean attribution.
_SET_STATISTICS_AXES: dict[str, tuple[str, ...]] = {
    "statistics_target_value": (
        "zero",
        "positive_integer",
        "maximum_value_10000",
        "negative_one_default",
        "default_keyword",
        "out_of_range",
    ),
}
# target_value_shape is DERIVED from statistics_target_value (1:1 tie) so the
# two never disagree and cluster F counts once.
_TARGET_VALUE_SHAPE_FOR: dict[str, str] = {
    "zero": "integer_value",
    "positive_integer": "integer_value",
    "maximum_value_10000": "integer_value",
    "negative_one_default": "negative_one",
    "default_keyword": "default_keyword",
    "out_of_range": "very_large_value",
}

_RENAME_BEHAVIOR_PAIRS = (
    ("rename_to_new_name", "simple_name"),
    ("rename_to_new_name", "quoted_name"),
    ("rename_to_existing_name_conflict", "existing_name_conflict"),
)

_OWNER_KEYWORD_PAIRS = (
    ("explicit_role_name", "existing_role"),
    ("explicit_role_name", "nonexistent_role"),
    ("current_role_keyword", "existing_role"),
    ("current_user_keyword", "existing_role"),
    ("session_user_keyword", "existing_role"),
)

_SET_SCHEMA_PAIRS = (
    ("existing_schema", "existing_schema"),
    ("nonexistent_schema", "nonexistent_schema"),
)

# Crossed behaviour-negative (factor, value) pairs across all branches.
# One representative per cluster; tied T3/T5 values are excluded to avoid
# double-counting a single failure.
_CROSSED_NEGATIVES = frozenset(
    {
        ("statistics_state", "non_existent"),
        ("executor_privilege", "non_owner_no_privilege"),
        ("statistics_target_value", "out_of_range"),
        ("rename_behavior", "rename_to_existing_name_conflict"),
        ("new_owner_shape", "nonexistent_role"),
        ("set_schema_behavior", "nonexistent_schema"),
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

    branch = assignment.get("target_action")
    if branch == "set_statistics":
        stv = assignment.get("statistics_target_value", "zero")
        tvs = assignment.get("target_value_shape", "integer_value")
        if _TARGET_VALUE_SHAPE_FOR.get(stv) != tvs:
            return False
    elif branch == "rename":
        rb = assignment.get("rename_behavior")
        nns = assignment.get("new_name_shape")
        if (rb, nns) not in _RENAME_BEHAVIOR_PAIRS:
            return False
    elif branch == "owner_to":
        ots = assignment.get("owner_to_shape")
        now = assignment.get("new_owner_shape")
        if (ots, now) not in _OWNER_KEYWORD_PAIRS:
            return False
    elif branch == "set_schema":
        ssb = assignment.get("set_schema_behavior")
        nss = assignment.get("new_schema_shape")
        if (ssb, nss) not in _SET_SCHEMA_PAIRS:
            return False
    else:
        return False
    # statistics_state <-> statistics_name_shape consistency (cluster A).
    ss = assignment.get("statistics_state", "exists")
    sns = assignment.get("statistics_name_shape", "simple_name")
    if (ss, sns) not in _STATE_NAME_PAIRS:
        return False
    # executor_privilege: superuser/table_owner never co-fire with the
    # privilege wall; non_owner is the only privilege failure.
    return _failure_unit_count(assignment) <= 1


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1/T3 values.

    The T5 single-value-negative factors carry only their declared
    (negative) value, so they are set to that declared value and fire only
    when the corresponding T1/T3 is also negative.  The extension's failure
    count uses T1/T3 crossed negatives only (:func:`_failure_unit_count`),
    so the always-on T5 values do not inflate the count.
    """

    a["nonexistent_statistics"] = "statistics_does_not_exist"
    a["privilege_insufficient"] = "non_table_owner_altering_statistics"
    a["nonexistent_schema"] = "schema_does_not_exist"
    a["nonexistent_owner"] = "owner_role_does_not_exist"
    a["target_out_of_range"] = "negative_other_than_minus_one"
    a["rename_conflict"] = "new_name_already_exists"

    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments (T6 at baseline) passing the filter."""

    configs = (
        ("set_statistics", _SET_STATISTICS_BASELINE),
        ("rename", _RENAME_BASELINE),
        ("owner_to", _OWNER_BASELINE),
        ("set_schema", _SET_SCHEMA_BASELINE),
    )
    combos: list[dict[str, str]] = []
    for branch, baseline in configs:
        if branch == "set_statistics":
            axes = {
                "state_name": tuple(range(len(_STATE_NAME_PAIRS))),
                "executor_privilege": _PRIVILEGE_AXES["executor_privilege"],
                "statistics_target_value": _SET_STATISTICS_AXES[
                    "statistics_target_value"
                ],
            }
            names = list(axes)
            for values in itertools.product(*[axes[n] for n in names]):
                assignment: dict[str, str] = dict(baseline)
                state_idx = values[names.index("state_name")]
                ss, sns = _STATE_NAME_PAIRS[state_idx]
                assignment["statistics_state"] = ss
                assignment["statistics_name_shape"] = sns
                assignment["executor_privilege"] = values[
                    names.index("executor_privilege")
                ]
                stv = values[names.index("statistics_target_value")]
                assignment["statistics_target_value"] = stv
                assignment["target_value_shape"] = (
                    _TARGET_VALUE_SHAPE_FOR[stv]
                )
                _derive_t5_factors(assignment)
                if not _is_valid_combination(assignment):
                    continue
                if len(assignment) != len(set(assignment)):
                    raise AlterStatisticsFactorExtensionError(
                        "duplicate factor key in extension assignment"
                    )
                combos.append(assignment)
        elif branch == "rename":
            axes = {
                "state_name": tuple(range(len(_STATE_NAME_PAIRS))),
                "executor_privilege": _PRIVILEGE_AXES["executor_privilege"],
                "rename_pair": tuple(range(len(_RENAME_BEHAVIOR_PAIRS))),
            }
            names = list(axes)
            for values in itertools.product(*[axes[n] for n in names]):
                assignment = dict(baseline)
                state_idx = values[names.index("state_name")]
                ss, sns = _STATE_NAME_PAIRS[state_idx]
                assignment["statistics_state"] = ss
                assignment["statistics_name_shape"] = sns
                assignment["executor_privilege"] = values[
                    names.index("executor_privilege")
                ]
                rb, nns = _RENAME_BEHAVIOR_PAIRS[
                    values[names.index("rename_pair")]
                ]
                assignment["rename_behavior"] = rb
                assignment["new_name_shape"] = nns
                _derive_t5_factors(assignment)
                if not _is_valid_combination(assignment):
                    continue
                if len(assignment) != len(set(assignment)):
                    raise AlterStatisticsFactorExtensionError(
                        "duplicate factor key in extension assignment"
                    )
                combos.append(assignment)
        elif branch == "owner_to":
            axes = {
                "state_name": tuple(range(len(_STATE_NAME_PAIRS))),
                "executor_privilege": _PRIVILEGE_AXES["executor_privilege"],
                "owner_pair": tuple(range(len(_OWNER_KEYWORD_PAIRS))),
            }
            names = list(axes)
            for values in itertools.product(*[axes[n] for n in names]):
                assignment = dict(baseline)
                state_idx = values[names.index("state_name")]
                ss, sns = _STATE_NAME_PAIRS[state_idx]
                assignment["statistics_state"] = ss
                assignment["statistics_name_shape"] = sns
                assignment["executor_privilege"] = values[
                    names.index("executor_privilege")
                ]
                ots, now = _OWNER_KEYWORD_PAIRS[
                    values[names.index("owner_pair")]
                ]
                assignment["owner_to_shape"] = ots
                assignment["new_owner_shape"] = now
                _derive_t5_factors(assignment)
                if not _is_valid_combination(assignment):
                    continue
                if len(assignment) != len(set(assignment)):
                    raise AlterStatisticsFactorExtensionError(
                        "duplicate factor key in extension assignment"
                    )
                combos.append(assignment)
        else:  # set_schema
            axes = {
                "state_name": tuple(range(len(_STATE_NAME_PAIRS))),
                "executor_privilege": _PRIVILEGE_AXES["executor_privilege"],
                "schema_pair": tuple(range(len(_SET_SCHEMA_PAIRS))),
            }
            names = list(axes)
            for values in itertools.product(*[axes[n] for n in names]):
                assignment = dict(baseline)
                state_idx = values[names.index("state_name")]
                ss, sns = _STATE_NAME_PAIRS[state_idx]
                assignment["statistics_state"] = ss
                assignment["statistics_name_shape"] = sns
                assignment["executor_privilege"] = values[
                    names.index("executor_privilege")
                ]
                ssb, nss = _SET_SCHEMA_PAIRS[
                    values[names.index("schema_pair")]
                ]
                assignment["set_schema_behavior"] = ssb
                assignment["new_schema_shape"] = nss
                _derive_t5_factors(assignment)
                if not _is_valid_combination(assignment):
                    continue
                if len(assignment) != len(set(assignment)):
                    raise AlterStatisticsFactorExtensionError(
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
    cases: tuple[AlterStatisticsFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"alter-statistics-factor-extension-v1\n"
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
    cases: tuple[AlterStatisticsFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"ALTER STATISTICS extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "alter_statistics_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "ALTER STATISTICS",
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


def build_alter_statistics_factor_extension_plan(
    repository_root: Path,
) -> AlterStatisticsFactorExtensionPlan:
    """Build the bounded ALTER STATISTICS post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_alter_statistics_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[AlterStatisticsFactorExtensionCase] = []
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
                    AlterStatisticsFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"ALTERSTATISTICS{ordinal:05d}",
                        sql_filename=f"ALTERSTATISTICS{ordinal:05d}.sql",
                        object_prefix=f"alterstatistics_{ordinal:05d}_",
                        derivation_id=(
                            f"ASTAT-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "alter_statistics_required_factor_value_matrix"
                        ),
                        derivation_reason=(
                            f"cross-factor extension: "
                            f"target_action="
                            f"{assignment['target_action']} "
                            f"x statistics_state="
                            f"{assignment['statistics_state']} "
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
    return AlterStatisticsFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(
            cases_tuple
        ),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "AlterStatisticsFactorExtensionError",
    "AlterStatisticsFactorExtensionCase",
    "AlterStatisticsFactorExtensionPlan",
    "build_alter_statistics_factor_extension_plan",
]
