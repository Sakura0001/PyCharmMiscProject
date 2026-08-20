"""Bounded post-coverage extension plan for CREATE LANGUAGE factor regress.

The baseline :mod:`create_language_factor_loop` assigns one local SQL
program to every ``SFV``/``GRM`` obligation (marginal 1:1).  This module
crosses the main-axis factor values with verification/cleanup axes under
an at-most-one-failure attribution policy, producing a bounded set of
additional regress programs that exercise pairwise factor interactions.

CREATE LANGUAGE is a catalog row DDL statement — it does not create
tables, so the bookend (DROP TABLE IF EXISTS) is never emitted.  The
``pg_catalog.pg_language`` catalog row (not a ``pg_class`` relation) is
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
from .create_language_factor_loop import (
    _BASELINE_DEFAULTS,
    _SFV_FAILURE_SQLSTATE,
    _SFV_FAILURE_VALUES,
)


class CreateLanguageFactorExtensionError(ValueError):
    """Raised when CREATE LANGUAGE extension input drifts."""


@dataclass(frozen=True)
class CreateLanguageFactorExtensionCase:
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
class CreateLanguageFactorExtensionPlan:
    cases: tuple[CreateLanguageFactorExtensionCase, ...]
    extension_multiset_sha256: str
    raw_combination_count: int
    dropped_combination_count: int


_BASELINE_COUNT = 44
_CAP = 20000

_VERIFICATION_MODES = ("catalog_query", "effect_query", "error_assertion")
_CLEANUP_MODES = ("drop_objects", "reset_state")

_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "target_object_state": ("absent", "exists"),
    "or_replace_clause": (
        "absent",
        "present_replace_new",
        "present_replace_existing",
    ),
    "trusted_clause": ("absent", "present"),
    "privilege_context": ("superuser", "non_superuser"),
    "name_shape": ("plain_identifier", "quoted_identifier"),
}

_HANDLER_AXES: dict[str, tuple[str, ...]] = {
    "handler_clause": ("handler_exists", "handler_missing"),
    "inline_clause": ("absent", "present"),
    "validator_clause": ("absent", "present"),
    "handler_name_shape": (
        "plain_function",
        "schema_qualified_function",
    ),
}

_HANDLERLESS_AXES: dict[str, tuple[str, ...]] = {}

_CROSSED_NEGATIVES = frozenset(
    {
        ("target_object_state", "exists"),
        ("handler_clause", "handler_missing"),
        ("privilege_context", "non_superuser"),
        ("statement_branch", "branch_2"),
    }
)

_COMBINATION_GROUP = "create_language_required_factor_value_matrix"

_CONSUMER_ACTION = {
    "with_handler": "with_handler",
    "handlerless_legacy": "handlerless_legacy",
}


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    """Consistency + at-most-one-failure attribution."""

    tos = assignment.get("target_object_state", "absent")
    or_replace = assignment.get("or_replace_clause", "absent")
    if tos == "absent" and or_replace == "present_replace_existing":
        return False

    failures = _failure_conditions(assignment)
    return len(failures) <= 1


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive related factors from T1-T4 values in extension."""

    or_replace = a.get("or_replace_clause", "absent")
    if or_replace == "present_replace_existing":
        a["target_object_state"] = "exists"
    elif or_replace == "present_replace_new":
        a["target_object_state"] = "absent"

    handler = a.get("handler_clause", "handler_exists")
    dep = a.get("dependency_state", "ready")
    if handler == "handler_missing":
        a["dependency_state"] = "missing_handler"
    if dep == "missing_handler":
        a["handler_clause"] = "handler_missing"
    elif dep == "missing_validator":
        a["validator_clause"] = "present"

    priv = a.get("privilege_context", "superuser")
    owner = a.get("ownership_boundary", "superuser")
    if priv == "non_superuser":
        a["ownership_boundary"] = "non_superuser"
        a["superuser_requirement"] = "superuser_required_only"
    if owner == "non_superuser":
        a["privilege_context"] = "non_superuser"
        a["superuser_requirement"] = "superuser_required_only"

    sb = a.get("statement_branch", "branch_1")
    if sb == "branch_2":
        a["handler_clause"] = "handler_missing"


def _failure_conditions(a: dict[str, str]) -> list[str]:
    """Return list of active failure condition names."""

    conditions: list[str] = []
    tos = a.get("target_object_state", "absent")
    or_replace = a.get("or_replace_clause", "absent")
    if tos == "exists" and or_replace == "absent":
        conditions.append("duplicate")
    if a.get("handler_clause") == "handler_missing":
        conditions.append("missing_handler")
    if a.get("privilege_context") == "non_superuser":
        conditions.append("insufficient_privilege")
    if a.get("statement_branch") == "branch_2":
        conditions.append("handlerless")
    return conditions


_FAILURE_SQLSTATE = {
    "duplicate": ("42710", "duplicate_language_provisional"),
    "missing_handler": (
        "42804",
        "missing_handler_dependency_provisional",
    ),
    "insufficient_privilege": (
        "42501",
        "insufficient_privilege_provisional",
    ),
    "handlerless": (
        "42704",
        "handlerless_extension_resolution_failure_provisional",
    ),
}


def _branch_factor_keys(branch: str) -> dict[str, tuple[str, ...]]:
    if branch == "with_handler":
        return {**_GENERAL_AXES, **_HANDLER_AXES}
    return {**_GENERAL_AXES, **_HANDLERLESS_AXES}


def _behavior_combinations(
    branch: str,
) -> list[dict[str, str]]:
    """Cartesian product of general + branch-specific axes, filtered."""

    axes = _branch_factor_keys(branch)
    all_keys = list(axes.keys())
    all_value_lists = [axes[k] for k in all_keys]

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
    a["statement_branch"] = (
        "branch_1"
        if branch == "with_handler"
        else "branch_2"
    )
    for key, value in behavior.items():
        a[key] = value
    a["verification_mode"] = verification
    a["cleanup_mode"] = cleanup
    _derive_overlapping_factors(a)
    failures = _failure_conditions(a)
    a["expected_status"] = "failure" if failures else "success"
    return a


def _extension_multiset_sha256(
    cases: tuple[CreateLanguageFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-language-factor-extension-v1\n"
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

    tos = a.get("target_object_state", "absent")
    or_replace = a.get("or_replace_clause", "absent")
    if tos == "exists" and or_replace == "absent":
        return ("target_object_state", "exists")
    if a.get("handler_clause") == "handler_missing":
        return ("handler_clause", "handler_missing")
    if a.get("privilege_context") == "non_superuser":
        return ("privilege_context", "non_superuser")
    if a.get("statement_branch") == "branch_2":
        return ("statement_branch", "branch_2")
    return None


def build_create_language_factor_extension_plan(
    repository_root: Path,
) -> CreateLanguageFactorExtensionPlan:
    """Build the bounded post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    catalog_rows = load_shipped_applicability_universe(
        root
    ).rows_for_statement("create_language")
    if len(catalog_rows) != 42:
        raise CreateLanguageFactorExtensionError(
            "catalog row count drift"
        )

    cases: list[CreateLanguageFactorExtensionCase] = []
    raw_count = 0
    ordinal = _BASELINE_COUNT

    for branch in ("with_handler", "handlerless_legacy"):
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
                        f"CLANG-EXT|{ordinal:05d}|"
                        f"{verification}|{cleanup}"
                    )
                    cases.append(
                        CreateLanguageFactorExtensionCase(
                            ordinal=ordinal,
                            case_id=f"CREATELANGUAGE{ordinal:05d}",
                            sql_filename=(
                                f"CREATELANGUAGE{ordinal:05d}.sql"
                            ),
                            object_prefix=f"createlanguage_{ordinal:05d}_",
                            derivation_id=derivation_id,
                            derived_from_combination_group=(
                                _COMBINATION_GROUP
                            ),
                            derivation_reason=(
                                f"CREATE LANGUAGE extension: "
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

    plan = CreateLanguageFactorExtensionPlan(
        cases=tuple(cases),
        extension_multiset_sha256=_extension_multiset_sha256(
            tuple(cases)
        ),
        raw_combination_count=raw_count,
        dropped_combination_count=dropped,
    )

    expected_min = 1000 - _BASELINE_COUNT
    if len(plan.cases) < expected_min:
        raise CreateLanguageFactorExtensionError(
            f"extension case count below threshold: {len(plan.cases)}"
        )
    if len(plan.cases) > _CAP:
        raise CreateLanguageFactorExtensionError(
            "extension case count exceeds cap"
        )
    ordinals = [case.ordinal for case in plan.cases]
    if ordinals != list(
        range(_BASELINE_COUNT + 1, _BASELINE_COUNT + 1 + len(plan.cases))
    ):
        raise CreateLanguageFactorExtensionError(
            "extension ordinal gap"
        )
    if len({case.case_id for case in plan.cases}) != len(plan.cases):
        raise CreateLanguageFactorExtensionError(
            "duplicate extension case_id"
        )
    if len({case.sql_filename for case in plan.cases}) != len(plan.cases):
        raise CreateLanguageFactorExtensionError(
            "duplicate extension sql_filename"
        )
    if not all(
        case.outcome == "success" or case.outcome == "expected_failure"
        for case in plan.cases
    ):
        raise CreateLanguageFactorExtensionError(
            "unknown extension outcome"
        )
    if not all(
        case.derivation_id.startswith("CLANG-EXT|") for case in plan.cases
    ):
        raise CreateLanguageFactorExtensionError(
            "extension derivation_id prefix drift"
        )
    return plan


__all__ = [
    "CreateLanguageFactorExtensionError",
    "CreateLanguageFactorExtensionCase",
    "CreateLanguageFactorExtensionPlan",
    "build_create_language_factor_extension_plan",
    "_BASELINE_COUNT",
    "_CAP",
    "_VERIFICATION_MODES",
    "_CLEANUP_MODES",
    "_CROSSED_NEGATIVES",
    "_present_failure_pair",
    "_extension_multiset_sha256",
]
