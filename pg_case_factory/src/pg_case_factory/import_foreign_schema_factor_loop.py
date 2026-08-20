"""Factor-value-loop obligation ledger for PostgreSQL 18.4 IMPORT FOREIGN SCHEMA.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``IMPORT FOREIGN SCHEMA`` (create foreign tables from a remote schema).
The statement has a single official synopsis branch:
``IMPORT FOREIGN SCHEMA remote_schema [ LIMIT TO | EXCEPT ] ( table_list )
FROM SERVER name INTO schema [ OPTIONS (...) ]``.  The statement creates
foreign tables (``pg_class.relkind='f'``) catalogued in ``pg_catalog.pg_class``,
so the catalog probe joins ``pg_class`` to ``pg_namespace`` on the local
schema name.

IMPORT FOREIGN SCHEMA creates FOREIGN TABLES (not ``CREATE TABLE``), so the
``audit_complete_table_script`` bookend gate does NOT trigger (class-2 N/A,
like ``drop_user_mapping``).  Cleanup uses ``DROP FOREIGN TABLE`` /
``DROP SCHEMA`` / ``DROP SERVER`` (no ``DROP TABLE`` bookend).

Each local obligation becomes exactly one regress program.  The 56 canonical
``SFV`` rows are loaded from the shipped applicability universe.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class ImportForeignSchemaFactorLoopError(ValueError):
    """Raised when a frozen IMPORT FOREIGN SCHEMA obligation input drifts."""


@dataclass(frozen=True)
class ImportForeignSchemaGrammarAction:
    """One official target action form of the IMPORT FOREIGN SCHEMA synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class ImportForeignSchemaFactorObligation:
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
class ImportForeignSchemaFactorCase:
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
class ImportForeignSchemaFactorLoopPlan:
    obligations: tuple[ImportForeignSchemaFactorObligation, ...]
    cases: tuple[ImportForeignSchemaFactorCase, ...]
    delegated: tuple[ImportForeignSchemaFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-importforeignschema.html).
_BRANCH_DEFINE = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-importforeignschema"

_REPRESENTATIVE_ACTION = "import_foreign_schema_statement"


def _canonical_consumer(row) -> str:
    """Map a canonical factor value to its target consumer action."""

    f = row.factor
    v = row.value
    if f == "expected_status":
        if v == "failure":
            return "import_foreign_schema_failure"
        return "import_foreign_schema_statement"
    if f == "statement_branch":
        if v == "branch_except":
            return "import_foreign_schema_except"
        if v == "branch_limit_to":
            return "import_foreign_schema_limit_to"
        return "import_foreign_schema_statement"
    if f == "filter_clause":
        if v == "except":
            return "import_foreign_schema_except_filter"
        if v == "limit_to":
            return "import_foreign_schema_limit_to_filter"
        return "import_foreign_schema_statement"
    if f == "local_schema_name_shape":
        if v == "nonexistent_schema":
            return "import_foreign_schema_missing_local_schema"
        if v == "quoted_id":
            return "import_foreign_schema_quoted_local_schema"
        return "import_foreign_schema_statement"
    if f == "remote_schema_name_shape":
        if v == "quoted_id":
            return "import_foreign_schema_quoted_remote_schema"
        return "import_foreign_schema_statement"
    if f == "server_name_shape":
        if v == "nonexistent_server":
            return "import_foreign_schema_missing_server_name"
        return "import_foreign_schema_statement"
    if f == "table_name_shape":
        if v == "nonexistent_table":
            return "import_foreign_schema_missing_table_name"
        return "import_foreign_schema_statement"
    if f == "privilege_level":
        if v == "no_create":
            return "import_foreign_schema_no_create"
        if v == "no_usage":
            return "import_foreign_schema_no_usage"
        if v == "usage_and_create":
            return "import_foreign_schema_usage_and_create"
        return "import_foreign_schema_statement"
    if f == "schema_existence":
        if v == "schema_not_exists":
            return "import_foreign_schema_schema_absent"
        return "import_foreign_schema_statement"
    if f == "server_existence":
        if v == "server_not_exists":
            return "import_foreign_schema_server_absent"
        return "import_foreign_schema_statement"
    if f == "fdw_dependency":
        if v == "fdw_not_support_import":
            return "import_foreign_schema_fdw_no_import"
        return "import_foreign_schema_statement"
    if f == "fdw_import_capability":
        if v == "not_supports_import":
            return "import_foreign_schema_fdw_no_capability"
        return "import_foreign_schema_statement"
    if f == "fdw_not_support_import":
        if v == "fdw_not_supports":
            return "import_foreign_schema_fdw_not_supports"
        return "import_foreign_schema_statement"
    if f == "server_dependency":
        if v == "invalid_server":
            return "import_foreign_schema_invalid_server"
        if v == "no_usage_privilege":
            return "import_foreign_schema_no_usage_dep"
        return "import_foreign_schema_statement"
    if f == "object_state":
        if v == "not_exists":
            return "import_foreign_schema_object_absent"
        return "import_foreign_schema_statement"
    if f == "nonexistent_local_schema":
        if v == "schema_missing":
            return "import_foreign_schema_local_schema_missing"
        return "import_foreign_schema_statement"
    if f == "nonexistent_server":
        if v == "server_missing":
            return "import_foreign_schema_server_missing"
        return "import_foreign_schema_statement"
    if f == "no_create_privilege":
        if v == "lacks_create":
            return "import_foreign_schema_lacks_create"
        return "import_foreign_schema_statement"
    if f == "no_usage_privilege":
        if v == "lacks_usage":
            return "import_foreign_schema_lacks_usage"
        return "import_foreign_schema_statement"
    if f == "duplicate_foreign_table":
        if v == "name_conflict":
            return "import_foreign_schema_name_conflict"
        return "import_foreign_schema_statement"
    if f == "table_name_mismatch":
        if v == "table_not_exists_remote":
            return "import_foreign_schema_remote_table_missing"
        return "import_foreign_schema_statement"
    if f == "options_clause":
        if v == "specified":
            return "import_foreign_schema_with_options"
        return "import_foreign_schema_statement"
    return _REPRESENTATIVE_ACTION


# Canonical (factor, value) pairs that the declared matrix marks as failure
# (provisional sqlstates — DB phase verifies on PG 18.4).  Only the declared
# expected_status=failure is a baseline expected_failure; every other
# canonical value is "covered" (marginal 1:1) and its failure interaction is
# exercised by the bounded extension module.
_SFV_FAILURE_VALUES = frozenset({("expected_status", "failure")})

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
# The baseline only looks up the expected_status=failure entry; the extra
# entries are consumed by the extension module's crossed-negative attribution.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "import_foreign_schema_declared_failure_provisional",
    ),
    ("fdw_dependency", "fdw_not_support_import"): (
        "42809",
        "fdw_not_support_import_provisional",
    ),
    ("fdw_import_capability", "not_supports_import"): (
        "42809",
        "fdw_no_import_capability_provisional",
    ),
    ("fdw_not_support_import", "fdw_not_supports"): (
        "42809",
        "fdw_not_supports_provisional",
    ),
    ("local_schema_name_shape", "nonexistent_schema"): (
        "3F001",
        "local_schema_missing_provisional",
    ),
    ("nonexistent_local_schema", "schema_missing"): (
        "3F001",
        "local_schema_missing_provisional",
    ),
    ("schema_existence", "schema_not_exists"): (
        "3F001",
        "schema_not_exists_provisional",
    ),
    ("nonexistent_server", "server_missing"): (
        "42704",
        "server_missing_provisional",
    ),
    ("server_existence", "server_not_exists"): (
        "42704",
        "server_not_exists_provisional",
    ),
    ("server_name_shape", "nonexistent_server"): (
        "42704",
        "server_name_missing_provisional",
    ),
    ("server_dependency", "invalid_server"): (
        "42704",
        "invalid_server_provisional",
    ),
    ("server_dependency", "no_usage_privilege"): (
        "42501",
        "no_usage_privilege_provisional",
    ),
    ("privilege_level", "no_create"): (
        "42501",
        "no_create_privilege_provisional",
    ),
    ("privilege_level", "no_usage"): (
        "42501",
        "no_usage_privilege_level_provisional",
    ),
    ("no_create_privilege", "lacks_create"): (
        "42501",
        "lacks_create_provisional",
    ),
    ("no_usage_privilege", "lacks_usage"): (
        "42501",
        "lacks_usage_provisional",
    ),
    ("table_name_shape", "nonexistent_table"): (
        "42P01",
        "nonexistent_table_provisional",
    ),
    ("table_name_mismatch", "table_not_exists_remote"): (
        "42P01",
        "remote_table_missing_provisional",
    ),
    ("object_state", "not_exists"): (
        "42P01",
        "object_not_exists_provisional",
    ),
}


def _load_grammar_actions() -> tuple[ImportForeignSchemaGrammarAction, ...]:
    """Freeze every IMPORT FOREIGN SCHEMA synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "import_foreign_schema_statement",
            _BRANCH_DEFINE,
            (
                "IMPORT FOREIGN SCHEMA remote_schema "
                "[ LIMIT TO | EXCEPT ] ( table_list ) "
                "FROM SERVER name INTO schema [ OPTIONS (...) ]"
            ),
            "synopsis-import-foreign-schema-statement",
        ),
    )
    actions = [
        ImportForeignSchemaGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 1:
        raise ImportForeignSchemaFactorLoopError(
            "import foreign schema action count drift"
        )
    return tuple(actions)


def _compile_grammar_obligations() -> (
    list[ImportForeignSchemaFactorObligation]
):
    rows: list[ImportForeignSchemaFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            ImportForeignSchemaFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"IMPORTFOREIGNSCHEMA-GRM|{action.grammar_branch_id}|"
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
        raise ImportForeignSchemaFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[ImportForeignSchemaFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("import_foreign_schema")
    if len(catalog_rows) != 56:
        raise ImportForeignSchemaFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[ImportForeignSchemaFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            ImportForeignSchemaFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"IMPORTFOREIGNSCHEMA-SFV|{row.row_id}|{consumer}"
                ),
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
    rows: tuple[ImportForeignSchemaFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"import-foreign-schema-factor-obligations-v1\n"
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


# Dense baseline defaults (all positive factor values).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_basic",
    "expected_status": "success",
    "filter_clause": "no_filter",
    "fdw_dependency": "fdw_supports_import",
    "fdw_import_capability": "supports_import",
    "fdw_not_support_import": "fdw_supports",
    "options_clause": "omitted",
    "server_dependency": "valid_server",
    "cleanup_mode": "drop_foreign_tables",
    "verification_mode": "pg_class_catalog_query",
    "local_schema_name_shape": "simple_id",
    "remote_schema_name_shape": "simple_id",
    "server_name_shape": "simple_id",
    "table_name_shape": "simple_id",
    "privilege_level": "superuser",
    "schema_existence": "schema_exists",
    "server_existence": "server_exists",
    "object_state": "exists",
    "nonexistent_local_schema": "schema_exists",
    "nonexistent_server": "server_exists",
    "no_create_privilege": "has_create",
    "no_usage_privilege": "has_usage",
    "duplicate_foreign_table": "no_conflict",
    "table_name_mismatch": "table_exists_remote",
}


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive expected_status from the failure count."""

    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _baseline_assignments(
    obligation: ImportForeignSchemaFactorObligation,
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
        raise ImportForeignSchemaFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: ImportForeignSchemaFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise ImportForeignSchemaFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_import_foreign_schema_factor_loop_plan(
    repository_root: Path,
) -> ImportForeignSchemaFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_import_foreign_schema_factor_loop_obligations(
        root
    )
    cases: list[ImportForeignSchemaFactorCase] = []
    delegated: list[ImportForeignSchemaFactorObligation] = []
    for obligation in obligations:
        if obligation.disposition == "delegated":
            delegated.append(obligation)
            continue
        ordinal = len(cases) + 1
        if obligation.disposition == "expected_failure":
            sqlstate, failure_reason = _expected_failure_details(
                obligation
            )
            outcome = "expected_failure"
        else:
            outcome = "success"
            sqlstate = "00000"
            failure_reason = None
        cases.append(
            ImportForeignSchemaFactorCase(
                ordinal=ordinal,
                case_id=f"IMPORTFOREIGNSCHEMA{ordinal:05d}",
                sql_filename=f"IMPORTFOREIGNSCHEMA{ordinal:05d}.sql",
                object_prefix=f"importforeignschema_{ordinal:05d}_",
                primary_obligation_id=obligation.obligation_id,
                kind=obligation.kind,
                factor_key=obligation.factor_key,
                factor_value=obligation.value,
                consumer_action_id=obligation.consumer_action_id,
                outcome=outcome,
                expected_sqlstate=sqlstate,
                expected_failure_reason=failure_reason,
                baseline_assignments=_baseline_assignments(
                    obligation
                ),
                execution_profile="serial_sql",
            )
        )
    plan = ImportForeignSchemaFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 57 or len(plan.delegated) != 0:
        raise ImportForeignSchemaFactorLoopError(
            "factor loop plan count drift"
        )
    if (
        len({row.primary_obligation_id for row in plan.cases})
        != 57
    ):
        raise ImportForeignSchemaFactorLoopError(
            "local obligation mapping drift"
        )
    if (
        len({row.sql_filename for row in plan.cases}) != 57
    ):
        raise ImportForeignSchemaFactorLoopError(
            "duplicate SQL filename"
        )
    return plan


def compile_import_foreign_schema_factor_loop_obligations(
    repository_root: Path,
) -> tuple[ImportForeignSchemaFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        ImportForeignSchemaFactorObligation(
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
    if len(rows) != 57:
        raise ImportForeignSchemaFactorLoopError(
            "obligation count drift"
        )
    if len({row.obligation_id for row in rows}) != len(rows):
        raise ImportForeignSchemaFactorLoopError(
            "duplicate obligation id"
        )
    expected_kind_counts = {"GRM": 1, "SFV": 56}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise ImportForeignSchemaFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise ImportForeignSchemaFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 57:
        raise ImportForeignSchemaFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise ImportForeignSchemaFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "ImportForeignSchemaFactorLoopError",
    "ImportForeignSchemaGrammarAction",
    "ImportForeignSchemaFactorObligation",
    "ImportForeignSchemaFactorCase",
    "ImportForeignSchemaFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_import_foreign_schema_factor_loop_obligations",
    "build_import_foreign_schema_factor_loop_plan",
    "_obligation_multiset_sha256",
    "_BASELINE_DEFAULTS",
]
