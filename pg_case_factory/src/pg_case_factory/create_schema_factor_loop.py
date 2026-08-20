"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE SCHEMA.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE SCHEMA``.  CREATE SCHEMA is a PostgreSQL namespace-management
DDL statement with four official synopsis branches: a named schema
(``CREATE SCHEMA name [AUTHORIZATION ...] [schema_element ...]``), an
owner-named schema (``CREATE SCHEMA AUTHORIZATION role [element ...]``),
an idempotent named schema (``CREATE SCHEMA IF NOT EXISTS name
[AUTHORIZATION ...]``), and an idempotent owner-named schema
(``CREATE SCHEMA IF NOT EXISTS AUTHORIZATION role``).  The statement
operates on the ``pg_catalog.pg_namespace`` catalog row (not a
``pg_class`` relation), so column/table/relation coverage is
``not_applicable`` and there is no ``INV`` block.

Each local obligation becomes exactly one regress program.  The
grammar ledger is self-contained: the four synopsis forms are frozen
inline.  The 58 canonical ``SFV`` rows are loaded from the shipped
applicability universe (``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CreateSchemaFactorLoopError(ValueError):
    """Raised when a frozen CREATE SCHEMA obligation input drifts."""


@dataclass(frozen=True)
class CreateSchemaGrammarAction:
    """One official target action form of the CREATE SCHEMA synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateSchemaFactorObligation:
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
class CreateSchemaFactorCase:
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
class CreateSchemaFactorLoopPlan:
    obligations: tuple[CreateSchemaFactorObligation, ...]
    cases: tuple[CreateSchemaFactorCase, ...]
    delegated: tuple[CreateSchemaFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-createschema.html).
_BRANCH_NAMED = "branch_named_schema"
_BRANCH_AUTH = "branch_auth_schema"
_BRANCH_INE_NAMED = "branch_if_not_exists_named"
_BRANCH_INE_AUTH = "branch_if_not_exists_auth"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createschema"

# A representative branch_named_schema action used as the baseline
# consumer for canonical factors that are not bound to one specific
# branch.  The named schema form is the simplest success path.
_REPRESENTATIVE_ACTION = "create_named_schema"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_NAMED: "create_named_schema",
    _BRANCH_AUTH: "create_auth_schema",
    _BRANCH_INE_NAMED: "create_if_not_exists_named",
    _BRANCH_INE_AUTH: "create_if_not_exists_auth",
}

# Branch action -> grammar branch id used by the renderer.
_ACTION_BRANCH = {
    "create_named_schema": _BRANCH_NAMED,
    "create_auth_schema": _BRANCH_AUTH,
    "create_if_not_exists_named": _BRANCH_INE_NAMED,
    "create_if_not_exists_auth": _BRANCH_INE_AUTH,
}

# Canonical factor -> the action where the value is observable.
# statement_branch is resolved in :func:`_canonical_consumer`.
_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "if_not_exists_clause": _REPRESENTATIVE_ACTION,
    "authorization_clause": _REPRESENTATIVE_ACTION,
    "schema_element_inclusion": _REPRESENTATIVE_ACTION,
    "role_specification_form": _REPRESENTATIVE_ACTION,
    "schema_name_shape": _REPRESENTATIVE_ACTION,
    "owner_name_shape": _REPRESENTATIVE_ACTION,
    "privilege_level": _REPRESENTATIVE_ACTION,
    "database_privilege": _REPRESENTATIVE_ACTION,
    "role_dependency": _REPRESENTATIVE_ACTION,
    "schema_element_dependency": _REPRESENTATIVE_ACTION,
    "duplicate_schema_name": _REPRESENTATIVE_ACTION,
    "pg_prefix_name": _REPRESENTATIVE_ACTION,
    "insufficient_privilege": _REPRESENTATIVE_ACTION,
    "if_not_exists_with_elements": _REPRESENTATIVE_ACTION,
    "forward_reference_in_elements": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target
# check and are rejected (provisional sqlstates; DB phase verifies).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "already_exists"),
        ("schema_name_shape", "pg_prefix_reserved"),
        ("owner_name_shape", "non_existing_role"),
        ("privilege_level", "non_creator_no_privilege"),
        ("database_privilege", "no_CREATE_privilege"),
        ("role_dependency", "role_not_exists"),
        ("role_dependency", "cannot_SET_ROLE"),
        ("duplicate_schema_name", "without_IF_NOT_EXISTS_error"),
        ("pg_prefix_name", "pg_prefix_schema_name"),
        ("insufficient_privilege", "no_CREATE_on_database"),
        ("insufficient_privilege", "cannot_SET_ROLE_to_owner"),
        ("if_not_exists_with_elements", "if_not_exists_with_schema_elements"),
        ("forward_reference_in_elements", "forward_reference_failure"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42710",
        "create_schema_failure_provisional",
    ),
    ("object_state", "already_exists"): (
        "42710",
        "duplicate_schema_provisional",
    ),
    ("schema_name_shape", "pg_prefix_reserved"): (
        "42939",
        "pg_prefix_reserved_schema_name_provisional",
    ),
    ("owner_name_shape", "non_existing_role"): (
        "42704",
        "undefined_role_provisional",
    ),
    ("privilege_level", "non_creator_no_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("database_privilege", "no_CREATE_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("role_dependency", "role_not_exists"): (
        "42704",
        "undefined_role_provisional",
    ),
    ("role_dependency", "cannot_SET_ROLE"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("duplicate_schema_name", "without_IF_NOT_EXISTS_error"): (
        "42710",
        "duplicate_schema_provisional",
    ),
    ("pg_prefix_name", "pg_prefix_schema_name"): (
        "42939",
        "pg_prefix_reserved_schema_name_provisional",
    ),
    ("insufficient_privilege", "no_CREATE_on_database"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("insufficient_privilege", "cannot_SET_ROLE_to_owner"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("if_not_exists_with_elements", "if_not_exists_with_schema_elements"): (
        "42601",
        "if_not_exists_with_elements_provisional",
    ),
    ("forward_reference_in_elements", "forward_reference_failure"): (
        "42P01",
        "forward_reference_provisional",
    ),
}


def _load_grammar_actions() -> tuple[CreateSchemaGrammarAction, ...]:
    """Freeze every CREATE SCHEMA synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "create_named_schema",
            _BRANCH_NAMED,
            "CREATE SCHEMA schema_name [AUTHORIZATION role] [schema_element ...]",
            "synopsis-named-schema",
        ),
        (
            "create_auth_schema",
            _BRANCH_AUTH,
            "CREATE SCHEMA AUTHORIZATION role [schema_element ...]",
            "synopsis-auth-schema",
        ),
        (
            "create_if_not_exists_named",
            _BRANCH_INE_NAMED,
            "CREATE SCHEMA IF NOT EXISTS schema_name [AUTHORIZATION role]",
            "synopsis-if-not-exists-named",
        ),
        (
            "create_if_not_exists_auth",
            _BRANCH_INE_AUTH,
            "CREATE SCHEMA IF NOT EXISTS AUTHORIZATION role",
            "synopsis-if-not-exists-auth",
        ),
    )
    actions = [
        CreateSchemaGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 4:
        raise CreateSchemaFactorLoopError("create schema action count drift")
    return tuple(actions)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise CreateSchemaFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise CreateSchemaFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> list[CreateSchemaFactorObligation]:
    rows: list[CreateSchemaFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateSchemaFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CSCHEMA-GRM|{action.grammar_branch_id}|"
                    f"{action.action_id}|target_action|{action.action_id}"
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
        raise CreateSchemaFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateSchemaFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_schema")
    if len(catalog_rows) != 58:
        raise CreateSchemaFactorLoopError("canonical obligation count drift")
    rows: list[CreateSchemaFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateSchemaFactorObligation(
                ordinal=0,
                obligation_id=f"CSCHEMA-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreateSchemaFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"create-schema-factor-obligations-v1\n")
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
                    "delegated_statement_key": row.delegated_statement_key,
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        digest.update(b"\n")
    return digest.hexdigest()


# Dense baseline defaults (all positive T1-T4 + T6 factor values).  The
# T5 single-value factors are derived in :func:`_derive_overlapping_factors`
# only when their failure cluster is active, so success cases omit them.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_NAMED,
    "grammar_branch": _BRANCH_NAMED,
    "target_action": "create_named_schema",
    "object_state": "not_exists",
    "expected_status": "success",
    "if_not_exists_clause": "absent",
    "authorization_clause": "absent",
    "schema_element_inclusion": "without_elements",
    "role_specification_form": "user_name",
    "schema_name_shape": "simple",
    "owner_name_shape": "existing_role",
    "privilege_level": "superuser",
    "database_privilege": "has_CREATE_privilege",
    "role_dependency": "role_exists",
    "schema_element_dependency": "element_table_exists",
    "verification_mode": "pg_namespace_catalog_query",
    "cleanup_mode": "DROP_SCHEMA_IF_EXISTS",
}


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1 for pair in _SFV_FAILURE_VALUES if a.get(pair[0]) == pair[1]
    )


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive overlapping T5 boundary factors from T1-T4 values.

    Each cluster only sets its T5 factors when active, mirroring the
    alter_subscription ledger so success cases stay free of failure
    values and attribution stays at most one.
    """

    # pg_prefix reserved-name cluster: schema_name_shape / pg_prefix_name
    sns = a.get("schema_name_shape", "simple")
    pgp = a.get("pg_prefix_name", "")
    if sns == "pg_prefix_reserved" or pgp == "pg_prefix_schema_name":
        a["schema_name_shape"] = "pg_prefix_reserved"
        a["pg_prefix_name"] = "pg_prefix_schema_name"

    # duplicate-name cluster: object_state / duplicate_schema_name.
    # already_exists + IF NOT EXISTS present -> no-op success; absent ->
    # duplicate error.  The IF NOT EXISTS coupling is reconciled below.
    os_state = a.get("object_state", "not_exists")
    dsn = a.get("duplicate_schema_name", "")
    ine = a.get("if_not_exists_clause", "absent")
    if dsn == "without_IF_NOT_EXISTS_error" or (
        os_state == "already_exists" and ine == "absent"
    ):
        a["object_state"] = "already_exists"
        a["duplicate_schema_name"] = "without_IF_NOT_EXISTS_error"
        a["if_not_exists_clause"] = "absent"
    elif dsn == "with_IF_NOT_EXISTS_noop" or (
        os_state == "already_exists" and ine == "present"
    ):
        a["object_state"] = "already_exists"
        a["duplicate_schema_name"] = "with_IF_NOT_EXISTS_noop"
        a["if_not_exists_clause"] = "present"

    # no-CREATE-privilege cluster: privilege_level / database_privilege /
    # insufficient_privilege
    pl = a.get("privilege_level", "superuser")
    dp = a.get("database_privilege", "has_CREATE_privilege")
    ip = a.get("insufficient_privilege", "")
    if (
        pl == "non_creator_no_privilege"
        or dp == "no_CREATE_privilege"
        or ip == "no_CREATE_on_database"
    ):
        a["privilege_level"] = "non_creator_no_privilege"
        a["database_privilege"] = "no_CREATE_privilege"
        a["insufficient_privilege"] = "no_CREATE_on_database"

    # cannot-SET-ROLE cluster: role_dependency / insufficient_privilege
    rd = a.get("role_dependency", "role_exists")
    ip2 = a.get("insufficient_privilege", "")
    if rd == "cannot_SET_ROLE" or ip2 == "cannot_SET_ROLE_to_owner":
        a["role_dependency"] = "cannot_SET_ROLE"
        a["insufficient_privilege"] = "cannot_SET_ROLE_to_owner"

    # non-existing-role cluster: owner_name_shape / role_dependency
    ons = a.get("owner_name_shape", "existing_role")
    rd2 = a.get("role_dependency", "role_exists")
    if ons == "non_existing_role" or rd2 == "role_not_exists":
        a["owner_name_shape"] = "non_existing_role"
        a["role_dependency"] = "role_not_exists"

    # IF NOT EXISTS with schema elements: a standalone syntax-error
    # boundary.  Forces an IF NOT EXISTS branch plus a CREATE TABLE
    # element so the render emits the rejected combination.
    ifne = a.get("if_not_exists_with_elements", "")
    if ifne == "if_not_exists_with_schema_elements":
        a["if_not_exists_clause"] = "present"
        a["schema_element_inclusion"] = "with_create_table"

    # forward-reference cluster: schema_element_dependency /
    # forward_reference_in_elements.  A view sub-command referencing a
    # not-yet-created table is rejected by PostgreSQL.
    fre = a.get("forward_reference_in_elements", "")
    sed = a.get("schema_element_dependency", "element_table_exists")
    if fre == "forward_reference_failure" or sed == "element_table_not_exists":
        a["forward_reference_in_elements"] = "forward_reference_failure"
        a["schema_element_dependency"] = "element_table_not_exists"
        a["schema_element_inclusion"] = "with_create_view"


# Reverse lookup for branch -> action (used by _reconcile_branch).
_BRANCH_ACTION_REV = {v: k for k, v in _ACTION_BRANCH.items()}


def _reconcile_branch(a: dict[str, str]) -> None:
    """Keep statement_branch consistent with if_not_exists_clause.

    The synopsis form is selected by the primary factor: when
    statement_branch is the primary the if_not_exists_clause is derived,
    and when if_not_exists_clause is the primary the branch is derived.
    The named/auth distinction is preserved from the primary branch.
    """

    sb = a.get("statement_branch", _BRANCH_NAMED)
    ine = a.get("if_not_exists_clause", "absent")
    use_auth = sb in {_BRANCH_AUTH, _BRANCH_INE_AUTH}
    if "if_not_exists" in sb:
        a["if_not_exists_clause"] = "present"
    elif ine == "present":
        a["statement_branch"] = (
            _BRANCH_INE_AUTH if use_auth else _BRANCH_INE_NAMED
        )
        a["grammar_branch"] = a["statement_branch"]
        a["target_action"] = _BRANCH_ACTION_REV[a["statement_branch"]]
    # Drop schema elements when an IF NOT EXISTS branch is in effect but
    # the if_not_exists_with_elements failure is not the active scenario.
    if (
        "if_not_exists" in a.get("statement_branch", _BRANCH_NAMED)
        and a.get("if_not_exists_with_elements", "")
        != "if_not_exists_with_schema_elements"
        and a.get("schema_element_inclusion", "without_elements")
        != "without_elements"
    ):
        a["schema_element_inclusion"] = "without_elements"


def _baseline_assignments(
    obligation: CreateSchemaFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    branch = _ACTION_BRANCH.get(
        obligation.consumer_action_id, _BRANCH_NAMED
    )
    assignments["grammar_branch"] = branch
    assignments["target_action"] = obligation.consumer_action_id
    assignments["statement_branch"] = branch
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    _reconcile_branch(assignments)
    failures = _count_baseline_failures(assignments)
    assignments["expected_status"] = "failure" if failures > 0 else "success"
    if len(assignments) != len(set(assignments)):
        raise CreateSchemaFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateSchemaFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateSchemaFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_schema_factor_loop_plan(
    repository_root: Path,
) -> CreateSchemaFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_schema_factor_loop_obligations(root)
    cases: list[CreateSchemaFactorCase] = []
    delegated: list[CreateSchemaFactorObligation] = []
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
            CreateSchemaFactorCase(
                ordinal=ordinal,
                case_id=f"CREATESCHEMA{ordinal:05d}",
                sql_filename=f"CREATESCHEMA{ordinal:05d}.sql",
                object_prefix=f"createschema_{ordinal:05d}_",
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
    plan = CreateSchemaFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 62 or len(plan.delegated) != 0:
        raise CreateSchemaFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 62:
        raise CreateSchemaFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 62:
        raise CreateSchemaFactorLoopError("duplicate SQL filename")
    return plan


def compile_create_schema_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateSchemaFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations() + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateSchemaFactorObligation(
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
    if len(rows) != 62:
        raise CreateSchemaFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateSchemaFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 4, "SFV": 58}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateSchemaFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateSchemaFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"} for row in rows
    ) != 62:
        raise CreateSchemaFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(row.disposition not in allowed_dispositions for row in rows):
        raise CreateSchemaFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "CreateSchemaFactorLoopError",
    "CreateSchemaGrammarAction",
    "CreateSchemaFactorObligation",
    "CreateSchemaFactorCase",
    "CreateSchemaFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "_BASELINE_DEFAULTS",
    "compile_create_schema_factor_loop_obligations",
    "build_create_schema_factor_loop_plan",
    "_obligation_multiset_sha256",
]
