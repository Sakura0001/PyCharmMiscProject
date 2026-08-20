"""Bounded post-coverage cross-factor extension expander for ALTER RULE.

The marginal factor-value-loop (:mod:`alter_rule_factor_loop`) is the
required baseline: one program per factor value, 46 local cases
(GRM 1 + SFV 43 + RISK 2).  This module adds the bounded post-coverage
extension phase allowed by ``alter_rule.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive T1-T4 behaviour axes (at most one
failure-causing value per case, so attribution stays clean), with
``verification_mode`` crossed and ``cleanup_mode`` crossed so every
declared T6 value is exercised.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``derived_extension_required_fields``) and is marked ``is_extension = True``.

SCALE rationale: ALTER RULE has a single grammar branch (rename only)
with ~43 factor values.  The bounded Option-A extension crosses the T3
name shapes (rule_name_shape 5 × table_name_shape 4 × new_name_shape 4)
× T4 privilege (3) × T2 table_type (2), with at-most-one-failure
attribution and the _RETURN_special→view applicability constraint,
yielding 262 behaviour combinations.  Crossing each with T6
(verification_mode 2 × cleanup_mode 4 = 8) reaches 2096 extension
cases — the thousands range mandated by the campaign directive.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .alter_rule_factor_loop import (
    _EXPECTED_BEHAVIOR_VALUES,
    _SFV_FAILURE_SQLSTATE,
    _SFV_FAILURE_VALUES,
    build_alter_rule_factor_loop_plan,
)


class AlterRuleFactorExtensionError(ValueError):
    """Raised when a frozen ALTER RULE extension input drifts."""


@dataclass(frozen=True)
class AlterRuleFactorExtensionCase:
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
class AlterRuleFactorExtensionPlan:
    cases: tuple[AlterRuleFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 46
_CAP = 20000

_VERIFICATION_MODES = (
    "catalog_query_pg_rewrite",
    "error_assertion",
)
_CLEANUP_MODES = (
    "revert_rename",
    "drop_rule",
    "drop_view",
    "drop_table",
)

_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_rename",
    "grammar_branch": "branch_rename",
    "alter_action": "rename",
    "object_state": "exists",
    "expected_status": "success",
    "table_type": "table",
    "rule_name_shape": "simple_id",
    "table_name_shape": "simple_id",
    "new_name_shape": "simple_id",
    "privilege_level": "superuser",
    "table_existence": "table_exists",
    "nonexistent_rule": "rule_exists",
    "nonexistent_table": "table_exists",
    "privilege_denied": "owner_execution",
    "duplicate_new_name": "no_conflict",
    "on_select_return_rename": "normal_rule_rename",
    "verification_mode": "catalog_query_pg_rewrite",
    "cleanup_mode": "revert_rename",
}

# Crossed axes (T2 + T3 + T4).  Each axis includes both positive and
# negative (failure-causing) values; the at-most-one-failure rule
# ensures clean attribution.
_AXES: dict[str, tuple[str, ...]] = {
    "table_type": ("table", "view"),
    "rule_name_shape": (
        "simple_id",
        "quoted_id",
        "_RETURN_special",
        "existing_name",
        "nonexistent_name",
    ),
    "table_name_shape": (
        "simple_id",
        "quoted_id",
        "schema_qualified",
        "nonexistent_table",
    ),
    "new_name_shape": (
        "simple_id",
        "quoted_id",
        "duplicate_name_same_table",
        "invalid_name",
    ),
    "privilege_level": (
        "superuser",
        "table_owner",
        "non_owner",
    ),
}

# Crossed behaviour-negative (factor, value) pairs.
_CROSSED_NEGATIVES = frozenset(
    {
        ("rule_name_shape", "nonexistent_name"),
        ("table_name_shape", "nonexistent_table"),
        ("new_name_shape", "duplicate_name_same_table"),
        ("new_name_shape", "invalid_name"),
        ("privilege_level", "non_owner"),
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
    """Applicability + at-most-one-failure attribution."""

    # rule_name_shape=_RETURN_special requires table_type=view (ON SELECT
    # _RETURN rule only exists on views).
    if (
        assignment.get("rule_name_shape") == "_RETURN_special"
        and assignment.get("table_type") != "view"
    ):
        return False
    return _failure_unit_count(assignment) <= 1


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T3/T4 values."""

    rns = a.get("rule_name_shape", "simple_id")
    tns = a.get("table_name_shape", "simple_id")
    nns = a.get("new_name_shape", "simple_id")
    pl = a.get("privilege_level", "superuser")
    tt = a.get("table_type", "table")

    a["nonexistent_rule"] = (
        "rule_missing" if rns == "nonexistent_name" else "rule_exists"
    )
    a["object_state"] = "not_exists" if rns == "nonexistent_name" else "exists"
    a["nonexistent_table"] = (
        "table_missing" if tns == "nonexistent_table" else "table_exists"
    )
    a["table_existence"] = (
        "table_not_exists" if tns == "nonexistent_table" else "table_exists"
    )
    a["duplicate_new_name"] = (
        "same_table_same_event_conflict"
        if nns == "duplicate_name_same_table"
        else "no_conflict"
    )
    if pl == "non_owner":
        a["privilege_denied"] = "non_owner_denied"
    elif pl == "table_owner":
        a["privilege_denied"] = "owner_execution"
    else:
        a["privilege_denied"] = "superuser_execution"
    a["on_select_return_rename"] = (
        "_RETURN_rename_breaks_view"
        if rns == "_RETURN_special" and tt == "view"
        else "normal_rule_rename"
    )
    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments (T6 at baseline) passing the filter."""

    combos: list[dict[str, str]] = []
    names = list(_AXES)
    for values in itertools.product(*(_AXES[n] for n in names)):
        assignment: dict[str, str] = dict(_BASELINE_DEFAULTS)
        for name, value in zip(names, values):
            assignment[name] = value
        _derive_t5_factors(assignment)
        if not _is_valid_combination(assignment):
            continue
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
    cases: tuple[AlterRuleFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"alter-rule-factor-extension-v1\n")
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
    cases: tuple[AlterRuleFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"ALTER RULE extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "alter_rule_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "ALTER RULE",
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


def build_alter_rule_factor_extension_plan(
    repository_root: Path,
) -> AlterRuleFactorExtensionPlan:
    """Build the bounded ALTER RULE post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_alter_rule_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[AlterRuleFactorExtensionCase] = []
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
                    AlterRuleFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"ALTERRULE{ordinal:05d}",
                        sql_filename=f"ALTERRULE{ordinal:05d}.sql",
                        object_prefix=f"alterrule_{ordinal:05d}_",
                        derivation_id=(
                            f"AR-EXT|{ordinal:05d}|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "alter_rule_required_baseline_factor_space"
                        ),
                        derivation_reason=(
                            f"cross-factor extension: "
                            f"table_type={assignment['table_type']} "
                            f"x rule_name_shape="
                            f"{assignment['rule_name_shape']} "
                            f"x table_name_shape="
                            f"{assignment['table_name_shape']} "
                            f"x new_name_shape="
                            f"{assignment['new_name_shape']} "
                            f"x privilege_level="
                            f"{assignment['privilege_level']} "
                            f"x verification_mode={verification} "
                            f"x cleanup_mode={cleanup}"
                        ),
                        factor_assignment=tuple(sorted(assignment.items())),
                        consumer_action_id="rename",
                        outcome=outcome,
                        expected_sqlstate=sqlstate,
                        expected_failure_reason=reason,
                        is_extension=True,
                    )
                )
    dropped = max(0, raw - _CAP)
    cases_tuple = tuple(cases)
    return AlterRuleFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "AlterRuleFactorExtensionError",
    "AlterRuleFactorExtensionCase",
    "AlterRuleFactorExtensionPlan",
    "build_alter_rule_factor_extension_plan",
]
