"""Render complete PostgreSQL 18.4 DROP OPERATOR factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_operator ... ORDER BY count(*)``
never nests a ``FROM`` inside an ``EXISTS`` subquery, so
``audit_catalog_observability`` accepts it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .cleanup_bookend import DropSpec, build_cleanup, build_pre_cleanup
from .drop_operator_factor_extension import (
    DropOperatorFactorExtensionCase,
)
from .drop_operator_factor_loop import (
    DropOperatorFactorCase,
    DropOperatorFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/operator/"
    "drop_operator.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/operator/"
    "drop_operator.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

# Primary (factor, value) pairs where the target operator is intentionally
# absent, so the drop surfaces a not-found error (or a notice under IF EXISTS)
# and the oracle asserts absence.
_ABSENT_PRIMARIES = frozenset(
    {
        ("expected_status", "failure"),
        ("target_object_state", "missing"),
    }
)

# Baseline primaries that imply a dependent object fixture must be created.
_DEPENDENCY_PRIMARIES = frozenset(
    {
        ("target_object_state", "exists_with_dependents"),
        ("dependency_state", "has_dependents"),
        ("cascade_behavior", "restrict_blocks"),
    }
)

# For an extension SUCCESS case (no present failure pair) the synthetic
# primary must be a neutral success primary whose helpers fall through to the
# assignment; the operator always exists in extensions (target_object_state
# held at exists unless it is a failure case).
_BRANCH_NEUTRAL_SUCCESS = ("target_object_state", "exists")

# Operand data type to SQL type name mapping.  custom_type requires a
# CREATE TYPE fixture.
_TYPE_NAMES: dict[str, str] = {
    "integer": "integer",
    "text": "text",
    "boolean": "boolean",
    "custom_type": "_custom",
}


def _synthetic_case(
    ext: DropOperatorFactorExtensionCase,
) -> DropOperatorFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .drop_operator_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropOperatorFactorCase(
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
    case: DropOperatorFactorCase | DropOperatorFactorExtensionCase,
) -> DropOperatorFactorCase:
    if isinstance(case, DropOperatorFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropOperatorFactorRenderError(ValueError):
    """Raised when a DROP OPERATOR case cannot be rendered."""


@dataclass(frozen=True)
class DropOperatorFactorWitness:
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


def _baseline(case: DropOperatorFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _op_name(case: DropOperatorFactorCase, a: dict[str, str], p: str) -> str:
    """The operator name as referenced inside DROP OPERATOR."""

    shape = a.get("name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f'"{p}Op"'
    if shape == "schema_qualified":
        return f"public.{p}op"
    return f"{p}op"


def _probe_name(case: DropOperatorFactorCase, a: dict[str, str], p: str) -> str:
    """The bare operator name (no quotes/schema) for the catalog probe."""

    shape = a.get("name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f"{p}Op"
    return f"{p}op"


def _func_name(p: str) -> str:
    return f"{p}opfn"


def _type_name(a: dict[str, str], p: str) -> str:
    data_type = a.get("operand_data_type", "integer")
    if data_type == "custom_type":
        return f"{p}customtype"
    return _TYPE_NAMES.get(data_type, data_type)


def _is_prefix(a: dict[str, str]) -> bool:
    return a.get("operand_type_shape") == "prefix_operator"


def _left_type_ref(a: dict[str, str], p: str) -> str:
    if _is_prefix(a):
        return "NONE"
    return _type_name(a, p)


def _right_type_ref(a: dict[str, str], p: str) -> str:
    return _type_name(a, p)


def _needs_custom_type(a: dict[str, str]) -> bool:
    return a.get("operand_data_type") == "custom_type"


def _fixture_kind(
    case: DropOperatorFactorCase, a: dict[str, str]
) -> str:
    """Whether an operator fixture must be created."""

    if case.kind == "RISK":
        return "operator"
    if (case.factor_key, case.factor_value) in _ABSENT_PRIMARIES:
        return "none"
    if case.kind == "EXT":
        if a.get("target_object_state") == "missing":
            return "none"
    return "operator"


def _if_exists_present(
    case: DropOperatorFactorCase, a: dict[str, str]
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
    case: DropOperatorFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP OPERATOR runs."""

    if case.kind == "EXT":
        privilege = a.get("privilege_context", "owner")
        ownership = a.get("ownership_boundary", "owner")
        if privilege in ("non_owner", "insufficient_privilege") or ownership == "non_owner":
            return f"{p}actor"
        return ""
    if case.factor_key == "privilege_context":
        return f"{p}actor" if case.factor_value in ("non_owner", "insufficient_privilege") else ""
    if case.factor_key == "ownership_boundary":
        return f"{p}actor" if case.factor_value == "non_owner" else ""
    return ""


def _needs_dependent(
    case: DropOperatorFactorCase, a: dict[str, str]
) -> bool:
    """Whether a dependent object fixture must be created."""

    if case.kind == "EXT":
        return (
            a.get("target_object_state") == "exists_with_dependents"
            or a.get("dependency_state") == "has_dependents"
        )
    if (case.factor_key, case.factor_value) in _DEPENDENCY_PRIMARIES:
        return True
    return a.get("dependency_state") == "has_dependents"


def _operator_absent_after(
    case: DropOperatorFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target operator is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if _fixture_kind(case, a) == "none":
        return True
    if case.outcome == "success":
        return True
    return False


def _probe_select(
    case: DropOperatorFactorCase, a: dict[str, str], p: str
) -> str:
    name = _probe_name(case, a, p)
    tname = _type_name(a, p)
    absent = _operator_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "operator_absent" if absent else "operator_present"
    if _is_prefix(a):
        left_cond = "oprkind = 'l'"
        right_cond = f"oprright = '{tname}'::regtype"
        where = f"WHERE oprname = '{name}' AND {left_cond} AND {right_cond}"
    else:
        where = (
            f"WHERE oprname = '{name}' AND oprleft = '{tname}'::regtype "
            f"AND oprright = '{tname}'::regtype"
        )
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_operator "
        f"{where} ORDER BY count(*) LIMIT 1;"
    )


def _role_names(
    case: DropOperatorFactorCase, p: str, effective: str
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}actor":
        roles.append(f"{p}actor")
    return tuple(roles)


def _resolve_case(case: DropOperatorFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    fixture_kind = _fixture_kind(case, a)
    op_ref = _op_name(case, a, p)
    func = _func_name(p)
    tname = _type_name(a, p)
    needs_dep = _needs_dependent(case, a)
    needs_custom = _needs_custom_type(a)

    setup: list[str] = []
    locus = "target.operator"

    # --- role fixtures (CREATE only; SET ROLE deferred to after the
    # operator fixture so they run as the superuser) ---
    effective = _effective_role(case, a, p)
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- custom type fixture (as superuser, before operator creation) ---
    if needs_custom:
        setup.append(f"CREATE TYPE {p}customtype AS (x integer);")
        locus = "fixture.type_state"

    # --- the target operator fixture (as superuser, before SET ROLE) ---
    if fixture_kind == "operator":
        if _is_prefix(a):
            setup.append(
                f"CREATE FUNCTION {func}({tname}) RETURNS {tname} "
                "AS $$ SELECT $1; $$ LANGUAGE immutable;"
            )
            setup.append(
                f"CREATE OPERATOR {op_ref} "
                f"(PROCEDURE = {func}, RIGHTARG = {tname});"
            )
        else:
            setup.append(
                f"CREATE FUNCTION {func}({tname}, {tname}) RETURNS {tname} "
                "AS $$ SELECT $1; $$ LANGUAGE immutable;"
            )
            setup.append(
                f"CREATE OPERATOR {op_ref} "
                f"(PROCEDURE = {func}, LEFTARG = {tname}, RIGHTARG = {tname});"
            )
    else:
        setup.append(
            "SELECT 1 AS target_operator_intentionally_absent;"
        )
        locus = "fixture.object_state"

    # --- dependent object fixture (as superuser, before SET ROLE) -------
    if needs_dep:
        setup.append(f"CREATE TABLE {p}t (c integer);")
        locus = "fixture.dependency_state"

    # --- arm the non-superuser role (AFTER operator creation) -----------
    if effective:
        setup.append(f"SET ROLE {p}actor;")
    if_exists = "IF EXISTS " if _if_exists_present(case, a) else ""
    cascade = _cascade_clause(a)
    left = _left_type_ref(a, p)
    right = _right_type_ref(a, p)
    target = f"DROP OPERATOR {if_exists}{op_ref} ({left}, {right})"
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

    # --- cleanup construction (shared idempotent bookends) -------------
    # Migrated to cleanup_bookend so every DROP carries IF EXISTS and
    # DROP OWNED BY is unreachable in pre-cleanup: the role fixture is
    # created by setup, so on a fresh database the role does not exist
    # yet at pre-cleanup time and DROP OWNED BY would crash
    # (ON_ERROR_STOP=1) before the target statement reaches execution.
    # Pre-cleanup drops roles via DROP ROLE IF EXISTS only; the
    # post-target cleanup runs DROP OWNED BY then DROP ROLE IF EXISTS
    # once setup has created the role.  The DROP TABLE IF EXISTS anchor
    # is first in pre-cleanup and last in cleanup, satisfying the
    # table-bookend gate.
    roles = _role_names(case, p, effective)
    specs: list[DropSpec] = []
    specs.append(DropSpec("OPERATOR", op_ref, f"({left}, {right})"))
    specs.append(DropSpec("FUNCTION", func))
    if needs_custom:
        specs.append(DropSpec("TYPE", f"{p}customtype"))
    table_names = [f"{p}t"] if needs_dep else []
    role_list = list(roles)
    pre_bookend = build_pre_cleanup(
        tables=table_names,
        specs=tuple(specs),
        roles=role_list,
    )
    cln_bookend = build_cleanup(
        tables=table_names,
        specs=tuple(specs),
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


def resolve_drop_operator_factor_witness(
    case: DropOperatorFactorCase | DropOperatorFactorExtensionCase,
    repository_root: Path,
) -> DropOperatorFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropOperatorFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_operator(sql: str) -> int:
    """Count the single credited DROP OPERATOR inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*DROP\s+OPERATOR\b", region)
    )


def _header(case: DropOperatorFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP OPERATOR {case.factor_key}={case.factor_value}",
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


def render_drop_operator_factor_case(
    case: DropOperatorFactorCase | DropOperatorFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP OPERATOR regress program."""

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地 operator 和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP OPERATOR。")
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


def generate_drop_operator_factor_programs(
    baseline_plan: DropOperatorFactorLoopPlan,
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
    case: DropOperatorFactorCase | DropOperatorFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_operator_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropOperatorFactorRenderError",
    "DropOperatorFactorWitness",
    "count_primary_drop_operator",
    "generate_drop_operator_factor_programs",
    "render_drop_operator_factor_case",
    "resolve_drop_operator_factor_witness",
]
