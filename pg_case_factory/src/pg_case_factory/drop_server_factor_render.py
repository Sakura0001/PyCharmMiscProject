"""Render complete PostgreSQL 18.4 DROP SERVER factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.
The file is assembled from a single :func:`_resolve_case` plan so that the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_foreign_server ...
ORDER BY count(*)`` never nests a ``FROM`` inside an ``EXISTS`` subquery, so
``audit_catalog_observability`` accepts it.  The name column targeted is the
real ``pg_foreign_server.srvname`` column (PG18 catalog).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .drop_server_factor_extension import (
    DropServerFactorExtensionCase,
)
from .drop_server_factor_loop import (
    DropServerFactorCase,
    DropServerFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/server/"
    "drop_server.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/server/"
    "drop_server.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

# Primary (factor, value) pairs where the target server is intentionally
# absent, so the drop surfaces a not-found error (or a notice under IF EXISTS)
# and the oracle asserts absence.
_ABSENT_PRIMARIES = frozenset(
    {
        ("expected_status", "failure"),
        ("server_existence", "server_not_exists"),
        ("server_name_shape", "non_existing_name"),
    }
)

# For an extension SUCCESS case (no present failure pair) the synthetic
# primary must be a neutral success primary whose helpers fall through to the
# assignment; the server always exists in extensions when the failure pair is
# None (object_state held at exists).
_BRANCH_NEUTRAL_SUCCESS = ("server_existence", "server_exists")

_QUOTE_SHAPES = frozenset({"quoted_name", "reserved_word_name"})
_RESERVED_WORDS = ("user", "order")


def _synthetic_case(
    ext: DropServerFactorExtensionCase,
) -> DropServerFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .drop_server_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropServerFactorCase(
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
    case: DropServerFactorCase | DropServerFactorExtensionCase,
) -> DropServerFactorCase:
    if isinstance(case, DropServerFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropServerFactorRenderError(ValueError):
    """Raised when a DROP SERVER case cannot be rendered."""


@dataclass(frozen=True)
class DropServerFactorWitness:
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


def _baseline(case: DropServerFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _ref(name: str, shape: str) -> str:
    """The server name as it appears inside CREATE/DROP SERVER."""

    if shape in _QUOTE_SHAPES:
        return f'"{name}"'
    return name


def _shape_base_names(
    case: DropServerFactorCase, a: dict[str, str], p: str
) -> tuple[list[str], list[str]]:
    """Return (created_names, drop_names) — dequoted server names."""

    shape = a.get("server_name_shape", "simple_name")
    multi = a.get("multi_target", "single_target")
    exists = a.get("server_existence") == "server_exists"

    if shape == "non_existing_name":
        if multi == "single_target":
            return [], [f"{p}noexist"]
        return [], [f"{p}noexist1", f"{p}noexist2"]

    if shape == "reserved_word_name":
        single = _RESERVED_WORDS[0]
        pair = list(_RESERVED_WORDS[:2])
    elif shape == "quoted_name":
        single = f"{p}Qsrv"
        pair = [f"{p}Qsrv1", f"{p}Qsrv2"]
    else:  # simple_name
        single = f"{p}srv"
        pair = [f"{p}srv1", f"{p}srv2"]

    if not exists:
        if multi == "single_target":
            return [], [single]
        return [], pair

    if multi == "single_target":
        return [single], [single]
    if multi == "multi_target_all_exist":
        return pair, pair
    # multi_target_some_not_exist: only the first server exists.
    return [pair[0]], pair


def _fdw_name(p: str) -> str:
    return f"{p}fdw"


def _if_exists_present(
    case: DropServerFactorCase, a: dict[str, str]
) -> bool:
    return a.get("if_exists_clause") == "with_if_exists"


def _cascade_clause(a: dict[str, str]) -> str:
    cascade = a.get("cascade_restrict_clause", "no_clause_default_restrict")
    if cascade == "cascade":
        return "CASCADE"
    if cascade == "restrict":
        return "RESTRICT"
    return ""  # no_clause_default_restrict: RESTRICT is the default


def _effective_role(
    case: DropServerFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP SERVER runs."""

    if case.kind == "EXT":
        level = a.get("privilege_context", "superuser")
        return f"{p}actor" if level == "non_owner_no_privilege" else ""
    if case.factor_key == "privilege_context":
        return (
            f"{p}actor"
            if case.factor_value == "non_owner_no_privilege"
            else ""
        )
    if case.factor_key == "executor_privilege":
        return (
            f"{p}actor"
            if case.factor_value == "non_owner_no_privilege"
            else ""
        )
    return ""


def _needs_user_mapping(
    case: DropServerFactorCase, a: dict[str, str]
) -> bool:
    """Whether a user mapping fixture must be created."""

    if case.kind == "EXT":
        return a.get("user_mapping_dependency") == "has_user_mapping_dependency"
    if (
        case.factor_key,
        case.factor_value,
    ) in {
        ("user_mapping_dependency", "has_user_mapping_dependency"),
        ("dependent_user_mapping", "restrict_with_user_mapping_fails"),
        ("dependent_user_mapping", "cascade_with_user_mapping_succeeds"),
    }:
        return True
    return a.get("user_mapping_dependency") == "has_user_mapping_dependency"


def _server_absent_after(
    case: DropServerFactorCase,
    a: dict[str, str],
    p: str,
) -> bool:
    """Whether the target server is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    created, _ = _shape_base_names(case, a, p)
    if not created:
        return True
    if case.outcome == "success":
        return True
    return False


def _probe_select(
    case: DropServerFactorCase, a: dict[str, str], p: str
) -> str:
    _, drop = _shape_base_names(case, a, p)
    absent = _server_absent_after(case, a, p)
    comparator = "= 0" if absent else "> 0"
    alias = "server_absent" if absent else "server_present"
    if len(drop) == 1:
        where = f"srvname = '{drop[0]}'"
    else:
        where = "srvname IN (" + ", ".join(f"'{n}'" for n in drop) + ")"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_foreign_server "
        f"WHERE {where} ORDER BY count(*) LIMIT 1;"
    )


def _role_names(
    case: DropServerFactorCase, p: str, effective: str
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}actor":
        roles.append(f"{p}actor")
    return tuple(roles)


def _resolve_case(case: DropServerFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    shape = a.get("server_name_shape", "simple_name")
    created, drop = _shape_base_names(case, a, p)
    fdw = _fdw_name(p)
    needs_um = _needs_user_mapping(case, a)
    effective = _effective_role(case, a, p)

    setup: list[str] = []
    locus = "target.foreign_server"

    # --- role fixtures (CREATE only; SET ROLE deferred to after the server
    # fixture so they run as the superuser) ---
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- FDW fixture (always; required to host the foreign server) ---
    setup.append(f"CREATE FOREIGN DATA WRAPPER {fdw};")
    locus = "fixture.foreign_data_wrapper"

    # --- the target server fixtures (as superuser, before SET ROLE) -------
    if created:
        for name in created:
            setup.append(
                f"CREATE SERVER {_ref(name, shape)} "
                f"FOREIGN DATA WRAPPER {fdw};"
            )
        locus = "fixture.object_state"
    else:
        setup.append(
            "SELECT 1 AS target_server_intentionally_absent;"
        )
        locus = "fixture.object_state"

    # --- user mapping fixture (as superuser, only when a server exists) ----
    if needs_um and created:
        setup.append(
            f"CREATE USER MAPPING FOR public SERVER {_ref(created[0], shape)};"
        )
        locus = "fixture.dependency_state"

    # --- arm the non-superuser role (AFTER server creation) ---------------
    if effective:
        setup.append(f"SET ROLE {p}actor;")
    if_exists = "IF EXISTS " if _if_exists_present(case, a) else ""
    cascade = _cascade_clause(a)
    refs = ", ".join(_ref(name, shape) for name in drop)
    target = f"DROP SERVER {if_exists}{refs}"
    if cascade:
        target += f" {cascade}"
    target += ";"

    # RISK transaction wrapper around the target.
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
    assert_lines.append(_probe_select(case, a, p))

    # --- cleanup construction -------------------------------------------
    um_drops = (
        [
            f"DROP USER MAPPING IF EXISTS FOR public SERVER {_ref(n, shape)};"
            for n in created
        ]
        if (needs_um and created)
        else []
    )
    server_drops = [
        f"DROP SERVER IF EXISTS {_ref(n, shape)} CASCADE;" for n in drop
    ]
    fdw_drop = f"DROP FOREIGN DATA WRAPPER IF EXISTS {fdw} CASCADE;"
    roles = _role_names(case, p, effective)
    role_drops = [
        statement
        for role in roles
        for statement in (
            f"DROP OWNED BY {role};",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    # Pre-cleanup: user mappings, servers, FDW, roles.
    pre_cleanup: list[str] = []
    pre_cleanup.extend(um_drops)
    pre_cleanup.extend(server_drops)
    pre_cleanup.append(fdw_drop)
    pre_cleanup.extend(role_drops)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # Cleanup: RESET ROLE, then user mappings, servers, FDW, roles.
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(um_drops)
    cleanup.extend(server_drops)
    cleanup.append(fdw_drop)
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


def resolve_drop_server_factor_witness(
    case: DropServerFactorCase | DropServerFactorExtensionCase,
    repository_root: Path,
) -> DropServerFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropServerFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_server(sql: str) -> int:
    """Count the single credited DROP SERVER inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*DROP\s+SERVER\b", region)
    )


def _header(case: DropServerFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP SERVER {case.factor_key}={case.factor_value}",
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


def render_drop_server_factor_case(
    case: DropServerFactorCase | DropServerFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP SERVER regress program."""

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地外部服务器和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP SERVER。")
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
    if not text.endswith(";"):
        text += ";"
    return text + "\n"


def generate_drop_server_factor_programs(
    baseline_plan: DropServerFactorLoopPlan,
    extension_plan: object,
    out_dir: Path,
) -> int:
    """Write every baseline + extension program; return the file count."""

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


def _write_program(
    case: DropServerFactorCase | DropServerFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_server_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropServerFactorRenderError",
    "DropServerFactorWitness",
    "count_primary_drop_server",
    "generate_drop_server_factor_programs",
    "render_drop_server_factor_case",
    "resolve_drop_server_factor_witness",
]
