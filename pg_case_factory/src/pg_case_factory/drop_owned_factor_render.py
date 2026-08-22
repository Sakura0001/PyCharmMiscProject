"""Render complete PostgreSQL 18.4 DROP OWNED factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.
The file is assembled from a single :func:`_resolve_case` plan so that the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_class ... ORDER BY count(*)``
never nests a ``FROM`` inside an ``EXISTS`` subquery, so
``audit_catalog_observability`` accepts it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .cleanup_bookend import DropSpec, build_cleanup, build_pre_cleanup
from .drop_owned_factor_extension import (
    DropOwnedFactorExtensionCase,
)
from .drop_owned_factor_loop import (
    DropOwnedFactorCase,
    DropOwnedFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/ownership/"
    "drop_owned.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/ownership/"
    "drop_owned.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

# Primary (factor, value) pairs where the target role is intentionally
# absent, so the drop surfaces a not-found error and the oracle asserts
# absence.
_ABSENT_PRIMARIES = frozenset(
    {
        ("role_existence", "role_not_exists"),
        ("nonexistent_role", "role_does_not_exist"),
        ("role_name_shape", "non_existing_name"),
        ("expected_status", "failure"),
    }
)

# Baseline primaries that imply a dependent object fixture must be created.
_DEPENDENCY_PRIMARIES = frozenset(
    {
        ("dependent_objects", "has_dependent_objects_cascade_succeeds"),
        ("dependent_objects", "has_dependent_objects_restrict_fails"),
    }
)

# For an extension SUCCESS case (no present failure pair) the synthetic
# primary must be a neutral success primary whose helpers fall through to the
# assignment; the role always exists in extensions (role_existence held at
# role_exists).
_BRANCH_NEUTRAL_SUCCESS = ("owned_objects_state", "owns_tables")


def _synthetic_case(
    ext: DropOwnedFactorExtensionCase,
) -> DropOwnedFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .drop_owned_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropOwnedFactorCase(
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
    case: DropOwnedFactorCase | DropOwnedFactorExtensionCase,
) -> DropOwnedFactorCase:
    if isinstance(case, DropOwnedFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropOwnedFactorRenderError(ValueError):
    """Raised when a DROP OWNED case cannot be rendered."""


@dataclass(frozen=True)
class DropOwnedFactorWitness:
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


def _baseline(case: DropOwnedFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _role_ref(case: DropOwnedFactorCase, a: dict[str, str], p: str) -> str:
    """The role reference as it appears inside DROP OWNED BY."""

    shape = a.get("role_shape", "explicit_role_name")
    if shape == "current_role_keyword":
        return "CURRENT_ROLE"
    if shape == "current_user_keyword":
        return "CURRENT_USER"
    if shape == "session_user_keyword":
        return "SESSION_USER"
    name_shape = a.get("role_name_shape", "simple_name")
    if name_shape == "quoted_name":
        return f'"{p}Quoted"'
    if name_shape == "reserved_word_name":
        return '"user"'
    if name_shape == "case_sensitive_name":
        return f'"{p}Case"'
    if name_shape == "non_existing_name":
        return f"{p}nonexistent"
    return f"{p}actor"


def _fixture_role_name(a: dict[str, str], p: str) -> str:
    """The role name for CREATE ROLE (always {p}actor for keyword shapes)."""

    shape = a.get("role_shape", "explicit_role_name")
    if shape != "explicit_role_name":
        return f"{p}actor"
    name_shape = a.get("role_name_shape", "simple_name")
    if name_shape == "quoted_name":
        return f'"{p}Quoted"'
    if name_shape == "reserved_word_name":
        return '"user"'
    if name_shape == "case_sensitive_name":
        return f'"{p}Case"'
    if name_shape == "non_existing_name":
        return f"{p}nonexistent"
    return f"{p}actor"


def _fixture_kind(
    case: DropOwnedFactorCase, a: dict[str, str]
) -> str:
    """Whether a role fixture must be created."""

    if case.kind == "RISK":
        return "role_with_table"
    if (case.factor_key, case.factor_value) in _ABSENT_PRIMARIES:
        return "none"
    if case.kind == "EXT":
        if a.get("role_existence") == "role_not_exists":
            return "none"
        if a.get("role_name_shape") == "non_existing_name":
            return "none"
    return "role_with_table"


def _needs_table(
    case: DropOwnedFactorCase, a: dict[str, str]
) -> bool:
    """Whether a table fixture must be created."""

    if case.kind == "RISK":
        return True
    if _fixture_kind(case, a) == "none":
        return False
    if case.kind == "EXT":
        return True
    state = a.get("owned_objects_state", "owns_no_objects")
    deps = a.get("dependent_objects", "no_dependent_objects")
    if state in ("owns_tables", "owns_multiple_objects"):
        return True
    if deps in (
        "has_dependent_objects_cascade_succeeds",
        "has_dependent_objects_restrict_fails",
    ):
        return True
    return False


def _needs_dependent(
    case: DropOwnedFactorCase, a: dict[str, str]
) -> bool:
    """Whether a dependent view fixture must be created."""

    if case.kind == "EXT":
        return a.get("dependent_objects") in (
            "has_dependent_objects_cascade_succeeds",
            "has_dependent_objects_restrict_fails",
        )
    if (case.factor_key, case.factor_value) in _DEPENDENCY_PRIMARIES:
        return True
    return a.get("dependent_objects") in (
        "has_dependent_objects_cascade_succeeds",
        "has_dependent_objects_restrict_fails",
    )


def _needs_second_object(
    case: DropOwnedFactorCase, a: dict[str, str]
) -> bool:
    """Whether a second owned object (view) must be created."""

    if _fixture_kind(case, a) == "none":
        return False
    if case.kind == "EXT":
        return a.get("owned_objects_state") == "owns_multiple_objects"
    return a.get("owned_objects_state") == "owns_multiple_objects"


def _cascade_clause(a: dict[str, str]) -> str:
    cascade = a.get("cascade_restrict_clause", "no_clause_default_restrict")
    if cascade == "cascade":
        return "CASCADE"
    if cascade == "restrict":
        return "RESTRICT"
    return ""


def _effective_role(
    case: DropOwnedFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP OWNED runs."""

    if case.kind == "EXT":
        priv = a.get("executor_privilege", "superuser")
        return f"{p}executor" if priv == "normal_user_no_privilege" else ""
    if case.factor_key == "executor_privilege":
        return (
            f"{p}executor"
            if case.factor_value == "normal_user_no_privilege"
            else ""
        )
    if case.factor_key == "privilege_insufficient":
        return (
            f"{p}executor"
            if case.factor_value in (
                "non_superuser_dropping_other_role_objects",
                "no_createrole_privilege",
            )
            else ""
        )
    return ""


def _needs_role_switch(
    case: DropOwnedFactorCase, a: dict[str, str], effective: str
) -> bool:
    """Whether SET ROLE is needed (for keyword shapes or privilege tests)."""

    if effective:
        return True
    shape = a.get("role_shape", "explicit_role_name")
    if shape != "explicit_role_name" and case.kind != "RISK":
        if _fixture_kind(case, a) != "none":
            return True
    return False


def _objects_absent_after(
    case: DropOwnedFactorCase, a: dict[str, str]
) -> bool:
    """Whether the owned objects are absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if _fixture_kind(case, a) == "none":
        return True
    if case.outcome == "success":
        return True
    return False


def _probe_select(
    case: DropOwnedFactorCase, a: dict[str, str], p: str
) -> str:
    vm = a.get("verification_mode", "pg_class_catalog_query")
    absent = _objects_absent_after(case, a)
    if vm == "error_assertion":
        return "SELECT 1 AS error_assertion_oracle;"
    if vm == "pg_roles_catalog_query":
        role_exists = _fixture_kind(case, a) != "none"
        if role_exists:
            comparator = "> 0"
            alias = "role_present"
        else:
            comparator = "= 0"
            alias = "role_absent"
        return (
            f"SELECT count(*) {comparator} AS {alias} "
            "FROM pg_catalog.pg_roles "
            f"WHERE rolname = '{p}actor' ORDER BY count(*) LIMIT 1;"
        )
    comparator = "= 0" if absent else "> 0"
    alias = "objects_absent" if absent else "objects_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_class "
        f"WHERE relname = '{p}t' ORDER BY count(*) LIMIT 1;"
    )


def _role_names(
    case: DropOwnedFactorCase, p: str, effective: str
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}executor":
        roles.append(f"{p}executor")
    return tuple(roles)


def _resolve_case(case: DropOwnedFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    fixture_kind = _fixture_kind(case, a)
    role_ref = _role_ref(case, a, p)
    fixture_role = _fixture_role_name(a, p)
    needs_table = _needs_table(case, a)
    needs_dep = _needs_dependent(case, a)
    needs_second = _needs_second_object(case, a)
    multi = a.get("multi_role", "single_role")

    setup: list[str] = []
    locus = "target.drop_owned"

    # --- role fixture (CREATE only; SET ROLE deferred) ----------------
    effective = _effective_role(case, a, p)
    if fixture_kind != "none":
        setup.append(f"CREATE ROLE {fixture_role} LOGIN;")
        if multi == "multiple_roles":
            setup.append(f"CREATE ROLE {p}actor2 LOGIN;")
        locus = "fixture.role_state"

    # --- table fixture (as superuser, before SET ROLE) -----------------
    if needs_table:
        setup.append(f"CREATE TABLE {p}t (c integer);")
        setup.append(f"ALTER TABLE {p}t OWNER TO {fixture_role};")
        locus = "fixture.owned_objects_state"

    # --- dependent view fixture (as superuser, before SET ROLE) -------
    if needs_dep:
        setup.append(f"CREATE VIEW {p}v AS SELECT * FROM {p}t;")
        locus = "fixture.dependency_state"

    # --- second owned object (for owns_multiple_objects) -------------
    if needs_second:
        setup.append(f"CREATE VIEW {p}v2 AS SELECT * FROM {p}t;")
        setup.append(f"ALTER VIEW {p}v2 OWNER TO {fixture_role};")

    # --- arm the executor role (AFTER fixture creation) --------------
    if effective:
        setup.append(f"CREATE ROLE {p}executor LOGIN NOSUPERUSER;")
        setup.append(f"SET ROLE {p}executor;")
    elif _needs_role_switch(case, a, effective):
        setup.append(f"SET ROLE {fixture_role};")

    if_exists = ""  # DROP OWNED has no IF EXISTS clause
    cascade = _cascade_clause(a)
    target = f"DROP OWNED BY {role_ref}"
    if multi == "multiple_roles":
        target += f", {p}actor2"
    if cascade:
        target += f" {cascade}"
    target += ";"

    # RISK transaction wrapper around the target.
    if case.kind == "RISK":
        setup.append("BEGIN;")
        locus = "target.transaction_boundary"

    # --- oracle / SQLSTATE assertion ------------------------------------
    assert_lines: list[str] = []
    if effective or _needs_role_switch(case, a, effective):
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
    # DROP OWNED BY is unreachable in pre-cleanup: the fixture role is
    # created by setup, so on a fresh database the role does not exist yet
    # at pre-cleanup time and DROP OWNED BY would crash (ON_ERROR_STOP=1)
    # before the target statement reaches execution. Pre-cleanup drops
    # roles via DROP ROLE IF EXISTS only; the post-target cleanup runs
    # DROP OWNED BY then DROP ROLE IF EXISTS once setup has created the
    # role. The DROP TABLE IF EXISTS anchor is first in pre-cleanup and
    # last in cleanup, satisfying the table-bookend gate.
    specs: list[DropSpec] = []
    if needs_dep:
        specs.append(DropSpec("VIEW", f"{p}v"))
    if needs_second:
        specs.append(DropSpec("VIEW", f"{p}v2"))
    table_names = [f"{p}t"] if needs_table else []
    roles = _role_names(case, p, effective)
    role_list = list(roles)
    if fixture_kind != "none":
        role_list.append(fixture_role)
        if multi == "multiple_roles":
            role_list.append(f"{p}actor2")
    pre_bookend = build_pre_cleanup(
        tables=table_names,
        specs=tuple(specs),
        roles=role_list,
    )
    cln_bookend = build_cleanup(
        tables=table_names,
        specs=tuple(specs),
        roles=role_list,
        drop_owned=bool(role_list),
        reset_role=bool(effective) or _needs_role_switch(case, a, effective),
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


def resolve_drop_owned_factor_witness(
    case: DropOwnedFactorCase | DropOwnedFactorExtensionCase,
    repository_root: Path,
) -> DropOwnedFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropOwnedFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_owned(sql: str) -> int:
    """Count the single credited DROP OWNED inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*DROP\s+OWNED\b", region)
    )


def _header(case: DropOwnedFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP OWNED {case.factor_key}={case.factor_value}",
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


def render_drop_owned_factor_case(
    case: DropOwnedFactorCase | DropOwnedFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP OWNED regress program."""

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
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP OWNED。")
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


def generate_drop_owned_factor_programs(
    baseline_plan: DropOwnedFactorLoopPlan,
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
    case: DropOwnedFactorCase | DropOwnedFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_owned_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropOwnedFactorRenderError",
    "DropOwnedFactorWitness",
    "count_primary_drop_owned",
    "generate_drop_owned_factor_programs",
    "render_drop_owned_factor_case",
    "resolve_drop_owned_factor_witness",
]
