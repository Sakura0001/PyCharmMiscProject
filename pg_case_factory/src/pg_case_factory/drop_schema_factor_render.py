"""Render complete PostgreSQL 18.4 DROP SCHEMA factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.
The file is assembled from a single :func:`_resolve_case` plan so that the
byte-level witness validator (which re-renders and compares) can never diverge
from the bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_namespace WHERE nspname = ...``
never nests a ``FROM`` inside an ``EXISTS`` subquery, and every catalog SELECT
carries a top-level ``ORDER BY``.  ``nspname`` is the real pg_namespace column
(PG18: oid, nspname, nspowner, nspacl).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .drop_schema_factor_extension import (
    DropSchemaFactorExtensionCase,
)
from .drop_schema_factor_loop import (
    DropSchemaFactorCase,
    DropSchemaFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/schema/"
    "drop_schema.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/schema/"
    "drop_schema.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

# Primary (factor, value) pairs where the target schema is intentionally
# absent, so the drop surfaces a not-found error (or a NOTICE under IF EXISTS)
# and the oracle asserts absence.
_ABSENT_PRIMARIES = frozenset(
    {
        ("object_state", "not_exists"),
        ("error_boundary", "non_existent_without_if_exists"),
        ("expected_status", "failure"),
    }
)

# For an extension SUCCESS case (no present failure pair) the synthetic
# primary must be a neutral success primary; the schema exists (empty) in
# extensions unless the assignment selects not_exists.
_BRANCH_NEUTRAL_SUCCESS = ("object_state", "exists_empty")


def _synthetic_case(
    ext: DropSchemaFactorExtensionCase,
) -> DropSchemaFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .drop_schema_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropSchemaFactorCase(
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
    case: DropSchemaFactorCase | DropSchemaFactorExtensionCase,
) -> DropSchemaFactorCase:
    if isinstance(case, DropSchemaFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropSchemaFactorRenderError(ValueError):
    """Raised when a DROP SCHEMA case cannot be rendered."""


@dataclass(frozen=True)
class DropSchemaFactorWitness:
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


def _baseline(case: DropSchemaFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _schema_name(a: dict[str, str], p: str) -> str:
    """The schema name as referenced inside DROP SCHEMA (may be quoted)."""

    shape = a.get("schema_name_shape", "simple")
    if shape == "quoted":
        return f'"{p}schq"'
    if shape == "reserved_word":
        return f'"{p}reserved"'
    # simple and schema_qualified (schemas cannot be schema-qualified; the
    # degenerate schema_qualified shape renders as a plain identifier).
    return f"{p}sch"


def _probe_schema_name(a: dict[str, str], p: str) -> str:
    """The bare schema name (no quotes) for the pg_namespace catalog probe."""

    shape = a.get("schema_name_shape", "simple")
    if shape == "quoted":
        return f"{p}schq"
    if shape == "reserved_word":
        return f"{p}reserved"
    return f"{p}sch"


def _effective_object_state(
    case: DropSchemaFactorCase, a: dict[str, str]
) -> str:
    """Resolve the schema's effective object state for fixture creation.

    The marginal baseline can pair a primary contained_objects_state value
    with the default object_state; contained objects or a cross-schema
    dependency force the schema to effectively hold objects.
    """

    contained = a.get("contained_objects_state", "empty_schema")
    cross = a.get("cross_schema_dependency", "no_cross_dependency")
    object_state = a.get("object_state", "exists_empty")
    if case.kind != "EXT" and case.factor_key == "object_state":
        object_state = case.factor_value
    if contained != "empty_schema" or cross != "no_cross_dependency":
        object_state = "exists_with_objects"
    return object_state


def _schema_exists(case: DropSchemaFactorCase, a: dict[str, str]) -> bool:
    if case.kind != "EXT" and (
        case.factor_key, case.factor_value
    ) in _ABSENT_PRIMARIES:
        return False
    return _effective_object_state(case, a) != "not_exists"


def _if_exists_present(
    case: DropSchemaFactorCase, a: dict[str, str]
) -> bool:
    if case.kind == "EXT":
        return a.get("if_exists_clause") == "present"
    # baseline: the if_exists_clause factor and statement_branch both speak
    if case.factor_key == "if_exists_clause":
        return case.factor_value == "present"
    if case.factor_key == "statement_branch":
        return case.factor_value == "branch_drop_schema_if_exists"
    return a.get("if_exists_clause") == "present"


def _cascade_clause(a: dict[str, str]) -> str:
    cascade = a.get("cascade_restrict", "none")
    if cascade == "cascade":
        return "CASCADE"
    if cascade == "restrict":
        return "RESTRICT"
    return ""  # none: RESTRICT is the default


def _is_multi_schema(
    case: DropSchemaFactorCase, a: dict[str, str]
) -> bool:
    if case.kind == "EXT":
        return a.get("multi_schema_drop") == "multi_schema"
    if case.factor_key == "multi_schema_drop":
        return case.factor_value == "multi_schema"
    return a.get("multi_schema_drop") == "multi_schema"


def _effective_role(
    case: DropSchemaFactorCase, a: dict[str, str]
) -> str:
    """The session role under which the target DROP SCHEMA runs.

    owner and non_owner both install a role fixture; non_owner runs as a
    non-owning role (privilege fires first), owner runs as the schema owner.
    """

    if case.kind == "EXT":
        level = a.get("privilege_level", "superuser")
        return "actor" if level in ("non_owner", "owner") else ""
    if case.factor_key == "privilege_level":
        return "actor"
    return ""


def _needs_referenced_table(
    case: DropSchemaFactorCase, a: dict[str, str]
) -> bool:
    """Whether a table inside {p}sch is created (bookend gate trigger)."""

    contained = a.get("contained_objects_state", "empty_schema")
    cross = a.get("cross_schema_dependency", "no_cross_dependency")
    if contained in ("has_tables", "has_multiple_object_types"):
        return True
    if cross != "no_cross_dependency":
        return True  # cross-schema FK/view references a {p}sch table
    if case.kind == "EXT":
        return False
    if case.factor_key == "contained_objects_state":
        return case.factor_value in (
            "has_tables",
            "has_multiple_object_types",
        )
    if case.factor_key == "cross_schema_dependency":
        return case.factor_value != "no_cross_dependency"
    return False


def _schema_absent_after(
    case: DropSchemaFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target schema is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if not _schema_exists(case, a):
        return True
    if case.outcome == "success":
        return True
    return False


def _probe_select(
    case: DropSchemaFactorCase, a: dict[str, str], p: str
) -> str:
    name = _probe_schema_name(a, p)
    absent = _schema_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "schema_absent" if absent else "schema_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_namespace "
        f"WHERE nspname = '{name}' ORDER BY count(*) LIMIT 1;"
    )


def _contained_fixtures(a: dict[str, str], p: str) -> list[str]:
    lines: list[str] = []
    contained = a.get("contained_objects_state", "empty_schema")
    if contained in ("has_tables", "has_multiple_object_types"):
        lines.append(f"CREATE TABLE {p}sch.{p}t (c integer);")
    if contained in ("has_views", "has_multiple_object_types"):
        lines.append(f"CREATE VIEW {p}sch.{p}v AS SELECT 1 AS c;")
    if contained in ("has_functions", "has_multiple_object_types"):
        lines.append(
            f"CREATE FUNCTION {p}sch.{p}f() RETURNS void "
            "AS $$ BEGIN END; $$ LANGUAGE plpgsql;"
        )
    return lines


def _cross_schema_fixtures(a: dict[str, str], p: str) -> list[str]:
    cross = a.get("cross_schema_dependency", "no_cross_dependency")
    if cross == "no_cross_dependency":
        return []
    lines: list[str] = [f"CREATE SCHEMA {p}sch2;"]
    if cross == "has_cross_schema_fk":
        lines.append(
            f"CREATE TABLE {p}sch2.{p}t2 "
            f"(c integer REFERENCES {p}sch.{p}t(c));"
        )
    elif cross == "has_cross_schema_view":
        lines.append(
            f"CREATE VIEW {p}sch2.{p}v2 AS SELECT * FROM {p}sch.{p}t;"
        )
    return lines


def _role_name(p: str) -> str:
    return f"{p}actor"


def _resolve_case(case: DropSchemaFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    schema_exists = _schema_exists(case, a)
    sch_name = _schema_name(a, p)
    needs_table = _needs_referenced_table(case, a)
    needs_sch2 = _is_multi_schema(case, a) or a.get(
        "cross_schema_dependency", "no_cross_dependency"
    ) != "no_cross_dependency"
    effective = _effective_role(case, a)

    setup: list[str] = []
    locus = "target.schema_namespace"

    # --- role fixture (CREATE only; SET ROLE deferred to after fixtures) ----
    if effective:
        level = a.get("privilege_level", "superuser") if case.kind == "EXT" else (
            case.factor_value if case.factor_key == "privilege_level"
            else a.get("privilege_level", "superuser")
        )
        if level == "non_owner":
            setup.append(
                f"CREATE ROLE {_role_name(p)} LOGIN NOSUPERUSER;"
            )
        else:
            setup.append(f"CREATE ROLE {_role_name(p)} LOGIN;")
        locus = "fixture.privilege_state"

    # --- target schema fixture (as superuser, before SET ROLE) -------------
    if schema_exists:
        auth = ""
        if effective:
            level = a.get("privilege_level", "superuser") if case.kind == "EXT" else (
                case.factor_value if case.factor_key == "privilege_level"
                else a.get("privilege_level", "superuser")
            )
            if level == "owner":
                auth = f" AUTHORIZATION {_role_name(p)}"
        setup.append(f"CREATE SCHEMA {sch_name}{auth};")
        setup.extend(_contained_fixtures(a, p))
        if (
            a.get("cross_schema_dependency", "no_cross_dependency")
            != "no_cross_dependency"
            and not _contained_fixtures(a, p)
        ):
            # cross-schema FK/view needs a referenced table in {p}sch
            setup.append(f"CREATE TABLE {p}sch.{p}t (c integer);")
        setup.extend(_cross_schema_fixtures(a, p))
        if _is_multi_schema(case, a) and a.get(
            "cross_schema_dependency", "no_cross_dependency"
        ) == "no_cross_dependency":
            setup.append(f"CREATE SCHEMA {p}sch2;")
    else:
        setup.append("SELECT 1 AS target_schema_intentionally_absent;")
        locus = "fixture.object_state"

    # --- arm the role (AFTER schema creation) -------------------------------
    if effective:
        setup.append(f"SET ROLE {_role_name(p)};")

    # --- target DROP SCHEMA ------------------------------------------------
    if_exists = "IF EXISTS " if _if_exists_present(case, a) else ""
    cascade = _cascade_clause(a)
    if _is_multi_schema(case, a):
        name_list = f"{sch_name}, {p}sch2"
    else:
        name_list = sch_name
    target = f"DROP SCHEMA {if_exists}{name_list}"
    if cascade:
        target += f" {cascade}"
    target += ";"

    # RISK transaction wrapper around the target.
    if case.kind == "RISK":
        setup.append("BEGIN;")
        locus = "target.transaction_boundary"

    # --- oracle / SQLSTATE assertion ---------------------------------------
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

    # --- cleanup construction (bookend split) -------------------------------
    role = _role_name(p)
    role_drops: list[str] = []
    if effective:
        role_drops = [
            f"DROP OWNED BY {role};",
            f"DROP ROLE IF EXISTS {role};",
        ]
    # Drop every schema-qualified table this script created, as a single
    # multi-target DROP TABLE statement.  The bookend gate requires the FIRST
    # and LAST executable statement to EACH be a DROP TABLE IF EXISTS listing
    # every created table (matched by set membership, schema-qualified and
    # lowercased -- exactly as the CREATE TABLE statements emit them).
    _table_targets: list[str] = []
    if needs_table:
        _table_targets.append(f"{p}sch.{p}t")
    if (
        a.get("cross_schema_dependency", "no_cross_dependency")
        == "has_cross_schema_fk"
    ):
        _table_targets.append(f"{p}sch2.{p}t2")
    table_drop = (
        [f"DROP TABLE IF EXISTS {', '.join(_table_targets)} CASCADE;"]
        if _table_targets
        else []
    )
    sch2_drop = (
        [f"DROP SCHEMA IF EXISTS {p}sch2 CASCADE;"] if needs_sch2 else []
    )
    sch_drop = f"DROP SCHEMA IF EXISTS {sch_name} CASCADE;"

    # Pre-cleanup: DROP TABLE first (bookend lead), then schemas, then roles.
    pre_cleanup: list[str] = []
    pre_cleanup.extend(table_drop)
    pre_cleanup.append(sch_drop)
    pre_cleanup.extend(sch2_drop)
    pre_cleanup.extend(role_drops)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # Cleanup: RESET ROLE, schema drops, role drops, then DROP TABLE last
    # (bookend tail).
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.append(sch_drop)
    cleanup.extend(sch2_drop)
    cleanup.extend(role_drops)
    cleanup.extend(table_drop)
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


def resolve_drop_schema_factor_witness(
    case: DropSchemaFactorCase | DropSchemaFactorExtensionCase,
    repository_root: Path,
) -> DropSchemaFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropSchemaFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_schema(sql: str) -> int:
    """Count the single credited DROP SCHEMA inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*DROP\s+SCHEMA\b", region)
    )


def _header(case: DropSchemaFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP SCHEMA {case.factor_key}={case.factor_value}",
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


def render_drop_schema_factor_case(
    case: DropSchemaFactorCase | DropSchemaFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP SCHEMA regress program."""

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    if _needs_referenced_table(rc, a := _baseline(rc)):
        # segment-merge boundary: a leading SELECT prevents the first real
        # setup statement from merging with the \set meta-command when a table
        # is created (siblings drop_owned/drop_policy require this).
        lines.append("SELECT 1 AS setup_boundary;")
    lines.append("-- 2. 创建完整本地 Schema 和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP SCHEMA。")
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


def generate_drop_schema_factor_programs(
    baseline_plan: DropSchemaFactorLoopPlan,
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
    case: DropSchemaFactorCase | DropSchemaFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_schema_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropSchemaFactorRenderError",
    "DropSchemaFactorWitness",
    "count_primary_drop_schema",
    "generate_drop_schema_factor_programs",
    "render_drop_schema_factor_case",
    "resolve_drop_schema_factor_witness",
]
