"""Factor-value-loop obligation ledger for PostgreSQL 18.4 ALTER TYPE.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``ALTER TYPE``.  ALTER TYPE is a PostgreSQL DDL statement with ten
official synopsis branches: OWNER TO, RENAME TO, SET SCHEMA, RENAME
ATTRIBUTE, composite attribute actions (ADD/DROP/ALTER ATTRIBUTE), ADD
VALUE, RENAME VALUE, and SET property.  The statement modifies a
``pg_catalog.pg_type`` row (and, for composite types, the linked
``pg_class``/``pg_attribute`` rows); it is not a relation-targeting
statement, so there is no ``INV`` block.

Each local obligation becomes exactly one regress program.  The grammar
ledger is self-contained (the ten synopsis actions are frozen inline).
The 84 canonical ``SFV`` rows are loaded from the shipped applicability
universe (``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class AlterTypeFactorLoopError(ValueError):
    """Raised when a frozen ALTER TYPE obligation input drifts."""


@dataclass(frozen=True)
class AlterTypeGrammarAction:
    """One official target action form of the ALTER TYPE synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class AlterTypeFactorObligation:
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
class AlterTypeFactorCase:
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
class AlterTypeFactorLoopPlan:
    obligations: tuple[AlterTypeFactorObligation, ...]
    cases: tuple[AlterTypeFactorCase, ...]
    delegated: tuple[AlterTypeFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-altertype.html).
_BRANCH_OWNER = "branch_owner"
_BRANCH_RENAME = "branch_rename"
_BRANCH_SET_SCHEMA = "branch_set_schema"
_BRANCH_RENAME_ATTRIBUTE = "branch_rename_attribute"
_BRANCH_ADD_ATTRIBUTE = "branch_add_attribute"
_BRANCH_DROP_ATTRIBUTE = "branch_drop_attribute"
_BRANCH_ALTER_ATTRIBUTE_TYPE = "branch_alter_attribute_type"
_BRANCH_ADD_VALUE = "branch_add_value"
_BRANCH_RENAME_VALUE = "branch_rename_value"
_BRANCH_SET_PROPERTY = "branch_set_property"

_DOC_SOURCE = "postgresql-18.4-doc:sql-altertype"

# A representative branch used as the baseline consumer for canonical
# factors that are not bound to one specific branch.  RENAME TO is
# simple, ownership-neutral, and works for every type category.
_REPRESENTATIVE_ACTION = "rename"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_OWNER: "owner_to",
    _BRANCH_RENAME: "rename",
    _BRANCH_SET_SCHEMA: "set_schema",
    _BRANCH_RENAME_ATTRIBUTE: "rename_attribute",
    _BRANCH_ADD_ATTRIBUTE: "add_attribute",
    _BRANCH_DROP_ATTRIBUTE: "drop_attribute",
    _BRANCH_ALTER_ATTRIBUTE_TYPE: "alter_attribute_type",
    _BRANCH_ADD_VALUE: "add_value",
    _BRANCH_RENAME_VALUE: "rename_value",
    _BRANCH_SET_PROPERTY: "set_property",
}

# insufficient_privilege value -> target action (value-dependent consumer).
_INSUFFICIENT_PRIVILEGE_CONSUMER = {
    "non_owner": "rename",
    "non_superuser_set_property": "set_property",
    "no_USAGE_on_attribute_type": "add_attribute",
}

# Canonical factor -> the action where the value is observable.  Factors
# whose consumer depends on the value (statement_branch,
# insufficient_privilege) are resolved in :func:`_canonical_consumer`.
_SFV_FACTOR_CONSUMER = {
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "type_category": _REPRESENTATIVE_ACTION,
    "cascade_restrict": "add_attribute",
    "if_exists_clause": "drop_attribute",
    "if_not_exists_clause": "add_value",
    "enum_position_clause": "add_value",
    "role_specification": "owner_to",
    "type_name_shape": _REPRESENTATIVE_ACTION,
    "attribute_name_shape": "rename_attribute",
    "new_attribute_type": "alter_attribute_type",
    "new_enum_value_shape": "add_value",
    "privilege_level": _REPRESENTATIVE_ACTION,
    "typed_table_dependency": "add_attribute",
    "attribute_usage_privilege": "add_attribute",
    "owner_change_privilege": "owner_to",
    "schema_privilege": "set_schema",
    "new_owner_schema_privilege": "owner_to",
    "enum_transaction_state": "add_value",
    "non_existent_type": _REPRESENTATIVE_ACTION,
    "non_existent_attribute": "drop_attribute",
    "cascade_with_typed_tables": "add_attribute",
    "restrict_with_typed_tables": "add_attribute",
    "enum_value_conflict": "add_value",
    "storage_plain_to_other_requires_superuser": "set_property",
    "storage_other_to_plain_never_allowed": "set_property",
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "not_exists"),
        ("non_existent_type", "target_not_exists"),
        ("non_existent_attribute", "attribute_not_exists_no_if_exists"),
        ("attribute_usage_privilege", "no_USAGE"),
        ("owner_change_privilege", "cannot_SET_ROLE"),
        ("schema_privilege", "no_CREATE"),
        ("new_owner_schema_privilege", "no_CREATE"),
        ("enum_value_conflict", "value_exists_no_if_not_exists"),
        ("insufficient_privilege", "non_owner"),
        ("insufficient_privilege", "non_superuser_set_property"),
        ("insufficient_privilege", "no_USAGE_on_attribute_type"),
        ("restrict_with_typed_tables", "restrict_refuses_typed_tables"),
        ("storage_other_to_plain_never_allowed", "other_to_plain_never_allowed"),
        ("privilege_level", "non_owner"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "target_type_does_not_exist_provisional",
    ),
    ("object_state", "not_exists"): (
        "42704",
        "target_type_does_not_exist",
    ),
    ("non_existent_type", "target_not_exists"): (
        "42704",
        "target_type_does_not_exist",
    ),
    ("non_existent_attribute", "attribute_not_exists_no_if_exists"): (
        "42704",
        "composite_attribute_does_not_exist",
    ),
    ("attribute_usage_privilege", "no_USAGE"): (
        "42501",
        "attribute_type_usage_privilege_missing",
    ),
    ("owner_change_privilege", "cannot_SET_ROLE"): (
        "42501",
        "owner_change_cannot_set_role",
    ),
    ("schema_privilege", "no_CREATE"): (
        "42501",
        "target_schema_create_privilege_missing",
    ),
    ("new_owner_schema_privilege", "no_CREATE"): (
        "42501",
        "new_owner_schema_create_privilege_missing",
    ),
    ("enum_value_conflict", "value_exists_no_if_not_exists"): (
        "42710",
        "enum_value_already_exists",
    ),
    ("insufficient_privilege", "non_owner"): (
        "42501",
        "alter_type_requires_type_owner",
    ),
    ("insufficient_privilege", "non_superuser_set_property"): (
        "42501",
        "alter_type_set_property_requires_superuser",
    ),
    ("insufficient_privilege", "no_USAGE_on_attribute_type"): (
        "42501",
        "attribute_type_usage_privilege_missing",
    ),
    ("restrict_with_typed_tables", "restrict_refuses_typed_tables"): (
        "2BP01",
        "restrict_refuses_typed_table_dependency",
    ),
    ("storage_other_to_plain_never_allowed", "other_to_plain_never_allowed"): (
        "55000",
        "storage_cannot_be_changed_back_to_plain",
    ),
    ("privilege_level", "non_owner"): (
        "42501",
        "alter_type_requires_type_owner",
    ),
}


def _load_grammar_actions() -> tuple[AlterTypeGrammarAction, ...]:
    """Freeze every ALTER TYPE synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "owner_to",
            _BRANCH_OWNER,
            "ALTER TYPE name OWNER TO "
            "{ new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }",
            "synopsis-owner-to",
        ),
        (
            "rename",
            _BRANCH_RENAME,
            "ALTER TYPE name RENAME TO new_name",
            "synopsis-rename",
        ),
        (
            "set_schema",
            _BRANCH_SET_SCHEMA,
            "ALTER TYPE name SET SCHEMA new_schema",
            "synopsis-set-schema",
        ),
        (
            "rename_attribute",
            _BRANCH_RENAME_ATTRIBUTE,
            "ALTER TYPE name RENAME ATTRIBUTE attribute_name "
            "TO new_attribute_name [ CASCADE | RESTRICT ]",
            "synopsis-rename-attribute",
        ),
        (
            "add_attribute",
            _BRANCH_ADD_ATTRIBUTE,
            "ALTER TYPE name ADD ATTRIBUTE attribute_name data_type "
            "[ COLLATE collation ] [ CASCADE | RESTRICT ]",
            "synopsis-add-attribute",
        ),
        (
            "drop_attribute",
            _BRANCH_DROP_ATTRIBUTE,
            "ALTER TYPE name DROP ATTRIBUTE [ IF EXISTS ] attribute_name "
            "[ CASCADE | RESTRICT ]",
            "synopsis-drop-attribute",
        ),
        (
            "alter_attribute_type",
            _BRANCH_ALTER_ATTRIBUTE_TYPE,
            "ALTER TYPE name ALTER ATTRIBUTE attribute_name "
            "[ SET DATA ] TYPE data_type [ COLLATE collation ] "
            "[ CASCADE | RESTRICT ]",
            "synopsis-alter-attribute-type",
        ),
        (
            "add_value",
            _BRANCH_ADD_VALUE,
            "ALTER TYPE name ADD VALUE [ IF NOT EXISTS ] new_enum_value "
            "[ { BEFORE | AFTER } neighbor_enum_value ]",
            "synopsis-add-value",
        ),
        (
            "rename_value",
            _BRANCH_RENAME_VALUE,
            "ALTER TYPE name RENAME VALUE existing_enum_value "
            "TO new_enum_value",
            "synopsis-rename-value",
        ),
        (
            "set_property",
            _BRANCH_SET_PROPERTY,
            "ALTER TYPE name SET ( property = value [, ... ] )",
            "synopsis-set-property",
        ),
    )
    actions = [
        AlterTypeGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 10:
        raise AlterTypeFactorLoopError("alter type action count drift")
    return tuple(actions)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterTypeFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "insufficient_privilege":
        try:
            return _INSUFFICIENT_PRIVILEGE_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterTypeFactorLoopError(
                f"unknown insufficient_privilege value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise AlterTypeFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> list[AlterTypeFactorObligation]:
    rows: list[AlterTypeFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            AlterTypeFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"ATYPE-GRM|{action.grammar_branch_id}|"
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
    if len(rows) != 10:
        raise AlterTypeFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[AlterTypeFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("alter_type")
    if len(catalog_rows) != 84:
        raise AlterTypeFactorLoopError("canonical obligation count drift")
    rows: list[AlterTypeFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            AlterTypeFactorObligation(
                ordinal=0,
                obligation_id=f"ATYPE-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[AlterTypeFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"alter-type-factor-obligations-v1\n")
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
    "owner_to": _BRANCH_OWNER,
    "rename": _BRANCH_RENAME,
    "set_schema": _BRANCH_SET_SCHEMA,
    "rename_attribute": _BRANCH_RENAME_ATTRIBUTE,
    "add_attribute": _BRANCH_ADD_ATTRIBUTE,
    "drop_attribute": _BRANCH_DROP_ATTRIBUTE,
    "alter_attribute_type": _BRANCH_ALTER_ATTRIBUTE_TYPE,
    "add_value": _BRANCH_ADD_VALUE,
    "rename_value": _BRANCH_RENAME_VALUE,
    "set_property": _BRANCH_SET_PROPERTY,
}

# Dense baseline defaults (all positive T1-T4 + T6 factor values).  The T5
# factors (non_existent_type, non_existent_attribute,
# insufficient_privilege, cascade_with_typed_tables,
# restrict_with_typed_tables, enum_value_conflict,
# storage_plain_to_other_requires_superuser,
# storage_other_to_plain_never_allowed) are NOT baselined here: every
# declared value is either a failure mode or a branch-specific boundary,
# so they are set only when they are the primary (or derived).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_RENAME,
    "target_action": "rename",
    "object_state": "exists",
    "expected_status": "success",
    "type_category": "composite",
    "cascade_restrict": "none",
    "if_exists_clause": "absent",
    "if_not_exists_clause": "absent",
    "enum_position_clause": "absent",
    "role_specification": "new_owner_role",
    "type_name_shape": "simple",
    "attribute_name_shape": "simple",
    "new_attribute_type": "integer",
    "new_enum_value_shape": "simple_value",
    "privilege_level": "type_owner",
    "typed_table_dependency": "no_typed_tables",
    "attribute_usage_privilege": "has_USAGE",
    "owner_change_privilege": "can_SET_ROLE",
    "schema_privilege": "has_CREATE",
    "new_owner_schema_privilege": "has_CREATE",
    "enum_transaction_state": "outside_transaction",
    "verification_mode": "pg_type_catalog_query",
    "cleanup_mode": "DROP_TYPE_IF_EXISTS",
}


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values.

    Overlapping T5/T4 factors describe the same scenario as their T1-T4
    counterparts.  When the primary factor is a T1-T4 value, the
    corresponding T5 value is derived; when the primary is a T5 value,
    the T1-T4 counterpart is derived.  This keeps the baseline assignment
    self-consistent so the render produces SQL that reaches the intended
    boundary.
    """

    os_state = a.get("object_state", "exists")
    net = a.get("non_existent_type", "")
    # nonexistent type cluster: object_state / non_existent_type
    if os_state == "not_exists" or net == "target_not_exists":
        a["object_state"] = "not_exists"
        a["non_existent_type"] = "target_not_exists"

    pl = a.get("privilege_level", "type_owner")
    ip = a.get("insufficient_privilege", "")
    # non-owner cluster: privilege_level / insufficient_privilege=non_owner
    if pl == "non_owner" or ip == "non_owner":
        a["privilege_level"] = "non_owner"
        a["insufficient_privilege"] = "non_owner"

    # set-property non-superuser cluster
    if ip == "non_superuser_set_property":
        a["privilege_level"] = "non_owner"
        a["insufficient_privilege"] = "non_superuser_set_property"

    aup = a.get("attribute_usage_privilege", "has_USAGE")
    # no-USAGE cluster: attribute_usage_privilege /
    # insufficient_privilege=no_USAGE_on_attribute_type
    if aup == "no_USAGE" or ip == "no_USAGE_on_attribute_type":
        a["attribute_usage_privilege"] = "no_USAGE"
        a["insufficient_privilege"] = "no_USAGE_on_attribute_type"

    # restrict + typed-table cluster: restrict_with_typed_tables implies
    # cascade_restrict=restrict AND typed_table_dependency=has_typed_tables
    rwt = a.get("restrict_with_typed_tables", "")
    if rwt == "restrict_refuses_typed_tables":
        a["cascade_restrict"] = "restrict"
        a["typed_table_dependency"] = "has_typed_tables"
        a["restrict_with_typed_tables"] = "restrict_refuses_typed_tables"

    # cascade + typed-table boundary
    cwt = a.get("cascade_with_typed_tables", "")
    if cwt == "cascade_propagates_to_typed_tables":
        a["cascade_restrict"] = "cascade"
        a["typed_table_dependency"] = "has_typed_tables"
        a["cascade_with_typed_tables"] = "cascade_propagates_to_typed_tables"

    # set-property storage clusters (standalone, branch=set_property)
    spt = a.get("storage_plain_to_other_requires_superuser", "")
    if spt == "plain_to_extended_requires_superuser":
        a["storage_plain_to_other_requires_superuser"] = (
            "plain_to_extended_requires_superuser"
        )
    sot = a.get("storage_other_to_plain_never_allowed", "")
    if sot == "other_to_plain_never_allowed":
        a["storage_other_to_plain_never_allowed"] = (
            "other_to_plain_never_allowed"
        )

    # enum conflict boundary (add_value branch)
    evc = a.get("enum_value_conflict", "")
    if evc in {
        "value_exists_no_if_not_exists",
        "value_exists_with_if_not_exists",
    }:
        a["enum_value_conflict"] = evc

    # non-existent-attribute boundary (drop/alter attribute branch)
    nea = a.get("non_existent_attribute", "")
    if nea in {
        "attribute_not_exists_no_if_exists",
        "attribute_not_exists_with_if_exists",
    }:
        a["non_existent_attribute"] = nea

    # expected_status=failure arms the missing-type scenario so the case
    # reaches a real, attributable PG target-check rejection.
    if a.get("expected_status") == "failure":
        if a.get("object_state") != "not_exists":
            a["object_state"] = "not_exists"
            a["non_existent_type"] = "target_not_exists"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: AlterTypeFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["statement_branch"] = _ACTION_BRANCH[
        obligation.consumer_action_id
    ]
    assignments["target_action"] = obligation.consumer_action_id
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    failures = _count_baseline_failures(assignments)
    assignments["expected_status"] = (
        "failure" if failures > 0 else "success"
    )
    if len(assignments) != len(set(assignments)):
        raise AlterTypeFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: AlterTypeFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise AlterTypeFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_alter_type_factor_loop_plan(
    repository_root: Path,
) -> AlterTypeFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_alter_type_factor_loop_obligations(root)
    cases: list[AlterTypeFactorCase] = []
    delegated: list[AlterTypeFactorObligation] = []
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
            AlterTypeFactorCase(
                ordinal=ordinal,
                case_id=f"ALTERTYPE{ordinal:05d}",
                sql_filename=f"ALTERTYPE{ordinal:05d}.sql",
                object_prefix=f"altertype_{ordinal:05d}_",
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
    plan = AlterTypeFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 94 or len(plan.delegated) != 0:
        raise AlterTypeFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 94:
        raise AlterTypeFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 94:
        raise AlterTypeFactorLoopError("duplicate SQL filename")
    return plan


def compile_alter_type_factor_loop_obligations(
    repository_root: Path,
) -> tuple[AlterTypeFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        AlterTypeFactorObligation(
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
    if len(rows) != 94:
        raise AlterTypeFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise AlterTypeFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 10, "SFV": 84}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise AlterTypeFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise AlterTypeFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 94:
        raise AlterTypeFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise AlterTypeFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "AlterTypeFactorLoopError",
    "AlterTypeGrammarAction",
    "AlterTypeFactorObligation",
    "AlterTypeFactorCase",
    "AlterTypeFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_alter_type_factor_loop_obligations",
    "build_alter_type_factor_loop_plan",
    "_obligation_multiset_sha256",
]
