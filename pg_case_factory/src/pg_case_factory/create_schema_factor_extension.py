"""Bounded post-coverage cross-factor extension expander for CREATE SCHEMA.

The marginal factor-value-loop (:mod:`create_schema_factor_loop`) is the
required baseline: one program per factor value, 62 local cases
(GRM 4 + SFV 58).  This module adds the bounded post-coverage extension
phase allowed by ``create_schema.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive T1-T4 behaviour axes across all four
grammar branches, with at most one failure-causing value per case so
attribution stays clean, and ``verification_mode``/``cleanup_mode``
crossed so every declared T6 value is exercised.

CREATE SCHEMA is a namespace-management DDL statement: it never creates
a standalone TABLE (any ``CREATE TABLE`` is a sub-clause of
``CREATE SCHEMA``), so the bookend (DROP TABLE IF EXISTS) is never
emitted.  The ``pg_catalog.pg_namespace`` catalog row (not a
``pg_class`` relation) is the semantic witness target.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record and is marked ``is_extension``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe
from .create_schema_factor_loop import _BASELINE_DEFAULTS


class CreateSchemaFactorExtensionError(ValueError):
    """Raised when a frozen CREATE SCHEMA extension input drifts."""


@dataclass(frozen=True)
class CreateSchemaFactorExtensionCase:
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
    is_extension: bool = True


@dataclass(frozen=True)
class CreateSchemaFactorExtensionPlan:
    cases: tuple[CreateSchemaFactorExtensionCase, ...]
    extension_multiset_sha256: str
    raw_combination_count: int
    dropped_combination_count: int


_BASELINE_COUNT = 62
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_namespace_catalog_query",
    "information_schema_schemata",
    "current_schema_query",
)
_CLEANUP_MODES = ("DROP_SCHEMA", "DROP_SCHEMA_IF_EXISTS", "DROP_SCHEMA_CASCADE")

_AUTHORIZATION_VALUES = (
    "absent",
    "explicit_user",
    "CURRENT_ROLE",
    "CURRENT_USER",
    "SESSION_USER",
)
_ROLE_SPEC_VALUES = (
    "user_name",
    "CURRENT_ROLE",
    "CURRENT_USER",
    "SESSION_USER",
)
_ELEMENT_VALUES = (
    "without_elements",
    "with_create_table",
    "with_create_view",
    "with_multiple_elements",
)

# General axes crossed for ALL four branches.
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "object_state": ("not_exists", "already_exists"),
    "schema_name_shape": (
        "simple",
        "quoted",
        "reserved_word",
        "pg_prefix_reserved",
    ),
    "privilege_level": ("superuser", "non_creator_no_privilege"),
    "owner_name_shape": (
        "existing_role",
        "non_existing_role",
        "CURRENT_ROLE",
    ),
    "database_privilege": ("has_CREATE_privilege", "no_CREATE_privilege"),
    "role_dependency": ("role_exists", "cannot_SET_ROLE"),
}

# Branch -> (statement_branch, target_action, branch-specific axes).
_BRANCH_CONFIG: tuple[
    tuple[str, str, dict[str, tuple[str, ...]], ...],
    ...,
] = (
    (
        "branch_named_schema",
        "create_named_schema",
        {
            "authorization_clause": _AUTHORIZATION_VALUES,
            "schema_element_inclusion": _ELEMENT_VALUES,
        },
    ),
    (
        "branch_auth_schema",
        "create_auth_schema",
        {
            "role_specification_form": _ROLE_SPEC_VALUES,
            "schema_element_inclusion": _ELEMENT_VALUES,
        },
    ),
    (
        "branch_if_not_exists_named",
        "create_if_not_exists_named",
        {
            "authorization_clause": _AUTHORIZATION_VALUES,
        },
    ),
    (
        "branch_if_not_exists_auth",
        "create_if_not_exists_auth",
        {
            "role_specification_form": _ROLE_SPEC_VALUES,
        },
    ),
)

# One representative (factor, value) per failure cluster.  These are all
# primary T1-T4 axis values crossed in the cartesian product.  Derived
# T5 factors (forward_reference_in_elements, if_not_exists_with_elements)
# are NOT listed — they are never set as primary values in the extension
# (coverage is held by the marginal baseline), so listing them would be
# dead entries that never match.
_CROSSED_NEGATIVES = frozenset(
    {
        ("object_state", "already_exists"),
        ("schema_name_shape", "pg_prefix_reserved"),
        ("owner_name_shape", "non_existing_role"),
        ("privilege_level", "non_creator_no_privilege"),
        ("role_dependency", "cannot_SET_ROLE"),
    }
)

_COMBINATION_GROUP = "create_schema_required_factor_value_matrix"


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

    sb = assignment.get("statement_branch", "branch_named_schema")
    sei = assignment.get("schema_element_inclusion", "without_elements")
    # IF NOT EXISTS branches cannot carry schema elements unless the
    # if_not_exists_with_elements failure is the active scenario.
    if "if_not_exists" in sb and sei != "without_elements":
        if assignment.get("if_not_exists_with_elements") != (
            "if_not_exists_with_schema_elements"
        ):
            return False

    # non_creator privilege must pair with no_CREATE database privilege.
    pl = assignment.get("privilege_level", "superuser")
    dp = assignment.get("database_privilege", "has_CREATE_privilege")
    if pl == "non_creator_no_privilege" and dp != "no_CREATE_privilege":
        return False
    if pl != "non_creator_no_privilege" and dp == "no_CREATE_privilege":
        return False

    # non_existing_role must pair with role_not_exists.
    ons = assignment.get("owner_name_shape", "existing_role")
    rd = assignment.get("role_dependency", "role_exists")
    if ons == "non_existing_role" and rd != "role_not_exists":
        return False
    if ons != "non_existing_role" and rd == "role_not_exists":
        return False

    return _failure_unit_count(assignment) <= 1


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values."""

    sns = a.get("schema_name_shape", "simple")
    if sns == "pg_prefix_reserved":
        a["pg_prefix_name"] = "pg_prefix_schema_name"
    else:
        a["pg_prefix_name"] = "pg_prefix_schema_name"

    os_state = a.get("object_state", "not_exists")
    sb = a.get("statement_branch", "branch_named_schema")
    if os_state == "already_exists" and "if_not_exists" not in sb:
        a["duplicate_schema_name"] = "without_IF_NOT_EXISTS_error"
    elif os_state == "already_exists" and "if_not_exists" in sb:
        a["duplicate_schema_name"] = "with_IF_NOT_EXISTS_noop"
    else:
        a["duplicate_schema_name"] = "with_IF_NOT_EXISTS_noop"

    pl = a.get("privilege_level", "superuser")
    rd = a.get("role_dependency", "role_exists")
    if pl == "non_creator_no_privilege":
        a["insufficient_privilege"] = "no_CREATE_on_database"
    elif rd == "cannot_SET_ROLE":
        a["insufficient_privilege"] = "cannot_SET_ROLE_to_owner"
    else:
        a["insufficient_privilege"] = "no_CREATE_on_database"

    # if_not_exists_with_elements: only meaningful on IF NOT EXISTS
    # branches that carry a schema element.
    sb = a.get("statement_branch", "branch_named_schema")
    sei = a.get("schema_element_inclusion", "without_elements")
    if "if_not_exists" in sb and sei != "without_elements":
        a["if_not_exists_with_elements"] = (
            "if_not_exists_with_schema_elements"
        )

    # forward-reference cluster: schema_element_dependency /
    # forward_reference_in_elements.  A view sub-command referencing a
    # non-existent table triggers 42P01; a plain ``CREATE VIEW v AS
    # SELECT 1`` succeeds.  Neither factor is a primary extension axis,
    # so this cluster is inactive here — forward_reference coverage
    # is held by the marginal baseline (one SFV obligation).
    fre = a.get("forward_reference_in_elements", "")
    sed = a.get("schema_element_dependency", "element_table_exists")
    if fre == "forward_reference_failure" or sed == "element_table_not_exists":
        a["forward_reference_in_elements"] = "forward_reference_failure"
        a["schema_element_dependency"] = "element_table_not_exists"
        a["schema_element_inclusion"] = "with_create_view"

    a["if_not_exists_clause"] = (
        "present" if "if_not_exists" in sb else "absent"
    )
    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _failure_conditions(a: dict[str, str]) -> list[str]:
    """Return the list of active failure condition names."""

    conditions: list[str] = []
    sb = a.get("statement_branch", "branch_named_schema")
    os_state = a.get("object_state", "not_exists")
    if os_state == "already_exists" and "if_not_exists" not in sb:
        conditions.append("duplicate")
    sns = a.get("schema_name_shape", "simple")
    if sns == "pg_prefix_reserved":
        conditions.append("pg_prefix")
    ons = a.get("owner_name_shape", "existing_role")
    rd = a.get("role_dependency", "role_exists")
    if ons == "non_existing_role" or rd == "role_not_exists":
        conditions.append("undefined_role")
    pl = a.get("privilege_level", "superuser")
    if pl == "non_creator_no_privilege":
        conditions.append("insufficient_privilege")
    if rd == "cannot_SET_ROLE":
        conditions.append("cannot_set_role")
    return conditions


_FAILURE_SQLSTATE = {
    "duplicate": ("42710", "duplicate_schema_provisional"),
    "pg_prefix": ("42939", "pg_prefix_reserved_schema_name_provisional"),
    "undefined_role": ("42704", "undefined_role_provisional"),
    "insufficient_privilege": (
        "42501",
        "insufficient_privilege_provisional",
    ),
    "cannot_set_role": ("42501", "insufficient_privilege_provisional"),
}


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments passing the filter, per branch."""

    combos: list[dict[str, str]] = []
    for branch, action, axes in _BRANCH_CONFIG:
        all_axes = dict(_GENERAL_AXES)
        all_axes.update(axes)
        names = list(all_axes)
        for values in itertools.product(*[all_axes[n] for n in names]):
            assignment: dict[str, str] = dict(_BASELINE_DEFAULTS)
            assignment["statement_branch"] = branch
            assignment["grammar_branch"] = branch
            assignment["target_action"] = action
            for name, value in zip(names, values):
                assignment[name] = value
            _derive_overlapping_factors(assignment)
            if not _is_valid_combination(assignment):
                continue
            if len(assignment) != len(set(assignment)):
                raise CreateSchemaFactorExtensionError(
                    "duplicate factor key in extension assignment"
                )
            combos.append(assignment)
    return combos


def _outcome_for(
    assignment: dict[str, str],
) -> tuple[str, str, str | None]:
    conditions = _failure_conditions(assignment)
    if not conditions:
        return "success", "00000", None
    condition = conditions[0]
    sqlstate, reason = _FAILURE_SQLSTATE[condition]
    return "expected_failure", sqlstate, reason


def _extension_multiset_sha256(
    cases: tuple[CreateSchemaFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"create-schema-factor-extension-v1\n")
    for case in cases:
        digest.update(
            json.dumps(
                {
                    "ordinal": case.ordinal,
                    "case_id": case.case_id,
                    "derivation_id": case.derivation_id,
                    "derived_from_combination_group": (
                        case.derived_from_combination_group
                    ),
                    "derivation_reason": case.derivation_reason,
                    "factor_assignment": [
                        list(item) for item in case.factor_assignment
                    ],
                    "consumer_action_id": case.consumer_action_id,
                    "outcome": case.outcome,
                    "expected_sqlstate": case.expected_sqlstate,
                    "expected_failure_reason": (
                        case.expected_failure_reason
                    ),
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        digest.update(b"\n")
    return digest.hexdigest()


def build_create_schema_factor_extension_plan(
    repository_root: Path,
) -> CreateSchemaFactorExtensionPlan:
    """Build the bounded CREATE SCHEMA post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    catalog_rows = load_shipped_applicability_universe(
        root
    ).rows_for_statement("create_schema")
    if len(catalog_rows) != 58:
        raise CreateSchemaFactorExtensionError("catalog row count drift")
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[CreateSchemaFactorExtensionCase] = []
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
                _derive_overlapping_factors(assignment)
                if not _is_valid_combination(assignment):
                    continue
                conditions = _failure_conditions(assignment)
                if len(conditions) > 1:
                    continue
                if conditions:
                    sqlstate, reason = _FAILURE_SQLSTATE[conditions[0]]
                    outcome = "expected_failure"
                else:
                    sqlstate = "00000"
                    reason = None
                    outcome = "success"
                ordinal += 1
                cases.append(
                    CreateSchemaFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"CREATESCHEMA{ordinal:05d}",
                        sql_filename=f"CREATESCHEMA{ordinal:05d}.sql",
                        object_prefix=f"createschema_{ordinal:05d}_",
                        derivation_id=(
                            f"CSCHEMA-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=_COMBINATION_GROUP,
                        derivation_reason=(
                            "cross-factor extension: "
                            f"statement_branch="
                            f"{assignment['statement_branch']} "
                            f"x object_state="
                            f"{assignment['object_state']} "
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
                    )
                )
    dropped = max(0, raw - _CAP)
    cases_tuple = tuple(cases)
    plan = CreateSchemaFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        raw_combination_count=raw,
        dropped_combination_count=dropped,
    )
    expected_min = 1000 - _BASELINE_COUNT
    if len(plan.cases) < expected_min:
        raise CreateSchemaFactorExtensionError(
            f"extension case count below threshold: {len(plan.cases)}"
        )
    if len(plan.cases) > _CAP:
        raise CreateSchemaFactorExtensionError(
            "extension case count exceeds cap"
        )
    ordinals = [case.ordinal for case in plan.cases]
    if ordinals != list(
        range(_BASELINE_COUNT + 1, _BASELINE_COUNT + 1 + len(plan.cases))
    ):
        raise CreateSchemaFactorExtensionError("extension ordinal gap")
    if len({case.case_id for case in plan.cases}) != len(plan.cases):
        raise CreateSchemaFactorExtensionError("duplicate extension case_id")
    if len({case.sql_filename for case in plan.cases}) != len(plan.cases):
        raise CreateSchemaFactorExtensionError(
            "duplicate extension sql_filename"
        )
    if not all(
        case.outcome in ("success", "expected_failure")
        for case in plan.cases
    ):
        raise CreateSchemaFactorExtensionError("unknown extension outcome")
    if not all(
        case.derivation_id.startswith("CSCHEMA-EXT|")
        for case in plan.cases
    ):
        raise CreateSchemaFactorExtensionError(
            "extension derivation_id prefix drift"
        )
    return plan


__all__ = [
    "CreateSchemaFactorExtensionError",
    "CreateSchemaFactorExtensionCase",
    "CreateSchemaFactorExtensionPlan",
    "build_create_schema_factor_extension_plan",
    "_BASELINE_COUNT",
    "_CAP",
    "_VERIFICATION_MODES",
    "_CLEANUP_MODES",
    "_CROSSED_NEGATIVES",
    "_present_failure_pair",
    "_extension_multiset_sha256",
]
