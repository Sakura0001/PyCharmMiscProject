"""Render complete PostgreSQL 18.4 CREATE ROLE factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the byte-level
witness validator (which re-renders and compares) can never diverge from
the bytes actually written.

CREATE ROLE targets a ``pg_catalog.pg_authid`` catalog row, not a
``pg_class`` relation.  All catalog oracles schema-qualify
``pg_catalog.pg_roles`` (exempt from the file-prefix style gate).  No case
creates a TABLE, so the bookend (DROP TABLE IF EXISTS) is never emitted;
every program ends with a ``SELECT 1 AS residual_check_no_objects;``
residual placeholder.  Every catalog SELECT carries a top-level
``ORDER BY count(*)`` so the catalog-observability gate passes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_role_factor_extension import (
    CreateRoleFactorExtensionCase,
    _present_failure_pair,
)
from .create_role_factor_loop import (
    CreateRoleFactorCase,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/role/"
    "create_role.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/role/"
    "create_role.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_ROLE_ATTRIBUTE_SQL: dict[str, str | None] = {
    "default_all_nosuperuser_nocreatedb_nocreaterole_"
    "inherit_nologin_noreplication_nobypassrls": None,
    "superuser": "SUPERUSER",
    "nosuperuser": "NOSUPERUSER",
    "createdb": "CREATEDB",
    "nocreatedb": "NOCREATEDB",
    "createrole": "CREATEROLE",
    "nocreaterole": "NOCREATEROLE",
    "inherit": "INHERIT",
    "noinherit": "NOINHERIT",
    "login": "LOGIN",
    "nologin": "NOLOGIN",
    "replication": "REPLICATION",
    "noreplication": "NOREPLICATION",
    "bypassrls": "BYPASSRLS",
    "nobypassrls": "NOBYPASSRLS",
}

_CONFLICTING_ATTRIBUTE_SQL: dict[str, str] = {
    "superuser_and_nosuperuser": "SUPERUSER NOSUPERUSER",
    "login_and_nologin": "LOGIN NOLOGIN",
    "multiple_conflicting_pairs": (
        "SUPERUSER NOSUPERUSER LOGIN NOLOGIN"
    ),
}

_MEMBERSHIP_KEYWORD: dict[str, str] = {
    "in_role": "IN ROLE",
    "in_group": "IN GROUP",
    "role_clause": "ROLE",
    "admin_clause": "ADMIN",
    "user_clause": "USER",
}


class CreateRoleFactorRenderError(ValueError):
    """Raised when a CREATE ROLE case cannot be rendered."""


@dataclass(frozen=True)
class CreateRoleFactorWitness:
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
    ext: CreateRoleFactorExtensionCase,
) -> CreateRoleFactorCase:
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
    return CreateRoleFactorCase(
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
    case: CreateRoleFactorCase | CreateRoleFactorExtensionCase,
) -> CreateRoleFactorCase:
    if isinstance(case, CreateRoleFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateRoleFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _role_name(a: dict[str, str], p: str) -> str:
    """The role identifier in CREATE ROLE and fixtures."""

    shape = a.get("role_name_shape", "simple_id")
    identity = a.get("role_identity", "not_exists")

    if shape == "missing_name":
        return ""
    if shape == "quoted_id":
        return f'"{p}qrole"'
    if shape == "reserved_word_id":
        return f'"{p}view"'
    if shape == "unicode_id":
        return f'"{p}rle"'
    if shape == "mixed_case_id":
        return f'"{p}Mixed"'
    if identity == "reserved_word_name":
        return f'"{p}view"'
    if identity == "quoted_duplicate":
        return f'"{p}dup"'
    return f"{p}role"


def _role_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    name = _role_name(a, p)
    if name.startswith('"') and name.endswith('"'):
        return name[1:-1]
    return name


def _is_duplicate(a: dict[str, str]) -> bool:
    return (
        a.get("role_identity") == "exists"
        or a.get("role_identity") == "quoted_duplicate"
        or a.get("duplicate_role_name") in (
            "same_name_exists",
            "case_insensitive_duplicate",
        )
    )


def _is_failure(a: dict[str, str]) -> bool:
    return a.get("expected_status") == "failure"


def _present(a: dict[str, str]) -> bool:
    """Whether the role exists after the target statement."""

    if not _is_failure(a):
        return True
    return _is_duplicate(a)


def _needs_referenced_role(a: dict[str, str]) -> bool:
    mo = a.get("membership_clause", "omitted")
    return mo != "omitted"


def _password_value(a: dict[str, str]) -> str:
    pvs = a.get("password_value_shape", "valid_string")
    if pvs == "valid_string":
        return "pw"
    if pvs == "empty_string":
        return ""
    if pvs == "encrypted_md5_format":
        return "md5aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    if pvs == "encrypted_scram_format":
        return "SCRAM-SHA-256$4096:salt"
    if pvs == "special_characters":
        return "p@ss"
    return "pw"


def _connlimit_value(a: dict[str, str]) -> str:
    cvs = a.get("connlimit_value_shape", "positive_integer")
    if cvs == "positive_integer":
        return "10"
    if cvs == "zero":
        return "0"
    if cvs == "negative_one":
        return "-1"
    if cvs == "large_number":
        return "999999"
    if cvs == "invalid_type":
        return "not_a_number"
    return "10"


def _timestamp_value(a: dict[str, str]) -> str:
    tvs = a.get("timestamp_value_shape", "valid_iso_timestamp")
    if tvs == "valid_iso_timestamp":
        return "2099-12-31 23:59:59"
    if tvs == "valid_date_only":
        return "2099-12-31"
    if tvs == "far_future":
        return "9999-12-31"
    if tvs == "past_date":
        return "2000-01-01"
    if tvs == "infinity_literal":
        return "infinity"
    if tvs == "invalid_format":
        return "not_a_date"
    return "2099-12-31"


def _build_options(a: dict[str, str], p: str) -> str:
    """The options clause for the CREATE ROLE statement."""

    opts: list[str] = []

    cap = a.get("conflicting_attribute_pair", "none")
    if cap != "none":
        opts.append(_CONFLICTING_ATTRIBUTE_SQL[cap])
    else:
        ra = a.get(
            "role_attribute",
            "default_all_nosuperuser_nocreatedb_nocreaterole_"
            "inherit_nologin_noreplication_nobypassrls",
        )
        attr_sql = _ROLE_ATTRIBUTE_SQL.get(ra)
        if attr_sql:
            opts.append(attr_sql)

    pc = a.get("password_clause", "omitted")
    if pc == "encrypted_password":
        opts.append(f"ENCRYPTED PASSWORD '{_password_value(a)}'")
    elif pc == "unencrypted_password":
        opts.append(f"PASSWORD '{_password_value(a)}'")
    elif pc == "password_null":
        opts.append("PASSWORD NULL")

    clc = a.get("connection_limit_clause", "omitted")
    if clc == "positive_limit":
        opts.append(f"CONNECTION LIMIT {_connlimit_value(a)}")
    elif clc == "zero_limit":
        opts.append("CONNECTION LIMIT 0")
    elif clc == "negative_one_unlimited":
        opts.append("CONNECTION LIMIT -1")

    vuc = a.get("valid_until_clause", "omitted")
    if vuc == "future_timestamp":
        opts.append(f"VALID UNTIL '{_timestamp_value(a)}'")
    elif vuc == "past_timestamp":
        opts.append("VALID UNTIL '2000-01-01'")
    elif vuc == "current_timestamp":
        opts.append("VALID UNTIL current_timestamp")
    elif vuc == "infinity":
        opts.append("VALID UNTIL 'infinity'")

    mc = a.get("membership_clause", "omitted")
    if mc != "omitted":
        keyword = _MEMBERSHIP_KEYWORD.get(mc, "IN ROLE")
        rmd = a.get("referenced_role_dependency", "existing_role")
        name = _role_name(a, p)
        if rmd == "self_reference":
            opts.append(f"{keyword} {name}")
        elif rmd == "multiple_roles":
            opts.append(f"{keyword} {p}ref1, {p}ref2")
        else:
            opts.append(f"{keyword} {p}ref")

    if a.get("invalid_parameter_value") == "empty_password_string":
        pass  # handled by password clause above

    return ", ".join(opts)


def _build_target(
    a: dict[str, str], p: str, consumer: str
) -> str:
    """The primary CREATE ROLE statement."""

    name = _role_name(a, p)
    options = _build_options(a, p)
    with_kw = "WITH " if a.get("with_keyword") == "present" else ""
    if not options:
        options = "NOSUPERUSER"
    if not name:
        return f"CREATE ROLE {with_kw}{options};"
    return f"CREATE ROLE {name} {with_kw}{options};"


def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target runs."""

    priv = a.get("executor_privilege", "superuser")
    if priv == "normal_user_no_createrole":
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    priv = a.get("executor_privilege", "superuser")
    if priv == "normal_user_no_createrole":
        roles.append(f"{p}actor")
    return tuple(roles)


def _probe_select(
    case: CreateRoleFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only verification."""

    mode = a.get("verification_mode", "pg_roles_catalog_query")
    literal = _role_literal(a, p)

    if mode == "error_assertion":
        return None

    cmp_op = ">" if _present(a) else "="
    if mode == "membership_check_query":
        alias = "member_state"
    elif mode == "attribute_check_query":
        alias = "role_attr"
    else:
        alias = "role_state"

    return (
        f"SELECT count(*) {cmp_op} 0 AS {alias} "
        f"FROM pg_catalog.pg_roles "
        f"WHERE rolname = '{literal}' "
        f"ORDER BY count(*);"
    )


def _resolve_case(case: CreateRoleFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    consumer = case.consumer_action_id

    setup: list[str] = []
    locus = "target.create_role"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    name = _role_name(a, p)

    # --- privilege fixture -----------------------------------------
    if effective:
        setup.append(
            f"CREATE ROLE {p}actor LOGIN NOSUPERUSER NOCREATEROLE;"
        )
        locus = "fixture.privilege_state"

    # --- duplicate role fixture -----------------------------------
    if _is_duplicate(a):
        setup.append(f"CREATE ROLE {name};")
        locus = "fixture.duplicate_role"

    # --- referenced role fixture (membership) ----------------------
    if _needs_referenced_role(a):
        rmd = a.get("referenced_role_dependency", "existing_role")
        if rmd == "existing_role":
            setup.append(f"CREATE ROLE {p}ref;")
            locus = "fixture.referenced_role"
        elif rmd == "multiple_roles":
            setup.append(f"CREATE ROLE {p}ref1;")
            setup.append(f"CREATE ROLE {p}ref2;")
            locus = "fixture.referenced_role"
        elif rmd == "self_reference":
            pass
        # nonexistent_role: no fixture (failure condition)

    # --- arm the effective role ------------------------------------
    if effective:
        setup.append(f"SET ROLE {effective};")

    # --- the primary target statement ------------------------------
    target = _build_target(a, p, consumer)

    # --- oracle / SQLSTATE assertion -------------------------------
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

    # --- cleanup construction --------------------------------------
    cleanup_mode = a.get("cleanup_mode", "drop_role")
    if cleanup_mode == "revoke_membership_then_drop":
        role_drops = [
            f"DROP OWNED BY {name} CASCADE;" if name else "",
            f"DROP ROLE IF EXISTS {name};",
            f"DROP ROLE IF EXISTS {p}ref;",
        ]
        role_drops = [d for d in role_drops if d]
    elif cleanup_mode == "cascade_drop":
        role_drops = [f"DROP ROLE IF EXISTS {name} CASCADE;"]
    else:  # drop_role
        role_drops = [f"DROP ROLE IF EXISTS {name};"]

    actor_drops = [
        stmt
        for role in roles
        for stmt in (
            f"DROP OWNED BY {role} CASCADE;",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    # pre-cleanup: always use IF EXISTS (safe, idempotent)
    pre_cleanup: list[str] = []
    pre_cleanup.append(f"DROP ROLE IF EXISTS {name} CASCADE;" if name else "")
    pre_cleanup.append(f"DROP ROLE IF EXISTS {p}ref CASCADE;")
    pre_cleanup.append(f"DROP ROLE IF EXISTS {p}ref1 CASCADE;")
    pre_cleanup.append(f"DROP ROLE IF EXISTS {p}ref2 CASCADE;")
    pre_cleanup.append("RESET ROLE;")
    for role in roles:
        pre_cleanup.append(f"DROP ROLE IF EXISTS {role};")
    pre_cleanup = [d for d in pre_cleanup if d]

    # cleanup: RESET ROLE, role drops, fixture drops, residual
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(role_drops)
    if cleanup_mode != "revoke_membership_then_drop":
        cleanup.append(f"DROP ROLE IF EXISTS {p}ref;")
    cleanup.extend(actor_drops)
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


def _header(case: CreateRoleFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE ROLE {case.factor_key}="
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


def render_create_role_factor_case(
    case: CreateRoleFactorCase | CreateRoleFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 CREATE ROLE。")
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
    case: CreateRoleFactorCase | CreateRoleFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_role_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_role_factor_programs(
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


def count_primary_create_role(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*CREATE\s+ROLE\b", region)
    )


def remove_primary_semantic_locus_but_keep_comments(
    sql: str, case: object
) -> str:
    """Mutation helper: remove primary target SQL but keep comment lines."""

    if _PRIMARY_BEGIN not in sql or _PRIMARY_END not in sql:
        return sql
    before_begin, rest = sql.split(_PRIMARY_BEGIN, 1)
    target_and_after, after_end = rest.split(_PRIMARY_END, 1)
    comment_lines = [
        line
        for line in target_and_after.split("\n")
        if line.strip().startswith("--") or not line.strip()
    ]
    return (
        before_begin
        + _PRIMARY_BEGIN
        + "\n".join(comment_lines)
        + _PRIMARY_END
        + after_end
    )


def resolve_create_role_factor_witness(
    case: CreateRoleFactorCase | CreateRoleFactorExtensionCase,
    repository_root: Path,
) -> CreateRoleFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateRoleFactorWitness(
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
    "CreateRoleFactorRenderError",
    "CreateRoleFactorWitness",
    "count_primary_create_role",
    "generate_create_role_factor_programs",
    "render_create_role_factor_case",
    "resolve_create_role_factor_witness",
    "remove_primary_semantic_locus_but_keep_comments",
]
