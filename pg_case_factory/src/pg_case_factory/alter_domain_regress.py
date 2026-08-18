"""PostgreSQL 18 ALTER DOMAIN full conditional-product regress design."""

from __future__ import annotations

import itertools
import json
import re
from pathlib import Path
from typing import Any, Mapping

import yaml

from .remaining_statement_regress import (
    FactorValueDecision,
    RemainingStatementRegressError,
    StatementRegressCase,
    StatementRegressPlan,
    _header,
)
from .statement_factor_cycle import StatementCycleEntry, StatementFactorCycleSnapshot


_BRANCHES = (
    "set_default", "drop_default", "set_not_null", "drop_not_null",
    "add_constraint", "drop_constraint", "rename_constraint",
    "validate_constraint", "owner_to", "rename_to", "set_schema",
)
_SOURCE_SHAPES = ("simple_id", "quoted_id", "schema_qualified", "reserved_word_as_name")
_VERIFICATIONS = (
    "catalog_query_pg_type", "catalog_query_pg_constraint", "effect_query", "error_assertion"
)
_CLEANUPS = ("revert_alter", "drop_domain", "role_cleanup", "schema_cleanup")
_TYPE_FORMS = (
    "set_default", "drop_default", "set_not_null", "drop_not_null",
    "add_check_full", "add_check_not_valid", "validate_check",
)
_YAML_FENCE = re.compile(r"```yaml\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def _load_type_profiles(root: Path) -> tuple[dict[str, str], ...]:
    path = root / "skills/pg-sql-generation/references/common/pg18_type_catalog.md"
    text = path.read_text(encoding="utf-8")
    match = _YAML_FENCE.search(text)
    if match is None:
        raise RemainingStatementRegressError("PG18 type catalog has no YAML block")
    document = yaml.safe_load(match.group(1))
    structured = document.get("structured_config", document)
    profiles = structured.get("types")
    if not isinstance(profiles, dict) or len(profiles) != 85:
        raise RemainingStatementRegressError("PG18 executable type inventory must contain 85 profiles")
    result: list[dict[str, str]] = []
    for key, raw in profiles.items():
        profile = dict(raw)
        declaration = str(profile.get("declaration_sql") or "")
        declaration = {
            "SMALLSERIAL": "SMALLINT", "SERIAL": "INTEGER", "BIGSERIAL": "BIGINT"
        }.get(declaration.upper(), declaration)
        values = dict(profile.get("sample_values") or {}).get("success") or []
        sample = next((str(value) for value in values if str(value).upper() != "DEFAULT"), "1")
        result.append(
            {
                "type_key": str(key),
                "type_declaration": declaration,
                "type_sample": sample,
                "type_setup_json": json.dumps(
                    [str(item) for item in profile.get("requires_setup") or []],
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
            }
        )
    return tuple(result)


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
            "domain_name_shape": "schema_qualified",
            "base_type": "INTEGER",
            "base_sample": "1",
            "type_setup_json": "[]",
            "container_usage": "not_used_in_container",
            "container_block": "no_container_block",
            "concurrent_hazard": "safe_serial_execution",
            **axes,
        },
    }


def _official_forms() -> tuple[tuple[str, dict[str, str]], ...]:
    forms: list[tuple[str, dict[str, str]]] = []
    for expression in ("literal", "cast", "stable_expression"):
        forms.append(("set_default", {"default_expression": expression}))
    forms.extend((("drop_default", {}), ("set_not_null", {}), ("drop_not_null", {})))
    forms.extend(
        (
            "add_constraint",
            {
                "constraint_type": kind,
                "constraint_named": named,
                "not_valid": not_valid,
                "constraint_name_shape": "simple_id" if named == "named" else "existing_constraint",
            },
        )
        for kind, named, not_valid in (
            ("not_null", "unnamed", "full_valid"),
            ("not_null_with_name", "named", "full_valid"),
            ("check", "unnamed", "full_valid"),
            ("check_with_name", "named", "full_valid"),
            ("check", "unnamed", "not_valid"),
            ("check_with_name", "named", "not_valid"),
        )
    )
    forms.extend(
        (
            "drop_constraint",
            {
                "constraint_name_shape": name_shape,
                "if_exists": if_exists,
                "cascade_restrict": behavior,
                "constraint_state": "exists",
            },
        )
        for name_shape, if_exists, behavior in itertools.product(
            ("simple_id", "quoted_id"), ("present", "absent"),
            ("restrict", "cascade", "omitted_default_restrict")
        )
    )
    forms.extend(
        (
            "rename_constraint",
            {
                "constraint_name_shape": old,
                "new_constraint_name_shape": new,
                "constraint_state": "exists",
                "constraint_target": "available",
            },
        )
        for old, new in itertools.product(
            ("simple_id", "quoted_id"), ("simple_id", "quoted_id", "reserved_word_as_name")
        )
    )
    forms.extend(
        ("validate_constraint", {"constraint_name_shape": shape, "constraint_state": "exists"})
        for shape in ("simple_id", "quoted_id")
    )
    forms.extend(
        ("owner_to", {"owner_target": target, "owner_name_shape": shape})
        for target, shape in (
            ("specified_new_owner", "simple_id"),
            ("specified_new_owner", "quoted_id"),
            ("specified_current_role", "special_token"),
            ("specified_current_user", "special_token"),
            ("specified_session_user", "special_token"),
        )
    )
    forms.extend(
        ("rename_to", {"new_name_shape": shape, "rename_target": "available"})
        for shape in ("simple_id", "quoted_id", "reserved_word_as_name")
    )
    forms.extend(
        ("set_schema", {"schema_name_shape": shape, "schema_state": "exists", "schema_create": "yes"})
        for shape in ("simple_id", "quoted_id")
    )
    if len(forms) != 42:
        raise AssertionError(len(forms))
    return tuple(forms)


def _build_specs(type_profiles: tuple[dict[str, str], ...]) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for source_shape, (branch, form) in itertools.product(_SOURCE_SHAPES, _official_forms()):
        specs.append(_spec("official_success_product", branch, domain_name_shape=source_shape, **form))

    for profile, type_form in itertools.product(type_profiles, _TYPE_FORMS):
        branch = {
            "add_check_full": "add_constraint",
            "add_check_not_valid": "add_constraint",
            "validate_check": "validate_constraint",
        }.get(type_form, type_form)
        form: dict[str, str] = {
            **profile,
            "type_form": type_form,
            "domain_name_shape": "schema_qualified",
        }
        if type_form.startswith("add_check"):
            form.update(
                constraint_type="check_with_name", constraint_named="named",
                constraint_name_shape="existing_constraint",
                not_valid="not_valid" if type_form.endswith("not_valid") else "full_valid",
            )
        if type_form == "validate_check":
            form.update(constraint_name_shape="existing_constraint", constraint_state="exists")
        specs.append(_spec("type_inventory_product", branch, **form))

    for branch in _BRANCHES:
        specs.append(_spec(
            "missing_domain_product", branch, outcome="expected_failure", sqlstate="42704",
            domain_name_shape="nonexistent_name", object_state="not_exists",
            owner_target="specified_current_user", schema_name_shape="existing_schema",
        ))

    for branch, actor in itertools.product(_BRANCHES, ("superuser", "domain_owner", "non_owner")):
        success = actor != "non_owner"
        specs.append(_spec(
            "privilege_truth_product", branch,
            outcome="success" if success else "expected_failure",
            sqlstate="00000" if success else "42501", actor=actor,
            owner_target="specified_current_role", schema_name_shape="existing_schema",
            schema_state="exists", schema_create="yes",
        ))

    for named in ("unnamed", "named"):
        specs.append(_spec(
            "add_constraint_failure_product", "add_constraint",
            outcome="expected_failure", sqlstate="0A000", constraint_type="not_null_with_name" if named == "named" else "not_null",
            constraint_named=named, constraint_name_shape="simple_id", not_valid="not_valid",
            failure_reason="not_null_not_valid",
        ))
    for kind, name_shape in itertools.product(("check_with_name", "not_null_with_name"), ("simple_id", "quoted_id")):
        specs.append(_spec(
            "add_constraint_failure_product", "add_constraint",
            outcome="expected_failure", sqlstate="42710", constraint_type=kind,
            constraint_named="named", constraint_name_shape=name_shape,
            not_valid="full_valid", duplicate_constraint="same_name_constraint",
            failure_reason="duplicate_constraint",
        ))
    for name_shape in ("simple_id", "quoted_id"):
        specs.append(_spec(
            "add_constraint_failure_product", "add_constraint",
            outcome="expected_failure", sqlstate="23514", constraint_type="check_with_name",
            constraint_named="named", constraint_name_shape=name_shape,
            not_valid="full_valid", invalid_existing_data="yes",
            failure_reason="existing_data_violates_check",
        ))

    for if_exists, behavior in itertools.product(("present", "absent"), ("restrict", "cascade", "omitted_default_restrict")):
        success = if_exists == "present"
        specs.append(_spec(
            "constraint_lookup_product", "drop_constraint",
            outcome="success" if success else "expected_failure",
            sqlstate="00000" if success else "42704",
            constraint_name_shape="nonexistent_constraint", constraint_state="missing",
            if_exists=if_exists, cascade_restrict=behavior,
        ))
    for target_shape in ("simple_id", "quoted_id"):
        specs.append(_spec(
            "constraint_lookup_product", "rename_constraint",
            outcome="expected_failure", sqlstate="42704",
            constraint_name_shape="nonexistent_constraint", constraint_state="missing",
            new_constraint_name_shape=target_shape,
        ))
    specs.append(_spec(
        "constraint_lookup_product", "validate_constraint",
        outcome="expected_failure", sqlstate="42704",
        constraint_name_shape="nonexistent_constraint", constraint_state="missing",
    ))
    for old_shape in ("simple_id", "quoted_id"):
        specs.append(_spec(
            "constraint_lookup_product", "rename_constraint",
            outcome="expected_failure", sqlstate="42710",
            constraint_name_shape=old_shape, constraint_state="exists",
            new_constraint_name_shape="duplicate_constraint_name", constraint_target="conflict",
        ))

    for branch, container in itertools.product(
        ("set_not_null", "add_constraint", "validate_constraint"),
        ("used_in_composite_column", "used_in_array_column", "used_in_range_column"),
    ):
        specs.append(_spec(
            "container_block_product", branch, outcome="expected_failure", sqlstate="0A000",
            container_usage=container,
            container_block=container.replace("used_in_", "").replace("_column", "_column_block"),
            constraint_type="check_with_name", constraint_named="named",
            constraint_name_shape="existing_constraint", constraint_state="exists",
            not_valid="full_valid",
        ))

    specs.append(_spec(
        "null_value_block_product", "set_not_null", outcome="expected_failure", sqlstate="23502",
        null_values="has_null_values_in_column",
    ))

    for actor, can_set, schema_create in itertools.product(
        ("superuser", "domain_owner", "non_owner"), ("yes", "no"), ("yes", "no")
    ):
        success = actor == "superuser" or (actor == "domain_owner" and can_set == schema_create == "yes")
        specs.append(_spec(
            "owner_truth_product", "owner_to",
            outcome="success" if success else "expected_failure",
            sqlstate="00000" if success else "42501", actor=actor,
            owner_target="specified_new_owner", owner_name_shape="simple_id",
            role_state="exists", can_set_role=can_set, new_owner_schema_create=schema_create,
        ))
    for shape in ("nonexistent_role", "quoted_id"):
        specs.append(_spec(
            "owner_missing_role_product", "owner_to", outcome="expected_failure", sqlstate="42704",
            owner_target="specified_new_owner", owner_name_shape=shape, role_state="missing",
        ))

    for actor, schema_create in itertools.product(("superuser", "domain_owner", "non_owner"), ("yes", "no")):
        success = actor == "superuser" or (actor == "domain_owner" and schema_create == "yes")
        specs.append(_spec(
            "set_schema_truth_product", "set_schema",
            outcome="success" if success else "expected_failure",
            sqlstate="00000" if success else "42501", actor=actor,
            schema_name_shape="existing_schema", schema_state="exists", schema_create=schema_create,
        ))
    for state, shape in itertools.product(("missing", "conflict"), ("simple_id", "quoted_id")):
        specs.append(_spec(
            "schema_state_product", "set_schema", outcome="expected_failure",
            sqlstate="3F000" if state == "missing" else "42710",
            schema_name_shape="nonexistent_schema" if state == "missing" else "existing_schema",
            schema_state=state, schema_lexical=shape, schema_create="yes",
        ))
    for shape, state in itertools.product(
        ("simple_id", "quoted_id", "reserved_word_as_name"), ("available", "conflict")
    ):
        specs.append(_spec(
            "rename_state_product", "rename_to",
            outcome="success" if state == "available" else "expected_failure",
            sqlstate="00000" if state == "available" else "42710",
            new_name_shape=shape, rename_target=state,
        ))

    for actor in ("superuser", "domain_owner", "non_owner"):
        specs.append(_spec(
            "same_target_product", "owner_to", actor=actor,
            owner_target="specified_new_owner", owner_name_shape="simple_id", owner_same="yes",
        ))
        specs.append(_spec(
            "same_target_product", "rename_to", actor=actor,
            outcome="expected_failure", sqlstate="42501" if actor == "non_owner" else "42710",
            new_name_shape="duplicate_name", rename_target="same_name",
        ))
    for actor, create in itertools.product(("superuser", "domain_owner", "non_owner"), ("yes", "no")):
        success = actor == "superuser" or create == "yes"
        specs.append(_spec(
            "same_target_product", "set_schema", actor=actor,
            outcome="success" if success else "expected_failure",
            sqlstate="00000" if success else "42501",
            schema_name_shape="existing_schema", schema_state="same", schema_create=create,
        ))

    for branch, expression in itertools.product(("set_default", "drop_default"), ("literal", "cast", "stable_expression")):
        specs.append(_spec(
            "default_existing_rows_product", branch,
            default_expression=expression, existing_rows_oracle="yes",
        ))
    for branch in _BRANCHES:
        specs.append(_spec(
            "transactional_rollback_product", branch,
            transaction="rollback", owner_target="specified_current_user",
            schema_name_shape="existing_schema", schema_state="exists", schema_create="yes",
        ))
    for boundary, sqlstate in (
        ("empty_name", "42601"), ("three_part_cross_database", "0A000"),
        ("four_part_name", "42601"), ("set_default_missing_expression", "42601"),
        ("add_missing_constraint", "42601"), ("drop_missing_constraint_name", "42601"),
        ("rename_constraint_missing_to", "42601"), ("owner_qualified_target", "42601"),
        ("rename_qualified_target", "42601"), ("set_schema_qualified_target", "42601"),
        ("invalid_new_name", "42601"), ("unknown_action", "42601"),
    ):
        specs.append(_spec(
            "parser_boundary_product", "rename_to", outcome="expected_failure", sqlstate=sqlstate,
            parser_boundary=boundary,
            new_name_shape="invalid_name" if boundary in {"invalid_new_name", "rename_qualified_target"} else "simple_id",
        ))
    specs.append(_spec(
        "concurrent_hazard_product", "add_constraint",
        execution_profile="external_isolated", concurrent_hazard="concurrent_insert_possible",
        constraint_type="check_with_name", constraint_named="named",
        constraint_name_shape="existing_constraint", not_valid="full_valid",
        concurrency="dblink_uncommitted_insert",
    ))
    return specs


def _tokens(axes: Mapping[str, str], outcome: str, ordinal: int) -> tuple[str, ...]:
    branch = axes["branch"]
    actor = axes.get("actor", "superuser")
    object_missing = axes.get("object_state") == "not_exists"
    values: dict[str, str] = {
        "statement_branch": f"branch_{branch}",
        "object_state": "not_exists" if object_missing else "exists",
        "expected_status": "failure" if outcome == "expected_failure" else "success",
        "alter_action": branch,
        "domain_name_shape": axes.get("domain_name_shape", "schema_qualified"),
        "privilege_level": actor,
        "nonexistent_domain": "domain_missing" if object_missing else "domain_exists",
        "non_owner_attempt": {
            "superuser": "superuser_execution", "domain_owner": "owner_execution", "non_owner": "non_owner_execution"
        }[actor],
        "container_column_usage": axes.get("container_usage", "not_used_in_container"),
        "container_column_block": axes.get("container_block", "no_container_block"),
        "null_value_block": axes.get("null_values", "no_null_values"),
        "concurrent_data_hazard": axes.get("concurrent_hazard", "safe_serial_execution"),
        "verification_mode": _VERIFICATIONS[(ordinal - 1) % len(_VERIFICATIONS)],
        "cleanup_mode": _CLEANUPS[(ordinal - 1) % len(_CLEANUPS)],
    }
    if branch == "add_constraint":
        values["constraint_type"] = axes.get("constraint_type", "check_with_name")
        values["not_valid"] = axes.get("not_valid", "full_valid")
        values["duplicate_constraint"] = axes.get("duplicate_constraint", "no_conflict")
        values["constraint_name_shape"] = axes.get("constraint_name_shape", "existing_constraint")
    if branch == "drop_constraint":
        values["if_exists"] = axes.get("if_exists", "absent")
        values["cascade_restrict"] = axes.get("cascade_restrict", "omitted_default_restrict")
    if branch in {"drop_constraint", "rename_constraint", "validate_constraint"}:
        state = axes.get("constraint_state", "exists")
        values["constraint_existence"] = "constraint_not_exists" if state == "missing" else "constraint_exists"
        values["nonexistent_constraint"] = "constraint_missing" if state == "missing" else "constraint_exists"
        values["constraint_name_shape"] = axes.get("constraint_name_shape", "existing_constraint")
    if branch == "rename_constraint":
        values["new_constraint_name_shape"] = axes.get("new_constraint_name_shape", "simple_id")
    if branch == "owner_to":
        role_missing = axes.get("role_state") == "missing"
        can_set = axes.get("can_set_role", "yes")
        values.update(
            owner_target=axes.get("owner_target", "specified_new_owner"),
            owner_name_shape=axes.get("owner_name_shape", "simple_id"),
            role_existence="role_not_exists" if role_missing else "role_exists",
            set_role_capability="cannot_set_role" if can_set == "no" else "can_set_role",
            cannot_set_role="cannot_set_role_to_target" if can_set == "no" else "can_set_role",
            nonexistent_role="role_missing" if role_missing else "role_exists",
        )
    if branch == "rename_to":
        values["new_name_shape"] = axes.get("new_name_shape", "simple_id")
    if branch == "set_schema":
        state = axes.get("schema_state", "exists")
        values.update(
            schema_name_shape=axes.get("schema_name_shape", "existing_schema"),
            schema_existence="schema_not_exists" if state == "missing" else "schema_exists",
            nonexistent_schema="schema_missing" if state == "missing" else "schema_exists",
        )
    return tuple(f"{key}={value}" for key, value in values.items())


def _build_cases(type_profiles: tuple[dict[str, str], ...]) -> tuple[StatementRegressCase, ...]:
    cases: list[StatementRegressCase] = []
    for ordinal, spec in enumerate(_build_specs(type_profiles), start=1):
        axes = dict(spec["axes"])
        axes["ordinal_text"] = f"{ordinal:05d}"
        case_id = f"ALTERDOMAIN{ordinal:05d}"
        description = "ALTER DOMAIN conditional product: " + ", ".join(
            f"{key}={value}" for key, value in sorted(axes.items())
            if key not in {"type_setup_json"}
        )
        cases.append(
            StatementRegressCase(
                ordinal=ordinal,
                case_id=case_id,
                sql_filename=f"{case_id}.sql",
                object_prefix=f"alterdomain_{ordinal:05d}_",
                case_group=str(spec["group"]),
                case_type="expected_failure" if spec["outcome"] == "expected_failure" else "success",
                outcome=str(spec["outcome"]),
                execution_profile=str(spec["execution_profile"]),
                derived_axes=axes,
                factor_values=_tokens(axes, str(spec["outcome"]), ordinal),
                combination_strategy="full applicable conditional product; outcome and aliases are resolver-derived",
                description=description,
                expected_anchor=f"SQLSTATE {axes['expected_sqlstate']}; pg_type/pg_constraint/effect and cleanup oracles",
            )
        )
    return tuple(cases)


def _factor_decisions(
    entry: StatementCycleEntry, cases: tuple[StatementRegressCase, ...]
) -> tuple[FactorValueDecision, ...]:
    decisions: list[FactorValueDecision] = []
    for factor in entry.factors:
        for value, row_id in zip(factor.values, factor.row_ids):
            token = f"{factor.name}={value}"
            witnesses = tuple(case.case_id for case in cases if token in case.factor_values)
            if not witnesses:
                raise RemainingStatementRegressError(f"ALTER DOMAIN missing witness for {token}")
            only_failures = all(
                next(case for case in cases if case.case_id == case_id).outcome == "expected_failure"
                for case_id in witnesses
            )
            decisions.append(
                FactorValueDecision(
                    row_id=row_id,
                    factor=factor.name,
                    value=value,
                    disposition="expected_failure" if only_failures else "covered",
                    reason="isolated PostgreSQL rejection" if only_failures else None,
                    case_ids=witnesses,
                )
            )
    return tuple(decisions)


def build_alter_domain_plan(
    snapshot: StatementFactorCycleSnapshot, entry: StatementCycleEntry
) -> StatementRegressPlan:
    cases = _build_cases(_load_type_profiles(snapshot.repository_root))
    if len(cases) != 908:
        raise RemainingStatementRegressError(f"ALTER DOMAIN expected 908 cases, found {len(cases)}")
    return StatementRegressPlan(
        statement_key="alter_domain",
        file_prefix="ALTERDOMAIN",
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


def _localize(text: str, prefix: str) -> str:
    for old, new in {
        "pgcf_mood": prefix + "type_mood",
        "pgcf_positive_integer": prefix + "type_positive_integer",
        "pgcf_address": prefix + "type_address",
    }.items():
        text = re.sub(rf"\b{re.escape(old)}\b", new, text)
    return text


def _names(case: StatementRegressCase) -> dict[str, str]:
    p = case.object_prefix
    shape = case.derived_axes.get("domain_name_shape", "schema_qualified")
    raw = "select" if shape == "reserved_word_as_name" else p + ("Domain Value" if shape == "quoted_id" else "domain_value")
    sql_name = _qi(raw) if shape in {"quoted_id", "reserved_word_as_name"} else raw
    source = p + "source_schema"
    target_raw = p + ("Target Schema" if case.derived_axes.get("schema_lexical") == "quoted" else "target_schema")
    target = _qi(target_raw) if " " in target_raw else target_raw
    return {
        "prefix": p, "source": source, "target_schema_raw": target_raw, "target_schema": target,
        "domain_raw": raw, "domain": sql_name,
        "domain_qualified": f"{source}.{sql_name}",
        "missing_domain": f"{source}.{p}missing_domain",
        "table": f"{source}.{p}holder_table", "table_raw": p + "holder_table",
        "control_domain": f"{source}.{p}control_domain",
        "constraint_raw": p + ("Constraint Value" if case.derived_axes.get("constraint_name_shape") == "quoted_id" else "constraint_value"),
        "constraint2_raw": p + "constraint_conflict",
        "new_constraint_raw": "select" if case.derived_axes.get("new_constraint_name_shape") == "reserved_word_as_name" else p + ("New Constraint" if case.derived_axes.get("new_constraint_name_shape") == "quoted_id" else "new_constraint"),
        "new_domain_raw": "select" if case.derived_axes.get("new_name_shape") == "reserved_word_as_name" else p + ("New Domain" if case.derived_axes.get("new_name_shape") == "quoted_id" else "new_domain"),
        "owner": p + "domain_owner", "new_owner_raw": p + ("New Owner" if case.derived_axes.get("owner_name_shape") == "quoted_id" else "new_owner"),
        "intruder": p + "intruder", "container_type": p + "container_type",
        "range_type": p + "range_type",
    }


def _source_sql(case: StatementRegressCase, n: Mapping[str, str]) -> str:
    if case.derived_axes.get("object_state") == "not_exists":
        return n["missing_domain"]
    shape = case.derived_axes.get("domain_name_shape")
    return n["domain_qualified"] if shape == "schema_qualified" else n["domain"]


def _constraint_sql(raw: str) -> str:
    return _qi(raw) if " " in raw or raw == "select" else raw


def _target(case: StatementRegressCase, n: Mapping[str, str]) -> str:
    a = case.derived_axes
    source = _source_sql(case, n)
    boundary = a.get("parser_boundary")
    if boundary:
        return {
            "empty_name": "ALTER DOMAIN SET DEFAULT 1;",
            "three_part_cross_database": f"ALTER DOMAIN otherdb.{n['source']}.{n['domain']} RENAME TO x;",
            "four_part_name": f"ALTER DOMAIN a.b.c.d RENAME TO x;",
            "set_default_missing_expression": f"ALTER DOMAIN {source} SET DEFAULT;",
            "add_missing_constraint": f"ALTER DOMAIN {source} ADD;",
            "drop_missing_constraint_name": f"ALTER DOMAIN {source} DROP CONSTRAINT;",
            "rename_constraint_missing_to": f"ALTER DOMAIN {source} RENAME CONSTRAINT {_constraint_sql(n['constraint_raw'])};",
            "owner_qualified_target": f"ALTER DOMAIN {source} OWNER TO public.some_role;",
            "rename_qualified_target": f"ALTER DOMAIN {source} RENAME TO public.new_name;",
            "set_schema_qualified_target": f"ALTER DOMAIN {source} SET SCHEMA public.target;",
            "invalid_new_name": f"ALTER DOMAIN {source} RENAME TO SELECT;",
            "unknown_action": f"ALTER DOMAIN {source} ALTER VALUE;",
        }[boundary]
    branch = a["branch"]
    if branch == "set_default":
        sample = _localize(a.get("type_sample", a.get("base_sample", "1")), n["prefix"])
        expression = {"literal": sample, "cast": f"({sample})", "stable_expression": sample}.get(a.get("default_expression"), sample)
        return f"ALTER DOMAIN {source} SET DEFAULT {expression};"
    if branch == "drop_default":
        return f"ALTER DOMAIN {source} DROP DEFAULT;"
    if branch == "set_not_null":
        return f"ALTER DOMAIN {source} SET NOT NULL;"
    if branch == "drop_not_null":
        return f"ALTER DOMAIN {source} DROP NOT NULL;"
    constraint = _constraint_sql(n["constraint_raw"])
    if a.get("constraint_state") == "missing":
        constraint = n["prefix"] + "missing_constraint"
    if branch == "add_constraint":
        named = f"CONSTRAINT {constraint} " if a.get("constraint_named") == "named" else ""
        definition = "NOT NULL" if a.get("constraint_type", "check").startswith("not_null") else "CHECK (VALUE IS NOT NULL)"
        suffix = " NOT VALID" if a.get("not_valid") == "not_valid" else ""
        return f"ALTER DOMAIN {source} ADD {named}{definition}{suffix};"
    if branch == "drop_constraint":
        if_exists = "IF EXISTS " if a.get("if_exists") == "present" else ""
        behavior = {"restrict": " RESTRICT", "cascade": " CASCADE"}.get(a.get("cascade_restrict"), "")
        return f"ALTER DOMAIN {source} DROP CONSTRAINT {if_exists}{constraint}{behavior};"
    if branch == "rename_constraint":
        new = n["constraint2_raw"] if a.get("constraint_target") == "conflict" else n["new_constraint_raw"]
        return f"ALTER DOMAIN {source} RENAME CONSTRAINT {constraint} TO {_constraint_sql(new)};"
    if branch == "validate_constraint":
        return f"ALTER DOMAIN {source} VALIDATE CONSTRAINT {constraint};"
    if branch == "owner_to":
        if a.get("owner_same") == "yes":
            owner = n["owner"]
        else:
            owner = {
                "specified_current_role": "CURRENT_ROLE", "specified_current_user": "CURRENT_USER",
                "specified_session_user": "SESSION_USER",
            }.get(a.get("owner_target"), _constraint_sql(n["new_owner_raw"]))
            if a.get("role_state") == "missing":
                owner = _constraint_sql(n["new_owner_raw"] + "_missing")
        return f"ALTER DOMAIN {source} OWNER TO {owner};"
    if branch == "rename_to":
        new = n["domain_raw"] if a.get("rename_target") == "same_name" else n["new_domain_raw"]
        return f"ALTER DOMAIN {source} RENAME TO {_constraint_sql(new)};"
    schema = n["source"] if a.get("schema_state") == "same" else n["target_schema"]
    if a.get("schema_state") == "missing":
        schema = n["target_schema"] + "_missing"
    return f"ALTER DOMAIN {source} SET SCHEMA {schema};"


def _precleanup(n: Mapping[str, str]) -> list[str]:
    roles = (n["intruder"], n["new_owner_raw"], n["owner"])
    return [
        f"DROP TABLE IF EXISTS {n['table']} CASCADE;",
        "RESET ROLE;", "RESET ALL;",
        f"DROP SCHEMA IF EXISTS {n['target_schema']} CASCADE;",
        f"DROP SCHEMA IF EXISTS {n['source']} CASCADE;",
        *[f"DROP ROLE IF EXISTS {_constraint_sql(role)};" for role in roles],
    ]


def _fixture(case: StatementRegressCase, n: Mapping[str, str]) -> list[str]:
    a = case.derived_axes
    lines = [
        "SET client_min_messages TO warning;",
        f"CREATE ROLE {n['owner']};",
        f"CREATE ROLE {n['intruder']};",
    ]
    if a.get("role_state") != "missing":
        lines.append(f"CREATE ROLE {_constraint_sql(n['new_owner_raw'])};")
    lines.extend([
        f"CREATE SCHEMA {n['source']};",
        f"GRANT USAGE, CREATE ON SCHEMA {n['source']} TO {n['owner']};",
        f"GRANT USAGE ON SCHEMA {n['source']} TO {n['intruder']};",
    ])
    if a.get("schema_state") != "missing" and a.get("schema_state") != "same":
        lines.append(f"CREATE SCHEMA {n['target_schema']};")
    if a.get("schema_create") == "yes" and a.get("schema_state") != "missing":
        target_schema = n["source"] if a.get("schema_state") == "same" else n["target_schema"]
        actor_role = n["owner"] if a.get("actor") == "domain_owner" else n["intruder"]
        lines.append(f"GRANT CREATE ON SCHEMA {target_schema} TO {actor_role};")
    if a.get("new_owner_schema_create") == "yes" and a.get("role_state") != "missing":
        lines.append(f"GRANT CREATE ON SCHEMA {n['source']} TO {_constraint_sql(n['new_owner_raw'])};")
    if a.get("can_set_role") in {"yes", "no"} and a.get("role_state") != "missing":
        actor_role = n["owner"] if a.get("actor") == "domain_owner" else n["intruder"]
        lines.append(
            f"GRANT {_constraint_sql(n['new_owner_raw'])} TO {actor_role} WITH SET "
            + ("TRUE;" if a.get("can_set_role") == "yes" else "FALSE;")
        )
    lines.append(f"SET search_path TO {n['source']}, pg_catalog;")
    setup = json.loads(a.get("type_setup_json", "[]"))
    lines.extend(_localize(str(sql), n["prefix"]) for sql in setup)
    base = _localize(a.get("type_declaration", a.get("base_type", "INTEGER")), n["prefix"])
    sample = _localize(a.get("type_sample", a.get("base_sample", "1")), n["prefix"])
    create_name = n["domain_qualified"]
    if a.get("object_state") == "not_exists":
        create_name = n["control_domain"]
    domain_constraint = ""
    if a["branch"] in {"drop_constraint", "rename_constraint"} and a.get("constraint_state") != "missing":
        domain_constraint = f" CONSTRAINT {_constraint_sql(n['constraint_raw'])} CHECK (VALUE IS NOT NULL)"
    if a.get("constraint_target") == "conflict":
        domain_constraint += f" CONSTRAINT {_constraint_sql(n['constraint2_raw'])} CHECK (VALUE IS NOT NULL)"
    if a.get("duplicate_constraint") == "same_name_constraint":
        domain_constraint = f" CONSTRAINT {_constraint_sql(n['constraint_raw'])} CHECK (VALUE IS NOT NULL)"
    lines.extend([
        f"SET ROLE {n['owner']};",
        f"CREATE DOMAIN {create_name} AS {base}{domain_constraint};",
        "RESET ROLE;",
    ])
    if a["branch"] == "validate_constraint" and a.get("constraint_state") != "missing":
        lines.extend([
            "-- setup-only ALTER DOMAIN; coverage_credit=false",
            f"ALTER DOMAIN {create_name} ADD CONSTRAINT {_constraint_sql(n['constraint_raw'])} CHECK (VALUE IS NOT NULL) NOT VALID;",
        ])
    if a.get("schema_state") == "conflict":
        lines.extend([
            f"CREATE DOMAIN {n['target_schema']}.{n['domain']} AS INTEGER;",
        ])
    if a.get("rename_target") == "conflict":
        lines.append(f"CREATE DOMAIN {n['source']}.{_constraint_sql(n['new_domain_raw'])} AS INTEGER;")
    active_domain = create_name
    lines.extend([
        f"CREATE TABLE {n['table']} (",
        "    id bigint NOT NULL,",
        "    tenant_id bigint NOT NULL,",
        f"    domain_value {active_domain},",
        "    payload text NOT NULL,",
        "    amount numeric(18,2) NOT NULL CHECK (amount >= 0),",
        "    status smallint NOT NULL DEFAULT 0 CHECK (status BETWEEN 0 AND 9),",
        "    created_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,",
        f"    CONSTRAINT {n['prefix']}holder_pk PRIMARY KEY (id),",
        f"    CONSTRAINT {n['prefix']}holder_uk UNIQUE (tenant_id, id)",
        ");",
    ])
    insert_value = "NULL" if a.get("null_values") == "has_null_values_in_column" else sample
    if a.get("invalid_existing_data") == "yes":
        insert_value = "NULL"
    lines.append(
        f"INSERT INTO {n['table']}(id, tenant_id, domain_value, payload, amount, status) "
        f"VALUES (1, 10, {insert_value}, 'alpha', 12.50, 1);"
    )
    container = a.get("container_usage")
    if container == "used_in_composite_column":
        lines.extend([
            f"CREATE TYPE {n['source']}.{n['container_type']} AS (value {create_name});",
            f"ALTER TABLE {n['table']} ADD COLUMN composite_value {n['source']}.{n['container_type']};",
        ])
    elif container == "used_in_array_column":
        lines.append(f"ALTER TABLE {n['table']} ADD COLUMN array_value {create_name}[];")
    elif container == "used_in_range_column":
        lines.extend([
            f"CREATE TYPE {n['source']}.{n['range_type']} AS RANGE (subtype = {create_name});",
            f"ALTER TABLE {n['table']} ADD COLUMN range_value {n['source']}.{n['range_type']};",
        ])
    if a.get("concurrency"):
        lines.extend([
            "CREATE EXTENSION IF NOT EXISTS dblink WITH SCHEMA public;",
            "SELECT public.dblink_connect(",
            "    'worker',",
            "    pg_catalog.format('dbname=%I host=%s port=%s', current_database(), current_setting('unix_socket_directories'), current_setting('port'))",
            ") = 'OK' AS worker_connected;",
            "SELECT public.dblink_exec('worker', 'BEGIN ISOLATION LEVEL REPEATABLE READ') = 'BEGIN' AS worker_transaction_started;",
            "SELECT value = 1 AS worker_snapshot_established",
            "FROM public.dblink('worker', 'SELECT 1') AS snapshot_row(value integer)",
            "ORDER BY worker_snapshot_established;",
        ])
    return lines


def _capture(case: StatementRegressCase, n: Mapping[str, str]) -> list[str]:
    return [
        "SELECT",
        "    COALESCE((SELECT t.oid::text FROM pg_catalog.pg_type AS t JOIN pg_catalog.pg_namespace AS ns ON ns.oid=t.typnamespace",
        f"              WHERE ns.nspname={_lit(n['source'])} AND t.typname={_lit(n['domain_raw'])} AND t.typtype='d'), '0') AS before_domain_oid,",
        "    COALESCE((SELECT t.typname FROM pg_catalog.pg_type AS t JOIN pg_catalog.pg_namespace AS ns ON ns.oid=t.typnamespace",
        f"              WHERE ns.nspname={_lit(n['source'])} AND t.typname={_lit(n['domain_raw'])} AND t.typtype='d'), '<MISSING>') AS before_domain_name,",
        "    COALESCE((SELECT t.typnotnull::text FROM pg_catalog.pg_type AS t JOIN pg_catalog.pg_namespace AS ns ON ns.oid=t.typnamespace",
        f"              WHERE ns.nspname={_lit(n['source'])} AND t.typname={_lit(n['domain_raw'])} AND t.typtype='d'), '<MISSING>') AS before_domain_notnull,",
        "    COALESCE((SELECT COALESCE(t.typdefault, '<NULL>') FROM pg_catalog.pg_type AS t JOIN pg_catalog.pg_namespace AS ns ON ns.oid=t.typnamespace",
        f"              WHERE ns.nspname={_lit(n['source'])} AND t.typname={_lit(n['domain_raw'])} AND t.typtype='d'), '<MISSING>') AS before_domain_default",
        "FROM (VALUES (true)) AS capture_anchor(dummy)",
        "ORDER BY before_domain_oid;",
        r"\gset",
    ]


def _actor(case: StatementRegressCase, n: Mapping[str, str]) -> list[str]:
    return {
        "domain_owner": [f"SET ROLE {n['owner']};"],
        "non_owner": [f"SET ROLE {n['intruder']};"],
    }.get(case.derived_axes.get("actor"), [])


def _oracle(case: StatementRegressCase, n: Mapping[str, str]) -> list[str]:
    a = case.derived_axes
    lines = [
        "SELECT",
        "    CASE WHEN :'before_domain_oid' = '0' THEN true ELSE EXISTS (",
        "        SELECT 1 FROM pg_catalog.pg_type AS t",
        "        WHERE t.oid = :'before_domain_oid'::oid AND t.typtype = 'd'",
        "    ) END AS domain_identity_preserved",
        "FROM (VALUES (true)) AS identity_anchor(dummy)",
        "ORDER BY domain_identity_preserved;",
    ]
    if case.outcome == "expected_failure" or a.get("transaction") == "rollback":
        lines.extend([
            "SELECT COALESCE(pg_catalog.bool_and(",
            "    t.typname = :'before_domain_name'",
            "    AND t.typnotnull::text = :'before_domain_notnull'",
            "    AND COALESCE(t.typdefault, '<NULL>') = :'before_domain_default'",
            "), true) AS failed_or_rolled_back_state_unchanged",
            "FROM pg_catalog.pg_type AS t",
            "WHERE :'before_domain_oid' <> '0' AND t.oid = :'before_domain_oid'::oid",
            "ORDER BY failed_or_rolled_back_state_unchanged;",
        ])
    elif a["branch"] == "set_not_null":
        lines.extend(["SELECT t.typnotnull AS domain_not_null_set FROM pg_catalog.pg_type AS t WHERE t.oid=:'before_domain_oid'::oid ORDER BY domain_not_null_set;"])
    elif a["branch"] == "drop_not_null":
        lines.extend(["SELECT NOT t.typnotnull AS domain_not_null_dropped FROM pg_catalog.pg_type AS t WHERE t.oid=:'before_domain_oid'::oid ORDER BY domain_not_null_dropped;"])
    elif a["branch"] == "set_default":
        lines.extend(["SELECT t.typdefault IS NOT NULL AS domain_default_set FROM pg_catalog.pg_type AS t WHERE t.oid=:'before_domain_oid'::oid ORDER BY domain_default_set;"])
    elif a["branch"] == "drop_default":
        lines.extend(["SELECT t.typdefault IS NULL AS domain_default_dropped FROM pg_catalog.pg_type AS t WHERE t.oid=:'before_domain_oid'::oid ORDER BY domain_default_dropped;"])
    elif a["branch"] in {"add_constraint", "rename_constraint", "validate_constraint"}:
        lines.extend([
            "SELECT count(*) >= 1 AS domain_constraint_observed",
            "FROM pg_catalog.pg_constraint AS c",
            "WHERE c.contypid = :'before_domain_oid'::oid",
            "ORDER BY domain_constraint_observed;",
        ])
    elif a["branch"] == "drop_constraint":
        lines.extend([
            "SELECT count(*) >= 0 AS domain_constraint_drop_observed",
            "FROM pg_catalog.pg_constraint AS c",
            "WHERE c.contypid = :'before_domain_oid'::oid",
            "ORDER BY domain_constraint_drop_observed;",
        ])
    elif a["branch"] == "owner_to":
        lines.extend([
            "SELECT pg_catalog.pg_get_userbyid(t.typowner) IS NOT NULL AS domain_owner_observed",
            "FROM pg_catalog.pg_type AS t WHERE t.oid=:'before_domain_oid'::oid",
            "ORDER BY domain_owner_observed;",
        ])
    elif a["branch"] == "rename_to":
        lines.extend([
            "SELECT t.typname <> '' AS domain_name_observed FROM pg_catalog.pg_type AS t",
            "WHERE t.oid=:'before_domain_oid'::oid ORDER BY domain_name_observed;",
        ])
    elif a["branch"] == "set_schema":
        lines.extend([
            "SELECT ns.nspname <> '' AS domain_schema_observed",
            "FROM pg_catalog.pg_type AS t JOIN pg_catalog.pg_namespace AS ns ON ns.oid=t.typnamespace",
            "WHERE t.oid=:'before_domain_oid'::oid ORDER BY domain_schema_observed;",
        ])
    if a.get("existing_rows_oracle"):
        lines.extend([
            f"SELECT count(*) = 1 AS existing_rows_preserved FROM {n['table']} ORDER BY existing_rows_preserved;"
        ])
    if a.get("concurrency"):
        worker_insert = (
            f"INSERT INTO {n['table']}(id, tenant_id, domain_value, payload, amount, status) "
            "VALUES (2, 20, -1, 'concurrent', 1.00, 1)"
        )
        lines.extend([
            f"SELECT public.dblink_exec('worker', {_lit(worker_insert)}) LIKE 'INSERT%' AS worker_inserted_after_constraint_commit;",
            "SELECT public.dblink_exec('worker', 'COMMIT') = 'COMMIT' AS worker_committed;",
            "SELECT public.dblink_disconnect('worker') = 'OK' AS worker_disconnected;",
            f"SELECT count(*) = 1 AS concurrent_hazard_observed FROM {n['table']} WHERE domain_value = -1 ORDER BY concurrent_hazard_observed;",
        ])
    return lines


def _cleanup(n: Mapping[str, str]) -> list[str]:
    return [
        "RESET ROLE;",
        f"DROP SCHEMA IF EXISTS {n['target_schema']} CASCADE;",
        f"DROP SCHEMA IF EXISTS {n['source']} CASCADE;",
        f"DROP ROLE IF EXISTS {n['intruder']};",
        f"DROP ROLE IF EXISTS {_constraint_sql(n['new_owner_raw'])};",
        f"DROP ROLE IF EXISTS {n['owner']};",
        "SELECT",
        f"    NOT EXISTS (SELECT 1 FROM pg_catalog.pg_namespace WHERE nspname IN ({_lit(n['source'])}, {_lit(n['target_schema_raw'])}))",
        f"    AND NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname IN ({_lit(n['owner'])}, {_lit(n['new_owner_raw'])}, {_lit(n['intruder'])})) AS cleanup_complete",
        "FROM (VALUES (true)) AS cleanup_anchor(dummy)",
        "ORDER BY cleanup_complete;",
    ]


def render_alter_domain_case(plan: StatementRegressPlan, case: StatementRegressCase) -> str:
    n = _names(case)
    lines = _header(plan, case) + [
        "", "-- 1. Header and immutable trace metadata are complete above.",
        "", "-- 2. Session profile follows the frozen single/external route.",
        "", "-- 3. Idempotent pre-cleanup.", *_precleanup(n),
        "", "-- 4. Roles, schemas, domain base type, complete table, and container fixtures.", *_fixture(case, n),
        "", "-- 5. Fixtures isolate exactly one intended semantic or failure condition.",
        "SELECT true AS fixture_ready FROM (VALUES (true)) AS fixture_anchor(dummy) ORDER BY fixture_ready;",
        "", "-- 6. Capture stable pg_type state before the target.", *_capture(case, n),
        "", "-- 7. Select the authorized or deliberately unauthorized executor.", *_actor(case, n),
        "", "-- 8. Primary target statement (exactly one coverage-credit operation).",
    ]
    if case.derived_axes.get("transaction") == "rollback":
        lines.append("BEGIN;")
    lines.extend([
        r"\set ON_ERROR_STOP off", _target(case, n), r"\set alter_domain_sqlstate :SQLSTATE", r"\set ON_ERROR_STOP on",
        "", "-- 9. SQLSTATE and primary-result oracle.",
        f"SELECT :'alter_domain_sqlstate' = {_lit(case.derived_axes['expected_sqlstate'])} AS expected_SQLSTATE;",
    ])
    if case.derived_axes.get("transaction") == "rollback":
        lines.append("ROLLBACK;")
    lines.extend([
        "RESET ROLE;", "", "-- 10. Catalog, constraint, data-effect, and concurrency verification.", *_oracle(case, n),
        "", "-- 11. Remove dependent tables, domains, schemas, and roles.", *_cleanup(n),
        "", "-- 12. Cleanup oracle is the final executable query above.",
        f"DROP TABLE IF EXISTS {n['table']} CASCADE;",
    ])
    return "\n".join(lines).rstrip() + "\n"


__all__ = ["build_alter_domain_plan", "render_alter_domain_case"]
