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
    """The name used in the fixture CREATE INDEX.

    Matches ``_index_name`` for quoted/reserved shapes; schema_qualified uses
    a plain name (CREATE INDEX cannot schema-qualify) and the index lands in
    the schema-qualified table's schema.
    """
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
    # RENAME TO takes a bare name (not schema-qualified); the renamed index
    # stays in the same namespace as the original schema-qualified target.
    if shape == "schema_qualified":
        return f"{p}renamed"
    if shape == "reserved_word":
        return f'"{p}from"'
    return f"{p}renamed"


def _tablespace_name(a: dict[str, str], p: str) -> str:
    return f"{p}dst_tbs"


def _qualify(a: dict[str, str], p: str, base: str) -> str:
    """Schema-qualify ``base`` when the name_shape is schema_qualified.

    PostgreSQL places an index in the *table's* schema (``CREATE INDEX
    schema.name`` is a syntax error), so the table itself is created in
    ``src_schema`` and every reference to it (and to its indexes) is
    schema-qualified.
    """
    if a.get("name_shape") == "schema_qualified":
        return f"{p}src_schema.{base}"
    return base


def _method_column(method: str) -> str:
    """The fixture column compatible with the index method."""
    if method == "gist":
        return "pt"
    if method == "gin":
        return "tsv"
    if method == "spgist":
        return "pt"
    return "id"


def _fixture_exists(a: dict[str, str]) -> bool:
    """Whether the target index fixture is created (object_state == exists).

    The fixture index is suppressed when the obligation is calibrated to target
    a non-existent index so the primary target raises ``42P01``: the
    ``object_state == not_exists`` value, the ``name_shape == missing_object``
    obligation, and the ``invalid_combination == nonexistent_index_no_if_exists``
    obligation.  The fixture table is still created (every other action needs a
    table for the catalog-audit oracle) but the index is left absent.
    """
    if a.get("object_state", "exists") != "exists":
        return False
    if a.get("name_shape") == "missing_object":
        return False
    if a.get("invalid_combination") == "nonexistent_index_no_if_exists":
        return False
    return True


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
        val = _storage_param_value(a)
        # Materialize the invalid_combination=system_catalog_index obligation:
        # target a built-in system catalog index (a btree) so PostgreSQL raises
        # 42501 "permission denied: ... is a system catalog" even as superuser.
        if a.get("invalid_combination") == "system_catalog_index":
            return f"ALTER INDEX pg_class_oid_index SET ({param}={val});"
        # Materialize the syntax_error=invalid_syntax obligation: a missing ``=``
        # is a parse-time syntax error (42601), distinct from a value boundary.
        if a.get("syntax_error") == "invalid_syntax":
            return f"ALTER INDEX {iff}{idx} SET ({param} {val});"
        # Materialize the expected_status=failure (negative boundary) obligation:
        # a fillfactor outside the [10,100] range raises 22023.
        if a.get("expected_status") == "failure":
            return f"ALTER INDEX {iff}{idx} SET (fillfactor=0);"
        return f"ALTER INDEX {iff}{idx} SET ({param}={val});"
    if action == "reset_storage":
        param = a.get("storage_parameter", _PARAM_VALUE_BY_METHOD.get(
            a.get("index_method", "btree"), "fillfactor"))
        return f"ALTER INDEX {iff}{idx} RESET ({param});"
    if action == "set_statistics":
        col = a.get("column_number_value", "valid_position")
        col_no = {"valid_position": "1", "out_of_range": "2", "zero": "0"}.get(
            col, "1"
        )
        # Materialize the invalid_combination=statistics_column_out_of_range
        # obligation: the baseline column_number_value is valid_position, but
        # the obligation's attribution (42703) requires an out-of-range column
        # number on the single-expression index, so surface column 2.
        if a.get("invalid_combination") == "statistics_column_out_of_range":
            col_no = "2"
        stat = a.get("statistics_value", "positive_integer")
        stat_val = {
            "positive_integer": "1000",
            "negative_one": "-1",
            "zero": "0",
            # PG18.4: a statistics target below -1 raises 22023 ("statistics
            # target N is too low"); values above 10000 only WARN and clamp,
            # so the out_of_range attribution must use a too-low target.
            "out_of_range": "-2",
        }.get(stat, "1000")
        return f"ALTER INDEX {iff}{idx} ALTER COLUMN {col_no} SET STATISTICS {stat_val};"
    if action == "depends_on_extension":
        return f"ALTER INDEX {iff}{idx} DEPENDS ON EXTENSION plpgsql;"
    if action == "no_depends_on_extension":
        return f"ALTER INDEX {iff}{idx} NO DEPENDS ON EXTENSION plpgsql;"
    if action == "attach_partition":
        # Attach a partition index to the parent partitioned index. The parent
        # index reference is schema-qualified when the name_shape requires it,
        # matching the (schema-qualified) table the index was created on.
        return (
            f"ALTER INDEX {iff}{_qualify(a, p, f'{p}parent_idx')} "
            f"ATTACH PARTITION {idx};"
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
        # Partitioned parent table + partition + matching indexes. When the
        # name_shape is schema_qualified the tables live in src_schema so the
        # plain-named indexes land there and the schema-qualified ATTACH
        # reference resolves.
        parent = _qualify(a, p, f"{p}parent")
        part = _qualify(a, p, f"{p}part")
        setup.append(
            f"CREATE TABLE {parent} (id integer) PARTITION BY RANGE (id);"
        )
        setup.append(
            f"CREATE TABLE {part} PARTITION OF {parent} FOR VALUES FROM (0) TO (1000);"
        )
        setup.append(
            f"CREATE INDEX {p}parent_idx ON {parent} (id);"
        )
        if _fixture_exists(a):
            part_idx = _fixture_index_name(a, p)
            setup.append(
                f"CREATE INDEX {part_idx} ON {part} (id);"
            )
        locus = "fixture.partition_index"
        return setup, locus

    # Standard fixture table carries one column per method family so every
    # method can build a compatible index on the same table.
    table = _qualify(a, p, f"{p}t")
    setup.append(
        f"CREATE TABLE {table} (id integer, tsv tsvector, pt point, rng int4range);"
    )
    if _fixture_exists(a):
        col = _method_column(method)
        fname = _fixture_index_name(a, p)
        # set_statistics can only target *expression* index columns. PostgreSQL
        # strips redundant parens around a bare column reference, so ((col)) is
        # still treated as a plain column; use a genuine expression (id+1).
        key_expr = "(id+1)" if action == "set_statistics" else col
        setup.append(
            f"CREATE INDEX {fname} ON {table} USING {method} ({key_expr});"
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
        if case.outcome == "expected_failure":
            # The rename is calibrated to fail (target index absent), so the
            # renamed index must NOT be visible: emit ``t`` when it is absent.
            lines.append(
                "SELECT count(*) = 0 AS renamed_index_absent "
                f"FROM pg_catalog.pg_class AS c "
                f"JOIN pg_catalog.pg_index AS i ON i.indexrelid = c.oid "
                f"WHERE c.relname = '{new_bare}' ORDER BY count(*) LIMIT 1;"
            )
        else:
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

    # The table-based style contract keys on created TABLE names: the first
    # executable statement (section 1) and the last (section 5) must each be a
    # single ``DROP TABLE IF EXISTS <all created tables>`` so the validator
    # credits every created table in both pre-cleanup and final-cleanup.
    # Tables and indexes are schema-qualified for schema_qualified so the
    # DROPs resolve in src_schema (search_path does not include it).
    if action == "attach_partition":
        created_tables = [_qualify(a, p, f"{p}parent"), _qualify(a, p, f"{p}part")]
        idx_drops = [
            f"DROP INDEX IF EXISTS {_qualify(a, p, f'{p}parent_idx')} CASCADE;",
            f"DROP INDEX IF EXISTS {_index_name(a, p)} CASCADE;",
        ]
    else:
        created_tables = [_qualify(a, p, f"{p}t")]
        # _index_name is schema-qualified for schema_qualified, matching the
        # ALTER INDEX reference; the fixture CREATE used the plain form which
        # landed in the (schema-qualified) table's schema.
        if action == "rename":
            # Rename success: the index now lives under the new name.
            renamed = _qualify(a, p, _new_index_name(a, p))
            idx_drops = [
                f"DROP INDEX IF EXISTS {renamed} CASCADE;",
                f"DROP INDEX IF EXISTS {_index_name(a, p)} CASCADE;",
            ]
        else:
            idx_drops = [f"DROP INDEX IF EXISTS {_index_name(a, p)} CASCADE;"]

    pre_drop = (
        f"DROP TABLE IF EXISTS {', '.join(created_tables)} CASCADE;"
        if created_tables
        else "SELECT 1 AS residual_check_no_objects;"
    )
    final_drop = (
        f"DROP TABLE IF EXISTS {', '.join(reversed(created_tables))} CASCADE;"
        if created_tables
        else "SELECT 1 AS residual_check_no_objects;"
    )

    # Section 1: DROP TABLE (all created tables) leads so it is statement[0];
    # the redundant index/schema/tablespace drops follow (CASCADE already
    # removes dependent indexes, but explicit IF EXISTS keeps re-runs
    # idempotent).
    pre: list[str] = [pre_drop, *idx_drops, *schema_drops, *tbs_drops]
    # Section 5: index/schema/tablespace drops first; DROP TABLE (all created,
    # reverse creation order) is last so it is statement[-1].
    cleanup: list[str] = [*idx_drops, *schema_drops, *tbs_drops, final_drop]
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
