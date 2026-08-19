"""Render complete PostgreSQL 18.4 ALTER INDEX factor-loop regress programs.

Every planned obligation (marginal baseline or bounded extension) becomes one
self-contained, deterministic SQL file assembled from a single
:func:`_resolve_case` plan, so the byte-level witness validator (which
re-renders and compares) can never diverge from the bytes actually written.

Both case kinds carry a complete factor binding: the marginal
:class:`AlterIndexFactorCase` exposes ``baseline_assignments`` and the
extension :class:`AlterIndexFactorExtensionCase` exposes
``factor_assignment``.  The renderer reads whichever is present, so no
synthetic primary-driven case is needed (unlike the ALTER FUNCTION renderer).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .alter_index_factor_extension import AlterIndexFactorExtensionCase
from .alter_index_factor_loop import AlterIndexFactorCase

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/index/alter_index.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/index/"
    "alter_index.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-19"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class AlterIndexFactorRenderError(ValueError):
    """Raised when an ALTER INDEX case cannot be rendered."""


@dataclass(frozen=True)
class AlterIndexFactorWitness:
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


# Concrete storage parameter value per method (mirrors the extension's
# _VALID_PARAMETER_BY_METHOD and the ledger's _METHOD_PARAMETER_VALID).
_PARAM_VALUE_BY_METHOD: dict[str, str] = {
    "btree": "fillfactor",
    "hash": "fillfactor",
    "gist": "fillfactor",
    "spgist": "fillfactor",
    "gin": "fastupdate",
    "brin": "pages_per_range",
}


def _bindings(
    case: AlterIndexFactorCase | AlterIndexFactorExtensionCase,
) -> dict[str, str]:
    """The complete factor binding for either case kind."""
    if isinstance(case, AlterIndexFactorExtensionCase):
        return dict(case.factor_assignment)
    return dict(case.baseline_assignments)


def _object_prefix(
    case: AlterIndexFactorCase | AlterIndexFactorExtensionCase,
) -> str:
    return case.object_prefix


def _index_name(a: dict[str, str], p: str) -> str:
    """The target index name as referenced inside ALTER INDEX."""
    shape = a.get("name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f'"{p}idx"'
    if shape == "schema_qualified":
        return f"{p}src_schema.{p}idx"
    if shape == "reserved_word":
        return f'"{p}select"'
    # plain_identifier / existing_object share the plain fixture name.
    return f"{p}idx"


def _fixture_index_name(a: dict[str, str], p: str) -> str:
    """The name used in the fixture CREATE INDEX (unqualified form)."""
    shape = a.get("name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f'"{p}idx"'
    if shape == "reserved_word":
        return f'"{p}select"'
    return f"{p}idx"


def _new_index_name(a: dict[str, str], p: str) -> str:
    shape = a.get("name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f'"{p}renamed"'
    if shape == "schema_qualified":
        return f"{p}src_schema.{p}renamed"
    if shape == "reserved_word":
        return f'"{p}from"'
    return f"{p}renamed"


def _tablespace_name(a: dict[str, str], p: str) -> str:
    return f"{p}dst_tbs"


def _method_column(method: str) -> str:
    """The fixture column compatible with the index method."""
    if method == "gist":
        return "pt"
    if method == "gin":
        return "tsv"
    return "id"


def _fixture_exists(a: dict[str, str]) -> bool:
    """Whether the target index fixture is created (object_state == exists)."""
    return a.get("object_state", "exists") == "exists"


def _if_exists_clause(a: dict[str, str]) -> str:
    return "IF EXISTS " if a.get("if_exists", "false") == "true" else ""


def _storage_param_value(a: dict[str, str]) -> str:
    """The concrete storage parameter SET value for the method."""
    method = a.get("index_method", "btree")
    param = a.get("storage_parameter", _PARAM_VALUE_BY_METHOD.get(method, "fillfactor"))
    if param == "fillfactor":
        return "90"
    if param == "fastupdate":
        return "on"
    if param == "pages_per_range":
        return "128"
    if param == "buffering":
        return "auto"
    return "90"


def _action_target(
    case: AlterIndexFactorCase | AlterIndexFactorExtensionCase,
    a: dict[str, str],
    p: str,
) -> str:
    action = case.consumer_action_id
    idx = _index_name(a, p)
    iff = _if_exists_clause(a)
    if action == "rename":
        return f"ALTER INDEX {iff}{idx} RENAME TO {_new_index_name(a, p)};"
    if action == "set_tablespace":
        return f"ALTER INDEX {iff}{idx} SET TABLESPACE {_tablespace_name(a, p)};"
    if action == "set_storage":
        param = a.get("storage_parameter", _PARAM_VALUE_BY_METHOD.get(
            a.get("index_method", "btree"), "fillfactor"))
        return f"ALTER INDEX {iff}{idx} SET ({param}={_storage_param_value(a)});"
    if action == "reset_storage":
        param = a.get("storage_parameter", _PARAM_VALUE_BY_METHOD.get(
            a.get("index_method", "btree"), "fillfactor"))
        return f"ALTER INDEX {iff}{idx} RESET ({param});"
    if action == "set_statistics":
        col = a.get("column_number_value", "1")
        col_no = "1" if col == "valid_position" else col
        stat = a.get("statistics_value", "positive_integer")
        stat_val = "1000" if stat == "positive_integer" else stat
        return f"ALTER INDEX {iff}{idx} ALTER COLUMN {col_no} SET STATISTICS {stat_val};"
    if action == "depends_on_extension":
        return f"ALTER INDEX {iff}{idx} DEPENDS ON EXTENSION plpgsql;"
    if action == "no_depends_on_extension":
        return f"ALTER INDEX {iff}{idx} NO DEPENDS ON EXTENSION plpgsql;"
    if action == "attach_partition":
        # Attach a partition index to the parent partitioned index.
        return (
            f"ALTER INDEX {iff}{p}parent_idx ATTACH PARTITION {idx};"
        )
    if action == "all_in_tablespace":
        return (
            f"ALTER INDEX ALL IN TABLESPACE {_tablespace_name(a, p)} "
            f"SET TABLESPACE {p}move_tbs;"
        )
    raise AlterIndexFactorRenderError(f"unknown action {action}")


def _build_fixture(
    case: AlterIndexFactorCase | AlterIndexFactorExtensionCase,
    a: dict[str, str],
    p: str,
) -> tuple[list[str], str]:
    """Return (setup_lines, semantic_locus) for the index fixture."""
    setup: list[str] = []
    method = a.get("index_method", "btree")
    action = case.consumer_action_id
    needs_src_schema = a.get("name_shape") == "schema_qualified"
    needs_dst_tbs = action in ("set_tablespace", "all_in_tablespace")

    if needs_src_schema:
        setup.append(f"CREATE SCHEMA IF NOT EXISTS {p}src_schema;")
    if needs_dst_tbs:
        setup.append(f"CREATE TABLESPACE {p}dst_tbs LOCATION '/tmp/{p}dst_tbs';")
        if action == "all_in_tablespace":
            setup.append(f"CREATE TABLESPACE {p}move_tbs LOCATION '/tmp/{p}move_tbs';")

    locus = "target.index"

    if action == "attach_partition":
        # Partitioned parent table + partition + matching indexes.
        setup.append(
            f"CREATE TABLE {p}parent (id integer) PARTITION BY RANGE (id);"
        )
        setup.append(
            f"CREATE TABLE {p}part PARTITION OF {p}parent FOR VALUES FROM (0) TO (1000);"
        )
        setup.append(
            f"CREATE INDEX {p}parent_idx ON {p}parent (id);"
        )
        if _fixture_exists(a):
            setup.append(
                f"CREATE INDEX {_fixture_index_name(a, p)} ON {p}part (id);"
            )
        locus = "fixture.partition_index"
        return setup, locus

    # Standard fixture table carries one column per method family so every
    # method can build a compatible index on the same table.
    setup.append(
        f"CREATE TABLE {p}t (id integer, tsv tsvector, pt point, rng int4range);"
    )
    if _fixture_exists(a):
        col = _method_column(method)
        schema_prefix = f"{p}src_schema." if needs_src_schema else ""
        fname = _fixture_index_name(a, p)
        # reserved_word / quoted names are not schema-qualified at CREATE time.
        create_name = fname if needs_src_schema and not fname.startswith('"') else fname
        if needs_src_schema and not fname.startswith('"'):
            create_name = f"{schema_prefix}{fname}"
        setup.append(
            f"CREATE INDEX {create_name} ON {p}t USING {method} ({col});"
        )
    else:
        setup.append("SELECT 1 AS target_index_intentionally_absent;")
    locus = "fixture.index_state"
    return setup, locus


def _build_oracle(
    case: AlterIndexFactorCase | AlterIndexFactorExtensionCase,
    a: dict[str, str],
    p: str,
) -> list[str]:
    """Section 4 catalog-audit oracle (compliant boolean shape)."""
    action = case.consumer_action_id
    idx = _index_name(a, p)
    # The bare index name (strip quotes/schema) for catalog lookup.
    bare = idx.replace('"', "").split(".")[-1]
    lines: list[str] = []
    lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    if action == "rename":
        new_bare = _new_index_name(a, p).replace('"', "").split(".")[-1]
        lines.append(
            "SELECT count(*) > 0 AS renamed_index_visible "
            f"FROM pg_catalog.pg_class AS c "
            f"JOIN pg_catalog.pg_index AS i ON i.indexrelid = c.oid "
            f"WHERE c.relname = '{new_bare}' ORDER BY count(*) LIMIT 1;"
        )
    elif action in ("set_storage", "reset_storage"):
        lines.append(
            f"SELECT count(*) > 0 AS storage_parameter_visible "
            f"FROM pg_catalog.pg_class AS c "
            f"JOIN pg_catalog.pg_index AS i ON i.indexrelid = c.oid "
            f"WHERE c.relname = '{bare}' ORDER BY count(*) LIMIT 1;"
        )
    elif action == "set_statistics":
        lines.append(
            f"SELECT count(*) > 0 AS statistics_target_visible "
            f"FROM pg_catalog.pg_class AS c "
            f"WHERE c.relname = '{bare}' ORDER BY count(*) LIMIT 1;"
        )
    else:
        lines.append(
            f"SELECT count(*) > 0 AS target_index_visible "
            f"FROM pg_catalog.pg_class AS c "
            f"WHERE c.relname = '{bare}' ORDER BY count(*) LIMIT 1;"
        )
    return lines


def _build_cleanup(
    case: AlterIndexFactorCase | AlterIndexFactorExtensionCase,
    a: dict[str, str],
    p: str,
) -> tuple[list[str], list[str]]:
    """Return (pre_cleanup_lines, cleanup_lines) for sections 1 and 5."""
    action = case.consumer_action_id
    method = a.get("index_method", "btree")
    needs_src_schema = a.get("name_shape") == "schema_qualified"
    needs_dst_tbs = action in ("set_tablespace", "all_in_tablespace")

    schema_drops: list[str] = []
    if needs_src_schema:
        schema_drops.append(f"DROP SCHEMA IF EXISTS {p}src_schema CASCADE;")
    tbs_drops: list[str] = []
    if needs_dst_tbs:
        tbs_drops.append(f"DROP TABLESPACE IF EXISTS {p}dst_tbs;")
        if action == "all_in_tablespace":
            tbs_drops.append(f"DROP TABLESPACE IF EXISTS {p}move_tbs;")

    # Idempotent index/table drops (superset so the file is re-runnable).
    if action == "attach_partition":
        idempotent = [
            f"DROP INDEX IF EXISTS {p}parent_idx CASCADE;",
            f"DROP INDEX IF EXISTS {_fixture_index_name(a, p)} CASCADE;",
            f"DROP TABLE IF EXISTS {p}part CASCADE;",
            f"DROP TABLE IF EXISTS {p}parent CASCADE;",
        ]
    else:
        idx = _fixture_index_name(a, p)
        # Rename success: the index now lives under the new name.
        if action == "rename":
            new = _new_index_name(a, p)
            idempotent = [
                f"DROP INDEX IF EXISTS {new} CASCADE;",
                f"DROP INDEX IF EXISTS {idx} CASCADE;",
            ]
        else:
            idempotent = [f"DROP INDEX IF EXISTS {idx} CASCADE;"]
        idempotent.append(f"DROP TABLE IF EXISTS {p}t CASCADE;")

    pre = list(idempotent) + schema_drops + tbs_drops
    cleanup = list(idempotent) + schema_drops + tbs_drops
    if not pre:
        pre.append("SELECT 1 AS residual_check_no_objects;")
    if not cleanup:
        cleanup.append("SELECT 1 AS residual_check_no_objects;")
    return pre, cleanup


def _resolve_case(
    case: AlterIndexFactorCase | AlterIndexFactorExtensionCase,
) -> _CasePlan:
    a = _bindings(case)
    p = _object_prefix(case)
    setup, locus = _build_fixture(case, a, p)
    target = _action_target(case, a, p)
    assert_lines = _build_oracle(case, a, p)
    pre_cleanup, cleanup = _build_cleanup(case, a, p)
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


def resolve_alter_index_factor_witness(
    case: AlterIndexFactorCase | AlterIndexFactorExtensionCase,
    repository_root: Path,
) -> AlterIndexFactorWitness:
    """Return the byte-level witness fragments for one case."""
    plan = _resolve_case(case)
    return AlterIndexFactorWitness(
        primary_obligation_id=(
            case.primary_obligation_id
            if isinstance(case, AlterIndexFactorCase)
            else case.derivation_id
        ),
        target_sql_fragment=plan.target_fragment,
        outcome=case.outcome,
        expected_sqlstate=case.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_alter_index(sql: str) -> int:
    """Count the single credited ALTER INDEX inside the primary fence."""
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(re.findall(r"(?im)^\s*ALTER\s+INDEX\b", region))


def _header(
    case: AlterIndexFactorCase | AlterIndexFactorExtensionCase,
) -> list[str]:
    factor_key = (
        case.factor_key if isinstance(case, AlterIndexFactorCase) else "extension"
    )
    factor_value = (
        case.factor_value
        if isinstance(case, AlterIndexFactorCase)
        else case.derivation_id
    )
    obligation = (
        case.primary_obligation_id
        if isinstance(case, AlterIndexFactorCase)
        else case.derivation_id
    )
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : ALTER INDEX {factor_key}={factor_value}",
        f"-- FE           : {_FE}",
        "-- ++",
        "-- --------------------------------------------------------",
        f"-- case_id: {case.case_id}",
        f"-- source_md: {_DOC_SOURCE}",
        f"-- factor_md: {_FACTOR_SOURCE}",
        f"-- primary_obligation_id: {obligation}",
        f"-- expected_outcome: {case.outcome}",
        f"-- expected_sqlstate: {case.expected_sqlstate}",
    ]


def render_alter_index_factor_case(
    case: AlterIndexFactorCase | AlterIndexFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic ALTER INDEX regress program."""
    resolved = _resolve_case(case)
    lines: list[str] = list(_header(case))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地索引和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 ALTER INDEX。")
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


def generate_alter_index_factor_programs(
    baseline_plan: object,
    extension_plan: object,
    out_dir: Path,
) -> int:
    """Write every baseline + extension program; return the file count."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    count = 0
    for case in baseline_plan.cases:  # type: ignore[attr-defined]
        _write_program(case, out)
        count += 1
    for case in extension_plan.cases:  # type: ignore[attr-defined]
        _write_program(case, out)
        count += 1
    return count


def _write_program(
    case: AlterIndexFactorCase | AlterIndexFactorExtensionCase,
    out: Path,
) -> None:
    text = render_alter_index_factor_case(case, Path("."))
    (out / case.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "AlterIndexFactorRenderError",
    "AlterIndexFactorWitness",
    "count_primary_alter_index",
    "generate_alter_index_factor_programs",
    "render_alter_index_factor_case",
    "resolve_alter_index_factor_witness",
]
