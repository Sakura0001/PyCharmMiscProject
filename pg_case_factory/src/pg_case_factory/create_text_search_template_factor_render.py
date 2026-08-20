"""Render complete PostgreSQL 18.4 CREATE TEXT SEARCH TEMPLATE factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CREATE TEXT SEARCH TEMPLATE is a catalog-row DDL statement: the target is a
``pg_catalog.pg_ts_template`` catalog row, not a ``pg_class`` relation.
All catalog oracles schema-qualify ``pg_catalog.pg_ts_template`` (exempt
from the file-prefix style gate via the ``pg_`` prefix).  No case creates
a TABLE, so the bookend (DROP TABLE IF EXISTS) is never emitted.  Every
catalog SELECT carries a top-level ``ORDER BY`` so the
catalog-observability gate passes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_text_search_template_factor_extension import (
    CreateTextSearchTemplateFactorExtensionCase,
    _present_failure_pair,
)
from .create_text_search_template_factor_loop import (
    CreateTextSearchTemplateFactorCase,
    CreateTextSearchTemplateFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/"
    "text_search_template/create_text_search_template.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/"
    "text_search_template/create_text_search_template.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class CreateTextSearchTemplateFactorRenderError(ValueError):
    """Raised when a CREATE TEXT SEARCH TEMPLATE case cannot be rendered."""


@dataclass(frozen=True)
class CreateTextSearchTemplateFactorWitness:
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
    ext: CreateTextSearchTemplateFactorExtensionCase,
) -> CreateTextSearchTemplateFactorCase:
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
    return CreateTextSearchTemplateFactorCase(
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
    case: CreateTextSearchTemplateFactorCase
    | CreateTextSearchTemplateFactorExtensionCase,
) -> CreateTextSearchTemplateFactorCase:
    if isinstance(
        case, CreateTextSearchTemplateFactorExtensionCase
    ):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateTextSearchTemplateFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _schema_name(p: str) -> str:
    return f"{p}schema"


def _template_name(a: dict[str, str], p: str) -> str:
    """The template identifier in CREATE TEXT SEARCH TEMPLATE."""

    shape = a.get("template_name_shape", "simple_id")
    schema = _schema_name(p)
    if shape == "schema_qualified_id":
        return f"{schema}.{p}template"
    if shape == "quoted_id":
        return f'"{p}Template"'
    if shape == "reserved_word_as_name":
        return "select"
    if shape == "invalid_name":
        return f"{p}123bad"
    if shape == "duplicate_name":
        return f"{schema}.{p}template"
    return f"{schema}.{p}template"


def _template_name_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    shape = a.get("template_name_shape", "simple_id")
    if shape == "quoted_id":
        return f"{p}Template"
    if shape == "reserved_word_as_name":
        return "select"
    if shape == "invalid_name":
        return f"{p}123bad"
    return f"{p}template"


def _function_name(a: dict[str, str], p: str, slot: str) -> str:
    """The function name referenced by a template slot."""

    shape = a.get("function_name_shape", "simple_id")
    schema = _schema_name(p)
    if shape == "nonexistent_name":
        return f"{schema}.{p}nofn"
    return f"{schema}.{p}{slot}"


def _is_duplicate(a: dict[str, str]) -> bool:
    return (
        a.get("object_state") == "exists"
        or a.get("template_name_shape") == "duplicate_name"
    )


def _is_syntax_error(a: dict[str, str]) -> bool:
    tns = a.get("template_name_shape", "simple_id")
    return tns in ("invalid_name", "reserved_word_as_name")


def _is_function_missing(a: dict[str, str]) -> bool:
    fd = a.get("function_dependency", "all_functions_valid")
    fe = a.get("function_existence", "all_functions_exist")
    nf = a.get("nonexistent_function", "function_exists")
    mlf = a.get(
        "missing_lexize_function", "lexize_present"
    )
    fns = a.get("function_name_shape", "simple_id")
    return (
        fd == "function_missing"
        or fe == "some_functions_missing"
        or nf == "function_missing"
        or mlf == "lexize_missing"
        or fns == "nonexistent_name"
    )


def _is_insufficient_privilege(a: dict[str, str]) -> bool:
    return a.get("privilege_level") == "non_superuser"


def _is_failure(a: dict[str, str]) -> bool:
    return a.get("expected_status") == "failure"


def _has_init(a: dict[str, str]) -> bool:
    return a.get("init_clause") == "specified"


def _effective_role(a: dict[str, str], p: str) -> str:
    if _is_insufficient_privilege(a):
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    if _is_insufficient_privilege(a):
        roles.append(f"{p}actor")
    return tuple(roles)


_SLOTS_REQUIRED = ("lexize",)


def _build_function_fixtures(
    a: dict[str, str], p: str
) -> list[str]:
    """Setup lines for the support function fixtures."""

    if _is_function_missing(a):
        return []
    schema = _schema_name(p)
    lines: list[str] = []
    for slot in _SLOTS_REQUIRED:
        lines.append(
            f"CREATE FUNCTION {schema}.{p}{slot}(internal) "
            f"RETURNS internal AS 'dsimple' "
            f"LANGUAGE C STRICT;"
        )
    if _has_init(a):
        lines.append(
            f"CREATE FUNCTION {schema}.{p}init(internal) "
            f"RETURNS internal AS 'dsimple' "
            f"LANGUAGE C STRICT;"
        )
    return lines


def _build_duplicate_fixture(
    a: dict[str, str], p: str
) -> list[str]:
    """Pre-create the template for duplicate-signature tests."""

    if not _is_duplicate(a):
        return []
    schema = _schema_name(p)
    lines: list[str] = []
    for slot in _SLOTS_REQUIRED:
        lines.append(
            f"CREATE FUNCTION {schema}.{p}{slot}(internal) "
            f"RETURNS internal AS 'dsimple' "
            f"LANGUAGE C STRICT;"
        )
    clauses = [
        f"lexize = {schema}.{p}lexize",
    ]
    lines.append(
        f"CREATE TEXT SEARCH TEMPLATE {schema}.{p}template "
        f"({', '.join(clauses)});"
    )
    return lines


def _build_target(
    a: dict[str, str], p: str
) -> str:
    """The primary CREATE TEXT SEARCH TEMPLATE statement."""

    name = _template_name(a, p)
    clauses: list[str] = []
    for slot in _SLOTS_REQUIRED:
        fn = _function_name(a, p, slot)
        clauses.append(f"{slot} = {fn}")
    if _has_init(a):
        fn = _function_name(a, p, "init")
        clauses.append(f"init = {fn}")
    return (
        f"CREATE TEXT SEARCH TEMPLATE {name} "
        f"({', '.join(clauses)});"
    )


def _probe_select(
    case: CreateTextSearchTemplateFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only verification."""

    mode = a.get(
        "verification_mode", "catalog_query_pg_ts_template"
    )
    if mode == "error_assertion":
        return None

    template_lit = _template_name_literal(a, p)
    present = not (
        _is_failure(a) and not _is_duplicate(a)
    )
    cmp_op = ">" if present else "="
    return (
        f"SELECT count(*) {cmp_op} 0 AS template_state "
        f"FROM pg_catalog.pg_ts_template "
        f"WHERE tmplname = '{template_lit}' "
        f"ORDER BY count(*);"
    )


def _build_cleanup(
    a: dict[str, str], p: str
) -> list[str]:
    """Cleanup lines after the primary target."""

    schema = _schema_name(p)
    cleanup_mode = a.get(
        "cleanup_mode", "drop_text_search_template"
    )
    lines: list[str] = []
    if _is_insufficient_privilege(a):
        lines.append("RESET ROLE;")
    if cleanup_mode == "drop_text_search_template":
        if not _is_syntax_error(a):
            lines.append(
                f"DROP TEXT SEARCH TEMPLATE IF EXISTS "
                f"{schema}.{p}template;"
            )
    if cleanup_mode == "drop_function" or True:
        for slot in _SLOTS_REQUIRED:
            lines.append(
                f"DROP FUNCTION IF EXISTS "
                f"{schema}.{p}{slot}(internal) CASCADE;"
            )
        if _has_init(a) or _is_duplicate(a):
            lines.append(
                f"DROP FUNCTION IF EXISTS "
                f"{schema}.{p}init(internal) CASCADE;"
            )
    lines.append(f"DROP SCHEMA IF EXISTS {schema} CASCADE;")
    for role in _role_names(a, p):
        lines.append(f"DROP OWNED BY {role} CASCADE;")
        lines.append(f"DROP ROLE IF EXISTS {role};")
    return lines


def _resolve_case(
    case: CreateTextSearchTemplateFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    schema = _schema_name(p)

    setup: list[str] = []
    locus = "target.create_text_search_template"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)

    # --- schema fixture ---
    setup.append(f"CREATE SCHEMA {schema};")
    locus = "fixture.schema"

    # --- support function fixtures ---
    if not _is_duplicate(a):
        setup.extend(_build_function_fixtures(a, p))
        if not _is_function_missing(a):
            locus = "fixture.support_functions"

    # --- duplicate template fixture ---
    if _is_duplicate(a):
        setup.extend(_build_duplicate_fixture(a, p))
        locus = "fixture.duplicate_template"

    # --- role fixture for privilege tests ---
    if effective:
        setup.append(
            f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;"
        )
        setup.append(
            f"GRANT USAGE ON SCHEMA {schema} TO {p}actor;"
        )
        locus = "fixture.privilege_state"

    if effective:
        setup.append(f"SET ROLE {effective};")

    # --- the primary target statement ---
    target = _build_target(a, p)

    # --- oracle / SQLSTATE assertion ---
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

    # --- cleanup construction ---
    cleanup = _build_cleanup(a, p)

    # --- pre-cleanup (safe, always IF EXISTS CASCADE) ---
    pre_cleanup: list[str] = []
    if not _is_syntax_error(a):
        pre_cleanup.append(
            f"DROP TEXT SEARCH TEMPLATE IF EXISTS "
            f"{schema}.{p}template;"
        )
    for slot in _SLOTS_REQUIRED:
        pre_cleanup.append(
            f"DROP FUNCTION IF EXISTS "
            f"{schema}.{p}{slot}(internal) CASCADE;"
        )
    pre_cleanup.append(
        f"DROP FUNCTION IF EXISTS "
        f"{schema}.{p}init(internal) CASCADE;"
    )
    pre_cleanup.append(f"DROP SCHEMA IF EXISTS {schema} CASCADE;")
    pre_cleanup.append("RESET ROLE;")
    for role in roles:
        pre_cleanup.append(f"DROP ROLE IF EXISTS {role};")
    if not pre_cleanup:
        pre_cleanup.append(
            "SELECT 1 AS residual_check_no_objects;"
        )

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


def _header(case: CreateTextSearchTemplateFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE TEXT SEARCH TEMPLATE "
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


def render_create_text_search_template_factor_case(
    case: CreateTextSearchTemplateFactorCase
    | CreateTextSearchTemplateFactorExtensionCase,
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
        "-- 3. 执行唯一获得覆盖信用的 CREATE TEXT SEARCH TEMPLATE。"
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
    case: CreateTextSearchTemplateFactorCase
    | CreateTextSearchTemplateFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_text_search_template_factor_case(
        case, Path(".")
    )
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_text_search_template_factor_programs(
    baseline_plan: CreateTextSearchTemplateFactorLoopPlan,
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


def count_primary_create_text_search_template(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(
            r"(?im)^CREATE\s+TEXT\s+SEARCH\s+TEMPLATE\b",
            region,
        )
    )


def resolve_create_text_search_template_factor_witness(
    case: CreateTextSearchTemplateFactorCase
    | CreateTextSearchTemplateFactorExtensionCase,
    repository_root: Path,
) -> CreateTextSearchTemplateFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateTextSearchTemplateFactorWitness(
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
    "CreateTextSearchTemplateFactorRenderError",
    "CreateTextSearchTemplateFactorWitness",
    "count_primary_create_text_search_template",
    "generate_create_text_search_template_factor_programs",
    "render_create_text_search_template_factor_case",
    "resolve_create_text_search_template_factor_witness",
]
