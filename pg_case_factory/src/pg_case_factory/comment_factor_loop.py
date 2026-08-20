"""Factor-value-loop obligation ledger for PostgreSQL 18.4 COMMENT ON.

This module compiles the marginal ``SFV`` obligation ledger for
``COMMENT ON``.  COMMENT ON is a PostgreSQL DDL statement that attaches
or removes a comment on a database object.  The statement has 43
official synopsis branches (one per ``object_type`` value), and the
``IS { string_literal | NULL }`` clause supports three comment actions
(set_comment, remove_comment_null, remove_comment_empty).

Each local obligation becomes exactly one regress program.  The 117
canonical ``SFV`` rows are loaded from the shipped applicability
universe (``postgresql_18_4_factor_audit.tsv``).  There are no
separate ``GRM`` obligations because ``object_type`` — the grammar
branch axis — is itself a T1 factor in the TSV.  No obligations are
delegated.

Provisional SQLSTATE expectations: 42704 (object does not exist),
42501 (insufficient privilege), 42601 (syntax error), 42883 (function
does not exist).  The DB phase verifies on PG 18.4.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CommentFactorLoopError(ValueError):
    """Raised when a frozen COMMENT obligation input drifts."""


@dataclass(frozen=True)
class CommentFactorObligation:
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
class CommentFactorCase:
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
class CommentFactorLoopPlan:
    obligations: tuple[CommentFactorObligation, ...]
    cases: tuple[CommentFactorCase, ...]
    delegated: tuple[CommentFactorObligation, ...]
    obligation_multiset_sha256: str


_DOC_SOURCE = "postgresql-18.4-doc:sql-comment"

# Default consumer (object_type) for factors whose value is not
# bound to a specific object_type branch.
_REPRESENTATIVE = "table"

# Factor -> default consumer object_type.
_SFV_FACTOR_CONSUMER: dict[str, str] = {
    "object_type": _REPRESENTATIVE,
    "comment_action": _REPRESENTATIVE,
    "expected_status": _REPRESENTATIVE,
    "privilege_level": _REPRESENTATIVE,
    "object_state": _REPRESENTATIVE,
    "identifier_format": _REPRESENTATIVE,
    "object_name_shape": _REPRESENTATIVE,
    "column_name_shape": "column",
    "constraint_name_shape": "constraint_on_table",
    "function_signature_shape": "function",
    "operator_signature_shape": "operator",
    "comment_text_shape": _REPRESENTATIVE,
    "prerequisite_object": _REPRESENTATIVE,
    "schema_privilege": "schema",
    "role_privilege": "role",
    "shared_object_scope": _REPRESENTATIVE,
    "object_not_exist": _REPRESENTATIVE,
    "privilege_denied": _REPRESENTATIVE,
    "wrong_identifier_format": _REPRESENTATIVE,
    "cast_type_not_exist": "cast",
    "aggregate_signature_invalid": "aggregate",
    "operator_none_misuse": "operator",
    "transform_type_or_lang_not_exist": "transform",
    "large_object_oid_invalid": "large_object",
    "verification_mode": _REPRESENTATIVE,
    "cleanup_mode": _REPRESENTATIVE,
}

# Value-dependent consumer overrides.
_FACTOR_VALUE_CONSUMER: dict[tuple[str, str], str] = {
    ("privilege_level", "superuser"): "access_method",
    ("privilege_level", "createrole_with_admin"): "role",
    ("identifier_format", "composite_format_column"): "column",
    ("identifier_format", "composite_format_constraint"): "constraint_on_table",
    ("identifier_format", "composite_format_operator"): "operator",
    ("identifier_format", "composite_format_aggregate"): "aggregate",
    ("shared_object_scope", "globally_visible"): "database",
    ("privilege_denied", "superuser_success"): "access_method",
    ("wrong_identifier_format", "missing_relation_for_column"): "column",
    ("wrong_identifier_format", "missing_on_for_constraint"): "constraint_on_table",
}

# Canonical (factor, value) pairs that reach the PG target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "object_not_exists"),
        ("privilege_level", "non_owner"),
        ("object_not_exist", "object_not_exists"),
        ("privilege_denied", "non_owner_failure"),
        ("wrong_identifier_format", "missing_relation_for_column"),
        ("wrong_identifier_format", "missing_on_for_constraint"),
        ("cast_type_not_exist", "source_type_not_exist"),
        ("cast_type_not_exist", "target_type_not_exist"),
        ("aggregate_signature_invalid", "signature_mismatch"),
        ("operator_none_misuse", "misplaced_none"),
        ("transform_type_or_lang_not_exist", "type_not_exist"),
        ("transform_type_or_lang_not_exist", "lang_not_exist"),
        ("large_object_oid_invalid", "nonexistent_oid"),
        ("prerequisite_object", "prerequisite_not_exists"),
        ("schema_privilege", "lacks_schema_privilege"),
        ("role_privilege", "no_privilege"),
    }
)

_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "object_does_not_exist_provisional",
    ),
    ("object_state", "object_not_exists"): (
        "42704",
        "object_does_not_exist_provisional",
    ),
    ("privilege_level", "non_owner"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("object_not_exist", "object_not_exists"): (
        "42704",
        "object_does_not_exist_provisional",
    ),
    ("privilege_denied", "non_owner_failure"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("wrong_identifier_format", "missing_relation_for_column"): (
        "42601",
        "syntax_error_provisional",
    ),
    ("wrong_identifier_format", "missing_on_for_constraint"): (
        "42601",
        "syntax_error_provisional",
    ),
    ("cast_type_not_exist", "source_type_not_exist"): (
        "42704",
        "type_does_not_exist_provisional",
    ),
    ("cast_type_not_exist", "target_type_not_exist"): (
        "42704",
        "type_does_not_exist_provisional",
    ),
    ("aggregate_signature_invalid", "signature_mismatch"): (
        "42883",
        "function_does_not_exist_provisional",
    ),
    ("operator_none_misuse", "misplaced_none"): (
        "42601",
        "syntax_error_provisional",
    ),
    ("transform_type_or_lang_not_exist", "type_not_exist"): (
        "42704",
        "type_does_not_exist_provisional",
    ),
    ("transform_type_or_lang_not_exist", "lang_not_exist"): (
        "42704",
        "language_does_not_exist_provisional",
    ),
    ("large_object_oid_invalid", "nonexistent_oid"): (
        "42704",
        "large_object_does_not_exist_provisional",
    ),
    ("prerequisite_object", "prerequisite_not_exists"): (
        "42704",
        "object_does_not_exist_provisional",
    ),
    ("schema_privilege", "lacks_schema_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("role_privilege", "no_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
}


def _canonical_consumer(row) -> str:
    key = (row.factor, row.value)
    if key in _FACTOR_VALUE_CONSUMER:
        return _FACTOR_VALUE_CONSUMER[key]
    if row.factor == "object_type":
        return row.value
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise CommentFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CommentFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("comment")
    if len(catalog_rows) != 117:
        raise CommentFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[CommentFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CommentFactorObligation(
                ordinal=0,
                obligation_id=f"COMMENT-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CommentFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"comment-factor-obligations-v1\n"
    )
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


# Dense baseline defaults (all positive success values).
_BASELINE_DEFAULTS: dict[str, str] = {
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
    "verification_mode": "obj_description_query",
    "cleanup_mode": "drop_prerequisite_object",
}


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive overlapping T5/T2 values and expected_status from T1-T4."""

    os_ = a.get("object_state", "object_exists")
    one = a.get("object_not_exist", "object_exists")
    po = a.get("prerequisite_object", "prerequisite_exists")
    pl = a.get("privilege_level", "object_owner")
    pd = a.get("privilege_denied", "owner_success")
    rp = a.get("role_privilege", "owner")
    sp = a.get("schema_privilege", "has_schema_privilege")

    if (
        os_ == "object_not_exists"
        or one == "object_not_exists"
        or po == "prerequisite_not_exists"
    ):
        a["object_state"] = "object_not_exists"
        a["object_not_exist"] = "object_not_exists"
        a["prerequisite_object"] = "prerequisite_not_exists"

    if pl == "non_owner" or pd == "non_owner_failure":
        a["privilege_level"] = "non_owner"
        a["privilege_denied"] = "non_owner_failure"

    if rp == "no_privilege":
        a["role_privilege"] = "no_privilege"

    if sp == "lacks_schema_privilege":
        a["schema_privilege"] = "lacks_schema_privilege"

    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: CommentFactorObligation,
) -> tuple[tuple[str, str], ...]:
    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["object_type"] = obligation.consumer_action_id
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    if len(assignments) != len(set(assignments)):
        raise CommentFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CommentFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CommentFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_comment_factor_loop_plan(
    repository_root: Path,
) -> CommentFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_comment_factor_loop_obligations(root)
    cases: list[CommentFactorCase] = []
    delegated: list[CommentFactorObligation] = []
    for obligation in obligations:
        if obligation.disposition == "delegated":
            delegated.append(obligation)
            continue
        ordinal = len(cases) + 1
        if obligation.disposition == "expected_failure":
            sqlstate, failure_reason = _expected_failure_details(
                obligation
            )
            outcome = "expected_failure"
        else:
            outcome = "success"
            sqlstate = "00000"
            failure_reason = None
        cases.append(
            CommentFactorCase(
                ordinal=ordinal,
                case_id=f"COMMENT{ordinal:05d}",
                sql_filename=f"COMMENT{ordinal:05d}.sql",
                object_prefix=f"comment_{ordinal:05d}_",
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
    plan = CommentFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 117 or len(plan.delegated) != 0:
        raise CommentFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 117:
        raise CommentFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 117:
        raise CommentFactorLoopError("duplicate SQL filename")
    return plan


def compile_comment_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CommentFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = _compile_canonical_obligations(root)
    rows = tuple(
        CommentFactorObligation(
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
    if len(rows) != 117:
        raise CommentFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CommentFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"SFV": 117}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CommentFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CommentFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 117:
        raise CommentFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CommentFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "CommentFactorLoopError",
    "CommentFactorObligation",
    "CommentFactorCase",
    "CommentFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_comment_factor_loop_obligations",
    "build_comment_factor_loop_plan",
    "_obligation_multiset_sha256",
]
