"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE TABLE.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE TABLE``.  CREATE TABLE is the central PostgreSQL DDL statement
with three official synopsis branches (regular column-list form,
``OF type_name`` typed-table form, and ``PARTITION OF`` partition form)
frozen as ``GRM`` target forms.

CREATE TABLE creates a relation (``pg_class.relkind = 'r'``).  The
bookend gate applies directly: the FIRST and LAST executable
``;``-statements are each ``DROP TABLE IF EXISTS <all created tables>``
and the script creates >=1 table.  The 185 canonical ``SFV`` rows are
loaded from the shipped applicability universe
(``postgresql_18_4_factor_audit.tsv``).  CREATE TABLE has no
``OR REPLACE`` form.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CreateTableFactorLoopError(ValueError):
    """Raised when a frozen CREATE TABLE obligation input drifts."""


@dataclass(frozen=True)
class CreateTableGrammarAction:
    """One official target action form of the CREATE TABLE synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateTableFactorObligation:
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
class CreateTableFactorCase:
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
class CreateTableFactorLoopPlan:
    obligations: tuple[CreateTableFactorObligation, ...]
    cases: tuple[CreateTableFactorCase, ...]
    delegated: tuple[CreateTableFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-createtable.html).
_BRANCH_REGULAR = "branch_1"
_BRANCH_TYPED = "branch_2"
_BRANCH_PARTITION = "branch_3"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createtable"

_REPRESENTATIVE_ACTION = "create_regular"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_REGULAR: "create_regular",
    _BRANCH_TYPED: "create_typed",
    _BRANCH_PARTITION: "create_partition",
}

# action -> grammar branch id used by the renderer.
_ACTION_BRANCH = {
    "create_regular": _BRANCH_REGULAR,
    "create_typed": _BRANCH_TYPED,
    "create_partition": _BRANCH_PARTITION,
}

# Canonical factor -> the default action where the value is observable.
_SFV_FACTOR_CONSUMER = {
    "base_table_template_coverage": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
    "collation_clause": _REPRESENTATIVE_ACTION,
    "column_definition_count": _REPRESENTATIVE_ACTION,
    "column_name_shape": _REPRESENTATIVE_ACTION,
    "constraint_type": _REPRESENTATIVE_ACTION,
    "constraint_violation_in_definition": _REPRESENTATIVE_ACTION,
    "data_type": _REPRESENTATIVE_ACTION,
    "default_value_shape": _REPRESENTATIVE_ACTION,
    "duplicate_column_name": _REPRESENTATIVE_ACTION,
    "duplicate_table_name": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "generated_clause": _REPRESENTATIVE_ACTION,
    "identifier_length_exceeded": _REPRESENTATIVE_ACTION,
    "if_not_exists_clause": _REPRESENTATIVE_ACTION,
    "inheritance_clause": _REPRESENTATIVE_ACTION,
    "invalid_data_type": _REPRESENTATIVE_ACTION,
    "like_clause": _REPRESENTATIVE_ACTION,
    "max_column_limit": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "on_commit_clause": _REPRESENTATIVE_ACTION,
    "on_commit_with_non_temporary": _REPRESENTATIVE_ACTION,
    "partition_clause": _REPRESENTATIVE_ACTION,
    "privilege_level": _REPRESENTATIVE_ACTION,
    "referenced_table_dependency": _REPRESENTATIVE_ACTION,
    "reserved_schema_name": _REPRESENTATIVE_ACTION,
    "role_dependency": _REPRESENTATIVE_ACTION,
    "schema_dependency": _REPRESENTATIVE_ACTION,
    "schema_permission_insufficient": _REPRESENTATIVE_ACTION,
    "table_name_shape": _REPRESENTATIVE_ACTION,
    "table_type": _REPRESENTATIVE_ACTION,
    "tablespace_dependency": _REPRESENTATIVE_ACTION,
    "temporary_table_scope_conflict": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "type_dependency": "create_typed",
    "parent_table_dependency": "create_partition",
    "partition_bound_invalid": "create_partition",
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "already_exists"),
        ("duplicate_table_name", "without_IF_NOT_EXISTS_error"),
        ("duplicate_column_name", "same_column_name_in_table"),
        ("table_name_shape", "duplicate"),
        ("column_name_shape", "duplicate_in_table"),
        ("constraint_violation_in_definition", "CHECK_expression_invalid"),
        (
            "constraint_violation_in_definition",
            "FK_references_nonexistent_table",
        ),
        ("constraint_violation_in_definition", "PK_with_nullable_column"),
        ("invalid_data_type", "unknown_type_name"),
        ("invalid_data_type", "wrong_array_syntax"),
        ("identifier_length_exceeded", "over_63_chars"),
        ("max_column_limit", "over_1600"),
        ("on_commit_with_non_temporary", "on_commit_on_permanent_table"),
        ("parent_table_dependency", "parent_table_not_exists"),
        ("parent_table_dependency", "parent_table_not_partitioned"),
        ("partition_bound_invalid", "bound_out_of_range"),
        ("partition_bound_invalid", "bound_type_mismatch"),
        ("privilege_level", "non_owner_no_privilege"),
        ("referenced_table_dependency", "referenced_table_not_exists"),
        ("reserved_schema_name", "information_schema"),
        ("reserved_schema_name", "pg_catalog"),
        ("role_dependency", "owner_role_not_exists"),
        ("schema_dependency", "information_schema_reserved"),
        ("schema_dependency", "pg_catalog_reserved"),
        ("schema_dependency", "schema_not_exists"),
        ("schema_permission_insufficient", "no_create_privilege_in_schema"),
        ("tablespace_dependency", "specified_tablespace_not_exists"),
        ("temporary_table_scope_conflict", "temp_table_same_name_permanent"),
        ("type_dependency", "composite_type_not_exists"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42710", "duplicate_object_provisional",
    ),
    ("object_state", "already_exists"): (
        "42710", "duplicate_object_provisional",
    ),
    ("duplicate_table_name", "without_IF_NOT_EXISTS_error"): (
        "42710", "duplicate_object_provisional",
    ),
    ("duplicate_column_name", "same_column_name_in_table"): (
        "42710", "duplicate_column_provisional",
    ),
    ("table_name_shape", "duplicate"): (
        "42710", "duplicate_object_provisional",
    ),
    ("column_name_shape", "duplicate_in_table"): (
        "42710", "duplicate_column_provisional",
    ),
    ("constraint_violation_in_definition", "CHECK_expression_invalid"): (
        "42P17", "invalid_table_definition_provisional",
    ),
    ("constraint_violation_in_definition", "FK_references_nonexistent_table"): (
        "42P01", "undefined_table_provisional",
    ),
    ("constraint_violation_in_definition", "PK_with_nullable_column"): (
        "42P17", "invalid_table_definition_provisional",
    ),
    ("invalid_data_type", "unknown_type_name"): (
        "42704", "undefined_object_provisional",
    ),
    ("invalid_data_type", "wrong_array_syntax"): (
        "42601", "syntax_error_provisional",
    ),
    ("identifier_length_exceeded", "over_63_chars"): (
        "42602", "invalid_name_provisional",
    ),
    ("max_column_limit", "over_1600"): (
        "54011", "too_many_columns_provisional",
    ),
    ("on_commit_with_non_temporary", "on_commit_on_permanent_table"): (
        "42809", "wrong_object_type_provisional",
    ),
    ("parent_table_dependency", "parent_table_not_exists"): (
        "42P01", "undefined_table_provisional",
    ),
    ("parent_table_dependency", "parent_table_not_partitioned"): (
        "42809", "wrong_object_type_provisional",
    ),
    ("partition_bound_invalid", "bound_out_of_range"): (
        "42804", "datatype_mismatch_provisional",
    ),
    ("partition_bound_invalid", "bound_type_mismatch"): (
        "42804", "datatype_mismatch_provisional",
    ),
    ("privilege_level", "non_owner_no_privilege"): (
        "42501", "insufficient_privilege_provisional",
    ),
    ("referenced_table_dependency", "referenced_table_not_exists"): (
        "42P01", "undefined_table_provisional",
    ),
    ("reserved_schema_name", "information_schema"): (
        "42501", "insufficient_privilege_provisional",
    ),
    ("reserved_schema_name", "pg_catalog"): (
        "42501", "insufficient_privilege_provisional",
    ),
    ("role_dependency", "owner_role_not_exists"): (
        "42704", "undefined_object_provisional",
    ),
    ("schema_dependency", "information_schema_reserved"): (
        "42501", "insufficient_privilege_provisional",
    ),
    ("schema_dependency", "pg_catalog_reserved"): (
        "42501", "insufficient_privilege_provisional",
    ),
    ("schema_dependency", "schema_not_exists"): (
        "3F000", "invalid_schema_name_provisional",
    ),
    ("schema_permission_insufficient", "no_create_privilege_in_schema"): (
        "42501", "insufficient_privilege_provisional",
    ),
    ("tablespace_dependency", "specified_tablespace_not_exists"): (
        "42704", "undefined_object_provisional",
    ),
    ("temporary_table_scope_conflict", "temp_table_same_name_permanent"): (
        "42710", "duplicate_object_provisional",
    ),
    ("type_dependency", "composite_type_not_exists"): (
        "42704", "undefined_object_provisional",
    ),
}


def _load_grammar_actions() -> tuple[CreateTableGrammarAction, ...]:
    """Freeze every CREATE TABLE synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "create_regular",
            _BRANCH_REGULAR,
            "CREATE [TEMP|UNLOGGED] TABLE [IF NOT EXISTS] name "
            "(col type [constraints] [, ...]) [INHERITS (parent)] "
            "[PARTITION BY ...] [WITH (...) | WITHOUT OIDS] "
            "[ON COMMIT ...] [TABLESPACE ...]",
            "synopsis-regular",
        ),
        (
            "create_typed",
            _BRANCH_TYPED,
            "CREATE TABLE [IF NOT EXISTS] name OF type_name "
            "[(col [WITH OPTIONS] [constraints] [, ...])] "
            "[PARTITION BY ...] [WITH (...) | WITHOUT OIDS] "
            "[ON COMMIT ...] [TABLESPACE ...]",
            "synopsis-typed",
        ),
        (
            "create_partition",
            _BRANCH_PARTITION,
            "CREATE TABLE [IF NOT EXISTS] name PARTITION OF parent "
            "[(col [constraints] [, ...])] "
            "{FOR VALUES partition_bound_spec | DEFAULT} "
            "[PARTITION BY ...] [WITH (...) | WITHOUT OIDS] "
            "[ON COMMIT ...] [TABLESPACE ...]",
            "synopsis-partition",
        ),
    )
    actions = [
        CreateTableGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 3:
        raise CreateTableFactorLoopError("action count drift")
    return tuple(actions)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise CreateTableFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "base_table_template_coverage":
        return "create_typed" if row.value == "table_04_typed_table" else (
            _REPRESENTATIVE_ACTION
        )
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise CreateTableFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> list[CreateTableFactorObligation]:
    rows: list[CreateTableFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateTableFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CT-GRM|{action.grammar_branch_id}|"
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
    if len(rows) != 3:
        raise CreateTableFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateTableFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_table")
    if len(catalog_rows) != 185:
        raise CreateTableFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[CreateTableFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateTableFactorObligation(
                ordinal=0,
                obligation_id=f"CT-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreateTableFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"create-table-factor-obligations-v1\n")
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


# Dense baseline defaults (all positive T1-T4 + T6 factor values).  T5
# single-value factors default to ``none`` and are derived in
# :func:`_derive_overlapping_factors`.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_REGULAR,
    "base_table_template_coverage": "table_01_comprehensive_types",
    "cleanup_mode": "DROP_TABLE",
    "collation_clause": "without_COLLATION",
    "column_definition_count": "single_column",
    "column_name_shape": "simple",
    "constraint_type": "NOT_NULL",
    "constraint_violation_in_definition": "none",
    "data_type": "integer",
    "default_value_shape": "without_DEFAULT",
    "duplicate_column_name": "none",
    "duplicate_table_name": "with_IF_NOT_EXISTS_noop",
    "expected_status": "success",
    "generated_clause": "none",
    "identifier_length_exceeded": "none",
    "if_not_exists_clause": "absent",
    "inheritance_clause": "no_inheritance",
    "invalid_data_type": "none",
    "like_clause": "no_LIKE",
    "max_column_limit": "approaching_1600",
    "object_state": "not_exists",
    "on_commit_clause": "absent",
    "on_commit_with_non_temporary": "none",
    "parent_table_dependency": "parent_table_exists",
    "partition_bound_invalid": "none",
    "partition_clause": "not_partitioned",
    "privilege_level": "superuser",
    "referenced_table_dependency": "referenced_table_exists",
    "reserved_schema_name": "none",
    "role_dependency": "owner_role_exists",
    "schema_dependency": "schema_exists",
    "schema_permission_insufficient": "none",
    "table_name_shape": "simple",
    "table_type": "permanent",
    "tablespace_dependency": "default_tablespace",
    "temporary_table_scope_conflict": "none",
    "type_dependency": "composite_type_exists",
    "verification_mode": "pg_class_catalog_query",
}


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(1 for pair in _SFV_FAILURE_VALUES if a.get(pair[0]) == pair[1])


def _derive_object_state_cluster(a: dict[str, str]) -> None:
    """Derive object_state / duplicate_table_name / table_name_shape."""

    os_val = a.get("object_state", "not_exists")
    dt = a.get("duplicate_table_name", "with_IF_NOT_EXISTS_noop")
    tns = a.get("table_name_shape", "simple")
    ttsc = a.get("temporary_table_scope_conflict", "none")
    if os_val == "already_exists" or dt == "without_IF_NOT_EXISTS_error" or (
        tns == "duplicate"
    ) or ttsc == "temp_table_same_name_permanent":
        a["object_state"] = "already_exists"
        a["duplicate_table_name"] = "without_IF_NOT_EXISTS_error"
        a["table_name_shape"] = "duplicate"


def _derive_schema_cluster(a: dict[str, str]) -> None:
    """Derive schema_dependency / reserved_schema_name."""

    sd = a.get("schema_dependency", "schema_exists")
    rsn = a.get("reserved_schema_name", "none")
    if sd == "information_schema_reserved" or rsn == "information_schema":
        a["schema_dependency"] = "information_schema_reserved"
        a["reserved_schema_name"] = "information_schema"
    elif sd == "pg_catalog_reserved" or rsn == "pg_catalog":
        a["schema_dependency"] = "pg_catalog_reserved"
        a["reserved_schema_name"] = "pg_catalog"


def _derive_privilege_cluster(a: dict[str, str]) -> None:
    """Derive privilege_level / schema_permission_insufficient."""

    pl = a.get("privilege_level", "superuser")
    spi = a.get("schema_permission_insufficient", "none")
    if pl == "non_owner_no_privilege" or spi == "no_create_privilege_in_schema":
        a["privilege_level"] = "non_owner_no_privilege"
        a["schema_permission_insufficient"] = "no_create_privilege_in_schema"


def _derive_parent_cluster(a: dict[str, str]) -> None:
    """Derive parent_table_dependency."""

    ptd = a.get("parent_table_dependency", "parent_table_exists")
    if ptd in ("parent_table_not_exists", "parent_table_not_partitioned"):
        a["parent_table_dependency"] = ptd


def _derive_type_cluster(a: dict[str, str]) -> None:
    """Derive type_dependency."""

    td = a.get("type_dependency", "composite_type_exists")
    if td == "composite_type_not_exists":
        a["type_dependency"] = "composite_type_not_exists"


def _derive_remaining_clusters(a: dict[str, str]) -> None:
    """Derive remaining T5 boundary factors from T1-T4 values."""

    rtd = a.get("referenced_table_dependency", "referenced_table_exists")
    if rtd == "referenced_table_not_exists":
        a["referenced_table_dependency"] = "referenced_table_not_exists"
    rd = a.get("role_dependency", "owner_role_exists")
    if rd == "owner_role_not_exists":
        a["role_dependency"] = "owner_role_not_exists"
    tsd = a.get("tablespace_dependency", "default_tablespace")
    if tsd == "specified_tablespace_not_exists":
        a["tablespace_dependency"] = "specified_tablespace_not_exists"
    cv = a.get("constraint_violation_in_definition", "none")
    if cv != "none":
        a["constraint_violation_in_definition"] = cv
    idt = a.get("invalid_data_type", "none")
    if idt != "none":
        a["invalid_data_type"] = idt


def _derive_branch_cluster(a: dict[str, str]) -> None:
    """Derive statement_branch from consumer action / partition axes."""

    action = a.get("__consumer_action", "create_regular")
    if action in _ACTION_BRANCH:
        a["statement_branch"] = _ACTION_BRANCH[action]
    pc = a.get("partition_clause", "not_partitioned")
    if pc in ("RANGE", "LIST", "HASH") and action == "create_regular":
        a["partition_clause"] = pc
    pbi = a.get("partition_bound_invalid", "none")
    if pbi != "none" and action == "create_partition":
        a["partition_bound_invalid"] = pbi


def _derive_reverse_t5(a: dict[str, str]) -> None:
    """Reverse-derive T1-T4 values from T5 factor overrides.

    The TSV catalog stores T5 meta-factors (``expected_status``,
    ``on_commit_with_non_temporary``) as primary overrides.  The renderer
    needs the underlying T1-T4 values to emit the correct SQL syntax.
    """

    if a.get("expected_status") == "failure":
        a["object_state"] = "already_exists"
    ocwt = a.get("on_commit_with_non_temporary", "none")
    if ocwt == "on_commit_on_permanent_table":
        if a.get("on_commit_clause", "absent") == "absent":
            a["on_commit_clause"] = "DELETE_ROWS"
        a["table_type"] = "permanent"


def _derive_on_commit_cluster(a: dict[str, str]) -> None:
    """Derive table_type from on_commit_clause (non-failure case)."""

    ocwt = a.get("on_commit_with_non_temporary", "none")
    oc = a.get("on_commit_clause", "absent")
    if ocwt == "on_commit_on_permanent_table":
        a["table_type"] = "permanent"
    elif oc != "absent":
        a["table_type"] = "temporary_global"


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values."""

    _derive_reverse_t5(a)
    _derive_object_state_cluster(a)
    _derive_schema_cluster(a)
    _derive_privilege_cluster(a)
    _derive_parent_cluster(a)
    _derive_type_cluster(a)
    _derive_on_commit_cluster(a)
    _derive_remaining_clusters(a)
    _derive_branch_cluster(a)
    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"
    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _baseline_assignments(
    obligation: CreateTableFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    if obligation.consumer_action_id in _ACTION_BRANCH:
        assignments["statement_branch"] = _ACTION_BRANCH[
            obligation.consumer_action_id
        ]
    assignments[obligation.factor_key] = obligation.value
    assignments["__consumer_action"] = obligation.consumer_action_id
    _derive_overlapping_factors(assignments)
    del assignments["__consumer_action"]
    failures = _count_baseline_failures(assignments)
    assignments["expected_status"] = (
        "failure" if failures > 0 else "success"
    )
    if len(assignments) != len(set(assignments)):
        raise CreateTableFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateTableFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateTableFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_table_factor_loop_plan(
    repository_root: Path,
) -> CreateTableFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_table_factor_loop_obligations(root)
    cases: list[CreateTableFactorCase] = []
    delegated: list[CreateTableFactorObligation] = []
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
            CreateTableFactorCase(
                ordinal=ordinal,
                case_id=f"CREATETABLE{ordinal:05d}",
                sql_filename=f"CREATETABLE{ordinal:05d}.sql",
                object_prefix=f"createtable_{ordinal:05d}_",
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
    plan = CreateTableFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 188 or len(plan.delegated) != 0:
        raise CreateTableFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 188:
        raise CreateTableFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 188:
        raise CreateTableFactorLoopError("duplicate SQL filename")
    return plan


def compile_create_table_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateTableFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateTableFactorObligation(
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
    if len(rows) != 188:
        raise CreateTableFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateTableFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 3, "SFV": 185}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateTableFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateTableFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 188:
        raise CreateTableFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreateTableFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "CreateTableFactorLoopError",
    "CreateTableGrammarAction",
    "CreateTableFactorObligation",
    "CreateTableFactorCase",
    "CreateTableFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "_BASELINE_DEFAULTS",
    "_ACTION_BRANCH",
    "_STATEMENT_BRANCH_CONSUMER",
    "compile_create_table_factor_loop_obligations",
    "build_create_table_factor_loop_plan",
    "_obligation_multiset_sha256",
]
