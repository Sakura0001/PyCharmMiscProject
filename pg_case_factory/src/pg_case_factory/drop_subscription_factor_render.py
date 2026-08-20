"""Render complete PostgreSQL 18.4 DROP SUBSCRIPTION factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.
The file is assembled from a single _resolve_case plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
SELECT count(*) <op> AS alias FROM pg_catalog.pg_subscription
WHERE subname = '...' ORDER BY count(*) LIMIT 1
never nests a FROM inside an EXISTS subquery, so audit_catalog_observability
accepts it.  The probe column is the real pg_subscription column (subname).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .drop_subscription_factor_extension import (
    DropSubscriptionFactorExtensionCase,
)
from .drop_subscription_factor_loop import (
    DropSubscriptionFactorCase,
    DropSubscriptionFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/subscription/"
    "drop_subscription.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/subscription/"
    "drop_subscription.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-21"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

# Baseline primaries whose target subscription is intentionally absent, so
# the DROP surfaces a not-found error (42704) and the oracle asserts absence.
_ABSENT_SUBSCRIPTION_PRIMARIES = frozenset(
    {
        ("expected_status", "failure"),
        ("subscription_existence", "subscription_not_exists"),
        ("nonexistent_subscription", "subscription_does_not_exist"),
        ("subscription_name_shape", "non_existing_name"),
    }
)

# For an extension SUCCESS case the synthetic primary is a neutral success
# primary whose helpers fall through to the assignment.
_BRANCH_NEUTRAL_SUCCESS = ("subscription_existence", "subscription_exists")

# Dummy conninfo for CREATE SUBSCRIPTION (never executed in no-DB phase).
_DUMMY_CONNINFO = "host=127.0.0.1 port=1 dbname=dummy"


def _synthetic_case(
    ext: DropSubscriptionFactorExtensionCase,
) -> DropSubscriptionFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .drop_subscription_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropSubscriptionFactorCase(
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
    case: DropSubscriptionFactorCase | DropSubscriptionFactorExtensionCase,
) -> DropSubscriptionFactorCase:
    if isinstance(case, DropSubscriptionFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropSubscriptionFactorRenderError(ValueError):
    """Raised when a DROP SUBSCRIPTION case cannot be rendered."""


@dataclass(frozen=True)
class DropSubscriptionFactorWitness:
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


def _baseline(case: DropSubscriptionFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _subscription_created(case: DropSubscriptionFactorCase, a: dict[str, str]) -> bool:
    """Whether a fixture subscription must be created."""

    if a.get("subscription_existence") == "subscription_not_exists":
        return False
    if a.get("subscription_name_shape") == "non_existing_name":
        return False
    if a.get("nonexistent_subscription") == "subscription_does_not_exist":
        return False
    if a.get("expected_status") == "failure":
        return False
    return True


def _subscription_target_name(
    case: DropSubscriptionFactorCase, a: dict[str, str], p: str
) -> str:
    """The subscription name as referenced inside DROP SUBSCRIPTION."""

    shape = a.get("subscription_name_shape", "simple_name")
    if shape == "quoted_name":
        return f'"{p}qsub"'
    if shape == "reserved_word_name":
        return '"user"'
    if shape == "non_existing_name":
        return f"{p}nosub"
    return f"{p}sub"


def _subscription_probe_name(
    case: DropSubscriptionFactorCase, a: dict[str, str], p: str
) -> str:
    """The bare subscription name (no quotes) for the catalog probe."""

    shape = a.get("subscription_name_shape", "simple_name")
    if shape == "quoted_name":
        return f"{p}qsub"
    if shape == "reserved_word_name":
        return "user"
    if shape == "non_existing_name":
        return f"{p}nosub"
    return f"{p}sub"


def _if_exists_present(
    case: DropSubscriptionFactorCase, a: dict[str, str]
) -> bool:
    return a.get("if_exists_clause") == "with_if_exists"


def _cascade_clause(a: dict[str, str]) -> str:
    cascade = a.get("cascade_restrict_clause", "no_clause_default_restrict")
    if cascade == "cascade":
        return "CASCADE"
    if cascade == "restrict":
        return "RESTRICT"
    return ""


def _effective_role(
    case: DropSubscriptionFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP SUBSCRIPTION runs."""

    if case.kind == "EXT":
        if a.get("privilege_context") == "non_superuser_no_privilege":
            return f"{p}actor"
        if a.get("executor_privilege") == "non_superuser":
            return f"{p}actor"
        return ""
    if case.factor_key == "privilege_context":
        return f"{p}actor" if case.factor_value == "non_superuser_no_privilege" else ""
    if case.factor_key == "executor_privilege":
        return f"{p}actor" if case.factor_value == "non_superuser" else ""
    if case.factor_key == "privilege_insufficient":
        return f"{p}actor" if case.factor_value == "non_superuser_dropping_subscription" else ""
    return ""


def _subscription_absent_after(
    case: DropSubscriptionFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target subscription is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if not _subscription_created(case, a):
        return True
    if case.outcome == "success":
        return True
    return False


def _probe_select(
    case: DropSubscriptionFactorCase, a: dict[str, str], p: str
) -> str:
    probe_name = _subscription_probe_name(case, a, p)
    absent = _subscription_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "subscription_absent" if absent else "subscription_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_subscription "
        f"WHERE subname = '{probe_name}' "
        "ORDER BY count(*) LIMIT 1;"
    )


def _role_names(
    case: DropSubscriptionFactorCase, p: str, effective: str
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}actor":
        roles.append(f"{p}actor")
    return tuple(roles)


def _resolve_case(case: DropSubscriptionFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    sub_created = _subscription_created(case, a)
    target_name = _subscription_target_name(case, a, p)

    setup: list[str] = []
    locus = "target.subscription"

    # --- setup boundary SELECT (prevents \set from merging with the first
    # CREATE so the bookend gate detects objects at col 0) ---
    setup.append("SELECT 1 AS setup_boundary;")

    # --- role fixtures (CREATE only; SET ROLE deferred to after the
    # subscription fixture so they run as the superuser) ---
    effective = _effective_role(case, a, p)
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- the subscription fixture (CREATE SUBSCRIPTION as superuser) ---
    if sub_created:
        setup.append(
            f"CREATE SUBSCRIPTION {target_name} "
            f"CONNECTION '{_DUMMY_CONNINFO}' "
            "PUBLICATION dummy_pub WITH (connect = false);"
        )
        if locus == "target.subscription":
            locus = "fixture.subscription"
    else:
        setup.append(
            "SELECT 1 AS target_subscription_intentionally_absent;"
        )
        locus = "fixture.object_state"

    # --- arm the non-superuser role (AFTER subscription creation) ----------
    if effective:
        setup.append(f"SET ROLE {p}actor;")
    if_exists = "IF EXISTS " if _if_exists_present(case, a) else ""
    cascade = _cascade_clause(a)
    target = f"DROP SUBSCRIPTION {if_exists}{target_name}"
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

    # --- cleanup construction -------------------------------------------
    subscription_drop = [
        f"DROP SUBSCRIPTION IF EXISTS {target_name} CASCADE;"
    ]
    roles = _role_names(case, p, effective)
    role_drops = [
        statement
        for role in roles
        for statement in (
            f"DROP OWNED BY {role};",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    # Pre-cleanup: DROP SUBSCRIPTION first, then role drops.
    pre_cleanup: list[str] = []
    pre_cleanup.extend(subscription_drop)
    pre_cleanup.extend(role_drops)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # Cleanup: RESET ROLE, then subscription drops, then role drops.
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(subscription_drop)
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


def resolve_drop_subscription_factor_witness(
    case: DropSubscriptionFactorCase | DropSubscriptionFactorExtensionCase,
    repository_root: Path,
) -> DropSubscriptionFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropSubscriptionFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_subscription(sql: str) -> int:
    """Count the single credited DROP SUBSCRIPTION inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*DROP\s+SUBSCRIPTION\b", region)
    )


def _header(case: DropSubscriptionFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP SUBSCRIPTION {case.factor_key}={case.factor_value}",
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


def render_drop_subscription_factor_case(
    case: DropSubscriptionFactorCase | DropSubscriptionFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP SUBSCRIPTION regress program."""

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地订阅和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP SUBSCRIPTION。")
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


def generate_drop_subscription_factor_programs(
    baseline_plan: DropSubscriptionFactorLoopPlan,
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
    case: DropSubscriptionFactorCase | DropSubscriptionFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_subscription_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropSubscriptionFactorRenderError",
    "DropSubscriptionFactorWitness",
    "count_primary_drop_subscription",
    "generate_drop_subscription_factor_programs",
    "render_drop_subscription_factor_case",
    "resolve_drop_subscription_factor_witness",
]
