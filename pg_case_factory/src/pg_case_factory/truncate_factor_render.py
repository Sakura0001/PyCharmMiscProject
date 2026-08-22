"""Render complete PostgreSQL 18.4 TRUNCATE factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

TRUNCATE is a DDL/DML table-truncation statement: the target is a
``pg_class`` relation of kind ``r`` (a base table).  All catalog
oracles schema-qualify ``pg_catalog.pg_class`` (exempt from the
file-prefix style gate via the ``pg_`` prefix) and carry a top-level
``ORDER BY``.  Success cases CREATE fixture TABLEs (the target
``{p}tbl`` plus an optional FK-referencing / second table ``{p}ref``),
so the bookend gate (DROP TABLE IF EXISTS first + last ``;``-stmt
covering every created table) applies.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .cleanup_bookend import DropSpec, build_cleanup, build_pre_cleanup
from .truncate_factor_extension import (
    TruncateFactorExtensionCase,
    _present_failure_pair,
)
from .truncate_factor_loop import (
    TruncateFactorCase,
    TruncateFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/table/"
    "truncate.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/table/"
    "truncate.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-21"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class TruncateFactorRenderError(ValueError):
    """Raised when a TRUNCATE case cannot be rendered."""


@dataclass(frozen=True)
class TruncateFactorWitness:
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
    ext: TruncateFactorExtensionCase,
) -> TruncateFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get("target_action", "truncate")
    return TruncateFactorCase(
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
    case: TruncateFactorCase | TruncateFactorExtensionCase,
) -> TruncateFactorCase:
    if isinstance(case, TruncateFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: TruncateFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _target_missing(a: dict[str, str]) -> bool:
    return a.get("object_state") == "table_does_not_exist"


def _table_name(p: str) -> str:
    return f"{p}tbl"


def _ref_table_name(p: str) -> str:
    return f"{p}ref"


def _missing_name(p: str) -> str:
    return f"{p}missing"


def _truncate_target(a: dict[str, str], p: str) -> str:
    """The TRUNCATE target identifier (with optional quoting/schema)."""

    shape = a.get("table_name_shape", "simple")
    if _target_missing(a):
        name = _missing_name(p)
    else:
        name = _table_name(p)
    if shape == "schema_qualified":
        return f"public.{name}"
    if shape == "quoted":
        return f'"{name}"'
    return name


def _ref_target(a: dict[str, str], p: str) -> str:
    """The second table identifier for multi_table=multiple."""

    shape = a.get("table_name_shape", "simple")
    name = _ref_table_name(p)
    if shape == "schema_qualified":
        return f"public.{name}"
    if shape == "quoted":
        return f'"{name}"'
    return name


def _target_relation_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    if _target_missing(a):
        return _missing_name(p)
    return _table_name(p)


def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target TRUNCATE runs."""

    pl = a.get("privilege_level", "owner")
    ip = a.get("insufficient_privilege", "none")
    if pl == "insufficient_privilege" or ip in (
        "no_truncate_privilege",
        "non_owner_truncate",
    ):
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    if _effective_role(a, p):
        roles.append(f"{p}actor")
    return tuple(roles)


def _build_target(a: dict[str, str], p: str) -> str:
    """The primary TRUNCATE statement."""

    parts: list[str] = ["TRUNCATE TABLE"]

    oc = a.get("only_clause", "without_only")
    if oc == "only":
        parts.append("ONLY")

    if _target_missing(a):
        parts.append(_truncate_target(a, p))
    elif a.get("multi_table") == "multiple":
        parts.append(
            f"{_truncate_target(a, p)}, {_ref_target(a, p)}"
        )
    else:
        parts.append(_truncate_target(a, p))

    io = a.get("identity_option", "none")
    if io == "continue_identity":
        parts.append("CONTINUE IDENTITY")
    elif io == "restart_identity":
        parts.append("RESTART IDENTITY")

    cr = a.get("cascade_restrict", "cascade")
    if cr == "cascade":
        parts.append("CASCADE")
    elif cr == "restrict":
        parts.append("RESTRICT")

    parts.append(";")
    return " ".join(parts)


def _probe_select(
    case: TruncateFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog/effect oracle, or None for sqlstate-only error_assertion."""

    mode = a.get("verification", "select_count_zero")
    if mode == "error_assertion":
        return None

    tbl = _table_name(p)
    rel_lit = _target_relation_literal(a, p)
    missing = _target_missing(a)

    if mode == "pg_class_relpages":
        cmp_op = ">" if not missing else "="
        return (
            f"SELECT count(*) {cmp_op} 0 AS relation_state "
            f"FROM pg_catalog.pg_class "
            f"WHERE relname = '{rel_lit}' AND relkind = 'r' "
            f"ORDER BY count(*);"
        )

    # select_count_zero and sequence_reset_check both probe
    # post-truncate state.
    if missing:
        return (
            f"SELECT count(*) = 0 AS effect_state "
            f"FROM pg_catalog.pg_class "
            f"WHERE relname = '{rel_lit}' AND relkind = 'r' "
            f"ORDER BY count(*);"
        )
    label = "effect_state"
    return (
        f"SELECT count(*) = 0 AS {label} "
        f"FROM {tbl} "
        f"ORDER BY count(*);"
    )


def _resolve_case(case: TruncateFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    missing = _target_missing(a)
    tbl = _table_name(p)
    ref = _ref_table_name(p)

    setup: list[str] = []
    locus = "target.truncate"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    fk_dep = a.get("fk_dependency", "no_fk_references")
    io = a.get("identity_option", "none")
    os_state = a.get("object_state", "table_exists")
    mt = a.get("multi_table", "single")
    ptb = a.get("partitioned_table_behavior", "none")
    tt = a.get("temporary_table_truncation", "none")
    empty = os_state in ("empty_table", "table_does_not_exist")

    # --- role fixtures ----------------------------------------------
    if effective == f"{p}actor":
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        setup.append(f"GRANT USAGE ON SCHEMA public TO {p}actor;")
        locus = "fixture.privilege_state"

    # --- target relation fixture ------------------------------------
    if missing:
        setup.append(
            "SELECT 1 AS target_relation_intentionally_absent;"
        )
        locus = "fixture.relation_missing"
    elif ptb == "partitioned_table_only":
        setup.append(
            f"CREATE TABLE {tbl} (id int, val int) "
            f"PARTITION BY RANGE (id);"
        )
        if not empty:
            setup.append(
                f"INSERT INTO {tbl} VALUES (1, 100), (2, 200);"
            )
        locus = "fixture.partitioned_table"
    elif ptb == "partitioned_table_with_descendants":
        setup.append(
            f"CREATE TABLE {tbl} (id int, val int) "
            f"PARTITION BY RANGE (id);"
        )
        setup.append(
            f"CREATE TABLE {ref} PARTITION OF {tbl} "
            f"FOR VALUES FROM (1) TO (100);"
        )
        if not empty:
            setup.append(
                f"INSERT INTO {tbl} VALUES (1, 100), (2, 200);"
            )
        locus = "fixture.partitioned_with_descendants"
    elif ptb == "single_partition":
        setup.append(
            f"CREATE TABLE {tbl} (id int, val int) "
            f"PARTITION BY RANGE (id);"
        )
        setup.append(
            f"CREATE TABLE {ref} PARTITION OF {tbl} "
            f"FOR VALUES FROM (1) TO (100);"
        )
        if not empty:
            setup.append(
                f"INSERT INTO {ref} VALUES (1, 100), (2, 200);"
            )
        locus = "fixture.single_partition"
    elif tt == "temporary_table":
        setup.append(f"CREATE TEMP TABLE {tbl} (id int, val int);")
        if not empty:
            setup.append(
                f"INSERT INTO {tbl} VALUES (1, 100), (2, 200);"
            )
        locus = "fixture.temporary_table"
    elif tt == "temp_table_with_sequences":
        setup.append(
            f"CREATE TEMP TABLE {tbl} (id serial, val int);"
        )
        if not empty:
            setup.append(
                f"INSERT INTO {tbl} (val) VALUES (100), (200);"
            )
        locus = "fixture.temp_table_with_sequences"
    elif fk_dep == "referenced_by_other_tables":
        setup.append(
            f"CREATE TABLE {tbl} (id int PRIMARY KEY, val int);"
        )
        setup.append(
            f"CREATE TABLE {ref} (id int REFERENCES {tbl}(id));"
        )
        if not empty:
            setup.append(f"INSERT INTO {tbl} VALUES (1, 100), (2, 200);")
            setup.append(f"INSERT INTO {ref} VALUES (1), (2);")
        locus = "fixture.fk_dependency"
    elif mt == "multiple":
        setup.append(f"CREATE TABLE {tbl} (id int, val int);")
        setup.append(f"CREATE TABLE {ref} (id int, val int);")
        if not empty:
            setup.append(
                f"INSERT INTO {tbl} VALUES (1, 100), (2, 200);"
            )
            setup.append(
                f"INSERT INTO {ref} VALUES (1, 100), (2, 200);"
            )
        locus = "fixture.multi_table"
    else:
        if io in ("restart_identity", "continue_identity"):
            setup.append(
                f"CREATE TABLE {tbl} "
                f"(id int GENERATED ALWAYS AS IDENTITY, val int);"
            )
            if not empty:
                setup.append(
                    f"INSERT INTO {tbl} (val) VALUES (100), (200);"
                )
        else:
            setup.append(f"CREATE TABLE {tbl} (id int, val int);")
            if not empty:
                setup.append(
                    f"INSERT INTO {tbl} VALUES (1, 100), (2, 200);"
                )
        locus = "fixture.table"

    # --- arm the effective role -------------------------------------
    if effective:
        setup.append(f"SET ROLE {effective};")

    # --- the primary target statement -------------------------------
    target = _build_target(a, p)

    # --- oracle / SQLSTATE assertion --------------------------------
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

    # --- cleanup construction (shared idempotent bookends) -----------
    # Migrated to cleanup_bookend so every DROP carries IF EXISTS and
    # DROP OWNED BY is unreachable in pre-cleanup: the granted_role
    # fixture is created by setup, so on a fresh database the role does
    # not exist yet at pre-cleanup time and DROP OWNED BY would crash
    # (ON_ERROR_STOP=1) before the target statement reaches execution.
    # Pre-cleanup drops roles via DROP ROLE IF EXISTS only; the post-target
    # cleanup runs DROP OWNED BY then DROP ROLE IF EXISTS once setup has
    # created the role.  The DROP TABLE IF EXISTS anchor is first in
    # pre-cleanup and last in cleanup, satisfying the table-bookend gate.
    specs: list[DropSpec] = []
    table_names = [tbl, ref]
    role_list = list(roles)
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


def resolve_truncate_factor_witness(
    case: TruncateFactorCase | TruncateFactorExtensionCase,
    repository_root: Path,
) -> TruncateFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return TruncateFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_truncate(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(re.findall(r"(?m)^TRUNCATE\b", region))


def _header(case: TruncateFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : TRUNCATE {case.factor_key}="
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


def render_truncate_factor_case(
    case: TruncateFactorCase | TruncateFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 TRUNCATE。")
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
    case: TruncateFactorCase | TruncateFactorExtensionCase,
    out: Path,
) -> None:
    text = render_truncate_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_truncate_factor_programs(
    baseline_plan: TruncateFactorLoopPlan,
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
    "TruncateFactorRenderError",
    "TruncateFactorWitness",
    "count_primary_truncate",
    "generate_truncate_factor_programs",
    "render_truncate_factor_case",
    "resolve_truncate_factor_witness",
]
