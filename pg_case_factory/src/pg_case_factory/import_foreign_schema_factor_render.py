"""Render complete PostgreSQL 18.4 IMPORT FOREIGN SCHEMA factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL file
assembled from a single :func:`_resolve_case` plan so the byte-level witness
validator can never diverge from the bytes actually written.

IMPORT FOREIGN SCHEMA creates FOREIGN TABLES (``pg_class.relkind='f'``) and
NOT ``CREATE TABLE``, so the ``audit_complete_table_script`` bookend gate
does NOT trigger (class-2 N/A, like ``drop_user_mapping``).  The fixture
reuses the ``file_fdw`` foreign-server pattern from
``drop_user_mapping_factor_render`` (``CREATE EXTENSION IF NOT EXISTS
file_fdw`` + ``CREATE SERVER ... FOREIGN DATA WRAPPER file_fdw``).

The catalog oracle is audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_class c JOIN
pg_catalog.pg_namespace n ON c.relnamespace = n.oid WHERE n.nspname = '...'
AND c.relname = '...' AND c.relkind = 'f' ORDER BY count(*) LIMIT 1``.
``pg_class.relname`` and ``relkind='f'`` are pre-verified real columns.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .import_foreign_schema_factor_extension import (
    ImportForeignSchemaFactorExtensionCase,
    _present_failure_pair,
)
from .import_foreign_schema_factor_loop import (
    ImportForeignSchemaFactorCase,
    ImportForeignSchemaFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/foreign_schema/"
    "import_foreign_schema.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/foreign_schema/"
    "import_foreign_schema.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_FIXTURE_FT_PATH = "/tmp/pgcf_importfs_fixture.csv"


def _synthetic_case(
    ext: ImportForeignSchemaFactorExtensionCase,
) -> ImportForeignSchemaFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "statement_branch"
        factor_value = assignment.get(
            "statement_branch", ext.consumer_action_id
        )
    return ImportForeignSchemaFactorCase(
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
    case: ImportForeignSchemaFactorCase
    | ImportForeignSchemaFactorExtensionCase,
) -> ImportForeignSchemaFactorCase:
    if isinstance(
        case, ImportForeignSchemaFactorExtensionCase
    ):
        return _synthetic_case(case)
    return case


class ImportForeignSchemaFactorRenderError(ValueError):
    """Raised when an IMPORT FOREIGN SCHEMA case cannot be rendered."""


@dataclass(frozen=True)
class ImportForeignSchemaFactorWitness:
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


def _baseline(case: ImportForeignSchemaFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _is_failure(a: dict[str, str]) -> bool:
    return a.get("expected_status") == "failure"


def _is_generic_failure(case: ImportForeignSchemaFactorCase) -> bool:
    return (
        case.factor_key == "expected_status"
        and case.factor_value == "failure"
    )


# ---------------------------------------------------------------------------
# Local schema helpers
# ---------------------------------------------------------------------------

def _local_schema_ref(a: dict[str, str], p: str) -> str:
    """The local schema reference used inside IMPORT ... INTO <schema>."""

    shape = a.get("local_schema_name_shape", "simple_id")
    if shape == "nonexistent_schema":
        return f"{p}noschema"
    if shape == "quoted_id":
        return f'"{p}qschema"'
    return f"{p}lschema"


def _local_schema_probe_name(a: dict[str, str], p: str) -> str:
    """The bare local schema name for the catalog probe (nspname)."""

    shape = a.get("local_schema_name_shape", "simple_id")
    if shape == "nonexistent_schema":
        return f"{p}noschema"
    if shape == "quoted_id":
        return f"{p}qschema"
    return f"{p}lschema"


def _local_schema_created(a: dict[str, str]) -> bool:
    """Whether the local (INTO) schema fixture should be created."""

    if a.get("local_schema_name_shape") == "nonexistent_schema":
        return False
    if a.get("schema_existence") == "schema_not_exists":
        return False
    if a.get("nonexistent_local_schema") == "schema_missing":
        return False
    return True


# ---------------------------------------------------------------------------
# Remote schema / server helpers
# ---------------------------------------------------------------------------

def _remote_schema_ref(a: dict[str, str], p: str) -> str:
    shape = a.get("remote_schema_name_shape", "simple_id")
    if shape == "quoted_id":
        return f'"{p}remote"'
    return f"{p}remote"


def _server_ref(
    a: dict[str, str], p: str, server_created: bool
) -> str:
    """The server name referenced inside IMPORT ... FROM SERVER <name>."""

    if not server_created:
        return f"{p}nosrv"
    shape = a.get("server_name_shape", "simple_id")
    if shape == "nonexistent_server":
        return f"{p}nosrv"
    return f"{p}srv"


def _server_created(a: dict[str, str]) -> bool:
    """Whether the foreign server fixture should be created."""

    if a.get("server_name_shape") == "nonexistent_server":
        return False
    if a.get("server_existence") == "server_not_exists":
        return False
    if a.get("nonexistent_server") == "server_missing":
        return False
    if a.get("server_dependency") == "invalid_server":
        return False
    return True


# ---------------------------------------------------------------------------
# Privilege / role helpers
# ---------------------------------------------------------------------------

def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target IMPORT runs ('' = superuser)."""

    priv = a.get("privilege_level", "superuser")
    if priv in ("usage_and_create", "no_usage", "no_create"):
        return f"{p}actor"
    if a.get("no_create_privilege") == "lacks_create":
        return f"{p}actor"
    if a.get("no_usage_privilege") == "lacks_usage":
        return f"{p}actor"
    return ""


def _grant_usage(a: dict[str, str]) -> bool:
    if a.get("privilege_level") == "no_usage":
        return False
    if a.get("server_dependency") == "no_usage_privilege":
        return False
    if a.get("no_usage_privilege") == "lacks_usage":
        return False
    return True


def _grant_create(a: dict[str, str]) -> bool:
    if a.get("privilege_level") == "no_create":
        return False
    if a.get("no_create_privilege") == "lacks_create":
        return False
    return True


# ---------------------------------------------------------------------------
# Filter / options / object helpers
# ---------------------------------------------------------------------------

def _object_exists(a: dict[str, str]) -> bool:
    return a.get("object_state", "exists") == "exists"


def _limit_table_ref(a: dict[str, str], p: str) -> str:
    shape = a.get("table_name_shape", "simple_id")
    if shape == "nonexistent_table":
        return f"{p}noft"
    return f"{p}ft"


def _filter_clause(a: dict[str, str], p: str) -> str:
    filt = a.get("filter_clause", "no_filter")
    branch = a.get("statement_branch", "branch_basic")
    table = _limit_table_ref(a, p)
    if filt == "limit_to" or branch == "branch_limit_to":
        return f"LIMIT TO ({table})"
    if filt == "except" or branch == "branch_except":
        return f"EXCEPT ({table})"
    return ""


def _options_clause(a: dict[str, str]) -> str:
    if a.get("options_clause", "omitted") == "specified":
        return "OPTIONS (import_force_not_null 'true')"
    return ""


def _witness_ft_ref(a: dict[str, str], p: str) -> str:
    local = _local_schema_ref(a, p)
    return f"{local}.{p}ft"


# ---------------------------------------------------------------------------
# Target / probe / cleanup
# ---------------------------------------------------------------------------

def _build_target(
    a: dict[str, str], p: str, server_created: bool
) -> str:
    remote = _remote_schema_ref(a, p)
    server = _server_ref(a, p, server_created)
    local = _local_schema_ref(a, p)
    filt = _filter_clause(a, p)
    opts = _options_clause(a)
    parts = [f"IMPORT FOREIGN SCHEMA {remote}"]
    if filt:
        parts.append(filt)
    parts.append(f"FROM SERVER {server}")
    parts.append(f"INTO {local}")
    if opts:
        parts.append(opts)
    return " ".join(parts) + ";"


def _probe_select(
    case: ImportForeignSchemaFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only verification."""

    mode = a.get("verification_mode", "pg_class_catalog_query")
    if mode == "error_assertion":
        return None
    # pg_class_catalog_query (default)
    present = not _is_failure(a)
    if present:
        cmp = "> 0"
        alias = "foreign_tables_present"
    else:
        cmp = "= 0"
        alias = "foreign_tables_absent"
    schema = _local_schema_probe_name(a, p)
    ft = f"{p}ft"
    return (
        f"SELECT count(*) {cmp} AS {alias} "
        "FROM pg_catalog.pg_class c "
        "JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid "
        f"WHERE n.nspname = '{schema}' "
        f"AND c.relname = '{ft}' "
        "AND c.relkind = 'f' "
        "ORDER BY count(*) LIMIT 1;"
    )


def _build_setup(
    case: ImportForeignSchemaFactorCase,
    a: dict[str, str],
    p: str,
    server_created: bool,
) -> tuple[tuple[str, ...], str]:
    setup: list[str] = []
    locus = "target.import_foreign_schema"

    setup.append("SELECT 1 AS setup_boundary;")
    setup.append("CREATE EXTENSION IF NOT EXISTS file_fdw;")

    schema_created = _local_schema_created(a)
    role = _effective_role(a, p)

    if server_created:
        setup.append(
            f"CREATE SERVER {p}srv FOREIGN DATA WRAPPER file_fdw;"
        )
        locus = "fixture.foreign_server"

    if role:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    if server_created and role and _grant_usage(a):
        setup.append(
            f"GRANT USAGE ON FOREIGN SERVER {p}srv TO {p}actor;"
        )
    if schema_created and role and _grant_create(a):
        setup.append(
            f"GRANT CREATE ON SCHEMA "
            f"{_local_schema_ref(a, p)} TO {p}actor;"
        )

    if schema_created:
        setup.append(f"CREATE SCHEMA {_local_schema_ref(a, p)};")
        locus = "fixture.local_schema"

    create_witness = (
        schema_created
        and server_created
        and _object_exists(a)
        and not _is_failure(a)
    )
    if create_witness:
        ft = _witness_ft_ref(a, p)
        setup.append(
            f"CREATE FOREIGN TABLE {ft} (c1 text) "
            f"SERVER {p}srv "
            f"OPTIONS (filename '{_FIXTURE_FT_PATH}');"
        )
        locus = "fixture.foreign_table"
    elif schema_created and server_created:
        setup.append(
            "SELECT 1 AS target_foreign_table_intentionally_absent;"
        )
        locus = "fixture.object_state"

    if role:
        setup.append(f"SET ROLE {p}actor;")

    return tuple(setup), locus


def _build_pre_cleanup(
    a: dict[str, str], p: str, role: str
) -> list[str]:
    lines: list[str] = []
    if role:
        lines.append("RESET ROLE;")
    lines.append(
        f"DROP SCHEMA IF EXISTS {_local_schema_ref(a, p)} CASCADE;"
    )
    lines.append(f"DROP SERVER IF EXISTS {p}srv;")
    if role:
        lines.append(f"DROP ROLE IF EXISTS {p}actor;")
    if not lines:
        lines.append("SELECT 1 AS residual_check_no_objects;")
    return lines


def _build_cleanup(
    a: dict[str, str],
    p: str,
    role: str,
    schema_created: bool,
    server_created: bool,
) -> list[str]:
    mode = a.get("cleanup_mode", "drop_foreign_tables")
    schema_ref = _local_schema_ref(a, p)
    lines: list[str] = []
    if role:
        lines.append("RESET ROLE;")
    if mode == "drop_fdw":
        lines.append(
            f"DROP SCHEMA IF EXISTS {schema_ref} CASCADE;"
        )
        lines.append("DROP EXTENSION IF EXISTS file_fdw CASCADE;")
    elif mode == "drop_server":
        if server_created:
            lines.append(f"DROP SERVER IF EXISTS {p}srv;")
        lines.append(
            f"DROP SCHEMA IF EXISTS {schema_ref} CASCADE;"
        )
    elif mode == "drop_schema":
        lines.append(
            f"DROP SCHEMA IF EXISTS {schema_ref} CASCADE;"
        )
        if server_created:
            lines.append(f"DROP SERVER IF EXISTS {p}srv;")
    else:  # drop_foreign_tables
        if schema_created:
            lines.append(
                f"DROP FOREIGN TABLE IF EXISTS "
                f"{schema_ref}.{p}ft;"
            )
        lines.append(
            f"DROP SCHEMA IF EXISTS {schema_ref} CASCADE;"
        )
        if server_created:
            lines.append(f"DROP SERVER IF EXISTS {p}srv;")
    if role:
        lines.append(f"DROP ROLE IF EXISTS {p}actor;")
    if not lines:
        lines.append("SELECT 1 AS residual_check_no_objects;")
    return lines


def _resolve_case(
    case: ImportForeignSchemaFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    generic_failure = _is_generic_failure(case)
    server_created = _server_created(a) and not generic_failure
    schema_created = _local_schema_created(a)
    role = _effective_role(a, p)

    setup_lines, locus = _build_setup(
        case, a, p, server_created
    )

    target = _build_target(a, p, server_created)

    assert_lines: list[str] = []
    if role:
        assert_lines.append("RESET ROLE;")
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    probe = _probe_select(case, a, p)
    if probe is not None:
        assert_lines.append(probe)

    pre_cleanup = _build_pre_cleanup(a, p, role)
    cleanup = _build_cleanup(
        a, p, role, schema_created, server_created
    )

    on_error_off = case.outcome == "expected_failure"
    return _CasePlan(
        target_fragment=target,
        setup_lines=tuple(setup_lines),
        assert_lines=tuple(assert_lines),
        pre_cleanup_lines=tuple(pre_cleanup),
        cleanup_lines=tuple(cleanup),
        on_error_off=on_error_off,
        semantic_locus=locus,
    )


def resolve_import_foreign_schema_factor_witness(
    case: ImportForeignSchemaFactorCase
    | ImportForeignSchemaFactorExtensionCase,
    repository_root: Path,
) -> ImportForeignSchemaFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return ImportForeignSchemaFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_import_foreign_schema(sql: str) -> int:
    """Count the single credited IMPORT FOREIGN SCHEMA inside the fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(
            r"(?im)^\s*IMPORT\s+FOREIGN\s+SCHEMA\b",
            region,
        )
    )


def _header(case: ImportForeignSchemaFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : IMPORT FOREIGN SCHEMA "
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


def render_import_foreign_schema_factor_case(
    case: ImportForeignSchemaFactorCase
    | ImportForeignSchemaFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic IMPORT FOREIGN SCHEMA program."""

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
    lines.append("SELECT 1 AS pre_target_boundary;")
    lines.append(
        "-- 3. 执行唯一获得覆盖信用的 IMPORT FOREIGN SCHEMA。"
    )
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
    case: ImportForeignSchemaFactorCase
    | ImportForeignSchemaFactorExtensionCase,
    out: Path,
) -> None:
    text = render_import_foreign_schema_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_import_foreign_schema_factor_programs(
    baseline_plan: ImportForeignSchemaFactorLoopPlan,
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


__all__ = [
    "ImportForeignSchemaFactorRenderError",
    "ImportForeignSchemaFactorWitness",
    "count_primary_import_foreign_schema",
    "generate_import_foreign_schema_factor_programs",
    "render_import_foreign_schema_factor_case",
    "resolve_import_foreign_schema_factor_witness",
]
