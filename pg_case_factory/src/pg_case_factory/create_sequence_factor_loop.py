"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE SEQUENCE.

Compiles the marginal ``GRM``/``SFV`` obligation ledger for ``CREATE
SEQUENCE`` (single synopsis branch).  Targets a ``pg_class`` relation
row (relkind ``S``).  Only ``OWNED BY table.column`` and
``same_name_conflict=same_name_table`` cases create tables (per-script
``DROP TABLE`` bookend); every other script is table-less-exempt.

The 70 canonical ``SFV`` rows are loaded from the shipped applicability
universe (``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CreateSequenceFactorLoopError(ValueError):
    """Raised when a frozen CREATE SEQUENCE obligation input drifts."""


@dataclass(frozen=True)
class CreateSequenceGrammarAction:
    """One official target action form of the CREATE SEQUENCE synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateSequenceFactorObligation:
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
class CreateSequenceFactorCase:
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
class CreateSequenceFactorLoopPlan:
    obligations: tuple[CreateSequenceFactorObligation, ...]
    cases: tuple[CreateSequenceFactorCase, ...]
    delegated: tuple[CreateSequenceFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-createsequence.html).
_BRANCH_DEFINE = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createsequence"

# A representative define action used as the baseline consumer for
# canonical factors not bound to one specific branch.
_REPRESENTATIVE_ACTION = "define_sequence"


def _canonical_consumer(row) -> str:
    """Map a canonical factor value to its target consumer action."""

    if row.factor == "statement_branch":
        return "define_sequence"
    if row.factor == "sequence_type":
        return "define_sequence"
    if row.factor == "object_state":
        return "define_sequence" if row.value == "not_exists" else (
            "define_duplicate"
        )
    if row.factor == "expected_status":
        return "define_sequence" if row.value == "success" else (
            "define_duplicate"
        )
    if row.factor == "as_data_type":
        return "define_sequence"
    if row.factor == "increment_direction":
        return "define_sequence"
    if row.factor == "increment_zero":
        return "define_zero_increment"
    if row.factor == "cycle_clause":
        return "define_sequence"
    if row.factor == "minvalue_maxvalue_setting":
        return "define_sequence"
    if row.factor == "minvalue_greater_than_maxvalue":
        return "define_min_gt_max"
    if row.factor == "start_value_setting":
        return "define_sequence"
    if row.factor == "start_out_of_range":
        return "define_start_out_of_range"
    if row.factor == "cache_value":
        return "define_sequence"
    if row.factor == "owned_by_clause":
        if row.value == "owned_by_column":
            return "define_owned_by_column"
        if row.value == "owned_by_none":
            return "define_owned_by_none"
        return "define_sequence"
    if row.factor == "owned_by_table_dependency":
        return "define_owned_by_column"
    if row.factor == "owned_by_different_owner":
        return "define_owned_by_different_owner"
    if row.factor == "owned_by_different_schema":
        return "define_owned_by_different_schema"
    if row.factor == "sequence_name_shape":
        if row.value == "schema_qualified":
            return "define_schema_qualified"
        if row.value == "quoted":
            return "define_quoted"
        if row.value == "reserved_word":
            return "define_reserved_word"
        if row.value == "non_existent":
            return "define_missing_schema"
        return "define_sequence"
    if row.factor == "schema_dependency":
        if row.value == "pg_catalog_reserved":
            return "define_pg_catalog"
        if row.value == "schema_not_exists":
            return "define_missing_schema"
        return "define_sequence"
    if row.factor == "privilege_level":
        if row.value == "non_creator_no_privilege":
            return "define_insufficient_priv"
        return "define_sequence"
    if row.factor == "insufficient_privilege":
        return "define_insufficient_priv"
    if row.factor == "if_not_exists_clause":
        return "define_sequence"
    if row.factor == "duplicate_sequence_name":
        if row.value == "with_IF_NOT_EXISTS_noop":
            return "define_if_not_exists_noop"
        return "define_duplicate"
    if row.factor == "same_name_conflict":
        if row.value == "same_name_table":
            return "define_same_name_table"
        return "define_same_name_view"
    if row.factor == "incompatible_data_type_values":
        return "define_smallint_overflow"
    if row.factor == "temporary_sequence_with_schema":
        return "define_temp_schema_illegal"
    if row.factor == "verification_mode":
        return "define_sequence"
    if row.factor == "cleanup_mode":
        return "define_sequence"
    return _REPRESENTATIVE_ACTION


# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("object_state", "already_exists"),
        ("expected_status", "failure"),
        ("duplicate_sequence_name", "without_IF_NOT_EXISTS_error"),
        ("schema_dependency", "pg_catalog_reserved"),
        ("schema_dependency", "schema_not_exists"),
        ("sequence_name_shape", "non_existent"),
        ("privilege_level", "non_creator_no_privilege"),
        ("insufficient_privilege", "no_CREATE_privilege"),
        ("owned_by_table_dependency", "table_column_not_exists"),
        ("owned_by_table_dependency", "different_owner"),
        ("owned_by_table_dependency", "different_schema"),
        ("owned_by_different_owner", "table_different_owner"),
        ("owned_by_different_schema", "table_different_schema"),
        ("same_name_conflict", "same_name_table"),
        ("same_name_conflict", "same_name_view"),
        ("incompatible_data_type_values", "smallint_overflow"),
        ("increment_zero", "zero_increment"),
        ("minvalue_greater_than_maxvalue", "min_greater_than_max"),
        ("start_out_of_range", "start_above_maxvalue"),
        ("start_out_of_range", "start_below_minvalue"),
        ("temporary_sequence_with_schema", "temp_with_schema_illegal"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("object_state", "already_exists"): (
        "42710",
        "duplicate_sequence_provisional",
    ),
    ("expected_status", "failure"): (
        "42710",
        "duplicate_sequence_provisional",
    ),
    ("duplicate_sequence_name", "without_IF_NOT_EXISTS_error"): (
        "42710",
        "duplicate_sequence_provisional",
    ),
    ("schema_dependency", "pg_catalog_reserved"): (
        "42939",
        "cannot_create_in_pg_catalog_provisional",
    ),
    ("schema_dependency", "schema_not_exists"): (
        "3F000",
        "invalid_schema_provisional",
    ),
    ("sequence_name_shape", "non_existent"): (
        "3F000",
        "invalid_schema_provisional",
    ),
    ("privilege_level", "non_creator_no_privilege"): (
        "42501",
        "insufficient_sequence_privilege_provisional",
    ),
    ("insufficient_privilege", "no_CREATE_privilege"): (
        "42501",
        "insufficient_sequence_privilege_provisional",
    ),
    ("owned_by_table_dependency", "table_column_not_exists"): (
        "42704",
        "undefined_table_provisional",
    ),
    ("owned_by_table_dependency", "different_owner"): (
        "42501",
        "sequence_owner_mismatch_provisional",
    ),
    ("owned_by_table_dependency", "different_schema"): (
        "42501",
        "sequence_schema_mismatch_provisional",
    ),
    ("owned_by_different_owner", "table_different_owner"): (
        "42501",
        "sequence_owner_mismatch_provisional",
    ),
    ("owned_by_different_schema", "table_different_schema"): (
        "42501",
        "sequence_schema_mismatch_provisional",
    ),
    ("same_name_conflict", "same_name_table"): (
        "42P07",
        "duplicate_table_provisional",
    ),
    ("same_name_conflict", "same_name_view"): (
        "42710",
        "duplicate_relation_provisional",
    ),
    ("incompatible_data_type_values", "smallint_overflow"): (
        "22023",
        "value_out_of_range_provisional",
    ),
    ("increment_zero", "zero_increment"): (
        "22023",
        "zero_increment_provisional",
    ),
    ("minvalue_greater_than_maxvalue", "min_greater_than_max"): (
        "22023",
        "minvalue_greater_than_maxvalue_provisional",
    ),
    ("start_out_of_range", "start_above_maxvalue"): (
        "22023",
        "start_above_maxvalue_provisional",
    ),
    ("start_out_of_range", "start_below_minvalue"): (
        "22023",
        "start_below_minvalue_provisional",
    ),
    ("temporary_sequence_with_schema", "temp_with_schema_illegal"): (
        "42601",
        "temp_sequence_schema_qualified_provisional",
    ),
}


def _load_grammar_actions() -> tuple[CreateSequenceGrammarAction, ...]:
    """Freeze every CREATE SEQUENCE synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "define_sequence",
            _BRANCH_DEFINE,
            "CREATE [TEMP|TEMPORARY|UNLOGGED] SEQUENCE [IF NOT EXISTS] name [AS type] [INCREMENT BY n] ...",
            "synopsis-define-sequence",
        ),
    )
    actions = [
        CreateSequenceGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise CreateSequenceFactorLoopError("action count drift")
    return tuple(actions)


def _compile_grammar_obligations() -> list[CreateSequenceFactorObligation]:
    rows: list[CreateSequenceFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateSequenceFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CSQ-GRM|{action.grammar_branch_id}|"
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
        raise CreateSequenceFactorLoopError("grammar obligation drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateSequenceFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_sequence")
    if len(catalog_rows) != 70:
        raise CreateSequenceFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[CreateSequenceFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateSequenceFactorObligation(
                ordinal=0,
                obligation_id=f"CSQ-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreateSequenceFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-sequence-factor-obligations-v1\n"
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


# Dense baseline defaults (all positive factor values).  Synthetic
# non-failure defaults are used for edge factors that only ship a
# failure value in the applicability universe.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_permanent",
    "sequence_type": "permanent",
    "object_state": "not_exists",
    "expected_status": "success",
    "as_data_type": "absent_default",
    "increment_direction": "ascending",
    "increment_zero": "nonzero_increment",
    "minvalue_maxvalue_setting": "absent_defaults",
    "minvalue_greater_than_maxvalue": "min_le_max",
    "start_value_setting": "absent_default",
    "start_out_of_range": "start_in_range",
    "cache_value": "absent_default",
    "cycle_clause": "absent_default",
    "owned_by_clause": "absent_default",
    "owned_by_table_dependency": "table_column_exists",
    "owned_by_different_owner": "same_owner",
    "owned_by_different_schema": "same_schema",
    "sequence_name_shape": "simple",
    "schema_dependency": "schema_exists",
    "privilege_level": "sequence_creator",
    "insufficient_privilege": "has_create_privilege",
    "if_not_exists_clause": "absent",
    "duplicate_sequence_name": "no_duplicate",
    "same_name_conflict": "no_conflict",
    "incompatible_data_type_values": "compatible_values",
    "temporary_sequence_with_schema": "temp_no_schema",
    "verification_mode": "pg_class_catalog_query",
    "cleanup_mode": "DROP_SEQUENCE_IF_EXISTS",
}


def _failure_conditions(a: dict[str, str]) -> list[str]:
    """Return the list of active failure condition names."""

    conditions: list[str] = []
    tos = a.get("object_state", "not_exists")
    ine = a.get("if_not_exists_clause", "absent")
    if tos == "already_exists" and ine != "present":
        conditions.append("duplicate")
    pl = a.get("privilege_level", "sequence_creator")
    ip = a.get("insufficient_privilege", "has_create_privilege")
    if pl == "non_creator_no_privilege" or ip == "no_CREATE_privilege":
        conditions.append("insufficient_privilege")
    ot = a.get("owned_by_table_dependency", "table_column_exists")
    if ot == "table_column_not_exists":
        conditions.append("missing_table")
    if ot == "different_owner" or a.get(
        "owned_by_different_owner"
    ) == "table_different_owner":
        conditions.append("different_owner")
    if ot == "different_schema" or a.get(
        "owned_by_different_schema"
    ) == "table_different_schema":
        conditions.append("different_schema")
    snc = a.get("same_name_conflict", "no_conflict")
    if snc == "same_name_table":
        conditions.append("name_conflict_table")
    if snc == "same_name_view":
        conditions.append("name_conflict_view")
    sd = a.get("schema_dependency", "schema_exists")
    if sd == "pg_catalog_reserved":
        conditions.append("pg_catalog_reserved")
    if sd == "schema_not_exists" or a.get(
        "sequence_name_shape"
    ) == "non_existent":
        conditions.append("missing_schema")
    if a.get("incompatible_data_type_values") == "smallint_overflow":
        conditions.append("smallint_overflow")
    if a.get("increment_zero") == "zero_increment":
        conditions.append("zero_increment")
    if a.get("minvalue_greater_than_maxvalue") == "min_greater_than_max":
        conditions.append("min_gt_max")
    sor = a.get("start_out_of_range", "start_in_range")
    if sor == "start_above_maxvalue":
        conditions.append("start_above")
    if sor == "start_below_minvalue":
        conditions.append("start_below")
    if a.get("temporary_sequence_with_schema") == "temp_with_schema_illegal":
        conditions.append("temp_schema_qualified")
    return conditions


_FAILURE_SQLSTATE: dict[str, tuple[str, str]] = {
    "duplicate": ("42710", "duplicate_sequence_provisional"),
    "insufficient_privilege": (
        "42501",
        "insufficient_sequence_privilege_provisional",
    ),
    "missing_table": ("42704", "undefined_table_provisional"),
    "different_owner": (
        "42501",
        "sequence_owner_mismatch_provisional",
    ),
    "different_schema": (
        "42501",
        "sequence_schema_mismatch_provisional",
    ),
    "name_conflict_table": ("42P07", "duplicate_table_provisional"),
    "name_conflict_view": ("42710", "duplicate_relation_provisional"),
    "pg_catalog_reserved": (
        "42939",
        "cannot_create_in_pg_catalog_provisional",
    ),
    "missing_schema": ("3F000", "invalid_schema_provisional"),
    "smallint_overflow": ("22023", "value_out_of_range_provisional"),
    "zero_increment": ("22023", "zero_increment_provisional"),
    "min_gt_max": (
        "22023",
        "minvalue_greater_than_maxvalue_provisional",
    ),
    "start_above": ("22023", "start_above_maxvalue_provisional"),
    "start_below": ("22023", "start_below_minvalue_provisional"),
    "temp_schema_qualified": (
        "42601",
        "temp_sequence_schema_qualified_provisional",
    ),
}


def _count_baseline_failures(a: dict[str, str]) -> int:
    return len(_failure_conditions(a))


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive overlapping boundary factors from the primary value.

    object_state ↔ duplicate_sequence_name ↔ if_not_exists_clause:
      already_exists + absent IF NOT EXISTS → without_IF_NOT_EXISTS_error
      already_exists + present IF NOT EXISTS → with_IF_NOT_EXISTS_noop (no failure)
    privilege_level ↔ insufficient_privilege (bidirectional)
    owned_by_clause ↔ owned_by_table_dependency ↔ owned_by_different_*
    schema_dependency ↔ sequence_name_shape (non_existent/schema_qualified)
    sequence_type ↔ statement_branch ↔ if_not_exists_clause
    temporary_sequence_with_schema → sequence_type=temporary + schema_qualified
    expected_status=failure → representative duplicate
    """

    # --- object_state ↔ duplicate_sequence_name ↔ if_not_exists ---
    tos = a.get("object_state", "not_exists")
    ine = a.get("if_not_exists_clause", "absent")
    dsn = a.get("duplicate_sequence_name", "no_duplicate")
    if tos == "already_exists":
        if ine == "present":
            a["duplicate_sequence_name"] = "with_IF_NOT_EXISTS_noop"
        else:
            a["duplicate_sequence_name"] = "without_IF_NOT_EXISTS_error"
            a["if_not_exists_clause"] = "absent"
    if dsn == "with_IF_NOT_EXISTS_noop":
        a["object_state"] = "already_exists"
        a["if_not_exists_clause"] = "present"
    if dsn == "without_IF_NOT_EXISTS_error":
        a["object_state"] = "already_exists"
        a["if_not_exists_clause"] = "absent"

    # --- expected_status=failure → representative duplicate ---
    es = a.get("expected_status", "success")
    if es == "failure":
        if a.get("object_state", "not_exists") != "already_exists":
            a["object_state"] = "already_exists"
        a["duplicate_sequence_name"] = "without_IF_NOT_EXISTS_error"
        a["if_not_exists_clause"] = "absent"

    # --- privilege_level ↔ insufficient_privilege ---
    pl = a.get("privilege_level", "sequence_creator")
    if pl == "non_creator_no_privilege":
        a["insufficient_privilege"] = "no_CREATE_privilege"
    ip = a.get("insufficient_privilege", "has_create_privilege")
    if ip == "no_CREATE_privilege":
        a["privilege_level"] = "non_creator_no_privilege"

    # --- owned_by_clause ↔ owned_by_table_dependency ---
    obc = a.get("owned_by_clause", "absent_default")
    otd = a.get("owned_by_table_dependency", "table_column_exists")
    if otd in ("table_column_not_exists", "different_owner",
               "different_schema"):
        a["owned_by_clause"] = "owned_by_column"
    if a.get("owned_by_different_owner") == "table_different_owner":
        a["owned_by_table_dependency"] = "different_owner"
        a["owned_by_clause"] = "owned_by_column"
    if a.get("owned_by_different_schema") == "table_different_schema":
        a["owned_by_table_dependency"] = "different_schema"
        a["owned_by_clause"] = "owned_by_column"
    if obc == "owned_by_column" and otd == "table_column_exists":
        a["owned_by_table_dependency"] = "table_column_exists"

    # --- schema_dependency ↔ sequence_name_shape ---
    sd = a.get("schema_dependency", "schema_exists")
    if sd == "schema_not_exists":
        a["sequence_name_shape"] = "non_existent"
    if sd == "pg_catalog_reserved":
        a["sequence_name_shape"] = "schema_qualified"
    if a.get("sequence_name_shape") == "non_existent":
        a["schema_dependency"] = "schema_not_exists"

    # --- temporary_sequence_with_schema → temp + schema_qualified ---
    if a.get("temporary_sequence_with_schema") == "temp_with_schema_illegal":
        a["sequence_type"] = "temporary"
        a["sequence_name_shape"] = "schema_qualified"

    # --- sequence_type ↔ statement_branch ↔ if_not_exists ---
    st = a.get("sequence_type", "permanent")
    ine = a.get("if_not_exists_clause", "absent")
    sb = a.get("statement_branch", "branch_permanent")
    if sb.startswith("branch_"):
        if sb == "branch_permanent":
            a["sequence_type"] = "permanent"
            a["if_not_exists_clause"] = "absent"
        elif sb == "branch_temp":
            a["sequence_type"] = "temporary_short"
            a["if_not_exists_clause"] = "absent"
        elif sb == "branch_temporary":
            a["sequence_type"] = "temporary"
            a["if_not_exists_clause"] = "absent"
        elif sb == "branch_unlogged":
            a["sequence_type"] = "unlogged"
            a["if_not_exists_clause"] = "absent"
        elif sb == "branch_if_not_exists_permanent":
            a["sequence_type"] = "permanent"
            a["if_not_exists_clause"] = "present"
        elif sb == "branch_if_not_exists_temporary":
            a["sequence_type"] = "temporary"
            a["if_not_exists_clause"] = "present"
    else:
        if st == "permanent":
            a["statement_branch"] = (
                "branch_if_not_exists_permanent"
                if ine == "present" else "branch_permanent"
            )
        elif st == "temporary":
            a["statement_branch"] = (
                "branch_if_not_exists_temporary"
                if ine == "present" else "branch_temporary"
            )
        elif st == "temporary_short":
            a["statement_branch"] = "branch_temp"
        elif st == "unlogged":
            a["statement_branch"] = "branch_unlogged"

    # --- Derive expected_status from failure count ---
    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _baseline_assignments(
    obligation: CreateSequenceFactorObligation,
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
        raise CreateSequenceFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateSequenceFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateSequenceFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_sequence_factor_loop_plan(
    repository_root: Path,
) -> CreateSequenceFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_sequence_factor_loop_obligations(root)
    cases: list[CreateSequenceFactorCase] = []
    delegated: list[CreateSequenceFactorObligation] = []
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
            CreateSequenceFactorCase(
                ordinal=ordinal,
                case_id=f"CREATESEQUENCE{ordinal:05d}",
                sql_filename=f"CREATESEQUENCE{ordinal:05d}.sql",
                object_prefix=f"createsequence_{ordinal:05d}_",
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
    plan = CreateSequenceFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 71 or len(plan.delegated) != 0:
        raise CreateSequenceFactorLoopError(
            "factor loop plan count drift"
        )
    if len({row.primary_obligation_id for row in plan.cases}) != 71:
        raise CreateSequenceFactorLoopError(
            "local obligation mapping drift"
        )
    if len({row.sql_filename for row in plan.cases}) != 71:
        raise CreateSequenceFactorLoopError("duplicate SQL filename")
    return plan


def compile_create_sequence_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateSequenceFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateSequenceFactorObligation(
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
        raise CreateSequenceFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateSequenceFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 70}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateSequenceFactorLoopError("kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateSequenceFactorLoopError("delegated count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 71:
        raise CreateSequenceFactorLoopError("local obligation drift")
    allowed = {"covered", "expected_failure", "delegated"}
    if any(row.disposition not in allowed for row in rows):
        raise CreateSequenceFactorLoopError("unknown disposition")
    return rows


__all__ = [
    "CreateSequenceFactorLoopError",
    "CreateSequenceGrammarAction",
    "CreateSequenceFactorObligation",
    "CreateSequenceFactorCase",
    "CreateSequenceFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "_BASELINE_DEFAULTS",
    "_FAILURE_SQLSTATE",
    "_failure_conditions",
    "compile_create_sequence_factor_loop_obligations",
    "build_create_sequence_factor_loop_plan",
    "_obligation_multiset_sha256",
]
