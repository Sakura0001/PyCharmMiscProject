"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE USER MAPPING.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE USER MAPPING``.  The statement has two official synopsis branches:
``CREATE USER MAPPING [IF NOT EXISTS] FOR {user|USER|CURRENT_ROLE|
CURRENT_USER|PUBLIC} SERVER server_name [OPTIONS (...)]``.  The statement
requires a foreign server (and transitively a foreign data wrapper) and
touches the ``pg_catalog.pg_user_mapping`` catalog row (not a ``pg_class``
relation), so column/table/relation coverage is ``not_applicable`` and
there is no ``INV`` block.

CREATE USER MAPPING does not create tables, so the bookend (DROP TABLE
IF EXISTS) is never emitted.  Cleanup uses ``DROP USER MAPPING IF EXISTS``
plus ``DROP SERVER IF EXISTS`` and ``DROP FOREIGN DATA WRAPPER IF EXISTS``.

Each local obligation becomes exactly one regress program.  The 45
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


class CreateUserMappingFactorLoopError(ValueError):
    """Raised when a frozen CREATE USER MAPPING obligation input drifts."""


@dataclass(frozen=True)
class CreateUserMappingGrammarAction:
    """One official target action form of the CREATE USER MAPPING synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateUserMappingFactorObligation:
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
class CreateUserMappingFactorCase:
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
class CreateUserMappingFactorLoopPlan:
    obligations: tuple[CreateUserMappingFactorObligation, ...]
    cases: tuple[CreateUserMappingFactorCase, ...]
    delegated: tuple[CreateUserMappingFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-createusermapping.html).
_BRANCH_DEFINE = "branch_create_user_mapping"
_BRANCH_IF_NOT_EXISTS = "branch_create_user_mapping_if_not_exists"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createusermapping"

_REPRESENTATIVE_ACTION = "define_mapping"


def _canonical_consumer(row) -> str:
    """Map a canonical factor value to its target consumer action."""

    if row.factor == "statement_branch":
        if row.value == _BRANCH_IF_NOT_EXISTS:
            return "define_if_not_exists"
        return "define_mapping"
    if row.factor == "object_state":
        if row.value == "exists":
            return "define_duplicate"
        return "define_mapping"
    if row.factor == "expected_status":
        if row.value == "failure":
            return "define_duplicate"
        return "define_mapping"
    if row.factor == "user_specification":
        return "define_mapping"
    if row.factor == "if_not_exists_clause":
        if row.value == "present":
            return "define_if_not_exists"
        return "define_mapping"
    if row.factor == "options_clause":
        return "define_mapping"
    if row.factor == "server_existence":
        if row.value == "server_not_exists":
            return "define_nonexistent_server"
        return "define_mapping"
    if row.factor == "user_name_shape":
        if row.value == "nonexistent_name":
            return "define_nonexistent_user"
        return "define_mapping"
    if row.factor == "server_name_shape":
        if row.value == "nonexistent_name":
            return "define_nonexistent_server"
        return "define_mapping"
    if row.factor == "option_value_shape":
        if row.value == "duplicate_option_name":
            return "define_duplicate_option"
        return "define_mapping"
    if row.factor == "privilege_level":
        if row.value == "non_privileged":
            return "define_insufficient_priv"
        return "define_mapping"
    if row.factor == "server_dependency":
        if row.value == "server_missing":
            return "define_nonexistent_server"
        return "define_mapping"
    if row.factor == "duplicate_mapping":
        if row.value == "existing_mapping_without_if_not_exists":
            return "define_duplicate"
        return "define_mapping"
    if row.factor == "nonexistent_server":
        if row.value == "server_missing":
            return "define_nonexistent_server"
        return "define_mapping"
    if row.factor == "insufficient_privilege":
        if row.value == "lacks_privilege":
            return "define_insufficient_priv"
        return "define_mapping"
    if row.factor == "duplicate_option_name":
        if row.value == "duplicate_option":
            return "define_duplicate_option"
        return "define_mapping"
    if row.factor == "verification_mode":
        return "define_mapping"
    if row.factor == "cleanup_mode":
        return "define_mapping"
    return _REPRESENTATIVE_ACTION


# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "exists"),
        ("duplicate_mapping", "existing_mapping_without_if_not_exists"),
        ("server_name_shape", "nonexistent_name"),
        ("server_existence", "server_not_exists"),
        ("nonexistent_server", "server_missing"),
        ("server_dependency", "server_missing"),
        ("privilege_level", "non_privileged"),
        ("insufficient_privilege", "lacks_privilege"),
        ("option_value_shape", "duplicate_option_name"),
        ("duplicate_option_name", "duplicate_option"),
        ("user_name_shape", "nonexistent_name"),
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
    (
        "duplicate_mapping",
        "existing_mapping_without_if_not_exists",
    ): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("server_name_shape", "nonexistent_name"): (
        "42704",
        "undefined_object_provisional",
    ),
    ("server_existence", "server_not_exists"): (
        "42704",
        "undefined_object_provisional",
    ),
    ("nonexistent_server", "server_missing"): (
        "42704",
        "undefined_object_provisional",
    ),
    ("server_dependency", "server_missing"): (
        "42704",
        "undefined_object_provisional",
    ),
    ("privilege_level", "non_privileged"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("insufficient_privilege", "lacks_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("option_value_shape", "duplicate_option_name"): (
        "42701",
        "duplicate_object_provisional",
    ),
    ("duplicate_option_name", "duplicate_option"): (
        "42701",
        "duplicate_object_provisional",
    ),
    ("user_name_shape", "nonexistent_name"): (
        "42704",
        "undefined_object_provisional",
    ),
}


def _load_grammar_actions() -> (
    tuple[CreateUserMappingGrammarAction, ...]
):
    """Freeze every CREATE USER MAPPING synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "define_mapping",
            _BRANCH_DEFINE,
            "CREATE USER MAPPING [IF NOT EXISTS] FOR "
            "{user|USER|CURRENT_ROLE|CURRENT_USER|PUBLIC} "
            "SERVER server_name [OPTIONS (...)]",
            "synopsis-define-mapping",
        ),
    )
    actions = [
        CreateUserMappingGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise CreateUserMappingFactorLoopError(
            "create user mapping action count drift"
        )
    return tuple(actions)


def _compile_grammar_obligations() -> (
    list[CreateUserMappingFactorObligation]
):
    rows: list[CreateUserMappingFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateUserMappingFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CUM-GRM|{action.grammar_branch_id}|"
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
        raise CreateUserMappingFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateUserMappingFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_user_mapping")
    if len(catalog_rows) != 45:
        raise CreateUserMappingFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[CreateUserMappingFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateUserMappingFactorObligation(
                ordinal=0,
                obligation_id=f"CUM-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreateUserMappingFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-user-mapping-factor-obligations-v1\n"
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


# Dense baseline defaults (all positive factor values).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_create_user_mapping",
    "object_state": "not_exists",
    "expected_status": "success",
    "user_specification": "named_user",
    "if_not_exists_clause": "omitted",
    "options_clause": "omitted",
    "server_existence": "server_exists",
    "user_name_shape": "simple_id",
    "server_name_shape": "simple_id",
    "option_value_shape": "valid_value",
    "privilege_level": "server_owner",
    "server_dependency": "server_exists_and_valid",
    "duplicate_mapping": "no_conflict",
    "nonexistent_server": "server_exists",
    "insufficient_privilege": "has_privilege",
    "duplicate_option_name": "unique_options",
    "verification_mode": "catalog_query_pg_user_mapping",
    "cleanup_mode": "drop_user_mapping",
}


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive overlapping boundary factors from the primary value.

    branch cluster: statement_branch <-> if_not_exists_clause
    privilege cluster: privilege_level <-> insufficient_privilege
    server cluster: server_name_shape <-> server_existence <->
                    nonexistent_server <-> server_dependency
    duplicate cluster: object_state <-> duplicate_mapping
    options cluster: option_value_shape <-> duplicate_option_name
    user cluster: user_specification=public -> user_name_shape=public_keyword
    """

    # --- branch cluster (bidirectional, read-then-write) ---
    sb = a.get("statement_branch", "branch_create_user_mapping")
    ine = a.get("if_not_exists_clause", "omitted")
    if sb == _BRANCH_IF_NOT_EXISTS or ine == "present":
        a["statement_branch"] = _BRANCH_IF_NOT_EXISTS
        a["if_not_exists_clause"] = "present"
    else:
        a["statement_branch"] = _BRANCH_DEFINE
        a["if_not_exists_clause"] = "omitted"

    # --- privilege cluster ---
    pl = a.get("privilege_level", "server_owner")
    if pl == "non_privileged":
        a["insufficient_privilege"] = "lacks_privilege"
    else:
        a["insufficient_privilege"] = "has_privilege"

    # --- server dependency cluster ---
    sns = a.get("server_name_shape", "simple_id")
    se = a.get("server_existence", "server_exists")
    ns = a.get("nonexistent_server", "server_exists")
    sd = a.get("server_dependency", "server_exists_and_valid")
    server_missing = (
        sns == "nonexistent_name"
        or se == "server_not_exists"
        or ns == "server_missing"
        or sd == "server_missing"
    )
    if server_missing:
        a["server_name_shape"] = "nonexistent_name"
        a["server_existence"] = "server_not_exists"
        a["nonexistent_server"] = "server_missing"
        a["server_dependency"] = "server_missing"
    else:
        a["server_name_shape"] = "simple_id"
        a["server_existence"] = "server_exists"
        a["nonexistent_server"] = "server_exists"
        a["server_dependency"] = "server_exists_and_valid"

    # --- duplicate cluster ---
    os_state = a.get("object_state", "not_exists")
    dm = a.get("duplicate_mapping", "no_conflict")
    if os_state == "exists" or dm == "existing_mapping_without_if_not_exists":
        a["object_state"] = "exists"
        a["duplicate_mapping"] = "existing_mapping_without_if_not_exists"
    else:
        a["object_state"] = "not_exists"
        a["duplicate_mapping"] = "no_conflict"

    # --- options cluster ---
    ovs = a.get("option_value_shape", "valid_value")
    don = a.get("duplicate_option_name", "unique_options")
    if ovs == "duplicate_option_name" or don == "duplicate_option":
        a["option_value_shape"] = "duplicate_option_name"
        a["duplicate_option_name"] = "duplicate_option"
    else:
        a["option_value_shape"] = "valid_value"
        a["duplicate_option_name"] = "unique_options"

    # --- user cluster (public consistency) ---
    us = a.get("user_specification", "named_user")
    uns = a.get("user_name_shape", "simple_id")
    if us == "public" and uns != "nonexistent_name":
        a["user_name_shape"] = "public_keyword"

    # --- Derive expected_status from failure count ---
    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _baseline_assignments(
    obligation: CreateUserMappingFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    failures = _count_baseline_failures(assignments)
    assignments["expected_status"] = (
        "failure" if failures > 0 else "success"
    )
    if len(assignments) != len(set(assignments)):
        raise CreateUserMappingFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateUserMappingFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateUserMappingFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_user_mapping_factor_loop_plan(
    repository_root: Path,
) -> CreateUserMappingFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = (
        compile_create_user_mapping_factor_loop_obligations(root)
    )
    cases: list[CreateUserMappingFactorCase] = []
    delegated: list[CreateUserMappingFactorObligation] = []
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
            CreateUserMappingFactorCase(
                ordinal=ordinal,
                case_id=f"CREATEUSERMAPPING{ordinal:05d}",
                sql_filename=(
                    f"CREATEUSERMAPPING{ordinal:05d}.sql"
                ),
                object_prefix=(
                    f"createusermapping_{ordinal:05d}_"
                ),
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
    plan = CreateUserMappingFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 46 or len(plan.delegated) != 0:
        raise CreateUserMappingFactorLoopError(
            "factor loop plan count drift"
        )
    if (
        len({row.primary_obligation_id for row in plan.cases})
        != 46
    ):
        raise CreateUserMappingFactorLoopError(
            "local obligation mapping drift"
        )
    if (
        len({row.sql_filename for row in plan.cases}) != 46
    ):
        raise CreateUserMappingFactorLoopError(
            "duplicate SQL filename"
        )
    return plan


def compile_create_user_mapping_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateUserMappingFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateUserMappingFactorObligation(
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
    if len(rows) != 46:
        raise CreateUserMappingFactorLoopError(
            "obligation count drift"
        )
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateUserMappingFactorLoopError(
            "duplicate obligation id"
        )
    expected_kind_counts = {"GRM": 1, "SFV": 45}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateUserMappingFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateUserMappingFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 46:
        raise CreateUserMappingFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreateUserMappingFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "CreateUserMappingFactorLoopError",
    "CreateUserMappingGrammarAction",
    "CreateUserMappingFactorObligation",
    "CreateUserMappingFactorCase",
    "CreateUserMappingFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_create_user_mapping_factor_loop_obligations",
    "build_create_user_mapping_factor_loop_plan",
    "_obligation_multiset_sha256",
    "_BASELINE_DEFAULTS",
]
