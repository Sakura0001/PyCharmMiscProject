"""PostgreSQL 18 ALTER DATABASE exhaustive conditional-product regress design."""

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


_DIFFERENT_SOURCES = ("different_simple", "different_quoted")
_CURRENT_SOURCES = ("current_simple", "current_quoted")
_SOURCES = _DIFFERENT_SOURCES + _CURRENT_SOURCES
_ACTORS = ("superuser", "database_owner", "non_owner")
_PARAMETERS = (
    "common_parameter",
    "search_path",
    "enable_indexscan",
    "superuser_only_parameter",
)


def _tokens(*values: str | None) -> tuple[str, ...]:
    result: list[str] = []
    keys: set[str] = set()
    for token in values:
        if token is None:
            continue
        key = token.split("=", 1)[0]
        if key in keys:
            raise RemainingStatementRegressError(
                f"ALTER DATABASE case binds factor {key!r} more than once"
            )
        keys.add(key)
        result.append(token)
    return tuple(result)


def _case(
    ordinal: int,
    *,
    group: str,
    axes: Mapping[str, str],
    factor_values: tuple[str, ...],
    outcome: str,
    expected_sqlstate: str,
    strategy: str,
) -> StatementRegressCase:
    number = f"{ordinal:05d}"
    external = (
        axes.get("branch") == "set_tablespace"
        or axes.get("connection_state") == "has_connections"
        or axes.get("file_copy_method") in {"copy", "clone"}
    )
    return StatementRegressCase(
        ordinal=ordinal,
        case_id=f"ALTERDATABASE{number}",
        sql_filename=f"ALTERDATABASE{number}.sql",
        object_prefix=f"alterdatabase_{number}_",
        case_group=group,
        case_type="expected_failure" if outcome == "expected_failure" else "success",
        outcome=outcome,
        execution_profile=(
            "external_isolated" if external else "same_session_multiphase"
        ),
        derived_axes={**dict(axes), "expected_sqlstate": expected_sqlstate},
        factor_values=factor_values,
        combination_strategy=strategy,
        description=(
            f"ALTER DATABASE {axes['branch']} conditional product: "
            + ", ".join(f"{key}={value}" for key, value in sorted(axes.items()))
        ),
        expected_anchor=f"SQLSTATE {expected_sqlstate}; deterministic catalog and cleanup oracle",
    )


def _source_tokens(source: str) -> tuple[str, ...]:
    if source == "missing":
        return _tokens(
            "object_state=not_exists",
            "database_name_shape=nonexistent_name",
            "database_not_exist=database_not_exists",
        )
    return _tokens(
        (
            "object_state=is_current_database"
            if source.startswith("current_")
            else "object_state=exists"
        ),
        (
            "database_name_shape=quoted_id"
            if source.endswith("quoted")
            else "database_name_shape=simple_id"
        ),
        "database_not_exist=database_exists",
    )


def _actor_tokens(actor: str) -> tuple[str, ...]:
    return _tokens(
        f"privilege_level={actor}",
        (
            "privilege_denied=non_owner_failure"
            if actor == "non_owner"
            else "privilege_denied=owner_or_superuser_success"
        ),
    )


def _status_token(outcome: str) -> str:
    return f"expected_status={'success' if outcome == 'success' else 'failure'}"


def _verification_token(branch: str, outcome: str, axes: Mapping[str, str]) -> str:
    if outcome == "expected_failure":
        return "verification_mode=error_assertion"
    if branch in {"set_parameter", "set_from_current", "reset_parameter", "reset_all"}:
        return "verification_mode=catalog_query_pg_db_role_setting"
    if branch == "with_options" and axes.get("option") == "allow_connections_true":
        return "verification_mode=connect_verify"
    return "verification_mode=catalog_query_pg_database"


def _cleanup_token(branch: str, axes: Mapping[str, str]) -> str:
    if branch in {"set_parameter", "set_from_current", "reset_parameter", "reset_all"}:
        return "cleanup_mode=reset_config_parameter"
    if axes.get("connection_state") == "has_connections" or axes.get("option") == "allow_connections_false":
        return "cleanup_mode=force_drop_database"
    return "cleanup_mode=drop_database"


def _base_tokens(
    branch: str,
    source: str,
    outcome: str,
    axes: Mapping[str, str],
    actor: str | None,
) -> tuple[str, ...]:
    return _tokens(
        f"statement_branch=branch_{branch}",
        *_source_tokens(source),
        _status_token(outcome),
        *_actor_tokens(actor) if actor is not None else (),
        _verification_token(branch, outcome, axes),
        _cleanup_token(branch, axes),
    )


def _createdb_actor_states() -> tuple[tuple[str, str], ...]:
    return (
        ("superuser", "has_createdb"),
        ("database_owner", "has_createdb"),
        ("database_owner", "lacks_createdb"),
        ("non_owner", "has_createdb"),
        ("non_owner", "lacks_createdb"),
    )


def _owner_actor_states() -> tuple[tuple[str, str, str], ...]:
    rows = [("superuser", "can_set_role", "has_createdb")]
    rows.extend(
        (actor, can_set, createdb)
        for actor in ("database_owner", "non_owner")
        for can_set in ("can_set_role", "cannot_set_role")
        for createdb in ("has_createdb", "lacks_createdb")
    )
    return tuple(rows)


def _rolespec_actor_states() -> tuple[tuple[str, str], ...]:
    return (
        ("superuser", "has_createdb"),
        ("database_owner", "has_createdb"),
        ("database_owner", "lacks_createdb"),
        ("non_owner", "has_createdb"),
        ("non_owner", "lacks_createdb"),
    )


def _with_forms() -> tuple[tuple[str, str, str], ...]:
    singles = (
        ("allow_connections_true", "ALLOW_CONNECTIONS true"),
        ("allow_connections_false", "ALLOW_CONNECTIONS false"),
        ("connection_limit_positive", "CONNECTION LIMIT 5"),
        ("connection_limit_negative_one", "CONNECTION LIMIT -1"),
        ("is_template_true", "IS_TEMPLATE true"),
        ("is_template_false", "IS_TEMPLATE false"),
    )
    result = [(value, value, clause) for value, clause in singles]
    clauses = (
        "ALLOW_CONNECTIONS true",
        "CONNECTION LIMIT 5",
        "IS_TEMPLATE false",
    )
    for ordinal, permutation in enumerate(itertools.permutations(clauses), start=1):
        result.append(
            (
                "multiple_options_combined",
                f"multiple_order_{ordinal}",
                " ".join(permutation),
            )
        )
    return tuple(result)


def _with_outcome(source: str, actor: str | None, option: str) -> tuple[str, str]:
    if source == "missing":
        return "expected_failure", "3D000"
    if actor == "non_owner":
        return "expected_failure", "42501"
    if source.startswith("current_") and option == "allow_connections_false":
        return "expected_failure", "22023"
    return "success", "00000"


def _rename_outcome(
    source: str,
    actor: str | None,
    createdb: str,
    conflict: str,
    connection: str,
) -> tuple[str, str]:
    if source == "missing":
        return "expected_failure", "3D000"
    if actor == "non_owner":
        return "expected_failure", "42501"
    if actor == "database_owner" and createdb == "lacks_createdb":
        return "expected_failure", "42501"
    if conflict == "new_name_exists":
        return "expected_failure", "42P04"
    if source.startswith("current_"):
        return "expected_failure", "0A000"
    if connection == "has_connections":
        return "expected_failure", "55006"
    if source.startswith("different_"):
        return "success", "00000"
    raise AssertionError(source)


def _owner_outcome(
    source: str,
    actor: str | None,
    can_set: str,
    createdb: str,
    *,
    rolespec: bool,
    rolespec_token: str | None = None,
    missing_target: bool = False,
) -> tuple[str, str]:
    if missing_target:
        return "expected_failure", "42704"
    if source == "missing":
        return "expected_failure", "3D000"
    if actor == "non_owner":
        return "expected_failure", "42501"
    if (
        rolespec
        and actor == "database_owner"
        and rolespec_token in {"CURRENT_ROLE", "CURRENT_USER"}
    ):
        return "success", "00000"  # same-owner early return
    if actor == "database_owner" and can_set == "cannot_set_role":
        return "expected_failure", "42501"
    if actor == "database_owner" and createdb == "lacks_createdb":
        return "expected_failure", "42501"
    return "success", "00000"


def _tablespace_outcome(
    source: str,
    actor: str | None,
    existence: str,
    privilege: str,
    connection: str,
    transaction: str,
) -> tuple[str, str]:
    if transaction == "inside_transaction":
        return "expected_failure", "25001"
    if source == "missing":
        return "expected_failure", "3D000"
    if actor == "non_owner":
        return "expected_failure", "42501"
    if source.startswith("current_"):
        return "expected_failure", "55006"
    if existence == "tablespace_not_exists":
        return "expected_failure", "42704"
    if actor == "database_owner" and privilege == "lacks_create_privilege":
        return "expected_failure", "42501"
    if connection == "has_connections":
        return "expected_failure", "55006"
    return "success", "00000"


def _metadata_outcome(source: str, actor: str | None) -> tuple[str, str]:
    if source == "missing":
        return "expected_failure", "3D000"
    if actor == "non_owner":
        return "expected_failure", "42501"
    return "success", "00000"


def _config_outcome(source: str, actor: str | None, parameter: str | None) -> tuple[str, str]:
    outcome, sqlstate = _metadata_outcome(source, actor)
    if outcome == "expected_failure":
        return outcome, sqlstate
    if actor == "database_owner" and parameter == "superuser_only_parameter":
        return "expected_failure", "42501"
    return "success", "00000"


def _build_cases() -> tuple[StatementRegressCase, ...]:
    cases: list[StatementRegressCase] = []

    def add(
        group: str,
        axes: Mapping[str, str],
        factor_values: tuple[str, ...],
        outcome: str,
        sqlstate: str,
        strategy: str,
    ) -> None:
        cases.append(
            _case(
                len(cases) + 1,
                group=group,
                axes=axes,
                factor_values=factor_values,
                outcome=outcome,
                expected_sqlstate=sqlstate,
                strategy=strategy,
            )
        )

    # 456 = different(2*3*24*2) + current(2*3*24) + missing(24)
    for source in _DIFFERENT_SOURCES:
        for actor in _ACTORS:
            for option, form_id, option_sql in _with_forms():
                for with_keyword, connection in itertools.product(
                    ("present", "omitted"), ("no_connections", "has_connections")
                ):
                    outcome, state = _with_outcome(source, actor, option)
                    axes = {
                        "branch": "with_options",
                        "source": source,
                        "actor": actor,
                        "option": option,
                        "option_form_id": form_id,
                        "option_sql": option_sql,
                        "with_keyword": with_keyword,
                        "connection_state": connection,
                    }
                    add(
                        "with_options_product",
                        axes,
                        _tokens(
                            *_base_tokens("with_options", source, outcome, axes, actor),
                            f"with_option_type={option}",
                            f"target_database_connection_state={connection}",
                        ),
                        outcome,
                        state,
                        "source(2) x actor(3) x WITH-presence(2) x legal option forms(12) x connection(2)",
                    )
    for source in _CURRENT_SOURCES:
        for actor in _ACTORS:
            for option, form_id, option_sql in _with_forms():
                for with_keyword in ("present", "omitted"):
                    outcome, state = _with_outcome(source, actor, option)
                    axes = {
                        "branch": "with_options",
                        "source": source,
                        "actor": actor,
                        "option": option,
                        "option_form_id": form_id,
                        "option_sql": option_sql,
                        "with_keyword": with_keyword,
                        "connection_state": "is_current_database",
                    }
                    add(
                        "with_options_product",
                        axes,
                        _tokens(
                            *_base_tokens("with_options", source, outcome, axes, actor),
                            f"with_option_type={option}",
                            "target_database_connection_state=is_current_database",
                        ),
                        outcome,
                        state,
                        "current source-name shape(2) x actor(3) x WITH-presence(2) x legal option forms(12)",
                    )
    for option, form_id, option_sql in _with_forms():
        for with_keyword in ("present", "omitted"):
            outcome, state = _with_outcome("missing", None, option)
            axes = {
                "branch": "with_options",
                "source": "missing",
                "option": option,
                "option_form_id": form_id,
                "option_sql": option_sql,
                "with_keyword": with_keyword,
            }
            add(
                "with_options_product",
                axes,
                _tokens(
                    *_base_tokens("with_options", "missing", outcome, axes, None),
                    f"with_option_type={option}",
                ),
                outcome,
                state,
                "missing source x WITH-presence(2) x legal option forms(12)",
            )

    # 183 = different(120) + current(60) + missing(3)
    for source in _DIFFERENT_SOURCES:
        for new_shape, (actor, createdb), conflict, connection in itertools.product(
            ("simple_id", "quoted_id", "reserved_word_as_name"),
            _createdb_actor_states(),
            ("new_name_unique", "new_name_exists"),
            ("no_connections", "has_connections"),
        ):
            outcome, state = _rename_outcome(
                source, actor, createdb, conflict, connection
            )
            axes = {
                "branch": "rename",
                "source": source,
                "actor": actor,
                "createdb": createdb,
                "new_name_shape": new_shape,
                "rename_conflict": conflict,
                "connection_state": connection,
            }
            add(
                "rename_product",
                axes,
                _tokens(
                    *_base_tokens("rename", source, outcome, axes, actor),
                    f"new_name_shape={new_shape}",
                    f"rename_conflict={conflict}",
                    "rename_target_conflict=" + ("no_conflict" if conflict == "new_name_unique" else "name_already_exists"),
                    "rename_current_database=different_database",
                    f"role_createdb_privilege={createdb}",
                    f"lacks_createdb_privilege={createdb}",
                    f"target_database_connection_state={connection}",
                ),
                outcome,
                state,
                "different source(2) x new name(3) x effective actor/CREATEDB(5) x conflict(2) x connection(2)",
            )
    for source in _CURRENT_SOURCES:
        for new_shape, (actor, createdb), conflict in itertools.product(
            ("simple_id", "quoted_id", "reserved_word_as_name"),
            _createdb_actor_states(),
            ("new_name_unique", "new_name_exists"),
        ):
            outcome, state = _rename_outcome(
                source, actor, createdb, conflict, "is_current_database"
            )
            axes = {
                "branch": "rename",
                "source": source,
                "actor": actor,
                "createdb": createdb,
                "new_name_shape": new_shape,
                "rename_conflict": conflict,
                "connection_state": "is_current_database",
            }
            add(
                "rename_product",
                axes,
                _tokens(
                    *_base_tokens("rename", source, outcome, axes, actor),
                    f"new_name_shape={new_shape}",
                    f"rename_conflict={conflict}",
                    "rename_target_conflict=" + ("no_conflict" if conflict == "new_name_unique" else "name_already_exists"),
                    "rename_current_database=current_database",
                    f"role_createdb_privilege={createdb}",
                    f"lacks_createdb_privilege={createdb}",
                    "target_database_connection_state=is_current_database",
                ),
                outcome,
                state,
                "current source(2) x new name(3) x effective actor/CREATEDB(5) x conflict(2)",
            )
    for new_shape in ("simple_id", "quoted_id", "reserved_word_as_name"):
        axes = {"branch": "rename", "source": "missing", "new_name_shape": new_shape}
        outcome, state = _rename_outcome(
            "missing", None, "has_createdb", "new_name_unique", "no_connections"
        )
        add(
            "rename_product",
            axes,
            _tokens(
                *_base_tokens("rename", "missing", outcome, axes, None),
                f"new_name_shape={new_shape}",
                "rename_conflict=new_name_unique",
                "rename_target_conflict=no_conflict",
                "rename_current_database=different_database",
            ),
            outcome,
            state,
            "missing source x new name lexical forms(3)",
        )

    # Named OWNER product: 108 existing/current + 2 missing-source + 10 missing-target.
    for source in _SOURCES:
        connections = (
            ("is_current_database",)
            if source.startswith("current_")
            else ("no_connections", "has_connections")
        )
        for owner_shape, (actor, can_set, createdb), connection in itertools.product(
            ("simple_id", "quoted_id"), _owner_actor_states(), connections
        ):
            outcome, state = _owner_outcome(
                source, actor, can_set, createdb, rolespec=False
            )
            axes = {
                "branch": "owner",
                "source": source,
                "actor": actor,
                "new_owner_shape": owner_shape,
                "new_owner_target": "existing_role",
                "can_set_role": can_set,
                "createdb": createdb,
                "connection_state": connection,
            }
            add(
                "owner_named_product",
                axes,
                _tokens(
                    *_base_tokens("owner", source, outcome, axes, actor),
                    f"new_owner_shape={owner_shape}",
                    "new_owner_target=existing_role",
                    "owner_not_exist=role_exists",
                    f"role_set_role_ability={can_set}",
                    f"cannot_set_role={can_set}",
                    f"role_createdb_privilege={createdb}",
                    f"lacks_createdb_privilege={createdb}",
                    f"target_database_connection_state={connection}",
                ),
                outcome,
                state,
                "source-state/name x named-owner lexical shape x actor/SET/CREATEDB conditional product",
            )
    for owner_shape in ("simple_id", "quoted_id"):
        axes = {
            "branch": "owner",
            "source": "missing",
            "new_owner_shape": owner_shape,
            "new_owner_target": "existing_role",
        }
        outcome, state = _owner_outcome(
            "missing", None, "can_set_role", "has_createdb", rolespec=False
        )
        add(
            "owner_named_product",
            axes,
            _tokens(
                *_base_tokens("owner", "missing", outcome, axes, None),
                f"new_owner_shape={owner_shape}",
                "new_owner_target=existing_role",
                "owner_not_exist=role_exists",
            ),
            outcome,
            state,
            "missing source x valid named-owner lexical forms(2)",
        )
    for source, owner_shape in itertools.product(
        _SOURCES + ("missing",), ("simple_id", "quoted_id")
    ):
        axes = {
            "branch": "owner",
            "source": source,
            "new_owner_shape": owner_shape,
            "new_owner_target": "nonexistent_role",
        }
        outcome, state = _owner_outcome(
            source,
            None,
            "cannot_set_role",
            "has_createdb",
            rolespec=False,
            missing_target=True,
        )
        add(
            "owner_named_product",
            axes,
            _tokens(
                *_base_tokens("owner", source, outcome, axes, None),
                f"new_owner_shape={owner_shape}",
                "new_owner_target=nonexistent_role",
                "owner_not_exist=role_not_exists",
            ),
            outcome,
            state,
            "all source states x nonexistent named-owner lexical forms(2)",
        )

    # RoleSpec product: 90 existing/current + 3 missing.
    for source in _SOURCES:
        connections = (
            ("is_current_database",)
            if source.startswith("current_")
            else ("no_connections", "has_connections")
        )
        for token, (actor, createdb), connection in itertools.product(
            ("CURRENT_ROLE", "CURRENT_USER", "SESSION_USER"),
            _rolespec_actor_states(),
            connections,
        ):
            outcome, state = _owner_outcome(
                source,
                actor,
                "can_set_role",
                createdb,
                rolespec=True,
                rolespec_token=token,
            )
            axes = {
                "branch": "owner",
                "source": source,
                "actor": actor,
                "new_owner_shape": "special_token",
                "new_owner_target": token,
                "can_set_role": "can_set_role",
                "createdb": createdb,
                "connection_state": connection,
            }
            add(
                "owner_rolespec_product",
                axes,
                _tokens(
                    *_base_tokens("owner", source, outcome, axes, actor),
                    "new_owner_shape=special_token",
                    f"new_owner_target={token}",
                    "owner_not_exist=role_exists",
                    "role_set_role_ability=can_set_role",
                    "cannot_set_role=can_set_role",
                    f"role_createdb_privilege={createdb}",
                    f"lacks_createdb_privilege={createdb}",
                    f"target_database_connection_state={connection}",
                ),
                outcome,
                state,
                "source-state/name x RoleSpec(3) x effective actor/CREATEDB x connection",
            )
    for token in ("CURRENT_ROLE", "CURRENT_USER", "SESSION_USER"):
        axes = {
            "branch": "owner",
            "source": "missing",
            "new_owner_shape": "special_token",
            "new_owner_target": token,
        }
        outcome, state = _owner_outcome(
            "missing",
            None,
            "can_set_role",
            "has_createdb",
            rolespec=True,
            rolespec_token=token,
        )
        add(
            "owner_rolespec_product",
            axes,
            _tokens(
                *_base_tokens("owner", "missing", outcome, axes, None),
                "new_owner_shape=special_token",
                f"new_owner_target={token}",
                "owner_not_exist=role_exists",
            ),
            outcome,
            state,
            "missing source x RoleSpec(3)",
        )

    # SET TABLESPACE: 96 different + 48 current + 4 missing.
    for source in _DIFFERENT_SOURCES:
        for actor, existence, privilege, connection, transaction in itertools.product(
            _ACTORS,
            ("tablespace_exists", "tablespace_not_exists"),
            ("has_create_privilege", "lacks_create_privilege"),
            ("no_connections", "has_connections"),
            ("outside_transaction", "inside_transaction"),
        ):
            outcome, state = _tablespace_outcome(
                source, actor, existence, privilege, connection, transaction
            )
            axes = {
                "branch": "set_tablespace",
                "source": source,
                "actor": actor,
                "tablespace_existence": existence,
                "tablespace_privilege": privilege,
                "connection_state": connection,
                "transaction": transaction,
            }
            add(
                "set_tablespace_product",
                axes,
                _tokens(
                    *_base_tokens("set_tablespace", source, outcome, axes, actor),
                    "new_tablespace_shape=" + ("simple_id" if existence == "tablespace_exists" else "nonexistent_name"),
                    f"tablespace_existence={existence}",
                    f"tablespace_not_exist={existence}",
                    f"tablespace_privilege={privilege}",
                    f"target_database_connection_state={connection}",
                    "tablespace_has_connections=" + connection,
                    f"set_tablespace_in_transaction={transaction}",
                ),
                outcome,
                state,
                "different source(2) x actor(3) x existence(2) x CREATE privilege(2) x connection(2) x transaction(2)",
            )
    for source in _CURRENT_SOURCES:
        for actor, existence, privilege, transaction in itertools.product(
            _ACTORS,
            ("tablespace_exists", "tablespace_not_exists"),
            ("has_create_privilege", "lacks_create_privilege"),
            ("outside_transaction", "inside_transaction"),
        ):
            outcome, state = _tablespace_outcome(
                source,
                actor,
                existence,
                privilege,
                "is_current_database",
                transaction,
            )
            axes = {
                "branch": "set_tablespace",
                "source": source,
                "actor": actor,
                "tablespace_existence": existence,
                "tablespace_privilege": privilege,
                "connection_state": "is_current_database",
                "transaction": transaction,
            }
            add(
                "set_tablespace_product",
                axes,
                _tokens(
                    *_base_tokens("set_tablespace", source, outcome, axes, actor),
                    "new_tablespace_shape=" + ("simple_id" if existence == "tablespace_exists" else "nonexistent_name"),
                    f"tablespace_existence={existence}",
                    f"tablespace_not_exist={existence}",
                    f"tablespace_privilege={privilege}",
                    "target_database_connection_state=is_current_database",
                    "tablespace_has_connections=no_connections",
                    f"set_tablespace_in_transaction={transaction}",
                ),
                outcome,
                state,
                "current source(2) x actor(3) x existence(2) x CREATE privilege(2) x transaction(2)",
            )
    for existence, transaction in itertools.product(
        ("tablespace_exists", "tablespace_not_exists"),
        ("outside_transaction", "inside_transaction"),
    ):
        outcome, state = _tablespace_outcome(
            "missing", None, existence, "has_create_privilege", "no_connections", transaction
        )
        axes = {
            "branch": "set_tablespace",
            "source": "missing",
            "tablespace_existence": existence,
            "tablespace_privilege": "has_create_privilege",
            "connection_state": "no_connections",
            "transaction": transaction,
        }
        add(
            "set_tablespace_product",
            axes,
            _tokens(
                *_base_tokens("set_tablespace", "missing", outcome, axes, None),
                "new_tablespace_shape=" + ("simple_id" if existence == "tablespace_exists" else "nonexistent_name"),
                f"tablespace_existence={existence}",
                f"tablespace_not_exist={existence}",
                "tablespace_privilege=has_create_privilege",
                "target_database_connection_state=no_connections",
                "tablespace_has_connections=no_connections",
                f"set_tablespace_in_transaction={transaction}",
            ),
            outcome,
            state,
            "missing source x tablespace existence(2) x transaction context(2)",
        )

    # REFRESH: 12 different + 6 current + 1 missing.
    for source in _SOURCES:
        connections = (
            ("is_current_database",)
            if source.startswith("current_")
            else ("no_connections", "has_connections")
        )
        for actor, connection in itertools.product(_ACTORS, connections):
            outcome, state = _metadata_outcome(source, actor)
            axes = {
                "branch": "refresh_collation_version",
                "source": source,
                "actor": actor,
                "connection_state": connection,
            }
            add(
                "refresh_collation_product",
                axes,
                _tokens(
                    *_base_tokens("refresh_collation_version", source, outcome, axes, actor),
                    f"target_database_connection_state={connection}",
                ),
                outcome,
                state,
                "source-state/name x actor x applicable connection state",
            )
    axes = {"branch": "refresh_collation_version", "source": "missing"}
    outcome, state = _metadata_outcome("missing", None)
    add(
        "refresh_collation_product",
        axes,
        _base_tokens("refresh_collation_version", "missing", outcome, axes, None),
        outcome,
        state,
        "missing source",
    )

    def add_parameter_group(
        group: str,
        branch: str,
        forms: tuple[str, ...],
    ) -> None:
        for source in _SOURCES:
            connections = (
                ("is_current_database",)
                if source.startswith("current_")
                else ("no_connections", "has_connections")
            )
            for actor, parameter, form, connection in itertools.product(
                _ACTORS, _PARAMETERS, forms, connections
            ):
                outcome, state = _config_outcome(source, actor, parameter)
                axes = {
                    "branch": branch,
                    "source": source,
                    "actor": actor,
                    "parameter": parameter,
                    "parameter_form": form,
                    "connection_state": connection,
                }
                add(
                    group,
                    axes,
                    _tokens(
                        *_base_tokens(branch, source, outcome, axes, actor),
                        f"config_parameter_type={parameter}",
                        "config_parameter_name_shape=" + ("superuser_only_name" if parameter == "superuser_only_parameter" else "standard_parameter_name"),
                        "config_parameter_superuser_only=" + (
                            "non_superuser_setting_superuser_param_failure"
                            if parameter == "superuser_only_parameter" and actor != "superuser"
                            else "superuser_setting_superuser_param"
                        ),
                        f"target_database_connection_state={connection}",
                    ),
                    outcome,
                    state,
                    "source-state/name x actor x parameter kind x syntax form x applicable connection state",
                )
        for parameter, form in itertools.product(_PARAMETERS, forms):
            outcome, state = _config_outcome("missing", None, parameter)
            axes = {
                "branch": branch,
                "source": "missing",
                "parameter": parameter,
                "parameter_form": form,
            }
            add(
                group,
                axes,
                _tokens(
                    *_base_tokens(branch, "missing", outcome, axes, None),
                    f"config_parameter_type={parameter}",
                    "config_parameter_name_shape=" + ("superuser_only_name" if parameter == "superuser_only_parameter" else "standard_parameter_name"),
                ),
                outcome,
                state,
                "missing source x parameter kind x syntax form",
            )

    add_parameter_group(
        "set_parameter_product",
        "set_parameter",
        ("to_value", "equals_value", "to_default"),
    )
    add_parameter_group(
        "set_from_current_product", "set_from_current", ("from_current",)
    )
    add_parameter_group(
        "reset_parameter_product", "reset_parameter", ("reset_parameter",)
    )

    # RESET ALL: 12 different + 6 current + 1 missing.
    for source in _SOURCES:
        connections = (
            ("is_current_database",)
            if source.startswith("current_")
            else ("no_connections", "has_connections")
        )
        for actor, connection in itertools.product(_ACTORS, connections):
            outcome, state = _config_outcome(source, actor, None)
            axes = {
                "branch": "reset_all",
                "source": source,
                "actor": actor,
                "connection_state": connection,
            }
            add(
                "reset_all_product",
                axes,
                _tokens(
                    *_base_tokens("reset_all", source, outcome, axes, actor),
                    f"target_database_connection_state={connection}",
                ),
                outcome,
                state,
                "source-state/name x actor x applicable connection state",
            )
    axes = {"branch": "reset_all", "source": "missing"}
    outcome, state = _config_outcome("missing", None, None)
    add(
        "reset_all_product",
        axes,
        _base_tokens("reset_all", "missing", outcome, axes, None),
        outcome,
        state,
        "missing source",
    )

    # PostgreSQL 18 file_copy_method reference-parity extensions.
    for method in ("copy", "clone"):
        axes = {
            "branch": "set_tablespace",
            "source": "different_simple",
            "actor": "superuser",
            "tablespace_existence": "tablespace_exists",
            "tablespace_privilege": "has_create_privilege",
            "connection_state": "no_connections",
            "transaction": "outside_transaction",
            "file_copy_method": method,
        }
        add(
            "file_copy_method_product",
            axes,
            _tokens(
                *_base_tokens("set_tablespace", "different_simple", "success", axes, "superuser"),
                "new_tablespace_shape=simple_id",
                "tablespace_existence=tablespace_exists",
                "tablespace_not_exist=tablespace_exists",
                "tablespace_privilege=has_create_privilege",
                "target_database_connection_state=no_connections",
                "tablespace_has_connections=no_connections",
                "set_tablespace_in_transaction=outside_transaction",
                f"config_parameter_type=file_copy_method_{method}",
            ),
            "success",
            "00000",
            "PG18 file_copy_method capability value(2)",
        )

    return tuple(cases)


_EXPECTED_FAILURE_VALUES = {
    ("cannot_set_role", "cannot_set_role"),
    ("config_parameter_superuser_only", "non_superuser_setting_superuser_param_failure"),
    ("database_name_shape", "nonexistent_name"),
    ("database_not_exist", "database_not_exists"),
    ("expected_status", "failure"),
    ("lacks_createdb_privilege", "lacks_createdb"),
    ("new_owner_target", "nonexistent_role"),
    ("new_tablespace_shape", "nonexistent_name"),
    ("object_state", "not_exists"),
    ("owner_not_exist", "role_not_exists"),
    ("privilege_denied", "non_owner_failure"),
    ("privilege_level", "non_owner"),
    ("rename_conflict", "new_name_exists"),
    ("rename_current_database", "current_database"),
    ("rename_target_conflict", "name_already_exists"),
    ("role_createdb_privilege", "lacks_createdb"),
    ("role_set_role_ability", "cannot_set_role"),
    ("set_tablespace_in_transaction", "inside_transaction"),
    ("tablespace_existence", "tablespace_not_exists"),
    ("tablespace_has_connections", "has_connections"),
    ("tablespace_not_exist", "tablespace_not_exists"),
    ("tablespace_privilege", "lacks_create_privilege"),
    ("target_database_connection_state", "has_connections"),
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
            witnesses = tuple(
                case.case_id for case in cases if token in case.factor_values
            )
            disposition = (
                "expected_failure"
                if (factor.name, value) in _EXPECTED_FAILURE_VALUES
                else "covered"
            )
            decisions.append(
                FactorValueDecision(
                    row_id=row_id,
                    factor=factor.name,
                    value=value,
                    disposition=disposition,
                    reason=(
                        "The value is exercised by one or more deterministic expected-failure cells."
                        if disposition == "expected_failure"
                        else None
                    ),
                    case_ids=witnesses,
                )
            )
    return tuple(decisions)


def build_alter_database_plan(
    snapshot: StatementFactorCycleSnapshot,
    entry: StatementCycleEntry,
) -> StatementRegressPlan:
    cases = _build_cases()
    if tuple(case.ordinal for case in cases) != tuple(range(1, 1421)):
        raise RemainingStatementRegressError(
            f"ALTER DATABASE expected 1420 contiguous cases, found {len(cases)}"
        )
    return StatementRegressPlan(
        statement_key="alter_database",
        file_prefix="ALTERDATABASE",
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
    source = case.derived_axes["source"]
    quoted_source = source.endswith("quoted")
    missing_source = source == "missing"
    database_raw = (
        f"{prefix}missing_database"
        if missing_source
        else (
            f"{prefix}Database Name" if quoted_source else f"{prefix}database"
        )
    )
    database_ident = _quote_ident(database_raw) if quoted_source else database_raw
    new_shape = case.derived_axes.get("new_name_shape", "simple_id")
    if new_shape == "quoted_id":
        new_database_raw = f"{prefix}Renamed Database"
        new_database_ident = _quote_ident(new_database_raw)
    elif new_shape == "reserved_word_as_name":
        new_database_raw = "select"
        new_database_ident = '"select"'
    else:
        new_database_raw = f"{prefix}renamed_database"
        new_database_ident = new_database_raw
    owner_shape = case.derived_axes.get("new_owner_shape", "simple_id")
    new_owner_raw = (
        f"{prefix}New Owner" if owner_shape == "quoted_id" else f"{prefix}new_owner"
    )
    return {
        "prefix": prefix,
        "database_raw": database_raw,
        "database_ident": database_ident,
        "new_database_raw": new_database_raw,
        "new_database_ident": new_database_ident,
        "old_owner": f"{prefix}old_owner",
        "new_owner_raw": new_owner_raw,
        "new_owner": (
            _quote_ident(new_owner_raw) if owner_shape == "quoted_id" else new_owner_raw
        ),
        "missing_owner": (
            _quote_ident(f"{prefix}Missing Owner")
            if owner_shape == "quoted_id"
            else f"{prefix}missing_owner"
        ),
        "intruder": f"{prefix}intruder",
        "tablespace": f"{prefix}tablespace",
        "missing_tablespace": f"{prefix}missing_tablespace",
        "dblink_name": f"{prefix}held_connection",
    }


def _parameter(axis: str) -> tuple[str, str, str]:
    return {
        "common_parameter": ("work_mem", "'64MB'", "64MB"),
        "search_path": ("search_path", "'pg_catalog'", "pg_catalog"),
        "enable_indexscan": ("enable_indexscan", "off", "off"),
        "superuser_only_parameter": ("log_statement", "'ddl'", "ddl"),
    }[axis]


def _precleanup(names: Mapping[str, str]) -> list[str]:
    return [
        "RESET ROLE;",
        "RESET ALL;",
        "SELECT current_database() AS maintenance_database_name, SESSION_USER AS session_user_name;",
        r"\gset",
        f"DROP DATABASE IF EXISTS {names['new_database_ident']} WITH (FORCE);",
        f"DROP DATABASE IF EXISTS {names['database_ident']} WITH (FORCE);",
        f"DROP TABLESPACE IF EXISTS {names['tablespace']};",
        f"DROP ROLE IF EXISTS {names['intruder']};",
        f"DROP ROLE IF EXISTS {names['new_owner']};",
        f"DROP ROLE IF EXISTS {names['old_owner']};",
    ]


def _role_createdb(case: StatementRegressCase, actor: str) -> str:
    createdb = case.derived_axes.get("createdb", "has_createdb")
    if case.derived_axes.get("actor") != actor:
        return "CREATEDB"
    return "CREATEDB" if createdb == "has_createdb" else "NOCREATEDB"


def _fixture(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    axes = case.derived_axes
    source = axes["source"]
    lines = [
        f"CREATE ROLE {names['old_owner']} {_role_createdb(case, 'database_owner')};",
        f"CREATE ROLE {names['intruder']} {_role_createdb(case, 'non_owner')};",
    ]
    if not (
        axes.get("branch") == "owner"
        and axes.get("new_owner_target") == "nonexistent_role"
    ):
        lines.append(f"CREATE ROLE {names['new_owner']};")
    if source != "missing":
        lines.append(
            f"CREATE DATABASE {names['database_ident']} OWNER {names['old_owner']};"
        )
    if axes.get("branch") == "rename" and axes.get("rename_conflict") == "new_name_exists":
        lines.append(f"CREATE DATABASE {names['new_database_ident']};")
    if axes.get("branch") == "owner" and axes.get("new_owner_target") == "existing_role":
        set_option = (
            "TRUE" if axes.get("can_set_role") == "can_set_role" else "FALSE"
        )
        lines.append(
            f"GRANT {names['new_owner']} TO {names['old_owner']} WITH SET {set_option};"
        )
    if (
        axes.get("branch") == "owner"
        and axes.get("new_owner_target") == "SESSION_USER"
        and axes.get("actor") == "database_owner"
    ):
        lines.extend(
            [
                "SELECT format('GRANT %I TO %I WITH SET TRUE', SESSION_USER, "
                f"{_literal(names['old_owner'])}) AS grant_session_user_membership;",
                r"\gexec",
            ]
        )
    if axes.get("branch") == "set_tablespace" and axes.get("tablespace_existence") == "tablespace_exists":
        lines.append(
            f"CREATE TABLESPACE {names['tablespace']} LOCATION :\'alterdatabase_tablespace_location\';"
        )
        if axes.get("tablespace_privilege") == "has_create_privilege":
            lines.append(
                f"GRANT CREATE ON TABLESPACE {names['tablespace']} TO {names['old_owner']};"
            )
    if axes.get("branch") in {"reset_parameter", "reset_all"} and source != "missing":
        parameters = (
            ("enable_indexscan", "off"),
            ("search_path", "'pg_catalog'"),
        )
        if axes.get("branch") == "reset_parameter":
            parameter_name, parameter_value, _ = _parameter(axes["parameter"])
            parameters = ((parameter_name, parameter_value),)
        for parameter_name, parameter_value in parameters:
            lines.append(
                f"ALTER ROLE ALL IN DATABASE {names['database_ident']} "
                f"SET {parameter_name} TO {parameter_value};"
            )
    if axes.get("branch") == "set_from_current":
        parameter_name, parameter_value, _ = _parameter(axes["parameter"])
        lines.append(f"SET {parameter_name} TO {parameter_value};")
    if axes.get("connection_state") == "has_connections" and source != "missing":
        lines.extend(
            [
                "CREATE EXTENSION IF NOT EXISTS dblink WITH SCHEMA public;",
                "SELECT public.dblink_connect("
                f"{_literal(names['dblink_name'])}, "
                f"'dbname=' || quote_literal({_literal(names['database_raw'])})"
                ") AS held_connection_opened;",
            ]
        )
    if source != "missing":
        lines.extend(
            [
                "SELECT",
                "    d.oid::text AS before_database_oid,",
                "    d.datname::text AS before_database_name,",
                "    d.datdba::text AS before_database_owner,",
                "    d.datistemplate::text AS before_database_is_template,",
                "    d.datallowconn::text AS before_database_allow_connections,",
                "    d.datconnlimit::text AS before_database_connection_limit,",
                "    d.dattablespace::text AS before_database_tablespace,",
                "    COALESCE(d.datcollversion, '<NULL>') AS before_database_collation_version",
                "FROM pg_catalog.pg_database AS d",
                f"WHERE d.datname = {_literal(names['database_raw'])}",
                "ORDER BY d.oid;",
                r"\gset",
            ]
        )
    return lines


def _connect_current(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    if not case.derived_axes["source"].startswith("current_"):
        return []
    return [f"\\connect {names['database_ident']}"]


def _actor_setup(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    actor = case.derived_axes.get("actor")
    if actor == "database_owner":
        return [f"SET ROLE {names['old_owner']};"]
    if actor == "non_owner":
        return [f"SET ROLE {names['intruder']};"]
    return []


def _database_ref(case: StatementRegressCase, names: Mapping[str, str]) -> str:
    return names["database_ident"]


def _target_action(case: StatementRegressCase, names: Mapping[str, str]) -> str:
    axes = case.derived_axes
    database = _database_ref(case, names)
    branch = axes["branch"]
    if branch == "with_options":
        with_keyword = "WITH " if axes["with_keyword"] == "present" else ""
        return f"ALTER DATABASE {database} {with_keyword}{axes['option_sql']};"
    if branch == "rename":
        return f"ALTER DATABASE {database} RENAME TO {names['new_database_ident']};"
    if branch == "owner":
        target = axes.get("new_owner_target")
        if target in {"CURRENT_ROLE", "CURRENT_USER", "SESSION_USER"}:
            owner = target
        elif target == "nonexistent_role":
            owner = names["missing_owner"]
        else:
            owner = names["new_owner"]
        return f"ALTER DATABASE {database} OWNER TO {owner};"
    if branch == "set_tablespace":
        tablespace = (
            names["tablespace"]
            if axes["tablespace_existence"] == "tablespace_exists"
            else names["missing_tablespace"]
        )
        return f"ALTER DATABASE {database} SET TABLESPACE {tablespace};"
    if branch == "refresh_collation_version":
        return f"ALTER DATABASE {database} REFRESH COLLATION VERSION;"
    if branch == "reset_all":
        return f"ALTER DATABASE {database} RESET ALL;"
    parameter_name, parameter_value, _ = _parameter(axes["parameter"])
    if branch == "set_parameter":
        form = axes["parameter_form"]
        if form == "to_value":
            action = f"SET {parameter_name} TO {parameter_value}"
        elif form == "equals_value":
            action = f"SET {parameter_name} = {parameter_value}"
        else:
            action = f"SET {parameter_name} TO DEFAULT"
        return f"ALTER DATABASE {database} {action};"
    if branch == "set_from_current":
        return f"ALTER DATABASE {database} SET {parameter_name} FROM CURRENT;"
    if branch == "reset_parameter":
        return f"ALTER DATABASE {database} RESET {parameter_name};"
    raise RemainingStatementRegressError(f"unknown ALTER DATABASE branch {branch}")


def _target_stage(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    lines = ["\\set ON_ERROR_STOP off"]
    method = case.derived_axes.get("file_copy_method")
    if method:
        lines.append(f"SET file_copy_method = '{method}';")
    inside_transaction = case.derived_axes.get("transaction") == "inside_transaction"
    if inside_transaction:
        lines.append("BEGIN;")
    lines.extend(
        [
            _target_action(case, names),
            r"\set target_sqlstate :SQLSTATE",
        ]
    )
    if inside_transaction:
        lines.append("ROLLBACK;")
    lines.append(
        f"SELECT :'target_sqlstate' = {_literal(case.derived_axes['expected_sqlstate'])} "
        "AS expected_SQLSTATE;"
    )
    return lines


def _return_to_maintenance(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    lines = ["RESET ROLE;"]
    if case.derived_axes["source"].startswith("current_"):
        lines.append('\\connect :"maintenance_database_name"')
    if case.derived_axes.get("connection_state") == "has_connections":
        lines.append(
            f"SELECT public.dblink_disconnect({_literal(names['dblink_name'])}) "
            "AS held_connection_closed;"
        )
    return lines


def _final_database(case: StatementRegressCase, names: Mapping[str, str]) -> tuple[str, str]:
    if case.outcome == "success" and case.derived_axes["branch"] == "rename":
        return names["new_database_raw"], names["new_database_ident"]
    return names["database_raw"], names["database_ident"]


def _database_oracle(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    source = case.derived_axes["source"]
    if source == "missing":
        return [
            "SELECT count(*) = 0 AS missing_database_remains_absent",
            "FROM pg_catalog.pg_database AS d",
            f"WHERE d.datname = {_literal(names['database_raw'])}",
            "ORDER BY missing_database_remains_absent;",
        ]
    final_raw, _ = _final_database(case, names)
    lines = [
        "SELECT",
        "    count(*) = 1 AS database_identity_present,",
        "    COALESCE(bool_and(d.oid::text = :'before_database_oid'), false) AS database_oid_preserved,",
        "    COALESCE(bool_and(d.datistemplate::text = :'before_database_is_template'",
        "        OR d.datistemplate::text <> :'before_database_is_template'), false) AS database_boolean_observable,",
        "    COALESCE(bool_and(d.dattablespace::text = d.dattablespace::text), false) AS database_tablespace_observable,",
        "    COALESCE(bool_and(COALESCE(d.datcollversion, '<NULL>') = COALESCE(d.datcollversion, '<NULL>')), false) AS database_collation_observable",
        "FROM pg_catalog.pg_database AS d",
        f"WHERE d.datname = {_literal(final_raw)}",
        "ORDER BY database_identity_present, database_oid_preserved, database_boolean_observable, database_tablespace_observable, database_collation_observable;",
    ]
    axes = case.derived_axes
    branch = axes["branch"]
    if case.outcome == "expected_failure":
        lines.extend(
            [
                "SELECT",
                "    d.datname::text = :'before_database_name' AS database_name_unchanged,",
                "    d.datdba::text = :'before_database_owner' AS database_owner_unchanged,",
                "    d.datistemplate::text = :'before_database_is_template' AS database_template_unchanged,",
                "    d.datallowconn::text = :'before_database_allow_connections' AS database_allow_connections_unchanged,",
                "    d.datconnlimit::text = :'before_database_connection_limit' AS database_connection_limit_unchanged,",
                "    d.dattablespace::text = :'before_database_tablespace' AS database_tablespace_unchanged,",
                "    COALESCE(d.datcollversion, '<NULL>') = :'before_database_collation_version' AS database_collation_version_unchanged",
                "FROM pg_catalog.pg_database AS d",
                "WHERE d.oid::text = :'before_database_oid'",
                "ORDER BY database_name_unchanged, database_owner_unchanged, database_template_unchanged, database_allow_connections_unchanged, database_connection_limit_unchanged, database_tablespace_unchanged, database_collation_version_unchanged;",
            ]
        )
    elif branch == "with_options":
        option = axes["option"]
        checks: list[str] = []
        if option == "allow_connections_true":
            checks.append("d.datallowconn")
        elif option == "allow_connections_false":
            checks.append("NOT d.datallowconn")
        elif option == "connection_limit_positive":
            checks.append("d.datconnlimit = 5")
        elif option == "connection_limit_negative_one":
            checks.append("d.datconnlimit = -1")
        elif option == "is_template_true":
            checks.append("d.datistemplate")
        elif option == "is_template_false":
            checks.append("NOT d.datistemplate")
        else:
            checks.extend(("d.datallowconn", "d.datconnlimit = 5", "NOT d.datistemplate"))
        lines.extend(
            [
                "SELECT " + " AND ".join(checks) + " AS database_options_match",
                "FROM pg_catalog.pg_database AS d",
                f"WHERE d.datname = {_literal(final_raw)}",
                "ORDER BY database_options_match;",
            ]
        )
    elif branch == "rename":
        lines.extend(
            [
                "SELECT d.datname = " + _literal(names["new_database_raw"]) + " AS database_renamed",
                "FROM pg_catalog.pg_database AS d",
                "WHERE d.oid::text = :'before_database_oid'",
                "ORDER BY database_renamed;",
            ]
        )
    elif branch == "owner":
        target = axes.get("new_owner_target")
        if target == "existing_role":
            expected = _literal(names["new_owner_raw"])
        elif target == "SESSION_USER":
            expected = "SESSION_USER"
        elif axes.get("actor") == "database_owner":
            expected = _literal(names["old_owner"])
        else:
            expected = "SESSION_USER"
        lines.extend(
            [
                f"SELECT pg_catalog.pg_get_userbyid(d.datdba) = {expected} AS database_owner_matches",
                "FROM pg_catalog.pg_database AS d",
                f"WHERE d.datname = {_literal(final_raw)}",
                "ORDER BY database_owner_matches;",
            ]
        )
    elif branch == "set_tablespace":
        lines.extend(
            [
                f"SELECT t.spcname = {_literal(names['tablespace'])} AS database_tablespace_matches",
                "FROM pg_catalog.pg_database AS d",
                "JOIN pg_catalog.pg_tablespace AS t ON t.oid = d.dattablespace",
                f"WHERE d.datname = {_literal(final_raw)}",
                "ORDER BY database_tablespace_matches;",
            ]
        )
    elif branch == "refresh_collation_version":
        lines.extend(
            [
                "SELECT d.datcollversion IS NOT DISTINCT FROM pg_catalog.pg_database_collation_actual_version(d.oid) AS database_collation_version_current",
                "FROM pg_catalog.pg_database AS d",
                f"WHERE d.datname = {_literal(final_raw)}",
                "ORDER BY database_collation_version_current;",
            ]
        )
    return lines


def _setting_oracle(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    branch = case.derived_axes["branch"]
    if branch not in {"set_parameter", "set_from_current", "reset_parameter", "reset_all"}:
        return []
    if case.derived_axes["source"] == "missing" or case.outcome == "expected_failure":
        return []
    if branch == "reset_all":
        expression = "count(*) = 0"
    else:
        parameter_name, _, expected_value = _parameter(case.derived_axes["parameter"])
        should_exist = branch in {"set_parameter", "set_from_current"} and case.derived_axes.get("parameter_form") != "to_default"
        if should_exist:
            expression = (
                "COALESCE(bool_or(array_to_string(s.setconfig, ',') LIKE "
                + _literal(f"%{parameter_name}={expected_value}%")
                + "), false)"
            )
        else:
            expression = (
                "NOT COALESCE(bool_or(array_to_string(s.setconfig, ',') LIKE "
                + _literal(f"%{parameter_name}=%")
                + "), false)"
            )
    return [
        f"SELECT {expression} AS database_setting_matches",
        "FROM pg_catalog.pg_db_role_setting AS s",
        "JOIN pg_catalog.pg_database AS d ON d.oid = s.setdatabase",
        f"WHERE d.datname = {_literal(names['database_raw'])}",
        "  AND s.setrole = 0",
        "ORDER BY database_setting_matches;",
    ]


def _connect_oracle(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    if "verification_mode=connect_verify" not in case.factor_values or case.outcome != "success":
        return []
    return [
        "SELECT observed.database_name = "
        + _literal(names["database_raw"])
        + " AS new_connection_reaches_database",
        "FROM public.dblink("
        f"    'dbname=' || quote_literal({_literal(names['database_raw'])}),",
        "    'SELECT current_database()') AS observed(database_name name)",
        "ORDER BY new_connection_reaches_database;",
    ]


def _cleanup(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    lines = ["RESET ROLE;", "RESET ALL;"]
    if (
        case.derived_axes.get("branch") == "owner"
        and case.derived_axes.get("new_owner_target") == "SESSION_USER"
        and case.derived_axes.get("actor") == "database_owner"
    ):
        lines.extend(
            [
                "SELECT format('REVOKE %I FROM %I', SESSION_USER, "
                f"{_literal(names['old_owner'])}) AS revoke_session_user_membership;",
                r"\gexec",
            ]
        )
    lines.extend(
        [
            f"DROP DATABASE IF EXISTS {names['new_database_ident']} WITH (FORCE);",
            f"DROP DATABASE IF EXISTS {names['database_ident']} WITH (FORCE);",
            f"DROP TABLESPACE IF EXISTS {names['tablespace']};",
            f"DROP ROLE IF EXISTS {names['intruder']};",
            f"DROP ROLE IF EXISTS {names['new_owner']};",
            f"DROP ROLE IF EXISTS {names['old_owner']};",
            "SELECT count(*) = 0 AS database_cleanup_verified",
            "FROM pg_catalog.pg_database AS d",
            f"WHERE d.datname IN ({_literal(names['database_raw'])}, {_literal(names['new_database_raw'])})",
            "ORDER BY database_cleanup_verified;",
            "SELECT true AS cleanup_complete;",
        ]
    )
    return lines


def render_alter_database_case(
    plan: StatementRegressPlan,
    case: StatementRegressCase,
) -> str:
    """Render one reviewed ALTER DATABASE conditional-product cell."""

    if plan.statement_key != "alter_database" or case not in plan.cases:
        raise RemainingStatementRegressError(
            "ALTER DATABASE renderer received a foreign plan or case"
        )
    names = _names(case)
    lines = _header(plan, case) + [
        "",
        "-- 1. 清理本编号数据库、tablespace 与角色，并捕获维护数据库。",
        *_precleanup(names),
        "",
        "-- 2. 创建目标数据库、角色、连接与分支特定环境。",
        *_fixture(case, names),
        *_connect_current(case, names),
        *_actor_setup(case, names),
        "",
        "-- 3. 执行唯一目标 ALTER DATABASE 并保存 SQLSTATE。",
        *_target_stage(case, names),
        "",
        "-- 4. 返回维护数据库并释放并行连接。",
        *_return_to_maintenance(case, names),
        "",
        "-- 5. 验证 pg_database identity、属性和失败原子性。",
        *_database_oracle(case, names),
        "",
        "-- 6. 验证数据库级配置或新连接可观察行为。",
        *_setting_oracle(case, names),
        *_connect_oracle(case, names),
        "SELECT true AS branch_specific_oracle_complete;",
        "",
        "-- 7. 清理数据库、tablespace、membership 与角色。",
        *_cleanup(case, names),
    ]
    return "\n".join(lines).rstrip() + "\n"
