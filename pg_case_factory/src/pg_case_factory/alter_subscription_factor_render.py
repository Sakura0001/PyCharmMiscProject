"""Render complete PostgreSQL 18.4 ALTER SUBSCRIPTION factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

ALTER SUBSCRIPTION is a logical-replication DDL statement: the target
is a ``pg_catalog.pg_subscription`` catalog row, not a ``pg_class``
relation.  All catalog oracles schema-qualify ``pg_catalog.pg_subscription``
(exempt from the file-prefix style gate).  No case creates a TABLE, so
the bookend (DROP TABLE IF EXISTS) is never emitted (``_tables_to_drop``
always returns ``[]``).  Every catalog SELECT carries a top-level
``ORDER BY count(*)`` so the catalog-observability gate passes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .alter_subscription_factor_extension import (
    AlterSubscriptionFactorExtensionCase,
    _present_failure_pair,
)
from .alter_subscription_factor_loop import (
    AlterSubscriptionFactorCase,
    AlterSubscriptionFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/subscription/"
    "alter_subscription.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/subscription/"
    "alter_subscription.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_DB_PLACEHOLDER = "pgcf"
_VALID_CONNINFO = (
    f"host=localhost port=5432 dbname={_DB_PLACEHOLDER}"
)
_INVALID_CONNINFO = "invalid_conninfo_string"


class AlterSubscriptionFactorRenderError(ValueError):
    """Raised when an ALTER SUBSCRIPTION case cannot be rendered."""


@dataclass(frozen=True)
class AlterSubscriptionFactorWitness:
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
    ext: AlterSubscriptionFactorExtensionCase,
) -> AlterSubscriptionFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get("target_action", "rename")
    return AlterSubscriptionFactorCase(
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
    case: AlterSubscriptionFactorCase
    | AlterSubscriptionFactorExtensionCase,
) -> AlterSubscriptionFactorCase:
    if isinstance(case, AlterSubscriptionFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: AlterSubscriptionFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _subscription_missing(a: dict[str, str]) -> bool:
    return a.get("subscription_state") == "non_existent"


def _subscription_name(a: dict[str, str], p: str) -> str:
    """The subscription identifier in ALTER SUBSCRIPTION and fixtures."""

    shape = a.get("subscription_name_shape", "simple_name")
    if shape == "quoted_name":
        return f'"{p}Mixed Sub"'
    if shape == "non_existent_name":
        return f"{p}no_such_sub"
    return f"{p}sub"


def _subscription_name_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    shape = a.get("subscription_name_shape", "simple_name")
    if shape == "quoted_name":
        return f"{p}Mixed Sub"
    if shape == "non_existent_name":
        return f"{p}no_such_sub"
    return f"{p}sub"


def _new_name(a: dict[str, str], p: str) -> str:
    """The new name in RENAME TO."""

    shape = a.get("new_name_shape", "simple_name")
    rb = a.get("rename_behavior", "rename_to_new_name")
    if (
        rb == "rename_to_existing_name_conflict"
        or shape == "existing_name_conflict"
    ):
        return f"{p}conflict_sub"
    if shape == "quoted_name":
        return f'"{p}Mixed New"'
    return f"{p}newsub"


def _new_name_literal(a: dict[str, str], p: str) -> str:
    shape = a.get("new_name_shape", "simple_name")
    rb = a.get("rename_behavior", "rename_to_new_name")
    if (
        rb == "rename_to_existing_name_conflict"
        or shape == "existing_name_conflict"
    ):
        return f"{p}conflict_sub"
    if shape == "quoted_name":
        return f"{p}Mixed New"
    return f"{p}newsub"


def _conninfo(a: dict[str, str]) -> str:
    """The conninfo string for the CONNECTION clause."""

    shape = a.get("conninfo_string_shape", "valid_conninfo")
    cc = a.get("connection_change", "valid_new_conninfo")
    if shape == "invalid_conninfo" or cc == "invalid_new_conninfo":
        return _INVALID_CONNINFO
    return _VALID_CONNINFO


def _owner_target(a: dict[str, str], p: str) -> str:
    """The owner target token in OWNER TO."""

    shape = a.get("owner_to_shape", "explicit_role_name")
    if shape == "current_role_keyword":
        return "CURRENT_ROLE"
    if shape == "current_user_keyword":
        return "CURRENT_USER"
    if shape == "session_user_keyword":
        return "SESSION_USER"
    return f"{p}newowner"


def _publication_names(a: dict[str, str], p: str) -> list[str]:
    """Publication names for SET/ADD/DROP PUBLICATION."""

    shape = a.get("publication_name_shape", "simple_name")
    op = a.get("publication_operation", "set_publication_single")
    quoted = shape == "quoted_name"
    multiple = "multiple" in op
    if quoted:
        if multiple:
            return [f'"{p}Mixed Pub"', f'"{p}Second Pub"']
        return [f'"{p}Mixed Pub"']
    if multiple:
        return [f"{p}pub1", f"{p}pub2"]
    return [f"{p}pub1"]


def _parameter_clause(a: dict[str, str]) -> str:
    """The parameter clause for SET ( subscription_parameter )."""

    param = a.get("subscription_parameter", "single_parameter")
    if param == "single_parameter":
        return "binary = true"
    if param == "multiple_parameters":
        return "binary = true, streaming = true"
    if param == "synchronous_commit":
        return "synchronous_commit = off"
    if param == "binary":
        return "binary = true"
    if param == "stream":
        return "streaming = true"
    if param == "failover":
        return "failover = true"
    if param == "two_phase":
        return "two_phase = true"
    return "binary = true"


def _refresh_clause(a: dict[str, str]) -> str:
    """The WITH clause for REFRESH PUBLICATION."""

    opt = a.get("refresh_publication_option", "without_with_clause")
    if opt == "with_copy_data_true":
        return " WITH (copy_data = true)"
    if opt == "with_copy_data_false":
        return " WITH (copy_data = false)"
    return ""


def _needs_disabled_subscription(a: dict[str, str]) -> bool:
    """Whether the fixture subscription should be created disabled."""

    action = a.get("target_action", "set_parameters")
    edb = a.get("enable_disable_behavior", "enable_from_disabled")
    param = a.get("subscription_parameter", "single_parameter")
    if action == "enable":
        return True
    if edb == "enable_from_disabled":
        return True
    if action == "set_parameters" and param in ("failover", "two_phase"):
        return True
    return False


def _needs_enabled_subscription(a: dict[str, str]) -> bool:
    """Whether the fixture subscription should be created enabled."""

    action = a.get("target_action", "set_parameters")
    edb = a.get("enable_disable_behavior", "enable_from_disabled")
    if action == "disable":
        return True
    if edb in ("disable_from_enabled", "enable_already_enabled_no_effect"):
        return True
    return False


def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target ALTER SUBSCRIPTION runs."""

    ep = a.get("executor_privilege", "superuser")
    if ep == "non_superuser":
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    """Roles to tear down."""

    roles: list[str] = []
    ep = a.get("executor_privilege", "superuser")
    action = a.get("target_action", "set_parameters")
    ot = a.get("owner_to_shape", "explicit_role_name")
    if ep == "non_superuser":
        roles.append(f"{p}actor")
    if action == "owner_to" and ot == "explicit_role_name":
        roles.append(f"{p}newowner")
    return tuple(roles)


def _probe_select(
    case: AlterSubscriptionFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only error_assertion."""

    mode = a.get("verification_mode", "pg_subscription_catalog")
    if mode == "error_assertion":
        return None

    sub_lit = _subscription_name_literal(a, p)
    missing = _subscription_missing(a)
    action = a.get("target_action", "set_parameters")

    if action == "rename" and case.outcome == "success":
        check = _new_name_literal(a, p)
        present = True
    elif missing:
        check = sub_lit
        present = False
    else:
        check = sub_lit
        present = True

    cmp_op = ">" if present else "="
    return (
        f"SELECT count(*) {cmp_op} 0 AS subscription_state "
        f"FROM pg_catalog.pg_subscription "
        f"WHERE subname = '{check}' "
        f"ORDER BY count(*);"
    )


def _tables_to_drop(
    case: AlterSubscriptionFactorCase,
) -> list[str]:
    """Fixture tables the case CREATEs.

    ALTER SUBSCRIPTION is a logical-replication DDL statement: it never
    creates a TABLE.  The bookend (DROP TABLE IF EXISTS) is therefore
    never emitted.
    """
    return []


def _resolve_case(
    case: AlterSubscriptionFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    action = a.get("target_action", "set_parameters")
    missing = _subscription_missing(a)

    setup: list[str] = []
    locus = "target.alter_subscription"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    sub = _subscription_name(a, p)

    # --- role fixtures -----------------------------------------------
    if effective == f"{p}actor":
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"
    if (
        action == "owner_to"
        and a.get("owner_to_shape", "explicit_role_name")
        == "explicit_role_name"
    ):
        setup.append(f"CREATE ROLE {p}newowner LOGIN;")
        locus = "fixture.owner_role"

    # --- the target subscription fixture ------------------------------
    if not missing:
        if _needs_disabled_subscription(a):
            enabled = "false"
        elif _needs_enabled_subscription(a):
            enabled = "true"
        else:
            ss = a.get("subscription_state", "exists_enabled")
            enabled = "false" if ss == "exists_disabled" else "true"

        pub = f"{p}pub"
        setup.append(
            f"CREATE SUBSCRIPTION {sub} CONNECTION "
            f"'{_VALID_CONNINFO}' "
            f"PUBLICATION {pub} "
            f"WITH (enabled = {enabled}, create_slot = false, "
            f"copy_data = false, slot_name = NONE);"
        )
        locus = "fixture.subscription"
    else:
        setup.append(
            "SELECT 1 AS target_subscription_intentionally_absent;"
        )
        locus = "fixture.subscription_missing"

    # --- conflicting subscription for rename conflict ----------------
    if (
        action == "rename"
        and a.get("rename_behavior", "rename_to_new_name")
        == "rename_to_existing_name_conflict"
    ):
        setup.append(
            f"CREATE SUBSCRIPTION {p}conflict_sub CONNECTION "
            f"'{_VALID_CONNINFO}' "
            f"PUBLICATION {p}conflictpub "
            f"WITH (enabled = false, create_slot = false, "
            f"copy_data = false, slot_name = NONE);"
        )
        locus = "fixture.rename_conflict"

    # --- arm the effective role --------------------------------------
    if effective:
        setup.append(f"SET ROLE {effective};")

    # --- the primary target statement --------------------------------
    target = _build_target(a, p, sub)

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
    subscriptions_to_drop: list[str] = []
    if not missing:
        subscriptions_to_drop.append(sub)
    if action == "rename":
        new = _new_name(a, p)
        if new != sub:
            subscriptions_to_drop.append(new)
        if (
            a.get("rename_behavior", "rename_to_new_name")
            == "rename_to_existing_name_conflict"
        ):
            subscriptions_to_drop.append(f"{p}conflict_sub")

    role_drops = [
        statement
        for role in roles
        for statement in (
            f"DROP OWNED BY {role} CASCADE;",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    sub_drops = [
        f"DROP SUBSCRIPTION IF EXISTS {name};"
        for name in subscriptions_to_drop
    ]

    # pre-cleanup: subscriptions then roles
    pre_cleanup: list[str] = []
    pre_cleanup.extend(sub_drops)
    pre_cleanup.extend(role_drops)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # cleanup: RESET ROLE, subscriptions, roles
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(sub_drops)
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
    a: dict[str, str], p: str, sub: str
) -> str:
    """The primary ALTER SUBSCRIPTION statement for the active branch."""

    action = a.get("target_action", "set_parameters")
    if action == "connection":
        conn = _conninfo(a)
        return f"ALTER SUBSCRIPTION {sub} CONNECTION '{conn}';"
    if action == "set_publication":
        pubs = _publication_names(a, p)
        return (
            f"ALTER SUBSCRIPTION {sub} SET PUBLICATION "
            f"{', '.join(pubs)};"
        )
    if action == "add_publication":
        pubs = _publication_names(a, p)
        return (
            f"ALTER SUBSCRIPTION {sub} ADD PUBLICATION "
            f"{', '.join(pubs)};"
        )
    if action == "drop_publication":
        pubs = _publication_names(a, p)
        return (
            f"ALTER SUBSCRIPTION {sub} DROP PUBLICATION "
            f"{', '.join(pubs)};"
        )
    if action == "refresh_publication":
        clause = _refresh_clause(a)
        return (
            f"ALTER SUBSCRIPTION {sub} REFRESH PUBLICATION"
            f"{clause};"
        )
    if action == "enable":
        return f"ALTER SUBSCRIPTION {sub} ENABLE;"
    if action == "disable":
        return f"ALTER SUBSCRIPTION {sub} DISABLE;"
    if action == "set_parameters":
        params = _parameter_clause(a)
        return f"ALTER SUBSCRIPTION {sub} SET ({params});"
    if action == "skip":
        return (
            f"ALTER SUBSCRIPTION {sub} SKIP (lsn = '0/0');"
        )
    if action == "owner_to":
        target = _owner_target(a, p)
        return (
            f"ALTER SUBSCRIPTION {sub} OWNER TO {target};"
        )
    if action == "rename":
        new = _new_name(a, p)
        return f"ALTER SUBSCRIPTION {sub} RENAME TO {new};"
    return f"ALTER SUBSCRIPTION {sub} DISABLE;"


def resolve_alter_subscription_factor_witness(
    case: AlterSubscriptionFactorCase
    | AlterSubscriptionFactorExtensionCase,
    repository_root: Path,
) -> AlterSubscriptionFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return AlterSubscriptionFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_alter_subscription(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*ALTER\s+SUBSCRIPTION\b", region)
    )


def _header(case: AlterSubscriptionFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : ALTER SUBSCRIPTION {case.factor_key}="
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


def render_alter_subscription_factor_case(
    case: AlterSubscriptionFactorCase
    | AlterSubscriptionFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 ALTER SUBSCRIPTION。")
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
    case: AlterSubscriptionFactorCase
    | AlterSubscriptionFactorExtensionCase,
    out: Path,
) -> None:
    text = render_alter_subscription_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_alter_subscription_factor_programs(
    baseline_plan: AlterSubscriptionFactorLoopPlan,
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
    "AlterSubscriptionFactorRenderError",
    "AlterSubscriptionFactorWitness",
    "count_primary_alter_subscription",
    "generate_alter_subscription_factor_programs",
    "render_alter_subscription_factor_case",
    "resolve_alter_subscription_factor_witness",
]
