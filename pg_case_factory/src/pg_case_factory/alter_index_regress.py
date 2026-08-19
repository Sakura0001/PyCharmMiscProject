"""Factor-ledger grammar for PostgreSQL 18.4 ALTER INDEX.

This module is the data layer for the marginal factor-value obligation ledger.
It loads the official combination matrix
``skills/pg-sql-generation/references/combinations/ddl/index/alter_index.yaml``
and exposes the nine ALTER INDEX branches (rename, set_tablespace,
attach_partition, depends_on_extension, no_depends_on_extension, set_storage,
reset_storage, set_statistics, all_in_tablespace) as grammar actions, the
eighteen canonical factors as grammar axes, and the declared compatibility
(success / failure / no-op) rules that bind factor values to expected
sqlstates.

It is deliberately data-driven from the combination matrix so that the
ledger remains a faithful mirror of the official syntax coverage contract.
The marginal ledger compiled from this grammar is the required-coverage
baseline; bounded post-coverage extensions (crossing positive T1–T4 axes
with T6 verification) are a separate, downstream phase that must not be
counted toward required coverage.
"""

from __future__ import annotations

import functools
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

_COMBINATION_MATRIX_REL = (
    "skills/pg-sql-generation/references/combinations/ddl/index/alter_index.yaml"
)

_STATEMENT_KEY = "alter_index"


@dataclass(frozen=True)
class AlterIndexGrammarAction:
    """One ALTER INDEX branch action derived from a combination group."""

    action_id: str
    group_id: str
    title: str
    lifecycle_role: str
    default_expected_status: str
    expected_failure_reasons: tuple[str, ...]
    sql_shape_template: str
    verification_mode: str
    verification_sql: str | None
    cleanup_steps: tuple[str, ...]
    success_when: tuple[str, ...]
    failure_when: tuple[tuple[str, str], ...]
    default_failure_reason: str
    baseline_factors: tuple[tuple[str, str], ...]
    source_locator: str


@dataclass(frozen=True)
class AlterIndexGrammarAxis:
    """One canonical factor axis bound to a branch action."""

    action_id: str
    group_id: str
    axis_id: str
    tier: str
    coverage_role: str
    values: tuple[str, ...]
    coverage_requirement: str
    source_locator: str


@dataclass(frozen=True)
class AlterIndexTypeWitness:
    """A representative indexed column type used in branch fixture setup."""

    selector_id: str
    member: str
    declaration_sql: str
    index_capabilities: tuple[str, ...]


# Expected SQLSTATE per declared failure reason.  These map the combination
# matrix ``compatibility`` failure reasons to PostgreSQL 18.4 sqlstate codes.
# The marginal ledger uses them to attribute expected-failure obligations;
# the downstream PG18.4 double-run calibration verifies and refines them.
EXPECTED_SQLSTATE_BY_REASON: dict[str, str] = {
    "relation_does_not_exist": "42P01",
    "extension_does_not_exist": "42704",
    "extension_dependency_binding_invalid": "42601",
    "partition_index_definition_mismatch": "42P17",
    "index_storage_parameter_not_supported_by_method": "0A000",
    "index_column_number_out_of_range": "42P16",
    "invalid_statistics_target": "22023",
    "set_statistics_binding_invalid": "42601",
    "tablespace_permission_denied": "42501",
    "must_own_index": "42501",
    "alter_index_all_in_tablespace_failed": "42501",
    "alter_index_syntax_is_invalid": "42601",
    "cannot_alter_system_catalog_index": "42501",
    "alter_index_negative_boundary": "42601",
    "pg18_revalidate_attached_parent_reference_failure": "0A000",
}

# Index-method × storage-parameter validity.  ``True`` means the parameter is
# accepted by the method under ALTER INDEX ... SET (parameter).  This table
# backs the semantic ``storage_parameter is [not] valid for index_method``
# compatibility condition for the storage-parameter branches.
_METHOD_PARAMETER_VALID: dict[tuple[str, str], bool] = {
    ("btree", "fillfactor"): True,
    ("hash", "fillfactor"): True,
    ("gist", "fillfactor"): True,
    ("gist", "buffering"): True,
    ("gin", "fastupdate"): True,
    ("gin", "gin_pending_list_limit"): True,
    ("spgist", "fillfactor"): True,
    ("brin", "pages_per_range"): True,
    ("brin", "autosummarize"): True,
}


def _matrix_path(repository_root: Path) -> Path:
    return Path(repository_root).resolve(strict=True) / _COMBINATION_MATRIX_REL


@functools.lru_cache(maxsize=4)
def _load_combination_matrix(repository_root: str) -> Mapping[str, Any]:
    path = _matrix_path(Path(repository_root))
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(document, Mapping):
        raise TypeError(f"combination matrix is not a mapping: {path}")
    if document.get("statement", {}).get("key") != _STATEMENT_KEY:
        raise ValueError(
            f"combination matrix statement key drift: {document.get('statement')}"
        )
    return document


def _factor_contract(document: Mapping[str, Any]) -> Mapping[str, Any]:
    factors = document.get("factor_contract", {}).get("factors", {})
    if not isinstance(factors, Mapping):
        raise ValueError("factor_contract.factors is not a mapping")
    return factors


def _branch_values(group: Mapping[str, Any]) -> list[str]:
    """The statement_branch values a combination group exercises.

    The baseline ``factors.statement_branch`` binding is a single string; the
    full branch list lives in ``expansion.statement_branch.values`` when the
    group spans more than one branch.  Either way, return the ordered list.
    """
    group_factors: Mapping[str, Any] = group.get("factors", {})
    expansion: Mapping[str, Any] = group.get("expansion", {}) or {}
    sb = group_factors.get("statement_branch")
    if isinstance(sb, list):
        return [str(v) for v in sb]
    if "statement_branch" in expansion and isinstance(
        expansion["statement_branch"], Mapping
    ):
        values = expansion["statement_branch"].get("values", [])
        if values:
            return [str(v) for v in values]
    if sb is not None:
        return [str(sb)]
    return []


def load_alter_index_grammar_actions(
    repository_root: Path,
) -> tuple[AlterIndexGrammarAction, ...]:
    """Compile one grammar action per (group, branch value) pair.

    A combination group expands its ``statement_branch`` across one or more
    values; each value becomes a distinct action so that every branch carries
    its own SQL shape, verification, cleanup, and compatibility rules.
    """
    document = _load_combination_matrix(str(repository_root))
    factors = _factor_contract(document)
    rows: list[AlterIndexGrammarAction] = []
    for group in document.get("combination_groups", []):
        group_factors: Mapping[str, Any] = group.get("factors", {})
        branch_values = _branch_values(group)
        if not branch_values:
            raise ValueError(
                f"combination group {group.get('id')} has no statement_branch"
            )
        compatibility = group.get("compatibility", {})
        success_when = tuple(
            str(rule) for rule in compatibility.get("success_when", [])
        )
        failure_when = tuple(
            (str(rule.get("condition", "")), str(rule.get("reason", "")))
            for rule in compatibility.get("failure_when", [])
        )
        cleanup = group.get("cleanup", {}) or {}
        cleanup_steps = tuple(str(s) for s in cleanup.get("steps", []) or [])
        verification = group.get("verification", {}) or {}
        for branch in branch_values:
            rows.append(
                AlterIndexGrammarAction(
                    action_id=str(branch),
                    group_id=str(group["id"]),
                    title=str(group.get("title", "")),
                    lifecycle_role=str(group.get("lifecycle_role", "")),
                    default_expected_status=str(
                        group.get("default_expected_status", "success")
                    ),
                    expected_failure_reasons=tuple(
                        str(r) for r in group.get("expected_failure_reasons", [])
                    ),
                    sql_shape_template=str(
                        group.get("sql_shape", {}).get("template", "")
                    ),
                    verification_mode=str(verification.get("mode", "")),
                    verification_sql=(
                        str(verification["sql"])
                        if verification.get("sql")
                        else None
                    ),
                    cleanup_steps=cleanup_steps,
                    success_when=success_when,
                    failure_when=failure_when,
                    default_failure_reason=str(
                        compatibility.get("default_failure_reason", "none")
                    ),
                    baseline_factors=tuple(
                        (str(k), str(v))
                        for k, v in group_factors.items()
                        if k != "statement_branch"
                    ),
                    source_locator=str(group["id"]),
                )
            )
    if not rows:
        raise ValueError("no ALTER INDEX grammar actions compiled")
    return tuple(rows)


def load_alter_index_grammar_axes(
    repository_root: Path,
) -> tuple[AlterIndexGrammarAxis, ...]:
    """Compile one grammar axis per (action, factor) with declared values.

    Each combination group declares an ``expansion`` block listing the factor
    values exercised by that branch.  Factors present in the group's baseline
    ``factors`` binding but absent from ``expansion`` contribute their
    declared ``required_values`` from the factor contract so that every
    canonical factor value remains witnessed in the marginal ledger.
    """
    document = _load_combination_matrix(str(repository_root))
    factors = _factor_contract(document)
    rows: list[AlterIndexGrammarAxis] = []
    for group in document.get("combination_groups", []):
        group_id = str(group["id"])
        group_factors: Mapping[str, Any] = group.get("factors", {})
        expansion: Mapping[str, Any] = group.get("expansion", {}) or {}
        for branch in _branch_values(group):
            action_id = str(branch)
            for factor_key, binding in group_factors.items():
                if factor_key == "statement_branch":
                    continue
                tier = str(factors.get(factor_key, {}).get("tier", ""))
                role = str(
                    factors.get(factor_key, {}).get("coverage_role", "")
                )
                requirement = str(
                    factors.get(factor_key, {}).get(
                        "coverage_requirement", "all_values"
                    )
                )
                if factor_key in expansion and isinstance(
                    expansion[factor_key], Mapping
                ):
                    values = tuple(
                        str(v)
                        for v in expansion[factor_key].get("values", [])
                    )
                else:
                    values = tuple(
                        str(v)
                        for v in factors.get(factor_key, {}).get(
                            "required_values", []
                        )
                    )
                if not values:
                    continue
                rows.append(
                    AlterIndexGrammarAxis(
                        action_id=action_id,
                        group_id=group_id,
                        axis_id=str(factor_key),
                        tier=tier,
                        coverage_role=role,
                        values=values,
                        coverage_requirement=requirement,
                        source_locator=f"{group_id}#{factor_key}",
                    )
                )
    return tuple(rows)


def load_alter_index_type_witnesses(
    repository_root: Path,
) -> tuple[AlterIndexTypeWitness, ...]:
    """Representative indexed column types per branch fixture setup.

    ALTER INDEX column-type coverage is ``conditional`` with
    ``branch_scoped_representative_types``: each branch declares representative
    concrete types in its ``column_types`` expansion.  Exhaustive type
    compatibility remains owned by CREATE INDEX, so these witnesses carry no
    per-type success/failure expectation (``require_each_type_success_or_failure``
    is false).
    """
    document = _load_combination_matrix(str(repository_root))
    declarations: dict[str, str] = {
        "integer": "integer",
        "text": "text",
        "jsonb": "jsonb",
        "tsvector": "tsvector",
        "int4range": "int4range",
        "point": "point",
    }
    seen: dict[tuple[str, str], AlterIndexTypeWitness] = {}
    for group in document.get("combination_groups", []):
        expansion: Mapping[str, Any] = group.get("expansion", {}) or {}
        column_types = expansion.get("column_types", {})
        if not isinstance(column_types, Mapping):
            continue
        for value in column_types.get("values", []):
            member = str(value)
            declaration = declarations.get(member, member)
            key = ("pg18", member)
            seen.setdefault(
                key,
                AlterIndexTypeWitness(
                    selector_id="pg18",
                    member=member,
                    declaration_sql=declaration,
                    index_capabilities=(),
                ),
            )
    return tuple(seen.values())


def is_storage_parameter_valid_for_method(
    method: str, parameter: str
) -> bool:
    """Back the semantic storage-parameter validity compatibility condition."""
    return _METHOD_PARAMETER_VALID.get((method, parameter), False)


# A tiny condition evaluator for the declared ``compatibility`` rules.  It
# understands the subset of predicate shapes used by the ALTER INDEX matrix:
# ``factor == value``, ``factor in [a, b]``, ``factor is [not] valid for
# index_method``, and the negative-control text conditions.  Anything it
# cannot resolve returns ``None`` so the caller falls back to the declared
# default expected status.
_EQ_RE = re.compile(r"^(\w+)\s*==\s*(\w+)$")
_IN_RE = re.compile(r"^(\w+)\s+in\s*\[([^\]]*)\]$")
_VALID_RE = re.compile(
    r"^storage_parameter is (not )?valid for index_method$"
)


def evaluate_condition(
    condition: str, bindings: Mapping[str, str]
) -> bool | None:
    """Evaluate a declared compatibility condition against factor bindings."""
    condition = condition.strip()
    if not condition:
        return None
    match = _EQ_RE.match(condition)
    if match:
        factor, value = match.group(1), match.group(2)
        return bindings.get(factor) == value
    match = _IN_RE.match(condition)
    if match:
        factor, raw = match.group(1), match.group(2)
        values = [v.strip() for v in raw.split(",") if v.strip()]
        return bindings.get(factor) in values
    match = _VALID_RE.match(condition)
    if match:
        negated = bool(match.group(1))
        method = bindings.get("index_method", "")
        parameter = bindings.get("storage_parameter", "")
        valid = is_storage_parameter_valid_for_method(method, parameter)
        return (not valid) if negated else valid
    # Reference-parity and fixture-state conditions are not factor-value
    # predicates; the caller resolves them via the declared default status.
    return None
