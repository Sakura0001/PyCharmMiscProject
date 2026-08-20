"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE DATABASE.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE DATABASE``.  The official synopsis has exactly one branch
(``CREATE DATABASE name [ WITH ] ...``), so there is a single ``GRM``
obligation.  The 67 canonical ``SFV`` rows are loaded from the shipped
applicability universe (``postgresql_18_4_factor_audit.tsv``).

CREATE DATABASE requires superuser or ``CREATEDB`` privilege.  Twenty
canonical factor values reach a failure surface (duplicate name,
insufficient privilege, incompatible encoding/locale, nonexistent
template/tablespace, transaction-block violation, etc.).  The remaining
47 ``SFV`` values plus the single ``GRM`` action are success-covered.

Each local obligation becomes exactly one regress program.  There are no
``RISK`` obligations.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CreateDatabaseFactorLoopError(ValueError):
    """Raised when a frozen CREATE DATABASE obligation input drifts."""


@dataclass(frozen=True)
class CreateDatabaseGrammarAction:
    """One official target action form of the CREATE DATABASE synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateDatabaseFactorObligation:
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
class CreateDatabaseFactorCase:
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
class CreateDatabaseFactorLoopPlan:
    obligations: tuple[CreateDatabaseFactorObligation, ...]
    cases: tuple[CreateDatabaseFactorCase, ...]
    delegated: tuple[CreateDatabaseFactorObligation, ...]
    obligation_multiset_sha256: str


_BRANCH = "branch_create_database"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createdatabase"

_REPRESENTATIVE_ACTION = "create_database"

_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH: "create_database",
}

_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "owner_clause": _REPRESENTATIVE_ACTION,
    "template_clause": _REPRESENTATIVE_ACTION,
    "encoding_clause": _REPRESENTATIVE_ACTION,
    "locale_clause": _REPRESENTATIVE_ACTION,
    "strategy_clause": _REPRESENTATIVE_ACTION,
    "privilege_level": _REPRESENTATIVE_ACTION,
    "database_name_shape": _REPRESENTATIVE_ACTION,
    "owner_name_shape": _REPRESENTATIVE_ACTION,
    "tablespace_name_shape": _REPRESENTATIVE_ACTION,
    "template_existence": _REPRESENTATIVE_ACTION,
    "encoding_locale_compatibility": _REPRESENTATIVE_ACTION,
    "role_set_role_ability": _REPRESENTATIVE_ACTION,
    "tablespace_existence": _REPRESENTATIVE_ACTION,
    "duplicate_database_name": _REPRESENTATIVE_ACTION,
    "privilege_denied": _REPRESENTATIVE_ACTION,
    "cannot_set_role_to_owner": _REPRESENTATIVE_ACTION,
    "template_has_connections": _REPRESENTATIVE_ACTION,
    "encoding_locale_incompatible": _REPRESENTATIVE_ACTION,
    "encoding_template_mismatch": _REPRESENTATIVE_ACTION,
    "nonexistent_template": _REPRESENTATIVE_ACTION,
    "nonexistent_tablespace": _REPRESENTATIVE_ACTION,
    "inside_transaction_block": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42501",
        "create_database_declared_failure_provisional",
    ),
    ("object_state", "exists"): (
        "42P04",
        "duplicate_database_provisional",
    ),
    ("privilege_level", "non_createdb_role"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("database_name_shape", "duplicate_name"): (
        "42P04",
        "duplicate_database_provisional",
    ),
    ("owner_name_shape", "nonexistent_role"): (
        "42704",
        "undefined_role_provisional",
    ),
    ("tablespace_name_shape", "nonexistent_tablespace"): (
        "42P27",
        "undefined_tablespace_provisional",
    ),
    ("template_existence", "template_not_exists"): (
        "3D000",
        "invalid_catalog_name_provisional",
    ),
    (
        "template_existence",
        "template_exists_with_connections",
    ): (
        "55006",
        "object_in_use_provisional",
    ),
    ("encoding_locale_compatibility", "incompatible"): (
        "22023",
        "invalid_parameter_value_provisional",
    ),
    ("role_set_role_ability", "cannot_set_role"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("tablespace_existence", "tablespace_not_exists"): (
        "42P27",
        "undefined_tablespace_provisional",
    ),
    ("duplicate_database_name", "same_name_conflict"): (
        "42P04",
        "duplicate_database_provisional",
    ),
    ("privilege_denied", "lacks_createdb"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("cannot_set_role_to_owner", "cannot_set_role"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("template_has_connections", "has_other_connections"): (
        "55006",
        "object_in_use_provisional",
    ),
    ("encoding_locale_incompatible", "incompatible"): (
        "22023",
        "invalid_parameter_value_provisional",
    ),
    (
        "encoding_template_mismatch",
        "mismatches_template_not_template0",
    ): (
        "42P21",
        "invalid_encoding_provisional",
    ),
    ("nonexistent_template", "template_not_exists"): (
        "3D000",
        "invalid_catalog_name_provisional",
    ),
    ("nonexistent_tablespace", "tablespace_not_exists"): (
        "42P27",
        "undefined_tablespace_provisional",
    ),
    ("inside_transaction_block", "inside_transaction"): (
        "25P01",
        "active_sql_transaction_provisional",
    ),
}

_SFV_FAILURE_VALUES = frozenset(_SFV_FAILURE_SQLSTATE.keys())


def _load_grammar_actions() -> tuple[CreateDatabaseGrammarAction, ...]:
    """Freeze every CREATE DATABASE synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "create_database",
            _BRANCH,
            "CREATE DATABASE name [ WITH ] [ OWNER ] ...",
            "sql-createdatabase",
        ),
    )
    actions = [
        CreateDatabaseGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise CreateDatabaseFactorLoopError("action count drift")
    return tuple(actions)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise CreateDatabaseFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise CreateDatabaseFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> list[CreateDatabaseFactorObligation]:
    rows: list[CreateDatabaseFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateDatabaseFactorObligation(
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
        raise CreateDatabaseFactorLoopError("grammar obligation drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateDatabaseFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_database")
    if len(catalog_rows) != 67:
        raise CreateDatabaseFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[CreateDatabaseFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateDatabaseFactorObligation(
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
    rows: tuple[CreateDatabaseFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-database-factor-obligations-v1\n"
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


_ACTION_BRANCH = {
    "create_database": _BRANCH,
}

_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH,
    "grammar_branch": _BRANCH,
    "target_action": "create_database",
    "object_state": "not_exists",
    "expected_status": "success",
    "owner_clause": "omitted",
    "template_clause": "omitted_default_template1",
    "encoding_clause": "omitted",
    "locale_clause": "omitted",
    "strategy_clause": "omitted_default_wal_log",
    "privilege_level": "superuser",
    "database_name_shape": "simple_id",
    "owner_name_shape": "simple_id",
    "tablespace_name_shape": "default_tablespace",
    "template_existence": "template_exists_no_connections",
    "encoding_locale_compatibility": "compatible",
    "role_set_role_ability": "can_set_role",
    "tablespace_existence": "tablespace_exists",
    "duplicate_database_name": "no_conflict",
    "privilege_denied": "has_createdb",
    "cannot_set_role_to_owner": "can_set_role",
    "template_has_connections": "no_other_connections",
    "encoding_locale_incompatible": "compatible",
    "encoding_template_mismatch": "matches_template",
    "nonexistent_template": "template_exists",
    "nonexistent_tablespace": "tablespace_exists",
    "inside_transaction_block": "outside_transaction",
    "verification_mode": "catalog_query_pg_database",
    "cleanup_mode": "drop_database",
}


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive overlapping failure-boundary factors for self-consistency."""

    is_dup = (
        a.get("object_state") == "exists"
        or a.get("database_name_shape") == "duplicate_name"
        or a.get("duplicate_database_name") == "same_name_conflict"
    )
    if is_dup:
        a["object_state"] = "exists"
        a["duplicate_database_name"] = "same_name_conflict"

    is_priv = (
        a.get("privilege_level") == "non_createdb_role"
        or a.get("privilege_denied") == "lacks_createdb"
        or a.get("expected_status") == "failure"
    )
    if is_priv:
        a["privilege_level"] = "non_createdb_role"
        a["privilege_denied"] = "lacks_createdb"

    is_set_role = (
        a.get("cannot_set_role_to_owner") == "cannot_set_role"
        or a.get("role_set_role_ability") == "cannot_set_role"
    )
    if is_set_role:
        a["cannot_set_role_to_owner"] = "cannot_set_role"
        a["role_set_role_ability"] = "cannot_set_role"
        a["owner_clause"] = "specified_other_role"

    if a.get("owner_name_shape") == "nonexistent_role":
        a["owner_clause"] = "specified_other_role"

    is_tmpl_conn = (
        a.get("template_existence") == "template_exists_with_connections"
        or a.get("template_has_connections") == "has_other_connections"
    )
    if is_tmpl_conn:
        a["template_existence"] = "template_exists_with_connections"
        a["template_has_connections"] = "has_other_connections"

    is_tmpl_ne = (
        a.get("template_existence") == "template_not_exists"
        or a.get("nonexistent_template") == "template_not_exists"
    )
    if is_tmpl_ne:
        a["template_existence"] = "template_not_exists"
        a["nonexistent_template"] = "template_not_exists"
        a["template_clause"] = "custom_template"

    is_enc_loc = (
        a.get("encoding_locale_compatibility") == "incompatible"
        or a.get("encoding_locale_incompatible") == "incompatible"
    )
    if is_enc_loc:
        a["encoding_locale_compatibility"] = "incompatible"
        a["encoding_locale_incompatible"] = "incompatible"
        a["template_clause"] = "custom_template"
        a["encoding_clause"] = "LATIN1"

    if (
        a.get("encoding_template_mismatch")
        == "mismatches_template_not_template0"
    ):
        a["template_clause"] = "custom_template"
        if a.get("encoding_clause") == "omitted":
            a["encoding_clause"] = "LATIN1"

    is_ts_ne = (
        a.get("tablespace_name_shape") == "nonexistent_tablespace"
        or a.get("tablespace_existence") == "tablespace_not_exists"
        or a.get("nonexistent_tablespace") == "tablespace_not_exists"
    )
    if is_ts_ne:
        a["tablespace_existence"] = "tablespace_not_exists"
        a["nonexistent_tablespace"] = "tablespace_not_exists"
        if a.get("tablespace_name_shape") != "nonexistent_tablespace":
            a["tablespace_name_shape"] = "nonexistent_tablespace"

    if (
        a.get("encoding_clause") != "omitted"
        or a.get("locale_clause") != "omitted"
    ):
        if a.get("template_clause") == "omitted_default_template1":
            a["template_clause"] = "template0"

    if a.get("locale_clause") == "builtin_locale":
        a["template_clause"] = "template0"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: CreateDatabaseFactorObligation,
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
        raise CreateDatabaseFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateDatabaseFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateDatabaseFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_database_factor_loop_plan(
    repository_root: Path,
) -> CreateDatabaseFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_database_factor_loop_obligations(root)
    cases: list[CreateDatabaseFactorCase] = []
    delegated: list[CreateDatabaseFactorObligation] = []
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
            CreateDatabaseFactorCase(
                ordinal=ordinal,
                case_id=f"CREATEDATABASE{ordinal:05d}",
                sql_filename=f"CREATEDATABASE{ordinal:05d}.sql",
                object_prefix=f"createdatabase_{ordinal:05d}_",
                primary_obligation_id=obligation.obligation_id,
                kind=obligation.kind,
                factor_key=obligation.factor_key,
                factor_value=obligation.value,
                consumer_action_id=obligation.consumer_action_id,
                outcome=outcome,
                expected_sqlstate=sqlstate,
                expected_failure_reason=failure_reason,
                baseline_assignments=_baseline_assignments(
                    obligation
                ),
                execution_profile="serial_sql",
            )
        )
    plan = CreateDatabaseFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 68 or len(plan.delegated) != 0:
        raise CreateDatabaseFactorLoopError("plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 68:
        raise CreateDatabaseFactorLoopError("obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 68:
        raise CreateDatabaseFactorLoopError("duplicate SQL filename")
    return plan


def compile_create_database_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateDatabaseFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateDatabaseFactorObligation(
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
    if len(rows) != 68:
        raise CreateDatabaseFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateDatabaseFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 67}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateDatabaseFactorLoopError("kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateDatabaseFactorLoopError("delegated count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 68:
        raise CreateDatabaseFactorLoopError("local obligation drift")
    allowed = {"covered", "expected_failure", "delegated"}
    if any(row.disposition not in allowed for row in rows):
        raise CreateDatabaseFactorLoopError("unknown disposition")
    return rows


__all__ = [
    "CreateDatabaseFactorLoopError",
    "CreateDatabaseGrammarAction",
    "CreateDatabaseFactorObligation",
    "CreateDatabaseFactorCase",
    "CreateDatabaseFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_create_database_factor_loop_obligations",
    "build_create_database_factor_loop_plan",
    "_obligation_multiset_sha256",
]
