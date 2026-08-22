"""Render complete PostgreSQL 18.4 DROP FUNCTION factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_proc ... ORDER BY count(*)``
never nests a ``FROM`` inside an ``EXISTS`` subquery, so
``audit_catalog_observability`` accepts it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .cleanup_bookend import DropSpec, build_cleanup, build_pre_cleanup
from .drop_function_factor_extension import (
    DropFunctionFactorExtensionCase,
)
from .drop_function_factor_loop import (
    DropFunctionFactorCase,
    DropFunctionFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/function/"
    "drop_function.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/function/"
    "drop_function.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

# Primary (factor, value) pairs where the target function is
# intentionally absent, so the drop surfaces a not-found error (or a notice
# under IF EXISTS) and the oracle asserts absence.
_ABSENT_PRIMARIES = frozenset(
    {
        ("object_state", "not_exists"),
        ("object_state", "different_signature_exists"),
        ("target_function_not_exists", "with_IF_EXISTS_noop"),
        ("target_function_not_exists", "without_IF_EXISTS_error"),
        ("expected_status", "failure"),
        ("schema_dependency", "schema_not_exists"),
        ("identifier_length_exceeded", "over_63_chars"),
    }
)

# Primary pairs where the target object exists but is a different type
# (aggregate or procedure), so DROP FUNCTION fails with wrong_object_type.
_WRONG_TYPE_PRIMARIES = frozenset(
    {
        ("target_function_different_type", "same_name_is_aggregate"),
        ("target_function_different_type", "same_name_is_procedure"),
    }
)

# Primary pairs where multiple functions share the name, so DROP without
# args fails with function_name_not_unique.
_MULTI_NAME_PRIMARIES = frozenset(
    {
        ("argtype_specification", "without_signature_multiple"),
    }
)

# Baseline primaries that imply a dependent object fixture must be created.
_DEPENDENCY_PRIMARIES = frozenset(
    {
        ("dependent_objects", "has_dependents_restrict_blocks"),
        ("dependent_objects", "has_dependents_cascade_removes"),
        ("cascade_destroys_dependents", "cascade_removes_trigger"),
        ("cascade_destroys_dependents", "cascade_removes_view"),
    }
)

# For an extension SUCCESS case (no present failure pair) the synthetic
# primary must be a neutral success primary whose helpers fall through to the
# assignment; the function always exists in extensions (object_state held at
# exists).
_BRANCH_NEUTRAL_SUCCESS = ("object_state", "exists")


def _synthetic_case(
    ext: DropFunctionFactorExtensionCase,
) -> DropFunctionFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .drop_function_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropFunctionFactorCase(
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
    case: DropFunctionFactorCase | DropFunctionFactorExtensionCase,
) -> DropFunctionFactorCase:
    if isinstance(case, DropFunctionFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropFunctionFactorRenderError(ValueError):
    """Raised when a DROP FUNCTION case cannot be rendered."""


@dataclass(frozen=True)
class DropFunctionFactorWitness:
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


def _baseline(case: DropFunctionFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _func_ref(case: DropFunctionFactorCase, a: dict[str, str], p: str) -> str:
    """The function name as referenced inside DROP FUNCTION."""

    shape = a.get("function_name_shape", "simple")
    if shape == "quoted":
        return f'"{p}QuotedFn"'
    if shape == "reserved_word":
        return f'"{p}select"'
    if shape == "schema_qualified":
        return f"public.{p}fn"
    return f"{p}fn"


def _probe_name(case: DropFunctionFactorCase, a: dict[str, str], p: str) -> str:
    """The bare function name (no quotes, no schema) for the catalog probe."""

    shape = a.get("function_name_shape", "simple")
    if shape == "quoted":
        return f"{p}QuotedFn"
    if shape == "reserved_word":
        return f"{p}select"
    return f"{p}fn"


def _needs_args(case: DropFunctionFactorCase, a: dict[str, str]) -> bool:
    """Whether the DROP FUNCTION statement includes argument types."""

    argtype = a.get("argtype_specification", "without_signature_single")
    if argtype == "with_full_signature":
        return True
    # different_signature_exists implies the user specifies a signature that
    # does not match; force args so the drop fails with 42704.
    if (case.factor_key, case.factor_value) == (
        "object_state",
        "different_signature_exists",
    ):
        return True
    if case.kind == "EXT" and a.get("object_state") == (
        "different_signature_exists"
    ):
        return True
    return False


def _fixture_kind(
    case: DropFunctionFactorCase, a: dict[str, str]
) -> str:
    """What kind of fixture (if any) must be created for the target."""

    if case.kind == "RISK":
        return "function"
    primary = (case.factor_key, case.factor_value)
    if primary in _WRONG_TYPE_PRIMARIES:
        if primary == ("target_function_different_type", "same_name_is_aggregate"):
            return "aggregate"
        return "procedure"
    if primary in _MULTI_NAME_PRIMARIES:
        return "function_multiple"
    if primary in _ABSENT_PRIMARIES:
        return "none"
    if case.kind == "EXT":
        if a.get("object_state") in ("not_exists", "different_signature_exists"):
            return "none"
    return "function"


def _if_exists_present(
    case: DropFunctionFactorCase, a: dict[str, str]
) -> bool:
    if (case.factor_key, case.factor_value) == (
        "target_function_not_exists",
        "with_IF_EXISTS_noop",
    ):
        return True
    return a.get("if_exists_clause") == "present"


def _cascade_clause(a: dict[str, str]) -> str:
    cascade = a.get("cascade_restrict_clause", "absent")
    if cascade == "CASCADE":
        return "CASCADE"
    if cascade == "RESTRICT":
        return "RESTRICT"
    return ""  # absent: RESTRICT is the default


def _effective_role(
    case: DropFunctionFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP FUNCTION runs."""

    if case.kind == "EXT":
        level = a.get("privilege_level", "superuser")
        return f"{p}actor" if level == "non_owner_no_privilege" else ""
    if case.factor_key == "privilege_level":
        return (
            f"{p}actor" if case.factor_value == "non_owner_no_privilege" else ""
        )
    if case.factor_key == "permission_insufficient":
        return f"{p}actor" if case.factor_value == "not_owner" else ""
    return ""


def _needs_dependent(
    case: DropFunctionFactorCase, a: dict[str, str]
) -> bool:
    """Whether a dependent object fixture must be created."""

    if case.kind == "EXT":
        return a.get("dependent_objects") in (
            "has_dependents_cascade_removes",
            "has_dependents_restrict_blocks",
        )
    if (case.factor_key, case.factor_value) in _DEPENDENCY_PRIMARIES:
        return True
    return a.get("dependent_objects") in (
        "has_dependents_cascade_removes",
        "has_dependents_restrict_blocks",
    )


def _function_absent_after(
    case: DropFunctionFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target function is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if _fixture_kind(case, a) == "none":
        return True
    if case.outcome == "success":
        return True
    return False


def _probe_select(
    case: DropFunctionFactorCase, a: dict[str, str], p: str
) -> str:
    name = _probe_name(case, a, p)
    absent = _function_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "function_absent" if absent else "function_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_proc "
        f"WHERE proname = '{name}' ORDER BY count(*) LIMIT 1;"
    )


def _role_names(
    case: DropFunctionFactorCase, p: str, effective: str
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}actor":
        roles.append(f"{p}actor")
    return tuple(roles)


def _resolve_case(case: DropFunctionFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    fixture_kind = _fixture_kind(case, a)
    fn_ref = _func_ref(case, a, p)
    needs_dep = _needs_dependent(case, a)

    setup: list[str] = []
    locus = "target.function"

    # --- role fixtures (CREATE only; SET ROLE deferred to after the
    # function fixture so they run as the superuser) ---
    effective = _effective_role(case, a, p)
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- the target function fixture (as superuser, before SET ROLE) -------
    if fixture_kind == "function":
        setup.append(
            f"CREATE FUNCTION {p}fn(integer) RETURNS integer "
            "AS $$ BEGIN RETURN 1; END; $$ LANGUAGE plpgsql;"
        )
    elif fixture_kind == "function_multiple":
        setup.append(
            f"CREATE FUNCTION {p}fn(integer) RETURNS integer "
            "AS $$ BEGIN RETURN 1; END; $$ LANGUAGE plpgsql;"
        )
        setup.append(
            f"CREATE FUNCTION {p}fn(text) RETURNS text "
            "AS $$ BEGIN RETURN 'x'; END; $$ LANGUAGE plpgsql;"
        )
    elif fixture_kind == "aggregate":
        setup.append(
            f"CREATE AGGREGATE {p}fn(integer) "
            "(SFUNC = int4_inc, INITCOND = '0', STYPE = bigint);"
        )
    elif fixture_kind == "procedure":
        setup.append(
            f"CREATE PROCEDURE {p}fn(integer) "
            "AS $$ BEGIN NULL; END; $$ LANGUAGE plpgsql;"
        )
    else:
        setup.append(
            "SELECT 1 AS target_function_intentionally_absent;"
        )
        locus = "fixture.object_state"

    # --- dependent object fixture (as superuser, before SET ROLE) ---------
    if needs_dep:
        setup.append(f"CREATE TABLE {p}t (c integer);")
        setup.append(
            f"CREATE VIEW {p}v AS SELECT {p}fn(c) AS result "
            f"FROM {p}t;"
        )
        locus = "fixture.dependency_state"

    # --- arm the non-superuser role (AFTER function creation) -------------
    if effective:
        setup.append(f"SET ROLE {p}actor;")
    if_exists = "IF EXISTS " if _if_exists_present(case, a) else ""
    cascade = _cascade_clause(a)
    args = "(integer)" if _needs_args(case, a) else ""
    target = f"DROP FUNCTION {if_exists}{fn_ref}{args}"
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

    # --- cleanup construction (shared idempotent bookends) -----------
    # Migrated to cleanup_bookend so every DROP carries IF EXISTS and
    # DROP OWNED BY is unreachable in pre-cleanup: the non-superuser role
    # is created by setup, so on a fresh database the role does not exist
    # yet at pre-cleanup time and DROP OWNED BY would crash
    # (ON_ERROR_STOP=1) before the target statement reaches execution.
    # Pre-cleanup drops roles via DROP ROLE IF EXISTS only; the post-target
    # cleanup runs DROP OWNED BY then DROP ROLE IF EXISTS once setup has
    # created the role.  The DROP TABLE IF EXISTS anchor is first in
    # pre-cleanup and last in cleanup, satisfying the table-bookend gate.
    specs: list[DropSpec] = []
    if needs_dep:
        specs.append(DropSpec("VIEW", f"{p}v"))
    if fixture_kind == "function_multiple":
        specs.append(DropSpec("FUNCTION", f"{p}fn", "(integer)"))
        specs.append(DropSpec("FUNCTION", f"{p}fn", "(text)"))
    elif fixture_kind == "aggregate":
        specs.append(
            DropSpec("AGGREGATE", f"{p}fn", "(integer)", cascade=False)
        )
    elif fixture_kind == "procedure":
        specs.append(
            DropSpec("PROCEDURE", f"{p}fn", "(integer)", cascade=False)
        )
    elif fixture_kind == "function":
        specs.append(DropSpec("FUNCTION", f"{p}fn", "(integer)"))

    table_names = [f"{p}t"] if needs_dep else []
    role_list = list(_role_names(case, p, effective))
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


def resolve_drop_function_factor_witness(
    case: DropFunctionFactorCase | DropFunctionFactorExtensionCase,
    repository_root: Path,
) -> DropFunctionFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropFunctionFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_function(sql: str) -> int:
    """Count the single credited DROP FUNCTION inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*DROP\s+FUNCTION\b", region)
    )


def _header(case: DropFunctionFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP FUNCTION {case.factor_key}={case.factor_value}",
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


def render_drop_function_factor_case(
    case: DropFunctionFactorCase | DropFunctionFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP FUNCTION regress program."""

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地函数和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP FUNCTION。")
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


def generate_drop_function_factor_programs(
    baseline_plan: DropFunctionFactorLoopPlan,
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
    case: DropFunctionFactorCase | DropFunctionFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_function_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropFunctionFactorRenderError",
    "DropFunctionFactorWitness",
    "count_primary_drop_function",
    "generate_drop_function_factor_programs",
    "render_drop_function_factor_case",
    "resolve_drop_function_factor_witness",
]
