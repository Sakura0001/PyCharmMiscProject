"""Render complete PostgreSQL 18.4 CREATE TEXT SEARCH DICTIONARY factor-loop programs.

Every planned obligation becomes one self-contained deterministic SQL file
assembled from :func:`_resolve_case` so the byte-level witness validator
can re-render and compare.  The catalog-row DDL target is
``pg_catalog.pg_ts_dict``; catalog oracles schema-qualify
``pg_catalog.pg_ts_dict``; there is no DROP TABLE bookend
(table-less-exempt); every catalog SELECT carries a top-level
``ORDER BY``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_text_search_dictionary_factor_extension import (
    CreateTextSearchDictionaryFactorExtensionCase,
    _present_failure_pair,
)
from .create_text_search_dictionary_factor_loop import (
    CreateTextSearchDictionaryFactorCase,
    CreateTextSearchDictionaryFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/"
    "text_search_dictionary/create_text_search_dictionary.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/"
    "text_search_dictionary/create_text_search_dictionary.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_RE_CREATE = re.compile(
    r"(?im)^\s*CREATE\s+TEXT\s+SEARCH\s+DICTIONARY\b"
)


class CreateTextSearchDictionaryFactorRenderError(ValueError):
    """Raised when a CREATE TEXT SEARCH DICTIONARY case cannot be rendered."""


@dataclass(frozen=True)
class CreateTextSearchDictionaryFactorWitness:
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
    ext: CreateTextSearchDictionaryFactorExtensionCase,
) -> CreateTextSearchDictionaryFactorCase:
    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get(
            "target_action", ext.consumer_action_id
        )
    return CreateTextSearchDictionaryFactorCase(
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
    case: CreateTextSearchDictionaryFactorCase
    | CreateTextSearchDictionaryFactorExtensionCase,
) -> CreateTextSearchDictionaryFactorCase:
    if isinstance(
        case, CreateTextSearchDictionaryFactorExtensionCase
    ):
        return _synthetic_case(case)
    return case


def _baseline(
    case: CreateTextSearchDictionaryFactorCase,
) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _dict_name(a: dict[str, str], p: str) -> str:
    shape = a.get("dict_name_shape", "simple_id")
    if shape == "schema_qualified_id":
        return f"public.{p}dict"
    if shape == "quoted_id":
        return f'"{p}QDict"'
    if shape == "reserved_word_as_name":
        return '"all"'
    if shape == "invalid_name":
        return "123baddict"
    return f"{p}dict"


def _dict_literal(a: dict[str, str], p: str) -> str:
    shape = a.get("dict_name_shape", "simple_id")
    if shape == "schema_qualified_id":
        return f"{p}dict"
    if shape == "quoted_id":
        return f"{p}QDict"
    if shape == "reserved_word_as_name":
        return "all"
    if shape == "invalid_name":
        return "123baddict"
    return f"{p}dict"


def _is_duplicate(a: dict[str, str]) -> bool:
    return a.get("object_state") == "exists"


def _is_failure(a: dict[str, str]) -> bool:
    return a.get("expected_status") == "failure"


def _present(a: dict[str, str]) -> bool:
    return not _is_failure(a) or _is_duplicate(a)


def _template_name(a: dict[str, str], p: str) -> str:
    te = a.get("template_existence", "template_exists")
    tns = a.get("template_name_shape", "simple_id")
    td = a.get("template_dependency", "template_exists_and_valid")
    nt = a.get("nonexistent_template", "template_exists")
    if (
        te == "template_not_exists"
        or tns == "nonexistent_name"
        or td == "template_missing"
        or nt == "template_missing"
    ):
        return f"{p}nosuchtmpl"
    if tns == "schema_qualified_id":
        return "pg_catalog.simple"
    return "simple"


def _option_value(a: dict[str, str], p: str, idx: int = 0) -> str:
    ovt = a.get("option_value_type", "simple_identifier")
    ovs = a.get("option_value_shape", "valid_value")
    if ovs == "invalid_value":
        return "@@invalid@@"
    if ovs == "quoted_value":
        return f"'{p}stop{idx}'"
    if ovt == "simple_identifier":
        return f"{p}stop{idx}"
    if ovt == "numeric_value":
        return str(5 + idx)
    if ovt == "quoted_string_value":
        return f"'{p}stop{idx}'"
    return f"{p}stop{idx}"


def _build_params(a: dict[str, str], p: str) -> str:
    template = _template_name(a, p)
    oc = a.get("option_clause", "only_template")
    if oc == "only_template":
        return f"TEMPLATE = {template}"
    ov1 = _option_value(a, p, 0)
    if oc == "template_plus_single_option":
        return f"TEMPLATE = {template}, stopwords = {ov1}"
    ov2 = _option_value(a, p, 1)
    return (
        f"TEMPLATE = {template}, stopwords = {ov1}, "
        f"language = {ov2}"
    )


def _build_target(a: dict[str, str], p: str) -> str:
    name = _dict_name(a, p)
    params = _build_params(a, p)
    return f"CREATE TEXT SEARCH DICTIONARY {name} ({params});"


def _effective_role(a: dict[str, str], p: str) -> str:
    if a.get("privilege_level") == "non_owner":
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    role = _effective_role(a, p)
    if role:
        return (role,)
    return ()


def _probe_select(
    case: CreateTextSearchDictionaryFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    vm = a.get("verification_mode", "catalog_query_pg_ts_dict")
    if vm == "error_assertion":
        return None
    literal = _dict_literal(a, p)
    cmp_op = ">" if _present(a) else "="
    return (
        f"SELECT count(*) {cmp_op} 0 AS dict_state "
        f"FROM pg_catalog.pg_ts_dict "
        f"WHERE dictname = '{literal}' "
        f"ORDER BY count(*);"
    )


def _resolve_case(
    case: CreateTextSearchDictionaryFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    name = _dict_name(a, p)
    roles = _role_names(a, p)
    effective = _effective_role(a, p)
    literal = _dict_literal(a, p)

    semantic_locus = "target.create_text_search_dictionary"

    # --- setup fixtures ---
    setup_lines: list[str] = []
    if effective:
        setup_lines.append(
            f"CREATE ROLE {effective} LOGIN NOSUPERUSER;"
        )
        setup_lines.append(f"SET ROLE {effective};")
        semantic_locus = "fixture.role"
    if _is_duplicate(a):
        setup_lines.append(
            f"CREATE TEXT SEARCH DICTIONARY {name} "
            f"(TEMPLATE = simple);"
        )
        semantic_locus = "fixture.duplicate_dict"

    # --- target ---
    target_fragment = _build_target(a, p)

    # --- assert / oracle ---
    assert_lines: list[str] = []
    if effective:
        assert_lines.append("RESET ROLE;")
    assert_lines.append(
        f"SELECT :'target_sqlstate' = "
        f"'{case.expected_sqlstate}' "
        f"AS target_sqlstate_matches_expected;"
    )
    probe = _probe_select(case, a, p)
    if probe is not None:
        assert_lines.append(probe)

    # --- pre-cleanup ---
    pre_cleanup_lines: list[str] = [
        f"DROP TEXT SEARCH DICTIONARY IF EXISTS {name} CASCADE;",
        f"DROP TEXT SEARCH TEMPLATE IF EXISTS {p}tmpl;",
    ]
    if effective:
        pre_cleanup_lines.append("RESET ROLE;")
        pre_cleanup_lines.append(
            f"DROP OWNED BY {effective} CASCADE;"
        )
        pre_cleanup_lines.append(
            f"DROP ROLE IF EXISTS {effective};"
        )

    # --- cleanup ---
    cleanup_lines: list[str] = []
    if effective:
        cleanup_lines.append("RESET ROLE;")
    cleanup_lines.append(
        f"DROP TEXT SEARCH DICTIONARY IF EXISTS {name} CASCADE;"
    )
    cleanup_mode = a.get(
        "cleanup_mode", "drop_text_search_dictionary"
    )
    if cleanup_mode == "drop_template":
        cleanup_lines.append(
            f"DROP TEXT SEARCH TEMPLATE IF EXISTS {p}tmpl;"
        )
    if effective:
        cleanup_lines.append(
            f"DROP OWNED BY {effective} CASCADE;"
        )
        cleanup_lines.append(
            f"DROP ROLE IF EXISTS {effective};"
        )

    on_error_off = case.outcome == "expected_failure"

    return _CasePlan(
        target_fragment=target_fragment,
        setup_lines=tuple(setup_lines),
        assert_lines=tuple(assert_lines),
        pre_cleanup_lines=tuple(pre_cleanup_lines),
        cleanup_lines=tuple(cleanup_lines),
        on_error_off=on_error_off,
        semantic_locus=semantic_locus,
    )


def _header(
    case: CreateTextSearchDictionaryFactorCase,
) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        (
            f"-- description  : CREATE TEXT SEARCH DICTIONARY "
            f"{case.factor_key}={case.factor_value}"
        ),
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


def render_create_text_search_dictionary_factor_case(
    case: CreateTextSearchDictionaryFactorCase
    | CreateTextSearchDictionaryFactorExtensionCase,
    repository_root: Path,
) -> str:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    lines: list[str] = []
    lines.extend(_header(rc))
    lines.append(
        "-- 1. 清理本编号对象，保证脚本可重复执行。"
    )
    lines.extend(plan.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("SELECT 1 AS setup_boundary;")
    lines.append(
        "-- 2. 创建完整本地规则和因子专用夹具。"
    )
    lines.extend(plan.setup_lines)
    if plan.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("SELECT 1 AS pre_target_boundary;")
    lines.append(
        "-- 3. 执行唯一获得覆盖信用的 "
        "CREATE TEXT SEARCH DICTIONARY。"
    )
    lines.append(_PRIMARY_BEGIN)
    lines.append(plan.target_fragment)
    lines.append(_PRIMARY_END)
    lines.append("\\set target_sqlstate :SQLSTATE")
    lines.append("\\echo PGCF_TARGET_SQLSTATE=:target_sqlstate")
    if plan.on_error_off:
        lines.append("\\set ON_ERROR_STOP on")
    lines.append(
        "-- 4. 验证 SQLSTATE、目录状态和数据行为。"
    )
    lines.extend(plan.assert_lines)
    lines.append("-- 5. 清理全部本编号对象。")
    lines.extend(plan.cleanup_lines)
    return "\n".join(lines) + "\n"


def _write_program(
    case: CreateTextSearchDictionaryFactorCase
    | CreateTextSearchDictionaryFactorExtensionCase,
    out: Path,
) -> None:
    rc = _as_render_case(case)
    text = render_create_text_search_dictionary_factor_case(
        rc, Path(out.anchor)
    )
    (out / rc.sql_filename).write_text(
        text, encoding="utf-8"
    )


def generate_create_text_search_dictionary_factor_programs(
    baseline_plan: CreateTextSearchDictionaryFactorLoopPlan,
    extension_plan: object,
    out_dir: Path,
) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for case in baseline_plan.cases:
        _write_program(case, out_dir)
        count += 1
    for case in extension_plan.cases:
        _write_program(case, out_dir)
        count += 1
    return count


def count_primary_create_text_search_dictionary(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1:
        return 0
    if sql.count(_PRIMARY_END) != 1:
        return 0
    begin_idx = sql.index(_PRIMARY_BEGIN)
    end_idx = sql.index(_PRIMARY_END)
    if begin_idx > end_idx:
        return 0
    region = sql[begin_idx:end_idx]
    return len(_RE_CREATE.findall(region))


def remove_primary_semantic_locus_but_keep_comments(
    sql: str, case: object
) -> str:
    rc = _as_render_case(case)
    trace = f"-- case_id: {rc.case_id}"
    if trace not in sql:
        raise CreateTextSearchDictionaryFactorRenderError(
            "case trace is missing"
        )
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        raise CreateTextSearchDictionaryFactorRenderError(
            "primary target markers not found"
        )
    begin_idx = sql.index(_PRIMARY_BEGIN) + len(_PRIMARY_BEGIN)
    end_idx = sql.index(_PRIMARY_END)
    region = sql[begin_idx:end_idx]
    kept: list[str] = []
    for line in region.split("\n"):
        stripped = line.strip()
        if stripped.startswith("--") or not stripped:
            kept.append(line)
    kept.append("SELECT true AS removed_primary_semantic_locus;")
    return sql[:begin_idx] + "\n".join(kept) + sql[end_idx:]


def resolve_create_text_search_dictionary_factor_witness(
    case: CreateTextSearchDictionaryFactorCase
    | CreateTextSearchDictionaryFactorExtensionCase,
    repository_root: Path,
) -> CreateTextSearchDictionaryFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    a = _baseline(rc)
    p = rc.object_prefix
    probe = _probe_select(rc, a, p)
    oracle_sql = tuple(plan.assert_lines)
    if probe is None and not oracle_sql:
        oracle_sql = ()
    return CreateTextSearchDictionaryFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=oracle_sql,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


__all__ = [
    "CreateTextSearchDictionaryFactorRenderError",
    "CreateTextSearchDictionaryFactorWitness",
    "count_primary_create_text_search_dictionary",
    "generate_create_text_search_dictionary_factor_programs",
    "render_create_text_search_dictionary_factor_case",
    "resolve_create_text_search_dictionary_factor_witness",
    "remove_primary_semantic_locus_but_keep_comments",
]
