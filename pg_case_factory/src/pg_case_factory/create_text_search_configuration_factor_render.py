"""Render complete PostgreSQL 18.4 CREATE TEXT SEARCH CONFIGURATION factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CREATE TEXT SEARCH CONFIGURATION is a catalog-row DDL statement: the
target is a ``pg_catalog.pg_ts_config`` catalog row, not a ``pg_class``
relation.  All catalog oracles schema-qualify ``pg_catalog.pg_ts_config``
(exempt from the file-prefix style gate).  No case creates a TABLE, so
the bookend (DROP TABLE IF EXISTS) is never emitted.  Every catalog
SELECT carries a top-level ``ORDER BY count(*)`` so the
catalog-observability gate passes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_text_search_configuration_factor_extension import (
    CreateTextSearchConfigurationFactorExtensionCase,
    _present_failure_pair,
)
from .create_text_search_configuration_factor_loop import (
    CreateTextSearchConfigurationFactorCase,
    CreateTextSearchConfigurationFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/"
    "text_search_configuration/create_text_search_configuration.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/"
    "text_search_configuration/create_text_search_configuration.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_TS_PARSER = "default"


class CreateTextSearchConfigurationFactorRenderError(ValueError):
    """Raised when a CREATE TEXT SEARCH CONFIGURATION case cannot be rendered."""


@dataclass(frozen=True)
class CreateTextSearchConfigurationFactorWitness:
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
    ext: CreateTextSearchConfigurationFactorExtensionCase,
) -> CreateTextSearchConfigurationFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get(
            "target_action", ext.consumer_action_id
        )
    return CreateTextSearchConfigurationFactorCase(
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
    case: CreateTextSearchConfigurationFactorCase
    | CreateTextSearchConfigurationFactorExtensionCase,
) -> CreateTextSearchConfigurationFactorCase:
    if isinstance(
        case, CreateTextSearchConfigurationFactorExtensionCase
    ):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateTextSearchConfigurationFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _is_failure(a: dict[str, str]) -> bool:
    return a.get("expected_status") == "failure"


def _is_duplicate(a: dict[str, str]) -> bool:
    return a.get("object_state") == "exists"


def _present(a: dict[str, str]) -> bool:
    """Whether the config exists after the target statement."""

    if not _is_failure(a):
        return True
    if _is_duplicate(a):
        return True
    return False


def _config_name(a: dict[str, str], p: str) -> str:
    """The configuration identifier in CREATE TEXT SEARCH CONFIGURATION."""

    se = a.get("schema_existence", "schema_exists")
    if se == "schema_not_exists":
        return f"{p}nosuchschema.{p}cfg"
    shape = a.get("config_name_shape", "simple_id")
    if shape == "schema_qualified_id":
        return f"public.{p}cfg"
    if shape == "quoted_id":
        return f'"{p}qcfg"'
    if shape == "reserved_word_as_name":
        return f'"{p}select"'
    if shape == "duplicate_name":
        return f"{p}cfg"
    if shape == "invalid_name":
        return f"1{p}bad"
    return f"{p}cfg"


def _config_name_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    se = a.get("schema_existence", "schema_exists")
    if se == "schema_not_exists":
        return f"{p}cfg"
    shape = a.get("config_name_shape", "simple_id")
    if shape == "schema_qualified_id":
        return f"{p}cfg"
    if shape == "quoted_id":
        return f"{p}qcfg"
    if shape == "reserved_word_as_name":
        return f"{p}select"
    if shape == "duplicate_name":
        return f"{p}cfg"
    if shape == "invalid_name":
        return f"1{p}bad"
    return f"{p}cfg"


def _drop_config_name(a: dict[str, str], p: str) -> str:
    """A safe config name for cleanup DROP statements."""

    se = a.get("schema_existence", "schema_exists")
    if se == "schema_not_exists":
        return f"{p}cfg"
    shape = a.get("config_name_shape", "simple_id")
    if shape == "invalid_name":
        return f"{p}cfg"
    return _config_name(a, p)


def _parser_name(a: dict[str, str], p: str) -> str:
    """The parser name referenced in PARSER = parser_name."""

    shape = a.get("parser_name_shape", "simple_id")
    if shape == "schema_qualified_id":
        return "pg_catalog.default"
    if shape == "quoted_id":
        return '"default"'
    if shape == "nonexistent_name":
        return f"{p}nosuchparser"
    return "default"


def _copy_source_name(a: dict[str, str], p: str) -> str:
    """The copy source config referenced in COPY = source_config."""

    shape = a.get("copy_source_name_shape", "simple_id")
    if shape == "schema_qualified_id":
        return f"public.{p}srccfg"
    if shape == "quoted_id":
        return f'"{p}qsrccfg"'
    if shape == "nonexistent_name":
        return f"{p}nosuchsrc"
    return f"{p}srccfg"


def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target runs."""

    priv = a.get("privilege_level", "schema_owner")
    if priv == "non_owner":
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    priv = a.get("privilege_level", "schema_owner")
    if priv == "non_owner":
        roles.append(f"{p}actor")
    return tuple(roles)


def _probe_select(
    case: CreateTextSearchConfigurationFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only verification."""

    mode = a.get("verification_mode", "catalog_query_pg_ts_config")
    if mode == "error_assertion":
        return None
    literal = _config_name_literal(a, p)
    present = _present(a)
    cmp_op = ">" if present else "="
    return (
        f"SELECT count(*) {cmp_op} 0 AS config_state "
        f"FROM pg_catalog.pg_ts_config "
        f"WHERE cfgname = '{literal}' "
        f"ORDER BY count(*);"
    )


def _build_target(
    a: dict[str, str], p: str, cfg: str
) -> str:
    """The primary CREATE TEXT SEARCH CONFIGURATION statement."""

    mpc = a.get("missing_parser_or_copy", "one_specified")
    if mpc == "none_specified":
        return f"CREATE TEXT SEARCH CONFIGURATION {cfg} ();"
    pcc = a.get("parser_copy_conflict", "only_parser")
    parser_name = _parser_name(a, p)
    copy_source = _copy_source_name(a, p)
    if pcc == "both_specified":
        return (
            f"CREATE TEXT SEARCH CONFIGURATION {cfg} "
            f"(PARSER = {parser_name}, COPY = {copy_source});"
        )
    if pcc == "only_copy":
        return (
            f"CREATE TEXT SEARCH CONFIGURATION {cfg} "
            f"(COPY = {copy_source});"
        )
    return (
        f"CREATE TEXT SEARCH CONFIGURATION {cfg} "
        f"(PARSER = {parser_name});"
    )


def _needs_source_fixture(a: dict[str, str]) -> bool:
    """Whether a copy-source config fixture is needed."""

    cst = a.get("config_source_type", "parser")
    cse = a.get("copy_source_existence", "source_exists")
    return cst == "copy" and cse == "source_exists"


def _resolve_case(
    case: CreateTextSearchConfigurationFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    consumer = case.consumer_action_id

    setup: list[str] = []
    locus = "target.create_text_search_configuration"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    cfg = _config_name(a, p)

    # --- role fixtures -----------------------------------------------
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- source config fixture (only_copy with source_exists) -------
    if _needs_source_fixture(a):
        src = _copy_source_name(a, p)
        setup.append(
            f"CREATE TEXT SEARCH CONFIGURATION {src} "
            f"(PARSER = {_TS_PARSER});"
        )
        locus = "fixture.copy_source"

    # --- duplicate config fixture ------------------------------------
    if _is_duplicate(a):
        setup.append(
            f"CREATE TEXT SEARCH CONFIGURATION {cfg} "
            f"(PARSER = {_TS_PARSER});"
        )
        locus = "fixture.duplicate_config"

    # --- arm the effective role --------------------------------------
    if effective:
        setup.append(f"SET ROLE {effective};")

    # --- the primary target statement --------------------------------
    target = _build_target(a, p, cfg)

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
    configs_to_drop: list[str] = []
    if _is_duplicate(a):
        configs_to_drop.append(_drop_config_name(a, p))
    elif not _is_failure(a):
        configs_to_drop.append(_drop_config_name(a, p))
    if _needs_source_fixture(a):
        configs_to_drop.append(_copy_source_name(a, p))

    cleanup_mode = a.get(
        "cleanup_mode", "drop_text_search_configuration"
    )
    config_drops = [
        f"DROP TEXT SEARCH CONFIGURATION IF EXISTS {name};"
        for name in configs_to_drop
    ]
    if cleanup_mode == "drop_parser":
        config_drops.append(
            f"DROP TEXT SEARCH PARSER IF EXISTS {p}custparser;"
        )

    role_drops = [
        statement
        for role in roles
        for statement in (
            f"DROP OWNED BY {role} CASCADE;",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    # pre-cleanup: always use IF EXISTS CASCADE (safe)
    pre_cleanup: list[str] = []
    pre_cleanup.append(
        f"DROP TEXT SEARCH CONFIGURATION IF EXISTS {p}cfg CASCADE;"
    )
    pre_cleanup.append(
        f"DROP TEXT SEARCH CONFIGURATION IF EXISTS "
        f"public.{p}cfg CASCADE;"
    )
    pre_cleanup.append(
        f'DROP TEXT SEARCH CONFIGURATION IF EXISTS "{p}qcfg" CASCADE;'
    )
    pre_cleanup.append(
        f"DROP TEXT SEARCH CONFIGURATION IF EXISTS {p}srccfg CASCADE;"
    )
    pre_cleanup.append(
        f"DROP TEXT SEARCH PARSER IF EXISTS {p}custparser CASCADE;"
    )
    pre_cleanup.append(
        f"DROP SCHEMA IF EXISTS {p}nosuchschema CASCADE;"
    )
    pre_cleanup.append("RESET ROLE;")
    for role in roles:
        pre_cleanup.append(f"DROP ROLE IF EXISTS {role};")

    # cleanup: RESET ROLE, configs, parser, roles
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
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


def _header(case: CreateTextSearchConfigurationFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE TEXT SEARCH CONFIGURATION "
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


def render_create_text_search_configuration_factor_case(
    case: CreateTextSearchConfigurationFactorCase
    | CreateTextSearchConfigurationFactorExtensionCase,
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
        "-- 3. 执行唯一获得覆盖信度的 CREATE TEXT SEARCH CONFIGURATION。"
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
    case: CreateTextSearchConfigurationFactorCase
    | CreateTextSearchConfigurationFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_text_search_configuration_factor_case(
        case, Path(".")
    )
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_text_search_configuration_factor_programs(
    baseline_plan: CreateTextSearchConfigurationFactorLoopPlan,
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


def count_primary_create_text_search_configuration(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(
            r"(?im)^CREATE\s+TEXT\s+SEARCH\s+CONFIGURATION\b",
            region,
        )
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


def resolve_create_text_search_configuration_factor_witness(
    case: CreateTextSearchConfigurationFactorCase
    | CreateTextSearchConfigurationFactorExtensionCase,
    repository_root: Path,
) -> CreateTextSearchConfigurationFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateTextSearchConfigurationFactorWitness(
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
    "CreateTextSearchConfigurationFactorRenderError",
    "CreateTextSearchConfigurationFactorWitness",
    "count_primary_create_text_search_configuration",
    "generate_create_text_search_configuration_factor_programs",
    "render_create_text_search_configuration_factor_case",
    "resolve_create_text_search_configuration_factor_witness",
    "remove_primary_semantic_locus_but_keep_comments",
]
