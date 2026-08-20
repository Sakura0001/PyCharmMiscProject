"""Factor-value-loop obligation ledger for PostgreSQL 18.4 DROP TEXT SEARCH CONFIGURATION.

This module compiles the marginal GRM/SFV/RISK obligation ledger for
``DROP TEXT SEARCH CONFIGURATION``.  The statement has no ``INV`` block,
so the canonical SFV obligations are derived one-to-one from the shipped
applicability matrix: exactly 35 rows, one local obligation per row.

The official synopsis has a single branch
(``DROP TEXT SEARCH CONFIGURATION [ IF EXISTS ] name [ CASCADE | RESTRICT ]``);
the grammar ledger freezes that one action skeleton as a GRM obligation.
A RISK pair (commit/rollback) exercises the transactional DDL boundary,
mirroring the sibling statement ledgers.

Every local obligation becomes exactly one regress program; there are no
delegated handoffs because every reachable negative boundary is a real
``DROP TEXT SEARCH CONFIGURATION`` error that belongs to this statement.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class DropTextSearchConfigurationFactorLoopError(ValueError):
    """Raised when a frozen DROP TEXT SEARCH CONFIGURATION obligation input drifts."""


@dataclass(frozen=True)
class DropTextSearchConfigurationFactorObligation:
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
class DropTextSearchConfigurationFactorCase:
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
class DropTextSearchConfigurationFactorLoopPlan:
    obligations: tuple[DropTextSearchConfigurationFactorObligation, ...]
    cases: tuple[DropTextSearchConfigurationFactorCase, ...]
    delegated: tuple[DropTextSearchConfigurationFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branch (PostgreSQL 18 sql-droptsconfiguration.html).
_BRANCH_1 = "branch_1"

_DOC_SOURCE = "postgresql-18.4-doc:sql-droptsconfiguration"

@dataclass(frozen=True)
class _GrammarAction:
    action_id: str
    grammar_branch_id: str
    source_locator: str


_GRAMMAR_ACTIONS: tuple[_GrammarAction, ...] = (
    _GrammarAction(
        action_id="drop_text_search_configuration",
        grammar_branch_id=_BRANCH_1,
        source_locator=f"{_DOC_SOURCE}:synopsis",
    ),
)

_REPRESENTATIVE_ACTION = "drop_text_search_configuration"

# Every canonical factor maps to the single DROP TEXT SEARCH CONFIGURATION
# consumer action.
_SFV_FACTOR_CONSUMER: dict[str, str] = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "if_exists_clause": _REPRESENTATIVE_ACTION,
    "cascade_restrict": _REPRESENTATIVE_ACTION,
    "authorization_path": _REPRESENTATIVE_ACTION,
    "dependency_status": _REPRESENTATIVE_ACTION,
    "config_name_shape": _REPRESENTATIVE_ACTION,
    "privilege_context": _REPRESENTATIVE_ACTION,
    "dependency_context": _REPRESENTATIVE_ACTION,
    "error_type": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

_STATEMENT_BRANCH_CONSUMER: dict[str, str] = {
    "branch_drop_ts_config": _REPRESENTATIVE_ACTION,
    "branch_drop_ts_config_if_exists": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach a PostgreSQL target check and
# are rejected (best-effort attribution against PG 18.4).  authorization_path=
# non_owner inherently fails (42501) because DROP TEXT SEARCH CONFIGURATION
# requires ownership.  object_state=absent / config_name_shape=
# non_existent_name inherently fail (42704) because the baseline default for
# if_exists_clause is "present" but these values force if_exists_clause=
# "absent" so the missing configuration surfaces a 42704 instead of a notice.
# dependency_status=has_dependencies / dependency_context=
# config_used_by_other_object inherently fail (2BP01) under the default
# RESTRICT policy.  expected_status=failure is the declared failure marker
# (configuration held absent, IF EXISTS omitted).  error_type carries the
# same three failure classes (non_existent_without_if_exists /
# dependent_object_exists / insufficient_privilege).  Kept minimal
# (Option-A marginal); cross-product failures live in EXTENSION.
_SFV_FAILURE_VALUES: frozenset[tuple[str, str]] = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "absent"),
        ("config_name_shape", "non_existent_name"),
        ("authorization_path", "non_owner"),
        ("privilege_context", "non_owner_session"),
        ("dependency_context", "config_used_by_other_object"),
        ("dependency_status", "has_dependencies"),
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
            raise DropTextSearchConfigurationFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise DropTextSearchConfigurationFactorLoopError(
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


def _compile_grammar_obligations() -> list[DropTextSearchConfigurationFactorObligation]:
    rows: list[DropTextSearchConfigurationFactorObligation] = []
    for action in _GRAMMAR_ACTIONS:
        rows.append(
            DropTextSearchConfigurationFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPTEXTSEARCHCONFIGURATION-GRM|{action.grammar_branch_id}|"
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
        raise DropTextSearchConfigurationFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[DropTextSearchConfigurationFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("drop_text_search_configuration")
    if len(catalog_rows) != 35:
        raise DropTextSearchConfigurationFactorLoopError("canonical obligation count drift")
    rows: list[DropTextSearchConfigurationFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            DropTextSearchConfigurationFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"DROPTEXTSEARCHCONFIGURATION-SFV|{row.row_id}|{consumer}"
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


def _compile_risk_obligations() -> list[DropTextSearchConfigurationFactorObligation]:
    return [
        DropTextSearchConfigurationFactorObligation(
            ordinal=0,
            obligation_id=f"DROPTEXTSEARCHCONFIGURATION-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-droptsconfiguration:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[DropTextSearchConfigurationFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(
        b"drop-text-search-configuration-factor-obligations-v1\n"
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
# This table is a superset of _SFV_FAILURE_VALUES: the baseline marks ten
# pairs as expected_failure, but the bounded extension crosses privilege,
# object-state (configuration-missing), and dependency negatives whose
# SQLSTATEs are resolved here too.  SQLSTATEs are provisional in the no-DB
# phase (a later DB phase verifies on PG18.4).
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "drop_text_search_configuration_declared_failure",
    ),
    ("object_state", "absent"): (
        "42704",
        "undefined_text_search_configuration",
    ),
    ("config_name_shape", "non_existent_name"): (
        "42704",
        "undefined_text_search_configuration_name",
    ),
    ("authorization_path", "non_owner"): (
        "42501",
        "insufficient_privilege",
    ),
    ("privilege_context", "non_owner_session"): (
        "42501",
        "insufficient_privilege",
    ),
    ("dependency_context", "config_used_by_other_object"): (
        "2BP01",
        "dependent_objects_exist",
    ),
    ("dependency_status", "has_dependencies"): (
        "2BP01",
        "dependent_objects_exist",
    ),
    ("error_type", "non_existent_without_if_exists"): (
        "42704",
        "undefined_text_search_configuration",
    ),
    ("error_type", "dependent_object_exists"): (
        "2BP01",
        "dependent_objects_exist",
    ),
    ("error_type", "insufficient_privilege"): (
        "42501",
        "insufficient_privilege",
    ),
}


def _expected_failure_details(
    obligation: DropTextSearchConfigurationFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise DropTextSearchConfigurationFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


# Dense baseline defaults (all positive factor values).  if_exists_clause is
# "present" (the safe IF EXISTS form) and cascade_restrict is
# "default_restrict" (RESTRICT is the default behavior).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": "branch_drop_ts_config",
    "grammar_branch": "branch_1",
    "target_action": "drop_text_search_configuration",
    "object_state": "exists",
    "expected_status": "success",
    "if_exists_clause": "present",
    "cascade_restrict": "default_restrict",
    "authorization_path": "owner",
    "dependency_status": "no_dependencies",
    "config_name_shape": "simple_id",
    "privilege_context": "owner_session",
    "dependency_context": "no_dependencies",
    "error_type": "none",
    "verification_mode": "catalog_query",
    "cleanup_mode": "cascade_cleanup",
}

# Baseline primaries whose target configuration is intentionally absent, so
# the DROP surfaces a not-found error (42704) and the oracle asserts
# absence.  For these the renderer forces object_state=absent and
# if_exists_clause=absent so the missing configuration surfaces a hard error
# rather than an IF EXISTS notice.
_ABSENT_CONFIG_PRIMARIES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "absent"),
        ("config_name_shape", "non_existent_name"),
        ("error_type", "non_existent_without_if_exists"),
    }
)

# Baseline primaries whose session role is a non-owner, so the DROP
# surfaces a privilege error (42501).  The renderer forces
# authorization_path=non_owner and privilege_context=non_owner_session.
_PRIVILEGE_PRIMARIES = frozenset(
    {
        ("authorization_path", "non_owner"),
        ("privilege_context", "non_owner_session"),
        ("error_type", "insufficient_privilege"),
    }
)

# Baseline primaries that carry a dependent object, so the DROP surfaces a
# dependency error (2BP01) under the default RESTRICT policy.  The renderer
# forces dependency_status=has_dependencies,
# dependency_context=config_used_by_other_object, and
# cascade_restrict=default_restrict.
_DEPENDENCY_PRIMARIES = frozenset(
    {
        ("dependency_status", "has_dependencies"),
        ("dependency_context", "config_used_by_other_object"),
        ("error_type", "dependent_object_exists"),
    }
)


def _baseline_assignments(
    obligation: DropTextSearchConfigurationFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides."""

    branch = _consumer_branch_map()[obligation.consumer_action_id]
    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["grammar_branch"] = branch
    assignments["target_action"] = obligation.consumer_action_id
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value
    if (obligation.factor_key, obligation.value) in _ABSENT_CONFIG_PRIMARIES:
        assignments["object_state"] = "absent"
        assignments["if_exists_clause"] = "absent"
    if (obligation.factor_key, obligation.value) in _PRIVILEGE_PRIMARIES:
        assignments["authorization_path"] = "non_owner"
        assignments["privilege_context"] = "non_owner_session"
    if (obligation.factor_key, obligation.value) in _DEPENDENCY_PRIMARIES:
        assignments["dependency_status"] = "has_dependencies"
        assignments["dependency_context"] = "config_used_by_other_object"
        assignments["cascade_restrict"] = "default_restrict"
    if obligation.factor_key == "statement_branch":
        # The bare branch omits IF EXISTS; the IF EXISTS branch carries it.
        if obligation.value == "branch_drop_ts_config_if_exists":
            assignments["if_exists_clause"] = "present"
        else:
            assignments["if_exists_clause"] = "absent"
    if len(assignments) != len(set(assignments)):
        raise DropTextSearchConfigurationFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_drop_text_search_configuration_factor_loop_plan(
    repository_root: Path,
) -> DropTextSearchConfigurationFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_drop_text_search_configuration_factor_loop_obligations(root)
    cases: list[DropTextSearchConfigurationFactorCase] = []
    delegated: list[DropTextSearchConfigurationFactorObligation] = []
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
            DropTextSearchConfigurationFactorCase(
                ordinal=ordinal,
                case_id=f"DROPTEXTSEARCHCONFIGURATION{ordinal:05d}",
                sql_filename=f"DROPTEXTSEARCHCONFIGURATION{ordinal:05d}.sql",
                object_prefix=f"droptextsearchconfiguration_{ordinal:05d}_",
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
    plan = DropTextSearchConfigurationFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 38 or len(plan.delegated) != 0:
        raise DropTextSearchConfigurationFactorLoopError("factor loop plan count drift")
    if (
        len({row.primary_obligation_id for row in plan.cases})
        != 38
    ):
        raise DropTextSearchConfigurationFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 38:
        raise DropTextSearchConfigurationFactorLoopError("duplicate SQL filename")
    return plan


_PLAN_CACHE: dict[Path, DropTextSearchConfigurationFactorLoopPlan] = {}


def _build_drop_text_search_configuration_factor_plan_lazily(
    repository_root: Path,
) -> DropTextSearchConfigurationFactorLoopPlan:
    """Return a cached frozen plan, building it on first access."""

    root = Path(repository_root).resolve(strict=True)
    if root not in _PLAN_CACHE:
        _PLAN_CACHE[root] = build_drop_text_search_configuration_factor_loop_plan(root)
    return _PLAN_CACHE[root]


def compile_drop_text_search_configuration_factor_loop_obligations(
    repository_root: Path,
) -> tuple[DropTextSearchConfigurationFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        DropTextSearchConfigurationFactorObligation(
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
    if len(rows) != 38:
        raise DropTextSearchConfigurationFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise DropTextSearchConfigurationFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 1, "SFV": 35, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise DropTextSearchConfigurationFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise DropTextSearchConfigurationFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 38:
        raise DropTextSearchConfigurationFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise DropTextSearchConfigurationFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "DropTextSearchConfigurationFactorLoopError",
    "DropTextSearchConfigurationFactorObligation",
    "DropTextSearchConfigurationFactorCase",
    "DropTextSearchConfigurationFactorLoopPlan",
    "compile_drop_text_search_configuration_factor_loop_obligations",
    "build_drop_text_search_configuration_factor_loop_plan",
    "_obligation_multiset_sha256",
    "_build_drop_text_search_configuration_factor_plan_lazily",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
]
