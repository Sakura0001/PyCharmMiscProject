"""Render complete PostgreSQL 18.4 DROP FOREIGN TABLE factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_class ... ORDER BY count(*)``
never nests a ``FROM`` inside an ``EXISTS`` subquery, so
``audit_catalog_observability`` accepts it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .cleanup_bookend import DropSpec, build_cleanup, build_pre_cleanup
from .drop_foreign_table_factor_extension import (
    DropForeignTableFactorExtensionCase,
)
from .drop_foreign_table_factor_loop import (
    DropForeignTableFactorCase,
    DropForeignTableFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/foreign_table/"
    "drop_foreign_table.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/foreign_table/"
    "drop_foreign_table.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

# Primary (factor, value) pairs where the target foreign table is
# intentionally absent, so the drop surfaces a not-found error (or a notice
# under IF EXISTS) and the oracle asserts absence.
_ABSENT_PRIMARIES = frozenset(
    {
        ("object_state", "not_exists"),
        ("nonexistent_table", "table_missing_no_if_exists"),
        ("table_name_shape", "nonexistent_name"),
        ("expected_status", "failure"),
        ("if_exists_notice", "notice_no_op"),
    }
)

# Baseline primaries that imply a dependent object fixture must be created.
_DEPENDENCY_PRIMARIES = frozenset(
    {
        ("dependency_state", "has_view_dependency"),
        ("dependent_objects", "view_dependencies"),
        ("dependent_objects", "other_dependencies"),
        ("dependent_with_restrict", "has_deps_cascade"),
        ("dependent_with_restrict", "has_deps_restrict"),
    }
)

# For an extension SUCCESS case (no present failure pair) the synthetic
# primary must be a neutral success primary whose helpers fall through to the
# assignment; the foreign table always exists in extensions (object_state held
# at exists).
_BRANCH_NEUTRAL_SUCCESS = ("object_state", "exists")


def _synthetic_case(
    ext: DropForeignTableFactorExtensionCase,
) -> DropForeignTableFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .drop_foreign_table_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropForeignTableFactorCase(
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
    case: DropForeignTableFactorCase | DropForeignTableFactorExtensionCase,
) -> DropForeignTableFactorCase:
    if isinstance(case, DropForeignTableFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropForeignTableFactorRenderError(ValueError):
    """Raised when a DROP FOREIGN TABLE case cannot be rendered."""


@dataclass(frozen=True)
class DropForeignTableFactorWitness:
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


def _baseline(case: DropForeignTableFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _ft_name(case: DropForeignTableFactorCase, a: dict[str, str], p: str) -> str:
    """The foreign table name as referenced inside DROP FOREIGN TABLE."""

    shape = a.get("table_name_shape", "simple_id")
    if shape == "quoted_id":
        return f'"{p}QuotedFt"'
    if shape == "nonexistent_name":
        return f"{p}nonexistent_ft"
    if shape == "schema_qualified":
        return f"public.{p}ft"
    return f"{p}ft"


def _probe_name(case: DropForeignTableFactorCase, a: dict[str, str], p: str) -> str:
    """The bare ftname (no schema/quotes) for the catalog probe."""

    shape = a.get("table_name_shape", "simple_id")
    if shape == "quoted_id":
        return f"{p}QuotedFt"
    if shape == "nonexistent_name":
        return f"{p}nonexistent_ft"
    return f"{p}ft"


def _ft2_name(p: str) -> str:
    return f"{p}ft2"


def _server_name(p: str) -> str:
    return f"{p}server"


def _view_name(p: str) -> str:
    return f"{p}v"


def _is_multi_table(
    case: DropForeignTableFactorCase, a: dict[str, str]
) -> bool:
    if case.kind == "EXT":
        return a.get("multi_table") == "multiple_tables"
    return case.factor_key == "multi_table" and case.factor_value == "multiple_tables"


def _fixture_kind(
    case: DropForeignTableFactorCase, a: dict[str, str]
) -> str:
    """Whether a foreign table fixture must be created."""

    if case.kind == "RISK":
        return "foreign_table"
    if (case.factor_key, case.factor_value) in _ABSENT_PRIMARIES:
        return "none"
    if case.kind == "EXT":
        if (
            a.get("nonexistent_table") == "table_missing_no_if_exists"
        ):
            return "none"
        if a.get("table_name_shape") == "nonexistent_name":
            return "none"
    return "foreign_table"


def _if_exists_present(
    case: DropForeignTableFactorCase, a: dict[str, str]
) -> bool:
    if case.factor_key == "if_exists_notice" and case.factor_value == "notice_no_op":
        return True
    return a.get("if_exists_clause") == "present"


def _cascade_clause(a: dict[str, str]) -> str:
    cascade = a.get("cascade_restrict", "restrict_default")
    if cascade == "cascade":
        return "CASCADE"
    return ""  # restrict_default: RESTRICT is the default


def _effective_role(
    case: DropForeignTableFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP FOREIGN TABLE runs."""

    if case.kind == "EXT":
        level = a.get("privilege_level", "superuser")
        return f"{p}actor" if level == "non_owner" else ""
    if case.factor_key == "privilege_level":
        return f"{p}actor" if case.factor_value == "non_owner" else ""
    if case.factor_key == "insufficient_privilege":
        return f"{p}actor" if case.factor_value == "non_owner_execution" else ""
    return ""


def _needs_dependent(
    case: DropForeignTableFactorCase, a: dict[str, str]
) -> bool:
    """Whether a dependent object fixture must be created."""

    if case.kind == "EXT":
        return a.get("dependency_state") == "has_view_dependency"
    if (case.factor_key, case.factor_value) in _DEPENDENCY_PRIMARIES:
        return True
    return a.get("dependency_state") == "has_view_dependency"


def _table_absent_after(
    case: DropForeignTableFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target foreign table is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if _fixture_kind(case, a) == "none":
        return True
    if case.outcome == "success":
        return True
    return False


def _probe_select(
    case: DropForeignTableFactorCase, a: dict[str, str], p: str
) -> str:
    name = _probe_name(case, a, p)
    absent = _table_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "foreign_table_absent" if absent else "foreign_table_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_class "
        f"WHERE relname = '{name}' AND relkind = 'f' "
        "ORDER BY count(*) LIMIT 1;"
    )


def _role_names(
    case: DropForeignTableFactorCase, p: str, effective: str
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}actor":
        roles.append(f"{p}actor")
    return tuple(roles)


def _resolve_case(case: DropForeignTableFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    fixture_kind = _fixture_kind(case, a)
    ft_ref = _ft_name(case, a, p)
    ft2 = _ft2_name(p)
    server = _server_name(p)
    view = _view_name(p)
    needs_dep = _needs_dependent(case, a)
    multi = _is_multi_table(case, a)

    setup: list[str] = []
    locus = "target.foreign_table"

    # --- role fixtures (CREATE only; SET ROLE deferred to after the
    # foreign table fixture so they run as the superuser) ---
    effective = _effective_role(case, a, p)
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- the target foreign table fixture (as superuser, before SET ROLE) -
    if fixture_kind == "foreign_table":
        setup.append("CREATE EXTENSION IF NOT EXISTS file_fdw;")
        setup.append(f"CREATE SERVER {server} FOREIGN DATA WRAPPER file_fdw;")
        setup.append(
            f"CREATE FOREIGN TABLE {ft_ref} (c integer) SERVER {server};"
        )
        if multi:
            setup.append(
                f"CREATE FOREIGN TABLE {ft2} (c integer) SERVER {server};"
            )
    else:
        setup.append(
            "SELECT 1 AS target_foreign_table_intentionally_absent;"
        )
        locus = "fixture.object_state"

    # --- dependent object fixture (as superuser, before SET ROLE) -------
    if needs_dep and fixture_kind == "foreign_table":
        setup.append(f"CREATE VIEW {view} AS SELECT * FROM {ft_ref};")
        locus = "fixture.dependency_state"

    # --- arm the non-superuser role (AFTER table creation) --------------
    if effective:
        setup.append(f"SET ROLE {p}actor;")
    if_exists = "IF EXISTS " if _if_exists_present(case, a) else ""
    cascade = _cascade_clause(a)
    if multi:
        target = f"DROP FOREIGN TABLE {if_exists}{ft_ref}, {ft2}"
    else:
        target = f"DROP FOREIGN TABLE {if_exists}{ft_ref}"
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
    # DROP OWNED BY is unreachable in pre-cleanup: the non-superuser
    # role fixture is created by setup, so on a fresh database the role
    # does not exist yet at pre-cleanup time and DROP OWNED BY would crash
    # (ON_ERROR_STOP=1) before the target statement reaches execution.
    # Pre-cleanup drops roles via DROP ROLE IF EXISTS only; the post-target
    # cleanup runs DROP OWNED BY then DROP ROLE IF EXISTS once setup has
    # created the role.  Specs are ordered in reverse-dependency order
    # (view -> ft2 -> ft_ref -> server); no base TABLE is created so the
    # tables= anchor is unused.
    roles = _role_names(case, p, effective)
    role_list = list(roles)
    specs: list[DropSpec] = []
    if needs_dep:
        specs.append(DropSpec("VIEW", view))
    if multi:
        specs.append(DropSpec("FOREIGN TABLE", ft2))
    specs.append(DropSpec("FOREIGN TABLE", ft_ref))
    specs.append(DropSpec("SERVER", server))
    pre_bookend = build_pre_cleanup(specs=tuple(specs), roles=role_list)
    cln_bookend = build_cleanup(
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


def resolve_drop_foreign_table_factor_witness(
    case: DropForeignTableFactorCase | DropForeignTableFactorExtensionCase,
    repository_root: Path,
) -> DropForeignTableFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropForeignTableFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_foreign_table(sql: str) -> int:
    """Count the single credited DROP FOREIGN TABLE inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*DROP\s+FOREIGN\s+TABLE\b", region)
    )


def _header(case: DropForeignTableFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP FOREIGN TABLE {case.factor_key}={case.factor_value}",
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


def render_drop_foreign_table_factor_case(
    case: DropForeignTableFactorCase | DropForeignTableFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP FOREIGN TABLE regress program."""

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地外部表和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP FOREIGN TABLE。")
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


def generate_drop_foreign_table_factor_programs(
    baseline_plan: DropForeignTableFactorLoopPlan,
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
    case: DropForeignTableFactorCase | DropForeignTableFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_foreign_table_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropForeignTableFactorRenderError",
    "DropForeignTableFactorWitness",
    "count_primary_drop_foreign_table",
    "generate_drop_foreign_table_factor_programs",
    "render_drop_foreign_table_factor_case",
    "resolve_drop_foreign_table_factor_witness",
]
