"""Factor-value-loop obligation ledger for PostgreSQL 18.4 ALTER TEXT SEARCH DICTIONARY.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``ALTER TEXT SEARCH DICTIONARY``.  ALTER TEXT SEARCH DICTIONARY is a
PostgreSQL full-text-search DDL statement with 4 official synopsis
branches: option modify (``name ( option [ = value ] [, ... ] )``),
RENAME TO, OWNER TO, and SET SCHEMA.  The statement requires owner
privilege on the dictionary and touches the ``pg_catalog.pg_ts_dict``
catalog row (not a ``pg_class`` relation), so column/table/relation
coverage is ``not_applicable`` and there is no ``INV`` block.

Each local obligation becomes exactly one regress program.  Because the
inventory declares no ``transaction_outcome`` factor, there are no
``RISK`` obligations.

The grammar ledger is self-contained (there is no separate
``alter_text_search_dictionary_regress`` module): the 4 synopsis actions
are frozen inline.  The 60 canonical ``SFV`` rows are loaded from the
shipped applicability universe (``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class AlterTextSearchDictionaryFactorLoopError(ValueError):
    """Raised when a frozen ALTER TEXT SEARCH DICTIONARY obligation input drifts."""


@dataclass(frozen=True)
class AlterTextSearchDictionaryGrammarAction:
    """One official target action form of the ALTER TEXT SEARCH DICTIONARY synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class AlterTextSearchDictionaryFactorObligation:
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
class AlterTextSearchDictionaryFactorCase:
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
class AlterTextSearchDictionaryFactorLoopPlan:
    obligations: tuple[AlterTextSearchDictionaryFactorObligation, ...]
    cases: tuple[AlterTextSearchDictionaryFactorCase, ...]
    delegated: tuple[AlterTextSearchDictionaryFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-altertsdictionary.html).
_BRANCH_OPTION = "branch_option"
_BRANCH_RENAME = "branch_rename"
_BRANCH_OWNER = "branch_owner"
_BRANCH_SET_SCHEMA = "branch_set_schema"

_DOC_SOURCE = "postgresql-18.4-doc:sql-altertsdictionary"

# A representative branch_option action used as the baseline consumer for
# canonical factors that are not bound to one specific branch.  The option
# form is the simplest branch: it needs no rename target, owner role, or
# destination schema.
_REPRESENTATIVE_ACTION = "option_modify"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_OPTION: "option_modify",
    _BRANCH_RENAME: "rename",
    _BRANCH_OWNER: "owner",
    _BRANCH_SET_SCHEMA: "set_schema",
}

# alter_action value -> target action (value-dependent consumer).
_ALTER_ACTION_CONSUMER = {
    "option_modify": "option_modify",
    "rename": "rename",
    "owner": "owner",
    "set_schema": "set_schema",
}

# Canonical factor -> the action where the value is observable.  Factors
# whose consumer depends on the value (statement_branch, alter_action)
# are resolved in :func:`_canonical_consumer`.
_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "alter_action": _REPRESENTATIVE_ACTION,
    "option_action": "option_modify",
    "owner_target": "owner",
    "dict_name_shape": _REPRESENTATIVE_ACTION,
    "new_name_shape": "rename",
    "owner_name_shape": "owner",
    "schema_name_shape": "set_schema",
    "privilege_level": _REPRESENTATIVE_ACTION,
    "role_existence": "owner",
    "set_role_capability": "owner",
    "schema_existence": "set_schema",
    "nonexistent_dict": _REPRESENTATIVE_ACTION,
    "duplicate_new_name": "rename",
    "nonexistent_owner_role": "owner",
    "nonexistent_target_schema": "set_schema",
    "non_owner_attempt": _REPRESENTATIVE_ACTION,
    "cannot_set_role": "owner",
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "not_exists"),
        ("dict_name_shape", "nonexistent_name"),
        ("nonexistent_dict", "dict_missing"),
        ("privilege_level", "non_owner"),
        ("non_owner_attempt", "non_owner_execution"),
        ("new_name_shape", "duplicate_name"),
        ("duplicate_new_name", "same_name_conflict"),
        ("owner_name_shape", "nonexistent_role"),
        ("role_existence", "role_not_exists"),
        ("nonexistent_owner_role", "role_missing"),
        ("schema_name_shape", "nonexistent_schema"),
        ("schema_existence", "schema_not_exists"),
        ("nonexistent_target_schema", "schema_missing"),
        ("set_role_capability", "cannot_set_role"),
        ("cannot_set_role", "cannot_set_role_to_target"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "undefined_object_provisional",
    ),
    ("object_state", "not_exists"): (
        "42704",
        "undefined_object_provisional",
    ),
    ("dict_name_shape", "nonexistent_name"): (
        "42704",
        "undefined_object_provisional",
    ),
    ("nonexistent_dict", "dict_missing"): (
        "42704",
        "undefined_object_provisional",
    ),
    ("privilege_level", "non_owner"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("non_owner_attempt", "non_owner_execution"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("new_name_shape", "duplicate_name"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("duplicate_new_name", "same_name_conflict"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("owner_name_shape", "nonexistent_role"): (
        "42704",
        "undefined_object_provisional",
    ),
    ("role_existence", "role_not_exists"): (
        "42704",
        "undefined_object_provisional",
    ),
    ("nonexistent_owner_role", "role_missing"): (
        "42704",
        "undefined_object_provisional",
    ),
    ("schema_name_shape", "nonexistent_schema"): (
        "3F000",
        "invalid_schema_name_provisional",
    ),
    ("schema_existence", "schema_not_exists"): (
        "3F000",
        "invalid_schema_name_provisional",
    ),
    ("nonexistent_target_schema", "schema_missing"): (
        "3F000",
        "invalid_schema_name_provisional",
    ),
    ("set_role_capability", "cannot_set_role"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("cannot_set_role", "cannot_set_role_to_target"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
}


def _load_grammar_actions() -> (
    tuple[AlterTextSearchDictionaryGrammarAction, ...]
):
    """Freeze every ALTER TEXT SEARCH DICTIONARY synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "option_modify",
            _BRANCH_OPTION,
            "ALTER TEXT SEARCH DICTIONARY name ( option [ = value ] [, ... ] )",
            "synopsis-option",
        ),
        (
            "rename",
            _BRANCH_RENAME,
            "ALTER TEXT SEARCH DICTIONARY name RENAME TO new_name",
            "synopsis-rename",
        ),
        (
            "owner",
            _BRANCH_OWNER,
            (
                "ALTER TEXT SEARCH DICTIONARY name OWNER TO "
                "{ new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }"
            ),
            "synopsis-owner",
        ),
        (
            "set_schema",
            _BRANCH_SET_SCHEMA,
            "ALTER TEXT SEARCH DICTIONARY name SET SCHEMA new_schema",
            "synopsis-set-schema",
        ),
    )
    actions = [
        AlterTextSearchDictionaryGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 4:
        raise AlterTextSearchDictionaryFactorLoopError(
            "alter text search dictionary action count drift"
        )
    return tuple(actions)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterTextSearchDictionaryFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "alter_action":
        try:
            return _ALTER_ACTION_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterTextSearchDictionaryFactorLoopError(
                f"unknown alter_action value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise AlterTextSearchDictionaryFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> (
    list[AlterTextSearchDictionaryFactorObligation]
):
    rows: list[AlterTextSearchDictionaryFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            AlterTextSearchDictionaryFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"ATSD-GRM|{action.grammar_branch_id}|"
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
        raise AlterTextSearchDictionaryFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[AlterTextSearchDictionaryFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("alter_text_search_dictionary")
    if len(catalog_rows) != 60:
        raise AlterTextSearchDictionaryFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[AlterTextSearchDictionaryFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            AlterTextSearchDictionaryFactorObligation(
                ordinal=0,
                obligation_id=f"ATSD-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[AlterTextSearchDictionaryFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"alter-text-search-dictionary-factor-obligations-v1\n"
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
    "option_modify": _BRANCH_OPTION,
    "rename": _BRANCH_RENAME,
    "owner": _BRANCH_OWNER,
    "set_schema": _BRANCH_SET_SCHEMA,
}

# Dense baseline defaults (all positive T1-T4 + T6 factor values).  The T5
# single-value factors (nonexistent_dict, duplicate_new_name,
# nonexistent_owner_role, nonexistent_target_schema, non_owner_attempt,
# cannot_set_role) are NOT baselined here: every declared value is either
# a failure mode or a branch-specific boundary, so they are set only when
# they are the primary (or derived in the extension).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_OPTION,
    "grammar_branch": _BRANCH_OPTION,
    "target_action": "option_modify",
    "object_state": "exists",
    "expected_status": "success",
    "alter_action": "option_modify",
    "option_action": "set_new_value",
    "owner_target": "specified_new_owner",
    "dict_name_shape": "simple_id",
    "new_name_shape": "simple_id",
    "owner_name_shape": "simple_id",
    "schema_name_shape": "simple_id",
    "privilege_level": "owner",
    "role_existence": "role_exists",
    "set_role_capability": "can_set_role",
    "schema_existence": "schema_exists",
    "nonexistent_dict": "dict_exists",
    "duplicate_new_name": "no_conflict",
    "nonexistent_owner_role": "role_exists",
    "nonexistent_target_schema": "schema_exists",
    "non_owner_attempt": "owner_execution",
    "cannot_set_role": "can_set_role",
    "verification_mode": "catalog_query_pg_ts_dict",
    "cleanup_mode": "revert_option",
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
    dns = a.get("dict_name_shape", "simple_id")
    nd = a.get("nonexistent_dict", "")
    pl = a.get("privilege_level", "owner")
    noa = a.get("non_owner_attempt", "")
    nns = a.get("new_name_shape", "simple_id")
    dnn = a.get("duplicate_new_name", "")
    ons = a.get("owner_name_shape", "simple_id")
    re_ = a.get("role_existence", "role_exists")
    nor = a.get("nonexistent_owner_role", "")
    sns = a.get("schema_name_shape", "simple_id")
    se = a.get("schema_existence", "schema_exists")
    nts = a.get("nonexistent_target_schema", "")
    src = a.get("set_role_capability", "can_set_role")
    csr = a.get("cannot_set_role", "")

    # dict-missing cluster: object_state / dict_name_shape /
    # nonexistent_dict
    if (
        os_ == "not_exists"
        or dns == "nonexistent_name"
        or nd == "dict_missing"
    ):
        a["object_state"] = "not_exists"
        a["dict_name_shape"] = "nonexistent_name"
        a["nonexistent_dict"] = "dict_missing"

    # non-owner cluster: privilege_level / non_owner_attempt
    if pl == "non_owner" or noa == "non_owner_execution":
        a["privilege_level"] = "non_owner"
        a["non_owner_attempt"] = "non_owner_execution"

    # rename-conflict cluster: new_name_shape / duplicate_new_name
    if (
        nns == "duplicate_name"
        or dnn == "same_name_conflict"
    ):
        a["new_name_shape"] = "duplicate_name"
        a["duplicate_new_name"] = "same_name_conflict"

    # owner-role-missing cluster: owner_name_shape / role_existence /
    # nonexistent_owner_role
    if (
        ons == "nonexistent_role"
        or re_ == "role_not_exists"
        or nor == "role_missing"
    ):
        a["owner_name_shape"] = "nonexistent_role"
        a["role_existence"] = "role_not_exists"
        a["nonexistent_owner_role"] = "role_missing"

    # target-schema-missing cluster: schema_name_shape /
    # schema_existence / nonexistent_target_schema
    if (
        sns == "nonexistent_schema"
        or se == "schema_not_exists"
        or nts == "schema_missing"
    ):
        a["schema_name_shape"] = "nonexistent_schema"
        a["schema_existence"] = "schema_not_exists"
        a["nonexistent_target_schema"] = "schema_missing"

    # cannot-set-role cluster: set_role_capability / cannot_set_role
    if (
        src == "cannot_set_role"
        or csr == "cannot_set_role_to_target"
    ):
        a["set_role_capability"] = "cannot_set_role"
        a["cannot_set_role"] = "cannot_set_role_to_target"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: AlterTextSearchDictionaryFactorObligation,
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
        raise AlterTextSearchDictionaryFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: AlterTextSearchDictionaryFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise AlterTextSearchDictionaryFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_alter_text_search_dictionary_factor_loop_plan(
    repository_root: Path,
) -> AlterTextSearchDictionaryFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_alter_text_search_dictionary_factor_loop_obligations(root)
    cases: list[AlterTextSearchDictionaryFactorCase] = []
    delegated: list[AlterTextSearchDictionaryFactorObligation] = []
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
            AlterTextSearchDictionaryFactorCase(
                ordinal=ordinal,
                case_id=f"ALTERTEXTSEARCHDICTIONARY{ordinal:05d}",
                sql_filename=f"ALTERTEXTSEARCHDICTIONARY{ordinal:05d}.sql",
                object_prefix=(
                    f"alter_text_search_dictionary_{ordinal:05d}_"
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
    plan = AlterTextSearchDictionaryFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 64 or len(plan.delegated) != 0:
        raise AlterTextSearchDictionaryFactorLoopError(
            "factor loop plan count drift"
        )
    if len({row.primary_obligation_id for row in plan.cases}) != 64:
        raise AlterTextSearchDictionaryFactorLoopError(
            "local obligation mapping drift"
        )
    if len({row.sql_filename for row in plan.cases}) != 64:
        raise AlterTextSearchDictionaryFactorLoopError("duplicate SQL filename")
    return plan


def compile_alter_text_search_dictionary_factor_loop_obligations(
    repository_root: Path,
) -> tuple[AlterTextSearchDictionaryFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        AlterTextSearchDictionaryFactorObligation(
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
    if len(rows) != 64:
        raise AlterTextSearchDictionaryFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise AlterTextSearchDictionaryFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 4, "SFV": 60}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise AlterTextSearchDictionaryFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise AlterTextSearchDictionaryFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 64:
        raise AlterTextSearchDictionaryFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise AlterTextSearchDictionaryFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "AlterTextSearchDictionaryFactorLoopError",
    "AlterTextSearchDictionaryGrammarAction",
    "AlterTextSearchDictionaryFactorObligation",
    "AlterTextSearchDictionaryFactorCase",
    "AlterTextSearchDictionaryFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_alter_text_search_dictionary_factor_loop_obligations",
    "build_alter_text_search_dictionary_factor_loop_plan",
    "_obligation_multiset_sha256",
]
