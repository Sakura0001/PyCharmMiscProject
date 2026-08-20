"""Render complete PostgreSQL 18.4 CREATE USER MAPPING factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CREATE USER MAPPING is a catalog-row DDL statement: the target is a
``pg_catalog.pg_user_mapping`` catalog row, not a ``pg_class`` relation.
All catalog oracles schema-qualify ``pg_catalog.pg_user_mapping`` /
``pg_catalog.pg_foreign_server`` (exempt from the file-prefix style gate
via the ``pg_`` prefix).  No case creates a TABLE, so the bookend
(DROP TABLE IF EXISTS) is never emitted.  Every catalog SELECT carries
a top-level ``ORDER BY`` so the catalog-observability gate passes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_user_mapping_factor_extension import (
    CreateUserMappingFactorExtensionCase,
    _present_failure_pair,
)
from .create_user_mapping_factor_loop import (
    CreateUserMappingFactorCase,
    CreateUserMappingFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/"
    "user_mapping/create_user_mapping.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/"
    "user_mapping/create_user_mapping.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class CreateUserMappingFactorRenderError(ValueError):
    """Raised when a CREATE USER MAPPING case cannot be rendered."""


@dataclass(frozen=True)
class CreateUserMappingFactorWitness:
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
    ext: CreateUserMappingFactorExtensionCase,
) -> CreateUserMappingFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_form"
        factor_value = assignment.get(
            "target_form", ext.consumer_action_id
        )
    return CreateUserMappingFactorCase(
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
    case: CreateUserMappingFactorCase
    | CreateUserMappingFactorExtensionCase,
) -> CreateUserMappingFactorCase:
    if isinstance(
        case, CreateUserMappingFactorExtensionCase
    ):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateUserMappingFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _schema_name(p: str) -> str:
    return f"{p}schema"


def _fdw_name(p: str) -> str:
    return f"{p}fdw"


def _server_name(a: dict[str, str], p: str) -> str:
    """The foreign server identifier referenced by SERVER."""

    shape = a.get("server_name_shape", "simple_id")
    if shape == "nonexistent_name":
        return f"{p}noserver"
    return f"{p}server"


def _server_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    shape = a.get("server_name_shape", "simple_id")
    if shape == "nonexistent_name":
        return f"{p}noserver"
    return f"{p}server"


def _for_user(a: dict[str, str], p: str) -> str:
    """The FOR clause value in CREATE USER MAPPING."""

    us = a.get("user_specification", "named_user")
    if us == "public":
        return "PUBLIC"
    if us == "user_keyword":
        return "USER"
    if us == "current_role":
        return "CURRENT_ROLE"
    if us == "current_user":
        return "CURRENT_USER"
    # named_user — shape determines the identifier
    shape = a.get("user_name_shape", "simple_id")
    if shape == "quoted_id":
        return f'"{p}User"'
    if shape == "nonexistent_name":
        return f"{p}nosuchuser"
    if shape == "public_keyword":
        return "PUBLIC"
    return f"{p}user"


def _for_user_literal(a: dict[str, str], p: str) -> str:
    """The unquoted role name literal for fixture/cleanup."""

    us = a.get("user_specification", "named_user")
    if us == "public":
        return "PUBLIC"
    if us in ("user_keyword", "current_role", "current_user"):
        return ""
    shape = a.get("user_name_shape", "simple_id")
    if shape == "quoted_id":
        return f"{p}User"
    if shape == "nonexistent_name":
        return f"{p}nosuchuser"
    if shape == "public_keyword":
        return "PUBLIC"
    return f"{p}user"


def _options_clause(a: dict[str, str], p: str) -> str:
    """The OPTIONS (...) clause or empty string."""

    ovs = a.get("option_value_shape", "valid_value")
    oc = a.get("options_clause", "omitted")

    if ovs == "duplicate_option_name":
        return "OPTIONS (user 'val1', user 'val2')"

    if oc == "omitted":
        return ""

    if ovs == "quoted_value":
        if oc == "single_option":
            return "OPTIONS (user 'val with space')"
        return (
            "OPTIONS (user 'val with space', "
            "password 'pass with space')"
        )

    if oc == "single_option":
        return "OPTIONS (user 'val1')"
    return "OPTIONS (user 'val1', password 'val2')"


def _is_duplicate(a: dict[str, str]) -> bool:
    return (
        a.get("object_state") == "exists"
        or a.get("duplicate_mapping")
        == "existing_mapping_without_if_not_exists"
    )


def _is_nonexistent_server(a: dict[str, str]) -> bool:
    return a.get("server_name_shape") == "nonexistent_name"


def _is_nonexistent_user(a: dict[str, str]) -> bool:
    return a.get("user_name_shape") == "nonexistent_name"


def _is_insufficient_privilege(a: dict[str, str]) -> bool:
    return a.get("privilege_level") == "non_privileged"


def _is_duplicate_option(a: dict[str, str]) -> bool:
    return (
        a.get("option_value_shape") == "duplicate_option_name"
        or a.get("duplicate_option_name") == "duplicate_option"
    )


def _is_failure(a: dict[str, str]) -> bool:
    return a.get("expected_status") == "failure"


def _has_if_not_exists(a: dict[str, str]) -> bool:
    return a.get("if_not_exists_clause") == "present"


def _is_user_with_usage(a: dict[str, str]) -> bool:
    return a.get("privilege_level") == "user_with_usage"


def _effective_role(a: dict[str, str], p: str) -> str:
    if _is_insufficient_privilege(a) or _is_user_with_usage(a):
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    if _effective_role(a, p):
        roles.append(f"{p}actor")
    us = a.get("user_specification", "named_user")
    shape = a.get("user_name_shape", "simple_id")
    if us == "named_user" and shape == "simple_id":
        roles.append(f"{p}user")
    return tuple(roles)


def _build_fdw_server_fixtures(
    a: dict[str, str], p: str
) -> list[str]:
    """Setup lines for FDW and foreign server fixtures."""

    if _is_nonexistent_server(a):
        return []
    schema = _schema_name(p)
    fdw = _fdw_name(p)
    server = _server_name(a, p)
    return [
        f"CREATE FOREIGN DATA WRAPPER {fdw};",
        f"CREATE SERVER {server} FOREIGN DATA WRAPPER {fdw};",
    ]


def _build_user_fixture(
    a: dict[str, str], p: str
) -> list[str]:
    """Setup line for the named user role (when needed)."""

    us = a.get("user_specification", "named_user")
    shape = a.get("user_name_shape", "simple_id")
    if us == "named_user" and shape == "simple_id":
        return [f"CREATE ROLE {p}user LOGIN;"]
    if us == "named_user" and shape == "quoted_id":
        return [f'CREATE ROLE "{p}User" LOGIN;']
    return []


def _build_privilege_fixture(
    a: dict[str, str], p: str
) -> list[str]:
    """Setup lines for privilege-context role fixtures."""

    role = _effective_role(a, p)
    if not role:
        return []
    lines: list[str] = [f"CREATE ROLE {role} LOGIN NOSUPERUSER;"]
    if _is_user_with_usage(a):
        server = _server_name(a, p)
        lines.append(
            f"GRANT USAGE ON FOREIGN SERVER {server} TO {role};"
        )
    return lines


def _build_duplicate_fixture(
    a: dict[str, str], p: str
) -> list[str]:
    """Pre-create the mapping for duplicate-signature tests."""

    if not _is_duplicate(a):
        return []
    if _is_nonexistent_server(a):
        return []
    server = _server_name(a, p)
    for_user = _for_user(a, p)
    for_lit = _for_user_literal(a, p)
    options = _options_clause(a, p)
    opts = f" {options}" if options else ""
    lines: list[str] = []
    if for_lit and for_lit != "PUBLIC":
        lines.append(f"CREATE ROLE {for_lit} LOGIN;")
    lines.append(
        f"CREATE USER MAPPING FOR {for_user} "
        f"SERVER {server}{opts};"
    )
    return lines


def _build_target(
    a: dict[str, str], p: str
) -> str:
    """The primary CREATE USER MAPPING statement."""

    ine = ""
    if _has_if_not_exists(a):
        ine = "IF NOT EXISTS "
    for_user = _for_user(a, p)
    server = _server_name(a, p)
    options = _options_clause(a, p)
    opts = f" {options}" if options else ""
    return (
        f"CREATE USER MAPPING {ine}FOR {for_user} "
        f"SERVER {server}{opts};"
    )


def _probe_select(
    case: CreateUserMappingFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only verification."""

    mode = a.get(
        "verification_mode", "catalog_query_pg_user_mapping"
    )
    if mode == "error_assertion":
        return None

    server_lit = _server_literal(a, p)
    present = not (
        _is_failure(a)
        and not _is_duplicate(a)
    )
    cmp_op = ">" if present else "="
    return (
        f"SELECT count(*) {cmp_op} 0 AS mapping_state "
        f"FROM pg_catalog.pg_user_mapping um "
        f"JOIN pg_catalog.pg_foreign_server fs "
        f"ON um.umserver = fs.oid "
        f"WHERE fs.srvname = '{server_lit}' "
        f"ORDER BY count(*);"
    )


def _build_cleanup(
    a: dict[str, str], p: str
) -> list[str]:
    """Cleanup lines after the primary target."""

    schema = _schema_name(p)
    fdw = _fdw_name(p)
    server = _server_name(a, p)
    cleanup_mode = a.get(
        "cleanup_mode", "drop_user_mapping"
    )
    lines: list[str] = []
    if _effective_role(a, p):
        lines.append("RESET ROLE;")
    if cleanup_mode in ("drop_user_mapping", "drop_server", "drop_fdw"):
        for_lit = _for_user_literal(a, p)
        if for_lit and for_lit != "PUBLIC":
            if not _is_nonexistent_server(a):
                lines.append(
                    f"DROP USER MAPPING IF EXISTS "
                    f"FOR {for_lit} SERVER {server};"
                )
    if cleanup_mode in ("drop_server", "drop_fdw"):
        if not _is_nonexistent_server(a):
            lines.append(
                f"DROP SERVER IF EXISTS {server} CASCADE;"
            )
    if cleanup_mode == "drop_fdw":
        lines.append(
            f"DROP FOREIGN DATA WRAPPER IF EXISTS {fdw} CASCADE;"
        )
    lines.append(f"DROP SCHEMA IF EXISTS {schema} CASCADE;")
    for role in _role_names(a, p):
        lines.append(f"DROP OWNED BY {role} CASCADE;")
        lines.append(f"DROP ROLE IF EXISTS {role};")
    return lines


def _resolve_case(
    case: CreateUserMappingFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    schema = _schema_name(p)
    fdw = _fdw_name(p)

    setup: list[str] = []
    locus = "target.create_user_mapping"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)

    # --- schema fixture ---
    setup.append(f"CREATE SCHEMA {schema};")
    locus = "fixture.schema"

    # --- FDW + server fixtures ---
    if not _is_nonexistent_server(a):
        setup.extend(_build_fdw_server_fixtures(a, p))
        locus = "fixture.foreign_server"

    # --- named user role fixture ---
    setup.extend(_build_user_fixture(a, p))

    # --- privilege context fixtures ---
    if effective:
        setup.extend(_build_privilege_fixture(a, p))
        locus = "fixture.privilege_state"

    # --- duplicate mapping fixture ---
    if _is_duplicate(a):
        setup.extend(_build_duplicate_fixture(a, p))
        locus = "fixture.duplicate_mapping"

    if effective:
        setup.append(f"SET ROLE {effective};")

    # --- the primary target statement ---
    target = _build_target(a, p)

    # --- oracle / SQLSTATE assertion ---
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

    # --- cleanup construction ---
    cleanup = _build_cleanup(a, p)

    # --- pre-cleanup (safe, always IF EXISTS CASCADE) ---
    pre_cleanup: list[str] = []
    for_lit = _for_user_literal(a, p)
    server = _server_name(a, p)
    if for_lit and for_lit != "PUBLIC":
        if not _is_nonexistent_server(a):
            pre_cleanup.append(
                f"DROP USER MAPPING IF EXISTS "
                f"FOR {for_lit} SERVER {server};"
            )
    if not _is_nonexistent_server(a):
        pre_cleanup.append(
            f"DROP SERVER IF EXISTS {server} CASCADE;"
        )
    pre_cleanup.append(
        f"DROP FOREIGN DATA WRAPPER IF EXISTS {fdw} CASCADE;"
    )
    pre_cleanup.append(f"DROP SCHEMA IF EXISTS {schema} CASCADE;")
    pre_cleanup.append("RESET ROLE;")
    for role in roles:
        pre_cleanup.append(f"DROP ROLE IF EXISTS {role};")
    if not pre_cleanup:
        pre_cleanup.append(
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


def _header(case: CreateUserMappingFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE USER MAPPING "
        f"{case.factor_key}={case.factor_value}",
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


def render_create_user_mapping_factor_case(
    case: CreateUserMappingFactorCase
    | CreateUserMappingFactorExtensionCase,
    repository_root: Path,
) -> str:
    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("SELECT 1 AS setup_boundary;")
    lines.append("-- 2. 创建完整本地规则和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("SELECT 1 AS pre_target_boundary;")
    lines.append(
        "-- 3. 执行唯一获得覆盖信用的 CREATE USER MAPPING。"
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
    case: CreateUserMappingFactorCase
    | CreateUserMappingFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_user_mapping_factor_case(
        case, Path(".")
    )
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_user_mapping_factor_programs(
    baseline_plan: CreateUserMappingFactorLoopPlan,
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


def count_primary_create_user_mapping(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(
            r"(?im)^CREATE\s+USER\s+MAPPING\b",
            region,
        )
    )


def resolve_create_user_mapping_factor_witness(
    case: CreateUserMappingFactorCase
    | CreateUserMappingFactorExtensionCase,
    repository_root: Path,
) -> CreateUserMappingFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateUserMappingFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


__all__ = [
    "CreateUserMappingFactorRenderError",
    "CreateUserMappingFactorWitness",
    "count_primary_create_user_mapping",
    "generate_create_user_mapping_factor_programs",
    "render_create_user_mapping_factor_case",
    "resolve_create_user_mapping_factor_witness",
]
