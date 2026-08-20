"""Bounded post-coverage cross-factor extension expander for DROP DATABASE.

The marginal factor-value-loop (:mod:`drop_database_factor_loop`) is the
required baseline: one program per factor value, 50 local cases
(GRM 1 + SFV 47 + Risk 2).  This module adds the bounded post-coverage
extension phase allowed by ``drop_database.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor combinations
of the positive behaviour axes (database-name shape, IF EXISTS, FORCE option)
with the single-value failure axes (privilege, transaction block, current
database, existence, object-in-use cluster), keeping at most one
failure-causing value per case so attribution stays clean.  ``verification_mode``
and ``cleanup_mode`` are crossed so every declared T6 value is exercised.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``derived_extension_required_fields``) and is marked ``is_extension = True``.
The failure values owned one-per-value by the marginal baseline
(``database_name_shape=nonexistent_name`` and the multi-valued
``active_connections`` / ``connected_to_target_database`` / ``privilege_denied``
/ ``force_with_unterminable_connections`` / ``active_connections_without_force``
axes) are never crossed here, so the at-most-one-failure attribution stays
clean.

The single official synopsis branch is crossed:

* ``branch_drop_database`` — ``database_name_shape`` x ``if_exists_clause`` x
  ``force_option`` x the eight single-value failure axes, with
  ``verification_mode`` x ``cleanup_mode`` crossed on top.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .drop_database_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_drop_database_factor_loop_plan,
)


class DropDatabaseFactorExtensionError(ValueError):
    """Raised when a frozen DROP DATABASE extension input drifts."""


@dataclass(frozen=True)
class DropDatabaseFactorExtensionCase:
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
class DropDatabaseFactorExtensionPlan:
    cases: tuple[DropDatabaseFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 50
# Safety backstop only; the natural at-most-one-failure cross is expected to
# stay well under this cap so no coverage-losing truncation occurs.  The exact
# frozen count is asserted in the companion test.
_CAP = 20000

_VERIFICATION_MODES = (
    "catalog_query_pg_database_absence",
    "error_assertion",
    "notice_assertion_if_exists",
)
_CLEANUP_MODES = (
    "drop_database_simple",
    "force_drop_database",
)

# Dense baseline assignment (all positive values + the synthetic
# grammar_branch/target_action keys).  The multi-valued failure axes owned
# one-per-value by the marginal baseline (database_name_shape=nonexistent_name,
# active_connections, connected_to_target_database, privilege_denied,
# force_with_unterminable_connections, active_connections_without_force,
# object_state, expected_status) are intentionally absent from the cross.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_database",
    "grammar_branch": "branch_drop_database",
    "target_action": "drop_database",
    "object_state": "exists",
    "expected_status": "success",
    "connection_state": "no_other_connections",
    "force_option": "omitted",
    "if_exists_clause": "omitted",
    "database_name_shape": "simple_id",
    "database_not_exist_no_if_exists": "database_exists",
    "drop_current_database": "different_database",
    "inside_transaction_block": "outside_transaction",
    "prepared_transactions": "no_prepared_transactions",
    "privilege_level": "superuser",
    "privilege_denied": "superuser_success",
    "replication_slots": "no_active_slots",
    "subscriptions": "no_subscriptions",
    "active_connections": "no_active_connections",
    "active_connections_without_force": "no_connections_or_force_used",
    "connected_to_target_database": "connected_to_different_database",
    "force_with_unterminable_connections": "all_connections_terminable",
    "cleanup_mode": "drop_database_simple",
    "verification_mode": "catalog_query_pg_database_absence",
}

# Official synopsis branch -> grammar_branch id used by the renderer.
_BRANCH_GRAMMAR: dict[str, str] = {
    "branch_drop_database": "branch_drop_database",
}

# Fixed consumer action per branch (the synopsis action form).
_BRANCH_FIXED_ACTION: dict[str, str] = {
    "branch_drop_database": "drop_database",
}

# Crossed positive behaviour axes per branch.  database_name_shape excludes
# nonexistent_name (a T3 negative owned by the marginal baseline).
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_drop_database": {
        "database_name_shape": ("simple_id", "quoted_id"),
        "if_exists_clause": ("omitted", "specified_if_exists"),
        "force_option": ("omitted", "specified_force"),
    },
}

# Crossed single-value failure axes (each has one failure value + one success
# value).  At most one failure value per case is kept so attribution stays
# clean; combos with two or more present failures are dropped.
_BRANCH_FAILURE_AXES: dict[str, dict[str, tuple[str, str]]] = {
    "branch_drop_database": {
        "privilege_level": ("superuser", "non_owner"),
        "inside_transaction_block": ("outside_transaction", "inside_transaction"),
        "drop_current_database": ("different_database", "current_database"),
        "database_not_exist_no_if_exists": (
            "database_exists",
            "database_not_exists_no_if_exists",
        ),
        "connection_state": ("no_other_connections", "has_other_connections"),
        "prepared_transactions": (
            "no_prepared_transactions",
            "has_prepared_transactions",
        ),
        "replication_slots": ("no_active_slots", "has_active_slots"),
        "subscriptions": ("no_subscriptions", "has_subscriptions"),
    },
}

# Failure attribution precedence (first match wins).  This mirrors the PG 18.4
# check order: transaction-block check fires first, then privilege, then the
# current-database guard, then existence, then the object-in-use cluster.
_FAILURE_PRECEDENCE: tuple[tuple[str, str], ...] = (
    ("inside_transaction_block", "inside_transaction"),
    ("privilege_level", "non_owner"),
    ("drop_current_database", "current_database"),
    ("database_not_exist_no_if_exists", "database_not_exists_no_if_exists"),
    ("connection_state", "has_other_connections"),
    ("prepared_transactions", "has_prepared_transactions"),
    ("replication_slots", "has_active_slots"),
    ("subscriptions", "has_subscriptions"),
)

# Factors held constant at the baseline success value (never crossed).  These
# are the multi-valued / baseline-owned negatives.  ``expected_status`` is
# derived from the present failure pair (not held constant).
_HELD_CONSTANT = {
    "object_state": "exists",
    "active_connections": "no_active_connections",
    "active_connections_without_force": "no_connections_or_force_used",
    "connected_to_target_database": "connected_to_different_database",
    "force_with_unterminable_connections": "all_connections_terminable",
    "privilege_denied": "superuser_success",
}


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success.

    The first matching failure in ``_FAILURE_PRECEDENCE`` wins; the
    at-most-one filter has already excluded combos with two or more present
    failures, so the first match is the only match.
    """

    for factor, value in _FAILURE_PRECEDENCE:
        if assignment.get(factor) == value:
            return (factor, value)
    return None


def _failure_unit_count(assignment: dict[str, str]) -> int:
    """Count present failure units; the at-most-one rule keeps this <= 1."""

    return sum(
        1
        for factor, value in _FAILURE_PRECEDENCE
        if assignment.get(factor) == value
    )


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    """At-most-one-failure attribution."""

    return _failure_unit_count(assignment) <= 1


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis + single-failure assignments passing the filter."""

    combos: list[dict[str, str]] = []
    for branch, axes in _BRANCH_AXES.items():
        failure_axes = _BRANCH_FAILURE_AXES[branch]
        pos_names = list(axes)
        fail_names = list(failure_axes)
        for pos_values in itertools.product(*(axes[n] for n in pos_names)):
            for fail_values in itertools.product(
                *(failure_axes[n] for n in fail_names)
            ):
                assignment: dict[str, str] = dict(_BASELINE_DEFAULTS)
                assignment["statement_branch"] = branch
                assignment["grammar_branch"] = _BRANCH_GRAMMAR[branch]
                assignment["target_action"] = _BRANCH_FIXED_ACTION[branch]
                for name, value in zip(pos_names, pos_values):
                    assignment[name] = value
                for name, value in zip(fail_names, fail_values):
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
    """Derive (outcome, expected_sqlstate, expected_failure_reason)."""

    pair = _present_failure_pair(assignment)
    if pair is None:
        return "success", "00000", None
    sqlstate, reason = _SFV_FAILURE_SQLSTATE[pair]
    return "expected_failure", sqlstate, reason


def _extension_multiset_sha256(
    cases: tuple[DropDatabaseFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"drop-database-factor-extension-v1\n")
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
    cases: tuple[DropDatabaseFactorExtensionCase, ...],
) -> str:
    """Emit the derived-extension ledger with the yaml required fields."""

    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"DROP DATABASE extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "drop_database_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "DROP DATABASE",
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


def build_drop_database_factor_extension_plan(
    repository_root: Path,
) -> DropDatabaseFactorExtensionPlan:
    """Build the bounded DROP DATABASE post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_drop_database_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[DropDatabaseFactorExtensionCase] = []
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
                    DropDatabaseFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"DROPDATABASE{ordinal:05d}",
                        sql_filename=f"DROPDATABASE{ordinal:05d}.sql",
                        object_prefix=f"dropdatabase_{ordinal:05d}_",
                        derivation_id=(
                            f"DROPDATABASE-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "drop_database_required_baseline_factor_space"
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
    return DropDatabaseFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "DropDatabaseFactorExtensionError",
    "DropDatabaseFactorExtensionCase",
    "DropDatabaseFactorExtensionPlan",
    "build_drop_database_factor_extension_plan",
    "_present_failure_pair",
    "_failure_unit_count",
]
