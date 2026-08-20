"""Render complete PostgreSQL 18.4 ALTER VIEW factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the byte-level
witness validator (which re-renders and compares) can never diverge from
the bytes actually written.

ALTER VIEW modifies an existing plain view relation (a ``pg_class`` row
of relkind ``v``).  The target view fixture is self-contained
(``CREATE VIEW v AS SELECT 1 AS col``); no base TABLE is ever created,
so the DROP-TABLE bookend contract does not apply and
``_tables_to_drop`` always returns ``[]``.  All catalog oracles
schema-qualify ``pg_catalog.*`` / ``information_schema.*`` (exempt from
the file-prefix style gate; every catalog SELECT carries a top-level
``ORDER BY count(*)``).  Quoted / reserved / dotted view-name factor
values stay byte-observable in the ALTER VIEW target only; the fixture
uses plain unqualified prefix-starting names.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .alter_view_factor_extension import (
    AlterViewFactorExtensionCase,
    _present_failure_pair,
)
from .alter_view_factor_loop import (
    AlterViewFactorCase,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/view/"
    "alter_view.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/view/"
    "alter_view.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class AlterViewFactorRenderError(ValueError):
    """Raised when an ALTER VIEW case cannot be rendered."""


@dataclass(frozen=True)
class AlterViewFactorWitness:
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


def _synthetic_case(
    ext: AlterViewFactorExtensionCase,
) -> AlterViewFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get("target_action", "set_option")
    return AlterViewFactorCase(
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
    case: AlterViewFactorCase | AlterViewFactorExtensionCase,
) -> AlterViewFactorCase:
    if isinstance(case, AlterViewFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: AlterViewFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _view_missing(a: dict[str, str]) -> bool:
    return a.get("object_state", "exists") == "not_exists"


def _wrong_type(a: dict[str, str]) -> bool:
    return a.get("error_boundary", "none") == "wrong_object_type"


def _if_exists_sql(a: dict[str, str]) -> str:
    return (
        "IF EXISTS "
        if a.get("if_exists_clause", "absent") == "present"
        else ""
    )


def _target_view(a: dict[str, str], p: str) -> str:
    """The view identifier in the ALTER VIEW target statement."""

    if _wrong_type(a):
        return f"{p}seq"
    shape = a.get("view_name_shape", "simple")
    if _view_missing(a):
        return f"{p}nosuchview"
    if shape == "quoted":
        return f'"{p}view"'
    if shape == "schema_qualified":
        return f"{p}viewschema.{p}view"
    return f"{p}view"


def _view_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    if _wrong_type(a):
        return f"{p}seq"
    if _view_missing(a):
        return f"{p}nosuchview"
    return f"{p}view"


def _fixture_view(a: dict[str, str], p: str) -> str | None:
    """The view name for CREATE VIEW, or None when not created."""

    if _view_missing(a) or _wrong_type(a):
        return None
    shape = a.get("view_name_shape", "simple")
    if shape == "schema_qualified":
        return f"{p}viewschema.{p}view"
    return f"{p}view"


def _column_name(a: dict[str, str], p: str) -> str:
    shape = a.get("column_name_shape", "simple")
    if shape == "quoted":
        return f'"{p}col"'
    return f"{p}col"


def _column_keyword(a: dict[str, str]) -> str:
    return (
        "COLUMN "
        if a.get("column_name_shape", "simple") == "with_column_keyword"
        else ""
    )


def _new_col_name(a: dict[str, str], p: str) -> str:
    return f"{p}newcol"


def _new_view_name(a: dict[str, str], p: str) -> str:
    """The new name in RENAME TO."""

    shape = a.get("new_name_shape", "simple")
    if shape == "same_as_existing":
        return f"{p}conflictview"
    if shape == "quoted":
        return f'"{p}newview"'
    return f"{p}newview"


def _new_schema(a: dict[str, str], p: str) -> str:
    """The target schema in SET SCHEMA."""

    shape = a.get("new_schema_shape", "schema_exists")
    if shape == "schema_not_exists":
        return f"{p}nosuchschema"
    if shape == "pg_catalog_reserved":
        return "pg_catalog"
    return f"{p}newschema"


def _owner_target(a: dict[str, str], p: str) -> str:
    """The owner target token in OWNER TO."""

    shape = a.get("owner_target_shape", "role_name")
    if shape == "current_role":
        return "CURRENT_ROLE"
    if shape == "current_user":
        return "CURRENT_USER"
    if shape == "session_user":
        return "SESSION_USER"
    if shape == "non_existent_role":
        return f"{p}nosuchrole"
    return f"{p}newowner"


def _option_clause(a: dict[str, str], reset: bool = False) -> str:
    """The view-option clause for SET / RESET."""

    shape = a.get("view_option_shape", "check_option_local")
    if reset:
        if shape == "multiple_options":
            return "check_option, security_barrier"
        name = shape.replace("_true", "").replace("_false", "")
        if name.startswith("check_option"):
            return "check_option"
        if name.startswith("security_barrier"):
            return "security_barrier"
        if name.startswith("security_invoker"):
            return "security_invoker"
        return "check_option"
    if shape == "check_option_local":
        return "check_option = local"
    if shape == "check_option_cascaded":
        return "check_option = cascaded"
    if shape == "security_barrier_true":
        return "security_barrier = true"
    if shape == "security_barrier_false":
        return "security_barrier = false"
    if shape == "security_invoker_true":
        return "security_invoker = true"
    if shape == "security_invoker_false":
        return "security_invoker = false"
    if shape == "multiple_options":
        return "check_option = local, security_barrier = true"
    return "check_option = local"


def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target ALTER VIEW runs."""

    pl = a.get("privilege_level", "owner")
    if pl in ("non_owner_with_privilege", "non_owner_no_privilege"):
        return f"{p}actor"
    return ""


def _actor_owns_view(a: dict[str, str]) -> bool:
    """Whether the fixture view is created by the actor (privilege case)."""

    return (
        a.get("privilege_level", "owner")
        == "non_owner_with_privilege"
    )


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    """Roles to tear down."""

    roles: list[str] = []
    pl = a.get("privilege_level", "owner")
    if pl in ("non_owner_with_privilege", "non_owner_no_privilege"):
        roles.append(f"{p}actor")
    ot = a.get("owner_target_shape", "role_name")
    if ot == "role_name" and a.get("target_action") == "owner_to":
        roles.append(f"{p}newowner")
    return tuple(roles)


def _view_present(a: dict[str, str]) -> bool:
    """Whether the target should be a present view in pg_class."""

    return not _view_missing(a) and not _wrong_type(a)


def _probe_select(
    case: AlterViewFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only error_assertion."""

    mode = a.get("verification_mode", "pg_class_query")
    if mode == "error_assertion":
        return None

    target = _target_view(a, p)
    present = _view_present(a)
    cmp_op = ">" if present else "="
    view_lit = _view_literal(a, p)

    if mode == "select_from_view":
        if not present:
            return None
        shape = a.get("view_name_shape", "simple")
        if shape in ("quoted", "schema_qualified"):
            return None
        return f"SELECT 1 AS view_probe FROM {target} LIMIT 1;"
    if mode == "pg_views_query":
        return (
            f"SELECT count(*) {cmp_op} 0 AS view_state "
            f"FROM pg_catalog.pg_views "
            f"WHERE viewname = '{view_lit}' "
            f"ORDER BY count(*);"
        )
    if mode == "information_schema_views":
        return (
            f"SELECT count(*) {cmp_op} 0 AS view_state "
            f"FROM information_schema.views "
            f"WHERE table_name = '{view_lit}' "
            f"ORDER BY count(*);"
        )
    # pg_class_query
    return (
        f"SELECT count(*) {cmp_op} 0 AS view_state "
        f"FROM pg_catalog.pg_class "
        f"WHERE relname = '{view_lit}' AND relkind = 'v' "
        f"ORDER BY count(*);"
    )


def _tables_to_drop(
    case: AlterViewFactorCase,
) -> list[str]:
    """Fixture tables the case CREATEs.

    ALTER VIEW fixtures create only views (self-contained SELECT), never
    a TABLE.  The bookend (DROP TABLE IF EXISTS) is therefore never
    emitted.
    """
    return []


def _resolve_case(
    case: AlterViewFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    action = a.get("target_action", "set_option")
    missing = _view_missing(a)
    wrong = _wrong_type(a)

    setup: list[str] = []
    locus = "target.alter_view"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    fixture = _fixture_view(a, p)
    target_view = _target_view(a, p)

    # --- role fixtures -----------------------------------------------
    if f"{p}actor" in roles:
        setup.append(f"CREATE ROLE {p}actor LOGIN;")
        locus = "fixture.privilege_state"
    if (
        action == "owner_to"
        and a.get("owner_target_shape", "role_name") == "role_name"
    ):
        setup.append(f"CREATE ROLE {p}newowner LOGIN;")
        locus = "fixture.owner_role"

    # --- schema fixture for schema-qualified view name ---------------
    if (
        fixture is not None
        and a.get("view_name_shape", "simple") == "schema_qualified"
    ):
        setup.append(f"CREATE SCHEMA {p}viewschema;")
        locus = "fixture.view_schema"

    # --- schema fixture for SET SCHEMA target -----------------------
    if (
        action == "set_schema"
        and a.get("new_schema_shape", "schema_exists") == "schema_exists"
    ):
        setup.append(f"CREATE SCHEMA {p}newschema;")
        locus = "fixture.target_schema"

    # --- arm the actor for non_owner_with_privilege (view owned by
    #     the actor because it is created after SET ROLE) ------------
    if effective and _actor_owns_view(a):
        setup.append(f"SET ROLE {effective};")
        locus = "fixture.privilege_state"

    # --- the target view fixture ------------------------------------
    if wrong:
        setup.append(f"CREATE SEQUENCE {p}seq;")
        locus = "fixture.wrong_object_type"
    elif missing:
        setup.append(
            "SELECT 1 AS target_view_intentionally_absent;"
        )
        locus = "fixture.view_missing"
    elif fixture is not None:
        setup.append(
            f"CREATE VIEW {fixture} AS SELECT 1 AS {p}col, "
            f"2 AS {p}col2;"
        )
        locus = "fixture.view"

    # --- conflicting view for rename conflict -----------------------
    if (
        action == "rename"
        and a.get("new_name_shape", "simple") == "same_as_existing"
    ):
        cf = _new_view_name(a, p)
        setup.append(f"CREATE VIEW {cf} AS SELECT 1 AS {p}col;")
        locus = "fixture.rename_conflict"

    # --- dependency view for other_view_depends ---------------------
    if a.get("dependency_state", "base_table_exists") == "other_view_depends":
        if fixture is not None:
            setup.append(
                f"CREATE VIEW {p}viewdep AS SELECT * FROM {fixture};"
            )
            locus = "fixture.dependent_view"

    # --- arm the actor for non_owner_no_privilege (view NOT owned) --
    if effective and not _actor_owns_view(a):
        setup.append(f"SET ROLE {effective};")
        locus = "fixture.privilege_state"

    # --- the primary target statement --------------------------------
    target = _build_target(a, p, target_view)

    # --- oracle / SQLSTATE assertion ---------------------------------
    assert_lines: list[str] = []
    if effective:
        assert_lines.append("RESET ROLE;")
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    probe = _probe_select(case, a, p)
    if probe is not None:
        assert_lines.append(probe)

    # --- cleanup construction -----------------------------------------
    views_to_drop: list[str] = []
    if fixture is not None:
        views_to_drop.append(fixture)
    if action == "rename" and not missing and not wrong:
        new = _new_view_name(a, p)
        if new != target_view:
            views_to_drop.append(new)
        if a.get("new_name_shape", "simple") == "same_as_existing":
            views_to_drop.append(_new_view_name(a, p))
    if a.get("dependency_state") == "other_view_depends" and fixture is not None:
        views_to_drop.append(f"{p}viewdep")
    if action == "set_schema" and not missing and not wrong:
        nss = a.get("new_schema_shape", "schema_exists")
        if nss == "schema_exists":
            views_to_drop.append(f"{p}newschema.{p}view")

    schemas_to_drop: list[str] = []
    if (
        fixture is not None
        and a.get("view_name_shape", "simple") == "schema_qualified"
    ):
        schemas_to_drop.append(f"{p}viewschema")
    if (
        action == "set_schema"
        and a.get("new_schema_shape", "schema_exists") == "schema_exists"
    ):
        schemas_to_drop.append(f"{p}newschema")

    sequences_to_drop: list[str] = []
    if wrong:
        sequences_to_drop.append(f"{p}seq")

    cleanup_mode = a.get("cleanup_mode", "drop_view_if_exists")
    cascade = " CASCADE" if cleanup_mode == "drop_view_cascade" else ""

    view_drops = [
        f"DROP VIEW IF EXISTS {v}{cascade};" for v in views_to_drop
    ]
    schema_drops = [
        f"DROP SCHEMA IF EXISTS {s} CASCADE;" for s in schemas_to_drop
    ]
    seq_drops = [
        f"DROP SEQUENCE IF EXISTS {s};" for s in sequences_to_drop
    ]
    role_drops = [
        stmt
        for role in roles
        for stmt in (
            f"DROP OWNED BY {role} CASCADE;",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    pre_cleanup: list[str] = []
    pre_cleanup.extend(view_drops)
    pre_cleanup.extend(schema_drops)
    pre_cleanup.extend(seq_drops)
    pre_cleanup.extend(role_drops)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(view_drops)
    cleanup.extend(schema_drops)
    cleanup.extend(seq_drops)
    cleanup.extend(role_drops)
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


def _build_target(
    a: dict[str, str], p: str, view: str
) -> str:
    """The primary ALTER VIEW statement for the active branch."""

    action = a.get("target_action", "set_option")
    if_exists = _if_exists_sql(a)
    if action == "set_default":
        col = _column_name(a, p)
        kw = _column_keyword(a)
        return (
            f"ALTER VIEW {if_exists}{view} ALTER {kw}{col} "
            f"SET DEFAULT 1;"
        )
    if action == "drop_default":
        col = _column_name(a, p)
        kw = _column_keyword(a)
        return (
            f"ALTER VIEW {if_exists}{view} ALTER {kw}{col} "
            f"DROP DEFAULT;"
        )
    if action == "owner_to":
        target = _owner_target(a, p)
        return f"ALTER VIEW {if_exists}{view} OWNER TO {target};"
    if action == "rename_column":
        col = _column_name(a, p)
        kw = _column_keyword(a)
        new_col = _new_col_name(a, p)
        return (
            f"ALTER VIEW {if_exists}{view} RENAME {kw}{col} "
            f"TO {new_col};"
        )
    if action == "rename":
        new = _new_view_name(a, p)
        return f"ALTER VIEW {if_exists}{view} RENAME TO {new};"
    if action == "set_schema":
        schema = _new_schema(a, p)
        return f"ALTER VIEW {if_exists}{view} SET SCHEMA {schema};"
    if action == "set_option":
        clause = _option_clause(a, reset=False)
        return f"ALTER VIEW {if_exists}{view} SET ({clause});"
    if action == "reset_option":
        clause = _option_clause(a, reset=True)
        return f"ALTER VIEW {if_exists}{view} RESET ({clause});"
    return f"ALTER VIEW {if_exists}{view} SET (check_option = local);"


def resolve_alter_view_factor_witness(
    case: AlterViewFactorCase | AlterViewFactorExtensionCase,
    repository_root: Path,
) -> AlterViewFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return AlterViewFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_alter_view(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(re.findall(r"(?im)^\s*ALTER\s+VIEW\b", region))


def _header(case: AlterViewFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : ALTER VIEW {case.factor_key}="
        f"{case.factor_value}",
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


def render_alter_view_factor_case(
    case: AlterViewFactorCase | AlterViewFactorExtensionCase,
    repository_root: Path,
) -> str:
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 ALTER VIEW。")
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
    if not text.endswith("\n"):
        text += "\n"
    return text


def _write_program(
    case: AlterViewFactorCase | AlterViewFactorExtensionCase,
    out: Path,
) -> None:
    text = render_alter_view_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_alter_view_factor_programs(
    baseline_plan: object,
    extension_plan: object,
    out_dir: Path,
) -> int:
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


__all__ = [
    "AlterViewFactorRenderError",
    "AlterViewFactorWitness",
    "count_primary_alter_view",
    "generate_alter_view_factor_programs",
    "render_alter_view_factor_case",
    "resolve_alter_view_factor_witness",
]
