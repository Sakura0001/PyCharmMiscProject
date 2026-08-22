"""Render complete PostgreSQL 18.4 DROP SEQUENCE factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_class
WHERE relname = '<name>' AND relkind = 'S' ORDER BY count(*) LIMIT 1``
queries the real ``pg_class`` catalog (relname + relkind columns).
``pg_sequence`` has no name column — it is never probed here.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .cleanup_bookend import DropSpec, build_cleanup, build_pre_cleanup
from .drop_sequence_factor_extension import (
    DropSequenceFactorExtensionCase,
)
from .drop_sequence_factor_loop import (
    DropSequenceFactorCase,
    DropSequenceFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/sequence/"
    "drop_sequence.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/sequence/"
    "drop_sequence.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

# Primary (factor, value) pairs where the target sequence is intentionally
# absent, so the drop surfaces a not-found error (or a notice under IF EXISTS)
# and the oracle asserts absence.
_ABSENT_PRIMARIES = frozenset(
    {
        ("object_state", "not_exists"),
        ("sequence_name_shape", "non_existent"),
        ("expected_status", "failure"),
    }
)

# Baseline primaries that imply a dependent object fixture must be created.
_DEPENDENCY_PRIMARIES = frozenset(
    {
        ("dependency_state", "used_by_identity_column"),
        ("dependency_state", "used_by_serial_column"),
        ("dependency_state", "owned_by_table_column"),
        ("dependency_state", "used_by_default_expression"),
    }
)

# For an extension SUCCESS case (no present failure pair) the synthetic
# primary must be a neutral success primary whose helpers fall through to the
# assignment; the sequence always exists in extensions (object_state held at
# exists_permanent unless crossed to not_exists).
_BRANCH_NEUTRAL_SUCCESS = ("object_state", "exists_permanent")


def _synthetic_case(
    ext: DropSequenceFactorExtensionCase,
) -> DropSequenceFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .drop_sequence_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropSequenceFactorCase(
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
    case: DropSequenceFactorCase | DropSequenceFactorExtensionCase,
) -> DropSequenceFactorCase:
    if isinstance(case, DropSequenceFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropSequenceFactorRenderError(ValueError):
    """Raised when a DROP SEQUENCE case cannot be rendered."""


@dataclass(frozen=True)
class DropSequenceFactorWitness:
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


def _baseline(case: DropSequenceFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _seq_name(case: DropSequenceFactorCase, a: dict[str, str], p: str) -> str:
    """The sequence name as referenced inside DROP SEQUENCE (shaped)."""

    shape = a.get("sequence_name_shape", "simple")
    if shape == "quoted":
        return f'"{p}QuotedSeq"'
    if shape == "schema_qualified":
        return f"public.{p}seq"
    if shape == "reserved_word":
        return f'"{p}user"'
    if shape == "non_existent":
        return f"{p}nonexistent"
    return f"{p}seq"


def _probe_name(case: DropSequenceFactorCase, a: dict[str, str], p: str) -> str:
    """The bare sequence name (no quotes/schema) for the pg_class probe."""

    shape = a.get("sequence_name_shape", "simple")
    if shape == "quoted":
        return f"{p}QuotedSeq"
    if shape == "schema_qualified":
        return f"{p}seq"
    if shape == "reserved_word":
        return f"{p}user"
    if shape == "non_existent":
        return f"{p}nonexistent"
    return f"{p}seq"


def _seq2_name(p: str) -> str:
    return f"{p}seq2"


def _sequence_definition(a: dict[str, str]) -> str:
    """Derive the CREATE SEQUENCE type keyword from object_state/permanence."""

    obj_state = a.get("object_state", "exists_permanent")
    perm = a.get("sequence_type_permanence", "permanent")
    if obj_state == "exists_temporary" or perm == "temporary":
        return "TEMP"
    if obj_state == "exists_unlogged" or perm == "unlogged":
        return "UNLOGGED"
    return ""


def _fixture_kind(
    case: DropSequenceFactorCase, a: dict[str, str]
) -> str:
    """Whether a sequence fixture must be created."""

    if case.kind == "RISK":
        return "sequence"
    if (case.factor_key, case.factor_value) in _ABSENT_PRIMARIES:
        return "none"
    if case.kind == "EXT":
        if a.get("object_state") == "not_exists":
            return "none"
        if a.get("sequence_name_shape") == "non_existent":
            return "none"
    return "sequence"


def _is_multi(a: dict[str, str]) -> bool:
    return a.get("multi_sequence_drop") == "multi_sequence"


def _if_exists_present(
    case: DropSequenceFactorCase, a: dict[str, str]
) -> bool:
    return a.get("if_exists_clause") == "present"


def _cascade_clause(a: dict[str, str]) -> str:
    cascade = a.get("cascade_restrict", "none")
    if cascade == "cascade":
        return "CASCADE"
    if cascade == "restrict":
        return "RESTRICT"
    return ""


def _effective_role(
    case: DropSequenceFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP SEQUENCE runs."""

    if case.kind == "EXT":
        level = a.get("privilege_level", "owner")
        return f"{p}actor" if level == "non_owner" else ""
    if case.factor_key == "privilege_level":
        return f"{p}actor" if case.factor_value == "non_owner" else ""
    return ""


def _needs_dependent(
    case: DropSequenceFactorCase, a: dict[str, str]
) -> bool:
    """Whether a dependent object fixture must be created."""

    if case.kind == "EXT":
        return a.get("dependency_state") != "no_dependents"
    if (case.factor_key, case.factor_value) in _DEPENDENCY_PRIMARIES:
        return True
    return a.get("dependency_state") != "no_dependents"


def _sequence_absent_after(
    case: DropSequenceFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target sequence is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if _fixture_kind(case, a) == "none":
        return True
    if case.outcome == "success":
        return True
    return False


def _probe_select(
    case: DropSequenceFactorCase, a: dict[str, str], p: str
) -> str:
    name = _probe_name(case, a, p)
    absent = _sequence_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "sequence_absent" if absent else "sequence_present"
    if _is_multi(a):
        seq2 = _seq2_name(p)
        return (
            f"SELECT count(*) {comparator} AS {alias} "
            "FROM pg_catalog.pg_class "
            f"WHERE relname IN ('{name}', '{seq2}') AND relkind = 'S' "
            "ORDER BY count(*) LIMIT 1;"
        )
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_class "
        f"WHERE relname = '{name}' AND relkind = 'S' "
        "ORDER BY count(*) LIMIT 1;"
    )


def _role_names(
    case: DropSequenceFactorCase, p: str, effective: str
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}actor":
        roles.append(f"{p}actor")
    return tuple(roles)


def _dependency_setup(
    dep_type: str, p: str, probe_name: str, seq_ref: str
) -> list[str]:
    """Build the dependent table fixture for a dependency type."""

    setup: list[str] = []
    setup.append(
        f"CREATE TABLE {p}t (c integer DEFAULT nextval('{probe_name}'));"
    )
    if dep_type == "owned_by_table_column":
        setup.append(
            f"ALTER SEQUENCE {seq_ref} OWNED BY {p}t.c;"
        )
    return setup


def _resolve_case(case: DropSequenceFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    fixture_kind = _fixture_kind(case, a)
    seq_ref = _seq_name(case, a, p)
    probe = _probe_name(case, a, p)
    multi = _is_multi(a)
    needs_dep = _needs_dependent(case, a)
    dep_type = a.get("dependency_state", "no_dependents")

    setup: list[str] = []
    locus = "target.sequence"

    # --- role fixtures (CREATE only; SET ROLE deferred to after the
    # sequence fixture so they run as the superuser) ---
    effective = _effective_role(case, a, p)
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- the target sequence fixture (as superuser, before SET ROLE) -------
    seqdef = _sequence_definition(a)
    prefix = f"CREATE {seqdef} SEQUENCE".strip()
    if fixture_kind == "sequence":
        setup.append(f"{prefix} {seq_ref};")
        if multi:
            setup.append(f"{prefix} {_seq2_name(p)};")
    else:
        setup.append(
            "SELECT 1 AS target_sequence_intentionally_absent;"
        )
        locus = "fixture.object_state"

    # --- dependent object fixture (as superuser, before SET ROLE) -------
    if needs_dep:
        setup.extend(_dependency_setup(dep_type, p, probe, seq_ref))
        locus = "fixture.dependency_state"

    # --- arm the non-superuser role (AFTER sequence creation) -----------
    if effective:
        setup.append(f"SET ROLE {p}actor;")
    if_exists = "IF EXISTS " if _if_exists_present(case, a) else ""
    cascade = _cascade_clause(a)
    if multi:
        target = f"DROP SEQUENCE {if_exists}{seq_ref}, {_seq2_name(p)}"
    else:
        target = f"DROP SEQUENCE {if_exists}{seq_ref}"
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
    # Migrated to cleanup_bookend so every DROP carries IF EXISTS (safe on
    # a fresh database and on run-02, where run-01's cleanup already dropped
    # the objects) and DROP OWNED BY is unreachable in pre-cleanup: the
    # {p}actor role is created by setup, so on a fresh database the role
    # does not exist yet at pre-cleanup time and DROP OWNED BY would crash
    # (ON_ERROR_STOP=1) before the target statement reaches execution.
    # Pre-cleanup drops roles via DROP ROLE IF EXISTS only; the post-target
    # cleanup runs DROP OWNED BY then DROP ROLE IF EXISTS once setup has
    # created the role.  The DROP TABLE IF EXISTS anchor is first in
    # pre-cleanup and last in cleanup, satisfying the table-bookend gate.
    roles = _role_names(case, p, effective)
    specs: list[DropSpec] = [DropSpec("SEQUENCE", seq_ref)]
    if multi:
        specs.append(DropSpec("SEQUENCE", _seq2_name(p)))
    table_names = [f"{p}t"] if needs_dep else []
    role_list = list(roles)
    pre_bookend = build_pre_cleanup(
        tables=table_names,
        specs=tuple(specs),
        roles=role_list,
    )
    cln_bookend = build_cleanup(
        tables=table_names,
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


def resolve_drop_sequence_factor_witness(
    case: DropSequenceFactorCase | DropSequenceFactorExtensionCase,
    repository_root: Path,
) -> DropSequenceFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropSequenceFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_sequence(sql: str) -> int:
    """Count the single credited DROP SEQUENCE inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*DROP\s+SEQUENCE\b", region)
    )


def _header(case: DropSequenceFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP SEQUENCE {case.factor_key}={case.factor_value}",
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


def render_drop_sequence_factor_case(
    case: DropSequenceFactorCase | DropSequenceFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP SEQUENCE regress program."""

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地序列和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP SEQUENCE。")
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


def generate_drop_sequence_factor_programs(
    baseline_plan: DropSequenceFactorLoopPlan,
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
    case: DropSequenceFactorCase | DropSequenceFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_sequence_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropSequenceFactorRenderError",
    "DropSequenceFactorWitness",
    "count_primary_drop_sequence",
    "generate_drop_sequence_factor_programs",
    "render_drop_sequence_factor_case",
    "resolve_drop_sequence_factor_witness",
]
