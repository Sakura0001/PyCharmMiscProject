"""PostgreSQL 18 ALTER COLLATION exhaustive regress plan and renderer.

The canonical matrix is dependency-heavy: action-specific target values are
not independent of the four official grammar branches.  This module records
the legal conditional products explicitly and emits one self-contained,
single-session SQL program for every cell.
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
from .statement_factor_cycle import (
    StatementCycleEntry,
    StatementFactorCycleSnapshot,
)


_SOURCE_SHAPES = ("plain_identifier", "quoted_identifier", "schema_qualified")
_DEPENDENCIES = ("no_dependencies", "table_column", "expression_index")
_NEW_NAME_SHAPES = ("plain_identifier", "quoted_identifier")
_OWNER_SHAPES = ("CURRENT_ROLE", "CURRENT_USER", "SESSION_USER", "plain_role")
_SCHEMA_SHAPES = ("plain_identifier", "quoted_identifier")
_ACTORS = ("superuser", "collation_owner", "non_owner")
_BRANCHES = ("refresh_version", "rename", "owner", "set_schema")


def _tokens(*values: str | None) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


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
    execution_profile: str = "same_session_multiphase",
) -> StatementRegressCase:
    number = f"{ordinal:05d}"
    return StatementRegressCase(
        ordinal=ordinal,
        case_id=f"ALTERCOLLATION{number}",
        sql_filename=f"ALTERCOLLATION{number}.sql",
        object_prefix=f"altercollation_{number}_",
        case_group=group,
        case_type=case_type,
        outcome=outcome,
        execution_profile=execution_profile,
        derived_axes=dict(axes),
        factor_values=factor_values,
        combination_strategy=strategy,
        description=description,
        expected_anchor=expected_anchor,
    )


def _branch_token(branch: str) -> str:
    return f"statement_branch=branch_{branch}"


def _dependency_tokens(dependency: str) -> tuple[str, ...]:
    usage = {
        "no_dependencies": "no_dependencies",
        "table_column": "referenced_by_table_column",
        "expression_index": "referenced_by_index",
    }[dependency]
    return _tokens(
        f"collation_usage_state={usage}",
        "referenced_objects=table_column_with_collate"
        if dependency == "table_column"
        else None,
        "referenced_objects=index_using_collation"
        if dependency == "expression_index"
        else None,
    )


def _evidence_tokens(ordinal: int) -> tuple[str, str]:
    verification = (
        "pg_collation_catalog_query",
        "pg_collation_actual_version_query",
        "collation_sort_verification",
    )[(ordinal - 1) % 3]
    cleanup = (
        "DROP_COLLATION_CASCADE",
        "DROP_DEPENDENT_OBJECTS_FIRST",
    )[(ordinal - 1) % 2]
    return verification, cleanup


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
        rotated_verification, rotated_cleanup = _evidence_tokens(ordinal)
        explicit = {
            token.split("=", 1)[0]: token.split("=", 1)[1]
            for token in factors
            if "=" in token
        }
        if "verification_mode" in explicit:
            verification = explicit["verification_mode"]
        elif axes.get("branch") == "refresh_version":
            verification = rotated_verification
        else:
            verification = (
                "pg_collation_catalog_query",
                "collation_sort_verification",
            )[(ordinal - 1) % 2]
        cleanup = explicit.get("cleanup_mode", rotated_cleanup)
        base_factors = tuple(
            token
            for token in factors
            if not token.startswith(("verification_mode=", "cleanup_mode="))
        )
        cases.append(
            _case(
                ordinal,
                group=group,
                case_type=case_type,
                outcome=outcome,
                axes={
                    **axes,
                    "verification_mode": verification,
                    "cleanup_mode": cleanup,
                },
                factor_values=_tokens(
                    *base_factors,
                    f"verification_mode={verification}",
                    f"cleanup_mode={cleanup}",
                ),
                strategy=strategy,
                description=description,
                expected_anchor=expected_anchor,
                execution_profile=(
                    "external_isolated"
                    if group == "refresh_provider_boundary_product"
                    and axes.get("provider_boundary")
                    in {"libc_capability", "icu_stale_version"}
                    else "same_session_multiphase"
                ),
            )
        )

    # 81 successful official-syntax cells.
    for source, dependency in itertools.product(_SOURCE_SHAPES, _DEPENDENCIES):
        add(
            group="success_refresh_product",
            case_type="syntax_semantics",
            outcome="success",
            axes={"branch": "refresh_version", "source_name_shape": source, "dependency_state": dependency, "actor": "superuser", "expected_sqlstate": "00000"},
            factors=_tokens(_branch_token("refresh_version"), "object_state=collation_exists", "expected_status=success", f"collation_name_shape={source}", "privilege_level=superuser", *_dependency_tokens(dependency)),
            strategy="full Cartesian 3 source-name shapes x 3 dependency states",
            description=f"Verify REFRESH VERSION for {source}/{dependency}",
            expected_anchor="SQLSTATE 00000, recorded version equals actual version, and dependencies are unchanged",
        )
    for source, new_name, dependency in itertools.product(_SOURCE_SHAPES, _NEW_NAME_SHAPES, _DEPENDENCIES):
        add(
            group="success_rename_product", case_type="syntax_semantics", outcome="success",
            axes={"branch": "rename", "source_name_shape": source, "new_name_shape": new_name, "dependency_state": dependency, "actor": "superuser", "expected_sqlstate": "00000"},
            factors=_tokens(_branch_token("rename"), "object_state=collation_exists", "expected_status=success", "target_state=new_name_available", f"collation_name_shape={source}", f"new_name_shape={new_name}", "privilege_level=superuser", *_dependency_tokens(dependency)),
            strategy="full Cartesian 3 source-name x 2 rename-target x 3 dependency states",
            description=f"Verify RENAME TO for {source}/{new_name}/{dependency}",
            expected_anchor="SQLSTATE 00000, stable collation OID, new name only, and dependencies preserved",
        )
    for source, owner, dependency in itertools.product(_SOURCE_SHAPES, _OWNER_SHAPES, _DEPENDENCIES):
        add(
            group="success_owner_product", case_type="syntax_semantics", outcome="success",
            axes={"branch": "owner", "source_name_shape": source, "owner_shape": owner, "dependency_state": dependency, "actor": "superuser", "expected_sqlstate": "00000"},
            factors=_tokens(_branch_token("owner"), "object_state=collation_exists", "expected_status=success", "target_state=new_owner_available", f"collation_name_shape={source}", f"new_owner_shape={owner}", "privilege_level=superuser", *_dependency_tokens(dependency)),
            strategy="full Cartesian 3 source-name x 4 RoleSpec targets x 3 dependency states",
            description=f"Verify OWNER TO for {source}/{owner}/{dependency}",
            expected_anchor="SQLSTATE 00000, exact owner change, stable OID, and dependencies preserved",
        )
    for source, target_schema, dependency in itertools.product(_SOURCE_SHAPES, _SCHEMA_SHAPES, _DEPENDENCIES):
        add(
            group="success_set_schema_product", case_type="syntax_semantics", outcome="success",
            axes={"branch": "set_schema", "source_name_shape": source, "target_schema_shape": target_schema, "dependency_state": dependency, "actor": "superuser", "expected_sqlstate": "00000"},
            factors=_tokens(_branch_token("set_schema"), "object_state=collation_exists", "expected_status=success", "target_state=new_schema_available", f"collation_name_shape={source}", "new_schema_shape=existing_schema", "privilege_level=superuser", *_dependency_tokens(dependency)),
            strategy="full Cartesian 3 source-name x 2 target-schema shapes x 3 dependency states",
            description=f"Verify SET SCHEMA for {source}/{target_schema}/{dependency}",
            expected_anchor="SQLSTATE 00000, stable OID in target schema, and dependencies preserved",
        )

    # 33 branch-state failures.
    for branch, source in itertools.product(_BRANCHES, _SOURCE_SHAPES):
        add(
            group="missing_object_product", case_type="negative", outcome="expected_failure",
            axes={"branch": branch, "source_name_shape": source, "dependency_state": "no_dependencies", "actor": "superuser", "expected_sqlstate": "42704"},
            factors=_tokens(_branch_token(branch), "object_state=collation_not_exists", "collation_not_exists=not_exists", "expected_status=failure", f"collation_name_shape={source}", "privilege_level=superuser", "verification_mode=pg_collation_catalog_query"),
            strategy="full Cartesian 4 official branches x 3 missing source-name shapes",
            description=f"Reject missing collation for {branch}/{source}", expected_anchor="SQLSTATE 42704 and target remains absent",
        )
    for source, new_name in itertools.product(_SOURCE_SHAPES, _NEW_NAME_SHAPES):
        add(
            group="rename_duplicate_product", case_type="negative", outcome="expected_failure",
            axes={"branch": "rename", "source_name_shape": source, "new_name_shape": new_name, "dependency_state": "no_dependencies", "actor": "superuser", "expected_sqlstate": "42710"},
            factors=_tokens(_branch_token("rename"), "object_state=collation_exists", "expected_status=failure", "target_state=new_name_conflict", f"collation_name_shape={source}", f"new_name_shape={new_name}", "new_name_conflict=name_already_exists", "privilege_level=superuser"),
            strategy="full Cartesian 3 source-name x 2 conflicting rename-target shapes",
            description=f"Reject duplicate rename target for {source}/{new_name}", expected_anchor="SQLSTATE 42710 and both collations retain their identities",
        )
    for source in _SOURCE_SHAPES:
        add(
            group="owner_missing_role_product", case_type="negative", outcome="expected_failure",
            axes={"branch": "owner", "source_name_shape": source, "owner_shape": "plain_role", "dependency_state": "no_dependencies", "actor": "superuser", "expected_sqlstate": "42704"},
            factors=_tokens(_branch_token("owner"), "object_state=collation_exists", "expected_status=failure", "target_state=new_owner_not_available", f"collation_name_shape={source}", "new_owner_shape=plain_role", "new_owner_not_exists=nonexistent_role", "privilege_level=superuser"),
            strategy="all 3 source-name shapes with an absent RoleSpec",
            description=f"Reject missing new owner for {source}", expected_anchor="SQLSTATE 42704 and owner is unchanged",
        )
    for group, conflict in (("set_schema_missing_product", False), ("set_schema_conflict_product", True)):
        for source, target_schema in itertools.product(_SOURCE_SHAPES, _SCHEMA_SHAPES):
            add(
                group=group, case_type="negative", outcome="expected_failure",
                axes={"branch": "set_schema", "source_name_shape": source, "target_schema_shape": target_schema, "dependency_state": "no_dependencies", "actor": "superuser", "expected_sqlstate": "42710" if conflict else "3F000"},
                factors=_tokens(_branch_token("set_schema"), "object_state=collation_exists", "expected_status=failure", "target_state=new_schema_conflict" if conflict else None, f"collation_name_shape={source}", "new_schema_shape=existing_schema" if conflict else "new_schema_shape=nonexistent_schema", "new_schema_same_name_conflict=same_name_in_target_schema" if conflict else "new_schema_not_exists=nonexistent_schema", "privilege_level=superuser"),
                strategy=f"full Cartesian 3 source-name x 2 target-schema lexical shapes for {'conflict' if conflict else 'missing schema'}",
                description=f"Reject SET SCHEMA {'name conflict' if conflict else 'missing target'} for {source}/{target_schema}",
                expected_anchor=f"SQLSTATE {'42710' if conflict else '3F000'} and source identity is unchanged",
            )

    # 27 privilege truth-table cells.
    for actor in _ACTORS:
        success = actor != "non_owner"
        add(
            group="refresh_privilege_truth_product", case_type="privilege", outcome="success" if success else "expected_failure",
            axes={"branch": "refresh_version", "source_name_shape": "schema_qualified", "dependency_state": "no_dependencies", "actor": actor, "expected_sqlstate": "00000" if success else "42501"},
            factors=_tokens(_branch_token("refresh_version"), "object_state=collation_exists", f"expected_status={'success' if success else 'failure'}", f"privilege_level={actor}", "insufficient_privilege=non_owner" if actor == "non_owner" else None),
            strategy="complete 3-actor ownership truth table for REFRESH VERSION",
            description=f"Verify REFRESH VERSION privilege for {actor}", expected_anchor=f"SQLSTATE {'00000' if success else '42501'} with deterministic version oracle",
        )
    for actor, schema_create in itertools.product(_ACTORS, ("yes", "no")):
        success = actor == "superuser" or (actor == "collation_owner" and schema_create == "yes")
        add(
            group="rename_privilege_truth_product", case_type="privilege", outcome="success" if success else "expected_failure",
            axes={"branch": "rename", "source_name_shape": "schema_qualified", "new_name_shape": "plain_identifier", "dependency_state": "no_dependencies", "actor": actor, "schema_create": schema_create, "expected_sqlstate": "00000" if success else "42501"},
            factors=_tokens(_branch_token("rename"), "object_state=collation_exists", f"expected_status={'success' if success else 'failure'}", "target_state=new_name_available", f"privilege_level={actor}", "insufficient_privilege=non_owner" if actor == "non_owner" else "insufficient_privilege=no_create_on_schema" if not success and schema_create == "no" else None),
            strategy="full Cartesian 3 actors x 2 source-schema CREATE states",
            description=f"Verify RENAME ownership/schema privilege for {actor}/{schema_create}", expected_anchor=f"SQLSTATE {'00000' if success else '42501'} and exact rename truth value",
        )
    for actor, can_set_role, new_owner_create in itertools.product(_ACTORS, ("yes", "no"), ("yes", "no")):
        success = actor == "superuser" or (actor == "collation_owner" and can_set_role == "yes" and new_owner_create == "yes")
        add(
            group="owner_privilege_truth_product", case_type="privilege", outcome="success" if success else "expected_failure",
            axes={"branch": "owner", "source_name_shape": "schema_qualified", "owner_shape": "plain_role", "dependency_state": "no_dependencies", "actor": actor, "can_set_role": can_set_role, "new_owner_create": new_owner_create, "expected_sqlstate": "00000" if success else "42501"},
            factors=_tokens(_branch_token("owner"), "object_state=collation_exists", f"expected_status={'success' if success else 'failure'}", "target_state=new_owner_available", "new_owner_shape=plain_role", f"privilege_level={actor}", f"owner_membership={'member_of_new_owner' if can_set_role == 'yes' else 'not_member_of_new_owner'}", "insufficient_privilege=non_owner" if actor == "non_owner" else "insufficient_privilege=no_create_on_schema" if actor == "collation_owner" and new_owner_create == "no" else None),
            strategy="full Cartesian 3 actors x SET ROLE yes/no x new-owner schema CREATE yes/no",
            description=f"Verify OWNER TO privilege for {actor}/{can_set_role}/{new_owner_create}", expected_anchor=f"SQLSTATE {'00000' if success else '42501'} and exact owner truth value",
        )
    for actor, schema_create in itertools.product(_ACTORS, ("yes", "no")):
        success = actor == "superuser" or (actor == "collation_owner" and schema_create == "yes")
        add(
            group="set_schema_privilege_truth_product", case_type="privilege", outcome="success" if success else "expected_failure",
            axes={"branch": "set_schema", "source_name_shape": "schema_qualified", "target_schema_shape": "plain_identifier", "dependency_state": "no_dependencies", "actor": actor, "schema_create": schema_create, "expected_sqlstate": "00000" if success else "42501"},
            factors=_tokens(_branch_token("set_schema"), "object_state=collation_exists", f"expected_status={'success' if success else 'failure'}", "target_state=new_schema_available", "new_schema_shape=existing_schema", f"privilege_level={actor}", "insufficient_privilege=non_owner" if actor == "non_owner" else "insufficient_privilege=no_create_on_schema" if not success and schema_create == "no" else None),
            strategy="full Cartesian 3 actors x 2 target-schema CREATE states",
            description=f"Verify SET SCHEMA privilege for {actor}/{schema_create}", expected_anchor=f"SQLSTATE {'00000' if success else '42501'} and exact namespace truth value",
        )

    # 12 permission-sensitive no-op cells.
    for source in _SOURCE_SHAPES:
        add(
            group="rename_same_name_product", case_type="noop_boundary", outcome="expected_failure",
            axes={"branch": "rename", "source_name_shape": source, "new_name_shape": "same_name", "dependency_state": "no_dependencies", "actor": "superuser", "expected_sqlstate": "42710"},
            factors=_tokens(_branch_token("rename"), "object_state=collation_exists", "expected_status=failure", "target_state=new_name_conflict", f"collation_name_shape={source}", "new_name_conflict=name_already_exists", "privilege_level=superuser"),
            strategy="all 3 source-name shapes at the same-name duplicate boundary",
            description=f"Reject RENAME TO the existing name for {source}", expected_anchor="SQLSTATE 42710 and identity remains unchanged",
        )
    for actor in _ACTORS:
        add(
            group="owner_same_owner_noop_product", case_type="noop", outcome="success",
            axes={"branch": "owner", "source_name_shape": "schema_qualified", "owner_shape": "plain_role", "dependency_state": "no_dependencies", "actor": actor, "expected_sqlstate": "00000"},
            factors=_tokens(_branch_token("owner"), "object_state=collation_exists", "expected_status=success", "target_state=new_owner_available", f"privilege_level={actor}"),
            strategy="complete 3-actor same-owner early-return truth table",
            description=f"Verify OWNER TO current owner no-op for {actor}", expected_anchor="SQLSTATE 00000 and owner identity remains unchanged",
        )
    for actor, schema_create in itertools.product(_ACTORS, ("yes", "no")):
        success = actor == "superuser" or schema_create == "yes"
        add(
            group="set_schema_same_schema_product", case_type="noop", outcome="success" if success else "expected_failure",
            axes={"branch": "set_schema", "source_name_shape": "schema_qualified", "target_schema_shape": "same_schema", "dependency_state": "no_dependencies", "actor": actor, "schema_create": schema_create, "expected_sqlstate": "00000" if success else "42501"},
            factors=_tokens(_branch_token("set_schema"), "object_state=collation_exists", f"expected_status={'success' if success else 'failure'}", "target_state=new_schema_available", "new_schema_shape=existing_schema", f"privilege_level={actor}", "insufficient_privilege=non_owner" if actor == "non_owner" else "insufficient_privilege=no_create_on_schema" if not success and schema_create == "no" else None),
            strategy="full Cartesian 3 actors x 2 same-schema CREATE states",
            description=f"Verify SET SCHEMA same-schema no-op for {actor}/{schema_create}", expected_anchor=f"SQLSTATE {'00000' if success else '42501'} and same namespace is preserved",
        )

    # Provider/default, parser/namespace, and rollback boundaries.
    provider_boundaries = (
        ("builtin_current_version", "success", "00000"),
        ("default_collation", "expected_failure", "XX000"),
        ("system_c_collation", "success", "00000"),
        ("libc_capability", "success", "00000"),
        ("icu_stale_version", "success", "00000"),
    )
    for boundary, outcome, sqlstate in provider_boundaries:
        verification_mode = (
            "pg_collation_catalog_query"
            if boundary == "default_collation"
            else "pg_collation_actual_version_query"
        )
        add(
            group="refresh_provider_boundary_product", case_type="provider_boundary", outcome=outcome,
            axes={"branch": "refresh_version", "source_name_shape": "schema_qualified", "dependency_state": "no_dependencies", "actor": "superuser", "provider_boundary": boundary, "expected_sqlstate": sqlstate},
            factors=_tokens(_branch_token("refresh_version"), "object_state=collation_exists", f"expected_status={'failure' if outcome == 'expected_failure' else 'success'}", "privilege_level=superuser", f"verification_mode={verification_mode}"),
            strategy="one isolated deterministic cell per portable built-in/default provider boundary",
            description=f"Verify REFRESH VERSION provider boundary {boundary}", expected_anchor=f"SQLSTATE {sqlstate} and stable version predicate",
        )

    parser_boundaries = (
        ("three_part_refresh_version", "refresh_version", "0A000"),
        ("three_part_rename", "rename", "0A000"),
        ("three_part_owner", "owner", "0A000"),
        ("three_part_set_schema", "set_schema", "0A000"),
        ("qualified_rename_target", "rename", "42601"),
        ("unquoted_reserved_rename_target", "rename", "42601"),
        ("qualified_owner_target", "owner", "42601"),
        ("qualified_set_schema_target", "set_schema", "42601"),
        ("pg_temp_move_into", "set_schema", "0A000"),
        ("pg_temp_move_out", "set_schema", "0A000"),
        ("pg_toast_move_into", "set_schema", "0A000"),
        ("pg_toast_move_out", "set_schema", "0A000"),
    )
    for boundary, branch, sqlstate in parser_boundaries:
        add(
            group="parser_namespace_boundary_product", case_type="parser_namespace", outcome="expected_failure",
            axes={"branch": branch, "source_name_shape": "schema_qualified", "dependency_state": "no_dependencies", "actor": "superuser", "boundary": boundary, "expected_sqlstate": sqlstate},
            factors=_tokens(_branch_token(branch), "object_state=collation_exists", "expected_status=failure", "privilege_level=superuser"),
            strategy=f"isolated official parser/namespace boundary {boundary}",
            description=f"Reject ALTER COLLATION boundary {boundary}", expected_anchor=f"SQLSTATE {sqlstate} and original catalog identity",
        )

    for branch in _BRANCHES:
        add(
            group="transactional_rollback_product", case_type="transactionality", outcome="success",
            axes={"branch": branch, "source_name_shape": "schema_qualified", "dependency_state": "table_column", "actor": "superuser", "expected_sqlstate": "00000"},
            factors=_tokens(_branch_token(branch), "object_state=collation_exists", "expected_status=success", "privilege_level=superuser", *_dependency_tokens("table_column")),
            strategy="all 4 official branches inside an explicit transaction followed by ROLLBACK",
            description=f"Verify transactional rollback of ALTER COLLATION {branch}", expected_anchor="SQLSTATE 00000 inside transaction and pre-action metadata after rollback",
        )

    if len(cases) != 174:
        raise RemainingStatementRegressError(
            f"ALTER COLLATION strict design expected 174 cases, found {len(cases)}"
        )
    return tuple(cases)


def _ids(cases: tuple[StatementRegressCase, ...], predicate: Callable[[StatementRegressCase], bool]) -> tuple[str, ...]:
    return tuple(case.case_id for case in cases if predicate(case))


def _factor_decisions(entry: StatementCycleEntry, cases: tuple[StatementRegressCase, ...]) -> tuple[FactorValueDecision, ...]:
    expected_failure_values = {
        ("collation_not_exists", "not_exists"),
        ("expected_status", "failure"),
        ("insufficient_privilege", "no_create_on_schema"),
        ("insufficient_privilege", "non_owner"),
        ("new_name_conflict", "name_already_exists"),
        ("new_owner_not_exists", "nonexistent_role"),
        ("new_schema_not_exists", "nonexistent_schema"),
        ("new_schema_same_name_conflict", "same_name_in_target_schema"),
        ("new_schema_shape", "nonexistent_schema"),
        ("object_state", "collation_not_exists"),
        ("owner_membership", "not_member_of_new_owner"),
        ("privilege_level", "non_owner"),
        ("target_state", "new_name_conflict"),
        ("target_state", "new_owner_not_available"),
        ("target_state", "new_schema_conflict"),
    }
    decisions: list[FactorValueDecision] = []
    for factor in entry.factors:
        for value, row_id in zip(factor.values, factor.row_ids):
            token = f"{factor.name}={value}"
            failure = (factor.name, value) in expected_failure_values
            witnesses = _ids(
                cases,
                lambda case, token=token, failure=failure: (
                    token in case.factor_values
                    and (not failure or case.outcome == "expected_failure")
                ),
            )
            if not witnesses:
                raise RemainingStatementRegressError(f"ALTER COLLATION has no real witness for {token}")
            decisions.append(
                FactorValueDecision(
                    row_id=row_id,
                    factor=factor.name,
                    value=value,
                    disposition="expected_failure" if failure else "covered",
                    reason="The canonical value is witnessed by an isolated expected-failure SQL program with a stable SQLSTATE oracle." if failure else None,
                    case_ids=witnesses,
                )
            )
    return tuple(decisions)


def build_alter_collation_plan(snapshot: StatementFactorCycleSnapshot, entry: StatementCycleEntry) -> StatementRegressPlan:
    cases = _build_cases()
    if tuple(case.ordinal for case in cases) != tuple(range(1, 175)):
        raise RemainingStatementRegressError("ALTER COLLATION case ordinals are not contiguous")
    return StatementRegressPlan(
        statement_key="alter_collation",
        file_prefix="ALTERCOLLATION",
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
    target_shape = case.derived_axes.get("target_schema_shape", "plain_identifier")
    target_schema_raw = (
        f"{prefix}Target Schema"
        if target_shape == "quoted_identifier"
        else f"{prefix}dst"
    )
    source_shape = case.derived_axes.get("source_name_shape", "schema_qualified")
    collation_raw = (
        f"{prefix}Collation Name"
        if source_shape == "quoted_identifier"
        else f"{prefix}coll"
    )
    new_shape = case.derived_axes.get("new_name_shape", "plain_identifier")
    new_raw = (
        f"{prefix}Renamed Collation"
        if new_shape == "quoted_identifier"
        else f"{prefix}renamed"
    )
    source_schema = source_schema_raw
    target_schema = (
        _quote_ident(target_schema_raw)
        if target_shape == "quoted_identifier"
        else target_schema_raw
    )
    collation_ident = (
        _quote_ident(collation_raw)
        if source_shape == "quoted_identifier"
        else collation_raw
    )
    source_qualified = f"{source_schema}.{collation_ident}"
    if source_shape == "schema_qualified":
        target_ref = source_qualified
    else:
        target_ref = collation_ident
    return {
        "prefix": prefix,
        "source_schema_raw": source_schema_raw,
        "source_schema": source_schema,
        "target_schema_raw": target_schema_raw,
        "target_schema": target_schema,
        "collation_raw": collation_raw,
        "collation_ident": collation_ident,
        "source_qualified": source_qualified,
        "target_ref": target_ref,
        "new_raw": new_raw,
        "new_ident": _quote_ident(new_raw) if new_shape == "quoted_identifier" else new_raw,
        "new_qualified": f"{source_schema}."
        + (_quote_ident(new_raw) if new_shape == "quoted_identifier" else new_raw),
        "moved_qualified": f"{target_schema}.{collation_ident}",
        "conflict_ident": _quote_ident(new_raw),
        "data_table": f"{prefix}data",
        "index_name": f"{prefix}sort_idx",
        "old_owner": f"{prefix}old_owner",
        "new_owner": f"{prefix}new_owner",
        "intruder": f"{prefix}intruder",
        "foreign_database": f"{prefix}foreign_db",
    }


def _uses_table(case: StatementRegressCase) -> bool:
    return case.derived_axes.get("dependency_state") in {
        "table_column",
        "expression_index",
    }


def _roles_cleanup(names: Mapping[str, str]) -> list[str]:
    return [
        "RESET ROLE;",
        "RESET SESSION AUTHORIZATION;",
        "DROP ROLE IF EXISTS "
        + ", ".join((names["intruder"], names["old_owner"], names["new_owner"]))
        + ";",
    ]


def _precleanup(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    lines: list[str] = []
    if _uses_table(case):
        # The table style contract deliberately requires this to be the first
        # executable statement and requires a matching final DROP.
        lines.append(f"DROP TABLE IF EXISTS public.{names['data_table']} CASCADE;")
    create_target_schema = case.case_group != "set_schema_missing_product"
    create_new_owner = case.case_group != "owner_missing_role_product"
    roles = [names["old_owner"], names["intruder"]]
    if create_new_owner:
        roles.insert(1, names["new_owner"])
    lines.extend(
        [
            "RESET ROLE;",
            "RESET SESSION AUTHORIZATION;",
            "SET client_min_messages TO warning;",
            r"\set ON_ERROR_STOP on",
            f"DROP SCHEMA IF EXISTS {names['target_schema']} CASCADE;",
            f"DROP SCHEMA IF EXISTS {names['source_schema']} CASCADE;",
            *_roles_cleanup(names),
            f"CREATE ROLE {names['old_owner']};",
            *([f"CREATE ROLE {names['new_owner']};"] if create_new_owner else []),
            f"CREATE ROLE {names['intruder']};",
            f"CREATE SCHEMA {names['source_schema']};",
            *([f"CREATE SCHEMA {names['target_schema']};"] if create_target_schema else []),
            f"GRANT USAGE ON SCHEMA {names['source_schema']} TO {', '.join(roles)};",
            *(
                [f"GRANT USAGE ON SCHEMA {names['target_schema']} TO {', '.join(roles)};"]
                if create_target_schema
                else []
            ),
            f"SET search_path TO {names['source_schema']}, pg_catalog;",
        ]
    )
    return lines


def _refresh_fixture(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    boundary = case.derived_axes.get("provider_boundary")
    target = names["source_qualified"]
    if boundary in {"default_collation", "system_c_collation"}:
        return []
    if boundary == "libc_capability":
        return [
            "SET client_min_messages TO error;",
            f"CREATE COLLATION {target} (PROVIDER = libc, LOCALE = 'C');"
        ]
    if boundary == "icu_stale_version":
        return [
            "SET client_min_messages TO error;",
            f"CREATE COLLATION {target} (PROVIDER = icu, LOCALE = 'und', VERSION = '0');"
        ]
    if boundary == "builtin_current_version":
        return [
            "SET client_min_messages TO error;",
            f"CREATE COLLATION {target} (PROVIDER = builtin, LOCALE = 'C.UTF-8');"
        ]
    return [
        "SET client_min_messages TO error;",
        f"CREATE COLLATION {target} (PROVIDER = builtin, LOCALE = 'C.UTF-8', VERSION = '0');"
    ]


def _needs_fixture(case: StatementRegressCase) -> bool:
    if case.case_group == "missing_object_product":
        return False
    if case.case_group == "refresh_provider_boundary_product" and case.derived_axes[
        "provider_boundary"
    ] in {"default_collation", "system_c_collation"}:
        return False
    return True


def _collation_fixture(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    if not _needs_fixture(case):
        return []
    if (
        case.case_group == "parser_namespace_boundary_product"
        and case.derived_axes["boundary"].endswith("move_out")
    ):
        return []
    if case.derived_axes["branch"] == "refresh_version" or (
        case.case_group == "transactional_rollback_product"
        and case.derived_axes["branch"] == "refresh_version"
    ):
        create_lines = _refresh_fixture(case, names)
    else:
        create_lines = [
            f"CREATE COLLATION {names['source_qualified']} (PROVIDER = libc, LOCALE = 'C');"
        ]
    if not _requires_role_owner(case):
        return create_lines
    return [
        f"GRANT CREATE ON SCHEMA {names['source_schema']} TO {names['old_owner']};",
        f"SET ROLE {names['old_owner']};",
        *create_lines,
        "RESET ROLE;",
        f"REVOKE CREATE ON SCHEMA {names['source_schema']} FROM {names['old_owner']};",
    ]


def _branch_state_fixture(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    if case.case_group == "rename_duplicate_product":
        return [
            f"CREATE COLLATION {names['new_qualified']} (PROVIDER = libc, LOCALE = 'C');"
        ]
    if case.case_group == "set_schema_conflict_product":
        return [
            f"CREATE COLLATION {names['moved_qualified']} (PROVIDER = libc, LOCALE = 'C');"
        ]
    return []


def _table_fixture(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    dependency = case.derived_axes.get("dependency_state")
    if dependency not in {"table_column", "expression_index"}:
        return []
    collation_clause = (
        f" COLLATE {names['source_qualified']}"
        if dependency == "table_column"
        else ""
    )
    lines = [
        f"CREATE TABLE public.{names['data_table']} (",
        "    id integer PRIMARY KEY,",
        f"    sort_key text{collation_clause} NOT NULL,",
        "    payload text NOT NULL CHECK (length(payload) > 0),",
        "    rank_no integer NOT NULL CHECK (rank_no > 0),",
        "    active boolean NOT NULL DEFAULT true,",
        f"    CONSTRAINT {names['prefix']}data_unique UNIQUE (rank_no, id)",
        ");",
        f"INSERT INTO public.{names['data_table']}(id, sort_key, payload, rank_no) VALUES",
        "    (1, 'alpha', 'first', 10),",
        "    (2, 'beta', 'second', 20),",
        "    (3, 'gamma', 'third', 30);",
    ]
    if dependency == "expression_index":
        lines.extend(
            [
                f"CREATE INDEX {names['index_name']}",
                f"ON public.{names['data_table']} ((sort_key COLLATE {names['source_qualified']}));",
                f"SELECT c.relfilenode::text AS before_index_relfilenode",
                "FROM pg_catalog.pg_class AS c",
                "JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace",
                "WHERE n.nspname = 'public'",
                f"  AND c.relname = {_literal(names['index_name'])}",
                "ORDER BY c.oid",
                r"\gset",
            ]
        )
    return lines


def _requires_role_owner(case: StatementRegressCase) -> bool:
    return case.case_group in {
        "refresh_privilege_truth_product",
        "rename_privilege_truth_product",
        "owner_privilege_truth_product",
        "set_schema_privilege_truth_product",
        "owner_same_owner_noop_product",
        "set_schema_same_schema_product",
    }


def _actor_grantee(actor: str, names: Mapping[str, str]) -> str:
    if actor == "superuser":
        return "SESSION_USER"
    if actor == "collation_owner":
        return names["old_owner"]
    return names["intruder"]


def _privilege_fixture(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    lines: list[str] = []
    group = case.case_group
    actor = case.derived_axes.get("actor", "superuser")
    schema_create = case.derived_axes.get("schema_create")
    if group in {"rename_privilege_truth_product", "rename_same_name_product"}:
        if schema_create == "yes":
            lines.append(
                f"GRANT CREATE ON SCHEMA {names['source_schema']} TO {_actor_grantee(actor, names)};"
            )
    if group in {"set_schema_privilege_truth_product"}:
        if schema_create == "yes":
            lines.append(
                f"GRANT CREATE ON SCHEMA {names['target_schema']} TO {_actor_grantee(actor, names)};"
            )
    if group == "set_schema_same_schema_product" and schema_create == "yes":
        lines.append(
            f"GRANT CREATE ON SCHEMA {names['source_schema']} TO {_actor_grantee(actor, names)};"
        )
    if group == "owner_privilege_truth_product":
        if case.derived_axes["can_set_role"] == "yes":
            grantee = _actor_grantee(actor, names)
            lines.append(
                f"GRANT {names['new_owner']} TO {grantee} WITH SET TRUE;"
            )
        if case.derived_axes["new_owner_create"] == "yes":
            lines.append(
                f"GRANT CREATE ON SCHEMA {names['source_schema']} TO {names['new_owner']};"
            )
    if group == "success_owner_product" and case.derived_axes["owner_shape"] == "plain_role":
        lines.append(
            f"GRANT CREATE ON SCHEMA {names['source_schema']} TO {names['new_owner']};"
        )
    if actor == "collation_owner":
        lines.append(f"SET ROLE {names['old_owner']};")
    elif actor == "non_owner":
        lines.append(f"SET ROLE {names['intruder']};")
    return lines


def _normal_action(case: StatementRegressCase, names: Mapping[str, str]) -> str:
    branch = case.derived_axes["branch"]
    group = case.case_group
    reference = names["target_ref"]
    if group == "refresh_provider_boundary_product":
        boundary = case.derived_axes["provider_boundary"]
        if boundary == "default_collation":
            reference = 'pg_catalog."default"'
        elif boundary == "system_c_collation":
            reference = 'pg_catalog."C"'
    if branch == "refresh_version":
        return f"ALTER COLLATION {reference} REFRESH VERSION;"
    if branch == "rename":
        if group == "rename_same_name_product":
            new_name = names["collation_ident"]
        else:
            new_name = names["new_ident"]
        return f"ALTER COLLATION {reference} RENAME TO {new_name};"
    if branch == "owner":
        if group == "owner_same_owner_noop_product":
            owner = names["old_owner"]
        else:
            owner_shape = case.derived_axes.get("owner_shape", "plain_role")
            owner = names["new_owner"] if owner_shape == "plain_role" else owner_shape
        return f"ALTER COLLATION {reference} OWNER TO {owner};"
    target = (
        names["source_schema"]
        if group == "set_schema_same_schema_product"
        else names["target_schema"]
    )
    return f"ALTER COLLATION {reference} SET SCHEMA {target};"


def _boundary_action(case: StatementRegressCase, names: Mapping[str, str]) -> str:
    boundary = case.derived_axes["boundary"]
    branch = case.derived_axes["branch"]
    if boundary.startswith("three_part_"):
        reference = (
            f"{_quote_ident(names['foreign_database'])}."
            f"{names['source_schema']}.{names['collation_ident']}"
        )
        if branch == "refresh_version":
            return f"ALTER COLLATION {reference} REFRESH VERSION;"
        if branch == "rename":
            return f"ALTER COLLATION {reference} RENAME TO {names['new_ident']};"
        if branch == "owner":
            # A valid RoleSpec ensures the cross-database name is the primary
            # error instead of an earlier missing-role diagnostic.
            return f"ALTER COLLATION {reference} OWNER TO CURRENT_USER;"
        return f"ALTER COLLATION {reference} SET SCHEMA {names['target_schema']};"
    if boundary == "qualified_rename_target":
        return f"ALTER COLLATION {names['source_qualified']} RENAME TO {names['target_schema']}.{names['new_ident']};"
    if boundary == "unquoted_reserved_rename_target":
        return f"ALTER COLLATION {names['source_qualified']} RENAME TO select;"
    if boundary == "qualified_owner_target":
        return f"ALTER COLLATION {names['source_qualified']} OWNER TO {names['source_schema']}.{names['new_owner']};"
    if boundary == "qualified_set_schema_target":
        return f"ALTER COLLATION {names['source_qualified']} SET SCHEMA {names['target_schema']}.{names['source_schema']};"
    if boundary.endswith("move_into"):
        namespace = "pg_temp" if boundary.startswith("pg_temp") else "pg_toast"
        return f"ALTER COLLATION {names['source_qualified']} SET SCHEMA {namespace};"
    # The fixture is created in the special namespace where PostgreSQL permits
    # creation; the action itself is the reviewed move-out boundary.
    namespace = "pg_temp" if boundary.startswith("pg_temp") else "pg_toast"
    return f"ALTER COLLATION {namespace}.{names['collation_ident']} SET SCHEMA {names['target_schema']};"


def _target_action(case: StatementRegressCase, names: Mapping[str, str]) -> str:
    if case.case_group == "parser_namespace_boundary_product":
        return _boundary_action(case, names)
    return _normal_action(case, names)


def _special_namespace_fixture(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    if case.case_group != "parser_namespace_boundary_product":
        return []
    boundary = case.derived_axes["boundary"]
    if not boundary.endswith("move_out"):
        return []
    namespace = "pg_temp" if boundary.startswith("pg_temp") else "pg_toast"
    return [
        f"DROP COLLATION IF EXISTS {namespace}.{names['collation_ident']} CASCADE;",
        f"CREATE COLLATION {namespace}.{names['collation_ident']} (PROVIDER = libc, LOCALE = 'C');",
    ]


def _capture_identity(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    boundary = case.derived_axes.get("boundary", "")
    provider_boundary = case.derived_axes.get("provider_boundary", "")
    if provider_boundary == "default_collation":
        namespace_predicate = "n.nspname = 'pg_catalog'"
        collation_predicate = "c.collname = 'default'"
    elif provider_boundary == "system_c_collation":
        namespace_predicate = "n.nspname = 'pg_catalog'"
        collation_predicate = "c.collname = 'C'"
    elif boundary == "pg_temp_move_out":
        namespace_predicate = "n.oid = pg_catalog.pg_my_temp_schema()"
        collation_predicate = f"c.collname = {_literal(names['collation_raw'])}"
    elif boundary == "pg_toast_move_out":
        namespace_predicate = "n.nspname = 'pg_toast'"
        collation_predicate = f"c.collname = {_literal(names['collation_raw'])}"
    else:
        namespace_predicate = f"n.nspname = {_literal(names['source_schema_raw'])}"
        collation_predicate = f"c.collname = {_literal(names['collation_raw'])}"
    return [
        "SELECT",
        "    c.oid::text AS before_collation_oid,",
        "    COALESCE(c.collversion, '<NULL>') AS before_collation_version,",
        "    pg_catalog.pg_get_userbyid(c.collowner) AS before_collation_owner",
        "FROM pg_catalog.pg_collation AS c",
        "JOIN pg_catalog.pg_namespace AS n ON n.oid = c.collnamespace",
        f"WHERE {namespace_predicate}",
        f"  AND {collation_predicate}",
        "ORDER BY c.oid",
        r"\gset",
    ]


def _final_identity(case: StatementRegressCase, names: Mapping[str, str]) -> tuple[str, str]:
    group = case.case_group
    if case.outcome == "success" and group == "success_rename_product":
        return names["source_schema_raw"], names["new_raw"]
    if case.outcome == "success" and group == "rename_privilege_truth_product":
        return names["source_schema_raw"], names["new_raw"]
    if case.outcome == "success" and group == "success_set_schema_product":
        return names["target_schema_raw"], names["collation_raw"]
    if case.outcome == "success" and group == "set_schema_privilege_truth_product":
        return names["target_schema_raw"], names["collation_raw"]
    return names["source_schema_raw"], names["collation_raw"]


def _identity_oracle(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    if not _needs_fixture(case):
        if case.case_group == "missing_object_product":
            return [
                "SELECT count(*) = 0 AS missing_collation_remains_absent",
                "FROM pg_catalog.pg_collation AS c",
                "JOIN pg_catalog.pg_namespace AS n ON n.oid = c.collnamespace",
                f"WHERE n.nspname = {_literal(names['source_schema_raw'])}",
                f"  AND c.collname = {_literal(names['collation_raw'])}",
                "ORDER BY missing_collation_remains_absent;",
            ]
        provider_boundary = case.derived_axes.get("provider_boundary", "")
        protected_name = "default" if provider_boundary == "default_collation" else "C"
        return [
            "SELECT",
            "    count(*) = 1 AS protected_system_collation_preserved,",
            "    COALESCE(bool_and(c.oid::text = :'before_collation_oid'), false) AS protected_collation_oid_stable,",
            "    COALESCE(bool_and(COALESCE(c.collversion, '<NULL>') = :'before_collation_version'), false) AS protected_collation_version_stable,",
            "    COALESCE(bool_and(pg_catalog.pg_get_userbyid(c.collowner) = :'before_collation_owner'), false) AS protected_collation_owner_stable",
            "FROM pg_catalog.pg_collation AS c",
            "JOIN pg_catalog.pg_namespace AS n ON n.oid = c.collnamespace",
            "WHERE n.nspname = 'pg_catalog'",
            f"  AND c.collname = {_literal(protected_name)}",
            "ORDER BY protected_system_collation_preserved, protected_collation_oid_stable, protected_collation_version_stable, protected_collation_owner_stable;",
        ]
    boundary = case.derived_axes.get("boundary", "")
    if boundary == "pg_temp_move_out":
        return [
            "SELECT",
            "    count(*) = 1 AS special_source_preserved,",
            "    COALESCE(bool_and(c.oid::text = :'before_collation_oid'), false) AS collation_oid_stable,",
            "    COALESCE(bool_and(COALESCE(c.collversion, '<NULL>') = :'before_collation_version'), false) AS collation_version_stable,",
            "    COALESCE(bool_and(pg_catalog.pg_get_userbyid(c.collowner) = :'before_collation_owner'), false) AS collation_owner_stable",
            "FROM pg_catalog.pg_collation AS c",
            "JOIN pg_catalog.pg_namespace AS n ON n.oid = c.collnamespace",
            "WHERE n.oid = pg_catalog.pg_my_temp_schema()",
            f"  AND c.collname = {_literal(names['collation_raw'])}",
            "ORDER BY special_source_preserved, collation_oid_stable, collation_version_stable, collation_owner_stable;",
        ]
    if boundary == "pg_toast_move_out":
        return [
            "SELECT",
            "    count(*) = 1 AS special_source_preserved,",
            "    COALESCE(bool_and(c.oid::text = :'before_collation_oid'), false) AS collation_oid_stable,",
            "    COALESCE(bool_and(COALESCE(c.collversion, '<NULL>') = :'before_collation_version'), false) AS collation_version_stable,",
            "    COALESCE(bool_and(pg_catalog.pg_get_userbyid(c.collowner) = :'before_collation_owner'), false) AS collation_owner_stable",
            "FROM pg_catalog.pg_collation AS c",
            "JOIN pg_catalog.pg_namespace AS n ON n.oid = c.collnamespace",
            "WHERE n.nspname = 'pg_toast'",
            f"  AND c.collname = {_literal(names['collation_raw'])}",
            "ORDER BY special_source_preserved, collation_oid_stable, collation_version_stable, collation_owner_stable;",
        ]
    final_schema, final_name = _final_identity(case, names)
    snapshot_must_be_preserved = (
        case.outcome == "expected_failure"
        or case.case_group == "transactional_rollback_product"
    )
    owner_must_be_preserved = snapshot_must_be_preserved or case.derived_axes["branch"] != "owner"
    version_must_be_preserved = snapshot_must_be_preserved or case.derived_axes["branch"] != "refresh_version"
    select_columns = [
        "    count(*) = 1 AS collation_identity_present",
        "    COALESCE(bool_and(c.oid::text = :'before_collation_oid'), false) AS collation_oid_stable",
    ]
    if version_must_be_preserved:
        select_columns.append(
            "    COALESCE(bool_and(COALESCE(c.collversion, '<NULL>') = :'before_collation_version'), false) AS collation_version_stable"
        )
    if owner_must_be_preserved:
        select_columns.append(
            "    COALESCE(bool_and(pg_catalog.pg_get_userbyid(c.collowner) = :'before_collation_owner'), false) AS collation_owner_stable"
        )
    lines = [
        "SELECT",
        *[
            column + ("," if index < len(select_columns) - 1 else "")
            for index, column in enumerate(select_columns)
        ],
        "FROM pg_catalog.pg_collation AS c",
        "JOIN pg_catalog.pg_namespace AS n ON n.oid = c.collnamespace",
        f"WHERE n.nspname = {_literal(final_schema)}",
        f"  AND c.collname = {_literal(final_name)}",
        "ORDER BY " + ", ".join(
            [
                "collation_identity_present",
                "collation_oid_stable",
                *( ["collation_version_stable"] if version_must_be_preserved else [] ),
                *( ["collation_owner_stable"] if owner_must_be_preserved else [] ),
            ]
        ) + ";",
    ]
    if case.derived_axes["branch"] == "owner" and case.outcome == "success":
        if case.case_group == "transactional_rollback_product":
            expected_owner = "session_user"
        elif case.case_group == "owner_same_owner_noop_product":
            expected_owner = _literal(names["old_owner"])
        elif case.derived_axes.get("owner_shape", "plain_role") == "plain_role":
            expected_owner = _literal(names["new_owner"])
        else:
            expected_owner = "session_user"
        lines.extend(
            [
                "SELECT count(*) = 1 AS collation_owner_matches",
                "FROM pg_catalog.pg_collation AS c",
                "JOIN pg_catalog.pg_namespace AS n ON n.oid = c.collnamespace",
                f"WHERE n.nspname = {_literal(final_schema)}",
                f"  AND c.collname = {_literal(final_name)}",
                f"  AND pg_catalog.pg_get_userbyid(c.collowner) = {expected_owner}",
                "ORDER BY collation_owner_matches;",
            ]
        )
    if case.case_group == "set_schema_same_schema_product":
        lines.append("SELECT true AS same_schema_noop_preserved;")
    return lines


def _version_oracle(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    branch = case.derived_axes["branch"]
    if branch != "refresh_version" or case.outcome != "success":
        return []
    if case.case_group == "transactional_rollback_product":
        return [
            "SELECT c.collversion = '0' AS refresh_version_rollback_preserved",
            "FROM pg_catalog.pg_collation AS c",
            "JOIN pg_catalog.pg_namespace AS n ON n.oid = c.collnamespace",
            f"WHERE n.nspname = {_literal(names['source_schema_raw'])}",
            f"  AND c.collname = {_literal(names['collation_raw'])}",
            "ORDER BY refresh_version_rollback_preserved;",
        ]
    if case.case_group == "refresh_provider_boundary_product" and case.derived_axes[
        "provider_boundary"
    ] == "system_c_collation":
        return [
            "SELECT c.collversion IS NOT DISTINCT FROM pg_catalog.pg_collation_actual_version(c.oid) AS collversion_matches_actual",
            "FROM pg_catalog.pg_collation AS c",
            "JOIN pg_catalog.pg_namespace AS n ON n.oid = c.collnamespace",
            "WHERE n.nspname = 'pg_catalog'",
            "  AND c.collname = 'C'",
            "ORDER BY collversion_matches_actual;",
        ]
    return [
        "SELECT c.collversion IS NOT DISTINCT FROM pg_catalog.pg_collation_actual_version(c.oid) AS collversion_matches_actual",
        "FROM pg_catalog.pg_collation AS c",
        "JOIN pg_catalog.pg_namespace AS n ON n.oid = c.collnamespace",
        f"WHERE n.nspname = {_literal(names['source_schema_raw'])}",
        f"  AND c.collname = {_literal(names['collation_raw'])}",
        "ORDER BY collversion_matches_actual;",
    ]


def _dependency_oracle(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    dependency = case.derived_axes.get("dependency_state")
    if dependency not in {"table_column", "expression_index"}:
        if not _needs_fixture(case):
            return ["SELECT true AS no_dependency_fixture_expected;"]
        boundary = case.derived_axes.get("boundary", "")
        if boundary == "pg_temp_move_out":
            collation_ref = f"pg_temp.{names['collation_ident']}"
        elif boundary == "pg_toast_move_out":
            collation_ref = f"pg_toast.{names['collation_ident']}"
        else:
            final_schema, final_name = _final_identity(case, names)
            collation_ref = f"{_quote_ident(final_schema)}.{_quote_ident(final_name)}"
        return [
            "SELECT array_agg(value ORDER BY value COLLATE "
            + collation_ref
            + ") = ARRAY['alpha', 'beta', 'gamma']::text[] AS collation_sort_verification",
            "FROM (VALUES ('gamma'::text), ('alpha'::text), ('beta'::text)) AS input(value);",
        ]
    lines: list[str] = []
    if dependency == "table_column":
        lines.extend(
            [
                "SELECT a.attcollation::text = :'before_collation_oid' AS table_column_dependency_preserved",
                "FROM pg_catalog.pg_attribute AS a",
                "JOIN pg_catalog.pg_class AS t ON t.oid = a.attrelid",
                "JOIN pg_catalog.pg_namespace AS n ON n.oid = t.relnamespace",
                "WHERE n.nspname = 'public'",
                f"  AND t.relname = {_literal(names['data_table'])}",
                "  AND a.attname = 'sort_key'",
                "ORDER BY table_column_dependency_preserved;",
            ]
        )
    else:
        lines.extend(
            [
                "SELECT c.relfilenode::text = :'before_index_relfilenode' AS index_relfilenode_unchanged",
                "FROM pg_catalog.pg_class AS c",
                "JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace",
                "WHERE n.nspname = 'public'",
                f"  AND c.relname = {_literal(names['index_name'])}",
                "ORDER BY index_relfilenode_unchanged;",
                "SELECT count(*) > 0 AS index_collation_dependency_preserved",
                "FROM pg_catalog.pg_depend AS d",
                "JOIN pg_catalog.pg_class AS i ON i.oid = d.objid",
                f"WHERE i.relname = {_literal(names['index_name'])}",
                "  AND d.classid = 'pg_catalog.pg_class'::pg_catalog.regclass",
                "  AND d.refclassid = 'pg_catalog.pg_collation'::pg_catalog.regclass",
                "  AND d.refobjid::text = :'before_collation_oid'",
                "ORDER BY index_collation_dependency_preserved;",
            ]
        )
    final_schema, final_name = _final_identity(case, names)
    final_ref = f"{_quote_ident(final_schema)}.{_quote_ident(final_name)}"
    lines.extend(
        [
            "SELECT array_agg(sort_key ORDER BY sort_key COLLATE "
            + final_ref
            + ") = ARRAY['alpha', 'beta', 'gamma']::text[] AS collation_sort_verification",
            f"FROM public.{names['data_table']};",
        ]
    )
    return lines


def _cleanup(case: StatementRegressCase, names: Mapping[str, str]) -> list[str]:
    lines = ["RESET ROLE;", "RESET SESSION AUTHORIZATION;"]
    if _uses_table(case) and case.derived_axes["cleanup_mode"] == "DROP_DEPENDENT_OBJECTS_FIRST":
        if case.derived_axes.get("dependency_state") == "expression_index":
            lines.append(f"DROP INDEX IF EXISTS public.{names['index_name']};")
        lines.append(f"DROP TABLE IF EXISTS public.{names['data_table']} CASCADE;")
    boundary = case.derived_axes.get("boundary", "")
    if boundary == "pg_temp_move_out":
        lines.append(f"DROP COLLATION IF EXISTS pg_temp.{names['collation_ident']} CASCADE;")
    elif boundary == "pg_toast_move_out":
        lines.append(f"DROP COLLATION IF EXISTS pg_toast.{names['collation_ident']} CASCADE;")
    lines.extend(
        [
            f"DROP COLLATION IF EXISTS {names['new_qualified']} CASCADE;",
            f"DROP COLLATION IF EXISTS {names['moved_qualified']} CASCADE;",
            f"DROP COLLATION IF EXISTS {names['source_qualified']} CASCADE;",
            f"DROP SCHEMA IF EXISTS {names['target_schema']} CASCADE;",
            f"DROP SCHEMA IF EXISTS {names['source_schema']} CASCADE;",
            *_roles_cleanup(names),
            "RESET ALL;",
            "SELECT true AS cleanup_complete;",
        ]
    )
    if _uses_table(case):
        lines.append(f"DROP TABLE IF EXISTS public.{names['data_table']} CASCADE;")
    return lines


def render_alter_collation_case(plan: StatementRegressPlan, case: StatementRegressCase) -> str:
    """Render one reviewed ALTER COLLATION logical cell."""

    if plan.statement_key != "alter_collation" or case not in plan.cases:
        raise RemainingStatementRegressError(
            "ALTER COLLATION renderer received a foreign plan or case"
        )
    names = _names(case)
    lines = _header(plan, case) + [
        "",
        "-- 1. 清理本编号表、schema、collation 和角色，建立单会话确定性环境。",
        *_precleanup(case, names),
        "",
        "-- 2. 创建目标 collation、完整依赖表/列/索引以及权限真值表角色。",
        *_collation_fixture(case, names),
        *_branch_state_fixture(case, names),
        *_special_namespace_fixture(case, names),
        *_table_fixture(case, names),
    ]
    lines.extend(_privilege_fixture(case, names))
    if _needs_fixture(case) or case.derived_axes.get("provider_boundary") in {
        "default_collation",
        "system_c_collation",
    }:
        lines.extend(_capture_identity(case, names))
    action = _target_action(case, names)
    lines.extend(
        [
            "",
            "-- 3. 执行唯一目标 ALTER COLLATION 分支并锚定 SQLSTATE。",
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
            "-- 4. 以 pg_collation 稳定布尔谓词验证 identity、OID、owner 与 namespace。",
            "RESET ROLE;",
            *_identity_oracle(case, names),
            "",
            "-- 5. 验证版本刷新或事务回滚结果，不输出环境相关版本文本。",
            *_version_oracle(case, names),
            "SELECT true AS version_oracle_complete;",
            "",
            "-- 6. 验证表列或表达式索引依赖与排序仍可执行。",
            *_dependency_oracle(case, names),
            "",
            "-- 7. 按声明清理模式删除依赖、collation、schema 和角色并确认完成。",
            *_cleanup(case, names),
        ]
    )
    return "\n".join(lines).rstrip() + "\n"
