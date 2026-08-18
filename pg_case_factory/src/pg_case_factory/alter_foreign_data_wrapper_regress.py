"""PostgreSQL 18 ALTER FOREIGN DATA WRAPPER full conditional regress suite."""

from __future__ import annotations

import itertools
from typing import Any, Mapping

from .remaining_statement_regress import (
    FactorValueDecision,
    RemainingStatementRegressError,
    StatementRegressCase,
    StatementRegressPlan,
    _header,
)
from .statement_factor_cycle import StatementCycleEntry, StatementFactorCycleSnapshot


_CLEANUP = ("drop_fdw", "revert_handler", "revert_owner", "revert_rename", "revert_validator")


def _spec(
    group: str,
    branch: str,
    *,
    outcome: str = "success",
    sqlstate: str = "00000",
    **axes: str,
) -> dict[str, Any]:
    return {
        "group": group,
        "outcome": outcome,
        "axes": {
            "branch": branch,
            "expected_sqlstate": sqlstate,
            "actor": "superuser",
            "fdw_name_shape": "simple_id",
            **axes,
        },
    }


def _build_specs() -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for name_shape, handler, validator, option_op in itertools.product(
        ("simple_id", "quoted_id"),
        ("omitted", "specified_new_handler", "no_handler"),
        ("omitted", "specified_new_validator", "no_validator"),
        ("add_option", "set_option", "drop_option", "combined_operations"),
    ):
        specs.append(
            _spec(
                "change_clause_product",
                "change_handler_validator_options",
                fdw_name_shape=name_shape,
                handler_change=handler,
                validator_change=validator,
                options_operation=option_op,
            )
        )

    owner_forms = (
        ("specified_new_owner", "simple_id"),
        ("specified_new_owner", "quoted_id"),
        ("specified_current_role", "special_token"),
        ("specified_current_user", "special_token"),
        ("specified_session_user", "special_token"),
    )
    for name_shape, (target, owner_shape) in itertools.product(
        ("simple_id", "quoted_id"), owner_forms
    ):
        specs.append(
            _spec(
                "owner_target_product",
                "owner",
                fdw_name_shape=name_shape,
                owner_target=target,
                owner_name_shape=owner_shape,
            )
        )

    for name_shape, new_shape in itertools.product(
        ("simple_id", "quoted_id"), ("simple_id", "quoted_id")
    ):
        specs.append(
            _spec(
                "rename_target_product",
                "rename",
                fdw_name_shape=name_shape,
                new_name_shape=new_shape,
                rename_state="available",
            )
        )

    for branch in ("change_handler_validator_options", "owner", "rename"):
        specs.append(
            _spec(
                "missing_fdw_product",
                branch,
                outcome="expected_failure",
                sqlstate="42704",
                fdw_name_shape="nonexistent_name",
                object_state="missing",
            )
        )

    for branch, actor in itertools.product(
        ("change_handler_validator_options", "owner", "rename"),
        ("superuser", "non_superuser"),
    ):
        specs.append(
            _spec(
                "privilege_truth_product",
                branch,
                outcome="success" if actor == "superuser" else "expected_failure",
                sqlstate="00000" if actor == "superuser" else "42501",
                actor=actor,
            )
        )

    for dependency, state in itertools.product(
        ("handler", "validator"), ("function_exists", "function_not_exists")
    ):
        missing = state == "function_not_exists"
        specs.append(
            _spec(
                "function_existence_product",
                "change_handler_validator_options",
                outcome="expected_failure" if missing else "success",
                sqlstate="42883" if missing else "00000",
                dependency_function=dependency,
                function_state=state,
            )
        )

    for scope, compatibility in itertools.product(
        ("wrapper", "server", "user_mapping", "foreign_table"),
        ("compatible", "potentially_incompatible"),
    ):
        specs.append(
            _spec(
                "validator_compatibility_product",
                "change_handler_validator_options",
                validator_change="specified_new_validator",
                dependency_scope=scope,
                preexisting_compatibility=compatibility,
                validator_switch="no_validator_switch",
            )
        )
    specs.append(
        _spec(
            "validator_compatibility_product",
            "change_handler_validator_options",
            outcome="expected_failure",
            sqlstate="HV00D",
            validator_change="specified_new_validator",
            dependency_scope="wrapper",
            preexisting_compatibility="potentially_incompatible",
            validator_switch="switch_with_incompatible_options",
        )
    )

    for operation, option_shape in itertools.product(
        ("add_option", "set_option", "drop_option", "combined_operations"),
        ("valid_option", "invalid_option"),
    ):
        invalid_rejected = option_shape == "invalid_option" and operation in {
            "add_option",
            "set_option",
        }
        specs.append(
            _spec(
                "option_shape_operation_product",
                "change_handler_validator_options",
                outcome="expected_failure" if invalid_rejected else "success",
                sqlstate="HV00D" if invalid_rejected else "00000",
                options_operation=operation,
                option_name_shape=option_shape,
                validator_change="specified_new_validator",
            )
        )

    option_boundaries = (
        ("default_add", "add_option", "00000", "success"),
        ("quoted_option", "add_option", "00000", "success"),
        ("add_existing", "add_option", "42710", "expected_failure"),
        ("set_missing", "set_option", "42704", "expected_failure"),
        ("drop_missing", "drop_option", "42704", "expected_failure"),
        ("duplicate_names", "combined_operations", "42710", "expected_failure"),
    )
    for boundary, operation, state, outcome in option_boundaries:
        specs.append(
            _spec(
                "option_state_boundary_product",
                "change_handler_validator_options",
                outcome=outcome,
                sqlstate=state,
                option_boundary=boundary,
                options_operation=operation,
                option_name_shape="valid_option",
            )
        )

    owner_boundaries = (
        ("missing_simple", "nonexistent_role", "42704", "expected_failure"),
        ("missing_quoted", "nonexistent_role", "42704", "expected_failure"),
        ("existing_non_superuser", "simple_id", "42501", "expected_failure"),
        ("same_current_owner", "simple_id", "00000", "success"),
    )
    for boundary, shape, state, outcome in owner_boundaries:
        specs.append(
            _spec(
                "owner_boundary_product",
                "owner",
                outcome=outcome,
                sqlstate=state,
                owner_boundary=boundary,
                owner_target="specified_new_owner" if boundary != "same_current_owner" else "specified_current_user",
                owner_name_shape=shape,
            )
        )

    for conflict_kind, new_shape in itertools.product(
        ("other_fdw", "same_name"), ("simple_id", "quoted_id")
    ):
        specs.append(
            _spec(
                "rename_conflict_product",
                "rename",
                outcome="expected_failure",
                sqlstate="42710",
                rename_state=conflict_kind,
                new_name_shape=new_shape,
            )
        )

    for handler_state in ("with_handler", "no_handler"):
        specs.append(
            _spec(
                "handler_access_product",
                "change_handler_validator_options",
                handler_change="specified_new_handler" if handler_state == "with_handler" else "no_handler",
                handler_access=handler_state,
                dependency_scope="foreign_table",
            )
        )

    signatures = (
        ("handler_wrong_return", "expected_failure", "42809"),
        ("handler_wrong_args", "expected_failure", "42883"),
        ("validator_ignored_return", "success", "00000"),
        ("validator_wrong_args", "expected_failure", "42883"),
    )
    for signature, outcome, state in signatures:
        specs.append(
            _spec(
                "support_signature_product",
                "change_handler_validator_options",
                outcome=outcome,
                sqlstate=state,
                support_signature=signature,
            )
        )

    parser_rows = (
        "empty_fdw_name",
        "qualified_fdw_name",
        "three_part_fdw_name",
        "missing_change_clause",
        "owner_qualified_target",
        "owner_missing_target",
        "rename_qualified_target",
        "rename_missing_target",
        "rename_unquoted_reserved",
        "options_without_parentheses",
        "reversed_clause_order",
        "trailing_tokens",
    )
    for boundary in parser_rows:
        specs.append(
            _spec(
                "parser_boundary_product",
                "change_handler_validator_options",
                outcome="expected_failure",
                sqlstate="42601",
                parser_boundary=boundary,
            )
        )

    for branch in ("change_handler_validator_options", "owner", "rename"):
        specs.append(
            _spec(
                "transactional_rollback_product",
                branch,
                transaction="rollback",
            )
        )

    for clause in ("handler", "no_handler", "validator", "no_validator"):
        specs.append(
            _spec(
                "single_clause_product",
                "change_handler_validator_options",
                single_clause=clause,
                handler_change=("specified_new_handler" if clause == "handler" else "no_handler" if clause == "no_handler" else "omitted"),
                validator_change=("specified_new_validator" if clause == "validator" else "no_validator" if clause == "no_validator" else "omitted"),
            )
        )
    return specs


def _factor_tokens(axes: Mapping[str, str], outcome: str, ordinal: int) -> tuple[str, ...]:
    branch = axes["branch"]
    missing = axes.get("object_state") == "missing"
    actor = axes.get("actor", "superuser")
    values: dict[str, str] = {
        "statement_branch": f"branch_{branch}",
        "object_state": "not_exists" if missing else "exists",
        "expected_status": "failure" if outcome == "expected_failure" else "success",
        "alter_action": {
            "change_handler_validator_options": "change_handler_validator_options",
            "owner": "owner",
            "rename": "rename",
        }[branch],
        "fdw_name_shape": axes.get("fdw_name_shape", "simple_id"),
        "privilege_level": "non_superuser" if actor == "non_superuser" else "superuser",
        "nonexistent_fdw": "fdw_missing" if missing else "fdw_exists",
        "non_superuser_attempt": "non_superuser_execution" if actor == "non_superuser" else "superuser_execution",
        "verification_mode": (
            "error_assertion"
            if outcome == "expected_failure"
            else "effect_query"
            if axes.get("handler_access") is not None
            else "pg_foreign_data_wrapper_catalog"
        ),
        "cleanup_mode": _CLEANUP[(ordinal - 1) % len(_CLEANUP)],
    }
    if branch == "change_handler_validator_options":
        if "handler_change" in axes:
            values["handler_change"] = axes["handler_change"]
        if "validator_change" in axes:
            values["validator_change"] = axes["validator_change"]
        if "options_operation" in axes:
            values["options_operation"] = axes["options_operation"]
        if "option_name_shape" in axes:
            values["option_name_shape"] = axes["option_name_shape"]
        if "preexisting_compatibility" in axes:
            values["preexisting_options_compatibility"] = axes["preexisting_compatibility"]
        if "validator_switch" in axes:
            values["validator_switch_option_incompatibility"] = axes["validator_switch"]
        if "handler_access" in axes:
            values["no_handler_access_limit"] = axes["handler_access"]
        if axes.get("dependency_function") == "handler":
            exists = axes["function_state"] == "function_exists"
            values["handler_function_existence"] = "function_exists" if exists else "function_not_exists"
            values["nonexistent_handler_function"] = "function_exists" if exists else "function_missing"
        if axes.get("dependency_function") == "validator":
            exists = axes["function_state"] == "function_exists"
            values["validator_function_existence"] = "function_exists" if exists else "function_not_exists"
            values["nonexistent_validator_function"] = "function_exists" if exists else "function_missing"
    if branch == "owner":
        if "owner_target" in axes:
            values["owner_target"] = axes["owner_target"]
        shape = axes.get("owner_name_shape")
        if shape in {"simple_id", "quoted_id", "nonexistent_role"}:
            values["owner_name_shape"] = shape
        boundary = axes.get("owner_boundary")
        if boundary in {"missing_simple", "missing_quoted"}:
            values["nonexistent_owner_role"] = "role_missing"
            values["owner_name_shape"] = "nonexistent_role"
        elif axes.get("owner_target") == "specified_new_owner":
            values["nonexistent_owner_role"] = "role_exists_superuser"
    if branch == "rename":
        if "new_name_shape" in axes:
            values["new_name_shape"] = (
                "duplicate_name"
                if axes.get("rename_state") in {"other_fdw", "same_name"}
                else axes["new_name_shape"]
            )
        values["duplicate_new_name"] = (
            "same_name_conflict"
            if axes.get("rename_state") in {"other_fdw", "same_name"}
            else "no_conflict"
        )
    return tuple(f"{key}={value}" for key, value in values.items())


def _build_cases() -> tuple[StatementRegressCase, ...]:
    cases: list[StatementRegressCase] = []
    for ordinal, spec in enumerate(_build_specs(), start=1):
        axes = dict(spec["axes"])
        case_id = f"ALTERFOREIGNDATAWRAPPER{ordinal:05d}"
        cases.append(
            StatementRegressCase(
                ordinal=ordinal,
                case_id=case_id,
                sql_filename=f"{case_id}.sql",
                object_prefix=f"alterforeigndatawrapper_{ordinal:05d}_",
                case_group=str(spec["group"]),
                case_type="expected_failure" if spec["outcome"] == "expected_failure" else "success",
                outcome=str(spec["outcome"]),
                execution_profile="same_session_multiphase",
                derived_axes=axes,
                factor_values=_factor_tokens(axes, str(spec["outcome"]), ordinal),
                combination_strategy="full PostgreSQL 18 branch-applicable conditional products; no sampling",
                description="ALTER FOREIGN DATA WRAPPER conditional product: "
                + ", ".join(f"{key}={value}" for key, value in sorted(axes.items())),
                expected_anchor=f"SQLSTATE {axes['expected_sqlstate']}; pg_foreign_data_wrapper catalog/effect oracle",
            )
        )
    return tuple(cases)


def _factor_decisions(
    entry: StatementCycleEntry,
    cases: tuple[StatementRegressCase, ...],
) -> tuple[FactorValueDecision, ...]:
    by_id = {case.case_id: case for case in cases}
    rows: list[FactorValueDecision] = []
    for factor in entry.factors:
        for value, row_id in zip(factor.values, factor.row_ids):
            token = f"{factor.name}={value}"
            witnesses = tuple(case.case_id for case in cases if token in case.factor_values)
            if not witnesses:
                raise RemainingStatementRegressError(
                    f"ALTER FOREIGN DATA WRAPPER missing witness for {token}"
                )
            failure_only = all(by_id[case_id].outcome == "expected_failure" for case_id in witnesses)
            rows.append(
                FactorValueDecision(
                    row_id=row_id,
                    factor=factor.name,
                    value=value,
                    disposition="expected_failure" if failure_only else "covered",
                    reason="isolated PostgreSQL rejection" if failure_only else None,
                    case_ids=witnesses,
                )
            )
    return tuple(rows)


def build_alter_foreign_data_wrapper_plan(
    snapshot: StatementFactorCycleSnapshot,
    entry: StatementCycleEntry,
) -> StatementRegressPlan:
    cases = _build_cases()
    if len(cases) != 155:
        raise RemainingStatementRegressError(
            f"ALTER FOREIGN DATA WRAPPER expected 155 cases, found {len(cases)}"
        )
    return StatementRegressPlan(
        statement_key="alter_foreign_data_wrapper",
        file_prefix="ALTERFOREIGNDATAWRAPPER",
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


def _qi(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _lit(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _names(case: StatementRegressCase) -> dict[str, str]:
    p = case.object_prefix
    shape = case.derived_axes.get("fdw_name_shape", "simple_id")
    raw = p + "fdw" if shape != "quoted_id" else f"FDW {case.ordinal:05d}"
    source = _qi(raw) if shape == "quoted_id" else raw
    if shape == "nonexistent_name":
        raw = p + "missing_fdw"
        source = raw
    new_shape = case.derived_axes.get("new_name_shape", "simple_id")
    new_raw = p + "renamed_fdw" if new_shape != "quoted_id" else f"Renamed FDW {case.ordinal:05d}"
    new_name = _qi(new_raw) if new_shape == "quoted_id" else new_raw
    if case.derived_axes.get("rename_state") == "same_name":
        new_raw, new_name = raw, source
    owner_shape = case.derived_axes.get("owner_name_shape", "simple_id")
    owner_raw = p + "new_owner" if owner_shape != "quoted_id" else f"FDW Owner {case.ordinal:05d}"
    owner = _qi(owner_raw) if owner_shape == "quoted_id" else owner_raw
    return {
        "p": p,
        "fdw_raw": raw,
        "fdw": source,
        "new_raw": new_raw,
        "new": new_name,
        "conflict_raw": new_raw,
        "conflict": new_name,
        "owner_raw": owner_raw,
        "owner": owner,
        "quoted_owner_raw": f"FDW Quoted Owner {case.ordinal:05d}",
        "quoted_owner": _qi(f"FDW Quoted Owner {case.ordinal:05d}"),
        "intruder": p + "intruder",
        "server": p + "server",
        "foreign_table": p + "foreign_table",
        "handler": p + "handler",
        "validator": p + "validator",
        "valid_validator": p + "valid_validator",
        "missing_handler": p + "missing_handler",
        "missing_validator": p + "missing_validator",
    }


def _columns() -> str:
    return (
        "id bigint NOT NULL, code text NOT NULL, payload jsonb NOT NULL, "
        "created_at timestamp with time zone NOT NULL, "
        "status smallint NOT NULL CHECK (status BETWEEN 0 AND 9)"
    )


def _options_for(operation: str) -> tuple[list[tuple[str, str]], str]:
    if operation == "add_option":
        return [("fdw_startup_cost", "100")], "OPTIONS (ADD fdw_tuple_cost '0.02')"
    if operation == "set_option":
        return [("fdw_startup_cost", "100")], "OPTIONS (SET fdw_startup_cost '200')"
    if operation == "drop_option":
        return [("fdw_startup_cost", "100")], "OPTIONS (DROP fdw_startup_cost)"
    return [
        ("fdw_startup_cost", "100"),
        ("fdw_tuple_cost", "0.01"),
    ], "OPTIONS (ADD extensions 'hstore', SET fdw_startup_cost '200', DROP fdw_tuple_cost)"


def _create_fdw(
    name: str,
    *,
    handler: bool = False,
    validator: str | None = None,
    options: list[tuple[str, str]] | None = None,
) -> str:
    pieces = [f"CREATE FOREIGN DATA WRAPPER {name}"]
    if handler:
        pieces.append("HANDLER public.postgres_fdw_handler")
    if validator is not None:
        pieces.append(f"VALIDATOR {validator}")
    if options:
        rendered = ", ".join(f"{key} {_lit(value)}" for key, value in options)
        pieces.append(f"OPTIONS ({rendered})")
    return " ".join(pieces) + ";"


def _precleanup(n: Mapping[str, str]) -> list[str]:
    return [
        "RESET ROLE;",
        "RESET search_path;",
        f"DROP SERVER IF EXISTS {n['server']} CASCADE;",
        f"DROP FOREIGN DATA WRAPPER IF EXISTS {n['fdw']} CASCADE;",
        f"DROP FOREIGN DATA WRAPPER IF EXISTS {n['new']} CASCADE;",
        "DROP EXTENSION IF EXISTS postgres_fdw CASCADE;",
        f"DROP FUNCTION IF EXISTS public.{n['handler']}() CASCADE;",
        f"DROP FUNCTION IF EXISTS public.{n['handler']}(integer) CASCADE;",
        f"DROP FUNCTION IF EXISTS public.{n['validator']}(text[], oid) CASCADE;",
        f"DROP FUNCTION IF EXISTS public.{n['validator']}(text[]) CASCADE;",
        f"DROP FUNCTION IF EXISTS public.{n['valid_validator']}(text[], oid) CASCADE;",
        f"DROP ROLE IF EXISTS {n['intruder']};",
        f"DROP ROLE IF EXISTS {n['owner']};",
        f"DROP ROLE IF EXISTS {n['quoted_owner']};",
    ]


def _base_fixture(n: Mapping[str, str]) -> list[str]:
    return [
        "CREATE EXTENSION postgres_fdw;",
        f"CREATE ROLE {n['owner']} SUPERUSER;",
        f"CREATE ROLE {n['quoted_owner']} SUPERUSER;",
        f"CREATE ROLE {n['intruder']};",
        "SET search_path TO public, pg_catalog;",
        f"CREATE FUNCTION public.{n['valid_validator']}(text[], oid) RETURNS void LANGUAGE plpgsql AS $body$ "
        "DECLARE item text; BEGIN FOREACH item IN ARRAY $1 LOOP "
        "IF pg_catalog.split_part(item, '=', 1) = 'invalid_option' "
        "OR pg_catalog.split_part(item, '=', 1) LIKE 'legacy%' THEN "
        "RAISE EXCEPTION 'invalid option %', pg_catalog.split_part(item, '=', 1) USING ERRCODE='HV00D'; "
        "END IF; END LOOP; END $body$;",
    ]


def _foreign_dependencies(
    n: Mapping[str, str],
    *,
    server_option: tuple[str, str] | None = None,
    mapping_option: tuple[str, str] | None = None,
    table_option: tuple[str, str] | None = None,
) -> list[str]:
    server_suffix = "" if server_option is None else f" OPTIONS ({server_option[0]} {_lit(server_option[1])})"
    lines = [f"CREATE SERVER {n['server']} FOREIGN DATA WRAPPER {n['fdw']}{server_suffix};"]
    if mapping_option is not None:
        lines.append(
            f"CREATE USER MAPPING FOR CURRENT_USER SERVER {n['server']} "
            f"OPTIONS ({mapping_option[0]} {_lit(mapping_option[1])});"
        )
    table_suffix = "" if table_option is None else f" OPTIONS ({table_option[0]} {_lit(table_option[1])})"
    lines.append(
        f"CREATE FOREIGN TABLE {n['foreign_table']} ({_columns()}) SERVER {n['server']}{table_suffix};"
    )
    return lines


def _fixture(case: StatementRegressCase, n: Mapping[str, str]) -> list[str]:
    a = case.derived_axes
    group = case.case_group
    lines = _base_fixture(n)
    if a.get("object_state") == "missing":
        return lines

    if group == "change_clause_product":
        options, _ = _options_for(a["options_operation"])
        lines.append(
            _create_fdw(
                n["fdw"],
                handler=a["handler_change"] != "specified_new_handler",
                validator=(
                    f"public.{n['valid_validator']}"
                    if a["validator_change"] != "specified_new_validator"
                    else None
                ),
                options=options,
            )
        )
    elif group in {"owner_target_product", "rename_target_product", "privilege_truth_product", "transactional_rollback_product"}:
        lines.append(_create_fdw(n["fdw"], handler=True, validator=f"public.{n['valid_validator']}", options=[("fdw_startup_cost", "100")]))
    elif group == "function_existence_product":
        lines.append(_create_fdw(n["fdw"]))
    elif group == "validator_compatibility_product":
        compatibility = a["preexisting_compatibility"]
        scope = a["dependency_scope"]
        valid = compatibility == "compatible"
        wrapper_options = [("fdw_startup_cost", "100")] if scope == "wrapper" and valid else [("legacy_option", "legacy")] if scope == "wrapper" else None
        lines.append(_create_fdw(n["fdw"], handler=True, options=wrapper_options))
        if scope != "wrapper":
            option = {
                "server": ("host", "localhost") if valid else ("legacy_server", "legacy"),
                "user_mapping": ("user", "tester") if valid else ("legacy_mapping", "legacy"),
                "foreign_table": ("schema_name", "public") if valid else ("legacy_table", "legacy"),
            }[scope]
            lines.extend(
                _foreign_dependencies(
                    n,
                    server_option=option if scope == "server" else None,
                    mapping_option=option if scope == "user_mapping" else None,
                    table_option=option if scope == "foreign_table" else None,
                )
            )
    elif group == "option_shape_operation_product":
        operation = a["options_operation"]
        invalid = a["option_name_shape"] == "invalid_option"
        if invalid and operation in {"set_option", "drop_option", "combined_operations"}:
            options = [("invalid_option", "old")]
        else:
            options, _ = _options_for(operation)
        lines.append(_create_fdw(n["fdw"], handler=True, validator=None if invalid else f"public.{n['valid_validator']}", options=options))
    elif group == "option_state_boundary_product":
        boundary = a["option_boundary"]
        if boundary in {"add_existing", "duplicate_names"}:
            options = [("fdw_startup_cost", "100")]
        else:
            options = []
        lines.append(_create_fdw(n["fdw"], handler=True, options=options))
    elif group == "owner_boundary_product":
        lines.append(_create_fdw(n["fdw"], handler=True))
    elif group == "rename_conflict_product":
        lines.append(_create_fdw(n["fdw"], handler=True))
        if a["rename_state"] == "other_fdw":
            lines.append(_create_fdw(n["conflict"], handler=True))
    elif group == "handler_access_product":
        lines.append(_create_fdw(n["fdw"], handler=True, validator=f"public.{n['valid_validator']}"))
        lines.extend(
            _foreign_dependencies(
                n,
                server_option=("host", "localhost"),
                table_option=("schema_name", "public"),
            )
        )
    elif group == "support_signature_product":
        lines.append(_create_fdw(n["fdw"]))
        signature = a["support_signature"]
        if signature == "handler_wrong_return":
            lines.append(f"CREATE FUNCTION public.{n['handler']}() RETURNS integer LANGUAGE sql AS 'SELECT 1';")
        elif signature == "handler_wrong_args":
            lines.append(f"CREATE FUNCTION public.{n['handler']}(integer) RETURNS integer LANGUAGE sql AS 'SELECT $1';")
        elif signature == "validator_ignored_return":
            lines.append(f"CREATE FUNCTION public.{n['validator']}(text[], oid) RETURNS integer LANGUAGE sql AS 'SELECT 1';")
        else:
            lines.append(f"CREATE FUNCTION public.{n['validator']}(text[]) RETURNS void LANGUAGE plpgsql AS $body$ BEGIN NULL; END $body$;")
    elif group == "single_clause_product":
        clause = a["single_clause"]
        lines.append(
            _create_fdw(
                n["fdw"],
                handler=clause != "handler",
                validator=f"public.{n['valid_validator']}" if clause != "validator" else None,
            )
        )
    else:
        lines.append(_create_fdw(n["fdw"], handler=True, validator=f"public.{n['valid_validator']}"))
    return lines


def _owner_target(case: StatementRegressCase, n: Mapping[str, str]) -> str:
    boundary = case.derived_axes.get("owner_boundary")
    if boundary == "missing_simple":
        return n["p"] + "missing_owner"
    if boundary == "missing_quoted":
        return _qi(f"Missing FDW Owner {case.ordinal:05d}")
    if boundary == "existing_non_superuser":
        return n["intruder"]
    target = case.derived_axes.get("owner_target", "specified_new_owner")
    return {
        "specified_new_owner": n["owner"],
        "specified_current_role": "CURRENT_ROLE",
        "specified_current_user": "CURRENT_USER",
        "specified_session_user": "SESSION_USER",
    }[target]


def _core_change_clause(case: StatementRegressCase, n: Mapping[str, str]) -> str:
    a = case.derived_axes
    clauses: list[str] = []
    handler = a["handler_change"]
    validator = a["validator_change"]
    if handler == "specified_new_handler":
        clauses.append("HANDLER public.postgres_fdw_handler")
    elif handler == "no_handler":
        clauses.append("NO HANDLER")
    if validator == "specified_new_validator":
        clauses.append(f"VALIDATOR public.{n['valid_validator']}")
    elif validator == "no_validator":
        clauses.append("NO VALIDATOR")
    _, option_clause = _options_for(a["options_operation"])
    clauses.append(option_clause)
    return " ".join(clauses)


def _target(case: StatementRegressCase, n: Mapping[str, str]) -> str:
    a = case.derived_axes
    group = case.case_group
    branch = a["branch"]
    if group == "parser_boundary_product":
        boundary = a["parser_boundary"]
        return {
            "empty_fdw_name": "ALTER FOREIGN DATA WRAPPER RENAME TO x;",
            "qualified_fdw_name": f"ALTER FOREIGN DATA WRAPPER public.{n['fdw']} RENAME TO x;",
            "three_part_fdw_name": f"ALTER FOREIGN DATA WRAPPER current_database.public.{n['fdw']} RENAME TO x;",
            "missing_change_clause": f"ALTER FOREIGN DATA WRAPPER {n['fdw']};",
            "owner_qualified_target": f"ALTER FOREIGN DATA WRAPPER {n['fdw']} OWNER TO public.{n['owner']};",
            "owner_missing_target": f"ALTER FOREIGN DATA WRAPPER {n['fdw']} OWNER TO;",
            "rename_qualified_target": f"ALTER FOREIGN DATA WRAPPER {n['fdw']} RENAME TO public.x;",
            "rename_missing_target": f"ALTER FOREIGN DATA WRAPPER {n['fdw']} RENAME TO;",
            "rename_unquoted_reserved": f"ALTER FOREIGN DATA WRAPPER {n['fdw']} RENAME TO SELECT;",
            "options_without_parentheses": f"ALTER FOREIGN DATA WRAPPER {n['fdw']} OPTIONS ADD x '1';",
            "reversed_clause_order": f"ALTER FOREIGN DATA WRAPPER {n['fdw']} OPTIONS (ADD fdw_startup_cost '1') HANDLER public.postgres_fdw_handler;",
            "trailing_tokens": f"ALTER FOREIGN DATA WRAPPER {n['fdw']} NO VALIDATOR unexpected_tokens;",
        }[boundary]
    if group == "change_clause_product":
        return f"ALTER FOREIGN DATA WRAPPER {n['fdw']} {_core_change_clause(case, n)};"
    if group == "function_existence_product":
        dependency = a["dependency_function"]
        if dependency == "handler":
            function = "public.postgres_fdw_handler" if a["function_state"] == "function_exists" else f"public.{n['missing_handler']}"
            clause = f"HANDLER {function}"
        else:
            function = f"public.{n['valid_validator']}" if a["function_state"] == "function_exists" else f"public.{n['missing_validator']}"
            clause = f"VALIDATOR {function}"
        return f"ALTER FOREIGN DATA WRAPPER {n['fdw']} {clause};"
    if group == "validator_compatibility_product":
        clause = f"VALIDATOR public.{n['valid_validator']}"
        if a["validator_switch"] == "switch_with_incompatible_options":
            clause += " OPTIONS (ADD fdw_startup_cost '200')"
        return f"ALTER FOREIGN DATA WRAPPER {n['fdw']} {clause};"
    if group == "option_shape_operation_product":
        operation = a["options_operation"]
        invalid = a["option_name_shape"] == "invalid_option"
        key = "invalid_option" if invalid else "fdw_startup_cost"
        if operation == "add_option":
            clause = f"OPTIONS (ADD {'fdw_tuple_cost' if not invalid else key} '200')"
        elif operation == "set_option":
            clause = f"OPTIONS (SET {key} '200')"
        elif operation == "drop_option":
            clause = f"OPTIONS (DROP {key})"
        elif invalid:
            clause = "OPTIONS (DROP invalid_option, ADD fdw_startup_cost '200')"
        else:
            clause = "OPTIONS (ADD extensions 'hstore', SET fdw_startup_cost '200', DROP fdw_tuple_cost)"
        validator = f"VALIDATOR public.{n['valid_validator']} " if invalid else ""
        return f"ALTER FOREIGN DATA WRAPPER {n['fdw']} {validator}{clause};"
    if group == "option_state_boundary_product":
        boundary = a["option_boundary"]
        clause = {
            "default_add": "OPTIONS (extensions 'hstore')",
            "quoted_option": "OPTIONS (ADD \"Mixed Option\" 'value')",
            "add_existing": "OPTIONS (ADD fdw_startup_cost '200')",
            "set_missing": "OPTIONS (SET fdw_tuple_cost '0.02')",
            "drop_missing": "OPTIONS (DROP fdw_tuple_cost)",
            "duplicate_names": "OPTIONS (ADD duplicate_option 'one', ADD duplicate_option 'two')",
        }[boundary]
        return f"ALTER FOREIGN DATA WRAPPER {n['fdw']} {clause};"
    if group == "handler_access_product":
        clause = "HANDLER public.postgres_fdw_handler" if a["handler_access"] == "with_handler" else "NO HANDLER"
        return f"ALTER FOREIGN DATA WRAPPER {n['fdw']} {clause};"
    if group == "support_signature_product":
        signature = a["support_signature"]
        if signature.startswith("handler"):
            return f"ALTER FOREIGN DATA WRAPPER {n['fdw']} HANDLER public.{n['handler']};"
        return f"ALTER FOREIGN DATA WRAPPER {n['fdw']} VALIDATOR public.{n['validator']};"
    if group == "single_clause_product":
        clause = {
            "handler": "HANDLER public.postgres_fdw_handler",
            "no_handler": "NO HANDLER",
            "validator": f"VALIDATOR public.{n['valid_validator']}",
            "no_validator": "NO VALIDATOR",
        }[a["single_clause"]]
        return f"ALTER FOREIGN DATA WRAPPER {n['fdw']} {clause};"
    if branch == "owner":
        return f"ALTER FOREIGN DATA WRAPPER {n['fdw']} OWNER TO {_owner_target(case, n)};"
    if branch == "rename":
        return f"ALTER FOREIGN DATA WRAPPER {n['fdw']} RENAME TO {n['new']};"
    return f"ALTER FOREIGN DATA WRAPPER {n['fdw']} OPTIONS (ADD fdw_tuple_cost '0.02');"


def _capture(n: Mapping[str, str]) -> list[str]:
    name = _lit(n["fdw_raw"])
    return [
        "SELECT",
        f"    COALESCE((SELECT oid::text FROM pg_catalog.pg_foreign_data_wrapper WHERE fdwname={name}), '0') AS before_fdw_oid,",
        f"    COALESCE((SELECT fdwowner::text FROM pg_catalog.pg_foreign_data_wrapper WHERE fdwname={name}), '0') AS before_fdw_owner,",
        f"    COALESCE((SELECT fdwhandler::text FROM pg_catalog.pg_foreign_data_wrapper WHERE fdwname={name}), '0') AS before_fdw_handler,",
        f"    COALESCE((SELECT fdwvalidator::text FROM pg_catalog.pg_foreign_data_wrapper WHERE fdwname={name}), '0') AS before_fdw_validator,",
        f"    COALESCE((SELECT pg_catalog.array_to_string(fdwoptions, E'\\n') FROM pg_catalog.pg_foreign_data_wrapper WHERE fdwname={name}), '<NULL>') AS before_fdw_options",
        "FROM (VALUES (true)) AS capture_anchor(dummy)",
        "ORDER BY before_fdw_oid;",
        r"\gset",
    ]


def _unchanged_oracle(n: Mapping[str, str]) -> list[str]:
    return [
        "SELECT COALESCE(pg_catalog.bool_and(",
        "    fdwowner::text = :'before_fdw_owner'",
        "    AND fdwhandler::text = :'before_fdw_handler'",
        "    AND fdwvalidator::text = :'before_fdw_validator'",
        "    AND COALESCE(pg_catalog.array_to_string(fdwoptions, E'\\n'), '<NULL>') = :'before_fdw_options'",
        "), :'before_fdw_oid' = '0') AS failed_or_rolled_back_fdw_unchanged",
        "FROM pg_catalog.pg_foreign_data_wrapper",
        "WHERE :'before_fdw_oid' <> '0' AND oid=:'before_fdw_oid'::oid",
        "ORDER BY failed_or_rolled_back_fdw_unchanged;",
    ]


def _success_change_conditions(case: StatementRegressCase) -> list[str]:
    a = case.derived_axes
    conditions = ["oid=:'before_fdw_oid'::oid"]
    if case.case_group == "change_clause_product":
        handler = a["handler_change"]
        validator = a["validator_change"]
        conditions.append("fdwhandler <> 0" if handler == "specified_new_handler" else "fdwhandler = 0" if handler == "no_handler" else "fdwhandler::text=:'before_fdw_handler'")
        conditions.append("fdwvalidator <> 0" if validator == "specified_new_validator" else "fdwvalidator = 0" if validator == "no_validator" else "fdwvalidator::text=:'before_fdw_validator'")
        operation = a["options_operation"]
        if operation == "add_option":
            conditions.append("'fdw_tuple_cost=0.02'=ANY(fdwoptions)")
        elif operation == "set_option":
            conditions.append("'fdw_startup_cost=200'=ANY(fdwoptions)")
        elif operation == "drop_option":
            conditions.append("NOT EXISTS (SELECT 1 FROM pg_catalog.unnest(fdwoptions) AS o(v) WHERE v LIKE 'fdw_startup_cost=%')")
        else:
            conditions.extend(("'extensions=hstore'=ANY(fdwoptions)", "'fdw_startup_cost=200'=ANY(fdwoptions)", "NOT EXISTS (SELECT 1 FROM pg_catalog.unnest(fdwoptions) AS o(v) WHERE v LIKE 'fdw_tuple_cost=%')"))
    elif case.case_group in {"function_existence_product", "support_signature_product"}:
        if a.get("dependency_function") == "handler" or a.get("support_signature", "").startswith("handler"):
            conditions.append("fdwhandler <> 0")
        else:
            conditions.append("fdwvalidator <> 0")
    elif case.case_group == "validator_compatibility_product":
        conditions.append("fdwvalidator <> 0")
        if a["preexisting_compatibility"] == "potentially_incompatible":
            conditions.append("true")
    elif case.case_group == "option_shape_operation_product":
        invalid = a["option_name_shape"] == "invalid_option"
        operation = a["options_operation"]
        if invalid and operation in {"drop_option", "combined_operations"}:
            conditions.append("NOT ('invalid_option=old'=ANY(COALESCE(fdwoptions, ARRAY[]::text[])))")
        elif operation == "drop_option":
            conditions.append("fdwoptions IS NULL OR NOT ('fdw_startup_cost=100'=ANY(fdwoptions))")
        else:
            conditions.append("fdwoptions IS NOT NULL")
    elif case.case_group == "handler_access_product":
        conditions.append("fdwhandler <> 0" if a["handler_access"] == "with_handler" else "fdwhandler = 0")
    elif case.case_group == "single_clause_product":
        conditions.append("true")
    else:
        conditions.append("true")
    return conditions


def _oracle(case: StatementRegressCase, n: Mapping[str, str]) -> list[str]:
    a = case.derived_axes
    if case.outcome == "expected_failure" or a.get("transaction") == "rollback":
        return _unchanged_oracle(n)
    if a["branch"] == "rename":
        return [
            f"SELECT oid=:'before_fdw_oid'::oid AND fdwname={_lit(n['new_raw'])} AS rename_catalog_matches",
            "FROM pg_catalog.pg_foreign_data_wrapper",
            f"WHERE fdwname={_lit(n['new_raw'])}",
            "ORDER BY rename_catalog_matches;",
        ]
    if a["branch"] == "owner":
        expected = n["owner_raw"] if a.get("owner_target", "specified_new_owner") == "specified_new_owner" else None
        if a.get("owner_boundary") == "same_current_owner" or expected is None:
            owner_expr = "SESSION_USER"
        else:
            owner_expr = _lit(expected)
        return [
            f"SELECT oid=:'before_fdw_oid'::oid AND pg_catalog.pg_get_userbyid(fdwowner)={owner_expr} AS owner_catalog_matches",
            "FROM pg_catalog.pg_foreign_data_wrapper",
            "WHERE oid=:'before_fdw_oid'::oid",
            "ORDER BY owner_catalog_matches;",
        ]
    conditions = "\n    AND ".join(_success_change_conditions(case))
    return [
        f"SELECT {conditions} AS fdw_catalog_matches",
        "FROM pg_catalog.pg_foreign_data_wrapper",
        "WHERE oid=:'before_fdw_oid'::oid",
        "ORDER BY fdw_catalog_matches;",
    ]


def _cleanup(n: Mapping[str, str]) -> list[str]:
    return [
        "RESET ROLE;",
        "RESET search_path;",
        f"DROP SERVER IF EXISTS {n['server']} CASCADE;",
        f"DROP FOREIGN DATA WRAPPER IF EXISTS {n['fdw']} CASCADE;",
        f"DROP FOREIGN DATA WRAPPER IF EXISTS {n['new']} CASCADE;",
        "DROP EXTENSION IF EXISTS postgres_fdw CASCADE;",
        f"DROP FUNCTION IF EXISTS public.{n['handler']}() CASCADE;",
        f"DROP FUNCTION IF EXISTS public.{n['handler']}(integer) CASCADE;",
        f"DROP FUNCTION IF EXISTS public.{n['validator']}(text[], oid) CASCADE;",
        f"DROP FUNCTION IF EXISTS public.{n['validator']}(text[]) CASCADE;",
        f"DROP FUNCTION IF EXISTS public.{n['valid_validator']}(text[], oid) CASCADE;",
        f"DROP ROLE IF EXISTS {n['intruder']};",
        f"DROP ROLE IF EXISTS {n['owner']};",
        f"DROP ROLE IF EXISTS {n['quoted_owner']};",
        "SELECT",
        "    NOT EXISTS (SELECT 1 FROM pg_catalog.pg_foreign_data_wrapper",
        f"                WHERE fdwname IN ({_lit(n['fdw_raw'])}, {_lit(n['new_raw'])}))",
        "    AND NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles",
        f"                    WHERE rolname IN ({_lit(n['owner_raw'])}, {_lit(n['quoted_owner_raw'])}, {_lit(n['intruder'])})) AS cleanup_complete",
        "FROM (VALUES (true)) AS cleanup_anchor(dummy)",
        "ORDER BY cleanup_complete;",
    ]


def render_alter_foreign_data_wrapper_case(
    plan: StatementRegressPlan,
    case: StatementRegressCase,
) -> str:
    n = _names(case)
    a = case.derived_axes
    lines = _header(plan, case) + [
        "",
        "-- 1. Header and immutable trace metadata are complete above.",
        "",
        "-- 2. Session settings are explicit and reset during cleanup.",
        "",
        "-- 3. Idempotent pre-cleanup.",
        *_precleanup(n),
        "",
        "-- 4. FDW, role, support-function, server, and foreign-table fixture.",
        *_fixture(case, n),
        "",
        "-- 5. Fixture is complete and each failure has one primary cause.",
        "SELECT true AS fixture_ready FROM (VALUES (true)) AS fixture_anchor(dummy) ORDER BY fixture_ready;",
        "",
        "-- 6. Capture FDW identity, owner, handler, validator, and options.",
        *_capture(n),
        "",
        "-- 7. Select the declared executor.",
    ]
    if a.get("actor") == "non_superuser":
        lines.append(f"SET ROLE {n['intruder']};")
    lines.extend(["", "-- 8. Primary target statement (exactly one coverage-credit operation)."])
    if a.get("transaction") == "rollback":
        lines.append("BEGIN;")
    lines.extend(
        [
            r"\set ON_ERROR_STOP off",
            _target(case, n),
            r"\set alter_fdw_sqlstate :SQLSTATE",
            r"\set ON_ERROR_STOP on",
            "",
            "-- 9. SQLSTATE and primary-result oracle.",
            f"SELECT :'alter_fdw_sqlstate' = {_lit(a['expected_sqlstate'])} AS expected_SQLSTATE;",
        ]
    )
    if a.get("transaction") == "rollback":
        lines.append("ROLLBACK;")
    lines.append("RESET ROLE;")
    if case.case_group == "handler_access_product" and a["handler_access"] == "no_handler":
        lines.extend(
            [
                r"\set ON_ERROR_STOP off",
                f"SELECT count(*) FROM {n['foreign_table']};",
                r"\set fdw_access_sqlstate :SQLSTATE",
                r"\set ON_ERROR_STOP on",
                "SELECT :'fdw_access_sqlstate' = '55000' AS no_handler_blocks_foreign_table_access;",
            ]
        )
    lines.extend(
        [
            "",
            "-- 10. Catalog, dependency, and downstream-effect verification.",
            *_oracle(case, n),
            "",
            "-- 11. Remove foreign tables, servers, wrappers, functions, and roles.",
            *_cleanup(n),
            "",
            "-- 12. Cleanup oracle is the final deterministic verification above.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


__all__ = [
    "build_alter_foreign_data_wrapper_plan",
    "render_alter_foreign_data_wrapper_case",
]
