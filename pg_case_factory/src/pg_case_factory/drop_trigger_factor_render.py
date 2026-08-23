"""Render complete PostgreSQL 18.4 DROP TRIGGER factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_trigger WHERE
tgname = '...' ORDER BY count(*) LIMIT 1`` never nests a ``FROM``
inside an ``EXISTS`` subquery, so ``audit_catalog_observability`` accepts it.
The probe column is a real ``pg_trigger`` column (``tgname``) — the no-DB
tickoff does not execute this probe, so a wrong column would pass all
static gates yet be a permanent latent runtime bug; the column is verified.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .cleanup_bookend import (
    DropSpec,
    OnDropSpec,
    build_cleanup,
    build_pre_cleanup,
)
from .drop_trigger_factor_extension import (
    DropTriggerFactorExtensionCase,
)
from .drop_trigger_factor_loop import (
    DropTriggerFactorCase,
    DropTriggerFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/trigger/drop_trigger.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/trigger/drop_trigger.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

# Baseline primaries whose target trigger is intentionally absent, so the DROP
# surfaces a not-found error (42704) and the oracle asserts absence.
_ABSENT_TRIGGER_PRIMARIES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "not_exists"),
        ("target_trigger_not_exists", "without_IF_EXISTS_error"),
        ("identifier_length_exceeded", "over_63_chars"),
    }
)

# Baseline primaries whose host relation is intentionally absent, so the DROP
# surfaces a relation-missing error (42P01) and no table is created.
_TABLE_MISSING_PRIMARIES = frozenset(
    {
        ("table_dependency", "table_not_exists"),
    }
)

# Baseline primaries that imply a dependent-object fixture must be created.
_DEPENDENCY_PRIMARIES = frozenset(
    {
        ("dependent_objects", "has_dependents_restrict_blocks"),
    }
)

# For an extension SUCCESS case (no present failure pair) the synthetic
# primary must be a neutral success primary whose helpers fall through to the
# assignment; the trigger always exists in extensions (object_state held at
# exists) unless object_state=not_exists.
_BRANCH_NEUTRAL_SUCCESS = ("object_state", "exists")


def _synthetic_case(
    ext: DropTriggerFactorExtensionCase,
) -> DropTriggerFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .drop_trigger_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropTriggerFactorCase(
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
    case: DropTriggerFactorCase | DropTriggerFactorExtensionCase,
) -> DropTriggerFactorCase:
    if isinstance(case, DropTriggerFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropTriggerFactorRenderError(ValueError):
    """Raised when a DROP TRIGGER case cannot be rendered."""


@dataclass(frozen=True)
class DropTriggerFactorWitness:
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


def _baseline(case: DropTriggerFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _host_kind(case: DropTriggerFactorCase, a: dict[str, str]) -> str:
    """Whether the host is a table or absent."""

    if a.get("table_dependency") == "table_not_exists":
        return "none"
    return "table"


def _table_shape_ref(shape: str, bare: str, quoted: str, schema: str) -> str:
    if shape == "quoted":
        return quoted
    if shape == "schema_qualified":
        return schema
    return bare


def _host_ref(case: DropTriggerFactorCase, a: dict[str, str], p: str) -> str:
    """The table name as referenced inside DROP TRIGGER ON target."""

    shape = a.get("table_name_shape", "simple")
    return _table_shape_ref(shape, f"{p}t", f'"{p}qt"', f"public.{p}t")


def _host_probe(case: DropTriggerFactorCase, a: dict[str, str], p: str) -> str:
    """The bare relname (no quotes/schema) for the catalog probe.

    The fixture base table is always created with a plain unqualified name so
    the bookend gate's identifier normalizer accepts it.  The stored relname
    is therefore always the plain form, regardless of ``table_name_shape``.
    """

    return f"{p}t"


def _base_table_ref(case: DropTriggerFactorCase, a: dict[str, str], p: str) -> str:
    """The base TABLE the case CREATEs (for bookend DROP TABLE).

    Always the plain unqualified ``{p}t`` so the bookend gate can normalize
    the CREATE/DROP TABLE identifiers; the quoted/schema-qualified shape is
    carried only by :func:`_host_ref` inside the DROP TRIGGER ON target.
    """

    kind = _host_kind(case, a)
    if kind == "none":
        return ""
    return f"{p}t"


def _trigger_ref(case: DropTriggerFactorCase, a: dict[str, str], p: str) -> str:
    """The trigger name as referenced inside DROP TRIGGER (quoted when needed)."""

    if case.kind != "EXT" and case.factor_key == "identifier_length_exceeded":
        return f"{p}{'a' * 64}"
    shape = a.get("trigger_name_shape", "simple")
    if shape == "quoted":
        return f'"{p}qtrg"'
    if shape == "reserved_word":
        return '"select"'
    return f"{p}trg"


def _trigger_probe(case: DropTriggerFactorCase, a: dict[str, str], p: str) -> str:
    """The bare trigger name (no quotes) for the catalog probe."""

    if case.kind != "EXT" and case.factor_key == "identifier_length_exceeded":
        return f"{p}{'a' * 64}"
    shape = a.get("trigger_name_shape", "simple")
    if shape == "quoted":
        return f"{p}qtrg"
    if shape == "reserved_word":
        return "select"
    return f"{p}trg"


def _trigger_created(case: DropTriggerFactorCase, a: dict[str, str]) -> bool:
    """Whether a trigger fixture must be created on the host.

    ``target_trigger_not_exists`` defaults to ``without_IF_EXISTS_error`` for
    every case, but it only describes a hypothetical absent-trigger scenario.
    It should suppress trigger creation only when it is the case's *primary*
    factor (baseline) — never as a background default.  Trigger existence is
    otherwise governed by ``object_state`` (``exists`` → created,
    ``not_exists`` → absent).
    """

    if _host_kind(case, a) == "none":
        return False
    if a.get("object_state") == "not_exists":
        return False
    if case.kind != "EXT":
        if (case.factor_key, case.factor_value) in _ABSENT_TRIGGER_PRIMARIES:
            return False
        if case.factor_key == "target_trigger_not_exists":
            return False
    return True


def _if_exists_present(case: DropTriggerFactorCase, a: dict[str, str]) -> bool:
    return a.get("if_exists_clause") == "present"


def _cascade_clause(a: dict[str, str]) -> str:
    cascade = a.get("cascade_restrict_clause", "absent")
    if cascade == "CASCADE":
        return "CASCADE"
    if cascade == "RESTRICT":
        return "RESTRICT"
    return ""  # absent: RESTRICT is the default


def _effective_role(
    case: DropTriggerFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP TRIGGER runs."""

    if case.kind == "EXT":
        level = a.get("privilege_level", "superuser")
        return f"{p}actor" if level == "non_owner_no_privilege" else ""
    if case.factor_key == "privilege_level":
        return f"{p}actor" if case.factor_value == "non_owner_no_privilege" else ""
    if case.factor_key == "permission_insufficient":
        return f"{p}actor" if case.factor_value == "not_table_owner" else ""
    return ""


def _needs_dependent(
    case: DropTriggerFactorCase, a: dict[str, str]
) -> bool:
    """Whether a dependent object fixture must be created."""

    if case.kind == "EXT":
        return a.get("dependent_objects") == "has_dependents_restrict_blocks"
    if (case.factor_key, case.factor_value) in _DEPENDENCY_PRIMARIES:
        return True
    return a.get("dependent_objects") == "has_dependents_restrict_blocks"


def _trigger_absent_after(
    case: DropTriggerFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target trigger is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if _host_kind(case, a) == "none":
        return True
    if not _trigger_created(case, a):
        return True
    if case.outcome == "success":
        return True
    return False


def _probe_select(
    case: DropTriggerFactorCase, a: dict[str, str], p: str
) -> str:
    trigger_probe = _trigger_probe(case, a, p)
    absent = _trigger_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "trigger_absent" if absent else "trigger_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_trigger "
        f"WHERE tgname = '{trigger_probe}' "
        "ORDER BY count(*) LIMIT 1;"
    )


def _role_names(
    case: DropTriggerFactorCase, p: str, effective: str
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}actor":
        roles.append(f"{p}actor")
    return tuple(roles)


def _resolve_case(case: DropTriggerFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    host_kind = _host_kind(case, a)
    host_ref = _host_ref(case, a, p)
    base_table = _base_table_ref(case, a, p)
    trigger_ref = _trigger_ref(case, a, p)
    trigger_created = _trigger_created(case, a)
    needs_dep = _needs_dependent(case, a)

    setup: list[str] = []
    locus = "target.trigger"

    # --- setup boundary SELECT (prevents \set from merging with the first
    # CREATE TABLE so the bookend gate detects the table at col 0) ---
    if host_kind != "none":
        setup.append("SELECT 1 AS setup_boundary;")

    # --- role fixtures (CREATE only; SET ROLE deferred to after the trigger
    # fixture so they run as the superuser) ---
    effective = _effective_role(case, a, p)
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- the host base TABLE (as superuser, before SET ROLE) ---
    if host_kind != "none":
        setup.append(f"CREATE TABLE {base_table} (c integer);")
        if locus == "target.trigger":
            locus = "fixture.host_table"

    # --- the trigger function + trigger fixture (as superuser, before SET
    # ROLE).  The function always uses a plain name; only the trigger name
    # varies by trigger_name_shape. ---
    if host_kind != "none" and trigger_created:
        setup.append(
            f"CREATE FUNCTION {p}fn() RETURNS trigger "
            "LANGUAGE plpgsql AS $$ BEGIN RETURN NULL; END; $$;"
        )
        if locus == "fixture.host_table":
            locus = "fixture.trigger_function"
        setup.append(
            f"CREATE TRIGGER {trigger_ref} BEFORE INSERT ON {base_table} "
            f"FOR EACH ROW EXECUTE FUNCTION {p}fn();"
        )
        if locus in ("fixture.trigger_function", "fixture.host_table"):
            locus = "fixture.trigger"
    elif host_kind != "none" and not trigger_created:
        setup.append(
            "SELECT 1 AS target_trigger_intentionally_absent;"
        )
        locus = "fixture.object_state"

    # --- dependent object fixture (as superuser, before SET ROLE) -------
    if needs_dep:
        setup.append(
            f"CREATE VIEW {p}depv AS SELECT * FROM {base_table};"
        )
        locus = "fixture.dependency_state"

    # --- arm the non-superuser role (AFTER trigger creation) ------------
    if effective:
        setup.append(f"SET ROLE {p}actor;")
    if_exists = "IF EXISTS " if _if_exists_present(case, a) else ""
    cascade = _cascade_clause(a)
    target = f"DROP TRIGGER {if_exists}{trigger_ref} ON {host_ref}"
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

    # --- cleanup construction (idempotent bookends via cleanup_bookend) ---
    # The TRIGGER drop is shape A (ON <table>) and goes through complex_specs.
    # It is routed to build_cleanup only: in pre_cleanup the table is dropped
    # first (CASCADE removes the trigger), so a later DROP TRIGGER ON <table>
    # would error on the missing relation.  IF EXISTS on the trigger does not
    # suppress a missing-table error, so the trigger stays out of pre_cleanup.
    cleanup_specs: list[DropSpec] = []
    complex_specs: tuple[OnDropSpec, ...] = ()
    if host_kind != "none":
        cleanup_specs.append(DropSpec("FUNCTION", f"{p}fn", args="()"))
        complex_specs = (OnDropSpec("TRIGGER", trigger_ref, base_table),)
    if needs_dep:
        cleanup_specs.append(DropSpec("VIEW", f"{p}depv"))
    roles = _role_names(case, p, effective)
    tables = (base_table,) if host_kind != "none" else ()

    pre_cleanup_bk = build_pre_cleanup(
        tables=tables,
        specs=tuple(cleanup_specs),
        roles=tuple(roles),
    )
    cleanup_bk = build_cleanup(
        tables=tables,
        specs=tuple(cleanup_specs),
        complex_specs=complex_specs,
        roles=tuple(roles),
        drop_owned=bool(roles),
        reset_role=effective,
    )
    pre_cleanup = list(pre_cleanup_bk.statements)
    cleanup = list(cleanup_bk.statements)

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


def resolve_drop_trigger_factor_witness(
    case: DropTriggerFactorCase | DropTriggerFactorExtensionCase,
    repository_root: Path,
) -> DropTriggerFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropTriggerFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_trigger(sql: str) -> int:
    """Count the single credited DROP TRIGGER inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*DROP\s+TRIGGER\b", region)
    )


def _header(case: DropTriggerFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP TRIGGER {case.factor_key}={case.factor_value}",
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


def render_drop_trigger_factor_case(
    case: DropTriggerFactorCase | DropTriggerFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP TRIGGER regress program."""

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地触发器和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP TRIGGER。")
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


def generate_drop_trigger_factor_programs(
    baseline_plan: DropTriggerFactorLoopPlan,
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
    case: DropTriggerFactorCase | DropTriggerFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_trigger_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropTriggerFactorRenderError",
    "DropTriggerFactorWitness",
    "count_primary_drop_trigger",
    "generate_drop_trigger_factor_programs",
    "render_drop_trigger_factor_case",
    "resolve_drop_trigger_factor_witness",
]
