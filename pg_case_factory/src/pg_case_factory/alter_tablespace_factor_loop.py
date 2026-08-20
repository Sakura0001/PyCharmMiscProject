"""Factor-value-loop obligation ledger for PostgreSQL 18.4 ALTER TABLESPACE.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``ALTER TABLESPACE``.  ALTER TABLESPACE is a PostgreSQL DDL statement with
4 official synopsis branches: RENAME TO, OWNER TO, SET (option), and RESET
(option).  The statement manages a tablespace storage object (a
``pg_catalog.pg_tablespace`` catalog row, not a ``pg_class`` relation), so
column/table/relation coverage is ``not_applicable`` and there is no
``INV`` block.

Each local obligation becomes exactly one regress program.  Because the
inventory declares no ``transaction_outcome`` factor, there are no ``RISK``
obligations.

The grammar ledger is self-contained (there is no separate
``alter_tablespace_regress`` module): the 4 synopsis actions are frozen
inline.  The 68 canonical ``SFV`` rows are loaded from the shipped
applicability universe (``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class AlterTablespaceFactorLoopError(ValueError):
    """Raised when a frozen ALTER TABLESPACE obligation input drifts."""


@dataclass(frozen=True)
class AlterTablespaceGrammarAction:
    """One official target action form of the ALTER TABLESPACE synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class AlterTablespaceFactorObligation:
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
class AlterTablespaceFactorCase:
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
class AlterTablespaceFactorLoopPlan:
    obligations: tuple[AlterTablespaceFactorObligation, ...]
    cases: tuple[AlterTablespaceFactorCase, ...]
    delegated: tuple[AlterTablespaceFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-altertablespace.html).
_BRANCH_RENAME = "branch_rename"
_BRANCH_OWNER = "branch_owner"
_BRANCH_SET = "branch_set"
_BRANCH_RESET = "branch_reset"

_DOC_SOURCE = "postgresql-18.4-doc:sql-altertablespace"

# A representative branch_rename action used as the baseline consumer for
# canonical factors that are not bound to one specific branch.  RENAME TO
# is simple and needs no role fixture.
_REPRESENTATIVE_ACTION = "rename"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_RENAME: "rename",
    _BRANCH_OWNER: "owner",
    _BRANCH_SET: "set",
    _BRANCH_RESET: "reset",
}

# alter_action value -> target action (value-dependent consumer).
_ALTER_ACTION_CONSUMER = {
    "rename": "rename",
    "owner": "owner",
    "set": "set",
    "reset": "reset",
}

# Canonical factor -> the action where the value is observable.  Factors
# whose consumer depends on the value (statement_branch, alter_action)
# are resolved in :func:`_canonical_consumer`.
_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "alter_action": _REPRESENTATIVE_ACTION,
    "owner_target": "owner",
    "tablespace_option": "set",
    "tablespace_name_shape": _REPRESENTATIVE_ACTION,
    "new_name_shape": "rename",
    "owner_name_shape": "owner",
    "option_name_shape": "set",
    "privilege_level": _REPRESENTATIVE_ACTION,
    "role_existence": "owner",
    "set_role_capability": "owner",
    "nonexistent_tablespace": _REPRESENTATIVE_ACTION,
    "pg_reserved_new_name": "rename",
    "duplicate_new_name": "rename",
    "non_owner_attempt": _REPRESENTATIVE_ACTION,
    "cannot_set_role": "owner",
    "nonexistent_owner_role": "owner",
    "invalid_option_name": "set",
    "invalid_option_value": "set",
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates -- DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "not_exists"),
        ("tablespace_name_shape", "nonexistent_name"),
        ("tablespace_name_shape", "invalid_name"),
        ("new_name_shape", "pg_prefix_reserved"),
        ("new_name_shape", "duplicate_name"),
        ("new_name_shape", "invalid_name"),
        ("owner_name_shape", "nonexistent_role"),
        ("option_name_shape", "invalid_option_name"),
        ("privilege_level", "non_owner"),
        ("role_existence", "role_not_exists"),
        ("set_role_capability", "cannot_set_role"),
        ("nonexistent_tablespace", "tablespace_missing"),
        ("pg_reserved_new_name", "pg_prefix_name"),
        ("duplicate_new_name", "same_name_conflict"),
        ("non_owner_attempt", "non_owner_execution"),
        ("cannot_set_role", "cannot_set_role_to_target"),
        ("nonexistent_owner_role", "role_missing"),
        ("invalid_option_name", "unrecognized_option"),
        ("invalid_option_value", "invalid_value"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "tablespace_does_not_exist_provisional",
    ),
    ("object_state", "not_exists"): (
        "42704",
        "tablespace_does_not_exist_provisional",
    ),
    ("tablespace_name_shape", "nonexistent_name"): (
        "42704",
        "tablespace_does_not_exist_provisional",
    ),
    ("tablespace_name_shape", "invalid_name"): (
        "42601",
        "syntax_error_provisional",
    ),
    ("new_name_shape", "pg_prefix_reserved"): (
        "42939",
        "reserved_name_provisional",
    ),
    ("new_name_shape", "duplicate_name"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("new_name_shape", "invalid_name"): (
        "42601",
        "syntax_error_provisional",
    ),
    ("owner_name_shape", "nonexistent_role"): (
        "42704",
        "role_does_not_exist_provisional",
    ),
    ("option_name_shape", "invalid_option_name"): (
        "42704",
        "unrecognized_parameter_provisional",
    ),
    ("privilege_level", "non_owner"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("role_existence", "role_not_exists"): (
        "42704",
        "role_does_not_exist_provisional",
    ),
    ("set_role_capability", "cannot_set_role"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("nonexistent_tablespace", "tablespace_missing"): (
        "42704",
        "tablespace_does_not_exist_provisional",
    ),
    ("pg_reserved_new_name", "pg_prefix_name"): (
        "42939",
        "reserved_name_provisional",
    ),
    ("duplicate_new_name", "same_name_conflict"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("non_owner_attempt", "non_owner_execution"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("cannot_set_role", "cannot_set_role_to_target"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("nonexistent_owner_role", "role_missing"): (
        "42704",
        "role_does_not_exist_provisional",
    ),
    ("invalid_option_name", "unrecognized_option"): (
        "42704",
        "unrecognized_parameter_provisional",
    ),
    ("invalid_option_value", "invalid_value"): (
        "22023",
        "invalid_parameter_value_provisional",
    ),
}


def _load_grammar_actions() -> (
    tuple[AlterTablespaceGrammarAction, ...]
):
    """Freeze every ALTER TABLESPACE synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "rename",
            _BRANCH_RENAME,
            "ALTER TABLESPACE name RENAME TO new_name",
            "synopsis-rename",
        ),
        (
            "owner",
            _BRANCH_OWNER,
            (
                "ALTER TABLESPACE name OWNER TO "
                "{ new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }"
            ),
            "synopsis-owner-to",
        ),
        (
            "set",
            _BRANCH_SET,
            (
                "ALTER TABLESPACE name SET "
                "( tablespace_option = value [, ...] )"
            ),
            "synopsis-set",
        ),
        (
            "reset",
            _BRANCH_RESET,
            "ALTER TABLESPACE name RESET ( tablespace_option [, ...] )",
            "synopsis-reset",
        ),
    )
    actions = [
        AlterTablespaceGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 4:
        raise AlterTablespaceFactorLoopError(
            "alter tablespace action count drift"
        )
    return tuple(actions)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterTablespaceFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "alter_action":
        try:
            return _ALTER_ACTION_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterTablespaceFactorLoopError(
                f"unknown alter_action value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise AlterTablespaceFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> (
    list[AlterTablespaceFactorObligation]
):
    rows: list[AlterTablespaceFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            AlterTablespaceFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"ATSP-GRM|{action.grammar_branch_id}|"
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
    if len(rows) != 4:
        raise AlterTablespaceFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[AlterTablespaceFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("alter_tablespace")
    if len(catalog_rows) != 68:
        raise AlterTablespaceFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[AlterTablespaceFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            AlterTablespaceFactorObligation(
                ordinal=0,
                obligation_id=f"ATSP-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[AlterTablespaceFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"alter-tablespace-factor-obligations-v1\n"
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
    "rename": _BRANCH_RENAME,
    "owner": _BRANCH_OWNER,
    "set": _BRANCH_SET,
    "reset": _BRANCH_RESET,
}

# Dense baseline defaults (all positive T1-T4 + T6 factor values).  The T5
# single-value factors (nonexistent_tablespace, pg_reserved_new_name,
# duplicate_new_name, non_owner_attempt, cannot_set_role,
# nonexistent_owner_role, invalid_option_name, invalid_option_value) are
# NOT baselined here: every declared value is either a failure mode or a
# boundary, so they are set only when they are the primary (or derived in
# the extension).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_RENAME,
    "grammar_branch": _BRANCH_RENAME,
    "target_action": "rename",
    "object_state": "exists",
    "expected_status": "success",
    "alter_action": "rename",
    "owner_target": "specified_new_owner",
    "tablespace_option": "seq_page_cost",
    "tablespace_name_shape": "simple_id",
    "new_name_shape": "simple_id",
    "owner_name_shape": "simple_id",
    "option_name_shape": "valid_option",
    "privilege_level": "superuser",
    "role_existence": "role_exists",
    "set_role_capability": "can_set_role",
    "verification_mode": "catalog_query_pg_tablespace",
    "cleanup_mode": "revert_rename",
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

    os_ = a.get("object_state", "exists")
    tns = a.get("tablespace_name_shape", "simple_id")
    nts = a.get("nonexistent_tablespace", "")

    pl = a.get("privilege_level", "superuser")
    noa = a.get("non_owner_attempt", "")

    nns = a.get("new_name_shape", "simple_id")
    prn = a.get("pg_reserved_new_name", "")
    dnn = a.get("duplicate_new_name", "")

    re_ = a.get("role_existence", "role_exists")
    nor = a.get("nonexistent_owner_role", "")
    ons = a.get("owner_name_shape", "simple_id")

    src = a.get("set_role_capability", "can_set_role")
    csr = a.get("cannot_set_role", "")

    opns = a.get("option_name_shape", "valid_option")
    ion = a.get("invalid_option_name", "")

    # nonexistent tablespace cluster: object_state /
    # tablespace_name_shape / nonexistent_tablespace
    if (
        os_ == "not_exists"
        or tns == "nonexistent_name"
        or nts == "tablespace_missing"
    ):
        a["object_state"] = "not_exists"
        a["tablespace_name_shape"] = "nonexistent_name"
        a["nonexistent_tablespace"] = "tablespace_missing"

    # non-owner cluster: privilege_level / non_owner_attempt
    if pl == "non_owner" or noa == "non_owner_execution":
        a["privilege_level"] = "non_owner"
        a["non_owner_attempt"] = "non_owner_execution"

    # pg-prefix cluster: new_name_shape / pg_reserved_new_name
    if (
        nns == "pg_prefix_reserved"
        or prn == "pg_prefix_name"
    ):
        a["new_name_shape"] = "pg_prefix_reserved"
        a["pg_reserved_new_name"] = "pg_prefix_name"

    # duplicate-name cluster: new_name_shape / duplicate_new_name
    if (
        nns == "duplicate_name"
        or dnn == "same_name_conflict"
    ):
        a["new_name_shape"] = "duplicate_name"
        a["duplicate_new_name"] = "same_name_conflict"

    # nonexistent-owner-role cluster: role_existence /
    # nonexistent_owner_role / owner_name_shape
    if (
        re_ == "role_not_exists"
        or nor == "role_missing"
        or ons == "nonexistent_role"
    ):
        a["role_existence"] = "role_not_exists"
        a["nonexistent_owner_role"] = "role_missing"
        a["owner_name_shape"] = "nonexistent_role"

    # cannot-set-role cluster: set_role_capability / cannot_set_role
    if (
        src == "cannot_set_role"
        or csr == "cannot_set_role_to_target"
    ):
        a["set_role_capability"] = "cannot_set_role"
        a["cannot_set_role"] = "cannot_set_role_to_target"

    # invalid-option-name cluster: option_name_shape / invalid_option_name
    if (
        opns == "invalid_option_name"
        or ion == "unrecognized_option"
    ):
        a["option_name_shape"] = "invalid_option_name"
        a["invalid_option_name"] = "unrecognized_option"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: AlterTablespaceFactorObligation,
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
    assignments["alter_action"] = obligation.consumer_action_id
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    failures = _count_baseline_failures(assignments)
    assignments["expected_status"] = (
        "failure" if failures > 0 else "success"
    )
    if len(assignments) != len(set(assignments)):
        raise AlterTablespaceFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: AlterTablespaceFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise AlterTablespaceFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_alter_tablespace_factor_loop_plan(
    repository_root: Path,
) -> AlterTablespaceFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_alter_tablespace_factor_loop_obligations(root)
    cases: list[AlterTablespaceFactorCase] = []
    delegated: list[AlterTablespaceFactorObligation] = []
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
            AlterTablespaceFactorCase(
                ordinal=ordinal,
                case_id=f"ALTERTABLESPACE{ordinal:05d}",
                sql_filename=f"ALTERTABLESPACE{ordinal:05d}.sql",
                object_prefix=(
                    f"alter_tablespace_{ordinal:05d}_"
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
    plan = AlterTablespaceFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 72 or len(plan.delegated) != 0:
        raise AlterTablespaceFactorLoopError(
            "factor loop plan count drift"
        )
    if len({row.primary_obligation_id for row in plan.cases}) != 72:
        raise AlterTablespaceFactorLoopError(
            "local obligation mapping drift"
        )
    if len({row.sql_filename for row in plan.cases}) != 72:
        raise AlterTablespaceFactorLoopError("duplicate SQL filename")
    return plan


def compile_alter_tablespace_factor_loop_obligations(
    repository_root: Path,
) -> tuple[AlterTablespaceFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        AlterTablespaceFactorObligation(
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
    if len(rows) != 72:
        raise AlterTablespaceFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise AlterTablespaceFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 4, "SFV": 68}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise AlterTablespaceFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise AlterTablespaceFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 72:
        raise AlterTablespaceFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise AlterTablespaceFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "AlterTablespaceFactorLoopError",
    "AlterTablespaceGrammarAction",
    "AlterTablespaceFactorObligation",
    "AlterTablespaceFactorCase",
    "AlterTablespaceFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_alter_tablespace_factor_loop_obligations",
    "build_alter_tablespace_factor_loop_plan",
    "_obligation_multiset_sha256",
]
