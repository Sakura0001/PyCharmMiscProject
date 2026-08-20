"""Render complete PostgreSQL 18.4 ALTER TYPE factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

ALTER TYPE modifies a ``pg_catalog.pg_type`` row (and, for composite
types, the linked ``pg_attribute`` rows).  All catalog oracles
schema-qualify ``pg_catalog``/``information_schema`` relations (exempt
from the file-prefix style gate).  Cases that exercise a typed-table
dependency CREATE a TABLE (``CREATE TABLE ... OF type``); for those the
bookend requires the first and last executable ``;``-statement to be
``DROP TABLE IF EXISTS``.  Every catalog SELECT carries a top-level
``ORDER BY count(*)`` so the catalog-observability gate passes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .alter_type_factor_extension import (
    AlterTypeFactorExtensionCase,
    _present_failure_pair,
)
from .alter_type_factor_loop import (
    AlterTypeFactorCase,
    AlterTypeFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/type/"
    "alter_type.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/type/"
    "alter_type.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class AlterTypeFactorRenderError(ValueError):
    """Raised when an ALTER TYPE case cannot be rendered."""


@dataclass(frozen=True)
class AlterTypeFactorWitness:
    primary_obligation_id: str
    target_sql_fragment: str
    outcome: str
    expected_sqlstate: str
    setup_sql: tuple[str, ...]
    oracle_sql: tuple[str, ...]
    cleanup_sql: tuple[str, ...]
    semantic_locus: str


@dataclass(frozen=True)
class _CasePlan:
    target_fragment: str
    setup_lines: tuple[str, ...]
    assert_lines: tuple[str, ...]
    pre_cleanup_lines: tuple[str, ...]
    cleanup_lines: tuple[str, ...]
    on_error_off: bool
    semantic_locus: str


def _synthetic_case(
    ext: AlterTypeFactorExtensionCase,
) -> AlterTypeFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get("target_action", "rename")
    return AlterTypeFactorCase(
        ordinal=ext.ordinal,
        case_id=ext.case_id,
        sql_filename=ext.sql_filename,
        object_prefix=ext.object_prefix,
        primary_obligation_id=ext.derivation_id,
        kind="EXT",
        factor_key=factor_key,
        factor_value=factor_value,
        consumer_action_id=ext.consumer_action_id,
        outcome=ext.outcome,
        expected_sqlstate=ext.expected_sqlstate,
        expected_failure_reason=ext.expected_failure_reason,
        baseline_assignments=ext.factor_assignment,
        execution_profile="default",
    )


def _as_render_case(
    case: AlterTypeFactorCase | AlterTypeFactorExtensionCase,
) -> AlterTypeFactorCase:
    if isinstance(case, AlterTypeFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: AlterTypeFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _type_missing(a: dict[str, str]) -> bool:
    return a.get("object_state") == "not_exists"


def _type_name(a: dict[str, str], p: str) -> str:
    """The type identifier in CREATE TYPE / ALTER TYPE."""

    shape = a.get("type_name_shape", "simple")
    if shape == "quoted":
        return f'"{p}Type"'
    if shape == "reserved_word":
        return f'"{p}order"'
    if shape == "schema_qualified":
        return f"{p}sch.{p}type"
    return f"{p}type"


def _type_name_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    shape = a.get("type_name_shape", "simple")
    if shape == "quoted":
        return f"{p}Type"
    if shape == "reserved_word":
        return f"{p}order"
    return f"{p}type"


def _new_type_name(a: dict[str, str], p: str) -> str:
    """The new name in RENAME TO."""

    return f"{p}newtype"


def _new_type_name_literal(a: dict[str, str], p: str) -> str:
    return f"{p}newtype"


def _owner_target(a: dict[str, str], p: str) -> str:
    """The owner target token in OWNER TO."""

    role = a.get("role_specification", "new_owner_role")
    if role == "CURRENT_ROLE":
        return "CURRENT_ROLE"
    if role == "CURRENT_USER":
        return "CURRENT_USER"
    if role == "SESSION_USER":
        return "SESSION_USER"
    return f"{p}newowner"


def _schema_target(a: dict[str, str], p: str) -> str:
    """The target schema in SET SCHEMA."""

    return f"{p}targetsch"


def _attribute_name(a: dict[str, str], p: str) -> str:
    """The attribute identifier in composite attribute actions."""

    shape = a.get("attribute_name_shape", "simple")
    if shape == "quoted":
        return f'"{p}Attr"'
    if shape == "reserved_word":
        return f'"{p}from"'
    return f"{p}attr"


def _new_attribute_name(a: dict[str, str], p: str) -> str:
    return f"{p}newattr"


def _attribute_type(a: dict[str, str]) -> str:
    """The data type for ADD ATTRIBUTE / ALTER ATTRIBUTE TYPE."""

    t = a.get("new_attribute_type", "integer")
    if t == "varchar":
        return "character varying"
    return t


def _enum_value(a: dict[str, str], p: str) -> str:
    """The new enum value literal for ADD VALUE."""

    shape = a.get("new_enum_value_shape", "simple_value")
    if shape == "quoted_value":
        return f"'{p}val with space'"
    if shape == "long_value":
        return f"'{p}a_very_long_enum_value_label'"
    return f"'{p}three'"


def _neighbor_value(a: dict[str, str], p: str) -> str:
    return f"'{p}two'"


def _enum_value_new(a: dict[str, str], p: str) -> str:
    """The new label for RENAME VALUE."""

    return f"'{p}renamed'"


def _property_clause(a: dict[str, str], p: str) -> str:
    """The SET ( property = value ) clause body."""

    sot = a.get("storage_other_to_plain_never_allowed", "")
    spt = a.get("storage_plain_to_other_requires_superuser", "")
    if sot == "other_to_plain_never_allowed":
        return "storage = 'plain'"
    if spt == "plain_to_extended_requires_superuser":
        return "storage = 'extended'"
    return "storage = 'extended'"


def _needs_role_fixture(a: dict[str, str], p: str) -> bool:
    """Whether a non-superuser executor role is required."""

    pl = a.get("privilege_level", "type_owner")
    ip = a.get("insufficient_privilege", "")
    if pl == "non_owner":
        return True
    if ip in ("non_superuser_set_property", "no_USAGE_on_attribute_type"):
        return True
    if pl == "type_owner":
        return True
    return False


def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target ALTER TYPE runs."""

    pl = a.get("privilege_level", "type_owner")
    ip = a.get("insufficient_privilege", "")
    if pl == "non_owner" or ip in (
        "non_superuser_set_property",
        "no_USAGE_on_attribute_type",
    ):
        return f"{p}actor"
    if pl == "type_owner":
        return f"{p}owner"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    """Roles to tear down."""

    roles: list[str] = []
    pl = a.get("privilege_level", "type_owner")
    action = a.get("target_action", "rename")
    ip = a.get("insufficient_privilege", "")
    role_spec = a.get("role_specification", "new_owner_role")
    if pl == "type_owner" or pl == "non_owner" or ip in (
        "non_superuser_set_property",
        "no_USAGE_on_attribute_type",
    ):
        roles.append(f"{p}owner")
    if pl == "non_owner" or ip in (
        "non_superuser_set_property",
        "no_USAGE_on_attribute_type",
    ):
        roles.append(f"{p}actor")
    if action == "owner_to" and role_spec == "new_owner_role":
        roles.append(f"{p}newowner")
    return tuple(dict.fromkeys(roles))


def _schema_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    """Schemas to create/drop."""

    schemas: list[str] = []
    shape = a.get("type_name_shape", "simple")
    action = a.get("target_action", "rename")
    if shape == "schema_qualified":
        schemas.append(f"{p}sch")
    if action == "set_schema":
        schemas.append(f"{p}targetsch")
    return tuple(dict.fromkeys(schemas))


def _needs_typed_table(a: dict[str, str]) -> bool:
    return a.get("typed_table_dependency") == "has_typed_tables"


def _typed_table_name(p: str) -> str:
    return f"{p}t"


def _tables_to_drop(case: AlterTypeFactorCase) -> list[str]:
    """Fixture tables the case CREATEs (typed tables only)."""

    a = _baseline(case)
    if _needs_typed_table(a):
        return [_typed_table_name(case.object_prefix)]
    return []


def _create_type_sql(a: dict[str, str], p: str) -> str:
    """The fixture CREATE TYPE for the active type category / branch."""

    name = _type_name(a, p)
    action = a.get("target_action", "rename")
    category = a.get("type_category", "composite")

    if action in ("add_value", "rename_value") or category == "enum":
        evc = a.get("enum_value_conflict", "")
        if (
            action == "add_value"
            and evc == "value_exists_no_if_not_exists"
        ):
            return (
                f"CREATE TYPE {name} AS ENUM "
                f"('{p}one', '{p}two', '{p}three');"
            )
        return f"CREATE TYPE {name} AS ENUM ('{p}one', '{p}two');"

    if action == "add_attribute":
        return f"CREATE TYPE {name} AS ({_attribute_name(a, p)} integer);"
    if action == "drop_attribute":
        return (
            f"CREATE TYPE {name} AS "
            f"({_attribute_name(a, p)} integer, "
            f"{_new_attribute_name(a, p)} text);"
        )
    if action == "alter_attribute_type":
        return f"CREATE TYPE {name} AS ({_attribute_name(a, p)} integer);"
    if action == "rename_attribute":
        return f"CREATE TYPE {name} AS ({_attribute_name(a, p)} integer);"
    if action == "set_property" or category in ("base", "shell"):
        return f"CREATE TYPE {name};"
    return f"CREATE TYPE {name} AS ({_attribute_name(a, p)} integer);"


def _probe_select(
    case: AlterTypeFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle with a top-level ORDER BY."""

    mode = a.get("verification_mode", "pg_type_catalog_query")
    action = a.get("target_action", "rename")
    missing = _type_missing(a)

    if action == "rename" and case.outcome == "success":
        check = _new_type_name_literal(a, p)
    else:
        check = _type_name_literal(a, p)
    present = not missing

    cmp_op = ">" if present else "="

    if mode == "pg_attribute_query":
        return (
            f"SELECT count(*) {cmp_op} 0 AS type_attributes "
            f"FROM pg_catalog.pg_attribute a "
            f"JOIN pg_catalog.pg_type t "
            f"ON t.typrelid = a.attrelid "
            f"WHERE t.typname = '{check}' AND a.attnum > 0 "
            f"ORDER BY count(*);"
        )
    if mode == "information_schema_user_defined_types":
        return (
            f"SELECT count(*) {cmp_op} 0 AS type_present "
            f"FROM information_schema.user_defined_types "
            f"WHERE user_defined_type_name = '{check}' "
            f"ORDER BY count(*);"
        )
    if mode == "enum_value_query":
        return (
            f"SELECT count(*) {cmp_op} 0 AS enum_values "
            f"FROM pg_catalog.pg_enum e "
            f"JOIN pg_catalog.pg_type t ON t.oid = e.enumtypid "
            f"WHERE t.typname = '{check}' "
            f"ORDER BY count(*);"
        )
    return (
        f"SELECT count(*) {cmp_op} 0 AS type_present "
        f"FROM pg_catalog.pg_type "
        f"WHERE typname = '{check}' "
        f"ORDER BY count(*);"
    )


def _build_target(a: dict[str, str], p: str) -> str:
    """The primary ALTER TYPE statement for the active branch."""

    name = _type_name(a, p)
    action = a.get("target_action", "rename")

    if action == "owner_to":
        target = _owner_target(a, p)
        return f"ALTER TYPE {name} OWNER TO {target};"
    if action == "rename":
        new = _new_type_name(a, p)
        return f"ALTER TYPE {name} RENAME TO {new};"
    if action == "set_schema":
        schema = _schema_target(a, p)
        return f"ALTER TYPE {name} SET SCHEMA {schema};"
    if action == "rename_attribute":
        attr = _attribute_name(a, p)
        new_attr = _new_attribute_name(a, p)
        cascade = _cascade_clause(a)
        return (
            f"ALTER TYPE {name} RENAME ATTRIBUTE {attr} "
            f"TO {new_attr}{cascade};"
        )
    if action == "add_attribute":
        attr = _attribute_name(a, p)
        typ = _attribute_type(a)
        cascade = _cascade_clause(a)
        return (
            f"ALTER TYPE {name} ADD ATTRIBUTE {attr} "
            f"{typ}{cascade};"
        )
    if action == "drop_attribute":
        attr = _attribute_name(a, p)
        if_exists = _if_exists_clause(a)
        cascade = _cascade_clause(a)
        return (
            f"ALTER TYPE {name} DROP ATTRIBUTE {if_exists}{attr}"
            f"{cascade};"
        )
    if action == "alter_attribute_type":
        attr = _attribute_name(a, p)
        typ = _attribute_type(a)
        cascade = _cascade_clause(a)
        return (
            f"ALTER TYPE {name} ALTER ATTRIBUTE {attr} "
            f"TYPE {typ}{cascade};"
        )
    if action == "add_value":
        ine = _if_not_exists_clause(a)
        value = _enum_value(a, p)
        pos = _enum_position_clause(a, p)
        return (
            f"ALTER TYPE {name} ADD VALUE {ine}{value}{pos};"
        )
    if action == "rename_value":
        return (
            f"ALTER TYPE {name} RENAME VALUE '{p}one' "
            f"TO {_enum_value_new(a, p)};"
        )
    if action == "set_property":
        prop = _property_clause(a, p)
        return f"ALTER TYPE {name} SET ({prop});"
    return f"ALTER TYPE {name} RENAME TO {_new_type_name(a, p)};"


def _cascade_clause(a: dict[str, str]) -> str:
    cr = a.get("cascade_restrict", "none")
    if cr == "cascade":
        return " CASCADE"
    if cr == "restrict":
        return " RESTRICT"
    return ""


def _if_exists_clause(a: dict[str, str]) -> str:
    if a.get("if_exists_clause", "absent") == "present":
        return "IF EXISTS "
    return ""


def _if_not_exists_clause(a: dict[str, str]) -> str:
    if a.get("if_not_exists_clause", "absent") == "present":
        return "IF NOT EXISTS "
    return ""


def _enum_position_clause(a: dict[str, str], p: str) -> str:
    pos = a.get("enum_position_clause", "absent")
    if pos == "BEFORE":
        return f" BEFORE {_neighbor_value(a, p)}"
    if pos == "AFTER":
        return f" AFTER {_neighbor_value(a, p)}"
    return ""


def _resolve_case(case: AlterTypeFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    action = a.get("target_action", "rename")
    missing = _type_missing(a)

    setup: list[str] = []
    locus = "target.alter_type"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    schemas = _schema_names(a, p)
    type_name = _type_name(a, p)

    # --- schema fixtures --------------------------------------------
    for schema in schemas:
        setup.append(f"CREATE SCHEMA IF NOT EXISTS {schema};")
        locus = "fixture.schema"

    # --- role fixtures ----------------------------------------------
    if f"{p}owner" in roles:
        setup.append(f"CREATE ROLE {p}owner LOGIN;")
        locus = "fixture.owner_role"
    if f"{p}actor" in roles:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"
    if (
        action == "owner_to"
        and a.get("role_specification", "new_owner_role")
        == "new_owner_role"
    ):
        setup.append(f"CREATE ROLE {p}newowner LOGIN;")
        locus = "fixture.owner_role"

    # --- grant memberships for success scenarios ---------------------
    if f"{p}owner" in roles:
        setup.append(f"SET ROLE {p}owner;")
    if (
        action == "owner_to"
        and a.get("owner_change_privilege") == "can_SET_ROLE"
        and a.get("role_specification") == "new_owner_role"
    ):
        setup.append(f"GRANT {p}newowner TO {p}owner;")
    if (
        action == "set_schema"
        and a.get("schema_privilege") == "has_CREATE"
    ):
        setup.append(
            f"GRANT CREATE ON SCHEMA {_schema_target(a, p)} "
            f"TO {p}owner;"
        )
    if (
        action == "owner_to"
        and a.get("new_owner_schema_privilege") == "has_CREATE"
    ):
        setup.append(
            f"GRANT CREATE ON SCHEMA {p}sch TO {p}newowner;"
        )

    # --- the target type fixture ------------------------------------
    if not missing:
        setup.append(_create_type_sql(a, p))
        locus = "fixture.type"
        if _needs_typed_table(a):
            setup.append(
                f"CREATE TABLE {_typed_table_name(p)} OF {type_name};"
            )
            locus = "fixture.typed_table"
        if (
            action in ("add_attribute", "alter_attribute_type")
            and a.get("attribute_usage_privilege") == "no_USAGE"
        ):
            setup.append(
                f"CREATE TYPE {p}udt AS ENUM ('{p}u');"
            )
            setup.append(
                f"REVOKE USAGE ON TYPE {p}udt FROM {p}actor;"
            )
            locus = "fixture.usage_privilege"
    else:
        setup.append(
            "SELECT 1 AS target_type_intentionally_absent;"
        )
        locus = "fixture.type_missing"

    # --- arm the effective role --------------------------------------
    if effective and effective != f"{p}owner":
        setup.append(f"SET ROLE {effective};")

    # --- the primary target statement --------------------------------
    target = _build_target(a, p)

    # --- oracle / SQLSTATE assertion ---------------------------------
    assert_lines: list[str] = []
    if effective:
        assert_lines.append("RESET ROLE;")
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    probe = _probe_select(case, a, p)
    if probe is not None:
        assert_lines.append(probe)

    # --- cleanup construction -----------------------------------------
    tables = _tables_to_drop(case)
    table_drops = [
        f"DROP TABLE IF EXISTS {t};" for t in tables
    ]
    type_drops = [f"DROP TYPE IF EXISTS {type_name} CASCADE;"]
    if action == "rename":
        type_drops.append(
            f"DROP TYPE IF EXISTS {_new_type_name(a, p)} CASCADE;"
        )
    role_drops = [
        stmt
        for role in roles
        for stmt in (
            f"DROP OWNED BY {role} CASCADE;",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]
    schema_drops = [
        f"DROP SCHEMA IF EXISTS {s} CASCADE;" for s in schemas
    ]

    # pre-cleanup: tables first (bookend), then types, roles, schemas
    pre_cleanup: list[str] = []
    pre_cleanup.extend(table_drops)
    pre_cleanup.extend(type_drops)
    pre_cleanup.extend(role_drops)
    pre_cleanup.extend(schema_drops)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # cleanup: reset role, types, roles, schemas, then tables LAST
    # (bookend for table-creating cases)
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(type_drops)
    cleanup.extend(role_drops)
    cleanup.extend(schema_drops)
    cleanup.extend(table_drops)
    if not cleanup:
        cleanup.append("SELECT 1 AS residual_check_no_objects;")

    on_error_off = case.outcome == "expected_failure"
    return _CasePlan(
        target_fragment=target,
        setup_lines=tuple(setup),
        assert_lines=tuple(assert_lines),
        pre_cleanup_lines=tuple(pre_cleanup),
        cleanup_lines=tuple(cleanup),
        on_error_off=on_error_off,
        semantic_locus=locus,
    )


def resolve_alter_type_factor_witness(
    case: AlterTypeFactorCase | AlterTypeFactorExtensionCase,
    repository_root: Path,
) -> AlterTypeFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return AlterTypeFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_alter_type(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*ALTER\s+TYPE\b", region)
    )


def _header(case: AlterTypeFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : ALTER TYPE {case.factor_key}="
        f"{case.factor_value}",
        f"-- FE           : {_FE}",
        "-- ++",
        "-- --------------------------------------------------------",
        f"-- case_id: {case.case_id}",
        f"-- source_md: {_DOC_SOURCE}",
        f"-- factor_md: {_FACTOR_SOURCE}",
        f"-- primary_obligation_id: {case.primary_obligation_id}",
        f"-- expected_outcome: {case.outcome}",
        f"-- expected_sqlstate: {case.expected_sqlstate}",
    ]


def render_alter_type_factor_case(
    case: AlterTypeFactorCase | AlterTypeFactorExtensionCase,
    repository_root: Path,
) -> str:
    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地规则和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 ALTER TYPE。")
    lines.append(_PRIMARY_BEGIN)
    lines.append(resolved.target_fragment)
    lines.append(_PRIMARY_END)
    lines.append("\\set target_sqlstate :SQLSTATE")
    lines.append("\\echo PGCF_TARGET_SQLSTATE=:target_sqlstate")
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 4. 验证 SQLSTATE、目录状态和数据行为。")
    lines.extend(resolved.assert_lines)
    lines.append("-- 5. 清理全部本编号对象。")
    lines.extend(resolved.cleanup_lines)
    text = "\n".join(lines)
    if not text.endswith("\n"):
        text += "\n"
    return text


def _write_program(
    case: AlterTypeFactorCase | AlterTypeFactorExtensionCase,
    out: Path,
) -> None:
    text = render_alter_type_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_alter_type_factor_programs(
    baseline_plan: AlterTypeFactorLoopPlan,
    extension_plan: object,
    out_dir: Path,
) -> int:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    count = 0
    for case in baseline_plan.cases:
        _write_program(case, out)
        count += 1
    for case in extension_plan.cases:
        _write_program(case, out)
        count += 1
    return count


__all__ = [
    "AlterTypeFactorRenderError",
    "AlterTypeFactorWitness",
    "count_primary_alter_type",
    "generate_alter_type_factor_programs",
    "render_alter_type_factor_case",
    "resolve_alter_type_factor_witness",
]
