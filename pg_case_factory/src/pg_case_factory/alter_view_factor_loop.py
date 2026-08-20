"""Factor-value-loop obligation ledger for PostgreSQL 18.4 ALTER VIEW.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``ALTER VIEW``.  ALTER VIEW is a PostgreSQL DDL statement with 8 official
synopsis branches: SET DEFAULT, DROP DEFAULT, OWNER TO, RENAME COLUMN,
RENAME TO, SET SCHEMA, SET (view_option), and RESET (view_option).  The
statement modifies an existing plain view relation (a ``pg_class`` row of
relkind ``v``); it does not create or transform base tables, so the
table-coverage scope is ``not_applicable`` and there is no ``INV`` block.

Each local obligation becomes exactly one regress program.  The 8 synopsis
actions are frozen inline as ``GRM`` obligations.  The 63 canonical ``SFV``
rows are loaded from the shipped applicability universe
(``postgresql_18_4_factor_audit.tsv``); they include the 8 ``statement_branch``
values, so every branch receives both a ``GRM`` and an ``SFV`` witness.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class AlterViewFactorLoopError(ValueError):
    """Raised when a frozen ALTER VIEW obligation input drifts."""


@dataclass(frozen=True)
class AlterViewGrammarAction:
    """One official target action form of the ALTER VIEW synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class AlterViewFactorObligation:
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
class AlterViewFactorCase:
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
class AlterViewFactorLoopPlan:
    obligations: tuple[AlterViewFactorObligation, ...]
    cases: tuple[AlterViewFactorCase, ...]
    delegated: tuple[AlterViewFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-alterview.html).
_BRANCH_SET_DEFAULT = "branch_set_default"
_BRANCH_DROP_DEFAULT = "branch_drop_default"
_BRANCH_OWNER_TO = "branch_owner_to"
_BRANCH_RENAME_COLUMN = "branch_rename_column"
_BRANCH_RENAME_VIEW = "branch_rename_view"
_BRANCH_SET_SCHEMA = "branch_set_schema"
_BRANCH_SET_OPTION = "branch_set_option"
_BRANCH_RESET_OPTION = "branch_reset_option"

_DOC_SOURCE = "postgresql-18.4-doc:sql-alterview"

# A representative branch action used as the baseline consumer for canonical
# factors that are not bound to one specific branch.  SET (view_option) is
# simple, ownership-neutral, and needs no extra fixtures beyond the view.
_REPRESENTATIVE_ACTION = "set_option"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_SET_DEFAULT: "set_default",
    _BRANCH_DROP_DEFAULT: "drop_default",
    _BRANCH_OWNER_TO: "owner_to",
    _BRANCH_RENAME_COLUMN: "rename_column",
    _BRANCH_RENAME_VIEW: "rename",
    _BRANCH_SET_SCHEMA: "set_schema",
    _BRANCH_SET_OPTION: "set_option",
    _BRANCH_RESET_OPTION: "reset_option",
}

# error_boundary canonical value -> the action where the boundary is
# observable.  non_existent_role needs OWNER TO; non_existent_schema needs
# SET SCHEMA; the rest are observable on the representative branch.
_ERROR_BOUNDARY_CONSUMER = {
    "none": "set_option",
    "view_not_exists_without_if_exists": "rename",
    "insufficient_privilege": "set_option",
    "non_existent_role": "owner_to",
    "non_existent_schema": "set_schema",
    "wrong_object_type": "rename",
}

# Canonical factor -> the action where the value is observable.  Factors
# whose consumer depends on the value (statement_branch, error_boundary)
# are resolved in :func:`_canonical_consumer`.
_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "if_exists_clause": _REPRESENTATIVE_ACTION,
    "view_name_shape": _REPRESENTATIVE_ACTION,
    "column_name_shape": "set_default",
    "new_name_shape": "rename",
    "new_schema_shape": "set_schema",
    "owner_target_shape": "owner_to",
    "view_option_shape": "set_option",
    "privilege_level": _REPRESENTATIVE_ACTION,
    "dependency_state": _REPRESENTATIVE_ACTION,
    "error_boundary": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("object_state", "not_exists"),
        ("view_name_shape", "non_existent"),
        ("error_boundary", "view_not_exists_without_if_exists"),
        ("expected_status", "failure"),
        ("privilege_level", "non_owner_no_privilege"),
        ("error_boundary", "insufficient_privilege"),
        ("owner_target_shape", "non_existent_role"),
        ("error_boundary", "non_existent_role"),
        ("new_schema_shape", "schema_not_exists"),
        ("error_boundary", "non_existent_schema"),
        ("new_schema_shape", "pg_catalog_reserved"),
        ("new_name_shape", "same_as_existing"),
        ("error_boundary", "wrong_object_type"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("object_state", "not_exists"): (
        "42704",
        "view_not_exists_without_if_exists",
    ),
    ("view_name_shape", "non_existent"): (
        "42704",
        "view_not_exists_without_if_exists",
    ),
    ("error_boundary", "view_not_exists_without_if_exists"): (
        "42704",
        "view_not_exists_without_if_exists",
    ),
    ("expected_status", "failure"): (
        "42704",
        "view_not_exists_without_if_exists",
    ),
    ("privilege_level", "non_owner_no_privilege"): (
        "42501",
        "insufficient_privilege",
    ),
    ("error_boundary", "insufficient_privilege"): (
        "42501",
        "insufficient_privilege",
    ),
    ("owner_target_shape", "non_existent_role"): (
        "42704",
        "non_existent_role",
    ),
    ("error_boundary", "non_existent_role"): (
        "42704",
        "non_existent_role",
    ),
    ("new_schema_shape", "schema_not_exists"): (
        "3F000",
        "non_existent_schema",
    ),
    ("error_boundary", "non_existent_schema"): (
        "3F000",
        "non_existent_schema",
    ),
    ("new_schema_shape", "pg_catalog_reserved"): (
        "42501",
        "non_existent_schema",
    ),
    ("new_name_shape", "same_as_existing"): (
        "42710",
        "duplicate_relation_name",
    ),
    ("error_boundary", "wrong_object_type"): (
        "42809",
        "wrong_object_type",
    ),
}


def _load_grammar_actions() -> tuple[AlterViewGrammarAction, ...]:
    """Freeze every ALTER VIEW synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "set_default",
            _BRANCH_SET_DEFAULT,
            (
                "ALTER VIEW [ IF EXISTS ] name ALTER [ COLUMN ] "
                "column_name SET DEFAULT expression"
            ),
            "synopsis-set-default",
        ),
        (
            "drop_default",
            _BRANCH_DROP_DEFAULT,
            (
                "ALTER VIEW [ IF EXISTS ] name ALTER [ COLUMN ] "
                "column_name DROP DEFAULT"
            ),
            "synopsis-drop-default",
        ),
        (
            "owner_to",
            _BRANCH_OWNER_TO,
            (
                "ALTER VIEW [ IF EXISTS ] name OWNER TO "
                "{ new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }"
            ),
            "synopsis-owner-to",
        ),
        (
            "rename_column",
            _BRANCH_RENAME_COLUMN,
            (
                "ALTER VIEW [ IF EXISTS ] name RENAME [ COLUMN ] "
                "column_name TO new_column_name"
            ),
            "synopsis-rename-column",
        ),
        (
            "rename",
            _BRANCH_RENAME_VIEW,
            "ALTER VIEW [ IF EXISTS ] name RENAME TO new_name",
            "synopsis-rename",
        ),
        (
            "set_schema",
            _BRANCH_SET_SCHEMA,
            "ALTER VIEW [ IF EXISTS ] name SET SCHEMA new_schema",
            "synopsis-set-schema",
        ),
        (
            "set_option",
            _BRANCH_SET_OPTION,
            (
                "ALTER VIEW [ IF EXISTS ] name SET "
                "( view_option_name [= view_option_value] [, ... ] )"
            ),
            "synopsis-set-option",
        ),
        (
            "reset_option",
            _BRANCH_RESET_OPTION,
            (
                "ALTER VIEW [ IF EXISTS ] name RESET "
                "( view_option_name [, ... ] )"
            ),
            "synopsis-reset-option",
        ),
    )
    actions = [
        AlterViewGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 8:
        raise AlterViewFactorLoopError("alter view action count drift")
    return tuple(actions)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterViewFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "error_boundary":
        try:
            return _ERROR_BOUNDARY_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterViewFactorLoopError(
                f"unknown error_boundary value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise AlterViewFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> list[AlterViewFactorObligation]:
    rows: list[AlterViewFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            AlterViewFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"AVIEW-GRM|{action.grammar_branch_id}|"
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
    if len(rows) != 8:
        raise AlterViewFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[AlterViewFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("alter_view")
    if len(catalog_rows) != 63:
        raise AlterViewFactorLoopError("canonical obligation count drift")
    rows: list[AlterViewFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            AlterViewFactorObligation(
                ordinal=0,
                obligation_id=f"AVIEW-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[AlterViewFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"alter-view-factor-obligations-v1\n")
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
    "set_default": _BRANCH_SET_DEFAULT,
    "drop_default": _BRANCH_DROP_DEFAULT,
    "owner_to": _BRANCH_OWNER_TO,
    "rename_column": _BRANCH_RENAME_COLUMN,
    "rename": _BRANCH_RENAME_VIEW,
    "set_schema": _BRANCH_SET_SCHEMA,
    "set_option": _BRANCH_SET_OPTION,
    "reset_option": _BRANCH_RESET_OPTION,
}

# Dense baseline defaults (all positive factor values).  The T5
# single-value error_boundary failures and the value-dependent factors are
# set only when they are the primary (or derived in the extension).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_SET_OPTION,
    "grammar_branch": _BRANCH_SET_OPTION,
    "target_action": "set_option",
    "object_state": "exists",
    "expected_status": "success",
    "if_exists_clause": "absent",
    "view_name_shape": "simple",
    "column_name_shape": "simple",
    "new_name_shape": "simple",
    "new_schema_shape": "schema_exists",
    "owner_target_shape": "role_name",
    "view_option_shape": "check_option_local",
    "privilege_level": "owner",
    "dependency_state": "base_table_exists",
    "error_boundary": "none",
    "verification_mode": "pg_class_query",
    "cleanup_mode": "drop_view_if_exists",
}


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values.

    The not-exists / privilege / role / schema clusters each describe the
    same scenario from two overlapping factor perspectives.  When the
    primary factor is one perspective, the other is derived so the baseline
    assignment stays self-consistent.
    """

    os_ = a.get("object_state", "exists")
    vns = a.get("view_name_shape", "simple")
    eb = a.get("error_boundary", "none")
    es = a.get("expected_status", "success")
    pl = a.get("privilege_level", "owner")
    ot = a.get("owner_target_shape", "role_name")
    nss = a.get("new_schema_shape", "schema_exists")

    # not-exists cluster: object_state / view_name_shape /
    # error_boundary=view_not_exists_without_if_exists / expected_status
    if (
        os_ == "not_exists"
        or vns == "non_existent"
        or eb == "view_not_exists_without_if_exists"
        or es == "failure"
    ):
        a["object_state"] = "not_exists"
        a["view_name_shape"] = "non_existent"
        a["error_boundary"] = "view_not_exists_without_if_exists"

    # non-owner cluster: privilege_level / error_boundary
    if pl == "non_owner_no_privilege" or eb == "insufficient_privilege":
        a["privilege_level"] = "non_owner_no_privilege"
        a["error_boundary"] = "insufficient_privilege"

    # non-existent-role cluster: owner_target_shape / error_boundary
    if ot == "non_existent_role" or eb == "non_existent_role":
        a["owner_target_shape"] = "non_existent_role"
        a["error_boundary"] = "non_existent_role"

    # non-existent-schema cluster: new_schema_shape / error_boundary
    if nss == "schema_not_exists" or eb == "non_existent_schema":
        a["new_schema_shape"] = "schema_not_exists"
        a["error_boundary"] = "non_existent_schema"

    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: AlterViewFactorObligation,
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
        raise AlterViewFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: AlterViewFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise AlterViewFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_alter_view_factor_loop_plan(
    repository_root: Path,
) -> AlterViewFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_alter_view_factor_loop_obligations(root)
    cases: list[AlterViewFactorCase] = []
    delegated: list[AlterViewFactorObligation] = []
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
            AlterViewFactorCase(
                ordinal=ordinal,
                case_id=f"ALTERVIEW{ordinal:05d}",
                sql_filename=f"ALTERVIEW{ordinal:05d}.sql",
                object_prefix=f"alterview_{ordinal:05d}_",
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
    plan = AlterViewFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 71 or len(plan.delegated) != 0:
        raise AlterViewFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 71:
        raise AlterViewFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 71:
        raise AlterViewFactorLoopError("duplicate SQL filename")
    return plan


def compile_alter_view_factor_loop_obligations(
    repository_root: Path,
) -> tuple[AlterViewFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        AlterViewFactorObligation(
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
    if len(rows) != 71:
        raise AlterViewFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise AlterViewFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 8, "SFV": 63}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise AlterViewFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise AlterViewFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 71:
        raise AlterViewFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise AlterViewFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "AlterViewFactorLoopError",
    "AlterViewGrammarAction",
    "AlterViewFactorObligation",
    "AlterViewFactorCase",
    "AlterViewFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_alter_view_factor_loop_obligations",
    "build_alter_view_factor_loop_plan",
    "_obligation_multiset_sha256",
]
