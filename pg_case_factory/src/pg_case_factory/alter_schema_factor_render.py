"""Render complete PostgreSQL 18.4 ALTER SCHEMA factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

ALTER SCHEMA is a NON-TABLE statement: the target is a
``pg_catalog.pg_namespace`` row, not a ``pg_class`` relation.  All
catalog oracles therefore schema-qualify ``pg_catalog.pg_namespace`` or
``information_schema.schemata`` (both exempt from the file-prefix style
gate).  When ``contained_objects_state`` is ``schema_with_tables`` the
setup creates a TABLE inside the schema (prefix-named so it satisfies the
style gate); cleanup uses ``DROP SCHEMA ... CASCADE`` which drops the
contained objects transitively.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .alter_schema_factor_extension import (
    AlterSchemaFactorExtensionCase,
    _present_failure_pair,
)
from .alter_schema_factor_loop import (
    AlterSchemaFactorCase,
    AlterSchemaFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/schema/"
    "alter_schema.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/schema/"
    "alter_schema.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

# Placeholder database name for provisional privilege grants (the style
# gate strips GRANT/REVOKE statements; the DB-phase runtime calibrates
# the real database).
_DB_PLACEHOLDER = "pgcf"


class AlterSchemaFactorRenderError(ValueError):
    """Raised when an ALTER SCHEMA case cannot be rendered."""


@dataclass(frozen=True)
class AlterSchemaFactorWitness:
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
    ext: AlterSchemaFactorExtensionCase,
) -> AlterSchemaFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get("target_action", "rename")
    return AlterSchemaFactorCase(
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
    case: AlterSchemaFactorCase | AlterSchemaFactorExtensionCase,
) -> AlterSchemaFactorCase:
    if isinstance(case, AlterSchemaFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: AlterSchemaFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _is_rename(a: dict[str, str]) -> bool:
    return a.get("target_action") == "rename"


def _is_owner(a: dict[str, str]) -> bool:
    return a.get("target_action") == "owner"


def _schema_missing(a: dict[str, str]) -> bool:
    return a.get("object_state") == "not_exists"


def _is_session_user_escape(a: dict[str, str]) -> bool:
    return a.get("owner_clause") == "SESSION_USER"


def _creates_table(a: dict[str, str]) -> bool:
    return a.get("contained_objects_state") == "schema_with_tables"


def _creates_view(a: dict[str, str]) -> bool:
    return a.get("contained_objects_state") == "schema_with_views"


def _schema_name(a: dict[str, str], p: str) -> str:
    """The schema identifier used inside ALTER SCHEMA and fixtures."""

    shape = a.get("schema_name_shape", "simple")
    if shape == "quoted":
        return f'"{p}Mixed Schema"'
    if shape == "reserved_word":
        return '"select"'
    if shape == "schema_qualified":
        return f'"{p}dotted.sch"'
    return f"{p}sch"


def _schema_name_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    shape = a.get("schema_name_shape", "simple")
    if shape == "quoted":
        return f"{p}Mixed Schema"
    if shape == "reserved_word":
        return "select"
    if shape == "schema_qualified":
        return f"{p}dotted.sch"
    return f"{p}sch"


def _new_name(a: dict[str, str], p: str) -> str:
    """The new name in RENAME TO."""

    shape = a.get("new_name_shape", "simple")
    rnc = a.get("rename_clause", "new_simple_name")
    if rnc == "new_existing_name":
        return f"{p}existsch"
    if shape == "pg_prefix_reserved":
        return f"pg_{p}reserved"
    if shape == "quoted":
        return f'"{p}Mixed New"'
    if shape == "reserved_word":
        return '"column"'
    return f"{p}newsch"


def _new_name_literal(a: dict[str, str], p: str) -> str:
    shape = a.get("new_name_shape", "simple")
    rnc = a.get("rename_clause", "new_simple_name")
    if rnc == "new_existing_name":
        return f"{p}existsch"
    if shape == "pg_prefix_reserved":
        return f"pg_{p}reserved"
    if shape == "quoted":
        return f"{p}Mixed New"
    if shape == "reserved_word":
        return "column"
    return f"{p}newsch"


def _owner_target(a: dict[str, str], p: str) -> str:
    """The owner target token in OWNER TO."""

    oc = a.get("owner_clause", "new_owner_role")
    if oc == "CURRENT_ROLE":
        return "CURRENT_ROLE"
    if oc == "CURRENT_USER":
        return "CURRENT_USER"
    if oc == "SESSION_USER":
        return "SESSION_USER"
    now = a.get("new_owner_shape", "existing_role")
    if now == "non_existing_role":
        return f"{p}no_such_role"
    return f"{p}newowner"


def _owner_role_needs_create(a: dict[str, str]) -> bool:
    return (
        a.get("owner_clause") == "new_owner_role"
        and a.get("new_owner_shape") == "existing_role"
    )


def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target ALTER SCHEMA runs."""

    level = a.get("privilege_level", "superuser")
    if level == "schema_owner":
        return f"{p}schowner"
    if level == "non_owner":
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    """Roles to tear down, members/grantees before the owner role."""

    roles: list[str] = []
    level = a.get("privilege_level", "superuser")
    if _is_owner(a) and _owner_role_needs_create(a):
        roles.append(f"{p}newowner")
    if level == "non_owner":
        roles.append(f"{p}actor")
    if level in ("schema_owner", "non_owner"):
        roles.append(f"{p}schowner")
    return tuple(roles)


def _probe_select(
    case: AlterSchemaFactorCase, a: dict[str, str], p: str
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only error_assertion."""

    mode = a.get("verification_mode", "pg_namespace_catalog_query")
    sch = _schema_name_literal(a, p)
    missing = _schema_missing(a)

    if _is_rename(a):
        new = _new_name_literal(a, p)
        if case.outcome == "success":
            check = new
            present = True
        elif missing:
            check = sch
            present = False
        else:
            check = sch
            present = True
    else:
        if missing:
            check = sch
            present = False
        else:
            check = sch
            present = True

    cmp_op = ">" if present else "="
    if mode == "information_schema_schemata":
        return (
            f"SELECT count(*) {cmp_op} 0 AS schema_state "
            f"FROM information_schema.schemata "
            f"WHERE schema_name = '{check}';"
        )
    if mode == "current_schema_query":
        if present:
            return (
                f'SET search_path TO "{check}"; '
                f"SELECT current_schema() = '{check}' "
                f"AS in_target_schema;"
            )
        return (
            f"SELECT current_schema() IS DISTINCT FROM '{check}' "
            f"AS schema_absent;"
        )
    return (
        f"SELECT count(*) {cmp_op} 0 AS schema_state "
        f"FROM pg_catalog.pg_namespace "
        f"WHERE nspname = '{check}';"
    )


def _resolve_case(case: AlterSchemaFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    rename = _is_rename(a)
    owner = _is_owner(a)
    missing = _schema_missing(a)

    setup: list[str] = []
    locus = "target.alter_schema"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    sch = _schema_name(a, p)
    sch_lit = _schema_name_literal(a, p)
    new = _new_name(a, p)
    owner_target = _owner_target(a, p)

    # --- role fixtures -------------------------------------------------
    if effective == f"{p}schowner":
        setup.append(f"CREATE ROLE {p}schowner LOGIN;")
        if owner and _owner_role_needs_create(a):
            setup.append(f"CREATE ROLE {p}newowner LOGIN;")
            nodp = a.get("new_owner_db_privilege", "has_CREATE_privilege")
            if nodp == "has_CREATE_privilege":
                setup.append(
                    f"GRANT CREATE ON DATABASE {_DB_PLACEHOLDER} "
                    f"TO {p}newowner;"
                )
        locus = "fixture.privilege_state"
    elif effective == f"{p}actor":
        setup.append(f"CREATE ROLE {p}schowner LOGIN;")
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        if owner and _owner_role_needs_create(a):
            setup.append(f"CREATE ROLE {p}newowner LOGIN;")
        locus = "fixture.privilege_state"

    # --- the target schema fixture ------------------------------------
    if not missing:
        setup.append(f"CREATE SCHEMA {sch};")
        locus = "fixture.schema"

        # transfer ownership to the schema owner (superuser bypasses)
        if effective in (f"{p}schowner", f"{p}actor"):
            setup.append(f"ALTER SCHEMA {sch} OWNER TO {p}schowner;")

        # contained objects inside the schema
        if _creates_table(a):
            setup.append(
                f"CREATE TABLE {sch}.{p}tab ({p}col integer);"
            )
            locus = "fixture.contained_table"
        elif _creates_view(a):
            setup.append(
                f"CREATE VIEW {sch}.{p}v AS SELECT 1 AS {p}vcol;"
            )
            locus = "fixture.contained_view"

        # duplicate-name fixture (rename conflict boundary)
        if (
            rename
            and a.get("rename_clause") == "new_existing_name"
        ):
            setup.append(f"CREATE SCHEMA {p}existsch;")

        # membership grant for owner transfer (done by superuser)
        if (
            owner
            and effective == f"{p}schowner"
            and _owner_role_needs_create(a)
            and a.get("owner_change_privilege")
            == "can_SET_ROLE_to_new_owner"
        ):
            setup.append(
                f"GRANT {p}newowner TO {p}schowner;"
            )

        # CREATE-on-database grant for the schema owner (rename needs it)
        if (
            rename
            and effective == f"{p}schowner"
            and a.get("rename_privilege") == "owner_with_CREATE_on_db"
        ):
            setup.append(
                f"GRANT CREATE ON DATABASE {_DB_PLACEHOLDER} "
                f"TO {p}schowner;"
            )
    else:
        setup.append(
            "SELECT 1 AS target_schema_intentionally_absent;"
        )
        locus = "fixture.schema_missing"

    # --- arm the effective role ----------------------------------------
    if effective:
        setup.append(f"SET ROLE {effective};")
        if effective == f"{p}actor" and owner and _owner_role_needs_create(a):
            setup.append("RESET ROLE;")
            setup.append(f"SET ROLE {p}actor;")

    # --- the primary target statement ---------------------------------
    if rename:
        target = f"ALTER SCHEMA {sch} RENAME TO {new};"
    else:
        target = f"ALTER SCHEMA {sch} OWNER TO {owner_target};"

    if case.kind == "RISK":
        setup.append("BEGIN;")
        locus = "target.transaction_boundary"

    # --- oracle / SQLSTATE assertion ------------------------------------
    assert_lines: list[str] = []
    if effective:
        assert_lines.append("RESET ROLE;")
    if case.kind == "RISK":
        assert_lines.append(
            "COMMIT;" if case.factor_value == "commit" else "ROLLBACK;"
        )
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    probe = _probe_select(case, a, p)
    if probe is not None:
        assert_lines.append(probe)

    # --- cleanup construction ------------------------------------------
    role_drops = [
        statement
        for role in roles
        for statement in (
            f"DROP OWNED BY {role} CASCADE;",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    # Schemas to drop.  For RENAME the schema may have been renamed, so
    # both the old and new names are dropped (IF EXISTS tolerates the
    # absent one).  For OWNER TO the name is unchanged.
    schema_drops: list[str] = []
    if not missing:
        schema_drops.append(f"DROP SCHEMA IF EXISTS {sch} CASCADE;")
        if rename:
            new_drop = _new_name(a, p)
            schema_drops.append(
                f"DROP SCHEMA IF EXISTS {new_drop} CASCADE;"
            )

    # pre-cleanup: residual schema + role drops
    pre_cleanup: list[str] = list(schema_drops)
    pre_cleanup.extend(role_drops)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # cleanup: schema drops then role drops
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(schema_drops)
    cleanup.extend(role_drops)
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


def resolve_alter_schema_factor_witness(
    case: AlterSchemaFactorCase | AlterSchemaFactorExtensionCase,
    repository_root: Path,
) -> AlterSchemaFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return AlterSchemaFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_alter_schema(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(re.findall(r"(?im)^\s*ALTER\s+SCHEMA\b", region))


def _header(case: AlterSchemaFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : ALTER SCHEMA {case.factor_key}="
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


def render_alter_schema_factor_case(
    case: AlterSchemaFactorCase | AlterSchemaFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 ALTER SCHEMA。")
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
    case: AlterSchemaFactorCase | AlterSchemaFactorExtensionCase,
    out: Path,
) -> None:
    text = render_alter_schema_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_alter_schema_factor_programs(
    baseline_plan: AlterSchemaFactorLoopPlan,
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
    "AlterSchemaFactorRenderError",
    "AlterSchemaFactorWitness",
    "count_primary_alter_schema",
    "generate_alter_schema_factor_programs",
    "render_alter_schema_factor_case",
    "resolve_alter_schema_factor_witness",
]
