"""Factor-value-loop obligation ledger for PostgreSQL 18.4 ALTER USER.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``ALTER USER``.  ALTER USER is a deprecated alias for ALTER ROLE that
changes a database role: it has 6 official synopsis branches (option
form, RENAME TO, SET config, SET FROM CURRENT, RESET config, RESET ALL).
The statement touches ``pg_catalog.pg_roles`` catalog rows, not
``pg_class`` relations, so column/table/relation coverage is
``not_applicable`` and there is no ``INV`` block.

Each local obligation becomes exactly one regress program.  Because
ALTER USER is a role DDL statement and the inventory declares no
``transaction_outcome`` factor, there are no ``RISK`` obligations.

The grammar ledger is self-contained: the 6 synopsis actions are frozen
inline.  The 69 canonical ``SFV`` rows are loaded from the shipped
applicability universe (``postgresql_18_4_factor_audit.tsv``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class AlterUserFactorLoopError(ValueError):
    """Raised when a frozen ALTER USER obligation input drifts."""


@dataclass(frozen=True)
class AlterUserGrammarAction:
    """One official target action form of the ALTER USER synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class AlterUserFactorObligation:
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
class AlterUserFactorCase:
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
class AlterUserFactorLoopPlan:
    obligations: tuple[AlterUserFactorObligation, ...]
    cases: tuple[AlterUserFactorCase, ...]
    delegated: tuple[AlterUserFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-alteruser.html).
_BRANCH_OPTION = "branch_option"
_BRANCH_RENAME = "branch_rename"
_BRANCH_SET_CONFIG = "branch_set_config"
_BRANCH_SET_FROM_CURRENT = "branch_set_from_current"
_BRANCH_RESET_CONFIG = "branch_reset_config"
_BRANCH_RESET_ALL = "branch_reset_all"

_DOC_SOURCE = "postgresql-18.4-doc:sql-alteruser"

# A representative branch_option action used as the baseline consumer for
# canonical factors that are not bound to one specific branch.  The option
# form is simple and exercises role attribute changes.
_REPRESENTATIVE_ACTION = "option_modify"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_OPTION: "option_modify",
    _BRANCH_RENAME: "rename",
    _BRANCH_SET_CONFIG: "set_config",
    _BRANCH_SET_FROM_CURRENT: "set_from_current",
    _BRANCH_RESET_CONFIG: "reset_config",
    _BRANCH_RESET_ALL: "reset_all",
}

# alter_action canonical value -> target action (value-dependent consumer).
_ALTER_ACTION_CONSUMER = {
    "option_modify": "option_modify",
    "rename": "rename",
    "set_config": "set_config",
    "set_from_current": "set_from_current",
    "reset_config": "reset_config",
    "reset_all": "reset_all",
}

# role_specification value -> target action (ALL only valid for SET/RESET).
_ROLE_SPECIFICATION_CONSUMER = {
    "named_role": "option_modify",
    "current_role": "option_modify",
    "current_user": "option_modify",
    "session_user": "option_modify",
    "all": "set_config",
}

# in_database_clause value -> target action (specified only for SET/RESET).
_IN_DATABASE_CONSUMER = {
    "omitted": "option_modify",
    "specified": "set_config",
}

# Canonical factor -> the action where the value is observable.  Factors
# whose consumer depends on the value (statement_branch, alter_action,
# role_specification, in_database_clause) are resolved in
# :func:`_canonical_consumer`.
_SFV_FACTOR_CONSUMER = {
    "statement_branch": _REPRESENTATIVE_ACTION,
    "object_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "alter_action": _REPRESENTATIVE_ACTION,
    "role_specification": _REPRESENTATIVE_ACTION,
    "in_database_clause": _REPRESENTATIVE_ACTION,
    "option_type": "option_modify",
    "role_name_shape": _REPRESENTATIVE_ACTION,
    "new_name_shape": "rename",
    "database_name_shape": "set_config",
    "config_param_shape": "set_config",
    "privilege_level": _REPRESENTATIVE_ACTION,
    "database_existence": "set_config",
    "nonexistent_role": _REPRESENTATIVE_ACTION,
    "duplicate_new_name": "rename",
    "nonexistent_database": "set_config",
    "insufficient_privilege": _REPRESENTATIVE_ACTION,
    "superuser_modification_by_non_superuser": "option_modify",
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected (provisional sqlstates -- DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "not_exists"),
        ("role_name_shape", "nonexistent_name"),
        ("nonexistent_role", "role_missing"),
        ("new_name_shape", "duplicate_name"),
        ("duplicate_new_name", "same_name_conflict"),
        ("database_name_shape", "nonexistent_name"),
        ("nonexistent_database", "database_missing"),
        ("database_existence", "database_not_exists"),
        ("config_param_shape", "invalid_param"),
        ("privilege_level", "non_createrole"),
        ("privilege_level", "non_owner"),
        ("insufficient_privilege", "lacks_createrole"),
        ("insufficient_privilege", "lacks_role_ownership"),
        (
            "superuser_modification_by_non_superuser",
            "non_superuser_attempting_superuser_toggle",
        ),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42704",
        "target_role_missing_provisional",
    ),
    ("object_state", "not_exists"): (
        "42704",
        "target_role_missing_provisional",
    ),
    ("role_name_shape", "nonexistent_name"): (
        "42704",
        "target_role_missing_provisional",
    ),
    ("nonexistent_role", "role_missing"): (
        "42704",
        "target_role_missing_provisional",
    ),
    ("new_name_shape", "duplicate_name"): (
        "42710",
        "duplicate_new_name_provisional",
    ),
    ("duplicate_new_name", "same_name_conflict"): (
        "42710",
        "duplicate_new_name_provisional",
    ),
    ("database_name_shape", "nonexistent_name"): (
        "3D000",
        "target_database_missing_provisional",
    ),
    ("nonexistent_database", "database_missing"): (
        "3D000",
        "target_database_missing_provisional",
    ),
    ("database_existence", "database_not_exists"): (
        "3D000",
        "target_database_missing_provisional",
    ),
    ("config_param_shape", "invalid_param"): (
        "42704",
        "invalid_configuration_parameter_provisional",
    ),
    ("privilege_level", "non_createrole"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("privilege_level", "non_owner"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("insufficient_privilege", "lacks_createrole"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("insufficient_privilege", "lacks_role_ownership"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    (
        "superuser_modification_by_non_superuser",
        "non_superuser_attempting_superuser_toggle",
    ): (
        "42501",
        "insufficient_privilege_provisional",
    ),
}


def _load_grammar_actions() -> tuple[AlterUserGrammarAction, ...]:
    """Freeze every ALTER USER synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "option_modify",
            _BRANCH_OPTION,
            "ALTER USER role_specification [ WITH ] option [ ... ]",
            "synopsis-option",
        ),
        (
            "rename",
            _BRANCH_RENAME,
            "ALTER USER name RENAME TO new_name",
            "synopsis-rename",
        ),
        (
            "set_config",
            _BRANCH_SET_CONFIG,
            (
                "ALTER USER { role_specification | ALL } "
                "[ IN DATABASE database_name ] SET "
                "configuration_parameter { TO | = } "
                "{ value | DEFAULT }"
            ),
            "synopsis-set-config",
        ),
        (
            "set_from_current",
            _BRANCH_SET_FROM_CURRENT,
            (
                "ALTER USER { role_specification | ALL } "
                "[ IN DATABASE database_name ] SET "
                "configuration_parameter FROM CURRENT"
            ),
            "synopsis-set-from-current",
        ),
        (
            "reset_config",
            _BRANCH_RESET_CONFIG,
            (
                "ALTER USER { role_specification | ALL } "
                "[ IN DATABASE database_name ] RESET "
                "configuration_parameter"
            ),
            "synopsis-reset-config",
        ),
        (
            "reset_all",
            _BRANCH_RESET_ALL,
            (
                "ALTER USER { role_specification | ALL } "
                "[ IN DATABASE database_name ] RESET ALL"
            ),
            "synopsis-reset-all",
        ),
    )
    actions = [
        AlterUserGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 6:
        raise AlterUserFactorLoopError("alter user action count drift")
    return tuple(actions)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterUserFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "alter_action":
        try:
            return _ALTER_ACTION_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterUserFactorLoopError(
                f"unknown alter_action value: {row.value}"
            ) from exc
    if row.factor == "role_specification":
        try:
            return _ROLE_SPECIFICATION_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterUserFactorLoopError(
                f"unknown role_specification value: {row.value}"
            ) from exc
    if row.factor == "in_database_clause":
        try:
            return _IN_DATABASE_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterUserFactorLoopError(
                f"unknown in_database_clause value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise AlterUserFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> list[AlterUserFactorObligation]:
    rows: list[AlterUserFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            AlterUserFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"AUSR-GRM|{action.grammar_branch_id}|"
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
    if len(rows) != 6:
        raise AlterUserFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[AlterUserFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("alter_user")
    if len(catalog_rows) != 69:
        raise AlterUserFactorLoopError("canonical obligation count drift")
    rows: list[AlterUserFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            AlterUserFactorObligation(
                ordinal=0,
                obligation_id=f"AUSR-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[AlterUserFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"alter-user-factor-obligations-v1\n")
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
    "option_modify": _BRANCH_OPTION,
    "rename": _BRANCH_RENAME,
    "set_config": _BRANCH_SET_CONFIG,
    "set_from_current": _BRANCH_SET_FROM_CURRENT,
    "reset_config": _BRANCH_RESET_CONFIG,
    "reset_all": _BRANCH_RESET_ALL,
}

# Dense baseline defaults (all positive success factor values).
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_OPTION,
    "grammar_branch": _BRANCH_OPTION,
    "target_action": "option_modify",
    "alter_action": "option_modify",
    "object_state": "exists",
    "expected_status": "success",
    "role_specification": "named_role",
    "in_database_clause": "omitted",
    "option_type": "superuser_toggle",
    "role_name_shape": "simple_id",
    "new_name_shape": "simple_id",
    "database_name_shape": "simple_id",
    "config_param_shape": "valid_param",
    "privilege_level": "createrole",
    "database_existence": "database_exists",
    "nonexistent_role": "role_exists",
    "duplicate_new_name": "no_conflict",
    "nonexistent_database": "database_exists",
    "insufficient_privilege": "has_privilege",
    "superuser_modification_by_non_superuser": "superuser_execution",
    "verification_mode": "catalog_query_pg_roles",
    "cleanup_mode": "revert_option",
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
    rns = a.get("role_name_shape", "simple_id")
    nr = a.get("nonexistent_role", "role_exists")
    nns = a.get("new_name_shape", "simple_id")
    dnn = a.get("duplicate_new_name", "no_conflict")
    dns = a.get("database_name_shape", "simple_id")
    nd = a.get("nonexistent_database", "database_exists")
    de = a.get("database_existence", "database_exists")
    pl = a.get("privilege_level", "createrole")
    ip = a.get("insufficient_privilege", "has_privilege")
    smns = a.get(
        "superuser_modification_by_non_superuser",
        "superuser_execution",
    )
    cps = a.get("config_param_shape", "valid_param")

    # Role-missing cluster: object_state / role_name_shape /
    # nonexistent_role
    if (
        os_ == "not_exists"
        or rns == "nonexistent_name"
        or nr == "role_missing"
    ):
        a["object_state"] = "not_exists"
        a["role_name_shape"] = "nonexistent_name"
        a["nonexistent_role"] = "role_missing"

    # Duplicate-name cluster: new_name_shape / duplicate_new_name
    if nns == "duplicate_name" or dnn == "same_name_conflict":
        a["new_name_shape"] = "duplicate_name"
        a["duplicate_new_name"] = "same_name_conflict"

    # Database-missing cluster: database_name_shape /
    # nonexistent_database / database_existence
    if (
        dns == "nonexistent_name"
        or nd == "database_missing"
        or de == "database_not_exists"
    ):
        a["database_name_shape"] = "nonexistent_name"
        a["nonexistent_database"] = "database_missing"
        a["database_existence"] = "database_not_exists"

    # Insufficient-privilege cluster: privilege_level /
    # insufficient_privilege
    if pl == "non_createrole" or ip == "lacks_createrole":
        a["privilege_level"] = "non_createrole"
        a["insufficient_privilege"] = "lacks_createrole"
    elif pl == "non_owner" or ip == "lacks_role_ownership":
        a["privilege_level"] = "non_owner"
        a["insufficient_privilege"] = "lacks_role_ownership"

    # superuser_modification_by_non_superuser <-> privilege non-createrole
    # + option_type=superuser_toggle
    ot = a.get("option_type", "superuser_toggle")
    if smns == "non_superuser_attempting_superuser_toggle":
        a["superuser_modification_by_non_superuser"] = (
            "non_superuser_attempting_superuser_toggle"
        )
        if ot == "superuser_toggle":
            a["privilege_level"] = "non_createrole"
            a["insufficient_privilege"] = "lacks_createrole"
    elif (
        pl in ("non_createrole", "non_owner")
        and ot == "superuser_toggle"
        and a.get("target_action") == "option_modify"
    ):
        a["superuser_modification_by_non_superuser"] = (
            "non_superuser_attempting_superuser_toggle"
        )

    # Invalid config param is standalone
    if cps == "invalid_param":
        a["config_param_shape"] = "invalid_param"


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _baseline_assignments(
    obligation: AlterUserFactorObligation,
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
        raise AlterUserFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: AlterUserFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise AlterUserFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_alter_user_factor_loop_plan(
    repository_root: Path,
) -> AlterUserFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_alter_user_factor_loop_obligations(root)
    cases: list[AlterUserFactorCase] = []
    delegated: list[AlterUserFactorObligation] = []
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
            AlterUserFactorCase(
                ordinal=ordinal,
                case_id=f"ALTERUSER{ordinal:05d}",
                sql_filename=f"ALTERUSER{ordinal:05d}.sql",
                object_prefix=f"alteruser_{ordinal:05d}_",
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
    plan = AlterUserFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 75 or len(plan.delegated) != 0:
        raise AlterUserFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 75:
        raise AlterUserFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 75:
        raise AlterUserFactorLoopError("duplicate SQL filename")
    return plan


def compile_alter_user_factor_loop_obligations(
    repository_root: Path,
) -> tuple[AlterUserFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        AlterUserFactorObligation(
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
    if len(rows) != 75:
        raise AlterUserFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise AlterUserFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 6, "SFV": 69}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise AlterUserFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise AlterUserFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 75:
        raise AlterUserFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise AlterUserFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "AlterUserFactorLoopError",
    "AlterUserGrammarAction",
    "AlterUserFactorObligation",
    "AlterUserFactorCase",
    "AlterUserFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_alter_user_factor_loop_obligations",
    "build_alter_user_factor_loop_plan",
    "_obligation_multiset_sha256",
]
