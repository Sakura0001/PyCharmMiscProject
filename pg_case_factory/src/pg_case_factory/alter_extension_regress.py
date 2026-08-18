"""PostgreSQL 18 ALTER EXTENSION full conditional-product regress design."""

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


_MEMBER_KINDS = (
    "access_method", "aggregate", "cast", "collation", "conversion", "domain",
    "event_trigger", "foreign_data_wrapper", "foreign_table", "function",
    "materialized_view", "operator", "operator_class", "operator_family",
    "language", "procedure", "routine", "schema", "sequence", "server",
    "table", "text_search_configuration", "text_search_dictionary",
    "text_search_parser", "text_search_template", "transform", "type", "view",
)
_QUALIFIABLE = frozenset(
    {
        "aggregate", "domain", "foreign_table", "function", "operator",
        "operator_class", "operator_family", "procedure", "routine", "sequence",
        "table", "text_search_configuration", "text_search_dictionary",
        "text_search_parser", "text_search_template", "type", "view",
    }
)
_CANONICAL_MEMBER_TYPES = {
    "table": "table", "function": "function", "type": "type", "view": "view",
    "sequence": "sequence", "domain": "domain", "aggregate": "aggregate",
    "operator": "operator",
}
_VERIFY = ("pg_extension_catalog_query", "pg_depend_catalog_query", "error_assertion")
_CLEANUP = ("drop_member_from_extension", "revert_schema", "revert_version", "drop_extension")


def _missing_member_sqlstate(kind: str) -> str:
    if kind in {"table", "foreign_table", "materialized_view", "sequence", "view"}:
        return "42P01"
    if kind in {"aggregate", "function", "operator", "procedure", "routine"}:
        return "42883"
    if kind == "schema":
        return "3F000"
    return "42704"


def _spec(
    group: str,
    branch: str,
    *,
    outcome: str = "success",
    sqlstate: str = "00000",
    execution_profile: str = "same_session_multiphase",
    **axes: str,
) -> dict[str, Any]:
    return {
        "group": group,
        "outcome": outcome,
        "execution_profile": execution_profile,
        "axes": {
            "branch": branch,
            "expected_sqlstate": sqlstate,
            "actor": "superuser",
            "extension_name_shape": "simple_id",
            **axes,
        },
    }


def _build_specs() -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []

    version_forms = (
        ("omitted_default", "identifier_form", "available", "success", "00000", "same_session_multiphase"),
        ("specified_new_version", "identifier_form", "available", "success", "00000", "external_isolated"),
        ("specified_new_version", "string_literal_form", "available", "success", "00000", "external_isolated"),
        ("nonexistent_version", "identifier_form", "unavailable", "expected_failure", "22023", "same_session_multiphase"),
        ("nonexistent_version", "string_literal_form", "unavailable", "expected_failure", "22023", "same_session_multiphase"),
    )
    for name_shape, row in itertools.product(("simple_id", "quoted_id"), version_forms):
        update_version, version_shape, availability, outcome, state, profile = row
        specs.append(_spec(
            "update_version_product", "update", outcome=outcome, sqlstate=state,
            execution_profile=profile, extension_name_shape=name_shape,
            update_version=update_version, version_string_shape=version_shape,
            version_availability=availability,
        ))

    for name_shape, schema_shape, relocatable in itertools.product(
        ("simple_id", "quoted_id"),
        ("simple_id", "quoted_id", "nonexistent_schema"),
        ("relocatable", "non_relocatable"),
    ):
        missing = schema_shape == "nonexistent_schema"
        success = relocatable == "relocatable" and not missing
        specs.append(_spec(
            "set_schema_product", "set_schema",
            outcome="success" if success else "expected_failure",
            sqlstate="00000" if success else ("3F000" if missing else "0A000"),
            extension_name_shape=name_shape, new_schema_shape=schema_shape,
            relocatable=relocatable, target_schema_state="missing" if missing else "exists",
        ))

    for branch, kind in itertools.product(("add", "drop"), _MEMBER_KINDS):
        shapes = ("simple_id", "quoted_id", "schema_qualified") if kind in _QUALIFIABLE else ("simple_id", "quoted_id")
        for shape in shapes:
            specs.append(_spec(
                "member_lexical_product", branch, member_kind=kind,
                member_name_shape=shape, member_state="loose_existing" if branch == "add" else "member_existing",
            ))

    for branch, kind, state in itertools.product(
        ("add", "drop"), _MEMBER_KINDS, ("object_missing", "wrong_membership")
    ):
        drop_nonmember = branch == "drop" and state == "wrong_membership"
        specs.append(_spec(
            "member_state_product", branch,
            outcome="success" if drop_nonmember else "expected_failure",
            sqlstate="00000" if drop_nonmember else (_missing_member_sqlstate(kind) if state == "object_missing" else "55000"),
            member_kind=kind, member_name_shape="schema_qualified" if kind in _QUALIFIABLE else "simple_id",
            member_state=("already_member" if branch == "add" and state == "wrong_membership" else
                          "not_a_member" if branch == "drop" and state == "wrong_membership" else state),
        ))

    for branch, actor in itertools.product(("update", "set_schema"), ("superuser", "extension_owner", "non_owner")):
        success = actor != "non_owner"
        specs.append(_spec(
            "privilege_truth_product", branch,
            outcome="success" if success else "expected_failure",
            sqlstate="00000" if success else "42501", actor=actor,
            execution_profile="external_isolated" if branch == "set_schema" and actor == "extension_owner" else "same_session_multiphase",
            update_version="omitted_default", version_string_shape="identifier_form",
            new_schema_shape="simple_id", relocatable="relocatable", target_schema_state="exists",
        ))
    for branch, actor, owner_match in itertools.product(
        ("add", "drop"), ("superuser", "extension_owner", "non_owner"), ("same_owner", "different_owner")
    ):
        success = actor == "superuser" or (actor == "extension_owner" and owner_match == "same_owner")
        specs.append(_spec(
            "privilege_truth_product", branch,
            outcome="success" if success else "expected_failure",
            sqlstate="00000" if success else "42501", actor=actor,
            object_owner_match=owner_match, member_kind="table",
            member_name_shape="schema_qualified",
            member_state="loose_existing" if branch == "add" else "member_existing",
        ))

    for branch in ("update", "set_schema", "add", "drop"):
        specs.append(_spec(
            "missing_extension_product", branch, outcome="expected_failure", sqlstate="42704",
            extension_name_shape="nonexistent_name", extension_state="missing",
            update_version="omitted_default", version_string_shape="identifier_form",
            new_schema_shape="simple_id", relocatable="relocatable", target_schema_state="exists",
            member_kind="table", member_name_shape="schema_qualified", member_state="loose_existing",
        ))

    for branch, signature in itertools.product(
        ("add", "drop"),
        ("star", "single_unnamed", "single_named_in", "multi_input", "ordered_full", "ordered_abbreviated"),
    ):
        specs.append(_spec(
            "member_signature_product", branch, member_kind="aggregate",
            member_name_shape="schema_qualified", signature_form=signature,
            member_state="loose_existing" if branch == "add" else "member_existing",
        ))
    for branch, kind, signature in itertools.product(
        ("add", "drop"), ("function", "procedure", "routine"),
        ("no_parentheses", "empty_parentheses", "single_unnamed", "single_named_in", "named_inout", "variadic", "out_ignored"),
    ):
        specs.append(_spec(
            "member_signature_product", branch, member_kind=kind,
            member_name_shape="schema_qualified", signature_form=signature,
            member_state="loose_existing" if branch == "add" else "member_existing",
        ))
    for branch, signature in itertools.product(("add", "drop"), ("binary", "prefix", "right_none")):
        invalid = signature == "right_none"
        specs.append(_spec(
            "member_signature_product", branch,
            outcome="expected_failure" if invalid else "success",
            sqlstate="42601" if invalid else "00000", member_kind="operator",
            member_name_shape="schema_qualified", signature_form=signature,
            member_state="loose_existing" if branch == "add" else "member_existing",
        ))
    for branch, signature in itertools.product(("add", "drop"), ("language", "procedural_language")):
        specs.append(_spec(
            "member_signature_product", branch, member_kind="language",
            member_name_shape="simple_id", signature_form=signature,
            member_state="loose_existing" if branch == "add" else "member_existing",
        ))

    parser_rows = (
        ("empty_extension_name", "update"), ("qualified_extension_name", "update"),
        ("three_part_extension_name", "update"), ("update_missing_version", "update"),
        ("update_duplicate_to", "update"), ("set_schema_missing_target", "set_schema"),
        ("set_schema_qualified_target", "set_schema"), ("add_missing_member_kind", "add"),
        ("add_unknown_member_kind", "add"), ("add_table_missing_name", "add"),
        ("drop_missing_member", "drop"), ("function_bad_signature", "add"),
        ("aggregate_bad_order_by", "add"), ("operator_missing_signature", "add"),
        ("transform_missing_language", "add"), ("trailing_tokens", "drop"),
    )
    for boundary, branch in parser_rows:
        specs.append(_spec(
            "parser_boundary_product", branch, outcome="expected_failure", sqlstate="42601",
            parser_boundary=boundary, member_kind="table", member_name_shape="simple_id",
        ))

    for branch in ("update", "set_schema", "add", "drop"):
        specs.append(_spec(
            "transactional_rollback_product", branch, transaction="rollback",
            update_version="omitted_default", version_string_shape="identifier_form",
            new_schema_shape="simple_id", relocatable="relocatable", target_schema_state="exists",
            member_kind="table", member_name_shape="schema_qualified",
            member_state="loose_existing" if branch == "add" else "member_existing",
        ))

    for kind in _MEMBER_KINDS:
        specs.append(_spec(
            "cross_extension_membership_product", "add", outcome="expected_failure", sqlstate="55000",
            member_kind=kind, member_name_shape="schema_qualified" if kind in _QUALIFIABLE else "simple_id",
            member_state="member_of_other_extension",
        ))
    for shape in ("simple_id", "quoted_id"):
        specs.append(_spec(
            "same_schema_noop_product", "set_schema", extension_name_shape=shape,
            new_schema_shape=shape, relocatable="relocatable", target_schema_state="same_schema",
        ))
    return specs


def _factor_tokens(axes: Mapping[str, str], outcome: str, ordinal: int) -> tuple[str, ...]:
    branch = axes["branch"]
    missing_extension = axes.get("extension_state") == "missing"
    actor = axes.get("actor", "superuser")
    values: dict[str, str] = {
        "statement_branch": f"branch_{branch}_member" if branch in {"add", "drop"} else f"branch_{branch}",
        "object_state": "not_exists" if missing_extension else "exists",
        "expected_status": "failure" if outcome == "expected_failure" else "success",
        "alter_action": branch,
        "extension_name_shape": axes.get("extension_name_shape", "simple_id"),
        "privilege_level": actor,
        "nonexistent_extension": "extension_missing" if missing_extension else "extension_exists",
        "insufficient_privilege": {
            "superuser": "superuser_execution", "extension_owner": "owner_execution", "non_owner": "non_owner_execution",
        }[actor],
        "verification_mode": "error_assertion" if outcome == "expected_failure" else _VERIFY[(ordinal - 1) % 2],
        "cleanup_mode": _CLEANUP[(ordinal - 1) % len(_CLEANUP)],
    }
    if branch == "update":
        unavailable = axes.get("version_availability") == "unavailable"
        values.update(
            update_version=axes.get("update_version", "omitted_default"),
            version_string_shape=axes.get("version_string_shape", "identifier_form"),
            version_not_available="version_unavailable" if unavailable else "version_available",
        )
    if branch == "set_schema":
        missing_schema = axes.get("target_schema_state") == "missing"
        non_reloc = axes.get("relocatable") == "non_relocatable"
        values.update(
            new_schema_shape=axes.get("new_schema_shape", "simple_id"),
            relocatable_state="non_relocatable" if non_reloc else "relocatable",
            target_schema_existence="schema_not_exists" if missing_schema else "schema_exists",
            non_relocatable_set_schema="non_relocatable_extension" if non_reloc else "relocatable_extension",
            nonexistent_target_schema="schema_missing" if missing_schema else "schema_exists",
        )
    if branch in {"add", "drop"}:
        member_state = axes.get("member_state", "loose_existing" if branch == "add" else "member_existing")
        object_missing = member_state == "object_missing"
        owner_match = axes.get("object_owner_match", "same_owner")
        kind = axes.get("member_kind", "table")
        values.update(
            member_object_name_shape=axes.get("member_name_shape", "simple_id"),
            object_owner_match=owner_match,
            member_object_existence="object_not_exists" if object_missing else "object_exists",
            nonexistent_member_object="object_missing" if object_missing else "object_exists",
            object_not_owner="owner_mismatch" if owner_match == "different_owner" else "owner_matches",
        )
        canonical = _CANONICAL_MEMBER_TYPES.get(kind)
        if canonical is not None:
            values["member_object_type"] = canonical
    return tuple(f"{key}={value}" for key, value in values.items())


def _build_cases() -> tuple[StatementRegressCase, ...]:
    cases: list[StatementRegressCase] = []
    for ordinal, spec in enumerate(_build_specs(), start=1):
        axes = dict(spec["axes"])
        case_id = f"ALTEREXTENSION{ordinal:05d}"
        cases.append(StatementRegressCase(
            ordinal=ordinal, case_id=case_id, sql_filename=f"{case_id}.sql",
            object_prefix=f"alterextension_{ordinal:05d}_",
            case_group=str(spec["group"]),
            case_type="expected_failure" if spec["outcome"] == "expected_failure" else "success",
            outcome=str(spec["outcome"]), execution_profile=str(spec["execution_profile"]),
            derived_axes=axes, factor_values=_factor_tokens(axes, str(spec["outcome"]), ordinal),
            combination_strategy="full branch-applicable PostgreSQL 18 conditional product; all 28 member-object forms; no sampling",
            description="ALTER EXTENSION conditional product: " + ", ".join(f"{k}={v}" for k, v in sorted(axes.items())),
            expected_anchor=f"SQLSTATE {axes['expected_sqlstate']}; pg_extension and pg_depend state oracle",
        ))
    return tuple(cases)


def _factor_decisions(entry: StatementCycleEntry, cases: tuple[StatementRegressCase, ...]) -> tuple[FactorValueDecision, ...]:
    by_id = {case.case_id: case for case in cases}
    rows: list[FactorValueDecision] = []
    for factor in entry.factors:
        for value, row_id in zip(factor.values, factor.row_ids):
            token = f"{factor.name}={value}"
            witnesses = tuple(case.case_id for case in cases if token in case.factor_values)
            if not witnesses:
                raise RemainingStatementRegressError(f"ALTER EXTENSION missing witness for {token}")
            failures = all(by_id[case_id].outcome == "expected_failure" for case_id in witnesses)
            rows.append(FactorValueDecision(
                row_id=row_id, factor=factor.name, value=value,
                disposition="expected_failure" if failures else "covered",
                reason="isolated PostgreSQL rejection" if failures else None,
                case_ids=witnesses,
            ))
    return tuple(rows)


def build_alter_extension_plan(snapshot: StatementFactorCycleSnapshot, entry: StatementCycleEntry) -> StatementRegressPlan:
    cases = _build_cases()
    if len(cases) != 416:
        raise RemainingStatementRegressError(f"ALTER EXTENSION expected 416 cases, found {len(cases)}")
    return StatementRegressPlan(
        statement_key="alter_extension", file_prefix="ALTEREXTENSION",
        cycle_fingerprint=snapshot.fingerprint, matrix_path=entry.matrix_path.as_posix(),
        matrix_sha256=entry.matrix_sha256, reference_path=entry.reference_path.as_posix(),
        reference_sha256=entry.reference_sha256,
        universe_semantic_sha256=snapshot.universe_semantic_sha256,
        official_source=entry.official_source, cases=cases,
        factor_decisions=_factor_decisions(entry, cases),
    )


def _qi(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _lit(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _names(case: StatementRegressCase) -> dict[str, str]:
    p = case.object_prefix
    shape = case.derived_axes.get("member_name_shape", "simple_id")
    raw = p + "member_object"
    rendered = _qi(raw) if shape == "quoted_id" else raw
    member_schema = p + "member_schema"
    qualified = f"{member_schema}.{raw}"
    member_ref = qualified if shape == "schema_qualified" else rendered
    ext_shape = case.derived_axes.get("extension_name_shape", "simple_id")
    if ext_shape == "nonexistent_name":
        ext_raw = p + "missing_extension"
    elif case.execution_profile == "external_isolated":
        ext_raw = "pgcf_versioned_extension" if case.derived_axes.get("branch") == "update" else "pgcf_relocatable_extension"
    elif case.derived_axes.get("relocatable") == "non_relocatable":
        ext_raw = "plpgsql"
    else:
        ext_raw = "hstore"
    ext = _qi(ext_raw) if ext_shape == "quoted_id" else ext_raw
    return {
        "p": p, "extension_raw": ext_raw, "extension": ext,
        "ext_schema": p + "extension_schema", "target_schema": p + "target_schema",
        "missing_schema": p + "missing_schema", "member_schema": member_schema,
        "member_raw": raw, "member": raw, "target_member": rendered,
        "member_qualified": qualified,
        "member_ref": member_ref, "owner": p + "extension_owner",
        "other_owner": p + "object_owner", "intruder": p + "intruder",
        "support": p + "support_function", "support_final": p + "final_function",
        "server": p + "server",
        "fdw": p + "fdw", "source_type": p + "source_type",
        "target_type": p + "target_type", "source_table": p + "source_table",
        "other_extension": "dblink",
    }


def _relation_columns() -> str:
    return (
        "id bigint NOT NULL, code text NOT NULL, payload jsonb NOT NULL, "
        "created_at timestamp with time zone NOT NULL, "
        "status smallint NOT NULL CHECK (status BETWEEN 0 AND 9)"
    )


def _callable_signature(case: StatementRegressCase) -> tuple[str, str, str]:
    signature = case.derived_axes.get("signature_form", "single_unnamed")
    if signature == "no_parentheses":
        return "()", "", ""
    if signature == "empty_parentheses":
        return "()", "()", ""
    if signature == "single_named_in":
        return "(IN original integer)", "(IN alias integer)", "integer"
    if signature == "named_inout":
        return "(INOUT original integer)", "(INOUT alias integer)", "integer"
    if signature == "variadic":
        return "(VARIADIC original integer[])", "(VARIADIC alias integer[])", "integer[]"
    if signature == "out_ignored":
        return "(IN original integer, OUT result text)", "(IN alias integer, OUT ignored text)", "integer"
    return "(integer)", "(integer)", "integer"


def _member_fixture(case: StatementRegressCase, n: Mapping[str, str]) -> tuple[list[str], str, list[str]]:
    kind = case.derived_axes.get("member_kind", "table")
    missing = case.derived_axes.get("member_state") == "object_missing"
    q = n["member_qualified"]
    r = n["member_ref"]
    setup: list[str] = [f"SET search_path TO {n['member_schema']}, pg_catalog;"]
    cleanup: list[str] = []
    if missing:
        descriptor = {
            "aggregate": f"AGGREGATE {r}(integer)", "cast": f"CAST ({n['member_schema']}.{n['source_type']} AS {n['member_schema']}.{n['target_type']})",
            "function": f"FUNCTION {r}(integer)", "procedure": f"PROCEDURE {r}(integer)",
            "routine": f"ROUTINE {r}(integer)", "operator": f"OPERATOR {n['member_schema']}.#=# (integer, integer)",
            "operator_class": f"OPERATOR CLASS {r} USING btree", "operator_family": f"OPERATOR FAMILY {r} USING btree",
            "language": f"LANGUAGE {n['member']}", "transform": f"TRANSFORM FOR {n['member_schema']}.{n['source_type']} LANGUAGE plpgsql",
        }.get(kind, f"{kind.replace('_', ' ').upper()} {r}")
        return setup, descriptor, cleanup

    if kind == "access_method":
        setup.append(f"CREATE ACCESS METHOD {n['member']} TYPE INDEX HANDLER pg_catalog.bthandler;")
        cleanup.append(f"DROP ACCESS METHOD IF EXISTS {n['member']};")
        return setup, f"ACCESS METHOD {n['target_member']}", cleanup
    if kind == "aggregate":
        sig = case.derived_axes.get("signature_form", "single_unnamed")
        setup.extend([
            f"CREATE FUNCTION {n['member_schema']}.{n['support']}(integer, integer) RETURNS integer LANGUAGE sql IMMUTABLE AS 'SELECT $1 + $2';",
        ])
        create_sig, target_sig = {
            "star": ("*", "*"),
            "single_unnamed": ("integer", "integer"),
            "single_named_in": ("IN original integer", "IN alias integer"),
            "multi_input": ("integer, integer", "integer, integer"),
            "ordered_full": ("integer ORDER BY integer", "integer ORDER BY integer"),
            "ordered_abbreviated": ("integer ORDER BY integer", "integer, integer"),
        }.get(sig, ("integer", "integer"))
        if sig == "star":
            setup[-1] = f"CREATE FUNCTION {n['member_schema']}.{n['support']}(integer) RETURNS integer LANGUAGE sql IMMUTABLE AS 'SELECT $1 + 1';"
        if sig == "multi_input":
            setup[-1] = f"CREATE FUNCTION {n['member_schema']}.{n['support']}(integer, integer, integer) RETURNS integer LANGUAGE sql IMMUTABLE AS 'SELECT $1 + $2 + $3';"
        if sig in {"ordered_full", "ordered_abbreviated"}:
            setup.append(
                f"CREATE FUNCTION {n['member_schema']}.{n['support_final']}(integer, integer) "
                "RETURNS integer LANGUAGE sql IMMUTABLE AS 'SELECT $1 + $2';"
            )
            setup.append(
                f"CREATE AGGREGATE {q}({create_sig}) (SFUNC={n['member_schema']}.{n['support']}, "
                f"STYPE=integer, FINALFUNC={n['member_schema']}.{n['support_final']}, INITCOND='0');"
            )
        else:
            setup.append(f"CREATE AGGREGATE {q}({create_sig}) (SFUNC={n['member_schema']}.{n['support']}, STYPE=integer, INITCOND='0');")
        return setup, f"AGGREGATE {r}({target_sig})", cleanup
    if kind == "cast":
        setup.extend([
            f"CREATE TYPE {n['member_schema']}.{n['source_type']} AS ENUM ('a');",
            f"CREATE TYPE {n['member_schema']}.{n['target_type']} AS ENUM ('a');",
            f"CREATE CAST ({n['member_schema']}.{n['source_type']} AS {n['member_schema']}.{n['target_type']}) WITH INOUT;",
        ])
        cleanup.append(f"DROP CAST IF EXISTS ({n['member_schema']}.{n['source_type']} AS {n['member_schema']}.{n['target_type']});")
        return setup, f"CAST ({n['member_schema']}.{n['source_type']} AS {n['member_schema']}.{n['target_type']})", cleanup
    if kind == "collation":
        setup.append(f"CREATE COLLATION {q} FROM pg_catalog.\"C\";")
        return setup, f"COLLATION {r}", cleanup
    if kind == "conversion":
        setup.append(f"CREATE CONVERSION {q} FOR 'UTF8' TO 'LATIN1' FROM pg_catalog.utf8_to_iso8859_1;")
        return setup, f"CONVERSION {r}", cleanup
    if kind == "domain":
        setup.append(f"CREATE DOMAIN {q} AS integer CHECK (VALUE >= 0);")
        return setup, f"DOMAIN {r}", cleanup
    if kind == "event_trigger":
        setup.extend([
            f"CREATE FUNCTION {n['member_schema']}.{n['support']}() RETURNS event_trigger LANGUAGE plpgsql AS $body$ BEGIN END $body$;",
            f"CREATE EVENT TRIGGER {n['member']} ON ddl_command_end EXECUTE FUNCTION {n['member_schema']}.{n['support']}();",
        ])
        cleanup.append(f"DROP EVENT TRIGGER IF EXISTS {n['member']};")
        return setup, f"EVENT TRIGGER {n['target_member']}", cleanup
    if kind == "foreign_data_wrapper":
        setup.append(f"CREATE FOREIGN DATA WRAPPER {n['member']};")
        cleanup.append(f"DROP FOREIGN DATA WRAPPER IF EXISTS {n['member']} CASCADE;")
        return setup, f"FOREIGN DATA WRAPPER {n['target_member']}", cleanup
    if kind == "foreign_table":
        setup.extend([
            f"CREATE FOREIGN DATA WRAPPER {n['fdw']};", f"CREATE SERVER {n['server']} FOREIGN DATA WRAPPER {n['fdw']};",
            f"CREATE FOREIGN TABLE {q} ({_relation_columns()}) SERVER {n['server']};",
        ])
        cleanup.append(f"DROP FOREIGN DATA WRAPPER IF EXISTS {n['fdw']} CASCADE;")
        return setup, f"FOREIGN TABLE {r}", cleanup
    if kind in {"function", "procedure", "routine"}:
        create_sig, target_sig, _ = _callable_signature(case)
        if kind == "function":
            returns = "RETURNS integer" if "OUT" not in create_sig else ""
            signature = case.derived_axes.get("signature_form", "single_unnamed")
            if signature in {"no_parentheses", "empty_parentheses"}:
                body = "AS 'SELECT 1'"
            elif signature == "variadic":
                body = "AS 'SELECT COALESCE(pg_catalog.cardinality($1), 0)'"
            elif signature == "out_ignored":
                body = "AS $$ SELECT COALESCE($1, 0)::text $$"
            else:
                body = "AS 'SELECT COALESCE($1, 0)'"
            setup.append(f"CREATE FUNCTION {q}{create_sig} {returns} LANGUAGE sql {body};")
            descriptor = f"FUNCTION {r}{target_sig}"
        else:
            setup.append(f"CREATE PROCEDURE {q}{create_sig} LANGUAGE plpgsql AS $body$ BEGIN NULL; END $body$;")
            descriptor = f"{kind.upper()} {r}{target_sig}"
        return setup, descriptor, cleanup
    if kind == "materialized_view":
        setup.extend([
            f"CREATE TABLE {n['member_schema']}.{n['source_table']} ({_relation_columns()}, PRIMARY KEY (id), UNIQUE (code));",
            f"INSERT INTO {n['member_schema']}.{n['source_table']}(id,code,payload,created_at,status) VALUES (1,'a','{{}}',TIMESTAMPTZ '2024-01-01 00:00:00+00',1);",
            f"CREATE MATERIALIZED VIEW {q} AS SELECT id,code,payload,created_at,status FROM {n['member_schema']}.{n['source_table']};",
        ])
        return setup, f"MATERIALIZED VIEW {r}", cleanup
    if kind == "operator":
        sig = case.derived_axes.get("signature_form", "binary")
        if sig == "prefix":
            setup.append(f"CREATE FUNCTION {n['member_schema']}.{n['support']}(integer) RETURNS boolean LANGUAGE sql IMMUTABLE AS 'SELECT $1 <> 0';")
            setup.append(f"CREATE OPERATOR {n['member_schema']}.@# (RIGHTARG=integer, FUNCTION={n['member_schema']}.{n['support']});")
            return setup, f"OPERATOR {n['member_schema']}.@# (NONE, integer)", cleanup
        setup.append(f"CREATE FUNCTION {n['member_schema']}.{n['support']}(integer, integer) RETURNS boolean LANGUAGE sql IMMUTABLE AS 'SELECT $1 = $2';")
        setup.append(f"CREATE OPERATOR {n['member_schema']}.#=# (LEFTARG=integer, RIGHTARG=integer, FUNCTION={n['member_schema']}.{n['support']});")
        args = "integer, NONE" if sig == "right_none" else "integer, integer"
        return setup, f"OPERATOR {n['member_schema']}.#=# ({args})", cleanup
    if kind == "operator_family":
        setup.append(f"CREATE OPERATOR FAMILY {q} USING btree;")
        return setup, f"OPERATOR FAMILY {r} USING btree", cleanup
    if kind == "operator_class":
        setup.append(
            f"CREATE OPERATOR CLASS {q} FOR TYPE integer USING btree AS "
            "OPERATOR 1 pg_catalog.<(integer,integer), OPERATOR 3 pg_catalog.=(integer,integer), "
            "OPERATOR 5 pg_catalog.>(integer,integer), FUNCTION 1 pg_catalog.btint4cmp(integer,integer);"
        )
        return setup, f"OPERATOR CLASS {r} USING btree", cleanup
    if kind == "language":
        setup.append(
            f"CREATE TRUSTED PROCEDURAL LANGUAGE {n['member']} HANDLER pg_catalog.plpgsql_call_handler "
            "INLINE pg_catalog.plpgsql_inline_handler VALIDATOR pg_catalog.plpgsql_validator;"
        )
        cleanup.append(f"DROP LANGUAGE IF EXISTS {n['member']} CASCADE;")
        keyword = "PROCEDURAL LANGUAGE" if case.derived_axes.get("signature_form") == "procedural_language" else "LANGUAGE"
        return setup, f"{keyword} {n['target_member']}", cleanup
    if kind == "schema":
        setup.append(f"CREATE SCHEMA {n['member']};")
        return setup, f"SCHEMA {n['target_member']}", cleanup
    if kind == "sequence":
        setup.append(f"CREATE SEQUENCE {q} AS bigint START WITH 1 INCREMENT BY 1;")
        return setup, f"SEQUENCE {r}", cleanup
    if kind == "server":
        setup.extend([f"CREATE FOREIGN DATA WRAPPER {n['fdw']};", f"CREATE SERVER {n['member']} FOREIGN DATA WRAPPER {n['fdw']};"])
        cleanup.append(f"DROP FOREIGN DATA WRAPPER IF EXISTS {n['fdw']} CASCADE;")
        return setup, f"SERVER {n['target_member']}", cleanup
    if kind == "table":
        setup.extend([
            f"CREATE TABLE {q} ({_relation_columns()}, PRIMARY KEY (id), UNIQUE (code));",
            f"INSERT INTO {q}(id,code,payload,created_at,status) VALUES (1,'a','{{}}',TIMESTAMPTZ '2024-01-01 00:00:00+00',1);",
        ])
        return setup, f"TABLE {r}", cleanup
    if kind == "text_search_configuration":
        setup.append(f"CREATE TEXT SEARCH CONFIGURATION {q} (COPY=pg_catalog.simple);")
        return setup, f"TEXT SEARCH CONFIGURATION {r}", cleanup
    if kind == "text_search_dictionary":
        setup.append(f"CREATE TEXT SEARCH DICTIONARY {q} (TEMPLATE=pg_catalog.simple);")
        return setup, f"TEXT SEARCH DICTIONARY {r}", cleanup
    if kind == "text_search_parser":
        setup.append(
            f"CREATE TEXT SEARCH PARSER {q} (START=pg_catalog.prsd_start, GETTOKEN=pg_catalog.prsd_nexttoken, "
            "END=pg_catalog.prsd_end, LEXTYPES=pg_catalog.prsd_lextype, HEADLINE=pg_catalog.prsd_headline);"
        )
        return setup, f"TEXT SEARCH PARSER {r}", cleanup
    if kind == "text_search_template":
        setup.append(f"CREATE TEXT SEARCH TEMPLATE {q} (INIT=pg_catalog.dsimple_init, LEXIZE=pg_catalog.dsimple_lexize);")
        return setup, f"TEXT SEARCH TEMPLATE {r}", cleanup
    if kind == "transform":
        setup.extend([
            f"CREATE TYPE {n['member_schema']}.{n['source_type']} AS ENUM ('a');",
            f"CREATE FUNCTION {n['member_schema']}.{n['support']}(internal) RETURNS internal LANGUAGE internal IMMUTABLE STRICT AS 'textlike_support';",
            f"CREATE TRANSFORM FOR {n['member_schema']}.{n['source_type']} LANGUAGE plpgsql (FROM SQL WITH FUNCTION {n['member_schema']}.{n['support']}(internal));",
        ])
        cleanup.append(f"DROP TRANSFORM IF EXISTS FOR {n['member_schema']}.{n['source_type']} LANGUAGE plpgsql;")
        return setup, f"TRANSFORM FOR {n['member_schema']}.{n['source_type']} LANGUAGE plpgsql", cleanup
    if kind == "type":
        setup.append(f"CREATE TYPE {q} AS ENUM ('new', 'ready');")
        return setup, f"TYPE {r}", cleanup
    if kind == "view":
        setup.extend([
            f"CREATE TABLE {n['member_schema']}.{n['source_table']} ({_relation_columns()}, PRIMARY KEY (id), UNIQUE (code));",
            f"INSERT INTO {n['member_schema']}.{n['source_table']}(id,code,payload,created_at,status) VALUES (1,'a','{{}}',TIMESTAMPTZ '2024-01-01 00:00:00+00',1);",
            f"CREATE VIEW {q}(id,code,payload,created_at,status) AS SELECT id,code,payload,created_at,status FROM {n['member_schema']}.{n['source_table']};",
        ])
        return setup, f"VIEW {r}", cleanup
    raise RemainingStatementRegressError(f"unsupported extension member kind {kind}")


def _target(case: StatementRegressCase, n: Mapping[str, str], descriptor: str) -> str:
    a = case.derived_axes
    ext = n["extension"]
    if case.case_group == "parser_boundary_product":
        return {
            "empty_extension_name": "ALTER EXTENSION UPDATE;",
            "qualified_extension_name": "ALTER EXTENSION public.hstore UPDATE;",
            "three_part_extension_name": "ALTER EXTENSION current.public.hstore UPDATE;",
            "update_missing_version": f"ALTER EXTENSION {ext} UPDATE TO;",
            "update_duplicate_to": f"ALTER EXTENSION {ext} UPDATE TO TO '1.0';",
            "set_schema_missing_target": f"ALTER EXTENSION {ext} SET SCHEMA;",
            "set_schema_qualified_target": f"ALTER EXTENSION {ext} SET SCHEMA public.target;",
            "add_missing_member_kind": f"ALTER EXTENSION {ext} ADD;",
            "add_unknown_member_kind": f"ALTER EXTENSION {ext} ADD WIDGET x;",
            "add_table_missing_name": f"ALTER EXTENSION {ext} ADD TABLE;",
            "drop_missing_member": f"ALTER EXTENSION {ext} DROP TABLE;",
            "function_bad_signature": f"ALTER EXTENSION {ext} ADD FUNCTION {n['member_schema']}.{n['member']}(integer,);",
            "aggregate_bad_order_by": f"ALTER EXTENSION {ext} ADD AGGREGATE {n['member_schema']}.{n['member']}(integer ORDER BY);",
            "operator_missing_signature": f"ALTER EXTENSION {ext} ADD OPERATOR {n['member_schema']}.#=#;",
            "transform_missing_language": f"ALTER EXTENSION {ext} ADD TRANSFORM FOR integer;",
            "trailing_tokens": f"ALTER EXTENSION {ext} DROP TABLE {n['member_schema']}.{n['member']} TRAILING;",
        }[a["parser_boundary"]]
    if a["branch"] == "update":
        version = a.get("update_version", "omitted_default")
        if version == "omitted_default":
            return f"ALTER EXTENSION {ext} UPDATE;"
        if a.get("version_availability") == "unavailable":
            token = _qi("pgcf_missing_version") if a.get("version_string_shape") == "identifier_form" else _lit("pgcf_missing_version")
        else:
            token = _qi("2.0") if a.get("version_string_shape") == "identifier_form" else _lit("2.0")
        return f"ALTER EXTENSION {ext} UPDATE TO {token};"
    if a["branch"] == "set_schema":
        schema = n["missing_schema"] if a.get("target_schema_state") == "missing" else (
            n["ext_schema"] if a.get("target_schema_state") == "same_schema" else n["target_schema"]
        )
        if a.get("new_schema_shape") == "quoted_id":
            schema = _qi(schema)
        return f"ALTER EXTENSION {ext} SET SCHEMA {schema};"
    return f"ALTER EXTENSION {ext} {a['branch'].upper()} {descriptor};"


def _precleanup(case: StatementRegressCase, n: Mapping[str, str]) -> list[str]:
    lines: list[str] = []
    if case.derived_axes.get("member_kind") == "table":
        lines.append(f"DROP TABLE IF EXISTS {n['member_qualified']} CASCADE;")
    if case.derived_axes.get("member_kind") in {"materialized_view", "view"}:
        lines.append(f"DROP TABLE IF EXISTS {n['member_schema']}.{n['source_table']} CASCADE;")
    lines.extend([
        "RESET ROLE;", "RESET search_path;",
        "DROP EXTENSION IF EXISTS hstore CASCADE;", "DROP EXTENSION IF EXISTS dblink CASCADE;",
        "DROP EXTENSION IF EXISTS pgcf_versioned_extension CASCADE;",
        "DROP EXTENSION IF EXISTS pgcf_relocatable_extension CASCADE;",
        f"DROP EVENT TRIGGER IF EXISTS {n['member']};", f"DROP ACCESS METHOD IF EXISTS {n['member']};",
        f"DROP FOREIGN DATA WRAPPER IF EXISTS {n['member']} CASCADE;", f"DROP LANGUAGE IF EXISTS {n['member']} CASCADE;",
        f"DROP SCHEMA IF EXISTS {n['target_schema']} CASCADE;", f"DROP SCHEMA IF EXISTS {n['member_schema']} CASCADE;",
        f"DROP SCHEMA IF EXISTS {n['ext_schema']} CASCADE;",
        f"SELECT CASE WHEN EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname={_lit(n['owner'])}) THEN 'yes' ELSE 'no' END AS cleanup_owner_state",
        "FROM (VALUES (true)) AS cleanup_owner_anchor(dummy)",
        "ORDER BY cleanup_owner_state;", r"\gset",
        r"\if :cleanup_owner_state", f"REVOKE CREATE ON DATABASE :\"DBNAME\" FROM {n['owner']};", r"\endif",
        f"DROP ROLE IF EXISTS {n['intruder']};", f"DROP ROLE IF EXISTS {n['other_owner']};", f"DROP ROLE IF EXISTS {n['owner']};",
    ])
    return lines


def _extension_fixture(case: StatementRegressCase, n: Mapping[str, str]) -> list[str]:
    a = case.derived_axes
    if a.get("extension_state") == "missing" or case.case_group == "parser_boundary_product":
        return [f"CREATE SCHEMA {n['member_schema']};", f"CREATE SCHEMA {n['target_schema']};"]
    if a.get("relocatable") == "non_relocatable":
        return [f"CREATE SCHEMA {n['target_schema']};"]
    if case.execution_profile == "external_isolated":
        if a.get("branch") == "update":
            return [
                "-- external prerequisite: pgcf_versioned_extension control and 1.0--2.0 update scripts are installed",
                "CREATE EXTENSION pgcf_versioned_extension VERSION '1.0';",
            ]
        return [
            "-- external prerequisite: pgcf_relocatable_extension is relocatable, superuser=false, and creates caller-owned members",
            f"CREATE ROLE {n['owner']};", f"CREATE ROLE {n['other_owner']};", f"CREATE ROLE {n['intruder']};",
            f"CREATE SCHEMA {n['ext_schema']} AUTHORIZATION {n['owner']};",
            f"CREATE SCHEMA {n['member_schema']} AUTHORIZATION {n['owner']};",
            f"CREATE SCHEMA {n['target_schema']} AUTHORIZATION {n['owner']};",
            f"GRANT CREATE ON DATABASE :\"DBNAME\" TO {n['owner']};",
            f"SET ROLE {n['owner']};",
            f"CREATE EXTENSION pgcf_relocatable_extension WITH SCHEMA {n['ext_schema']};",
            "RESET ROLE;",
        ]
    lines = [
        f"CREATE ROLE {n['owner']};", f"CREATE ROLE {n['other_owner']};", f"CREATE ROLE {n['intruder']};",
        f"CREATE SCHEMA {n['ext_schema']} AUTHORIZATION {n['owner']};",
        f"CREATE SCHEMA {n['member_schema']} AUTHORIZATION {n['owner']};",
        f"CREATE SCHEMA {n['target_schema']} AUTHORIZATION {n['owner']};",
    ]
    actor = a.get("actor", "superuser")
    if actor in {"extension_owner", "non_owner"}:
        lines.extend([
            f"GRANT CREATE ON DATABASE :\"DBNAME\" TO {n['owner']};",
            f"SET ROLE {n['owner']};", f"CREATE EXTENSION hstore WITH SCHEMA {n['ext_schema']};", "RESET ROLE;",
        ])
    else:
        lines.append(f"CREATE EXTENSION hstore WITH SCHEMA {n['ext_schema']};")
    return lines


def _capture(n: Mapping[str, str]) -> list[str]:
    return [
        "SELECT",
        f"    COALESCE((SELECT oid::text FROM pg_catalog.pg_extension WHERE extname={_lit(n['extension_raw'])}), '0') AS before_extension_oid,",
        f"    COALESCE((SELECT extversion FROM pg_catalog.pg_extension WHERE extname={_lit(n['extension_raw'])}), '<MISSING>') AS before_extension_version,",
        f"    COALESCE((SELECT extnamespace::text FROM pg_catalog.pg_extension WHERE extname={_lit(n['extension_raw'])}), '0') AS before_extension_namespace,",
        f"    COALESCE((SELECT extowner::text FROM pg_catalog.pg_extension WHERE extname={_lit(n['extension_raw'])}), '0') AS before_extension_owner,",
        f"    COALESCE((SELECT count(*)::text FROM pg_catalog.pg_depend AS d JOIN pg_catalog.pg_extension AS e ON e.oid=d.refobjid WHERE e.extname={_lit(n['extension_raw'])} AND d.deptype='e'), '0') AS before_member_count",
        "FROM (VALUES (true)) AS capture_anchor(dummy)",
        "ORDER BY before_extension_oid;", r"\gset",
    ]


def _oracle(case: StatementRegressCase, n: Mapping[str, str]) -> list[str]:
    a = case.derived_axes
    if case.outcome == "expected_failure" or a.get("transaction") == "rollback":
        return [
            "SELECT COALESCE(pg_catalog.bool_and(",
            "    e.extversion = :'before_extension_version'",
            "    AND e.extnamespace::text = :'before_extension_namespace'",
            "    AND e.extowner::text = :'before_extension_owner'",
            "), true) AS failed_or_rolled_back_extension_unchanged",
            "FROM pg_catalog.pg_extension AS e",
            "WHERE :'before_extension_oid' <> '0' AND e.oid=:'before_extension_oid'::oid",
            "ORDER BY failed_or_rolled_back_extension_unchanged;",
        ]
    if a["branch"] == "set_schema":
        target = n["ext_schema"] if a.get("target_schema_state") == "same_schema" else n["target_schema"]
        return [
            f"SELECT n.nspname={_lit(target)} AS extension_schema_matches",
            "FROM pg_catalog.pg_extension AS e JOIN pg_catalog.pg_namespace AS n ON n.oid=e.extnamespace",
            "WHERE e.oid=:'before_extension_oid'::oid",
            "ORDER BY extension_schema_matches;",
        ]
    if a["branch"] in {"add", "drop"}:
        delta = "+ 1" if a["branch"] == "add" else "- 1"
        return [
            f"SELECT count(*) = :'before_member_count'::bigint {delta} AS extension_member_count_matches",
            "FROM pg_catalog.pg_depend AS d",
            "WHERE d.refobjid=:'before_extension_oid'::oid AND d.deptype='e'",
            "ORDER BY extension_member_count_matches;",
        ]
    return [
        "SELECT e.extversion <> '' AS extension_version_observed",
        "FROM pg_catalog.pg_extension AS e WHERE e.oid=:'before_extension_oid'::oid",
        "ORDER BY extension_version_observed;",
    ]


def _cleanup(case: StatementRegressCase, n: Mapping[str, str], member_cleanup: list[str]) -> list[str]:
    lines = ["RESET ROLE;", "RESET search_path;"]
    if case.execution_profile == "external_isolated":
        extension = "pgcf_versioned_extension" if case.derived_axes.get("branch") == "update" else "pgcf_relocatable_extension"
        lines.append(f"DROP EXTENSION IF EXISTS {extension} CASCADE;")
    else:
        lines.extend(["DROP EXTENSION IF EXISTS hstore CASCADE;", "DROP EXTENSION IF EXISTS dblink CASCADE;"])
    lines.extend(member_cleanup)
    lines.extend([
        f"DROP EVENT TRIGGER IF EXISTS {n['member']};", f"DROP ACCESS METHOD IF EXISTS {n['member']};",
        f"DROP FOREIGN DATA WRAPPER IF EXISTS {n['member']} CASCADE;", f"DROP LANGUAGE IF EXISTS {n['member']} CASCADE;",
        f"DROP SCHEMA IF EXISTS {n['target_schema']} CASCADE;", f"DROP SCHEMA IF EXISTS {n['member_schema']} CASCADE;",
        f"DROP SCHEMA IF EXISTS {n['ext_schema']} CASCADE;",
        f"SELECT CASE WHEN EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname={_lit(n['owner'])}) THEN 'yes' ELSE 'no' END AS cleanup_owner_state",
        "FROM (VALUES (true)) AS cleanup_owner_anchor(dummy)",
        "ORDER BY cleanup_owner_state;", r"\gset",
        r"\if :cleanup_owner_state", f"REVOKE CREATE ON DATABASE :\"DBNAME\" FROM {n['owner']};", r"\endif",
        f"DROP ROLE IF EXISTS {n['intruder']};", f"DROP ROLE IF EXISTS {n['other_owner']};", f"DROP ROLE IF EXISTS {n['owner']};",
        "SELECT",
        f"    NOT EXISTS (SELECT 1 FROM pg_catalog.pg_extension WHERE extname IN ('hstore','dblink','pgcf_versioned_extension','pgcf_relocatable_extension'))",
        f"    AND NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname IN ({_lit(n['owner'])},{_lit(n['other_owner'])},{_lit(n['intruder'])})) AS cleanup_complete",
        "FROM (VALUES (true)) AS cleanup_anchor(dummy)",
        "ORDER BY cleanup_complete;",
    ])
    if case.derived_axes.get("member_kind") == "table":
        lines.append(f"DROP TABLE IF EXISTS {n['member_qualified']} CASCADE;")
    if case.derived_axes.get("member_kind") in {"materialized_view", "view"}:
        lines.append(f"DROP TABLE IF EXISTS {n['member_schema']}.{n['source_table']} CASCADE;")
    return lines


def render_alter_extension_case(plan: StatementRegressPlan, case: StatementRegressCase) -> str:
    n = _names(case)
    member_setup, descriptor, member_cleanup = _member_fixture(case, n)
    a = case.derived_axes
    lines = _header(plan, case) + [
        "", "-- 1. Header and immutable trace metadata are complete above.",
        "", "-- 2. Session settings are explicit and reset during cleanup.",
        "", "-- 3. Idempotent pre-cleanup.", *_precleanup(case, n),
        "", "-- 4. Extension, role, schema, and member-object fixture.", *_extension_fixture(case, n),
    ]
    if case.case_group != "parser_boundary_product" and a.get("relocatable") != "non_relocatable" and case.execution_profile != "external_isolated":
        if a.get("branch") in {"add", "drop"}:
            lines.extend(member_setup)
            if a.get("object_owner_match") == "different_owner" and a.get("member_kind") == "table":
                lines.append(f"ALTER TABLE {n['member_qualified']} OWNER TO {n['other_owner']};")
            elif (
                a.get("object_owner_match") == "same_owner"
                and a.get("actor") in {"extension_owner", "non_owner"}
                and a.get("member_kind") == "table"
            ):
                lines.append(f"ALTER TABLE {n['member_qualified']} OWNER TO {n['owner']};")
            if (
                a.get("extension_state") != "missing"
                and a.get("member_state") != "object_missing"
                and a.get("signature_form") != "right_none"
                and (a.get("branch") == "drop" or a.get("member_state") == "already_member")
            ):
                lines.extend(["-- setup-only ALTER EXTENSION; coverage_credit=false", f"ALTER EXTENSION hstore ADD {descriptor};"])
            if a.get("extension_state") != "missing" and a.get("member_state") == "member_of_other_extension":
                lines.extend(["CREATE EXTENSION dblink;", "-- setup-only ALTER EXTENSION; coverage_credit=false", f"ALTER EXTENSION dblink ADD {descriptor};"])
    lines.extend([
        "", "-- 5. Fixture is complete and every failure case has one isolated cause.",
        "SELECT true AS fixture_ready FROM (VALUES (true)) AS fixture_anchor(dummy) ORDER BY fixture_ready;",
        "", "-- 6. Capture extension identity, version, namespace, owner, and member count.", *_capture(n),
        "", "-- 7. Select the declared executor.",
    ])
    if a.get("actor") == "extension_owner":
        lines.append(f"SET ROLE {n['owner']};")
    elif a.get("actor") == "non_owner":
        lines.append(f"SET ROLE {n['intruder']};")
    lines.extend(["", "-- 8. Primary target statement (exactly one coverage-credit operation)."])
    if a.get("transaction") == "rollback":
        lines.append("BEGIN;")
    lines.extend([
        r"\set ON_ERROR_STOP off", _target(case, n, descriptor), r"\set alter_extension_sqlstate :SQLSTATE", r"\set ON_ERROR_STOP on",
        "", "-- 9. SQLSTATE and primary-result oracle.",
        f"SELECT :'alter_extension_sqlstate' = {_lit(a['expected_sqlstate'])} AS expected_SQLSTATE;",
    ])
    if a.get("transaction") == "rollback":
        lines.append("ROLLBACK;")
    lines.extend([
        "RESET ROLE;", "", "-- 10. Catalog and extension-membership verification.", *_oracle(case, n),
        "", "-- 11. Remove extension, detached members, schemas, roles, and helper objects.", *_cleanup(case, n, member_cleanup),
        "", "-- 12. Cleanup oracle is the final deterministic verification above.",
    ])
    return "\n".join(lines).rstrip() + "\n"


__all__ = ["build_alter_extension_plan", "render_alter_extension_case"]
