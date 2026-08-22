"""Render complete PostgreSQL 18.4 DROP PROCEDURE factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_proc ... ORDER BY count(*)``
filters on the real PG18 ``pg_proc`` columns ``proname`` and ``prokind`` (the
latter distinguishes a procedure ``'p'`` from a function/aggregate/window),
so ``audit_catalog_observability`` accepts it.  No ``FROM`` subquery is nested
inside ``EXISTS``.  No case creates a table, so the bookend gate is N/A.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .cleanup_bookend import DropSpec, build_cleanup, build_pre_cleanup
from .drop_procedure_factor_extension import (
    DropProcedureFactorExtensionCase,
)
from .drop_procedure_factor_loop import (
    DropProcedureFactorCase,
    DropProcedureFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/procedure/"
    "drop_procedure.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/procedure/"
    "drop_procedure.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

# Primary (factor, value) pairs where the target procedure is intentionally
# absent, so the drop surfaces a not-found error (or a notice under IF EXISTS)
# and the oracle asserts absence.
_ABSENT_PRIMARIES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "not_exists"),
        ("target_procedure_not_exists", "without_IF_EXISTS_error"),
    }
)

# Absent but IF EXISTS is forced so the drop surfaces a NOTICE (no-op success).
_IF_EXISTS_FORCED_PRIMARY = (
    "target_procedure_not_exists",
    "with_IF_EXISTS_noop",
)

_FUNCTION_PRIMARY = (
    "target_procedure_different_type",
    "same_name_is_function",
)
_DIFF_SIG_PRIMARY = ("object_state", "different_signature_exists")
_SCHEMA_ABSENT_PRIMARY = ("schema_dependency", "schema_not_exists")
_AMBIGUOUS_PRIMARY = ("argtype_specification", "without_signature_multiple")
_MULTIPLE_PRIMARIES = frozenset(
    {
        ("multiple_objects", "multiple_procedures"),
        ("statement_branch", "branch_2"),
    }
)
_CASCADE_FORCED_PRIMARY = (
    "cascade_destroys_dependents",
    "cascade_removes_trigger",
)
_HAS_DEPENDENTS_PRIMARIES = frozenset(
    {
        ("dependent_objects", "has_dependents_restrict_blocks"),
        ("dependent_objects", "has_dependents_cascade_removes"),
        ("cascade_destroys_dependents", "cascade_removes_trigger"),
    }
)

# For an extension SUCCESS case (no present failure pair) the synthetic
# primary is a neutral success primary whose helpers fall through to the
# assignment; the procedure always exists in extensions (object_state held
# at exists).
_BRANCH_NEUTRAL_SUCCESS = ("object_state", "exists")

_HAS_DEPENDENTS_VALUES = frozenset(
    {"has_dependents_restrict_blocks", "has_dependents_cascade_removes"}
)


def _synthetic_case(
    ext: DropProcedureFactorExtensionCase,
) -> DropProcedureFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .drop_procedure_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropProcedureFactorCase(
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
    case: DropProcedureFactorCase | DropProcedureFactorExtensionCase,
) -> DropProcedureFactorCase:
    if isinstance(case, DropProcedureFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropProcedureFactorRenderError(ValueError):
    """Raised when a DROP PROCEDURE case cannot be rendered."""


@dataclass(frozen=True)
class DropProcedureFactorWitness:
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


def _baseline(case: DropProcedureFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _proc_name(case: DropProcedureFactorCase, a: dict[str, str], p: str) -> str:
    """The procedure name as referenced inside DROP PROCEDURE."""

    shape = a.get("procedure_name_shape", "simple")
    pair = (case.factor_key, case.factor_value)
    if pair == _SCHEMA_ABSENT_PRIMARY:
        return f"{p}schema.{p}proc"
    if shape == "quoted":
        return f'"{p}QuotedProc"'
    if shape == "reserved_word":
        return f'"{p}select"'
    if shape == "schema_qualified":
        return f"{p}schema.{p}proc"
    if (case.factor_key, case.factor_value) == (
        "identifier_length_exceeded",
        "over_63_chars",
    ):
        return _long_name(p)
    return f"{p}proc"


def _long_name(p: str) -> str:
    """A 64-char identifier; PG truncates to 63 for storage on both sides."""

    base = f"{p}proc"
    return (base + "x" * 64)[:64]


def _probe_name(case: DropProcedureFactorCase, a: dict[str, str], p: str) -> str:
    """The bare proname (no quotes, no schema) for the catalog probe."""

    shape = a.get("procedure_name_shape", "simple")
    pair = (case.factor_key, case.factor_value)
    if pair == _SCHEMA_ABSENT_PRIMARY:
        return f"{p}proc"
    if shape == "quoted":
        return f"{p}QuotedProc"
    if shape == "reserved_word":
        return f"{p}select"
    if shape == "schema_qualified":
        return f"{p}proc"
    if (case.factor_key, case.factor_value) == (
        "identifier_length_exceeded",
        "over_63_chars",
    ):
        return _long_name(p)[:63]
    return f"{p}proc"


def _proc_name2(p: str) -> str:
    return f"{p}proc2"


def _probe_name2(p: str) -> str:
    return f"{p}proc2"


def _dep_func(p: str) -> str:
    return f"{p}dep"


def _drop_args(case: DropProcedureFactorCase, a: dict[str, str]) -> str:
    spec = a.get("argtype_specification", "with_full_signature")
    pair = (case.factor_key, case.factor_value)
    if pair == _DIFF_SIG_PRIMARY:
        return "(integer)"  # target signature that does not match
    if spec == "without_signature_single":
        return ""
    if spec == "without_signature_multiple":
        return ""
    return "(integer)"


def _fixture_kind(
    case: DropProcedureFactorCase, a: dict[str, str]
) -> str:
    """What target fixture to create."""

    if case.kind == "RISK":
        return "procedure"
    pair = (case.factor_key, case.factor_value)
    if pair in _ABSENT_PRIMARIES:
        return "absent"
    if pair == _IF_EXISTS_FORCED_PRIMARY:
        return "absent"  # absent + IF EXISTS -> notice (no-op success)
    if pair == _FUNCTION_PRIMARY:
        return "function"
    if pair == _DIFF_SIG_PRIMARY:
        return "different_signature"
    if pair == _SCHEMA_ABSENT_PRIMARY:
        return "schema_absent"
    if pair == _AMBIGUOUS_PRIMARY:
        return "ambiguous"
    if pair in _MULTIPLE_PRIMARIES:
        return "multiple_drop"
    return "procedure"


def _if_exists_present(
    case: DropProcedureFactorCase, a: dict[str, str]
) -> bool:
    if (case.factor_key, case.factor_value) == _IF_EXISTS_FORCED_PRIMARY:
        return True
    return a.get("if_exists_clause") == "present"


def _cascade_clause(
    case: DropProcedureFactorCase, a: dict[str, str]
) -> str:
    if (case.factor_key, case.factor_value) == _CASCADE_FORCED_PRIMARY:
        return "CASCADE"
    cascade = a.get("cascade_restrict_clause", "absent")
    if cascade == "CASCADE":
        return "CASCADE"
    if cascade == "RESTRICT":
        return "RESTRICT"
    return ""  # absent -> default RESTRICT


def _effective_role(
    case: DropProcedureFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP PROCEDURE runs."""

    if case.kind == "EXT":
        level = a.get("privilege_level", "superuser")
        return f"{p}actor" if level == "non_owner_no_privilege" else ""
    if case.factor_key == "privilege_level":
        return (
            f"{p}actor"
            if case.factor_value == "non_owner_no_privilege"
            else ""
        )
    if case.factor_key == "permission_insufficient":
        return f"{p}actor" if case.factor_value == "not_owner" else ""
    return ""


def _needs_schema(
    case: DropProcedureFactorCase, a: dict[str, str]
) -> bool:
    shape = a.get("procedure_name_shape", "simple")
    pair = (case.factor_key, case.factor_value)
    if pair == _SCHEMA_ABSENT_PRIMARY:
        return False
    return shape == "schema_qualified"


def _needs_dependent(
    case: DropProcedureFactorCase, a: dict[str, str]
) -> bool:
    """Whether a dependent function fixture must be created."""

    fixture = _fixture_kind(case, a)
    if fixture not in ("procedure",):
        return False
    if case.kind == "EXT":
        return a.get("dependent_objects") in _HAS_DEPENDENTS_VALUES
    return (case.factor_key, case.factor_value) in _HAS_DEPENDENTS_PRIMARIES


def _procedure_absent_after(
    case: DropProcedureFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target procedure is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    fixture = _fixture_kind(case, a)
    if fixture in ("absent", "schema_absent", "function"):
        return True
    if case.outcome == "success":
        return True
    return False  # failure with a real procedure still present


def _probe_select(
    case: DropProcedureFactorCase, a: dict[str, str], p: str
) -> str:
    name = _probe_name(case, a, p)
    absent = _procedure_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "procedure_absent" if absent else "procedure_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_proc "
        f"WHERE proname = '{name}' AND prokind = 'p' "
        "ORDER BY count(*) LIMIT 1;"
    )


def _role_names(
    case: DropProcedureFactorCase, p: str, effective: str
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}actor":
        roles.append(f"{p}actor")
    return tuple(roles)


def _create_procedure_stmt(name: str, args: str) -> str:
    body = f"{name}{args} AS $$ BEGIN END; $$ LANGUAGE plpgsql;"
    return f"CREATE PROCEDURE {body}"


def _resolve_case(case: DropProcedureFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    fixture = _fixture_kind(case, a)
    name = _proc_name(case, a, p)
    dep = _dep_func(p)
    needs_schema = _needs_schema(case, a)
    needs_dep = _needs_dependent(case, a)
    drop_args = _drop_args(case, a)

    setup: list[str] = []
    locus = "target.procedure"

    # --- role fixtures (CREATE only; SET ROLE deferred to after the
    # procedure fixture so they run as the superuser) ---
    effective = _effective_role(case, a, p)
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- schema fixture (as superuser, before the procedure) ---
    if needs_schema:
        setup.append(f"CREATE SCHEMA {p}schema;")
        locus = "fixture.schema_state"

    # --- the target procedure fixture (as superuser, before SET ROLE) ----
    if fixture == "procedure":
        setup.append(_create_procedure_stmt(name, "(integer)"))
    elif fixture == "different_signature":
        setup.append(_create_procedure_stmt(name, "(text)"))
    elif fixture == "function":
        setup.append(
            f"CREATE FUNCTION {name}() RETURNS void "
            "AS $$ BEGIN END; $$ LANGUAGE plpgsql;"
        )
        locus = "fixture.object_type_state"
    elif fixture == "ambiguous":
        setup.append(_create_procedure_stmt(name, "(integer)"))
        setup.append(_create_procedure_stmt(name, "(text)"))
        locus = "fixture.signature_ambiguity_state"
    elif fixture == "multiple_drop":
        setup.append(_create_procedure_stmt(name, "(integer)"))
        setup.append(_create_procedure_stmt(_proc_name2(p), "(integer)"))
        locus = "fixture.multiple_object_state"
    elif fixture == "schema_absent":
        setup.append(
            "SELECT 1 AS target_schema_intentionally_absent;"
        )
        locus = "fixture.schema_absent_state"
    else:  # absent
        setup.append(
            "SELECT 1 AS target_procedure_intentionally_absent;"
        )
        locus = "fixture.object_state"

    # --- dependent function fixture (as superuser, before SET ROLE) ------
    if needs_dep:
        setup.append(
            f"CREATE FUNCTION {dep}() RETURNS void "
            f"AS $$ BEGIN CALL {name}(0); END; $$ LANGUAGE plpgsql;"
        )
        locus = "fixture.dependency_state"

    # --- arm the non-superuser role (AFTER procedure creation) -----------
    if effective:
        setup.append(f"SET ROLE {p}actor;")
    if_exists = "IF EXISTS " if _if_exists_present(case, a) else ""
    cascade = _cascade_clause(case, a)
    cascade_str = f" {cascade}" if cascade else ""

    if fixture == "multiple_drop":
        name2 = _proc_name2(p)
        target = (
            f"DROP PROCEDURE {if_exists}{name}{drop_args}, "
            f"{name2}{drop_args}{cascade_str};"
        )
    else:
        target = f"DROP PROCEDURE {if_exists}{name}{drop_args}{cascade_str};"

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
    # DROP OWNED BY is unreachable in pre-cleanup: the {p}actor role is
    # created by setup, so on a fresh database the role does not exist
    # yet at pre-cleanup time and DROP OWNED BY would crash
    # (ON_ERROR_STOP=1) before the target statement reaches execution.
    # Pre-cleanup drops roles via DROP ROLE IF EXISTS only; the
    # post-target cleanup runs DROP OWNED BY then DROP ROLE IF EXISTS
    # once setup has created the role. No case creates a table, so the
    # DROP TABLE anchor is not emitted (bookend gate N/A per the module
    # docstring); the residual SELECT keeps each region non-empty.
    specs: list[DropSpec] = [DropSpec("PROCEDURE", name, "(integer)")]
    if fixture == "multiple_drop":
        specs.append(DropSpec("PROCEDURE", _proc_name2(p), "(integer)"))
    if fixture == "function":
        specs.append(DropSpec("FUNCTION", name))
    if needs_dep:
        specs.append(DropSpec("FUNCTION", dep))
    schemas = (f"{p}schema",) if needs_schema else ()
    roles = _role_names(case, p, effective)
    role_list = list(roles)
    pre_bookend = build_pre_cleanup(
        specs=tuple(specs),
        schemas=schemas,
        roles=role_list,
    )
    cln_bookend = build_cleanup(
        specs=tuple(specs),
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


def resolve_drop_procedure_factor_witness(
    case: DropProcedureFactorCase | DropProcedureFactorExtensionCase,
    repository_root: Path,
) -> DropProcedureFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropProcedureFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_procedure(sql: str) -> int:
    """Count the single credited DROP PROCEDURE inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*DROP\s+PROCEDURE\b", region)
    )


def _header(case: DropProcedureFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP PROCEDURE {case.factor_key}={case.factor_value}",
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


def render_drop_procedure_factor_case(
    case: DropProcedureFactorCase | DropProcedureFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP PROCEDURE regress program."""

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地过程和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP PROCEDURE。")
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


def generate_drop_procedure_factor_programs(
    baseline_plan: DropProcedureFactorLoopPlan,
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
    case: DropProcedureFactorCase | DropProcedureFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_procedure_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropProcedureFactorRenderError",
    "DropProcedureFactorWitness",
    "count_primary_drop_procedure",
    "generate_drop_procedure_factor_programs",
    "render_drop_procedure_factor_case",
    "resolve_drop_procedure_factor_witness",
]
