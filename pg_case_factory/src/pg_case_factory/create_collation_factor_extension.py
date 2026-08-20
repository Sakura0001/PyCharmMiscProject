"""Bounded post-coverage extension plan for CREATE COLLATION factor regress.

The baseline :mod:`create_collation_factor_loop` assigns one local SQL
program to every ``SFV``/``GRM`` obligation (marginal 1:1).  This module
crosses the main-axis factor values with verification/cleanup axes under
an at-most-one-failure attribution policy, producing a bounded set of
additional regress programs that exercise pairwise factor interactions.

CREATE COLLATION is a catalog row DDL statement — it does not create
tables, so the bookend (DROP TABLE IF EXISTS) is never emitted.  The
``pg_catalog.pg_collation`` catalog row (not a ``pg_class`` relation) is
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
from .create_collation_factor_loop import (
    _BASELINE_DEFAULTS,
    _BUILTIN_LOCALES,
    _SFV_FAILURE_SQLSTATE,
    _SFV_FAILURE_VALUES,
)


class CreateCollationFactorExtensionError(ValueError):
    """Raised when CREATE COLLATION extension input drifts."""


@dataclass(frozen=True)
class CreateCollationFactorExtensionCase:
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
class CreateCollationFactorExtensionPlan:
    cases: tuple[CreateCollationFactorExtensionCase, ...]
    extension_multiset_sha256: str
    raw_combination_count: int
    dropped_combination_count: int


_BASELINE_COUNT = 55
_CAP = 20000

_VERIFICATION_MODES = ("pg_collation_catalog_query", "actual_collation_usage")
_CLEANUP_MODES = ("DROP_COLLATION", "DROP_COLLATION_IF_EXISTS", "DROP_COLLATION_CASCADE")

_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "object_state": ("not_exists", "already_exists"),
    "if_not_exists_clause": ("absent", "present_no_conflict", "present_with_conflict"),
    "collation_name_shape": ("plain_identifier", "quoted_identifier", "schema_qualified"),
    "privilege_level": ("schema_owner_with_create", "non_schema_owner"),
}

_DEFINE_AXES: dict[str, tuple[str, ...]] = {
    "provider": ("libc_default", "icu"),
    "locale_setting": ("LOCALE_only", "LC_COLLATE_LC_CTYPE_separate", "LOCALE_with_provider"),
    "deterministic_option": ("true_default", "false_icu_only"),
}

_FROM_AXES: dict[str, tuple[str, ...]] = {
    "from_collation_shape": ("existing_builtin_collation", "existing_user_collation", "nonexistent_collation"),
    "from_collation_dependency": ("from_exists", "from_not_exists"),
}

_CROSSED_NEGATIVES = frozenset(
    {
        ("object_state", "already_exists"),
        ("privilege_level", "non_schema_owner"),
        ("from_collation_shape", "nonexistent_collation"),
        ("from_collation_dependency", "from_not_exists"),
        ("deterministic_option", "false_icu_only"),
    }
)

_COMBINATION_GROUP = "create_collation_required_factor_value_matrix"

_CONSUMER_ACTION = {
    "define_with_params": "define_with_params",
    "from_existing": "from_existing",
}


def _is_valid_combination(assignment: dict[str, str]) -> bool:
    """Consistency + at-most-one-failure attribution."""

    os = assignment.get("object_state", "not_exists")
    ifne = assignment.get("if_not_exists_clause", "absent")
    if os == "not_exists" and ifne == "present_with_conflict":
        return False
    if os == "already_exists" and ifne == "present_no_conflict":
        return False

    fcs = assignment.get("from_collation_shape", "existing_builtin_collation")
    fcd = assignment.get("from_collation_dependency", "from_exists")
    if fcs == "nonexistent_collation" and fcd == "from_exists":
        return False
    if fcs != "nonexistent_collation" and fcd == "from_not_exists":
        return False

    failures = [
        pair
        for pair in _CROSSED_NEGATIVES
        if assignment.get(pair[0]) == pair[1]
    ]
    return len(failures) <= 1


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors from T1-T4 values in extension."""

    os = a.get("object_state", "not_exists")
    ifne = a.get("if_not_exists_clause", "absent")
    if os == "already_exists" and ifne == "absent":
        a["duplicate_collation"] = "same_schema_same_name_no_ifne"
    elif os == "already_exists" and ifne == "present_with_conflict":
        a["duplicate_collation"] = "same_schema_same_name_with_ifne"

    fcs = a.get("from_collation_shape", "existing_builtin_collation")
    fcd = a.get("from_collation_dependency", "from_exists")
    if fcs == "nonexistent_collation":
        a["from_collation_dependency"] = "from_not_exists"
        fcd = "from_not_exists"
    elif fcd == "from_not_exists":
        a["from_collation_shape"] = "nonexistent_collation"
        fcs = "nonexistent_collation"

    prov = a.get("provider", "libc_default")
    det = a.get("deterministic_option", "true_default")
    rules = a.get("rules_setting", "no_rules")
    if prov == "libc_default" and det == "false_icu_only":
        a["nondeterministic_non_icu"] = "deterministic_false_libc"
    if prov == "libc_default" and rules == "with_rules":
        a["rules_non_icu"] = "rules_with_libc"
    if prov == "icu":
        a["icu_availability"] = "icu_available"

    priv = a.get("privilege_level", "schema_owner_with_create")
    if priv == "non_schema_owner":
        a["insufficient_privilege"] = "no_create_on_schema"

    ls = a.get("locale_setting", "LOCALE_only")
    if ls in _BUILTIN_LOCALES:
        a["provider"] = "builtin"


def _failure_conditions(a: dict[str, str]) -> list[str]:
    """Return list of active failure condition names."""

    conditions: list[str] = []
    os = a.get("object_state", "not_exists")
    ifne = a.get("if_not_exists_clause", "absent")
    if os == "already_exists" and ifne == "absent":
        conditions.append("duplicate")
    fcs = a.get("from_collation_shape", "")
    fcd = a.get("from_collation_dependency", "")
    if fcs == "nonexistent_collation" or fcd == "from_not_exists":
        conditions.append("missing_source")
    priv = a.get("privilege_level", "")
    if priv == "non_schema_owner":
        conditions.append("insufficient_privilege")
    prov = a.get("provider", "")
    det = a.get("deterministic_option", "")
    if prov == "libc_default" and det == "false_icu_only":
        conditions.append("nondeterministic")
    return conditions


_FAILURE_SQLSTATE = {
    "duplicate": ("42710", "duplicate_collation_provisional"),
    "missing_source": ("42704", "missing_source_collation_provisional"),
    "insufficient_privilege": ("42501", "insufficient_privilege_provisional"),
    "nondeterministic": ("22023", "nondeterministic_non_icu_provisional"),
}


def _branch_factor_keys(branch: str) -> tuple[str, ...]:
    if branch == "define_with_params":
        return ("provider", "locale_setting", "deterministic_option")
    return ("from_collation_shape", "from_collation_dependency")


def _behavior_combinations(
    branch: str,
) -> list[dict[str, str]]:
    """Cartesian product of general + branch-specific axes, filtered."""

    general_items = list(_GENERAL_AXES.items())
    branch_axes = _DEFINE_AXES if branch == "define_with_params" else _FROM_AXES
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
    a["statement_branch"] = (
        "branch_define_with_params"
        if branch == "define_with_params"
        else "branch_from_existing"
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
    cases: tuple[CreateCollationFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-collation-factor-extension-v1\n"
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

    os = a.get("object_state", "not_exists")
    ifne = a.get("if_not_exists_clause", "absent")
    if os == "already_exists" and ifne == "absent":
        return ("object_state", "already_exists")
    fcs = a.get("from_collation_shape", "")
    if fcs == "nonexistent_collation":
        return ("from_collation_shape", "nonexistent_collation")
    fcd = a.get("from_collation_dependency", "")
    if fcd == "from_not_exists":
        return ("from_collation_dependency", "from_not_exists")
    priv = a.get("privilege_level", "")
    if priv == "non_schema_owner":
        return ("privilege_level", "non_schema_owner")
    prov = a.get("provider", "")
    det = a.get("deterministic_option", "")
    if prov == "libc_default" and det == "false_icu_only":
        return ("deterministic_option", "false_icu_only")
    return None


def build_create_collation_factor_extension_plan(
    repository_root: Path,
) -> CreateCollationFactorExtensionPlan:
    """Build the bounded post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    catalog_rows = load_shipped_applicability_universe(
        root
    ).rows_for_statement("create_collation")
    if len(catalog_rows) != 50:
        raise CreateCollationFactorExtensionError(
            "catalog row count drift"
        )

    cases: list[CreateCollationFactorExtensionCase] = []
    raw_count = 0
    ordinal = _BASELINE_COUNT

    for branch in ("define_with_params", "from_existing"):
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
                        f"CCOL-EXT|{ordinal:05d}|"
                        f"{verification}|{cleanup}"
                    )
                    cases.append(
                        CreateCollationFactorExtensionCase(
                            ordinal=ordinal,
                            case_id=f"CREATECOLLATION{ordinal:05d}",
                            sql_filename=f"CREATECOLLATION{ordinal:05d}.sql",
                            object_prefix=f"createcollation_{ordinal:05d}_",
                            derivation_id=derivation_id,
                            derived_from_combination_group=_COMBINATION_GROUP,
                            derivation_reason=(
                                f"CREATE COLLATION extension: "
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

    plan = CreateCollationFactorExtensionPlan(
        cases=tuple(cases),
        extension_multiset_sha256=_extension_multiset_sha256(
            tuple(cases)
        ),
        raw_combination_count=raw_count,
        dropped_combination_count=dropped,
    )

    expected_min = 1000 - _BASELINE_COUNT
    if len(plan.cases) < expected_min:
        raise CreateCollationFactorExtensionError(
            f"extension case count below threshold: {len(plan.cases)}"
        )
    if len(plan.cases) > _CAP:
        raise CreateCollationFactorExtensionError(
            "extension case count exceeds cap"
        )
    ordinals = [case.ordinal for case in plan.cases]
    if ordinals != list(range(_BASELINE_COUNT + 1, _BASELINE_COUNT + 1 + len(plan.cases))):
        raise CreateCollationFactorExtensionError(
            "extension ordinal gap"
        )
    if len({case.case_id for case in plan.cases}) != len(plan.cases):
        raise CreateCollationFactorExtensionError(
            "duplicate extension case_id"
        )
    if len({case.sql_filename for case in plan.cases}) != len(plan.cases):
        raise CreateCollationFactorExtensionError(
            "duplicate extension sql_filename"
        )
    if not all(case.outcome == "success" or case.outcome == "expected_failure" for case in plan.cases):
        raise CreateCollationFactorExtensionError(
            "unknown extension outcome"
        )
    if not all(case.derivation_id.startswith("CCOL-EXT|") for case in plan.cases):
        raise CreateCollationFactorExtensionError(
            "extension derivation_id prefix drift"
        )
    return plan


__all__ = [
    "CreateCollationFactorExtensionError",
    "CreateCollationFactorExtensionCase",
    "CreateCollationFactorExtensionPlan",
    "build_create_collation_factor_extension_plan",
    "_BASELINE_COUNT",
    "_CAP",
    "_VERIFICATION_MODES",
    "_CLEANUP_MODES",
    "_CROSSED_NEGATIVES",
    "_present_failure_pair",
    "_extension_multiset_sha256",
]
