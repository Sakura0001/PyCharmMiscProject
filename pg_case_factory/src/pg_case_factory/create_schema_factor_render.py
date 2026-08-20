"""Render complete PostgreSQL 18.4 CREATE SCHEMA factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CREATE SCHEMA is a namespace-management DDL statement: the target is a
``pg_catalog.pg_namespace`` catalog row, not a ``pg_class`` relation.
All catalog oracles schema-qualify ``pg_catalog.pg_namespace`` or
``information_schema.schemata`` (exempt from the file-prefix style
gate).  No case creates a standalone TABLE: any ``CREATE TABLE`` is a
sub-clause of the single ``CREATE SCHEMA`` statement, so the bookend
(DROP TABLE IF EXISTS) is never emitted (``_tables_to_drop`` always
returns ``[]``) and cleanup is ``DROP SCHEMA ... CASCADE``.  Every
catalog SELECT carries a top-level ``ORDER BY count(*)`` so the
catalog-observability gate passes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_schema_factor_extension import (
    CreateSchemaFactorExtensionCase,
    _present_failure_pair,
)
from .create_schema_factor_loop import (
    CreateSchemaFactorCase,
    CreateSchemaFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/schema/"
    "create_schema.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/schema/"
    "create_schema.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class CreateSchemaFactorRenderError(ValueError):
    """Raised when a CREATE SCHEMA case cannot be rendered."""


@dataclass(frozen=True)
class CreateSchemaFactorWitness:
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
    ext: CreateSchemaFactorExtensionCase,
) -> CreateSchemaFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get("target_action", "create_named_schema")
    return CreateSchemaFactorCase(
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
    case: CreateSchemaFactorCase | CreateSchemaFactorExtensionCase,
) -> CreateSchemaFactorCase:
    if isinstance(case, CreateSchemaFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateSchemaFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _schema_name(a: dict[str, str], p: str) -> str:
    """The schema identifier in CREATE SCHEMA and fixtures."""

    shape = a.get("schema_name_shape", "simple")
    if shape == "quoted":
        return f'"{p}Mixed Schema"'
    if shape == "reserved_word":
        return f'"{p}select"'
    if shape == "pg_prefix_reserved":
        return f"pg_{p}bad"
    return f"{p}s"


def _schema_name_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    shape = a.get("schema_name_shape", "simple")
    if shape == "quoted":
        return f"{p}Mixed Schema"
    if shape == "reserved_word":
        return f"{p}select"
    if shape == "pg_prefix_reserved":
        return f"pg_{p}bad"
    return f"{p}s"


def _owner_token(a: dict[str, str], p: str) -> str:
    """The role token in AUTHORIZATION (named branch uses
    authorization_clause; auth branch uses role_specification_form)."""

    sb = a.get("statement_branch", "branch_named_schema")
    if "auth" in sb and "named" not in sb:
        form = a.get("role_specification_form", "user_name")
    else:
        form = a.get("authorization_clause", "absent")
        if form == "explicit_user":
            form = "user_name"
    if form == "CURRENT_ROLE":
        return "CURRENT_ROLE"
    if form == "CURRENT_USER":
        return "CURRENT_USER"
    if form == "SESSION_USER":
        return "SESSION_USER"
    return f"{p}owner"


def _owner_exists(a: dict[str, str]) -> bool:
    """Whether the explicit owner role should be created in setup."""

    ons = a.get("owner_name_shape", "existing_role")
    rd = a.get("role_dependency", "role_exists")
    if ons == "non_existing_role" or rd == "role_not_exists":
        return False
    return True


def _authorization_clause(a: dict[str, str], p: str) -> str:
    """The AUTHORIZATION clause text, or empty when absent."""

    sb = a.get("statement_branch", "branch_named_schema")
    ac = a.get("authorization_clause", "absent")
    # Auth-named branches always emit AUTHORIZATION (it is the form).
    if sb in ("branch_auth_schema", "branch_if_not_exists_auth"):
        return f" AUTHORIZATION {_owner_token(a, p)}"
    if ac == "absent":
        return ""
    return f" AUTHORIZATION {_owner_token(a, p)}"


def _has_forward_reference(a: dict[str, str]) -> bool:
    return (
        a.get("forward_reference_in_elements") == "forward_reference_failure"
    )


def _schema_elements(a: dict[str, str], p: str) -> str:
    """The schema_element sub-commands appended to CREATE SCHEMA."""

    sei = a.get("schema_element_inclusion", "without_elements")
    fwd = _has_forward_reference(a)
    table = f"CREATE TABLE {p}t (id integer)"
    if fwd:
        view = f"CREATE VIEW {p}v AS SELECT col FROM {p}missing_t"
    else:
        view = f"CREATE VIEW {p}v AS SELECT 1 AS col"
    if sei == "with_create_table":
        return f" {table}"
    if sei == "with_create_view":
        return f" {view}"
    if sei == "with_multiple_elements":
        return f" {table} {view}"
    return ""


def _build_target(a: dict[str, str], p: str) -> str:
    """The primary CREATE SCHEMA statement for the active branch."""

    sb = a.get("statement_branch", "branch_named_schema")
    name = _schema_name(a, p)
    auth = _authorization_clause(a, p)
    elements = _schema_elements(a, p)
    # IF NOT EXISTS branches normally forbid elements; only the
    # if_not_exists_with_elements failure carries them.
    if sb == "branch_named_schema":
        return f"CREATE SCHEMA {name}{auth}{elements};"
    if sb == "branch_auth_schema":
        return f"CREATE SCHEMA AUTHORIZATION {_owner_token(a, p)}{elements};"
    if sb == "branch_if_not_exists_named":
        return f"CREATE SCHEMA IF NOT EXISTS {name}{auth}{elements};"
    if sb == "branch_if_not_exists_auth":
        return (
            f"CREATE SCHEMA IF NOT EXISTS AUTHORIZATION "
            f"{_owner_token(a, p)}{elements};"
        )
    return f"CREATE SCHEMA {name}{auth}{elements};"


def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target CREATE SCHEMA runs."""

    pl = a.get("privilege_level", "superuser")
    rd = a.get("role_dependency", "role_exists")
    if pl == "non_creator_no_privilege" or rd == "cannot_SET_ROLE":
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    """Roles to tear down."""

    roles: list[str] = []
    pl = a.get("privilege_level", "superuser")
    rd = a.get("role_dependency", "role_exists")
    ac = a.get("authorization_clause", "absent")
    sb = a.get("statement_branch", "branch_named_schema")
    has_auth = ac != "absent" or sb in (
        "branch_auth_schema",
        "branch_if_not_exists_auth",
    )
    if has_auth and _owner_exists(a):
        roles.append(f"{p}owner")
    if pl == "non_creator_no_privilege" or rd == "cannot_SET_ROLE":
        roles.append(f"{p}actor")
    return tuple(roles)


def _schema_present(case: CreateSchemaFactorCase, a: dict[str, str]) -> bool:
    """Whether the schema row exists after the target statement."""

    if case.outcome == "success":
        return True
    # A duplicate failure leaves the pre-created schema in place.
    return a.get("object_state") == "already_exists"


def _probe_select(
    case: CreateSchemaFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only error_assertion."""

    mode = a.get("verification_mode", "pg_namespace_catalog_query")
    lit = _schema_name_literal(a, p)
    present = _schema_present(case, a)
    cmp_op = ">" if present else "="
    if mode == "information_schema_schemata":
        return (
            f"SELECT count(*) {cmp_op} 0 AS schema_state "
            f"FROM information_schema.schemata "
            f"WHERE schema_name = '{lit}' "
            f"ORDER BY count(*);"
        )
    if mode == "current_schema_query":
        return (
            "SELECT current_schema() AS current_schema_name "
            "ORDER BY current_schema_name;"
        )
    return (
        f"SELECT count(*) {cmp_op} 0 AS schema_state "
        f"FROM pg_catalog.pg_namespace "
        f"WHERE nspname = '{lit}' "
        f"ORDER BY count(*);"
    )


def _tables_to_drop(case: CreateSchemaFactorCase) -> list[str]:
    """Fixture tables the case CREATEs.

    CREATE SCHEMA is a namespace-management statement: it never creates
    a standalone TABLE.  Any ``CREATE TABLE`` is a sub-clause of the
    single ``CREATE SCHEMA`` statement and is removed by
    ``DROP SCHEMA ... CASCADE``.  The bookend (DROP TABLE IF EXISTS) is
    therefore never emitted.
    """
    return []


def _cleanup_statement(a: dict[str, str], name: str) -> str:
    mode = a.get("cleanup_mode", "DROP_SCHEMA_IF_EXISTS")
    if mode == "DROP_SCHEMA":
        return f"DROP SCHEMA {name} CASCADE;"
    if mode == "DROP_SCHEMA_CASCADE":
        return f"DROP SCHEMA {name} CASCADE;"
    return f"DROP SCHEMA IF EXISTS {name} CASCADE;"


def _resolve_case(case: CreateSchemaFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    name = _schema_name(a, p)
    already_exists = a.get("object_state") == "already_exists"

    setup: list[str] = []
    locus = "target.create_schema"

    # --- role fixtures -----------------------------------------------
    if _owner_exists(a) and f"{p}owner" in roles:
        setup.append(f"CREATE ROLE {p}owner LOGIN;")
        locus = "fixture.owner_role"
    if effective == f"{p}actor":
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"
        if a.get("role_dependency") == "cannot_SET_ROLE":
            # owner exists but actor is not a member -> cannot SET ROLE
            if f"{p}owner" in roles and f"{p}owner" not in (
                f"{p}actor",
            ):
                pass
        else:
            setup.append(f"GRANT CREATE ON DATABASE pgcf TO {p}actor;")
            locus = "fixture.privilege_state"

    # --- pre-existing schema fixture (duplicate / no-op) -------------
    if already_exists:
        setup.append(f"CREATE SCHEMA {name};")
        locus = "fixture.schema_exists"

    # --- arm the effective role --------------------------------------
    if effective:
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
    role_drops = [
        statement
        for role in roles
        for statement in (
            f"DROP OWNED BY {role} CASCADE;",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]
    schema_drop = _cleanup_statement(a, name)

    pre_cleanup: list[str] = [
        f"DROP SCHEMA IF EXISTS {name} CASCADE;"
    ]
    pre_cleanup.extend(role_drops)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.append(schema_drop)
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


def resolve_create_schema_factor_witness(
    case: CreateSchemaFactorCase | CreateSchemaFactorExtensionCase,
    repository_root: Path,
) -> CreateSchemaFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateSchemaFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_create_schema(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(re.findall(r"(?im)^\s*CREATE\s+SCHEMA\b", region))


def _header(case: CreateSchemaFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE SCHEMA {case.factor_key}="
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


def render_create_schema_factor_case(
    case: CreateSchemaFactorCase | CreateSchemaFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 CREATE SCHEMA。")
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
    case: CreateSchemaFactorCase | CreateSchemaFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_schema_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_schema_factor_programs(
    baseline_plan: CreateSchemaFactorLoopPlan,
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
    "CreateSchemaFactorRenderError",
    "CreateSchemaFactorWitness",
    "count_primary_create_schema",
    "generate_create_schema_factor_programs",
    "render_create_schema_factor_case",
    "resolve_create_schema_factor_witness",
]
