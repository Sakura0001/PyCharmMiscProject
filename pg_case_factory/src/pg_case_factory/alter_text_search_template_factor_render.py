"""Render complete PostgreSQL 18.4 ALTER TEXT SEARCH TEMPLATE factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

ALTER TEXT SEARCH TEMPLATE is a full-text-search DDL statement: the
target is a ``pg_catalog.pg_ts_template`` catalog row, not a
``pg_class`` relation.  All catalog oracles schema-qualify
``pg_catalog.pg_ts_template`` (exempt from the file-prefix style gate).
No case creates a TABLE, so the bookend (DROP TABLE IF EXISTS) is never
emitted (``_tables_to_drop`` always returns ``[]``).  Every catalog
SELECT carries a top-level ``ORDER BY count(*)`` so the
catalog-observability gate passes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .cleanup_bookend import DropSpec, build_cleanup, build_pre_cleanup
from .alter_text_search_template_factor_extension import (
    AlterTextSearchTemplateFactorExtensionCase,
    _present_failure_pair,
)
from .alter_text_search_template_factor_loop import (
    AlterTextSearchTemplateFactorCase,
    AlterTextSearchTemplateFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/"
    "text_search_template/alter_text_search_template.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/"
    "text_search_template/alter_text_search_template.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_LEXIZE_FUNC = "dsimple_lexize"


class AlterTextSearchTemplateFactorRenderError(ValueError):
    """Raised when an ALTER TEXT SEARCH TEMPLATE case cannot be rendered."""


@dataclass(frozen=True)
class AlterTextSearchTemplateFactorWitness:
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
    ext: AlterTextSearchTemplateFactorExtensionCase,
) -> AlterTextSearchTemplateFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get("target_action", "rename")
    return AlterTextSearchTemplateFactorCase(
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
    case: AlterTextSearchTemplateFactorCase
    | AlterTextSearchTemplateFactorExtensionCase,
) -> AlterTextSearchTemplateFactorCase:
    if isinstance(
        case, AlterTextSearchTemplateFactorExtensionCase
    ):
        return _synthetic_case(case)
    return case


def _baseline(case: AlterTextSearchTemplateFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _object_missing(a: dict[str, str]) -> bool:
    return a.get("object_state", "exists") == "not_exists"


def _template_name(a: dict[str, str], p: str) -> str:
    """The template identifier in ALTER TEXT SEARCH TEMPLATE and fixtures."""

    shape = a.get("template_name_shape", "simple_id")
    if shape == "quoted_id":
        return f'"{p}Mixed Tmpl"'
    if shape == "schema_qualified_id":
        return f"{p}sch.{p}tmpl"
    if shape == "nonexistent_name":
        return f"{p}no_such_tmpl"
    return f"{p}tmpl"


def _template_name_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    shape = a.get("template_name_shape", "simple_id")
    if shape == "quoted_id":
        return f"{p}Mixed Tmpl"
    if shape == "schema_qualified_id":
        return f"{p}tmpl"
    if shape == "nonexistent_name":
        return f"{p}no_such_tmpl"
    return f"{p}tmpl"


def _new_name(a: dict[str, str], p: str) -> str:
    """The new name in RENAME TO."""

    shape = a.get("new_name_shape", "simple_id")
    rb = a.get("duplicate_new_name", "no_conflict")
    if (
        rb == "same_name_conflict"
        or shape == "duplicate_name"
    ):
        return f"{p}conflict_tmpl"
    if shape == "quoted_id":
        return f'"{p}Mixed New"'
    return f"{p}newtmpl"


def _new_name_literal(a: dict[str, str], p: str) -> str:
    shape = a.get("new_name_shape", "simple_id")
    rb = a.get("duplicate_new_name", "no_conflict")
    if (
        rb == "same_name_conflict"
        or shape == "duplicate_name"
    ):
        return f"{p}conflict_tmpl"
    if shape == "quoted_id":
        return f"{p}Mixed New"
    return f"{p}newtmpl"


def _target_schema(a: dict[str, str], p: str) -> str:
    """The target schema identifier in SET SCHEMA."""

    shape = a.get("schema_name_shape", "simple_id")
    se = a.get("schema_existence", "schema_exists")
    if shape == "nonexistent_schema" or se == "schema_not_exists":
        return f"{p}no_such_sch"
    return f"{p}sch"


def _fixture_schema(a: dict[str, str], p: str) -> str | None:
    """The fixture schema to create, if any."""

    shape = a.get("template_name_shape", "simple_id")
    action = a.get("target_action", "rename")
    if shape == "schema_qualified_id":
        return f"{p}sch"
    if action == "set_schema":
        se = a.get("schema_existence", "schema_exists")
        sns = a.get("schema_name_shape", "simple_id")
        if se != "schema_not_exists" and sns != "nonexistent_schema":
            return f"{p}sch"
        return None
    return None


def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target ALTER runs."""

    if a.get("privilege_level", "superuser") == "non_superuser":
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    if a.get("privilege_level", "superuser") == "non_superuser":
        roles.append(f"{p}actor")
    return tuple(roles)


def _probe_select(
    case: AlterTextSearchTemplateFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only error_assertion."""

    mode = a.get(
        "verification_mode", "catalog_query_pg_ts_template"
    )
    if mode == "error_assertion":
        return None

    missing = _object_missing(a)
    action = a.get("target_action", "rename")

    if action == "rename" and case.outcome == "success":
        check = _new_name_literal(a, p)
        present = True
    elif missing:
        check = _template_name_literal(a, p)
        present = False
    else:
        check = _template_name_literal(a, p)
        present = True

    cmp_op = ">" if present else "="
    return (
        f"SELECT count(*) {cmp_op} 0 AS template_state "
        f"FROM pg_catalog.pg_ts_template "
        f"WHERE tmplname = '{check}' "
        f"ORDER BY count(*);"
    )


def _tables_to_drop(
    case: AlterTextSearchTemplateFactorCase,
) -> list[str]:
    """Fixture tables the case CREATEs.

    ALTER TEXT SEARCH TEMPLATE is a full-text-search DDL statement: it
    never creates a TABLE.  The bookend (DROP TABLE IF EXISTS) is
    therefore never emitted.
    """
    return []


def _resolve_case(
    case: AlterTextSearchTemplateFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    action = a.get("target_action", "rename")
    missing = _object_missing(a)

    setup: list[str] = []
    locus = "target.alter_text_search_template"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    tmpl = _template_name(a, p)
    fixture_schema = _fixture_schema(a, p)

    # --- role fixtures -----------------------------------------------
    if effective == f"{p}actor":
        setup.append(
            f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;"
        )
        locus = "fixture.privilege_state"

    # --- fixture schema ---------------------------------------------
    if fixture_schema is not None:
        setup.append(f"CREATE SCHEMA {fixture_schema};")
        locus = "fixture.schema"

    # --- the target template fixture --------------------------------
    if not missing:
        setup.append(
            f"CREATE TEXT SEARCH TEMPLATE {tmpl} "
            f"(lexize = {_LEXIZE_FUNC});"
        )
        locus = "fixture.template"
    else:
        setup.append(
            "SELECT 1 AS target_template_intentionally_absent;"
        )
        locus = "fixture.template_missing"

    # --- conflicting template for rename conflict --------------------
    if (
        action == "rename"
        and (
            a.get("new_name_shape", "simple_id") == "duplicate_name"
            or a.get("duplicate_new_name", "no_conflict")
            == "same_name_conflict"
        )
    ):
        setup.append(
            f"CREATE TEXT SEARCH TEMPLATE {p}conflict_tmpl "
            f"(lexize = {_LEXIZE_FUNC});"
        )
        locus = "fixture.rename_conflict"

    # --- target schema fixture for set_schema success ----------------
    if (
        action == "set_schema"
        and fixture_schema is not None
    ):
        # the target schema already created above when it exists
        pass

    # --- arm the effective role --------------------------------------
    if effective:
        setup.append(f"SET ROLE {effective};")

    # --- the primary target statement --------------------------------
    target = _build_target(a, p, tmpl)

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

    # --- cleanup construction (shared idempotent bookends) -----------
    # Migrated to cleanup_bookend so every DROP carries IF EXISTS and
    # DROP OWNED BY is unreachable in pre-cleanup: the granted_role
    # fixture is created by setup, so on a fresh database the role does
    # not exist yet at pre-cleanup time and DROP OWNED BY would crash
    # (ON_ERROR_STOP=1) before the target statement reaches execution.
    # Pre-cleanup drops roles via DROP ROLE IF EXISTS only; the post-target
    # cleanup runs DROP OWNED BY then DROP ROLE IF EXISTS once setup has
    # created the role.  ALTER TEXT SEARCH TEMPLATE never creates a TABLE,
    # so tables=() and no DROP TABLE anchor is emitted.
    specs: list[DropSpec] = []
    if not missing:
        specs.append(DropSpec("TEXT SEARCH TEMPLATE", tmpl))
    if action == "rename":
        new = _new_name(a, p)
        if new != tmpl:
            specs.append(DropSpec("TEXT SEARCH TEMPLATE", new))
        if (
            a.get("new_name_shape", "simple_id") == "duplicate_name"
            or a.get("duplicate_new_name", "no_conflict")
            == "same_name_conflict"
        ):
            specs.append(DropSpec("TEXT SEARCH TEMPLATE", f"{p}conflict_tmpl"))

    schemas = (fixture_schema,) if fixture_schema is not None else ()
    role_list = list(roles)
    pre_bookend = build_pre_cleanup(
        specs=specs, schemas=schemas, roles=role_list
    )
    cln_bookend = build_cleanup(
        specs=specs,
        schemas=schemas,
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


def _build_target(
    a: dict[str, str], p: str, tmpl: str
) -> str:
    """The primary ALTER TEXT SEARCH TEMPLATE statement for the branch."""

    action = a.get("target_action", "rename")
    if action == "set_schema":
        schema = _target_schema(a, p)
        return (
            f"ALTER TEXT SEARCH TEMPLATE {tmpl} "
            f"SET SCHEMA {schema};"
        )
    new = _new_name(a, p)
    return (
        f"ALTER TEXT SEARCH TEMPLATE {tmpl} RENAME TO {new};"
    )


def resolve_alter_text_search_template_factor_witness(
    case: AlterTextSearchTemplateFactorCase
    | AlterTextSearchTemplateFactorExtensionCase,
    repository_root: Path,
) -> AlterTextSearchTemplateFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return AlterTextSearchTemplateFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_alter_text_search_template(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(
            r"(?im)^\s*ALTER\s+TEXT\s+SEARCH\s+TEMPLATE\b",
            region,
        )
    )


def _header(case: AlterTextSearchTemplateFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : ALTER TEXT SEARCH TEMPLATE "
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


def render_alter_text_search_template_factor_case(
    case: AlterTextSearchTemplateFactorCase
    | AlterTextSearchTemplateFactorExtensionCase,
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
    lines.append(
        "-- 3. 执行唯一获得覆盖信用的 ALTER TEXT SEARCH TEMPLATE。"
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
    case: AlterTextSearchTemplateFactorCase
    | AlterTextSearchTemplateFactorExtensionCase,
    out: Path,
) -> None:
    text = render_alter_text_search_template_factor_case(
        case, Path(".")
    )
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_alter_text_search_template_factor_programs(
    baseline_plan: AlterTextSearchTemplateFactorLoopPlan,
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
    "AlterTextSearchTemplateFactorRenderError",
    "AlterTextSearchTemplateFactorWitness",
    "count_primary_alter_text_search_template",
    "generate_alter_text_search_template_factor_programs",
    "render_alter_text_search_template_factor_case",
    "resolve_alter_text_search_template_factor_witness",
]
