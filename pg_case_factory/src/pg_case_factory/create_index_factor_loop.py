"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE INDEX.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE INDEX``.  CREATE INDEX is a PostgreSQL DDL statement with one
official synopsis (``sql-createindex.html``) whose 12 canonical
statement-branch forms (single-column btree, multi-column btree, unique,
partial, covering, expression, hash, gist, sp-gist, gin, brin, and
concurrent build) are frozen as ``GRM`` target forms.

CREATE INDEX operates ON a relation (table or materialised view).  The
no-DB ledger prefers a fixture table for fuller coverage and bookend
gate compliance.  The 89 canonical ``SFV`` rows are loaded from the
shipped applicability universe (``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CreateIndexFactorLoopError(ValueError):
    """Raised when a frozen CREATE INDEX obligation input drifts."""


@dataclass(frozen=True)
class CreateIndexGrammarAction:
    """One official target action form of the CREATE INDEX synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateIndexFactorObligation:
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
class CreateIndexFactorCase:
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
class CreateIndexFactorLoopPlan:
    obligations: tuple[CreateIndexFactorObligation, ...]
    cases: tuple[CreateIndexFactorCase, ...]
    delegated: tuple[CreateIndexFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-createindex.html).
_BRANCH_SINGLE_BTREE = "branch_single_column_btree"
_BRANCH_MULTI_BTREE = "branch_multi_column_btree"
_BRANCH_UNIQUE_BTREE = "branch_unique_btree"
_BRANCH_PARTIAL = "branch_partial_index"
_BRANCH_COVERING = "branch_covering_index"
_BRANCH_EXPRESSION = "branch_expression_index"
_BRANCH_HASH = "branch_hash_index"
_BRANCH_GIST = "branch_gist_index"
_BRANCH_SPGIST = "branch_spgist_index"
_BRANCH_GIN = "branch_gin_index"
_BRANCH_BRIN = "branch_brin_index"
_BRANCH_CONCURRENT = "branch_concurrent_build"

_DOC_SOURCE = "postgresql-18.4-doc:sql-createindex"

_REPRESENTATIVE_ACTION = "single_column_btree"

_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_SINGLE_BTREE: "single_column_btree",
    _BRANCH_MULTI_BTREE: "multi_column_btree",
    _BRANCH_UNIQUE_BTREE: "unique_btree",
    _BRANCH_PARTIAL: "partial_index",
    _BRANCH_COVERING: "covering_index",
    _BRANCH_EXPRESSION: "expression_index",
    _BRANCH_HASH: "hash_index",
    _BRANCH_GIST: "gist_index",
    _BRANCH_SPGIST: "spgist_index",
    _BRANCH_GIN: "gin_index",
    _BRANCH_BRIN: "brin_index",
    _BRANCH_CONCURRENT: "concurrent_build",
}

# statement_branch canonical value -> target action.
_SBV_TO_ACTION = {
    "single_column_btree": "single_column_btree",
    "multi_column_btree": "multi_column_btree",
    "unique_btree": "unique_btree",
    "partial_index": "partial_index",
    "covering_index": "covering_index",
    "expression_index": "expression_index",
    "hash_index": "hash_index",
    "gist_index": "gist_index",
    "spgist_index": "spgist_index",
    "gin_index": "gin_index",
    "brin_index": "brin_index",
    "concurrent_build": "concurrent_build",
}

# method canonical value -> target action.
_METHOD_CONSUMER = {
    "btree": "single_column_btree",
    "hash": "hash_index",
    "gist": "gist_index",
    "spgist": "spgst_index",
    "gin": "gin_index",
    "brin": "brin_index",
}

# column_type_compatibility canonical value -> target action.
_CTC_CONSUMER = {
    "btree_compatible": "single_column_btree",
    "hash_compatible": "hash_index",
    "gist_compatible": "gist_index",
    "spgist_compatible": "spgst_index",
    "gin_compatible": "gin_index",
    "brin_compatible": "brin_index",
    "method_type_incompatible": "single_column_btree",
}


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _SBV_TO_ACTION[row.value]
        except KeyError as exc:
            raise CreateIndexFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "method":
        try:
            return _METHOD_CONSUMER[row.value]
        except KeyError as exc:
            raise CreateIndexFactorLoopError(
                f"unknown method value: {row.value}"
            ) from exc
    if row.factor == "unique":
        return "unique_btree" if row.value == "true" else (
            "single_column_btree"
        )
    if row.factor == "predicate":
        return "partial_index" if row.value == "true" else (
            "single_column_btree"
        )
    if row.factor == "include":
        return "covering_index" if row.value == "true" else (
            "single_column_btree"
        )
    if row.factor == "concurrently":
        return "concurrent_build" if row.value == "true" else (
            "single_column_btree"
        )
    if row.factor == "expression_index":
        return "expression_index" if row.value != "column_only" else (
            "single_column_btree"
        )
    if row.factor == "column_type_compatibility":
        try:
            return _CTC_CONSUMER[row.value]
        except KeyError as exc:
            raise CreateIndexFactorLoopError(
                f"unknown column_type_compatibility value: {row.value}"
            ) from exc
    if row.factor == "only":
        return "single_column_btree"
    return _REPRESENTATIVE_ACTION


# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates — DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("invalid_combination", "unique_with_non_btree"),
        ("invalid_combination", "include_with_unsupported_method"),
        (
            "invalid_combination",
            "multi_column_with_unsupported_method",
        ),
        ("syntax_error", "invalid_syntax"),
        ("concurrent_failure", "in_transaction_block"),
        ("concurrent_failure", "invalid_index_leftover"),
        ("column_type_compatibility", "method_type_incompatible"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42710",
        "duplicate_index_provisional",
    ),
    ("invalid_combination", "unique_with_non_btree"): (
        "42809",
        "unique_not_supported_for_method_provisional",
    ),
    ("invalid_combination", "include_with_unsupported_method"): (
        "42809",
        "include_not_supported_for_method_provisional",
    ),
    ("invalid_combination", "multi_column_with_unsupported_method"): (
        "42809",
        "multicolumn_not_supported_for_method_provisional",
    ),
    ("syntax_error", "invalid_syntax"): (
        "42601",
        "syntax_error_provisional",
    ),
    ("concurrent_failure", "in_transaction_block"): (
        "0A000",
        "concurrently_in_transaction_block_provisional",
    ),
    ("concurrent_failure", "invalid_index_leftover"): (
        "0A000",
        "concurrent_failure_invalid_index_provisional",
    ),
    ("column_type_compatibility", "method_type_incompatible"): (
        "42704",
        "operator_class_missing_provisional",
    ),
}


def _load_grammar_actions() -> tuple[CreateIndexGrammarAction, ...]:
    """Freeze every CREATE INDEX synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "single_column_btree",
            _BRANCH_SINGLE_BTREE,
            "CREATE [UNIQUE] INDEX [CONCURRENTLY] [IF NOT EXISTS] name "
            "ON [ONLY] table [USING method] (column [...])",
            "synopsis-single-column-btree",
        ),
        (
            "multi_column_btree",
            _BRANCH_MULTI_BTREE,
            "CREATE INDEX name ON table USING method (col1, col2, ...)",
            "synopsis-multi-column-btree",
        ),
        (
            "unique_btree",
            _BRANCH_UNIQUE_BTREE,
            "CREATE UNIQUE INDEX name ON table USING btree (column)",
            "synopsis-unique-btree",
        ),
        (
            "partial_index",
            _BRANCH_PARTIAL,
            "CREATE INDEX name ON table USING btree (column) WHERE predicate",
            "synopsis-partial-index",
        ),
        (
            "covering_index",
            _BRANCH_COVERING,
            "CREATE INDEX name ON table USING method (column) "
            "INCLUDE (column, ...)",
            "synopsis-covering-index",
        ),
        (
            "expression_index",
            _BRANCH_EXPRESSION,
            "CREATE INDEX name ON table USING btree ((expression))",
            "synopsis-expression-index",
        ),
        (
            "hash_index",
            _BRANCH_HASH,
            "CREATE INDEX name ON table USING hash (column)",
            "synopsis-hash-index",
        ),
        (
            "gist_index",
            _BRANCH_GIST,
            "CREATE INDEX name ON table USING gist (column)",
            "synopsis-gist-index",
        ),
        (
            "spgist_index",
            _BRANCH_SPGIST,
            "CREATE INDEX name ON table USING spgist (column)",
            "synopsis-spgist-index",
        ),
        (
            "gin_index",
            _BRANCH_GIN,
            "CREATE INDEX name ON table USING gin (column)",
            "synopsis-gin-index",
        ),
        (
            "brin_index",
            _BRANCH_BRIN,
            "CREATE INDEX name ON table USING brin (column)",
            "synopsis-brin-index",
        ),
        (
            "concurrent_build",
            _BRANCH_CONCURRENT,
            "CREATE INDEX CONCURRENTLY name ON table USING btree (column)",
            "synopsis-concurrent-build",
        ),
    )
    actions = [
        CreateIndexGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 12:
        raise CreateIndexFactorLoopError("action count drift")
    return tuple(actions)


def _compile_grammar_obligations() -> list[CreateIndexFactorObligation]:
    rows: list[CreateIndexFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateIndexFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CINX-GRM|{action.grammar_branch_id}|"
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
    if len(rows) != 12:
        raise CreateIndexFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateIndexFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_index")
    if len(catalog_rows) != 89:
        raise CreateIndexFactorLoopError("canonical obligation count drift")
    rows: list[CreateIndexFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateIndexFactorObligation(
                ordinal=0,
                obligation_id=f"CINX-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreateIndexFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"create-index-factor-obligations-v1\n")
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
    "single_column_btree": _BRANCH_SINGLE_BTREE,
    "multi_column_btree": _BRANCH_MULTI_BTREE,
    "unique_btree": _BRANCH_UNIQUE_BTREE,
    "partial_index": _BRANCH_PARTIAL,
    "covering_index": _BRANCH_COVERING,
    "expression_index": _BRANCH_EXPRESSION,
    "hash_index": _BRANCH_HASH,
    "gist_index": _BRANCH_GIST,
    "spgist_index": _BRANCH_SPGIST,
    "gin_index": _BRANCH_GIN,
    "brin_index": _BRANCH_BRIN,
    "concurrent_build": _BRANCH_CONCURRENT,
}

# method canonical value -> statement_branch
_METHOD_TO_SBV = {
    "btree": "single_column_btree",
    "hash": "hash_index",
    "gist": "gist_index",
    "spgist": "spgist_index",
    "gin": "gin_index",
    "brin": "brin_index",
}

# statement_branch canonical value -> method
_SBV_TO_METHOD = {
    "single_column_btree": "btree",
    "multi_column_btree": "btree",
    "unique_btree": "btree",
    "partial_index": "btree",
    "covering_index": "btree",
    "expression_index": "btree",
    "hash_index": "hash",
    "gist_index": "gist",
    "spgist_index": "spgist",
    "gin_index": "gin",
    "brin_index": "brin",
    "concurrent_build": "btree",
}

_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "single_column_btree",
    "method": "btree",
    "column_source": "all_template_columns",
    "unique": "false",
    "predicate": "false",
    "include": "false",
    "concurrently": "false",
    "expected_status": "success",
    "order": "none",
    "nulls": "none",
    "if_not_exists": "false",
    "nulls_distinct": "none",
    "only": "false",
    "name_style": "explicit_compact",
    "collation": "none",
    "opclass": "none",
    "column_type_compatibility": "btree_compatible",
    "with_storage": "none",
    "tablespace": "none",
    "expression_index": "column_only",
    "invalid_combination": "none",
    "syntax_error": "none",
    "concurrent_failure": "none",
    "partition_constraint": "none",
    "verification_mode": "catalog_query",
    "cleanup_mode": "drop_index",
}


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive overlapping T1/T5 factors and expected_status."""

    # method ↔ statement_branch
    method = a.get("method", "btree")
    sbv = a.get("statement_branch", "single_column_btree")
    if sbv in _SBV_TO_METHOD and _SBV_TO_METHOD[sbv] != method:
        if a.get("statement_branch") == _BASELINE_DEFAULTS["statement_branch"]:
            a["method"] = _SBV_TO_METHOD[sbv]
            method = a["method"]
    if method in _METHOD_TO_SBV and _METHOD_TO_SBV[method] != sbv:
        if a.get("method", "") != _BASELINE_DEFAULTS["method"] or True:
            a["statement_branch"] = _METHOD_TO_SBV[method]
            sbv = a["statement_branch"]

    # unique → statement_branch
    if a.get("unique") == "true" and sbv not in ("unique_btree",):
        a["statement_branch"] = "unique_btree"
        sbv = "unique_btree"
        a["method"] = "btree"
        method = "btree"

    # predicate → statement_branch
    if a.get("predicate") == "true" and sbv != "partial_index":
        a["statement_branch"] = "partial_index"
        sbv = "partial_index"

    # include → statement_branch
    if a.get("include") == "true" and sbv != "covering_index":
        a["statement_branch"] = "covering_index"
        sbv = "covering_index"

    # concurrently → statement_branch
    if a.get("concurrently") == "true" and sbv != "concurrent_build":
        a["statement_branch"] = "concurrent_build"
        sbv = "concurrent_build"

    # expression_index → statement_branch
    ei = a.get("expression_index", "column_only")
    if ei != "column_only" and sbv != "expression_index":
        a["statement_branch"] = "expression_index"
        sbv = "expression_index"

    # T5 failure derivation → T1 counterparts
    ic = a.get("invalid_combination", "none")
    if ic == "unique_with_non_btree":
        a["unique"] = "true"
        a["method"] = "hash"
        a["statement_branch"] = "unique_btree"
        sbv = "unique_btree"
    elif ic == "include_with_unsupported_method":
        a["include"] = "true"
        a["method"] = "hash"
        a["statement_branch"] = "covering_index"
        sbv = "covering_index"
    elif ic == "multi_column_with_unsupported_method":
        a["statement_branch"] = "multi_column_btree"
        sbv = "multi_column_btree"
        a["method"] = "hash"

    cf = a.get("concurrent_failure", "none")
    if cf == "in_transaction_block":
        a["concurrently"] = "true"
        a["statement_branch"] = "concurrent_build"
        sbv = "concurrent_build"
    elif cf == "invalid_index_leftover":
        a["concurrently"] = "true"
        a["statement_branch"] = "concurrent_build"
        sbv = "concurrent_build"

    ctc = a.get("column_type_compatibility", "btree_compatible")
    if ctc == "method_type_incompatible":
        a["method"] = "hash"
        a["statement_branch"] = "hash_index"
        sbv = "hash_index"

    se = a.get("syntax_error", "none")
    if se == "invalid_syntax":
        a["statement_branch"] = "single_column_btree"
        a["method"] = "btree"
        sbv = "single_column_btree"

    # partition_constraint → only
    pc = a.get("partition_constraint", "none")
    if pc in ("only_on_partitioned", "concurrently_on_partitioned"):
        a["only"] = "true"
        if pc == "concurrently_on_partitioned":
            a["concurrently"] = "true"
            a["statement_branch"] = "concurrent_build"
            sbv = "concurrent_build"

    # expected_status=failure → duplicate index scenario
    es = a.get("expected_status", "success")
    if es == "failure":
        # Only set up duplicate scenario if no other failure is active
        if _count_baseline_failures(a) == 0:
            a["if_not_exists"] = "false"

    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _baseline_assignments(
    obligation: CreateIndexFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["statement_branch"] = _ACTION_BRANCH_CONSUMER_INV.get(
        obligation.consumer_action_id,
        obligation.consumer_action_id,
    )
    if obligation.consumer_action_id in _ACTION_BRANCH:
        assignments["statement_branch"] = obligation.consumer_action_id
    if obligation.consumer_action_id in _SBV_TO_METHOD:
        assignments["method"] = _SBV_TO_METHOD[
            obligation.consumer_action_id
        ]
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    failures = _count_baseline_failures(assignments)
    assignments["expected_status"] = (
        "failure" if failures > 0 else "success"
    )
    if len(assignments) != len(set(assignments)):
        raise CreateIndexFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


_ACTION_BRANCH_CONSUMER_INV = {v: k for k, v in _STATEMENT_BRANCH_CONSUMER.items()}


def _expected_failure_details(
    obligation: CreateIndexFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateIndexFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_index_factor_loop_plan(
    repository_root: Path,
) -> CreateIndexFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_index_factor_loop_obligations(root)
    cases: list[CreateIndexFactorCase] = []
    delegated: list[CreateIndexFactorObligation] = []
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
            CreateIndexFactorCase(
                ordinal=ordinal,
                case_id=f"CREATEINDEX{ordinal:05d}",
                sql_filename=f"CREATEINDEX{ordinal:05d}.sql",
                object_prefix=f"createindex_{ordinal:05d}_",
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
    plan = CreateIndexFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 101 or len(plan.delegated) != 0:
        raise CreateIndexFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 101:
        raise CreateIndexFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 101:
        raise CreateIndexFactorLoopError("duplicate SQL filename")
    return plan


def compile_create_index_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateIndexFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateIndexFactorObligation(
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
    if len(rows) != 101:
        raise CreateIndexFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateIndexFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 12, "SFV": 89}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateIndexFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateIndexFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 101:
        raise CreateIndexFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreateIndexFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "CreateIndexFactorLoopError",
    "CreateIndexGrammarAction",
    "CreateIndexFactorObligation",
    "CreateIndexFactorCase",
    "CreateIndexFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "_BASELINE_DEFAULTS",
    "_ACTION_BRANCH",
    "_SBV_TO_METHOD",
    "_METHOD_TO_SBV",
    "compile_create_index_factor_loop_obligations",
    "build_create_index_factor_loop_plan",
    "_obligation_multiset_sha256",
]
