"""Render complete PostgreSQL 18.4 ALTER SEQUENCE factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.
The file is assembled from a single :func:`_resolve_case` plan so that the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .alter_sequence_factor_extension import (
    AlterSequenceFactorExtensionCase,
)
from .alter_sequence_factor_loop import (
    AlterSequenceFactorCase,
    AlterSequenceFactorLoopPlan,
)


_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/sequence/"
    "alter_sequence.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/sequence/"
    "alter_sequence.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_ALTER_PARAMETERS = "branch_alter_parameters"
_BRANCH_SET_LOGGED_UNLOGGED = "branch_set_logged_unlogged"
_BRANCH_OWNER = "branch_owner"
_BRANCH_RENAME = "branch_rename"
_BRANCH_SET_SCHEMA = "branch_set_schema"


def _synthetic_case(
    ext: AlterSequenceFactorExtensionCase,
) -> AlterSequenceFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .alter_sequence_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    branch = assignment["grammar_branch"]
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    elif branch == _BRANCH_RENAME and ext.outcome == "success":
        factor_key = "sequence_name_shape"
        factor_value = assignment["sequence_name_shape"]
    else:
        factor_key = "object_state"
        factor_value = assignment.get("object_state", "exists")
    return AlterSequenceFactorCase(
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
        execution_profile="serial_sql",
    )


def _as_render_case(
    case: AlterSequenceFactorCase | AlterSequenceFactorExtensionCase,
) -> AlterSequenceFactorCase:
    if isinstance(case, AlterSequenceFactorExtensionCase):
        return _synthetic_case(case)
    return case


class AlterSequenceFactorRenderError(ValueError):
    """Raised when an ALTER SEQUENCE case cannot be rendered."""


@dataclass(frozen=True)
class AlterSequenceFactorWitness:
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


@dataclass(frozen=True)
class _FixtureState:
    needs_sequence: bool
    needs_table: bool
    needs_schema: bool
    needs_diff_schema: bool
    needs_role: bool
    needs_new_owner_role: bool
    needs_temp: bool
    effective: str
    sequence_name: str
    table_name: str
    schema_name: str
    diff_schema_name: str
    should_create_schema: bool
    is_session_user_escape: bool


def _baseline(case: AlterSequenceFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _sequence_name(a: dict[str, str], p: str) -> str:
    """Sequence name in the target ALTER (and fixture CREATE)."""

    shape = a.get("sequence_name_shape", "simple")
    if shape == "quoted":
        return f'"{p}Mixed Seq"'
    if shape == "reserved_word":
        return f'"{p}user"'
    if shape == "schema_qualified":
        return f"{p}sch.{p}seq"
    return f"{p}seq"


def _probe_name(
    case: AlterSequenceFactorCase, a: dict[str, str], p: str
) -> str:
    """Name to probe in verification (new name for RENAME success)."""

    return _sequence_name(a, p).strip('"')


def _new_owner_target(a: dict[str, str], p: str) -> str:
    """OWNER TO target role expression."""

    spec = a.get("role_specification", "new_owner_role")
    if spec == "CURRENT_ROLE":
        return "CURRENT_ROLE"
    if spec == "CURRENT_USER":
        return "CURRENT_USER"
    if spec == "SESSION_USER":
        return "SESSION_USER"
    # explicit role name
    if a.get("new_owner_shape") == "non_existing_role":
        return f"{p}no_such_role"
    return f"{p}new_owner"


def _new_schema_name(a: dict[str, str], p: str) -> str:
    """SET SCHEMA target schema name."""

    if a.get("new_schema_name") == "non_existing_schema":
        return f"{p}no_such_sch"
    return f"{p}new_sch"


def _parameter_clause(a: dict[str, str], p: str) -> str:
    """Render the parameter clause for branch_alter_parameters."""

    param = a.get("alter_parameter_type", "none_parameter")
    if param == "change_data_type":
        return f"AS {a.get('new_data_type', 'smallint')}"
    if param == "change_increment":
        by = " BY" if a.get("increment_by_keyword") == "present" else ""
        return f"INCREMENT{by} 5"
    if param == "change_minmax":
        return "MINVALUE 1 MAXVALUE 10000"
    if param == "change_start":
        with_kw = " WITH" if a.get("start_with_keyword") == "present" else ""
        return f"START{with_kw} 1"
    if param == "restart_with":
        with_kw = " WITH" if a.get("restart_with_keyword") == "present" else ""
        if with_kw:
            return f"RESTART{with_kw} 1"
        return "RESTART"
    if param == "change_cache":
        return "CACHE 5"
    if param == "change_cycle":
        no = "NO " if a.get("cycle_no_keyword") == "present" else ""
        return f"{no}CYCLE"
    if param == "change_owned_by":
        dep = a.get("owned_by_table_dependency", "same_owner_same_schema")
        if dep == "different_schema":
            return f"OWNED BY {_diff_schema_name(a, p)}.{p}owned_tbl.col"
        return f"OWNED BY {p}owned_tbl.col"
    if param == "none_parameter":
        return ""
    raise AlterSequenceFactorRenderError(f"unknown parameter: {param}")


def _diff_schema_name(a: dict[str, str], p: str) -> str:
    return f"{p}diff_sch"


def _is_non_existent(case: AlterSequenceFactorCase, a: dict[str, str]) -> bool:
    """Whether the target sequence does not exist (failure or notice)."""

    if case.kind != "EXT" and a.get("expected_status") == "failure":
        ne = a.get("non_existent_sequence")
        return ne == "target_not_exists_no_if_exists"
    if a.get("object_state") == "not_exists":
        return True
    return False


def _is_notice_noop(case: AlterSequenceFactorCase, a: dict[str, str]) -> bool:
    """IF EXISTS on a non-existent target → NOTICE (00000, no-op success)."""

    return a.get("non_existent_sequence") == "target_not_exists_with_if_exists"


def _privilege_denied(
    case: AlterSequenceFactorCase, a: dict[str, str]
) -> bool:
    if case.kind != "EXT" and a.get("expected_status") == "failure":
        return False
    if a.get("privilege_level") == "non_owner":
        return True
    return False


def _is_sequence_owner(a: dict[str, str]) -> bool:
    return a.get("privilege_level") == "sequence_owner"


def _effective_role(
    case: AlterSequenceFactorCase, a: dict[str, str], p: str
) -> str:
    if _privilege_denied(case, a):
        return f"{p}actor"
    if _is_sequence_owner(a):
        return f"{p}owner"
    return ""


def _needs_table(a: dict[str, str]) -> bool:
    return (
        a.get("grammar_branch") == _BRANCH_ALTER_PARAMETERS
        and a.get("alter_parameter_type") == "change_owned_by"
    )


def _needs_schema(a: dict[str, str]) -> bool:
    return a.get("grammar_branch") == _BRANCH_SET_SCHEMA


def _needs_diff_schema(a: dict[str, str]) -> bool:
    return (
        a.get("grammar_branch") == _BRANCH_ALTER_PARAMETERS
        and a.get("alter_parameter_type") == "change_owned_by"
        and a.get("owned_by_table_dependency") == "different_schema"
    )


def _needs_temp(a: dict[str, str]) -> bool:
    return a.get("grammar_branch") == _BRANCH_SET_LOGGED_UNLOGGED


def _needs_new_owner_role(a: dict[str, str], p: str) -> bool:
    """Whether to CREATE ROLE for the OWNER TO explicit target."""

    if a.get("grammar_branch") != _BRANCH_OWNER:
        return False
    target = _new_owner_target(a, p)
    return target not in {"CURRENT_ROLE", "CURRENT_USER", "SESSION_USER"} and target != f"{p}no_such_role"


def _compute_state(
    case: AlterSequenceFactorCase,
) -> _FixtureState:
    a = _baseline(case)
    p = case.object_prefix
    branch = a["grammar_branch"]
    non_existent = _is_non_existent(case, a)
    notice = _is_notice_noop(case, a)
    effective = _effective_role(case, a, p)
    is_escape = (
        branch == _BRANCH_OWNER
        and a.get("role_specification") == "SESSION_USER"
        and effective == f"{p}actor"
    )
    return _FixtureState(
        needs_sequence=not non_existent and not notice,
        needs_table=_needs_table(a),
        needs_schema=_needs_schema(a),
        needs_diff_schema=_needs_diff_schema(a),
        needs_role=bool(effective),
        needs_new_owner_role=_needs_new_owner_role(a, p),
        needs_temp=_needs_temp(a),
        effective=effective,
        sequence_name=_sequence_name(a, p),
        table_name=f"{p}owned_tbl",
        schema_name=_new_schema_name(a, p),
        diff_schema_name=_diff_schema_name(a, p),
        should_create_schema=(
            _needs_schema(a)
            and a.get("new_schema_name") != "non_existing_schema"
        ),
        is_session_user_escape=is_escape,
    )


def _probe_select(
    case: AlterSequenceFactorCase, a: dict[str, str], p: str
) -> tuple[str, ...]:
    mode = a.get("verification_mode", "pg_class_catalog_query")
    if case.factor_key == "verification_mode":
        mode = case.factor_value
    name = _probe_name(case, a, p)
    if mode == "sequence_inspection_query":
        return (
            "SELECT s.seqtypid::regtype AS seqtype, s.seqstart, "
            "s.seqincrement, s.seqmin, s.seqmax, s.seqcache, s.seqcycle "
            "FROM pg_catalog.pg_sequence AS s "
            "JOIN pg_catalog.pg_class AS c ON s.seqrelid = c.oid "
            f"WHERE c.relname = '{name}' AND c.relkind = 'S' "
            "ORDER BY s.seqtypid;",
        )
    if mode == "nextval_call":
        return (f"SELECT nextval('{name}') AS nextval_verified;",)
    if mode == "currval_call":
        return (
            f"SELECT nextval('{name}') AS nextval_prerequisite;",
            f"SELECT currval('{name}') AS currval_verified;",
        )
    return (
        f"SELECT count(*) AS seq_exists FROM pg_catalog.pg_class "
        f"WHERE relname = '{name}' AND relkind = 'S';",
    )


def _build_setup(
    case: AlterSequenceFactorCase,
    st: _FixtureState,
) -> tuple[list[str], str]:
    a = _baseline(case)
    p = case.object_prefix
    branch = a["grammar_branch"]
    setup: list[str] = []
    locus = "target.sequence"
    # Schema fixtures (for SET SCHEMA or different-schema OWNED BY).
    if st.should_create_schema:
        setup.append(f"CREATE SCHEMA IF NOT EXISTS {st.schema_name};")
    if st.needs_diff_schema:
        setup.append(f"CREATE SCHEMA IF NOT EXISTS {st.diff_schema_name};")
    if a.get("sequence_name_shape") == "schema_qualified":
        setup.append(f"CREATE SCHEMA IF NOT EXISTS {p}sch;")
    # Role fixtures.
    if st.needs_new_owner_role:
        setup.append(f"CREATE ROLE {p}new_owner LOGIN;")
    effective = st.effective
    if effective:
        setup.append(f"CREATE ROLE {p}owner LOGIN;")
        if _privilege_denied(case, a):
            setup.append(f"CREATE ROLE {p}actor LOGIN;")
        setup.append(f"GRANT USAGE ON SCHEMA public TO {p}owner;")
        if _privilege_denied(case, a):
            setup.append(f"GRANT USAGE ON SCHEMA public TO {p}actor;")
        locus = "fixture.privilege_state"
    # Target sequence fixture.
    if st.needs_sequence:
        seq_type = a.get("new_data_type", "bigint")
        if branch == _BRANCH_ALTER_PARAMETERS:
            param = a.get("alter_parameter_type")
            if param == "change_data_type":
                # Pre-create with a different type so the AS change is
                # observable; use bigint as the starting type.
                setup.append(
                    f"CREATE SEQUENCE {st.sequence_name} AS bigint "
                    f"START WITH 1;"
                )
            elif param == "change_owned_by":
                setup.append(
                    f"CREATE SEQUENCE {st.sequence_name} AS bigint "
                    f"START WITH 1;"
                )
            else:
                setup.append(
                    f"CREATE SEQUENCE {st.sequence_name} AS bigint "
                    f"START WITH 1 INCREMENT BY 1;"
                )
        elif st.needs_temp:
            setup.append(f"CREATE TEMP SEQUENCE {st.sequence_name};")
        else:
            setup.append(
                f"CREATE SEQUENCE {st.sequence_name} AS bigint "
                f"START WITH 1;"
            )
    # Table fixture for OWNED BY.
    if st.needs_table:
        if st.needs_diff_schema:
            setup.append(
                f"CREATE TABLE {st.diff_schema_name}.{st.table_name} "
                f"(col integer);"
            )
        else:
            setup.append(
                f"CREATE TABLE {st.table_name} (col integer);"
            )
    # Transfer ownership of fixture objects to the owner role.
    if _is_sequence_owner(a):
        if st.needs_sequence:
            setup.append(
                f"ALTER SEQUENCE {st.sequence_name} "
                f"OWNER TO {p}owner;"
            )
        if st.needs_table:
            tbl = (
                f"{st.diff_schema_name}.{st.table_name}"
                if st.needs_diff_schema
                else st.table_name
            )
            setup.append(f"ALTER TABLE {tbl} OWNER TO {p}owner;")
    # SET ROLE to the effective role.
    if effective and not st.is_session_user_escape:
        setup.append(f"SET ROLE {effective};")
    elif effective and st.is_session_user_escape:
        # For non_owner + SESSION_USER: the no-op escape only works when
        # SESSION_USER IS the current owner.  The sequence was created by
        # pgcf_superuser (= SESSION_USER), so DO NOT transfer it; the
        # actor's OWNER TO SESSION_USER is then a no-op (00000).
        setup.append(f"SET ROLE {effective};")
    if case.kind == "RISK":
        setup.append("BEGIN;")
        locus = "target.transaction_boundary"
    if not setup:
        setup.append("SELECT 1 AS no_fixture_required;")
    return setup, locus


def _if_exists_clause(a: dict[str, str]) -> str:
    if a.get("if_exists_clause") == "present":
        return "IF EXISTS "
    return ""


def _build_target(
    case: AlterSequenceFactorCase,
    st: _FixtureState,
) -> str:
    a = _baseline(case)
    p = case.object_prefix
    branch = a["grammar_branch"]
    ref = _sequence_name(a, p)
    ie = _if_exists_clause(a)
    if branch == _BRANCH_ALTER_PARAMETERS:
        clause = _parameter_clause(a, p)
        if clause:
            return f"ALTER SEQUENCE {ie}{ref} {clause};"
        return f"ALTER SEQUENCE {ie}{ref};"
    if branch == _BRANCH_SET_LOGGED_UNLOGGED:
        lu = a.get("logged_unlogged_clause", "LOGGED")
        return f"ALTER SEQUENCE {ie}{ref} SET {lu};"
    if branch == _BRANCH_OWNER:
        return f"ALTER SEQUENCE {ie}{ref} OWNER TO {_new_owner_target(a, p)};"
    if branch == _BRANCH_RENAME:
        return f"ALTER SEQUENCE {ie}{ref} RENAME TO {p}renamed_seq;"
    if branch == _BRANCH_SET_SCHEMA:
        return f"ALTER SEQUENCE {ie}{ref} SET SCHEMA {_new_schema_name(a, p)};"
    raise AlterSequenceFactorRenderError(f"unknown branch {branch}")


def _build_assert(
    case: AlterSequenceFactorCase,
) -> tuple[str, ...]:
    a = _baseline(case)
    p = case.object_prefix
    lines: list[str] = []
    if case.kind == "RISK":
        lines.append(
            "COMMIT;" if case.factor_value == "commit"
            else "ROLLBACK;"
        )
    lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    lines.extend(_probe_select(case, a, p))
    return tuple(lines)


def _tables_to_drop(
    case: AlterSequenceFactorCase, st: _FixtureState
) -> list[str]:
    p = case.object_prefix
    tables: list[str] = []
    if st.needs_table:
        if st.needs_diff_schema:
            tables.append(f"{st.diff_schema_name}.{st.table_name}")
        else:
            tables.append(st.table_name)
    return tables


def _sequences_to_drop(
    case: AlterSequenceFactorCase, st: _FixtureState
) -> list[str]:
    names: list[str] = []
    if st.needs_sequence:
        names.append(st.sequence_name)
    if case.kind == "RISK":
        names.append(st.sequence_name)
    return names


def _roles_to_drop(
    case: AlterSequenceFactorCase, a: dict[str, str], p: str
) -> list[str]:
    roles: list[str] = []
    if _effective_role(case, a, p):
        roles.append(f"{p}owner")
        if _privilege_denied(case, a):
            roles.append(f"{p}actor")
    if st_needs_new_owner(a, p):
        roles.append(f"{p}new_owner")
    return roles


def st_needs_new_owner(a: dict[str, str], p: str) -> bool:
    return _needs_new_owner_role(a, p)


def _schemas_to_drop(
    case: AlterSequenceFactorCase, st: _FixtureState
) -> list[str]:
    schemas: list[str] = []
    if st.should_create_schema:
        schemas.append(st.schema_name)
    if st.needs_diff_schema:
        schemas.append(st.diff_schema_name)
    if _baseline(case).get("sequence_name_shape") == "schema_qualified":
        schemas.append(f"{case.object_prefix}sch")
    return schemas


def _build_pre_cleanup(
    case: AlterSequenceFactorCase, st: _FixtureState
) -> tuple[str, ...]:
    a = _baseline(case)
    p = case.object_prefix
    tables = _tables_to_drop(case, st)
    seqs = _sequences_to_drop(case, st)
    schemas = _schemas_to_drop(case, st)
    lines: list[str] = []
    if tables:
        lines.append(f"DROP TABLE IF EXISTS {', '.join(tables)} CASCADE;")
    lines.extend(f"DROP SEQUENCE IF EXISTS {n} CASCADE;" for n in seqs)
    for s in schemas:
        lines.append(f"DROP SCHEMA IF EXISTS {s} CASCADE;")
    for role in _roles_to_drop(case, a, p):
        lines.append(f"DROP ROLE IF EXISTS {role};")
    if not lines:
        lines.append("SELECT 1 AS residual_check_no_objects;")
    return tuple(lines)


def _build_cleanup(
    case: AlterSequenceFactorCase, st: _FixtureState
) -> tuple[str, ...]:
    a = _baseline(case)
    p = case.object_prefix
    tables = _tables_to_drop(case, st)
    seqs = _sequences_to_drop(case, st)
    schemas = _schemas_to_drop(case, st)
    lines: list[str] = []
    if st.effective:
        lines.append("RESET ROLE;")
    lines.extend(f"DROP SEQUENCE IF EXISTS {n} CASCADE;" for n in seqs)
    for s in schemas:
        lines.append(f"DROP SCHEMA IF EXISTS {s} CASCADE;")
    for role in _roles_to_drop(case, a, p):
        lines.append(f"DROP OWNED BY {role};")
        lines.append(f"DROP ROLE IF EXISTS {role};")
    if tables:
        lines.append(f"DROP TABLE IF EXISTS {', '.join(tables)} CASCADE;")
    if not lines:
        lines.append("SELECT 1 AS residual_check_no_objects;")
    return tuple(lines)


def _resolve_case(
    case: AlterSequenceFactorCase,
) -> _CasePlan:
    st = _compute_state(case)
    setup, locus = _build_setup(case, st)
    target = _build_target(case, st)
    assert_lines = _build_assert(case)
    pre_cleanup = _build_pre_cleanup(case, st)
    cleanup = _build_cleanup(case, st)
    on_error_off = case.outcome == "expected_failure"
    return _CasePlan(
        target_fragment=target,
        setup_lines=tuple(setup),
        assert_lines=assert_lines,
        pre_cleanup_lines=pre_cleanup,
        cleanup_lines=cleanup,
        on_error_off=on_error_off,
        semantic_locus=locus,
    )


def resolve_alter_sequence_factor_witness(
    case: AlterSequenceFactorCase | AlterSequenceFactorExtensionCase,
    repository_root: Path,
) -> AlterSequenceFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return AlterSequenceFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_alter_sequence(sql: str) -> int:
    """Count the single credited ALTER SEQUENCE inside the fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(re.findall(r"(?im)^\s*ALTER\s+SEQUENCE\b", region))


def _header(case: AlterSequenceFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : ALTER SEQUENCE "
        f"{case.factor_key}={case.factor_value}",
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


def render_alter_sequence_factor_case(
    case: AlterSequenceFactorCase | AlterSequenceFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic ALTER SEQUENCE regress program."""

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
    lines.append("-- 3. 执行唯一获得覆盖信用的 ALTER SEQUENCE。")
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


def generate_alter_sequence_factor_programs(
    baseline_plan: AlterSequenceFactorLoopPlan,
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
    case: AlterSequenceFactorCase | AlterSequenceFactorExtensionCase,
    out: Path,
) -> None:
    text = render_alter_sequence_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "AlterSequenceFactorRenderError",
    "AlterSequenceFactorWitness",
    "count_primary_alter_sequence",
    "generate_alter_sequence_factor_programs",
    "render_alter_sequence_factor_case",
    "resolve_alter_sequence_factor_witness",
]
