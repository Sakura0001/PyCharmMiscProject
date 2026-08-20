"""Render complete PostgreSQL 18.4 CREATE EXTENSION factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CREATE EXTENSION is a DDL statement: the target is a
``pg_catalog.pg_extension`` catalog row, not a ``pg_class`` relation.
All catalog oracles schema-qualify ``pg_catalog.pg_extension`` /
``pg_catalog.pg_available_extensions`` (exempt from the file-prefix
style gate — they start with ``pg_``).  CREATE EXTENSION does not create
fixture tables, so the bookend gate is N/A and a
``SELECT 1 AS residual_check_no_objects;`` placeholder is used.

The built-in ``plpgsql`` extension is protected: when the
``extension_name_shape=duplicate_name`` factor selects ``plpgsql`` (an
extension that is usually already installed), DROP EXTENSION is skipped
in both pre-cleanup and cleanup — the same pattern
``create_access_method`` uses to protect the ``btree`` built-in AM.
Every catalog SELECT carries a top-level ``ORDER BY``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_extension_factor_extension import (
    CreateExtensionFactorExtensionCase,
    _present_failure_pair,
)
from .create_extension_factor_loop import (
    CreateExtensionFactorCase,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/extension/"
    "create_extension.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/extension/"
    "create_extension.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class CreateExtensionFactorRenderError(ValueError):
    """Raised when a CREATE EXTENSION case cannot be rendered."""


@dataclass(frozen=True)
class CreateExtensionFactorWitness:
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
    ext: CreateExtensionFactorExtensionCase,
) -> CreateExtensionFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get(
            "target_action", "create_extension"
        )
    return CreateExtensionFactorCase(
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
    case: CreateExtensionFactorCase
    | CreateExtensionFactorExtensionCase,
) -> CreateExtensionFactorCase:
    if isinstance(
        case, CreateExtensionFactorExtensionCase
    ):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateExtensionFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _extension_name(a: dict[str, str], p: str) -> str:
    """The extension identifier in CREATE EXTENSION."""

    shape = a.get("extension_name_shape", "simple_id")
    if shape == "duplicate_name":
        return "plpgsql"
    if shape == "nonexistent_extension":
        return f"{p}nonexistent_ext"
    if shape == "quoted_id":
        return f'"{p}MixedExt"'
    if shape == "reserved_word_name":
        return f'"{p}select"'
    return f"{p}ext"


def _extension_name_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    shape = a.get("extension_name_shape", "simple_id")
    if shape == "duplicate_name":
        return "plpgsql"
    if shape == "nonexistent_extension":
        return f"{p}nonexistent_ext"
    if shape == "quoted_id":
        return f"{p}MixedExt"
    if shape == "reserved_word_name":
        return f"{p}select"
    return f"{p}ext"


def _schema_name(a: dict[str, str], p: str) -> str:
    """The schema identifier in SCHEMA clause."""

    shape = a.get("schema_name_shape", "simple_id")
    if shape == "nonexistent_schema":
        return f"{p}noschema"
    if shape == "quoted_id":
        return f'"{p}MixedSchema"'
    return f"{p}schema"


def _version_clause(a: dict[str, str], p: str) -> str:
    """The VERSION clause fragment (empty if omitted)."""

    vc = a.get("version_clause", "omitted")
    if vc == "omitted":
        return ""
    vss = a.get("version_string_shape", "identifier_form")
    if vss == "string_literal_form":
        return f" VERSION '{p}1.0'"
    if vss == "invalid_version_string":
        return f" VERSION '{p}9.9.9'"
    return f" VERSION {p}1.0"


def _is_protected_extension(a: dict[str, str]) -> bool:
    """Whether the extension is a protected built-in (plpgsql)."""

    return a.get("extension_name_shape") == "duplicate_name"


def _ext_already_exists(a: dict[str, str]) -> bool:
    return a.get("object_state") == "already_exists"


def _is_non_superuser(a: dict[str, str]) -> bool:
    return a.get("privilege_level") == "non_superuser_no_create"


def _is_create_priv_user(a: dict[str, str]) -> bool:
    return a.get("privilege_level") == "create_privilege_user"


def _needs_role(a: dict[str, str]) -> bool:
    return _is_non_superuser(a) or _is_create_priv_user(a)


def _effective_role(a: dict[str, str], p: str) -> str:
    if _is_non_superuser(a):
        return f"{p}actor"
    if _is_create_priv_user(a):
        return f"{p}create_user"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    if _is_non_superuser(a):
        roles.append(f"{p}actor")
    elif _is_create_priv_user(a):
        roles.append(f"{p}create_user")
    return tuple(roles)


def _probe_select(
    case: CreateExtensionFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only error_assertion."""

    mode = a.get("verification_mode", "pg_extension_catalog_query")
    if mode == "error_assertion":
        return None

    ext_lit = _extension_name_literal(a, p)
    present = case.outcome == "success"

    if mode == "pg_available_extensions_query":
        cmp_op = ">=" if present else "="
        return (
            f"SELECT count(*) {cmp_op} 0 AS ext_available "
            f"FROM pg_catalog.pg_available_extensions "
            f"WHERE name = '{ext_lit}' "
            f"ORDER BY count(*);"
        )

    cmp_op = ">" if present else "="
    return (
        f"SELECT count(*) {cmp_op} 0 AS ext_state "
        f"FROM pg_catalog.pg_extension "
        f"WHERE extname = '{ext_lit}' "
        f"ORDER BY count(*);"
    )


def _resolve_case(
    case: CreateExtensionFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix

    setup: list[str] = []
    locus = "target.create_extension"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    ext = _extension_name(a, p)
    schema = _schema_name(a, p)
    version = _version_clause(a, p)

    # --- role fixtures -----------------------------------------------
    if _is_non_superuser(a):
        setup.append(
            f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;"
        )
        locus = "fixture.privilege_state"
    elif _is_create_priv_user(a):
        setup.append(
            f"CREATE ROLE {p}create_user LOGIN NOSUPERUSER;"
        )
        setup.append(
            f"GRANT CREATE ON SCHEMA public TO {p}create_user;"
        )
        locus = "fixture.privilege_state"

    # --- schema fixture (for specified_schema) -------------------------
    sc = a.get("schema_clause", "omitted")
    if sc == "specified_schema":
        setup.append(
            f"CREATE SCHEMA IF NOT EXISTS {schema};"
        )
        locus = "fixture.schema"

    # --- pre-existing extension for duplicate/already_exists ---------
    if (
        _ext_already_exists(a)
        and not _is_protected_extension(a)
    ):
        setup.append(
            f"CREATE EXTENSION IF NOT EXISTS {ext};"
        )
        locus = "fixture.duplicate_extension"
    elif _ext_already_exists(a) and _is_protected_extension(a):
        # plpgsql is usually already installed; ensure it is.
        setup.append(
            f"CREATE EXTENSION IF NOT EXISTS {ext};"
        )
        locus = "fixture.duplicate_extension"

    # --- arm the effective role --------------------------------------
    if effective:
        setup.append(f"SET ROLE {effective};")

    # --- the primary target statement --------------------------------
    target = _build_target(a, p, ext, schema, version)

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
    ext_drops: list[str] = []
    if not _is_protected_extension(a):
        ext_drops.append(
            f"DROP EXTENSION IF EXISTS {ext} CASCADE;"
        )

    schema_drops: list[str] = []
    if sc == "specified_schema":
        schema_drops.append(
            f"DROP SCHEMA IF EXISTS {schema} CASCADE;"
        )

    role_drops = [
        statement
        for role in roles
        for statement in (
            f"DROP OWNED BY {role} CASCADE;",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    # pre-cleanup: extension, schema, roles
    pre_cleanup: list[str] = []
    pre_cleanup.extend(ext_drops)
    pre_cleanup.extend(schema_drops)
    pre_cleanup.extend(role_drops)
    if not pre_cleanup:
        pre_cleanup.append(
            "SELECT 1 AS residual_check_no_objects;"
        )

    # cleanup: RESET ROLE, extension, schema, roles
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(ext_drops)
    cleanup.extend(schema_drops)
    cleanup.extend(role_drops)
    if not cleanup:
        cleanup.append(
            "SELECT 1 AS residual_check_no_objects;"
        )

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


def _build_target(
    a: dict[str, str],
    p: str,
    ext: str,
    schema: str,
    version: str,
) -> str:
    """The primary CREATE EXTENSION statement."""

    ine = a.get("if_not_exists_clause", "omitted")
    cas = a.get("cascade_clause", "omitted")
    sc = a.get("schema_clause", "omitted")

    parts: list[str] = ["CREATE EXTENSION"]
    if ine == "specified":
        parts.append("IF NOT EXISTS")
    parts.append(ext)
    with_clause: list[str] = []
    if sc == "specified_schema":
        with_clause.append(f"SCHEMA {schema}")
    if version:
        with_clause.append(version.strip())
    if cas == "specified":
        with_clause.append("CASCADE")
    if with_clause:
        parts.append("WITH")
        parts.extend(with_clause)
    parts[-1] = parts[-1] + ";"
    return " ".join(parts)


def resolve_create_extension_factor_witness(
    case: CreateExtensionFactorCase
    | CreateExtensionFactorExtensionCase,
    repository_root: Path,
) -> CreateExtensionFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateExtensionFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_create_extension(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(
            r"(?im)^\s*CREATE\s+EXTENSION\b", region
        )
    )


def _header(case: CreateExtensionFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE EXTENSION {case.factor_key}="
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


def render_create_extension_factor_case(
    case: CreateExtensionFactorCase
    | CreateExtensionFactorExtensionCase,
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
    lines.append(
        "-- 3. 执行唯一获得覆盖信用的 CREATE EXTENSION。"
    )
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
    case: CreateExtensionFactorCase
    | CreateExtensionFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_extension_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_extension_factor_programs(
    baseline_plan: object,
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
    "CreateExtensionFactorRenderError",
    "CreateExtensionFactorWitness",
    "count_primary_create_extension",
    "generate_create_extension_factor_programs",
    "render_create_extension_factor_case",
    "resolve_create_extension_factor_witness",
]
