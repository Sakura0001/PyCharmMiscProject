"""Render complete PostgreSQL 18.4 DROP TEXT SEARCH PARSER factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_ts_parser WHERE prsname =
'...' ORDER BY count(*) LIMIT 1`` never nests a ``FROM`` inside an ``EXISTS``
subquery, so ``audit_catalog_observability`` accepts it.  The probe column is
the real ``pg_ts_parser.prsname`` — the no-DB tickoff does not execute this
probe, so a wrong column would pass all static gates yet be a permanent latent
runtime bug; the column is verified.

DROP TEXT SEARCH PARSER does not create/drop tables → the bookend gate is N/A.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .drop_text_search_parser_factor_extension import (
    DropTsParserFactorExtensionCase,
)
from .drop_text_search_parser_factor_loop import (
    DropTsParserFactorCase,
    DropTsParserFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/"
    "text_search_parser/drop_text_search_parser.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/"
    "text_search_parser/drop_text_search_parser.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-21"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

# Baseline primaries whose target parser is intentionally absent, so the DROP
# surfaces a not-found error (42704) and the oracle asserts absence.
_ABSENT_PARSER_PRIMARIES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "absent"),
        ("parser_name_shape", "non_existent_name"),
        ("error_type", "non_existent_without_if_exists"),
    }
)

# Baseline primaries that imply a non-superuser role fixture must be armed.
_PRIVILEGE_PRIMARIES = frozenset(
    {
        ("privilege_requirement", "non_superuser"),
        ("privilege_context", "non_superuser_session"),
        ("error_type", "insufficient_privilege"),
    }
)

# Baseline primaries that imply a dependent text search configuration fixture
# must be created.
_DEPENDENCY_PRIMARIES = frozenset(
    {
        ("dependency_context", "config_using_parser"),
        ("dependency_status", "has_config_dependencies"),
        ("error_type", "dependent_object_exists"),
    }
)

# For an extension SUCCESS case (no present failure pair) the synthetic
# primary must be a neutral success primary whose helpers fall through to the
# assignment; the parser always exists in extensions (object_state held at
# exists) unless object_state=absent / parser_name_shape=non_existent_name.
_BRANCH_NEUTRAL_SUCCESS = ("object_state", "exists")


def _synthetic_case(
    ext: DropTsParserFactorExtensionCase,
) -> DropTsParserFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .drop_text_search_parser_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropTsParserFactorCase(
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
    case: DropTsParserFactorCase | DropTsParserFactorExtensionCase,
) -> DropTsParserFactorCase:
    if isinstance(case, DropTsParserFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropTsParserFactorRenderError(ValueError):
    """Raised when a DROP TEXT SEARCH PARSER case cannot be rendered."""


@dataclass(frozen=True)
class DropTsParserFactorWitness:
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


def _baseline(case: DropTsParserFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _parser_created(case: DropTsParserFactorCase, a: dict[str, str]) -> bool:
    """Whether a parser fixture must be created."""

    if case.kind == "EXT":
        if a.get("object_state") == "absent":
            return False
        if a.get("parser_name_shape") == "non_existent_name":
            return False
        return True
    if (case.factor_key, case.factor_value) in _ABSENT_PARSER_PRIMARIES:
        return False
    if a.get("object_state") == "absent":
        return False
    if a.get("parser_name_shape") == "non_existent_name":
        return False
    if a.get("error_type") == "non_existent_without_if_exists":
        return False
    return True


def _needs_config(case: DropTsParserFactorCase, a: dict[str, str]) -> bool:
    """Whether a text search configuration fixture must be created."""

    if case.kind == "EXT":
        return a.get("dependency_context") == "config_using_parser"
    if (case.factor_key, case.factor_value) in _DEPENDENCY_PRIMARIES:
        return True
    return a.get("dependency_context") == "config_using_parser"


def _effective_role(
    case: DropTsParserFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP TEXT SEARCH PARSER runs."""

    if case.kind == "EXT":
        level = a.get("privilege_requirement", "superuser")
        return f"{p}actor" if level == "non_superuser" else ""
    if (case.factor_key, case.factor_value) in _PRIVILEGE_PRIMARIES:
        return f"{p}actor"
    if a.get("privilege_requirement") == "non_superuser":
        return f"{p}actor"
    if a.get("privilege_context") == "non_superuser_session":
        return f"{p}actor"
    return ""


def _parser_ref(case: DropTsParserFactorCase, a: dict[str, str], p: str) -> str:
    """The parser name as referenced inside DROP TEXT SEARCH PARSER."""

    shape = a.get("parser_name_shape", "simple_id")
    if shape == "schema_qualified_id":
        return f"public.{p}parser"
    if shape == "quoted_id":
        return f'"{p}qparser"'
    if shape == "reserved_word_id":
        return '"user"'
    if shape == "non_existent_name":
        return f"{p}noexist"
    return f"{p}parser"


def _parser_probe(case: DropTsParserFactorCase, a: dict[str, str], p: str) -> str:
    """The bare prsname (no quotes/schema) for the catalog probe."""

    shape = a.get("parser_name_shape", "simple_id")
    if shape == "quoted_id":
        return f"{p}qparser"
    if shape == "reserved_word_id":
        return "user"
    if shape == "non_existent_name":
        return f"{p}noexist"
    return f"{p}parser"


def _if_exists_present(case: DropTsParserFactorCase, a: dict[str, str]) -> bool:
    return a.get("if_exists_clause") == "present"


def _cascade_clause(a: dict[str, str]) -> str:
    cascade = a.get("cascade_restrict", "default_restrict")
    if cascade == "explicit_cascade":
        return "CASCADE"
    if cascade == "explicit_restrict":
        return "RESTRICT"
    return ""  # default_restrict: RESTRICT is the default


def _parser_absent_after(
    case: DropTsParserFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target parser is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if not _parser_created(case, a):
        return True
    if case.outcome == "success":
        return True
    return False


def _probe_select(
    case: DropTsParserFactorCase, a: dict[str, str], p: str
) -> str:
    parser_probe = _parser_probe(case, a, p)
    absent = _parser_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "parser_absent" if absent else "parser_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_ts_parser "
        f"WHERE prsname = '{parser_probe}' "
        "ORDER BY count(*) LIMIT 1;"
    )


def _role_names(
    case: DropTsParserFactorCase, p: str, effective: str
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}actor":
        roles.append(f"{p}actor")
    return tuple(roles)


def _resolve_case(case: DropTsParserFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    parser_ref = _parser_ref(case, a, p)
    parser_created = _parser_created(case, a)
    needs_config = _needs_config(case, a)

    setup: list[str] = []
    locus = "target.ts_parser"

    # --- setup boundary SELECT (prevents \set from merging with the first
    # statement so the style gate detects the program boundary cleanly) ---
    setup.append("SELECT 1 AS setup_boundary;")

    # --- role fixtures (CREATE only; SET ROLE deferred to after the parser
    # fixture so they run as the superuser) ---
    effective = _effective_role(case, a, p)
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- the parser fixture (as superuser, before SET ROLE) ---
    if parser_created:
        setup.append(
            f"CREATE TEXT SEARCH PARSER {parser_ref} ("
            " START = prsd_start,"
            " GETTOKEN = prsd_nexttoken,"
            " END = prsd_end,"
            " LEXTYPES = prsd_lextype,"
            " HEADLINE = prsd_headline"
            ");"
        )
        if locus == "target.ts_parser":
            locus = "fixture.ts_parser"
    else:
        setup.append(
            "SELECT 1 AS target_parser_intentionally_absent;"
        )
        locus = "fixture.object_state"

    # --- the configuration fixture (as superuser, before SET ROLE) -------
    if needs_config:
        setup.append(
            f"CREATE TEXT SEARCH CONFIGURATION {p}config "
            f"(PARSER = {parser_ref});"
        )
        locus = "fixture.dependency_state"

    # --- arm the non-superuser role (AFTER parser creation) --------------
    if effective:
        setup.append(f"SET ROLE {p}actor;")
    if_exists = "IF EXISTS " if _if_exists_present(case, a) else ""
    cascade = _cascade_clause(a)
    target = f"DROP TEXT SEARCH PARSER {if_exists}{parser_ref}"
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

    # --- cleanup construction -------------------------------------------
    config_drop = (
        [f"DROP TEXT SEARCH CONFIGURATION IF EXISTS {p}config CASCADE;"]
        if needs_config
        else []
    )
    parser_drop = (
        [f"DROP TEXT SEARCH PARSER IF EXISTS {parser_ref} CASCADE;"]
        if parser_created
        else []
    )
    roles = _role_names(case, p, effective)
    role_drops = [
        statement
        for role in roles
        for statement in (
            f"DROP OWNED BY {role};",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    # Pre-cleanup: config first, then parser, then roles.
    pre_cleanup: list[str] = []
    pre_cleanup.extend(config_drop)
    pre_cleanup.extend(parser_drop)
    pre_cleanup.extend(role_drops)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # Cleanup: RESET ROLE, then config/parser/role drops.
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(config_drop)
    cleanup.extend(parser_drop)
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


def resolve_drop_text_search_parser_factor_witness(
    case: DropTsParserFactorCase | DropTsParserFactorExtensionCase,
    repository_root: Path,
) -> DropTsParserFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropTsParserFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_text_search_parser(sql: str) -> int:
    """Count the single credited DROP TEXT SEARCH PARSER inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*DROP\s+TEXT\s+SEARCH\s+PARSER\b", region)
    )


def _header(case: DropTsParserFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP TEXT SEARCH PARSER "
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


def render_drop_text_search_parser_factor_case(
    case: DropTsParserFactorCase | DropTsParserFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP TEXT SEARCH PARSER regress program."""

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地解析器和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP TEXT SEARCH PARSER。")
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


def generate_drop_text_search_parser_factor_programs(
    baseline_plan: DropTsParserFactorLoopPlan,
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
    case: DropTsParserFactorCase | DropTsParserFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_text_search_parser_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropTsParserFactorRenderError",
    "DropTsParserFactorWitness",
    "count_primary_drop_text_search_parser",
    "generate_drop_text_search_parser_factor_programs",
    "render_drop_text_search_parser_factor_case",
    "resolve_drop_text_search_parser_factor_witness",
]
