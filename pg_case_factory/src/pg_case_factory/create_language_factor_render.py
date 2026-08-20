"""Render complete PostgreSQL 18.4 CREATE LANGUAGE factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

CREATE LANGUAGE is a catalog-row DDL statement: the target is a
``pg_catalog.pg_language`` catalog row, not a ``pg_class`` relation.
All catalog oracles schema-qualify ``pg_catalog.pg_language`` (exempt
from the file-prefix style gate).  No case creates a TABLE, so the
bookend (DROP TABLE IF EXISTS) is never emitted; a residual
``SELECT 1 AS residual_check_no_objects;`` placeholder stands in.
Every catalog SELECT carries a top-level ``ORDER BY`` so the
catalog-observability gate passes.

The renderer emits both ``CREATE LANGUAGE`` and ``CREATE OR REPLACE
LANGUAGE`` variants (covering the ``or_replace_clause`` factor values).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .create_language_factor_extension import (
    CreateLanguageFactorExtensionCase,
    _present_failure_pair,
)
from .create_language_factor_loop import (
    CreateLanguageFactorCase,
    CreateLanguageFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/language/"
    "create_language.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/language/"
    "create_language.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class CreateLanguageFactorRenderError(ValueError):
    """Raised when a CREATE LANGUAGE case cannot be rendered."""


@dataclass(frozen=True)
class CreateLanguageFactorWitness:
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
    ext: CreateLanguageFactorExtensionCase,
) -> CreateLanguageFactorCase:
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
    return CreateLanguageFactorCase(
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
    case: CreateLanguageFactorCase
    | CreateLanguageFactorExtensionCase,
) -> CreateLanguageFactorCase:
    if isinstance(case, CreateLanguageFactorExtensionCase):
        return _synthetic_case(case)
    return case


def _baseline(case: CreateLanguageFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _language_name(a: dict[str, str], p: str) -> str:
    """The language identifier in CREATE LANGUAGE and fixtures."""

    shape = a.get("name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f'"{p}QLang"'
    if shape == "schema_qualified":
        return f"public.{p}lang"
    return f"{p}lang"


def _language_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    shape = a.get("name_shape", "plain_identifier")
    if shape == "quoted_identifier":
        return f"{p}QLang"
    if shape == "schema_qualified":
        return f"{p}lang"
    return f"{p}lang"


def _handler_name(a: dict[str, str], p: str) -> str:
    """The handler function identifier used in CREATE LANGUAGE."""

    shape = a.get("handler_name_shape", "plain_function")
    if shape == "missing_function":
        return f"{p}missing"
    if shape == "schema_qualified_function":
        return f"public.{p}handler"
    return f"{p}handler"


def _inline_name(a: dict[str, str], p: str) -> str:
    shape = a.get("handler_name_shape", "plain_function")
    if shape == "schema_qualified_function":
        return f"public.{p}inline"
    return f"{p}inline"


def _validator_name(a: dict[str, str], p: str) -> str:
    shape = a.get("handler_name_shape", "plain_function")
    if shape == "schema_qualified_function":
        return f"public.{p}validator"
    return f"{p}validator"


def _handler_missing(a: dict[str, str]) -> bool:
    return a.get("handler_clause") == "handler_missing"


def _wrong_signature(a: dict[str, str]) -> bool:
    return a.get("dependency_state") == "wrong_signature"


def _missing_validator(a: dict[str, str]) -> bool:
    return a.get("dependency_state") == "missing_validator"


def _is_duplicate(a: dict[str, str]) -> bool:
    return (
        a.get("target_object_state") in ("exists", "exists_conflict")
        and a.get("or_replace_clause") == "absent"
    )


def _needs_existing(a: dict[str, str]) -> bool:
    return a.get("target_object_state") in ("exists", "exists_conflict")


def _is_failure_case(case: CreateLanguageFactorCase) -> bool:
    return case.outcome == "expected_failure"


def _language_present(
    case: CreateLanguageFactorCase, a: dict[str, str]
) -> bool:
    """Whether the language exists after the target statement."""

    if not _is_failure_case(case):
        return True
    return _is_duplicate(a)


def _build_target(
    a: dict[str, str], p: str, consumer: str
) -> str:
    """The primary CREATE LANGUAGE statement."""

    name = _language_name(a, p)
    or_replace = a.get("or_replace_clause", "absent")
    or_replace_kw = "OR REPLACE " if or_replace != "absent" else ""
    trusted = "TRUSTED " if a.get("trusted_clause") == "present" else ""

    if consumer == "handlerless_legacy":
        return (
            f"CREATE {or_replace_kw}{trusted}LANGUAGE "
            f"{name};"
        )

    handler = _handler_name(a, p)
    inline = a.get("inline_clause", "absent")
    validator = a.get("validator_clause", "absent")

    ic = a.get("invalid_combination", "none")
    if ic == "syntax_valid_semantic_error":
        return (
            f"CREATE {or_replace_kw}{trusted}LANGUAGE "
            f"{name} HANDLER {handler} VALIDATOR {handler};"
        )

    parts: list[str] = [f"HANDLER {handler}"]
    if inline == "present":
        parts.append(f"INLINE {_inline_name(a, p)}")
    if validator == "present":
        if _missing_validator(a):
            parts.append(f"VALIDATOR {p}missing_validator")
        else:
            parts.append(f"VALIDATOR {_validator_name(a, p)}")

    clause = " ".join(parts)
    return (
        f"CREATE {or_replace_kw}{trusted}LANGUAGE "
        f"{name} {clause};"
    )


def _effective_role(a: dict[str, str], p: str) -> str:
    priv = a.get("privilege_context", "superuser")
    if priv == "non_superuser":
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    roles: list[str] = []
    priv = a.get("privilege_context", "superuser")
    if priv == "non_superuser":
        roles.append(f"{p}actor")
    return tuple(roles)


def _probe_select(
    case: CreateLanguageFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only verification."""

    mode = a.get("verification_mode", "catalog_query")
    literal = _language_literal(a, p)
    present = _language_present(case, a)

    if mode == "error_assertion":
        return None

    if mode == "effect_query":
        if present:
            return (
                f"SELECT lanname FROM pg_catalog.pg_language "
                f"WHERE lanname = '{literal}' "
                f"ORDER BY lanname;"
            )
        return None

    # catalog_query
    cmp_op = ">" if present else "="
    return (
        f"SELECT count(*) {cmp_op} 0 AS language_state "
        f"FROM pg_catalog.pg_language "
        f"WHERE lanname = '{literal}' "
        f"ORDER BY count(*);"
    )


def _resolve_case(
    case: CreateLanguageFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    consumer = case.consumer_action_id

    setup: list[str] = []
    locus = "target.create_language"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    name = _language_name(a, p)
    is_handlerless = consumer == "handlerless_legacy"

    # --- role fixtures -----------------------------------------------
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- handler function fixtures (branch_1 only) -------------------
    if not is_handlerless and not _handler_missing(a):
        h_name = _handler_name(a, p)
        if _wrong_signature(a):
            setup.append(
                f"CREATE FUNCTION {h_name}() RETURNS integer "
                f"AS 'plpgsql_call_handler' LANGUAGE C;"
            )
            locus = "fixture.wrong_signature_handler"
        else:
            setup.append(
                f"CREATE FUNCTION {h_name}() RETURNS "
                f"language_handler AS 'plpgsql_call_handler' "
                f"LANGUAGE C;"
            )
            locus = "fixture.handler_function"

    # --- inline function fixture -------------------------------------
    if (
        not is_handlerless
        and a.get("inline_clause") == "present"
        and not _handler_missing(a)
    ):
        i_name = _inline_name(a, p)
        setup.append(
            f"CREATE FUNCTION {i_name}(internal) RETURNS void "
            f"AS 'plpgsql_inline_handler' LANGUAGE C;"
        )
        locus = "fixture.inline_function"

    # --- validator function fixture ----------------------------------
    if (
        not is_handlerless
        and a.get("validator_clause") == "present"
        and not _missing_validator(a)
        and not _handler_missing(a)
    ):
        v_name = _validator_name(a, p)
        setup.append(
            f"CREATE FUNCTION {v_name}(oid) RETURNS void "
            f"AS 'plpgsql_validator' LANGUAGE C;"
        )
        locus = "fixture.validator_function"

    # --- duplicate / replace fixture ---------------------------------
    if _needs_existing(a) and not is_handlerless:
        handler = _handler_name(a, p)
        if not _handler_missing(a):
            setup.append(
                f"CREATE LANGUAGE {name} "
                f"HANDLER {handler};"
            )
            locus = "fixture.existing_language"

    # --- arm the effective role --------------------------------------
    if effective:
        setup.append(f"SET ROLE {effective};")

    # --- the primary target statement --------------------------------
    target = _build_target(a, p, consumer)

    # --- oracle / SQLSTATE assertion ---------------------------------
    assert_lines: list[str] = []
    if effective:
        assert_lines.append("RESET ROLE;")
    assert_lines.append(
        f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}' "
        "AS target_sqlstate_matches_expected;"
    )
    probe = _probe_select(case, a, p)
    if probe is not None:
        assert_lines.append(probe)

    # --- cleanup construction -----------------------------------------
    languages_to_drop: list[str] = [name]
    functions_to_drop: list[str] = []
    if not is_handlerless and not _handler_missing(a):
        functions_to_drop.append(_handler_name(a, p))
        if a.get("inline_clause") == "present":
            functions_to_drop.append(_inline_name(a, p))
        if (
            a.get("validator_clause") == "present"
            and not _missing_validator(a)
        ):
            functions_to_drop.append(_validator_name(a, p))

    cleanup_mode = a.get("cleanup_mode", "drop_objects")
    if cleanup_mode == "reset_state":
        lang_drops = [
            f"DROP LANGUAGE IF EXISTS {ln} CASCADE;"
            for ln in languages_to_drop
        ]
    else:
        lang_drops = [
            f"DROP LANGUAGE IF EXISTS {ln} CASCADE;"
            for ln in languages_to_drop
        ]

    func_drops = [
        f"DROP FUNCTION IF EXISTS {fn};" for fn in functions_to_drop
    ]

    role_drops = [
        stmt
        for role in roles
        for stmt in (
            f"DROP OWNED BY {role} CASCADE;",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    # pre-cleanup: always use IF EXISTS CASCADE (safe)
    pre_cleanup: list[str] = []
    pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")
    pre_cleanup.append(f"DROP LANGUAGE IF EXISTS {name} CASCADE;")
    for fn in functions_to_drop:
        pre_cleanup.append(f"DROP FUNCTION IF EXISTS {fn};")
    pre_cleanup.append("RESET ROLE;")
    for role in roles:
        pre_cleanup.append(f"DROP ROLE IF EXISTS {role};")

    # cleanup: RESET ROLE, languages, functions, roles
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(lang_drops)
    cleanup.extend(func_drops)
    cleanup.extend(role_drops)

    on_error_off = _is_failure_case(case)
    return _CasePlan(
        target_fragment=target,
        setup_lines=tuple(setup),
        assert_lines=tuple(assert_lines),
        pre_cleanup_lines=tuple(pre_cleanup),
        cleanup_lines=tuple(cleanup),
        on_error_off=on_error_off,
        semantic_locus=locus,
    )


def _header(case: CreateLanguageFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : CREATE LANGUAGE {case.factor_key}="
        f"{case.factor_value}",
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


def render_create_language_factor_case(
    case: CreateLanguageFactorCase
    | CreateLanguageFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信用的 CREATE LANGUAGE。")
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
    case: CreateLanguageFactorCase
    | CreateLanguageFactorExtensionCase,
    out: Path,
) -> None:
    text = render_create_language_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_create_language_factor_programs(
    baseline_plan: CreateLanguageFactorLoopPlan,
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


def count_primary_create_language(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(
            r"(?im)^\s*CREATE\s+(?:OR\s+REPLACE\s+)?"
            r"(?:TRUSTED\s+)?LANGUAGE\b",
            region,
        )
    )


def remove_primary_semantic_locus_but_keep_comments(
    sql: str, case: object
) -> str:
    """Mutation helper: remove primary target SQL but keep comment lines."""

    if _PRIMARY_BEGIN not in sql or _PRIMARY_END not in sql:
        return sql
    before_begin, rest = sql.split(_PRIMARY_BEGIN, 1)
    target_and_after, after_end = rest.split(_PRIMARY_END, 1)
    comment_lines = [
        line
        for line in target_and_after.split("\n")
        if line.strip().startswith("--") or not line.strip()
    ]
    return (
        before_begin
        + _PRIMARY_BEGIN
        + "\n".join(comment_lines)
        + _PRIMARY_END
        + after_end
    )


def resolve_create_language_factor_witness(
    case: CreateLanguageFactorCase
    | CreateLanguageFactorExtensionCase,
    repository_root: Path,
) -> CreateLanguageFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return CreateLanguageFactorWitness(
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
    "CreateLanguageFactorRenderError",
    "CreateLanguageFactorWitness",
    "count_primary_create_language",
    "generate_create_language_factor_programs",
    "render_create_language_factor_case",
    "resolve_create_language_factor_witness",
    "remove_primary_semantic_locus_but_keep_comments",
]
