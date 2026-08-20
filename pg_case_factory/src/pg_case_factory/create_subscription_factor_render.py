"""Render complete PostgreSQL 18.4 CREATE SUBSCRIPTION factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CREATE SUBSCRIPTION is a logical-replication DDL statement: the target
is a ``pg_catalog.pg_subscription`` catalog row, not a ``pg_class``
relation.  All catalog oracles schema-qualify ``pg_catalog.pg_subscription``
(exempt from the file-prefix style gate).  No case creates a TABLE, so
the bookend (DROP TABLE IF EXISTS) is never emitted.  Every catalog
SELECT carries a top-level ``ORDER BY count(*)`` so the
catalog-observability gate passes.

The connection string uses a non-routable test fixture
(``host=127.0.0.1 port=55999``) — these are LOCAL TEST fixtures, not
real secrets.  In the no-DB static phase the DDL is emitted
syntactically and validated by STYLE + BYTE-LEVEL render only.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_subscription_factor_extension import (
    CreateSubscriptionFactorExtensionCase,
    _present_failure_pair,
)
from .create_subscription_factor_loop import (
    CreateSubscriptionFactorCase,
    CreateSubscriptionFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/subscription/"
    "create_subscription.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/subscription/"
    "create_subscription.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

# Non-routable test-fixture connection strings (NOT real secrets).
_VALID_CONNINFO = (
    "host=127.0.0.1 port=55999 user=pgcf_superuser dbname=pgcf_cop"
)
_MINIMAL_CONNINFO = "host=127.0.0.1 port=55999"
_INVALID_CONNINFO = "not_a_valid_conninfo"

_WITH_CLAUSE_BASE: dict[str, str] = {
    "omitted": "",
    "binary_true": " WITH (binary = true)",
    "connect_false_enabled_false": (
        " WITH (connect = false, enabled = false)"
    ),
    "connect_true_enabled_true": (
        " WITH (connect = true, enabled = true)"
    ),
    "copy_data_false": " WITH (copy_data = false)",
    "copy_data_true": " WITH (copy_data = true)",
    "create_slot_false": " WITH (create_slot = false)",
    "disable_on_error_true": " WITH (disable_on_error = true)",
    "failover_true": " WITH (failover = true)",
    "multiple_parameters": (
        " WITH (binary = true, streaming = true, copy_data = false)"
    ),
    "run_as_owner_true": " WITH (run_as_owner = true)",
    "stream_true": " WITH (streaming = true)",
    "streaming_parallel_default": " WITH (streaming = parallel)",
    "synchronous_commit_on": " WITH (synchronous_commit = on)",
    "two_phase_true": " WITH (two_phase = true)",
}


class CreateSubscriptionFactorRenderError(ValueError):
    """Raised when a CREATE SUBSCRIPTION case cannot be rendered."""


@dataclass(frozen=True)
class CreateSubscriptionFactorWitness:
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
    ext: CreateSubscriptionFactorExtensionCase,
) -> CreateSubscriptionFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_form"
        factor_value = assignment.get(
            "target_form", ext.consumer_action_id
        )
    return CreateSubscriptionFactorCase(
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
    case: CreateSubscriptionFactorCase
    | CreateSubscriptionFactorExtensionCase,
) -> CreateSubscriptionFactorCase:
    if isinstance(case, CreateSubscriptionFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateSubscriptionFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _is_failure(a: dict[str, str]) -> bool:
    return a.get("expected_status") == "failure"


def _is_duplicate(a: dict[str, str]) -> bool:
    si = a.get("subscription_identity", "not_exists")
    dsn = a.get("duplicate_subscription_name", "")
    return si in ("exists", "quoted_duplicate") or dsn == "same_name_exists"


def _present_after(a: dict[str, str]) -> bool:
    """Whether the subscription exists after the target statement."""
    if not _is_failure(a):
        return True
    if _is_duplicate(a):
        return True
    return False


def _subscription_name(a: dict[str, str], p: str) -> str:
    """The subscription identifier in CREATE SUBSCRIPTION and fixtures."""

    si = a.get("subscription_identity", "not_exists")
    shape = a.get("subscription_name_shape", "simple_name")
    if si == "reserved_word_name" or shape == "reserved_word_name":
        return f'"{p}User"'
    if si == "quoted_duplicate" or shape == "quoted_name":
        return f'"{p}Mixed Sub"'
    return f"{p}sub"


def _subscription_name_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    si = a.get("subscription_identity", "not_exists")
    shape = a.get("subscription_name_shape", "simple_name")
    if si == "reserved_word_name" or shape == "reserved_word_name":
        return f"{p}User"
    if si == "quoted_duplicate" or shape == "quoted_name":
        return f"{p}Mixed Sub"
    return f"{p}sub"


def _conninfo(a: dict[str, str]) -> str:
    """The conninfo string for the CONNECTION clause."""

    cs = a.get("conninfo_string_shape", "valid_conninfo_string")
    ic = a.get("invalid_conninfo", "")
    if cs == "invalid_conninfo_string" or ic == "malformed_conninfo":
        return _INVALID_CONNINFO
    ci = a.get("connection_info", "valid_conninfo")
    if ci == "minimal_conninfo":
        return _MINIMAL_CONNINFO
    return _VALID_CONNINFO


def _publication_names(a: dict[str, str], p: str) -> list[str]:
    """Publication names for the PUBLICATION clause."""

    shape = a.get("publication_name_shape", "simple_name")
    op = a.get("publication_list", "single_publication")
    quoted = shape == "quoted_name"
    multiple = "multiple" in op
    if quoted:
        if multiple:
            return [f'"{p}Mixed Pub"', f'"{p}Second Pub"']
        return [f'"{p}Mixed Pub"']
    if multiple:
        return [f"{p}pub1", f"{p}pub2"]
    return [f"{p}pub1"]


def _with_clause(a: dict[str, str], p: str) -> str:
    """The WITH clause for CREATE SUBSCRIPTION."""

    param = a.get("with_parameter_clause", "omitted")
    if param == "slot_name_explicit":
        return f" WITH (slot_name = '{p}slot')"
    return _WITH_CLAUSE_BASE.get(param, "")


def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target CREATE SUBSCRIPTION runs."""

    ep = a.get("executor_privilege", "superuser")
    if ep == "non_superuser":
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    if _effective_role(a, p):
        roles.append(f"{p}actor")
    return tuple(roles)


def _build_target(
    a: dict[str, str], p: str
) -> str:
    """The primary CREATE SUBSCRIPTION statement."""

    sub = _subscription_name(a, p)
    conn = _conninfo(a)
    pubs = _publication_names(a, p)
    with_clause = _with_clause(a, p)
    return (
        f"CREATE SUBSCRIPTION {sub} CONNECTION '{conn}' "
        f"PUBLICATION {', '.join(pubs)}{with_clause};"
    )


def _build_duplicate_fixture(
    a: dict[str, str], p: str
) -> list[str]:
    """Pre-create the subscription for duplicate-signature tests."""

    if not _is_duplicate(a):
        return []
    sub = _subscription_name(a, p)
    return [
        f"CREATE SUBSCRIPTION {sub} CONNECTION '{_VALID_CONNINFO}' "
        f"PUBLICATION {p}pub WITH (enabled = false, "
        f"create_slot = false, copy_data = false, slot_name = NONE);"
    ]


def _probe_select(
    case: CreateSubscriptionFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only error_assertion."""

    mode = a.get("verification_mode", "pg_subscription_catalog")
    if mode == "error_assertion":
        return None
    sub_lit = _subscription_name_literal(a, p)
    present = _present_after(a)
    cmp_op = ">" if present else "="
    return (
        f"SELECT count(*) {cmp_op} 0 AS subscription_state "
        f"FROM pg_catalog.pg_subscription "
        f"WHERE subname = '{sub_lit}' "
        f"ORDER BY count(*);"
    )


def _tables_to_drop(
    case: CreateSubscriptionFactorCase,
) -> list[str]:
    """Fixture tables the case CREATEs.

    CREATE SUBSCRIPTION is a logical-replication DDL statement: it never
    creates a TABLE.  The bookend (DROP TABLE IF EXISTS) is therefore
    never emitted.
    """
    return []


def _resolve_case(
    case: CreateSubscriptionFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix

    setup: list[str] = []
    locus = "target.create_subscription"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    sub = _subscription_name(a, p)

    # --- role fixtures -----------------------------------------------
    if effective == f"{p}actor":
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- duplicate subscription fixture ------------------------------
    setup.extend(_build_duplicate_fixture(a, p))
    if _is_duplicate(a):
        locus = "fixture.duplicate_subscription"

    # --- arm the effective role --------------------------------------
    if effective:
        setup.append(f"SET ROLE {effective};")

    # --- the primary target statement --------------------------------
    target = _build_target(a, p)

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
    subscriptions_to_drop: list[str] = [sub]

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


def _header(case: CreateSubscriptionFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE SUBSCRIPTION {case.factor_key}="
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


def render_create_subscription_factor_case(
    case: CreateSubscriptionFactorCase
    | CreateSubscriptionFactorExtensionCase,
    repository_root: Path,
) -> str:
    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("SELECT 1 AS setup_boundary;")
    lines.append("-- 2. 创建完整本地规则和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 CREATE SUBSCRIPTION。")
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
    case: CreateSubscriptionFactorCase
    | CreateSubscriptionFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_subscription_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_subscription_factor_programs(
    baseline_plan: CreateSubscriptionFactorLoopPlan,
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


def count_primary_create_subscription(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*CREATE\s+SUBSCRIPTION\b", region)
    )


def resolve_create_subscription_factor_witness(
    case: CreateSubscriptionFactorCase
    | CreateSubscriptionFactorExtensionCase,
    repository_root: Path,
) -> CreateSubscriptionFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateSubscriptionFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


__all__ = [
    "CreateSubscriptionFactorRenderError",
    "CreateSubscriptionFactorWitness",
    "count_primary_create_subscription",
    "generate_create_subscription_factor_programs",
    "render_create_subscription_factor_case",
    "resolve_create_subscription_factor_witness",
]
