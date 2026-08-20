"""Bounded post-coverage cross-factor extension expander for ALTER SCHEMA.

The marginal factor-value-loop (:mod:`alter_schema_factor_loop`) is the
required baseline: one program per factor value, 57 local cases
(GRM 2 + SFV 53 + RISK 2).  This module adds the bounded post-coverage
extension phase allowed by ``alter_schema.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive T1-T4 behaviour axes for BOTH grammar
branches (rename and owner), with at most one failure-causing value per
case so attribution stays clean, and ``verification_mode`` crossed with
``cleanup_mode`` crossed so every declared T6 value is exercised.

ALTER SCHEMA's OWNER-TO branch carries a membership wall: a
non-superuser schema owner transferring ownership to an explicit role,
``CURRENT_ROLE``, or ``CURRENT_USER`` must be a member of the target
role (``SET ROLE``), else ``42501``.  ``OWNER TO SESSION_USER`` is a
permitted no-op transfer that escapes the wall (mirrors
``alter_publication``): it is enforced here as the consistency rule
``owner_clause == SESSION_USER -> owner_change_privilege ==
can_SET_ROLE_to_new_owner`` so the wall never fires for the escape.

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

from .alter_schema_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_alter_schema_factor_loop_plan,
)


class AlterSchemaFactorExtensionError(ValueError):
    """Raised when a frozen ALTER SCHEMA extension input drifts."""


@dataclass(frozen=True)
class AlterSchemaFactorExtensionCase:
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
class AlterSchemaFactorExtensionPlan:
    cases: tuple[AlterSchemaFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 57
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_namespace_catalog_query",
    "information_schema_schemata",
    "current_schema_query",
)
_CLEANUP_MODES = (
    "DROP_SCHEMA",
    "DROP_SCHEMA_IF_EXISTS",
    "DROP_SCHEMA_CASCADE",
)

# Dense positive baselines per branch.  The T5 single-value-negative
# factors (non_existent_schema, pg_prefix_new_name, new_name_conflict,
# new_owner_not_exists, insufficient_privilege) are NOT baselined here;
# :func:`_derive_t5_factors` adds them at their declared values.
_RENAME_BASELINE: dict[str, str] = {
    "statement_branch": "branch_rename",
    "grammar_branch": "branch_rename",
    "target_action": "rename",
    "object_state": "exists",
    "expected_status": "success",
    "rename_clause": "new_simple_name",
    "owner_clause": "new_owner_role",
    "new_name_constraint": "not_pg_prefix",
    "schema_name_shape": "simple",
    "new_name_shape": "simple",
    "new_owner_shape": "existing_role",
    "privilege_level": "superuser",
    "rename_privilege": "owner_with_CREATE_on_db",
    "owner_change_privilege": "can_SET_ROLE_to_new_owner",
    "new_owner_db_privilege": "has_CREATE_privilege",
    "contained_objects_state": "empty_schema",
    "verification_mode": "pg_namespace_catalog_query",
    "cleanup_mode": "DROP_SCHEMA",
}

_OWNER_BASELINE: dict[str, str] = {
    "statement_branch": "branch_owner",
    "grammar_branch": "branch_owner",
    "target_action": "owner",
    "object_state": "exists",
    "expected_status": "success",
    "rename_clause": "new_simple_name",
    "owner_clause": "new_owner_role",
    "new_name_constraint": "not_pg_prefix",
    "schema_name_shape": "simple",
    "new_name_shape": "simple",
    "new_owner_shape": "existing_role",
    "privilege_level": "superuser",
    "rename_privilege": "owner_with_CREATE_on_db",
    "owner_change_privilege": "can_SET_ROLE_to_new_owner",
    "new_owner_db_privilege": "has_CREATE_privilege",
    "contained_objects_state": "empty_schema",
    "verification_mode": "pg_namespace_catalog_query",
    "cleanup_mode": "DROP_SCHEMA",
}

# Crossed axes per branch (T2 + T3 + T4).  Each axis includes both
# positive and negative (failure-causing) values; the at-most-one-failure
# rule ensures clean attribution.
_RENAME_AXES: dict[str, tuple[str, ...]] = {
    "object_state": ("exists", "not_exists"),
    "rename_clause": (
        "new_simple_name",
        "new_pg_prefix_name",
        "new_existing_name",
    ),
    "new_name_shape": ("simple", "pg_prefix_reserved"),
    "schema_name_shape": (
        "simple",
        "quoted",
        "reserved_word",
        "schema_qualified",
    ),
    "privilege_level": ("superuser", "schema_owner", "non_owner"),
    "rename_privilege": (
        "owner_with_CREATE_on_db",
        "owner_no_CREATE_on_db",
    ),
    "contained_objects_state": (
        "empty_schema",
        "schema_with_tables",
        "schema_with_views",
    ),
}

_OWNER_AXES: dict[str, tuple[str, ...]] = {
    "object_state": ("exists", "not_exists"),
    "owner_clause": (
        "new_owner_role",
        "CURRENT_ROLE",
        "CURRENT_USER",
        "SESSION_USER",
    ),
    "new_owner_shape": (
        "existing_role",
        "non_existing_role",
        "CURRENT_ROLE",
        "CURRENT_USER",
        "SESSION_USER",
    ),
    "privilege_level": ("superuser", "schema_owner", "non_owner"),
    "owner_change_privilege": (
        "can_SET_ROLE_to_new_owner",
        "cannot_SET_ROLE_to_new_owner",
    ),
    "new_owner_db_privilege": (
        "has_CREATE_privilege",
        "no_CREATE_privilege",
    ),
    "contained_objects_state": (
        "empty_schema",
        "schema_with_tables",
        "schema_with_views",
    ),
    "schema_name_shape": (
        "simple",
        "quoted",
        "reserved_word",
        "schema_qualified",
    ),
}

# Crossed behaviour-negative (factor, value) pairs across both branches.
# The pg_prefix boundary is represented by rename_clause=new_pg_prefix_name
# only: new_name_shape=pg_prefix_reserved is tied 1:1 to it by the
# consistency rule, so counting both would double-count a single failure
# and break the at-most-one attribution.
_CROSSED_NEGATIVES = frozenset(
    {
        ("object_state", "not_exists"),
        ("rename_clause", "new_pg_prefix_name"),
        ("rename_clause", "new_existing_name"),
        ("privilege_level", "non_owner"),
        ("rename_privilege", "owner_no_CREATE_on_db"),
        ("new_owner_shape", "non_existing_role"),
        ("owner_change_privilege", "cannot_SET_ROLE_to_new_owner"),
        ("new_owner_db_privilege", "no_CREATE_privilege"),
    }
)

# Valid (owner_clause, new_owner_shape) keyword-agreement pairs.
_OWNER_KEYWORD_PAIRS = frozenset(
    {
        ("new_owner_role", "existing_role"),
        ("new_owner_role", "non_existing_role"),
        ("CURRENT_ROLE", "CURRENT_ROLE"),
        ("CURRENT_USER", "CURRENT_USER"),
        ("SESSION_USER", "SESSION_USER"),
    }
)

_BRANCH_CONFIG = (
    ("rename", _RENAME_AXES, _RENAME_BASELINE),
    ("owner", _OWNER_AXES, _OWNER_BASELINE),
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
    if branch == "rename":
        rnc = assignment.get("rename_clause")
        nns = assignment.get("new_name_shape")
        if rnc == "new_pg_prefix_name" and nns != "pg_prefix_reserved":
            return False
        if rnc != "new_pg_prefix_name" and nns == "pg_prefix_reserved":
            return False
        pl = assignment.get("privilege_level")
        rp = assignment.get("rename_privilege")
        if pl == "superuser" and rp != "owner_with_CREATE_on_db":
            return False
        if pl == "non_owner" and rp != "owner_with_CREATE_on_db":
            return False
    elif branch == "owner":
        oc = assignment.get("owner_clause")
        now = assignment.get("new_owner_shape")
        if (oc, now) not in _OWNER_KEYWORD_PAIRS:
            return False
        pl = assignment.get("privilege_level")
        ocp = assignment.get("owner_change_privilege")
        nodp = assignment.get("new_owner_db_privilege")
        if pl == "superuser" and (
            ocp != "can_SET_ROLE_to_new_owner"
            or nodp != "has_CREATE_privilege"
        ):
            return False
        if pl == "non_owner" and (
            ocp != "can_SET_ROLE_to_new_owner"
            or nodp != "has_CREATE_privilege"
        ):
            return False
        # SESSION_USER escape: the wall never fires for the escape.
        if (
            oc == "SESSION_USER"
            and ocp != "can_SET_ROLE_to_new_owner"
        ):
            return False
    else:
        return False
    return _failure_unit_count(assignment) <= 1


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T3/T4 values.

    The T5 single-value-negative factors carry only their declared
    (negative) value, so they are set to that declared value and fire
    only when the corresponding T3/T4 is also negative.  The extension's
    failure count uses T3/T4 crossed negatives only
    (:func:`_failure_unit_count`), so the always-on T5 values do not
    inflate the count.
    """

    rnc = a.get("rename_clause", "new_simple_name")
    nns = a.get("new_name_shape", "simple")
    pl = a.get("privilege_level", "superuser")
    rp = a.get("rename_privilege", "owner_with_CREATE_on_db")
    ocp = a.get("owner_change_privilege", "can_SET_ROLE_to_new_owner")

    a["non_existent_schema"] = "target_not_exists"
    a["new_name_conflict"] = "new_name_already_exists"
    a["new_owner_not_exists"] = "specified_role_not_exists"

    if rnc == "new_pg_prefix_name" or nns == "pg_prefix_reserved":
        a["pg_prefix_new_name"] = "pg_prefix_illegal"
        a["new_name_constraint"] = "pg_prefix_illegal"
    else:
        a["pg_prefix_new_name"] = "pg_prefix_illegal"
        a["new_name_constraint"] = "not_pg_prefix"

    if pl == "non_owner":
        a["insufficient_privilege"] = "non_owner_attempt"
    elif rp == "owner_no_CREATE_on_db":
        a["insufficient_privilege"] = "owner_no_CREATE_on_db"
    elif ocp == "cannot_SET_ROLE_to_new_owner":
        a["insufficient_privilege"] = "cannot_SET_ROLE"
    else:
        a["insufficient_privilege"] = "non_owner_attempt"

    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments (T6 at baseline) passing the filter."""

    combos: list[dict[str, str]] = []
    for _branch, axes, baseline in _BRANCH_CONFIG:
        names = list(axes)
        for values in itertools.product(*[axes[n] for n in names]):
            assignment: dict[str, str] = dict(baseline)
            for name, value in zip(names, values):
                assignment[name] = value
            _derive_t5_factors(assignment)
            if not _is_valid_combination(assignment):
                continue
            if len(assignment) != len(set(assignment)):
                raise AlterSchemaFactorExtensionError(
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
    cases: tuple[AlterSchemaFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"alter-schema-factor-extension-v1\n")
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
    cases: tuple[AlterSchemaFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"ALTER SCHEMA extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "alter_schema_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "ALTER SCHEMA",
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


def build_alter_schema_factor_extension_plan(
    repository_root: Path,
) -> AlterSchemaFactorExtensionPlan:
    """Build the bounded ALTER SCHEMA post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_alter_schema_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[AlterSchemaFactorExtensionCase] = []
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
                    AlterSchemaFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"ALTERSCHEMA{ordinal:05d}",
                        sql_filename=f"ALTERSCHEMA{ordinal:05d}.sql",
                        object_prefix=f"alterschema_{ordinal:05d}_",
                        derivation_id=(
                            f"AS-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "alter_schema_required_factor_value_matrix"
                        ),
                        derivation_reason=(
                            f"cross-factor extension: "
                            f"target_action="
                            f"{assignment['target_action']} "
                            f"x object_state="
                            f"{assignment['object_state']} "
                            f"x privilege_level="
                            f"{assignment['privilege_level']} "
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
    return AlterSchemaFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "AlterSchemaFactorExtensionError",
    "AlterSchemaFactorExtensionCase",
    "AlterSchemaFactorExtensionPlan",
    "build_alter_schema_factor_extension_plan",
]
