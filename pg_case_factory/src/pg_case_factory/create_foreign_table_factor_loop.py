"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE FOREIGN TABLE.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE FOREIGN TABLE``.  CREATE FOREIGN TABLE is a PostgreSQL DDL
statement with 2 official synopsis branches (regular column-definition
form and ``PARTITION OF`` form) plus 3 PG18 reference-parity forms
(``LIKE`` source, ``VIRTUAL NOT ENFORCED`` generated column, and
table-level ``NOT NULL ... NO INHERIT``).  The 5 grammar target forms are
frozen inline; the 91 canonical ``SFV`` rows are loaded from the shipped
applicability universe (``postgresql_18_4_factor_audit.tsv``).

CREATE FOREIGN TABLE creates a foreign-table relation
(``pg_class.relkind = 'f'``), not a regular table.  The shared bookend
gate's ``CREATE TABLE`` pattern deliberately does not match
``CREATE FOREIGN TABLE`` (``FOREIGN`` sits between ``CREATE`` and
``TABLE``), so scripts that create only foreign tables are table-less and
bookend-exempt.  Cases that fixture a regular parent/source table
(partition parent, ``INHERITS`` parent, ``LIKE`` source) do create a
``CREATE TABLE`` and therefore carry the ``DROP TABLE IF EXISTS``
bookend.  CREATE FOREIGN TABLE does not support ``OR REPLACE``.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CreateForeignTableFactorLoopError(ValueError):
    """Raised when a frozen CREATE FOREIGN TABLE obligation input drifts."""


@dataclass(frozen=True)
class CreateForeignTableGrammarAction:
    """One official target action form of the CREATE FOREIGN TABLE synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateForeignTableFactorObligation:
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
class CreateForeignTableFactorCase:
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
class CreateForeignTableFactorLoopPlan:
    obligations: tuple[CreateForeignTableFactorObligation, ...]
    cases: tuple[CreateForeignTableFactorCase, ...]
    delegated: tuple[CreateForeignTableFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-createforeigntable.html).
_BRANCH_REGULAR = "branch_regular"
_BRANCH_PARTITION = "branch_partition"
_BRANCH_LIKE = "branch_pg18_like_source"
_BRANCH_VIRTUAL = "branch_pg18_virtual_generated"
_BRANCH_TABLE_NOT_NULL = "branch_pg18_table_not_null"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createforeigntable"

# A representative create_regular action used as the baseline consumer for
# canonical factors that are not bound to one specific branch.
_REPRESENTATIVE_ACTION = "create_regular"

# table_form canonical value -> target action.
_TABLE_FORM_CONSUMER = {
    "regular": "create_regular",
    "partition_of": "create_partition",
    "like_source": "pg18_like_source",
    "regular_virtual_generated": "pg18_virtual_generated",
    "regular_table_not_null": "pg18_table_not_null",
}

# table_form canonical value -> statement_branch.
_TABLE_FORM_BRANCH = {
    "regular": _BRANCH_REGULAR,
    "partition_of": _BRANCH_PARTITION,
    "like_source": _BRANCH_REGULAR,
    "regular_virtual_generated": _BRANCH_REGULAR,
    "regular_table_not_null": _BRANCH_REGULAR,
}

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_REGULAR: "create_regular",
    _BRANCH_PARTITION: "create_partition",
}

# Canonical factor -> the action where the value is observable.  Factors
# whose consumer depends on the value (statement_branch, table_form) are
# resolved in :func:`_canonical_consumer`.
_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "table_form": _REPRESENTATIVE_ACTION,
    "if_not_exists_clause": _REPRESENTATIVE_ACTION,
    "column_count": _REPRESENTATIVE_ACTION,
    "column_data_type": _REPRESENTATIVE_ACTION,
    "inherits_clause": "create_regular",
    "partition_bound_spec": "create_partition",
    "server_clause": _REPRESENTATIVE_ACTION,
    "table_name_shape": _REPRESENTATIVE_ACTION,
    "column_name_shape": _REPRESENTATIVE_ACTION,
    "server_name_shape": _REPRESENTATIVE_ACTION,
    "constraint_name_shape": _REPRESENTATIVE_ACTION,
    "collation_name_shape": _REPRESENTATIVE_ACTION,
    "privilege_level": _REPRESENTATIVE_ACTION,
    "server_existence": _REPRESENTATIVE_ACTION,
    "parent_table_existence": "create_partition",
    "schema_existence": _REPRESENTATIVE_ACTION,
    "type_name_conflict": _REPRESENTATIVE_ACTION,
    "duplicate_table_name": _REPRESENTATIVE_ACTION,
    "nonexistent_server": _REPRESENTATIVE_ACTION,
    "nonexistent_parent_table": "create_partition",
    "no_server_usage_privilege": _REPRESENTATIVE_ACTION,
    "no_type_usage_privilege": _REPRESENTATIVE_ACTION,
    "if_not_exists_no_op": _REPRESENTATIVE_ACTION,
    "zero_column_table": _REPRESENTATIVE_ACTION,
    "constraint_not_enforced": _REPRESENTATIVE_ACTION,
    "type_name_conflict_error": _REPRESENTATIVE_ACTION,
    "parent_has_unique_index": "create_partition",
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "already_exists"),
        ("object_state", "type_name_conflict"),
        ("table_name_shape", "duplicate_name"),
        ("server_clause", "nonexistent_server"),
        ("server_name_shape", "nonexistent_server"),
        ("server_existence", "server_not_exists"),
        ("nonexistent_server", "server_missing"),
        ("privilege_level", "no_server_usage"),
        ("privilege_level", "no_type_usage"),
        ("no_server_usage_privilege", "lacks_usage"),
        ("no_type_usage_privilege", "lacks_usage"),
        ("parent_table_existence", "parent_not_exists"),
        ("nonexistent_parent_table", "parent_missing"),
        ("parent_has_unique_index", "parent_has_unique"),
        ("type_name_conflict", "same_as_existing_type"),
        ("type_name_conflict_error", "conflict_with_existing_type"),
        ("duplicate_table_name", "same_name_conflict"),
        ("schema_existence", "schema_not_exists"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("object_state", "already_exists"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("object_state", "type_name_conflict"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("table_name_shape", "duplicate_name"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("server_clause", "nonexistent_server"): (
        "42704",
        "undefined_object_provisional",
    ),
    ("server_name_shape", "nonexistent_server"): (
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
    ("privilege_level", "no_server_usage"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("privilege_level", "no_type_usage"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("no_server_usage_privilege", "lacks_usage"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("no_type_usage_privilege", "lacks_usage"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("parent_table_existence", "parent_not_exists"): (
        "42P01",
        "undefined_table_provisional",
    ),
    ("nonexistent_parent_table", "parent_missing"): (
        "42P01",
        "undefined_table_provisional",
    ),
    ("parent_has_unique_index", "parent_has_unique"): (
        "42P17",
        "invalid_table_definition_provisional",
    ),
    ("type_name_conflict", "same_as_existing_type"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("type_name_conflict_error", "conflict_with_existing_type"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("duplicate_table_name", "same_name_conflict"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("schema_existence", "schema_not_exists"): (
        "3F000",
        "invalid_schema_provisional",
    ),
}


def _load_grammar_actions() -> (
    tuple[CreateForeignTableGrammarAction, ...]
):
    """Freeze every CREATE FOREIGN TABLE synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "create_regular",
            _BRANCH_REGULAR,
            (
                "CREATE FOREIGN TABLE [IF NOT EXISTS] name "
                "( [column_def [, ...]] ) [INHERITS (parent [, ...])] "
                "SERVER server_name [OPTIONS (option 'value' [, ...])]"
            ),
            "synopsis-regular",
        ),
        (
            "create_partition",
            _BRANCH_PARTITION,
            (
                "CREATE FOREIGN TABLE [IF NOT EXISTS] name "
                "PARTITION OF parent [(column_def [, ...])] "
                "{FOR VALUES partition_bound_spec | DEFAULT} "
                "SERVER server_name [OPTIONS (option 'value' [, ...])]"
            ),
            "synopsis-partition",
        ),
        (
            "pg18_like_source",
            _BRANCH_LIKE,
            (
                "CREATE FOREIGN TABLE name (LIKE source INCLUDING ALL) "
                "SERVER server_name"
            ),
            "pg18-like-source",
        ),
        (
            "pg18_virtual_generated",
            _BRANCH_VIRTUAL,
            (
                "CREATE FOREIGN TABLE name (col integer GENERATED ALWAYS "
                "AS (1) VIRTUAL NOT ENFORCED) SERVER server_name"
            ),
            "pg18-virtual-generated",
        ),
        (
            "pg18_table_not_null",
            _BRANCH_TABLE_NOT_NULL,
            (
                "CREATE FOREIGN TABLE name (col integer, NOT NULL col "
                "NO INHERIT) SERVER server_name"
            ),
            "pg18-table-not-null",
        ),
    )
    actions = [
        CreateForeignTableGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 5:
        raise CreateForeignTableFactorLoopError(
            "create foreign table action count drift"
        )
    return tuple(actions)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise CreateForeignTableFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "table_form":
        try:
            return _TABLE_FORM_CONSUMER[row.value]
        except KeyError as exc:
            raise CreateForeignTableFactorLoopError(
                f"unknown table_form value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise CreateForeignTableFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> (
    list[CreateForeignTableFactorObligation]
):
    rows: list[CreateForeignTableFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateForeignTableFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CFT-GRM|{action.grammar_branch_id}|"
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
    if len(rows) != 5:
        raise CreateForeignTableFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateForeignTableFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_foreign_table")
    if len(catalog_rows) != 91:
        raise CreateForeignTableFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[CreateForeignTableFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateForeignTableFactorObligation(
                ordinal=0,
                obligation_id=f"CFT-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreateForeignTableFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-foreign-table-factor-obligations-v1\n"
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
    "create_regular": _BRANCH_REGULAR,
    "create_partition": _BRANCH_PARTITION,
    "pg18_like_source": _BRANCH_LIKE,
    "pg18_virtual_generated": _BRANCH_VIRTUAL,
    "pg18_table_not_null": _BRANCH_TABLE_NOT_NULL,
}

# Dense baseline defaults (all positive T1-T4 + T6 factor values).  The T5
# single-value factors are derived in :func:`_derive_overlapping_factors`.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_REGULAR,
    "object_state": "not_exists",
    "expected_status": "success",
    "table_form": "regular",
    "if_not_exists_clause": "omitted",
    "column_count": "single_column",
    "column_data_type": "integer",
    "inherits_clause": "omitted",
    "partition_bound_spec": "for_values_in",
    "server_clause": "valid_server",
    "table_name_shape": "simple_id",
    "column_name_shape": "simple_id",
    "server_name_shape": "simple_id",
    "constraint_name_shape": "omitted",
    "collation_name_shape": "omitted",
    "privilege_level": "usage_on_server_and_types",
    "server_existence": "server_exists",
    "parent_table_existence": "parent_exists",
    "schema_existence": "schema_exists",
    "type_name_conflict": "no_conflict",
    "duplicate_table_name": "no_conflict",
    "nonexistent_server": "server_exists",
    "nonexistent_parent_table": "parent_exists",
    "no_server_usage_privilege": "has_usage",
    "no_type_usage_privilege": "has_usage",
    "if_not_exists_no_op": "new_create",
    "zero_column_table": "has_columns",
    "constraint_not_enforced": "no_constraints",
    "type_name_conflict_error": "no_conflict",
    "parent_has_unique_index": "parent_no_unique",
    "verification_mode": "pg_class_catalog_query",
    "cleanup_mode": "drop_foreign_table",
}


def _count_baseline_failures(a: dict[str, str]) -> int:
    count = 0
    for pair in _SFV_FAILURE_VALUES:
        if a.get(pair[0]) != pair[1]:
            continue
        # IF NOT EXISTS + already_exists is a no-op NOTICE (success), not
        # a duplicate error; do not count it as a failure.
        if (
            pair == ("object_state", "already_exists")
            and a.get("if_not_exists_clause") == "specified"
        ):
            continue
        count += 1
    return count


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values.

    The T5 single-value factors describe the same scenario as their T1-T4
    counterparts.  When the primary factor is a T1-T4 value, the
    corresponding T5 value is derived; when the primary is a T5 value, the
    T1-T4 counterpart is derived.  This keeps the baseline assignment
    self-consistent so the render produces SQL that reaches the intended
    boundary.
    """

    # --- object_state cluster ---------------------------------------
    os_val = a.get("object_state", "not_exists")
    dt = a.get("duplicate_table_name", "")
    tnc = a.get("type_name_conflict", "")
    tnce = a.get("type_name_conflict_error", "")
    tns = a.get("table_name_shape", "simple_id")

    if os_val == "already_exists" or dt == "same_name_conflict" or (
        tns == "duplicate_name"
    ):
        a["object_state"] = "already_exists"
        a["duplicate_table_name"] = "same_name_conflict"
        a["table_name_shape"] = "duplicate_name"

    if (
        os_val == "type_name_conflict"
        or tnc == "same_as_existing_type"
        or tnce == "conflict_with_existing_type"
    ):
        a["object_state"] = "type_name_conflict"
        a["type_name_conflict"] = "same_as_existing_type"
        a["type_name_conflict_error"] = "conflict_with_existing_type"

    # --- server cluster --------------------------------------------
    sc = a.get("server_clause", "valid_server")
    se = a.get("server_existence", "server_exists")
    sns = a.get("server_name_shape", "simple_id")
    ns = a.get("nonexistent_server", "server_exists")
    if (
        sc == "nonexistent_server"
        or se == "server_not_exists"
        or sns == "nonexistent_server"
        or ns == "server_missing"
    ):
        a["server_clause"] = "nonexistent_server"
        a["server_existence"] = "server_not_exists"
        a["server_name_shape"] = "nonexistent_server"
        a["nonexistent_server"] = "server_missing"
    else:
        a["nonexistent_server"] = "server_exists"

    # --- privilege cluster -----------------------------------------
    pl = a.get("privilege_level", "usage_on_server_and_types")
    nsp = a.get("no_server_usage_privilege", "has_usage")
    ntp = a.get("no_type_usage_privilege", "has_usage")
    if pl == "no_server_usage" or nsp == "lacks_usage":
        a["privilege_level"] = "no_server_usage"
        a["no_server_usage_privilege"] = "lacks_usage"
    if pl == "no_type_usage" or ntp == "lacks_usage":
        a["privilege_level"] = "no_type_usage"
        a["no_type_usage_privilege"] = "lacks_usage"

    # --- parent cluster (partition form) --------------------------
    pte = a.get("parent_table_existence", "parent_exists")
    npt = a.get("nonexistent_parent_table", "parent_exists")
    if pte == "parent_not_exists" or npt == "parent_missing":
        a["parent_table_existence"] = "parent_not_exists"
        a["nonexistent_parent_table"] = "parent_missing"

    # --- if_not_exists_no_op <-> if_not_exists_clause / object_state
    ifne = a.get("if_not_exists_clause", "omitted")
    ino = a.get("if_not_exists_no_op", "new_create")
    os_val = a.get("object_state", "not_exists")
    if ifne == "specified" and os_val == "already_exists":
        a["if_not_exists_no_op"] = "no_op_notice"
    elif ifne == "specified" and os_val == "not_exists":
        a["if_not_exists_no_op"] = "new_create"
    elif ino == "no_op_notice":
        a["if_not_exists_clause"] = "specified"
        a["object_state"] = "already_exists"

    # --- zero_column_table <-> column_count -----------------------
    cc = a.get("column_count", "single_column")
    zct = a.get("zero_column_table", "has_columns")
    if cc == "zero_columns" or zct == "zero_columns":
        a["column_count"] = "zero_columns"
        a["zero_column_table"] = "zero_columns"
    else:
        a["zero_column_table"] = "has_columns"

    # --- table_form <-> statement_branch --------------------------
    tf = a.get("table_form", "regular")
    if tf in _TABLE_FORM_CONSUMER:
        a["statement_branch"] = _TABLE_FORM_BRANCH[tf]
    sb = a.get("statement_branch", _BRANCH_REGULAR)
    if sb == _BRANCH_PARTITION and tf == "regular":
        a["table_form"] = "partition_of"

    # --- schema_existence <-> table_name_shape --------------------
    se_schema = a.get("schema_existence", "schema_exists")
    if se_schema == "schema_not_exists":
        a["table_name_shape"] = "schema_qualified"

    # --- expected_status from failure count -----------------------
    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _baseline_assignments(
    obligation: CreateForeignTableFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["statement_branch"] = _ACTION_BRANCH[
        obligation.consumer_action_id
    ]
    if obligation.consumer_action_id in _TABLE_FORM_CONSUMER.values():
        for tf, action in _TABLE_FORM_CONSUMER.items():
            if action == obligation.consumer_action_id:
                assignments["table_form"] = tf
                break
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    failures = _count_baseline_failures(assignments)
    assignments["expected_status"] = (
        "failure" if failures > 0 else "success"
    )
    if len(assignments) != len(set(assignments)):
        raise CreateForeignTableFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateForeignTableFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateForeignTableFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_foreign_table_factor_loop_plan(
    repository_root: Path,
) -> CreateForeignTableFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_foreign_table_factor_loop_obligations(root)
    cases: list[CreateForeignTableFactorCase] = []
    delegated: list[CreateForeignTableFactorObligation] = []
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
            CreateForeignTableFactorCase(
                ordinal=ordinal,
                case_id=f"CREATEFOREIGNTABLE{ordinal:05d}",
                sql_filename=f"CREATEFOREIGNTABLE{ordinal:05d}.sql",
                object_prefix=f"createforeigntable_{ordinal:05d}_",
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
    plan = CreateForeignTableFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 96 or len(plan.delegated) != 0:
        raise CreateForeignTableFactorLoopError(
            "factor loop plan count drift"
        )
    if len({row.primary_obligation_id for row in plan.cases}) != 96:
        raise CreateForeignTableFactorLoopError(
            "local obligation mapping drift"
        )
    if len({row.sql_filename for row in plan.cases}) != 96:
        raise CreateForeignTableFactorLoopError("duplicate SQL filename")
    return plan


def compile_create_foreign_table_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateForeignTableFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateForeignTableFactorObligation(
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
    if len(rows) != 96:
        raise CreateForeignTableFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateForeignTableFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 5, "SFV": 91}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateForeignTableFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateForeignTableFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 96:
        raise CreateForeignTableFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreateForeignTableFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "CreateForeignTableFactorLoopError",
    "CreateForeignTableGrammarAction",
    "CreateForeignTableFactorObligation",
    "CreateForeignTableFactorCase",
    "CreateForeignTableFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_create_foreign_table_factor_loop_obligations",
    "build_create_foreign_table_factor_loop_plan",
    "_obligation_multiset_sha256",
]
