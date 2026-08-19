"""Factor-value-loop obligation ledger for PostgreSQL 18.4 ALTER ROLE.

This module compiles the marginal ``GRM``/``SFV``/``RISK`` obligation ledger
for ``ALTER ROLE``.  ``alter_role.yaml`` marks column/table/relation coverage
``not_applicable``, so there is no ``INV`` block.  Each local obligation
becomes exactly one regress program; there are no delegated handoffs
because every reachable negative boundary is a real ``ALTER ROLE`` error
that belongs to this statement.

The six official synopsis branches and the 18 attribute options are NOT
re-emitted as GRM obligations: they are already canonical ``SFV`` rows
(``statement_branch`` / ``attribute_option``), so duplicating them would
break conservation (the ``alter_index`` anti-pattern).  Only the four pure
grammar modifiers -- the optional ``WITH`` keyword, the optional
``ENCRYPTED`` keyword, the one-vs-many action-list cardinality, and the
``TO`` vs ``=`` assignment spelling -- are frozen as GRM axes.

Privilege is modelled as a cluster: ``privilege_level``,
``privilege_requirement`` and ``role_membership_dependency`` are kept
consistent so a single non-superuser executor is the attributable cause
rather than three contradictory baseline values.  ``privilege_insufficient``
is a pure negative factor (every value is a failure mode), so it is set
only when it is the primary, never as an inert baseline.  The
``self_password_only`` path (``privilege_level=ordinary_role_self``) is a
SUCCESS path -- an ordinary role may ALTER its OWN password without
CREATEROLE -- and is therefore excluded from the privilege wall.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .alter_role_regress import (
    AlterRoleRegressError,
    STATEMENT_BRANCH_ACTIONS,
    load_alter_role_grammar_axes,
)
from .applicability import load_shipped_applicability_universe


class AlterRoleFactorLoopError(ValueError):
    """Raised when a frozen ALTER ROLE obligation input drifts."""


@dataclass(frozen=True)
class AlterRoleFactorObligation:
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
class AlterRoleFactorCase:
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
class AlterRoleFactorLoopPlan:
    obligations: tuple[AlterRoleFactorObligation, ...]
    cases: tuple[AlterRoleFactorCase, ...]
    delegated: tuple[AlterRoleFactorObligation, ...]
    obligation_multiset_sha256: str


# A representative branch_1 action used as the baseline consumer for
# factors whose consumer does not depend on the value.
_REPRESENTATIVE_ACTION = "with_option"

# statement_branch canonical value -> target action.
_STATEMENT_BRANCH_CONSUMER = dict(STATEMENT_BRANCH_ACTIONS)

# config_parameter_behavior canonical value -> the branch action it lives in.
_CONFIG_PARAMETER_BEHAVIOR_CONSUMER = {
    "set_value": "set_value",
    "set_default": "set_value",
    "set_from_current": "set_from_current",
    "reset_parameter": "reset_parameter",
    "reset_all": "reset_all",
    "all_roles": "set_value",
    "in_database_specific": "set_value",
}

# privilege_insufficient canonical value -> the branch action it lives in.
_PRIVILEGE_INSUFFICIENT_CONSUMER = {
    "ordinary_role_altering_other_role_attributes": "with_option",
    "createrole_altering_superuser": "with_option",
    "createrole_without_admin_option": "with_option",
    "ordinary_role_altering_other_role_config": "set_value",
    "bootstrap_superuser_property_change": "with_option",
}

# Canonical factor -> the action where the value is observable.  Factors
# whose consumer depends on the value (statement_branch,
# config_parameter_behavior, privilege_insufficient) are resolved in
# :func:`_canonical_consumer`.
_SFV_FACTOR_CONSUMER = {
    "role_state": _REPRESENTATIVE_ACTION,
    "expected_status": _REPRESENTATIVE_ACTION,
    "attribute_option": _REPRESENTATIVE_ACTION,
    "rename_behavior": "rename",
    "privilege_level": _REPRESENTATIVE_ACTION,
    "role_name_shape": _REPRESENTATIVE_ACTION,
    "new_name_shape": "rename",
    "config_parameter_shape": "set_value",
    "database_name_shape": "set_value",
    "table_column_index_involvement": _REPRESENTATIVE_ACTION,
    "privilege_requirement": _REPRESENTATIVE_ACTION,
    "config_parameter_dependency": "set_value",
    "role_membership_dependency": _REPRESENTATIVE_ACTION,
    "nonexistent_role": _REPRESENTATIVE_ACTION,
    "invalid_config_parameter": "set_value",
    "rename_current_session_user": "rename",
    "rename_clears_password": "rename",
    "password_security": _REPRESENTATIVE_ACTION,
    "verification_mode": _REPRESENTATIVE_ACTION,
    "cleanup_mode": _REPRESENTATIVE_ACTION,
}

# Canonical (factor, value) pairs that reach the PostgreSQL target check
# and are rejected.  Provisional SQLSTATEs (marked below) are verified
# against PG 18.4 in the DB phase.  The four BEHAVIOR assertions
# (rename_clears_password / password_security) are SUCCESS paths with
# state-checking oracles, so they are deliberately NOT failure values.
_SFV_FAILURE_VALUES = frozenset(
    {
        ("expected_status", "failure"),
        ("role_state", "non_existent"),
        ("role_name_shape", "non_existent_name"),
        ("new_name_shape", "existing_name_conflict"),
        ("privilege_level", "createrole_without_admin_option"),
        ("privilege_level", "ordinary_role_other"),
        ("privilege_insufficient", "ordinary_role_altering_other_role_attributes"),
        ("privilege_insufficient", "createrole_altering_superuser"),
        ("privilege_insufficient", "createrole_without_admin_option"),
        ("privilege_insufficient", "ordinary_role_altering_other_role_config"),
        ("privilege_insufficient", "bootstrap_superuser_property_change"),
        ("role_membership_dependency", "admin_option_not_granted"),
        ("invalid_config_parameter", "superuser_only_parameter_by_non_superuser"),
        ("invalid_config_parameter", "parameter_cannot_be_set_at_role_level"),
        ("invalid_config_parameter", "invalid_parameter_name"),
        ("config_parameter_shape", "invalid_parameter"),
        ("rename_current_session_user", "session_user_rename_blocked"),
    }
)


def _canonical_consumer(row) -> str:
    if row.factor == "statement_branch":
        try:
            return _STATEMENT_BRANCH_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterRoleFactorLoopError(
                f"unknown statement branch value: {row.value}"
            ) from exc
    if row.factor == "config_parameter_behavior":
        try:
            return _CONFIG_PARAMETER_BEHAVIOR_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterRoleFactorLoopError(
                f"unknown config_parameter_behavior value: {row.value}"
            ) from exc
    if row.factor == "privilege_insufficient":
        try:
            return _PRIVILEGE_INSUFFICIENT_CONSUMER[row.value]
        except KeyError as exc:
            raise AlterRoleFactorLoopError(
                f"unknown privilege_insufficient value: {row.value}"
            ) from exc
    try:
        return _SFV_FACTOR_CONSUMER[row.factor]
    except KeyError as exc:
        raise AlterRoleFactorLoopError(
            f"canonical factor has no consumer action: {row.factor}"
        ) from exc


def _compile_grammar_obligations() -> list[AlterRoleFactorObligation]:
    rows: list[AlterRoleFactorObligation] = []
    for axis in load_alter_role_grammar_axes():
        consumer = (
            _REPRESENTATIVE_ACTION
            if axis.action_id == "__outer_action__"
            else axis.action_id
        )
        factor_key = f"outer:{axis.axis_id}"
        for value in axis.values:
            rows.append(
                AlterRoleFactorObligation(
                    ordinal=0,
                    obligation_id=(
                        f"ALTERROLE-GRM|{axis.grammar_branch_id}|"
                        f"{axis.action_id}|{axis.axis_id}|{value}"
                    ),
                    kind="GRM",
                    factor_key=factor_key,
                    value=value,
                    consumer_action_id=consumer,
                    disposition="covered",
                    source_locator=axis.source_locator,
                )
            )
    if len(rows) != 8:
        raise AlterRoleFactorLoopError("grammar obligation count drift")
    return rows


def _compile_canonical_obligations(
    repository_root: Path,
) -> list[AlterRoleFactorObligation]:
    catalog_rows = load_shipped_applicability_universe(
        repository_root
    ).rows_for_statement("alter_role")
    if len(catalog_rows) != 98:
        raise AlterRoleFactorLoopError("canonical obligation count drift")
    rows: list[AlterRoleFactorObligation] = []
    for row in catalog_rows:
        consumer = _canonical_consumer(row)
        rows.append(
            AlterRoleFactorObligation(
                ordinal=0,
                obligation_id=f"ALTERROLE-SFV|{row.row_id}|{consumer}",
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


def _compile_risk_obligations() -> list[AlterRoleFactorObligation]:
    return [
        AlterRoleFactorObligation(
            ordinal=0,
            obligation_id=f"ALTERROLE-RISK|transaction|{value}",
            kind="RISK",
            factor_key="transaction_outcome",
            value=value,
            consumer_action_id=_REPRESENTATIVE_ACTION,
            disposition="covered",
            source_locator=(
                "postgresql-18.4-doc:sql-alterrole:transactional-ddl"
            ),
        )
        for value in ("commit", "rollback")
    ]


def _obligation_multiset_sha256(
    rows: tuple[AlterRoleFactorObligation, ...],
) -> str:
    digest = hashlib.sha256(b"alter-role-factor-obligations-v1\n")
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


def _renderer_factor_key(factor_key: str) -> str:
    """Map an obligation factor key to the renderer's flat factor namespace."""

    if factor_key.startswith("outer:"):
        return factor_key.split(":", 1)[1]
    return factor_key


# Verified / provisional PG 18.4 SQLSTATE for each reachable expected-failure
# value.  Entries tagged ``_provisional`` in the reason are verified against
# an isolated 18.4 instance in the DB phase (the no-DB ledger freezes a
# starting point the DB fork calibrates).
_SFV_FAILURE_SQLSTATE: dict[tuple[str, str], tuple[str, str]] = {
    ("expected_status", "failure"): ("42704", "target_role_missing"),
    ("role_state", "non_existent"): ("42704", "role_does_not_exist"),
    ("role_name_shape", "non_existent_name"): (
        "42704",
        "role_does_not_exist",
    ),
    ("new_name_shape", "existing_name_conflict"): (
        "42710",
        "duplicate_object",
    ),
    ("privilege_level", "createrole_without_admin_option"): (
        "42501",
        "permission_denied",
    ),
    ("privilege_level", "ordinary_role_other"): (
        "42501",
        "permission_denied",
    ),
    ("privilege_insufficient", "ordinary_role_altering_other_role_attributes"): (
        "42501",
        "permission_denied",
    ),
    ("privilege_insufficient", "createrole_altering_superuser"): (
        "42501",
        "permission_denied",
    ),
    ("privilege_insufficient", "createrole_without_admin_option"): (
        "42501",
        "permission_denied",
    ),
    ("privilege_insufficient", "ordinary_role_altering_other_role_config"): (
        "42501",
        "permission_denied",
    ),
    ("privilege_insufficient", "bootstrap_superuser_property_change"): (
        "42501",
        "bootstrap_superuser_property_is_immutable",
    ),
    ("role_membership_dependency", "admin_option_not_granted"): (
        "42501",
        "permission_denied",
    ),
    ("invalid_config_parameter", "superuser_only_parameter_by_non_superuser"): (
        "42501",
        "permission_denied_to_set_parameter_provisional",
    ),
    ("invalid_config_parameter", "parameter_cannot_be_set_at_role_level"): (
        "42809",
        "object_not_in_prerequisite_state_provisional",
    ),
    ("invalid_config_parameter", "invalid_parameter_name"): (
        "42704",
        "unrecognized_configuration_parameter_provisional",
    ),
    ("config_parameter_shape", "invalid_parameter"): (
        "42704",
        "unrecognized_configuration_parameter_provisional",
    ),
    ("rename_current_session_user", "session_user_rename_blocked"): (
        "42501",
        "session_user_rename_blocked_provisional",
    ),
}


def _expected_failure_details(
    obligation: AlterRoleFactorObligation,
) -> tuple[str, str]:
    try:
        return _SFV_FAILURE_SQLSTATE[(obligation.factor_key, obligation.value)]
    except KeyError as exc:
        raise AlterRoleFactorLoopError(
            "missing expected-failure SQLSTATE for "
            f"{obligation.factor_key}={obligation.value}"
        ) from exc


# Branch action -> grammar branch id used by the renderer.
_ACTION_BRANCH = {action: branch for branch, action in STATEMENT_BRANCH_ACTIONS}

# The success (superuser) privilege profile -- the default for every
# non-privilege primary.
_PRIVILEGE_SUFFICIENT = {
    "privilege_level": "superuser",
    "privilege_requirement": "superuser_required",
    "role_membership_dependency": "admin_option_granted",
}

# Per-(factor, value) privilege profiles.  When the primary is one of these,
# the cluster is set to the matching (possibly failure) state so attribution
# stays to a single non-superuser executor.  ordinary_role_self is a SUCCESS
# path (self password) and is listed so its cluster stays consistent.
_PRIVILEGE_PROFILE: dict[tuple[str, str], dict[str, str]] = {
    ("privilege_level", "superuser"): _PRIVILEGE_SUFFICIENT,
    ("privilege_level", "createrole_with_admin_option"): {
        "privilege_level": "createrole_with_admin_option",
        "privilege_requirement": "createrole_with_admin_option_required",
        "role_membership_dependency": "admin_option_granted",
    },
    ("privilege_level", "ordinary_role_self"): {
        "privilege_level": "ordinary_role_self",
        "privilege_requirement": "self_password_only",
        "role_membership_dependency": "admin_option_granted",
    },
    ("privilege_level", "createrole_without_admin_option"): {
        "privilege_level": "createrole_without_admin_option",
        "privilege_requirement": "createrole_with_admin_option_required",
        "role_membership_dependency": "admin_option_not_granted",
    },
    ("privilege_level", "ordinary_role_other"): {
        "privilege_level": "ordinary_role_other",
        "privilege_requirement": "createrole_with_admin_option_required",
        "role_membership_dependency": "admin_option_granted",
    },
    ("privilege_requirement", "self_password_only"): {
        "privilege_level": "ordinary_role_self",
        "privilege_requirement": "self_password_only",
        "role_membership_dependency": "admin_option_granted",
    },
    ("privilege_requirement", "all_roles_requires_superuser"): {
        "privilege_level": "superuser",
        "privilege_requirement": "all_roles_requires_superuser",
        "role_membership_dependency": "admin_option_granted",
    },
    ("privilege_requirement", "createrole_with_admin_option_required"): {
        "privilege_level": "createrole_with_admin_option",
        "privilege_requirement": "createrole_with_admin_option_required",
        "role_membership_dependency": "admin_option_granted",
    },
    ("privilege_insufficient", "ordinary_role_altering_other_role_attributes"): {
        "privilege_level": "ordinary_role_other",
        "privilege_requirement": "createrole_with_admin_option_required",
        "role_membership_dependency": "admin_option_granted",
    },
    ("privilege_insufficient", "createrole_altering_superuser"): {
        "privilege_level": "createrole_with_admin_option",
        "privilege_requirement": "superuser_required",
        "role_membership_dependency": "admin_option_granted",
    },
    ("privilege_insufficient", "createrole_without_admin_option"): {
        "privilege_level": "createrole_without_admin_option",
        "privilege_requirement": "createrole_with_admin_option_required",
        "role_membership_dependency": "admin_option_not_granted",
    },
    ("privilege_insufficient", "ordinary_role_altering_other_role_config"): {
        "privilege_level": "ordinary_role_other",
        "privilege_requirement": "createrole_with_admin_option_required",
        "role_membership_dependency": "admin_option_granted",
    },
    ("privilege_insufficient", "bootstrap_superuser_property_change"): {
        "privilege_level": "superuser",
        "privilege_requirement": "superuser_required",
        "role_membership_dependency": "admin_option_granted",
    },
    ("role_membership_dependency", "admin_option_not_granted"): {
        "privilege_level": "createrole_without_admin_option",
        "privilege_requirement": "createrole_with_admin_option_required",
        "role_membership_dependency": "admin_option_not_granted",
    },
    ("role_membership_dependency", "admin_option_granted"): _PRIVILEGE_SUFFICIENT,
    ("role_membership_dependency", "role_is_member_of_another"): {
        "privilege_level": "superuser",
        "privilege_requirement": "createrole_with_admin_option_required",
        "role_membership_dependency": "role_is_member_of_another",
    },
}

# privilege_level values that fire the privilege wall in the extension
# (ordinary_role_self is the self-password SUCCESS path and is excluded).
_PRIVILEGE_FAILURE_LEVELS = frozenset(
    {"createrole_without_admin_option", "ordinary_role_other"}
)

# The four BEHAVIOR assertions: SUCCESS paths with state-checking oracles,
# frozen so the DB phase can verify rolpassword / catalog state.
_BEHAVIOR_ASSERTIONS = frozenset(
    {
        ("rename_clears_password", "md5_password_cleared_on_rename"),
        ("rename_clears_password", "scram_password_preserved_on_rename"),
        ("password_security", "password_null_removes_password"),
        ("password_security", "plaintext_password_in_sql"),
    }
)

_BASELINE_DEFAULTS: dict[str, str] = {
    "role_state": "exists",
    "expected_status": "success",
    "attribute_option": "login",
    "rename_behavior": "rename_to_new_name",
    "privilege_level": "superuser",
    "privilege_requirement": "superuser_required",
    "role_membership_dependency": "admin_option_granted",
    "role_name_shape": "simple_name",
    "new_name_shape": "simple_name",
    "config_parameter_shape": "valid_parameter",
    "database_name_shape": "omitted_no_database_clause",
    "table_column_index_involvement": "not_involved",
    "config_parameter_dependency": "settable_by_any_role",
    "verification_mode": "pg_roles_catalog",
    "cleanup_mode": "drop_role",
    "with_keyword": "absent",
    "encrypted_keyword": "omitted",
    "action_list_cardinality": "one_action",
    "set_assignment_form": "to_value",
}


def _apply_privilege_cluster(
    assignments: dict[str, str],
    obligation: AlterRoleFactorObligation,
) -> None:
    """Keep the privilege factors consistent with the primary value."""

    profile = _PRIVILEGE_PROFILE.get(
        (obligation.factor_key, obligation.value)
    )
    if profile is None:
        # invalid_config_parameter / config_parameter_dependency primaries
        # surface a non-privilege failure under the superuser baseline, but
        # the superuser_only_parameter_by_non_superuser case must run as a
        # non-superuser so the 42501 fires.
        if (
            obligation.factor_key == "invalid_config_parameter"
            and obligation.value
            == "superuser_only_parameter_by_non_superuser"
        ):
            profile = {
                "privilege_level": "ordinary_role_other",
                "privilege_requirement": "superuser_required",
                "role_membership_dependency": "admin_option_granted",
            }
        else:
            profile = _PRIVILEGE_SUFFICIENT
    assignments.update(profile)


def _branch_defaults(action: str) -> dict[str, str]:
    """Branch-specific canonical defaults beyond the shared baseline."""

    branch = _ACTION_BRANCH[action]
    extras: dict[str, str] = {"statement_branch": branch}
    if action == "with_option":
        extras["config_parameter_behavior"] = "set_value"
    elif action == "rename":
        extras["config_parameter_behavior"] = "set_value"
    elif action == "set_value":
        extras["config_parameter_behavior"] = "set_value"
        extras["config_parameter_shape"] = "valid_parameter"
    elif action == "set_from_current":
        extras["config_parameter_behavior"] = "set_from_current"
        extras["config_parameter_shape"] = "valid_parameter"
    elif action == "reset_parameter":
        extras["config_parameter_behavior"] = "reset_parameter"
        extras["config_parameter_shape"] = "valid_parameter"
    elif action == "reset_all":
        extras["config_parameter_behavior"] = "reset_all"
        extras["config_parameter_shape"] = "valid_parameter"
    return extras


def _baseline_assignments(
    obligation: AlterRoleFactorObligation,
) -> tuple[tuple[str, str], ...]:
    """One legal baseline value per action-applicable key; primary overrides."""

    action = obligation.consumer_action_id
    assignments: dict[str, str] = dict(_BASELINE_DEFAULTS)
    assignments["grammar_branch"] = _ACTION_BRANCH[action]
    assignments["target_action"] = action
    assignments.update(_branch_defaults(action))
    _apply_privilege_cluster(assignments, obligation)
    # The primary value overrides exactly one key.
    assignments[_renderer_factor_key(obligation.factor_key)] = obligation.value
    # (expected_status, failure) is a meta flag with no concrete cause of its
    # own; give it the documented default failure cause (target_role_missing)
    # so the rendered target actually fails (42704).
    if (
        obligation.factor_key == "expected_status"
        and obligation.value == "failure"
    ):
        assignments["role_state"] = "non_existent"
    # The bootstrap-superuser case targets the immutable bootstrap superuser.
    if (
        obligation.factor_key == "privilege_insufficient"
        and obligation.value == "bootstrap_superuser_property_change"
    ):
        assignments["attribute_option"] = "nosuperuser"
    # The self-password behavior targets the session user's own password.
    if obligation.factor_key == "password_security":
        assignments["attribute_option"] = (
            "password_null"
            if obligation.value == "password_null_removes_password"
            else "encrypted_password"
        )
    if (
        obligation.factor_key == "rename_clears_password"
        and obligation.value == "md5_password_cleared_on_rename"
    ):
        assignments["attribute_option"] = "encrypted_password"
    if (
        obligation.factor_key == "rename_clears_password"
        and obligation.value == "scram_password_preserved_on_rename"
    ):
        assignments["attribute_option"] = "encrypted_password"
    if len(assignments) != len(set(assignments)):
        raise AlterRoleFactorLoopError("duplicate baseline factor key")
    return tuple(sorted(assignments.items()))


def build_alter_role_factor_loop_plan(
    repository_root: Path,
) -> AlterRoleFactorLoopPlan:
    """Assign one stable local SQL program to every non-delegated obligation."""

    root = Path(repository_root).resolve(strict=True)
    obligations = compile_alter_role_factor_loop_obligations(root)
    cases: list[AlterRoleFactorCase] = []
    delegated: list[AlterRoleFactorObligation] = []
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
            AlterRoleFactorCase(
                ordinal=ordinal,
                case_id=f"ALTERROLE{ordinal:04d}",
                sql_filename=f"ALTERROLE{ordinal:04d}.sql",
                object_prefix=f"alterrole_{ordinal:04d}_",
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
    plan = AlterRoleFactorLoopPlan(
        obligations=obligations,
        cases=tuple(cases),
        delegated=tuple(delegated),
        obligation_multiset_sha256=_obligation_multiset_sha256(obligations),
    )
    if len(plan.cases) != 108 or len(plan.delegated) != 0:
        raise AlterRoleFactorLoopError("factor loop plan count drift")
    if len({row.primary_obligation_id for row in plan.cases}) != 108:
        raise AlterRoleFactorLoopError("local obligation mapping drift")
    if len({row.sql_filename for row in plan.cases}) != 108:
        raise AlterRoleFactorLoopError("duplicate SQL filename")
    return plan


def compile_alter_role_factor_loop_obligations(
    repository_root: Path,
) -> tuple[AlterRoleFactorObligation, ...]:
    """Compile the exact marginal obligation ledger in frozen source order."""

    root = Path(repository_root).resolve(strict=True)
    unordered_rows = (
        _compile_grammar_obligations()
        + _compile_canonical_obligations(root)
        + _compile_risk_obligations()
    )
    rows = tuple(
        AlterRoleFactorObligation(
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
    if len(rows) != 108:
        raise AlterRoleFactorLoopError("obligation count drift")
    if len({row.obligation_id for row in rows}) != len(rows):
        raise AlterRoleFactorLoopError("duplicate obligation id")
    expected_kind_counts = {"GRM": 8, "SFV": 98, "RISK": 2}
    if Counter(row.kind for row in rows) != expected_kind_counts:
        raise AlterRoleFactorLoopError("obligation kind count drift")
    if sum(row.disposition == "delegated" for row in rows) != 0:
        raise AlterRoleFactorLoopError("delegated obligation count drift")
    if sum(
        row.disposition in {"covered", "expected_failure"} for row in rows
    ) != 108:
        raise AlterRoleFactorLoopError("local obligation count drift")
    allowed_dispositions = {"covered", "expected_failure", "delegated"}
    if any(row.disposition not in allowed_dispositions for row in rows):
        raise AlterRoleFactorLoopError("unknown obligation disposition")
    return rows


__all__ = [
    "AlterRoleFactorLoopError",
    "AlterRoleFactorObligation",
    "AlterRoleFactorCase",
    "AlterRoleFactorLoopPlan",
    "compile_alter_role_factor_loop_obligations",
    "build_alter_role_factor_loop_plan",
    "_obligation_multiset_sha256",
]
