"""Render complete PostgreSQL 18.4 CREATE TRANSFORM factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CREATE TRANSFORM is a catalog-row DDL statement: the target is a
``pg_catalog.pg_transform`` catalog row, not a ``pg_class`` relation.
All catalog oracles schema-qualify ``pg_catalog.pg_transform`` (exempt
from the file-prefix style gate via the ``pg_`` prefix).  No case creates
a TABLE, so the bookend (DROP TABLE IF EXISTS) is never emitted.  Every
catalog SELECT carries a top-level ``ORDER BY`` so the
catalog-observability gate passes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_transform_factor_extension import (
    CreateTransformFactorExtensionCase,
    _present_failure_pair,
)
from .create_transform_factor_loop import (
    CreateTransformFactorCase,
    CreateTransformFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/"
    "transform/create_transform.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/"
    "transform/create_transform.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class CreateTransformFactorRenderError(ValueError):
    """Raised when a CREATE TRANSFORM case cannot be rendered."""


@dataclass(frozen=True)
class CreateTransformFactorWitness:
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
    ext: CreateTransformFactorExtensionCase,
) -> CreateTransformFactorCase:
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
    return CreateTransformFactorCase(
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
    case: CreateTransformFactorCase
    | CreateTransformFactorExtensionCase,
) -> CreateTransformFactorCase:
    if isinstance(case, CreateTransformFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateTransformFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _schema_name(p: str) -> str:
    return f"{p}schema"


def _type_name(a: dict[str, str], p: str) -> str:
    """The type identifier in CREATE TRANSFORM."""

    shape = a.get("type_name_shape", "simple_id")
    schema = _schema_name(p)
    if shape == "nonexistent_name":
        return f"{schema}.{p}notype"
    if shape == "quoted_id":
        return f'"{schema}"."{p}Type"'
    return f"{schema}.{p}type"


def _type_name_literal(a: dict[str, str], p: str) -> str:
    """The catalog string literal for oracle queries."""

    shape = a.get("type_name_shape", "simple_id")
    if shape == "quoted_id":
        return f"{p}Type"
    if shape == "nonexistent_name":
        return f"{p}notype"
    return f"{p}type"


def _language_name(a: dict[str, str], p: str) -> str:
    """The language identifier in CREATE TRANSFORM."""

    shape = a.get("language_name_shape", "simple_id")
    if shape == "nonexistent_name":
        return f"{p}nolang"
    return "plpgsql"


def _function_name(a: dict[str, str], p: str, direction: str) -> str:
    """The function name referenced by a transform direction."""

    shape = a.get("function_name_shape", "simple_id")
    schema = _schema_name(p)
    if shape == "nonexistent_name":
        return f"{schema}.{p}nofn"
    return f"{schema}.{p}{direction}sql"


def _is_duplicate(a: dict[str, str]) -> bool:
    return (
        a.get("duplicate_transform") == "existing_transform_without_or_replace"
    )


def _is_type_missing(a: dict[str, str]) -> bool:
    return (
        a.get("type_existence") == "type_not_exists"
        or a.get("type_dependency") == "type_missing"
        or a.get("nonexistent_type") == "type_missing"
        or a.get("type_name_shape") == "nonexistent_name"
    )


def _is_language_missing(a: dict[str, str]) -> bool:
    return (
        a.get("language_existence") == "language_not_exists"
        or a.get("language_dependency") == "language_missing"
        or a.get("nonexistent_language") == "language_missing"
        or a.get("language_name_shape") == "nonexistent_name"
    )


def _is_function_missing(a: dict[str, str]) -> bool:
    return (
        a.get("function_existence") == "some_functions_missing"
        or a.get("nonexistent_function") == "function_missing"
        or a.get("function_name_shape") == "nonexistent_name"
    )


def _is_signature_mismatch(a: dict[str, str]) -> bool:
    return a.get("function_signature_mismatch") == "signature_mismatch"


def _is_type_priv_failure(a: dict[str, str]) -> bool:
    return (
        a.get("privilege_on_type") == "no_usage_privilege"
        or a.get("insufficient_type_privilege") == "lacks_privilege"
    )


def _is_language_priv_failure(a: dict[str, str]) -> bool:
    return (
        a.get("privilege_on_language") == "no_usage"
        or a.get("insufficient_language_privilege") == "lacks_privilege"
    )


def _is_function_priv_failure(a: dict[str, str]) -> bool:
    return (
        a.get("privilege_on_function") == "no_execute_privilege"
        or a.get("insufficient_function_privilege") == "lacks_privilege"
    )


def _is_insufficient_privilege(a: dict[str, str]) -> bool:
    return (
        _is_type_priv_failure(a)
        or _is_language_priv_failure(a)
        or _is_function_priv_failure(a)
    )


def _is_failure(a: dict[str, str]) -> bool:
    return a.get("expected_status") == "failure"


def _has_direction(a: dict[str, str], direction: str) -> bool:
    d = a.get("transform_direction", "both_from_and_to_sql")
    if d == "both_from_and_to_sql":
        return True
    if d == "only_from_sql":
        return direction == "from"
    if d == "only_to_sql":
        return direction == "to"
    return True


def _can_drop_transform(a: dict[str, str]) -> bool:
    return not _is_type_missing(a) and not _is_language_missing(a)


def _effective_role(a: dict[str, str], p: str) -> str:
    if _is_insufficient_privilege(a):
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    if _is_insufficient_privilege(a):
        roles.append(f"{p}actor")
    return tuple(roles)


def _build_type_fixture(
    a: dict[str, str], p: str
) -> list[str]:
    """Setup line for the transform's type."""

    if _is_type_missing(a):
        return []
    schema = _schema_name(p)
    type_name = _type_name(a, p)
    return [f"CREATE TYPE {type_name} AS ENUM ('a');"]


def _build_function_fixtures(
    a: dict[str, str], p: str
) -> list[str]:
    """Setup lines for the support function fixtures."""

    if _is_function_missing(a):
        return []
    schema = _schema_name(p)
    type_name = _type_name(a, p)
    mismatch = _is_signature_mismatch(a)
    lines: list[str] = []
    if _has_direction(a, "from"):
        fn = _function_name(a, p, "from")
        if mismatch:
            lines.append(
                f"CREATE FUNCTION {fn}(internal) "
                f"RETURNS text LANGUAGE internal "
                f"IMMUTABLE STRICT AS 'textlike_support';"
            )
        else:
            lines.append(
                f"CREATE FUNCTION {fn}(internal) "
                f"RETURNS internal LANGUAGE internal "
                f"IMMUTABLE STRICT AS 'textlike_support';"
            )
    if _has_direction(a, "to"):
        fn = _function_name(a, p, "to")
        if mismatch:
            lines.append(
                f"CREATE FUNCTION {fn}(internal) "
                f"RETURNS text LANGUAGE internal "
                f"IMMUTABLE STRICT AS 'textlike_support';"
            )
        elif not _is_type_missing(a):
            lines.append(
                f"CREATE FUNCTION {fn}(internal) "
                f"RETURNS {type_name} LANGUAGE internal "
                f"IMMUTABLE STRICT AS 'textlike_support';"
            )
    return lines


def _build_duplicate_fixture(
    a: dict[str, str], p: str
) -> list[str]:
    """Pre-create the transform for duplicate-signature tests."""

    if not _is_duplicate(a):
        return []
    if _is_type_missing(a) or _is_language_missing(a):
        return []
    schema = _schema_name(p)
    type_name = _type_name(a, p)
    lang_name = _language_name(a, p)
    lines: list[str] = []
    fn_from = _function_name(a, p, "from")
    fn_to = _function_name(a, p, "to")
    if _has_direction(a, "from"):
        lines.append(
            f"CREATE FUNCTION {fn_from}(internal) "
            f"RETURNS internal LANGUAGE internal "
            f"IMMUTABLE STRICT AS 'textlike_support';"
        )
    if _has_direction(a, "to"):
        lines.append(
            f"CREATE FUNCTION {fn_to}(internal) "
            f"RETURNS {type_name} LANGUAGE internal "
            f"IMMUTABLE STRICT AS 'textlike_support';"
        )
    clauses: list[str] = []
    if _has_direction(a, "from"):
        clauses.append(
            f"FROM SQL WITH FUNCTION {fn_from}(internal)"
        )
    if _has_direction(a, "to"):
        clauses.append(
            f"TO SQL WITH FUNCTION {fn_to}(internal)"
        )
    lines.append(
        f"CREATE TRANSFORM FOR {type_name} "
        f"LANGUAGE {lang_name} ({', '.join(clauses)});"
    )
    return lines


def _build_privilege_fixture(
    a: dict[str, str], p: str
) -> list[str]:
    """Setup lines for privilege-insufficient tests."""

    if not _is_insufficient_privilege(a):
        return []
    schema = _schema_name(p)
    type_name = _type_name(a, p)
    lines: list[str] = []
    lines.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
    lines.append(f"GRANT USAGE ON SCHEMA {schema} TO {p}actor;")
    if not _is_type_priv_failure(a) and not _is_type_missing(a):
        lines.append(
            f"GRANT USAGE ON TYPE {type_name} TO {p}actor;"
        )
    if _is_language_priv_failure(a):
        lines.append(
            "REVOKE USAGE ON LANGUAGE plpgsql FROM PUBLIC;"
        )
    if not _is_function_priv_failure(a) and not _is_function_missing(a):
        for direction in ("from", "to"):
            if _has_direction(a, direction):
                fn = _function_name(a, p, direction)
                lines.append(
                    f"GRANT EXECUTE ON FUNCTION "
                    f"{fn}(internal) TO {p}actor;"
                )
    lines.append(f"SET ROLE {p}actor;")
    return lines


def _build_target(
    a: dict[str, str], p: str
) -> str:
    """The primary CREATE TRANSFORM statement."""

    or_replace = ""
    if a.get("or_replace_clause") == "present":
        or_replace = "OR REPLACE "
    type_name = _type_name(a, p)
    lang_name = _language_name(a, p)
    clauses: list[str] = []
    if _has_direction(a, "from"):
        fn = _function_name(a, p, "from")
        clauses.append(f"FROM SQL WITH FUNCTION {fn}(internal)")
    if _has_direction(a, "to"):
        fn = _function_name(a, p, "to")
        clauses.append(f"TO SQL WITH FUNCTION {fn}(internal)")
    return (
        f"CREATE {or_replace}TRANSFORM FOR {type_name} "
        f"LANGUAGE {lang_name} ({', '.join(clauses)});"
    )


def _probe_select(
    case: CreateTransformFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only verification."""

    mode = a.get("verification_mode", "catalog_query_pg_transform")
    if mode == "error_assertion":
        return None

    type_lit = _type_name_literal(a, p)
    lang_name = _language_name(a, p)
    present = not (_is_failure(a) and not _is_duplicate(a))
    cmp_op = ">" if present else "="
    return (
        f"SELECT count(*) {cmp_op} 0 AS transform_state "
        f"FROM pg_catalog.pg_transform "
        f"WHERE trftype = '{type_lit}'::regtype "
        f"AND trflang = (SELECT oid FROM pg_catalog.pg_language "
        f"WHERE lanname = '{lang_name}') "
        f"ORDER BY count(*);"
    )


def _build_cleanup(
    a: dict[str, str], p: str
) -> list[str]:
    """Cleanup lines after the primary target."""

    schema = _schema_name(p)
    type_name = _type_name(a, p)
    lang_name = _language_name(a, p)
    lines: list[str] = []
    if _is_insufficient_privilege(a):
        lines.append("RESET ROLE;")
    if _is_language_priv_failure(a):
        lines.append(
            "GRANT USAGE ON LANGUAGE plpgsql TO PUBLIC;"
        )
    if _can_drop_transform(a):
        lines.append(
            f"DROP TRANSFORM IF EXISTS FOR {type_name} "
            f"LANGUAGE {lang_name} CASCADE;"
        )
    for direction in ("from", "to"):
        if _has_direction(a, direction):
            fn = _function_name(a, p, direction)
            lines.append(
                f"DROP FUNCTION IF EXISTS "
                f"{fn}(internal) CASCADE;"
            )
    if not _is_type_missing(a):
        lines.append(f"DROP TYPE IF EXISTS {type_name} CASCADE;")
    lines.append(f"DROP SCHEMA IF EXISTS {schema} CASCADE;")
    for role in _role_names(a, p):
        lines.append(f"DROP OWNED BY {role} CASCADE;")
        lines.append(f"DROP ROLE IF EXISTS {role};")
    return lines


def _resolve_case(
    case: CreateTransformFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    schema = _schema_name(p)

    setup: list[str] = []
    locus = "target.create_transform"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)

    # --- schema fixture ---
    setup.append(f"CREATE SCHEMA {schema};")
    locus = "fixture.schema"

    # --- type fixture ---
    if not _is_duplicate(a):
        setup.extend(_build_type_fixture(a, p))
        if not _is_type_missing(a):
            locus = "fixture.type"

    # --- support function fixtures ---
    if not _is_duplicate(a):
        setup.extend(_build_function_fixtures(a, p))
        if not _is_function_missing(a):
            locus = "fixture.support_functions"

    # --- duplicate transform fixture ---
    if _is_duplicate(a):
        setup.extend(_build_duplicate_fixture(a, p))
        locus = "fixture.duplicate_transform"

    # --- privilege fixture ---
    if effective:
        setup.extend(_build_privilege_fixture(a, p))
        locus = "fixture.privilege_state"

    # --- the primary target statement ---
    target = _build_target(a, p)

    # --- oracle / SQLSTATE assertion ---
    assert_lines: list[str] = []
    if effective:
        assert_lines.append("RESET ROLE;")
    if _is_language_priv_failure(a):
        assert_lines.append(
            "GRANT USAGE ON LANGUAGE plpgsql TO PUBLIC;"
        )
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    probe = _probe_select(case, a, p)
    if probe is not None:
        assert_lines.append(probe)

    # --- cleanup construction ---
    cleanup = _build_cleanup(a, p)

    # --- pre-cleanup (safe, always IF EXISTS CASCADE) ---
    pre_cleanup: list[str] = []
    type_name = _type_name(a, p)
    lang_name = _language_name(a, p)
    if _can_drop_transform(a):
        pre_cleanup.append(
            f"DROP TRANSFORM IF EXISTS FOR {type_name} "
            f"LANGUAGE {lang_name} CASCADE;"
        )
    for direction in ("from", "to"):
        if _has_direction(a, direction):
            fn = _function_name(a, p, direction)
            pre_cleanup.append(
                f"DROP FUNCTION IF EXISTS "
                f"{fn}(internal) CASCADE;"
            )
    if not _is_type_missing(a):
        pre_cleanup.append(
            f"DROP TYPE IF EXISTS {type_name} CASCADE;"
        )
    pre_cleanup.append(f"DROP SCHEMA IF EXISTS {schema} CASCADE;")
    pre_cleanup.append("RESET ROLE;")
    if _is_language_priv_failure(a):
        pre_cleanup.append(
            "GRANT USAGE ON LANGUAGE plpgsql TO PUBLIC;"
        )
    for role in roles:
        pre_cleanup.append(f"DROP OWNED BY {role} CASCADE;")
        pre_cleanup.append(f"DROP ROLE IF EXISTS {role};")
    if not pre_cleanup:
        pre_cleanup.append(
            "SELECT 1 AS residual_check_no_objects;"
        )

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


def _header(case: CreateTransformFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE TRANSFORM "
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


def render_create_transform_factor_case(
    case: CreateTransformFactorCase
    | CreateTransformFactorExtensionCase,
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
    lines.append("SELECT 1 AS pre_target_boundary;")
    lines.append(
        "-- 3. 执行唯一获得覆盖信用的 CREATE TRANSFORM。"
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
    case: CreateTransformFactorCase
    | CreateTransformFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_transform_factor_case(
        case, Path(".")
    )
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_transform_factor_programs(
    baseline_plan: CreateTransformFactorLoopPlan,
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


def count_primary_create_transform(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(
            r"(?im)^CREATE\s+(?:OR\s+REPLACE\s+)?TRANSFORM\b",
            region,
        )
    )


def resolve_create_transform_factor_witness(
    case: CreateTransformFactorCase
    | CreateTransformFactorExtensionCase,
    repository_root: Path,
) -> CreateTransformFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateTransformFactorWitness(
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
    "CreateTransformFactorRenderError",
    "CreateTransformFactorWitness",
    "count_primary_create_transform",
    "generate_create_transform_factor_programs",
    "render_create_transform_factor_case",
    "resolve_create_transform_factor_witness",
]
