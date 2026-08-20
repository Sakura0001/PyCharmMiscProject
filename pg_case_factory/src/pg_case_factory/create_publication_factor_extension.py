"""Bounded post-coverage extension plan for CREATE PUBLICATION factor regress.

The baseline :mod:`create_publication_factor_loop` assigns one local SQL
program to every ``SFV``/``GRM`` obligation (marginal 1:1).  This module
crosses the main-axis factor values with verification/cleanup axes under
an at-most-one-failure attribution policy, producing a bounded set of
additional regress programs that exercise pairwise factor interactions.

CREATE PUBLICATION is a catalog row DDL statement — it does not create
tables, so the bookend (DROP TABLE IF EXISTS) is never emitted.  The
``pg_catalog.pg_publication`` catalog row (not a ``pg_class`` relation) is
the semantic witness target.

The extension is deterministic: given the same repository root, it always
produces the same frozen multiset SHA-256 and the same contiguous case
ordinals starting at ``_BASELINE_COUNT + 1``.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe
from .create_publication_factor_loop import (
    _BASELINE_DEFAULTS,
    _FOR_CLAUSE_TO_BRANCH,
    _SFV_FAILURE_VALUES,
)


class CreatePublicationFactorExtensionError(ValueError):
    """Raised when CREATE PUBLICATION extension input drifts."""


@dataclass(frozen=True)
class CreatePublicationFactorExtensionCase:
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
class CreatePublicationFactorExtensionPlan:
    cases: tuple[CreatePublicationFactorExtensionCase, ...]
    extension_multiset_sha256: str
    raw_combination_count: int
    dropped_combination_count: int


_BASELINE_COUNT = 72
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_publication_catalog",
    "pg_publication_tables_catalog",
    "error_assertion",
)
_CLEANUP_MODES = ("DROP_PUBLICATION", "DROP_PUBLICATION_IF_EXISTS")

_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "publication_identity": ("not_exists", "exists"),
    "with_parameter_clause": (
        "omitted",
        "publish_insert_only",
        "publish_all_operations",
        "publish_via_partition_root",
        "multiple_parameters",
    ),
    "executor_privilege": ("superuser", "non_superuser"),
}

_FOR_TABLE_AXES: dict[str, tuple[str, ...]] = {
    "column_filter": (
        "no_column_filter",
        "single_column_filter",
        "multiple_column_filter",
    ),
    "where_clause": (
        "no_where",
        "simple_where_condition",
        "complex_where_expression",
    ),
    "only_keyword": ("without_only", "with_only"),
    "table_dependency": ("table_exists", "table_not_exists", "partition_table"),
}

_FOR_SCHEMA_AXES: dict[str, tuple[str, ...]] = {
    "schema_name_shape": (
        "simple_name",
        "quoted_name",
        "current_schema_keyword",
        "nonexistent_schema",
    ),
    "schema_dependency": ("schema_exists", "schema_not_exists"),
}

_CROSSED_NEGATIVES = frozenset(
    {
        ("publication_identity", "exists"),
        ("executor_privilege", "non_superuser"),
        ("table_dependency", "table_not_exists"),
        ("schema_dependency", "schema_not_exists"),
        ("schema_name_shape", "nonexistent_schema"),
    }
)

_COMBINATION_GROUP = "create_publication_required_factor_value_matrix"

_CONSUMER_ACTION = {
    "for_all_tables": "for_all_tables",
    "for_table": "for_table",
    "for_tables_in_schema": "for_tables_in_schema",
    "no_for": "no_for",
}


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    """Consistency + at-most-one-failure attribution."""

    failures = [
        pair
        for pair in _CROSSED_NEGATIVES
        if assignment.get(pair[0]) == pair[1]
    ]
    return len(failures) <= 1


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors from T1-T4 values in extension."""

    # statement_branch <-> for_clause_shape
    fcs = a.get("for_clause_shape", "for_all_tables")
    if fcs in _FOR_CLAUSE_TO_BRANCH:
        a["statement_branch"] = _FOR_CLAUSE_TO_BRANCH[fcs]

    pi = a.get("publication_identity", "not_exists")
    if pi in ("exists", "quoted_duplicate"):
        a["duplicate_publication_name"] = "same_name_exists"

    ep = a.get("executor_privilege", "superuser")
    if ep == "non_superuser":
        a["privilege_insufficient"] = "non_superuser_creating_publication"

    td = a.get("table_dependency", "table_exists")
    if td == "table_not_exists":
        a["nonexistent_table"] = "table_not_exists_failure"
        a["table_name_shape"] = "nonexistent_table"

    sd = a.get("schema_dependency", "schema_exists")
    if sd == "schema_not_exists":
        a["nonexistent_schema"] = "schema_not_exists_failure"
        a["schema_name_shape"] = "nonexistent_schema"

    sns = a.get("schema_name_shape", "simple_name")
    if sns == "nonexistent_schema":
        a["schema_dependency"] = "schema_not_exists"
        a["nonexistent_schema"] = "schema_not_exists_failure"

    pi2 = a.get("publication_identity", "not_exists")
    if pi2 == "quoted_duplicate":
        a["publication_name_shape"] = "quoted_name"


def _failure_conditions(a: dict[str, str]) -> list[str]:
    """Return list of active failure condition names."""

    conditions: list[str] = []
    pi = a.get("publication_identity", "not_exists")
    if pi in ("exists", "quoted_duplicate"):
        conditions.append("duplicate")
    ep = a.get("executor_privilege", "")
    if ep == "non_superuser":
        conditions.append("insufficient_privilege")
    td = a.get("table_dependency", "")
    if td == "table_not_exists":
        conditions.append("missing_table")
    sd = a.get("schema_dependency", "")
    if sd == "schema_not_exists":
        conditions.append("missing_schema")
    sns = a.get("schema_name_shape", "")
    if sns == "nonexistent_schema":
        conditions.append("missing_schema")
    return conditions


_FAILURE_SQLSTATE = {
    "duplicate": ("42710", "duplicate_publication_provisional"),
    "insufficient_privilege": ("42501", "insufficient_privilege_provisional"),
    "missing_table": ("42P01", "undefined_table_provisional"),
    "missing_schema": ("3F000", "invalid_schema_name_provisional"),
}


def _branch_factor_keys(branch: str) -> tuple[str, ...]:
    if branch == "for_table":
        return tuple(_FOR_TABLE_AXES.keys())
    if branch == "for_tables_in_schema":
        return tuple(_FOR_SCHEMA_AXES.keys())
    return ()


def _behavior_combinations(
    branch: str,
) -> list[dict[str, str]]:
    """Cartesian product of general + branch-specific axes, filtered."""

    general_items = list(_GENERAL_AXES.items())
    if branch == "for_table":
        branch_axes = _FOR_TABLE_AXES
    elif branch == "for_tables_in_schema":
        branch_axes = _FOR_SCHEMA_AXES
    else:
        branch_axes = {}
    branch_items = list(branch_axes.items())

    all_keys = [k for k, _ in general_items] + [k for k, _ in branch_items]
    all_value_lists = (
        [v for _, v in general_items] + [v for _, v in branch_items]
    )

    combos: list[dict[str, str]] = []
    for values in itertools.product(*all_value_lists):
        assignment = dict(zip(all_keys, values))
        if _is_valid_combination(assignment):
            combos.append(assignment)
    return combos


def _full_assignment(
    branch: str,
    behavior: dict[str, str],
    verification: str,
    cleanup: str,
) -> dict[str, str]:
    a: dict[str, str] = dict(_BASELINE_DEFAULTS)
    branch_to_fcs = {
        "for_all_tables": "for_all_tables",
        "for_table": "for_table_single",
        "for_tables_in_schema": "for_tables_in_schema",
        "no_for": "no_for_clause",
    }
    a["for_clause_shape"] = branch_to_fcs.get(branch, "for_all_tables")
    a["statement_branch"] = _FOR_CLAUSE_TO_BRANCH.get(
        a["for_clause_shape"], "branch_for_all_tables"
    )
    for key, value in behavior.items():
        a[key] = value
    a["verification_mode"] = verification
    a["cleanup_mode"] = cleanup
    _derive_t5_factors(a)
    failures = _failure_conditions(a)
    a["expected_status"] = "failure" if failures else "success"
    return a


def _extension_multiset_sha256(
    cases: tuple[CreatePublicationFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-publication-factor-extension-v1\n"
    )
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


def _present_failure_pair(
    a: dict[str, str],
) -> tuple[str, str] | None:
    """Return the (factor, value) pair representing the active failure."""

    pi = a.get("publication_identity", "not_exists")
    if pi in ("exists", "quoted_duplicate"):
        return ("publication_identity", pi)
    ep = a.get("executor_privilege", "")
    if ep == "non_superuser":
        return ("executor_privilege", "non_superuser")
    td = a.get("table_dependency", "")
    if td == "table_not_exists":
        return ("table_dependency", "table_not_exists")
    sd = a.get("schema_dependency", "")
    if sd == "schema_not_exists":
        return ("schema_dependency", "schema_not_exists")
    sns = a.get("schema_name_shape", "")
    if sns == "nonexistent_schema":
        return ("schema_name_shape", "nonexistent_schema")
    return None


def build_create_publication_factor_extension_plan(
    repository_root: Path,
) -> CreatePublicationFactorExtensionPlan:
    """Build the bounded post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    catalog_rows = load_shipped_applicability_universe(
        root
    ).rows_for_statement("create_publication")
    if len(catalog_rows) != 68:
        raise CreatePublicationFactorExtensionError(
            "catalog row count drift"
        )

    cases: list[CreatePublicationFactorExtensionCase] = []
    raw_count = 0
    ordinal = _BASELINE_COUNT

    for branch in ("for_all_tables", "for_table", "for_tables_in_schema", "no_for"):
        behavior_combos = _behavior_combinations(branch)
        for behavior in behavior_combos:
            for verification in _VERIFICATION_MODES:
                for cleanup in _CLEANUP_MODES:
                    raw_count += 1
                    full = _full_assignment(
                        branch, behavior, verification, cleanup
                    )
                    failures = _failure_conditions(full)
                    if len(failures) > 1:
                        continue
                    if failures:
                        condition = failures[0]
                        sqlstate, reason = _FAILURE_SQLSTATE[condition]
                        outcome = "expected_failure"
                    else:
                        sqlstate = "00000"
                        reason = None
                        outcome = "success"
                    ordinal += 1
                    sorted_assignment = tuple(sorted(full.items()))
                    derivation_id = (
                        f"CPUB-EXT|{ordinal:05d}|"
                        f"{verification}|{cleanup}"
                    )
                    cases.append(
                        CreatePublicationFactorExtensionCase(
                            ordinal=ordinal,
                            case_id=f"CREATEPUBLICATION{ordinal:05d}",
                            sql_filename=f"CREATEPUBLICATION{ordinal:05d}.sql",
                            object_prefix=f"createpublication_{ordinal:05d}_",
                            derivation_id=derivation_id,
                            derived_from_combination_group=_COMBINATION_GROUP,
                            derivation_reason=(
                                f"CREATE PUBLICATION extension: "
                                f"branch={branch}, "
                                f"verification={verification}, "
                                f"cleanup={cleanup}"
                            ),
                            factor_assignment=sorted_assignment,
                            consumer_action_id=_CONSUMER_ACTION[branch],
                            outcome=outcome,
                            expected_sqlstate=sqlstate,
                            expected_failure_reason=reason,
                        )
                    )

    dropped = max(0, raw_count - _CAP)
    if dropped > 0:
        cases = cases[: _CAP]

    plan = CreatePublicationFactorExtensionPlan(
        cases=tuple(cases),
        extension_multiset_sha256=_extension_multiset_sha256(
            tuple(cases)
        ),
        raw_combination_count=raw_count,
        dropped_combination_count=dropped,
    )

    expected_min = 1000 - _BASELINE_COUNT
    if len(plan.cases) < expected_min:
        raise CreatePublicationFactorExtensionError(
            f"extension case count below threshold: {len(plan.cases)}"
        )
    if len(plan.cases) > _CAP:
        raise CreatePublicationFactorExtensionError(
            "extension case count exceeds cap"
        )
    ordinals = [case.ordinal for case in plan.cases]
    if ordinals != list(range(_BASELINE_COUNT + 1, _BASELINE_COUNT + 1 + len(plan.cases))):
        raise CreatePublicationFactorExtensionError(
            "extension ordinal gap"
        )
    if len({case.case_id for case in plan.cases}) != len(plan.cases):
        raise CreatePublicationFactorExtensionError(
            "duplicate extension case_id"
        )
    if len({case.sql_filename for case in plan.cases}) != len(plan.cases):
        raise CreatePublicationFactorExtensionError(
            "duplicate extension sql_filename"
        )
    if not all(case.outcome in ("success", "expected_failure") for case in plan.cases):
        raise CreatePublicationFactorExtensionError(
            "unknown extension outcome"
        )
    if not all(case.derivation_id.startswith("CPUB-EXT|") for case in plan.cases):
        raise CreatePublicationFactorExtensionError(
            "extension derivation_id prefix drift"
        )
    return plan


__all__ = [
    "CreatePublicationFactorExtensionError",
    "CreatePublicationFactorExtensionCase",
    "CreatePublicationFactorExtensionPlan",
    "build_create_publication_factor_extension_plan",
    "_BASELINE_COUNT",
    "_CAP",
    "_VERIFICATION_MODES",
    "_CLEANUP_MODES",
    "_CROSSED_NEGATIVES",
    "_present_failure_pair",
    "_extension_multiset_sha256",
]
