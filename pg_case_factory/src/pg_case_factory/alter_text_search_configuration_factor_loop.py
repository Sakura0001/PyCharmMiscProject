"""Factor-value-loop obligation ledger for PostgreSQL 18.4 ALTER TEXT SEARCH CONFIGURATION.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``ALTER TEXT SEARCH CONFIGURATION``.  ALTER TEXT SEARCH CONFIGURATION is a
PostgreSQL text-search DDL statement with 8 official synopsis branches:
ADD MAPPING, ALTER MAPPING, ALTER MAPPING REPLACE, ALTER MAPPING FOR
REPLACE, DROP MAPPING, RENAME TO, OWNER TO, and SET SCHEMA.  The statement
requires the executor to be the configuration's owner (superusers
implicitly qualify) and mutates ``pg_catalog.pg_ts_config`` /
``pg_catalog.pg_ts_config_map`` catalog rows (not ``pg_class`` relations),
so column/table/relation coverage is ``not_applicable`` and there is no
``INV`` block.

Each local obligation becomes exactly one regress program.  Because the
inventory declares no ``transaction_outcome`` factor, there are no
``RISK`` obligations.

The grammar ledger is self-contained: the 8 synopsis actions are frozen
inline.  The 81 canonical ``SFV`` rows are loaded from the shipped
applicability universe (``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class AlterTextSearchConfigurationFactorLoopError(ValueError):
    """Raised when a frozen ALTER TEXT SEARCH CONFIGURATION obligation input drifts."""


@dataclass(frozen=True)
class AlterTextSearchConfigurationGrammarAction:
    """One official target action form of the ALTER TEXT SEARCH CONFIGURATION synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class AlterTextSearchConfigurationFactorObligation:
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
class AlterTextSearchConfigurationFactorCase:
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
class AlterTextSearchConfigurationFactorLoopPlan:
    obligations: tuple[AlterTextSearchConfigurationFactorObligation, ...]
    cases: tuple[AlterTextSearchConfigurationFactorCase, ...]
    delegated: tuple[AlterTextSearchConfigurationFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-altertsconfiguration.html).
_BRANCH_ADD_MAPPING = "branch_add_mapping"
_BRANCH_ALTER_MAPPING = "branch_alter_mapping"
_BRANCH_ALTER_MAPPING_REPLACE = "branch_alter_mapping_replace"
_BRANCH_ALTER_MAPPING_FOR_REPLACE = "branch_alter_mapping_for_replace"
_BRANCH_DROP_MAPPING = "branch_drop_mapping"
_BRANCH_RENAME = "branch_rename"
_BRANCH_OWNER = "branch_owner"
_BRANCH_SET_SCHEMA = "branch_set_schema"

_DOC_SOURCE = "postgresql-18.4-doc:sql-altertsconfiguration"

# A representative branch_rename action used as the baseline consumer for
# canonical factors that are not bound to one specific branch.  RENAME TO
# is simple, owner-only, and needs no dictionary dependency.
_REPRESENTATIVE_ACTION = "rename"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_ADD_MAPPING: "add_mapping",
    _BRANCH_ALTER_MAPPING: "alter_mapping",
    _BRANCH_ALTER_MAPPING_REPLACE: "alter_mapping_replace",
    _BRANCH_ALTER_MAPPING_FOR_REPLACE: "alter_mapping_for_replace",
    _BRANCH_DROP_MAPPING: "drop_mapping",
    _BRANCH_RENAME: "rename",
    _BRANCH_OWNER: "owner",
    _BRANCH_SET_SCHEMA: "set_schema",
}

# alter_action value -> target action (value-dependent consumer).
_ALTER_ACTION_CONSUMER = {
    "add_mapping": "add_mapping",
    "alter_mapping": "alter_mapping",
    "alter_mapping_replace": "alter_mapping_replace",
    "alter_mapping_for_replace": "alter_mapping_for_replace",
    "drop_mapping": "drop_mapping",
    "rename": "rename",
    "owner": "owner",
    "set_schema": "set_schema",
}

# Canonical factor -> the action where the value is observable.  Factors
# whose consumer depends on the value (statement_branch, alter_action) are
# resolved in :func:`_canonical_consumer`.
_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "alter_action": _REPRESENTATIVE_ACTION,
    "if_exists_clause": "drop_mapping",
    "owner_target": "owner",
    "dictionary_existence": "add_mapping",
    "token_type_existence": "drop_mapping",
    "config_name_shape": _REPRESENTATIVE_ACTION,
    "new_name_shape": "rename",
    "owner_name_shape": "owner",
    "schema_name_shape": "set_schema",
    "dictionary_name_shape": "add_mapping",
    "token_type_name_shape": "drop_mapping",
    "privilege_level": _REPRESENTATIVE_ACTION,
    "role_existence": "owner",
    "schema_existence": "set_schema",
    "dictionary_dependency": "add_mapping",
    "nonexistent_config": _REPRESENTATIVE_ACTION,
    "nonexistent_dictionary": "add_mapping",
    "nonexistent_token_type_mapping": "drop_mapping",
    "duplicate_new_name": "rename",
    "nonexistent_owner_role": "owner",
    "nonexistent_target_schema": "set_schema",
    "non_owner_attempt": _REPRESENTATIVE_ACTION,
    "drop_mapping_without_if_exists": "drop_mapping",
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "not_exists"),
        ("nonexistent_config", "config_missing"),
        ("config_name_shape", "nonexistent_name"),
        ("dictionary_existence", "dictionary_not_exists"),
        ("dictionary_dependency", "dictionary_missing"),
        ("nonexistent_dictionary", "dictionary_missing"),
        ("dictionary_name_shape", "nonexistent_name"),
        ("privilege_level", "non_owner"),
        ("non_owner_attempt", "non_owner_execution"),
        ("role_existence", "role_not_exists"),
        ("nonexistent_owner_role", "role_missing"),
        ("owner_name_shape", "nonexistent_role"),
        ("schema_existence", "schema_not_exists"),
        ("nonexistent_target_schema", "schema_missing"),
        ("schema_name_shape", "nonexistent_schema"),
        ("duplicate_new_name", "same_name_conflict"),
        ("new_name_shape", "duplicate_name"),
        ("token_type_existence", "token_type_not_mapped"),
        ("nonexistent_token_type_mapping", "mapping_missing"),
        ("token_type_name_shape", "invalid_token_type"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "config_does_not_exist_provisional",
    ),
    ("object_state", "not_exists"): (
        "42704",
        "config_does_not_exist_provisional",
    ),
    ("nonexistent_config", "config_missing"): (
        "42704",
        "config_does_not_exist_provisional",
    ),
    ("config_name_shape", "nonexistent_name"): (
        "42704",
        "config_does_not_exist_provisional",
    ),
    ("dictionary_existence", "dictionary_not_exists"): (
        "42704",
        "dictionary_does_not_exist_provisional",
    ),
    ("dictionary_dependency", "dictionary_missing"): (
        "42704",
        "dictionary_does_not_exist_provisional",
    ),
    ("nonexistent_dictionary", "dictionary_missing"): (
        "42704",
        "dictionary_does_not_exist_provisional",
    ),
    ("dictionary_name_shape", "nonexistent_name"): (
        "42704",
        "dictionary_does_not_exist_provisional",
    ),
    ("privilege_level", "non_owner"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("non_owner_attempt", "non_owner_execution"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("role_existence", "role_not_exists"): (
        "42704",
        "role_does_not_exist_provisional",
    ),
    ("nonexistent_owner_role", "role_missing"): (
        "42704",
        "role_does_not_exist_provisional",
    ),
    ("owner_name_shape", "nonexistent_role"): (
        "42704",
        "role_does_not_exist_provisional",
    ),
    ("schema_existence", "schema_not_exists"): (
        "3F000",
        "schema_does_not_exist_provisional",
    ),
    ("nonexistent_target_schema", "schema_missing"): (
        "3F000",
        "schema_does_not_exist_provisional",
    ),
    ("schema_name_shape", "nonexistent_schema"): (
        "3F000",
        "schema_does_not_exist_provisional",
    ),
    ("duplicate_new_name", "same_name_conflict"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("new_name_shape", "duplicate_name"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("token_type_existence", "token_type_not_mapped"): (
        "42704",
        "token_type_not_mapped_provisional",
    ),
    ("nonexistent_token_type_mapping", "mapping_missing"): (
        "42704",
        "token_type_not_mapped_provisional",
    ),
    ("token_type_name_shape", "invalid_token_type"): (
        "42704",
        "token_type_does_not_exist_provisional",
    ),
}


def _load_grammar_actions() -> (
    tuple[AlterTextSearchConfigurationGrammarAction, ...]
):
    """Freeze every ALTER TEXT SEARCH CONFIGURATION synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "add_mapping",
            _BRANCH_ADD_MAPPING,
            "ALTER TEXT SEARCH CONFIGURATION name ADD MAPPING FOR token_type [, ...] WITH dictionary_name [, ...]",
            "synopsis-add-mapping",
        ),
        (
            "alter_mapping",
            _BRANCH_ALTER_MAPPING,
            "ALTER TEXT SEARCH CONFIGURATION name ALTER MAPPING FOR token_type [, ...] WITH dictionary_name [, ...]",
            "synopsis-alter-mapping",
        ),
        (
            "alter_mapping_replace",
            _BRANCH_ALTER_MAPPING_REPLACE,
            "ALTER TEXT SEARCH CONFIGURATION name ALTER MAPPING REPLACE old_dictionary WITH new_dictionary",
            "synopsis-alter-mapping-replace",
        ),
        (
            "alter_mapping_for_replace",
            _BRANCH_ALTER_MAPPING_FOR_REPLACE,
            "ALTER TEXT SEARCH CONFIGURATION name ALTER MAPPING FOR token_type [, ...] REPLACE old_dictionary WITH new_dictionary",
            "synopsis-alter-mapping-for-replace",
        ),
        (
            "drop_mapping",
            _BRANCH_DROP_MAPPING,
            "ALTER TEXT SEARCH CONFIGURATION name DROP MAPPING [ IF EXISTS ] FOR token_type [, ...]",
            "synopsis-drop-mapping",
        ),
        (
            "rename",
            _BRANCH_RENAME,
            "ALTER TEXT SEARCH CONFIGURATION name RENAME TO new_name",
            "synopsis-rename",
        ),
        (
            "owner",
            _BRANCH_OWNER,
            "ALTER TEXT SEARCH CONFIGURATION name OWNER TO { new_owner | CURRENT_ROLE | CURRENT_USER | SESSION_USER }",
            "synopsis-owner",
        ),
        (
            "set_schema",
            _BRANCH_SET_SCHEMA,
            "ALTER TEXT SEARCH CONFIGURATION name SET SCHEMA new_schema",
            "synopsis-set-schema",
        ),
    )
    actions = [
        AlterTextSearchConfigurationGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 8:
        raise AlterTextSearchConfigurationFactorLoopError(
            "alter text search configuration action count drift"
        )
    return tuple(actions)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterTextSearchConfigurationFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "alter_action":
        try:
            return _ALTER_ACTION_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterTextSearchConfigurationFactorLoopError(
                f"unknown alter_action value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise AlterTextSearchConfigurationFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> (
    list[AlterTextSearchConfigurationFactorObligation]
):
    rows: list[AlterTextSearchConfigurationFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            AlterTextSearchConfigurationFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"ATSC-GRM|{action.grammar_branch_id}|"
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
        raise AlterTextSearchConfigurationFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[AlterTextSearchConfigurationFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("alter_text_search_configuration")
    if len(catalog_rows) != 81:
        raise AlterTextSearchConfigurationFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[AlterTextSearchConfigurationFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            AlterTextSearchConfigurationFactorObligation(
                ordinal=0,
                obligation_id=f"ATSC-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[AlterTextSearchConfigurationFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"alter-text-search-configuration-factor-obligations-v1\n"
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
    "add_mapping": _BRANCH_ADD_MAPPING,
    "alter_mapping": _BRANCH_ALTER_MAPPING,
    "alter_mapping_replace": _BRANCH_ALTER_MAPPING_REPLACE,
    "alter_mapping_for_replace": _BRANCH_ALTER_MAPPING_FOR_REPLACE,
    "drop_mapping": _BRANCH_DROP_MAPPING,
    "rename": _BRANCH_RENAME,
    "owner": _BRANCH_OWNER,
    "set_schema": _BRANCH_SET_SCHEMA,
}

# Dense baseline defaults (all positive T1-T4 + T6 factor values).  The T5
# single-value factors (nonexistent_config, nonexistent_dictionary,
# nonexistent_token_type_mapping, duplicate_new_name,
# nonexistent_owner_role, nonexistent_target_schema, non_owner_attempt,
# drop_mapping_without_if_exists) are NOT baselined here: every declared
# value is either a failure mode or a branch-specific boundary, so they are
# set only when they are the primary (or derived in the extension).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_ADD_MAPPING,
    "grammar_branch": _BRANCH_ADD_MAPPING,
    "target_action": "add_mapping",
    "alter_action": "add_mapping",
    "object_state": "exists",
    "expected_status": "success",
    "if_exists_clause": "omitted",
    "owner_target": "specified_new_owner",
    "dictionary_existence": "dictionary_exists",
    "token_type_existence": "token_type_mapped",
    "config_name_shape": "simple_id",
    "new_name_shape": "simple_id",
    "owner_name_shape": "simple_id",
    "schema_name_shape": "simple_id",
    "dictionary_name_shape": "simple_id",
    "token_type_name_shape": "valid_token_type",
    "privilege_level": "owner",
    "role_existence": "role_exists",
    "schema_existence": "schema_exists",
    "dictionary_dependency": "dictionary_exists_and_valid",
    "verification_mode": "catalog_query_pg_ts_config",
    "cleanup_mode": "drop_mapping_revert",
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
    cns = a.get("config_name_shape", "simple_id")
    nc = a.get("nonexistent_config", "")
    de = a.get("dictionary_existence", "dictionary_exists")
    dd = a.get("dictionary_dependency", "dictionary_exists_and_valid")
    nd = a.get("nonexistent_dictionary", "")
    dns = a.get("dictionary_name_shape", "simple_id")
    pl = a.get("privilege_level", "owner")
    noa = a.get("non_owner_attempt", "")
    re_ = a.get("role_existence", "role_exists")
    nor = a.get("nonexistent_owner_role", "")
    ons = a.get("owner_name_shape", "simple_id")
    se = a.get("schema_existence", "schema_exists")
    nts = a.get("nonexistent_target_schema", "")
    sns = a.get("schema_name_shape", "simple_id")
    dnn = a.get("duplicate_new_name", "")
    nns = a.get("new_name_shape", "simple_id")
    tte = a.get("token_type_existence", "token_type_mapped")
    nttm = a.get("nonexistent_token_type_mapping", "")
    ttns = a.get("token_type_name_shape", "valid_token_type")
    iec = a.get("if_exists_clause", "omitted")

    # config-existence cluster: object_state / config_name_shape /
    # nonexistent_config
    if (
        os_ == "not_exists"
        or cns == "nonexistent_name"
        or nc == "config_missing"
    ):
        a["object_state"] = "not_exists"
        a["config_name_shape"] = "nonexistent_name"
        a["nonexistent_config"] = "config_missing"

    # dictionary-existence cluster: dictionary_existence /
    # dictionary_dependency / nonexistent_dictionary / dictionary_name_shape
    if (
        de == "dictionary_not_exists"
        or dd == "dictionary_missing"
        or nd == "dictionary_missing"
        or dns == "nonexistent_name"
    ):
        a["dictionary_existence"] = "dictionary_not_exists"
        a["dictionary_dependency"] = "dictionary_missing"
        a["nonexistent_dictionary"] = "dictionary_missing"
        a["dictionary_name_shape"] = "nonexistent_name"

    # privilege cluster: privilege_level / non_owner_attempt
    if pl == "non_owner" or noa == "non_owner_execution":
        a["privilege_level"] = "non_owner"
        a["non_owner_attempt"] = "non_owner_execution"

    # role-existence cluster: role_existence / nonexistent_owner_role /
    # owner_name_shape
    if (
        re_ == "role_not_exists"
        or nor == "role_missing"
        or ons == "nonexistent_role"
    ):
        a["role_existence"] = "role_not_exists"
        a["nonexistent_owner_role"] = "role_missing"
        a["owner_name_shape"] = "nonexistent_role"

    # schema-existence cluster: schema_existence /
    # nonexistent_target_schema / schema_name_shape
    if (
        se == "schema_not_exists"
        or nts == "schema_missing"
        or sns == "nonexistent_schema"
    ):
        a["schema_existence"] = "schema_not_exists"
        a["nonexistent_target_schema"] = "schema_missing"
        a["schema_name_shape"] = "nonexistent_schema"

    # rename-conflict cluster: duplicate_new_name / new_name_shape
    if (
        dnn == "same_name_conflict"
        or nns == "duplicate_name"
    ):
        a["duplicate_new_name"] = "same_name_conflict"
        a["new_name_shape"] = "duplicate_name"

    # token-type-mapping cluster: token_type_existence /
    # nonexistent_token_type_mapping / token_type_name_shape
    if (
        tte == "token_type_not_mapped"
        or nttm == "mapping_missing"
        or ttns == "invalid_token_type"
    ):
        a["token_type_existence"] = "token_type_not_mapped"
        a["nonexistent_token_type_mapping"] = "mapping_missing"
        a["token_type_name_shape"] = "invalid_token_type"

    # if_exists cluster: if_exists_clause / drop_mapping_without_if_exists
    if iec == "omitted":
        a["drop_mapping_without_if_exists"] = "without_if_exists"
    else:
        a["drop_mapping_without_if_exists"] = "with_if_exists"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: AlterTextSearchConfigurationFactorObligation,
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
        raise AlterTextSearchConfigurationFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: AlterTextSearchConfigurationFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise AlterTextSearchConfigurationFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_alter_text_search_configuration_factor_loop_plan(
    repository_root: Path,
) -> AlterTextSearchConfigurationFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_alter_text_search_configuration_factor_loop_obligations(root)
    cases: list[AlterTextSearchConfigurationFactorCase] = []
    delegated: list[AlterTextSearchConfigurationFactorObligation] = []
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
            AlterTextSearchConfigurationFactorCase(
                ordinal=ordinal,
                case_id=f"ALTERTEXTSEARCHCONFIGURATION{ordinal:05d}",
                sql_filename=f"ALTERTEXTSEARCHCONFIGURATION{ordinal:05d}.sql",
                object_prefix=(
                    f"alter_text_search_configuration_{ordinal:05d}_"
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
    plan = AlterTextSearchConfigurationFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 89 or len(plan.delegated) != 0:
        raise AlterTextSearchConfigurationFactorLoopError(
            "factor loop plan count drift"
        )
    if len({row.primary_obligation_id for row in plan.cases}) != 89:
        raise AlterTextSearchConfigurationFactorLoopError(
            "local obligation mapping drift"
        )
    if len({row.sql_filename for row in plan.cases}) != 89:
        raise AlterTextSearchConfigurationFactorLoopError("duplicate SQL filename")
    return plan


def compile_alter_text_search_configuration_factor_loop_obligations(
    repository_root: Path,
) -> tuple[AlterTextSearchConfigurationFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        AlterTextSearchConfigurationFactorObligation(
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
    if len(rows) != 89:
        raise AlterTextSearchConfigurationFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise AlterTextSearchConfigurationFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 8, "SFV": 81}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise AlterTextSearchConfigurationFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise AlterTextSearchConfigurationFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 89:
        raise AlterTextSearchConfigurationFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise AlterTextSearchConfigurationFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "AlterTextSearchConfigurationFactorLoopError",
    "AlterTextSearchConfigurationGrammarAction",
    "AlterTextSearchConfigurationFactorObligation",
    "AlterTextSearchConfigurationFactorCase",
    "AlterTextSearchConfigurationFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_alter_text_search_configuration_factor_loop_obligations",
    "build_alter_text_search_configuration_factor_loop_plan",
    "_obligation_multiset_sha256",
]
