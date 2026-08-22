"""Render complete PostgreSQL 18.4 DROP TYPE factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_type WHERE typname = '...'
ORDER BY count(*) LIMIT 1`` never nests a ``FROM`` inside an ``EXISTS``
subquery, so ``audit_catalog_observability`` accepts it.  The probe column
``typname`` is a real ``pg_type`` column (pre-verified against PG18.4) — the
no-DB tickoff does not execute this probe, so a wrong column would pass all
static gates yet be a permanent latent runtime bug; the column is verified.

Bookend note: DROP TYPE itself drops a TYPE (CREATE TYPE does not trigger the
table bookend gate).  However, dependency-failure cases that CREATE a TABLE
referencing the custom type (``used_in_table_columns`` / ``used_in_typed_tables``)
DO trigger the shared ``audit_complete_table_script`` gate.  For those cases the
first + last executable ``;``-statement are each ``DROP TABLE IF EXISTS`` with
unquoted lowercase fixture names (the gate's identifier normalizer rejects
quoted/dotted table identifiers).  For the TYPE fixture itself, quoting is fine
(the gate only audits TABLE creates/drops).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .cleanup_bookend import DropSpec, build_cleanup, build_pre_cleanup
from .drop_type_factor_extension import (
    DropTypeFactorExtensionCase,
)
from .drop_type_factor_loop import (
    DropTypeFactorCase,
    DropTypeFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/type/drop_type.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/type/drop_type.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-21"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

# Baseline primaries whose target type is intentionally absent, so the DROP
# surfaces a not-found error (42704) and the oracle asserts absence.
_ABSENT_TYPE_PRIMARIES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "not_exists"),
        ("error_boundary", "non_existent_without_if_exists"),
    }
)

# For an extension SUCCESS case (no present failure pair) the synthetic
# primary must be a neutral success primary whose helpers fall through to the
# assignment; the type always exists in extensions (object_state held at
# exists_composite) unless object_state=not_exists.
_BRANCH_NEUTRAL_SUCCESS = ("object_state", "exists_composite")

# Dependency states that CREATE a TABLE (triggering the bookend gate).
_TABLE_DEPENDENCIES = frozenset(
    {"used_in_table_columns", "used_in_typed_tables"}
)
_ALL_DEPENDENCIES = frozenset(
    {
        "used_in_table_columns",
        "used_in_function_params",
        "used_in_operators",
        "used_in_typed_tables",
    }
)


def _synthetic_case(
    ext: DropTypeFactorExtensionCase,
) -> DropTypeFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .drop_type_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropTypeFactorCase(
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
    case: DropTypeFactorCase | DropTypeFactorExtensionCase,
) -> DropTypeFactorCase:
    if isinstance(case, DropTypeFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropTypeFactorRenderError(ValueError):
    """Raised when a DROP TYPE case cannot be rendered."""


@dataclass(frozen=True)
class DropTypeFactorWitness:
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


def _baseline(case: DropTypeFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _type_name_shape(a: dict[str, str]) -> str:
    return a.get("type_name_shape", "simple")


def _type_ref(case: DropTypeFactorCase, a: dict[str, str], p: str) -> str:
    """The type name as referenced inside CREATE/DROP TYPE."""

    shape = _type_name_shape(a)
    if shape == "quoted":
        return f'"{p}qtype"'
    if shape == "schema_qualified":
        return f"public.{p}type"
    if shape == "reserved_word":
        return '"order"'
    return f"{p}type"


def _type_probe(case: DropTypeFactorCase, a: dict[str, str], p: str) -> str:
    """The bare typname (no quotes/schema) for the catalog probe."""

    shape = _type_name_shape(a)
    if shape == "quoted":
        return f"{p}qtype"
    if shape == "schema_qualified":
        return f"{p}type"
    if shape == "reserved_word":
        return "order"
    return f"{p}type"


def _second_type_ref(p: str) -> str:
    """The second type for multi_type drops (always plain)."""

    return f"{p}type2"


def _type_created(case: DropTypeFactorCase, a: dict[str, str]) -> bool:
    """Whether a type fixture must be created (absent otherwise)."""

    return a.get("object_state") != "not_exists"


def _is_multi(a: dict[str, str]) -> bool:
    return a.get("multi_type_drop") == "multi_type"


def _if_exists_present(a: dict[str, str]) -> bool:
    return a.get("if_exists_clause") == "present"


def _cascade_clause(a: dict[str, str]) -> str:
    cascade = a.get("cascade_restrict", "none")
    if cascade == "cascade":
        return "CASCADE"
    if cascade == "restrict":
        return "RESTRICT"
    return ""  # none: RESTRICT is the default


def _effective_role(
    case: DropTypeFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP TYPE runs."""

    if case.kind == "EXT":
        level = a.get("privilege_level", "superuser")
        return f"{p}actor" if level == "non_owner" else ""
    if case.factor_key == "privilege_level":
        return f"{p}actor" if case.factor_value == "non_owner" else ""
    if case.factor_key == "error_boundary":
        return f"{p}actor" if case.factor_value == "insufficient_privilege" else ""
    return ""


def _needs_dependent(case: DropTypeFactorCase, a: dict[str, str]) -> bool:
    """Whether a dependent object fixture must be created."""

    if case.kind == "EXT":
        return a.get("dependency_state") in _ALL_DEPENDENCIES
    return a.get("dependency_state") in _ALL_DEPENDENCIES


def _dependency_kind(a: dict[str, str]) -> str:
    return a.get("dependency_state", "no_dependents")


def _creates_table(a: dict[str, str]) -> bool:
    return a.get("dependency_state") in _TABLE_DEPENDENCIES


def _created_table_name(a: dict[str, str], p: str) -> str:
    dep = a.get("dependency_state", "no_dependents")
    if dep == "used_in_table_columns":
        return f"{p}deptbl"
    if dep == "used_in_typed_tables":
        return f"{p}dtbl"
    return ""


def _type_absent_after(
    case: DropTypeFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target type is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if not _type_created(case, a):
        return True
    if case.outcome == "success":
        return True
    return False


def _probe_select(
    case: DropTypeFactorCase, a: dict[str, str], p: str
) -> str:
    type_probe = _type_probe(case, a, p)
    absent = _type_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "type_absent" if absent else "type_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_type WHERE typname = '" + type_probe + "' "
        "ORDER BY count(*) LIMIT 1;"
    )


def _create_type_sql(type_ref: str, category: str) -> str:
    if category == "composite":
        return f"CREATE TYPE {type_ref} AS (c integer);"
    if category == "enum":
        return f"CREATE TYPE {type_ref} AS ENUM ('a', 'b');"
    if category == "range":
        return f"CREATE TYPE {type_ref} AS RANGE (SUBTYPE = integer);"
    # base (shell type)
    return f"CREATE TYPE {type_ref};"


def _role_names(
    case: DropTypeFactorCase, p: str, effective: str
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}actor":
        roles.append(f"{p}actor")
    return tuple(roles)


def _dependency_setup(
    a: dict[str, str], p: str, type_ref: str
) -> list[str]:
    """Fixture statements creating a dependent on the target type."""

    dep = _dependency_kind(a)
    if dep == "used_in_table_columns":
        return [f"CREATE TABLE {p}deptbl (c {type_ref});"]
    if dep == "used_in_typed_tables":
        return [f"CREATE TABLE {p}dtbl OF {type_ref};"]
    if dep == "used_in_function_params":
        return [
            f"CREATE FUNCTION {p}fn(x {type_ref}) RETURNS integer "
            "LANGUAGE sql AS $$ SELECT 1; $$;"
        ]
    if dep == "used_in_operators":
        return [
            f"CREATE FUNCTION {p}opfn({type_ref}, {type_ref}) "
            "RETURNS boolean LANGUAGE sql AS "
            "$$ SELECT $1 IS NOT NULL; $$;",
            f"CREATE OPERATOR # (PROCEDURE = {p}opfn, "
            f"LEFTARG = {type_ref}, RIGHTARG = {type_ref});",
        ]
    return []


def _resolve_case(case: DropTypeFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    type_ref = _type_ref(case, a, p)
    type_created = _type_created(case, a)
    category = a.get("type_category", "composite")
    needs_dep = _needs_dependent(case, a)
    effective = _effective_role(case, a, p)
    multi = _is_multi(a)
    creates_table = _creates_table(a)
    table_name = _created_table_name(a, p)

    setup: list[str] = []
    locus = "target.type"

    # --- setup boundary SELECT (keeps \set from merging with the first
    # CREATE so the bookend gate detects created objects at col 0) ---
    if type_created or needs_dep or effective:
        setup.append("SELECT 1 AS setup_boundary;")

    # --- role fixture (CREATE only; SET ROLE deferred to after the type
    # fixture so they run as the superuser) ---
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- the target TYPE (as superuser, before SET ROLE) ---
    if type_created:
        setup.append(_create_type_sql(type_ref, category))
        if multi:
            setup.append(_create_type_sql(_second_type_ref(p), category))
        if locus == "target.type":
            locus = "fixture.type"

    # --- dependent fixture (as superuser, before SET ROLE) --------------
    if needs_dep:
        setup.extend(_dependency_setup(a, p, type_ref))
        locus = "fixture.dependency_state"

    # --- arm the non-superuser role (AFTER type/dependent creation) ------
    if effective:
        setup.append(f"SET ROLE {p}actor;")
    if_exists = "IF EXISTS " if _if_exists_present(a) else ""
    cascade = _cascade_clause(a)
    target_type = type_ref
    if multi:
        target_type = f"{type_ref}, {_second_type_ref(p)}"
    target = f"DROP TYPE {if_exists}{target_type}"
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
    # DROP OWNED BY is unreachable in pre-cleanup: the actor role
    # fixture is created by setup, so on a fresh database the role does
    # not exist yet at pre-cleanup time and DROP OWNED BY would crash
    # (ON_ERROR_STOP=1) before the target statement reaches execution.
    # Pre-cleanup drops roles via DROP ROLE IF EXISTS only; the post-target
    # cleanup runs DROP OWNED BY then DROP ROLE IF EXISTS once setup has
    # created the role.  The DROP TABLE IF EXISTS anchor is first in
    # pre-cleanup and last in cleanup, satisfying the table-bookend gate.
    #
    # The operator ``#`` (a symbolic name the helper's identifier
    # validator rejects, and PostgreSQL rejects as a quoted identifier)
    # is dropped implicitly: ``DROP FUNCTION opfn CASCADE`` cascades to
    # the operator whose ``PROCEDURE = opfn``, so no separate OPERATOR
    # DropSpec is needed.
    specs: list[DropSpec] = []
    dep = _dependency_kind(a)
    if dep == "used_in_operators":
        specs.append(DropSpec("FUNCTION", f"{p}opfn"))
    if dep == "used_in_function_params":
        specs.append(DropSpec("FUNCTION", f"{p}fn"))
    specs.append(DropSpec("TYPE", type_ref))
    if multi:
        specs.append(DropSpec("TYPE", _second_type_ref(p)))
    table_names = [table_name] if creates_table else []
    roles = _role_names(case, p, effective)
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


def resolve_drop_type_factor_witness(
    case: DropTypeFactorCase | DropTypeFactorExtensionCase,
    repository_root: Path,
) -> DropTypeFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropTypeFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_type(sql: str) -> int:
    """Count the single credited DROP TYPE inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*DROP\s+TYPE\b", region)
    )


def _header(case: DropTypeFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP TYPE {case.factor_key}={case.factor_value}",
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


def render_drop_type_factor_case(
    case: DropTypeFactorCase | DropTypeFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP TYPE regress program."""

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地类型和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP TYPE。")
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


def generate_drop_type_factor_programs(
    baseline_plan: DropTypeFactorLoopPlan,
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
    case: DropTypeFactorCase | DropTypeFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_type_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropTypeFactorRenderError",
    "DropTypeFactorWitness",
    "count_primary_drop_type",
    "generate_drop_type_factor_programs",
    "render_drop_type_factor_case",
    "resolve_drop_type_factor_witness",
]
