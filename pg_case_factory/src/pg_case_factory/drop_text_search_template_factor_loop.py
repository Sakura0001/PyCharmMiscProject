"""Factor-value-loop obligation ledger for PostgreSQL 18.4 DROP TEXT SEARCH TEMPLATE.

This module compiles the marginal GRM/SFV/RISK obligation ledger for
``DROP TEXT SEARCH TEMPLATE``.  The statement targets text search template
catalog objects (``pg_catalog.pg_ts_template``) and has no ``INV`` block, so
the canonical SFV obligations are derived one-to-one from the shipped
applicability matrix: exactly 33 rows, one local obligation per row.

The official synopsis has a single branch
(``DROP TEXT SEARCH TEMPLATE [ IF EXISTS ] name [ CASCADE | RESTRICT ]``);
the grammar ledger freezes that one action skeleton as a GRM obligation.
A RISK pair (commit/rollback) exercises the transactional DDL boundary.

Every local obligation becomes exactly one regress program; there are no
delegated handoffs because every reachable negative boundary is a real
``DROP TEXT SEARCH TEMPLATE`` error that belongs to this statement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class DropTextSearchTemplateFactorLoopError(ValueError):
    """Raised when a frozen DROP TEXT SEARCH TEMPLATE obligation input drifts."""


@dataclass(frozen=True)
class DropTextSearchTemplateFactorObligation:
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
class DropTextSearchTemplateFactorCase:
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
class DropTextSearchTemplateFactorLoopPlan:
    obligations: tuple[DropTextSearchTemplateFactorObligation, ...]
    cases: tuple[DropTextSearchTemplateFactorCase, ...]
    delegated: tuple[DropTextSearchTemplateFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-droptstemplate.html).
_BRANCH_1 = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-droptstemplate"

@dataclass(frozen=True)
class _GrammarAction:
    action_id: str
    grammar_branch_id: str
    source_locator: str


_GRAMMAR_ACTIONS: tuple[_GrammarAction, ...] = (
    _GrammarAction(
        action_id="drop_text_search_template",
        grammar_branch_id=_BRANCH_1,
        source_locator=f"{_DOC_SOURCE}:synopsis",
    ),
)

_REPRESENTATIVE_ACTION = "drop_text_search_template"

# Every canonical factor maps to the single DROP TEXT SEARCH TEMPLATE
# consumer action.
_SFV_FACTOR_CONSUMER: dict[str, str] = {
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "if_exists_clause": _REPRESENTATIVE_ACTION,
    "cascade_restrict": _REPRESENTATIVE_ACTION,
    "privilege_requirement": _REPRESENTATIVE_ACTION,
    "dependency_status": _REPRESENTATIVE_ACTION,
    "template_name_shape": _REPRESENTATIVE_ACTION,
    "privilege_context": _REPRESENTATIVE_ACTION,
    "dependency_context": _REPRESENTATIVE_ACTION,
    "error_type": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

_STATEMENT_BRANCH_CONSUMER: dict[str, str] = {
    "branch_drop_ts_template": "drop_text_search_template",
    "branch_drop_ts_template_if_exists": "drop_text_search_template",
}

# Canonical (factor, value) pairs that reach a PostgreSQL target check and
# are rejected (best-effort attribution against PG 18.4).  privilege_requirement
# = non_superuser inherently fails (42501) because DROP TEXT SEARCH TEMPLATE
# requires superuser.  object_state=absent / template_name_shape=
# non_existent_name inherently errors (42704) when IF EXISTS is omitted.
# dependency_context=dict_using_template under RESTRICT inherently errors
# (2BP01).  error_type values mirror these boundaries.  Kept minimal (Option-A
# marginal); cross-product failures live in EXTENSION.
_SFV_FAILURE_VALUES: frozenset[tuple[str, str]] = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "absent"),
        ("privilege_requirement", "non_superuser"),
        ("privilege_context", "non_superuser_session"),
        ("dependency_status", "has_dict_dependencies"),
        ("dependency_context", "dict_using_template"),
        ("template_name_shape", "non_existent_name"),
        ("error_type", "non_existent_without_if_exists"),
        ("error_type", "dependent_object_exists"),
        ("error_type", "insufficient_privilege"),
    }
)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise DropTextSearchTemplateFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise DropTextSearchTemplateFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _consumer_branch_map() -> dict[str, str]:
    return {
        action.action_id: action.grammar_branch_id
        for action in _GRAMMAR_ACTIONS
    }


def _renderer_factor_key(factor_key: str) -> str:
    if factor_key.startswith("outer:") or factor_key.startswith("local:"):
        return factor_key.split(":", 1)[1]
    return factor_key


def _compile_grammar_obligations() -> list[DropTextSearchTemplateFactorObligation]:
    rows: list[DropTextSearchTemplateFactorObligation] = []
    for action in _GRAMMAR_ACTIONS:
        rows.append(
            DropTextSearchTemplateFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPTEXTSEARCHTEMPLATE-GRM|{action.grammar_branch_id}|"
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
    if len(rows) != 1:
        raise DropTextSearchTemplateFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[DropTextSearchTemplateFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("drop_text_search_template")
    if len(catalog_rows) != 33:
        raise DropTextSearchTemplateFactorLoopError("canonical obligation count drift")
    rows: list[DropTextSearchTemplateFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            DropTextSearchTemplateFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPTEXTSEARCHTEMPLATE-SFV|{row.row_id}|{consumer}"
                ),
                kind="SFV",
                factor_key=row.factor,
                value=row.value,
                consumer_action_id=consumer,
                disposition=(
                    "expected_failure"
                    if (row.factor, row.value) in _SFV_FAILURE_VALUES
                    else "covered"
                ),
                source_locator=f"{row.source_reference}#{row.row_id}",
            )
        )
    return rows


def _compile_risk_obligations() -> list[DropTextSearchTemplateFactorObligation]:
    return [
        DropTextSearchTemplateFactorObligation(
            ordinal=0,
            obligation_id=f"DROPTEXTSEARCHTEMPLATE-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-droptstemplate:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[DropTextSearchTemplateFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"drop-text-search-template-factor-obligations-v1\n")
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


# Best-effort PG 18.4 SQLSTATE attribution for each reachable expected-failure
# value.  The frozen counts and sha256s in the companion tests are the spec.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "drop_ts_template_declared_failure",
    ),
    ("object_state", "absent"): (
        "42704",
        "undefined_ts_template_absent",
    ),
    ("privilege_requirement", "non_superuser"): (
        "42501",
        "insufficient_ts_template_privilege",
    ),
    ("privilege_context", "non_superuser_session"): (
        "42501",
        "insufficient_ts_template_privilege",
    ),
    ("dependency_status", "has_dict_dependencies"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
    ("dependency_context", "dict_using_template"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
    ("template_name_shape", "non_existent_name"): (
        "42704",
        "undefined_ts_template_name",
    ),
    ("error_type", "non_existent_without_if_exists"): (
        "42704",
        "undefined_ts_template_no_if_exists",
    ),
    ("error_type", "dependent_object_exists"): (
        "2BP01",
        "dependent_objects_restricted",
    ),
    ("error_type", "insufficient_privilege"): (
        "42501",
        "insufficient_ts_template_privilege",
    ),
}


def _expected_failure_details(
    obligation: DropTextSearchTemplateFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise DropTextSearchTemplateFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


# Dense baseline defaults (all positive factor values).  if_exists_clause is
# "present" (the safe IF EXISTS form) and cascade_restrict is
# "default_restrict" (RESTRICT is the default behavior).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_ts_template",
    "grammar_branch": "branch_1",
    "target_action": "drop_text_search_template",
    "object_state": "exists",
    "expected_status": "success",
    "if_exists_clause": "present",
    "cascade_restrict": "default_restrict",
    "privilege_requirement": "superuser",
    "dependency_status": "no_dependencies",
    "template_name_shape": "simple_id",
    "privilege_context": "superuser_session",
    "dependency_context": "no_dependencies",
    "error_type": "none",
    "verification_mode": "catalog_query",
    "cleanup_mode": "cascade_cleanup",
}

# Baseline primaries whose target template is intentionally absent, so the DROP
# surfaces a not-found error (42704) and the oracle asserts absence.  For
# these the renderer forces if_exists_clause=absent so the missing template
# surfaces a hard error rather than an IF EXISTS notice.
_ABSENT_TEMPLATE_PRIMARIES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "absent"),
        ("template_name_shape", "non_existent_name"),
        ("error_type", "non_existent_without_if_exists"),
    }
)

# Baseline primaries that imply a non-superuser privilege fixture must be
# created.
_PRIVILEGE_PRIMARIES = frozenset(
    {
        ("privilege_requirement", "non_superuser"),
        ("privilege_context", "non_superuser_session"),
        ("error_type", "insufficient_privilege"),
    }
)

# Baseline primaries that imply a dictionary dependency fixture must be
# created under RESTRICT.
_DEPENDENCY_PRIMARIES = frozenset(
    {
        ("dependency_context", "dict_using_template"),
        ("dependency_status", "has_dict_dependencies"),
        ("error_type", "dependent_object_exists"),
    }
)


def _baseline_assignments(
    obligation: DropTextSearchTemplateFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides."""

    branch = _consumer_branch_map()[obligation.consumer_action_id]
    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["grammar_branch"] = branch
    assignments["target_action"] = obligation.consumer_action_id
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value
    if (obligation.factor_key, obligation.value) in _ABSENT_TEMPLATE_PRIMARIES:
        assignments["if_exists_clause"] = "absent"
        assignments["object_state"] = "absent"
    if (obligation.factor_key, obligation.value) in _PRIVILEGE_PRIMARIES:
        assignments["privilege_requirement"] = "non_superuser"
        assignments["privilege_context"] = "non_superuser_session"
    if (obligation.factor_key, obligation.value) in _DEPENDENCY_PRIMARIES:
        assignments["dependency_context"] = "dict_using_template"
        assignments["dependency_status"] = "has_dict_dependencies"
        assignments["cascade_restrict"] = "explicit_restrict"
    if obligation.factor_key == "statement_branch":
        if obligation.value == "branch_drop_ts_template_if_exists":
            assignments["if_exists_clause"] = "present"
    if len(assignments) != len(set(assignments)):
        raise DropTextSearchTemplateFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_drop_text_search_template_factor_loop_plan(
    repository_root: Path,
) -> DropTextSearchTemplateFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_drop_text_search_template_factor_loop_obligations(root)
    cases: list[DropTextSearchTemplateFactorCase] = []
    delegated: list[DropTextSearchTemplateFactorObligation] = []
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
            DropTextSearchTemplateFactorCase(
                ordinal=ordinal,
                case_id=f"DROPTEXTSEARCHTEMPLATE{ordinal:05d}",
                sql_filename=f"DROPTEXTSEARCHTEMPLATE{ordinal:05d}.sql",
                object_prefix=f"droptextsearchtemplate_{ordinal:05d}_",
                primary_obligation_id=obligation.obligation_id,
                kind=obligation.kind,
                factor_key=_renderer_factor_key(obligation.factor_key),
                factor_value=obligation.value,
                consumer_action_id=obligation.consumer_action_id,
                outcome=outcome,
                expected_sqlstate=sqlstate,
                expected_failure_reason=failure_reason,
                baseline_assignments=_baseline_assignments(obligation),
                execution_profile="serial_sql",
            )
        )
    plan = DropTextSearchTemplateFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 36 or len(plan.delegated) != 0:
        raise DropTextSearchTemplateFactorLoopError("factor loop plan count drift")
    if (
        len({row.primary_obligation_id for row in plan.cases})
        != 36
    ):
        raise DropTextSearchTemplateFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 36:
        raise DropTextSearchTemplateFactorLoopError("duplicate SQL filename")
    return plan


_PLAN_CACHE: dict[Path, DropTextSearchTemplateFactorLoopPlan] = {}


def _build_drop_text_search_template_factor_plan_lazily(
    repository_root: Path,
) -> DropTextSearchTemplateFactorLoopPlan:
    """Return a cached frozen plan, building it on first access."""

    root = Path(repository_root).resolve(strict=True)
    if root not in _PLAN_CACHE:
        _PLAN_CACHE[root] = build_drop_text_search_template_factor_loop_plan(root)
    return _PLAN_CACHE[root]


def compile_drop_text_search_template_factor_loop_obligations(
    repository_root: Path,
) -> tuple[DropTextSearchTemplateFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        DropTextSearchTemplateFactorObligation(
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
    if len(rows) != 36:
        raise DropTextSearchTemplateFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise DropTextSearchTemplateFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 33, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise DropTextSearchTemplateFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise DropTextSearchTemplateFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 36:
        raise DropTextSearchTemplateFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise DropTextSearchTemplateFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "DropTextSearchTemplateFactorLoopError",
    "DropTextSearchTemplateFactorObligation",
    "DropTextSearchTemplateFactorCase",
    "DropTextSearchTemplateFactorLoopPlan",
    "compile_drop_text_search_template_factor_loop_obligations",
    "build_drop_text_search_template_factor_loop_plan",
    "_obligation_multiset_sha256",
    "_build_drop_text_search_template_factor_plan_lazily",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
]
