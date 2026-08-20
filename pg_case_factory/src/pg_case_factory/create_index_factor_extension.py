"""Bounded post-coverage extension plan for CREATE INDEX factor regress.

The baseline :mod:`create_index_factor_loop` assigns one local SQL program
to every ``SFV``/``GRM`` obligation (marginal 1:1).  This module crosses
the main-axis factor values with verification/cleanup axes under an
at-most-one-failure attribution policy, producing a bounded set of
additional regress programs that exercise pairwise factor interactions.

CREATE INDEX operates ON a relation (table).  The no-DB ledger prefers a
fixture table for fuller coverage and bookend gate compliance.

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
from .create_index_factor_loop import (
    _BASELINE_DEFAULTS,
    _SBV_TO_METHOD,
    _SFV_FAILURE_SQLSTATE,
    _SFV_FAILURE_VALUES,
)


class CreateIndexFactorExtensionError(ValueError):
    """Raised when CREATE INDEX extension input drifts."""


@dataclass(frozen=True)
class CreateIndexFactorExtensionCase:
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
class CreateIndexFactorExtensionPlan:
    cases: tuple[CreateIndexFactorExtensionCase, ...]
    extension_multiset_sha256: str
    raw_combination_count: int
    dropped_combination_count: int


_BASELINE_COUNT = 101
_CAP = 20000

_VERIFICATION_MODES = (
    "catalog_query",
    "index_validity_check",
    "explain_index_scan",
)
_CLEANUP_MODES = ("drop_index", "rollback")

_METHODS = ("btree", "hash", "gist", "spgist", "gin", "brin")

_MAIN_AXES: dict[str, tuple[str, ...]] = {
    "unique": ("false", "true"),
    "predicate": ("false", "true"),
    "include": ("false", "true"),
    "concurrently": ("false", "true"),
}

_SECONDARY_AXES: list[tuple[str, tuple[str, ...]]] = [
    ("order", ("none", "asc", "desc")),
    ("nulls", ("none", "first", "last")),
    ("if_not_exists", ("false", "true")),
    ("nulls_distinct", ("none", "distinct", "not_distinct")),
    ("only", ("false", "true")),
    ("name_style", ("explicit_compact", "explicit_semantic", "implicit")),
    ("collation", ("none", "default_collation", "non_default_collation")),
    ("opclass", ("none", "default_opclass", "non_default_opclass")),
    ("with_storage", (
        "none", "btree_fillfactor", "btree_deduplicate_items",
        "gist_buffering", "gin_fastupdate", "gin_pending_list_limit",
        "brin_pages_per_range", "brin_autosummarize",
    )),
    ("tablespace", ("none", "pg_default", "custom_tablespace")),
    ("expression_index", ("column_only", "simple_expression", "complex_expression")),
    ("partition_constraint", ("none", "only_on_partitioned", "concurrently_on_partitioned")),
]

_CROSSED_NEGATIVES = frozenset(
    {
        ("invalid_combination", "unique_with_non_btree"),
        ("invalid_combination", "include_with_unsupported_method"),
        ("invalid_combination", "multi_column_with_unsupported_method"),
        ("syntax_error", "invalid_syntax"),
        ("concurrent_failure", "in_transaction_block"),
        ("concurrent_failure", "invalid_index_leftover"),
        ("column_type_compatibility", "method_type_incompatible"),
        ("expected_status", "failure"),
    }
)

_COMBINATION_GROUP = "create_index_required_factor_value_matrix"


def _is_unique_with_non_btree(a: dict[str, str]) -> bool:
    return a.get("unique") == "true" and a.get("method") != "btree"


def _is_include_with_unsupported(a: dict[str, str]) -> bool:
    return (
        a.get("include") == "true"
        and a.get("method") in ("hash", "gin", "brin")
    )


def _is_concurrently_in_txn(a: dict[str, str]) -> bool:
    return a.get("concurrently") == "true" and a.get(
        "concurrent_failure"
    ) == "in_transaction_block"


def _is_concurrent_leftover(a: dict[str, str]) -> bool:
    return a.get("concurrently") == "true" and a.get(
        "concurrent_failure"
    ) == "invalid_index_leftover"


def _is_type_incompatible(a: dict[str, str]) -> bool:
    return a.get("column_type_compatibility") == (
        "method_type_incompatible"
    )


def _is_syntax_error(a: dict[str, str]) -> bool:
    return a.get("syntax_error") == "invalid_syntax"


def _is_expected_failure_status(a: dict[str, str]) -> bool:
    return a.get("expected_status") == "failure"


def _failure_conditions(a: dict[str, str]) -> list[str]:
    """Return list of active failure condition names."""

    conditions: list[str] = []
    if _is_unique_with_non_btree(a):
        conditions.append("unique_with_non_btree")
    if _is_include_with_unsupported(a):
        conditions.append("include_with_unsupported_method")
    if _is_concurrently_in_txn(a):
        conditions.append("in_transaction_block")
    if _is_concurrent_leftover(a):
        conditions.append("invalid_index_leftover")
    if _is_type_incompatible(a):
        conditions.append("method_type_incompatible")
    if _is_syntax_error(a):
        conditions.append("syntax_error")
    if _is_expected_failure_status(a):
        conditions.append("expected_failure_status")
    return conditions


def _is_valid_combination(a: dict[str, str]) -> bool:
    """Consistency + at-most-one-failure attribution."""

    failures = _failure_conditions(a)
    return len(failures) <= 1


_FAILURE_SQLSTATE = {
    "unique_with_non_btree": (
        "42809",
        "unique_not_supported_for_method_provisional",
    ),
    "include_with_unsupported_method": (
        "42809",
        "include_not_supported_for_method_provisional",
    ),
    "in_transaction_block": (
        "0A000",
        "concurrently_in_transaction_block_provisional",
    ),
    "invalid_index_leftover": (
        "0A000",
        "concurrent_failure_invalid_index_provisional",
    ),
    "method_type_incompatible": (
        "42704",
        "operator_class_missing_provisional",
    ),
    "syntax_error": (
        "42601",
        "syntax_error_provisional",
    ),
    "expected_failure_status": (
        "42710",
        "duplicate_index_provisional",
    ),
}


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors from T1-T4 values in extension."""

    method = a.get("method", "btree")
    if method in _SBV_TO_METHOD:
        a["statement_branch"] = _SBV_TO_METHOD[method]
    if a.get("unique") == "true":
        a["statement_branch"] = "unique_btree"
        a["method"] = "btree"
        method = "btree"
    if a.get("predicate") == "true":
        a["statement_branch"] = "partial_index"
    if a.get("include") == "true":
        a["statement_branch"] = "covering_index"
    if a.get("concurrently") == "true":
        a["statement_branch"] = "concurrent_build"
    ei = a.get("expression_index", "column_only")
    if ei != "column_only":
        a["statement_branch"] = "expression_index"

    # T5 → T1 derivation
    ic = a.get("invalid_combination", "none")
    if ic == "unique_with_non_btree":
        a["unique"] = "true"
        a["method"] = "hash"
        a["statement_branch"] = "unique_btree"
    elif ic == "include_with_unsupported_method":
        a["include"] = "true"
        a["method"] = "hash"
        a["statement_branch"] = "covering_index"
    elif ic == "multi_column_with_unsupported_method":
        a["statement_branch"] = "multi_column_btree"
        a["method"] = "hash"

    cf = a.get("concurrent_failure", "none")
    if cf in ("in_transaction_block", "invalid_index_leftover"):
        a["concurrently"] = "true"
        a["statement_branch"] = "concurrent_build"

    ctc = a.get("column_type_compatibility", "btree_compatible")
    if ctc == "method_type_incompatible":
        a["method"] = "hash"
        a["statement_branch"] = "hash_index"

    se = a.get("syntax_error", "none")
    if se == "invalid_syntax":
        a["statement_branch"] = "single_column_btree"
        a["method"] = "btree"

    pc = a.get("partition_constraint", "none")
    if pc in ("only_on_partitioned", "concurrently_on_partitioned"):
        a["only"] = "true"
        if pc == "concurrently_on_partitioned":
            a["concurrently"] = "true"
            a["statement_branch"] = "concurrent_build"

    failures = _failure_conditions(a)
    a["expected_status"] = "failure" if failures else "success"


def _present_failure_pair(
    a: dict[str, str],
) -> tuple[str, str] | None:
    """Return the (factor, value) pair representing the active failure."""

    if _is_unique_with_non_btree(a):
        return ("invalid_combination", "unique_with_non_btree")
    if _is_include_with_unsupported(a):
        return ("invalid_combination", "include_with_unsupported_method")
    if _is_concurrently_in_txn(a):
        return ("concurrent_failure", "in_transaction_block")
    if _is_concurrent_leftover(a):
        return ("concurrent_failure", "invalid_index_leftover")
    if _is_type_incompatible(a):
        return ("column_type_compatibility", "method_type_incompatible")
    if _is_syntax_error(a):
        return ("syntax_error", "invalid_syntax")
    if _is_expected_failure_status(a):
        return ("expected_status", "failure")
    return None


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
    _derive_t5_factors(a)
    failures = _failure_conditions(a)
    a["expected_status"] = "failure" if failures else "success"
    return a


def _extension_multiset_sha256(
    cases: tuple[CreateIndexFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-index-factor-extension-v1\n"
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


def _consumer_for(a: dict[str, str]) -> str:
    """Resolve the consumer action from the derived statement_branch."""
    sbv = a.get("statement_branch", "single_column_btree")
    mapping = {
        "single_column_btree": "single_column_btree",
        "multi_column_btree": "multi_column_btree",
        "unique_btree": "unique_btree",
        "partial_index": "partial_index",
        "covering_index": "covering_index",
        "expression_index": "expression_index",
        "hash_index": "hash_index",
        "gist_index": "gist_index",
        "spgist_index": "spgst_index",
        "gin_index": "gin_index",
        "brin_index": "brin_index",
        "concurrent_build": "concurrent_build",
    }
    return mapping.get(sbv, "single_column_btree")


def _emit_case(
    ordinal: int,
    full: dict[str, str],
    verification: str,
    cleanup: str,
    round_label: str,
) -> CreateIndexFactorExtensionCase | None:
    failures = _failure_conditions(full)
    if len(failures) > 1:
        return None
    if failures:
        condition = failures[0]
        sqlstate, reason = _FAILURE_SQLSTATE[condition]
        outcome = "expected_failure"
    else:
        sqlstate = "00000"
        reason = None
        outcome = "success"
    sorted_assignment = tuple(sorted(full.items()))
    derivation_id = (
        f"CINX-EXT|{ordinal:05d}|"
        f"{verification}|{cleanup}|{round_label}"
    )
    consumer = _consumer_for(full)
    return CreateIndexFactorExtensionCase(
        ordinal=ordinal,
        case_id=f"CREATEINDEX{ordinal:05d}",
        sql_filename=f"CREATEINDEX{ordinal:05d}.sql",
        object_prefix=f"createindex_{ordinal:05d}_",
        derivation_id=derivation_id,
        derived_from_combination_group=_COMBINATION_GROUP,
        derivation_reason=(
            f"CREATE INDEX extension ({round_label}): "
            f"method={full.get('method')}, "
            f"verification={verification}, "
            f"cleanup={cleanup}"
        ),
        factor_assignment=sorted_assignment,
        consumer_action_id=consumer,
        outcome=outcome,
        expected_sqlstate=sqlstate,
        expected_failure_reason=reason,
    )


def build_create_index_factor_extension_plan(
    repository_root: Path,
) -> CreateIndexFactorExtensionPlan:
    """Build the bounded post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    catalog_rows = load_shipped_applicability_universe(
        root
    ).rows_for_statement("create_index")
    if len(catalog_rows) != 89:
        raise CreateIndexFactorExtensionError("catalog row count drift")

    cases: list[CreateIndexFactorExtensionCase] = []
    raw_count = 0
    ordinal = _BASELINE_COUNT

    # Round 1: main axes cross (method × unique × predicate × include
    # × concurrently) × verification × cleanup
    main_keys = list(_MAIN_AXES.keys())
    main_value_lists = [v for v in _MAIN_AXES.values()]
    for method in _METHODS:
        for main_values in itertools.product(*main_value_lists):
            behavior = dict(zip(main_keys, main_values))
            behavior["method"] = method
            for verification in _VERIFICATION_MODES:
                for cleanup in _CLEANUP_MODES:
                    raw_count += 1
                    full = _full_assignment(
                        behavior, verification, cleanup
                    )
                    case = _emit_case(
                        ordinal + 1, full, verification, cleanup,
                        "main",
                    )
                    if case is not None:
                        ordinal += 1
                        cases.append(case)

    # Round 2: secondary axis rotations (each axis crossed with method
    # × verification × cleanup, with main axes at defaults)
    for axis_name, axis_values in _SECONDARY_AXES:
        for method in _METHODS:
            for axis_value in axis_values:
                for verification in _VERIFICATION_MODES:
                    for cleanup in _CLEANUP_MODES:
                        raw_count += 1
                        behavior = {"method": method, axis_name: axis_value}
                        full = _full_assignment(
                            behavior, verification, cleanup
                        )
                        case = _emit_case(
                            ordinal + 1, full, verification, cleanup,
                            f"secondary_{axis_name}",
                        )
                        if case is not None:
                            ordinal += 1
                            cases.append(case)

    dropped = max(0, raw_count - len(cases))
    if len(cases) > _CAP:
        cases = cases[:_CAP]

    plan = CreateIndexFactorExtensionPlan(
        cases=tuple(cases),
        extension_multiset_sha256=_extension_multiset_sha256(
            tuple(cases)
        ),
        raw_combination_count=raw_count,
        dropped_combination_count=dropped,
    )

    expected_min = 1000 - _BASELINE_COUNT
    if len(plan.cases) < expected_min:
        raise CreateIndexFactorExtensionError(
            f"extension case count below threshold: {len(plan.cases)}"
        )
    if len(plan.cases) > _CAP:
        raise CreateIndexFactorExtensionError(
            "extension case count exceeds cap"
        )
    ordinals = [case.ordinal for case in plan.cases]
    if ordinals != list(range(
        _BASELINE_COUNT + 1, _BASELINE_COUNT + 1 + len(plan.cases)
    )):
        raise CreateIndexFactorExtensionError("extension ordinal gap")
    if len({case.case_id for case in plan.cases}) != len(plan.cases):
        raise CreateIndexFactorExtensionError("duplicate extension case_id")
    if len({case.sql_filename for case in plan.cases}) != len(plan.cases):
        raise CreateIndexFactorExtensionError(
            "duplicate extension sql_filename"
        )
    if not all(
        case.outcome in ("success", "expected_failure")
        for case in plan.cases
    ):
        raise CreateIndexFactorExtensionError("unknown extension outcome")
    if not all(
        case.derivation_id.startswith("CINX-EXT|")
        for case in plan.cases
    ):
        raise CreateIndexFactorExtensionError(
            "extension derivation_id prefix drift"
        )
    return plan


__all__ = [
    "CreateIndexFactorExtensionError",
    "CreateIndexFactorExtensionCase",
    "CreateIndexFactorExtensionPlan",
    "build_create_index_factor_extension_plan",
    "_BASELINE_COUNT",
    "_CAP",
    "_VERIFICATION_MODES",
    "_CLEANUP_MODES",
    "_CROSSED_NEGATIVES",
    "_present_failure_pair",
    "_extension_multiset_sha256",
]
