"""Render complete PostgreSQL 18.4 DROP STATISTICS factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_statistic_ext WHERE
stxname = '...' ORDER BY count(*) LIMIT 1`` never nests a ``FROM``
inside an ``EXISTS`` subquery, so ``audit_catalog_observability`` accepts it.
The probe column is the real ``pg_statistic_ext.stxname`` column — the no-DB
tickoff does not execute this probe, so a wrong column would pass all static
gates yet be a permanent latent runtime bug; the column is verified.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .cleanup_bookend import DropSpec, build_cleanup, build_pre_cleanup
from .drop_statistics_factor_extension import (
    DropStatisticsFactorExtensionCase,
)
from .drop_statistics_factor_loop import (
    DropStatisticsFactorCase,
    DropStatisticsFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/statistics/"
    "drop_statistics.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/statistics/"
    "drop_statistics.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-21"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

# Baseline primaries whose target statistics is intentionally absent.
_ABSENT_STATISTICS_PRIMARIES = frozenset(
    {
        ("expected_status", "failure"),
        ("statistics_existence", "statistics_not_exists"),
        ("nonexistent_statistics", "statistics_does_not_exist"),
        ("statistics_name_shape", "non_existing_name"),
    }
)

# For an extension SUCCESS case the synthetic primary must be a neutral
# success primary whose helpers fall through to the assignment.
_BRANCH_NEUTRAL_SUCCESS = ("statistics_existence", "statistics_exists")


def _synthetic_case(
    ext: DropStatisticsFactorExtensionCase,
) -> DropStatisticsFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .drop_statistics_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropStatisticsFactorCase(
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
    case: DropStatisticsFactorCase | DropStatisticsFactorExtensionCase,
) -> DropStatisticsFactorCase:
    if isinstance(case, DropStatisticsFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropStatisticsFactorRenderError(ValueError):
    """Raised when a DROP STATISTICS case cannot be rendered."""


@dataclass(frozen=True)
class DropStatisticsFactorWitness:
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


def _baseline(case: DropStatisticsFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _stat_ref(case: DropStatisticsFactorCase, a: dict[str, str], p: str) -> str:
    """The statistics name as referenced inside DROP STATISTICS."""

    shape = a.get("statistics_name_shape", "simple_name")
    if shape == "schema_qualified_name":
        return f"public.{p}stat"
    if shape == "quoted_name":
        return f'"{p}qstat"'
    if shape == "reserved_word_name":
        return '"user"'
    if shape == "non_existing_name":
        return f"{p}nostat"
    return f"{p}stat"  # simple_name


def _stat_probe(case: DropStatisticsFactorCase, a: dict[str, str], p: str) -> str:
    """The bare statistics name (no quotes/schema) for the catalog probe."""

    shape = a.get("statistics_name_shape", "simple_name")
    if shape == "schema_qualified_name":
        return f"{p}stat"
    if shape == "quoted_name":
        return f"{p}qstat"
    if shape == "reserved_word_name":
        return "user"
    if shape == "non_existing_name":
        return f"{p}nostat"
    return f"{p}stat"  # simple_name


def _stat_created(case: DropStatisticsFactorCase, a: dict[str, str]) -> bool:
    """Whether a statistics fixture must be created."""

    if a.get("statistics_existence") == "statistics_not_exists":
        return False
    if a.get("statistics_name_shape") == "non_existing_name":
        return False
    return True


def _if_exists_present(case: DropStatisticsFactorCase, a: dict[str, str]) -> bool:
    return a.get("if_exists_clause") == "with_if_exists"


def _cascade_clause(a: dict[str, str]) -> str:
    cascade = a.get("cascade_restrict_clause", "no_clause_default_restrict")
    if cascade == "cascade":
        return "CASCADE"
    if cascade == "restrict":
        return "RESTRICT"
    return ""


def _effective_role(
    case: DropStatisticsFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP STATISTICS runs."""

    if case.kind == "EXT":
        if a.get("privilege_context") == "non_owner_no_privilege":
            return f"{p}actor"
        if a.get("executor_privilege") == "non_owner_no_privilege":
            return f"{p}actor"
        return ""
    if case.factor_key == "privilege_context":
        return f"{p}actor" if case.factor_value == "non_owner_no_privilege" else ""
    if case.factor_key == "executor_privilege":
        return f"{p}actor" if case.factor_value == "non_owner_no_privilege" else ""
    if case.factor_key == "privilege_insufficient":
        return f"{p}actor" if case.factor_value == "non_table_owner_dropping_statistics" else ""
    return ""


def _multi_target(a: dict[str, str]) -> str:
    return a.get("multi_target", "single_target")


def _stat_absent_after(
    case: DropStatisticsFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target statistics is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if not _stat_created(case, a):
        return True
    if case.outcome == "success":
        return True
    return False  # expected_failure: stat still exists


def _probe_select(
    case: DropStatisticsFactorCase, a: dict[str, str], p: str
) -> str:
    stat_probe = _stat_probe(case, a, p)
    absent = _stat_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "statistics_absent" if absent else "statistics_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_statistic_ext "
        f"WHERE stxname = '{stat_probe}' "
        "ORDER BY count(*) LIMIT 1;"
    )


def _role_names(
    case: DropStatisticsFactorCase, p: str, effective: str
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}actor":
        roles.append(f"{p}actor")
    return tuple(roles)


def _resolve_case(case: DropStatisticsFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    stat_ref = _stat_ref(case, a, p)
    stat_created = _stat_created(case, a)
    multi = _multi_target(a)

    setup: list[str] = []
    locus = "target.statistics"

    # --- setup boundary SELECT ---
    setup.append("SELECT 1 AS setup_boundary;")

    # --- role fixtures (CREATE only; SET ROLE deferred to after stat creation) ---
    effective = _effective_role(case, a, p)
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- the host base TABLE (always, for bookend + CREATE STATISTICS) ---
    setup.append(f"CREATE TABLE {p}t (c1 integer, c2 integer);")
    if locus == "target.statistics":
        locus = "fixture.host_table"

    # --- the statistics fixture (if it exists) ---
    if stat_created:
        setup.append(
            f"CREATE STATISTICS {stat_ref} ON {p}t (c1, c2);"
        )
        if locus == "target.statistics":
            locus = "fixture.statistics"
        # second stat for multi_target_all_exist
        if multi == "multi_target_all_exist":
            setup.append(
                f"CREATE STATISTICS {p}stat2 ON {p}t (c1, c2);"
            )
    else:
        setup.append(
            "SELECT 1 AS target_statistics_intentionally_absent;"
        )
        locus = "fixture.statistics_state"

    # --- arm the non-superuser role (AFTER statistics creation) ---
    if effective:
        setup.append(f"SET ROLE {p}actor;")
    if_exists = "IF EXISTS " if _if_exists_present(case, a) else ""
    cascade = _cascade_clause(a)

    # --- build the DROP STATISTICS target ---
    if multi == "single_target":
        target = f"DROP STATISTICS {if_exists}{stat_ref}"
    elif multi == "multi_target_all_exist":
        target = f"DROP STATISTICS {if_exists}{stat_ref}, {p}stat2"
    else:  # multi_target_some_not_exist
        target = f"DROP STATISTICS {if_exists}{stat_ref}, {p}nostat2"
    if cascade:
        target += f" {cascade}"
    target += ";"

    # RISK transaction wrapper around the target.
    if case.kind == "RISK":
        setup.append("BEGIN;")
        locus = "target.transaction_boundary"

    # --- oracle / SQLSTATE assertion ---
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

    # --- cleanup construction (idempotent bookends via cleanup_bookend) ---
    stat_specs = [DropSpec("STATISTICS", stat_ref)]
    if multi == "multi_target_all_exist":
        stat_specs.append(DropSpec("STATISTICS", f"{p}stat2"))
    elif multi == "multi_target_some_not_exist":
        stat_specs.append(DropSpec("STATISTICS", f"{p}nostat2"))
    roles = _role_names(case, p, effective)

    pre_cleanup_bk = build_pre_cleanup(
        tables=(f"{p}t",),
        specs=tuple(stat_specs),
        roles=tuple(roles),
    )
    cleanup_bk = build_cleanup(
        tables=(f"{p}t",),
        specs=tuple(stat_specs),
        roles=tuple(roles),
        drop_owned=bool(roles),
        reset_role=effective,
    )
    pre_cleanup = list(pre_cleanup_bk.statements)
    cleanup = list(cleanup_bk.statements)

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


def resolve_drop_statistics_factor_witness(
    case: DropStatisticsFactorCase | DropStatisticsFactorExtensionCase,
    repository_root: Path,
) -> DropStatisticsFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropStatisticsFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_statistics(sql: str) -> int:
    """Count the single credited DROP STATISTICS inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*DROP\s+STATISTICS\b", region)
    )


def _header(case: DropStatisticsFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP STATISTICS {case.factor_key}={case.factor_value}",
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


def render_drop_statistics_factor_case(
    case: DropStatisticsFactorCase | DropStatisticsFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP STATISTICS regress program."""

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地统计和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP STATISTICS。")
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


def generate_drop_statistics_factor_programs(
    baseline_plan: DropStatisticsFactorLoopPlan,
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
    case: DropStatisticsFactorCase | DropStatisticsFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_statistics_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropStatisticsFactorRenderError",
    "DropStatisticsFactorWitness",
    "count_primary_drop_statistics",
    "generate_drop_statistics_factor_programs",
    "render_drop_statistics_factor_case",
    "resolve_drop_statistics_factor_witness",
]
