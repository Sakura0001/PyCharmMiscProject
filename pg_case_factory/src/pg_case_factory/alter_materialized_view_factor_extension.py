"""Bounded post-coverage cross-factor extension expander for ALTER MATERIALIZED VIEW.

The marginal factor-value-loop (:mod:`alter_materialized_view_factor_loop`) is
the required baseline: one program per factor value, 61 local cases
(GRM 6 + SFV 53 + RISK 2).  This module adds the bounded post-coverage
extension phase allowed by ``alter_materialized_view.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor combinations
of the positive T1-T4 behaviour axes across the ``branch_action`` synopsis
branch (at most one failure-causing value per case, so attribution stays
clean), with ``verification_mode`` crossed and ``cleanup_mode`` crossed so
every declared T6 value is exercised.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``derived_extension_required_fields``) and is marked ``is_extension = True``.
The T5 negative factors (``invalid_combination``, ``ownership_boundary``)
are owned one-per-value by the marginal baseline and are never crossed here,
so the at-most-one-failure attribution stays clean.

The ``new_owner_shape`` axis is crossed only for the ``owner_to`` action
(the only action that references a new owner); for the other eleven
``alter_action_type`` values it stays at the ``plain_role`` baseline, so
``missing_role`` is only ever attributable where ``OWNER TO`` is actually
rendered.  ``target_object_state = missing`` is a failure only when
``if_exists_clause = absent`` (``IF EXISTS`` makes the missing-target case a
no-op success), mirroring the yaml's
``missing_and_wrong_target_failures`` compatibility rule.

The owner-transfer mechanics (SESSION_USER no-op-transfer,
``_privilege_boundary_fires``, ``_present_failure_pair``) are salvaged
verbatim from ``alter_large_object_factor_extension`` (commit 5035161b),
because ``OWNER TO`` is the same owner-transfer shape.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .alter_materialized_view_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_alter_materialized_view_factor_loop_plan,
)


class AlterMaterializedViewFactorExtensionError(ValueError):
    """Raised when a frozen ALTER MATERIALIZED VIEW extension input drifts."""


@dataclass(frozen=True)
class AlterMaterializedViewFactorExtensionCase:
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
class AlterMaterializedViewFactorExtensionPlan:
    cases: tuple[AlterMaterializedViewFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 61
# Safety backstop only; the natural at-most-one-failure cross is expected to
# stay well under this cap so no coverage-losing truncation occurs.  The exact
# frozen count is asserted in the companion test.
_CAP = 20000

_VERIFICATION_MODES = ("catalog_query", "effect_query", "error_assertion")
_CLEANUP_MODES = ("drop_objects", "reset_state")

# Privilege cluster: the insufficient-privilege value models the
# must_be_owner_of_materialized_view (42501) boundary and is counted as a
# single attributable failure unit.
_PRIVILEGE_CLUSTER_VALUES = frozenset({"insufficient_privilege"})

# Dense baseline assignment (all positive T1-T4 + T6 baselines).  The T5
# negative factors (invalid_combination, ownership_boundary) are intentionally
# absent: they are owned one-per-value by the marginal baseline and are never
# crossed here, so the at-most-one-failure attribution stays clean.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_action",
    "grammar_branch": "branch_action",
    "target_action": "set_statistics",
    "alter_action_type": "set_statistics",
    "target_object_state": "exists",
    "expected_status": "success",
    "if_exists_clause": "absent",
    "new_owner_shape": "plain_role",
    "privilege_context": "owner",
    "name_shape": "plain_identifier",
    "column_name_shape": "plain_identifier",
    "dependency_state": "ready",
    "extension_state": "extension_exists",
    "invalid_combination": "none",
    "ownership_boundary": "owner",
    "verification_mode": "catalog_query",
    "cleanup_mode": "drop_objects",
}

_BRANCH_ACTION = "branch_action"

# The twelve alter_action_type values (per the matrix; all live under
# branch_action).  owner_to is the only action that references a new owner.
_ALTER_ACTION_TYPES = (
    "set_statistics",
    "set_attribute_option",
    "reset_attribute_option",
    "set_storage",
    "set_compression",
    "cluster_on",
    "set_without_cluster",
    "set_access_method",
    "set_tablespace",
    "set_storage_parameter",
    "reset_storage_parameter",
    "owner_to",
)

_NEW_OWNER_SHAPES = (
    "plain_role",
    "current_role",
    "current_user",
    "session_user",
    "missing_role",
)
_TARGET_OBJECT_STATES = ("exists", "missing", "wrong_object_type")
_PRIVILEGE_CONTEXTS = ("owner", "granted_role", "insufficient_privilege")
_IF_EXISTS_CLAUSES = ("absent", "present")
_NAME_SHAPES = ("plain_identifier", "schema_qualified", "quoted_identifier")
_COLUMN_NAME_SHAPES = ("plain_identifier", "quoted_identifier")

# Crossed behaviour-negative (factor, value) pairs.  target_object_state=
# missing is a failure ONLY when if_exists_clause=absent (handled in
# _present_failure_pair / _failure_unit_count, not counted unconditionally
# here).  The privilege cluster (insufficient_privilege) is counted as a
# single unit via _PRIVILEGE_CLUSTER_VALUES and is therefore not duplicated
# here.
_CROSSED_BEHAVIOUR_NEGATIVES = frozenset(
    {
        ("target_object_state", "wrong_object_type"),
        ("new_owner_shape", "missing_role"),
    }
)


def _privilege_boundary_fires(assignment: dict[str, str]) -> bool:
    """Whether the must_be_owner_of_materialized_view check actually fires.

    ``SESSION_USER`` resolves to the session user (the superuser that owns
    every test materialized view in this framework), making
    ``OWNER TO SESSION_USER`` a no-op transfer to the existing owner that
    PG 18.4 allows even for non-owners.  Verified on the PG 18.4 cluster
    (salvaged from alter_large_object commit 5035161b, originally from
    alter_language commit 6b576686).  The privilege boundary does not fire
    for this specific sub-case, so the outcome is success (00000) rather than
    42501.
    """

    return assignment.get("new_owner_shape") != "session_user"


def _target_missing_fires(assignment: dict[str, str]) -> bool:
    """target_object_state=missing is a failure only without IF EXISTS.

    ``ALTER MATERIALIZED VIEW IF EXISTS`` on a missing materialized view is a
    no-op success (01000 NOTICE); without ``IF EXISTS`` it is a 42P01 error.
    """

    return (
        assignment.get("target_object_state") == "missing"
        and assignment.get("if_exists_clause") == "absent"
    )


def _if_exists_missing_noop(assignment: dict[str, str]) -> bool:
    """Whether IF EXISTS short-circuits a missing target to a no-op success.

    ``ALTER MATERIALIZED VIEW IF EXISTS`` on a missing materialized view never
    reaches the privilege, role, or object-type checks (PG 18.4 emits a 01000
    NOTICE and returns 00000), so no failure pair is attributable regardless of
    the co-occurring privilege_context / new_owner_shape / target_object_state
    values.  This only governs the *disposition* (expected_sqlstate) — the
    at-most-one failure-unit count is unchanged, so previously-excluded
    double-failure combinations stay excluded and the frozen case count is
    stable.
    """

    return (
        assignment.get("target_object_state") == "missing"
        and assignment.get("if_exists_clause") == "present"
    )


def _failure_unit_count(assignment: dict[str, str]) -> int:
    """Privilege cluster (1) + behaviour negatives; must stay at most one."""

    level = assignment.get("privilege_context")
    cluster = (
        1
        if level in _PRIVILEGE_CLUSTER_VALUES
        and _privilege_boundary_fires(assignment)
        else 0
    )
    negatives = sum(
        1
        for factor, value in _CROSSED_BEHAVIOUR_NEGATIVES
        if assignment.get(factor) == value
    )
    if _target_missing_fires(assignment):
        negatives += 1
    return cluster + negatives


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success.

    The privilege cluster is attributed first when present and the boundary
    actually fires, then any single co-occurring behaviour-negative (the
    at-most-one rule has already excluded double-failure cases from the kept
    set).  ``target_object_state = missing`` with ``if_exists_clause = present``
    is a no-op success (no failure pair).
    """

    if _if_exists_missing_noop(assignment):
        return None
    level = assignment.get("privilege_context")
    if (
        level in _PRIVILEGE_CLUSTER_VALUES
        and _privilege_boundary_fires(assignment)
    ):
        return ("privilege_context", level)
    if assignment.get("target_object_state") == "wrong_object_type":
        return ("target_object_state", "wrong_object_type")
    if _target_missing_fires(assignment):
        return ("target_object_state", "missing")
    if assignment.get("new_owner_shape") == "missing_role":
        return ("new_owner_shape", "missing_role")
    return None


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    """At-most-one-failure attribution."""

    return _failure_unit_count(assignment) <= 1


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments (T6 at baseline) passing the filter."""

    combos: list[dict[str, str]] = []
    for action in _ALTER_ACTION_TYPES:
        # new_owner_shape is only relevant for owner_to; for the other eleven
        # actions it stays at the plain_role baseline so missing_role is never
        # attributable where OWNER TO is not rendered.
        owner_shapes = _NEW_OWNER_SHAPES if action == "owner_to" else ("plain_role",)
        for owner in owner_shapes:
            for target in _TARGET_OBJECT_STATES:
                for privilege in _PRIVILEGE_CONTEXTS:
                    for if_exists in _IF_EXISTS_CLAUSES:
                        for name in _NAME_SHAPES:
                            for column_name in _COLUMN_NAME_SHAPES:
                                assignment: dict[str, str] = dict(_BASELINE_DEFAULTS)
                                assignment["alter_action_type"] = action
                                assignment["target_action"] = action
                                assignment["new_owner_shape"] = owner
                                assignment["target_object_state"] = target
                                assignment["privilege_context"] = privilege
                                assignment["if_exists_clause"] = if_exists
                                assignment["name_shape"] = name
                                assignment["column_name_shape"] = column_name
                                if not _is_valid_combination(assignment):
                                    continue
                                # expected_status follows the ACTUAL outcome
                                # (from _present_failure_pair), not the
                                # filter's failure-unit count.
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
    cases: tuple[AlterMaterializedViewFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"alter-materialized-view-factor-extension-v1\n"
    )
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
    cases: tuple[AlterMaterializedViewFactorExtensionCase, ...],
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
                    f"ALTER MATERIALIZED VIEW extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "alter_materialized_view_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "ALTER MATERIALIZED VIEW",
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


def build_alter_materialized_view_factor_extension_plan(
    repository_root: Path,
) -> AlterMaterializedViewFactorExtensionPlan:
    """Build the bounded ALTER MATERIALIZED VIEW post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_alter_materialized_view_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    # Stable sort so any cap truncation is deterministic.
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[AlterMaterializedViewFactorExtensionCase] = []
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
                    AlterMaterializedViewFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"ALTERMATERIALIZEDVIEW{ordinal:05d}",
                        sql_filename=f"ALTERMATERIALIZEDVIEW{ordinal:05d}.sql",
                        object_prefix=f"altermaterializedview_{ordinal:05d}_",
                        derivation_id=(
                            f"AMV-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "alter_materialized_view_required_baseline_factor_space"
                        ),
                        derivation_reason=(
                            f"cross-factor extension: alter_action_type="
                            f"{assignment['alter_action_type']} "
                            f"x target_object_state="
                            f"{assignment['target_object_state']} "
                            f"x privilege_context={verification} "
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
    return AlterMaterializedViewFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "AlterMaterializedViewFactorExtensionError",
    "AlterMaterializedViewFactorExtensionCase",
    "AlterMaterializedViewFactorExtensionPlan",
    "build_alter_materialized_view_factor_extension_plan",
]
