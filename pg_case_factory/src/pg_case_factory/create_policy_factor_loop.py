"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE POLICY.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE POLICY``.  CREATE POLICY is a PostgreSQL table-level DDL statement
with a single official synopsis branch:
``CREATE POLICY name ON table_name [ AS ] [ FOR ] [ TO ] [ USING ] [ WITH CHECK ]``.

The statement touches the ``pg_catalog.pg_policy`` catalog row (not a
``pg_class`` relation directly, but it requires a backing TABLE that
must be created and RLS-enabled as a fixture).  Each case therefore
CREATEs a fixture TABLE, so the bookend (DROP TABLE IF EXISTS) is
always emitted as the first and last executable ``;``-statement.

CREATE POLICY does NOT support OR REPLACE.  Policy names must be unique
within a table; different tables may share the same policy name.

Each local obligation becomes exactly one regress program.  The 80
canonical ``SFV`` rows are loaded from the shipped applicability universe
(``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CreatePolicyFactorLoopError(ValueError):
    """Raised when a frozen CREATE POLICY obligation input drifts."""


@dataclass(frozen=True)
class CreatePolicyGrammarAction:
    """One official target action form of the CREATE POLICY synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreatePolicyFactorObligation:
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
class CreatePolicyFactorCase:
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
class CreatePolicyFactorLoopPlan:
    obligations: tuple[CreatePolicyFactorObligation, ...]
    cases: tuple[CreatePolicyFactorCase, ...]
    delegated: tuple[CreatePolicyFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-createpolicy.html).
_BRANCH_CREATE_POLICY = "branch_create_policy"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createpolicy"

# The single representative consumer action used as the baseline consumer
# for all canonical factors (there is only one synopsis branch).
_REPRESENTATIVE_ACTION = "create_policy"


def _load_grammar_actions() -> tuple[CreatePolicyGrammarAction, ...]:
    """Freeze every CREATE POLICY synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "create_policy",
            _BRANCH_CREATE_POLICY,
            (
                "CREATE POLICY name ON table_name "
                "[ AS { PERMISSIVE | RESTRICTIVE } ] "
                "[ FOR { ALL | SELECT | INSERT | UPDATE | DELETE } ] "
                "[ TO { role | PUBLIC | CURRENT_ROLE | CURRENT_USER | SESSION_USER } [, ...] ] "
                "[ USING ( expr ) ] [ WITH CHECK ( expr ) ]"
            ),
            "synopsis-create-policy",
        ),
    )
    actions = [
        CreatePolicyGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise CreatePolicyFactorLoopError(
            "create policy action count drift"
        )
    return tuple(actions)


def _compile_grammar_obligations() -> list[CreatePolicyFactorObligation]:
    rows: list[CreatePolicyFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreatePolicyFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CPOL-GRM|{action.grammar_branch_id}|"
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
    if len(rows) != 1:
        raise CreatePolicyFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _canonical_consumer(row) -> str:
    """All CREATE POLICY factors use the single consumer action."""
    return _REPRESENTATIVE_ACTION


# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "exists_same_table"),
        ("duplicate_policy_name", "same_table_same_name"),
        ("policy_name_shape", "duplicate_name_same_table"),
        ("table_existence", "table_not_exists"),
        ("nonexistent_table", "table_missing"),
        ("table_name_shape", "nonexistent_table"),
        ("privilege_level", "non_owner"),
        ("privilege_denied", "non_owner_denied"),
        ("role_existence", "role_not_exists"),
        ("role_name_shape", "nonexistent_role"),
        ("expression_compatibility", "select_with_check_incompatible"),
        ("expression_compatibility", "insert_with_using_incompatible"),
        ("expression_compatibility", "delete_with_check_incompatible"),
        ("select_with_check_conflict", "incompatible_with_check"),
        ("insert_with_using_conflict", "incompatible_using"),
        ("invalid_expression", "aggregate_in_expression"),
        ("invalid_expression", "window_function_in_expression"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42710",
        "duplicate_policy_provisional",
    ),
    ("object_state", "exists_same_table"): (
        "42710",
        "duplicate_policy_provisional",
    ),
    ("duplicate_policy_name", "same_table_same_name"): (
        "42710",
        "duplicate_policy_provisional",
    ),
    ("policy_name_shape", "duplicate_name_same_table"): (
        "42710",
        "duplicate_policy_provisional",
    ),
    ("table_existence", "table_not_exists"): (
        "42P01",
        "undefined_table_provisional",
    ),
    ("nonexistent_table", "table_missing"): (
        "42P01",
        "undefined_table_provisional",
    ),
    ("table_name_shape", "nonexistent_table"): (
        "42P01",
        "undefined_table_provisional",
    ),
    ("privilege_level", "non_owner"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("privilege_denied", "non_owner_denied"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("role_existence", "role_not_exists"): (
        "42704",
        "undefined_role_provisional",
    ),
    ("role_name_shape", "nonexistent_role"): (
        "42704",
        "undefined_role_provisional",
    ),
    ("expression_compatibility", "select_with_check_incompatible"): (
        "42601",
        "syntax_error_provisional",
    ),
    ("expression_compatibility", "insert_with_using_incompatible"): (
        "42601",
        "syntax_error_provisional",
    ),
    ("expression_compatibility", "delete_with_check_incompatible"): (
        "42601",
        "syntax_error_provisional",
    ),
    ("select_with_check_conflict", "incompatible_with_check"): (
        "42601",
        "syntax_error_provisional",
    ),
    ("insert_with_using_conflict", "incompatible_using"): (
        "42601",
        "syntax_error_provisional",
    ),
    ("invalid_expression", "aggregate_in_expression"): (
        "42803",
        "grouping_error_provisional",
    ),
    ("invalid_expression", "window_function_in_expression"): (
        "42803",
        "grouping_error_provisional",
    ),
}


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreatePolicyFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_policy")
    if len(catalog_rows) != 80:
        raise CreatePolicyFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[CreatePolicyFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreatePolicyFactorObligation(
                ordinal=0,
                obligation_id=f"CPOL-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreatePolicyFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-policy-factor-obligations-v1\n"
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


# Branch action -> grammar branch id used by the renderer.
_ACTION_BRANCH = {
    "create_policy": _BRANCH_CREATE_POLICY,
}

# Command-type values that are PG18 behaviour test points (not standard
# FOR clause values).  Mapped to a representative FOR clause in the
# renderer.
_PG18_COMMAND_MAP = {
    "MERGE": "ALL",
    "INSERT_ON_CONFLICT": "SELECT",
    "DML_RETURNING": "SELECT",
}

# Dense baseline defaults (all positive factor values).  T5 single-value
# factors are derived in :func:`_derive_overlapping_factors`.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_CREATE_POLICY,
    "policy_type": "permissive",
    "command_type": "ALL",
    "object_state": "not_exists",
    "expected_status": "success",
    "role_target": "PUBLIC",
    "using_expression": "omitted",
    "with_check_expression": "omitted",
    "expression_compatibility": "compatible_pairing",
    "policy_name_shape": "simple_id",
    "table_name_shape": "simple_id",
    "role_name_shape": "simple_id",
    "privilege_level": "superuser",
    "rls_enabled": "rls_enabled",
    "table_existence": "table_exists",
    "role_existence": "role_exists",
    "duplicate_policy_name": "no_conflict",
    "nonexistent_table": "table_exists",
    "rls_not_enabled": "rls_enabled",
    "privilege_denied": "owner_execution",
    "select_with_check_conflict": "compatible_no_with_check",
    "insert_with_using_conflict": "compatible_no_using",
    "only_restrictive_policy": "has_permissive_policy",
    "invalid_expression": "valid_expression",
    "verification_mode": "catalog_query_pg_policy",
    "cleanup_mode": "drop_policy",
}


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values.

    The T5 single-value factors describe the same scenario as their
    T1-T4 counterparts.  When the primary factor is a T1-T4 value, the
    corresponding T5 value is derived; when the primary is a T5 value,
    the T1-T4 counterpart is derived.  This keeps the baseline assignment
    self-consistent so the render produces SQL that reaches the intended
    boundary.
    """

    # --- object_state ↔ duplicate_policy_name ↔ policy_name_shape ---
    os = a.get("object_state", "not_exists")
    dpn = a.get("duplicate_policy_name", "no_conflict")
    pns = a.get("policy_name_shape", "simple_id")

    if os == "exists_same_table":
        a["duplicate_policy_name"] = "same_table_same_name"
        if pns not in {"duplicate_name_same_table"}:
            a["policy_name_shape"] = "duplicate_name_same_table"
    elif os == "exists_different_table":
        a["duplicate_policy_name"] = "no_conflict"
        if pns not in {"duplicate_name_different_table"}:
            a["policy_name_shape"] = "duplicate_name_different_table"

    if dpn == "same_table_same_name":
        a["object_state"] = "exists_same_table"
    elif dpn == "no_conflict" and os == "not_exists":
        pass

    pns = a.get("policy_name_shape", "simple_id")
    if pns == "duplicate_name_same_table":
        a["object_state"] = "exists_same_table"
        a["duplicate_policy_name"] = "same_table_same_name"
    elif pns == "duplicate_name_different_table":
        a["object_state"] = "exists_different_table"
        a["duplicate_policy_name"] = "no_conflict"

    # --- table_existence ↔ nonexistent_table ↔ table_name_shape ---
    te = a.get("table_existence", "table_exists")
    nt = a.get("nonexistent_table", "table_exists")
    tns = a.get("table_name_shape", "simple_id")

    if te == "table_not_exists":
        a["nonexistent_table"] = "table_missing"
        a["table_name_shape"] = "nonexistent_table"
    elif te == "table_exists":
        a["nonexistent_table"] = "table_exists"

    if nt == "table_missing":
        a["table_existence"] = "table_not_exists"
        a["table_name_shape"] = "nonexistent_table"
    elif nt == "table_exists":
        a["table_existence"] = "table_exists"

    tns = a.get("table_name_shape", "simple_id")
    if tns == "nonexistent_table":
        a["table_existence"] = "table_not_exists"
        a["nonexistent_table"] = "table_missing"

    # --- rls_enabled ↔ rls_not_enabled ---
    rls = a.get("rls_enabled", "rls_enabled")
    if rls == "rls_not_enabled":
        a["rls_not_enabled"] = "rls_not_enabled"
    else:
        a["rls_not_enabled"] = "rls_enabled"

    rls5 = a.get("rls_not_enabled", "rls_enabled")
    if rls5 == "rls_not_enabled":
        a["rls_enabled"] = "rls_not_enabled"
    else:
        a["rls_enabled"] = "rls_enabled"

    # --- privilege_level ↔ privilege_denied ---
    pl = a.get("privilege_level", "superuser")
    if pl == "non_owner":
        a["privilege_denied"] = "non_owner_denied"
    elif pl == "table_owner":
        a["privilege_denied"] = "owner_execution"
    else:
        a["privilege_denied"] = "superuser_execution"

    pd = a.get("privilege_denied", "owner_execution")
    if pd == "non_owner_denied":
        a["privilege_level"] = "non_owner"
    elif pd == "owner_execution":
        a["privilege_level"] = "table_owner"
    else:
        a["privilege_level"] = "superuser"

    # --- expression_compatibility ↔ command_type ↔ conflict factors ---
    ec = a.get("expression_compatibility", "compatible_pairing")
    ct = a.get("command_type", "ALL")

    if ec == "select_with_check_incompatible":
        a["command_type"] = "SELECT"
        a["select_with_check_conflict"] = "incompatible_with_check"
        a["with_check_expression"] = "simple_boolean_expr"
    elif ec == "insert_with_using_incompatible":
        a["command_type"] = "INSERT"
        a["insert_with_using_conflict"] = "incompatible_using"
        a["using_expression"] = "simple_boolean_expr"
    elif ec == "delete_with_check_incompatible":
        a["command_type"] = "DELETE"
        a["with_check_expression"] = "simple_boolean_expr"

    # Reverse: T5 conflict factors → expression_compatibility
    swcc = a.get("select_with_check_conflict", "compatible_no_with_check")
    if swcc == "incompatible_with_check":
        a["expression_compatibility"] = "select_with_check_incompatible"
        a["command_type"] = "SELECT"
        a["with_check_expression"] = "simple_boolean_expr"

    iwuc = a.get("insert_with_using_conflict", "compatible_no_using")
    if iwuc == "incompatible_using":
        a["expression_compatibility"] = "insert_with_using_incompatible"
        a["command_type"] = "INSERT"
        a["using_expression"] = "simple_boolean_expr"

    # --- invalid_expression ↔ using_expression ---
    ie = a.get("invalid_expression", "valid_expression")
    if ie == "aggregate_in_expression":
        a["using_expression"] = "complex_expr"
    elif ie == "window_function_in_expression":
        a["using_expression"] = "complex_expr"

    ue = a.get("using_expression", "omitted")
    if ie == "valid_expression" and ue == "complex_expr":
        a["invalid_expression"] = "valid_expression"

    # --- only_restrictive_policy ↔ policy_type ---
    orp = a.get("only_restrictive_policy", "has_permissive_policy")
    if orp == "only_restrictive_no_permissive":
        a["policy_type"] = "restrictive"

    # --- role_name_shape ↔ role_existence ↔ role_target ---
    rns = a.get("role_name_shape", "simple_id")
    if rns == "nonexistent_role":
        a["role_existence"] = "role_not_exists"
        a["role_target"] = "single_role"
    elif rns == "PUBLIC_keyword":
        a["role_target"] = "PUBLIC"
        a["role_existence"] = "role_exists"
    else:
        if rns in {"simple_id", "quoted_id"}:
            a["role_target"] = "single_role"
            a["role_existence"] = "role_exists"

    re = a.get("role_existence", "role_exists")
    if re == "role_not_exists":
        a["role_name_shape"] = "nonexistent_role"
        a["role_target"] = "single_role"

    rt = a.get("role_target", "PUBLIC")
    if rt == "PUBLIC":
        a["role_name_shape"] = "PUBLIC_keyword"
        a["role_existence"] = "role_exists"
    elif rt in {"single_role", "multiple_roles"}:
        if rns not in {"nonexistent_role", "PUBLIC_keyword"}:
            a["role_name_shape"] = "simple_id"
        a["role_existence"] = "role_exists"

    # --- command_type → expression consistency ---
    ct = a.get("command_type", "ALL")
    ec = a.get("expression_compatibility", "compatible_pairing")
    if ec == "compatible_pairing":
        # Set compatible using/with_check for the command type
        if ct in {"ALL", "UPDATE", "MERGE"}:
            if a.get("using_expression", "omitted") == "omitted":
                a["using_expression"] = "simple_boolean_expr"
            if a.get("with_check_expression", "omitted") == "omitted":
                a["with_check_expression"] = "simple_boolean_expr"
        elif ct in {"SELECT", "DELETE", "DML_RETURNING", "INSERT_ON_CONFLICT"}:
            if a.get("using_expression", "omitted") == "omitted":
                a["using_expression"] = "simple_boolean_expr"
            a["with_check_expression"] = "omitted"
        elif ct == "INSERT":
            a["using_expression"] = "omitted"
            if a.get("with_check_expression", "omitted") == "omitted":
                a["with_check_expression"] = "simple_boolean_expr"

    # --- expected_status=failure → representative failure ---
    es = a.get("expected_status", "success")
    if es == "failure":
        a["object_state"] = "exists_same_table"
        a["duplicate_policy_name"] = "same_table_same_name"
        a["policy_name_shape"] = "duplicate_name_same_table"

    # --- Derive expected_status from failure count ---
    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _baseline_assignments(
    obligation: CreatePolicyFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
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
        raise CreatePolicyFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreatePolicyFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreatePolicyFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_policy_factor_loop_plan(
    repository_root: Path,
) -> CreatePolicyFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_policy_factor_loop_obligations(root)
    cases: list[CreatePolicyFactorCase] = []
    delegated: list[CreatePolicyFactorObligation] = []
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
            CreatePolicyFactorCase(
                ordinal=ordinal,
                case_id=f"CREATEPOLICY{ordinal:05d}",
                sql_filename=f"CREATEPOLICY{ordinal:05d}.sql",
                object_prefix=f"createpolicy_{ordinal:05d}_",
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
    plan = CreatePolicyFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 81 or len(plan.delegated) != 0:
        raise CreatePolicyFactorLoopError(
            "factor loop plan count drift"
        )
    if len({row.primary_obligation_id for row in plan.cases}) != 81:
        raise CreatePolicyFactorLoopError(
            "local obligation mapping drift"
        )
    if len({row.sql_filename for row in plan.cases}) != 81:
        raise CreatePolicyFactorLoopError("duplicate SQL filename")
    return plan


def compile_create_policy_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreatePolicyFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreatePolicyFactorObligation(
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
    if len(rows) != 81:
        raise CreatePolicyFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreatePolicyFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 80}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreatePolicyFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreatePolicyFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 81:
        raise CreatePolicyFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreatePolicyFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "CreatePolicyFactorLoopError",
    "CreatePolicyGrammarAction",
    "CreatePolicyFactorObligation",
    "CreatePolicyFactorCase",
    "CreatePolicyFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_create_policy_factor_loop_obligations",
    "build_create_policy_factor_loop_plan",
    "_obligation_multiset_sha256",
]
