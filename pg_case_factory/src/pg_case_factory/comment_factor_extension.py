"""Bounded post-coverage cross-factor extension expander for COMMENT ON.

The marginal factor-value-loop (:mod:`comment_factor_loop`) is the
required baseline: one program per factor value, 117 local SFV cases.
This module adds the bounded post-coverage extension phase allowed by
``comment.yaml`` ``post_coverage_extension_policy.enabled: true``:
cross-factor combinations of the positive T1-T2 behaviour axes across
all 43 ``object_type`` branches, with at most one failure-causing value
per case so attribution stays clean, and ``verification_mode`` crossed
so every declared T6 value is exercised.

The T5 single-value factors (object_not_exist, privilege_denied,
prerequisite_object, schema_privilege, role_privilege) are derived from
their T1-T2 counterparts, not crossed as axes.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path

import yaml

from .comment_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_comment_factor_loop_plan,
)


class CommentFactorExtensionError(ValueError):
    """Raised when a frozen COMMENT extension input drifts."""


@dataclass(frozen=True)
class CommentFactorExtensionCase:
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
class CommentFactorExtensionPlan:
    cases: tuple[CommentFactorExtensionCase, ...]
    extension_multiset_sha256: str
    derived_combinations_yaml: str
    dropped_count: int
    raw_combination_count: int


_BASELINE_COUNT = 117
_CAP = 20000

_VERIFICATION_MODES = (
    "obj_description_query",
    "col_description_query",
    "shobj_description_query",
    "psql_dd_command",
    "catalog_query_pg_description",
)
_CLEANUP_MODES = (
    "drop_prerequisite_object",
    "comment_is_null_cleanup",
    "cascade_drop",
)

# General axes crossed for ALL 43 object_type branches.
_GENERAL_AXES: dict[str, tuple[str, ...]] = {
    "comment_action": (
        "set_comment",
        "remove_comment_null",
        "remove_comment_empty",
    ),
    "privilege_level": (
        "object_owner",
        "non_owner",
        "superuser",
        "createrole_with_admin",
    ),
    "object_state": (
        "object_exists",
        "object_not_exists",
    ),
}

# Dense positive baseline (all success values).
_BASELINE: dict[str, str] = {
    "object_type": "table",
    "comment_action": "set_comment",
    "expected_status": "success",
    "privilege_level": "object_owner",
    "object_state": "object_exists",
    "identifier_format": "simple_name",
    "object_name_shape": "simple_id",
    "column_name_shape": "simple_column_name",
    "constraint_name_shape": "simple_constraint_name",
    "function_signature_shape": "no_args",
    "operator_signature_shape": "both_types_specified",
    "comment_text_shape": "short_literal",
    "prerequisite_object": "prerequisite_exists",
    "schema_privilege": "has_schema_privilege",
    "role_privilege": "owner",
    "shared_object_scope": "locally_visible",
    "object_not_exist": "object_exists",
    "privilege_denied": "owner_success",
    "wrong_identifier_format": "correct_format",
    "cast_type_not_exist": "both_types_exist",
    "aggregate_signature_invalid": "signature_matches",
    "operator_none_misuse": "correct_none_usage",
    "transform_type_or_lang_not_exist": "both_exist",
    "large_object_oid_invalid": "valid_oid",
}

# Crossed behaviour-negative (factor, value) pairs — one representative
# per failure scenario.
_CROSSED_NEGATIVES = frozenset(
    {
        ("object_state", "object_not_exists"),
        ("privilege_level", "non_owner"),
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
    """Applicability + at-most-one-failure attribution."""

    return _failure_unit_count(assignment) <= 1


def _derive_t5_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T2 values."""

    os_ = a.get("object_state", "object_exists")
    pl = a.get("privilege_level", "object_owner")

    if os_ == "object_not_exists":
        a["object_not_exist"] = "object_not_exists"
        a["prerequisite_object"] = "prerequisite_not_exists"
    else:
        a["object_not_exist"] = "object_exists"
        a["prerequisite_object"] = "prerequisite_exists"

    if pl == "non_owner":
        a["privilege_denied"] = "non_owner_failure"
        a["schema_privilege"] = "lacks_schema_privilege"
        a["role_privilege"] = "no_privilege"
    elif pl == "superuser":
        a["privilege_denied"] = "superuser_success"
        a["schema_privilege"] = "has_schema_privilege"
        a["role_privilege"] = "owner"
    elif pl == "createrole_with_admin":
        a["privilege_denied"] = "owner_success"
        a["schema_privilege"] = "has_schema_privilege"
        a["role_privilege"] = "createrole_with_admin_option"
    else:
        a["privilege_denied"] = "owner_success"
        a["schema_privilege"] = "has_schema_privilege"
        a["role_privilege"] = "owner"

    failures = _failure_unit_count(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _behavior_combinations() -> list[dict[str, str]]:
    """Full positive-axis assignments passing the filter."""

    combos: list[dict[str, str]] = []
    object_types = sorted(
        {
            "access_method", "aggregate", "cast", "collation",
            "column", "constraint_on_domain", "constraint_on_table",
            "conversion", "database", "domain", "extension",
            "event_trigger", "foreign_data_wrapper", "foreign_table",
            "function", "index", "large_object", "materialized_view",
            "operator", "operator_class", "operator_family", "policy",
            "procedural_language", "procedure", "publication", "role",
            "routine", "rule", "schema", "sequence", "server",
            "statistics", "subscription", "table", "tablespace",
            "text_search_configuration", "text_search_dictionary",
            "text_search_parser", "text_search_template", "transform",
            "trigger", "type", "view",
        }
    )
    names = list(_GENERAL_AXES)
    for ot in object_types:
        for values in itertools.product(
            *[_GENERAL_AXES[n] for n in names]
        ):
            assignment: dict[str, str] = dict(_BASELINE)
            assignment["object_type"] = ot
            for name, value in zip(names, values):
                assignment[name] = value
            _derive_t5_factors(assignment)
            if not _is_valid_combination(assignment):
                continue
            if len(assignment) != len(set(assignment)):
                raise CommentFactorExtensionError(
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
    cases: tuple[CommentFactorExtensionCase, ...],
) -> str:
    digest = hashlib.sha256(
        b"comment-factor-extension-v1\n"
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
    cases: tuple[CommentFactorExtensionCase, ...],
) -> str:
    entries: list[dict[str, object]] = []
    for case in cases:
        assignment = dict(case.factor_assignment)
        pair = _present_failure_pair(assignment)
        entries.append(
            {
                "id": case.derivation_id,
                "title": (
                    f"COMMENT ON extension "
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
                    "resolver": "comment_factor_extension",
                    "attribution_pair": pair,
                    "success_when": case.outcome == "success",
                    "failure_when": (
                        case.outcome == "expected_failure"
                    ),
                },
                "sql_shape": {
                    "target": "COMMENT ON",
                    "primary_fence": "primary-target-begin/end",
                    "consumer_action_id": case.consumer_action_id,
                },
                "verification": {
                    "verification_mode": assignment.get(
                        "verification_mode", "obj_description_query"
                    ),
                    "expected_sqlstate": case.expected_sqlstate,
                },
                "cleanup": {
                    "cleanup_mode": assignment.get(
                        "cleanup_mode", "drop_prerequisite_object"
                    ),
                },
            }
        )
    return yaml.safe_dump(
        entries, sort_keys=False, allow_unicode=True
    )


def build_comment_factor_extension_plan(
    repository_root: Path,
) -> CommentFactorExtensionPlan:
    """Build the bounded COMMENT post-coverage extension plan."""

    root = Path(repository_root).resolve(strict=True)
    build_comment_factor_loop_plan(root)
    behaviors = _behavior_combinations()
    behaviors.sort(key=lambda a: tuple(sorted(a.items())))
    cases: list[CommentFactorExtensionCase] = []
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
                cases.append(
                    CommentFactorExtensionCase(
                        ordinal=ordinal,
                        case_id=f"COMMENT{ordinal:05d}",
                        sql_filename=f"COMMENT{ordinal:05d}.sql",
                        object_prefix=f"comment_{ordinal:05d}_",
                        derivation_id=(
                            f"COMMENT-EXT|{ordinal:05d}|"
                            f"{verification}|{cleanup}"
                        ),
                        derived_from_combination_group=(
                            "comment_required_factor_value_matrix"
                        ),
                        derivation_reason=(
                            "cross-factor extension: "
                            f"object_type="
                            f"{assignment['object_type']} "
                            f"x comment_action="
                            f"{assignment['comment_action']} "
                            f"x privilege_level="
                            f"{assignment['privilege_level']} "
                            f"x object_state="
                            f"{assignment['object_state']} "
                            f"x verification_mode={verification} "
                            f"x cleanup_mode={cleanup}"
                        ),
                        factor_assignment=tuple(
                            sorted(assignment.items())
                        ),
                        consumer_action_id=assignment[
                            "object_type"
                        ],
                        outcome=outcome,
                        expected_sqlstate=sqlstate,
                        expected_failure_reason=reason,
                        is_extension=True,
                    )
                )
    dropped = max(0, raw - _CAP)
    cases_tuple = tuple(cases)
    return CommentFactorExtensionPlan(
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
    "CommentFactorExtensionError",
    "CommentFactorExtensionCase",
    "CommentFactorExtensionPlan",
    "build_comment_factor_extension_plan",
]
