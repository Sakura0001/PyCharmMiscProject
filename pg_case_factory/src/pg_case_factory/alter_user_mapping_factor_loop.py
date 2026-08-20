"""Factor-value-loop obligation ledger for PostgreSQL 18.4 ALTER USER MAPPING.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``ALTER USER MAPPING``.  ALTER USER MAPPING is a PostgreSQL foreign-data
DDL statement with a single official synopsis branch: ``ALTER USER MAPPING
FOR { user_name | USER | CURRENT_ROLE | CURRENT_USER | SESSION_USER | PUBLIC }
SERVER server_name OPTIONS ( [ ADD | SET | DROP ] option ['value'] [, ... ] )``.
The statement modifies a ``pg_catalog.pg_user_mapping`` catalog row (not a
``pg_class`` relation), so column/table/relation coverage is
``not_applicable`` and there is no ``INV`` block.

Each local obligation becomes exactly one regress program.  The statement
is transactional (it runs inside a transaction block) and the inventory
declares no ``transaction_outcome`` factor, so there are no ``RISK``
obligations.

The grammar ledger is self-contained: the single synopsis action is frozen
inline.  The 54 canonical ``SFV`` rows are loaded from the shipped
applicability universe (``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class AlterUserMappingFactorLoopError(ValueError):
    """Raised when a frozen ALTER USER MAPPING obligation input drifts."""


@dataclass(frozen=True)
class AlterUserMappingGrammarAction:
    """One official target action form of the ALTER USER MAPPING synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class AlterUserMappingFactorObligation:
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
class AlterUserMappingFactorCase:
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
class AlterUserMappingFactorLoopPlan:
    obligations: tuple[AlterUserMappingFactorObligation, ...]
    cases: tuple[AlterUserMappingFactorCase, ...]
    delegated: tuple[AlterUserMappingFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-alterusermapping.html).
_BRANCH_OPTIONS = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-alterusermapping"

# The single target action for the OPTIONS modification branch.
_REPRESENTATIVE_ACTION = "options"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_OPTIONS: "options",
}

# Canonical factor -> the action where the value is observable.  Because
# ALTER USER MAPPING has a single branch, every factor consumes "options".
_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "user_specification": _REPRESENTATIVE_ACTION,
    "option_action": _REPRESENTATIVE_ACTION,
    "option_clause": _REPRESENTATIVE_ACTION,
    "mapping_existence": _REPRESENTATIVE_ACTION,
    "user_name_shape": _REPRESENTATIVE_ACTION,
    "server_name_shape": _REPRESENTATIVE_ACTION,
    "option_name_shape": _REPRESENTATIVE_ACTION,
    "option_value_shape": _REPRESENTATIVE_ACTION,
    "privilege_level": _REPRESENTATIVE_ACTION,
    "server_dependency": _REPRESENTATIVE_ACTION,
    "nonexistent_mapping": _REPRESENTATIVE_ACTION,
    "nonexistent_server": _REPRESENTATIVE_ACTION,
    "insufficient_privilege": _REPRESENTATIVE_ACTION,
    "invalid_option": _REPRESENTATIVE_ACTION,
    "duplicate_option_name": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates - DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        # Cluster A: target user mapping does not exist.
        ("expected_status", "failure"),
        ("object_state", "not_exists"),
        ("mapping_existence", "mapping_not_exists"),
        ("nonexistent_mapping", "mapping_missing"),
        ("user_name_shape", "nonexistent_name"),
        # Cluster B: referenced foreign server does not exist.
        ("nonexistent_server", "server_missing"),
        ("server_dependency", "server_missing"),
        ("server_name_shape", "nonexistent_name"),
        # Cluster C: insufficient privilege.
        ("privilege_level", "non_privileged"),
        ("insufficient_privilege", "lacks_privilege"),
        # Cluster D: invalid option (FDW validation).
        ("invalid_option", "invalid_option_name"),
        ("invalid_option", "invalid_option_value"),
        ("option_name_shape", "invalid_option"),
        # Cluster E: duplicate option name.
        ("duplicate_option_name", "duplicate_option"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    # Cluster A: user mapping does not exist.
    ("expected_status", "failure"): (
        "42704",
        "user_mapping_does_not_exist_provisional",
    ),
    ("object_state", "not_exists"): (
        "42704",
        "user_mapping_does_not_exist_provisional",
    ),
    ("mapping_existence", "mapping_not_exists"): (
        "42704",
        "user_mapping_does_not_exist_provisional",
    ),
    ("nonexistent_mapping", "mapping_missing"): (
        "42704",
        "user_mapping_does_not_exist_provisional",
    ),
    ("user_name_shape", "nonexistent_name"): (
        "42704",
        "user_mapping_does_not_exist_provisional",
    ),
    # Cluster B: foreign server does not exist.
    ("nonexistent_server", "server_missing"): (
        "42704",
        "foreign_server_does_not_exist_provisional",
    ),
    ("server_dependency", "server_missing"): (
        "42704",
        "foreign_server_does_not_exist_provisional",
    ),
    ("server_name_shape", "nonexistent_name"): (
        "42704",
        "foreign_server_does_not_exist_provisional",
    ),
    # Cluster C: insufficient privilege.
    ("privilege_level", "non_privileged"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("insufficient_privilege", "lacks_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    # Cluster D: invalid option (FDW validation).
    ("invalid_option", "invalid_option_name"): (
        "42704",
        "invalid_option_name_provisional",
    ),
    ("invalid_option", "invalid_option_value"): (
        "22023",
        "invalid_option_value_provisional",
    ),
    ("option_name_shape", "invalid_option"): (
        "42704",
        "invalid_option_name_provisional",
    ),
    # Cluster E: duplicate option name.
    ("duplicate_option_name", "duplicate_option"): (
        "42710",
        "duplicate_option_provisional",
    ),
}


def _load_grammar_actions() -> (
    tuple[AlterUserMappingGrammarAction, ...]
):
    """Freeze every ALTER USER MAPPING synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "options",
            _BRANCH_OPTIONS,
            (
                "ALTER USER MAPPING FOR "
                "{ user_name | USER | CURRENT_ROLE | CURRENT_USER | "
                "SESSION_USER | PUBLIC } SERVER server_name "
                "OPTIONS ( [ ADD | SET | DROP ] option ['value'] [, ... ] )"
            ),
            "synopsis-options",
        ),
    )
    actions = [
        AlterUserMappingGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise AlterUserMappingFactorLoopError(
            "alter user mapping action count drift"
        )
    return tuple(actions)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterUserMappingFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise AlterUserMappingFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> (
    list[AlterUserMappingFactorObligation]
):
    rows: list[AlterUserMappingFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            AlterUserMappingFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"AUM-GRM|{action.grammar_branch_id}|"
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
        raise AlterUserMappingFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[AlterUserMappingFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("alter_user_mapping")
    if len(catalog_rows) != 54:
        raise AlterUserMappingFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[AlterUserMappingFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            AlterUserMappingFactorObligation(
                ordinal=0,
                obligation_id=f"AUM-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[AlterUserMappingFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"alter-user-mapping-factor-obligations-v1\n"
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
    "options": _BRANCH_OPTIONS,
}

# Dense baseline defaults (all positive factor values).  statement_branch /
# target_action / grammar_branch are overridden per obligation.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_OPTIONS,
    "grammar_branch": _BRANCH_OPTIONS,
    "target_action": "options",
    "object_state": "exists",
    "expected_status": "success",
    "user_specification": "named_user",
    "option_action": "add",
    "option_clause": "single_option_add",
    "mapping_existence": "mapping_exists",
    "user_name_shape": "simple_id",
    "server_name_shape": "simple_id",
    "option_name_shape": "valid_option",
    "option_value_shape": "valid_value",
    "privilege_level": "server_owner",
    "server_dependency": "server_exists_and_valid",
    "nonexistent_mapping": "mapping_exists",
    "nonexistent_server": "server_exists",
    "insufficient_privilege": "has_privilege",
    "invalid_option": "valid_option_and_value",
    "duplicate_option_name": "unique_options",
    "verification_mode": "catalog_query_pg_user_mapping",
    "cleanup_mode": "revert_option",
}


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values.

    The T5 boundary factors describe the same scenario as their T1-T4
    counterparts.  When the primary factor is a T1-T4 value, the
    corresponding T5 value is derived; when the primary is a T5 value, the
    T1-T4 counterpart is derived.  This keeps the baseline assignment
    self-consistent so the render produces SQL that reaches the intended
    boundary.
    """

    os_ = a.get("object_state", "exists")
    me = a.get("mapping_existence", "mapping_exists")
    nm = a.get("nonexistent_mapping", "mapping_exists")
    uns = a.get("user_name_shape", "simple_id")

    sd = a.get("server_dependency", "server_exists_and_valid")
    sns = a.get("server_name_shape", "simple_id")
    ns = a.get("nonexistent_server", "server_exists")

    pl = a.get("privilege_level", "server_owner")
    ip = a.get("insufficient_privilege", "has_privilege")

    ion = a.get("invalid_option", "valid_option_and_value")
    ons = a.get("option_name_shape", "valid_option")

    don = a.get("duplicate_option_name", "unique_options")

    # Cluster A: mapping does not exist.  object_state / mapping_existence /
    # nonexistent_mapping / user_name_shape=nonexistent_name.
    if (
        os_ == "not_exists"
        or me == "mapping_not_exists"
        or nm == "mapping_missing"
        or uns == "nonexistent_name"
    ):
        a["object_state"] = "not_exists"
        a["mapping_existence"] = "mapping_not_exists"
        a["nonexistent_mapping"] = "mapping_missing"
        if uns not in ("public_keyword",):
            a["user_name_shape"] = "nonexistent_name"
    else:
        a["object_state"] = "exists"
        a["mapping_existence"] = "mapping_exists"
        a["nonexistent_mapping"] = "mapping_exists"

    # Cluster B: foreign server does not exist.  server_dependency /
    # nonexistent_server / server_name_shape=nonexistent_name.
    if (
        sd == "server_missing"
        or ns == "server_missing"
        or sns == "nonexistent_name"
    ):
        a["server_dependency"] = "server_missing"
        a["nonexistent_server"] = "server_missing"
        a["server_name_shape"] = "nonexistent_name"
    else:
        a["server_dependency"] = "server_exists_and_valid"
        a["nonexistent_server"] = "server_exists"
        a["server_name_shape"] = "simple_id"

    # Cluster C: insufficient privilege.  privilege_level /
    # insufficient_privilege.
    if pl == "non_privileged" or ip == "lacks_privilege":
        a["privilege_level"] = "non_privileged"
        a["insufficient_privilege"] = "lacks_privilege"
    else:
        a["privilege_level"] = pl
        a["insufficient_privilege"] = "has_privilege"

    # Cluster D: invalid option.  invalid_option / option_name_shape.
    if ion in ("invalid_option_name", "invalid_option_value") or ons == "invalid_option":
        a["option_name_shape"] = "invalid_option"
        a["invalid_option"] = "invalid_option_name"
    else:
        a["option_name_shape"] = "valid_option"
        a["invalid_option"] = "valid_option_and_value"

    # Cluster E: duplicate option name.
    if don == "duplicate_option":
        a["duplicate_option_name"] = "duplicate_option"
    else:
        a["duplicate_option_name"] = "unique_options"

    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: AlterUserMappingFactorObligation,
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
        raise AlterUserMappingFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: AlterUserMappingFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise AlterUserMappingFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_alter_user_mapping_factor_loop_plan(
    repository_root: Path,
) -> AlterUserMappingFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_alter_user_mapping_factor_loop_obligations(root)
    cases: list[AlterUserMappingFactorCase] = []
    delegated: list[AlterUserMappingFactorObligation] = []
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
            AlterUserMappingFactorCase(
                ordinal=ordinal,
                case_id=f"ALTERUSERMAPPING{ordinal:05d}",
                sql_filename=f"ALTERUSERMAPPING{ordinal:05d}.sql",
                object_prefix=(
                    f"alterusermapping_{ordinal:05d}_"
                ),
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
    plan = AlterUserMappingFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 55 or len(plan.delegated) != 0:
        raise AlterUserMappingFactorLoopError(
            "factor loop plan count drift"
        )
    if len({row.primary_obligation_id for row in plan.cases}) != 55:
        raise AlterUserMappingFactorLoopError(
            "local obligation mapping drift"
        )
    if len({row.sql_filename for row in plan.cases}) != 55:
        raise AlterUserMappingFactorLoopError("duplicate SQL filename")
    return plan


def compile_alter_user_mapping_factor_loop_obligations(
    repository_root: Path,
) -> tuple[AlterUserMappingFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        AlterUserMappingFactorObligation(
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
    if len(rows) != 55:
        raise AlterUserMappingFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise AlterUserMappingFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 54}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise AlterUserMappingFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise AlterUserMappingFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 55:
        raise AlterUserMappingFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise AlterUserMappingFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "AlterUserMappingFactorLoopError",
    "AlterUserMappingGrammarAction",
    "AlterUserMappingFactorObligation",
    "AlterUserMappingFactorCase",
    "AlterUserMappingFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_alter_user_mapping_factor_loop_obligations",
    "build_alter_user_mapping_factor_loop_plan",
    "_obligation_multiset_sha256",
]
