"""Bounded post-coverage cross-factor extension expander for CREATE CONVERSION.

The marginal factor-value-loop (:mod:`create_conversion_factor_loop`) is
the required baseline: one program per factor value, 66 local cases
(GRM 2 + SFV 64).  This module adds the bounded post-coverage extension
phase allowed by ``create_conversion.yaml``
``post_coverage_extension_policy.enabled: true``: cross-factor
combinations of the positive T1-T4 behaviour axes across both grammar
branches, with at most one failure-causing value per case so attribution
stays clean, and ``verification_mode`` / ``cleanup_mode`` crossed so
every declared T6 value is exercised.

CREATE CONVERSION requires CREATE privilege on the target schema and
EXECUTE privilege on the conversion function, so
``privilege_level=non_owner_no_create`` and
``function_privilege=no_execute`` are unconditional failures.  The T5
single-value factors (duplicate_conversion_name,
duplicate_default_for_encoding_pair, nonexistent_function,
function_signature_mismatch, sql_ascii_encoding, nonexistent_encoding,
nonexistent_schema) are derived from their T1-T4 counterparts, not
crossed as axes.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .create_conversion_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_create_conversion_factor_loop_plan,
)


class CreateConversionFactorExtensionError(ValueError):
    """Raised when a frozen CREATE CONVERSION extension input drifts."""


@dataclass(frozen=True)
class CreateConversionFactorExtensionCase:
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
class CreateConversionFactorExtensionPlan:
    cases: tuple[CreateConversionFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 66
_CAP = 20000

_VERIFICATION_MODES = (
    "catalog_query_pg_conversion",
    "error_assertion",
)
_CLEANUP_MODES = (
    "drop_conversion",
    "cascade_drop",
)

_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "object_state": (
        "not_exists",
        "exists",
        "same_encoding_pair_default_exists",
    ),
    "privilege_level": (
        "superuser",
        "schema_owner_with_create",
        "non_owner_no_create",
    ),
    "conversion_function_state": (
        "function_exists_valid_signature",
        "function_not_exists",
        "function_exists_invalid_signature",
    ),
    "function_privilege": (
        "has_execute",
        "no_execute",
    ),
    "schema_existence": (
        "schema_exists",
        "schema_not_exists",
    ),
}

_BASELINE: dict[str, str] = {
    "statement_branch": "branch_create_conversion",
    "grammar_branch": "branch_create_conversion",
    "target_action": "create_conversion",
    "source_encoding": "UTF8",
    "dest_encoding": "LATIN1",
    "object_state": "not_exists",
    "expected_status": "success",
    "default_flag": "omitted",
    "conversion_function_state": "function_exists_valid_signature",
    "encoding_pair_direction": "single_direction",
    "conversion_name_shape": "simple_id",
    "function_name_shape": "simple_id",
    "encoding_name_shape": "valid_encoding_name",
    "privilege_level": "superuser",
    "schema_existence": "schema_exists",
    "function_privilege": "has_execute",
    "duplicate_conversion_name": "no_conflict",
    "duplicate_default_for_encoding_pair": "no_existing_default",
    "nonexistent_function": "function_exists",
    "function_signature_mismatch": "valid_conv_proc_signature",
    "sql_ascii_encoding": "neither_is_sql_ascii",
    "nonexistent_encoding": "encoding_exists",
    "nonexistent_schema": "schema_exists",
    "verification_mode": "catalog_query_pg_conversion",
    "cleanup_mode": "drop_conversion",
}

_BRANCH_CONFIG: tuple[
    tuple[str, str, dict[str, tuple[str, ...]]], ...
] = (
    (
        "branch_create_conversion",
        "create_conversion",
        {
            "conversion_name_shape": (
                "simple_id",
                "quoted_id",
                "schema_qualified",
                "reserved_word_as_name",
                "duplicate_name",
            ),
            "function_name_shape": (
                "simple_id",
                "schema_qualified",
                "nonexistent_name",
            ),
        },
    ),
    (
        "branch_create_default_conversion",
        "create_default_conversion",
        {
            "encoding_pair_direction": (
                "single_direction",
                "reverse_direction_exists",
            ),
            "conversion_name_shape": (
                "simple_id",
                "quoted_id",
                "schema_qualified",
                "reserved_word_as_name",
                "duplicate_name",
            ),
            "function_name_shape": (
                "simple_id",
                "schema_qualified",
                "nonexistent_name",
            ),
        },
    ),
)

_CROSSED_NEGATIVES = frozenset(
    {
        ("object_state", "exists"),
        ("object_state", "same_encoding_pair_default_exists"),
        ("privilege_level", "non_owner_no_create"),
        ("conversion_function_state", "function_not_exists"),
        ("conversion_function_state", "function_exists_invalid_signature"),
        ("conversion_name_shape", "duplicate_name"),
        ("function_name_shape", "nonexistent_name"),
        ("schema_existence", "schema_not_exists"),
        ("function_privilege", "no_execute"),
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

    os_ = assignment.get("object_state", "not_exists")
    cns = assignment.get("conversion_name_shape", "simple_id")
    if os_ == "exists" and cns != "duplicate_name":
        return False
    if os_ != "exists" and cns == "duplicate_name":
        return False

    sx = assignment.get("schema_existence", "schema_exists")
    if sx == "schema_not_exists":
        if cns == "schema_qualified":
            return False
        if assignment.get("function_name_shape", "simple_id") == "schema_qualified":
            return False

    return _failure_unit_count(assignment) <= 1


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values."""

    os_ = a.get("object_state", "not_exists")
    dcn = a.get("duplicate_conversion_name", "no_conflict")
    cns = a.get("conversion_name_shape", "simple_id")

    if os_ == "exists" or dcn == "same_schema_conflict" or cns == "duplicate_name":
        a["object_state"] = "exists"
        a["duplicate_conversion_name"] = "same_schema_conflict"
        a["conversion_name_shape"] = "duplicate_name"
    else:
        a["duplicate_conversion_name"] = "no_conflict"

    dd = a.get(
        "duplicate_default_for_encoding_pair", "no_existing_default"
    )
    if (
        os_ == "same_encoding_pair_default_exists"
        or dd == "default_already_exists"
    ):
        a["object_state"] = "same_encoding_pair_default_exists"
        a["duplicate_default_for_encoding_pair"] = "default_already_exists"
    else:
        a["duplicate_default_for_encoding_pair"] = "no_existing_default"

    cfs = a.get(
        "conversion_function_state",
        "function_exists_valid_signature",
    )
    fns = a.get("function_name_shape", "simple_id")
    nf = a.get("nonexistent_function", "function_exists")
    if (
        cfs == "function_not_exists"
        or fns == "nonexistent_name"
        or nf == "function_not_exists"
    ):
        a["conversion_function_state"] = "function_not_exists"
        a["function_name_shape"] = "nonexistent_name"
        a["nonexistent_function"] = "function_not_exists"
    else:
        a["nonexistent_function"] = "function_exists"

    fsm = a.get(
        "function_signature_mismatch", "valid_conv_proc_signature"
    )
    if (
        cfs == "function_exists_invalid_signature"
        or fsm == "invalid_signature"
    ):
        a["conversion_function_state"] = (
            "function_exists_invalid_signature"
        )
        a["function_signature_mismatch"] = "invalid_signature"
    else:
        a["function_signature_mismatch"] = "valid_conv_proc_signature"

    se = a.get("source_encoding", "UTF8")
    de = a.get("dest_encoding", "LATIN1")
    sae = a.get("sql_ascii_encoding", "neither_is_sql_ascii")
    ens = a.get("encoding_name_shape", "valid_encoding_name")
    if (
        se == "SQL_ASCII"
        or sae == "source_is_sql_ascii"
        or ens == "sql_ascii_encoding_name"
    ):
        a["source_encoding"] = "SQL_ASCII"
        a["sql_ascii_encoding"] = "source_is_sql_ascii"
        a["encoding_name_shape"] = "sql_ascii_encoding_name"
    elif de == "SQL_ASCII" or sae == "dest_is_sql_ascii":
        a["dest_encoding"] = "SQL_ASCII"
        a["sql_ascii_encoding"] = "dest_is_sql_ascii"
        a["encoding_name_shape"] = "sql_ascii_encoding_name"
    else:
        a["sql_ascii_encoding"] = "neither_is_sql_ascii"

    ne = a.get("nonexistent_encoding", "encoding_exists")
    if (
        ens == "nonexistent_encoding_name"
        or ne == "encoding_not_exists"
    ):
        a["encoding_name_shape"] = "nonexistent_encoding_name"
        a["nonexistent_encoding"] = "encoding_not_exists"
    else:
        a["nonexistent_encoding"] = "encoding_exists"

    sx = a.get("schema_existence", "schema_exists")
    ns = a.get("nonexistent_schema", "schema_exists")
    if sx == "schema_not_exists" or ns == "schema_not_exists":
        a["schema_existence"] = "schema_not_exists"
        a["nonexistent_schema"] = "schema_not_exists"
    else:
        a["nonexistent_schema"] = "schema_exists"

    fp = a.get("function_privilege", "has_execute")
    if fp == "no_execute":
        if a.get("privilege_level", "superuser") == "superuser":
            a["privilege_level"] = "schema_owner_with_create"

    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments (T6 at baseline) passing the filter."""

    combos: list[dict[str, str]] = []
    for branch, action, axes in _BRANCH_CONFIG:
        all_axes = dict(_GENERAL_AXES)
        all_axes.update(axes)
        names = list(all_axes)
        for values in itertools.product(
            *[all_axes[n] for n in names]
        ):
            assignment: dict[str, str] = dict(_BASELINE)
            assignment["statement_branch"] = branch
            assignment["grammar_branch"] = branch
            assignment["target_action"] = action
            if action == "create_default_conversion":
                assignment["default_flag"] = "specified_default"
            else:
                assignment["default_flag"] = "omitted"
            for name, value in zip(names, values):
                assignment[name] = value
            _derive_t5_factors(assignment)
            if not _is_valid_combination(assignment):
                continue
            if len(assignment) != len(set(assignment)):
                raise CreateConversionFactorExtensionError(
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
    cases: tuple[CreateConversionFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-conversion-factor-extension-v1\n"
    )
    for case in cases:
        digest.update(
            json.dumps(
                {
                    "derivation_id": case.derivation_id,
                    "factor_assignment": list(
                        case.factor_assignment
                    ),
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
    cases: tuple[CreateConversionFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"CREATE CONVERSION extension "
                    f"{case.ordinal:05d}: "
                    f"{case.consumer_action_id}"
                ),
                "derived_from_combination_group": (
                    case.derived_from_combination_group
                ),
                "derivation_reason": case.derivation_reason,
                "factors": assignment,
                "expected_status_policy": case.outcome,
                "compatibility": {
                    "resolver": (
                        "create_conversion_factor_extension"
                    ),
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "CREATE CONVERSION",
                    "primary_fence": (
                        "primary-target-begin/end"
                    ),
                    "consumer_action_id": case.consumer_action_id,
                },
                "verification": {
                    "verification_mode": assignment[
                        "verification_mode"
                    ],
                    "expected_sqlstate": case.expected_sqlstate,
                },
                "cleanup": {
                    "cleanup_mode": assignment["cleanup_mode"],
                },
            }
        )
    return yaml.safe_dump(
        entries, sort_keys=False, allow_unicode=True
    )


def build_create_conversion_factor_extension_plan(
    repository_root: Path,
) -> CreateConversionFactorExtensionPlan:
    """Build the bounded CREATE CONVERSION post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_create_conversion_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[CreateConversionFactorExtensionCase] = []
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
                outcome, sqlstate, reason = _outcome_for(
                    assignment
                )
                ordinal += 1
                cases.append(
                    CreateConversionFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=(
                            f"CREATECONVERSION{ordinal:05d}"
                        ),
                        sql_filename=(
                            f"CREATECONVERSION{ordinal:05d}.sql"
                        ),
                        object_prefix=(
                            f"createconversion_{ordinal:05d}_"
                        ),
                        derivation_id=(
                            f"CCONV-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "create_conversion_required_factor_"
                            "value_matrix"
                        ),
                        derivation_reason=(
                            "cross-factor extension: "
                            f"target_action="
                            f"{assignment['target_action']} "
                            f"x object_state="
                            f"{assignment['object_state']} "
                            f"x privilege_level="
                            f"{assignment['privilege_level']} "
                            f"x conversion_function_state="
                            f"{assignment['conversion_function_state']} "
                            f"x verification_mode="
                            f"{verification} "
                            f"x cleanup_mode={cleanup}"
                        ),
                        factor_assignment=tuple(
                            sorted(assignment.items())
                        ),
                        consumer_action_id=assignment[
                            "target_action"
                        ],
                        outcome=outcome,
                        expected_sqlstate=sqlstate,
                        expected_failure_reason=reason,
                        is_extension=True,
                    )
                )
    dropped = max(0, raw - _CAP)
    cases_tuple = tuple(cases)
    return CreateConversionFactorExtensionPlan(
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
    "CreateConversionFactorExtensionError",
    "CreateConversionFactorExtensionCase",
    "CreateConversionFactorExtensionPlan",
    "build_create_conversion_factor_extension_plan",
]
