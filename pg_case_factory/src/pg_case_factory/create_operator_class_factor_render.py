"""Render complete PostgreSQL 18.4 CREATE OPERATOR CLASS factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CREATE OPERATOR CLASS is a catalog-row DDL statement: the target is a
``pg_catalog.pg_opclass`` catalog row, not a ``pg_class`` relation.
All catalog oracles schema-qualify ``pg_catalog.pg_opclass`` (exempt
from the file-prefix style gate).  No case creates a TABLE, so the
bookend (DROP TABLE IF EXISTS) is never emitted.  Every catalog SELECT
carries a top-level ``ORDER BY`` so the catalog-observability gate
passes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_operator_class_factor_extension import (
    CreateOperatorClassFactorExtensionCase,
    _present_failure_pair,
)
from .create_operator_class_factor_loop import (
    _DATA_TYPE_METHOD,
    CreateOperatorClassFactorCase,
    CreateOperatorClassFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/operator_class/"
    "create_operator_class.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/operator_class/"
    "create_operator_class.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class CreateOperatorClassFactorRenderError(ValueError):
    """Raised when a CREATE OPERATOR CLASS case cannot be rendered."""


@dataclass(frozen=True)
class CreateOperatorClassFactorWitness:
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
    ext: CreateOperatorClassFactorExtensionCase,
) -> CreateOperatorClassFactorCase:
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
    return CreateOperatorClassFactorCase(
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
    case: CreateOperatorClassFactorCase
    | CreateOperatorClassFactorExtensionCase,
) -> CreateOperatorClassFactorCase:
    if isinstance(
        case, CreateOperatorClassFactorExtensionCase
    ):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateOperatorClassFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _resolve_data_type(a: dict[str, str], p: str) -> str:
    """The data type used for fixtures and the FOR TYPE clause."""

    dtim = a.get("data_type_index_method", "btree_integer")
    data_type, _ = _DATA_TYPE_METHOD.get(dtim, ("integer", "btree"))
    if data_type == "custom":
        return f"{p}geom"
    return data_type


def _resolve_index_method(a: dict[str, str]) -> str:
    """The index method."""

    dtim = a.get("data_type_index_method", "btree_integer")
    _, method = _DATA_TYPE_METHOD.get(dtim, ("integer", "btree"))
    return method


def _resolve_for_type(a: dict[str, str], p: str) -> str:
    """The FOR TYPE clause value, handling incompatible cases."""

    imc = a.get("index_method_compatibility", "compatible")
    if imc == "incompatible":
        return f"{p}badtype"
    return _resolve_data_type(a, p)


def _opclass_name(a: dict[str, str], p: str) -> str:
    """The operator class identifier in CREATE OPERATOR CLASS and fixtures."""

    shape = a.get("name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f'"{p}Qoc"'
    if shape == "schema_qualified":
        return f"public.{p}oc"
    return f"{p}oc"


def _opclass_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    shape = a.get("name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f"{p}Qoc"
    return f"{p}oc"


def _is_duplicate(a: dict[str, str]) -> bool:
    return a.get("target_object_state") in ("exists", "exists_conflict")


def _is_failure(a: dict[str, str]) -> bool:
    return a.get("expected_status") == "failure"


def _present(a: dict[str, str]) -> bool:
    """Whether the operator class exists after the target statement."""

    if not _is_failure(a):
        return True
    if _is_duplicate(a):
        return True
    return False


def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target runs."""

    priv = a.get("privilege_context", "superuser")
    if priv == "insufficient_privilege":
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    priv = a.get("privilege_context", "superuser")
    if priv == "insufficient_privilege":
        roles.append(f"{p}actor")
    return tuple(roles)


def _build_operator_entries(
    a: dict[str, str],
    p: str,
    op_name: str,
    data_type: str,
) -> list[str]:
    """Build the OPERATOR clause variant."""

    op_entry = a.get("operator_entry", "for_search")
    if op_entry == "for_search":
        return [f"OPERATOR 1 {op_name} FOR SEARCH"]
    if op_entry == "for_order_by":
        return [f"OPERATOR 1 {op_name} FOR ORDER BY {p}sortfam"]
    if op_entry == "with_op_type":
        return [
            f"OPERATOR 1 {op_name} ({data_type}, {data_type})"
        ]
    # without_op_type
    return [f"OPERATOR 1 {op_name}"]


def _build_function_entries(
    a: dict[str, str],
    fn_name: str,
    data_type: str,
) -> list[str]:
    """Build the FUNCTION clause variant."""

    fn_entry = a.get("function_entry", "with_op_type")
    if fn_entry == "with_op_type":
        return [
            f"FUNCTION 1 ({data_type}) {fn_name} "
            f"({data_type}, {data_type})"
        ]
    # without_op_type
    return [
        f"FUNCTION 1 {fn_name} ({data_type}, {data_type})"
    ]


def _build_storage_entries(
    a: dict[str, str],
    p: str,
    data_type: str,
) -> list[str]:
    """Build the STORAGE clause variant."""

    storage_entry = a.get("storage_entry", "absent")
    if storage_entry == "absent":
        return []
    return [f"STORAGE {data_type}"]


def _build_target(
    a: dict[str, str],
    p: str,
    name: str,
    data_type: str,
    index_method: str,
    op_name: str,
    fn_name: str,
    family_name: str | None,
) -> str:
    """The primary CREATE OPERATOR CLASS statement."""

    default_clause = (
        "DEFAULT " if a.get("default_clause") == "present" else ""
    )
    family_clause = f" FAMILY {family_name}" if family_name else ""
    for_type = _resolve_for_type(a, p)

    entries: list[str] = []
    entries.extend(
        _build_operator_entries(a, p, op_name, data_type)
    )
    entries.extend(
        _build_function_entries(a, fn_name, data_type)
    )
    entries.extend(_build_storage_entries(a, p, data_type))

    entries_str = ",\n  ".join(entries)
    return (
        f"CREATE OPERATOR CLASS {default_clause}{name} "
        f"FOR TYPE {for_type} USING {index_method}"
        f"{family_clause} AS\n  {entries_str};"
    )


def _probe_select(
    case: CreateOperatorClassFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only verification."""

    mode = a.get("verification_mode", "catalog_query")
    literal = _opclass_literal(a, p)

    if mode == "error_assertion":
        return None

    if mode == "effect_query":
        if _present(a):
            return (
                f"SELECT opcname AS opclass_effect "
                f"FROM pg_catalog.pg_opclass "
                f"WHERE opcname = '{literal}' "
                f"ORDER BY opcname;"
            )
        return None

    # catalog_query
    if _present(a):
        cmp_op = ">"
    else:
        cmp_op = "="
    return (
        f"SELECT count(*) {cmp_op} 0 AS opclass_state "
        f"FROM pg_catalog.pg_opclass "
        f"WHERE opcname = '{literal}' "
        f"ORDER BY count(*);"
    )


def _resolve_case(
    case: CreateOperatorClassFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix

    setup: list[str] = []
    locus = "target.create_operator_class"

    data_type = _resolve_data_type(a, p)
    index_method = _resolve_index_method(a)
    for_type = _resolve_for_type(a, p)
    name = _opclass_name(a, p)
    op_name = f"{p}op"
    opfn_name = f"{p}opfn"
    fn_name = f"{p}fn"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)

    ds = a.get("dependency_state", "ready")

    # --- role fixtures -----------------------------------------------
    if effective:
        setup.append(
            f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;"
        )
        locus = "fixture.privilege_state"

    # --- custom type (for gist) -------------------------------------
    if data_type == f"{p}geom":
        setup.append(
            f"CREATE TYPE {p}geom AS (x float8, y float8);"
        )
        locus = "fixture.custom_type"

    # --- sort family (for_order_by) ---------------------------------
    op_entry = a.get("operator_entry", "for_search")
    if op_entry == "for_order_by":
        setup.append(
            f"CREATE OPERATOR FAMILY {p}sortfam USING btree;"
        )
        locus = "fixture.sort_family"

    # --- existing family (present_existing) ------------------------
    family_name: str | None = None
    fc = a.get("family_clause", "absent_auto_created")
    if fc == "present_existing":
        family_name = f"{p}fam"
        setup.append(
            f"CREATE OPERATOR FAMILY {family_name} "
            f"USING {index_method};"
        )
        locus = "fixture.existing_family"
    elif fc == "present_missing":
        family_name = f"{p}nofam"
        locus = "fixture.missing_family"

    # --- operator procedure function (always, unless missing_function)
    fn_sig = f"({data_type}, {data_type})"
    if ds != "missing_function":
        setup.append(
            f"CREATE FUNCTION {opfn_name}{fn_sig} "
            f"RETURNS boolean AS 'SELECT $1 = $2' "
            f"LANGUAGE SQL IMMUTABLE;"
        )
        setup.append(
            f"CREATE OPERATOR {op_name} "
            f"(LEFTARG = {data_type}, RIGHTARG = {data_type}, "
            f"PROCEDURE = {opfn_name});"
        )
        locus = "fixture.operator_and_function"
    elif ds == "missing_function":
        # Create the operator with a builtin procedure so the OPERATOR
        # clause resolves, but skip the support function {fn_name}.
        builtin_fn = _builtin_proc(data_type)
        if builtin_fn:
            setup.append(
                f"CREATE OPERATOR {op_name} "
                f"(LEFTARG = {data_type}, RIGHTARG = {data_type}, "
                f"PROCEDURE = {builtin_fn});"
            )
        locus = "fixture.operator_without_support_function"

    # --- support function (unless missing_function) -----------------
    if ds != "missing_function":
        setup.append(
            f"CREATE FUNCTION {fn_name}{fn_sig} "
            f"RETURNS boolean AS 'SELECT $1 = $2' "
            f"LANGUAGE SQL IMMUTABLE;"
        )

    # --- duplicate operator class fixture ---------------------------
    if _is_duplicate(a):
        simple_target = _build_target(
            a, p, name, data_type, index_method,
            op_name, fn_name, family_name,
        )
        setup.append(simple_target)
        locus = "fixture.duplicate_opclass"

    # --- arm the effective role --------------------------------------
    if effective:
        setup.append(f"SET ROLE {effective};")

    # --- the primary target statement --------------------------------
    target = _build_target(
        a, p, name, data_type, index_method,
        op_name, fn_name, family_name,
    )

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
    cleanup_mode = a.get("cleanup_mode", "drop_objects")
    objects_to_drop: list[str] = [name]
    if family_name:
        objects_to_drop.append(family_name)
    if op_entry == "for_order_by":
        objects_to_drop.append(f"{p}sortfam")

    if cleanup_mode == "reset_state":
        opclass_drops = [
            f"DROP OPERATOR CLASS IF EXISTS {obj} CASCADE;"
            for obj in objects_to_drop
        ]
    else:
        opclass_drops = [
            f"DROP OPERATOR CLASS IF EXISTS {obj} CASCADE;"
            for obj in objects_to_drop
        ]

    fn_drops: list[str] = []
    if ds != "missing_function":
        fn_drops.append(
            f"DROP OPERATOR IF EXISTS {op_name}{fn_sig};"
        )
        fn_drops.append(
            f"DROP FUNCTION IF EXISTS {opfn_name}{fn_sig};"
        )
        fn_drops.append(
            f"DROP FUNCTION IF EXISTS {fn_name}{fn_sig};"
        )
    elif ds == "missing_function" and _builtin_proc(data_type):
        fn_drops.append(
            f"DROP OPERATOR IF EXISTS {op_name}{fn_sig};"
        )

    type_drops: list[str] = []
    if data_type == f"{p}geom":
        type_drops.append(f"DROP TYPE IF EXISTS {p}geom CASCADE;")
    if _resolve_for_type(a, p) == f"{p}badtype":
        type_drops.append(
            f"DROP TYPE IF EXISTS {p}badtype CASCADE;"
        )

    role_drops = [
        stmt
        for role in roles
        for stmt in (
            f"DROP OWNED BY {role} CASCADE;",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    # pre-cleanup: always use IF EXISTS CASCADE (safe)
    pre_cleanup: list[str] = []
    pre_cleanup.append(
        f"DROP OPERATOR CLASS IF EXISTS {name} CASCADE;"
    )
    pre_cleanup.append(
        f"DROP OPERATOR CLASS IF EXISTS {p}oc CASCADE;"
    )
    pre_cleanup.append(
        f"DROP OPERATOR FAMILY IF EXISTS {p}fam CASCADE;"
    )
    pre_cleanup.append(
        f"DROP OPERATOR FAMILY IF EXISTS {p}nofam CASCADE;"
    )
    pre_cleanup.append(
        f"DROP OPERATOR FAMILY IF EXISTS {p}sortfam CASCADE;"
    )
    pre_cleanup.append(
        f"DROP OPERATOR IF EXISTS {op_name}{fn_sig};"
    )
    pre_cleanup.append(
        f"DROP FUNCTION IF EXISTS {opfn_name}{fn_sig};"
    )
    pre_cleanup.append(
        f"DROP FUNCTION IF EXISTS {fn_name}{fn_sig};"
    )
    pre_cleanup.append(
        f"DROP TYPE IF EXISTS {p}geom CASCADE;"
    )
    pre_cleanup.append(
        f"DROP TYPE IF EXISTS {p}badtype CASCADE;"
    )
    pre_cleanup.append("RESET ROLE;")
    for role in roles:
        pre_cleanup.append(f"DROP ROLE IF EXISTS {role};")

    # cleanup: RESET ROLE, opclasses, operators, functions, types, roles
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(opclass_drops)
    cleanup.extend(fn_drops)
    cleanup.extend(type_drops)
    cleanup.extend(role_drops)

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


def _builtin_proc(data_type: str) -> str:
    """A builtin function name for the data type, or empty."""

    if data_type == "integer":
        return "int4eq"
    if data_type == "text":
        return "texteq"
    return ""


def _header(case: CreateOperatorClassFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE OPERATOR CLASS "
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


def render_create_operator_class_factor_case(
    case: CreateOperatorClassFactorCase
    | CreateOperatorClassFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 CREATE OPERATOR CLASS。")
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
    case: CreateOperatorClassFactorCase
    | CreateOperatorClassFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_operator_class_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_operator_class_factor_programs(
    baseline_plan: CreateOperatorClassFactorLoopPlan,
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


def count_primary_create_operator_class(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(
            r"(?im)^\s*CREATE\s+OPERATOR\s+CLASS\b",
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


def resolve_create_operator_class_factor_witness(
    case: CreateOperatorClassFactorCase
    | CreateOperatorClassFactorExtensionCase,
    repository_root: Path,
) -> CreateOperatorClassFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateOperatorClassFactorWitness(
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
    "CreateOperatorClassFactorRenderError",
    "CreateOperatorClassFactorWitness",
    "count_primary_create_operator_class",
    "generate_create_operator_class_factor_programs",
    "render_create_operator_class_factor_case",
    "resolve_create_operator_class_factor_witness",
    "remove_primary_semantic_locus_but_keep_comments",
]
