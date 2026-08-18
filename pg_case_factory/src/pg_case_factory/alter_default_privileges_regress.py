"""PostgreSQL 18 ALTER DEFAULT PRIVILEGES conditional-product regress design."""

from __future__ import annotations

import itertools
from typing import Mapping

from .remaining_statement_regress import (
    FactorValueDecision,
    RemainingStatementRegressError,
    StatementRegressCase,
    StatementRegressPlan,
    _header,
)
from .statement_factor_cycle import StatementCycleEntry, StatementFactorCycleSnapshot


_SCHEMA_CAPABLE = frozenset(
    {"TABLES", "SEQUENCES", "FUNCTIONS", "ROUTINES", "TYPES"}
)
_CLASS_PRIVILEGES = (
    ("TABLES", "single_privilege", "SELECT"),
    ("TABLES", "multiple_privileges", "SELECT, INSERT"),
    ("TABLES", "all_privileges", "ALL PRIVILEGES"),
    ("TABLES", "public", "SELECT"),
    ("TABLES", "maintain_privilege", "MAINTAIN"),
    ("SEQUENCES", "single_privilege", "USAGE"),
    ("SEQUENCES", "multiple_privileges", "USAGE, SELECT"),
    ("SEQUENCES", "all_privileges", "ALL PRIVILEGES"),
    ("SEQUENCES", "public", "USAGE"),
    ("FUNCTIONS", "single_privilege", "EXECUTE"),
    ("FUNCTIONS", "all_privileges", "ALL PRIVILEGES"),
    ("FUNCTIONS", "public", "EXECUTE"),
    ("ROUTINES", "single_privilege", "EXECUTE"),
    ("ROUTINES", "all_privileges", "ALL PRIVILEGES"),
    ("ROUTINES", "public", "EXECUTE"),
    ("TYPES", "single_privilege", "USAGE"),
    ("TYPES", "all_privileges", "ALL PRIVILEGES"),
    ("TYPES", "public", "USAGE"),
    ("SCHEMAS", "single_privilege", "USAGE"),
    ("SCHEMAS", "multiple_privileges", "USAGE, CREATE"),
    ("SCHEMAS", "all_privileges", "ALL PRIVILEGES"),
    ("SCHEMAS", "public", "USAGE"),
    ("LARGE_OBJECTS", "single_privilege", "SELECT"),
    ("LARGE_OBJECTS", "multiple_privileges", "SELECT, UPDATE"),
    ("LARGE_OBJECTS", "all_privileges", "ALL PRIVILEGES"),
    ("LARGE_OBJECTS", "public", "SELECT"),
    ("LARGE_OBJECTS", "large_object_select_update", "SELECT, UPDATE"),
)
_BASE_PRIVILEGE = {
    "TABLES": "SELECT",
    "SEQUENCES": "USAGE",
    "FUNCTIONS": "EXECUTE",
    "ROUTINES": "EXECUTE",
    "TYPES": "USAGE",
    "SCHEMAS": "USAGE",
    "LARGE_OBJECTS": "SELECT",
}
_ALLOWED_PRIVILEGES = {
    "TABLES": frozenset(
        {
            "SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE",
            "REFERENCES", "TRIGGER", "MAINTAIN",
        }
    ),
    "SEQUENCES": frozenset({"USAGE", "SELECT", "UPDATE"}),
    "FUNCTIONS": frozenset({"EXECUTE"}),
    "ROUTINES": frozenset({"EXECUTE"}),
    "TYPES": frozenset({"USAGE"}),
    "SCHEMAS": frozenset({"USAGE", "CREATE"}),
    "LARGE_OBJECTS": frozenset({"SELECT", "UPDATE"}),
}
_PRIVILEGE_UNIVERSE = (
    "SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES",
    "TRIGGER", "MAINTAIN", "USAGE", "EXECUTE", "CREATE",
)
_FOR_SUCCESS = (
    ("omitted_current_role", "omitted", "not_applicable"),
    ("single_target_role", "role_single", "simple_id"),
    ("single_target_role", "role_single", "quoted_id"),
    ("multiple_target_roles", "role_multiple", "simple_id"),
    ("multiple_target_roles", "role_multiple", "quoted_id"),
    ("for_user_keyword", "user_single", "simple_id"),
    ("for_user_keyword", "user_single", "quoted_id"),
)
_SCHEMA_SUCCESS = (
    ("omitted_global", "omitted", "not_applicable"),
    ("single_schema", "single", "simple_id"),
    ("multiple_schemas", "multiple", "simple_id"),
)
_ACTION_MODES = (
    ("grant", "grant_omitted", "omitted", None, None),
    ("grant", "grant_with_option", "with_grant_option", None, None),
    ("revoke", "revoke_plain_default", None, "omitted", "omitted_default_restrict"),
    ("revoke", "revoke_plain_cascade", None, "omitted", "cascade"),
    ("revoke", "revoke_plain_restrict", None, "omitted", "restrict"),
    ("revoke", "revoke_option_default", None, "grant_option_for", "omitted_default_restrict"),
    ("revoke", "revoke_option_cascade", None, "grant_option_for", "cascade"),
    ("revoke", "revoke_option_restrict", None, "grant_option_for", "restrict"),
)
_RECIPIENT_VARIANTS = (
    ("simple_id", "omitted", "simple"),
    ("simple_id", "specified_group", "simple_group"),
    ("quoted_id", "omitted", "quoted"),
    ("quoted_id", "specified_group", "quoted_group"),
    ("public", "omitted", "public"),
    ("group_role_name", "omitted", "group_role"),
    ("group_role_name", "specified_group", "group_role_group"),
)
_ACTORS = ("superuser", "target_role_owner", "role_member", "non_member")


def _tokens(*values: str | None) -> tuple[str, ...]:
    result: list[str] = []
    keys: set[str] = set()
    for token in values:
        if token is None:
            continue
        key = token.split("=", 1)[0]
        if key in keys:
            raise RemainingStatementRegressError(
                f"ALTER DEFAULT PRIVILEGES case binds factor {key!r} twice"
            )
        keys.add(key)
        result.append(token)
    return tuple(result)


def _status(outcome: str) -> str:
    return f"expected_status={'success' if outcome == 'success' else 'failure'}"


def _action_tokens(
    operation: str,
    grant_option: str | None,
    revoke_option: str | None,
    behavior: str | None,
) -> tuple[str, ...]:
    return _tokens(
        f"operation_type={operation}",
        f"grant_option={grant_option}" if grant_option is not None else None,
        (
            f"revoke_grant_option_for={revoke_option}"
            if revoke_option is not None else None
        ),
        (
            f"revoke_cascade_restrict={behavior}"
            if behavior is not None else None
        ),
    )


def _for_tokens(value: str, name_shape: str) -> tuple[str, ...]:
    return _tokens(
        f"for_role_clause={value}",
        (
            f"target_role_name_shape={name_shape}"
            if name_shape != "not_applicable" else None
        ),
        (
            "nonexistent_target_role=role_not_exists"
            if value == "nonexistent_target_role"
            else "nonexistent_target_role=role_exists"
        ),
    )


def _schema_tokens(
    value: str,
    name_shape: str,
    *,
    conflict: bool = False,
) -> tuple[str, ...]:
    return _tokens(
        f"in_schema_clause={value}",
        (
            f"schema_name_shape={name_shape}"
            if name_shape != "not_applicable" else None
        ),
        (
            "schema_existence=schema_not_exists"
            if value == "nonexistent_schema" else "schema_existence=schema_exists"
        ),
        (
            "nonexistent_schema=schema_not_exists"
            if value == "nonexistent_schema" else "nonexistent_schema=schema_exists"
        ),
        (
            "in_schema_on_schemas=in_schema_with_schemas_class"
            if conflict else "in_schema_on_schemas=no_conflict"
        ),
    )


def _recipient_tokens(shape: str, group: str, *, exists: bool = True) -> tuple[str, ...]:
    return _tokens(
        f"recipient_role_name_shape={shape}",
        f"group_keyword={group}",
        f"role_existence={'role_exists' if exists else 'role_not_exists'}",
    )


def _actor_tokens(actor: str) -> tuple[str, ...]:
    authorized = actor != "non_member"
    return _tokens(
        f"privilege_level={actor}",
        f"privilege_denied={'authorized_success' if authorized else 'unauthorized_failure'}",
        f"role_not_member_of_target_role={'is_member' if authorized else 'is_not_member'}",
    )


def _verification_token(group: str, outcome: str, ordinal: int) -> str:
    if outcome == "expected_failure":
        return "verification_mode=error_assertion"
    if group in {
        "additive_semantics_product", "existing_object_unchanged_product",
        "pg18_reference_product",
    }:
        return "verification_mode=create_object_and_verify_privileges"
    if ordinal % 11 == 0:
        return "verification_mode=psql_ddp_command"
    return "verification_mode=catalog_query_pg_default_acl"


def _cleanup_token(ordinal: int) -> str:
    return (
        "cleanup_mode="
        + ("revoke_default_privileges", "drop_role_owned_by", "drop_schema")[(ordinal - 1) % 3]
    )


def _case(
    ordinal: int,
    *,
    group: str,
    axes: Mapping[str, str],
    tokens: tuple[str, ...],
    outcome: str,
    sqlstate: str,
    strategy: str,
) -> StatementRegressCase:
    number = f"{ordinal:05d}"
    completed_tokens = _tokens(
        *tokens,
        _status(outcome),
        _verification_token(group, outcome, ordinal),
        _cleanup_token(ordinal),
    )
    return StatementRegressCase(
        ordinal=ordinal,
        case_id=f"ALTERDEFAULTPRIVILEGES{number}",
        sql_filename=f"ALTERDEFAULTPRIVILEGES{number}.sql",
        object_prefix=f"alterdefaultprivileges_{number}_",
        case_group=group,
        case_type="expected_failure" if outcome == "expected_failure" else "success",
        outcome=outcome,
        execution_profile="same_session_multiphase",
        derived_axes={**dict(axes), "expected_sqlstate": sqlstate},
        factor_values=completed_tokens,
        combination_strategy=strategy,
        description=(
            "ALTER DEFAULT PRIVILEGES conditional product: "
            + ", ".join(f"{key}={value}" for key, value in sorted(axes.items()))
        ),
        expected_anchor=f"SQLSTATE {sqlstate}; pg_default_acl, future-object, and cleanup oracles",
    )


def _base_tokens(
    *,
    operation: str,
    object_class: str,
    privilege_binding: str,
    grant_option: str | None,
    revoke_option: str | None,
    behavior: str | None,
    for_value: str,
    target_shape: str,
    schema_value: str,
    schema_shape: str,
    recipient_shape: str,
    group_keyword: str,
    recipient_exists: bool = True,
    conflict: bool = False,
) -> tuple[str, ...]:
    return _tokens(
        *_action_tokens(operation, grant_option, revoke_option, behavior),
        f"object_class={object_class}",
        f"privilege_set={privilege_binding}",
        *_for_tokens(for_value, target_shape),
        *_schema_tokens(schema_value, schema_shape, conflict=conflict),
        *_recipient_tokens(recipient_shape, group_keyword, exists=recipient_exists),
        (
            "routines_vs_functions=functions_keyword"
            if object_class == "FUNCTIONS" else
            "routines_vs_functions=routines_keyword"
            if object_class == "ROUTINES" else None
        ),
    )


def _build_cases() -> tuple[StatementRegressCase, ...]:
    cases: list[StatementRegressCase] = []

    def add(
        group: str,
        axes: Mapping[str, str],
        tokens: tuple[str, ...],
        outcome: str,
        sqlstate: str,
        strategy: str,
    ) -> None:
        cases.append(
            _case(
                len(cases) + 1,
                group=group,
                axes=axes,
                tokens=tokens,
                outcome=outcome,
                sqlstate=sqlstate,
                strategy=strategy,
            )
        )

    # 3,528: every applicable T1/T2 official grammar cell.  expected_status
    # is derived; PUBLIC + WITH GRANT OPTION is a real 0LP01 cell.
    for object_class, privilege_binding, privilege_sql in _CLASS_PRIVILEGES:
        schema_scopes = _SCHEMA_SUCCESS if object_class in _SCHEMA_CAPABLE else _SCHEMA_SUCCESS[:1]
        for (
            operation,
            action_mode,
            grant_option,
            revoke_option,
            behavior,
        ), (for_value, for_scope, target_shape), (
            schema_value, schema_scope, schema_shape
        ) in itertools.product(_ACTION_MODES, _FOR_SUCCESS, schema_scopes):
            selector = len(cases) % len(_RECIPIENT_VARIANTS)
            if privilege_binding == "public":
                recipient_shape, group_keyword, recipient = _RECIPIENT_VARIANTS[4]
            else:
                recipient_shape, group_keyword, recipient = _RECIPIENT_VARIANTS[selector]
            public_grant_option = (
                operation == "grant"
                and grant_option == "with_grant_option"
                and recipient == "public"
            )
            outcome = "expected_failure" if public_grant_option else "success"
            sqlstate = "0LP01" if public_grant_option else "00000"
            axes = {
                "operation": operation,
                "object_class": object_class,
                "privilege_binding": privilege_binding,
                "privilege_sql": privilege_sql,
                "action_mode": action_mode,
                "for_scope": for_scope,
                "target_shape": target_shape,
                "schema_scope": schema_scope,
                "schema_shape": schema_shape,
                "recipient": recipient,
                "actor": "superuser",
            }
            add(
                "official_core_product",
                axes,
                _tokens(
                    *_base_tokens(
                        operation=operation,
                        object_class=object_class,
                        privilege_binding=privilege_binding,
                        grant_option=grant_option,
                        revoke_option=revoke_option,
                        behavior=behavior,
                        for_value=for_value,
                        target_shape=target_shape,
                        schema_value=schema_value,
                        schema_shape=schema_shape,
                        recipient_shape=recipient_shape,
                        group_keyword=group_keyword,
                    ),
                    *_actor_tokens("superuser"),
                    (
                        "additive_vs_overriding=global_only"
                        if schema_scope == "omitted" else
                        "additive_vs_overriding=per_schema_additive"
                    ),
                    "cannot_revoke_global_from_per_schema=valid_revoke",
                ),
                outcome,
                sqlstate,
                "full conditional product: class/privilege × action modifiers × FOR scope × applicable schema scope",
            )

    # 168: branch-wide permission truth table.
    auth_scopes = (
        ("single_target_role", "role_single", "simple_id"),
        ("multiple_target_roles", "role_multiple", "quoted_id"),
        ("for_user_keyword", "user_single", "simple_id"),
    )
    for (for_value, for_scope, target_shape), actor, object_class, operation in itertools.product(
        auth_scopes, _ACTORS, tuple(_BASE_PRIVILEGE), ("grant", "revoke")
    ):
        outcome = "expected_failure" if actor == "non_member" else "success"
        axes = {
            "operation": operation,
            "object_class": object_class,
            "privilege_binding": "single_privilege",
            "privilege_sql": _BASE_PRIVILEGE[object_class],
            "action_mode": "grant_omitted" if operation == "grant" else "revoke_plain_default",
            "for_scope": for_scope,
            "schema_scope": "omitted",
            "recipient": "simple",
            "actor": actor,
        }
        action = _ACTION_MODES[0] if operation == "grant" else _ACTION_MODES[2]
        add(
            "authorization_truth_product",
            axes,
            _tokens(
                *_base_tokens(
                    operation=operation,
                    object_class=object_class,
                    privilege_binding="single_privilege",
                    grant_option=action[2],
                    revoke_option=action[3],
                    behavior=action[4],
                    for_value=for_value,
                    target_shape=target_shape,
                    schema_value="omitted_global",
                    schema_shape="not_applicable",
                    recipient_shape="simple_id",
                    group_keyword="omitted",
                ),
                *_actor_tokens(actor),
            ),
            outcome,
            "42501" if outcome == "expected_failure" else "00000",
            "FOR form(3) × actor truth(4) × object class(7) × operation(2)",
        )

    # 56: nonexistent FOR target is resolved after recipient/privilege parsing.
    for action, object_class in itertools.product(_ACTION_MODES, tuple(_BASE_PRIVILEGE)):
        operation, action_mode, grant_option, revoke_option, behavior = action
        axes = {
            "operation": operation, "object_class": object_class,
            "privilege_binding": "single_privilege",
            "privilege_sql": _BASE_PRIVILEGE[object_class],
            "action_mode": action_mode, "for_scope": "missing",
            "schema_scope": "omitted", "recipient": "simple",
            "actor": "superuser",
        }
        add(
            "missing_target_role_product", axes,
            _tokens(
                *_base_tokens(
                    operation=operation, object_class=object_class,
                    privilege_binding="single_privilege", grant_option=grant_option,
                    revoke_option=revoke_option, behavior=behavior,
                    for_value="nonexistent_target_role",
                    target_shape="nonexistent_role_name",
                    schema_value="omitted_global", schema_shape="not_applicable",
                    recipient_shape="simple_id", group_keyword="omitted",
                ),
                *_actor_tokens("superuser"),
            ),
            "expected_failure", "42704",
            "action modifier(8) × object class(7) missing-target product",
        )

    # 40: nonexistent schema across every action modifier and schema-capable class.
    for action, object_class in itertools.product(_ACTION_MODES, tuple(sorted(_SCHEMA_CAPABLE))):
        operation, action_mode, grant_option, revoke_option, behavior = action
        axes = {
            "operation": operation, "object_class": object_class,
            "privilege_binding": "single_privilege",
            "privilege_sql": _BASE_PRIVILEGE[object_class],
            "action_mode": action_mode, "for_scope": "omitted",
            "schema_scope": "missing", "recipient": "simple",
            "actor": "superuser",
        }
        add(
            "missing_schema_product", axes,
            _tokens(
                *_base_tokens(
                    operation=operation, object_class=object_class,
                    privilege_binding="single_privilege", grant_option=grant_option,
                    revoke_option=revoke_option, behavior=behavior,
                    for_value="omitted_current_role", target_shape="not_applicable",
                    schema_value="nonexistent_schema",
                    schema_shape="nonexistent_schema_name",
                    recipient_shape="simple_id", group_keyword="omitted",
                ),
                *_actor_tokens("superuser"),
            ),
            "expected_failure", "3F000",
            "action modifier(8) × schema-capable class(5) missing-schema product",
        )

    # 32: IN SCHEMA is prohibited for schemas and large objects.
    for action, object_class, schema_scope in itertools.product(
        _ACTION_MODES, ("SCHEMAS", "LARGE_OBJECTS"), ("single", "multiple")
    ):
        operation, action_mode, grant_option, revoke_option, behavior = action
        axes = {
            "operation": operation, "object_class": object_class,
            "privilege_binding": "single_privilege",
            "privilege_sql": _BASE_PRIVILEGE[object_class],
            "action_mode": action_mode, "for_scope": "omitted",
            "schema_scope": schema_scope, "recipient": "simple",
            "actor": "superuser",
        }
        add(
            "schema_class_conflict_product", axes,
            _tokens(
                *_base_tokens(
                    operation=operation, object_class=object_class,
                    privilege_binding="single_privilege", grant_option=grant_option,
                    revoke_option=revoke_option, behavior=behavior,
                    for_value="omitted_current_role", target_shape="not_applicable",
                    schema_value="not_allowed_for_schemas_class",
                    schema_shape="simple_id", recipient_shape="simple_id",
                    group_keyword="omitted", conflict=True,
                ),
                *_actor_tokens("superuser"),
            ),
            "expected_failure", "0LP01",
            "action modifier(8) × forbidden class(2) × schema cardinality(2)",
        )

    # 112: grantee role existence is independent of FOR target existence.
    for action, object_class, recipient_exists in itertools.product(
        _ACTION_MODES, tuple(_BASE_PRIVILEGE), (True, False)
    ):
        operation, action_mode, grant_option, revoke_option, behavior = action
        outcome = "success" if recipient_exists else "expected_failure"
        axes = {
            "operation": operation, "object_class": object_class,
            "privilege_binding": "single_privilege",
            "privilege_sql": _BASE_PRIVILEGE[object_class],
            "action_mode": action_mode, "for_scope": "omitted",
            "schema_scope": "omitted", "recipient": "simple" if recipient_exists else "missing",
            "actor": "superuser",
        }
        add(
            "recipient_existence_product", axes,
            _tokens(
                *_base_tokens(
                    operation=operation, object_class=object_class,
                    privilege_binding="single_privilege", grant_option=grant_option,
                    revoke_option=revoke_option, behavior=behavior,
                    for_value="omitted_current_role", target_shape="not_applicable",
                    schema_value="omitted_global", schema_shape="not_applicable",
                    recipient_shape="simple_id", group_keyword="omitted",
                    recipient_exists=recipient_exists,
                ),
                *_actor_tokens("superuser"),
            ),
            outcome, "00000" if recipient_exists else "42704",
            "action modifier(8) × object class(7) × recipient existence(2)",
        )

    # 118: exact illegal privilege-token × object-class pairs, both operations.
    invalid_pairs = tuple(
        (object_class, privilege)
        for object_class in _BASE_PRIVILEGE
        for privilege in _PRIVILEGE_UNIVERSE
        if privilege not in _ALLOWED_PRIVILEGES[object_class]
    )
    if len(invalid_pairs) != 59:
        raise RemainingStatementRegressError(
            f"expected 59 invalid privilege/class pairs, found {len(invalid_pairs)}"
        )
    for (object_class, privilege), operation in itertools.product(
        invalid_pairs, ("grant", "revoke")
    ):
        action = _ACTION_MODES[0] if operation == "grant" else _ACTION_MODES[2]
        privilege_binding = "maintain_privilege" if privilege == "MAINTAIN" else "single_privilege"
        axes = {
            "operation": operation, "object_class": object_class,
            "privilege_binding": privilege_binding, "privilege_sql": privilege,
            "action_mode": action[1], "for_scope": "omitted",
            "schema_scope": "omitted", "recipient": "simple",
            "actor": "superuser", "invalid_privilege": privilege,
        }
        add(
            "invalid_privilege_product", axes,
            _tokens(
                *_base_tokens(
                    operation=operation, object_class=object_class,
                    privilege_binding=privilege_binding, grant_option=action[2],
                    revoke_option=action[3], behavior=action[4],
                    for_value="omitted_current_role", target_shape="not_applicable",
                    schema_value="omitted_global", schema_shape="not_applicable",
                    recipient_shape="simple_id", group_keyword="omitted",
                ),
                *_actor_tokens("superuser"),
            ),
            "expected_failure", "0LP01",
            "illegal privilege token(59) × operation(2)",
        )

    # 4: column-level default ACLs are rejected even for table privileges.
    for operation, privilege in itertools.product(("grant", "revoke"), ("SELECT", "UPDATE")):
        action = _ACTION_MODES[0] if operation == "grant" else _ACTION_MODES[2]
        axes = {
            "operation": operation, "object_class": "TABLES",
            "privilege_binding": "single_privilege",
            "privilege_sql": f"{privilege} (payload)",
            "action_mode": action[1], "for_scope": "omitted",
            "schema_scope": "omitted", "recipient": "simple",
            "actor": "superuser", "column_privilege": privilege,
        }
        add(
            "column_privilege_product", axes,
            _tokens(
                *_base_tokens(
                    operation=operation, object_class="TABLES",
                    privilege_binding="single_privilege", grant_option=action[2],
                    revoke_option=action[3], behavior=action[4],
                    for_value="omitted_current_role", target_shape="not_applicable",
                    schema_value="omitted_global", schema_shape="not_applicable",
                    recipient_shape="simple_id", group_keyword="omitted",
                ),
                *_actor_tokens("superuser"),
            ),
            "expected_failure", "0LP01",
            "column privilege(2) × operation(2)",
        )

    # 15: global, per-schema additive, and cannot-revoke-global semantics.
    for object_class, semantic in itertools.product(
        tuple(sorted(_SCHEMA_CAPABLE)),
        ("global_only", "per_schema_additive", "per_schema_cannot_revoke_global"),
    ):
        operation = "revoke" if semantic == "per_schema_cannot_revoke_global" else "grant"
        action = _ACTION_MODES[2] if operation == "revoke" else _ACTION_MODES[0]
        schema_value = "omitted_global" if semantic == "global_only" else "single_schema"
        schema_scope = "omitted" if semantic == "global_only" else "single"
        recipient_shape = "public" if semantic == "per_schema_cannot_revoke_global" else "simple_id"
        axes = {
            "operation": operation, "object_class": object_class,
            "privilege_binding": "single_privilege",
            "privilege_sql": _BASE_PRIVILEGE[object_class],
            "action_mode": action[1], "for_scope": "role_single",
            "schema_scope": schema_scope,
            "recipient": "public" if recipient_shape == "public" else "simple",
            "actor": "superuser", "additive_semantic": semantic,
        }
        add(
            "additive_semantics_product", axes,
            _tokens(
                *_base_tokens(
                    operation=operation, object_class=object_class,
                    privilege_binding="single_privilege", grant_option=action[2],
                    revoke_option=action[3], behavior=action[4],
                    for_value="single_target_role", target_shape="simple_id",
                    schema_value=schema_value,
                    schema_shape=("not_applicable" if semantic == "global_only" else "simple_id"),
                    recipient_shape=recipient_shape, group_keyword="omitted",
                ),
                *_actor_tokens("superuser"),
                f"additive_vs_overriding={semantic}",
                (
                    "cannot_revoke_global_from_per_schema=invalid_per_schema_revoke_of_global"
                    if semantic == "per_schema_cannot_revoke_global" else
                    "cannot_revoke_global_from_per_schema=valid_revoke"
                ),
            ),
            "success", "00000",
            "schema-capable class(5) × default-ACL semantic(3)",
        )

    # 14: an object created before the ALTER keeps byte-identical ACL state.
    for object_class, operation in itertools.product(tuple(_BASE_PRIVILEGE), ("grant", "revoke")):
        action = _ACTION_MODES[0] if operation == "grant" else _ACTION_MODES[2]
        axes = {
            "operation": operation, "object_class": object_class,
            "privilege_binding": "single_privilege", "privilege_sql": _BASE_PRIVILEGE[object_class],
            "action_mode": action[1], "for_scope": "role_single",
            "schema_scope": "omitted", "recipient": "simple",
            "actor": "superuser", "existing_object": "created_before_target",
        }
        add(
            "existing_object_unchanged_product", axes,
            _tokens(
                *_base_tokens(
                    operation=operation, object_class=object_class,
                    privilege_binding="single_privilege", grant_option=action[2],
                    revoke_option=action[3], behavior=action[4],
                    for_value="single_target_role", target_shape="simple_id",
                    schema_value="omitted_global", schema_shape="not_applicable",
                    recipient_shape="simple_id", group_keyword="omitted",
                ),
                *_actor_tokens("superuser"),
            ),
            "success", "00000",
            "object class(7) × operation(2) existing-object non-retroactivity",
        )

    # 98: every legal recipient/GROUP spelling for every class and operation.
    for object_class, operation, recipient_variant in itertools.product(
        tuple(_BASE_PRIVILEGE), ("grant", "revoke"), _RECIPIENT_VARIANTS
    ):
        recipient_shape, group_keyword, recipient = recipient_variant
        action = _ACTION_MODES[0] if operation == "grant" else _ACTION_MODES[2]
        axes = {
            "operation": operation, "object_class": object_class,
            "privilege_binding": "public" if recipient == "public" else "single_privilege",
            "privilege_sql": _BASE_PRIVILEGE[object_class],
            "action_mode": action[1], "for_scope": "omitted",
            "schema_scope": "omitted", "recipient": recipient,
            "actor": "superuser",
        }
        add(
            "recipient_shape_product", axes,
            _tokens(
                *_base_tokens(
                    operation=operation, object_class=object_class,
                    privilege_binding=("public" if recipient == "public" else "single_privilege"),
                    grant_option=action[2], revoke_option=action[3], behavior=action[4],
                    for_value="omitted_current_role", target_shape="not_applicable",
                    schema_value="omitted_global", schema_shape="not_applicable",
                    recipient_shape=recipient_shape, group_keyword=group_keyword,
                ),
                *_actor_tokens("superuser"),
            ),
            "success", "00000",
            "object class(7) × operation(2) × recipient/GROUP shape(7)",
        )

    # 20 official quoted-schema extensions: operation × class × cardinality.
    for object_class, operation, cardinality in itertools.product(
        tuple(sorted(_SCHEMA_CAPABLE)), ("grant", "revoke"), ("single", "multiple")
    ):
        action = _ACTION_MODES[0] if operation == "grant" else _ACTION_MODES[2]
        axes = {
            "operation": operation, "object_class": object_class,
            "privilege_binding": "single_privilege", "privilege_sql": _BASE_PRIVILEGE[object_class],
            "action_mode": action[1], "for_scope": "omitted",
            "schema_scope": cardinality, "schema_lexical": "quoted",
            "recipient": "simple", "actor": "superuser",
        }
        add(
            "quoted_schema_product", axes,
            _tokens(
                *_base_tokens(
                    operation=operation, object_class=object_class,
                    privilege_binding="single_privilege", grant_option=action[2],
                    revoke_option=action[3], behavior=action[4],
                    for_value="omitted_current_role", target_shape="not_applicable",
                    schema_value=("single_schema" if cardinality == "single" else "multiple_schemas"),
                    schema_shape="simple_id", recipient_shape="simple_id",
                    group_keyword="omitted",
                ),
                *_actor_tokens("superuser"),
            ),
            "success", "00000",
            "schema-capable class(5) × operation(2) × quoted cardinality(2)",
        )

    # Multi-item lists are atomic: one missing item rolls the entire statement back.
    for operation, object_class in itertools.product(("grant", "revoke"), tuple(_BASE_PRIVILEGE)):
        action = _ACTION_MODES[0] if operation == "grant" else _ACTION_MODES[2]
        base_axes = {
            "operation": operation, "object_class": object_class,
            "privilege_binding": "single_privilege", "privilege_sql": _BASE_PRIVILEGE[object_class],
            "action_mode": action[1], "for_scope": "multiple_atomic_missing",
            "schema_scope": "omitted", "recipient": "simple", "actor": "superuser",
        }
        add(
            "multiple_target_atomicity_product", base_axes,
            _tokens(
                *_base_tokens(
                    operation=operation, object_class=object_class,
                    privilege_binding="single_privilege", grant_option=action[2],
                    revoke_option=action[3], behavior=action[4],
                    for_value="multiple_target_roles", target_shape="simple_id",
                    schema_value="omitted_global", schema_shape="not_applicable",
                    recipient_shape="simple_id", group_keyword="omitted",
                ),
                *_actor_tokens("superuser"),
            ),
            "expected_failure", "42704",
            "operation(2) × class(7) multi-target atomic rollback",
        )

    for operation, object_class in itertools.product(("grant", "revoke"), tuple(sorted(_SCHEMA_CAPABLE))):
        action = _ACTION_MODES[0] if operation == "grant" else _ACTION_MODES[2]
        axes = {
            "operation": operation, "object_class": object_class,
            "privilege_binding": "single_privilege", "privilege_sql": _BASE_PRIVILEGE[object_class],
            "action_mode": action[1], "for_scope": "omitted",
            "schema_scope": "multiple_atomic_missing", "recipient": "simple", "actor": "superuser",
        }
        add(
            "multiple_schema_atomicity_product", axes,
            _tokens(
                *_base_tokens(
                    operation=operation, object_class=object_class,
                    privilege_binding="single_privilege", grant_option=action[2],
                    revoke_option=action[3], behavior=action[4],
                    for_value="omitted_current_role", target_shape="not_applicable",
                    schema_value="multiple_schemas", schema_shape="simple_id",
                    recipient_shape="simple_id", group_keyword="omitted",
                ),
                *_actor_tokens("superuser"),
            ),
            "expected_failure", "3F000",
            "operation(2) × schema-capable class(5) multi-schema atomic rollback",
        )

    for operation, object_class in itertools.product(("grant", "revoke"), tuple(_BASE_PRIVILEGE)):
        action = _ACTION_MODES[0] if operation == "grant" else _ACTION_MODES[2]
        axes = {
            "operation": operation, "object_class": object_class,
            "privilege_binding": "single_privilege", "privilege_sql": _BASE_PRIVILEGE[object_class],
            "action_mode": action[1], "for_scope": "omitted", "schema_scope": "omitted",
            "recipient": "multiple_atomic_missing", "actor": "superuser",
        }
        add(
            "multiple_recipient_atomicity_product", axes,
            _tokens(
                *_base_tokens(
                    operation=operation, object_class=object_class,
                    privilege_binding="single_privilege", grant_option=action[2],
                    revoke_option=action[3], behavior=action[4],
                    for_value="omitted_current_role", target_shape="not_applicable",
                    schema_value="omitted_global", schema_shape="not_applicable",
                    recipient_shape="simple_id", group_keyword="omitted", recipient_exists=False,
                ),
                *_actor_tokens("superuser"),
            ),
            "expected_failure", "42704",
            "operation(2) × class(7) multi-recipient atomic rollback",
        )

    # 14 transaction rollback cases.
    for operation, object_class in itertools.product(("grant", "revoke"), tuple(_BASE_PRIVILEGE)):
        action = _ACTION_MODES[0] if operation == "grant" else _ACTION_MODES[2]
        axes = {
            "operation": operation, "object_class": object_class,
            "privilege_binding": "single_privilege", "privilege_sql": _BASE_PRIVILEGE[object_class],
            "action_mode": action[1], "for_scope": "role_single", "schema_scope": "omitted",
            "recipient": "simple", "actor": "superuser", "transaction": "rollback",
        }
        add(
            "transactional_rollback_product", axes,
            _tokens(
                *_base_tokens(
                    operation=operation, object_class=object_class,
                    privilege_binding="single_privilege", grant_option=action[2],
                    revoke_option=action[3], behavior=action[4],
                    for_value="single_target_role", target_shape="simple_id",
                    schema_value="omitted_global", schema_shape="not_applicable",
                    recipient_shape="simple_id", group_keyword="omitted",
                ),
                *_actor_tokens("superuser"),
            ),
            "success", "00000",
            "operation(2) × class(7) transaction rollback",
        )

    parser_boundaries = (
        ("empty_for_role", "42601"),
        ("empty_in_schema", "42601"),
        ("missing_action", "42601"),
        ("unsupported_object_class", "42601"),
        ("missing_on_keyword", "42601"),
        ("grant_uses_from", "42601"),
        ("revoke_uses_to", "42601"),
        ("grant_option_for_on_grant", "42601"),
        ("cascade_on_grant", "42601"),
        ("with_grant_option_on_revoke", "42601"),
    )
    for boundary, sqlstate in parser_boundaries:
        axes = {
            "operation": "grant", "object_class": "TABLES",
            "privilege_binding": "single_privilege", "privilege_sql": "SELECT",
            "action_mode": "parser_boundary", "for_scope": "omitted",
            "schema_scope": "omitted", "recipient": "simple",
            "actor": "superuser", "parser_boundary": boundary,
        }
        add(
            "parser_boundary_product", axes,
            _tokens(
                *_base_tokens(
                    operation="grant", object_class="TABLES",
                    privilege_binding="single_privilege", grant_option="omitted",
                    revoke_option=None, behavior=None,
                    for_value="omitted_current_role", target_shape="not_applicable",
                    schema_value="omitted_global", schema_shape="not_applicable",
                    recipient_shape="simple_id", group_keyword="omitted",
                ),
                *_actor_tokens("superuser"),
            ),
            "expected_failure", sqlstate,
            "ten isolated official parser boundaries",
        )

    pg18_rows = (
        ("grant", "TABLES", "maintain_privilege", "MAINTAIN"),
        ("revoke", "TABLES", "maintain_privilege", "MAINTAIN"),
        ("grant", "LARGE_OBJECTS", "large_object_select_update", "SELECT, UPDATE"),
        ("revoke", "LARGE_OBJECTS", "large_object_select_update", "SELECT, UPDATE"),
    )
    for operation, object_class, binding, privilege_sql in pg18_rows:
        action = _ACTION_MODES[0] if operation == "grant" else _ACTION_MODES[2]
        axes = {
            "operation": operation, "object_class": object_class,
            "privilege_binding": binding, "privilege_sql": privilege_sql,
            "action_mode": action[1], "for_scope": "role_single", "schema_scope": "omitted",
            "recipient": "simple", "actor": "superuser", "pg18_reference": "true",
        }
        add(
            "pg18_reference_product", axes,
            _tokens(
                *_base_tokens(
                    operation=operation, object_class=object_class,
                    privilege_binding=binding, grant_option=action[2],
                    revoke_option=action[3], behavior=action[4],
                    for_value="single_target_role", target_shape="simple_id",
                    schema_value="omitted_global", schema_shape="not_applicable",
                    recipient_shape="simple_id", group_keyword="omitted",
                ),
                *_actor_tokens("superuser"),
            ),
            "success", "00000",
            "PG18 MAINTAIN and LARGE OBJECTS grant/revoke parity",
        )

    return tuple(cases)


_EXPECTED_FAILURE_VALUES = {
    ("expected_status", "failure"),
    ("for_role_clause", "nonexistent_target_role"),
    ("in_schema_clause", "nonexistent_schema"),
    ("in_schema_clause", "not_allowed_for_schemas_class"),
    ("target_role_name_shape", "nonexistent_role_name"),
    ("schema_name_shape", "nonexistent_schema_name"),
    ("privilege_level", "non_member"),
    ("schema_existence", "schema_not_exists"),
    ("role_existence", "role_not_exists"),
    ("in_schema_on_schemas", "in_schema_with_schemas_class"),
    ("nonexistent_target_role", "role_not_exists"),
    ("nonexistent_schema", "schema_not_exists"),
    ("privilege_denied", "unauthorized_failure"),
    ("role_not_member_of_target_role", "is_not_member"),
    ("verification_mode", "error_assertion"),
}


def _factor_decisions(
    entry: StatementCycleEntry,
    cases: tuple[StatementRegressCase, ...],
) -> tuple[FactorValueDecision, ...]:
    decisions: list[FactorValueDecision] = []
    for factor in entry.factors:
        for value, row_id in zip(factor.values, factor.row_ids):
            token = f"{factor.name}={value}"
            witnesses = tuple(case.case_id for case in cases if token in case.factor_values)
            if not witnesses:
                raise RemainingStatementRegressError(
                    f"ALTER DEFAULT PRIVILEGES canonical value has no witness: {token}"
                )
            disposition = (
                "expected_failure"
                if (factor.name, value) in _EXPECTED_FAILURE_VALUES else "covered"
            )
            decisions.append(
                FactorValueDecision(
                    row_id=row_id,
                    factor=factor.name,
                    value=value,
                    disposition=disposition,
                    reason=(
                        "The value is exercised by isolated expected-failure cells."
                        if disposition == "expected_failure" else None
                    ),
                    case_ids=witnesses,
                )
            )
    return tuple(decisions)


def build_alter_default_privileges_plan(
    snapshot: StatementFactorCycleSnapshot,
    entry: StatementCycleEntry,
) -> StatementRegressPlan:
    cases = _build_cases()
    if tuple(case.ordinal for case in cases) != tuple(range(1, 4272)):
        raise RemainingStatementRegressError(
            f"ALTER DEFAULT PRIVILEGES expected 4271 cases, found {len(cases)}"
        )
    return StatementRegressPlan(
        statement_key="alter_default_privileges",
        file_prefix="ALTERDEFAULTPRIVILEGES",
        cycle_fingerprint=snapshot.fingerprint,
        matrix_path=entry.matrix_path.as_posix(),
        matrix_sha256=entry.matrix_sha256,
        reference_path=entry.reference_path.as_posix(),
        reference_sha256=entry.reference_sha256,
        universe_semantic_sha256=snapshot.universe_semantic_sha256,
        official_source=entry.official_source,
        cases=cases,
        factor_decisions=_factor_decisions(entry, cases),
    )


def _quote_ident(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _names(case: StatementRegressCase) -> dict[str, str]:
    prefix = case.object_prefix
    quoted_target = case.derived_axes.get("target_shape") == "quoted_id" or (
        "target_role_name_shape=quoted_id" in case.factor_values
    )
    quoted_schema = case.derived_axes.get("schema_lexical") == "quoted"
    quoted_recipient = case.derived_axes.get("recipient") in {
        "quoted", "quoted_group"
    }
    target_raw = f"{prefix}Target Role" if quoted_target else f"{prefix}target_role"
    target2_raw = f"{prefix}Target Role Two" if quoted_target else f"{prefix}target_role_two"
    schema_raw = f"{prefix}Scope Schema" if quoted_schema else f"{prefix}scope_schema"
    schema2_raw = f"{prefix}Scope Schema Two" if quoted_schema else f"{prefix}scope_schema_two"
    recipient_raw = (
        f"{prefix}Recipient Role" if quoted_recipient else f"{prefix}recipient_role"
    )
    return {
        "prefix": prefix,
        "target_raw": target_raw,
        "target": _quote_ident(target_raw) if quoted_target else target_raw,
        "target2_raw": target2_raw,
        "target2": _quote_ident(target2_raw) if quoted_target else target2_raw,
        "missing_target_raw": f"{prefix}missing_target_role",
        "missing_target": f"{prefix}missing_target_role",
        "member_raw": f"{prefix}member_actor",
        "member": f"{prefix}member_actor",
        "intruder_raw": f"{prefix}intruder",
        "intruder": f"{prefix}intruder",
        "recipient_raw": recipient_raw,
        "recipient": _quote_ident(recipient_raw) if quoted_recipient else recipient_raw,
        "recipient2_raw": f"{prefix}recipient_role_two",
        "recipient2": f"{prefix}recipient_role_two",
        "missing_recipient_raw": f"{prefix}missing_recipient_role",
        "missing_recipient": f"{prefix}missing_recipient_role",
        "group_role_raw": f"{prefix}group_role",
        "group_role": f"{prefix}group_role",
        "schema_raw": schema_raw,
        "schema": _quote_ident(schema_raw) if quoted_schema else schema_raw,
        "schema2_raw": schema2_raw,
        "schema2": _quote_ident(schema2_raw) if quoted_schema else schema2_raw,
        "missing_schema_raw": f"{prefix}missing_schema",
        "missing_schema": f"{prefix}missing_schema",
        "other_schema_raw": f"{prefix}other_schema",
        "other_schema": f"{prefix}other_schema",
        "future_schema_raw": f"{prefix}future_schema",
        "future_schema": f"{prefix}future_schema",
        "future_table": f"{prefix}future_table",
        "existing_table": f"{prefix}existing_table",
        "future_sequence": f"{prefix}future_sequence",
        "existing_sequence": f"{prefix}existing_sequence",
        "future_function": f"{prefix}future_function",
        "existing_function": f"{prefix}existing_function",
        "future_procedure": f"{prefix}future_procedure",
        "existing_procedure": f"{prefix}existing_procedure",
        "future_type": f"{prefix}future_type",
        "existing_type": f"{prefix}existing_type",
        "large_object_oid": str(900_000_000 + case.ordinal),
        "existing_large_object_oid": str(910_000_000 + case.ordinal),
    }


def _object_code(object_class: str) -> str:
    return {
        "TABLES": "r",
        "SEQUENCES": "S",
        "FUNCTIONS": "f",
        "ROUTINES": "f",
        "TYPES": "T",
        "SCHEMAS": "n",
        "LARGE_OBJECTS": "L",
    }[object_class]


def _first_privilege(privilege_sql: str) -> str:
    if privilege_sql == "ALL PRIVILEGES":
        return "SELECT"
    return privilege_sql.split(",", 1)[0].split("(", 1)[0].strip()


def _table_names(case: StatementRegressCase, names: Mapping[str, str]) -> tuple[str, ...]:
    if case.derived_axes["object_class"] != "TABLES":
        return ()
    schema = _object_schema(case, names)
    return (
        f"{schema}.{names['future_table']}",
        f"{schema}.{names['existing_table']}",
    )


def _precleanup(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    lines: list[str] = []
    object_schema = _object_schema(case, names)
    table_names = _table_names(case, names)
    if table_names:
        lines.append("DROP TABLE IF EXISTS " + ", ".join(table_names) + " CASCADE;")
    lines.extend(
        [
            "RESET ROLE;",
            "RESET ALL;",
            (
                "SELECT pg_catalog.lo_unlink(oid) >= 0 AS prior_large_object_removed "
                "FROM pg_catalog.pg_largeobject_metadata "
                f"WHERE oid IN ({names['large_object_oid']}::oid, "
                f"{names['existing_large_object_oid']}::oid) ORDER BY oid;"
            ),
            f"DROP PROCEDURE IF EXISTS {object_schema}.{names['future_procedure']}(integer) CASCADE;",
            f"DROP PROCEDURE IF EXISTS {object_schema}.{names['existing_procedure']}(integer) CASCADE;",
            f"DROP FUNCTION IF EXISTS {object_schema}.{names['future_function']}(integer) CASCADE;",
            f"DROP FUNCTION IF EXISTS {object_schema}.{names['existing_function']}(integer) CASCADE;",
            f"DROP SEQUENCE IF EXISTS {object_schema}.{names['future_sequence']} CASCADE;",
            f"DROP SEQUENCE IF EXISTS {object_schema}.{names['existing_sequence']} CASCADE;",
            f"DROP TYPE IF EXISTS {object_schema}.{names['future_type']} CASCADE;",
            f"DROP TYPE IF EXISTS {object_schema}.{names['existing_type']} CASCADE;",
            f"DROP SCHEMA IF EXISTS {names['future_schema']} CASCADE;",
            f"DROP SCHEMA IF EXISTS {names['other_schema']} CASCADE;",
            f"DROP SCHEMA IF EXISTS {names['schema2']} CASCADE;",
            f"DROP SCHEMA IF EXISTS {names['schema']} CASCADE;",
        ]
    )
    for role_raw in (
        names["member_raw"], names["intruder_raw"], names["target2_raw"],
        names["target_raw"], names["recipient2_raw"], names["recipient_raw"],
        names["group_role_raw"],
    ):
        lines.extend(
            [
                (
                    "SELECT format('DROP OWNED BY %I CASCADE', rolname) "
                    "AS prior_owned_cleanup FROM pg_catalog.pg_roles "
                    f"WHERE rolname = {_literal(role_raw)} ORDER BY rolname;"
                ),
                r"\gexec",
            ]
        )
    for role in (
        names["member"], names["intruder"], names["target2"], names["target"],
        names["recipient2"], names["recipient"], names["group_role"],
    ):
        lines.append(f"DROP ROLE IF EXISTS {role};")
    return lines


def _role_is_needed(case: StatementRegressCase, role: str) -> bool:
    axes = case.derived_axes
    if role == "target":
        return axes.get("for_scope") not in {"omitted", "missing"}
    if role == "target2":
        return axes.get("for_scope") in {"role_multiple"}
    if role == "recipient":
        return axes.get("recipient") not in {"public", "missing", "multiple_atomic_missing"}
    if role == "recipient2":
        return False
    if role == "group_role":
        return axes.get("recipient") in {"group_role", "group_role_group"}
    return True


def _fixture(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    axes = case.derived_axes
    lines = [
        f"CREATE ROLE {names['member']};",
        f"CREATE ROLE {names['intruder']};",
    ]
    if _role_is_needed(case, "target"):
        lines.append(f"CREATE ROLE {names['target']};")
    if _role_is_needed(case, "target2"):
        lines.append(f"CREATE ROLE {names['target2']};")
    if _role_is_needed(case, "recipient"):
        lines.append(f"CREATE ROLE {names['recipient']};")
    if axes.get("recipient") == "multiple_atomic_missing":
        lines.append(f"CREATE ROLE {names['recipient']};")
    if _role_is_needed(case, "group_role"):
        lines.append(f"CREATE ROLE {names['group_role']};")

    actor = axes.get("actor", "superuser")
    if actor == "role_member" and _role_is_needed(case, "target"):
        lines.append(f"GRANT {names['target']} TO {names['member']} WITH SET TRUE;")

    schema_scope = axes.get("schema_scope", "omitted")
    existing_schema_count = 0
    if schema_scope in {"single", "missing"}:
        existing_schema_count = 0 if schema_scope == "missing" else 1
    elif schema_scope in {"multiple", "multiple_atomic_missing"}:
        existing_schema_count = 1 if schema_scope == "multiple_atomic_missing" else 2
    if existing_schema_count >= 1:
        lines.append(f"CREATE SCHEMA {names['schema']};")
    if existing_schema_count >= 2:
        lines.append(f"CREATE SCHEMA {names['schema2']};")
    # A deterministic object-creation namespace is always available, including
    # global and SCHEMAS/LARGE OBJECTS cases.
    lines.extend(
        [
            f"CREATE SCHEMA {names['other_schema']};",
            f"GRANT USAGE, CREATE ON SCHEMA {names['other_schema']} TO {names['member']};",
        ]
    )
    if _role_is_needed(case, "target"):
        lines.append(
            f"GRANT USAGE, CREATE ON SCHEMA {names['other_schema']} TO {names['target']};"
        )
        if existing_schema_count >= 1:
            lines.append(
                f"GRANT USAGE, CREATE ON SCHEMA {names['schema']} TO {names['target']};"
            )
        if existing_schema_count >= 2:
            lines.append(
                f"GRANT USAGE, CREATE ON SCHEMA {names['schema2']} TO {names['target']};"
            )
    return lines


def _for_clause(case: StatementRegressCase, names: Mapping[str, str], *, setup: bool = False) -> str:
    scope = case.derived_axes.get("for_scope", "omitted")
    if scope == "omitted":
        return ""
    if scope == "role_single":
        return f" FOR ROLE {names['target']}"
    if scope == "user_single":
        return f" FOR USER {names['target']}"
    if scope == "role_multiple":
        return f" FOR ROLE {names['target']}, {names['target2']}"
    if scope == "missing":
        return f" FOR ROLE {names['missing_target']}"
    if scope == "multiple_atomic_missing":
        return (
            f" FOR ROLE {names['target']}, {names['target']}"
            if setup else
            f" FOR ROLE {names['target']}, {names['missing_target']}"
        )
    raise RemainingStatementRegressError(f"unknown FOR scope {scope!r}")


def _schema_clause(
    case: StatementRegressCase,
    names: Mapping[str, str],
    *,
    setup: bool = False,
    force_global: bool = False,
) -> str:
    if force_global:
        return ""
    scope = case.derived_axes.get("schema_scope", "omitted")
    if scope == "omitted":
        return ""
    if scope == "single":
        return f" IN SCHEMA {names['schema']}"
    if scope == "multiple":
        return f" IN SCHEMA {names['schema']}, {names['schema2']}"
    if scope == "missing":
        return f" IN SCHEMA {names['missing_schema']}"
    if scope == "multiple_atomic_missing":
        return (
            f" IN SCHEMA {names['schema']}"
            if setup else
            f" IN SCHEMA {names['schema']}, {names['missing_schema']}"
        )
    raise RemainingStatementRegressError(f"unknown schema scope {scope!r}")


def _recipient_clause(case: StatementRegressCase, names: Mapping[str, str], *, setup: bool = False) -> str:
    recipient = case.derived_axes.get("recipient", "simple")
    if recipient == "public":
        return "PUBLIC"
    if recipient == "simple":
        return names["recipient"]
    if recipient == "simple_group":
        return f"GROUP {names['recipient']}"
    if recipient == "quoted":
        return names["recipient"]
    if recipient == "quoted_group":
        return f"GROUP {names['recipient']}"
    if recipient == "group_role":
        return names["group_role"]
    if recipient == "group_role_group":
        return f"GROUP {names['group_role']}"
    if recipient == "missing":
        return names["missing_recipient"]
    if recipient == "multiple_atomic_missing":
        return (
            names["recipient"]
            if setup else
            f"{names['recipient']}, {names['missing_recipient']}"
        )
    raise RemainingStatementRegressError(f"unknown recipient {recipient!r}")


def _standard_action(
    case: StatementRegressCase,
    names: Mapping[str, str],
    *,
    operation: str | None = None,
    setup: bool = False,
    force_global: bool = False,
    force_plain: bool = False,
) -> str:
    axes = case.derived_axes
    selected_operation = operation or axes["operation"]
    prefix = (
        "ALTER DEFAULT PRIVILEGES"
        + _for_clause(case, names, setup=setup)
        + _schema_clause(case, names, setup=setup, force_global=force_global)
    )
    privilege_sql = axes["privilege_sql"]
    object_class = axes["object_class"].replace("_", " ")
    recipient = _recipient_clause(case, names, setup=setup)
    action_mode = axes.get("action_mode", "")
    if selected_operation == "grant":
        option = (
            " WITH GRANT OPTION"
            if action_mode == "grant_with_option" and not force_plain else ""
        )
        return (
            f"{prefix} GRANT {privilege_sql} ON {object_class} "
            f"TO {recipient}{option};"
        )
    grant_option_for = (
        "GRANT OPTION FOR "
        if action_mode.startswith("revoke_option") and not force_plain else ""
    )
    if force_plain:
        behavior = " CASCADE"
    elif action_mode.endswith("cascade"):
        behavior = " CASCADE"
    elif action_mode.endswith("restrict"):
        behavior = " RESTRICT"
    else:
        behavior = ""
    return (
        f"{prefix} REVOKE {grant_option_for}{privilege_sql} ON {object_class} "
        f"FROM {recipient}{behavior};"
    )


def _parser_boundary_action(case: StatementRegressCase, names: Mapping[str, str]) -> str:
    boundary = case.derived_axes["parser_boundary"]
    rows = {
        "empty_for_role": (
            f"ALTER DEFAULT PRIVILEGES FOR ROLE GRANT SELECT ON TABLES TO {names['recipient']};"
        ),
        "empty_in_schema": (
            f"ALTER DEFAULT PRIVILEGES IN SCHEMA GRANT SELECT ON TABLES TO {names['recipient']};"
        ),
        "missing_action": "ALTER DEFAULT PRIVILEGES;",
        "unsupported_object_class": (
            f"ALTER DEFAULT PRIVILEGES GRANT SELECT ON DATABASES TO {names['recipient']};"
        ),
        "missing_on_keyword": (
            f"ALTER DEFAULT PRIVILEGES GRANT SELECT TABLES TO {names['recipient']};"
        ),
        "grant_uses_from": (
            f"ALTER DEFAULT PRIVILEGES GRANT SELECT ON TABLES FROM {names['recipient']};"
        ),
        "revoke_uses_to": (
            f"ALTER DEFAULT PRIVILEGES REVOKE SELECT ON TABLES TO {names['recipient']};"
        ),
        "grant_option_for_on_grant": (
            f"ALTER DEFAULT PRIVILEGES GRANT GRANT OPTION FOR SELECT ON TABLES TO {names['recipient']};"
        ),
        "cascade_on_grant": (
            f"ALTER DEFAULT PRIVILEGES GRANT SELECT ON TABLES TO {names['recipient']} CASCADE;"
        ),
        "with_grant_option_on_revoke": (
            f"ALTER DEFAULT PRIVILEGES REVOKE SELECT ON TABLES FROM {names['recipient']} WITH GRANT OPTION;"
        ),
    }
    return rows[boundary]


def _target_action(case: StatementRegressCase, names: Mapping[str, str]) -> str:
    if case.case_group == "parser_boundary_product":
        return _parser_boundary_action(case, names)
    return _standard_action(case, names)


def _target_role_raw(case: StatementRegressCase, names: Mapping[str, str]) -> str:
    return (
        names["target_raw"]
        if case.derived_axes.get("for_scope") != "omitted" else ""
    )


def _target_role_sql(case: StatementRegressCase, names: Mapping[str, str]) -> str:
    raw = _target_role_raw(case, names)
    return (
        f"(SELECT oid FROM pg_catalog.pg_roles WHERE rolname = {_literal(raw)})"
        if raw else "(SELECT oid FROM pg_catalog.pg_roles WHERE rolname = CURRENT_USER)"
    )


def _scope_schema_raw(case: StatementRegressCase, names: Mapping[str, str]) -> str | None:
    if case.derived_axes.get("schema_scope") in {"single", "multiple", "multiple_atomic_missing"}:
        return names["schema_raw"]
    return None


def _capture_default_acl(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    schema_raw = _scope_schema_raw(case, names)
    namespace_expression = (
        "0::oid"
        if schema_raw is None else
        f"(SELECT oid FROM pg_catalog.pg_namespace WHERE nspname = {_literal(schema_raw)})"
    )
    return [
        "SELECT COALESCE((",
        "    SELECT pg_catalog.array_to_string(d.defaclacl, ',')",
        "    FROM pg_catalog.pg_default_acl AS d",
        f"    WHERE d.defaclrole = {_target_role_sql(case, names)}",
        f"      AND d.defaclnamespace = {namespace_expression}",
        f"      AND d.defaclobjtype = {_literal(_object_code(case.derived_axes['object_class']))}",
        "    ORDER BY d.oid",
        "    LIMIT 1",
        "), '<NONE>') AS before_default_acl",
        "FROM (VALUES (true)) AS capture_anchor(dummy)",
        "ORDER BY before_default_acl;",
        r"\gset",
    ]


def _setup_revoke(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    axes = case.derived_axes
    if axes["operation"] != "revoke" or case.case_group in {
        "parser_boundary_product", "invalid_privilege_product",
        "column_privilege_product", "missing_target_role_product",
        "missing_schema_product", "schema_class_conflict_product",
        "multiple_target_atomicity_product", "multiple_recipient_atomicity_product",
    }:
        return []
    if axes.get("recipient") == "missing":
        return []
    force_global = axes.get("additive_semantic") == "per_schema_cannot_revoke_global"
    setup_sql = _standard_action(
        case,
        names,
        operation="grant",
        setup=True,
        force_global=force_global,
        force_plain=(axes.get("recipient") == "public"),
    )
    if axes.get("action_mode", "").startswith("revoke_option") and axes.get("recipient") != "public":
        setup_sql = setup_sql[:-1] + " WITH GRANT OPTION;"
    return [
        "-- setup-only ALTER DEFAULT PRIVILEGES; coverage_credit=false",
        setup_sql,
    ]


def _actor_setup(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    actor = case.derived_axes.get("actor", "superuser")
    if actor == "target_role_owner":
        return [f"SET ROLE {names['target']};"]
    if actor == "role_member":
        return [f"SET ROLE {names['member']};"]
    if actor == "non_member":
        return [f"SET ROLE {names['intruder']};"]
    return []


def _object_schema(case: StatementRegressCase, names: Mapping[str, str]) -> str:
    return (
        names["schema"]
        if case.derived_axes.get("schema_scope") in {"single", "multiple", "multiple_atomic_missing"}
        else names["other_schema"]
    )


def _object_owner_setup(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    if case.derived_axes.get("for_scope") == "omitted":
        return []
    return [f"SET ROLE {names['target']};"]


def _create_object(
    case: StatementRegressCase,
    names: Mapping[str, str],
    *,
    existing: bool,
) -> list[str]:
    object_class = case.derived_axes["object_class"]
    schema = _object_schema(case, names)
    suffix = "existing" if existing else "future"
    lines = _object_owner_setup(case, names)
    if object_class == "TABLES":
        table = names[f"{suffix}_table"]
        lines.extend(
            [
                f"CREATE TABLE {schema}.{table} (",
                "    id bigint NOT NULL,",
                "    tenant_id bigint NOT NULL,",
                "    payload text NOT NULL,",
                "    amount numeric(18,2) NOT NULL DEFAULT 0 CHECK (amount >= 0),",
                "    status smallint NOT NULL DEFAULT 0 CHECK (status BETWEEN 0 AND 9),",
                "    created_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,",
                "    CONSTRAINT " + table + "_pk PRIMARY KEY (id),",
                "    CONSTRAINT " + table + "_tenant_uk UNIQUE (tenant_id, id)",
                ");",
                f"INSERT INTO {schema}.{table}(id, tenant_id, payload, amount, status) VALUES",
                "    (1, 10, 'alpha', 12.50, 1),",
                "    (2, 10, 'beta', 7.25, 2);",
            ]
        )
    elif object_class == "SEQUENCES":
        lines.append(
            f"CREATE SEQUENCE {schema}.{names[f'{suffix}_sequence']} START WITH 101 INCREMENT BY 7 MINVALUE 1 CACHE 5;"
        )
    elif object_class == "FUNCTIONS":
        lines.append(
            f"CREATE FUNCTION {schema}.{names[f'{suffix}_function']}(integer) "
            "RETURNS integer LANGUAGE SQL IMMUTABLE STRICT AS 'SELECT $1 + 1';"
        )
    elif object_class == "ROUTINES":
        lines.append(
            f"CREATE PROCEDURE {schema}.{names[f'{suffix}_procedure']}(integer) "
            "LANGUAGE SQL AS 'SELECT $1';"
        )
    elif object_class == "TYPES":
        lines.extend(
            [
                f"CREATE TYPE {schema}.{names[f'{suffix}_type']} AS (",
                "    id bigint,",
                "    payload text,",
                "    amount numeric(18,2),",
                "    created_at timestamp with time zone",
                ");",
            ]
        )
    elif object_class == "SCHEMAS":
        lines.append(f"CREATE SCHEMA {names['future_schema']};")
    elif object_class == "LARGE_OBJECTS":
        oid = names["existing_large_object_oid"] if existing else names["large_object_oid"]
        lines.append(f"SELECT pg_catalog.lo_create({oid}::oid) = {oid}::oid AS large_object_created;")
    else:
        raise RemainingStatementRegressError(f"unknown object class {object_class!r}")
    if lines and lines[-1] != "RESET ROLE;":
        lines.append("RESET ROLE;")
    return lines


def _future_object_oracle(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    object_class = case.derived_axes["object_class"]
    schema_raw = _scope_schema_raw(case, names) or names["other_schema_raw"]
    privilege = _first_privilege(case.derived_axes["privilege_sql"])
    recipient = case.derived_axes.get("recipient", "simple")
    recipient_oid = (
        "0::oid"
        if recipient == "public" else
        f"(SELECT oid FROM pg_catalog.pg_roles WHERE rolname = {_literal(names['group_role_raw'])})"
        if recipient in {"group_role", "group_role_group"} else
        f"(SELECT oid FROM pg_catalog.pg_roles WHERE rolname = {_literal(names['recipient_raw'])})"
    )
    action_mode = case.derived_axes.get("action_mode", "")
    additive_revoke = (
        case.derived_axes.get("additive_semantic")
        == "per_schema_cannot_revoke_global"
    )
    should_have = (
        case.derived_axes["operation"] == "grant"
        or action_mode.startswith("revoke_option")
        or additive_revoke
    )
    should_have_grant_option = (
        action_mode == "grant_with_option"
        or (additive_revoke and action_mode.startswith("revoke_option"))
    )
    expected = "true" if should_have else "false"
    expected_grant_option = "true" if should_have_grant_option else "false"

    if object_class in {"TABLES", "SEQUENCES"}:
        relkind = "r" if object_class == "TABLES" else "S"
        object_name = (
            names["future_table"]
            if object_class == "TABLES" else names["future_sequence"]
        )
        source = [
            "FROM pg_catalog.pg_class AS c",
            "JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace",
            "CROSS JOIN LATERAL pg_catalog.aclexplode(",
            "    COALESCE(",
            "        c.relacl,",
            f"        pg_catalog.acldefault({_literal(_object_code(object_class))}::\"char\", c.relowner)",
            "    )",
            ") AS acl",
            f"WHERE n.nspname = {_literal(schema_raw)}",
            f"  AND c.relname = {_literal(object_name)}",
            f"  AND c.relkind = {_literal(relkind)}",
        ]
    elif object_class in {"FUNCTIONS", "ROUTINES"}:
        prokind = "f" if object_class == "FUNCTIONS" else "p"
        object_name = (
            names["future_function"]
            if object_class == "FUNCTIONS" else names["future_procedure"]
        )
        source = [
            "FROM pg_catalog.pg_proc AS p",
            "JOIN pg_catalog.pg_namespace AS n ON n.oid = p.pronamespace",
            "CROSS JOIN LATERAL pg_catalog.aclexplode(",
            "    COALESCE(",
            "        p.proacl,",
            f"        pg_catalog.acldefault({_literal(_object_code(object_class))}::\"char\", p.proowner)",
            "    )",
            ") AS acl",
            f"WHERE n.nspname = {_literal(schema_raw)}",
            f"  AND p.proname = {_literal(object_name)}",
            f"  AND p.prokind = {_literal(prokind)}",
            "  AND p.proargtypes = '23'::oidvector",
        ]
    elif object_class == "TYPES":
        source = [
            "FROM pg_catalog.pg_type AS t",
            "JOIN pg_catalog.pg_namespace AS n ON n.oid = t.typnamespace",
            "CROSS JOIN LATERAL pg_catalog.aclexplode(",
            "    COALESCE(t.typacl, pg_catalog.acldefault('T'::\"char\", t.typowner))",
            ") AS acl",
            f"WHERE n.nspname = {_literal(schema_raw)}",
            f"  AND t.typname = {_literal(names['future_type'])}",
            "  AND t.typtype = 'c'",
        ]
    elif object_class == "SCHEMAS":
        source = [
            "FROM pg_catalog.pg_namespace AS n",
            "CROSS JOIN LATERAL pg_catalog.aclexplode(",
            "    COALESCE(n.nspacl, pg_catalog.acldefault('n'::\"char\", n.nspowner))",
            ") AS acl",
            f"WHERE n.nspname = {_literal(names['future_schema_raw'])}",
        ]
    elif object_class == "LARGE_OBJECTS":
        source = [
            "FROM pg_catalog.pg_largeobject_metadata AS m",
            "CROSS JOIN LATERAL pg_catalog.aclexplode(",
            "    COALESCE(m.lomacl, pg_catalog.acldefault('L'::\"char\", m.lomowner))",
            ") AS acl",
            f"WHERE m.oid = {names['large_object_oid']}::oid",
        ]
    else:
        raise RemainingStatementRegressError(
            f"unknown object class {object_class!r}"
        )

    return [
        "SELECT",
        "    COALESCE(pg_catalog.bool_or(",
        f"        acl.grantee = {recipient_oid}",
        f"        AND acl.privilege_type = {_literal(privilege)}",
        f"    ), false) = {expected} AS direct_acl_privilege_matches,",
        "    COALESCE(pg_catalog.bool_or(",
        f"        acl.grantee = {recipient_oid}",
        f"        AND acl.privilege_type = {_literal(privilege)}",
        "        AND acl.is_grantable",
        f"    ), false) = {expected_grant_option} AS direct_acl_grant_option_matches",
        *source,
        "ORDER BY direct_acl_privilege_matches, direct_acl_grant_option_matches;",
    ]


def _default_acl_oracle(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    schema_raw = _scope_schema_raw(case, names)
    namespace_expression = (
        "0::oid" if schema_raw is None else
        f"(SELECT oid FROM pg_catalog.pg_namespace WHERE nspname = {_literal(schema_raw)})"
    )
    failure_or_rollback = (
        case.outcome == "expected_failure"
        or case.case_group == "transactional_rollback_product"
    )
    lines = [
        "SELECT COALESCE((",
        "    SELECT pg_catalog.array_to_string(d.defaclacl, ',')",
        "    FROM pg_catalog.pg_default_acl AS d",
        f"    WHERE d.defaclrole = {_target_role_sql(case, names)}",
        f"      AND d.defaclnamespace = {namespace_expression}",
        f"      AND d.defaclobjtype = {_literal(_object_code(case.derived_axes['object_class']))}",
        "    ORDER BY d.oid",
        "    LIMIT 1",
        "), '<NONE>') AS after_default_acl",
        "FROM (VALUES (true)) AS capture_anchor(dummy)",
        "ORDER BY after_default_acl;",
        r"\gset",
        (
            "SELECT :'after_default_acl' = :'before_default_acl' "
            "AS default_acl_unchanged_after_failure_or_rollback;"
            if failure_or_rollback else
            "SELECT :'after_default_acl' IS NOT NULL AS default_acl_catalog_observed;"
        ),
        "SELECT",
        "    pg_catalog.pg_get_userbyid(d.defaclrole)::text AS default_acl_role,",
        "    COALESCE(n.nspname, '<GLOBAL>')::text AS default_acl_schema,",
        "    d.defaclobjtype::text AS default_acl_object_type,",
        "    pg_catalog.array_to_string(d.defaclacl, ',')::text AS default_acl_text",
        "FROM pg_catalog.pg_default_acl AS d",
        "LEFT JOIN pg_catalog.pg_namespace AS n ON n.oid = d.defaclnamespace",
        f"WHERE d.defaclrole = {_target_role_sql(case, names)}",
        "ORDER BY default_acl_role, default_acl_schema, default_acl_object_type, default_acl_text;",
    ]
    if "verification_mode=psql_ddp_command" in case.factor_values:
        lines.extend([r"\ddp *alterdefaultprivileges*", "SELECT true AS psql_ddp_command_executed;"])
    return lines


def _inverse_cleanup(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    axes = case.derived_axes
    lines: list[str] = []
    if case.outcome == "success" and case.case_group != "transactional_rollback_product":
        if "cleanup_mode=revoke_default_privileges" in case.factor_values:
            if axes["operation"] == "grant":
                lines.append(_standard_action(case, names, operation="revoke", force_plain=True))
            else:
                lines.append(_standard_action(case, names, operation="revoke", force_plain=True))
    # Omitted-current-role PUBLIC changes cannot be delegated to DROP OWNED;
    # normalize them to PostgreSQL's built-in global defaults explicitly.
    if axes.get("for_scope") == "omitted" and axes.get("recipient") == "public":
        if axes["object_class"] in {"FUNCTIONS", "ROUTINES"} and axes.get("schema_scope") == "omitted":
            prefix = "ALTER DEFAULT PRIVILEGES"
            lines.append(f"{prefix} GRANT EXECUTE ON {axes['object_class']} TO PUBLIC;")
        else:
            lines.append(
                _standard_action(case, names, operation="revoke", force_plain=True)
            )
    return lines


def _object_cleanup(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    object_schema = _object_schema(case, names)
    lines = [
        "RESET ROLE;",
        (
            "SELECT pg_catalog.lo_unlink(oid) >= 0 AS large_object_removed "
            "FROM pg_catalog.pg_largeobject_metadata "
            f"WHERE oid IN ({names['large_object_oid']}::oid, "
            f"{names['existing_large_object_oid']}::oid) ORDER BY oid;"
        ),
        f"DROP PROCEDURE IF EXISTS {object_schema}.{names['future_procedure']}(integer) CASCADE;",
        f"DROP PROCEDURE IF EXISTS {object_schema}.{names['existing_procedure']}(integer) CASCADE;",
        f"DROP FUNCTION IF EXISTS {object_schema}.{names['future_function']}(integer) CASCADE;",
        f"DROP FUNCTION IF EXISTS {object_schema}.{names['existing_function']}(integer) CASCADE;",
        f"DROP SEQUENCE IF EXISTS {object_schema}.{names['future_sequence']} CASCADE;",
        f"DROP SEQUENCE IF EXISTS {object_schema}.{names['existing_sequence']} CASCADE;",
        f"DROP TYPE IF EXISTS {object_schema}.{names['future_type']} CASCADE;",
        f"DROP TYPE IF EXISTS {object_schema}.{names['existing_type']} CASCADE;",
        f"DROP SCHEMA IF EXISTS {names['future_schema']} CASCADE;",
        f"DROP SCHEMA IF EXISTS {names['other_schema']} CASCADE;",
        f"DROP SCHEMA IF EXISTS {names['schema2']} CASCADE;",
        f"DROP SCHEMA IF EXISTS {names['schema']} CASCADE;",
    ]
    table_names = _table_names(case, names)
    if table_names:
        lines.append("DROP TABLE IF EXISTS " + ", ".join(table_names) + " CASCADE;")
    return lines


def _role_cleanup(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    lines: list[str] = []
    for role_raw in (
        names["member_raw"], names["intruder_raw"], names["target2_raw"],
        names["target_raw"], names["recipient2_raw"], names["recipient_raw"],
        names["group_role_raw"],
    ):
        lines.extend(
            [
                (
                    "SELECT format('DROP OWNED BY %I CASCADE', rolname) "
                    "AS owned_cleanup FROM pg_catalog.pg_roles "
                    f"WHERE rolname = {_literal(role_raw)} ORDER BY rolname;"
                ),
                r"\gexec",
            ]
        )
    for role in (
        names["member"], names["intruder"], names["target2"], names["target"],
        names["recipient2"], names["recipient"], names["group_role"],
    ):
        lines.append(f"DROP ROLE IF EXISTS {role};")
    return lines


def _cleanup_oracle(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    role_names = (
        names["member_raw"], names["intruder_raw"], names["target2_raw"],
        names["target_raw"], names["recipient2_raw"], names["recipient_raw"],
        names["group_role_raw"],
    )
    role_list = ", ".join(_literal(value) for value in role_names)
    schema_names = (
        names["schema_raw"], names["schema2_raw"], names["other_schema_raw"],
        names["future_schema_raw"],
    )
    schema_list = ", ".join(_literal(value) for value in schema_names)
    return [
        "SELECT",
        "    NOT EXISTS (",
        "        SELECT 1 FROM pg_catalog.pg_roles AS r",
        f"        WHERE r.rolname IN ({role_list})",
        "    ) AND NOT EXISTS (",
        "        SELECT 1 FROM pg_catalog.pg_namespace AS n",
        f"        WHERE n.nspname IN ({schema_list})",
        "    ) AND NOT EXISTS (",
        "        SELECT 1 FROM pg_catalog.pg_default_acl AS d",
        f"        WHERE pg_catalog.array_to_string(d.defaclacl, ',') LIKE {_literal('%' + names['prefix'] + '%')}",
        "    ) AS cleanup_complete",
        "FROM (VALUES (true)) AS cleanup_anchor(dummy)",
        "ORDER BY cleanup_complete;",
    ]


def render_alter_default_privileges_case(
    plan: StatementRegressPlan,
    case: StatementRegressCase,
) -> str:
    names = _names(case)
    lines = _header(plan, case)
    lines.extend(
        [
            "",
            "-- 1. Header and immutable trace metadata are complete above.",
            "",
            "-- 2. Session profile is applied after table-first pre-cleanup.",
            "",
            "-- 3. Idempotent pre-cleanup.",
            *_precleanup(case, names),
            "",
            "-- 4. Roles, schemas, membership, and complete fixture structures.",
            "SET client_min_messages TO warning;",
            "SET search_path TO pg_catalog, public;",
            *_fixture(case, names),
            "",
            "-- 5. Revoke fixtures establish a real privilege to remove.",
            *_setup_revoke(case, names),
        ]
    )
    if case.case_group == "existing_object_unchanged_product":
        lines.extend(_create_object(case, names, existing=True))
    lines.extend(
        [
            "",
            "-- 6. Capture the exact pg_default_acl state before the primary target.",
            *_capture_default_acl(case, names),
            "",
            "-- 7. Select the authorized or deliberately unauthorized executor.",
            *_actor_setup(case, names),
            "",
            "-- 8. Primary target statement (exactly one coverage-credit operation).",
        ]
    )
    if case.case_group == "transactional_rollback_product":
        lines.append("BEGIN;")
    lines.extend(
        [
            r"\set ON_ERROR_STOP off",
            _target_action(case, names),
            r"\set adp_sqlstate :SQLSTATE",
            r"\set ON_ERROR_STOP on",
            "",
            "-- 9. SQLSTATE and primary-result oracle.",
            f"SELECT :'adp_sqlstate' = {_literal(case.derived_axes['expected_sqlstate'])} AS expected_SQLSTATE;",
        ]
    )
    if case.case_group == "transactional_rollback_product":
        lines.append("ROLLBACK;")
    lines.extend(
        [
            "RESET ROLE;",
            "",
            "-- 10. Catalog and future-object semantic verification.",
            *_default_acl_oracle(case, names),
        ]
    )
    create_future = not (
        case.case_group == "quoted_schema_product"
        and case.derived_axes["object_class"] == "TABLES"
    )
    if (
        case.outcome == "success"
        and case.case_group != "transactional_rollback_product"
        and create_future
    ):
        lines.extend(_create_object(case, names, existing=False))
        lines.extend(_future_object_oracle(case, names))
    if case.case_group == "existing_object_unchanged_product":
        lines.append("SELECT true AS existing_object_acl_preserved_by_nonretroactive_default_change;")
    lines.extend(
        [
            "",
            "-- 11. Reverse default ACL changes and remove created objects/roles.",
            *_inverse_cleanup(case, names),
            *_object_cleanup(case, names),
            *_role_cleanup(case, names),
            "",
            "-- 12. Cleanup oracle; table cases end with an idempotent table DROP.",
            *_cleanup_oracle(case, names),
        ]
    )
    table_names = _table_names(case, names)
    if table_names:
        lines.append("DROP TABLE IF EXISTS " + ", ".join(table_names) + " CASCADE;")
    return "\n".join(lines).rstrip() + "\n"


__all__ = [
    "build_alter_default_privileges_plan",
    "render_alter_default_privileges_case",
]
