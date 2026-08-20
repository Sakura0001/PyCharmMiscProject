"""Render complete PostgreSQL 18.4 DROP INDEX factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.

Every DROP INDEX program is table-based: a base ``CREATE TABLE {p}t`` carries
the index fixture, so the object-naming bookend gate applies — the first and
last executable statements are always ``DROP TABLE IF EXISTS {p}t``.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_class ... ORDER BY count(*)``
never nests a ``FROM`` inside an ``EXISTS`` subquery, so
``audit_catalog_observability`` accepts it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .drop_index_factor_extension import (
    DropIndexFactorExtensionCase,
)
from .drop_index_factor_loop import (
    DropIndexFactorCase,
    DropIndexFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/index/"
    "drop_index.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/index/"
    "drop_index.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

# Primary (factor, value) pairs where the target index is intentionally
# absent, so the drop surfaces a not-found error (or a no-op notice under
# IF EXISTS) and the oracle asserts absence.
_ABSENT_PRIMARIES = frozenset(
    {
        ("object_state", "not_exists"),
        ("name_shape", "missing_object"),
        ("expected_status", "failure"),
        ("expected_status", "no_op"),
    }
)

# Baseline primaries that imply a dependent constraint fixture must be
# created so that RESTRICT surfaces 2BP01.
_DEPENDENCY_PRIMARIES = frozenset(
    {
        ("object_state", "depended_by_constraint"),
        ("invalid_combination", "restrict_with_dependency"),
    }
)

# Baseline primaries that force CONCURRENTLY on for the DROP INDEX target
# (the invalid_combination values that centre on a CONCURRENTLY misuse).
_CONCURRENTLY_FORCED_PRIMARIES = frozenset(
    {
        ("invalid_combination", "concurrently_in_transaction"),
        ("invalid_combination", "concurrently_on_partitioned"),
        ("invalid_combination", "concurrently_with_cascade"),
        ("invalid_combination", "concurrently_with_multiple_indexes"),
        ("statement_branch", "drop_concurrently"),
    }
)

# Baseline primaries that force a partitioned base table (so CONCURRENTLY
# surfaces 0A000 on a partitioned index).
_PARTITIONED_PRIMARIES = frozenset(
    {
        ("invalid_combination", "concurrently_on_partitioned"),
    }
)

# For an extension SUCCESS case (no present failure pair) the synthetic
# primary must be a neutral success primary whose helpers fall through to the
# assignment; the index always exists in extensions (object_state held at
# exists unless the not-exist negative fires).
_BRANCH_NEUTRAL_SUCCESS = ("object_state", "exists")


def _synthetic_case(
    ext: DropIndexFactorExtensionCase,
) -> DropIndexFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .drop_index_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropIndexFactorCase(
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
    case: DropIndexFactorCase | DropIndexFactorExtensionCase,
) -> DropIndexFactorCase:
    if isinstance(case, DropIndexFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropIndexFactorRenderError(ValueError):
    """Raised when a DROP INDEX case cannot be rendered."""


@dataclass(frozen=True)
class DropIndexFactorWitness:
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


def _baseline(case: DropIndexFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _idx_name(case: DropIndexFactorCase, a: dict[str, str], p: str) -> str:
    """The index name as referenced inside DROP INDEX."""

    shape = a.get("name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f'"{p}IdxQ"'
    if shape == "reserved_word":
        return f'"{p}column"'
    if shape == "schema_qualified":
        return f"public.{p}idx"
    if shape == "missing_object":
        return f"{p}missing_idx"
    return f"{p}idx"


def _probe_name(case: DropIndexFactorCase, a: dict[str, str], p: str) -> str:
    """The bare index name (no quotes/schema) for the catalog probe."""

    shape = a.get("name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f"{p}IdxQ"
    if shape == "reserved_word":
        return f"{p}column"
    if shape == "missing_object":
        return f"{p}missing_idx"
    return f"{p}idx"


def _idx2_name(p: str) -> str:
    return f"{p}idx2"


def _table_name(p: str) -> str:
    return f"{p}t"


def _constraint_name(p: str) -> str:
    return f"{p}ukey"


def _fixture_kind(
    case: DropIndexFactorCase, a: dict[str, str]
) -> str:
    """Whether an index fixture must be created."""

    if case.kind == "RISK":
        return "index"
    if (case.factor_key, case.factor_value) in _ABSENT_PRIMARIES:
        return "none"
    if case.kind == "EXT":
        if a.get("object_state") == "not_exists":
            return "none"
        if a.get("name_shape") == "missing_object":
            return "none"
    return "index"


def _if_exists_present(
    case: DropIndexFactorCase, a: dict[str, str]
) -> bool:
    if case.kind == "EXT":
        return a.get("if_exists") == "true"
    if (case.factor_key, case.factor_value) == ("expected_status", "no_op"):
        return True
    return a.get("if_exists") == "true"


def _concurrently_present(
    case: DropIndexFactorCase, a: dict[str, str]
) -> bool:
    if case.kind == "EXT":
        return a.get("concurrently") == "true"
    if (case.factor_key, case.factor_value) in _CONCURRENTLY_FORCED_PRIMARIES:
        return True
    return a.get("concurrently") == "true"


def _multi_index_present(
    case: DropIndexFactorCase, a: dict[str, str]
) -> bool:
    if case.kind == "EXT":
        return a.get("multi_index") == "multiple"
    if case.factor_key == "statement_branch" and case.factor_value == "drop_multiple":
        return True
    if (
        case.factor_key == "invalid_combination"
        and case.factor_value == "concurrently_with_multiple_indexes"
    ):
        return True
    return a.get("multi_index") == "multiple"


def _cascade_clause(case: DropIndexFactorCase, a: dict[str, str]) -> str:
    if case.factor_key == "statement_branch" and case.factor_value == "drop_cascade":
        return "CASCADE"
    if (
        case.factor_key == "invalid_combination"
        and case.factor_value == "concurrently_with_cascade"
    ):
        return "CASCADE"
    cascade = a.get("cascade_restrict", "restrict")
    if cascade == "cascade":
        return "CASCADE"
    return "RESTRICT"


def _is_partitioned(
    case: DropIndexFactorCase, a: dict[str, str]
) -> bool:
    return (case.factor_key, case.factor_value) in _PARTITIONED_PRIMARIES


def _effective_role(
    case: DropIndexFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP INDEX runs."""

    if case.kind == "EXT":
        level = a.get("permission", "owner")
        return f"{p}actor" if level == "non_owner" else ""
    if case.factor_key == "permission" and case.factor_value == "non_owner":
        return f"{p}actor"
    if case.factor_key == "permission_insufficient" and case.factor_value in (
        "non_owner_drop",
        "no_schema_privilege",
    ):
        return f"{p}actor"
    return ""


def _needs_dependent(
    case: DropIndexFactorCase, a: dict[str, str]
) -> bool:
    """Whether a dependent constraint fixture must be created."""

    if case.kind == "EXT":
        return a.get("dependency_type") == "unique_pk_constraint"
    if (case.factor_key, case.factor_value) in _DEPENDENCY_PRIMARIES:
        return True
    return a.get("dependency_type") == "unique_pk_constraint"


def _index_absent_after(
    case: DropIndexFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target index is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if _fixture_kind(case, a) == "none":
        return True
    if case.outcome == "success":
        return True
    return False


def _probe_select(
    case: DropIndexFactorCase, a: dict[str, str], p: str
) -> str:
    name = _probe_name(case, a, p)
    absent = _index_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "index_absent" if absent else "index_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_class "
        f"WHERE relname = '{name}' AND relkind = 'i' "
        "ORDER BY count(*) LIMIT 1;"
    )


def _role_names(
    case: DropIndexFactorCase, p: str, effective: str
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}actor":
        roles.append(f"{p}actor")
    return tuple(roles)


def _resolve_case(case: DropIndexFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    fixture_kind = _fixture_kind(case, a)
    idx_ref = _idx_name(case, a, p)
    table = _table_name(p)
    idx2 = _idx2_name(p)
    constraint = _constraint_name(p)
    needs_dep = _needs_dependent(case, a)
    partitioned = _is_partitioned(case, a)

    setup: list[str] = []
    locus = "target.index"

    # --- role fixtures (CREATE only; SET ROLE deferred to after the index
    # fixture so they run as the superuser) ---
    effective = _effective_role(case, a, p)
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- the base table fixture (always present; carries the index) -------
    if partitioned:
        setup.append(f"CREATE TABLE {table} (c integer) PARTITION BY RANGE (c);")
    else:
        setup.append(f"CREATE TABLE {table} (c integer);")

    # --- the target index fixture (as superuser, before SET ROLE) ---------
    method = a.get("index_method", "btree")
    if fixture_kind == "index":
        if needs_dep:
            setup.append(
                f"CREATE UNIQUE INDEX {idx_ref} ON {table} USING btree (c);"
            )
            setup.append(
                f"ALTER TABLE {table} ADD CONSTRAINT {constraint} "
                f"UNIQUE USING INDEX {idx_ref};"
            )
            locus = "fixture.dependency_state"
        else:
            setup.append(
                f"CREATE INDEX {idx_ref} ON {table} USING {method} (c);"
            )
        if _multi_index_present(case, a):
            setup.append(
                f"CREATE INDEX {idx2} ON {table} USING {method} (c);"
            )
    else:
        setup.append(
            "SELECT 1 AS target_index_intentionally_absent;"
        )
        locus = "fixture.object_state"

    # --- arm the non-superuser role (AFTER index creation) ----------------
    if effective:
        setup.append(f"SET ROLE {p}actor;")

    # --- build the target DROP INDEX fragment -----------------------------
    if case.factor_key == "syntax_error" and case.factor_value == "invalid_syntax":
        if_exists = "IF EXISTS " if _if_exists_present(case, a) else ""
        target = f"DROP INDEX {if_exists}{idx_ref} CASCADE RESTRICT;"
    else:
        concurrently = (
            "CONCURRENTLY " if _concurrently_present(case, a) else ""
        )
        if_exists = "IF EXISTS " if _if_exists_present(case, a) else ""
        names = idx_ref
        if _multi_index_present(case, a):
            names = f"{idx_ref}, {idx2}"
        cascade = _cascade_clause(case, a)
        target = f"DROP INDEX {concurrently}{if_exists}{names}"
        target += f" {cascade}"
        target += ";"

    # RISK / concurrently-in-transaction wrapper around the target.
    in_transaction = False
    if case.kind == "RISK":
        setup.append("BEGIN;")
        locus = "target.transaction_boundary"
    elif (
        case.factor_key == "invalid_combination"
        and case.factor_value == "concurrently_in_transaction"
    ):
        setup.append("BEGIN;")
        locus = "target.transaction_boundary"
        in_transaction = True

    # --- oracle / SQLSTATE assertion ------------------------------------
    assert_lines: list[str] = []
    if effective:
        assert_lines.append("RESET ROLE;")
    if case.kind == "RISK":
        assert_lines.append(
            "COMMIT;" if case.factor_value == "commit" else "ROLLBACK;"
        )
    if in_transaction:
        assert_lines.append("ROLLBACK;")
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    assert_lines.append(_probe_select(case, a, p))

    # --- cleanup construction -------------------------------------------
    index_drops = [f"DROP INDEX IF EXISTS {idx_ref};"]
    if _multi_index_present(case, a):
        index_drops.append(f"DROP INDEX IF EXISTS {idx2};")
    table_drop = f"DROP TABLE IF EXISTS {table} CASCADE;"
    roles = _role_names(case, p, effective)
    role_drops = [
        statement
        for role in roles
        for statement in (
            f"DROP OWNED BY {role};",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    # Pre-cleanup: DROP TABLE first (bookend gate), then indexes, then roles.
    pre_cleanup: list[str] = []
    pre_cleanup.append(table_drop)
    pre_cleanup.extend(index_drops)
    pre_cleanup.extend(role_drops)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # Cleanup: RESET ROLE, then index drops, then role drops, then DROP
    # TABLE last (bookend gate).
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(index_drops)
    cleanup.extend(role_drops)
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


def resolve_drop_index_factor_witness(
    case: DropIndexFactorCase | DropIndexFactorExtensionCase,
    repository_root: Path,
) -> DropIndexFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropIndexFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_index(sql: str) -> int:
    """Count the single credited DROP INDEX inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*DROP\s+INDEX\b", region)
    )


def _header(case: DropIndexFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP INDEX {case.factor_key}={case.factor_value}",
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


def render_drop_index_factor_case(
    case: DropIndexFactorCase | DropIndexFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP INDEX regress program."""

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地索引和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP INDEX。")
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


def generate_drop_index_factor_programs(
    baseline_plan: DropIndexFactorLoopPlan,
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
    case: DropIndexFactorCase | DropIndexFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_index_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropIndexFactorRenderError",
    "DropIndexFactorWitness",
    "count_primary_drop_index",
    "generate_drop_index_factor_programs",
    "render_drop_index_factor_case",
    "resolve_drop_index_factor_witness",
]
