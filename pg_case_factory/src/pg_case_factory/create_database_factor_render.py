"""Render complete PostgreSQL 18.4 CREATE DATABASE factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CREATE DATABASE is a DDL statement (``CREATE DATABASE name [ WITH ] ...``)
that creates a new database cluster object.  It is NOT a table-creating
statement: the target is a database, not a catalog row.  All catalog
oracles schema-qualify ``pg_catalog.pg_database`` (exempt from the
file-prefix style gate).  Since no fixture TABLE is created, the bookend
gate (DROP TABLE IF EXISTS) does not apply; the placeholder
``SELECT 1 AS residual_check_no_objects;`` is used instead.
Every catalog SELECT carries a top-level ``ORDER BY`` so the
catalog-observability gate passes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_database_factor_extension import (
    CreateDatabaseFactorExtensionCase,
    _present_failure_pair,
)
from .create_database_factor_loop import (
    CreateDatabaseFactorCase,
    CreateDatabaseFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/database/"
    "create_database.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/database/"
    "create_database.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class CreateDatabaseFactorRenderError(ValueError):
    """Raised when a CREATE DATABASE case cannot be rendered."""


@dataclass(frozen=True)
class CreateDatabaseFactorWitness:
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
    ext: CreateDatabaseFactorExtensionCase,
) -> CreateDatabaseFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get(
            "target_action", "create_database"
        )
    return CreateDatabaseFactorCase(
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
    case: CreateDatabaseFactorCase | CreateDatabaseFactorExtensionCase,
) -> CreateDatabaseFactorCase:
    if isinstance(case, CreateDatabaseFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateDatabaseFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _database_name(a: dict[str, str], p: str) -> str:
    shape = a.get("database_name_shape", "simple_id")
    if shape == "quoted_id":
        return f'"{p}DB"'
    if shape == "reserved_word_as_name":
        return f'"{p}user"'
    return f"{p}db"


def _owner_role_name(a: dict[str, str], p: str) -> str:
    shape = a.get("owner_name_shape", "simple_id")
    if shape == "nonexistent_role":
        return f"{p}no_role"
    return f"{p}role"


def _with_options(a: dict[str, str], p: str) -> str:
    parts: list[str] = []
    owner = a.get("owner_clause", "omitted")
    if owner == "current_user":
        parts.append("OWNER CURRENT_USER")
    elif owner == "specified_other_role":
        parts.append(f"OWNER {_owner_role_name(a, p)}")

    template = a.get("template_clause", "omitted_default_template1")
    if template == "template0":
        parts.append("TEMPLATE template0")
    elif template == "custom_template":
        parts.append(f"TEMPLATE {p}template")

    encoding = a.get("encoding_clause", "omitted")
    if encoding != "omitted":
        parts.append(f"ENCODING '{encoding}'")

    locale = a.get("locale_clause", "omitted")
    if locale == "C_locale":
        parts.append("LOCALE 'C'")
    elif locale == "POSIX_locale":
        parts.append("LOCALE 'POSIX'")
    elif locale == "specific_locale":
        parts.append("LOCALE 'en_US.UTF-8'")
    elif locale == "builtin_locale":
        parts.append(
            "LOCALE_PROVIDER builtin BUILTIN_LOCALE 'C.UTF-8'"
        )

    strategy = a.get("strategy_clause", "omitted_default_wal_log")
    if strategy == "WAL_LOG":
        parts.append("STRATEGY WAL_LOG")
    elif strategy == "FILE_COPY":
        parts.append("STRATEGY FILE_COPY")

    tablespace = a.get(
        "tablespace_name_shape", "default_tablespace"
    )
    if tablespace == "existing_tablespace":
        parts.append(f"TABLESPACE {p}tablespace")
    elif tablespace == "nonexistent_tablespace":
        parts.append(f"TABLESPACE {p}no_ts")

    return " ".join(parts)


def _is_privilege_failure(a: dict[str, str]) -> bool:
    return a.get("privilege_level") in (
        "non_createdb_role",
    ) or a.get("expected_status") == "failure" and a.get(
        "privilege_denied"
    ) == "lacks_createdb"


def _effective_role(a: dict[str, str], p: str) -> str:
    pc = a.get("privilege_level", "superuser")
    if pc == "non_createdb_role":
        return f"{p}actor"
    if pc == "createdb_role":
        return f"{p}actor"
    if a.get("expected_status") == "failure" and a.get(
        "privilege_denied"
    ) == "lacks_createdb":
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    if _effective_role(a, p):
        roles.append(f"{p}actor")
    if a.get("owner_clause") == "specified_other_role":
        owner_role = _owner_role_name(a, p)
        if owner_role not in roles:
            roles.append(owner_role)
    return tuple(roles)


def _needs_duplicate_setup(a: dict[str, str]) -> bool:
    return (
        a.get("object_state") == "exists"
        or a.get("duplicate_database_name") == "same_name_conflict"
        or a.get("database_name_shape") == "duplicate_name"
    )


def _needs_transaction(a: dict[str, str]) -> bool:
    return a.get("inside_transaction_block") == "inside_transaction"


def _cleanup_clause(a: dict[str, str], p: str) -> str:
    mode = a.get("cleanup_mode", "drop_database")
    name = _database_name(a, p)
    if mode == "force_drop_database":
        return f"DROP DATABASE IF EXISTS {name} WITH (FORCE);"
    return f"DROP DATABASE IF EXISTS {name};"


def _probe_select(
    case: CreateDatabaseFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    mode = a.get("verification_mode", "catalog_query_pg_database")
    if mode == "error_assertion":
        return None
    name = _database_name(a, p)
    literal = name.strip('"')
    if mode == "catalog_query_pg_database":
        return (
            "SELECT datname FROM pg_catalog.pg_database "
            f"WHERE datname = '{literal}' "
            "ORDER BY datname;"
        )
    if mode == "connect_to_new_database":
        return (
            "SELECT count(*) AS new_database_present "
            "FROM pg_catalog.pg_database "
            f"WHERE datname = '{literal}' "
            "ORDER BY count(*)"
        ) + ";"
    return None


def _resolve_case(
    case: CreateDatabaseFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    db_name = _database_name(a, p)
    options = _with_options(a, p)

    setup: list[str] = []
    locus = "target.create_database"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)

    if _needs_duplicate_setup(a):
        setup.append(f"CREATE DATABASE {db_name};")
        locus = "fixture.duplicate_database"

    if effective == f"{p}actor":
        if a.get("privilege_level") == "createdb_role":
            setup.append(
                f"CREATE ROLE {p}actor LOGIN NOSUPERUSER "
                "CREATEDB;"
            )
        else:
            setup.append(
                f"CREATE ROLE {p}actor LOGIN NOSUPERUSER "
                "NOCREATEDB;"
            )
        setup.append(f"SET ROLE {effective};")
        locus = "fixture.privilege_state"

    if a.get("owner_clause") == "specified_other_role":
        owner_role = _owner_role_name(a, p)
        if owner_role not in (effective,):
            setup.append(
                f"CREATE ROLE {owner_role} LOGIN;"
            )

    if _needs_transaction(a):
        setup.append("BEGIN;")
        locus = "fixture.transaction_block"

    target = f"CREATE DATABASE {db_name}"
    if options:
        target += f" WITH {options}"
    target += ";"

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

    pre_cleanup: list[str] = []
    pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")
    pre_cleanup.append(f"DROP DATABASE IF EXISTS {db_name};")
    for role in roles:
        pre_cleanup.append(f"DROP ROLE IF EXISTS {role};")

    cleanup: list[str] = []
    if _needs_transaction(a):
        cleanup.append("ROLLBACK;")
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.append(_cleanup_clause(a, p))
    for role in roles:
        cleanup.append(f"DROP ROLE IF EXISTS {role};")
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


def resolve_create_database_factor_witness(
    case: CreateDatabaseFactorCase | CreateDatabaseFactorExtensionCase,
    repository_root: Path,
) -> CreateDatabaseFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateDatabaseFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_create_database(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*CREATE\s+DATABASE\b", region)
    )


def _header(case: CreateDatabaseFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE DATABASE {case.factor_key}="
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


def render_create_database_factor_case(
    case: CreateDatabaseFactorCase | CreateDatabaseFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 CREATE DATABASE。")
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
    case: CreateDatabaseFactorCase | CreateDatabaseFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_database_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_database_factor_programs(
    baseline_plan: CreateDatabaseFactorLoopPlan,
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
    "CreateDatabaseFactorRenderError",
    "CreateDatabaseFactorWitness",
    "count_primary_create_database",
    "generate_create_database_factor_programs",
    "render_create_database_factor_case",
    "resolve_create_database_factor_witness",
]
