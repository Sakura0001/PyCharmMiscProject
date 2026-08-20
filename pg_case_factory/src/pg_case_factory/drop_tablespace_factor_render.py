"""Render complete PostgreSQL 18.4 DROP TABLESPACE factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL file.
The file is assembled from a single :func:`_resolve_case` plan so that the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

``DROP TABLESPACE`` is a cluster-level storage object: it does NOT create a
TABLE, so the bookend gate (DROP TABLE at first+last) is N/A (table-less
scripts are exempt).  The fixture creates only TABLESPACE objects (and a
ROLE for privilege-negative cases); the ``LOCATION`` path is parse-valid SQL
but is never accessed in the no-DB static phase.

The oracle probe is catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_tablespace WHERE spcname =
'...' ORDER BY count(*) LIMIT 1``.  ``spcname`` is the real PG18
``pg_tablespace`` name column (cols: oid, spcname, spcowner, spcacl,
spcoptions); a wrong column would pass all static gates yet be a permanent
latent runtime bug, so the column is verified.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .drop_tablespace_factor_extension import (
    DropTablespaceFactorExtensionCase,
)
from .drop_tablespace_factor_loop import (
    DropTablespaceFactorCase,
    DropTablespaceFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/tablespace/"
    "drop_tablespace.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/tablespace/"
    "drop_tablespace.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-21"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

# Baseline primaries whose target tablespace is intentionally absent, so the
# DROP surfaces a not-found error (42704) and the oracle asserts absence.
_ABSENT_TABLESPACE_PRIMARIES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "absent"),
        ("tablespace_name_shape", "non_existent_name"),
        ("error_type", "non_existent_without_if_exists"),
    }
)

# For an extension SUCCESS case the synthetic primary must be a neutral
# success primary whose helpers fall through to the assignment; the
# tablespace always exists in extensions unless object_state=absent /
# tablespace_name_shape=non_existent_name.
_BRANCH_NEUTRAL_SUCCESS = ("object_state", "exists")


def _synthetic_case(
    ext: DropTablespaceFactorExtensionCase,
) -> DropTablespaceFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .drop_tablespace_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropTablespaceFactorCase(
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
    case: DropTablespaceFactorCase | DropTablespaceFactorExtensionCase,
) -> DropTablespaceFactorCase:
    if isinstance(case, DropTablespaceFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropTablespaceFactorRenderError(ValueError):
    """Raised when a DROP TABLESPACE case cannot be rendered."""


@dataclass(frozen=True)
class DropTablespaceFactorWitness:
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


def _baseline(case: DropTablespaceFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _tablespace_created(
    case: DropTablespaceFactorCase, a: dict[str, str]
) -> bool:
    """Whether a TABLESPACE fixture must be created."""

    if a.get("object_state") != "exists":
        return False
    if a.get("tablespace_name_shape") == "non_existent_name":
        return False
    return True


def _tablespace_ref(
    case: DropTablespaceFactorCase, a: dict[str, str], p: str
) -> str:
    """The tablespace name as referenced inside CREATE/DROP (quoted if needed)."""

    shape = a.get("tablespace_name_shape", "simple_id")
    if shape == "quoted_id":
        return f'"{p}qts"'
    if shape == "reserved_word_id":
        return '"abort"'
    if shape == "non_existent_name":
        return f"{p}noexist"
    return f"{p}ts"  # simple_id, existing_name


def _tablespace_probe(
    case: DropTablespaceFactorCase, a: dict[str, str], p: str
) -> str:
    """The bare tablespace name (no quotes) for the catalog probe."""

    shape = a.get("tablespace_name_shape", "simple_id")
    if shape == "quoted_id":
        return f"{p}qts"
    if shape == "reserved_word_id":
        return "abort"
    if shape == "non_existent_name":
        return f"{p}noexist"
    return f"{p}ts"


def _if_exists_present(
    case: DropTablespaceFactorCase, a: dict[str, str]
) -> bool:
    return a.get("if_exists_clause") == "present"


def _effective_role(
    case: DropTablespaceFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP TABLESPACE runs."""

    if case.kind == "EXT":
        level = a.get("authorization_path", "superuser")
        return f"{p}actor" if level == "non_owner_non_superuser" else ""
    if case.factor_key == "authorization_path":
        return f"{p}actor" if case.factor_value == "non_owner_non_superuser" else ""
    if case.factor_key == "privilege_context":
        return f"{p}actor" if case.factor_value == "non_owner_session" else ""
    if case.factor_key == "error_type":
        return f"{p}actor" if case.factor_value == "insufficient_privilege" else ""
    return ""


def _is_transaction_block(
    case: DropTablespaceFactorCase, a: dict[str, str]
) -> bool:
    if case.kind == "EXT":
        return a.get("environment_context") == "inside_transaction_block"
    if case.factor_key == "environment_context":
        return case.factor_value == "inside_transaction_block"
    if case.factor_key == "error_type":
        return case.factor_value == "inside_transaction_block"
    return a.get("environment_context") == "inside_transaction_block"


def _tablespace_absent_after(
    case: DropTablespaceFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target tablespace is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if not _tablespace_created(case, a):
        return True
    if case.outcome == "success":
        return True
    return False


def _probe_select(
    case: DropTablespaceFactorCase, a: dict[str, str], p: str
) -> str:
    name = _tablespace_probe(case, a, p)
    absent = _tablespace_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "tablespace_absent" if absent else "tablespace_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        f"FROM pg_catalog.pg_tablespace WHERE spcname = '{name}' "
        "ORDER BY count(*) LIMIT 1;"
    )


def _role_names(
    case: DropTablespaceFactorCase, p: str, effective: str
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}actor":
        roles.append(f"{p}actor")
    return tuple(roles)


def _resolve_case(case: DropTablespaceFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    created = _tablespace_created(case, a)
    ts_ref = _tablespace_ref(case, a, p)
    effective = _effective_role(case, a, p)
    is_txn = _is_transaction_block(case, a)

    setup: list[str] = []
    locus = "target.tablespace"

    # --- setup boundary SELECT (separates \set from the first CREATE) ---
    setup.append("SELECT 1 AS setup_boundary;")

    # --- role fixtures (CREATE only; SET ROLE deferred to after the
    # tablespace fixture so they run as the superuser) ---
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- the tablespace fixture (as superuser, before SET ROLE) ---
    if created:
        setup.append(
            f"CREATE TABLESPACE {ts_ref} LOCATION '/tmp/{p}tsloc';"
        )
        if locus == "target.tablespace":
            locus = "fixture.tablespace"
    elif not created:
        setup.append(
            "SELECT 1 AS target_tablespace_intentionally_absent;"
        )
        locus = "fixture.object_state"

    # --- arm the non-superuser role (AFTER tablespace creation) ---
    if effective:
        setup.append(f"SET ROLE {p}actor;")

    # --- transaction wrapper around the target (RISK or txn-block) ---
    if case.kind == "RISK":
        setup.append("BEGIN;")
        locus = "target.transaction_boundary"
    elif is_txn:
        setup.append("BEGIN;")
        locus = "target.transaction_boundary"

    if_exists = "IF EXISTS " if _if_exists_present(case, a) else ""
    target = f"DROP TABLESPACE {if_exists}{ts_ref};"

    # --- oracle / SQLSTATE assertion ------------------------------------
    assert_lines: list[str] = []
    if case.kind == "RISK":
        assert_lines.append(
            "COMMIT;" if case.factor_value == "commit" else "ROLLBACK;"
        )
    elif is_txn:
        assert_lines.append("ROLLBACK;")
    if effective:
        assert_lines.append("RESET ROLE;")
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    assert_lines.append(_probe_select(case, a, p))

    # --- cleanup construction -------------------------------------------
    roles = _role_names(case, p, effective)
    role_drops = [
        statement
        for role in roles
        for statement in (
            f"DROP OWNED BY {role};",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]
    ts_drop = f"DROP TABLESPACE IF EXISTS {ts_ref};"

    # Pre-cleanup: drop residual objects from a prior run.
    pre_cleanup: list[str] = []
    pre_cleanup.append(ts_drop)
    pre_cleanup.extend(role_drops)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # Cleanup: RESET ROLE, then tablespace + role drops.
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.append(ts_drop)
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


def resolve_drop_tablespace_factor_witness(
    case: DropTablespaceFactorCase | DropTablespaceFactorExtensionCase,
    repository_root: Path,
) -> DropTablespaceFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropTablespaceFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_tablespace(sql: str) -> int:
    """Count the single credited DROP TABLESPACE inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*DROP\s+TABLESPACE\b", region)
    )


def _header(case: DropTablespaceFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP TABLESPACE {case.factor_key}={case.factor_value}",
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


def render_drop_tablespace_factor_case(
    case: DropTablespaceFactorCase | DropTablespaceFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP TABLESPACE regress program."""

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地表空间和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP TABLESPACE。")
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


def generate_drop_tablespace_factor_programs(
    baseline_plan: DropTablespaceFactorLoopPlan,
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
    case: DropTablespaceFactorCase | DropTablespaceFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_tablespace_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropTablespaceFactorRenderError",
    "DropTablespaceFactorWitness",
    "count_primary_drop_tablespace",
    "generate_drop_tablespace_factor_programs",
    "render_drop_tablespace_factor_case",
    "resolve_drop_tablespace_factor_witness",
]
