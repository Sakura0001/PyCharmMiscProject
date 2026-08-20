"""Render complete PostgreSQL 18.4 DROP TEXT SEARCH TEMPLATE factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_ts_template WHERE
tmplname = '...' ORDER BY count(*) LIMIT 1`` never nests a ``FROM`` inside an
``EXISTS`` subquery.  The probe column is a real ``pg_ts_template`` column
(``tmplname``) — verified against PG 18.4.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .drop_text_search_template_factor_extension import (
    DropTextSearchTemplateFactorExtensionCase,
)
from .drop_text_search_template_factor_loop import (
    DropTextSearchTemplateFactorCase,
    DropTextSearchTemplateFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/text_search_template/"
    "drop_text_search_template.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/text_search_template/"
    "drop_text_search_template.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-21"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

# Baseline primaries whose target template is intentionally absent, so the DROP
# surfaces a not-found error (42704) and the oracle asserts absence.
_ABSENT_TEMPLATE_PRIMARIES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "absent"),
        ("template_name_shape", "non_existent_name"),
        ("error_type", "non_existent_without_if_exists"),
    }
)

# Baseline primaries that imply a non-superuser privilege fixture.
_PRIVILEGE_PRIMARIES = frozenset(
    {
        ("privilege_requirement", "non_superuser"),
        ("privilege_context", "non_superuser_session"),
        ("error_type", "insufficient_privilege"),
    }
)

# Baseline primaries that imply a dictionary dependency fixture under RESTRICT.
_DEPENDENCY_PRIMARIES = frozenset(
    {
        ("dependency_context", "dict_using_template"),
        ("dependency_status", "has_dict_dependencies"),
        ("error_type", "dependent_object_exists"),
    }
)

# For an extension SUCCESS case the synthetic primary must be a neutral success
# primary whose helpers fall through to the assignment.
_BRANCH_NEUTRAL_SUCCESS = ("object_state", "exists")


def _synthetic_case(
    ext: DropTextSearchTemplateFactorExtensionCase,
) -> DropTextSearchTemplateFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .drop_text_search_template_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropTextSearchTemplateFactorCase(
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
    case: (
        DropTextSearchTemplateFactorCase
        | DropTextSearchTemplateFactorExtensionCase
    ),
) -> DropTextSearchTemplateFactorCase:
    if isinstance(
        case, DropTextSearchTemplateFactorExtensionCase
    ):
        return _synthetic_case(case)
    return case


class DropTextSearchTemplateFactorRenderError(ValueError):
    """Raised when a DROP TEXT SEARCH TEMPLATE case cannot be rendered."""


@dataclass(frozen=True)
class DropTextSearchTemplateFactorWitness:
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


def _baseline(
    case: DropTextSearchTemplateFactorCase,
) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _template_ref(
    case: DropTextSearchTemplateFactorCase, a: dict[str, str], p: str
) -> str:
    """The template name as referenced inside DROP TEXT SEARCH TEMPLATE."""

    shape = a.get("template_name_shape", "simple_id")
    if shape == "quoted_id":
        return f'"{p}qtmpl"'
    if shape == "schema_qualified_id":
        return f"public.{p}tmpl"
    if shape == "reserved_word_id":
        return '"select"'
    if shape == "non_existent_name":
        return f"{p}noexist"
    return f"{p}tmpl"


def _template_probe(
    case: DropTextSearchTemplateFactorCase, a: dict[str, str], p: str
) -> str:
    """The bare tmplname (no quotes/schema) for the catalog probe."""

    shape = a.get("template_name_shape", "simple_id")
    if shape == "quoted_id":
        return f"{p}qtmpl"
    if shape == "schema_qualified_id":
        return f"{p}tmpl"
    if shape == "reserved_word_id":
        return "select"
    if shape == "non_existent_name":
        return f"{p}noexist"
    return f"{p}tmpl"


def _template_created(
    case: DropTextSearchTemplateFactorCase, a: dict[str, str]
) -> bool:
    """Whether a template fixture must be created."""

    if a.get("object_state") == "absent":
        return False
    if a.get("template_name_shape") == "non_existent_name":
        return False
    return True


def _if_exists_present(
    case: DropTextSearchTemplateFactorCase, a: dict[str, str]
) -> bool:
    return a.get("if_exists_clause") == "present"


def _cascade_clause(a: dict[str, str]) -> str:
    cascade = a.get("cascade_restrict", "default_restrict")
    if cascade == "explicit_cascade":
        return "CASCADE"
    if cascade == "explicit_restrict":
        return "RESTRICT"
    return ""  # default_restrict: RESTRICT is the default


def _effective_role(
    case: DropTextSearchTemplateFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP TEXT SEARCH TEMPLATE runs."""

    if case.kind == "EXT":
        level = a.get("privilege_requirement", "superuser")
        context = a.get("privilege_context", "superuser_session")
        if level == "non_superuser" or context == "non_superuser_session":
            return f"{p}actor"
        return ""
    if (case.factor_key, case.factor_value) in _PRIVILEGE_PRIMARIES:
        return f"{p}actor"
    return ""


def _needs_dependent(
    case: DropTextSearchTemplateFactorCase, a: dict[str, str]
) -> bool:
    """Whether a dictionary dependency fixture must be created."""

    if not _template_created(case, a):
        return False
    if case.kind == "EXT":
        return (
            a.get("dependency_context") == "dict_using_template"
            or a.get("dependency_status") == "has_dict_dependencies"
        )
    if (case.factor_key, case.factor_value) in _DEPENDENCY_PRIMARIES:
        return True
    return (
        a.get("dependency_context") == "dict_using_template"
        or a.get("dependency_status") == "has_dict_dependencies"
    )


def _template_absent_after(
    case: DropTextSearchTemplateFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target template is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if not _template_created(case, a):
        return True
    if case.outcome == "success":
        return True
    return False


def _probe_select(
    case: DropTextSearchTemplateFactorCase, a: dict[str, str], p: str
) -> str:
    template_probe = _template_probe(case, a, p)
    absent = _template_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "template_absent" if absent else "template_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_ts_template "
        f"WHERE tmplname = '{template_probe}' "
        "ORDER BY count(*) LIMIT 1;"
    )


def _role_names(
    case: DropTextSearchTemplateFactorCase, p: str, effective: str
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}actor":
        roles.append(f"{p}actor")
    return tuple(roles)


def _resolve_case(
    case: DropTextSearchTemplateFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    template_ref = _template_ref(case, a, p)
    template_created = _template_created(case, a)
    needs_dep = _needs_dependent(case, a)

    setup: list[str] = []
    locus = "target.text_search_template"

    # --- role fixtures (CREATE only; SET ROLE deferred to after the template
    # fixture so they run as the superuser) ---
    effective = _effective_role(case, a, p)
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- the template fixture (as superuser, before SET ROLE) ---
    if template_created:
        setup.append(
            f"CREATE TEXT SEARCH TEMPLATE {template_ref} "
            "INIT (dsimple_init) LEXIZE (dsimple_lexize);"
        )
        if locus == "target.text_search_template":
            locus = "fixture.template"
    elif not template_created:
        setup.append(
            "SELECT 1 AS target_template_intentionally_absent;"
        )
        locus = "fixture.object_state"

    # --- dictionary dependency fixture (as superuser, before SET ROLE) ---
    if needs_dep:
        setup.append(
            f"CREATE TEXT SEARCH DICTIONARY {p}dict "
            f"TEMPLATE {template_ref};"
        )
        locus = "fixture.dependency_state"

    # --- arm the non-superuser role (AFTER template creation) ---
    if effective:
        setup.append(f"SET ROLE {p}actor;")
    if_exists = "IF EXISTS " if _if_exists_present(case, a) else ""
    cascade = _cascade_clause(a)
    target = f"DROP TEXT SEARCH TEMPLATE {if_exists}{template_ref}"
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
    dep_drop = (
        [f"DROP TEXT SEARCH DICTIONARY IF EXISTS {p}dict CASCADE;"]
        if needs_dep
        else []
    )
    tmpl_drop = [
        f"DROP TEXT SEARCH TEMPLATE IF EXISTS {template_ref} CASCADE;"
    ]
    roles = _role_names(case, p, effective)
    role_drops = [
        statement
        for role in roles
        for statement in (
            f"DROP OWNED BY {role};",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    # Pre-cleanup: drop dictionary first, then template, then role.
    pre_cleanup: list[str] = []
    pre_cleanup.extend(dep_drop)
    pre_cleanup.extend(tmpl_drop)
    pre_cleanup.extend(role_drops)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # Cleanup: RESET ROLE, then dictionary/template/role drops.
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(dep_drop)
    cleanup.extend(tmpl_drop)
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


def resolve_drop_text_search_template_factor_witness(
    case: (
        DropTextSearchTemplateFactorCase
        | DropTextSearchTemplateFactorExtensionCase
    ),
    repository_root: Path,
) -> DropTextSearchTemplateFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropTextSearchTemplateFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_text_search_template(sql: str) -> int:
    """Count the single credited DROP TEXT SEARCH TEMPLATE inside the fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(
            r"(?im)^\s*DROP\s+TEXT\s+SEARCH\s+TEMPLATE\b", region
        )
    )


def _header(
    case: DropTextSearchTemplateFactorCase,
) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP TEXT SEARCH TEMPLATE "
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


def render_drop_text_search_template_factor_case(
    case: (
        DropTextSearchTemplateFactorCase
        | DropTextSearchTemplateFactorExtensionCase
    ),
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP TEXT SEARCH TEMPLATE regress program."""

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地模板和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP TEXT SEARCH TEMPLATE。")
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


def generate_drop_text_search_template_factor_programs(
    baseline_plan: DropTextSearchTemplateFactorLoopPlan,
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
    case: (
        DropTextSearchTemplateFactorCase
        | DropTextSearchTemplateFactorExtensionCase
    ),
    out: Path,
) -> None:
    text = render_drop_text_search_template_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropTextSearchTemplateFactorRenderError",
    "DropTextSearchTemplateFactorWitness",
    "count_primary_drop_text_search_template",
    "generate_drop_text_search_template_factor_programs",
    "render_drop_text_search_template_factor_case",
    "resolve_drop_text_search_template_factor_witness",
]
