"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE TYPE.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE TYPE``.  The statement has five official synopsis branches:
composite (``CREATE TYPE name AS (...)``), enum (``AS ENUM (...)``),
range (``AS RANGE (...)``), base (``(INPUT=..., OUTPUT=...)``) and shell
(``CREATE TYPE name``).  Each branch is a distinct official target action
form, so the ``GRM`` layer contributes five obligations.

CREATE TYPE defines standalone type-system objects against the
``pg_catalog.pg_type`` catalog row (not a ``pg_class`` relation), so
column/table/relation coverage is ``not_applicable`` and there is no
``INV`` block.  CREATE TYPE does not create tables, so the bookend
(DROP TABLE IF EXISTS) is never emitted.  Cleanup uses
``DROP TYPE IF EXISTS`` plus any fixture (function/schema/role) drops.

The 91 canonical ``SFV`` rows are loaded from the shipped applicability
universe (``postgresql_18_4_factor_audit.tsv``).  Each local obligation
becomes exactly one regress program (marginal 1:1 baseline).  The bounded
post-coverage extension lives in
:mod:`create_type_factor_extension`.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CreateTypeFactorLoopError(ValueError):
    """Raised when a frozen CREATE TYPE obligation input drifts."""


@dataclass(frozen=True)
class CreateTypeGrammarAction:
    """One official target action form of the CREATE TYPE synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateTypeFactorObligation:
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
class CreateTypeFactorCase:
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
class CreateTypeFactorLoopPlan:
    obligations: tuple[CreateTypeFactorObligation, ...]
    cases: tuple[CreateTypeFactorCase, ...]
    delegated: tuple[CreateTypeFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-createtype.html).
_BRANCH_COMPOSITE = "branch_composite"
_BRANCH_ENUM = "branch_enum"
_BRANCH_RANGE = "branch_range"
_BRANCH_BASE = "branch_base"
_BRANCH_SHELL = "branch_shell"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createtype"

# branch <-> form mapping (the two always describe the same form).
_BRANCH_FORM: dict[str, str] = {
    _BRANCH_COMPOSITE: "composite",
    _BRANCH_ENUM: "enum",
    _BRANCH_RANGE: "range",
    _BRANCH_BASE: "base",
    _BRANCH_SHELL: "shell",
}


def _grammar_action_for_branch(branch: str) -> str:
    return {
        _BRANCH_COMPOSITE: "define_composite",
        _BRANCH_ENUM: "define_enum",
        _BRANCH_RANGE: "define_range",
        _BRANCH_BASE: "define_base",
        _BRANCH_SHELL: "define_shell",
    }[branch]


def _canonical_consumer(row) -> str:
    """Map a canonical factor value to its target consumer action."""

    if row.factor == "statement_branch":
        return _grammar_action_for_branch(row.value)
    if row.factor == "type_form":
        return f"define_{row.value}"
    if row.factor == "object_state":
        return "define_duplicate" if row.value == "already_exists" else "define_composite"
    if row.factor == "expected_status":
        return "define_duplicate" if row.value == "failure" else "define_composite"
    if row.factor == "privilege_level":
        if row.value == "non_owner":
            return "define_insufficient_priv"
        if row.value == "superuser":
            return "define_base"
        return "define_composite"
    if row.factor == "schema_dependency":
        return "define_schema_missing" if row.value == "schema_not_exists" else "define_composite"
    if row.factor == "duplicate_type_name":
        return "define_duplicate_table" if row.value == "with_existing_table" else "define_duplicate"
    if row.factor == "underscore_prefix_name":
        return "define_underscore_name"
    if row.factor == "insufficient_privilege":
        if row.value == "non_superuser_base_type":
            return "define_base_failure"
        return "define_insufficient_priv"
    if row.factor == "type_name_shape":
        return {
            "schema_qualified": "define_schema_qualified",
            "quoted": "define_quoted_name",
            "reserved_word": "define_reserved_name",
            "underscore_prefix": "define_underscore_name",
            "simple": "define_composite",
        }.get(row.value, "define_composite")
    if row.factor in {
        "attribute_count",
        "attribute_name_shape",
        "attribute_data_type",
        "zero_attributes_composite",
        "invalid_data_type_in_attribute",
    }:
        return "define_composite"
    if row.factor in {
        "enum_label_count",
        "enum_label_shape",
        "zero_labels_enum",
        "invalid_enum_label",
    }:
        return "define_enum"
    if row.factor in {
        "range_subtype",
        "range_option_completeness",
        "subtype_opclass_dependency",
        "canonical_function_dependency",
        "subtype_diff_dependency",
        "subtype_no_btree_opclass",
        "shell_type_dependency",
    }:
        return "define_range"
    if row.factor in {
        "base_type_io_functions",
        "base_type_option_completeness",
        "function_dependency",
        "missing_required_functions",
    }:
        return "define_base"
    if row.factor in {"verification_mode", "cleanup_mode"}:
        return "define_composite"
    return "define_composite"


# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("object_state", "already_exists"),
        ("duplicate_type_name", "with_existing_type"),
        ("duplicate_type_name", "with_existing_table"),
        ("schema_dependency", "schema_not_exists"),
        ("invalid_data_type_in_attribute", "unknown_type"),
        ("function_dependency", "input_output_functions_not_exist"),
        ("missing_required_functions", "no_input_function"),
        ("missing_required_functions", "no_output_function"),
        ("privilege_level", "non_owner"),
        ("insufficient_privilege", "non_superuser_base_type"),
        ("insufficient_privilege", "non_owner_create"),
        ("subtype_opclass_dependency", "opclass_not_exists"),
        ("canonical_function_dependency", "function_not_exists"),
        ("subtype_diff_dependency", "function_not_exists"),
        ("subtype_no_btree_opclass", "no_opclass"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("object_state", "already_exists"): ("42710", "duplicate_object_provisional"),
    ("duplicate_type_name", "with_existing_type"): ("42710", "duplicate_object_provisional"),
    ("duplicate_type_name", "with_existing_table"): ("42710", "duplicate_object_provisional"),
    ("schema_dependency", "schema_not_exists"): ("3F000", "invalid_schema_name_provisional"),
    ("invalid_data_type_in_attribute", "unknown_type"): ("42704", "undefined_object_provisional"),
    ("function_dependency", "input_output_functions_not_exist"): ("42883", "undefined_function_provisional"),
    ("missing_required_functions", "no_input_function"): ("42883", "undefined_function_provisional"),
    ("missing_required_functions", "no_output_function"): ("42883", "undefined_function_provisional"),
    ("privilege_level", "non_owner"): ("42501", "insufficient_privilege_provisional"),
    ("insufficient_privilege", "non_superuser_base_type"): ("42501", "insufficient_privilege_provisional"),
    ("insufficient_privilege", "non_owner_create"): ("42501", "insufficient_privilege_provisional"),
    ("subtype_opclass_dependency", "opclass_not_exists"): ("42704", "undefined_object_provisional"),
    ("canonical_function_dependency", "function_not_exists"): ("42883", "undefined_function_provisional"),
    ("subtype_diff_dependency", "function_not_exists"): ("42883", "undefined_function_provisional"),
    ("subtype_no_btree_opclass", "no_opclass"): ("42704", "undefined_object_provisional"),
}


def _load_grammar_actions() -> tuple[CreateTypeGrammarAction, ...]:
    """Freeze every CREATE TYPE synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        ("define_composite", _BRANCH_COMPOSITE,
         "CREATE TYPE name AS ( attribute_name data_type [, ... ] )",
         "synopsis-define-composite"),
        ("define_enum", _BRANCH_ENUM,
         "CREATE TYPE name AS ENUM ( 'label' [, ... ] )",
         "synopsis-define-enum"),
        ("define_range", _BRANCH_RANGE,
         "CREATE TYPE name AS RANGE ( SUBTYPE = subtype [, ... ] )",
         "synopsis-define-range"),
        ("define_base", _BRANCH_BASE,
         "CREATE TYPE name ( INPUT = input_function, OUTPUT = output_function [, ... ] )",
         "synopsis-define-base"),
        ("define_shell", _BRANCH_SHELL,
         "CREATE TYPE name",
         "synopsis-define-shell"),
    )
    actions = [
        CreateTypeGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 5:
        raise CreateTypeFactorLoopError("create type action count drift")
    return tuple(actions)


def _compile_grammar_obligations() -> list[CreateTypeFactorObligation]:
    rows: list[CreateTypeFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateTypeFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CT-GRM|{action.grammar_branch_id}|"
                    f"{action.action_id}|target_form|"
                    f"{action.action_id}"
                ),
                kind="GRM",
                factor_key="target_form",
                value=action.action_id,
                consumer_action_id=action.action_id,
                disposition="covered",
                source_locator=action.source_locator,
            )
        )
    if len(rows) != 5:
        raise CreateTypeFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateTypeFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_type")
    if len(catalog_rows) != 91:
        raise CreateTypeFactorLoopError("canonical obligation count drift")
    rows: list[CreateTypeFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateTypeFactorObligation(
                ordinal=0,
                obligation_id=f"CT-SFV|{row.row_id}|{consumer}",
                kind="SFV",
                factor_key=row.factor,
                value=row.value,
                consumer_action_id=consumer,
                disposition="expected_failure" if is_failure else "covered",
                source_locator=f"{row.source_reference}#{row.row_id}",
            )
        )
    return rows


def _obligation_multiset_sha256(
    rows: tuple[CreateTypeFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"create-type-factor-obligations-v1\n")
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
                    "delegated_statement_key": row.delegated_statement_key,
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        digest.update(b"\n")
    return digest.hexdigest()


# Dense baseline defaults (all positive factor values) for the composite
# branch — the representative default form.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_COMPOSITE,
    "object_state": "not_exists",
    "expected_status": "success",
    "type_form": "composite",
    "attribute_count": "single_attribute",
    "attribute_name_shape": "simple",
    "attribute_data_type": "integer",
    "enum_label_count": "multiple_labels",
    "enum_label_shape": "simple_label",
    "range_subtype": "integer",
    "range_option_completeness": "minimal",
    "base_type_io_functions": "with_shell_type_first",
    "base_type_option_completeness": "required_only",
    "type_name_shape": "simple",
    "privilege_level": "type_owner",
    "function_dependency": "input_output_functions_exist",
    "subtype_opclass_dependency": "opclass_exists",
    "canonical_function_dependency": "function_exists",
    "subtype_diff_dependency": "function_exists",
    "shell_type_dependency": "shell_type_exists",
    "schema_dependency": "schema_exists",
    "verification_mode": "pg_type_catalog_query",
    "cleanup_mode": "DROP_TYPE_IF_EXISTS",
}

# Single-value boundary factors omitted from _BASELINE_DEFAULTS; they are
# only attached to an assignment when they are the primary obligation.
_BOUNDARY_SINGLE_VALUE_FACTORS = frozenset(
    {
        "duplicate_type_name",
        "underscore_prefix_name",
        "invalid_data_type_in_attribute",
        "invalid_enum_label",
        "zero_attributes_composite",
        "zero_labels_enum",
        "subtype_no_btree_opclass",
        "insufficient_privilege",
    }
)

# Branch-specific factors determine which synopsis form a case exercises.
_FACTOR_BRANCH: dict[str, str] = {
    "attribute_count": _BRANCH_COMPOSITE,
    "attribute_name_shape": _BRANCH_COMPOSITE,
    "attribute_data_type": _BRANCH_COMPOSITE,
    "zero_attributes_composite": _BRANCH_COMPOSITE,
    "invalid_data_type_in_attribute": _BRANCH_COMPOSITE,
    "enum_label_count": _BRANCH_ENUM,
    "enum_label_shape": _BRANCH_ENUM,
    "zero_labels_enum": _BRANCH_ENUM,
    "invalid_enum_label": _BRANCH_ENUM,
    "range_subtype": _BRANCH_RANGE,
    "range_option_completeness": _BRANCH_RANGE,
    "subtype_opclass_dependency": _BRANCH_RANGE,
    "canonical_function_dependency": _BRANCH_RANGE,
    "subtype_diff_dependency": _BRANCH_RANGE,
    "subtype_no_btree_opclass": _BRANCH_RANGE,
    "shell_type_dependency": _BRANCH_RANGE,
    "base_type_io_functions": _BRANCH_BASE,
    "base_type_option_completeness": _BRANCH_BASE,
    "function_dependency": _BRANCH_BASE,
    "missing_required_functions": _BRANCH_BASE,
}


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(1 for pair in _SFV_FAILURE_VALUES if a.get(pair[0]) == pair[1])


def _sync_branch_form(a: dict[str, str]) -> None:
    """Keep statement_branch and type_form describing the same form."""

    branch = a.get("statement_branch", _BRANCH_COMPOSITE)
    a["statement_branch"] = branch
    a["type_form"] = _BRANCH_FORM.get(branch, "composite")


def _derive_privilege_cluster(a: dict[str, str]) -> None:
    """privilege_level <-> insufficient_privilege (same failure scenario)."""

    ip = a.get("insufficient_privilege")
    if ip == "non_superuser_base_type":
        a["privilege_level"] = "non_owner"
        a["statement_branch"] = _BRANCH_BASE
        a["type_form"] = "base"
        return
    if ip == "non_owner_create":
        a["privilege_level"] = "non_owner"
        return
    pl = a.get("privilege_level", "type_owner")
    if pl == "non_owner":
        a["insufficient_privilege"] = "non_owner_create"


def _derive_duplicate_cluster(a: dict[str, str]) -> None:
    """object_state <-> duplicate_type_name (same failure scenario)."""

    os_state = a.get("object_state", "not_exists")
    dtn = a.get("duplicate_type_name")
    if dtn in {"with_existing_type", "with_existing_table"}:
        a["object_state"] = "already_exists"
        return
    if os_state == "already_exists" and "duplicate_type_name" not in a:
        a["duplicate_type_name"] = "with_existing_type"


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive overlapping boundary factors from the primary value."""

    _sync_branch_form(a)
    _derive_privilege_cluster(a)
    _sync_branch_form(a)
    _derive_duplicate_cluster(a)
    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _baseline_assignments(
    obligation: CreateTypeFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments[obligation.factor_key] = obligation.value
    branch_for_factor = _FACTOR_BRANCH.get(obligation.factor_key)
    if branch_for_factor is not None:
        assignments["statement_branch"] = branch_for_factor
    _derive_overlapping_factors(assignments)
    failures = _count_baseline_failures(assignments)
    assignments["expected_status"] = "failure" if failures > 0 else "success"
    if len(assignments) != len(set(assignments)):
        raise CreateTypeFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateTypeFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise CreateTypeFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_type_factor_loop_plan(
    repository_root: Path,
) -> CreateTypeFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_type_factor_loop_obligations(root)
    cases: list[CreateTypeFactorCase] = []
    delegated: list[CreateTypeFactorObligation] = []
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
            CreateTypeFactorCase(
                ordinal=ordinal,
                case_id=f"CREATETYPE{ordinal:05d}",
                sql_filename=f"CREATETYPE{ordinal:05d}.sql",
                object_prefix=f"createtype_{ordinal:05d}_",
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
    plan = CreateTypeFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 96 or len(plan.delegated) != 0:
        raise CreateTypeFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 96:
        raise CreateTypeFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 96:
        raise CreateTypeFactorLoopError("duplicate SQL filename")
    return plan


def compile_create_type_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateTypeFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateTypeFactorObligation(
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
    if len(rows) != 96:
        raise CreateTypeFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateTypeFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 5, "SFV": 91}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateTypeFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateTypeFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"} for row in rows
    ) != 96:
        raise CreateTypeFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(row.disposition not in allowed_dispositions for row in rows):
        raise CreateTypeFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "CreateTypeFactorLoopError",
    "CreateTypeGrammarAction",
    "CreateTypeFactorObligation",
    "CreateTypeFactorCase",
    "CreateTypeFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_create_type_factor_loop_obligations",
    "build_create_type_factor_loop_plan",
    "_obligation_multiset_sha256",
    "_BASELINE_DEFAULTS",
    "_BOUNDARY_SINGLE_VALUE_FACTORS",
]
