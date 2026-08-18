"""PostgreSQL 18 ALTER CONVERSION exhaustive regress design.

The raw matrix contains aliases, derived outcomes, and branch-only axes.  This
module therefore records reviewed conditional Cartesian products instead of
expanding all twenty-four factors as if they were independent.
"""

from __future__ import annotations

import itertools
from typing import Callable, Mapping

from .remaining_statement_regress import (
    FactorValueDecision,
    RemainingStatementRegressError,
    StatementRegressCase,
    StatementRegressPlan,
    _header,
)
from .statement_factor_cycle import StatementCycleEntry, StatementFactorCycleSnapshot


_SOURCES = ("simple_id", "quoted_id", "schema_qualified")
_DEFAULTS = ("is_default_conversion", "is_not_default_conversion")
_NEW_NAMES = ("simple_id", "quoted_id", "reserved_word_as_name")
_NAMED_OWNERS = ("simple_id", "quoted_id")
_OWNER_TOKENS = ("CURRENT_ROLE", "CURRENT_USER", "SESSION_USER")
_TARGET_SCHEMAS = ("simple_id", "quoted_id")
_SUCCESS_ACTORS = ("superuser", "conversion_owner")
_ACTORS = ("superuser", "conversion_owner", "non_owner")
_BRANCHES = ("rename", "owner", "set_schema")
_CLEANUPS = ("drop_conversion", "drop_schema", "drop_role", "cascade_cleanup")


def _tokens(*values: str | None) -> tuple[str, ...]:
    result: list[str] = []
    names: set[str] = set()
    for value in values:
        if not value:
            continue
        name = value.split("=", 1)[0]
        if name in names:
            raise RemainingStatementRegressError(
                f"ALTER CONVERSION case binds factor {name!r} more than once"
            )
        names.add(name)
        result.append(value)
    return tuple(result)


def _case(
    ordinal: int,
    *,
    group: str,
    case_type: str,
    outcome: str,
    axes: Mapping[str, str],
    factor_values: tuple[str, ...],
    strategy: str,
    description: str,
    expected_anchor: str,
) -> StatementRegressCase:
    number = f"{ordinal:05d}"
    return StatementRegressCase(
        ordinal=ordinal,
        case_id=f"ALTERCONVERSION{number}",
        sql_filename=f"ALTERCONVERSION{number}.sql",
        object_prefix=f"alterconversion_{number}_",
        case_group=group,
        case_type=case_type,
        outcome=outcome,
        execution_profile="same_session_multiphase",
        derived_axes=dict(axes),
        factor_values=factor_values,
        combination_strategy=strategy,
        description=description,
        expected_anchor=expected_anchor,
    )


def _branch_token(branch: str) -> str:
    return f"statement_branch=branch_{branch}"


def _actor_tokens(actor: str, outcome: str) -> tuple[str, ...]:
    privilege = {
        "superuser": "superuser",
        "conversion_owner": "conversion_owner",
        "non_owner": "non_owner",
    }[actor]
    denied = None
    if actor == "superuser" and outcome == "success":
        denied = "privilege_denied=superuser_success"
    elif actor == "conversion_owner" and outcome == "success":
        denied = "privilege_denied=owner_success"
    elif actor == "non_owner" and outcome == "expected_failure":
        denied = "privilege_denied=non_owner_failure"
    return _tokens(f"privilege_level={privilege}", denied)


def _base_tokens(
    branch: str,
    *,
    outcome: str,
    actor: str,
    source: str | None = None,
    default_status: str | None = None,
) -> tuple[str, ...]:
    return _tokens(
        _branch_token(branch),
        "object_state=exists",
        "conversion_not_exist=conversion_exists",
        f"expected_status={'success' if outcome == 'success' else 'failure'}",
        f"conversion_name_shape={source}" if source else None,
        f"conversion_default_status={default_status}" if default_status else None,
        *_actor_tokens(actor, outcome),
    )


def _build_cases() -> tuple[StatementRegressCase, ...]:
    cases: list[StatementRegressCase] = []

    def add(
        *,
        group: str,
        case_type: str,
        outcome: str,
        axes: Mapping[str, str],
        factors: tuple[str, ...],
        strategy: str,
        description: str,
        expected_anchor: str,
    ) -> None:
        ordinal = len(cases) + 1
        verification = (
            "error_assertion"
            if outcome == "expected_failure"
            else (
                "catalog_query_pg_namespace"
                if axes.get("branch") == "set_schema"
                else "catalog_query_pg_conversion"
            )
        )
        cleanup = _CLEANUPS[(ordinal - 1) % len(_CLEANUPS)]
        axes_with_evidence = {
            **axes,
            "verification_mode": verification,
            "cleanup_mode": cleanup,
        }
        cases.append(
            _case(
                ordinal,
                group=group,
                case_type=case_type,
                outcome=outcome,
                axes=axes_with_evidence,
                factor_values=_tokens(
                    *factors,
                    f"verification_mode={verification}",
                    f"cleanup_mode={cleanup}",
                ),
                strategy=strategy,
                description=description,
                expected_anchor=expected_anchor,
            )
        )

    # Canonical main products plus the quoted target-schema extension: 102.
    for source, new_name, default_status, actor in itertools.product(
        _SOURCES, _NEW_NAMES, _DEFAULTS, _SUCCESS_ACTORS
    ):
        add(
            group="success_rename_product",
            case_type="syntax_semantics",
            outcome="success",
            axes={
                "branch": "rename",
                "source_name_shape": source,
                "new_name_shape": new_name,
                "default_status": default_status,
                "actor": actor,
                "expected_sqlstate": "00000",
            },
            factors=_tokens(
                *_base_tokens("rename", outcome="success", actor=actor, source=source, default_status=default_status),
                f"new_name_shape={new_name}",
                "rename_conflict=new_name_unique",
                "rename_target_conflict=no_conflict",
                "schema_privilege=has_create_privilege",
            ),
            strategy="full Cartesian source(3) x new-name(3) x default(2) x legal actor(2)",
            description=f"RENAME {source}/{new_name}/{default_status}/{actor}",
            expected_anchor="SQLSTATE 00000; only conname changes and all identity metadata remains stable",
        )

    for source, owner_shape, default_status, actor in itertools.product(
        _SOURCES, _NAMED_OWNERS, _DEFAULTS, _SUCCESS_ACTORS
    ):
        membership = actor == "conversion_owner"
        add(
            group="success_owner_product",
            case_type="syntax_semantics",
            outcome="success",
            axes={
                "branch": "owner",
                "source_name_shape": source,
                "owner_shape": owner_shape,
                "owner_target": "existing_role",
                "default_status": default_status,
                "actor": actor,
                "expected_sqlstate": "00000",
            },
            factors=_tokens(
                *_base_tokens("owner", outcome="success", actor=actor, source=source, default_status=default_status),
                f"new_owner_shape={owner_shape}",
                "new_owner_target=existing_role",
                "owner_not_exist=role_exists",
                "owner_membership=can_set_role" if membership else None,
                "cannot_set_role_to_new_owner=can_set_role" if membership else None,
                "schema_privilege=has_create_privilege",
                "no_create_privilege_on_target_schema=has_create_privilege",
            ),
            strategy="full Cartesian source(3) x named-owner lexical shape(2) x default(2) x legal actor(2)",
            description=f"OWNER named {source}/{owner_shape}/{default_status}/{actor}",
            expected_anchor="SQLSTATE 00000; only conowner and the owner dependency change",
        )

    for source, token, default_status in itertools.product(
        _SOURCES, _OWNER_TOKENS, _DEFAULTS
    ):
        add(
            group="success_owner_product",
            case_type="syntax_semantics",
            outcome="success",
            axes={
                "branch": "owner",
                "source_name_shape": source,
                "owner_shape": token,
                "owner_target": token,
                "default_status": default_status,
                "actor": "superuser",
                "expected_sqlstate": "00000",
            },
            factors=_tokens(
                *_base_tokens("owner", outcome="success", actor="superuser", source=source, default_status=default_status),
                "new_owner_shape=special_token",
                f"new_owner_target={token}",
                "owner_not_exist=role_exists",
            ),
            strategy="full Cartesian source(3) x RoleSpec token(3) x default(2)",
            description=f"OWNER RoleSpec {source}/{token}/{default_status}",
            expected_anchor="SQLSTATE 00000 and exact RoleSpec owner with stable conversion identity",
        )

    for source, target_shape, default_status, actor in itertools.product(
        _SOURCES, _TARGET_SCHEMAS, _DEFAULTS, _SUCCESS_ACTORS
    ):
        add(
            group="success_set_schema_product",
            case_type="syntax_semantics",
            outcome="success",
            axes={
                "branch": "set_schema",
                "source_name_shape": source,
                "target_schema_shape": target_shape,
                "default_status": default_status,
                "actor": actor,
                "expected_sqlstate": "00000",
            },
            factors=_tokens(
                *_base_tokens("set_schema", outcome="success", actor=actor, source=source, default_status=default_status),
                "new_schema_shape=simple_id" if target_shape == "simple_id" else None,
                "schema_conflict=target_schema_exists_no_conflict",
                "schema_not_exist=schema_exists",
                "schema_name_conflict=no_conflict",
                "schema_privilege=has_create_privilege",
                "no_create_privilege_on_target_schema=has_create_privilege",
            ),
            strategy="full Cartesian source(3) x target schema lexical shape(2) x default(2) x legal actor(2)",
            description=f"SET SCHEMA {source}/{target_shape}/{default_status}/{actor}",
            expected_anchor="SQLSTATE 00000; only connamespace and its dependency change",
        )

    # Isolated state failures: 30 plus one source-level DEFAULT behavior.
    for branch in _BRANCHES:
        add(
            group="missing_conversion_product",
            case_type="negative",
            outcome="expected_failure",
            axes={"branch": branch, "source_name_shape": "nonexistent_name", "actor": "superuser", "expected_sqlstate": "42704"},
            factors=_tokens(
                _branch_token(branch), "object_state=not_exists", "conversion_not_exist=conversion_not_exists",
                "conversion_name_shape=nonexistent_name", "expected_status=failure", "privilege_level=superuser",
            ),
            strategy="all three branches with a missing conversion and otherwise-valid target",
            description=f"Reject missing conversion in {branch}",
            expected_anchor="SQLSTATE 42704 and the missing conversion remains absent",
        )

    for source, new_name in itertools.product(_SOURCES, _NEW_NAMES):
        add(
            group="rename_conflict_product", case_type="negative", outcome="expected_failure",
            axes={"branch": "rename", "source_name_shape": source, "new_name_shape": new_name, "actor": "superuser", "expected_sqlstate": "42710"},
            factors=_tokens(
                *_base_tokens("rename", outcome="expected_failure", actor="superuser", source=source),
                f"new_name_shape={new_name}", "rename_conflict=new_name_exists_in_schema",
                "rename_target_conflict=name_already_exists", "schema_privilege=has_create_privilege",
            ),
            strategy="full Cartesian source(3) x conflicting new-name lexical shape(3)",
            description=f"Reject RENAME conflict {source}/{new_name}",
            expected_anchor="SQLSTATE 42710 and both conversion identities remain unchanged",
        )

    for source, owner_shape in itertools.product(_SOURCES, _NAMED_OWNERS):
        add(
            group="owner_missing_role_product", case_type="negative", outcome="expected_failure",
            axes={"branch": "owner", "source_name_shape": source, "owner_shape": owner_shape, "owner_target": "nonexistent_role", "actor": "superuser", "expected_sqlstate": "42704"},
            factors=_tokens(
                *_base_tokens("owner", outcome="expected_failure", actor="superuser", source=source),
                f"new_owner_shape={owner_shape}", "new_owner_target=nonexistent_role", "owner_not_exist=role_not_exists",
            ),
            strategy="full Cartesian source(3) x absent owner lexical shape(2)",
            description=f"Reject missing OWNER target {source}/{owner_shape}",
            expected_anchor="SQLSTATE 42704 and all conversion metadata remains unchanged",
        )

    for source, target_shape in itertools.product(_SOURCES, _TARGET_SCHEMAS):
        add(
            group="set_schema_missing_product", case_type="negative", outcome="expected_failure",
            axes={"branch": "set_schema", "source_name_shape": source, "target_schema_shape": target_shape, "actor": "superuser", "expected_sqlstate": "3F000"},
            factors=_tokens(
                *_base_tokens("set_schema", outcome="expected_failure", actor="superuser", source=source),
                "new_schema_shape=nonexistent_schema_name" if target_shape == "simple_id" else None,
                "schema_conflict=target_schema_not_exists", "schema_not_exist=schema_not_exists",
            ),
            strategy="full Cartesian source(3) x absent target-schema lexical shape(2)",
            description=f"Reject missing target schema {source}/{target_shape}",
            expected_anchor="SQLSTATE 3F000 and source metadata remains unchanged",
        )
        add(
            group="set_schema_conflict_product", case_type="negative", outcome="expected_failure",
            axes={"branch": "set_schema", "source_name_shape": source, "target_schema_shape": target_shape, "actor": "superuser", "expected_sqlstate": "42710"},
            factors=_tokens(
                *_base_tokens("set_schema", outcome="expected_failure", actor="superuser", source=source),
                "new_schema_shape=simple_id" if target_shape == "simple_id" else None,
                "schema_conflict=target_schema_exists_with_conflict", "schema_not_exist=schema_exists",
                "schema_name_conflict=same_name_in_target_schema", "schema_privilege=has_create_privilege",
            ),
            strategy="full Cartesian source(3) x conflicting target-schema lexical shape(2)",
            description=f"Reject target-schema name conflict {source}/{target_shape}",
            expected_anchor="SQLSTATE 42710 and source/target conversion identities remain unchanged",
        )

    add(
        group="default_pair_move_product", case_type="compatibility", outcome="success",
        axes={"branch": "set_schema", "source_name_shape": "schema_qualified", "target_schema_shape": "simple_id", "default_status": "is_default_conversion", "actor": "superuser", "expected_sqlstate": "00000"},
        factors=_tokens(
            *_base_tokens("set_schema", outcome="success", actor="superuser", source="schema_qualified", default_status="is_default_conversion"),
            "new_schema_shape=simple_id", "schema_conflict=target_schema_exists_no_conflict",
            "schema_not_exist=schema_exists", "schema_name_conflict=no_conflict", "schema_privilege=has_create_privilege",
        ),
        strategy="source-derived compatibility boundary for two differently named DEFAULT conversions",
        description="Move a DEFAULT conversion beside a different-name DEFAULT for the same encoding pair",
        expected_anchor="SQLSTATE 00000 and exactly two DEFAULT entries for the encoding pair",
    )

    # Permission truth tables: 30.
    for actor, schema_create in itertools.product(_ACTORS, ("yes", "no")):
        success = actor == "superuser" or (actor == "conversion_owner" and schema_create == "yes")
        outcome = "success" if success else "expected_failure"
        add(
            group="rename_privilege_truth_product", case_type="privilege", outcome=outcome,
            axes={"branch": "rename", "source_name_shape": "schema_qualified", "new_name_shape": "simple_id", "actor": actor, "schema_create": schema_create, "expected_sqlstate": "00000" if success else "42501"},
            factors=_tokens(
                *_base_tokens("rename", outcome=outcome, actor=actor, source="schema_qualified"),
                "new_name_shape=simple_id", "rename_conflict=new_name_unique", "rename_target_conflict=no_conflict",
                f"schema_privilege={'has_create_privilege' if schema_create == 'yes' else 'lacks_create_privilege'}",
            ),
            strategy="full Cartesian actor(3) x current-schema CREATE state(2)",
            description=f"RENAME privilege ordering {actor}/{schema_create}",
            expected_anchor=f"SQLSTATE {'00000' if success else '42501'} with exact owner-before-CREATE behavior",
        )

    for actor, can_set_role, new_owner_create in itertools.product(_ACTORS, ("yes", "no"), ("yes", "no")):
        success = actor == "superuser" or (actor == "conversion_owner" and can_set_role == "yes" and new_owner_create == "yes")
        outcome = "success" if success else "expected_failure"
        membership_tokens = actor == "conversion_owner"
        add(
            group="owner_privilege_truth_product", case_type="privilege", outcome=outcome,
            axes={"branch": "owner", "source_name_shape": "schema_qualified", "owner_shape": "simple_id", "owner_target": "existing_role", "actor": actor, "can_set_role": can_set_role, "new_owner_create": new_owner_create, "expected_sqlstate": "00000" if success else "42501"},
            factors=_tokens(
                *_base_tokens("owner", outcome=outcome, actor=actor, source="schema_qualified"),
                "new_owner_shape=simple_id", "new_owner_target=existing_role", "owner_not_exist=role_exists",
                f"owner_membership={'can_set_role' if can_set_role == 'yes' else 'cannot_set_role'}" if membership_tokens else None,
                f"cannot_set_role_to_new_owner={'can_set_role' if can_set_role == 'yes' else 'cannot_set_role'}" if membership_tokens else None,
                f"schema_privilege={'has_create_privilege' if new_owner_create == 'yes' else 'lacks_create_privilege'}",
                f"no_create_privilege_on_target_schema={'has_create_privilege' if new_owner_create == 'yes' else 'lacks_create_privilege'}",
            ),
            strategy="full Cartesian actor(3) x SET option(2) x new-owner schema CREATE(2)",
            description=f"OWNER privilege ordering {actor}/{can_set_role}/{new_owner_create}",
            expected_anchor=f"SQLSTATE {'00000' if success else '42501'} with owner-SET-CREATE ordering",
        )

    for actor, schema_create, target_shape in itertools.product(_ACTORS, ("yes", "no"), _TARGET_SCHEMAS):
        success = actor == "superuser" or (actor == "conversion_owner" and schema_create == "yes")
        outcome = "success" if success else "expected_failure"
        add(
            group="set_schema_privilege_truth_product", case_type="privilege", outcome=outcome,
            axes={"branch": "set_schema", "source_name_shape": "schema_qualified", "target_schema_shape": target_shape, "actor": actor, "schema_create": schema_create, "expected_sqlstate": "00000" if success else "42501"},
            factors=_tokens(
                *_base_tokens("set_schema", outcome=outcome, actor=actor, source="schema_qualified"),
                "new_schema_shape=simple_id" if target_shape == "simple_id" else None,
                "schema_conflict=target_schema_exists_no_conflict", "schema_not_exist=schema_exists", "schema_name_conflict=no_conflict",
                f"schema_privilege={'has_create_privilege' if schema_create == 'yes' else 'lacks_create_privilege'}",
                f"no_create_privilege_on_target_schema={'has_create_privilege' if schema_create == 'yes' else 'lacks_create_privilege'}",
            ),
            strategy="full Cartesian actor(3) x target CREATE(2) x target-schema lexical shape(2)",
            description=f"SET SCHEMA privilege ordering {actor}/{schema_create}/{target_shape}",
            expected_anchor=f"SQLSTATE {'00000' if success else '42501'} with target-CREATE-before-owner behavior",
        )

    # Same-target/no-op source-order boundaries: 15.
    for actor, schema_create in itertools.product(_ACTORS, ("yes", "no")):
        duplicate_reached = actor == "superuser" or (actor == "conversion_owner" and schema_create == "yes")
        add(
            group="rename_same_name_product", case_type="source_boundary", outcome="expected_failure",
            axes={"branch": "rename", "source_name_shape": "schema_qualified", "new_name_shape": "same_name", "actor": actor, "schema_create": schema_create, "expected_sqlstate": "42710" if duplicate_reached else "42501"},
            factors=_tokens(
                *_base_tokens("rename", outcome="expected_failure", actor=actor, source="schema_qualified"),
                "rename_conflict=new_name_exists_in_schema" if duplicate_reached else None,
                "rename_target_conflict=name_already_exists" if duplicate_reached else None,
                f"schema_privilege={'has_create_privilege' if schema_create == 'yes' else 'lacks_create_privilege'}",
            ),
            strategy="full Cartesian actor(3) x current-schema CREATE(2) for rename-to-self ordering",
            description=f"RENAME TO same name {actor}/{schema_create}",
            expected_anchor=f"SQLSTATE {'42710' if duplicate_reached else '42501'} and unchanged identity",
        )

    for actor in _ACTORS:
        add(
            group="owner_same_owner_noop_product", case_type="source_boundary", outcome="success",
            axes={"branch": "owner", "source_name_shape": "schema_qualified", "owner_shape": "same_owner", "owner_target": "existing_role", "actor": actor, "expected_sqlstate": "00000"},
            factors=_tokens(
                *_base_tokens("owner", outcome="success", actor=actor, source="schema_qualified"),
                "new_owner_shape=simple_id", "new_owner_target=existing_role", "owner_not_exist=role_exists",
            ),
            strategy="all three actors for the same-owner early return",
            description=f"OWNER TO current owner no-op as {actor}",
            expected_anchor="SQLSTATE 00000 even for non-owner; owner and dependencies remain unchanged",
        )

    for actor, schema_create in itertools.product(_ACTORS, ("yes", "no")):
        success = actor == "superuser" or schema_create == "yes"
        outcome = "success" if success else "expected_failure"
        add(
            group="set_schema_same_schema_product", case_type="source_boundary", outcome=outcome,
            axes={"branch": "set_schema", "source_name_shape": "schema_qualified", "target_schema_shape": "same_schema", "actor": actor, "schema_create": schema_create, "expected_sqlstate": "00000" if success else "42501"},
            factors=_tokens(
                *_base_tokens("set_schema", outcome=outcome, actor=actor, source="schema_qualified"),
                "new_schema_shape=simple_id", "schema_conflict=target_schema_exists_no_conflict", "schema_not_exist=schema_exists",
                "schema_name_conflict=no_conflict", f"schema_privilege={'has_create_privilege' if schema_create == 'yes' else 'lacks_create_privilege'}",
                f"no_create_privilege_on_target_schema={'has_create_privilege' if schema_create == 'yes' else 'lacks_create_privilege'}",
            ),
            strategy="full Cartesian actor(3) x current-schema CREATE(2) for same-schema early return",
            description=f"SET SCHEMA current schema {actor}/{schema_create}",
            expected_anchor=f"SQLSTATE {'00000' if success else '42501'} with CREATE check before owner bypass",
        )

    # Lookup and parser boundaries: 25.
    source_boundaries = (
        ("same_database_three_part", "success", "00000"),
        ("cross_database_three_part", "expected_failure", "0A000"),
        ("four_part_source", "expected_failure", "42601"),
        ("missing_source_schema", "expected_failure", "3F000"),
        ("source_schema_no_usage", "expected_failure", "42501"),
    )
    for stem, outcome, sqlstate in source_boundaries:
        for branch in _BRANCHES:
            add(
                group="lookup_parser_boundary_product", case_type="lookup_parser", outcome=outcome,
                axes={"branch": branch, "source_name_shape": "schema_qualified", "boundary": f"{stem}_{branch}", "actor": "superuser" if stem != "source_schema_no_usage" else "conversion_owner", "expected_sqlstate": sqlstate},
                factors=_tokens(
                    _branch_token(branch), "object_state=exists" if stem not in {"missing_source_schema"} else "object_state=not_exists",
                    "conversion_not_exist=conversion_exists" if stem not in {"missing_source_schema"} else "conversion_not_exist=conversion_not_exists",
                    f"expected_status={'success' if outcome == 'success' else 'failure'}",
                    "conversion_name_shape=schema_qualified",
                ),
                strategy="five source lookup states x all three official branches",
                description=f"Source lookup boundary {stem}/{branch}",
                expected_anchor=f"SQLSTATE {sqlstate} with a branch-valid target",
            )

    invalid_targets = (
        ("qualified_rename_target", "rename", "42601"),
        ("unquoted_reserved_rename_target", "rename", "42601"),
        ("qualified_owner_target", "owner", "42601"),
        ("owner_public_target", "owner", "42704"),
        ("owner_none_target", "owner", "42939"),
        ("qualified_set_schema_target", "set_schema", "42601"),
        ("unquoted_reserved_set_schema_target", "set_schema", "42601"),
    )
    for boundary, branch, sqlstate in invalid_targets:
        add(
            group="lookup_parser_boundary_product", case_type="lookup_parser", outcome="expected_failure",
            axes={"branch": branch, "source_name_shape": "schema_qualified", "boundary": boundary, "actor": "superuser", "expected_sqlstate": sqlstate},
            factors=_tokens(*_base_tokens(branch, outcome="expected_failure", actor="superuser", source="schema_qualified")),
            strategy="each official target grammar boundary exactly once",
            description=f"Reject invalid target syntax {boundary}",
            expected_anchor=f"SQLSTATE {sqlstate} and unchanged source conversion",
        )

    for boundary in ("search_path_first_match", "search_path_later_match"):
        add(
            group="lookup_parser_boundary_product", case_type="lookup", outcome="success",
            axes={"branch": "rename", "source_name_shape": "simple_id", "boundary": boundary, "actor": "superuser", "expected_sqlstate": "00000"},
            factors=_tokens(*_base_tokens("rename", outcome="success", actor="superuser", source="simple_id"), "new_name_shape=simple_id", "rename_conflict=new_name_unique", "rename_target_conflict=no_conflict"),
            strategy="two deterministic search_path resolution positions",
            description=f"Resolve unqualified conversion through {boundary}",
            expected_anchor="SQLSTATE 00000 and only the selected schema object changes",
        )

    add(
        group="lookup_parser_boundary_product", case_type="lookup", outcome="expected_failure",
        axes={"branch": "rename", "source_name_shape": "simple_id", "boundary": "temp_unqualified_lookup", "actor": "superuser", "expected_sqlstate": "42704"},
        factors=_tokens(_branch_token("rename"), "object_state=not_exists", "conversion_not_exist=conversion_not_exists", "expected_status=failure", "conversion_name_shape=nonexistent_name", "privilege_level=superuser"),
        strategy="source-derived temporary-schema search-path exclusion",
        description="Reject unqualified lookup when the only conversion is in pg_temp",
        expected_anchor="SQLSTATE 42704 because get_conversion_oid skips myTempNamespace",
    )

    # Protected/system namespaces: 10.
    protected = (
        ("pg_temp_move_into", "set_schema", "expected_failure", "0A000"),
        ("pg_temp_move_out", "set_schema", "expected_failure", "0A000"),
        ("pg_toast_move_into", "set_schema", "expected_failure", "0A000"),
        ("pg_toast_move_out", "set_schema", "expected_failure", "0A000"),
        ("pg_temp_same_schema_noop", "set_schema", "success", "00000"),
        ("pg_toast_same_schema_noop", "set_schema", "success", "00000"),
        ("pg_catalog_move_into_success", "set_schema", "success", "00000"),
        ("pg_catalog_move_out_success", "set_schema", "success", "00000"),
        ("pg_catalog_rename_success", "rename", "success", "00000"),
        ("pg_catalog_owner_create_denied", "owner", "expected_failure", "42501"),
    )
    for boundary, branch, outcome, sqlstate in protected:
        add(
            group="protected_namespace_product", case_type="namespace", outcome=outcome,
            axes={"branch": branch, "source_name_shape": "schema_qualified", "boundary": boundary, "actor": "conversion_owner" if boundary == "pg_catalog_owner_create_denied" else "superuser", "expected_sqlstate": sqlstate},
            factors=_tokens(*_base_tokens(branch, outcome=outcome, actor="conversion_owner" if boundary == "pg_catalog_owner_create_denied" else "superuser", source="schema_qualified")),
            strategy="all temp/toast changed/no-op directions plus pg_catalog positive and privilege boundaries",
            description=f"Namespace boundary {boundary}",
            expected_anchor=f"SQLSTATE {sqlstate} and exact namespace/identity oracle",
        )

    for branch in _BRANCHES:
        add(
            group="transactional_rollback_product", case_type="transaction", outcome="success",
            axes={"branch": branch, "source_name_shape": "schema_qualified", "actor": "superuser", "expected_sqlstate": "00000"},
            factors=_tokens(*_base_tokens(branch, outcome="success", actor="superuser", source="schema_qualified", default_status="is_not_default_conversion")),
            strategy="all three official branches inside BEGIN followed by ROLLBACK",
            description=f"Rollback ALTER CONVERSION {branch}",
            expected_anchor="SQLSTATE 00000 inside the transaction and the complete pre-action snapshot after rollback",
        )

    if len(cases) != 216:
        raise RemainingStatementRegressError(
            f"ALTER CONVERSION strict design expected 216 cases, found {len(cases)}"
        )
    return tuple(cases)


def _ids(cases: tuple[StatementRegressCase, ...], predicate: Callable[[StatementRegressCase], bool]) -> tuple[str, ...]:
    return tuple(case.case_id for case in cases if predicate(case))


def _factor_decisions(entry: StatementCycleEntry, cases: tuple[StatementRegressCase, ...]) -> tuple[FactorValueDecision, ...]:
    failures = {
        ("cannot_set_role_to_new_owner", "cannot_set_role"),
        ("conversion_name_shape", "nonexistent_name"),
        ("conversion_not_exist", "conversion_not_exists"),
        ("expected_status", "failure"),
        ("new_owner_target", "nonexistent_role"),
        ("new_schema_shape", "nonexistent_schema_name"),
        ("no_create_privilege_on_target_schema", "lacks_create_privilege"),
        ("object_state", "not_exists"),
        ("owner_membership", "cannot_set_role"),
        ("owner_not_exist", "role_not_exists"),
        ("privilege_denied", "non_owner_failure"),
        ("privilege_level", "non_owner"),
        ("rename_conflict", "new_name_exists_in_schema"),
        ("rename_target_conflict", "name_already_exists"),
        ("schema_conflict", "target_schema_exists_with_conflict"),
        ("schema_conflict", "target_schema_not_exists"),
        ("schema_name_conflict", "same_name_in_target_schema"),
        ("schema_not_exist", "schema_not_exists"),
        ("schema_privilege", "lacks_create_privilege"),
    }
    decisions: list[FactorValueDecision] = []
    for factor in entry.factors:
        for value, row_id in zip(factor.values, factor.row_ids):
            token = f"{factor.name}={value}"
            failure = (factor.name, value) in failures
            witnesses = _ids(
                cases,
                lambda case, token=token, failure=failure: token in case.factor_values
                and (not failure or case.outcome == "expected_failure"),
            )
            if not witnesses:
                raise RemainingStatementRegressError(
                    f"ALTER CONVERSION has no real witness for {token}"
                )
            decisions.append(
                FactorValueDecision(
                    row_id=row_id,
                    factor=factor.name,
                    value=value,
                    disposition="expected_failure" if failure else "covered",
                    reason=(
                        "The canonical value is isolated in an expected-failure SQL program with an exact SQLSTATE and unchanged catalog snapshot."
                        if failure
                        else None
                    ),
                    case_ids=witnesses,
                )
            )
    return tuple(decisions)


def build_alter_conversion_plan(
    snapshot: StatementFactorCycleSnapshot,
    entry: StatementCycleEntry,
) -> StatementRegressPlan:
    cases = _build_cases()
    if tuple(case.ordinal for case in cases) != tuple(range(1, 217)):
        raise RemainingStatementRegressError("ALTER CONVERSION ordinals are not contiguous")
    return StatementRegressPlan(
        statement_key="alter_conversion",
        file_prefix="ALTERCONVERSION",
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
    source_schema_raw = f"{prefix}src"
    target_schema_raw = (
        f"{prefix}Target Schema"
        if case.derived_axes.get("target_schema_shape") == "quoted_id"
        else f"{prefix}dst"
    )
    shadow_schema_raw = f"{prefix}shadow"
    source_shape = case.derived_axes.get("source_name_shape", "schema_qualified")
    conversion_raw = (
        f"{prefix}Conversion Name" if source_shape == "quoted_id" else f"{prefix}conv"
    )
    conversion_ident = _quote_ident(conversion_raw)
    source_schema = _quote_ident(source_schema_raw)
    target_schema = _quote_ident(target_schema_raw)
    shadow_schema = _quote_ident(shadow_schema_raw)
    source_qualified = f"{source_schema}.{conversion_ident}"
    if source_shape == "simple_id":
        target_ref = conversion_ident
    elif source_shape == "quoted_id":
        target_ref = conversion_ident
    else:
        target_ref = source_qualified
    new_shape = case.derived_axes.get("new_name_shape", "simple_id")
    if new_shape == "quoted_id":
        new_raw = f"{prefix}Renamed Conversion"
    elif new_shape == "reserved_word_as_name":
        new_raw = "select"
    elif new_shape == "same_name":
        new_raw = conversion_raw
    else:
        new_raw = f"{prefix}renamed"
    owner_shape = case.derived_axes.get("owner_shape", "simple_id")
    new_owner_raw = (
        f"{prefix}New Owner" if owner_shape == "quoted_id" else f"{prefix}new_owner"
    )
    new_owner_ident = (
        _quote_ident(new_owner_raw) if owner_shape == "quoted_id" else new_owner_raw
    )
    return {
        "prefix": prefix,
        "source_schema_raw": source_schema_raw,
        "source_schema": source_schema,
        "target_schema_raw": target_schema_raw,
        "target_schema": target_schema,
        "shadow_schema_raw": shadow_schema_raw,
        "shadow_schema": shadow_schema,
        "conversion_raw": conversion_raw,
        "conversion_ident": conversion_ident,
        "source_qualified": source_qualified,
        "target_ref": target_ref,
        "new_raw": new_raw,
        "new_ident": _quote_ident(new_raw),
        "new_qualified": f"{source_schema}.{_quote_ident(new_raw)}",
        "moved_qualified": f"{target_schema}.{conversion_ident}",
        "shadow_qualified": f"{shadow_schema}.{conversion_ident}",
        "old_owner": f"{prefix}old_owner",
        "new_owner_raw": new_owner_raw,
        "new_owner": new_owner_ident,
        "intruder": f"{prefix}intruder",
        "missing_owner": f"{prefix}missing_owner",
        "missing_schema": _quote_ident(f"{prefix}missing_schema"),
        "conflict_conversion": f"{target_schema}.{conversion_ident}",
        "default_pair": f"{target_schema}.{_quote_ident(prefix + 'other_default')}",
        "foreign_database": f"{prefix}otherdb",
    }


def _create_conversion(reference: str, *, is_default: bool) -> str:
    default = "DEFAULT " if is_default else ""
    return (
        f"CREATE {default}CONVERSION {reference} FOR 'UTF8' TO 'LATIN1' "
        "FROM pg_catalog.utf8_to_iso8859_1;"
    )


def _roles_cleanup(names: Mapping[str, str]) -> list[str]:
    return [
        f"DROP ROLE IF EXISTS {names['intruder']};",
        f"DROP ROLE IF EXISTS {names['old_owner']};",
        f"DROP ROLE IF EXISTS {names['new_owner']};",
    ]


def _precleanup(names: Mapping[str, str]) -> list[str]:
    return [
        "RESET ROLE;",
        "RESET SESSION AUTHORIZATION;",
        "RESET search_path;",
        f"DROP CONVERSION IF EXISTS pg_catalog.{names['conversion_ident']} CASCADE;",
        f"DROP CONVERSION IF EXISTS pg_catalog.{names['new_ident']} CASCADE;",
        f"DROP CONVERSION IF EXISTS pg_toast.{names['conversion_ident']} CASCADE;",
        f"DROP SCHEMA IF EXISTS {names['target_schema']} CASCADE;",
        f"DROP SCHEMA IF EXISTS {names['shadow_schema']} CASCADE;",
        f"DROP SCHEMA IF EXISTS {names['source_schema']} CASCADE;",
        *_roles_cleanup(names),
    ]


def _actor_sql(actor: str, names: Mapping[str, str]) -> str | None:
    if actor == "conversion_owner":
        return f"SET ROLE {names['old_owner']};"
    if actor == "non_owner":
        return f"SET ROLE {names['intruder']};"
    return None


def _source_namespace(case: StatementRegressCase, names: Mapping[str, str]) -> tuple[str, str]:
    boundary = case.derived_axes.get("boundary", "")
    if boundary in {"pg_temp_move_out", "pg_temp_same_schema_noop"}:
        return "pg_temp", f"pg_temp.{names['conversion_ident']}"
    if boundary in {"pg_toast_move_out", "pg_toast_same_schema_noop"}:
        return "pg_toast", f"pg_toast.{names['conversion_ident']}"
    if boundary in {
        "pg_catalog_move_out_success",
        "pg_catalog_rename_success",
        "pg_catalog_owner_create_denied",
    }:
        return "pg_catalog", f"pg_catalog.{names['conversion_ident']}"
    return names["source_schema_raw"], names["source_qualified"]


def _needs_source_conversion(case: StatementRegressCase) -> bool:
    if case.case_group == "missing_conversion_product":
        return False
    boundary = case.derived_axes.get("boundary", "")
    return not boundary.startswith("missing_source_schema_")


def _owned_fixture(case: StatementRegressCase) -> bool:
    return case.derived_axes.get("actor") in {"conversion_owner", "non_owner"} or case.case_group in {
        "owner_same_owner_noop_product",
    } or case.derived_axes.get("boundary") == "pg_catalog_owner_create_denied"


def _fixture(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    boundary = case.derived_axes.get("boundary", "")
    group = case.case_group
    lines = [
        f"CREATE ROLE {names['old_owner']};",
        f"CREATE ROLE {names['new_owner']};",
        f"CREATE ROLE {names['intruder']};",
    ]
    if not boundary.startswith("missing_source_schema_"):
        lines.append(f"CREATE SCHEMA {names['source_schema']};")
    if group not in {"set_schema_missing_product"} and not boundary.startswith(
        "missing_source_schema_"
    ):
        lines.append(f"CREATE SCHEMA {names['target_schema']};")
    if boundary in {"search_path_first_match", "search_path_later_match"}:
        lines.append(f"CREATE SCHEMA {names['shadow_schema']};")

    if not _needs_source_conversion(case):
        return lines

    is_default = case.derived_axes.get("default_status") == "is_default_conversion"
    namespace_raw, reference = _source_namespace(case, names)
    if boundary == "temp_unqualified_lookup":
        namespace_raw = "pg_temp"
        reference = f"pg_temp.{names['conversion_ident']}"
    owned = _owned_fixture(case)
    if owned:
        lines.extend(
            [
                f"GRANT USAGE, CREATE ON SCHEMA {_quote_ident(namespace_raw) if namespace_raw not in {'pg_temp', 'pg_catalog', 'pg_toast'} else namespace_raw} TO {names['old_owner']};",
                f"SET ROLE {names['old_owner']};",
                _create_conversion(reference, is_default=is_default),
                "RESET ROLE;",
            ]
        )
    else:
        lines.append(_create_conversion(reference, is_default=is_default))

    if boundary in {"search_path_first_match", "search_path_later_match"}:
        lines.append(_create_conversion(names["shadow_qualified"], is_default=False))
    if group == "rename_conflict_product":
        lines.append(_create_conversion(names["new_qualified"], is_default=False))
    if group == "set_schema_conflict_product":
        lines.append(_create_conversion(names["conflict_conversion"], is_default=False))
    if group == "default_pair_move_product":
        lines.append(_create_conversion(names["default_pair"], is_default=True))
    return lines


def _actor_grantee(actor: str, names: Mapping[str, str]) -> str:
    if actor == "superuser":
        return "SESSION_USER"
    if actor == "conversion_owner":
        return names["old_owner"]
    return names["intruder"]


def _privilege_fixture(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    actor = case.derived_axes.get("actor", "superuser")
    group = case.case_group
    boundary = case.derived_axes.get("boundary", "")
    lines: list[str] = []
    if not boundary.startswith("missing_source_schema_"):
        lines.extend(
            [
                f"GRANT USAGE ON SCHEMA {names['source_schema']} TO {names['old_owner']};",
                f"GRANT USAGE ON SCHEMA {names['source_schema']} TO {names['intruder']};",
            ]
        )
    if group in {"success_rename_product"} and actor == "conversion_owner":
        lines.append(
            f"GRANT CREATE ON SCHEMA {names['source_schema']} TO {names['old_owner']};"
        )
    if group in {"rename_privilege_truth_product", "rename_same_name_product"}:
        grantee = _actor_grantee(actor, names)
        if case.derived_axes["schema_create"] == "yes":
            lines.append(f"GRANT CREATE ON SCHEMA {names['source_schema']} TO {grantee};")
        else:
            lines.append(f"REVOKE CREATE ON SCHEMA {names['source_schema']} FROM {grantee};")

    if group == "success_owner_product" and case.derived_axes.get("owner_target") == "existing_role":
        lines.append(
            f"GRANT CREATE ON SCHEMA {names['source_schema']} TO {names['new_owner']};"
        )
        if actor == "conversion_owner":
            lines.append(
                f"GRANT {names['new_owner']} TO {names['old_owner']} WITH SET TRUE;"
            )
    if group == "owner_privilege_truth_product":
        grantee = _actor_grantee(actor, names)
        set_value = "TRUE" if case.derived_axes["can_set_role"] == "yes" else "FALSE"
        lines.append(f"GRANT {names['new_owner']} TO {grantee} WITH SET {set_value};")
        if case.derived_axes["new_owner_create"] == "yes":
            lines.append(
                f"GRANT CREATE ON SCHEMA {names['source_schema']} TO {names['new_owner']};"
            )
        else:
            lines.append(
                f"REVOKE CREATE ON SCHEMA {names['source_schema']} FROM {names['new_owner']};"
            )

    if group == "success_set_schema_product" and actor == "conversion_owner":
        lines.append(
            f"GRANT CREATE ON SCHEMA {names['target_schema']} TO {names['old_owner']};"
        )
    if group == "set_schema_privilege_truth_product":
        grantee = _actor_grantee(actor, names)
        if case.derived_axes["schema_create"] == "yes":
            lines.append(f"GRANT CREATE ON SCHEMA {names['target_schema']} TO {grantee};")
        else:
            lines.append(f"REVOKE CREATE ON SCHEMA {names['target_schema']} FROM {grantee};")
    if group == "set_schema_same_schema_product":
        grantee = _actor_grantee(actor, names)
        if case.derived_axes["schema_create"] == "yes":
            lines.append(f"GRANT CREATE ON SCHEMA {names['source_schema']} TO {grantee};")
        else:
            lines.append(f"REVOKE CREATE ON SCHEMA {names['source_schema']} FROM {grantee};")

    if boundary.startswith("source_schema_no_usage_"):
        grantee = _actor_grantee(actor, names)
        lines.append(f"REVOKE USAGE ON SCHEMA {names['source_schema']} FROM {grantee};")

    role = _actor_sql(actor, names)
    if role is not None:
        lines.append(role)
    if case.derived_axes.get("source_name_shape") in {"simple_id", "quoted_id"}:
        lines.append(f"SET search_path TO {names['source_schema']}, pg_catalog;")
    if boundary == "search_path_first_match":
        lines.append(
            f"SET search_path TO {names['source_schema']}, {names['shadow_schema']}, pg_catalog;"
        )
    elif boundary == "search_path_later_match":
        lines.append(
            f"SET search_path TO {names['shadow_schema']}, {names['source_schema']}, pg_catalog;"
        )
    return lines


def _branch_action(
    branch: str,
    reference: str,
    case: StatementRegressCase,
    names: Mapping[str, str],
) -> str:
    group = case.case_group
    if branch == "rename":
        new_name = (
            names["conversion_ident"]
            if group == "rename_same_name_product"
            else names["new_ident"]
        )
        return f"ALTER CONVERSION {reference} RENAME TO {new_name};"
    if branch == "owner":
        if group == "owner_same_owner_noop_product":
            owner = names["old_owner"]
        elif group == "owner_missing_role_product":
            owner = names["missing_owner"]
        else:
            owner_shape = case.derived_axes.get("owner_shape", "simple_id")
            owner = owner_shape if owner_shape in _OWNER_TOKENS else names["new_owner"]
        return f"ALTER CONVERSION {reference} OWNER TO {owner};"
    if group == "set_schema_missing_product":
        target = names["missing_schema"]
    elif group == "set_schema_same_schema_product":
        target = names["source_schema"]
    else:
        target = names["target_schema"]
    return f"ALTER CONVERSION {reference} SET SCHEMA {target};"


def _target_action(case: StatementRegressCase, names: Mapping[str, str]) -> str:
    branch = case.derived_axes["branch"]
    boundary = case.derived_axes.get("boundary", "")
    if boundary.startswith("same_database_three_part_"):
        reference = (
            f':"current_database_name".{names["source_schema"]}.{names["conversion_ident"]}'
        )
        return _branch_action(branch, reference, case, names)
    if boundary.startswith("cross_database_three_part_"):
        reference = (
            f'{_quote_ident(names["foreign_database"])}.{names["source_schema"]}.'
            f'{names["conversion_ident"]}'
        )
        return _branch_action(branch, reference, case, names)
    if boundary.startswith("four_part_source_"):
        reference = (
            f'{_quote_ident(names["foreign_database"])}.extra.{names["source_schema"]}.'
            f'{names["conversion_ident"]}'
        )
        return _branch_action(branch, reference, case, names)
    if boundary.startswith("missing_source_schema_"):
        reference = f"{names['missing_schema']}.{names['conversion_ident']}"
        return _branch_action(branch, reference, case, names)
    if boundary == "qualified_rename_target":
        return (
            f"ALTER CONVERSION {names['source_qualified']} RENAME TO "
            f"{names['target_schema']}.{names['new_ident']};"
        )
    if boundary == "unquoted_reserved_rename_target":
        return f"ALTER CONVERSION {names['source_qualified']} RENAME TO select;"
    if boundary == "qualified_owner_target":
        return (
            f"ALTER CONVERSION {names['source_qualified']} OWNER TO "
            f"{names['source_schema']}.{names['new_owner']};"
        )
    if boundary == "owner_public_target":
        return f"ALTER CONVERSION {names['source_qualified']} OWNER TO PUBLIC;"
    if boundary == "owner_none_target":
        return f"ALTER CONVERSION {names['source_qualified']} OWNER TO none;"
    if boundary == "qualified_set_schema_target":
        return (
            f"ALTER CONVERSION {names['source_qualified']} SET SCHEMA "
            f"{names['target_schema']}.extra;"
        )
    if boundary == "unquoted_reserved_set_schema_target":
        return f"ALTER CONVERSION {names['source_qualified']} SET SCHEMA select;"
    if boundary == "temp_unqualified_lookup":
        return _branch_action(branch, names["conversion_ident"], case, names)
    if boundary.startswith("pg_temp_move_into"):
        return f"ALTER CONVERSION {names['source_qualified']} SET SCHEMA pg_temp;"
    if boundary.startswith("pg_temp_move_out"):
        return f"ALTER CONVERSION pg_temp.{names['conversion_ident']} SET SCHEMA {names['target_schema']};"
    if boundary.startswith("pg_temp_same_schema"):
        return f"ALTER CONVERSION pg_temp.{names['conversion_ident']} SET SCHEMA pg_temp;"
    if boundary.startswith("pg_toast_move_into"):
        return f"ALTER CONVERSION {names['source_qualified']} SET SCHEMA pg_toast;"
    if boundary.startswith("pg_toast_move_out"):
        return f"ALTER CONVERSION pg_toast.{names['conversion_ident']} SET SCHEMA {names['target_schema']};"
    if boundary.startswith("pg_toast_same_schema"):
        return f"ALTER CONVERSION pg_toast.{names['conversion_ident']} SET SCHEMA pg_toast;"
    if boundary == "pg_catalog_move_into_success":
        return f"ALTER CONVERSION {names['source_qualified']} SET SCHEMA pg_catalog;"
    if boundary == "pg_catalog_move_out_success":
        return f"ALTER CONVERSION pg_catalog.{names['conversion_ident']} SET SCHEMA {names['target_schema']};"
    if boundary == "pg_catalog_rename_success":
        return f"ALTER CONVERSION pg_catalog.{names['conversion_ident']} RENAME TO {names['new_ident']};"
    if boundary == "pg_catalog_owner_create_denied":
        return f"ALTER CONVERSION pg_catalog.{names['conversion_ident']} OWNER TO {names['new_owner']};"
    return _branch_action(branch, names["target_ref"], case, names)


def _capture_location(
    case: StatementRegressCase,
    names: Mapping[str, str],
) -> tuple[str, str, bool]:
    boundary = case.derived_axes.get("boundary", "")
    if boundary == "search_path_later_match":
        return names["shadow_schema_raw"], names["conversion_raw"], False
    if boundary in {"pg_temp_move_out", "pg_temp_same_schema_noop", "temp_unqualified_lookup"}:
        return "pg_temp", names["conversion_raw"], True
    if boundary in {"pg_toast_move_out", "pg_toast_same_schema_noop"}:
        return "pg_toast", names["conversion_raw"], False
    if boundary in {
        "pg_catalog_move_out_success",
        "pg_catalog_rename_success",
        "pg_catalog_owner_create_denied",
    }:
        return "pg_catalog", names["conversion_raw"], False
    return names["source_schema_raw"], names["conversion_raw"], False


def _capture_identity(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    if not _needs_source_conversion(case):
        return []
    namespace, conversion, temporary = _capture_location(case, names)
    namespace_predicate = (
        "n.oid = pg_catalog.pg_my_temp_schema()"
        if temporary
        else f"n.nspname = {_literal(namespace)}"
    )
    return [
        "SELECT",
        "    c.oid::text AS before_conversion_oid,",
        "    c.conowner::text AS before_conversion_owner,",
        "    c.connamespace::text AS before_conversion_namespace,",
        "    c.conproc::text AS before_conversion_proc,",
        "    c.conforencoding::text AS before_conversion_for_encoding,",
        "    c.contoencoding::text AS before_conversion_to_encoding,",
        "    c.condefault::text AS before_conversion_default",
        "FROM pg_catalog.pg_conversion AS c",
        "JOIN pg_catalog.pg_namespace AS n ON n.oid = c.connamespace",
        f"WHERE {namespace_predicate}",
        f"  AND c.conname = {_literal(conversion)}",
        "ORDER BY c.oid",
        r"\gset",
    ]


def _final_location(
    case: StatementRegressCase,
    names: Mapping[str, str],
) -> tuple[str, str, bool]:
    original_namespace, original_name, original_temp = _capture_location(case, names)
    if case.outcome == "expected_failure" or case.case_group == "transactional_rollback_product":
        return original_namespace, original_name, original_temp
    boundary = case.derived_axes.get("boundary", "")
    branch = case.derived_axes["branch"]
    if branch == "rename":
        return original_namespace, names["new_raw"], original_temp
    if branch == "set_schema":
        if case.case_group == "set_schema_same_schema_product":
            return original_namespace, original_name, original_temp
        if boundary == "pg_temp_same_schema_noop":
            return "pg_temp", original_name, True
        if boundary == "pg_toast_same_schema_noop":
            return "pg_toast", original_name, False
        if boundary == "pg_catalog_move_into_success":
            return "pg_catalog", original_name, False
        return names["target_schema_raw"], original_name, False
    return original_namespace, original_name, original_temp


def _absence_oracle(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    boundary = case.derived_axes.get("boundary", "")
    namespace = (
        names["missing_schema"].strip('"')
        if boundary.startswith("missing_source_schema_")
        else names["source_schema_raw"]
    )
    return [
        "SELECT count(*) = 0 AS missing_conversion_remains_absent",
        "FROM pg_catalog.pg_conversion AS c",
        "JOIN pg_catalog.pg_namespace AS n ON n.oid = c.connamespace",
        f"WHERE n.nspname = {_literal(namespace)}",
        f"  AND c.conname = {_literal(names['conversion_raw'])}",
        "ORDER BY missing_conversion_remains_absent;",
    ]


def _identity_oracle(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    if not _needs_source_conversion(case):
        return _absence_oracle(case, names)
    namespace, conversion, temporary = _final_location(case, names)
    namespace_predicate = (
        "n.oid = pg_catalog.pg_my_temp_schema()"
        if temporary
        else f"n.nspname = {_literal(namespace)}"
    )
    snapshot = case.outcome == "expected_failure" or case.case_group == "transactional_rollback_product"
    lines = [
        "SELECT",
        "    count(*) = 1 AS conversion_identity_present,",
        "    COALESCE(bool_and(c.oid::text = :'before_conversion_oid'), false) AS conversion_oid_preserved,",
        "    COALESCE(bool_and(c.conproc::text = :'before_conversion_proc'), false) AS conversion_proc_preserved,",
        "    COALESCE(bool_and(c.conforencoding::text = :'before_conversion_for_encoding'), false) AS conversion_for_encoding_preserved,",
        "    COALESCE(bool_and(c.contoencoding::text = :'before_conversion_to_encoding'), false) AS conversion_to_encoding_preserved,",
        "    COALESCE(bool_and(c.condefault::text = :'before_conversion_default'), false) AS condefault_preserved,",
        "    COALESCE(bool_and(c.oid::text = :'before_conversion_oid'",
        "        AND c.conproc::text = :'before_conversion_proc'",
        "        AND c.conforencoding::text = :'before_conversion_for_encoding'",
        "        AND c.contoencoding::text = :'before_conversion_to_encoding'",
        "        AND c.condefault::text = :'before_conversion_default'), false) AS conversion_snapshot_preserved",
        "FROM pg_catalog.pg_conversion AS c",
        "JOIN pg_catalog.pg_namespace AS n ON n.oid = c.connamespace",
        f"WHERE {namespace_predicate}",
        f"  AND c.conname = {_literal(conversion)}",
        "ORDER BY conversion_identity_present, conversion_oid_preserved, conversion_proc_preserved, conversion_for_encoding_preserved, conversion_to_encoding_preserved, condefault_preserved, conversion_snapshot_preserved;",
    ]
    if case.derived_axes["branch"] == "owner" and case.outcome == "success":
        if case.case_group in {"owner_same_owner_noop_product", "transactional_rollback_product"}:
            expected = ":'before_conversion_owner'"
        elif case.derived_axes.get("owner_shape") in _OWNER_TOKENS:
            expected = "(SELECT oid::text FROM pg_catalog.pg_roles WHERE rolname = SESSION_USER)"
        else:
            expected = f"(SELECT oid::text FROM pg_catalog.pg_roles WHERE rolname = {_literal(names['new_owner_raw'])})"
        lines.extend(
            [
                "SELECT c.conowner::text = " + expected + " AS conversion_owner_matches",
                "FROM pg_catalog.pg_conversion AS c",
                "JOIN pg_catalog.pg_namespace AS n ON n.oid = c.connamespace",
                f"WHERE {namespace_predicate}",
                f"  AND c.conname = {_literal(conversion)}",
                "ORDER BY conversion_owner_matches;",
            ]
        )
    if case.case_group == "owner_same_owner_noop_product":
        lines.append("SELECT true AS same_owner_noop_preserved;")
    if case.case_group == "set_schema_same_schema_product" and case.outcome == "success":
        lines.append("SELECT true AS same_schema_noop_preserved;")
    if snapshot:
        lines.extend(
            [
                "SELECT count(*) = 1 AS conversion_owner_and_namespace_preserved",
                "FROM pg_catalog.pg_conversion AS c",
                f"WHERE c.oid::text = :'before_conversion_oid'",
                "  AND c.conowner::text = :'before_conversion_owner'",
                "  AND c.connamespace::text = :'before_conversion_namespace'",
                "ORDER BY conversion_owner_and_namespace_preserved;",
            ]
        )
    return lines


def _dependency_oracle(case: StatementRegressCase) -> list[str]:
    if not _needs_source_conversion(case):
        return ["SELECT true AS no_conversion_dependency_expected;"]
    return [
        "SELECT count(*) > 0 AS conversion_function_dependency_present",
        "FROM pg_catalog.pg_depend AS d",
        "WHERE d.classid = 'pg_catalog.pg_conversion'::pg_catalog.regclass",
        "  AND d.objid::text = :'before_conversion_oid'",
        "  AND d.refclassid = 'pg_catalog.pg_proc'::pg_catalog.regclass",
        "  AND d.refobjid::text = :'before_conversion_proc'",
        "ORDER BY conversion_function_dependency_present;",
        "SELECT count(*) > 0 AS conversion_owner_dependency_present",
        "FROM pg_catalog.pg_shdepend AS d",
        "WHERE d.classid = 'pg_catalog.pg_conversion'::pg_catalog.regclass",
        "  AND d.objid::text = :'before_conversion_oid'",
        "ORDER BY conversion_owner_dependency_present;",
    ]


def _default_pair_oracle(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    if case.case_group != "default_pair_move_product":
        return []
    return [
        "SELECT count(*) = 2 AND bool_and(c.condefault) AS default_pair_count_is_two",
        "FROM pg_catalog.pg_conversion AS c",
        "JOIN pg_catalog.pg_namespace AS n ON n.oid = c.connamespace",
        f"WHERE n.nspname = {_literal(names['target_schema_raw'])}",
        "  AND c.conforencoding = pg_catalog.pg_char_to_encoding('UTF8')",
        "  AND c.contoencoding = pg_catalog.pg_char_to_encoding('LATIN1')",
        "ORDER BY default_pair_count_is_two;",
    ]


def _cleanup(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    boundary = case.derived_axes.get("boundary", "")
    lines = ["RESET ROLE;", "RESET SESSION AUTHORIZATION;", "RESET search_path;"]
    if boundary in {"pg_temp_move_out", "pg_temp_same_schema_noop", "temp_unqualified_lookup"}:
        lines.append(
            f"DROP CONVERSION IF EXISTS pg_temp.{names['conversion_ident']} CASCADE;"
        )
    if boundary in {"pg_toast_move_out", "pg_toast_same_schema_noop"}:
        lines.append(
            f"DROP CONVERSION IF EXISTS pg_toast.{names['conversion_ident']} CASCADE;"
        )
    if boundary.startswith("pg_catalog_"):
        lines.extend(
            [
                f"DROP CONVERSION IF EXISTS pg_catalog.{names['new_ident']} CASCADE;",
                f"DROP CONVERSION IF EXISTS pg_catalog.{names['conversion_ident']} CASCADE;",
            ]
        )
    lines.extend(
        [
            f"DROP CONVERSION IF EXISTS {names['new_qualified']} CASCADE;",
            f"DROP CONVERSION IF EXISTS {names['moved_qualified']} CASCADE;",
            f"DROP CONVERSION IF EXISTS {names['shadow_qualified']} CASCADE;",
            f"DROP CONVERSION IF EXISTS {names['source_qualified']} CASCADE;",
            f"DROP SCHEMA IF EXISTS {names['target_schema']} CASCADE;",
            f"DROP SCHEMA IF EXISTS {names['shadow_schema']} CASCADE;",
            f"DROP SCHEMA IF EXISTS {names['source_schema']} CASCADE;",
            *_roles_cleanup(names),
            "RESET ALL;",
            "SELECT true AS cleanup_complete;",
        ]
    )
    return lines


def render_alter_conversion_case(
    plan: StatementRegressPlan,
    case: StatementRegressCase,
) -> str:
    """Render one reviewed ALTER CONVERSION conditional-product cell."""

    if plan.statement_key != "alter_conversion" or case not in plan.cases:
        raise RemainingStatementRegressError(
            "ALTER CONVERSION renderer received a foreign plan or case"
        )
    names = _names(case)
    lines = _header(plan, case) + [
        "",
        "-- 1. 清理本编号 conversion、schema 和角色，建立幂等单会话环境。",
        *_precleanup(names),
        "",
        "-- 2. 创建 UTF8→LATIN1 conversion、目标 namespace 与精确权限状态。",
        *_fixture(case, names),
        *_privilege_fixture(case, names),
    ]
    if _needs_source_conversion(case):
        lines.extend(_capture_identity(case, names))
    if case.derived_axes.get("boundary", "").startswith("same_database_three_part_"):
        lines.extend(["SELECT current_database() AS current_database_name", r"\gset"])
    action = _target_action(case, names)
    lines.extend(
        [
            "",
            "-- 3. 执行唯一目标 ALTER CONVERSION 并捕获该目标语句 SQLSTATE。",
            "SET client_min_messages TO warning;",
        ]
    )
    if case.case_group == "transactional_rollback_product":
        lines.extend(["BEGIN;", action, r"\set target_sqlstate :SQLSTATE", "ROLLBACK;"])
    elif case.outcome == "expected_failure":
        lines.extend(
            [
                r"\set ON_ERROR_STOP off",
                action,
                r"\set target_sqlstate :SQLSTATE",
                r"\set ON_ERROR_STOP on",
            ]
        )
    else:
        lines.extend([action, r"\set target_sqlstate :SQLSTATE"])
    lines.extend(
        [
            f"SELECT :'target_sqlstate' = '{case.derived_axes['expected_sqlstate']}' AS expected_SQLSTATE;",
            "",
            "-- 4. 从 pg_conversion 重建 identity、owner、namespace、encoding、proc 与 DEFAULT 不变量。",
            "RESET ROLE;",
            *_identity_oracle(case, names),
            "",
            "-- 5. 验证 DEFAULT 同编码对边界和失败/回滚后的完整快照。",
            *_default_pair_oracle(case, names),
            "SELECT true AS conversion_catalog_oracle_complete;",
            "",
            "-- 6. 验证 conversion 对函数与 owner 的目录依赖仍然闭合。",
            *_dependency_oracle(case),
            "",
            "-- 7. 按声明清理 conversion、schema、membership 和角色并确认完成。",
            *_cleanup(case, names),
        ]
    )
    return "\n".join(lines).rstrip() + "\n"
