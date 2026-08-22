"""Render complete PostgreSQL 18.4 DROP ROLE factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_roles WHERE rolname = '...' ORDER BY count(*)``
never nests a ``FROM`` inside an ``EXISTS`` subquery, so
``audit_catalog_observability`` accepts it.  ``rolname`` is a real column of
both ``pg_roles`` and ``pg_authid``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .cleanup_bookend import DropSpec, build_cleanup, build_pre_cleanup
from .drop_role_factor_extension import (
    DropRoleFactorExtensionCase,
)
from .drop_role_factor_loop import (
    DropRoleFactorCase,
    DropRoleFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/role/drop_role.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/role/drop_role.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

# Primary (factor, value) pairs where the target role is intentionally absent,
# so the drop surfaces a not-found error (or a notice under IF EXISTS) and the
# oracle asserts absence.
_ABSENT_PRIMARIES = frozenset(
    {
        ("expected_status", "failure"),
        ("role_existence", "role_not_exists"),
        ("role_name_shape", "non_existing_name"),
        ("role_name_shape", "invalid_name"),
    }
)

# Role-name shapes that never receive a created role fixture.
_ABSENT_SHAPES = frozenset({"non_existing_name", "invalid_name"})

# For an extension SUCCESS case (no present failure pair) the synthetic
# primary must be a neutral success primary; the role always exists in
# extensions (role_existence held at role_exists unless crossed).
_BRANCH_NEUTRAL_SUCCESS = ("role_existence", "role_exists")


def _synthetic_case(
    ext: DropRoleFactorExtensionCase,
) -> DropRoleFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .drop_role_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropRoleFactorCase(
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
    case: DropRoleFactorCase | DropRoleFactorExtensionCase,
) -> DropRoleFactorCase:
    if isinstance(case, DropRoleFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropRoleFactorRenderError(ValueError):
    """Raised when a DROP ROLE case cannot be rendered."""


@dataclass(frozen=True)
class DropRoleFactorWitness:
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


def _baseline(case: DropRoleFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _role_target_name(a: dict[str, str], p: str) -> str:
    """The role name as written inside DROP ROLE (may be quoted)."""

    shape = a.get("role_name_shape", "simple_name")
    if shape == "quoted_name":
        return f'"{p}QuotedRole"'
    if shape == "reserved_word_name":
        return f'"{p}user"'
    if shape == "case_sensitive_name":
        return f'"{p}MixedCase"'
    if shape == "non_existing_name":
        return f"{p}nonexistent_role"
    if shape == "invalid_name":
        return f"{p}invalid.role"
    return f"{p}role"


def _role_probe_name(a: dict[str, str], p: str) -> str:
    """The bare role name (no quotes) for the catalog probe."""

    shape = a.get("role_name_shape", "simple_name")
    if shape == "quoted_name":
        return f"{p}QuotedRole"
    if shape == "reserved_word_name":
        return f"{p}user"
    if shape == "case_sensitive_name":
        return f"{p}MixedCase"
    if shape == "non_existing_name":
        return f"{p}nonexistent_role"
    if shape == "invalid_name":
        return f"{p}invalid.role"
    return f"{p}role"


def _secondary_role(p: str) -> str:
    return f"{p}role2"


def _secondary_nonexistent(p: str) -> str:
    return f"{p}nonexistent_role2"


def _fixture_kind(
    case: DropRoleFactorCase, a: dict[str, str]
) -> str:
    """Whether a target role fixture must be created."""

    if case.kind == "RISK":
        return "role"
    shape = a.get("role_name_shape", "simple_name")
    if shape in _ABSENT_SHAPES:
        return "none"
    if a.get("role_existence") == "role_not_exists":
        return "none"
    if a.get("expected_status") == "failure":
        return "none"
    if case.kind == "EXT":
        if a.get("role_existence") == "role_not_exists":
            return "none"
        if a.get("role_name_shape") in _ABSENT_SHAPES:
            return "none"
    return "role"


def _if_exists(a: dict[str, str]) -> str:
    branch = a.get("statement_branch", "branch_drop_role")
    if branch == "branch_drop_role_if_exists":
        return "IF EXISTS "
    if a.get("if_exists_clause") == "with_if_exists":
        return "IF EXISTS "
    return ""


def _effective_actor(
    case: DropRoleFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP ROLE runs ("" = superuser)."""

    if case.kind == "EXT":
        pc = a.get("privilege_context", "superuser")
        return f"{p}actor" if pc != "superuser" else ""
    if case.factor_key == "privilege_context":
        return f"{p}actor" if case.factor_value != "superuser" else ""
    if case.factor_key == "privilege_insufficient":
        return f"{p}actor" if case.factor_value != "sufficient_privilege" else ""
    return ""


def _actor_create_clause(pc: str, p: str) -> str:
    if pc == "createrole_with_admin":
        return f"CREATE ROLE {p}actor CREATEROLE;"
    return f"CREATE ROLE {p}actor;"


def _owned_kind(a: dict[str, str]) -> frozenset[str]:
    owned = a.get("owned_objects", "no_owned_objects")
    kinds: set[str] = set()
    if owned in ("owns_tables", "owns_multiple_objects"):
        kinds.add("table")
    if owned in ("owns_sequences", "owns_multiple_objects"):
        kinds.add("sequence")
    if owned in ("owns_views", "owns_multiple_objects"):
        kinds.add("view")
    if owned in ("owns_functions", "owns_multiple_objects"):
        kinds.add("function")
    return frozenset(kinds)


def _role_absent_after(
    case: DropRoleFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target role is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if _fixture_kind(case, a) == "none":
        return True
    if case.outcome == "success":
        return True
    return False


def _probe_select(
    case: DropRoleFactorCase, a: dict[str, str], p: str
) -> str:
    name = _role_probe_name(a, p)
    absent = _role_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "role_absent" if absent else "role_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_roles "
        f"WHERE rolname = '{name}' ORDER BY count(*) LIMIT 1;"
    )


def _target_roles(
    case: DropRoleFactorCase, a: dict[str, str], p: str
) -> tuple[str, ...]:
    """The role list as written inside DROP ROLE."""

    mt = a.get("multi_target", "single_target")
    primary = _role_target_name(a, p)
    if mt == "multi_target_all_exist":
        return (primary, _secondary_role(p))
    if mt == "multi_target_some_not_exist":
        return (primary, _secondary_nonexistent(p))
    return (primary,)


def _created_roles(
    case: DropRoleFactorCase, a: dict[str, str], p: str
) -> tuple[str, ...]:
    """Roles that receive a CREATE ROLE fixture (a subset of target list)."""

    if _fixture_kind(case, a) == "none":
        return ()
    mt = a.get("multi_target", "single_target")
    primary = _role_target_name(a, p)
    if mt == "multi_target_all_exist":
        return (primary, _secondary_role(p))
    return (primary,)


def _resolve_case(case: DropRoleFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    fixture = _fixture_kind(case, a)
    created = _created_roles(case, a, p)
    targets = _target_roles(case, a, p)
    primary_ref = targets[0]
    owned = _owned_kind(a)

    setup: list[str] = []
    locus = "target.role"

    # --- actor role fixture (CREATE only; SET ROLE deferred) -------------
    effective = _effective_actor(case, a, p)
    if effective:
        pc = a.get("privilege_context", "superuser")
        setup.append(_actor_create_clause(pc, p))
        locus = "fixture.privilege_state"

    # --- target role fixture (as superuser, before SET ROLE) -------------
    if fixture == "role":
        for role in created:
            setup.append(f"CREATE ROLE {role};")
        locus = "fixture.object_state"
    else:
        setup.append("SELECT 1 AS target_role_intentionally_absent;")
        locus = "fixture.object_state"

    # --- owned-object fixtures (as superuser, before SET ROLE) ------------
    if owned:
        owner = primary_ref
        if "table" in owned:
            setup.append(f"CREATE TABLE {p}t (c integer);")
            setup.append(f"ALTER TABLE {p}t OWNER TO {owner};")
        if "sequence" in owned:
            setup.append(f"CREATE SEQUENCE {p}seq;")
            setup.append(f"ALTER SEQUENCE {p}seq OWNER TO {owner};")
        if "view" in owned:
            setup.append(f"CREATE VIEW {p}v AS SELECT 1;")
            setup.append(f"ALTER VIEW {p}v OWNER TO {owner};")
        if "function" in owned:
            setup.append(
                f"CREATE FUNCTION {p}fn() RETURNS integer "
                "AS 'SELECT 1' LANGUAGE sql;"
            )
            setup.append(f"ALTER FUNCTION {p}fn() OWNER TO {owner};")
        locus = "fixture.dependency_state"

    # --- segment-merge boundary when a table is created (lesson 6) -------
    has_table = "table" in owned
    if has_table:
        setup.insert(0, "SELECT 1 AS setup_boundary;")

    # --- arm the non-superuser role (AFTER role/object creation) ----------
    if effective:
        setup.append(f"SET ROLE {p}actor;")

    if_exists = _if_exists(a)
    role_list = ", ".join(targets)
    target = f"DROP ROLE {if_exists}{role_list}"

    # RISK transaction wrapper around the target.
    if case.kind == "RISK":
        setup.append("BEGIN;")
        locus = "target.transaction_boundary"
    target += ";"

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

    # --- cleanup construction (shared idempotent bookends) -----------
    # Migrated to cleanup_bookend so every DROP carries IF EXISTS and
    # DROP OWNED BY is unreachable in pre-cleanup: on a fresh database the
    # role fixture is created by setup, so the role does not exist yet at
    # pre-cleanup time and DROP OWNED BY would crash (ON_ERROR_STOP=1)
    # before the target statement reaches execution.  Pre-cleanup drops
    # roles via DROP ROLE IF EXISTS only; the post-target cleanup runs
    # DROP OWNED BY then DROP ROLE IF EXISTS once setup has created the
    # role.  The DROP TABLE IF EXISTS anchor is first in pre-cleanup and
    # last in cleanup, satisfying the table-bookend gate.  Only roles that
    # setup actually creates (the target-role fixtures plus the actor) are
    # passed to the helper so DROP OWNED BY is never emitted for a role
    # that cannot exist; nonexistent target roles are a no-op and are
    # intentionally omitted.
    specs: list[DropSpec] = []
    if "function" in owned:
        specs.append(DropSpec("FUNCTION", f"{p}fn", args="()"))
    if "view" in owned:
        specs.append(DropSpec("VIEW", f"{p}v"))
    if "sequence" in owned:
        specs.append(DropSpec("SEQUENCE", f"{p}seq"))
    table_names = [f"{p}t"] if has_table else []
    cleanup_roles = list(created)
    if effective:
        cleanup_roles.append(effective)
    pre_bookend = build_pre_cleanup(
        tables=table_names,
        specs=tuple(specs),
        roles=cleanup_roles,
    )
    cln_bookend = build_cleanup(
        tables=table_names,
        specs=tuple(specs),
        roles=cleanup_roles,
        drop_owned=bool(cleanup_roles),
        reset_role=bool(effective),
    )
    pre_cleanup = list(pre_bookend.statements)
    cleanup = list(cln_bookend.statements)

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


def resolve_drop_role_factor_witness(
    case: DropRoleFactorCase | DropRoleFactorExtensionCase,
    repository_root: Path,
) -> DropRoleFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropRoleFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_role(sql: str) -> int:
    """Count the single credited DROP ROLE inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*DROP\s+ROLE\b", region)
    )


def _header(case: DropRoleFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP ROLE {case.factor_key}={case.factor_value}",
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


def render_drop_role_factor_case(
    case: DropRoleFactorCase | DropRoleFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP ROLE regress program."""

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地角色和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP ROLE。")
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


def generate_drop_role_factor_programs(
    baseline_plan: DropRoleFactorLoopPlan,
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
    case: DropRoleFactorCase | DropRoleFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_role_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropRoleFactorRenderError",
    "DropRoleFactorWitness",
    "count_primary_drop_role",
    "generate_drop_role_factor_programs",
    "render_drop_role_factor_case",
    "resolve_drop_role_factor_witness",
]
