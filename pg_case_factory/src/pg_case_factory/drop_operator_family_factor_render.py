"""Render complete PostgreSQL 18.4 DROP OPERATOR FAMILY factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_opfamily ... ORDER BY count(*)``
never nests a ``FROM`` inside an ``EXISTS`` subquery, so
``audit_catalog_observability`` accepts it.  The ``pg_opfamily`` columns used
are the real PG18 catalog columns ``opfname`` (name match); ``opfmethod`` is
the index-method OID but the no-DB probe matches by name only.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .drop_operator_family_factor_extension import (
    DropOperatorFamilyFactorExtensionCase,
)
from .drop_operator_family_factor_loop import (
    DropOperatorFamilyFactorCase,
    DropOperatorFamilyFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/operator_family/"
    "drop_operator_family.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/operator_family/"
    "drop_operator_family.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

# Primary (factor, value) pairs where the target operator family is
# intentionally absent, so the drop surfaces a not-found error (or a notice
# under IF EXISTS) and the oracle asserts absence.
_ABSENT_PRIMARIES = frozenset(
    {
        ("target_object_state", "missing"),
        ("expected_status", "failure"),
    }
)

# Baseline primaries that imply a dependent object fixture must be created.
# A contained operator class (with a hosting table + index) blocks
# DROP OPERATOR FAMILY RESTRICT (2BP01).
_DEPENDENCY_PRIMARIES = frozenset(
    {
        ("dependency_state", "has_dependents"),
        ("contained_opclass_state", "has_contained_opclass"),
        ("contained_opclass_state", "contained_opclass_with_dependents"),
        ("target_object_state", "exists_with_dependents"),
        ("target_object_state", "exists_with_contained_opclass"),
    }
)

_DEPENDENT_OBJECT_STATES = frozenset(
    {"exists_with_dependents", "exists_with_contained_opclass"}
)
_DEPENDENT_OPCLASS_STATES = frozenset(
    {"has_contained_opclass", "contained_opclass_with_dependents"}
)

# For an extension SUCCESS case (no present failure pair) the synthetic
# primary must be a neutral success primary whose helpers fall through to the
# assignment; the family always exists in extensions (object_state held at
# exists unless the crossed axis sets missing, which is a failure boundary).
_BRANCH_NEUTRAL_SUCCESS = ("target_object_state", "exists")


def _synthetic_case(
    ext: DropOperatorFamilyFactorExtensionCase,
) -> DropOperatorFamilyFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .drop_operator_family_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropOperatorFamilyFactorCase(
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
    case: DropOperatorFamilyFactorCase | DropOperatorFamilyFactorExtensionCase,
) -> DropOperatorFamilyFactorCase:
    if isinstance(case, DropOperatorFamilyFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropOperatorFamilyFactorRenderError(ValueError):
    """Raised when a DROP OPERATOR FAMILY case cannot be rendered."""


@dataclass(frozen=True)
class DropOperatorFamilyFactorWitness:
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


def _baseline(case: DropOperatorFamilyFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _family_name(case: DropOperatorFamilyFactorCase, a: dict[str, str], p: str) -> str:
    """The operator family name as referenced inside DROP OPERATOR FAMILY."""

    shape = a.get("name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f'"{p}opf"'
    if shape == "schema_qualified":
        return f"public.{p}opf"
    return f"{p}opf"


def _probe_name(case: DropOperatorFamilyFactorCase, a: dict[str, str], p: str) -> str:
    """The bare opfname (no quotes/schema) for the catalog probe."""

    return f"{p}opf"


def _opclass_name(p: str) -> str:
    return f"{p}opc"


def _methods(case: DropOperatorFamilyFactorCase, a: dict[str, str]) -> tuple[str, str]:
    """Return (create_method, drop_method).

    For invalid_combination=syntax_valid_semantic_error the family is created
    with btree but dropped with hash, surfacing a method-mismatch 42704.
    """

    method = a.get("index_method_shape", "btree")
    if a.get("invalid_combination") == "syntax_valid_semantic_error":
        return ("btree", "hash")
    return (method, method)


def _fixture_kind(
    case: DropOperatorFamilyFactorCase, a: dict[str, str]
) -> str:
    """Whether an operator family fixture must be created."""

    if case.kind == "RISK":
        return "operator_family"
    if case.kind == "EXT":
        return (
            "none" if a.get("target_object_state") == "missing"
            else "operator_family"
        )
    if (case.factor_key, case.factor_value) in _ABSENT_PRIMARIES:
        return "none"
    return "operator_family"


def _if_exists_present(
    case: DropOperatorFamilyFactorCase, a: dict[str, str]
) -> bool:
    return a.get("if_exists_clause") == "present"


def _cascade_clause(a: dict[str, str]) -> str:
    cascade = a.get("cascade_clause", "restrict_default")
    if cascade == "cascade":
        return "CASCADE"
    if cascade == "restrict_explicit":
        return "RESTRICT"
    return ""  # restrict_default: RESTRICT is the default


def _effective_role(
    case: DropOperatorFamilyFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP OPERATOR FAMILY runs."""

    if case.kind == "EXT":
        level = a.get("privilege_context", "superuser")
        return f"{p}actor" if level in {"non_owner", "insufficient_privilege"} else ""
    if case.factor_key == "privilege_context":
        return (
            f"{p}actor"
            if case.factor_value in {"non_owner", "insufficient_privilege"}
            else ""
        )
    if case.factor_key == "ownership_boundary":
        return f"{p}actor" if case.factor_value == "non_owner" else ""
    return ""


def _has_dependents_present(a: dict[str, str]) -> bool:
    return (
        a.get("dependency_state") == "has_dependents"
        or a.get("contained_opclass_state") in _DEPENDENT_OPCLASS_STATES
        or a.get("target_object_state") in _DEPENDENT_OBJECT_STATES
    )


def _needs_dependent(
    case: DropOperatorFamilyFactorCase, a: dict[str, str]
) -> bool:
    """Whether a dependent object fixture must be created."""

    if case.kind == "EXT":
        return _has_dependents_present(a)
    if (case.factor_key, case.factor_value) in _DEPENDENCY_PRIMARIES:
        return True
    return _has_dependents_present(a)


def _family_absent_after(
    case: DropOperatorFamilyFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target family is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if _fixture_kind(case, a) == "none":
        return True
    if case.outcome == "success":
        return True
    return False


def _probe_select(
    case: DropOperatorFamilyFactorCase, a: dict[str, str], p: str
) -> str:
    name = _probe_name(case, a, p)
    absent = _family_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "family_absent" if absent else "family_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_opfamily "
        f"WHERE opfname = '{name}' ORDER BY count(*) LIMIT 1;"
    )


def _role_names(
    case: DropOperatorFamilyFactorCase, p: str, effective: str
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}actor":
        roles.append(f"{p}actor")
    return tuple(roles)


def _resolve_case(case: DropOperatorFamilyFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    fixture_kind = _fixture_kind(case, a)
    fam_ref = _family_name(case, a, p)
    opc = _opclass_name(p)
    create_method, drop_method = _methods(case, a)
    needs_dep = _needs_dependent(case, a)

    setup: list[str] = []
    locus = "target.operator_family"

    # --- role fixtures (CREATE only; SET ROLE deferred to after the
    # operator family fixture so they run as the superuser) ---
    effective = _effective_role(case, a, p)
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- the target operator family fixture (as superuser, before SET ROLE) -
    if fixture_kind == "operator_family":
        setup.append(
            f"CREATE OPERATOR FAMILY {fam_ref} USING {create_method};"
        )
    else:
        setup.append(
            "SELECT 1 AS target_operator_family_intentionally_absent;"
        )
        locus = "fixture.object_state"

    # --- dependent object fixture (as superuser, before SET ROLE) -------
    if needs_dep:
        setup.append(
            f"CREATE OPERATOR CLASS {opc} FOR integer "
            f"USING {create_method} FAMILY {fam_ref} AS STORAGE integer;"
        )
        setup.append(f"CREATE TABLE {p}t (c integer);")
        setup.append(
            f"CREATE INDEX {p}idx ON {p}t USING {create_method} "
            f"(c {opc});"
        )
        locus = "fixture.dependency_state"

    # --- arm the non-superuser role (AFTER family creation) -----------
    if effective:
        setup.append(f"SET ROLE {p}actor;")
    if_exists = "IF EXISTS " if _if_exists_present(case, a) else ""
    cascade = _cascade_clause(a)
    target = f"DROP OPERATOR FAMILY {if_exists}{fam_ref} USING {drop_method}"
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
    family_drop = (
        f"DROP OPERATOR FAMILY IF EXISTS {fam_ref} "
        f"USING {create_method} CASCADE;"
    )
    dep_drops = (
        [f"DROP TABLE IF EXISTS {p}t CASCADE;"] if needs_dep else []
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

    # Pre-cleanup: DROP TABLE first (bookend gate), then family, then roles.
    pre_cleanup: list[str] = []
    pre_cleanup.extend(dep_drops)
    pre_cleanup.append(family_drop)
    pre_cleanup.extend(role_drops)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # Cleanup: RESET ROLE, then family/role drops, then DROP
    # TABLE last (bookend gate).
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.append(family_drop)
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


def resolve_drop_operator_family_factor_witness(
    case: DropOperatorFamilyFactorCase | DropOperatorFamilyFactorExtensionCase,
    repository_root: Path,
) -> DropOperatorFamilyFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropOperatorFamilyFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_operator_family(sql: str) -> int:
    """Count the single credited DROP OPERATOR FAMILY inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*DROP\s+OPERATOR\s+FAMILY\b", region)
    )


def _header(case: DropOperatorFamilyFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP OPERATOR FAMILY {case.factor_key}={case.factor_value}",
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


def render_drop_operator_family_factor_case(
    case: DropOperatorFamilyFactorCase | DropOperatorFamilyFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP OPERATOR FAMILY regress program."""

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地操作符族和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP OPERATOR FAMILY。")
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


def generate_drop_operator_family_factor_programs(
    baseline_plan: DropOperatorFamilyFactorLoopPlan,
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
    case: DropOperatorFamilyFactorCase | DropOperatorFamilyFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_operator_family_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropOperatorFamilyFactorRenderError",
    "DropOperatorFamilyFactorWitness",
    "count_primary_drop_operator_family",
    "generate_drop_operator_family_factor_programs",
    "render_drop_operator_family_factor_case",
    "resolve_drop_operator_family_factor_witness",
]
