"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE TABLESPACE.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE TABLESPACE``.  CREATE TABLESPACE is a PostgreSQL storage-level
DDL statement with a single official synopsis branch:
``CREATE TABLESPACE name [ OWNER {...} ] LOCATION 'directory' [ WITH (...) ]``.
The statement requires superuser privilege and registers a
``pg_catalog.pg_tablespace`` catalog row plus a filesystem directory
marker (not a ``pg_class`` relation), so column/table/relation coverage
is ``not_applicable`` and there is no ``INV`` block.  CREATE TABLESPACE
does not create tables, so the bookend (DROP TABLE IF EXISTS) is never
emitted (table-less-exempt).  Cleanup uses ``DROP TABLESPACE IF EXISTS``
plus ``DROP ROLE IF EXISTS``.

Each local obligation becomes exactly one regress program.  The 1
``GRM`` obligation covers the single synopsis branch; the 66 canonical
``SFV`` rows are loaded from the shipped applicability universe
(``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CreateTablespaceFactorLoopError(ValueError):
    """Raised when a frozen CREATE TABLESPACE obligation input drifts."""


@dataclass(frozen=True)
class CreateTablespaceGrammarAction:
    """One official target action form of the CREATE TABLESPACE synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateTablespaceFactorObligation:
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
class CreateTablespaceFactorCase:
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
class CreateTablespaceFactorLoopPlan:
    obligations: tuple[CreateTablespaceFactorObligation, ...]
    cases: tuple[CreateTablespaceFactorCase, ...]
    delegated: tuple[CreateTablespaceFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-createtablespace.html).
_BRANCH_CREATE = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createtablespace"

# The single consumer action for every CREATE TABLESPACE obligation.
_REPRESENTATIVE_ACTION = "create"

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "exists"),
        ("object_state", "reserved_name_conflict"),
        ("tablespace_name_shape", "duplicate_name"),
        ("tablespace_name_shape", "invalid_name"),
        ("tablespace_name_shape", "pg_prefix_reserved"),
        ("privilege_level", "non_superuser"),
        ("non_superuser_attempt", "non_superuser_execution"),
        ("directory_condition", "not_exists"),
        ("directory_condition", "permission_denied"),
        ("directory_condition", "non_empty"),
        ("filesystem_dependency", "directory_not_exists"),
        ("filesystem_dependency", "directory_wrong_owner"),
        ("filesystem_dependency", "path_not_absolute"),
        ("nonexistent_directory", "directory_missing"),
        ("directory_permission_denied", "wrong_owner"),
        ("directory_path_shape", "relative_path"),
        ("directory_path_shape", "empty_path"),
        ("non_absolute_path", "relative_path"),
        ("transaction_context", "inside_transaction_block"),
        ("inside_transaction_block", "inside_transaction"),
        ("role_existence", "role_not_exists"),
        ("nonexistent_owner_role", "role_missing"),
        ("owner_name_shape", "nonexistent_role"),
        ("invalid_option", "invalid_option_name"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("object_state", "exists"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("object_state", "reserved_name_conflict"): (
        "42939",
        "reserved_name_provisional",
    ),
    ("tablespace_name_shape", "duplicate_name"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("tablespace_name_shape", "invalid_name"): (
        "42602",
        "invalid_name_provisional",
    ),
    ("tablespace_name_shape", "pg_prefix_reserved"): (
        "42939",
        "reserved_name_provisional",
    ),
    ("privilege_level", "non_superuser"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("non_superuser_attempt", "non_superuser_execution"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("directory_condition", "not_exists"): (
        "58P01",
        "directory_does_not_exist_provisional",
    ),
    ("directory_condition", "permission_denied"): (
        "42501",
        "directory_permission_denied_provisional",
    ),
    ("directory_condition", "non_empty"): (
        "42809",
        "directory_not_empty_provisional",
    ),
    ("filesystem_dependency", "directory_not_exists"): (
        "58P01",
        "directory_does_not_exist_provisional",
    ),
    ("filesystem_dependency", "directory_wrong_owner"): (
        "42501",
        "directory_permission_denied_provisional",
    ),
    ("filesystem_dependency", "path_not_absolute"): (
        "42601",
        "path_not_absolute_provisional",
    ),
    ("nonexistent_directory", "directory_missing"): (
        "58P01",
        "directory_does_not_exist_provisional",
    ),
    ("directory_permission_denied", "wrong_owner"): (
        "42501",
        "directory_permission_denied_provisional",
    ),
    ("directory_path_shape", "relative_path"): (
        "42601",
        "path_not_absolute_provisional",
    ),
    ("directory_path_shape", "empty_path"): (
        "42601",
        "empty_path_provisional",
    ),
    ("non_absolute_path", "relative_path"): (
        "42601",
        "path_not_absolute_provisional",
    ),
    ("transaction_context", "inside_transaction_block"): (
        "0A000",
        "transaction_block_not_supported_provisional",
    ),
    ("inside_transaction_block", "inside_transaction"): (
        "0A000",
        "transaction_block_not_supported_provisional",
    ),
    ("role_existence", "role_not_exists"): (
        "42704",
        "role_does_not_exist_provisional",
    ),
    ("nonexistent_owner_role", "role_missing"): (
        "42704",
        "role_does_not_exist_provisional",
    ),
    ("owner_name_shape", "nonexistent_role"): (
        "42704",
        "role_does_not_exist_provisional",
    ),
    ("invalid_option", "invalid_option_name"): (
        "42704",
        "invalid_option_provisional",
    ),
}


def _load_grammar_actions() -> tuple[CreateTablespaceGrammarAction, ...]:
    """Freeze every CREATE TABLESPACE synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "create",
            _BRANCH_CREATE,
            (
                "CREATE TABLESPACE tablespace_name "
                "[ OWNER { new_owner | CURRENT_ROLE | "
                "CURRENT_USER | SESSION_USER } ] "
                "LOCATION 'directory' "
                "[ WITH ( tablespace_option = value [, ... ] ) ]"
            ),
            "synopsis-create-tablespace",
        ),
    )
    actions = [
        CreateTablespaceGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise CreateTablespaceFactorLoopError(
            "create tablespace action count drift"
        )
    return tuple(actions)


def _compile_grammar_obligations() -> list[CreateTablespaceFactorObligation]:
    rows: list[CreateTablespaceFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateTablespaceFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CTSP-GRM|{action.grammar_branch_id}|"
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
        raise CreateTablespaceFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateTablespaceFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_tablespace")
    if len(catalog_rows) != 66:
        raise CreateTablespaceFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[CreateTablespaceFactorObligation] = []
    for row in catalog_rows:
        consumer = _REPRESENTATIVE_ACTION
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateTablespaceFactorObligation(
                ordinal=0,
                obligation_id=f"CTSP-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreateTablespaceFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-tablespace-factor-obligations-v1\n"
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
    "create": _BRANCH_CREATE,
}

# Dense baseline defaults (all positive factor values).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_CREATE,
    "grammar_branch": _BRANCH_CREATE,
    "target_action": "create",
    "object_state": "not_exists",
    "expected_status": "success",
    "owner_clause": "omitted",
    "with_clause": "omitted",
    "directory_condition": "exists_valid",
    "tablespace_name_shape": "simple_id",
    "owner_name_shape": "simple_id",
    "directory_path_shape": "absolute_path",
    "privilege_level": "superuser",
    "filesystem_dependency": "directory_exists_owned_by_postgres",
    "transaction_context": "outside_transaction",
    "role_existence": "role_exists",
    "duplicate_tablespace_name": "no_conflict",
    "pg_reserved_name": "normal_name",
    "nonexistent_directory": "directory_exists",
    "non_absolute_path": "absolute_path",
    "invalid_option": "valid_option",
    "directory_permission_denied": "proper_permission",
    "non_superuser_attempt": "superuser_execution",
    "inside_transaction_block": "outside_transaction",
    "nonexistent_owner_role": "role_exists",
    "verification_mode": "catalog_query_pg_tablespace",
    "cleanup_mode": "drop_tablespace",
}


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values.

    The T5 single-value factors describe the same scenario as their T1-T4
    counterparts.  When the primary factor is a T1-T4 value, the
    corresponding T5 value is derived; when the primary is a T5 value, the
    T1-T4 counterpart is derived.  This keeps the baseline assignment
    self-consistent so the render produces SQL that reaches the intended
    boundary.
    """

    os_ = a.get("object_state", "not_exists")
    tns = a.get("tablespace_name_shape", "simple_id")
    dtn = a.get("duplicate_tablespace_name", "no_conflict")
    pgr = a.get("pg_reserved_name", "normal_name")

    # duplicate-name cluster: object_state / tablespace_name_shape /
    # duplicate_tablespace_name
    if (
        os_ == "exists"
        or tns == "duplicate_name"
        or dtn == "same_name_conflict"
    ):
        a["object_state"] = "exists"
        a["tablespace_name_shape"] = "duplicate_name"
        a["duplicate_tablespace_name"] = "same_name_conflict"

    # reserved-name cluster: object_state / tablespace_name_shape /
    # pg_reserved_name
    if (
        os_ == "reserved_name_conflict"
        or tns == "pg_prefix_reserved"
        or pgr == "pg_prefix_name"
    ):
        a["object_state"] = "reserved_name_conflict"
        a["tablespace_name_shape"] = "pg_prefix_reserved"
        a["pg_reserved_name"] = "pg_prefix_name"

    # non-superuser cluster: privilege_level / non_superuser_attempt
    ep = a.get("privilege_level", "superuser")
    nsa = a.get("non_superuser_attempt", "superuser_execution")
    if ep == "non_superuser" or nsa == "non_superuser_execution":
        a["privilege_level"] = "non_superuser"
        a["non_superuser_attempt"] = "non_superuser_execution"

    # directory clusters: directory_condition / filesystem_dependency /
    # nonexistent_directory / directory_permission_denied
    dc = a.get("directory_condition", "exists_valid")
    fd = a.get("filesystem_dependency", "")
    nd = a.get("nonexistent_directory", "directory_exists")
    dpd = a.get("directory_permission_denied", "proper_permission")

    if (
        dc == "not_exists"
        or fd == "directory_not_exists"
        or nd == "directory_missing"
    ):
        a["directory_condition"] = "not_exists"
        a["filesystem_dependency"] = "directory_not_exists"
        a["nonexistent_directory"] = "directory_missing"
    elif (
        dc == "permission_denied"
        or fd == "directory_wrong_owner"
        or dpd == "wrong_owner"
    ):
        a["directory_condition"] = "permission_denied"
        a["filesystem_dependency"] = "directory_wrong_owner"
        a["directory_permission_denied"] = "wrong_owner"
    elif dc == "non_empty":
        a["filesystem_dependency"] = "directory_exists_owned_by_postgres"
    else:
        a["filesystem_dependency"] = "directory_exists_owned_by_postgres"

    # non-absolute-path cluster: directory_path_shape / non_absolute_path /
    # filesystem_dependency=path_not_absolute
    dps = a.get("directory_path_shape", "absolute_path")
    nap = a.get("non_absolute_path", "absolute_path")
    if (
        dps == "relative_path"
        or nap == "relative_path"
        or fd == "path_not_absolute"
    ):
        a["directory_path_shape"] = "relative_path"
        a["non_absolute_path"] = "relative_path"
        a["filesystem_dependency"] = "path_not_absolute"

    # transaction cluster: transaction_context / inside_transaction_block
    tc = a.get("transaction_context", "outside_transaction")
    itb = a.get("inside_transaction_block", "outside_transaction")
    if (
        tc == "inside_transaction_block"
        or itb == "inside_transaction"
    ):
        a["transaction_context"] = "inside_transaction_block"
        a["inside_transaction_block"] = "inside_transaction"

    # owner-missing cluster: role_existence / nonexistent_owner_role /
    # owner_name_shape
    re_ = a.get("role_existence", "role_exists")
    nor = a.get("nonexistent_owner_role", "role_exists")
    ons = a.get("owner_name_shape", "simple_id")
    if (
        re_ == "role_not_exists"
        or nor == "role_missing"
        or ons == "nonexistent_role"
    ):
        a["role_existence"] = "role_not_exists"
        a["nonexistent_owner_role"] = "role_missing"
        a["owner_name_shape"] = "nonexistent_role"

    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: CreateTablespaceFactorObligation,
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
    if len(assignments) != len(set(assignments)):
        raise CreateTablespaceFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateTablespaceFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateTablespaceFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_tablespace_factor_loop_plan(
    repository_root: Path,
) -> CreateTablespaceFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_tablespace_factor_loop_obligations(root)
    cases: list[CreateTablespaceFactorCase] = []
    delegated: list[CreateTablespaceFactorObligation] = []
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
            CreateTablespaceFactorCase(
                ordinal=ordinal,
                case_id=f"CREATETABLESPACE{ordinal:05d}",
                sql_filename=f"CREATETABLESPACE{ordinal:05d}.sql",
                object_prefix=f"createtablespace_{ordinal:05d}_",
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
    plan = CreateTablespaceFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 67 or len(plan.delegated) != 0:
        raise CreateTablespaceFactorLoopError(
            "factor loop plan count drift"
        )
    if len({row.primary_obligation_id for row in plan.cases}) != 67:
        raise CreateTablespaceFactorLoopError(
            "local obligation mapping drift"
        )
    if len({row.sql_filename for row in plan.cases}) != 67:
        raise CreateTablespaceFactorLoopError("duplicate SQL filename")
    return plan


def compile_create_tablespace_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateTablespaceFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateTablespaceFactorObligation(
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
    if len(rows) != 67:
        raise CreateTablespaceFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateTablespaceFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 66}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateTablespaceFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateTablespaceFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 67:
        raise CreateTablespaceFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreateTablespaceFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "CreateTablespaceFactorLoopError",
    "CreateTablespaceGrammarAction",
    "CreateTablespaceFactorObligation",
    "CreateTablespaceFactorCase",
    "CreateTablespaceFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_create_tablespace_factor_loop_obligations",
    "build_create_tablespace_factor_loop_plan",
    "_obligation_multiset_sha256",
]
