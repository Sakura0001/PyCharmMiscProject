"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE ROLE.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE ROLE``.  CREATE ROLE defines a database role (a
``pg_catalog.pg_authid`` catalog row), not a ``pg_class`` relation.  The
official synopsis has a single branch:
``CREATE ROLE name [ [ WITH ] option [ ... ] ]``.

The statement touches the ``pg_catalog.pg_authid`` catalog row (not a
relation), so column/table/relation coverage is ``not_applicable`` and
there is no ``INV`` block.  CREATE ROLE does not create tables, so the
bookend (DROP TABLE IF EXISTS) is never emitted; a residual
``SELECT 1 AS residual_check_no_objects;`` placeholder witnesses the
table-less nature of every program.

Each local obligation becomes exactly one regress program.  The 101
canonical ``SFV`` rows are loaded from the shipped applicability universe
(``postgresql_18_4_factor_audit.tsv``); the 1 ``GRM`` target form is
frozen from the official synopsis branch.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CreateRoleFactorLoopError(ValueError):
    """Raised when a frozen CREATE ROLE obligation input drifts."""


@dataclass(frozen=True)
class CreateRoleGrammarAction:
    """One official target action form of the CREATE ROLE synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateRoleFactorObligation:
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
class CreateRoleFactorCase:
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
class CreateRoleFactorLoopPlan:
    obligations: tuple[CreateRoleFactorObligation, ...]
    cases: tuple[CreateRoleFactorCase, ...]
    delegated: tuple[CreateRoleFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-createrole.html).
_BRANCH = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createrole"

# A representative action used as the baseline consumer for canonical
# factors that are not bound to one specific branch.
_REPRESENTATIVE_ACTION = "create_role_branch_1"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH: "create_role_branch_1",
}


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise CreateRoleFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "with_keyword":
        return "create_role_branch_1"
    return _REPRESENTATIVE_ACTION


# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates -- DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        # duplicate_object_name (42710)
        ("expected_status", "failure"),
        ("role_identity", "exists"),
        ("role_identity", "quoted_duplicate"),
        ("duplicate_role_name", "same_name_exists"),
        ("duplicate_role_name", "case_insensitive_duplicate"),
        # insufficient_privilege (42501)
        ("executor_privilege", "normal_user_no_createrole"),
        ("privilege_insufficient", "no_createrole_privilege"),
        ("privilege_insufficient", "non_superuser_creating_superuser"),
        ("privilege_insufficient", "non_superuser_creating_replication"),
        ("privilege_insufficient", "non_superuser_creating_bypassrls"),
        # missing_referenced_role (42704)
        ("referenced_role_dependency", "nonexistent_role"),
        ("nonexistent_referenced_role", "in_role_references_nonexistent"),
        ("nonexistent_referenced_role", "role_clause_references_nonexistent"),
        ("nonexistent_referenced_role", "admin_clause_references_nonexistent"),
        # syntax_error (42601)
        ("conflicting_attribute_pair", "superuser_and_nosuperuser"),
        ("conflicting_attribute_pair", "login_and_nologin"),
        ("conflicting_attribute_pair", "multiple_conflicting_pairs"),
        ("role_name_shape", "missing_name"),
        # invalid_parameter_value (22023)
        ("invalid_parameter_value", "invalid_connlimit_type"),
        ("invalid_parameter_value", "empty_password_string"),
        ("connlimit_value_shape", "invalid_type"),
        # invalid_datetime_format (22007)
        ("invalid_parameter_value", "invalid_timestamp_format"),
        ("timestamp_value_shape", "invalid_format"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42710",
        "duplicate_role_provisional",
    ),
    ("role_identity", "exists"): (
        "42710",
        "duplicate_role_provisional",
    ),
    ("role_identity", "quoted_duplicate"): (
        "42710",
        "duplicate_role_provisional",
    ),
    ("duplicate_role_name", "same_name_exists"): (
        "42710",
        "duplicate_role_provisional",
    ),
    ("duplicate_role_name", "case_insensitive_duplicate"): (
        "42710",
        "duplicate_role_provisional",
    ),
    ("executor_privilege", "normal_user_no_createrole"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("privilege_insufficient", "no_createrole_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("privilege_insufficient", "non_superuser_creating_superuser"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("privilege_insufficient", "non_superuser_creating_replication"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("privilege_insufficient", "non_superuser_creating_bypassrls"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("referenced_role_dependency", "nonexistent_role"): (
        "42704",
        "undefined_role_provisional",
    ),
    ("nonexistent_referenced_role", "in_role_references_nonexistent"): (
        "42704",
        "undefined_role_provisional",
    ),
    ("nonexistent_referenced_role", "role_clause_references_nonexistent"): (
        "42704",
        "undefined_role_provisional",
    ),
    ("nonexistent_referenced_role", "admin_clause_references_nonexistent"): (
        "42704",
        "undefined_role_provisional",
    ),
    ("conflicting_attribute_pair", "superuser_and_nosuperuser"): (
        "42601",
        "syntax_error_provisional",
    ),
    ("conflicting_attribute_pair", "login_and_nologin"): (
        "42601",
        "syntax_error_provisional",
    ),
    ("conflicting_attribute_pair", "multiple_conflicting_pairs"): (
        "42601",
        "syntax_error_provisional",
    ),
    ("role_name_shape", "missing_name"): (
        "42601",
        "syntax_error_provisional",
    ),
    ("invalid_parameter_value", "invalid_connlimit_type"): (
        "22023",
        "invalid_parameter_value_provisional",
    ),
    ("invalid_parameter_value", "empty_password_string"): (
        "22023",
        "invalid_parameter_value_provisional",
    ),
    ("connlimit_value_shape", "invalid_type"): (
        "22023",
        "invalid_parameter_value_provisional",
    ),
    ("invalid_parameter_value", "invalid_timestamp_format"): (
        "22007",
        "invalid_datetime_format_provisional",
    ),
    ("timestamp_value_shape", "invalid_format"): (
        "22007",
        "invalid_datetime_format_provisional",
    ),
}


def _load_grammar_actions() -> tuple[CreateRoleGrammarAction, ...]:
    """Freeze every CREATE ROLE synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "create_role_branch_1",
            _BRANCH,
            "CREATE ROLE name [ [ WITH ] option [ ... ] ]",
            "synopsis-create-role-branch-1",
        ),
    )
    actions = [
        CreateRoleGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise CreateRoleFactorLoopError("create role action count drift")
    return tuple(actions)


def _compile_grammar_obligations() -> list[CreateRoleFactorObligation]:
    rows: list[CreateRoleFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateRoleFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CRP-GRM|{action.grammar_branch_id}|"
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
        raise CreateRoleFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateRoleFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_role")
    if len(catalog_rows) != 101:
        raise CreateRoleFactorLoopError("canonical obligation count drift")
    rows: list[CreateRoleFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateRoleFactorObligation(
                ordinal=0,
                obligation_id=f"CRP-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreateRoleFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"create-role-factor-obligations-v1\n")
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
    "create_role_branch_1": _BRANCH,
}

# Dense baseline defaults (all positive factor values).  Boundary factors
# are derived in :func:`_derive_overlapping_factors`.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH,
    "role_identity": "not_exists",
    "expected_status": "success",
    "role_attribute": (
        "default_all_nosuperuser_nocreatedb_nocreaterole_"
        "inherit_nologin_noreplication_nobypassrls"
    ),
    "password_clause": "omitted",
    "connection_limit_clause": "omitted",
    "valid_until_clause": "omitted",
    "membership_clause": "omitted",
    "with_keyword": "present",
    "role_name_shape": "simple_id",
    "password_value_shape": "valid_string",
    "connlimit_value_shape": "positive_integer",
    "timestamp_value_shape": "valid_iso_timestamp",
    "executor_privilege": "superuser",
    "referenced_role_dependency": "existing_role",
    "duplicate_role_name": "none",
    "privilege_insufficient": "none",
    "nonexistent_referenced_role": "none",
    "invalid_parameter_value": "none",
    "conflicting_attribute_pair": "none",
    "verification_mode": "pg_roles_catalog_query",
    "cleanup_mode": "drop_role",
}


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive boundary factors and expected_status from primary values.

    Keeps the baseline assignment self-consistent so the render produces
    SQL that reaches the intended boundary.
    """

    # --- Group 1: duplicate scenario -------------------------------
    # expected_status / role_identity / duplicate_role_name
    if a.get("expected_status") == "failure":
        a["role_identity"] = "exists"
        a["duplicate_role_name"] = "same_name_exists"
    if a.get("role_identity") == "exists":
        a["duplicate_role_name"] = "same_name_exists"
    if a.get("role_identity") == "quoted_duplicate":
        a["duplicate_role_name"] = "case_insensitive_duplicate"
    if a.get("duplicate_role_name") == "same_name_exists":
        a["role_identity"] = "exists"
    if a.get("duplicate_role_name") == "case_insensitive_duplicate":
        a["role_identity"] = "quoted_duplicate"

    # --- Group 2: privilege ----------------------------------------
    if a.get("executor_privilege") == "normal_user_no_createrole":
        a["privilege_insufficient"] = "no_createrole_privilege"
    if a.get("privilege_insufficient") == "no_createrole_privilege":
        a["executor_privilege"] = "normal_user_no_createrole"
    if a.get("privilege_insufficient") == "non_superuser_creating_superuser":
        a["role_attribute"] = "superuser"
        a["executor_privilege"] = "createrole_privilege"
    if a.get("privilege_insufficient") == "non_superuser_creating_replication":
        a["role_attribute"] = "replication"
        a["executor_privilege"] = "createrole_privilege"
    if a.get("privilege_insufficient") == "non_superuser_creating_bypassrls":
        a["role_attribute"] = "bypassrls"
        a["executor_privilege"] = "createrole_privilege"
    # role_attribute requiring superuser executor (only when no
    # privilege_insufficient is active)
    if a.get("privilege_insufficient") == "none":
        ra = a.get("role_attribute", "default_all_nosuperuser")
        if ra in ("superuser", "replication", "bypassrls"):
            a["executor_privilege"] = "superuser"

    # --- Group 3: referenced-role failure --------------------------
    if a.get("referenced_role_dependency") == "nonexistent_role":
        a["nonexistent_referenced_role"] = "in_role_references_nonexistent"
        a["membership_clause"] = "in_role"
    if a.get("nonexistent_referenced_role") == "in_role_references_nonexistent":
        a["referenced_role_dependency"] = "nonexistent_role"
        a["membership_clause"] = "in_role"
    if a.get("nonexistent_referenced_role") == "role_clause_references_nonexistent":
        a["referenced_role_dependency"] = "nonexistent_role"
        a["membership_clause"] = "role_clause"
    if a.get("nonexistent_referenced_role") == "admin_clause_references_nonexistent":
        a["referenced_role_dependency"] = "nonexistent_role"
        a["membership_clause"] = "admin_clause"
    # self_reference / multiple_roles arm membership
    rmd = a.get("referenced_role_dependency", "existing_role")
    if rmd == "self_reference":
        a["membership_clause"] = "in_role"
    elif rmd == "multiple_roles":
        a["membership_clause"] = "in_role"

    # --- Group 4: invalid parameter / syntax ----------------------
    if a.get("invalid_parameter_value") == "invalid_connlimit_type":
        a["connlimit_value_shape"] = "invalid_type"
        a["connection_limit_clause"] = "positive_limit"
    if a.get("connlimit_value_shape") == "invalid_type":
        a["invalid_parameter_value"] = "invalid_connlimit_type"
        a["connection_limit_clause"] = "positive_limit"
    if a.get("invalid_parameter_value") == "invalid_timestamp_format":
        a["timestamp_value_shape"] = "invalid_format"
        a["valid_until_clause"] = "future_timestamp"
    if a.get("timestamp_value_shape") == "invalid_format":
        a["invalid_parameter_value"] = "invalid_timestamp_format"
        a["valid_until_clause"] = "future_timestamp"
    if a.get("invalid_parameter_value") == "empty_password_string":
        a["password_value_shape"] = "empty_string"
        a["password_clause"] = "unencrypted_password"

    # --- Group 5: arm clauses for non-default T3 values -----------
    pvs = a.get("password_value_shape", "valid_string")
    if pvs == "null_value":
        a["password_clause"] = "password_null"
    elif pvs in ("empty_string", "special_characters"):
        a["password_clause"] = "unencrypted_password"
    elif pvs in ("encrypted_md5_format", "encrypted_scram_format"):
        a["password_clause"] = "encrypted_password"

    cvs = a.get("connlimit_value_shape", "positive_integer")
    if cvs == "zero":
        a["connection_limit_clause"] = "zero_limit"
    elif cvs == "negative_one":
        a["connection_limit_clause"] = "negative_one_unlimited"
    elif cvs == "large_number":
        a["connection_limit_clause"] = "positive_limit"

    tvs = a.get("timestamp_value_shape", "valid_iso_timestamp")
    if tvs in ("valid_date_only", "far_future"):
        a["valid_until_clause"] = "future_timestamp"
    elif tvs == "past_date":
        a["valid_until_clause"] = "past_timestamp"
    elif tvs == "infinity_literal":
        a["valid_until_clause"] = "infinity"

    # --- Derive expected_status from failure count -----------------
    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _baseline_assignments(
    obligation: CreateRoleFactorObligation,
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
        raise CreateRoleFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateRoleFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateRoleFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_role_factor_loop_plan(
    repository_root: Path,
) -> CreateRoleFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_role_factor_loop_obligations(root)
    cases: list[CreateRoleFactorCase] = []
    delegated: list[CreateRoleFactorObligation] = []
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
            CreateRoleFactorCase(
                ordinal=ordinal,
                case_id=f"CREATEROLE{ordinal:05d}",
                sql_filename=f"CREATEROLE{ordinal:05d}.sql",
                object_prefix=f"createrole_{ordinal:05d}_",
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
    plan = CreateRoleFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 102 or len(plan.delegated) != 0:
        raise CreateRoleFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 102:
        raise CreateRoleFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 102:
        raise CreateRoleFactorLoopError("duplicate SQL filename")
    return plan


def compile_create_role_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateRoleFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateRoleFactorObligation(
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
    if len(rows) != 102:
        raise CreateRoleFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateRoleFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 101}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateRoleFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateRoleFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 102:
        raise CreateRoleFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreateRoleFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "CreateRoleFactorLoopError",
    "CreateRoleGrammarAction",
    "CreateRoleFactorObligation",
    "CreateRoleFactorCase",
    "CreateRoleFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_create_role_factor_loop_obligations",
    "build_create_role_factor_loop_plan",
    "_obligation_multiset_sha256",
]
