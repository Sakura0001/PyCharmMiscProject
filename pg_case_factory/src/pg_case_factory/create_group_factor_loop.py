"""Factor-value-loop obligation ledger for PostgreSQL 18.4 CREATE GROUP.

This module compiles the marginal ``GRM``/``SFV`` obligation ledger for
``CREATE GROUP``.  CREATE GROUP is a **deprecated alias for CREATE ROLE**
that defines a database role (a ``pg_catalog.pg_authid`` catalog row), not a
``pg_class`` relation.  The official synopsis has two branches: the simple
form (``CREATE GROUP name``) and the with-options form
(``CREATE GROUP name [ WITH ] option [ ... ]``).

The statement touches the ``pg_catalog.pg_authid`` catalog row (not a
relation), so column/table/relation coverage is ``not_applicable`` and
there is no ``INV`` block.  CREATE GROUP does not create tables, so the
bookend (DROP TABLE IF EXISTS) is never emitted; a residual
``SELECT 1 AS residual_check_no_objects;`` placeholder witnesses the
table-less nature of every program.

Each local obligation becomes exactly one regress program.  The 64
canonical ``SFV`` rows are loaded from the shipped applicability universe
(``postgresql_18_4_factor_audit.tsv``); the 2 ``GRM`` target forms are
frozen from the official synopsis branches.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .applicability import load_shipped_applicability_universe


class CreateGroupFactorLoopError(ValueError):
    """Raised when a frozen CREATE GROUP obligation input drifts."""


@dataclass(frozen=True)
class CreateGroupGrammarAction:
    """One official target action form of the CREATE GROUP synopsis."""

    action_id: str
    grammar_branch_id: str
    syntax_template: str
    source_locator: str


@dataclass(frozen=True)
class CreateGroupFactorObligation:
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
class CreateGroupFactorCase:
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
class CreateGroupFactorLoopPlan:
    obligations: tuple[CreateGroupFactorObligation, ...]
    cases: tuple[CreateGroupFactorCase, ...]
    delegated: tuple[CreateGroupFactorObligation, ...]
    obligation_multiset_sha256: str


# Official synopsis branches (PostgreSQL 18 sql-creategroup.html).
_BRANCH_SIMPLE = "branch_create_group_simple"
_BRANCH_WITH_OPTIONS = "branch_create_group_with_options"

_DOC_SOURCE = "postgresql-18.4-doc:sql-creategroup"

# A representative with-options action used as the baseline consumer for
# canonical factors that are not bound to one specific branch.
_REPRESENTATIVE_ACTION = "create_group_with_options"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = {
    _BRANCH_SIMPLE: "create_group_simple",
    _BRANCH_WITH_OPTIONS: "create_group_with_options",
}


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise CreateGroupFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "with_clause":
        return (
            "create_group_simple"
            if row.value == "omitted"
            else "create_group_with_options"
        )
    return _REPRESENTATIVE_ACTION


# Canonical (factor, value) pairs that reach the PostgreSQL target check and
# are rejected (provisional sqlstates -- DB phase verifies on PG 18.4).
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "already_exists"),
        ("group_name_shape", "duplicate_name"),
        ("duplicate_group_name", "same_name_conflict"),
        ("privilege_level", "non_createrole"),
        ("insufficient_privilege", "lacks_createrole"),
        ("referenced_role_existence", "role_not_exists"),
        ("referenced_role_shape", "nonexistent_role"),
        ("nonexistent_referenced_role", "role_missing"),
    }
)

# Provisional PG 18.4 SQLSTATE for each reachable expected-failure value.
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): (
        "42710",
        "duplicate_role_provisional",
    ),
    ("object_state", "already_exists"): (
        "42710",
        "duplicate_role_provisional",
    ),
    ("group_name_shape", "duplicate_name"): (
        "42710",
        "duplicate_role_provisional",
    ),
    ("duplicate_group_name", "same_name_conflict"): (
        "42710",
        "duplicate_role_provisional",
    ),
    ("privilege_level", "non_createrole"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("insufficient_privilege", "lacks_createrole"): (
        "42501",
        "insufficient_privilege_provisional",
    ),
    ("referenced_role_existence", "role_not_exists"): (
        "42704",
        "undefined_role_provisional",
    ),
    ("referenced_role_shape", "nonexistent_role"): (
        "42704",
        "undefined_role_provisional",
    ),
    ("nonexistent_referenced_role", "role_missing"): (
        "42704",
        "undefined_role_provisional",
    ),
}


def _load_grammar_actions() -> tuple[CreateGroupGrammarAction, ...]:
    """Freeze every CREATE GROUP synopsis target action."""

    rows: tuple[tuple[str, str, str, str], ...] = (
        (
            "create_group_simple",
            _BRANCH_SIMPLE,
            "CREATE GROUP name",
            "synopsis-create-group-simple",
        ),
        (
            "create_group_with_options",
            _BRANCH_WITH_OPTIONS,
            "CREATE GROUP name [ WITH ] option [ ... ]",
            "synopsis-create-group-with-options",
        ),
    )
    actions = [
        CreateGroupGrammarAction(
            action_id=action_id,
            grammar_branch_id=branch,
            syntax_template=syntax,
            source_locator=f"{_DOC_SOURCE}:{locator}",
        )
        for action_id, branch, syntax, locator in rows
    ]
    if len(actions) != 2:
        raise CreateGroupFactorLoopError("create group action count drift")
    return tuple(actions)


def _compile_grammar_obligations() -> list[CreateGroupFactorObligation]:
    rows: list[CreateGroupFactorObligation] = []
    for action in _load_grammar_actions():
        rows.append(
            CreateGroupFactorObligation(
                ordinal=0,
                obligation_id=(
                    f"CGP-GRM|{action.grammar_branch_id}|"
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
    if len(rows) != 2:
        raise CreateGroupFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[CreateGroupFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("create_group")
    if len(catalog_rows) != 64:
        raise CreateGroupFactorLoopError("canonical obligation count drift")
    rows: list[CreateGroupFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        is_failure = (row.factor, row.value) in _SFV_FAILURE_VALUES
        rows.append(
            CreateGroupFactorObligation(
                ordinal=0,
                obligation_id=f"CGP-SFV|{row.row_id}|{consumer}",
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
    rows: tuple[CreateGroupFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"create-group-factor-obligations-v1\n")
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
    "create_group_simple": _BRANCH_SIMPLE,
    "create_group_with_options": _BRANCH_WITH_OPTIONS,
}

# Dense baseline defaults (all positive factor values).  The T5 single-value
# boundary factors are derived in :func:`_derive_overlapping_factors`.
_BASELINE_DEFAULTS: dict[str, str] = {
    "statement_branch": _BRANCH_SIMPLE,
    "object_state": "not_exists",
    "expected_status": "success",
    "with_clause": "omitted",
    "superuser_option": "nosuperuser_default",
    "login_option": "nologin_default",
    "createdb_option": "nocreatedb_default",
    "createrole_option": "nocreaterole_default",
    "password_option": "omitted",
    "membership_option": "omitted",
    "deprecated_aliases": "no_deprecated_syntax",
    "group_name_shape": "simple_id",
    "referenced_role_shape": "simple_id",
    "password_shape": "valid_password",
    "privilege_level": "createrole_privilege",
    "referenced_role_existence": "role_exists",
    "duplicate_group_name": "no_conflict",
    "insufficient_privilege": "has_createrole",
    "nonexistent_referenced_role": "role_exists",
    "sysid_ignored": "no_sysid",
    "in_group_deprecated_alias": "use_in_role",
    "user_deprecated_alias": "use_role",
    "encrypted_keyword_ignored": "no_encrypted",
    "verification_mode": "pg_authid_catalog_query",
    "cleanup_mode": "drop_group",
}


def _count_baseline_failures(a: dict[str, str]) -> int:
    return sum(
        1
        for pair in _SFV_FAILURE_VALUES
        if a.get(pair[0]) == pair[1]
    )


def _derive_overlapping_factors(a: dict[str, str]) -> None:
    """Derive T5 boundary factors and expected_status from T1-T4 values.

    The T5 single-value factors describe the same scenario as their T1-T4
    counterparts.  When the primary factor is a T1-T4 value, the
    corresponding T5 value is derived; when the primary is a T5 value, the
    T1-T4 counterpart is derived.  This keeps the baseline assignment
    self-consistent so the render produces SQL that reaches the intended
    boundary.
    """

    # --- Group 1: duplicate scenario -------------------------------
    # object_state / duplicate_group_name / group_name_shape / expected_status
    if a.get("expected_status") == "failure":
        a["object_state"] = "already_exists"
        a["duplicate_group_name"] = "same_name_conflict"
        a["group_name_shape"] = "duplicate_name"
    if a.get("object_state") == "already_exists":
        a["duplicate_group_name"] = "same_name_conflict"
        a["group_name_shape"] = "duplicate_name"
    if a.get("duplicate_group_name") == "same_name_conflict":
        a["object_state"] = "already_exists"
        a["group_name_shape"] = "duplicate_name"
    if a.get("group_name_shape") == "duplicate_name":
        a["object_state"] = "already_exists"
        a["duplicate_group_name"] = "same_name_conflict"

    # --- Group 2: privilege ----------------------------------------
    if a.get("privilege_level") == "non_createrole":
        a["insufficient_privilege"] = "lacks_createrole"
    if a.get("insufficient_privilege") == "lacks_createrole":
        a["privilege_level"] = "non_createrole"
    # superuser_option=superuser requires the executor to be a superuser.
    if a.get("superuser_option") == "superuser":
        a["privilege_level"] = "superuser"
        a["insufficient_privilege"] = "has_createrole"

    # --- Group 3: referenced-role failure --------------------------
    # When the referenced role is missing, arm a standard IN ROLE clause so
    # the missing dependency is observable in the target statement.
    if a.get("referenced_role_existence") == "role_not_exists":
        a["membership_option"] = "in_role"
        a["nonexistent_referenced_role"] = "role_missing"
        a["referenced_role_shape"] = "nonexistent_role"
    if a.get("nonexistent_referenced_role") == "role_missing":
        a["membership_option"] = "in_role"
        a["referenced_role_existence"] = "role_not_exists"
        a["referenced_role_shape"] = "nonexistent_role"
    if a.get("referenced_role_shape") == "nonexistent_role":
        a["membership_option"] = "in_role"
        a["referenced_role_existence"] = "role_not_exists"
        a["nonexistent_referenced_role"] = "role_missing"

    # --- Group 4: coarse deprecated_aliases (T2 primary) ----------
    da = a.get("deprecated_aliases", "no_deprecated_syntax")
    if da == "in_group_alias":
        a["membership_option"] = "in_group"
        a["in_group_deprecated_alias"] = "use_in_group"
    elif da == "user_alias":
        a["membership_option"] = "user_clause"
        a["user_deprecated_alias"] = "use_user"
    elif da == "sysid_ignored":
        a["sysid_ignored"] = "sysid_ignored"
        a["membership_option"] = "omitted"
    elif da == "encrypted_ignored":
        a["encrypted_keyword_ignored"] = "encrypted_ignored"
        a["password_option"] = "encrypted_password"

    # --- Group 5: fine deprecated-alias boundary (T5 primary) ------
    if a.get("in_group_deprecated_alias") == "use_in_group":
        a["membership_option"] = "in_group"
        a["deprecated_aliases"] = "in_group_alias"
    if a.get("user_deprecated_alias") == "use_user":
        a["membership_option"] = "user_clause"
        a["deprecated_aliases"] = "user_alias"
    if a.get("sysid_ignored") == "sysid_ignored":
        a["deprecated_aliases"] = "sysid_ignored"
        a["membership_option"] = "omitted"
    if a.get("encrypted_keyword_ignored") == "encrypted_ignored":
        a["deprecated_aliases"] = "encrypted_ignored"
        a["password_option"] = "encrypted_password"

    # --- Group 6: membership_option -> deprecated aliases ----------
    mo = a.get("membership_option", "omitted")
    if mo == "in_role":
        a["in_group_deprecated_alias"] = "use_in_role"
        a["user_deprecated_alias"] = "use_role"
    elif mo == "in_group":
        a["in_group_deprecated_alias"] = "use_in_group"
        a["user_deprecated_alias"] = "use_role"
        a["deprecated_aliases"] = "in_group_alias"
    elif mo == "role_clause":
        a["user_deprecated_alias"] = "use_role"
        a["in_group_deprecated_alias"] = "use_in_role"
    elif mo == "user_clause":
        a["user_deprecated_alias"] = "use_user"
        a["in_group_deprecated_alias"] = "use_in_role"
        a["deprecated_aliases"] = "user_alias"
    elif mo == "admin_clause":
        a["user_deprecated_alias"] = "use_role"
        a["in_group_deprecated_alias"] = "use_in_role"
    else:  # omitted
        a["in_group_deprecated_alias"] = "use_in_role"
        a["user_deprecated_alias"] = "use_role"

    # --- Group 7: password_option / password_shape / encrypted -----
    if a.get("password_option") == "password_null":
        a["password_shape"] = "null_password"
    elif a.get("password_shape") == "null_password":
        a["password_option"] = "password_null"
    if a.get("password_option") == "encrypted_password":
        a["encrypted_keyword_ignored"] = "encrypted_ignored"
        a["deprecated_aliases"] = "encrypted_ignored"
        a["password_shape"] = "valid_password"

    # --- Group 8: statement_branch / with_clause ------------------
    if a.get("statement_branch") == _BRANCH_SIMPLE:
        a["with_clause"] = "omitted"
    if a.get("with_clause") == "specified":
        a["statement_branch"] = _BRANCH_WITH_OPTIONS

    # --- Derive expected_status from failure count -----------------
    failures = _count_baseline_failures(a)
    a["expected_status"] = "failure" if failures > 0 else "success"


def _baseline_assignments(
    obligation: CreateGroupFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per factor key; primary overrides."""

    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["statement_branch"] = _ACTION_BRANCH[
        obligation.consumer_action_id
    ]
    assignments[obligation.factor_key] = obligation.value
    _derive_overlapping_factors(assignments)
    failures = _count_baseline_failures(assignments)
    assignments["expected_status"] = (
        "failure" if failures > 0 else "success"
    )
    if len(assignments) != len(set(assignments)):
        raise CreateGroupFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def _expected_failure_details(
    obligation: CreateGroupFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[
            (obligation.factor_key, obligation.value)
        ]
    except KeyError as exc:
        raise CreateGroupFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


def build_create_group_factor_loop_plan(
    repository_root: Path,
) -> CreateGroupFactorLoopPlan:
    """Assign one stable local SQL program to every obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_create_group_factor_loop_obligations(root)
    cases: list[CreateGroupFactorCase] = []
    delegated: list[CreateGroupFactorObligation] = []
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
            CreateGroupFactorCase(
                ordinal=ordinal,
                case_id=f"CREATEGROUP{ordinal:05d}",
                sql_filename=f"CREATEGROUP{ordinal:05d}.sql",
                object_prefix=f"creategroup_{ordinal:05d}_",
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
    plan = CreateGroupFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(
            obligations
        ),
    )
    if len(plan.cases) != 66 or len(plan.delegated) != 0:
        raise CreateGroupFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 66:
        raise CreateGroupFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 66:
        raise CreateGroupFactorLoopError("duplicate SQL filename")
    return plan


def compile_create_group_factor_loop_obligations(
    repository_root: Path,
) -> tuple[CreateGroupFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
    )
    rows = tuple(
        CreateGroupFactorObligation(
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
    if len(rows) != 66:
        raise CreateGroupFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise CreateGroupFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 2, "SFV": 64}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise CreateGroupFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise CreateGroupFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"}
        for row in rows
    ) != 66:
        raise CreateGroupFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(
        row.disposition not in allowed_dispositions for row in rows
    ):
        raise CreateGroupFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "CreateGroupFactorLoopError",
    "CreateGroupGrammarAction",
    "CreateGroupFactorObligation",
    "CreateGroupFactorCase",
    "CreateGroupFactorLoopPlan",
    "_SFV_FAILURE_SQLSTATE",
    "_SFV_FAILURE_VALUES",
    "compile_create_group_factor_loop_obligations",
    "build_create_group_factor_loop_plan",
    "_obligation_multiset_sha256",
]
