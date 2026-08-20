"""Render complete PostgreSQL 18.4 ALTER SERVER factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

ALTER SERVER is a NON-TABLE statement: the target is a
``pg_catalog.pg_foreign_server`` row backed by a foreign data wrapper,
not a ``pg_class`` relation.  All catalog oracles therefore
schema-qualify ``pg_catalog.pg_foreign_server`` (exempt from the
file-prefix style gate).  No ``CREATE TABLE`` is ever emitted, so the
bookend contract is satisfied vacuously (``_tables_to_drop`` is always
empty); the bookend scaffolding is kept for structural parity with
``alter_schema_factor_render``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .alter_server_factor_extension import (
    AlterServerFactorExtensionCase,
    _present_failure_pair,
)
from .alter_server_factor_loop import (
    AlterServerFactorCase,
    AlterServerFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/server/"
    "alter_server.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/server/"
    "alter_server.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class AlterServerFactorRenderError(ValueError):
    """Raised when an ALTER SERVER case cannot be rendered."""


@dataclass(frozen=True)
class AlterServerFactorWitness:
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
    ext: AlterServerFactorExtensionCase,
) -> AlterServerFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get("target_action", "version_options")
    return AlterServerFactorCase(
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
    case: AlterServerFactorCase | AlterServerFactorExtensionCase,
) -> AlterServerFactorCase:
    if isinstance(case, AlterServerFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: AlterServerFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _is_rename(a: dict[str, str]) -> bool:
    return a.get("target_action") == "rename"


def _is_owner(a: dict[str, str]) -> bool:
    return a.get("target_action") == "owner"


def _is_version_options(a: dict[str, str]) -> bool:
    return a.get("target_action") == "version_options"


def _server_missing(a: dict[str, str]) -> bool:
    return a.get("server_state") == "non_existent"


def _server_name(a: dict[str, str], p: str) -> str:
    """The server identifier used inside ALTER SERVER and fixtures."""

    shape = a.get("server_name_shape", "simple_name")
    if shape == "quoted_name":
        return f'"{p}Mixed Server"'
    return f"{p}srv"


def _server_name_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    shape = a.get("server_name_shape", "simple_name")
    if shape == "quoted_name":
        return f"{p}Mixed Server"
    return f"{p}srv"


def _new_name(a: dict[str, str], p: str) -> str:
    """The new name in RENAME TO."""

    shape = a.get("new_name_shape", "simple_name")
    if shape == "existing_name_conflict":
        return f"{p}conflictsrv"
    if shape == "quoted_name":
        return f'"{p}Mixed New"'
    return f"{p}newsrv"


def _new_name_literal(a: dict[str, str], p: str) -> str:
    shape = a.get("new_name_shape", "simple_name")
    if shape == "existing_name_conflict":
        return f"{p}conflictsrv"
    if shape == "quoted_name":
        return f"{p}Mixed New"
    return f"{p}newsrv"


def _owner_target(a: dict[str, str], p: str) -> str:
    """The owner target token in OWNER TO."""

    oc = a.get("owner_to_shape", "explicit_role_name")
    if oc == "current_role_keyword":
        return "CURRENT_ROLE"
    if oc == "current_user_keyword":
        return "CURRENT_USER"
    if oc == "session_user_keyword":
        return "SESSION_USER"
    now = a.get("new_owner_shape", "existing_role")
    if now == "nonexistent_role":
        return f"{p}no_such_role"
    return f"{p}newowner"


def _owner_role_needs_create(a: dict[str, str]) -> bool:
    return (
        a.get("owner_to_shape") == "explicit_role_name"
        and a.get("new_owner_shape") == "existing_role"
    )


def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target ALTER SERVER runs."""

    level = a.get("executor_privilege", "superuser")
    if level == "owner_with_usage_on_fdw":
        return f"{p}srvowner"
    if level == "non_owner_no_privilege":
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    """Roles to tear down, members/grantees before the owner role."""

    roles: list[str] = []
    level = a.get("executor_privilege", "superuser")
    if _is_owner(a) and _owner_role_needs_create(a):
        roles.append(f"{p}newowner")
    if level == "non_owner_no_privilege":
        roles.append(f"{p}actor")
    if level == "owner_with_usage_on_fdw":
        roles.append(f"{p}srvowner")
    return tuple(roles)


def _validator_function(a: dict[str, str], p: str) -> str:
    """A plpgsql FDW validator that rejects the ``invalid_option`` key."""

    return (
        f"CREATE OR REPLACE FUNCTION {p}validator(text[], oid) RETURNS "
        f"void LANGUAGE plpgsql AS $body$ DECLARE item text; BEGIN "
        f"FOREACH item IN ARRAY $1 LOOP IF "
        f"pg_catalog.split_part(item, '=', 1) = 'invalid_option' THEN "
        f"RAISE EXCEPTION 'invalid option %', item "
        f"USING ERRCODE='HV00D'; END IF; END LOOP; END $body$;"
    )


def _server_options_fixture(a: dict[str, str]) -> list[tuple[str, str]]:
    """Pre-existing server options required by SET / DROP / combined ops."""

    op = a.get("options_operation", "omitted_no_options")
    if op in ("set_option", "drop_option"):
        return [("opt1", "init1")]
    if op == "add_and_set_combined":
        return [("opt2", "init2"), ("opt3", "init3")]
    return []


def _alter_options_clause(a: dict[str, str], p: str) -> str:
    """The OPTIONS (...) clause for the version_options branch."""

    op = a.get("options_operation", "omitted_no_options")
    invalid = (
        a.get("option_key_value_shape")
        == "invalid_option_rejected_by_validator"
    )
    if op == "omitted_no_options":
        return ""
    if op == "add_option":
        key = "invalid_option" if invalid else "opt1"
        return f" OPTIONS (ADD {key} 'val1')"
    if op == "set_option":
        key = "invalid_option" if invalid else "opt1"
        return f" OPTIONS (SET {key} 'val2')"
    if op == "drop_option":
        key = "invalid_option" if invalid else "opt1"
        return f" OPTIONS (DROP {key})"
    if op == "add_and_set_combined":
        if invalid:
            return (
                " OPTIONS (ADD invalid_option 'x', SET opt2 'val2', "
                "DROP opt3)"
            )
        return (
            " OPTIONS (ADD opt1 'val1', SET opt2 'val2', DROP opt3)"
        )
    return ""


def _version_clause(a: dict[str, str]) -> str:
    """The VERSION clause for the version_options branch."""

    vc = a.get("version_clause", "omitted")
    if vc == "set_new_version":
        return " VERSION '1.0'"
    if vc == "set_version_null":
        return " VERSION NULL"
    return ""


def _probe_select(
    case: AlterServerFactorCase, a: dict[str, str], p: str
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only error_assertion."""

    mode = a.get("verification_mode", "pg_foreign_server_catalog")
    srv = _server_name_literal(a, p)
    missing = _server_missing(a)

    if _is_rename(a):
        new = _new_name_literal(a, p)
        if case.outcome == "success":
            check, present = new, True
        elif missing:
            check, present = srv, False
        else:
            check, present = srv, True
    else:
        check = srv
        present = not missing

    cmp_op = ">" if present else "="
    if mode == "error_assertion":
        return None
    if mode == "pg_foreign_server_options_query":
        if (
            not missing
            and case.outcome == "success"
            and _is_version_options(a)
        ):
            return (
                f"SELECT count(*) > 0 AS server_has_options "
                f"FROM pg_catalog.pg_foreign_server "
                f"WHERE srvname = '{check}' AND srvoptions IS NOT NULL "
                f"ORDER BY count(*);"
            )
        return (
            f"SELECT count(*) {cmp_op} 0 AS server_state "
            f"FROM pg_catalog.pg_foreign_server "
            f"WHERE srvname = '{check}' "
            f"ORDER BY count(*);"
        )
    return (
        f"SELECT count(*) {cmp_op} 0 AS server_state "
        f"FROM pg_catalog.pg_foreign_server "
        f"WHERE srvname = '{check}' "
        f"ORDER BY count(*);"
    )


def _tables_to_drop(case: AlterServerFactorCase) -> list[str]:
    """Fixture tables the case CREATEs, as the bookend gate must drop them.

    ALTER SERVER never creates a ``pg_class`` table: the only fixtures are
    foreign-data wrappers, foreign servers, user mappings, validator
    functions and roles (none of which are ``CREATE TABLE`` targets the
    bookend gate tracks).  The list is therefore always empty and no
    ``DROP TABLE`` bookend is emitted; the scaffolding is kept for
    structural parity with ``alter_schema_factor_render``.
    """

    return []


def _server_fixture_lines(
    a: dict[str, str], p: str, srv: str, new: str
) -> tuple[list[str], str]:
    """Build the FDW + server (+ conflict) fixture lines and locus."""

    lines: list[str] = []
    locus = "fixture.server"
    lines.append(_validator_function(a, p))
    lines.append(
        f"CREATE FOREIGN DATA WRAPPER {p}fdw "
        f"VALIDATOR {p}validator;"
    )
    opts = _server_options_fixture(a)
    opts_clause = ""
    if opts:
        rendered = ", ".join(f"{k} '{v}'" for k, v in opts)
        opts_clause = f" OPTIONS ({rendered})"
    lines.append(
        f"CREATE SERVER {srv} FOREIGN DATA WRAPPER {p}fdw{opts_clause};"
    )
    if _is_rename(a) and a.get("new_name_shape") == "existing_name_conflict":
        lines.append(
            f"CREATE SERVER {new} FOREIGN DATA WRAPPER {p}fdw;"
        )
        locus = "fixture.rename_conflict"
    return lines, locus


def _cleanup_drops(
    a: dict[str, str],
    p: str,
    srv: str,
    new: str,
    roles: tuple[str, ...],
) -> list[str]:
    """Comprehensive teardown ordered by cleanup_mode (all IF EXISTS)."""

    mode = a.get("cleanup_mode", "drop_server")
    missing = _server_missing(a)
    has_user_mapping = (
        a.get("user_mapping_dependency") == "has_user_mapping"
    )
    has_fdw = not missing
    lines: list[str] = []

    if (
        mode == "drop_user_mapping_then_drop_server"
        and has_user_mapping
        and not missing
    ):
        lines.append(
            f"DROP USER MAPPING IF EXISTS FOR CURRENT_USER SERVER {srv};"
        )
    if mode == "drop_fdw_then_drop_server" and has_fdw:
        lines.append(
            f"DROP FOREIGN DATA WRAPPER IF EXISTS {p}fdw CASCADE;"
        )
    lines.append(f"DROP SERVER IF EXISTS {srv} CASCADE;")
    if _is_rename(a):
        lines.append(f"DROP SERVER IF EXISTS {new} CASCADE;")
    if mode != "drop_fdw_then_drop_server" and has_fdw:
        lines.append(
            f"DROP FOREIGN DATA WRAPPER IF EXISTS {p}fdw CASCADE;"
        )
    if (
        has_user_mapping
        and not missing
        and mode != "drop_user_mapping_then_drop_server"
    ):
        lines.append(
            f"DROP USER MAPPING IF EXISTS FOR CURRENT_USER SERVER {srv};"
        )
    if has_fdw:
        lines.append(
            f"DROP FUNCTION IF EXISTS {p}validator(text[], oid) CASCADE;"
        )
    for role in roles:
        lines.append(f"DROP OWNED BY {role} CASCADE;")
        lines.append(f"DROP ROLE IF EXISTS {role};")
    return lines


def _resolve_case(case: AlterServerFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    rename = _is_rename(a)
    owner = _is_owner(a)
    missing = _server_missing(a)

    setup: list[str] = []
    locus = "target.alter_server"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    srv = _server_name(a, p)
    new = _new_name(a, p)
    owner_target = _owner_target(a, p)

    # --- role fixtures -----------------------------------------------
    if effective == f"{p}srvowner":
        setup.append(f"CREATE ROLE {p}srvowner LOGIN;")
        if owner and _owner_role_needs_create(a):
            setup.append(f"CREATE ROLE {p}newowner LOGIN;")
        locus = "fixture.privilege_state"
    elif effective == f"{p}actor":
        setup.append(f"CREATE ROLE {p}srvowner LOGIN;")
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        if owner and _owner_role_needs_create(a):
            setup.append(f"CREATE ROLE {p}newowner LOGIN;")
        locus = "fixture.privilege_state"

    # --- the target server fixture -----------------------------------
    if not missing:
        srv_lines, srv_locus = _server_fixture_lines(a, p, srv, new)
        setup.extend(srv_lines)
        locus = srv_locus

        if effective in (f"{p}srvowner", f"{p}actor"):
            setup.append(f"ALTER SERVER {srv} OWNER TO {p}srvowner;")

        if a.get("user_mapping_dependency") == "has_user_mapping":
            setup.append(
                f"CREATE USER MAPPING FOR CURRENT_USER SERVER {srv} "
                f"OPTIONS (user 'tester');"
            )
            locus = "fixture.user_mapping"
    else:
        setup.append(
            "SELECT 1 AS target_server_intentionally_absent;"
        )
        locus = "fixture.server_missing"

    # --- arm the effective role --------------------------------------
    if effective:
        setup.append(f"SET ROLE {effective};")

    # --- the primary target statement --------------------------------
    if rename:
        target = f"ALTER SERVER {srv} RENAME TO {new};"
    elif owner:
        target = f"ALTER SERVER {srv} OWNER TO {owner_target};"
    else:
        target = (
            f"ALTER SERVER {srv}{_version_clause(a)}"
            f"{_alter_options_clause(a, p)};"
        )

    if case.kind == "RISK":
        setup.append("BEGIN;")
        locus = "target.transaction_boundary"

    # --- oracle / SQLSTATE assertion ----------------------------------
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
    server_drops = _cleanup_drops(a, p, srv, new, roles)
    tables = _tables_to_drop(case)

    pre_cleanup: list[str] = []
    if tables:
        pre_cleanup.append(
            f"DROP TABLE IF EXISTS {', '.join(tables)} CASCADE;"
        )
    pre_cleanup.extend(server_drops)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(server_drops)
    if tables:
        cleanup.append(
            f"DROP TABLE IF EXISTS {', '.join(tables)} CASCADE;"
        )
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


def resolve_alter_server_factor_witness(
    case: AlterServerFactorCase | AlterServerFactorExtensionCase,
    repository_root: Path,
) -> AlterServerFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return AlterServerFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_alter_server(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(re.findall(r"(?im)^\s*ALTER\s+SERVER\b", region))


def _header(case: AlterServerFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : ALTER SERVER {case.factor_key}="
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


def render_alter_server_factor_case(
    case: AlterServerFactorCase | AlterServerFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 ALTER SERVER。")
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
    case: AlterServerFactorCase | AlterServerFactorExtensionCase,
    out: Path,
) -> None:
    text = render_alter_server_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_alter_server_factor_programs(
    baseline_plan: AlterServerFactorLoopPlan,
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
    "AlterServerFactorRenderError",
    "AlterServerFactorWitness",
    "count_primary_alter_server",
    "generate_alter_server_factor_programs",
    "render_alter_server_factor_case",
    "resolve_alter_server_factor_witness",
]
