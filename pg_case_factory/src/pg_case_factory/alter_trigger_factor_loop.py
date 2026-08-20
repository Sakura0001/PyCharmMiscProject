"""Factor-value-loop obligation ledger for PostgreSQL 18.4 ALTER TRIGGER.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``ALTER TRIGGER``.  ALTER TRIGGER is a PostgreSQL DDL statement with
2 official synopsis branches: RENAME TO and [ NO ] DEPENDS ON EXTENSION.
The statement targets a trigger on a table and requires ownership of the
table.

Each local obligation becomes exactly one regress program.  Because
ALTER TRIGGER is table-dependent (it targets a trigger ON a table), the
render creates tables, trigger functions, and triggers; the bookend gate
(DROP TABLE IF EXISTS) applies.

The grammar ledger is self-contained (there is no separate
``alter_trigger_regress`` module): the 2 synopsis actions are frozen
inline.  The 41 canonical ``SFV`` rows are loaded from the shipped
applicability universe (``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class AlterTriggerFactorLoopError(ValueError):
    """Raised when a frozen ALTER TRIGGER obligation input drifts."""


@dataclass(frozen=True)
class AlterTriggerGrammarAction:
    """One official target action form of the ALTER TRIGGER synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class AlterTriggerFactorObligation:
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
class AlterTriggerFactorCase:
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
class AlterTriggerFactorLoopPlan:
    obligations: tuple[AlterTriggerFactorObligation, ...]
    cases: tuple[AlterTriggerFactorCase, ...]
    delegated: tuple[AlterTriggerFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-altertrigger.html).
_BRANCH_RENAME = "branch_1"
_BRANCH_DEPENDS_ON_EXTENSION = "branch_2"

_DOC_SOURCE = "postgresql-18.4-doc:sql-altertrigger"

# A representative branch_rename action used as the baseline consumer for
# canonical factors that are not bound to one specific branch.  RENAME TO
# is simple, ownership-only, and needs no extension.
_REPRESENTATIVE_ACTION = "rename"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_RENAME: "rename",
    _BRANCH_DEPENDS_ON_EXTENSION: "depends_on_extension",
}

# Canonical factor -> the action where the value is observable.  Factors
# whose consumer depends on the value (statement_branch) are resolved in
# :func:`_canonical_consumer`.
_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "rename_target": "rename",
    "extension_target": "depends_on_extension",
    "partitioned_table_effect": _REPRESENTATIVE_ACTION,
    "trigger_name_shape": _REPRESENTATIVE_ACTION,
    "table_name_shape": _REPRESENTATIVE_ACTION,
    "new_name_shape": "rename",
    "privilege_level": _REPRESENTATIVE_ACTION,
    "extension_dependency": "depends_on_extension",
    "table_dependency": _REPRESENTATIVE_ACTION,
    "target_trigger_not_exists": _REPRESENTATIVE_ACTION,
    "permission_insufficient": _REPRESENTATIVE_ACTION,
    "target_extension_not_exists": "depends_on_extension",
    "identifier_length_exceeded": "rename",
    "trigger_name_duplicate": "rename",
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "not_exists"),
        ("table_dependency", "table_not_exists"),
        ("privilege_level", "non_owner_no_privilege"),
        ("extension_target", "extension_not_exists"),
        ("rename_target", "duplicate_name"),
        ("trigger_name_shape", "schema_qualified"),
        ("target_trigger_not_exists", "trigger_not_found"),
        ("permission_insufficient", "not_table_owner"),
        ("target_extension_not_exists", "extension_name_not_found"),
        ("identifier_length_exceeded", "over_63_chars"),
        ("trigger_name_duplicate", "same_table_same_name"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "trigger_does_not_exist_provisional",
    ),
    ("object_state", "not_exists"): (
        "42704",
        "trigger_does_not_exist_provisional",
    ),
    ("table_dependency", "table_not_exists"): (
        "42P01",
        "undefined_table_provisional",
    ),
    ("privilege_level", "non_owner_no_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("extension_target", "extension_not_exists"): (
        "42704",
        "extension_does_not_exist_provisional",
    ),
    ("rename_target", "duplicate_name"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("trigger_name_shape", "schema_qualified"): (
        "42704",
        "trigger_does_not_exist_provisional",
    ),
    ("target_trigger_not_exists", "trigger_not_found"): (
        "42704",
        "trigger_does_not_exist_provisional",
    ),
    ("permission_insufficient", "not_table_owner"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("target_extension_not_exists", "extension_name_not_found"): (
        "42704",
        "extension_does_not_exist_provisional",
    ),
    ("identifier_length_exceeded", "over_63_chars"): (
        "42622",
        "name_too_long_provisional",
    ),
    ("trigger_name_duplicate", "same_table_same_name"): (
        "42710",
        "duplicate_object_provisional",
    ),
}


def _load_grammar_actions() -> (
    tuple[AlterTriggerGrammarAction, ...]
):
    """Freeze every ALTER TRIGGER synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "rename",
            _BRANCH_RENAME,
            "ALTER TRIGGER name ON table_name RENAME TO new_name",
            "synopsis-rename",
        ),
        (
            "depends_on_extension",
            _BRANCH_DEPENDS_ON_EXTENSION,
            (
                "ALTER TRIGGER name ON table_name "
                "[ NO ] DEPENDS ON EXTENSION extension_name"
            ),
            "synopsis-depends-on-extension",
        ),
    )
    actions = [
        AlterTriggerGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 2:
        raise AlterTriggerFactorLoopError(
            "alter trigger action count drift"
        )
    return tuple(actions)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterTriggerFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise AlterTriggerFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> (
    list[AlterTriggerFactorObligation]
):
    rows: list[AlterTriggerFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            AlterTriggerFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"ATRG-GRM|{action.grammar_branch_id}|"
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
    if len(rows) != 2:
        raise AlterTriggerFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[AlterTriggerFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("alter_trigger")
    if len(catalog_rows) != 41:
        raise AlterTriggerFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[AlterTriggerFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            AlterTriggerFactorObligation(
                ordinal=0,
                obligation_id=f"ATRG-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[AlterTriggerFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"alter-trigger-factor-obligations-v1\n"
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
    "depends_on_extension": _BRANCH_DEPENDS_ON_EXTENSION,
}

# Dense baseline defaults (all positive T1-T4 + T6 factor values).  The T5
# single-value factors (target_trigger_not_exists, permission_insufficient,
# target_extension_not_exists, identifier_length_exceeded,
# trigger_name_duplicate) are NOT baselined here: every declared value is
# a failure mode, so they are set only when they are the primary (or
# derived in the extension).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_RENAME,
    "grammar_branch": _BRANCH_RENAME,
    "target_action": "rename",
    "object_state": "exists",
    "expected_status": "success",
    "rename_target": "simple",
    "extension_target": "extension_exists",
    "partitioned_table_effect": "regular_table",
    "trigger_name_shape": "simple",
    "table_name_shape": "simple",
    "new_name_shape": "simple",
    "privilege_level": "superuser",
    "extension_dependency": "extension_installed",
    "table_dependency": "table_exists",
    "verification_mode": "pg_trigger_catalog_query",
    "cleanup_mode": "DROP_TRIGGER",
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

    os = a.get("object_state", "exists")
    ttn = a.get("target_trigger_not_exists", "")
    td = a.get("table_dependency", "table_exists")
    pl = a.get("privilege_level", "superuser")
    pi = a.get("permission_insufficient", "")
    et = a.get("extension_target", "extension_exists")
    ten = a.get("target_extension_not_exists", "")
    rt = a.get("rename_target", "simple")
    tnd = a.get("trigger_name_duplicate", "")
    ile = a.get("identifier_length_exceeded", "")

    # trigger-not-exists cluster: object_state / target_trigger_not_exists
    if os == "not_exists" or ttn == "trigger_not_found":
        a["object_state"] = "not_exists"
        a["target_trigger_not_exists"] = "trigger_not_found"

    # table-not-exists cluster: table_dependency
    if td == "table_not_exists":
        a["table_dependency"] = "table_not_exists"

    # non-owner cluster: privilege_level / permission_insufficient
    if pl == "non_owner_no_privilege" or pi == "not_table_owner":
        a["privilege_level"] = "non_owner_no_privilege"
        a["permission_insufficient"] = "not_table_owner"

    # extension-not-exists cluster: extension_target /
    # target_extension_not_exists
    if et == "extension_not_exists" or ten == "extension_name_not_found":
        a["extension_target"] = "extension_not_exists"
        a["target_extension_not_exists"] = "extension_name_not_found"

    # duplicate-name cluster: rename_target / trigger_name_duplicate
    if rt == "duplicate_name" or tnd == "same_table_same_name":
        a["rename_target"] = "duplicate_name"
        a["trigger_name_duplicate"] = "same_table_same_name"

    # identifier-length-exceeded is standalone
    if ile == "over_63_chars":
        a["identifier_length_exceeded"] = "over_63_chars"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: AlterTriggerFactorObligation,
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
        raise AlterTriggerFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: AlterTriggerFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise AlterTriggerFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_alter_trigger_factor_loop_plan(
    repository_root: Path,
) -> AlterTriggerFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_alter_trigger_factor_loop_obligations(root)
    cases: list[AlterTriggerFactorCase] = []
    delegated: list[AlterTriggerFactorObligation] = []
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
            AlterTriggerFactorCase(
                ordinal=ordinal,
                case_id=f"ALTERTRIGGER{ordinal:05d}",
                sql_filename=f"ALTERTRIGGER{ordinal:05d}.sql",
                object_prefix=f"altertrigger_{ordinal:05d}_",
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
    plan = AlterTriggerFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 43 or len(plan.delegated) != 0:
        raise AlterTriggerFactorLoopError(
            "factor loop plan count drift"
        )
    if len({row.primary_obligation_id for row in plan.cases}) != 43:
        raise AlterTriggerFactorLoopError(
            "local obligation mapping drift"
        )
    if len({row.sql_filename for row in plan.cases}) != 43:
        raise AlterTriggerFactorLoopError("duplicate SQL filename")
    return plan


def compile_alter_trigger_factor_loop_obligations(
    repository_root: Path,
) -> tuple[AlterTriggerFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        AlterTriggerFactorObligation(
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
    if len(rows) != 43:
        raise AlterTriggerFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise AlterTriggerFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 2, "SFV": 41}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise AlterTriggerFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise AlterTriggerFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 43:
        raise AlterTriggerFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise AlterTriggerFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "AlterTriggerFactorLoopError",
    "AlterTriggerGrammarAction",
    "AlterTriggerFactorObligation",
    "AlterTriggerFactorCase",
    "AlterTriggerFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_alter_trigger_factor_loop_obligations",
    "build_alter_trigger_factor_loop_plan",
    "_obligation_multiset_sha256",
]
