"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE DOMAIN.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE DOMAIN``.  CREATE DOMAIN is a PostgreSQL DDL statement that
defines a new domain (a typed, constraint-bearing user-defined type) over
a base data type.  The official synopsis has exactly one branch
(``CREATE DOMAIN name [ AS ] data_type [ COLLATE ] [ DEFAULT ]
[ constraint ... ]``), so there is a single ``GRM`` obligation.  The 96
canonical ``SFV`` rows are loaded from the shipped applicability universe
(``postgresql_18_4_factor_audit.tsv``): 28 factors (T1-T6) covering the
base type, default, collate, constraint, naming, privilege, schema,
collation and verification/cleanup axes.

CREATE DOMAIN's reachable failure surfaces (provisional PG 18.4
SQLSTATEs — a later DB phase verifies on PG 18.4) are modelled as 24
canonical ``(factor, value)`` pairs spanning twelve overlap clusters:
duplicate/exists (42710), type-name conflict (42710), nonexistent base
type (42704), nonexistent collation (42704), collate-on-non-collatable
(42804), insufficient privilege (42501), nonexistent schema (3F000),
default subquery (0A000), default type mismatch (42804), check subquery
(0A000), non-boolean check (42804), null/not-null conflict (42601) and
invalid domain name (42601).  The remaining 72 values are success-covered.

Each local obligation becomes exactly one regress program.  There are no
``RISK`` obligations (CREATE DOMAIN has no ``transaction_outcome``
factor) and no ``delegated`` obligations (every value is owned by
``create_domain``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CreateDomainFactorLoopError(ValueError):
    """Raised when a frozen CREATE DOMAIN obligation input drifts."""


@dataclass(frozen=True)
class CreateDomainGrammarAction:
    """One official target action form of the CREATE DOMAIN synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateDomainFactorObligation:
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
class CreateDomainFactorCase:
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
class CreateDomainFactorLoopPlan:
    obligations: tuple[CreateDomainFactorObligation, ...]
    cases: tuple[CreateDomainFactorCase, ...]
    delegated: tuple[CreateDomainFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-createdomain.html).
_BRANCH_CREATE_DOMAIN = "branch_create_domain"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createdomain"

# The single representative action for all canonical factors.  CREATE
# DOMAIN has exactly one synopsis form, so every factor observes on the
# single ``create_domain`` action.
_REPRESENTATIVE_ACTION = "create_domain"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_CREATE_DOMAIN: "create_domain",
}

# Canonical factor -> the action where the value is observable.  Since
# CREATE DOMAIN has only one synopsis form, every factor observes on the
# single ``create_domain`` action.  ``statement_branch`` is resolved
# separately in :func:`_canonical_consumer` because it is value-bound.
_SFV_FACTOR_CONSUMER = {
    "base_data_type": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "default_clause": _REPRESENTATIVE_ACTION,
    "collate_clause": _REPRESENTATIVE_ACTION,
    "constraint_type": _REPRESENTATIVE_ACTION,
    "constraint_naming": _REPRESENTATIVE_ACTION,
    "domain_name_shape": _REPRESENTATIVE_ACTION,
    "type_name_shape": _REPRESENTATIVE_ACTION,
    "collation_name_shape": _REPRESENTATIVE_ACTION,
    "constraint_name_shape": _REPRESENTATIVE_ACTION,
    "default_expression_shape": _REPRESENTATIVE_ACTION,
    "privilege_level": _REPRESENTATIVE_ACTION,
    "schema_existence": _REPRESENTATIVE_ACTION,
    "base_type_privilege": _REPRESENTATIVE_ACTION,
    "collation_existence": _REPRESENTATIVE_ACTION,
    "duplicate_domain_name": _REPRESENTATIVE_ACTION,
    "nonexistent_base_type": _REPRESENTATIVE_ACTION,
    "privilege_denied_on_base_type": _REPRESENTATIVE_ACTION,
    "invalid_default_expression": _REPRESENTATIVE_ACTION,
    "null_constraint_conflict": _REPRESENTATIVE_ACTION,
    "check_expr_subquery": _REPRESENTATIVE_ACTION,
    "check_expr_non_boolean": _REPRESENTATIVE_ACTION,
    "collation_on_non_collatable_type": _REPRESENTATIVE_ACTION,
    "reserved_name_conflict": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates -- DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        # Cluster: domain-already-exists duplicate (42710).
        ("expected_status", "failure"),
        ("object_state", "exists"),
        ("domain_name_shape", "duplicate_name"),
        ("duplicate_domain_name", "same_schema_conflict"),
        # Cluster: type-name conflict (42710).
        ("object_state", "type_name_conflict"),
        ("reserved_name_conflict", "name_conflicts_with_type"),
        # Cluster: invalid domain name (42601).
        ("domain_name_shape", "invalid_name"),
        # Cluster: nonexistent base type (42704).
        ("type_name_shape", "nonexistent_type"),
        ("nonexistent_base_type", "type_not_exists"),
        # Cluster: nonexistent collation (42704).
        ("collation_name_shape", "nonexistent_collation"),
        ("collation_existence", "collation_not_exists"),
        # Cluster: collate on non-collatable type (42804).
        ("collation_existence", "base_type_not_collatable"),
        ("collation_on_non_collatable_type", "non_collatable_type_with_collate"),
        # Cluster: insufficient privilege (42501).
        ("privilege_level", "non_owner_no_create"),
        ("base_type_privilege", "no_usage"),
        ("privilege_denied_on_base_type", "lacks_usage_privilege"),
        # Cluster: nonexistent schema (3F000).
        ("schema_existence", "schema_not_exists"),
        # Cluster: default subquery (0A000).
        ("default_expression_shape", "subquery_illegal"),
        ("invalid_default_expression", "subquery_in_default"),
        # Cluster: default type mismatch (42804).
        ("default_expression_shape", "type_mismatching_expression"),
        ("invalid_default_expression", "type_mismatch_default"),
        # Cluster: check subquery (0A000).
        ("check_expr_subquery", "subquery_in_check"),
        # Cluster: non-boolean check (42804).
        ("check_expr_non_boolean", "non_boolean_check"),
        # Cluster: null / not-null conflict (42601).
        ("null_constraint_conflict", "conflicting_null_not_null"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42710",
        "create_domain_declared_failure",
    ),
    ("object_state", "exists"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("domain_name_shape", "duplicate_name"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("duplicate_domain_name", "same_schema_conflict"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("object_state", "type_name_conflict"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("reserved_name_conflict", "name_conflicts_with_type"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("domain_name_shape", "invalid_name"): (
        "42601",
        "invalid_identifier_provisional",
    ),
    ("type_name_shape", "nonexistent_type"): (
        "42704",
        "type_does_not_exist_provisional",
    ),
    ("nonexistent_base_type", "type_not_exists"): (
        "42704",
        "type_does_not_exist_provisional",
    ),
    ("collation_name_shape", "nonexistent_collation"): (
        "42704",
        "undefined_collation_provisional",
    ),
    ("collation_existence", "collation_not_exists"): (
        "42704",
        "undefined_collation_provisional",
    ),
    ("collation_existence", "base_type_not_collatable"): (
        "42804",
        "datatype_mismatch_provisional",
    ),
    ("collation_on_non_collatable_type", "non_collatable_type_with_collate"): (
        "42804",
        "datatype_mismatch_provisional",
    ),
    ("privilege_level", "non_owner_no_create"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("base_type_privilege", "no_usage"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("privilege_denied_on_base_type", "lacks_usage_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("schema_existence", "schema_not_exists"): (
        "3F000",
        "invalid_schema_provisional",
    ),
    ("default_expression_shape", "subquery_illegal"): (
        "0A000",
        "feature_not_supported_provisional",
    ),
    ("invalid_default_expression", "subquery_in_default"): (
        "0A000",
        "feature_not_supported_provisional",
    ),
    ("default_expression_shape", "type_mismatching_expression"): (
        "42804",
        "datatype_mismatch_provisional",
    ),
    ("invalid_default_expression", "type_mismatch_default"): (
        "42804",
        "datatype_mismatch_provisional",
    ),
    ("check_expr_subquery", "subquery_in_check"): (
        "0A000",
        "feature_not_supported_provisional",
    ),
    ("check_expr_non_boolean", "non_boolean_check"): (
        "42804",
        "datatype_mismatch_provisional",
    ),
    ("null_constraint_conflict", "conflicting_null_not_null"): (
        "42601",
        "syntax_error_provisional",
    ),
}


def _load_grammar_actions() -> tuple[CreateDomainGrammarAction, ...]:
    """Freeze every CREATE DOMAIN synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "create_domain",
            _BRANCH_CREATE_DOMAIN,
            (
                "CREATE DOMAIN name [ AS ] data_type "
                "[ COLLATE collation ] [ DEFAULT expression ] "
                "[ constraint [ ... ] ]"
            ),
            "synopsis-create-domain",
        ),
    )
    actions = [
        CreateDomainGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise CreateDomainFactorLoopError("create domain action count drift")
    return tuple(actions)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise CreateDomainFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise CreateDomainFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> list[CreateDomainFactorObligation]:
    rows: list[CreateDomainFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateDomainFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CD-GRM|{action.grammar_branch_id}|"
                    f"{action.action_id}|target_action|"
                    f"{action.action_id}"
                ),
                kind="GRM",
                factor_key="target_action",
                value=action.action_id,
                consumer_action_id=action.action_id,
                disposition="covered",
                source_locator=action.source_locator,
            )
        )
    if len(rows) != 1:
        raise CreateDomainFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateDomainFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_domain")
    if len(catalog_rows) != 96:
        raise CreateDomainFactorLoopError("canonical obligation count drift")
    rows: list[CreateDomainFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateDomainFactorObligation(
                ordinal=0,
                obligation_id=f"CD-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreateDomainFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"create-domain-factor-obligations-v1\n")
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


# Branch action -> grammar branch id used by the renderer.
_ACTION_BRANCH = {
    "create_domain": _BRANCH_CREATE_DOMAIN,
}

# Dense baseline defaults (all positive T1-T6 factor values).  Every
# success-path factor gets one legal value; the primary overrides one.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_CREATE_DOMAIN,
    "grammar_branch": _BRANCH_CREATE_DOMAIN,
    "target_action": "create_domain",
    "base_data_type": "integer",
    "object_state": "not_exists",
    "expected_status": "success",
    "default_clause": "omitted",
    "collate_clause": "omitted",
    "constraint_type": "none",
    "constraint_naming": "auto_named",
    "domain_name_shape": "simple_id",
    "type_name_shape": "standard_type_name",
    "collation_name_shape": "default_collation",
    "constraint_name_shape": "auto_generated",
    "default_expression_shape": "literal_value",
    "privilege_level": "superuser",
    "schema_existence": "schema_exists",
    "base_type_privilege": "has_usage",
    "collation_existence": "collation_exists",
    "duplicate_domain_name": "no_conflict",
    "nonexistent_base_type": "type_exists",
    "privilege_denied_on_base_type": "has_usage_privilege",
    "invalid_default_expression": "valid_expression",
    "null_constraint_conflict": "single_constraint",
    "check_expr_subquery": "valid_check",
    "check_expr_non_boolean": "boolean_check",
    "collation_on_non_collatable_type": "collatable_type_with_collate",
    "reserved_name_conflict": "unique_name",
    "verification_mode": "catalog_query_pg_type",
    "cleanup_mode": "drop_domain",
}


def _is_duplicate_cluster(a: dict[str, str]) -> bool:
    """Domain-already-exists duplicate sub-cluster (42710)."""

    return (
        a.get("object_state") == "exists"
        or a.get("domain_name_shape") == "duplicate_name"
        or a.get("duplicate_domain_name") == "same_schema_conflict"
        or a.get("expected_status") == "failure"
    )


def _is_type_conflict_cluster(a: dict[str, str]) -> bool:
    """Type-name-conflict sub-cluster (42710)."""

    return (
        a.get("object_state") == "type_name_conflict"
        or a.get("reserved_name_conflict") == "name_conflicts_with_type"
    )


def _is_nonexistent_type_cluster(a: dict[str, str]) -> bool:
    return (
        a.get("type_name_shape") == "nonexistent_type"
        or a.get("nonexistent_base_type") == "type_not_exists"
    )


def _is_nonexistent_collation_cluster(a: dict[str, str]) -> bool:
    return (
        a.get("collation_name_shape") == "nonexistent_collation"
        or a.get("collation_existence") == "collation_not_exists"
    )


def _is_noncollatable_cluster(a: dict[str, str]) -> bool:
    return (
        a.get("collation_existence") == "base_type_not_collatable"
        or a.get("collation_on_non_collatable_type")
        == "non_collatable_type_with_collate"
    )


def _is_privilege_cluster(a: dict[str, str]) -> bool:
    return (
        a.get("privilege_level") == "non_owner_no_create"
        or a.get("base_type_privilege") == "no_usage"
        or a.get("privilege_denied_on_base_type") == "lacks_usage_privilege"
    )


def _is_default_subquery_cluster(a: dict[str, str]) -> bool:
    return (
        a.get("default_expression_shape") == "subquery_illegal"
        or a.get("invalid_default_expression") == "subquery_in_default"
    )


def _is_default_mismatch_cluster(a: dict[str, str]) -> bool:
    return (
        a.get("default_expression_shape") == "type_mismatching_expression"
        or a.get("invalid_default_expression") == "type_mismatch_default"
    )


def _is_check_subquery_cluster(a: dict[str, str]) -> bool:
    return a.get("check_expr_subquery") == "subquery_in_check"


def _is_nonboolean_check_cluster(a: dict[str, str]) -> bool:
    return a.get("check_expr_non_boolean") == "non_boolean_check"


def _is_null_conflict_cluster(a: dict[str, str]) -> bool:
    return (
        a.get("null_constraint_conflict") == "conflicting_null_not_null"
    )


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive overlap-cluster and T5 boundary factors from each other.

    The T5 single-value factors describe the same scenario as their T1-T4
    counterparts.  When the primary factor is a T1-T4 value, the
    corresponding T5 value is derived; when the primary is a T5 value, the
    T1-T4 counterpart is derived.  This keeps the baseline assignment
    self-consistent so the render produces SQL that reaches the intended
    boundary.
    """

    # Cluster: domain-already-exists duplicate (42710).  The meta-factor
    # ``expected_status=failure`` maps to this canonical create-domain
    # failure.
    if _is_duplicate_cluster(a):
        a["object_state"] = "exists"
        a["domain_name_shape"] = "duplicate_name"
        a["duplicate_domain_name"] = "same_schema_conflict"
        a["expected_status"] = "failure"
        a["reserved_name_conflict"] = "unique_name"

    # Cluster: type-name conflict (42710) — distinct sub-scenario.
    if _is_type_conflict_cluster(a):
        a["object_state"] = "type_name_conflict"
        a["reserved_name_conflict"] = "name_conflicts_with_type"

    # Cluster: nonexistent base type (42704).
    if _is_nonexistent_type_cluster(a):
        a["type_name_shape"] = "nonexistent_type"
        a["nonexistent_base_type"] = "type_not_exists"

    # Cluster: nonexistent collation (42704).
    if _is_nonexistent_collation_cluster(a):
        a["collation_name_shape"] = "nonexistent_collation"
        a["collation_existence"] = "collation_not_exists"
        a["collate_clause"] = "specified_collation"

    # Cluster: collate on non-collatable type (42804).
    if _is_noncollatable_cluster(a):
        a["collation_existence"] = "base_type_not_collatable"
        a["collation_on_non_collatable_type"] = (
            "non_collatable_type_with_collate"
        )
        a["collate_clause"] = "specified_collation"
        a["collation_name_shape"] = "default_collation"

    # Cluster: insufficient privilege (42501).
    if _is_privilege_cluster(a):
        a["privilege_level"] = "non_owner_no_create"
        a["base_type_privilege"] = "no_usage"
        a["privilege_denied_on_base_type"] = "lacks_usage_privilege"

    # Cluster: default subquery (0A000).
    if _is_default_subquery_cluster(a):
        a["default_expression_shape"] = "subquery_illegal"
        a["invalid_default_expression"] = "subquery_in_default"
        a["default_clause"] = "expression_default"

    # Cluster: default type mismatch (42804).
    if _is_default_mismatch_cluster(a):
        a["default_expression_shape"] = "type_mismatching_expression"
        a["invalid_default_expression"] = "type_mismatch_default"
        a["default_clause"] = "expression_default"

    # Cluster: check subquery (0A000).
    if _is_check_subquery_cluster(a):
        a["constraint_type"] = "check_only"

    # Cluster: non-boolean check (42804).
    if _is_nonboolean_check_cluster(a):
        a["constraint_type"] = "check_only"

    # Cluster: null / not-null conflict (42601).
    if _is_null_conflict_cluster(a):
        a["constraint_type"] = "not_null"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: CreateDomainFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["grammar_branch"] = _ACTION_BRANCH[
        obligation.consumer_action_id
    ]
    assignments["target_action"] = obligation.consumer_action_id
    assignments["statement_branch"] = _ACTION_BRANCH[
        obligation.consumer_action_id
    ]
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    failures = _count_baseline_failures(assignments)
    assignments["expected_status"] = (
        "failure" if failures > 0 else "success"
    )
    if len(assignments) != len(set(assignments)):
        raise CreateDomainFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateDomainFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateDomainFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_domain_factor_loop_plan(
    repository_root: Path,
) -> CreateDomainFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_domain_factor_loop_obligations(root)
    cases: list[CreateDomainFactorCase] = []
    delegated: list[CreateDomainFactorObligation] = []
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
            CreateDomainFactorCase(
                ordinal=ordinal,
                case_id=f"CREATEDOMAIN{ordinal:05d}",
                sql_filename=f"CREATEDOMAIN{ordinal:05d}.sql",
                object_prefix=f"createdomain_{ordinal:05d}_",
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
    plan = CreateDomainFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 97 or len(plan.delegated) != 0:
        raise CreateDomainFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 97:
        raise CreateDomainFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 97:
        raise CreateDomainFactorLoopError("duplicate SQL filename")
    return plan


def compile_create_domain_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateDomainFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateDomainFactorObligation(
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
    if len(rows) != 97:
        raise CreateDomainFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateDomainFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 96}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateDomainFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateDomainFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 97:
        raise CreateDomainFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreateDomainFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "CreateDomainFactorLoopError",
    "CreateDomainGrammarAction",
    "CreateDomainFactorObligation",
    "CreateDomainFactorCase",
    "CreateDomainFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_create_domain_factor_loop_obligations",
    "build_create_domain_factor_loop_plan",
    "_obligation_multiset_sha256",
]
