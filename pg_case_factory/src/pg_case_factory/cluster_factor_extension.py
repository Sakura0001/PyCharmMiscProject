"""Bounded post-coverage cross-factor extension expander for CLUSTER.

The marginal factor-value-loop (:mod:`cluster_factor_loop`) is the required
baseline: one program per factor value, 55 local SFV cases.  This module
adds the bounded post-coverage extension phase allowed by
``cluster.yaml`` ``post_coverage_extension_policy.enabled: true``:
cross-factor combinations of the positive behaviour axes across all 8
statement branches, with at most one failure-causing value per case so
attribution stays clean, and ``verification`` / ``cleanup`` crossed so
every declared T6 value is exercised.

CLUSTER operates on a ``pg_class`` table relation and indirectly depends
on an existing index.  Success-path cases CREATE the fixture table (and
index) as setup, so the bookend contract (DROP TABLE IF EXISTS first/last)
applies to those cases.  The T5 single-value factors
(``nonexistent_table``, ``nonexistent_index``, ``insufficient_privilege``,
``index_not_on_table``) overlap their T1/T4 counterparts and are derived
in :func:`_derive_t5_factors`, not crossed as axes, so a single failure is
not double-counted.

The extension phase never replaces a required-baseline obligation.  Each
extension case carries a derivation record (per yaml
``post_coverage_extension_policy.required_fields``) and is marked
``is_extension``.  Filtering happens BEFORE counting (``raw += 1``), so
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

from .cluster_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_cluster_factor_loop_plan,
)


class ClusterFactorExtensionError(ValueError):
    """Raised when a frozen CLUSTER extension input drifts."""


@dataclass(frozen=True)
class ClusterFactorExtensionCase:
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
class ClusterFactorExtensionPlan:
    cases: tuple[ClusterFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 55
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_class_relclustered",
    "physical_ordering_check",
    "pg_stat_progress_cluster",
    "error_assertion",
)
_CLEANUP_MODES = (
    "drop_objects",
    "none",
)

# General axes crossed for branches that target a single table (1-6).
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "table_name_shape": (
        "simple",
        "quoted",
        "schema_qualified",
    ),
    "privilege_level": (
        "owner",
        "superuser",
        "insufficient_privilege",
    ),
}

# Dense positive baseline (all success values).  statement_branch /
# using_clause / verbose_option / cluster_all are overridden per branch.
_BASELINE: dict[str, str] = {
    "statement_branch": "cluster_table_using_index",
    "object_state": "table_exists_index_exists",
    "expected_status": "success",
    "using_clause": "using_index",
    "verbose_option": "no_verbose",
    "cluster_all": "single_table",
    "table_name_shape": "simple",
    "index_name_shape": "simple",
    "privilege_level": "owner",
    "index_dependency": "index_exists_on_table",
    "partitioned_table": "none",
    "nonexistent_table": "none",
    "nonexistent_index": "none",
    "insufficient_privilege": "none",
    "index_not_on_table": "none",
    "transaction_block_restriction": "none",
    "verification": "pg_class_relclustered",
    "cleanup": "drop_objects",
}

# Branch -> (using_clause, verbose_option, cluster_all, branch_axes).
# branch_axes are crossed IN ADDITION to the general axes (for table
# branches) or alone (for all-tables branches).
_BRANCH_CONFIG: tuple[
    tuple[str, str, str, str, dict[str, tuple[str, ...]]], ...
] = (
    (
        "cluster_table_using_index",
        "using_index",
        "no_verbose",
        "single_table",
        {
            "object_state": (
                "table_exists_index_exists",
                "table_does_not_exist",
                "table_exists_index_does_not_exist",
            ),
            "index_name_shape": ("simple", "quoted"),
            "index_dependency": (
                "index_exists_on_table",
                "index_not_on_table",
            ),
            "partitioned_table": (
                "none",
                "partitioned_table_with_partitioned_index",
            ),
        },
    ),
    (
        "cluster_table_recluster",
        "without_using",
        "no_verbose",
        "single_table",
        {
            "object_state": (
                "table_exists_clustered_index_recorded",
                "table_does_not_exist",
                "table_exists_no_clustered_index_recorded",
            ),
            "partitioned_table": (
                "none",
                "partitioned_table_with_partitioned_index",
                "partitioned_table_without_index_specified",
            ),
        },
    ),
    (
        "cluster_verbose_table_using_index",
        "using_index",
        "verbose_keyword",
        "single_table",
        {
            "object_state": (
                "table_exists_index_exists",
                "table_does_not_exist",
                "table_exists_index_does_not_exist",
            ),
            "index_name_shape": ("simple", "quoted"),
            "index_dependency": (
                "index_exists_on_table",
                "index_not_on_table",
            ),
            "partitioned_table": (
                "none",
                "partitioned_table_with_partitioned_index",
            ),
        },
    ),
    (
        "cluster_verbose_table_recluster",
        "without_using",
        "verbose_keyword",
        "single_table",
        {
            "object_state": (
                "table_exists_clustered_index_recorded",
                "table_does_not_exist",
                "table_exists_no_clustered_index_recorded",
            ),
            "partitioned_table": (
                "none",
                "partitioned_table_with_partitioned_index",
                "partitioned_table_without_index_specified",
            ),
        },
    ),
    (
        "cluster_paren_option_table_using_index",
        "using_index",
        "paren_verbose_true",
        "single_table",
        {
            "object_state": (
                "table_exists_index_exists",
                "table_does_not_exist",
                "table_exists_index_does_not_exist",
            ),
            "index_name_shape": ("simple", "quoted"),
            "index_dependency": (
                "index_exists_on_table",
                "index_not_on_table",
            ),
            "partitioned_table": (
                "none",
                "partitioned_table_with_partitioned_index",
            ),
        },
    ),
    (
        "cluster_paren_option_table_recluster",
        "without_using",
        "paren_verbose_true",
        "single_table",
        {
            "verbose_option": (
                "paren_verbose_true",
                "paren_verbose_false",
            ),
            "object_state": (
                "table_exists_clustered_index_recorded",
                "table_does_not_exist",
                "table_exists_no_clustered_index_recorded",
            ),
            "partitioned_table": (
                "none",
                "partitioned_table_with_partitioned_index",
                "partitioned_table_without_index_specified",
            ),
        },
    ),
    (
        "cluster_all",
        "without_using",
        "no_verbose",
        "all_tables",
        {
            "privilege_level": (
                "owner",
                "superuser",
                "insufficient_privilege",
            ),
            "partitioned_table": (
                "none",
                "partitioned_table_with_partitioned_index",
            ),
            "transaction_block_restriction": (
                "none",
                "cluster_all_inside_transaction_block",
            ),
        },
    ),
    (
        "cluster_verbose_all",
        "without_using",
        "verbose_keyword",
        "all_tables",
        {
            "privilege_level": (
                "owner",
                "superuser",
                "insufficient_privilege",
            ),
            "partitioned_table": (
                "none",
                "partitioned_table_with_partitioned_index",
            ),
            "transaction_block_restriction": (
                "none",
                "cluster_all_inside_transaction_block",
            ),
        },
    ),
)

# Crossed behaviour-negative (factor, value) pairs - one representative
# per failure scenario.  Overlapping T5/T3 values are NOT listed here
# (they are derived in :func:`_derive_t5_factors`) so counting both would
# double-count a single failure and break at-most-one attribution.
_CROSSED_NEGATIVES = frozenset(
    {
        ("object_state", "table_does_not_exist"),
        ("object_state", "table_exists_index_does_not_exist"),
        ("object_state", "table_exists_no_clustered_index_recorded"),
        ("privilege_level", "insufficient_privilege"),
        (
            "partitioned_table",
            "partitioned_table_without_index_specified",
        ),
        ("index_dependency", "index_not_on_table"),
        (
            "transaction_block_restriction",
            "cluster_all_inside_transaction_block",
        ),
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

    os_ = a.get("object_state", "table_exists_index_exists")
    tns = a.get("table_name_shape", "simple")
    id_ = a.get("index_dependency", "index_exists_on_table")
    iot = a.get("index_not_on_table", "none")
    pl = a.get("privilege_level", "owner")
    ip = a.get("insufficient_privilege", "none")
    ni = a.get("nonexistent_index", "none")
    ins = a.get("index_name_shape", "simple")
    nt = a.get("nonexistent_table", "none")

    # table-missing cluster
    if os_ == "table_does_not_exist":
        a["table_name_shape"] = "non_existent"
        a["nonexistent_table"] = "cluster_nonexistent_table"
    else:
        a["nonexistent_table"] = "none"

    # index-missing cluster (USING branches)
    if os_ == "table_exists_index_does_not_exist":
        a["nonexistent_index"] = "cluster_with_nonexistent_index"
        a["index_name_shape"] = "non_existent"
        a["index_dependency"] = "index_exists_on_table"
    elif id_ == "index_not_on_table":
        a["index_not_on_table"] = "index_belongs_to_different_table"
    elif os_ == "table_exists_no_clustered_index_recorded":
        a["index_dependency"] = "no_clustered_index_recorded"
    else:
        a["nonexistent_index"] = "none"
        a["index_not_on_table"] = "none"

    # privilege-insufficient cluster
    if pl == "insufficient_privilege":
        a["insufficient_privilege"] = "non_owner_cluster"
    else:
        a["insufficient_privilege"] = "none"

    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments (T6 at baseline) passing the filter."""

    combos: list[dict[str, str]] = []
    for branch, uc, vo, ca, axes in _BRANCH_CONFIG:
        all_axes: dict[str, tuple[str, ...]] = {}
        if ca == "single_table":
            all_axes.update(_GENERAL_AXES)
        all_axes.update(axes)
        names = list(all_axes)
        for values in itertools.product(
            *[all_axes[n] for n in names]
        ):
            assignment: dict[str, str] = dict(_BASELINE)
            assignment["statement_branch"] = branch
            assignment["using_clause"] = uc
            assignment["verbose_option"] = vo
            assignment["cluster_all"] = ca
            for name, value in zip(names, values):
                assignment[name] = value
            _derive_t5_factors(assignment)
            if not _is_valid_combination(assignment):
                continue
            if len(assignment) != len(set(assignment)):
                raise ClusterFactorExtensionError(
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
    cases: tuple[ClusterFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(b"cluster-factor-extension-v1\n")
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
    cases: tuple[ClusterFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"CLUSTER extension {case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": "cluster_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "CLUSTER",
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


def build_cluster_factor_extension_plan(
    repository_root: Path,
) -> ClusterFactorExtensionPlan:
    """Build the bounded CLUSTER post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_cluster_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[ClusterFactorExtensionCase] = []
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
                outcome, sqlstate, reason = _outcome_for(assignment)
                ordinal += 1
                cases.append(
                    ClusterFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"CLUSTER{ordinal:05d}",
                        sql_filename=f"CLUSTER{ordinal:05d}.sql",
                        object_prefix=f"cluster_{ordinal:05d}_",
                        derivation_id=(
                            f"CLUSTER-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "cluster_required_factor_value_matrix"
                        ),
                        derivation_reason=(
                            "cross-factor extension: "
                            f"statement_branch="
                            f"{assignment['statement_branch']} "
                            f"x object_state="
                            f"{assignment['object_state']} "
                            f"x privilege_level="
                            f"{assignment['privilege_level']} "
                            f"x verification={verification} "
                            f"x cleanup={cleanup}"
                        ),
                        factor_assignment=tuple(
                            sorted(assignment.items())
                        ),
                        consumer_action_id=assignment[
                            "statement_branch"
                        ],
                        outcome=outcome,
                        expected_sqlstate=sqlstate,
                        expected_failure_reason=reason,
                        is_extension=True,
                    )
                )
    dropped = max(0, raw - _CAP)
    cases_tuple = tuple(cases)
    return ClusterFactorExtensionPlan(
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
    "ClusterFactorExtensionError",
    "ClusterFactorExtensionCase",
    "ClusterFactorExtensionPlan",
    "build_cluster_factor_extension_plan",
]
