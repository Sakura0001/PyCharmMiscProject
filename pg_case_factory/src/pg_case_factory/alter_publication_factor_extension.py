"""Bounded post-coverage cross-factor extension expander for ALTER PUBLICATION.

The marginal factor-value-loop (:mod:`alter_publication_factor_loop`) is the
required baseline: one program per factor value, 93 local cases
(GRM 26 + SFV 65 + RISK 2).  This module adds the bounded post-coverage
extension phase allowed by ``alter_publication.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor combinations
of the positive T1-T4 behaviour axes (at most one failure-causing value per
case, so attribution stays clean), with ``verification_mode`` crossed and
``cleanup_mode`` crossed so every declared T6 value is exercised.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``derived_extension_required_fields``) and is marked ``is_extension = True``.

SESSION_USER owner-transfer no-op: ``OWNER TO SESSION_USER`` is a permitted
no-op transfer (PG 18.4 allows it even for non-owners), so the privilege
boundary does not fire for ``owner_to_clause = session_user_keyword``.  Under
a non-superuser publication owner, OWNER TO with an explicit role or
CURRENT_ROLE / CURRENT_USER fails 42501 (requires superuser); only
``session_user_keyword`` escapes (the membership wall is excluded for it).
Under ``non_owner_no_privilege`` the privilege cluster (42501) fires for
every branch except the SESSION_USER owner-transfer escape.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .alter_publication_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_alter_publication_factor_loop_plan,
)


class AlterPublicationFactorExtensionError(ValueError):
    """Raised when a frozen ALTER PUBLICATION extension input drifts."""


@dataclass(frozen=True)
class AlterPublicationFactorExtensionCase:
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
class AlterPublicationFactorExtensionPlan:
    cases: tuple[AlterPublicationFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 93
# Safety backstop only; the natural at-most-one-failure cross is expected to
# stay well under this cap so no coverage-losing truncation occurs.  The
# exact frozen count is asserted in the companion test.
_CAP = 50000

_VERIFICATION_MODES = (
    "pg_publication_catalog",
    "pg_publication_tables_catalog",
    "error_assertion",
)
_CLEANUP_MODES = (
    "drop_publication",
)

_BRANCH_ADD = "branch_add"
_BRANCH_SET_OBJECT = "branch_set_object"
_BRANCH_DROP = "branch_drop"
_BRANCH_SET_PARAMETER = "branch_set_parameter"
_BRANCH_OWNER_TO = "branch_owner_to"
_BRANCH_RENAME = "branch_rename"

_TABLE_OPERATIONS = frozenset(
    {"add_table", "set_table", "drop_table"}
)
_SCHEMA_OPERATIONS = frozenset(
    {"add_tables_in_schema", "set_tables_in_schema", "drop_tables_in_schema"}
)

# Privilege cluster: the non-owner privilege level models the
# must_be_owner_of_publication (42501) boundary and is counted as a single
# attributable failure unit.
_PRIVILEGE_CLUSTER_VALUES = frozenset({"non_owner_no_privilege"})
# SESSION_USER is a permitted no-op transfer (PG 18.4 allows even for
# non-owners), so it escapes the privilege boundary.  Only the explicit role
# and CURRENT_ROLE / CURRENT_USER require superuser under the publication
# owner (the membership wall).
_SESSION_USER_ESCAPE = "session_user_keyword"
_OWNER_TARGET_REQUIRES_MEMBERSHIP = frozenset(
    {"explicit_role_name", "current_role_keyword", "current_user_keyword"}
)

# Dense baseline assignment (all positive T1-T4 + T6 + GRM-axis baselines).
# The T5 negative factors are intentionally absent: they are owned
# one-per-value by the marginal baseline and are never crossed here, so the
# at-most-one-failure attribution stays clean.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_add",
    "grammar_branch": "branch_add",
    "target_action": "add_object",
    "publication_state": "exists",
    "expected_status": "success",
    "add_set_drop_operation": "add_table",
    "publication_parameter": "publish_insert_only",
    "owner_to_clause": "explicit_role_name",
    "column_filter": "no_column_filter",
    "where_clause": "no_where",
    "publication_name_shape": "simple_name",
    "table_name_shape": "simple_name",
    "schema_name_shape": "simple_name",
    "new_name_shape": "simple_name",
    "new_owner_shape": "existing_role",
    "executor_privilege": "superuser",
    "table_dependency": "table_exists",
    "schema_dependency": "schema_exists",
    "verification_mode": "pg_publication_catalog",
    "cleanup_mode": "drop_publication",
    "only_keyword": "absent",
    "star_marker": "absent",
    "object_list_cardinality": "one_object",
    "parameter_assignment_form": "equals_value",
}

# Official synopsis branch -> grammar_branch id used by the renderer.
_BRANCH_GRAMMAR = {
    "branch_add": "branch_add",
    "branch_set_object": "branch_set_object",
    "branch_drop": "branch_drop",
    "branch_set_parameter": "branch_set_parameter",
    "branch_owner_to": "branch_owner_to",
    "branch_rename": "branch_rename",
}

# Fixed consumer action for every branch (the add_set_drop_operation factor
# selects the operation variant but the consumer action is the branch itself).
_BRANCH_FIXED_ACTION = {
    "branch_add": "add_object",
    "branch_set_object": "set_object",
    "branch_drop": "drop_object",
    "branch_set_parameter": "set_parameter",
    "branch_owner_to": "owner",
    "branch_rename": "rename",
}

# Crossed positive behaviour axes per branch.
_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_add": {
        "add_set_drop_operation": (
            "add_table",
            "add_tables_in_schema",
        ),
        "publication_state": (
            "exists",
            "non_existent",
            "exists_as_for_all_tables",
            "exists_with_tables",
        ),
        "table_dependency": ("table_exists", "table_not_exists"),
        "schema_dependency": ("schema_exists", "schema_not_exists"),
        "column_filter": (
            "no_column_filter",
            "single_column_filter",
            "multiple_column_filter",
        ),
        "where_clause": ("no_where", "simple_where_condition"),
        "publication_name_shape": (
            "simple_name",
            "quoted_name",
            "non_existent_name",
        ),
        "table_name_shape": (
            "simple_name",
            "schema_qualified_name",
            "quoted_name",
            "nonexistent_table",
        ),
        "schema_name_shape": (
            "simple_name",
            "current_schema_keyword",
            "quoted_name",
            "nonexistent_schema",
        ),
        "executor_privilege": (
            "superuser",
            "owner_of_publication",
            "non_owner_no_privilege",
        ),
    },
    "branch_set_object": {
        "add_set_drop_operation": (
            "set_table",
            "set_tables_in_schema",
        ),
        "publication_state": (
            "exists",
            "non_existent",
            "exists_as_for_all_tables",
            "exists_with_tables",
        ),
        "table_dependency": ("table_exists", "table_not_exists"),
        "schema_dependency": ("schema_exists", "schema_not_exists"),
        "column_filter": (
            "no_column_filter",
            "single_column_filter",
            "multiple_column_filter",
        ),
        "where_clause": ("no_where", "simple_where_condition"),
        "publication_name_shape": (
            "simple_name",
            "quoted_name",
            "non_existent_name",
        ),
        "table_name_shape": (
            "simple_name",
            "schema_qualified_name",
            "quoted_name",
            "nonexistent_table",
        ),
        "schema_name_shape": (
            "simple_name",
            "current_schema_keyword",
            "quoted_name",
            "nonexistent_schema",
        ),
        "executor_privilege": (
            "superuser",
            "owner_of_publication",
            "non_owner_no_privilege",
        ),
    },
    "branch_drop": {
        "add_set_drop_operation": (
            "drop_table",
            "drop_tables_in_schema",
        ),
        "publication_state": (
            "exists",
            "non_existent",
            "exists_as_for_all_tables",
            "exists_with_tables",
        ),
        "table_dependency": ("table_exists", "table_not_exists"),
        "schema_dependency": ("schema_exists", "schema_not_exists"),
        "publication_name_shape": (
            "simple_name",
            "quoted_name",
            "non_existent_name",
        ),
        "table_name_shape": (
            "simple_name",
            "schema_qualified_name",
            "quoted_name",
            "nonexistent_table",
        ),
        "schema_name_shape": (
            "simple_name",
            "current_schema_keyword",
            "quoted_name",
            "nonexistent_schema",
        ),
        "executor_privilege": (
            "superuser",
            "owner_of_publication",
            "non_owner_no_privilege",
        ),
    },
    "branch_set_parameter": {
        "publication_parameter": (
            "publish_insert_only",
            "publish_all_operations",
            "publish_via_partition_root",
            "multiple_parameters",
        ),
        "publication_state": (
            "exists",
            "non_existent",
            "exists_as_for_all_tables",
            "exists_with_tables",
        ),
        "publication_name_shape": (
            "simple_name",
            "quoted_name",
            "non_existent_name",
        ),
        "executor_privilege": (
            "superuser",
            "owner_of_publication",
            "non_owner_no_privilege",
        ),
    },
    "branch_owner_to": {
        "owner_to_clause": (
            "explicit_role_name",
            "current_role_keyword",
            "current_user_keyword",
            "session_user_keyword",
        ),
        "new_owner_shape": ("existing_role", "nonexistent_role"),
        "publication_state": (
            "exists",
            "non_existent",
            "exists_as_for_all_tables",
            "exists_with_tables",
        ),
        "publication_name_shape": (
            "simple_name",
            "quoted_name",
            "non_existent_name",
        ),
        "executor_privilege": (
            "superuser",
            "owner_of_publication",
            "non_owner_no_privilege",
        ),
    },
    "branch_rename": {
        "new_name_shape": (
            "simple_name",
            "quoted_name",
            "existing_name_conflict",
        ),
        "publication_state": (
            "exists",
            "non_existent",
            "exists_as_for_all_tables",
            "exists_with_tables",
        ),
        "publication_name_shape": (
            "simple_name",
            "quoted_name",
            "non_existent_name",
        ),
        "executor_privilege": (
            "superuser",
            "owner_of_publication",
            "non_owner_no_privilege",
        ),
    },
}

# Crossed behaviour-negative (factor, value) pairs.  The privilege cluster
# (executor_privilege=non_owner_no_privilege) is counted as a single unit
# via _PRIVILEGE_CLUSTER_VALUES and is therefore not duplicated here.
_CROSSED_BEHAVIOUR_NEGATIVES = frozenset(
    {
        ("publication_state", "non_existent"),
        ("publication_state", "exists_as_for_all_tables"),
        ("table_dependency", "table_not_exists"),
        ("schema_dependency", "schema_not_exists"),
        ("table_name_shape", "nonexistent_table"),
        ("schema_name_shape", "nonexistent_schema"),
        ("publication_name_shape", "non_existent_name"),
        ("new_owner_shape", "nonexistent_role"),
        ("new_name_shape", "existing_name_conflict"),
    }
)


def _owner_privilege_failure(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """The superuser-only owner-transfer wall firing here, else None.

    Under ``owner_of_publication`` (a non-superuser owner), OWNER TO with an
    explicit role or CURRENT_ROLE / CURRENT_USER requires superuser and
    surfaces 42501 before the action takes effect.  SESSION_USER is a
    permitted no-op transfer and does NOT fire this wall.  Only
    ``owner_of_publication`` is reachable: the non_owner cluster already
    attributes 42501 and superuser passes, so neither adds this unit.
    Co-occurrence with a behaviour-negative is excluded by the at-most-one
    rule (the shadowed negative is never reached), so the kept cases carry
    this as the sole failure unit.
    """

    if assignment.get("executor_privilege") != "owner_of_publication":
        return None
    # owner_to_clause is crossed only in branch_owner_to; in the other
    # branches it holds its baseline value, so scoping the membership check
    # on target_action ("owner") keeps it from firing on unrelated branches.
    target_action = assignment.get("target_action")
    if (
        target_action == "owner"
        and assignment.get("owner_to_clause") in _OWNER_TARGET_REQUIRES_MEMBERSHIP
    ):
        return ("owner_to_clause", "membership_required_under_owner")
    return None


def _privilege_cluster_fires(assignment: dict[str, str]) -> bool:
    """The privilege wall firing for non-owners, EXCEPT SESSION_USER.

    SESSION_USER is a permitted no-op transfer (PG 18.4 allows even for
    non-owners), so the privilege boundary does not fire when
    ``owner_to_clause = session_user_keyword``.  In branches other than
    branch_owner_to, ``owner_to_clause`` holds its baseline value
    (``explicit_role_name``), so the escape only applies to the
    owner-transfer branch where it is crossed.
    """

    level = assignment.get("executor_privilege")
    if level not in _PRIVILEGE_CLUSTER_VALUES:
        return False
    if assignment.get("owner_to_clause") == _SESSION_USER_ESCAPE:
        return False
    return True


def _is_table_op(assignment: dict[str, str]) -> bool:
    return assignment.get("add_set_drop_operation") in _TABLE_OPERATIONS


def _is_schema_op(assignment: dict[str, str]) -> bool:
    return assignment.get("add_set_drop_operation") in _SCHEMA_OPERATIONS


def _applicable_negative(
    factor: str, value: str, assignment: dict[str, str]
) -> bool:
    """Whether a crossed behaviour-negative actually fires for this case."""

    if assignment.get(factor) != value:
        return False
    branch = assignment.get("grammar_branch")
    # exists_as_for_all_tables only fails on the DROP branch; on ADD / SET it
    # is a valid success (the publication exists and is alterable).
    if (factor, value) == ("publication_state", "exists_as_for_all_tables"):
        return branch == _BRANCH_DROP
    # Table negatives only apply to TABLE operations; schema negatives only
    # to TABLES-IN-SCHEMA operations.  In the non-object branches these
    # factors hold positive baseline values so they never fire here.
    if factor in ("table_dependency", "table_name_shape"):
        return _is_table_op(assignment)
    if factor in ("schema_dependency", "schema_name_shape"):
        return _is_schema_op(assignment)
    return True


def _failure_unit_count(assignment: dict[str, str]) -> int:
    """Privilege cluster (1) + owner-privilege wall (1) + behaviour negatives.

    The privilege cluster (non_owner_no_privilege) and the owner-privilege
    wall (owner_of_publication + role-membership) are mutually exclusive -- a
    case has exactly one executor_privilege -- so the two never double-count.
    """

    cluster = 1 if _privilege_cluster_fires(assignment) else 0
    owner_priv = 1 if _owner_privilege_failure(assignment) else 0
    negatives = sum(
        1
        for factor, value in _CROSSED_BEHAVIOUR_NEGATIVES
        if _applicable_negative(factor, value, assignment)
    )
    return cluster + owner_priv + negatives


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success.

    The owner-privilege wall (superuser-only transfer) fires before the
    action takes effect, so it is attributed first when present (it shadows
    any co-occurring behaviour-negative, which the at-most-one rule has
    already excluded from the kept set).
    """

    pair = _owner_privilege_failure(assignment)
    if pair is not None:
        return pair
    if _privilege_cluster_fires(assignment):
        level = assignment.get("executor_privilege")
        return ("executor_privilege", level)
    for neg_factor, neg_value in _CROSSED_BEHAVIOUR_NEGATIVES:
        if _applicable_negative(neg_factor, neg_value, assignment):
            return (neg_factor, neg_value)
    return None


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    """Branch-local applicability + at-most-one-failure attribution."""

    # TABLES-IN-SCHEMA operations do not reference a table: column lists,
    # WHERE filters, table-dependency and table-name-shape negatives are
    # semantically invalid here (the table object is never named).
    if _is_schema_op(assignment):
        if assignment.get("column_filter") != "no_column_filter":
            return False
        if assignment.get("where_clause") != "no_where":
            return False
        if assignment.get("table_dependency") == "table_not_exists":
            return False
        if assignment.get("table_name_shape") == "nonexistent_table":
            return False
    # TABLE operations do not reference a schema: schema-dependency and
    # schema-name-shape negatives are semantically invalid here.
    if _is_table_op(assignment):
        if assignment.get("schema_dependency") == "schema_not_exists":
            return False
        if assignment.get("schema_name_shape") == "nonexistent_schema":
            return False
    return _failure_unit_count(assignment) <= 1


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments (T6 at baseline) passing the filter."""

    combos: list[dict[str, str]] = []
    for branch, axes in _BRANCH_AXES.items():
        names = list(axes)
        for values in itertools.product(*(axes[name] for name in names)):
            assignment: dict[str, str] = dict(_BASELINE_DEFAULTS)
            assignment["statement_branch"] = branch
            assignment["grammar_branch"] = _BRANCH_GRAMMAR[branch]
            assignment["target_action"] = _BRANCH_FIXED_ACTION[branch]
            for name, value in zip(names, values):
                assignment[name] = value
            if not _is_valid_combination(assignment):
                continue
            unit = _failure_unit_count(assignment)
            assignment["expected_status"] = (
                "failure" if unit == 1 else "success"
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
    cases: tuple[AlterPublicationFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"alter-publication-factor-extension-v1\n")
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
    cases: tuple[AlterPublicationFactorExtensionCase, ...],
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
                    f"ALTER PUBLICATION extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "alter_publication_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": case.outcome == "expected_failure",
                },
                "sql_shape": {
                    "target": "ALTER PUBLICATION",
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


def build_alter_publication_factor_extension_plan(
    repository_root: Path,
) -> AlterPublicationFactorExtensionPlan:
    """Build the bounded ALTER PUBLICATION post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_alter_publication_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    # Stable sort so any cap truncation is deterministic and interleaves
    # branches rather than favouring the first branch.
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[AlterPublicationFactorExtensionCase] = []
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
                    AlterPublicationFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"ALTERPUBLICATION{ordinal:05d}",
                        sql_filename=f"ALTERPUBLICATION{ordinal:05d}.sql",
                        object_prefix=f"alterpublication_{ordinal:05d}_",
                        derivation_id=(
                            f"ALTPUB-EXT|{ordinal:05d}|{action}"
                            f"|{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "alter_publication_required_baseline_factor_space"
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
    return AlterPublicationFactorExtensionPlan(
        cases=cases_tuple,
        extension_multiset_sha256=_extension_multiset_sha256(cases_tuple),
        derived_combinations_yaml=_derived_combinations_yaml(cases_tuple),
        dropped_count=dropped,
        raw_combination_count=raw,
    )


__all__ = [
    "AlterPublicationFactorExtensionError",
    "AlterPublicationFactorExtensionCase",
    "AlterPublicationFactorExtensionPlan",
    "build_alter_publication_factor_extension_plan",
]
