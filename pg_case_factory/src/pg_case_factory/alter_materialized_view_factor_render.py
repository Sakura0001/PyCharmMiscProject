"""Render complete PostgreSQL 18.4 ALTER MATERIALIZED VIEW factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_class ... ORDER BY count(*)``
never nests a ``FROM`` inside an ``EXISTS`` subquery, so
``audit_catalog_observability`` accepts it.

The owner-transfer mechanics (SESSION_USER/special-token owner targets,
RESET-ROLE before the catalog-audit oracle, idempotent cleanup) are salvaged
verbatim from ``alter_large_object_factor_render`` (commit 5035161b), because
``OWNER TO`` is the same owner-transfer shape.  The multi-branch action
dispatch (ALTER COLUMN / CLUSTER / SET / RESET / RENAME / SET SCHEMA /
DEPENDS ON EXTENSION) and the column-inv + wrong-object-type fixtures are
specific to ALTER MATERIALIZED VIEW.

All fixture decisions are read from the frozen *assignment* dict (not the
case's primary factor key/value), so extension cases — whose primary is a
synthetic attribution pair derived in
:mod:`alter_materialized_view_factor_extension` — render identically to a
baseline case carrying the same factor assignment.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .alter_materialized_view_factor_extension import (
    AlterMaterializedViewFactorExtensionCase,
    _present_failure_pair,
)
from .alter_materialized_view_factor_loop import (
    AlterMaterializedViewFactorCase,
    AlterMaterializedViewFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/materialized_view/"
    "alter_materialized_view.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/materialized_view/"
    "alter_materialized_view.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

# Actions that reference a column (column-inv).
_COLUMN_ACTIONS = frozenset(
    {
        "set_statistics",
        "set_attribute_option",
        "reset_attribute_option",
        "set_storage",
        "set_compression",
        "rename_column",
    }
)
# Actions that need an index fixture.
_INDEX_ACTIONS = frozenset({"cluster_on"})
# Actions that need an extension fixture (only when the case expects success,
# so extension_missing / missing_dependency failures intentionally omit it).
_EXTENSION_ACTIONS = frozenset({"depends_on_extension"})

_DEFAULT_SCHEMA = "public"


def _synthetic_case(
    ext: AlterMaterializedViewFactorExtensionCase,
) -> AlterMaterializedViewFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    elif ext.consumer_action_id == "owner_to" and ext.outcome == "success":
        factor_key = "new_owner_shape"
        factor_value = assignment["new_owner_shape"]
    else:
        factor_key = "alter_action_type"
        factor_value = assignment["alter_action_type"]
    return AlterMaterializedViewFactorCase(
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
    case: AlterMaterializedViewFactorCase | AlterMaterializedViewFactorExtensionCase,
) -> AlterMaterializedViewFactorCase:
    if isinstance(case, AlterMaterializedViewFactorExtensionCase):
        return _synthetic_case(case)
    return case


class AlterMaterializedViewFactorRenderError(ValueError):
    """Raised when an ALTER MATERIALIZED VIEW case cannot be rendered."""


@dataclass(frozen=True)
class AlterMaterializedViewFactorWitness:
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


def _baseline(case: AlterMaterializedViewFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _base_name(case: AlterMaterializedViewFactorCase, p: str) -> str:
    return f"{p}mv"


def _wrong_rel_name(case: AlterMaterializedViewFactorCase, p: str) -> str:
    return f"{p}tbl"


def _index_name(case: AlterMaterializedViewFactorCase, p: str) -> str:
    return f"{p}idx"


def _ext_name(case: AlterMaterializedViewFactorCase, p: str) -> str:
    """The extension named by DEPENDS ON EXTENSION.

    The success path needs a *real* installed extension so CREATE EXTENSION +
    DEPENDS ON EXTENSION both succeed (00000); only ``plpgsql`` is preinstalled
    on the isolated cluster, so the success outcome uses it (CREATE EXTENSION IF
    NOT EXISTS plpgsql is a no-op NOTICE, and dropping the materialized view
    later removes the recorded dependency — plpgsql itself is never dropped
    because PG 18.4 forbids dropping the required plpgsql extension).  The
    failure path (extension_missing) names a non-existent extension so DEPENDS
    ON EXTENSION surfaces 42704 (extension_does_not_exist).
    """

    if case.outcome == "expected_failure":
        return f"{p}no_such_extension"
    return "plpgsql"


def _new_col_name(case: AlterMaterializedViewFactorCase, p: str) -> str:
    return f"{p}col_new"


def _new_mv_name(case: AlterMaterializedViewFactorCase, p: str) -> str:
    return f"{p}mv_new"


def _qualify(name_shape: str, base: str) -> str:
    if name_shape == "schema_qualified":
        return f"{_DEFAULT_SCHEMA}.{base}"
    if name_shape == "quoted_identifier":
        return f'"{base}"'
    return base


def _name_shape(a: dict[str, str]) -> str:
    return a.get("name_shape", "plain_identifier")


def _mv_qualified(case: AlterMaterializedViewFactorCase, a: dict[str, str], p: str) -> str:
    return _qualify(_name_shape(a), _base_name(case, p))


def _col_name(case: AlterMaterializedViewFactorCase, a: dict[str, str], p: str) -> str:
    base = f"{p}col"
    if a.get("column_name_shape", "plain_identifier") == "quoted_identifier":
        return f'"{base}"'
    return base


def _no_fixture(case: AlterMaterializedViewFactorCase, a: dict[str, str]) -> bool:
    """Whether the fixture intentionally creates NO target relation.

    Only ``target_object_state = missing`` suppresses the mview.  The derived
    ``expected_status = failure`` does NOT, because for a privilege or
    missing-role failure the materialized view still exists (the action is
    merely rejected); suppressing it would assert absence where there is
    presence.  The ``expected_status = failure`` *baseline* sentinel instead
    carries ``target_object_state = missing`` in its own assignment, so this
    single check covers both.
    """

    if case.kind == "RISK":
        return False
    return a.get("target_object_state") == "missing"


def _wrong_type_target(a: dict[str, str]) -> bool:
    """Whether the target relation is a plain table (surfaces 42809)."""

    return (
        a.get("target_object_state") == "wrong_object_type"
        or a.get("invalid_combination") == "object_type_mismatch"
    )


def _target_relation(
    case: AlterMaterializedViewFactorCase, a: dict[str, str], p: str
) -> str:
    """The relation name inside ALTER MATERIALIZED VIEW."""

    if _wrong_type_target(a):
        return _qualify(_name_shape(a), _wrong_rel_name(case, p))
    return _mv_qualified(case, a, p)


def _probe_relname(
    case: AlterMaterializedViewFactorCase, a: dict[str, str], p: str
) -> str:
    """The relation name the catalog-audit oracle queries."""

    if _wrong_type_target(a):
        return _wrong_rel_name(case, p)
    # A successful RENAME TO moves the materialized view to the new name, so the
    # presence oracle must query the new name (the old name no longer exists).
    if case.consumer_action_id == "rename" and case.outcome == "success":
        return _new_mv_name(case, p)
    return _base_name(case, p)


def _owner_target(
    case: AlterMaterializedViewFactorCase, a: dict[str, str], p: str
) -> str:
    value = a.get("new_owner_shape", "plain_role")
    if value in ("CURRENT_ROLE", "current_role"):
        return "CURRENT_ROLE"
    if value in ("CURRENT_USER", "current_user"):
        return "CURRENT_USER"
    if value in ("SESSION_USER", "session_user"):
        return "SESSION_USER"
    if value == "missing_role":
        return f"{p}nonexistent_role"
    return f"{p}new_owner"


def _effective_role(
    case: AlterMaterializedViewFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target ALTER MATERIALIZED VIEW runs."""

    # SESSION_USER resolves to the session user (the superuser that owns every
    # test materialized view), so ``OWNER TO SESSION_USER`` is a no-op transfer
    # to the existing owner.  PG 18.4 allows the *owner* to perform this no-op,
    # so for the session_user sub-case the action runs as the owner (no SET
    # ROLE) — the privilege boundary does not fire and the outcome is success
    # (00000) rather than 42501.  A non-owner attempting the transfer is still
    # denied (must_be_owner), but the expander already attributes that as a
    # success-bearing combination because the boundary does not fire for
    # session_user, so the render must match by not arming the actor role.
    if (
        case.consumer_action_id == "owner_to"
        and a.get("new_owner_shape", "").lower() == "session_user"
    ):
        return ""
    level = a.get("privilege_context", "owner")
    boundary = a.get("ownership_boundary", "owner")
    if level == "insufficient_privilege" or boundary == "non_owner":
        return f"{p}actor"
    return ""


def _if_exists_sql(a: dict[str, str]) -> str:
    return "IF EXISTS " if a.get("if_exists_clause") == "present" else ""


def _action_target_sql(
    case: AlterMaterializedViewFactorCase, a: dict[str, str], p: str
) -> str:
    """The ALTER MATERIALIZED VIEW statement for the case's consumer action."""

    ifx = _if_exists_sql(a)
    rel = _target_relation(case, a, p)
    col = _col_name(case, a, p)
    action = case.consumer_action_id
    if a.get("invalid_combination") == "syntax_valid_semantic_error":
        # The "invalid alter combination" sentinel: the SET STATISTICS clause
        # without its ALTER COLUMN host is a malformed ALTER MATERIALIZED VIEW
        # that surfaces SQLSTATE 42601 (syntax_error) — the syntax-class code
        # this failure value maps to.  Every "cannot be performed on relation"
        # alternative (ADD COLUMN / DROP NOT NULL / ALTER CONSTRAINT) instead
        # yields 42809, which collides with wrong_object_type, so the parse
        # error is the only unique-code bearer.  ON_ERROR_STOP is off for
        # expected_failure cases, so the program still emits
        # PGCF_TARGET_SQLSTATE=42601 after the parse error.
        return f"ALTER MATERIALIZED VIEW {ifx}{rel} SET STATISTICS 100;"
    if action == "set_statistics":
        return f"ALTER MATERIALIZED VIEW {ifx}{rel} ALTER COLUMN {col} SET STATISTICS 100;"
    if action == "set_attribute_option":
        return f"ALTER MATERIALIZED VIEW {ifx}{rel} ALTER COLUMN {col} SET (n_distinct=0.1);"
    if action == "reset_attribute_option":
        return f"ALTER MATERIALIZED VIEW {ifx}{rel} ALTER COLUMN {col} RESET (n_distinct);"
    if action == "set_storage":
        return f"ALTER MATERIALIZED VIEW {ifx}{rel} ALTER COLUMN {col} SET STORAGE PLAIN;"
    if action == "set_compression":
        return f"ALTER MATERIALIZED VIEW {ifx}{rel} ALTER COLUMN {col} SET COMPRESSION pglz;"
    if action == "cluster_on":
        return f"ALTER MATERIALIZED VIEW {ifx}{rel} CLUSTER ON {_index_name(case, p)};"
    if action == "set_without_cluster":
        return f"ALTER MATERIALIZED VIEW {ifx}{rel} SET WITHOUT CLUSTER;"
    if action == "set_access_method":
        return f"ALTER MATERIALIZED VIEW {ifx}{rel} SET ACCESS METHOD heap;"
    if action == "set_tablespace":
        return f"ALTER MATERIALIZED VIEW {ifx}{rel} SET TABLESPACE pg_default;"
    if action == "set_storage_parameter":
        return f"ALTER MATERIALIZED VIEW {ifx}{rel} SET (autovacuum_enabled=true);"
    if action == "reset_storage_parameter":
        return f"ALTER MATERIALIZED VIEW {ifx}{rel} RESET (autovacuum_enabled);"
    if action == "owner_to":
        return f"ALTER MATERIALIZED VIEW {ifx}{rel} OWNER TO {_owner_target(case, a, p)};"
    if action == "depends_on_extension":
        return f"ALTER MATERIALIZED VIEW {ifx}{rel} DEPENDS ON EXTENSION {_ext_name(case, p)};"
    if action == "rename_column":
        return f"ALTER MATERIALIZED VIEW {ifx}{rel} RENAME COLUMN {col} TO {_new_col_name(case, p)};"
    if action == "rename":
        return f"ALTER MATERIALIZED VIEW {ifx}{rel} RENAME TO {_new_mv_name(case, p)};"
    if action == "set_schema":
        return f"ALTER MATERIALIZED VIEW {ifx}{rel} SET SCHEMA {_DEFAULT_SCHEMA};"
    raise AlterMaterializedViewFactorRenderError(
        f"unknown consumer action: {action}"
    )


def _probe_select(
    case: AlterMaterializedViewFactorCase, a: dict[str, str], p: str
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only error_assertion.

    ``absent`` follows the *fixture* state (no materialized view created, or a
    wrong-type plain table created), not the case outcome: a privilege or
    missing-role failure leaves the existing materialized view in place, so its
    probe must assert *presence*, while a missing/wrong-type target must assert
    *absence*.  ``error_assertion`` carries no count probe — the SQLSTATE check
    alone is the assertion, which also keeps the three verification modes
    byte-distinct.
    """

    mode = a.get("verification_mode", "catalog_query")
    if mode == "error_assertion":
        return None
    relname = _probe_relname(case, a, p)
    absent = _no_fixture(case, a) or _wrong_type_target(a)
    if (
        mode == "effect_query"
        and not absent
        and case.consumer_action_id == "owner_to"
        and case.outcome == "success"
    ):
        owner = _owner_target(case, a, p)
        if owner in ("CURRENT_ROLE", "CURRENT_USER", "SESSION_USER"):
            role_filter = f"r.rolname = {owner.lower()}"
        else:
            role_filter = f"r.rolname = '{owner}'"
        return (
            "SELECT count(*) > 0 AS owner_is_target "
            "FROM pg_catalog.pg_class AS c "
            "JOIN pg_catalog.pg_roles AS r ON c.relowner = r.oid "
            f"WHERE c.relname = '{relname}' AND c.relkind = 'm' AND {role_filter} "
            "ORDER BY count(*) LIMIT 1;"
        )
    comparator = "= 0" if absent else "> 0"
    if mode == "effect_query":
        alias = "effect_not_verified" if absent else "effect_verified"
    else:
        alias = "mview_absent" if absent else "mview_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_class "
        f"WHERE relname = '{relname}' AND relkind = 'm' "
        "ORDER BY count(*) LIMIT 1;"
    )


def _role_names(
    case: AlterMaterializedViewFactorCase,
    a: dict[str, str],
    p: str,
    effective: str,
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}actor":
        roles.append(f"{p}actor")
    if _owner_target(case, a, p) == f"{p}new_owner":
        roles.append(f"{p}new_owner")
    return tuple(roles)


def _resolve_case(case: AlterMaterializedViewFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    action = case.consumer_action_id
    no_mview = _no_fixture(case, a)
    wrong = _wrong_type_target(a)

    setup: list[str] = []
    locus = "target.materialized_view"

    effective = _effective_role(case, a, p)
    owner = _owner_target(case, a, p)

    # --- role fixtures -------------------------------------------------
    if owner == f"{p}new_owner":
        setup.append(f"CREATE ROLE {p}new_owner LOGIN;")
    if effective == f"{p}actor":
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")

    # --- the target relation fixture ----------------------------------
    if no_mview:
        setup.append("SELECT 1 AS target_materialized_view_intentionally_absent;")
        locus = "fixture.object_state"
    elif wrong:
        setup.append(f"CREATE TABLE {_wrong_rel_name(case, p)} AS SELECT 1 AS c;")
        locus = "fixture.wrong_object_type"
    else:
        # Create the materialized view with the column the column-level
        # actions (set_statistics / set_attribute_option / reset_attribute_option
        # / set_storage / set_compression / rename_column) target.  ``_col_name``
        # returns ``{p}col`` (plain) or ``"{p}col"`` (quoted); the quoted form
        # resolves to the same lowercase identifier, so creating the plain base
        # satisfies both column_name_shape values.  set_compression needs a
        # TOAST-able (varlena) column type — an integer column surfaces 0A000
        # "column data type integer does not support compression" — so a text
        # column is used for that action only; every other column-level action
        # is type-agnostic.
        col_expr = "'x'::text" if action == "set_compression" else "1"
        setup.append(
            f"CREATE MATERIALIZED VIEW {_base_name(case, p)} "
            f"AS SELECT {col_expr} AS {p}col;"
        )
        if action in _INDEX_ACTIONS:
            setup.append(
                f"CREATE INDEX {_index_name(case, p)} "
                f"ON {_base_name(case, p)}({p}col);"
            )
        if action in _EXTENSION_ACTIONS and case.outcome == "success":
            setup.append(
                f"CREATE EXTENSION IF NOT EXISTS {_ext_name(case, p)};"
            )

    # --- arm the effective role (superuser is the default) -------------
    if effective:
        setup.append(f"SET ROLE {effective};")
        locus = "fixture.privilege_state"

    # --- the primary target statement ---------------------------------
    target = _action_target_sql(case, a, p)

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
    probe = _probe_select(case, a, p)
    if probe is not None:
        assert_lines.append(probe)

    # --- cleanup construction ------------------------------------------
    drop_mode = a.get("cleanup_mode", "drop_objects")
    cascade = "" if drop_mode == "reset_state" else " CASCADE"
    roles = _role_names(case, a, p, effective)

    object_drops: list[str] = []
    # The wrong-object-type fixture creates a TABLE (the "wrong" relation).
    # audit_complete_table_script requires every table-creating script to
    # bookend with a DROP TABLE IF EXISTS naming each created table, so the
    # table drop is kept separate and hoisted to the first (pre-cleanup) and
    # last (final-cleanup) executable statement.  Every cleanup drop is IF
    # EXISTS over an independent object, so reordering is runtime-neutral
    # (sqlstates and the oracle are unchanged).
    table_drop: str | None = None
    # depends_on_extension success uses plpgsql (a required, un-droppable
    # extension); dropping the materialized view already removes the recorded
    # dependency, so no DROP EXTENSION is emitted (it would fail on plpgsql).
    if action in _INDEX_ACTIONS and not no_mview and not wrong:
        object_drops.append(f"DROP INDEX IF EXISTS {_index_name(case, p)};")
    if not no_mview:
        if action == "rename":
            object_drops.append(
                f"ALTER MATERIALIZED VIEW IF EXISTS {_new_mv_name(case, p)} "
                f"RENAME TO {_base_name(case, p)};"
            )
        object_drops.append(f"DROP MATERIALIZED VIEW IF EXISTS {_base_name(case, p)};")
    if wrong:
        table_drop = f"DROP TABLE IF EXISTS {_wrong_rel_name(case, p)};"
    role_drops = [
        statement
        for role in roles
        for statement in (
            f"DROP OWNED BY {role}{cascade};",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    pre_cleanup: list[str] = []
    if table_drop is not None:
        pre_cleanup.append(table_drop)
    pre_cleanup.extend(object_drops)
    pre_cleanup.extend(f"DROP ROLE IF EXISTS {role};" for role in roles)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(object_drops)
    cleanup.extend(role_drops)
    if table_drop is not None:
        cleanup.append(table_drop)
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


def resolve_alter_materialized_view_factor_witness(
    case: AlterMaterializedViewFactorCase | AlterMaterializedViewFactorExtensionCase,
    repository_root: Path,
) -> AlterMaterializedViewFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return AlterMaterializedViewFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_alter_materialized_view(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(re.findall(r"(?im)^\s*ALTER\s+MATERIALIZED\s+VIEW\b", region))


def _header(case: AlterMaterializedViewFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : ALTER MATERIALIZED VIEW {case.factor_key}={case.factor_value}",
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


def render_alter_materialized_view_factor_case(
    case: AlterMaterializedViewFactorCase | AlterMaterializedViewFactorExtensionCase,
    repository_root: Path,
) -> str:
    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地物化视图和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 ALTER MATERIALIZED VIEW。")
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


def generate_alter_materialized_view_factor_programs(
    baseline_plan: AlterMaterializedViewFactorLoopPlan,
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


def _write_program(
    case: AlterMaterializedViewFactorCase | AlterMaterializedViewFactorExtensionCase,
    out: Path,
) -> None:
    text = render_alter_materialized_view_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "AlterMaterializedViewFactorRenderError",
    "AlterMaterializedViewFactorWitness",
    "count_primary_alter_materialized_view",
    "generate_alter_materialized_view_factor_programs",
    "render_alter_materialized_view_factor_case",
    "resolve_alter_materialized_view_factor_witness",
]
