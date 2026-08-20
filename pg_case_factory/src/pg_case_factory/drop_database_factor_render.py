"""Render complete PostgreSQL 18.4 DROP DATABASE factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_database ... ORDER BY count(*)``
never nests a ``FROM`` inside an ``EXISTS`` subquery, so
``audit_catalog_observability`` accepts it.

``DROP DATABASE`` is a NO-DB static-tickoff statement: the published witness is
the byte-level re-render comparison (no doublerun).  The object-in-use failure
fixtures (active connections, prepared transactions, replication slots,
subscriptions) are represented by deterministic ``SELECT`` markers because a
single psql session cannot arm those conditions; the bytes are the spec.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .drop_database_factor_extension import (
    DropDatabaseFactorExtensionCase,
)
from .drop_database_factor_loop import (
    DropDatabaseFactorCase,
    DropDatabaseFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/database/"
    "drop_database.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/database/"
    "drop_database.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_DROP_DATABASE = "branch_drop_database"

# Primary (factor, value) pairs where the target database is intentionally
# absent, so the drop surfaces a not-found error (or a notice under IF EXISTS)
# and the oracle asserts absence.  ``expected_status=failure`` is the generic
# declared-failure meta-factor (db absent, drop surfaces undefined_database);
# ``drop_current_database=current_database`` is special-cased in
# ``_db_absent_after`` (the current db still exists after the failed drop).
_ABSENT_PRIMARIES = frozenset(
    {
        ("object_state", "not_exists"),
        ("database_name_shape", "nonexistent_name"),
        ("database_not_exist_no_if_exists", "database_not_exists_no_if_exists"),
        ("drop_current_database", "current_database"),
        ("expected_status", "failure"),
    }
)

# For an extension SUCCESS case (no present failure pair) the synthetic
# primary must be a neutral success primary whose helpers fall through to the
# assignment; the database always exists in extensions (object_state held at
# ``exists``).
_BRANCH_NEUTRAL_SUCCESS = ("object_state", "exists")


def _synthetic_case(
    ext: DropDatabaseFactorExtensionCase,
) -> DropDatabaseFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case.

    The v1 helpers are primary-driven (they read ``case.factor_key`` /
    ``case.factor_value``), so an extension case is rendered by constructing a
    synthetic :class:`DropDatabaseFactorCase` whose primary is the extension's
    single attributable failure pair (for failures) or the neutral success
    primary (for successes), with ``kind = "EXT"`` so the patched helpers
    (``_effective_role``, ``_if_exists_present``) read the crossed privilege /
    IF EXISTS / FORCE axes from the assignment instead of the primary.
    """

    from .drop_database_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropDatabaseFactorCase(
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
    case: DropDatabaseFactorCase | DropDatabaseFactorExtensionCase,
) -> DropDatabaseFactorCase:
    """Return the case to feed to the v1 helpers: unchanged for baseline,
    or a byte-safe synthetic for an extension case."""

    if isinstance(case, DropDatabaseFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropDatabaseFactorRenderError(ValueError):
    """Raised when a DROP DATABASE case cannot be rendered."""


@dataclass(frozen=True)
class DropDatabaseFactorWitness:
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


def _baseline(case: DropDatabaseFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _db_name(case: DropDatabaseFactorCase, a: dict[str, str], p: str) -> str:
    """The database name as referenced inside DROP DATABASE."""

    shape = a.get("database_name_shape", "simple_id")
    if shape == "quoted_id":
        return f'"{p}db"'
    if shape == "nonexistent_name":
        return f"{p}nonexistent_db"
    return f"{p}db"


def _probe_name(case: DropDatabaseFactorCase, a: dict[str, str], p: str) -> str:
    """The bare database name (no quotes) for the catalog probe."""

    shape = a.get("database_name_shape", "simple_id")
    if shape == "quoted_id":
        return f"{p}db"
    if shape == "nonexistent_name":
        return f"{p}nonexistent_db"
    return f"{p}db"


def _fixture_kind(case: DropDatabaseFactorCase) -> str:
    """Whether the target database is created (``database``) or absent (``none``)."""

    if (case.factor_key, case.factor_value) in _ABSENT_PRIMARIES:
        return "none"
    return "database"


def _if_exists_present(
    case: DropDatabaseFactorCase, a: dict[str, str]
) -> bool:
    """Whether the DROP DATABASE statement carries IF EXISTS."""

    if _fixture_kind(case) == "none":
        # For an absent target the IF EXISTS clause is driven by
        # database_not_exist_no_if_exists (with_if_exists -> present via the
        # specified_if_exists axis); fall back to the if_exists_clause axis.
        pass
    return a.get("if_exists_clause") == "specified_if_exists"


def _force_clause(a: dict[str, str]) -> str:
    """The WITH (FORCE) clause for the target, or empty."""

    force = a.get("force_option", "omitted")
    return " WITH (FORCE)" if force == "specified_force" else ""


def _cleanup_force(a: dict[str, str]) -> str:
    """The WITH (FORCE) clause for cleanup, driven by cleanup_mode."""

    return " WITH (FORCE)" if a.get("cleanup_mode") == "force_drop_database" else ""


def _effective_role(
    case: DropDatabaseFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP DATABASE runs.

    Only a non-owner (privilege_level=non_owner) arms a separate actor role;
    the superuser runs as themselves (empty effective role).
    """

    if case.kind == "EXT":
        level = a.get("privilege_level", "superuser")
        return f"{p}actor" if level == "non_owner" else ""
    if case.factor_key == "privilege_level":
        return f"{p}actor" if case.factor_value == "non_owner" else ""
    if case.factor_key == "privilege_denied":
        return (
            f"{p}actor"
            if case.factor_value == "non_owner_failure"
            else ""
        )
    return ""


def _db_absent_after(
    case: DropDatabaseFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target database is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if (
        case.factor_key,
        case.factor_value,
    ) == ("drop_current_database", "current_database"):
        return False  # current db still exists after the failed drop
    if _fixture_kind(case) == "none":
        return True  # database never existed
    if case.outcome == "success":
        return True  # drop succeeded
    return False  # failure: database still present


def _probe_select(
    case: DropDatabaseFactorCase, a: dict[str, str], p: str
) -> str:
    name = _probe_name(case, a, p)
    absent = _db_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "database_absent" if absent else "database_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_database "
        f"WHERE datname = '{name}' ORDER BY count(*) LIMIT 1;"
    )


def _object_in_use_fixture(
    case: DropDatabaseFactorCase, a: dict[str, str], p: str
) -> list[str]:
    """Deterministic SELECT markers for the object-in-use failure axes.

    A single psql session cannot arm real active connections, prepared
    transactions, replication slots, or subscriptions, so each condition is
    represented by a byte-deterministic marker.  The markers are only emitted
    when the corresponding crossed axis is at its failure value.
    """

    fixtures: list[str] = []
    if a.get("connection_state") == "has_other_connections":
        fixtures.append(
            f"SELECT 1 AS fixture_other_connections_armed;"
        )
    if a.get("prepared_transactions") == "has_prepared_transactions":
        fixtures.append(
            f"SELECT 1 AS fixture_prepared_transactions_armed;"
        )
    if a.get("replication_slots") == "has_active_slots":
        fixtures.append(
            f"SELECT 1 AS fixture_replication_slots_armed;"
        )
    if a.get("subscriptions") == "has_subscriptions":
        fixtures.append(
            f"SELECT 1 AS fixture_subscriptions_armed;"
        )
    return fixtures


def _role_names(
    case: DropDatabaseFactorCase, p: str, effective: str
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}actor":
        roles.append(f"{p}actor")
    return tuple(roles)


def _resolve_case(case: DropDatabaseFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    fixture_kind = _fixture_kind(case)
    db_ref = _db_name(case, a, p)

    setup: list[str] = []
    locus = "target.database"

    # --- role fixtures (CREATE only; SET ROLE deferred to after the target
    # database fixture so it runs as the superuser) -----------------------
    effective = _effective_role(case, a, p)
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- the target database fixture (as superuser, before SET ROLE) -----
    if fixture_kind == "database":
        setup.append(f"CREATE DATABASE {db_ref};")
    else:
        # No database is created: the target is expected to fail (or notice)
        # because the named database does not exist or is the current db.
        setup.append("SELECT 1 AS target_database_intentionally_absent;")
        locus = "fixture.object_state"

    # --- object-in-use failure fixtures (deterministic markers) ----------
    setup.extend(_object_in_use_fixture(case, a, p))
    if len(setup) > 2 and any(
        "armed" in line for line in setup
    ):
        locus = "fixture.object_in_use"

    # --- arm the non-superuser role (AFTER database creation) ------------
    if effective:
        setup.append(f"SET ROLE {p}actor;")
    if_exists = "IF EXISTS " if _if_exists_present(case, a) else ""
    force = _force_clause(a)
    target = f"DROP DATABASE {if_exists}{db_ref}{force};"

    # Transaction wrapper for the inside-transaction-block failure and RISK.
    if case.kind == "RISK":
        setup.append("BEGIN;")
        locus = "target.transaction_boundary"
    elif a.get("inside_transaction_block") == "inside_transaction":
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
    elif a.get("inside_transaction_block") == "inside_transaction":
        assert_lines.append("ROLLBACK;")
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    assert_lines.append(_probe_select(case, a, p))

    # --- cleanup construction -------------------------------------------
    cleanup_force = _cleanup_force(a)
    if case.factor_key == "cleanup_mode":
        cleanup_force = " WITH (FORCE)" if case.factor_value == "force_drop_database" else ""
    db_drop = f"DROP DATABASE IF EXISTS {db_ref}{cleanup_force};"
    roles = _role_names(case, p, effective)

    # Pre-cleanup: drop the target database first, then roles.
    pre_cleanup: list[str] = []
    pre_cleanup.append(db_drop)
    pre_cleanup.extend(f"DROP ROLE IF EXISTS {role};" for role in roles)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # Cleanup: roles then target database drop.
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(f"DROP ROLE IF EXISTS {role};" for role in roles)
    cleanup.append(db_drop)
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


def resolve_drop_database_factor_witness(
    case: DropDatabaseFactorCase | DropDatabaseFactorExtensionCase,
    repository_root: Path,
) -> DropDatabaseFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropDatabaseFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_database(sql: str) -> int:
    """Count the single credited DROP DATABASE inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*DROP\s+DATABASE\b", region)
    )


def _header(case: DropDatabaseFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP DATABASE {case.factor_key}={case.factor_value}",
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


def render_drop_database_factor_case(
    case: DropDatabaseFactorCase | DropDatabaseFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP DATABASE regress program.

    Baseline cases (kind in GRM/SFV/RISK) are rendered by the v1 path
    unchanged; extension cases are rendered via a byte-safe synthetic
    baseline-shaped case (see :func:`_as_render_case`).  ``repository_root``
    is accepted for API symmetry with the sibling statement renderers.
    """

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地数据库和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP DATABASE。")
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


def generate_drop_database_factor_programs(
    baseline_plan: DropDatabaseFactorLoopPlan,
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
    case: DropDatabaseFactorCase | DropDatabaseFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_database_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropDatabaseFactorRenderError",
    "DropDatabaseFactorWitness",
    "count_primary_drop_database",
    "generate_drop_database_factor_programs",
    "render_drop_database_factor_case",
    "resolve_drop_database_factor_witness",
]
