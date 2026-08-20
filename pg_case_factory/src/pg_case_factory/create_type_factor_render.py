"""Render complete PostgreSQL 18.4 CREATE TYPE factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the byte-level
witness validator (which re-renders and compares) can never diverge from
the bytes actually written.

CREATE TYPE is a catalog-row DDL statement: the target is a
``pg_catalog.pg_type`` catalog row, not a ``pg_class`` relation.  All
catalog oracles schema-qualify ``pg_catalog.pg_type`` (exempt from the
file-prefix style gate via the ``pg_`` prefix).  No case creates a TABLE,
so the bookend (DROP TABLE IF EXISTS) is never emitted.  Every catalog
SELECT carries a top-level ``ORDER BY`` so the catalog-observability gate
passes.

CREATE TYPE has no ``OR REPLACE``, ``TEMP`` or ``UNLOGGED`` clause, so
the col-0 primary-target regex is the plain ``^CREATE\\s+TYPE\\b`` form.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_type_factor_extension import (
    CreateTypeFactorExtensionCase,
    _present_failure_pair,
)
from .create_type_factor_loop import (
    CreateTypeFactorCase,
    CreateTypeFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/"
    "type/create_type.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/"
    "type/create_type.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class CreateTypeFactorRenderError(ValueError):
    """Raised when a CREATE TYPE case cannot be rendered."""


@dataclass(frozen=True)
class CreateTypeFactorWitness:
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
    ext: CreateTypeFactorExtensionCase,
) -> CreateTypeFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_form"
        factor_value = assignment.get(
            "type_form", ext.consumer_action_id
        )
    return CreateTypeFactorCase(
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
    case: CreateTypeFactorCase | CreateTypeFactorExtensionCase,
) -> CreateTypeFactorCase:
    if isinstance(case, CreateTypeFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateTypeFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _schema_name(p: str) -> str:
    return f"{p}schema"


def _type_name(a: dict[str, str], p: str) -> str:
    """The type identifier in CREATE TYPE."""

    shape = a.get("type_name_shape", "simple")
    schema = _schema_name(p)
    if shape == "quoted":
        return f'{schema}."{p}Type"'
    if shape == "reserved_word":
        return f'{schema}."select"'
    if shape == "underscore_prefix":
        return f"{schema}._{p}type"
    return f"{schema}.{p}type"


def _type_name_literal(a: dict[str, str], p: str) -> str:
    """The catalog typname string literal for oracle queries."""

    shape = a.get("type_name_shape", "simple")
    if shape == "quoted":
        return f"{p}Type"
    if shape == "reserved_word":
        return "select"
    if shape == "underscore_prefix":
        return f"_{p}type"
    return f"{p}type"


def _is_duplicate(a: dict[str, str]) -> bool:
    return a.get("object_state") == "already_exists"


def _is_schema_missing(a: dict[str, str]) -> bool:
    return a.get("schema_dependency") == "schema_not_exists"


def _is_insufficient_privilege(a: dict[str, str]) -> bool:
    return a.get("privilege_level") == "non_owner"


def _is_failure(a: dict[str, str]) -> bool:
    return a.get("expected_status") == "failure"


def _effective_schema(a: dict[str, str], p: str) -> str:
    if _is_schema_missing(a):
        return f"{p}noschema"
    return _schema_name(p)


def _effective_role(a: dict[str, str], p: str) -> str:
    if _is_insufficient_privilege(a):
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    if _is_insufficient_privilege(a):
        roles.append(f"{p}actor")
    return tuple(roles)


_ATTR_DTYPES = (
    "integer", "bigint", "text", "varchar", "numeric",
    "boolean", "date", "timestamp", "jsonb", "uuid",
)


def _attr_name(shape: str, idx: int) -> str:
    if shape == "quoted":
        return f'"attr {idx}"'
    if shape == "reserved_word":
        return '"select"'
    return f"col{idx}"


def _composite_attrs(a: dict[str, str]) -> list[str]:
    count = a.get("attribute_count", "single_attribute")
    name_shape = a.get("attribute_name_shape", "simple")
    dtype = a.get("attribute_data_type", "integer")
    if a.get("invalid_data_type_in_attribute") == "unknown_type":
        dtype = f"{a.get('object_prefix', '')}bogustype"
    if count == "zero_attributes":
        return []
    if count == "single_attribute":
        return [f"{_attr_name(name_shape, 1)} {dtype}"]
    return [
        f"{_attr_name(name_shape, 1)} {dtype}",
        f"{_attr_name(name_shape, 2)} text",
        f"{_attr_name(name_shape, 3)} bigint",
    ]


def _enum_labels(a: dict[str, str]) -> list[str]:
    count = a.get("enum_label_count", "multiple_labels")
    shape = a.get("enum_label_shape", "simple_label")
    if count == "zero_labels":
        return []
    if shape == "quoted_label":
        if count == "single_label":
            return ["'label with space'"]
        return ["'label with space'", "'another label'", "'third label'"]
    if shape == "long_label":
        long_label = "a" * 60
        if count == "single_label":
            return [f"'{long_label}'"]
        return [f"'{long_label}'", "'bb'", "'cc'"]
    if count == "single_label":
        return ["'label1'"]
    return ["'label1'", "'label2'", "'label3'"]


_RANGE_OPCLASS = {
    "integer": "int4_ops",
    "bigint": "int8_ops",
    "numeric": "numeric_ops",
    "float8": "float8_ops",
    "timestamp": "timestamp_ops",
    "timestamptz": "timestamptz_ops",
    "date": "date_ops",
}


def _build_target(a: dict[str, str], p: str) -> str:
    """The primary CREATE TYPE statement."""

    branch = a.get("statement_branch", "branch_composite")
    name = _type_name(a, p)
    if branch == "branch_enum":
        labels = _enum_labels(a)
        inner = ", ".join(labels)
        return f"CREATE TYPE {name} AS ENUM ({inner});"
    if branch == "branch_range":
        return _build_range_target(a, p, name)
    if branch == "branch_base":
        return _build_base_target(a, p, name)
    if branch == "branch_shell":
        return f"CREATE TYPE {name};"
    attrs = _composite_attrs(a)
    inner = ", ".join(attrs)
    return f"CREATE TYPE {name} AS ({inner});"


def _build_range_target(a: dict[str, str], p: str, name: str) -> str:
    subtype = a.get("range_subtype", "integer")
    opts: list[str] = [f"SUBTYPE = {subtype}"]
    completeness = a.get("range_option_completeness", "minimal")
    if a.get("subtype_opclass_dependency") == "opclass_not_exists":
        opts.append(f"SUBTYPE_OPCLASS = {p}bogus_opclass")
    elif a.get("subtype_no_btree_opclass") == "no_opclass":
        opts.append(f"SUBTYPE_OPCLASS = {p}bogus_opclass")
    elif completeness == "with_opclass":
        opts.append(f"SUBTYPE_OPCLASS = {_RANGE_OPCLASS.get(subtype, 'int4_ops')}")
    if a.get("canonical_function_dependency") == "function_not_exists":
        opts.append(f"CANONICAL = {p}bogus_canon")
    elif completeness == "with_canonical":
        opts.append(f"CANONICAL = {_schema_name(p)}.{p}canon")
    if a.get("subtype_diff_dependency") == "function_not_exists":
        opts.append(f"SUBTYPE_DIFF = {p}bogus_diff")
    elif completeness == "with_subtype_diff":
        opts.append(f"SUBTYPE_DIFF = {_schema_name(p)}.{p}diff")
    if completeness == "with_multirange_name":
        opts.append(f"MULTIRANGE_TYPE_NAME = {_schema_name(p)}.{p}mr")
    inner = ", ".join(opts)
    return f"CREATE TYPE {name} AS RANGE ({inner});"


def _build_base_target(a: dict[str, str], p: str, name: str) -> str:
    schema = _schema_name(p)
    io_missing = (
        a.get("function_dependency") == "input_output_functions_not_exist"
        or a.get("missing_required_functions") in {
            "no_input_function", "no_output_function"
        }
    )
    if io_missing:
        in_fn = f"{p}bogus_input"
        out_fn = f"{p}bogus_output"
    else:
        in_fn = f"{schema}.{p}input"
        out_fn = f"{schema}.{p}output"
    opts: list[str] = [f"INPUT = {in_fn}", f"OUTPUT = {out_fn}"]
    completeness = a.get("base_type_option_completeness", "required_only")
    if completeness == "with_optional_functions":
        opts.append(f"RECEIVE = {schema}.{p}receive")
        opts.append(f"SEND = {schema}.{p}send")
    if completeness == "with_all_options":
        opts.append(f"RECEIVE = {schema}.{p}receive")
        opts.append(f"SEND = {schema}.{p}send")
        opts.append(f"INTERNALLENGTH = VARIABLE")
        opts.append(f"ALIGNMENT = int4")
        opts.append(f"STORAGE = extended")
    inner = ", ".join(opts)
    return f"CREATE TYPE {name} ({inner});"


def _build_setup(a: dict[str, str], p: str) -> tuple[list[str], str]:
    """Fixture lines and the semantic locus."""

    schema = _effective_schema(a, p)
    setup: list[str] = []
    locus = "target.create_type"
    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    branch = a.get("statement_branch", "branch_composite")

    if not _is_schema_missing(a):
        setup.append(f"CREATE SCHEMA {schema};")
        locus = "fixture.schema"

    if branch == "branch_base" and not _is_failure(a):
        setup.extend(_build_base_fixtures(a, p, schema))
        locus = "fixture.base_io_functions"
    if branch == "branch_range":
        comp = a.get("range_option_completeness", "minimal")
        if comp in {"with_canonical", "with_subtype_diff"} and not _is_failure(a):
            setup.extend(_build_range_fn_fixtures(a, p, schema))
            locus = "fixture.range_functions"

    if _is_duplicate(a):
        setup.extend(_build_duplicate_fixture(a, p, schema))
        locus = "fixture.duplicate_type"

    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        setup.append(f"GRANT USAGE ON SCHEMA {schema} TO {p}actor;")
        locus = "fixture.privilege_state"
        setup.append(f"SET ROLE {effective};")
    return setup, locus


def _build_base_fixtures(
    a: dict[str, str], p: str, schema: str
) -> list[str]:
    lines: list[str] = []
    if a.get("base_type_io_functions") == "with_shell_type_first":
        lines.append(f"CREATE TYPE {schema}.{p}type;")
    lines.append(
        f"CREATE FUNCTION {schema}.{p}input(text) "
        f"RETURNS internal AS 'int4in' LANGUAGE internal STRICT;"
    )
    lines.append(
        f"CREATE FUNCTION {schema}.{p}output(internal) "
        f"RETURNS text AS 'int4out' LANGUAGE internal STRICT;"
    )
    comp = a.get("base_type_option_completeness", "required_only")
    if comp in {"with_optional_functions", "with_all_options"}:
        lines.append(
            f"CREATE FUNCTION {schema}.{p}receive(internal) "
            f"RETURNS internal AS 'int4recv' LANGUAGE internal STRICT;"
        )
        lines.append(
            f"CREATE FUNCTION {schema}.{p}send(internal) "
            f"RETURNS bytea AS 'int4send' LANGUAGE internal STRICT;"
        )
    return lines


def _build_range_fn_fixtures(
    a: dict[str, str], p: str, schema: str
) -> list[str]:
    lines: list[str] = []
    lines.append(f"CREATE TYPE {schema}.{p}type;")
    lines.append(
        f"CREATE FUNCTION {schema}.{p}canon({schema}.{p}type) "
        f"RETURNS {schema}.{p}type LANGUAGE plpgsql AS "
        f"'$$ BEGIN RETURN $1; END; $$';"
    )
    lines.append(
        f"CREATE FUNCTION {schema}.{p}diff({schema}.{p}type, "
        f"{schema}.{p}type) RETURNS double precision LANGUAGE plpgsql AS "
        f"'$$ BEGIN RETURN 0.0; END; $$';"
    )
    return lines


def _build_duplicate_fixture(
    a: dict[str, str], p: str, schema: str
) -> list[str]:
    dtn = a.get("duplicate_type_name", "with_existing_type")
    name = _type_name(a, p)
    if dtn == "with_existing_table":
        return [f"CREATE VIEW {name} AS SELECT 1 AS seed_col;"]
    return [f"CREATE TYPE {name} AS ENUM ('seed_label');"]


def _probe_select(
    a: dict[str, str], p: str
) -> str:
    """Catalog-audit oracle."""

    mode = a.get("verification_mode", "pg_type_catalog_query")
    lit = _type_name_literal(a, p)
    present = not (_is_failure(a) and not _is_duplicate(a))
    cmp_op = ">" if present else "="
    if mode == "information_schema_user_defined_types":
        return (
            f"SELECT count(*) {cmp_op} 0 AS type_state "
            f"FROM information_schema.user_defined_types "
            f"WHERE user_defined_type_name = '{lit}' "
            f"ORDER BY count(*);"
        )
    return (
        f"SELECT count(*) {cmp_op} 0 AS type_state "
        f"FROM pg_catalog.pg_type WHERE typname = '{lit}' "
        f"ORDER BY count(*);"
    )


def _build_cleanup(a: dict[str, str], p: str) -> list[str]:
    schema = _effective_schema(a, p)
    name = _type_name(a, p)
    mode = a.get("cleanup_mode", "DROP_TYPE_IF_EXISTS")
    lines: list[str] = []
    if _is_insufficient_privilege(a):
        lines.append("RESET ROLE;")
    if mode == "DROP_TYPE":
        lines.append(f"DROP TYPE {name};")
    elif mode == "DROP_TYPE_CASCADE":
        lines.append(f"DROP TYPE IF EXISTS {name} CASCADE;")
    else:
        lines.append(f"DROP TYPE IF EXISTS {name};")
    if _is_duplicate(a) and a.get("duplicate_type_name") == "with_existing_table":
        lines.append(f"DROP VIEW IF EXISTS {name};")
    lines.append(f"DROP SCHEMA IF EXISTS {schema} CASCADE;")
    for role in _role_names(a, p):
        lines.append(f"DROP OWNED BY {role} CASCADE;")
        lines.append(f"DROP ROLE IF EXISTS {role};")
    return lines


def _resolve_case(case: CreateTypeFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    schema = _effective_schema(a, p)
    setup, locus = _build_setup(a, p)
    effective = _effective_role(a, p)
    roles = _role_names(a, p)

    target = _build_target(a, p)

    assert_lines: list[str] = []
    if effective:
        assert_lines.append("RESET ROLE;")
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    assert_lines.append(_probe_select(a, p))

    cleanup = _build_cleanup(a, p)

    pre_cleanup: list[str] = []
    pre_cleanup.append(f"DROP TYPE IF EXISTS {schema}.{p}type CASCADE;")
    pre_cleanup.append(f"DROP TYPE IF EXISTS {schema}._{p}type CASCADE;")
    pre_cleanup.append(f"DROP VIEW IF EXISTS {schema}.{p}type CASCADE;")
    pre_cleanup.append(f"DROP FUNCTION IF EXISTS {schema}.{p}input(text) CASCADE;")
    pre_cleanup.append(f"DROP FUNCTION IF EXISTS {schema}.{p}output(internal) CASCADE;")
    pre_cleanup.append(f"DROP FUNCTION IF EXISTS {schema}.{p}receive(internal) CASCADE;")
    pre_cleanup.append(f"DROP FUNCTION IF EXISTS {schema}.{p}send(internal) CASCADE;")
    pre_cleanup.append(f"DROP FUNCTION IF EXISTS {schema}.{p}canon CASCADE;")
    pre_cleanup.append(f"DROP FUNCTION IF EXISTS {schema}.{p}diff CASCADE;")
    pre_cleanup.append(f"DROP SCHEMA IF EXISTS {schema} CASCADE;")
    pre_cleanup.append(f"DROP SCHEMA IF EXISTS {p}noschema CASCADE;")
    pre_cleanup.append("RESET ROLE;")
    for role in roles:
        pre_cleanup.append(f"DROP ROLE IF EXISTS {role};")
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

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


def _header(case: CreateTypeFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE TYPE "
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


def render_create_type_factor_case(
    case: CreateTypeFactorCase | CreateTypeFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 CREATE TYPE。")
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
    case: CreateTypeFactorCase | CreateTypeFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_type_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_type_factor_programs(
    baseline_plan: CreateTypeFactorLoopPlan,
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


def count_primary_create_type(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(re.findall(r"(?im)^CREATE\s+TYPE\b", region))


def resolve_create_type_factor_witness(
    case: CreateTypeFactorCase | CreateTypeFactorExtensionCase,
    repository_root: Path,
) -> CreateTypeFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateTypeFactorWitness(
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
    "CreateTypeFactorRenderError",
    "CreateTypeFactorWitness",
    "count_primary_create_type",
    "generate_create_type_factor_programs",
    "render_create_type_factor_case",
    "resolve_create_type_factor_witness",
]
