"""Render complete PostgreSQL 18.4 CREATE DOMAIN factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CREATE DOMAIN is a type-defining DDL statement: the target is a
``pg_catalog.pg_type`` catalog row (``typtype = 'd'``), not a
``pg_class`` relation.  All catalog oracles schema-qualify
``pg_catalog.pg_type`` (exempt from the file-prefix style gate).  No case
creates a TABLE, so the bookend (DROP TABLE IF EXISTS) is never emitted
(``_tables_to_drop`` always returns ``[]``); when a case creates no
cleanup objects the ``SELECT 1 AS residual_check_no_objects;``
placeholder is emitted instead.  Every catalog SELECT carries a
top-level ``ORDER BY count(*)`` so the catalog-observability gate passes.
The ``CREATE DOMAIN`` keyword always begins a line at column 0 so the
parent's ``(?m)^CREATE\\s+DOMAIN`` target-pattern gate matches.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .cleanup_bookend import DropSpec, build_cleanup, build_pre_cleanup
from .create_domain_factor_extension import (
    CreateDomainFactorExtensionCase,
    _present_failure_pair,
)
from .create_domain_factor_loop import (
    CreateDomainFactorCase,
    CreateDomainFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/domain/"
    "create_domain.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/domain/"
    "create_domain.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

# base_data_type canonical value -> PostgreSQL SQL type expression.
_BASE_TYPE_SQL: dict[str, str] = {
    "integer": "integer",
    "bigint": "bigint",
    "smallint": "smallint",
    "numeric": "numeric",
    "real": "real",
    "double_precision": "double precision",
    "text": "text",
    "varchar": "varchar",
    "character": "character",
    "boolean": "boolean",
    "date": "date",
    "timestamp": "timestamp",
    "timestamptz": "timestamptz",
    "time": "time",
    "interval": "interval",
    "uuid": "uuid",
    "jsonb": "jsonb",
    "bytea": "bytea",
    "int_array": "integer[]",
    "text_array": "text[]",
}

_NUMERIC_TYPES = frozenset(
    {
        "integer",
        "bigint",
        "smallint",
        "numeric",
        "real",
        "double_precision",
    }
)
_TEXT_TYPES = frozenset({"text", "varchar", "character"})
_ARRAY_TYPES = frozenset({"int_array", "text_array"})


class CreateDomainFactorRenderError(ValueError):
    """Raised when a CREATE DOMAIN case cannot be rendered."""


@dataclass(frozen=True)
class CreateDomainFactorWitness:
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
    ext: CreateDomainFactorExtensionCase,
) -> CreateDomainFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get("target_action", "create_domain")
    return CreateDomainFactorCase(
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
    case: CreateDomainFactorCase
    | CreateDomainFactorExtensionCase,
) -> CreateDomainFactorCase:
    if isinstance(case, CreateDomainFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateDomainFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _is_privilege_failure(a: dict[str, str]) -> bool:
    return (
        a.get("privilege_level") == "non_owner_no_create"
        or a.get("base_type_privilege") == "no_usage"
        or a.get("privilege_denied_on_base_type")
        == "lacks_usage_privilege"
    )


def _is_duplicate(a: dict[str, str]) -> bool:
    return a.get("object_state") == "exists"


def _is_type_conflict(a: dict[str, str]) -> bool:
    return (
        a.get("object_state") == "type_name_conflict"
        or a.get("reserved_name_conflict") == "name_conflicts_with_type"
    )


def _is_explicit_collation(a: dict[str, str]) -> bool:
    return (
        a.get("collation_name_shape") == "explicit_collation_name"
        and a.get("collation_existence") == "collation_exists"
        and a.get("collate_clause") == "specified_collation"
    )


def _effective_base_type(a: dict[str, str]) -> str:
    """Base type after collation-driven overrides (render-level)."""

    cot = a.get(
        "collation_on_non_collatable_type", "collatable_type_with_collate"
    )
    cc = a.get("collate_clause", "omitted")
    bdt = a.get("base_data_type", "integer")
    if cot == "non_collatable_type_with_collate":
        return "boolean"
    if cc == "specified_collation":
        return "text"
    return bdt


def _base_type_expr(a: dict[str, str], p: str) -> str:
    tns = a.get("type_name_shape", "standard_type_name")
    bdt = _effective_base_type(a)
    mapped = _BASE_TYPE_SQL.get(bdt, "integer")
    if tns == "nonexistent_type":
        return f"{p}nonexisttype"
    if tns == "quoted_type_name":
        return f'"{mapped}"'
    if tns == "array_type_specifier":
        return "integer[]"
    return mapped


def _domain_name(a: dict[str, str], p: str) -> str:
    se = a.get("schema_existence", "schema_exists")
    dns = a.get("domain_name_shape", "simple_id")
    base = f"{p}dom"
    if se == "schema_not_exists":
        return f"{p}badschema.{base}"
    if dns == "schema_qualified":
        return f"public.{base}"
    if dns == "quoted_id":
        return f'"{base}"'
    if dns == "invalid_name":
        return "123bad"
    # simple_id, reserved_word_as_name, duplicate_name
    return base


def _normalize_dom_name(dom: str) -> str:
    last = dom.split(".")[-1]
    return last.strip('"').lower()


def _collation_clause(a: dict[str, str], p: str) -> str:
    cc = a.get("collate_clause", "omitted")
    if cc == "omitted":
        return ""
    cns = a.get("collation_name_shape", "default_collation")
    ce = a.get("collation_existence", "collation_exists")
    if cns == "nonexistent_collation" or ce == "collation_not_exists":
        return f"COLLATE {p}noecoll"
    if _is_explicit_collation(a):
        return f"COLLATE {p}mycoll"
    return 'COLLATE "C"'


_VALID_LITERALS: dict[str, str] = {
    "integer": "0",
    "bigint": "0",
    "smallint": "0",
    "numeric": "0",
    "real": "0",
    "double_precision": "0",
    "text": "'x'",
    "varchar": "'x'",
    "character": "'x'",
    "boolean": "TRUE",
    "date": "'2000-01-01'",
    "timestamp": "'2000-01-01 00:00:00'",
    "timestamptz": "'2000-01-01 00:00:00'",
    "time": "'00:00:00'",
    "interval": "'0'",
    "uuid": "'00000000-0000-0000-0000-000000000000'",
    "jsonb": "'{}'",
    "bytea": "'\\x'",
    "int_array": "'{}'",
    "text_array": "'{}'",
}


def _type_literal(bdt: str) -> str:
    """A valid DEFAULT literal (assignment-castable to the base type)."""

    return _VALID_LITERALS.get(bdt, "0")


def _type_expression(bdt: str) -> str:
    """A valid non-trivial DEFAULT expression for the base type."""

    if bdt in _NUMERIC_TYPES:
        return "1+1"
    if bdt in _TEXT_TYPES:
        return "'a' || 'b'"
    if bdt == "boolean":
        return "TRUE OR FALSE"
    mapped = _BASE_TYPE_SQL.get(bdt, "integer")
    return f"{_VALID_LITERALS.get(bdt, '0')}::{mapped}"


def _domain_test_value(bdt: str) -> str:
    """A non-NULL value satisfying every CHECK the render can emit."""

    if bdt in _NUMERIC_TYPES:
        return "1"  # satisfies CHECK (VALUE > 0)
    if bdt in _TEXT_TYPES:
        return "'x'"  # satisfies CHECK (VALUE <> '')
    return _VALID_LITERALS.get(bdt, "1")  # satisfies VALUE IS NOT NULL


def _default_clause(a: dict[str, str], p: str) -> str:
    dc = a.get("default_clause", "omitted")
    des = a.get("default_expression_shape", "literal_value")
    if dc == "omitted":
        return ""
    if des == "subquery_illegal":
        return "DEFAULT (SELECT 1)"
    if des == "type_mismatching_expression":
        return "DEFAULT 'wrong'"
    eff = _effective_base_type(a)
    if dc == "literal_default":
        return f"DEFAULT {_type_literal(eff)}"
    if dc == "expression_default":
        return f"DEFAULT ({_type_expression(eff)})"
    if dc == "null_default":
        return "DEFAULT NULL"
    return ""


def _check_expression(bdt: str) -> str:
    if bdt in _NUMERIC_TYPES:
        return "VALUE > 0"
    if bdt in _TEXT_TYPES:
        return "VALUE <> ''"
    return "VALUE IS NOT NULL"


def _constraint_clause(a: dict[str, str], p: str) -> str:
    ct = a.get("constraint_type", "none")
    cn = a.get("constraint_naming", "auto_named")
    cns_shape = a.get("constraint_name_shape", "auto_generated")
    ces = a.get("check_expr_subquery", "valid_check")
    cen = a.get("check_expr_non_boolean", "boolean_check")
    ncc = a.get("null_constraint_conflict", "single_constraint")

    if ncc == "conflicting_null_not_null":
        return "NOT NULL NULL"

    name = ""
    if cn == "explicitly_named":
        if cns_shape == "quoted_id":
            name = f'CONSTRAINT "{p}chk" '
        else:
            name = f"CONSTRAINT {p}chk "

    parts: list[str] = []
    if ct in ("not_null", "not_null_and_check"):
        parts.append("NOT NULL")
    if ct == "null_explicit":
        parts.append("NULL")
    if ct in ("check_only", "not_null_and_check", "multiple_check"):
        if ces == "subquery_in_check":
            parts.append("CHECK ((SELECT 1) > 0)")
        elif cen == "non_boolean_check":
            parts.append("CHECK (1)")
        else:
            chk = _check_expression(_effective_base_type(a))
            parts.append(f"CHECK ({chk})")
            if ct == "multiple_check":
                parts.append(f"CHECK ({chk})")
    if not parts:
        return ""
    return name + " ".join(parts)


def _target_fragment(a: dict[str, str], p: str) -> str:
    dom = _domain_name(a, p)
    btype = _base_type_expr(a, p)
    parts = [f"CREATE DOMAIN {dom} AS {btype}"]
    coll = _collation_clause(a, p)
    if coll:
        parts.append(coll)
    default = _default_clause(a, p)
    if default:
        parts.append(default)
    constr = _constraint_clause(a, p)
    if constr:
        parts.append(constr)
    return " ".join(parts) + ";"


def _probe_select(
    case: CreateDomainFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit or domain-value oracle, or None for error-only."""

    mode = a.get("verification_mode", "catalog_query_pg_type")
    if mode == "error_assertion":
        return None
    dom = _domain_name(a, p)
    if mode == "catalog_query_pg_type":
        present = case.outcome == "success"
        cmp_op = ">" if present else "="
        norm = _normalize_dom_name(dom)
        return (
            f"SELECT count(*) {cmp_op} 0 AS domain_state "
            f"FROM pg_catalog.pg_type "
            f"WHERE typname = '{norm}' AND typtype = 'd' "
            f"ORDER BY count(*);"
        )
    if mode == "domain_value_test":
        if case.outcome == "success":
            val = _domain_test_value(_effective_base_type(a))
            return f"SELECT ({val})::{dom} AS domain_value_check;"
        return None
    return None


def _tables_to_drop(
    case: CreateDomainFactorCase,
) -> list[str]:
    """Fixture tables the case CREATEs.

    CREATE DOMAIN is a type-defining DDL statement: it never creates a
    TABLE.  The bookend (DROP TABLE IF EXISTS) is therefore never emitted.
    """
    return []


def _needs_role(a: dict[str, str]) -> bool:
    return _is_privilege_failure(a)


def _resolve_case(
    case: CreateDomainFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix

    setup: list[str] = []
    locus = "target.create_domain"

    dom = _domain_name(a, p)

    # --- explicit collation fixture (success specified_collation) ----
    if _is_explicit_collation(a):
        setup.append(
            f"CREATE COLLATION {p}mycoll (locale = 'C');"
        )
        locus = "fixture.collation"

    # --- pre-create TYPE for type-name conflict (42710) --------------
    if _is_type_conflict(a):
        setup.append(
            f"CREATE TYPE {dom} AS ENUM ('a', 'b');"
        )
        locus = "fixture.pre_existing_type"

    # --- pre-create DOMAIN for duplicate (42710) ----------------------
    if _is_duplicate(a):
        setup.append(
            f"CREATE DOMAIN {dom} AS integer;"
        )
        locus = "fixture.pre_existing_domain"

    # --- non-superuser role for privilege failure (42501) ---------------
    if _needs_role(a):
        setup.append(
            f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;"
        )
        setup.append(f"SET ROLE {p}actor;")
        locus = "fixture.privilege_state"

    # --- the primary target statement --------------------------------
    target = _target_fragment(a, p)

    # --- oracle / SQLSTATE assertion ---------------------------------
    assert_lines: list[str] = []
    if _needs_role(a):
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
    # DROP OWNED BY is unreachable in pre-cleanup: the {p}actor role
    # fixture is created by setup, so on a fresh database the role does
    # not exist yet at pre-cleanup time and DROP OWNED BY would crash
    # (ON_ERROR_STOP=1) before the target statement reaches execution.
    # Pre-cleanup drops roles via DROP ROLE IF EXISTS only; the post-target
    # cleanup runs DROP OWNED BY then DROP ROLE IF EXISTS once setup has
    # created the role.  CREATE DOMAIN never creates a TABLE, so the
    # DROP TABLE IF EXISTS anchor is never emitted and a residual SELECT
    # fills the region when nothing is dropped.
    specs: list[DropSpec] = []
    if case.outcome == "success" or _is_duplicate(a):
        specs.append(DropSpec("DOMAIN", dom))
    if _is_type_conflict(a):
        specs.append(DropSpec("TYPE", dom))
    if _is_explicit_collation(a):
        specs.append(DropSpec("COLLATION", f"{p}mycoll"))
    role_list = [f"{p}actor"] if _needs_role(a) else []
    pre_bookend = build_pre_cleanup(
        specs=tuple(specs),
        roles=role_list,
    )
    cln_bookend = build_cleanup(
        specs=tuple(specs),
        roles=role_list,
        drop_owned=bool(role_list),
        reset_role=bool(role_list),
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


def resolve_create_domain_factor_witness(
    case: CreateDomainFactorCase
    | CreateDomainFactorExtensionCase,
    repository_root: Path,
) -> CreateDomainFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateDomainFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_create_domain(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*CREATE\s+DOMAIN\b", region)
    )


def _header(case: CreateDomainFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE DOMAIN {case.factor_key}="
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


def render_create_domain_factor_case(
    case: CreateDomainFactorCase
    | CreateDomainFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 CREATE DOMAIN。")
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
    case: CreateDomainFactorCase
    | CreateDomainFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_domain_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_domain_factor_programs(
    baseline_plan: CreateDomainFactorLoopPlan,
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
    "CreateDomainFactorRenderError",
    "CreateDomainFactorWitness",
    "count_primary_create_domain",
    "generate_create_domain_factor_programs",
    "render_create_domain_factor_case",
    "resolve_create_domain_factor_witness",
]
