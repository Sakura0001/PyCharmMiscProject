"""Render complete PostgreSQL 18.4 DROP TABLE factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_class WHERE relname = '...'
AND relkind = 'r' ORDER BY count(*) LIMIT 1`` never nests a ``FROM``
inside an ``EXISTS`` subquery, so ``audit_catalog_observability`` accepts it.
The probe columns are real ``pg_class`` columns (``relname``, ``relkind``) —
the no-DB tickoff does not execute this probe, so a wrong column would pass all
static gates yet be a permanent latent runtime bug; the columns are verified.
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
from .drop_table_factor_extension import (
    DropTableFactorExtensionCase,
)
from .drop_table_factor_loop import (
    DropTableFactorCase,
    DropTableFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/table/drop_table.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/table/drop_table.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-21"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

# Baseline primaries whose target table is intentionally absent, so the DROP
# surfaces a not-found error (42P01) and the oracle asserts absence.
_ABSENT_TABLE_PRIMARIES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "not_exists"),
        ("error_boundary", "non_existent_without_if_exists"),
    }
)

# Baseline primaries that imply a dependent-object fixture must be created.
_DEPENDENCY_PRIMARIES = frozenset(
    {
        ("dependency_state", "has_views"),
        ("dependency_state", "has_fk_references"),
        ("error_boundary", "dependent_objects_without_cascade"),
    }
)

# Baseline primaries that imply a non-owner role fixture.
_PRIVILEGE_PRIMARIES = frozenset(
    {
        ("privilege_level", "non_owner"),
        ("error_boundary", "insufficient_privilege"),
    }
)

# Baseline primaries that simulate a table-in-use boundary.
_IN_USE_PRIMARIES = frozenset(
    {
        ("error_boundary", "drop_table_in_use"),
    }
)

# Baseline primaries that create a self-referential FK table.
_SELF_FK_PRIMARIES = frozenset(
    {
        ("error_boundary", "self_referential_fk"),
    }
)

# For an extension SUCCESS case (no present failure pair) the synthetic
# primary must be a neutral success primary whose helpers fall through to the
# assignment; the table always exists in extensions (object_state held at
# exists_permanent) unless object_state=not_exists.
_BRANCH_NEUTRAL_SUCCESS = ("object_state", "exists_permanent")


def _synthetic_case(
    ext: DropTableFactorExtensionCase,
) -> DropTableFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .drop_table_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropTableFactorCase(
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
    case: DropTableFactorCase | DropTableFactorExtensionCase,
) -> DropTableFactorCase:
    if isinstance(case, DropTableFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropTableFactorRenderError(ValueError):
    """Raised when a DROP TABLE case cannot be rendered."""


@dataclass(frozen=True)
class DropTableFactorWitness:
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


def _baseline(case: DropTableFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _table_created(case: DropTableFactorCase, a: dict[str, str]) -> bool:
    """Whether the target table is created as a fixture."""

    if a.get("object_state") == "not_exists":
        return False
    if (case.factor_key, case.factor_value) in _ABSENT_TABLE_PRIMARIES:
        return False
    if case.kind == "EXT":
        return a.get("object_state") != "not_exists"
    return True


def _table_create_kind(a: dict[str, str]) -> str:
    """permanent / temporary / unlogged based on assignment."""

    obj = a.get("object_state", "exists_permanent")
    if obj == "exists_temporary":
        return "temporary"
    if obj == "exists_unlogged":
        return "unlogged"
    ttp = a.get("table_type_permanence", "permanent")
    if ttp == "temporary":
        return "temporary"
    if ttp == "unlogged":
        return "unlogged"
    return "permanent"


def _table_create_ref(case: DropTableFactorCase, a: dict[str, str], p: str) -> str:
    """The unquoted base table name used in CREATE TABLE and bookend DROP TABLE.

    This is deliberately UNQUOTED for every name_shape: the shared
    ``audit_complete_table_script`` gate (``_normalize_identifier`` /
    ``_split_identifier_list``) rejects ``"`` characters, so a quoted
    fixture name would leave ``created_tables`` empty and break the
    bookend (first/last must be ``DROP TABLE IF EXISTS``).  The bare
    lowercase identifier is the same object the quoted/ shaped
    ``_table_drop_ref`` target drops, so the factor is still exercised
    by the credited DROP TABLE while the fixture stays gate-parseable.
    """

    shape = a.get("table_name_shape", "simple")
    if shape == "quoted":
        return f"{p}qt"
    if shape == "reserved_word":
        return f"{p}select"
    return f"{p}t"


def _table_drop_ref(case: DropTableFactorCase, a: dict[str, str], p: str) -> str:
    """The table name used in the DROP TABLE target (shaped)."""

    shape = a.get("table_name_shape", "simple")
    if shape == "quoted":
        return f'"{p}qt"'
    if shape == "schema_qualified":
        return f"public.{p}t"
    if shape == "non_existent":
        return f"{p}noexist"
    if shape == "reserved_word":
        return f'"{p}select"'
    return f"{p}t"


def _table_probe_name(case: DropTableFactorCase, a: dict[str, str], p: str) -> str:
    """The bare relname (no quotes/schema) for the catalog probe."""

    shape = a.get("table_name_shape", "simple")
    if shape == "quoted":
        return f"{p}qt"
    if shape == "reserved_word":
        return f"{p}select"
    return f"{p}t"


def _table_columns(case: DropTableFactorCase, a: dict[str, str], p: str) -> str:
    """Column definition for CREATE TABLE, depends on dependency kind."""

    dep = _dependency_kind(case, a)
    if dep == "fk":
        return "(id integer PRIMARY KEY, c integer)"
    if dep == "self_fk":
        return f"(id integer PRIMARY KEY, parent_id integer REFERENCES {p}t(id))"
    return "(c integer)"


def _dependency_kind(case: DropTableFactorCase, a: dict[str, str]) -> str:
    """The kind of dependency fixture, or 'none'."""

    if case.kind == "EXT":
        dep = a.get("dependency_state", "no_dependents")
        if dep in ("has_views", "has_fk_references", "has_triggers",
                    "has_indexes", "has_policies", "has_rules"):
            return dep
        return "none"
    if (case.factor_key, case.factor_value) in _DEPENDENCY_PRIMARIES:
        if case.factor_key == "error_boundary":
            return "has_views"
        return case.factor_value
    if (case.factor_key, case.factor_value) in _SELF_FK_PRIMARIES:
        return "self_fk"
    dep = a.get("dependency_state", "no_dependents")
    if dep in ("has_views", "has_fk_references", "has_triggers",
                "has_indexes", "has_policies", "has_rules"):
        return dep
    return "none"


def _is_multi_table(case: DropTableFactorCase, a: dict[str, str]) -> bool:
    if case.kind == "EXT":
        return a.get("multi_table_drop") == "multi_table"
    return case.factor_key == "multi_table_drop" and case.factor_value == "multi_table"


def _if_exists_present(case: DropTableFactorCase, a: dict[str, str]) -> bool:
    return a.get("if_exists_clause") == "present"


def _cascade_clause(a: dict[str, str]) -> str:
    cascade = a.get("cascade_restrict", "none")
    if cascade == "cascade":
        return "CASCADE"
    if cascade == "restrict":
        return "RESTRICT"
    return ""  # none: RESTRICT is the default


def _effective_role(
    case: DropTableFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP TABLE runs."""

    if case.kind == "EXT":
        level = a.get("privilege_level", "owner")
        return f"{p}actor" if level == "non_owner" else ""
    if case.factor_key == "privilege_level":
        return f"{p}actor" if case.factor_value == "non_owner" else ""
    if (case.factor_key, case.factor_value) in _PRIVILEGE_PRIMARIES:
        return f"{p}actor"
    return ""


def _is_in_use_case(case: DropTableFactorCase, a: dict[str, str]) -> bool:
    if case.kind == "EXT":
        return False
    return (case.factor_key, case.factor_value) in _IN_USE_PRIMARIES


def _table_absent_after(
    case: DropTableFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target table is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if not _table_created(case, a):
        return True
    if case.outcome == "success":
        return True
    return False


def _probe_select(
    case: DropTableFactorCase, a: dict[str, str], p: str
) -> str:
    probe_name = _table_probe_name(case, a, p)
    absent = _table_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "table_absent" if absent else "table_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_class "
        f"WHERE relname = '{probe_name}' AND relkind = 'r' "
        "ORDER BY count(*) LIMIT 1;"
    )


def _role_names(
    case: DropTableFactorCase, p: str, effective: str
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}actor":
        roles.append(f"{p}actor")
    return tuple(roles)


def _created_table_refs(
    case: DropTableFactorCase, a: dict[str, str], p: str
) -> list[str]:
    """All table names created by this case (for bookend DROP TABLE)."""

    refs: list[str] = []
    if _table_created(case, a):
        refs.append(_table_create_ref(case, a, p))
    if _dependency_kind(case, a) == "fk":
        refs.append(f"{p}fkt")
    if _is_multi_table(case, a):
        refs.append(f"{p}mt2")
    return refs


def _resolve_case(case: DropTableFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    table_created = _table_created(case, a)
    create_ref = _table_create_ref(case, a, p)
    drop_ref = _table_drop_ref(case, a, p)
    dep_kind = _dependency_kind(case, a)
    effective = _effective_role(case, a, p)
    in_use = _is_in_use_case(case, a)
    is_multi = _is_multi_table(case, a)

    setup: list[str] = []
    locus = "target.table"

    # --- setup boundary SELECT (prevents \set from merging with the first
    # CREATE TABLE so the bookend gate detects the table at col 0) ---
    if table_created:
        setup.append("SELECT 1 AS setup_boundary;")

    # --- role fixtures (CREATE only; SET ROLE deferred to after fixtures) ---
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- the target TABLE (as superuser, before SET ROLE) ---
    if table_created:
        kind = _table_create_kind(a)
        cols = _table_columns(case, a, p)
        if kind == "temporary":
            setup.append(f"CREATE TEMPORARY TABLE {create_ref} {cols};")
        elif kind == "unlogged":
            setup.append(f"CREATE UNLOGGED TABLE {create_ref} {cols};")
        else:
            setup.append(f"CREATE TABLE {create_ref} {cols};")
        locus = "fixture.target_table"

    # --- dependent object fixtures ---
    if dep_kind == "view":
        setup.append(f"CREATE VIEW {p}depv AS SELECT * FROM {create_ref};")
        locus = "fixture.dependency_view"
    elif dep_kind == "fk":
        setup.append(
            f"CREATE TABLE {p}fkt (id integer, fk integer REFERENCES {create_ref}(id));"
        )
        locus = "fixture.dependency_fk"
    elif dep_kind == "trigger":
        setup.append(
            f"CREATE FUNCTION {p}trgfn() RETURNS trigger AS "
            "$$ BEGIN RETURN NEW; END; $$ LANGUAGE plpgsql;"
        )
        setup.append(
            f"CREATE TRIGGER {p}trg BEFORE INSERT ON {create_ref} "
            f"FOR EACH ROW EXECUTE FUNCTION {p}trgfn();"
        )
        locus = "fixture.dependency_trigger"
    elif dep_kind == "index":
        setup.append(f"CREATE INDEX {p}idx ON {create_ref} (c);")
        locus = "fixture.dependency_index"
    elif dep_kind == "policy":
        setup.append(f"ALTER TABLE {create_ref} ENABLE ROW LEVEL SECURITY;")
        setup.append(f"CREATE POLICY {p}pol ON {create_ref} USING (true);")
        locus = "fixture.dependency_policy"
    elif dep_kind == "rule":
        setup.append(
            f"CREATE RULE {p}rl AS ON INSERT TO {create_ref} DO INSTEAD NOTHING;"
        )
        locus = "fixture.dependency_rule"

    # --- multi-table fixture ---
    if is_multi:
        setup.append(f"CREATE TABLE {p}mt2 (c integer);")
        locus = "fixture.multi_table"

    # --- arm the non-superuser role (AFTER table creation) ---
    if effective:
        setup.append(f"SET ROLE {p}actor;")

    # --- in-use cursor fixture ---
    if in_use:
        setup.append("BEGIN;")
        setup.append(f"DECLARE {p}c CURSOR FOR SELECT * FROM {create_ref};")
        locus = "fixture.in_use_state"

    if_exists = "IF EXISTS " if _if_exists_present(case, a) else ""
    cascade = _cascade_clause(a)
    target = f"DROP TABLE {if_exists}{drop_ref}"
    if is_multi:
        target += f", {p}mt2"
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
    if in_use:
        assert_lines.append("ROLLBACK;")
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
    # Standard drops (VIEW/FUNCTION/INDEX) go through specs= in both
    # bookends; the shape-A ON-table drops (TRIGGER/POLICY/RULE) go through
    # complex_specs= routed to build_cleanup ONLY.  In pre-cleanup the table
    # anchor (DROP TABLE CASCADE) removes these dependents, so a later
    # DROP <KIND> ON <already-gone-table> would error even with IF EXISTS;
    # IF EXISTS suppresses a missing-object NOTICE but not a missing-relation
    # ERROR.  FK/multi tables fold into the tables= anchor (already in
    # _created_table_refs), so no separate specs are needed for them.
    cleanup_specs: list[DropSpec] = []
    complex_specs: list[OnDropSpec] = []
    if dep_kind == "view":
        cleanup_specs.append(DropSpec("VIEW", f"{p}depv"))
    elif dep_kind == "trigger":
        cleanup_specs.append(DropSpec("FUNCTION", f"{p}trgfn", args="()"))
        complex_specs.append(OnDropSpec("TRIGGER", f"{p}trg", create_ref))
    elif dep_kind == "index":
        cleanup_specs.append(DropSpec("INDEX", f"{p}idx"))
    elif dep_kind == "policy":
        complex_specs.append(OnDropSpec("POLICY", f"{p}pol", create_ref))
    elif dep_kind == "rule":
        complex_specs.append(OnDropSpec("RULE", f"{p}rl", create_ref))

    roles = _role_names(case, p, effective)
    tables = tuple(_created_table_refs(case, a, p))

    pre_cleanup_bk = build_pre_cleanup(
        tables=tables,
        specs=tuple(cleanup_specs),
        roles=tuple(roles),
    )
    cleanup_bk = build_cleanup(
        tables=tables,
        specs=tuple(cleanup_specs),
        complex_specs=tuple(complex_specs),
        roles=tuple(roles),
        drop_owned=bool(roles),
        reset_role=bool(effective),
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


def resolve_drop_table_factor_witness(
    case: DropTableFactorCase | DropTableFactorExtensionCase,
    repository_root: Path,
) -> DropTableFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropTableFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_table(sql: str) -> int:
    """Count the single credited DROP TABLE inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*DROP\s+TABLE\b", region)
    )


def _header(case: DropTableFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP TABLE {case.factor_key}={case.factor_value}",
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


def render_drop_table_factor_case(
    case: DropTableFactorCase | DropTableFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP TABLE regress program."""

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地规则和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP TABLE。")
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


def generate_drop_table_factor_programs(
    baseline_plan: DropTableFactorLoopPlan,
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
    case: DropTableFactorCase | DropTableFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_table_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropTableFactorRenderError",
    "DropTableFactorWitness",
    "count_primary_drop_table",
    "generate_drop_table_factor_programs",
    "render_drop_table_factor_case",
    "resolve_drop_table_factor_witness",
]
