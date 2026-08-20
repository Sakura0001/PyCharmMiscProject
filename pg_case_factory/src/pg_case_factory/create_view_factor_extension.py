"""Bounded post-coverage extension plan for CREATE VIEW factor regress.

The baseline :mod:`create_view_factor_loop` assigns one local SQL program
to every ``SFV``/``GRM`` obligation (marginal 1:1).  This module crosses
the main-axis factor values with verification/cleanup axes under an
at-most-one-failure attribution policy, producing a bounded set of
additional regress programs that exercise pairwise factor interactions.

CREATE VIEW creates a ``pg_class`` relation of kind ``v`` (not a base
table), so the bookend (DROP TABLE IF EXISTS) is never emitted as the
col-0 primary target.  Fixture base tables use ``CREATE TABLE`` in the
setup section and ``DROP TABLE IF EXISTS`` in the cleanup section, which
do not trigger the bookend gate (the gate matches ``CREATE TABLE`` only
when checking first/last segments as the col-0 primary).

The extension is deterministic: given the same repository root, it
always produces the same frozen multiset SHA-256 and the same contiguous
case ordinals starting at ``_BASELINE_COUNT + 1``.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe
from .create_view_factor_loop import (
    _BASELINE_DEFAULTS,
    _SFV_FAILURE_SQLSTATE,
)


class CreateViewFactorExtensionError(ValueError):
    """Raised when CREATE VIEW extension input drifts."""


@dataclass(frozen=True)
class CreateViewFactorExtensionCase:
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
class CreateViewFactorExtensionPlan:
    cases: tuple[CreateViewFactorExtensionCase, ...]
    extension_multiset_sha256: str
    raw_combination_count: int
    dropped_combination_count: int


_BASELINE_COUNT = 71
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_class_query",
    "information_schema_views",
    "select_from_view",
    "error_assertion",
)
_CLEANUP_MODES = (
    "drop_view_if_exists",
    "drop_view_cascade",
    "drop_base_table_cascade",
)

_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "object_state": ("not_exists", "already_exists"),
    "privilege_level": ("owner", "non_owner_no_privilege"),
}

_BRANCH_TEMP_AXES: dict[str, tuple[str, ...]] = {
    "statement_branch": (
        "branch_create_view",
        "branch_create_or_replace_view",
        "branch_create_temp_view",
        "branch_create_recursive_view",
    ),
    "temporary_clause": ("permanent", "temp", "temporary"),
}

_BRANCH_REPLACE_AXES: dict[str, tuple[str, ...]] = {
    "statement_branch": (
        "branch_create_view",
        "branch_create_or_replace_view",
        "branch_create_temp_view",
        "branch_create_recursive_view",
    ),
    "or_replace_clause": ("absent", "present"),
}

_RECURSIVE_COL_AXES: dict[str, tuple[str, ...]] = {
    "recursive_clause": ("absent", "present"),
    "column_name_list": ("absent", "present", "required_for_recursive"),
}

_WITH_CHECK_AXES: dict[str, tuple[str, ...]] = {
    "with_options_clause": (
        "absent",
        "security_barrier",
        "security_invoker",
        "check_option",
        "multiple_options",
    ),
    "check_option_clause": ("absent", "cascaded", "local"),
}

_NAME_AXES: dict[str, tuple[str, ...]] = {
    "view_name_shape": (
        "simple",
        "quoted",
        "reserved_word",
        "schema_qualified",
        "duplicate",
    ),
    "column_name_shape": ("simple", "quoted", "reserved_word"),
}

_QUERY_TYPE_AXES: dict[str, tuple[str, ...]] = {
    "query_shape": (
        "select_simple",
        "select_with_where",
        "select_with_join",
        "select_with_aggregate",
        "values_clause",
        "select_with_expression",
        "merge_updatable_view",
    ),
    "base_table_coverage": (
        "representative_int_types",
        "representative_string_types",
        "representative_datetime_types",
        "representative_numeric_types",
        "representative_json_types",
        "representative_boolean_types",
    ),
}

_DEPENDENCY_AXES: dict[str, tuple[str, ...]] = {
    "dependency_state": (
        "base_table_exists",
        "referenced_view_exists",
        "base_table_not_exists",
        "referenced_view_not_exists",
    ),
}

_BRANCH_QUERY_AXES: dict[str, tuple[str, ...]] = {
    "statement_branch": (
        "branch_create_view",
        "branch_create_or_replace_view",
        "branch_create_temp_view",
        "branch_create_recursive_view",
    ),
    "query_shape": (
        "select_simple",
        "select_with_where",
        "select_with_join",
        "select_with_aggregate",
        "values_clause",
        "select_with_expression",
        "merge_updatable_view",
    ),
}

_TEMP_NAME_AXES: dict[str, tuple[str, ...]] = {
    "temporary_clause": ("permanent", "temp", "temporary"),
    "view_name_shape": (
        "simple",
        "quoted",
        "reserved_word",
        "schema_qualified",
        "duplicate",
    ),
}

_RECURSIVE_CHECK_AXES: dict[str, tuple[str, ...]] = {
    "recursive_clause": ("absent", "present"),
    "check_option_clause": ("absent", "cascaded", "local"),
}

_TEMP_REPLACE_AXES: dict[str, tuple[str, ...]] = {
    "temporary_clause": ("permanent", "temp", "temporary"),
    "or_replace_clause": ("absent", "present"),
}

_BRANCH_WITH_AXES: dict[str, tuple[str, ...]] = {
    "statement_branch": (
        "branch_create_view",
        "branch_create_or_replace_view",
        "branch_create_temp_view",
        "branch_create_recursive_view",
    ),
    "with_options_clause": (
        "absent",
        "security_barrier",
        "security_invoker",
        "check_option",
        "multiple_options",
    ),
}

_QUERY_NAME_AXES: dict[str, tuple[str, ...]] = {
    "query_shape": (
        "select_simple",
        "select_with_where",
        "select_with_join",
        "select_with_aggregate",
        "values_clause",
        "select_with_expression",
        "merge_updatable_view",
    ),
    "view_name_shape": (
        "simple",
        "quoted",
        "reserved_word",
        "schema_qualified",
        "duplicate",
    ),
}

_TYPE_COLNAME_AXES: dict[str, tuple[str, ...]] = {
    "base_table_coverage": (
        "representative_int_types",
        "representative_string_types",
        "representative_datetime_types",
        "representative_numeric_types",
        "representative_json_types",
        "representative_boolean_types",
    ),
    "column_name_shape": ("simple", "quoted", "reserved_word"),
}

_WITH_COLNAME_AXES: dict[str, tuple[str, ...]] = {
    "with_options_clause": (
        "absent",
        "security_barrier",
        "security_invoker",
        "check_option",
        "multiple_options",
    ),
    "column_name_list": ("absent", "present", "required_for_recursive"),
}

# Representative failure (factor, value) pairs — one per failure scenario.
# Overlapping error_boundary values are derived, not crossed, so they are
# NOT listed here (would double-count a single failure and break
# attribution).  view_name_shape=duplicate overlaps with
# object_state=already_exists (the duplicate cluster derives both), so
# both are listed but the at-most-one-failure filter drops combinations
# where both end up present after derivation.
_CROSSED_NEGATIVES = frozenset(
    {
        ("object_state", "already_exists"),
        ("privilege_level", "non_owner_no_privilege"),
        ("view_name_shape", "duplicate"),
        ("dependency_state", "base_table_not_exists"),
        ("dependency_state", "referenced_view_not_exists"),
    }
)

_COMBINATION_GROUP = "create_view_required_factor_value_matrix"

_CONSUMER_ACTION = "define_view"


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

    rc = assignment.get("recursive_clause")
    cnl = assignment.get("column_name_list")
    co = assignment.get("check_option_clause")

    # recursive consistency — when recursive is present, the derivation
    # forces column_name_list=required_for_recursive and
    # check_option_clause=absent for the success path.  An explicit
    # (recursive=present, column_list=absent) or (recursive=present,
    # check_option!=absent) combo would be silently overridden, so
    # drop it to avoid attributing a failure case as success.
    if rc == "present":
        if cnl == "absent":
            return False
        if co is not None and co != "absent":
            return False

    return _failure_unit_count(assignment) <= 1


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive overlapping boundary factors and expected_status from values.

    Mirrors the baseline derivation in create_view_factor_loop.
    """

    eb = a.get("error_boundary", "none")

    if eb == "duplicate_without_or_replace":
        a["object_state"] = "already_exists"
        a["view_name_shape"] = "duplicate"
        a["or_replace_clause"] = "absent"
        a["recursive_clause"] = "absent"
    elif eb == "or_replace_column_mismatch":
        a["object_state"] = "already_exists"
        a["view_name_shape"] = "duplicate"
        a["or_replace_clause"] = "present"
        a["recursive_clause"] = "absent"
    elif eb == "recursive_without_column_list":
        a["recursive_clause"] = "present"
        a["column_name_list"] = "absent"
        a["check_option_clause"] = "absent"
        a["statement_branch"] = "branch_create_recursive_view"
    elif eb == "check_option_on_recursive":
        a["recursive_clause"] = "present"
        a["column_name_list"] = "required_for_recursive"
        a["check_option_clause"] = "cascaded"
        a["statement_branch"] = "branch_create_recursive_view"
    elif eb == "base_table_not_exists":
        a["dependency_state"] = "base_table_not_exists"
        a["recursive_clause"] = "absent"
    elif eb == "insufficient_privilege":
        a["privilege_level"] = "non_owner_no_privilege"
        a["recursive_clause"] = "absent"
    elif eb == "merge_view_with_rules":
        a["recursive_clause"] = "absent"

    os_state = a.get("object_state", "not_exists")
    vns = a.get("view_name_shape", "simple")
    if os_state == "already_exists" or vns == "duplicate":
        a["object_state"] = "already_exists"
        a["view_name_shape"] = "duplicate"
        if a.get("error_boundary", "none") == "none":
            a["error_boundary"] = "duplicate_without_or_replace"
        if a.get("or_replace_clause", "absent") != "present":
            a["or_replace_clause"] = "absent"
        a["recursive_clause"] = "absent"

    rc = a.get("recursive_clause", "absent")
    if rc == "present":
        if a.get("error_boundary", "none") == "none":
            a["column_name_list"] = "required_for_recursive"
            a["check_option_clause"] = "absent"
            a["statement_branch"] = "branch_create_recursive_view"

    ds = a.get("dependency_state", "base_table_exists")
    if ds in ("base_table_not_exists", "referenced_view_not_exists"):
        if a.get("error_boundary", "none") == "none":
            a["error_boundary"] = "base_table_not_exists"
        a["recursive_clause"] = "absent"

    pl = a.get("privilege_level", "owner")
    if pl == "non_owner_no_privilege":
        if a.get("error_boundary", "none") == "none":
            a["error_boundary"] = "insufficient_privilege"
        a["recursive_clause"] = "absent"

    if (
        a.get("expected_status") == "failure"
        and a.get("error_boundary", "none") == "none"
    ):
        a["object_state"] = "already_exists"
        a["view_name_shape"] = "duplicate"
        a["error_boundary"] = "duplicate_without_or_replace"
        a["or_replace_clause"] = "absent"
        a["recursive_clause"] = "absent"

    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _behavior_combinations(
    axes: dict[str, tuple[str, ...]],
) -> list[dict[str, str]]:
    """Cartesian product of given axes, filtered by consistency."""

    keys = list(axes.keys())
    value_lists = [axes[k] for k in keys]
    combos: list[dict[str, str]] = []
    for values in itertools.product(*value_lists):
        assignment = dict(zip(keys, values))
        if _is_valid_combination(assignment):
            combos.append(assignment)
    return combos


def _full_assignment(
    behavior: dict[str, str],
    verification: str,
    cleanup: str,
) -> dict[str, str]:
    a: dict[str, str] = dict(_BASELINE_DEFAULTS)
    for key, value in behavior.items():
        a[key] = value
    a["verification_mode"] = verification
    a["cleanup_mode"] = cleanup
    _derive_overlapping_factors(a)
    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"
    return a


def _outcome_for(
    assignment: dict[str, str],
) -> tuple[str, str, str | None]:
    pair = _present_failure_pair(assignment)
    if pair is None:
        return "success", "00000", None
    sqlstate, reason = _SFV_FAILURE_SQLSTATE[pair]
    return "expected_failure", sqlstate, reason


def _extension_multiset_sha256(
    cases: tuple[CreateViewFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"create-view-factor-extension-v1\n")
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


def build_create_view_factor_extension_plan(
    repository_root: Path,
) -> CreateViewFactorExtensionPlan:
    """Build the bounded post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    catalog_rows = load_shipped_applicability_universe(
        root
    ).rows_for_statement("create_view")
    if len(catalog_rows) != 70:
        raise CreateViewFactorExtensionError("catalog row count drift")

    cases: list[CreateViewFactorExtensionCase] = []
    raw_count = 0
    ordinal = _BASELINE_COUNT

    cross_groups: list[tuple[str, dict[str, tuple[str, ...]]]] = [
        ("branch_temp", _BRANCH_TEMP_AXES),
        ("branch_replace", _BRANCH_REPLACE_AXES),
        ("recursive_col", _RECURSIVE_COL_AXES),
        ("with_check", _WITH_CHECK_AXES),
        ("name_shape", _NAME_AXES),
        ("query_type", _QUERY_TYPE_AXES),
        ("dependency", _DEPENDENCY_AXES),
        ("branch_query", _BRANCH_QUERY_AXES),
        ("temp_name", _TEMP_NAME_AXES),
        ("recursive_check", _RECURSIVE_CHECK_AXES),
        ("temp_replace", _TEMP_REPLACE_AXES),
        ("branch_with", _BRANCH_WITH_AXES),
        ("query_name", _QUERY_NAME_AXES),
        ("type_colname", _TYPE_COLNAME_AXES),
        ("with_colname", _WITH_COLNAME_AXES),
    ]

    for group_name, behavior_axes in cross_groups:
        all_axes = dict(_GENERAL_AXES)
        all_axes.update(behavior_axes)
        behavior_combos = _behavior_combinations(all_axes)
        for behavior in behavior_combos:
            for verification in _VERIFICATION_MODES:
                for cleanup in _CLEANUP_MODES:
                    raw_count += 1
                    full = _full_assignment(
                        behavior, verification, cleanup
                    )
                    if not _is_valid_combination(full):
                        continue
                    if len(full) != len(set(full)):
                        raise CreateViewFactorExtensionError(
                            "duplicate factor key in assignment"
                        )
                    outcome, sqlstate, reason = _outcome_for(full)
                    ordinal += 1
                    sorted_assignment = tuple(sorted(full.items()))
                    derivation_id = (
                        f"CV-EXT|{ordinal:05d}|"
                        f"{verification}|{cleanup}|{group_name}"
                    )
                    cases.append(
                        CreateViewFactorExtensionCase(
                            ordinal=ordinal,
                            case_id=f"CREATEVIEW{ordinal:05d}",
                            sql_filename=(
                                f"CREATEVIEW{ordinal:05d}.sql"
                            ),
                            object_prefix=(
                                f"createview_{ordinal:05d}_"
                            ),
                            derivation_id=derivation_id,
                            derived_from_combination_group=(
                                _COMBINATION_GROUP
                            ),
                            derivation_reason=(
                                f"CREATE VIEW extension: "
                                f"group={group_name}, "
                                f"verification={verification}, "
                                f"cleanup={cleanup}"
                            ),
                            factor_assignment=sorted_assignment,
                            consumer_action_id=_CONSUMER_ACTION,
                            outcome=outcome,
                            expected_sqlstate=sqlstate,
                            expected_failure_reason=reason,
                        )
                    )

    dropped = max(0, raw_count - _CAP)
    if dropped > 0:
        cases = cases[: _CAP]

    plan = CreateViewFactorExtensionPlan(
        cases=tuple(cases),
        extension_multiset_sha256=_extension_multiset_sha256(
            tuple(cases)
        ),
        raw_combination_count=raw_count,
        dropped_combination_count=dropped,
    )

    expected_min = 1000 - _BASELINE_COUNT
    if len(plan.cases) < expected_min:
        raise CreateViewFactorExtensionError(
            f"extension case count below threshold: {len(plan.cases)}"
        )
    if len(plan.cases) > _CAP:
        raise CreateViewFactorExtensionError(
            "extension case count exceeds cap"
        )
    ordinals = [case.ordinal for case in plan.cases]
    expected_ordinals = list(
        range(
            _BASELINE_COUNT + 1,
            _BASELINE_COUNT + 1 + len(plan.cases),
        )
    )
    if ordinals != expected_ordinals:
        raise CreateViewFactorExtensionError("extension ordinal gap")
    if (
        len({case.case_id for case in plan.cases})
        != len(plan.cases)
    ):
        raise CreateViewFactorExtensionError(
            "duplicate extension case_id"
        )
    if (
        len({case.sql_filename for case in plan.cases})
        != len(plan.cases)
    ):
        raise CreateViewFactorExtensionError(
            "duplicate extension sql_filename"
        )
    if not all(
        case.outcome in ("success", "expected_failure")
        for case in plan.cases
    ):
        raise CreateViewFactorExtensionError("unknown extension outcome")
    if not all(
        case.derivation_id.startswith("CV-EXT|")
        for case in plan.cases
    ):
        raise CreateViewFactorExtensionError(
            "extension derivation_id prefix drift"
        )
    return plan


__all__ = [
    "CreateViewFactorExtensionError",
    "CreateViewFactorExtensionCase",
    "CreateViewFactorExtensionPlan",
    "build_create_view_factor_extension_plan",
    "_BASELINE_COUNT",
    "_CAP",
    "_VERIFICATION_MODES",
    "_CLEANUP_MODES",
    "_CROSSED_NEGATIVES",
    "_present_failure_pair",
    "_extension_multiset_sha256",
]
