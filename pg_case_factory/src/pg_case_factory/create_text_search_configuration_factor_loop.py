"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE TEXT SEARCH CONFIGURATION.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE TEXT SEARCH CONFIGURATION``.  CREATE TEXT SEARCH CONFIGURATION is a
PostgreSQL text-search DDL statement with 2 official synopsis branches:
the ``PARSER = parser_name`` form and the ``COPY = source_config`` form.
The statement requires the executor to hold ``CREATE`` privilege on the
target schema (superusers implicitly qualify) and inserts a
``pg_catalog.pg_ts_config`` catalog row (not a ``pg_class`` relation), so
column/table/relation coverage is ``not_applicable`` and there is no
``INV`` block.  ``PARSER`` and ``COPY`` are mutually exclusive; specifying
both or neither is a syntax error.

Each local obligation becomes exactly one regress program.  Because the
inventory declares no ``transaction_outcome`` factor, there are no
``RISK`` obligations.

The grammar ledger is self-contained: the 2 synopsis actions are frozen
inline.  The 52 canonical ``SFV`` rows are loaded from the shipped
applicability universe (``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CreateTextSearchConfigurationFactorLoopError(ValueError):
    """Raised when a frozen CREATE TEXT SEARCH CONFIGURATION obligation input drifts."""


@dataclass(frozen=True)
class CreateTextSearchConfigurationGrammarAction:
    """One official target action form of the CREATE TEXT SEARCH CONFIGURATION synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateTextSearchConfigurationFactorObligation:
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
class CreateTextSearchConfigurationFactorCase:
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
class CreateTextSearchConfigurationFactorLoopPlan:
    obligations: tuple[CreateTextSearchConfigurationFactorObligation, ...]
    cases: tuple[CreateTextSearchConfigurationFactorCase, ...]
    delegated: tuple[CreateTextSearchConfigurationFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-createtsconfiguration.html).
_BRANCH_PARSER = "branch_parser"
_BRANCH_COPY = "branch_copy"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createtsconfiguration"

# A representative branch_parser action used as the baseline consumer for
# canonical factors that are not bound to one specific branch.  The PARSER
# form is the simpler, dependency-light baseline.
_REPRESENTATIVE_ACTION = "parser"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_PARSER: "parser",
    _BRANCH_COPY: "copy",
}

# config_source_type value -> target action (value-dependent consumer).
_CONFIG_SOURCE_TYPE_CONSUMER = {
    "parser": "parser",
    "copy": "copy",
}

# Canonical factor -> the action where the value is observable.  Factors
# whose consumer depends on the value (statement_branch, config_source_type)
# are resolved in :func:`_canonical_consumer`.
_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "config_source_type": _REPRESENTATIVE_ACTION,
    "parser_existence": "parser",
    "copy_source_existence": "copy",
    "parser_copy_conflict": _REPRESENTATIVE_ACTION,
    "config_name_shape": _REPRESENTATIVE_ACTION,
    "parser_name_shape": "parser",
    "copy_source_name_shape": "copy",
    "privilege_level": _REPRESENTATIVE_ACTION,
    "schema_existence": _REPRESENTATIVE_ACTION,
    "parser_dependency": "parser",
    "duplicate_config_name": _REPRESENTATIVE_ACTION,
    "nonexistent_parser": "parser",
    "nonexistent_copy_source": "copy",
    "parser_copy_both_specified": _REPRESENTATIVE_ACTION,
    "missing_parser_or_copy": _REPRESENTATIVE_ACTION,
    "schema_permission_denied": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "exists"),
        ("config_name_shape", "duplicate_name"),
        ("config_name_shape", "invalid_name"),
        ("parser_existence", "parser_not_exists"),
        ("parser_name_shape", "nonexistent_name"),
        ("parser_dependency", "parser_missing"),
        ("nonexistent_parser", "parser_missing"),
        ("copy_source_existence", "source_not_exists"),
        ("copy_source_name_shape", "nonexistent_name"),
        ("nonexistent_copy_source", "source_missing"),
        ("parser_copy_conflict", "both_specified"),
        ("parser_copy_both_specified", "both_specified"),
        ("missing_parser_or_copy", "none_specified"),
        ("privilege_level", "non_owner"),
        ("schema_permission_denied", "lacks_create_privilege"),
        ("schema_existence", "schema_not_exists"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("object_state", "exists"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("config_name_shape", "duplicate_name"): (
        "42710",
        "duplicate_object_provisional",
    ),
    ("config_name_shape", "invalid_name"): (
        "42601",
        "syntax_error_provisional",
    ),
    ("parser_existence", "parser_not_exists"): (
        "42704",
        "parser_does_not_exist_provisional",
    ),
    ("parser_name_shape", "nonexistent_name"): (
        "42704",
        "parser_does_not_exist_provisional",
    ),
    ("parser_dependency", "parser_missing"): (
        "42704",
        "parser_does_not_exist_provisional",
    ),
    ("nonexistent_parser", "parser_missing"): (
        "42704",
        "parser_does_not_exist_provisional",
    ),
    ("copy_source_existence", "source_not_exists"): (
        "42704",
        "config_does_not_exist_provisional",
    ),
    ("copy_source_name_shape", "nonexistent_name"): (
        "42704",
        "config_does_not_exist_provisional",
    ),
    ("nonexistent_copy_source", "source_missing"): (
        "42704",
        "config_does_not_exist_provisional",
    ),
    ("parser_copy_conflict", "both_specified"): (
        "42601",
        "syntax_error_provisional",
    ),
    ("parser_copy_both_specified", "both_specified"): (
        "42601",
        "syntax_error_provisional",
    ),
    ("missing_parser_or_copy", "none_specified"): (
        "42601",
        "syntax_error_provisional",
    ),
    ("privilege_level", "non_owner"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("schema_permission_denied", "lacks_create_privilege"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("schema_existence", "schema_not_exists"): (
        "3F000",
        "schema_does_not_exist_provisional",
    ),
}


def _load_grammar_actions() -> (
    tuple[CreateTextSearchConfigurationGrammarAction, ...]
):
    """Freeze every CREATE TEXT SEARCH CONFIGURATION synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "parser",
            _BRANCH_PARSER,
            "CREATE TEXT SEARCH CONFIGURATION name (PARSER = parser_name)",
            "synopsis-parser",
        ),
        (
            "copy",
            _BRANCH_COPY,
            "CREATE TEXT SEARCH CONFIGURATION name (COPY = source_config)",
            "synopsis-copy",
        ),
    )
    actions = [
        CreateTextSearchConfigurationGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 2:
        raise CreateTextSearchConfigurationFactorLoopError(
            "create text search configuration action count drift"
        )
    return tuple(actions)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise CreateTextSearchConfigurationFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "config_source_type":
        try:
            return _CONFIG_SOURCE_TYPE_CONSUMER[row.value]
        except KeyError as exc:
            raise CreateTextSearchConfigurationFactorLoopError(
                f"unknown config_source_type value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise CreateTextSearchConfigurationFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> (
    list[CreateTextSearchConfigurationFactorObligation]
):
    rows: list[CreateTextSearchConfigurationFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateTextSearchConfigurationFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CTSC-GRM|{action.grammar_branch_id}|"
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
        raise CreateTextSearchConfigurationFactorLoopError(
            "grammar obligation count drift"
        )
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateTextSearchConfigurationFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_text_search_configuration")
    if len(catalog_rows) != 52:
        raise CreateTextSearchConfigurationFactorLoopError(
            "canonical obligation count drift"
        )
    rows: list[CreateTextSearchConfigurationFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateTextSearchConfigurationFactorObligation(
                ordinal=0,
                obligation_id=f"CTSC-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreateTextSearchConfigurationFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"create-text-search-configuration-factor-obligations-v1\n"
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
    "parser": _BRANCH_PARSER,
    "copy": _BRANCH_COPY,
}

# Dense baseline defaults (all positive T1-T4 + T6 factor values).  The T5
# single-value factors (duplicate_config_name, nonexistent_parser,
# nonexistent_copy_source, parser_copy_both_specified,
# missing_parser_or_copy, schema_permission_denied) are NOT baselined
# here: every declared value is either a failure mode or a branch-specific
# boundary, so they are set only when they are the primary (or derived in
# the extension).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_PARSER,
    "grammar_branch": _BRANCH_PARSER,
    "target_action": "parser",
    "object_state": "not_exists",
    "expected_status": "success",
    "config_source_type": "parser",
    "parser_existence": "parser_exists",
    "copy_source_existence": "source_exists",
    "parser_copy_conflict": "only_parser",
    "config_name_shape": "simple_id",
    "parser_name_shape": "simple_id",
    "copy_source_name_shape": "simple_id",
    "privilege_level": "schema_owner",
    "schema_existence": "schema_exists",
    "parser_dependency": "parser_exists_and_valid",
    "duplicate_config_name": "no_conflict",
    "nonexistent_parser": "parser_exists",
    "nonexistent_copy_source": "source_exists",
    "parser_copy_both_specified": "one_specified",
    "missing_parser_or_copy": "one_specified",
    "schema_permission_denied": "has_create_privilege",
    "verification_mode": "catalog_query_pg_ts_config",
    "cleanup_mode": "drop_text_search_configuration",
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

    os_ = a.get("object_state", "not_exists")
    cns = a.get("config_name_shape", "simple_id")
    dcn = a.get("duplicate_config_name", "no_conflict")
    pe = a.get("parser_existence", "parser_exists")
    pns = a.get("parser_name_shape", "simple_id")
    np_ = a.get("nonexistent_parser", "")
    pd = a.get("parser_dependency", "parser_exists_and_valid")
    cse = a.get("copy_source_existence", "source_exists")
    csns = a.get("copy_source_name_shape", "simple_id")
    ncs = a.get("nonexistent_copy_source", "")
    pl = a.get("privilege_level", "schema_owner")
    spd = a.get("schema_permission_denied", "has_create_privilege")
    se = a.get("schema_existence", "schema_exists")
    pcc = a.get("parser_copy_conflict", "only_parser")
    pcbs = a.get("parser_copy_both_specified", "one_specified")
    mpc = a.get("missing_parser_or_copy", "one_specified")
    cst = a.get("config_source_type", "parser")

    # duplicate-config cluster: object_state / config_name_shape /
    # duplicate_config_name
    if (
        os_ == "exists"
        or cns == "duplicate_name"
        or dcn == "same_name_conflict"
    ):
        a["object_state"] = "exists"
        a["config_name_shape"] = "duplicate_name"
        a["duplicate_config_name"] = "same_name_conflict"

    # nonexistent-parser cluster: parser_existence / parser_name_shape /
    # nonexistent_parser / parser_dependency
    if (
        pe == "parser_not_exists"
        or pns == "nonexistent_name"
        or np_ == "parser_missing"
        or pd == "parser_missing"
    ):
        a["parser_existence"] = "parser_not_exists"
        a["parser_name_shape"] = "nonexistent_name"
        a["nonexistent_parser"] = "parser_missing"
        a["parser_dependency"] = "parser_missing"

    # nonexistent-copy-source cluster: copy_source_existence /
    # copy_source_name_shape / nonexistent_copy_source
    if (
        cse == "source_not_exists"
        or csns == "nonexistent_name"
        or ncs == "source_missing"
    ):
        a["copy_source_existence"] = "source_not_exists"
        a["copy_source_name_shape"] = "nonexistent_name"
        a["nonexistent_copy_source"] = "source_missing"

    # privilege cluster: privilege_level / schema_permission_denied
    if pl == "non_owner" or spd == "lacks_create_privilege":
        a["privilege_level"] = "non_owner"
        a["schema_permission_denied"] = "lacks_create_privilege"

    # schema-existence cluster: schema_existence
    if se == "schema_not_exists":
        a["schema_existence"] = "schema_not_exists"

    # parser-copy-conflict cluster: config_source_type /
    # parser_copy_conflict / parser_copy_both_specified /
    # missing_parser_or_copy.  These four factors all describe what is
    # specified inside the parentheses; they are synced so the render
    # produces a self-consistent target.
    if pcc == "both_specified" or pcbs == "both_specified":
        a["parser_copy_conflict"] = "both_specified"
        a["parser_copy_both_specified"] = "both_specified"
        a["missing_parser_or_copy"] = "one_specified"
    elif mpc == "none_specified":
        a["missing_parser_or_copy"] = "none_specified"
        a["parser_copy_conflict"] = "only_parser"
        a["parser_copy_both_specified"] = "one_specified"
    elif cst == "copy" or pcc == "only_copy":
        a["config_source_type"] = "copy"
        a["parser_copy_conflict"] = "only_copy"
        a["parser_copy_both_specified"] = "one_specified"
        a["missing_parser_or_copy"] = "one_specified"
        a["statement_branch"] = _BRANCH_COPY
    else:
        a["config_source_type"] = "parser"
        a["parser_copy_conflict"] = "only_parser"
        a["parser_copy_both_specified"] = "one_specified"
        a["missing_parser_or_copy"] = "one_specified"
        a["statement_branch"] = _BRANCH_PARSER


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: CreateTextSearchConfigurationFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    consumer = obligation.consumer_action_id
    branch = _ACTION_BRANCH[consumer]
    assignments["grammar_branch"] = branch
    assignments["target_action"] = consumer
    assignments["statement_branch"] = branch
    if consumer == "copy":
        assignments["config_source_type"] = "copy"
        assignments["parser_copy_conflict"] = "only_copy"
    else:
        assignments["config_source_type"] = "parser"
        assignments["parser_copy_conflict"] = "only_parser"
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    failures = _count_baseline_failures(assignments)
    assignments["expected_status"] = (
        "failure" if failures > 0 else "success"
    )
    if len(assignments) != len(set(assignments)):
        raise CreateTextSearchConfigurationFactorLoopError(
            "duplicate baseline factor key"
        )
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateTextSearchConfigurationFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateTextSearchConfigurationFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_text_search_configuration_factor_loop_plan(
    repository_root: Path,
) -> CreateTextSearchConfigurationFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_text_search_configuration_factor_loop_obligations(root)
    cases: list[CreateTextSearchConfigurationFactorCase] = []
    delegated: list[CreateTextSearchConfigurationFactorObligation] = []
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
            CreateTextSearchConfigurationFactorCase(
                ordinal=ordinal,
                case_id=f"CREATETEXTSEARCHCONFIGURATION{ordinal:05d}",
                sql_filename=f"CREATETEXTSEARCHCONFIGURATION{ordinal:05d}.sql",
                object_prefix=(
                    f"createtextsearchconfiguration_{ordinal:05d}_"
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
    plan = CreateTextSearchConfigurationFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 54 or len(plan.delegated) != 0:
        raise CreateTextSearchConfigurationFactorLoopError(
            "factor loop plan count drift"
        )
    if len({row.primary_obligation_id for row in plan.cases}) != 54:
        raise CreateTextSearchConfigurationFactorLoopError(
            "local obligation mapping drift"
        )
    if len({row.sql_filename for row in plan.cases}) != 54:
        raise CreateTextSearchConfigurationFactorLoopError("duplicate SQL filename")
    return plan


def compile_create_text_search_configuration_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateTextSearchConfigurationFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateTextSearchConfigurationFactorObligation(
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
    if len(rows) != 54:
        raise CreateTextSearchConfigurationFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateTextSearchConfigurationFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 2, "SFV": 52}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateTextSearchConfigurationFactorLoopError(
            "obligation kind count drift"
        )
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateTextSearchConfigurationFactorLoopError(
            "delegated obligation count drift"
        )
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 54:
        raise CreateTextSearchConfigurationFactorLoopError(
            "local obligation count drift"
        )
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreateTextSearchConfigurationFactorLoopError(
            "unknown obligation disposition"
        )
    return rows


__all__ = [
    "CreateTextSearchConfigurationFactorLoopError",
    "CreateTextSearchConfigurationGrammarAction",
    "CreateTextSearchConfigurationFactorObligation",
    "CreateTextSearchConfigurationFactorCase",
    "CreateTextSearchConfigurationFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_create_text_search_configuration_factor_loop_obligations",
    "build_create_text_search_configuration_factor_loop_plan",
    "_obligation_multiset_sha256",
]
