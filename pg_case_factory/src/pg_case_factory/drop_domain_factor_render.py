"""Render complete PostgreSQL 18.4 DROP DOMAIN factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_type ... ORDER BY count(*)``
never nests a ``FROM`` inside an ``EXISTS`` subquery, so
``audit_catalog_observability`` accepts it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .drop_domain_factor_extension import (
    DropDomainFactorExtensionCase,
)
from .drop_domain_factor_loop import (
    DropDomainFactorCase,
    DropDomainFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/domain/"
    "drop_domain.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/domain/"
    "drop_domain.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_DROP = "branch_drop_domain"

# Primary (factor, value) pairs where the target domain is intentionally
# absent, so the drop surfaces a not-found error (or a notice under IF EXISTS)
# and the oracle asserts absence.
_ABSENT_PRIMARIES = frozenset(
    {
        ("object_state", "absent"),
        ("nonexistent_domain", "domain_missing_without_if_exists"),
        ("expected_status", "failure"),
        ("domain_name_shape", "nonexistent_name"),
    }
)

# For an extension SUCCESS case (no present failure pair) the synthetic
# primary must be a neutral success primary whose helpers fall through to the
# assignment; the domain always exists in extensions (object_state held at
# exists).
_BRANCH_NEUTRAL_SUCCESS = ("object_state", "exists")


def _synthetic_case(
    ext: DropDomainFactorExtensionCase,
) -> DropDomainFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .drop_domain_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropDomainFactorCase(
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
    case: DropDomainFactorCase | DropDomainFactorExtensionCase,
) -> DropDomainFactorCase:
    if isinstance(case, DropDomainFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropDomainFactorRenderError(ValueError):
    """Raised when a DROP DOMAIN case cannot be rendered."""


@dataclass(frozen=True)
class DropDomainFactorWitness:
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


def _baseline(case: DropDomainFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _domain_name(
    case: DropDomainFactorCase, a: dict[str, str], p: str
) -> str:
    """The domain name as referenced inside DROP DOMAIN."""

    shape = a.get("domain_name_shape", "simple_id")
    if shape == "schema_qualified":
        return f"{p}schema.{p}dom"
    if shape == "quoted_id":
        return f'"{p}Quoted"'
    if shape == "reserved_word_as_name":
        return f'"{p}Reserved"'
    if shape == "nonexistent_name":
        return f"{p}nonexistent_dom"
    return f"{p}dom"


def _probe_name(
    case: DropDomainFactorCase, a: dict[str, str], p: str
) -> str:
    """The bare domain name (no quotes/schema) for the catalog probe."""

    shape = a.get("domain_name_shape", "simple_id")
    if shape == "quoted_id":
        return f"{p}Quoted"
    if shape == "reserved_word_as_name":
        return f"{p}Reserved"
    if shape == "nonexistent_name":
        return f"{p}nonexistent_dom"
    return f"{p}dom"


def _needs_schema(a: dict[str, str]) -> bool:
    return a.get("domain_name_shape") == "schema_qualified"


def _is_multi_domain(a: dict[str, str]) -> bool:
    return a.get("multi_domain") == "multiple_domains"


def _fixture_kind(case: DropDomainFactorCase) -> str:
    if case.kind == "RISK":
        return "domain"
    if (case.factor_key, case.factor_value) in _ABSENT_PRIMARIES:
        return "none"
    return "domain"


def _needs_dependent(
    case: DropDomainFactorCase, a: dict[str, str]
) -> bool:
    """Whether a dependent table-column fixture must be created."""

    hdr = a.get("has_dependents_restrict", "no_dependents_safe")
    if hdr == "dependents_block_restrict":
        return True
    dep_ctx = a.get("dependency_context", "no_dependencies")
    if dep_ctx == "column_using_domain":
        return True
    dep_stat = a.get("dependency_status", "no_dependents")
    return dep_stat in (
        "has_table_column_dependent",
        "has_other_dependent",
    )


def _if_exists_present(
    case: DropDomainFactorCase, a: dict[str, str]
) -> bool:
    """Whether the DROP DOMAIN statement carries IF EXISTS."""

    if _fixture_kind(case) == "none":
        return a.get("if_exists_clause") == "present"
    return a.get("if_exists_clause") == "present"


def _cascade_clause(a: dict[str, str]) -> str:
    cascade = a.get("cascade_restrict", "omitted_default_restrict")
    if cascade == "cascade":
        return "CASCADE"
    if cascade == "restrict":
        return "RESTRICT"
    return ""


def _effective_role(
    case: DropDomainFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP DOMAIN runs."""

    if case.kind == "EXT":
        level = a.get("privilege_level", "superuser")
        return f"{p}actor" if level == "non_owner" else ""
    if case.factor_key == "privilege_level":
        return f"{p}actor" if case.factor_value == "non_owner" else ""
    if case.factor_key == "privilege_denied":
        return (
            f"{p}actor"
            if case.factor_value == "non_owner_denied"
            else ""
        )
    return ""


def _domain_absent_after(
    case: DropDomainFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target domain is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if _fixture_kind(case) == "none":
        return True
    if case.outcome == "success":
        return True
    return False


def _probe_select(
    case: DropDomainFactorCase, a: dict[str, str], p: str
) -> str:
    name = _probe_name(case, a, p)
    absent = _domain_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "domain_absent" if absent else "domain_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_type "
        f"WHERE typname = '{name}' ORDER BY count(*) LIMIT 1;"
    )


def _role_names(
    case: DropDomainFactorCase, p: str, effective: str
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}actor":
        roles.append(f"{p}actor")
    return tuple(roles)


def _domain_list(
    case: DropDomainFactorCase, a: dict[str, str], p: str
) -> str:
    """The comma-separated domain list for DROP DOMAIN."""

    primary = _domain_name(case, a, p)
    if _is_multi_domain(a):
        return f"{primary}, {p}dom2"
    return primary


def _resolve_case(case: DropDomainFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    fixture_kind = _fixture_kind(case)
    dom_ref = _domain_name(case, a, p)
    needs_schema = _needs_schema(a)
    needs_dep = _needs_dependent(case, a)
    multi = _is_multi_domain(a)

    setup: list[str] = []
    locus = "target.domain"

    # --- schema fixture -------------------------------------------------
    if needs_schema:
        setup.append(f"CREATE SCHEMA IF NOT EXISTS {p}schema;")

    # --- role fixtures (CREATE only; SET ROLE deferred) ---
    effective = _effective_role(case, a, p)
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        if needs_schema:
            setup.append(
                f"GRANT USAGE ON SCHEMA {p}schema TO {p}actor;"
            )
        locus = "fixture.privilege_state"

    # --- the target domain fixture (as superuser, before SET ROLE) -------
    if fixture_kind == "domain":
        setup.append(
            f"CREATE DOMAIN {dom_ref} AS integer NOT NULL;"
        )
        if multi:
            setup.append(
                f"CREATE DOMAIN {p}dom2 AS integer NOT NULL;"
            )
    else:
        setup.append(
            "SELECT 1 AS target_domain_intentionally_absent;"
        )
        locus = "fixture.object_state"

    # --- dependent table-column fixture (as superuser) ------------------
    if needs_dep:
        setup.append(f"CREATE TABLE {p}t (c {dom_ref});")
        locus = "fixture.dependency_state"

    # --- arm the non-superuser role (AFTER domain creation) -------------
    if effective:
        setup.append(f"SET ROLE {p}actor;")
    if_exists = "IF EXISTS " if _if_exists_present(case, a) else ""
    cascade = _cascade_clause(a)
    dom_list = _domain_list(case, a, p)
    target = f"DROP DOMAIN {if_exists}{dom_list}"
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
    cleanup_mode = a.get("cleanup_mode", "drop_domain")
    if case.factor_key == "cleanup_mode":
        cleanup_mode = case.factor_value
    dom_cleanup = f"DROP DOMAIN IF EXISTS {dom_ref} CASCADE;"
    dom2_cleanup = (
        f"DROP DOMAIN IF EXISTS {p}dom2 CASCADE;" if multi else ""
    )
    roles = _role_names(case, p, effective)
    schema_drop = (
        [f"DROP SCHEMA IF EXISTS {p}schema CASCADE;"] if needs_schema else []
    )
    dep_drops = (
        [f"DROP TABLE IF EXISTS {p}t CASCADE;"] if needs_dep else []
    )
    role_drops = [
        statement
        for role in roles
        for statement in (
            f"DROP OWNED BY {role};",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    # Pre-cleanup: DROP TABLE first (table audit requires it as the first
    # executable statement / bookend gate), then domains, schema, roles.
    pre_cleanup: list[str] = []
    pre_cleanup.extend(dep_drops)
    pre_cleanup.append(dom_cleanup)
    if dom2_cleanup:
        pre_cleanup.append(dom2_cleanup)
    pre_cleanup.extend(schema_drop)
    pre_cleanup.extend(
        f"DROP ROLE IF EXISTS {role};" for role in roles
    )
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # Cleanup: RESET ROLE, then domain/table/schema/role drops, then DROP
    # TABLE last (the table audit requires the final executable statement
    # to be DROP TABLE IF EXISTS for scripts that create tables / bookend).
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.append(dom_cleanup)
    if dom2_cleanup:
        cleanup.append(dom2_cleanup)
    cleanup.extend(schema_drop)
    cleanup.extend(role_drops)
    cleanup.extend(dep_drops)
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


def resolve_drop_domain_factor_witness(
    case: DropDomainFactorCase | DropDomainFactorExtensionCase,
    repository_root: Path,
) -> DropDomainFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropDomainFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_domain(sql: str) -> int:
    """Count the single credited DROP DOMAIN inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*DROP\s+DOMAIN\b", region)
    )


def _header(case: DropDomainFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP DOMAIN {case.factor_key}={case.factor_value}",
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


def render_drop_domain_factor_case(
    case: DropDomainFactorCase | DropDomainFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP DOMAIN regress program."""

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地域和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP DOMAIN。")
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


def generate_drop_domain_factor_programs(
    baseline_plan: DropDomainFactorLoopPlan,
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
    case: DropDomainFactorCase | DropDomainFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_domain_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropDomainFactorRenderError",
    "DropDomainFactorWitness",
    "count_primary_drop_domain",
    "generate_drop_domain_factor_programs",
    "render_drop_domain_factor_case",
    "resolve_drop_domain_factor_witness",
]
