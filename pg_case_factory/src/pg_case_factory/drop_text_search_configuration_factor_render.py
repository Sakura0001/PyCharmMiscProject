"""Render complete PostgreSQL 18.4 DROP TEXT SEARCH CONFIGURATION factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_ts_config WHERE cfgname =
'...' ORDER BY count(*) LIMIT 1`` never nests a ``FROM`` inside an ``EXISTS``
subquery, so ``audit_catalog_observability`` accepts it.  The probe column is
the real ``pg_ts_config`` column ``cfgname`` — the no-DB tickoff does not
execute this probe, so a wrong column would pass all static gates yet be a
permanent latent runtime bug; the column is verified against PG 18.4.

DROP TEXT SEARCH CONFIGURATION is a text-search DDL statement: the target is a
``pg_catalog.pg_ts_config`` catalog row, not a ``pg_class`` relation.  No case
creates a TABLE, so the bookend (DROP TABLE IF EXISTS) is never emitted.  The
dependent-object fixture (for RESTRICT dependency cases) is a table-less SQL
function whose ``::regconfig`` body resolves the configuration OID, so a
DROP ... RESTRICT surfaces a 2BP01 dependent-objects error.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .drop_text_search_configuration_factor_extension import (
    DropTextSearchConfigurationFactorExtensionCase,
)
from .drop_text_search_configuration_factor_loop import (
    DropTextSearchConfigurationFactorCase,
    DropTextSearchConfigurationFactorLoopPlan,
    _DEPENDENCY_PRIMARIES,
    _PRIVILEGE_PRIMARIES,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/"
    "text_search_configuration/drop_text_search_configuration.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/"
    "text_search_configuration/drop_text_search_configuration.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-21"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_TS_PARSER = "default"


def _synthetic_case(
    ext: DropTextSearchConfigurationFactorExtensionCase,
) -> DropTextSearchConfigurationFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .drop_text_search_configuration_factor_extension import (
        _present_failure_pair,
    )

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = ("object_state", "exists")
    return DropTextSearchConfigurationFactorCase(
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
    case: DropTextSearchConfigurationFactorCase
    | DropTextSearchConfigurationFactorExtensionCase,
) -> DropTextSearchConfigurationFactorCase:
    if isinstance(
        case, DropTextSearchConfigurationFactorExtensionCase
    ):
        return _synthetic_case(case)
    return case


class DropTextSearchConfigurationFactorRenderError(ValueError):
    """Raised when a DROP TEXT SEARCH CONFIGURATION case cannot be rendered."""


@dataclass(frozen=True)
class DropTextSearchConfigurationFactorWitness:
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


def _baseline(case: DropTextSearchConfigurationFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _config_name(a: dict[str, str], p: str) -> str:
    """The configuration identifier in DROP TEXT SEARCH CONFIGURATION."""

    shape = a.get("config_name_shape", "simple_id")
    if shape == "schema_qualified_id":
        return f"public.{p}cfg"
    if shape == "quoted_id":
        return f'"{p}qcfg"'
    if shape == "reserved_word_id":
        return f'"{p}select"'
    if shape == "non_existent_name":
        return f"{p}nosuchcfg"
    return f"{p}cfg"


def _config_probe(a: dict[str, str], p: str) -> str:
    """The bare cfgname (no quotes/schema) for the catalog probe."""

    shape = a.get("config_name_shape", "simple_id")
    if shape == "schema_qualified_id":
        return f"{p}cfg"
    if shape == "quoted_id":
        return f"{p}qcfg"
    if shape == "reserved_word_id":
        return f"{p}select"
    if shape == "non_existent_name":
        return f"{p}nosuchcfg"
    return f"{p}cfg"


def _config_created(a: dict[str, str]) -> bool:
    """Whether a configuration fixture must be created."""

    if a.get("object_state") == "absent":
        return False
    if a.get("config_name_shape") == "non_existent_name":
        return False
    return True


def _config_exists(a: dict[str, str]) -> bool:
    return (
        a.get("object_state") == "exists"
        and a.get("config_name_shape") != "non_existent_name"
    )


def _if_exists_present(case: DropTextSearchConfigurationFactorCase, a: dict[str, str]) -> bool:
    return a.get("if_exists_clause") == "present"


def _cascade_clause(a: dict[str, str]) -> str:
    cascade = a.get("cascade_restrict", "default_restrict")
    if cascade == "explicit_cascade":
        return "CASCADE"
    if cascade == "explicit_restrict":
        return "RESTRICT"
    return ""  # default_restrict: RESTRICT is the default


def _effective_role(
    case: DropTextSearchConfigurationFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP runs."""

    if case.kind == "EXT":
        return f"{p}actor" if a.get("authorization_path") == "non_owner" else ""
    if (case.factor_key, case.factor_value) in _PRIVILEGE_PRIMARIES:
        return f"{p}actor"
    return ""


def _needs_dependent(
    case: DropTextSearchConfigurationFactorCase, a: dict[str, str]
) -> bool:
    """Whether a dependent-object fixture must be created.

    A dependent can only block a drop of an existing configuration, so the
    fixture is suppressed when the configuration itself is absent.
    """

    if not _config_exists(a):
        return False
    if case.kind == "EXT":
        return a.get("dependency_status") == "has_dependencies"
    if (case.factor_key, case.factor_value) in _DEPENDENCY_PRIMARIES:
        return True
    return a.get("dependency_context") == "config_used_by_other_object"


def _config_absent_after(
    case: DropTextSearchConfigurationFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target configuration is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if not _config_created(a):
        return True
    if case.outcome == "expected_failure":
        return False
    return True


def _probe_select(
    case: DropTextSearchConfigurationFactorCase, a: dict[str, str], p: str
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only error_assertion."""

    mode = a.get("verification_mode", "catalog_query")
    if mode == "error_assertion":
        return None
    cfg_probe = _config_probe(a, p)
    absent = _config_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "config_absent" if absent else "config_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_ts_config "
        f"WHERE cfgname = '{cfg_probe}' "
        "ORDER BY count(*) LIMIT 1;"
    )


def _role_names(
    case: DropTextSearchConfigurationFactorCase, p: str, effective: str
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}actor":
        roles.append(f"{p}actor")
    return tuple(roles)


def _resolve_case(case: DropTextSearchConfigurationFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    cfg = _config_name(a, p)
    config_created = _config_created(a)
    needs_dep = _needs_dependent(case, a)
    cfg_probe = _config_probe(a, p)

    setup: list[str] = []
    locus = "target.drop_text_search_configuration"

    effective = _effective_role(case, a, p)
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    if config_created:
        setup.append(
            f"CREATE TEXT SEARCH CONFIGURATION {cfg} "
            f"(PARSER = {_TS_PARSER});"
        )
        if locus == "target.drop_text_search_configuration":
            locus = "fixture.configuration"
    else:
        setup.append("SELECT 1 AS target_config_intentionally_absent;")
        locus = "fixture.configuration_missing"

    if needs_dep:
        setup.append(
            f"CREATE FUNCTION {p}depfn() RETURNS tsvector LANGUAGE SQL "
            f"AS $$ SELECT to_tsvector('{cfg_probe}'::regconfig, "
            f"''::text) $$;"
        )
        locus = "fixture.dependency_state"

    if effective:
        setup.append(f"SET ROLE {p}actor;")
    if_exists = "IF EXISTS " if _if_exists_present(case, a) else ""
    cascade = _cascade_clause(a)
    target = f"DROP TEXT SEARCH CONFIGURATION {if_exists}{cfg}"
    if cascade:
        target += f" {cascade}"
    target += ";"

    if case.kind == "RISK":
        setup.append("BEGIN;")
        locus = "target.transaction_boundary"

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

    config_drops = (
        [f"DROP TEXT SEARCH CONFIGURATION IF EXISTS {cfg};"]
        if config_created
        else []
    )
    function_drops = (
        [f"DROP FUNCTION IF EXISTS {p}depfn;"] if needs_dep else []
    )
    roles = _role_names(case, p, effective)
    role_drops = [
        statement
        for role in roles
        for statement in (
            f"DROP OWNED BY {role};",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    pre_cleanup: list[str] = []
    pre_cleanup.extend(function_drops)
    pre_cleanup.extend(config_drops)
    pre_cleanup.extend(role_drops)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(function_drops)
    cleanup.extend(config_drops)
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


def resolve_drop_text_search_configuration_factor_witness(
    case: DropTextSearchConfigurationFactorCase
    | DropTextSearchConfigurationFactorExtensionCase,
    repository_root: Path,
) -> DropTextSearchConfigurationFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropTextSearchConfigurationFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_text_search_configuration(sql: str) -> int:
    """Count the single credited DROP TEXT SEARCH CONFIGURATION in the fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(
            r"(?im)^\s*DROP\s+TEXT\s+SEARCH\s+CONFIGURATION\b",
            region,
        )
    )


def _header(case: DropTextSearchConfigurationFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP TEXT SEARCH CONFIGURATION "
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


def render_drop_text_search_configuration_factor_case(
    case: DropTextSearchConfigurationFactorCase
    | DropTextSearchConfigurationFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP TEXT SEARCH CONFIGURATION program."""

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
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP TEXT SEARCH CONFIGURATION。")
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


def generate_drop_text_search_configuration_factor_programs(
    baseline_plan: DropTextSearchConfigurationFactorLoopPlan,
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
    case: DropTextSearchConfigurationFactorCase
    | DropTextSearchConfigurationFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_text_search_configuration_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropTextSearchConfigurationFactorRenderError",
    "DropTextSearchConfigurationFactorWitness",
    "count_primary_drop_text_search_configuration",
    "generate_drop_text_search_configuration_factor_programs",
    "render_drop_text_search_configuration_factor_case",
    "resolve_drop_text_search_configuration_factor_witness",
]
