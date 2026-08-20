"""Render complete PostgreSQL 18.4 DROP CONVERSION factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_conversion ... ORDER BY count(*)``
never nests a ``FROM`` inside an ``EXISTS`` subquery, so
``audit_catalog_observability`` accepts it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .drop_conversion_factor_extension import (
    DropConversionFactorExtensionCase,
)
from .drop_conversion_factor_loop import (
    DropConversionFactorCase,
    DropConversionFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/conversion/"
    "drop_conversion.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/conversion/"
    "drop_conversion.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

# Primary (factor, value) pairs where the target conversion is intentionally
# absent, so the drop surfaces a not-found error (or a notice under IF EXISTS)
# and the oracle asserts absence.
_ABSENT_PRIMARIES = frozenset(
    {
        ("object_state", "not_exists"),
        ("conversion_not_exist", "conversion_not_exists"),
        ("conversion_name_shape", "nonexistent_name"),
        ("nonexistent_name", "nonexistent_conversion_name"),
        ("expected_status", "failure"),
    }
)

# For an extension SUCCESS case (no present failure pair) the synthetic
# primary must be a neutral success primary whose helpers fall through to the
# assignment; the conversion always exists in extensions (object_state held at
# exists).
_BRANCH_NEUTRAL_SUCCESS = ("object_state", "exists")


def _synthetic_case(
    ext: DropConversionFactorExtensionCase,
) -> DropConversionFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .drop_conversion_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropConversionFactorCase(
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
    case: DropConversionFactorCase | DropConversionFactorExtensionCase,
) -> DropConversionFactorCase:
    if isinstance(case, DropConversionFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropConversionFactorRenderError(ValueError):
    """Raised when a DROP CONVERSION case cannot be rendered."""


@dataclass(frozen=True)
class DropConversionFactorWitness:
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


def _baseline(case: DropConversionFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _conv_name(case: DropConversionFactorCase, a: dict[str, str], p: str) -> str:
    """The conversion name as referenced inside DROP CONVERSION."""

    shape = a.get("conversion_name_shape", "simple_id")
    if shape == "quoted_id":
        return f'"{p}QuotedConv"'
    if shape == "schema_qualified":
        return f"{p}schema.{p}conv"
    if shape == "nonexistent_name":
        return f"{p}nonexistent_conv"
    return f"{p}conv"


def _probe_name(case: DropConversionFactorCase, a: dict[str, str], p: str) -> str:
    """The bare conname (no quotes/schema) for the catalog probe."""

    shape = a.get("conversion_name_shape", "simple_id")
    if shape == "quoted_id":
        return f"{p}QuotedConv"
    if shape == "nonexistent_name":
        return f"{p}nonexistent_conv"
    return f"{p}conv"


def _needs_schema(a: dict[str, str]) -> bool:
    return a.get("conversion_name_shape") == "schema_qualified"


def _fixture_kind(case: DropConversionFactorCase, a: dict[str, str]) -> str:
    """Whether a conversion fixture must be created."""

    if case.kind == "RISK":
        return "conversion"
    if (case.factor_key, case.factor_value) in _ABSENT_PRIMARIES:
        return "none"
    if case.kind == "EXT":
        if a.get("conversion_not_exist") == "conversion_not_exists":
            return "none"
        if a.get("conversion_name_shape") == "nonexistent_name":
            return "none"
        if (
            a.get("schema_existence") == "schema_not_exists"
            and a.get("conversion_name_shape") == "schema_qualified"
        ):
            return "none"
    return "conversion"


def _if_exists_present(
    case: DropConversionFactorCase, a: dict[str, str]
) -> bool:
    return a.get("if_exists_clause") == "specified_if_exists"


def _cascade_clause(a: dict[str, str]) -> str:
    cascade = a.get("cascade_restrict", "omitted")
    if cascade == "cascade":
        return "CASCADE"
    if cascade == "restrict":
        return "RESTRICT"
    return ""


def _effective_role(
    case: DropConversionFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP CONVERSION runs."""

    if case.kind == "EXT":
        level = a.get("privilege_level", "superuser")
        return f"{p}actor" if level == "non_owner" else ""
    if case.factor_key == "privilege_level":
        return f"{p}actor" if case.factor_value == "non_owner" else ""
    if case.factor_key == "conversion_ownership":
        return f"{p}actor" if case.factor_value == "is_not_owner" else ""
    if case.factor_key == "privilege_denied":
        return f"{p}actor" if case.factor_value == "non_owner_failure" else ""
    return ""


def _conv_absent_after(
    case: DropConversionFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target conversion is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if _fixture_kind(case, a) == "none":
        return True
    if case.outcome == "success":
        return True
    return False


def _probe_select(
    case: DropConversionFactorCase, a: dict[str, str], p: str
) -> str:
    name = _probe_name(case, a, p)
    absent = _conv_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "conversion_absent" if absent else "conversion_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_conversion "
        f"WHERE conname = '{name}' ORDER BY count(*) LIMIT 1;"
    )


def _role_names(
    case: DropConversionFactorCase, p: str, effective: str
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}actor":
        roles.append(f"{p}actor")
    return tuple(roles)


def _resolve_case(case: DropConversionFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    fixture_kind = _fixture_kind(case, a)
    conv_ref = _conv_name(case, a, p)
    needs_schema = _needs_schema(a)

    setup: list[str] = []
    locus = "target.conversion"

    # --- schema fixture -------------------------------------------------
    if needs_schema:
        setup.append(f"CREATE SCHEMA IF NOT EXISTS {p}schema;")

    # --- role fixtures (CREATE only; SET ROLE deferred to after the
    # conversion fixture so they run as the superuser) ---
    effective = _effective_role(case, a, p)
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- the target conversion fixture (as superuser, before SET ROLE) -
    if fixture_kind == "conversion":
        setup.append(
            f"CREATE CONVERSION {conv_ref} "
            f"FOR 'LATIN1' TO 'UTF8' FROM {p}convfn;"
        )
    else:
        setup.append("SELECT 1 AS target_conversion_intentionally_absent;")
        locus = "fixture.object_state"

    # --- arm the non-superuser role (AFTER conversion creation) -------
    if effective:
        setup.append(f"SET ROLE {p}actor;")
    if_exists = "IF EXISTS " if _if_exists_present(case, a) else ""
    cascade = _cascade_clause(a)
    target = f"DROP CONVERSION {if_exists}{conv_ref}"
    if cascade:
        target += f" {cascade}"
    target += ";"

    # RISK transaction wrapper around the target.
    if case.kind == "RISK":
        setup.append("BEGIN;")
        locus = "target.transaction_boundary"

    # --- oracle / SQLSTATE assertion ------------------------------------
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

    # --- cleanup construction -------------------------------------------
    conv_drop = f"DROP CONVERSION IF EXISTS {conv_ref};"
    roles = _role_names(case, p, effective)
    schema_drop = (
        [f"DROP SCHEMA IF EXISTS {p}schema CASCADE;"] if needs_schema else []
    )

    # Pre-cleanup: conversion first, then schema, then roles.
    pre_cleanup: list[str] = []
    pre_cleanup.append(conv_drop)
    pre_cleanup.extend(schema_drop)
    pre_cleanup.extend(f"DROP ROLE IF EXISTS {role};" for role in roles)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # Cleanup: RESET ROLE, then conversion/schema/role drops.
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.append(conv_drop)
    cleanup.extend(schema_drop)
    cleanup.extend(role_drops for role in roles for role_drops in (
        f"DROP OWNED BY {role};",
        f"DROP ROLE IF EXISTS {role};",
    ))
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


def resolve_drop_conversion_factor_witness(
    case: DropConversionFactorCase | DropConversionFactorExtensionCase,
    repository_root: Path,
) -> DropConversionFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropConversionFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_conversion(sql: str) -> int:
    """Count the single credited DROP CONVERSION inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*DROP\s+CONVERSION\b", region)
    )


def _header(case: DropConversionFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP CONVERSION {case.factor_key}={case.factor_value}",
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


def render_drop_conversion_factor_case(
    case: DropConversionFactorCase | DropConversionFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP CONVERSION regress program."""

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地转换和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP CONVERSION。")
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


def generate_drop_conversion_factor_programs(
    baseline_plan: DropConversionFactorLoopPlan,
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
    case: DropConversionFactorCase | DropConversionFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_conversion_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropConversionFactorRenderError",
    "DropConversionFactorWitness",
    "count_primary_drop_conversion",
    "generate_drop_conversion_factor_programs",
    "render_drop_conversion_factor_case",
    "resolve_drop_conversion_factor_witness",
]
