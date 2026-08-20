"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CLUSTER.

This module compiles the marginal ``SFV`` obligation ledger for
``CLUSTER``.  CLUSTER is a PostgreSQL DDL statement that physically
reorders a table according to an index.  The official synopsis has three
top-level forms (``CLUSTER [VERBOSE] table [USING index]``,
``CLUSTER ( option ) table [USING index]`` and ``CLUSTER [VERBOSE]`` for
all-tables reclustering), yielding 8 declared ``statement_branch`` values.

Unlike ``ALTER SUBSCRIPTION``, CLUSTER has no separate ``target_action``
grammar axis: the 8 ``statement_branch`` values ARE the syntax branches,
and they are themselves canonical ``SFV`` rows in the shipped applicability
universe.  Every one of the 55 declared factor values is therefore a
single ``SFV`` obligation (no ``GRM`` block, no ``INV`` block, no
``RISK``).  Each local obligation becomes exactly one regress program, so
the baseline case count equals the obligation count (55) with zero
delegated rows.

CLUSTER operates on a ``pg_class`` table relation and indirectly depends
on an existing index.  Cases that exercise a success path CREATE the
fixture table (and index) as setup, so the bookend contract (DROP TABLE
IF EXISTS first/last) applies to those cases.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class ClusterFactorLoopError(ValueError):
    """Raised when a frozen CLUSTER obligation input drifts."""


@dataclass(frozen=True)
class ClusterFactorObligation:
    ordinal: int
    obligation_id: str
    kind: str
    factor_key: str
    value: str
    consumer_action_id: str
    disposition: str
    source_locator: str
    delegated_statement_key: str | None = None


@dataclass(frozen=True)
class ClusterFactorCase:
    ordinal: int
    case_id: str
    sql_filename: str
    object_prefix: str
    primary_obligation_id: str
    kind: str
    factor_key: str
    factor_value: str
    consumer_action_id: str
    outcome: str
    expected_sqlstate: str
    expected_failure_reason: str | None
    baseline_assignments: tuple[tuple[str, str], ...]
    execution_profile: str


@dataclass(frozen=True)
class ClusterFactorLoopPlan:
    obligations: tuple[ClusterFactorObligation, ...]
    cases: tuple[ClusterFactorCase, ...]
    delegated: tuple[ClusterFactorObligation, ...]
    obligation_multiset_sha256: str


_DOC_SOURCE = "postgresql-18.4-doc:sql-cluster"

# Representative branch used as the baseline consumer for canonical factor
# values that are not bound to one specific statement_branch.  CLUSTER
# table_name USING index_name is the simplest success branch.
_REPRESENTATIVE_BRANCH = "cluster_table_using_index"

# statement_branch canonical value -> consumer (the branch itself).
_STATEMENT_BRANCH_CONSUMER = {
    "cluster_table_using_index": "cluster_table_using_index",
    "cluster_table_recluster": "cluster_table_recluster",
    "cluster_verbose_table_using_index": "cluster_verbose_table_using_index",
    "cluster_verbose_table_recluster": "cluster_verbose_table_recluster",
    "cluster_paren_option_table_using_index": (
        "cluster_paren_option_table_using_index"
    ),
    "cluster_paren_option_table_recluster": (
        "cluster_paren_option_table_recluster"
    ),
    "cluster_all": "cluster_all",
    "cluster_verbose_all": "cluster_verbose_all",
}

# cluster_all value -> consumer branch.
_CLUSTER_ALL_CONSUMER = {
    "all_tables": "cluster_all",
    "single_table": "cluster_table_using_index",
}

# using_clause value -> consumer branch.
_USING_CLAUSE_CONSUMER = {
    "using_index": "cluster_table_using_index",
    "without_using": "cluster_table_recluster",
}

# verbose_option value -> consumer branch.
_VERBOSE_OPTION_CONSUMER = {
    "no_verbose": "cluster_table_using_index",
    "verbose_keyword": "cluster_verbose_table_using_index",
    "paren_verbose_true": "cluster_paren_option_table_using_index",
    "paren_verbose_false": "cluster_paren_option_table_recluster",
}

# transaction_block_restriction value -> consumer branch.
_TXN_BLOCK_CONSUMER = {
    "cluster_all_inside_transaction_block": "cluster_all",
    "none": "cluster_table_using_index",
}

# Canonical factor -> the branch where the value is observable.  Factors
# whose consumer depends on the value (statement_branch, cluster_all,
# using_clause, verbose_option, transaction_block_restriction) are
# resolved in :func:`_canonical_consumer`.
_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_BRANCH,
    "object_state": _REPRESENTATIVE_BRANCH,
    "expected_status": _REPRESENTATIVE_BRANCH,
    "using_clause": _REPRESENTATIVE_BRANCH,
    "verbose_option": _REPRESENTATIVE_BRANCH,
    "cluster_all": _REPRESENTATIVE_BRANCH,
    "table_name_shape": _REPRESENTATIVE_BRANCH,
    "index_name_shape": _REPRESENTATIVE_BRANCH,
    "privilege_level": _REPRESENTATIVE_BRANCH,
    "index_dependency": _REPRESENTATIVE_BRANCH,
    "partitioned_table": _REPRESENTATIVE_BRANCH,
    "nonexistent_table": _REPRESENTATIVE_BRANCH,
    "nonexistent_index": _REPRESENTATIVE_BRANCH,
    "insufficient_privilege": _REPRESENTATIVE_BRANCH,
    "index_not_on_table": _REPRESENTATIVE_BRANCH,
    "transaction_block_restriction": _REPRESENTATIVE_BRANCH,
    "verification": _REPRESENTATIVE_BRANCH,
    "cleanup": _REPRESENTATIVE_BRANCH,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates - DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "table_does_not_exist"),
        ("object_state", "table_exists_index_does_not_exist"),
        ("object_state", "table_exists_no_clustered_index_recorded"),
        ("nonexistent_table", "cluster_nonexistent_table"),
        ("nonexistent_index", "cluster_with_nonexistent_index"),
        ("index_dependency", "index_not_on_table"),
        ("index_dependency", "no_clustered_index_recorded"),
        ("index_not_on_table", "index_belongs_to_different_table"),
        ("insufficient_privilege", "non_owner_cluster"),
        ("privilege_level", "insufficient_privilege"),
        (
            "transaction_block_restriction",
            "cluster_all_inside_transaction_block",
        ),
        ("table_name_shape", "non_existent"),
        ("index_name_shape", "non_existent"),
        (
            "partitioned_table",
            "partitioned_table_without_index_specified",
        ),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42P01",
        "cluster_target_or_index_missing_provisional",
    ),
    ("object_state", "table_does_not_exist"): (
        "42P01",
        "cluster_target_or_index_missing_provisional",
    ),
    ("object_state", "table_exists_index_does_not_exist"): (
        "42704",
        "cluster_target_or_index_missing_provisional",
    ),
    ("object_state", "table_exists_no_clustered_index_recorded"): (
        "42704",
        "cluster_target_or_index_missing_provisional",
    ),
    ("nonexistent_table", "cluster_nonexistent_table"): (
        "42P01",
        "cluster_target_or_index_missing_provisional",
    ),
    ("nonexistent_index", "cluster_with_nonexistent_index"): (
        "42704",
        "cluster_target_or_index_missing_provisional",
    ),
    ("index_dependency", "index_not_on_table"): (
        "42809",
        "cluster_index_not_on_table_provisional",
    ),
    ("index_dependency", "no_clustered_index_recorded"): (
        "42704",
        "cluster_target_or_index_missing_provisional",
    ),
    ("index_not_on_table", "index_belongs_to_different_table"): (
        "42809",
        "cluster_index_not_on_table_provisional",
    ),
    ("insufficient_privilege", "non_owner_cluster"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("privilege_level", "insufficient_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    (
        "transaction_block_restriction",
        "cluster_all_inside_transaction_block",
    ): (
        "25001",
        "cluster_all_transaction_block_forbidden_provisional",
    ),
    ("table_name_shape", "non_existent"): (
        "42P01",
        "cluster_target_or_index_missing_provisional",
    ),
    ("index_name_shape", "non_existent"): (
        "42704",
        "cluster_target_or_index_missing_provisional",
    ),
    (
        "partitioned_table",
        "partitioned_table_without_index_specified",
    ): (
        "42809",
        "cluster_target_or_index_missing_provisional",
    ),
}


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise ClusterFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "cluster_all":
        try:
            return _CLUSTER_ALL_CONSUMER[row.value]
        except KeyError as exc:
            raise ClusterFactorLoopError(
                f"unknown cluster_all value: {row.value}"
            ) from exc
    if row.factor == "using_clause":
        try:
            return _USING_CLAUSE_CONSUMER[row.value]
        except KeyError as exc:
            raise ClusterFactorLoopError(
                f"unknown using_clause value: {row.value}"
            ) from exc
    if row.factor == "verbose_option":
        try:
            return _VERBOSE_OPTION_CONSUMER[row.value]
        except KeyError as exc:
            raise ClusterFactorLoopError(
                f"unknown verbose_option value: {row.value}"
            ) from exc
    if row.factor == "transaction_block_restriction":
        try:
            return _TXN_BLOCK_CONSUMER[row.value]
        except KeyError as exc:
            raise ClusterFactorLoopError(
                f"unknown transaction_block_restriction value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise ClusterFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[ClusterFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("cluster")
    if len(catalog_rows) != 55:
        raise ClusterFactorLoopError("canonical obligation count drift")
    rows: list[ClusterFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            ClusterFactorObligation(
                ordinal=0,
                obligation_id=f"CLUSTER-SFV|{row.row_id}|{consumer}",
                kind="SFV",
                factor_key=row.factor,
                value=row.value,
                consumer_action_id=consumer,
                disposition=(
                    "expected_failure" if is_failure else "covered"
                ),
                source_locator=f"{row.source_reference}#{row.row_id}",
            )
        )
    return rows


def _obligation_multiset_sha256(
    rows: tuple[ClusterFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"cluster-factor-obligations-v1\n")
    for row in rows:
        digest.update(
            json.dumps(
                {
                    "obligation_id": row.obligation_id,
                    "kind": row.kind,
                    "factor_key": row.factor_key,
                    "value": row.value,
                    "consumer_action_id": row.consumer_action_id,
                    "disposition": row.disposition,
                    "delegated_statement_key": (
                        row.delegated_statement_key
                    ),
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        digest.update(b"\n")
    return digest.hexdigest()


# statement_branch -> (using_clause, verbose_option, cluster_all).
_BRANCH_OPTIONS: dict[str, tuple[str, str, str]] = {
    "cluster_table_using_index": (
        "using_index",
        "no_verbose",
        "single_table",
    ),
    "cluster_table_recluster": (
        "without_using",
        "no_verbose",
        "single_table",
    ),
    "cluster_verbose_table_using_index": (
        "using_index",
        "verbose_keyword",
        "single_table",
    ),
    "cluster_verbose_table_recluster": (
        "without_using",
        "verbose_keyword",
        "single_table",
    ),
    "cluster_paren_option_table_using_index": (
        "using_index",
        "paren_verbose_true",
        "single_table",
    ),
    "cluster_paren_option_table_recluster": (
        "without_using",
        "paren_verbose_true",
        "single_table",
    ),
    "cluster_all": (
        "without_using",
        "no_verbose",
        "all_tables",
    ),
    "cluster_verbose_all": (
        "without_using",
        "verbose_keyword",
        "all_tables",
    ),
}

# (using_clause, verbose_option, cluster_all) -> statement_branch.
_OPTION_BRANCH: dict[tuple[str, str, str], str] = {
    ("using_index", "no_verbose", "single_table"): (
        "cluster_table_using_index"
    ),
    ("without_using", "no_verbose", "single_table"): (
        "cluster_table_recluster"
    ),
    ("using_index", "verbose_keyword", "single_table"): (
        "cluster_verbose_table_using_index"
    ),
    ("without_using", "verbose_keyword", "single_table"): (
        "cluster_verbose_table_recluster"
    ),
    ("using_index", "paren_verbose_true", "single_table"): (
        "cluster_paren_option_table_using_index"
    ),
    ("without_using", "paren_verbose_true", "single_table"): (
        "cluster_paren_option_table_recluster"
    ),
    ("without_using", "paren_verbose_false", "single_table"): (
        "cluster_paren_option_table_recluster"
    ),
    ("without_using", "no_verbose", "all_tables"): "cluster_all",
    ("without_using", "verbose_keyword", "all_tables"): (
        "cluster_verbose_all"
    ),
}

# Dense baseline defaults (all positive factor values).
_BASELINE_DEFAULTS: dict[str, str] = {
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


def _resolve_branch_options(a: dict[str, str]) -> None:
    """Derive statement_branch from (and constrain) the option factors."""

    uc = a.get("using_clause", "using_index")
    vo = a.get("verbose_option", "no_verbose")
    ca = a.get("cluster_all", "single_table")
    pt = a.get("partitioned_table", "none")
    # Implicit option constraints: all-tables and paren-verbose-false and
    # partitioned-without-index all force the USING clause off.
    if ca == "all_tables":
        uc = "without_using"
    if vo == "paren_verbose_false":
        uc = "without_using"
    if pt == "partitioned_table_without_index_specified":
        uc = "without_using"
    key = (uc, vo, ca)
    if key in _OPTION_BRANCH:
        a["statement_branch"] = _OPTION_BRANCH[key]
        a["using_clause"] = uc
        a["verbose_option"] = vo
        a["cluster_all"] = ca
    else:
        branch = a.get(
            "statement_branch", "cluster_table_using_index"
        )
        if branch in _BRANCH_OPTIONS:
            bu, bv, bc = _BRANCH_OPTIONS[branch]
            a["using_clause"] = bu
            a["verbose_option"] = bv
            a["cluster_all"] = bc


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values."""

    os_ = a.get("object_state", "table_exists_index_exists")
    tns = a.get("table_name_shape", "simple")
    nt = a.get("nonexistent_table", "none")
    ni = a.get("nonexistent_index", "none")
    ins = a.get("index_name_shape", "simple")
    id_ = a.get("index_dependency", "index_exists_on_table")
    iot = a.get("index_not_on_table", "none")
    pl = a.get("privilege_level", "owner")
    ip = a.get("insufficient_privilege", "none")

    # table-missing cluster: object_state / table_name_shape /
    # nonexistent_table
    if (
        os_ == "table_does_not_exist"
        or tns == "non_existent"
        or nt == "cluster_nonexistent_table"
    ):
        a["object_state"] = "table_does_not_exist"
        a["table_name_shape"] = "non_existent"
        a["nonexistent_table"] = "cluster_nonexistent_table"

    # index-missing cluster: object_state / nonexistent_index /
    # index_name_shape
    if (
        os_ == "table_exists_index_does_not_exist"
        or ni == "cluster_with_nonexistent_index"
        or ins == "non_existent"
    ):
        a["object_state"] = "table_exists_index_does_not_exist"
        a["nonexistent_index"] = "cluster_with_nonexistent_index"
        a["index_name_shape"] = "non_existent"

    # no-clustered-index cluster: object_state / index_dependency
    if (
        os_ == "table_exists_no_clustered_index_recorded"
        or id_ == "no_clustered_index_recorded"
    ):
        a["object_state"] = "table_exists_no_clustered_index_recorded"
        a["index_dependency"] = "no_clustered_index_recorded"

    # index-not-on-table cluster: index_dependency / index_not_on_table
    if (
        id_ == "index_not_on_table"
        or iot == "index_belongs_to_different_table"
    ):
        a["index_dependency"] = "index_not_on_table"
        a["index_not_on_table"] = "index_belongs_to_different_table"

    # privilege-insufficient cluster: privilege_level / insufficient_privilege
    if (
        pl == "insufficient_privilege"
        or ip == "non_owner_cluster"
    ):
        a["privilege_level"] = "insufficient_privilege"
        a["insufficient_privilege"] = "non_owner_cluster"

    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: ClusterFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments[obligation.factor_key] = obligation.value
    if obligation.factor_key == "statement_branch":
        # The branch is the primary: derive the option factors from it.
        bu, bv, bc = _BRANCH_OPTIONS[obligation.value]
        assignments["using_clause"] = bu
        assignments["verbose_option"] = bv
        assignments["cluster_all"] = bc
    else:
        _resolve_branch_options(assignments)
    _derive_overlapping_factors(assignments)
    # Re-derive the branch in case overlapping factors constrained an
    # option (e.g. partitioned_table_without_index_specified).
    if obligation.factor_key != "statement_branch":
        _resolve_branch_options(assignments)
    if len(assignments) != len(set(assignments)):
        raise ClusterFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: ClusterFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise ClusterFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_cluster_factor_loop_plan(
    repository_root: Path,
) -> ClusterFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_cluster_factor_loop_obligations(root)
    cases: list[ClusterFactorCase] = []
    delegated: list[ClusterFactorObligation] = []
    for obligation in obligations:
        if obligation.disposition == "delegated":
            delegated.append(obligation)
            continue
        ordinal = len(cases) + 1
        if obligation.disposition == "expected_failure":
            sqlstate, failure_reason = _expected_failure_details(obligation)
            outcome = "expected_failure"
        else:
            outcome = "success"
            sqlstate = "00000"
            failure_reason = None
        cases.append(
            ClusterFactorCase(
                ordinal=ordinal,
                case_id=f"CLUSTER{ordinal:05d}",
                sql_filename=f"CLUSTER{ordinal:05d}.sql",
                object_prefix=f"cluster_{ordinal:05d}_",
                primary_obligation_id=obligation.obligation_id,
                kind=obligation.kind,
                factor_key=obligation.factor_key,
                factor_value=obligation.value,
                consumer_action_id=obligation.consumer_action_id,
                outcome=outcome,
                expected_sqlstate=sqlstate,
                expected_failure_reason=failure_reason,
                baseline_assignments=_baseline_assignments(obligation),
                execution_profile="serial_sql",
            )
        )
    plan = ClusterFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 55 or len(plan.delegated) != 0:
        raise ClusterFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 55:
        raise ClusterFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 55:
        raise ClusterFactorLoopError("duplicate SQL filename")
    return plan


def compile_cluster_factor_loop_obligations(
    repository_root: Path,
) -> tuple[ClusterFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = _compile_canonical_obligations(root)
    rows = tuple(
        ClusterFactorObligation(
            ordinal=ordinal,
            obligation_id=row.obligation_id,
            kind=row.kind,
            factor_key=row.factor_key,
            value=row.value,
            consumer_action_id=row.consumer_action_id,
            disposition=row.disposition,
            source_locator=row.source_locator,
            delegated_statement_key=row.delegated_statement_key,
        )
        for ordinal, row in enumerate(unordered_rows, start=1)
    )
    if len(rows) != 55:
        raise ClusterFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise ClusterFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"SFV": 55}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise ClusterFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise ClusterFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"} for row in rows
    ) != 55:
        raise ClusterFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(row.disposition not in allowed_dispositions for row in rows):
        raise ClusterFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "ClusterFactorLoopError",
    "ClusterFactorObligation",
    "ClusterFactorCase",
    "ClusterFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_cluster_factor_loop_obligations",
    "build_cluster_factor_loop_plan",
    "_obligation_multiset_sha256",
]
