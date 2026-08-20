"""Bounded post-coverage extension plan for CREATE FUNCTION factor regress.

The baseline :mod:`create_function_factor_loop` assigns one local SQL
program to every ``SFV`` obligation (marginal 1:1, 121 cases).  This
module crosses the main-axis factor values with verification/cleanup
axes under an at-most-one-failure attribution policy, producing a bounded
set of additional regress programs that exercise pairwise factor
interactions.

CREATE FUNCTION is a catalog-row DDL statement -- it does not create
tables, so the bookend (DROP TABLE IF EXISTS) is never emitted.  The
``pg_catalog.pg_proc`` catalog row (not a ``pg_class`` relation) is the
semantic witness target.  The PG18 PARALLEL delta (SAFE/UNSAFE/RESTRICTED/
absent) is exercised as a first-class general axis here.

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
from .create_function_factor_loop import (
    _BASELINE_DEFAULTS,
    _SFV_FAILURE_VALUES,
)


class CreateFunctionFactorExtensionError(ValueError):
    """Raised when CREATE FUNCTION extension input drifts."""


@dataclass(frozen=True)
class CreateFunctionFactorExtensionCase:
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
class CreateFunctionFactorExtensionPlan:
    cases: tuple[CreateFunctionFactorExtensionCase, ...]
    extension_multiset_sha256: str
    raw_combination_count: int
    dropped_combination_count: int


_BASELINE_COUNT = 121
_CAP = 20000

_VERIFICATION_MODES = (
    "pg_proc_catalog_query",
    "information_schema_routines",
    "SELECT_function_call",
    "pg_get_functiondef",
)
_CLEANUP_MODES = (
    "DROP_FUNCTION",
    "DROP_FUNCTION_IF_EXISTS",
    "DROP_FUNCTION_CASCADE",
)

_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "statement_branch": ("branch_1", "branch_2"),
    "or_replace_clause": ("present", "absent"),
    "returns_clause": (
        "RETURNS_rettype",
        "RETURNS_TABLE",
        "absent",
    ),
    "language_clause": ("sql", "plpgsql", "c", "internal", "other"),
    "volatility_clause": (
        "IMMUTABLE",
        "STABLE",
        "VOLATILE",
        "absent",
    ),
    "parallel_clause": ("UNSAFE", "RESTRICTED", "SAFE", "absent"),
}

# No negative (failure-inducing) values in the general axes -- all
# extension cases are successes.
_CROSSED_NEGATIVES: frozenset[tuple[str, str]] = frozenset()

_COMBINATION_GROUP = "create_function_required_baseline_factor_space"
_CONSUMER_ACTION = "create_function"


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    """Consistency check: RETURNS TABLE requires branch_2."""

    rc = assignment.get("returns_clause", "RETURNS_rettype")
    sb = assignment.get("statement_branch", "branch_1")
    if rc == "RETURNS_TABLE" and sb != "branch_2":
        return False
    return True


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors from T1-T4 values in extension.

    Since all general-axis values are positive and the baseline keeps
    ``object_state=not_exists`` and ``privilege_level=superuser``, no T5
    failures are triggered.  The derivation is kept for consistency with
    the baseline obligation ledger.
    """

    os_ = a.get("object_state", "not_exists")
    orr = a.get("or_replace_clause", "absent")
    if os_ == "already_exists_same_signature":
        if orr == "present":
            a["duplicate_function_signature"] = (
                "with_OR_REPLACE_replace"
            )
        else:
            a["duplicate_function_signature"] = (
                "without_OR_REPLACE_error"
            )
    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _failure_conditions(a: dict[str, str]) -> list[str]:
    """Return list of active failure condition names (always empty)."""

    return []


_FAILURE_SQLSTATE: dict[str, tuple[str, str]] = {}


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
    cases: tuple[CreateFunctionFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-function-factor-extension-v1\n"
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
    """Return the (factor, value) pair representing the active failure.

    Always returns ``None`` in the extension because all general-axis
    values are positive and the baseline keeps ``object_state=not_exists``
    and ``privilege_level=superuser``.
    """

    return None


def build_create_function_factor_extension_plan(
    repository_root: Path,
) -> CreateFunctionFactorExtensionPlan:
    """Build the bounded post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    catalog_rows = load_shipped_applicability_universe(
        root
    ).rows_for_statement("create_function")
    if len(catalog_rows) != 121:
        raise CreateFunctionFactorExtensionError(
            "catalog row count drift"
        )

    cases: list[CreateFunctionFactorExtensionCase] = []
    raw_count = 0
    ordinal = _BASELINE_COUNT

    general_items = list(_GENERAL_AXES.items())
    all_keys = [k for k, _ in general_items]
    all_value_lists = [v for _, v in general_items]

    for values in itertools.product(*all_value_lists):
        assignment = dict(zip(all_keys, values))
        if not _is_valid_combination(assignment):
            continue
        for verification in _VERIFICATION_MODES:
            for cleanup in _CLEANUP_MODES:
                raw_count += 1
                full = _full_assignment(
                    assignment, verification, cleanup
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
                branch = assignment.get("statement_branch", "branch_1")
                derivation_id = (
                    f"CFUNC-EXT|{ordinal:05d}|"
                    f"{branch}|{verification}|{cleanup}"
                )
                cases.append(
                    CreateFunctionFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"CREATEFUNCTION{ordinal:05d}",
                        sql_filename=f"CREATEFUNCTION{ordinal:05d}.sql",
                        object_prefix=(
                            f"createfunction_{ordinal:05d}_"
                        ),
                        derivation_id=derivation_id,
                        derived_from_combination_group=_COMBINATION_GROUP,
                        derivation_reason=(
                            f"CREATE FUNCTION extension: "
                            f"branch={branch}, "
                            f"or_replace="
                            f"{assignment.get('or_replace_clause')}, "
                            f"returns="
                            f"{assignment.get('returns_clause')}, "
                            f"language="
                            f"{assignment.get('language_clause')}, "
                            f"volatility="
                            f"{assignment.get('volatility_clause')}, "
                            f"parallel="
                            f"{assignment.get('parallel_clause')}, "
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

    plan = CreateFunctionFactorExtensionPlan(
        cases=tuple(cases),
        extension_multiset_sha256=_extension_multiset_sha256(
            tuple(cases)
        ),
        raw_combination_count=raw_count,
        dropped_combination_count=dropped,
    )

    expected_min = 1000 - _BASELINE_COUNT
    if len(plan.cases) < expected_min:
        raise CreateFunctionFactorExtensionError(
            f"extension case count below threshold: {len(plan.cases)}"
        )
    if len(plan.cases) > _CAP:
        raise CreateFunctionFactorExtensionError(
            "extension case count exceeds cap"
        )
    ordinals = [case.ordinal for case in plan.cases]
    if ordinals != list(
        range(
            _BASELINE_COUNT + 1,
            _BASELINE_COUNT + 1 + len(plan.cases),
        )
    ):
        raise CreateFunctionFactorExtensionError(
            "extension ordinal gap"
        )
    if len({case.case_id for case in plan.cases}) != len(plan.cases):
        raise CreateFunctionFactorExtensionError(
            "duplicate extension case_id"
        )
    if len({case.sql_filename for case in plan.cases}) != len(
        plan.cases
    ):
        raise CreateFunctionFactorExtensionError(
            "duplicate extension sql_filename"
        )
    if not all(
        case.outcome == "success" or case.outcome == "expected_failure"
        for case in plan.cases
    ):
        raise CreateFunctionFactorExtensionError(
            "unknown extension outcome"
        )
    if not all(
        case.derivation_id.startswith("CFUNC-EXT|")
        for case in plan.cases
    ):
        raise CreateFunctionFactorExtensionError(
            "extension derivation_id prefix drift"
        )
    return plan


__all__ = [
    "CreateFunctionFactorExtensionError",
    "CreateFunctionFactorExtensionCase",
    "CreateFunctionFactorExtensionPlan",
    "build_create_function_factor_extension_plan",
    "_BASELINE_COUNT",
    "_CAP",
    "_VERIFICATION_MODES",
    "_CLEANUP_MODES",
    "_CROSSED_NEGATIVES",
    "_present_failure_pair",
    "_extension_multiset_sha256",
]
