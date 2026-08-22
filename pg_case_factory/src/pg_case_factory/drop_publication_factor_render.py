"""Render complete PostgreSQL 18.4 DROP PUBLICATION factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.  The
file is assembled from a single :func:`_resolve_case` plan so that the byte-level
witness validator (which re-renders and compares) can never diverge from the
bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_publication ... ORDER BY count(*)``
never nests a ``FROM`` inside an ``EXISTS`` subquery, so
``audit_catalog_observability`` accepts it.  The ``pubname`` column is a real
``pg_catalog.pg_publication`` column on PostgreSQL 18.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .cleanup_bookend import DropSpec, build_cleanup, build_pre_cleanup
from .drop_publication_factor_extension import (
    DropPublicationFactorExtensionCase,
)
from .drop_publication_factor_loop import (
    DropPublicationFactorCase,
    DropPublicationFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/publication/"
    "drop_publication.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/publication/"
    "drop_publication.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

# Primary (factor, value) pairs where the target publication is intentionally
# absent, so the drop surfaces a not-found error (or a notice under IF EXISTS)
# and the oracle asserts absence.
_ABSENT_PRIMARIES = frozenset(
    {
        ("expected_status", "failure"),
        ("publication_existence", "publication_not_exists"),
        ("nonexistent_publication", "publication_does_not_exist"),
        ("publication_name_shape", "non_existing_name"),
    }
)

# For an extension SUCCESS case (no present failure pair) the synthetic primary
# must be a neutral success primary whose helpers fall through to the
# assignment; the publication always exists in extensions (publication_existence
# held at exists when no lookup failure fires).
_BRANCH_NEUTRAL_SUCCESS = ("publication_existence", "publication_exists")


def _synthetic_case(
    ext: DropPublicationFactorExtensionCase,
) -> DropPublicationFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .drop_publication_factor_extension import _present_failure_pair

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropPublicationFactorCase(
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
    case: DropPublicationFactorCase | DropPublicationFactorExtensionCase,
) -> DropPublicationFactorCase:
    if isinstance(case, DropPublicationFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropPublicationFactorRenderError(ValueError):
    """Raised when a DROP PUBLICATION case cannot be rendered."""


@dataclass(frozen=True)
class DropPublicationFactorWitness:
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


def _baseline(case: DropPublicationFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _pub_name(
    case: DropPublicationFactorCase, a: dict[str, str], p: str
) -> str:
    """The primary publication name as referenced inside DROP PUBLICATION."""

    shape = a.get("publication_name_shape", "simple_name")
    if shape == "quoted_name":
        return f'"{p}QuotedPub"'
    if shape == "reserved_word_name":
        return f'"{p}all"'
    if shape == "non_existing_name":
        return f"{p}nonexistent_pub"
    return f"{p}pub"


def _probe_name(
    case: DropPublicationFactorCase, a: dict[str, str], p: str
) -> str:
    """The bare pubname (no quotes) for the catalog probe."""

    shape = a.get("publication_name_shape", "simple_name")
    if shape == "quoted_name":
        return f"{p}QuotedPub"
    if shape == "reserved_word_name":
        return f"{p}all"
    if shape == "non_existing_name":
        return f"{p}nonexistent_pub"
    return f"{p}pub"


def _target_names(
    case: DropPublicationFactorCase, a: dict[str, str], p: str
) -> tuple[str, ...]:
    """The list of publication names in the DROP PUBLICATION target."""

    primary = _pub_name(case, a, p)
    multi = a.get("multi_target", "single_target")
    if multi == "single_target":
        return (primary,)
    return (primary, f"{p}pub2")


def _fixture_pubs(
    case: DropPublicationFactorCase, a: dict[str, str], p: str
) -> tuple[str, ...]:
    """The list of publication names to CREATE (existing ones only)."""

    primary = _pub_name(case, a, p)
    multi = a.get("multi_target", "single_target")
    if multi == "multi_target_all_exist":
        return (primary, f"{p}pub2")
    # single_target and multi_target_some_not_exist: only the primary exists.
    return (primary,)


def _needs_pub2(a: dict[str, str]) -> bool:
    return a.get("multi_target", "single_target") != "single_target"


def _fixture_kind(
    case: DropPublicationFactorCase, a: dict[str, str]
) -> str:
    """Whether a publication fixture must be created."""

    if case.kind == "RISK":
        return "publication"
    if (case.factor_key, case.factor_value) in _ABSENT_PRIMARIES:
        return "none"
    if case.kind == "EXT":
        if a.get("publication_existence") == "publication_not_exists":
            return "none"
        if a.get("publication_name_shape") == "non_existing_name":
            return "none"
    return "publication"


def _if_exists_present(
    case: DropPublicationFactorCase, a: dict[str, str]
) -> bool:
    return a.get("if_exists_clause") == "with_if_exists"


def _cascade_clause(a: dict[str, str]) -> str:
    clause = a.get("cascade_restrict_clause", "no_clause_default_restrict")
    if clause == "cascade":
        return "CASCADE"
    if clause == "restrict":
        return "RESTRICT"
    return ""  # no_clause_default_restrict: RESTRICT is the default


def _effective_role(
    case: DropPublicationFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP PUBLICATION runs."""

    if case.kind == "EXT":
        level = a.get("privilege_context", "superuser")
        return f"{p}actor" if level == "non_owner_no_privilege" else ""
    if case.factor_key == "privilege_context":
        return f"{p}actor" if case.factor_value == "non_owner_no_privilege" else ""
    return ""


def _needs_subscription(
    case: DropPublicationFactorCase, a: dict[str, str]
) -> bool:
    """Whether a subscription dependency fixture must be created."""

    return a.get("subscription_dependency") == "has_subscription_dependency"


def _pub_absent_after(
    case: DropPublicationFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target publication is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if _fixture_kind(case, a) == "none":
        return True
    if case.outcome == "success":
        return True
    return False


def _probe_select(
    case: DropPublicationFactorCase, a: dict[str, str], p: str
) -> str:
    name = _probe_name(case, a, p)
    absent = _pub_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "publication_absent" if absent else "publication_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_publication "
        f"WHERE pubname = '{name}' ORDER BY count(*) LIMIT 1;"
    )


def _role_names(
    case: DropPublicationFactorCase, p: str, effective: str
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}actor":
        roles.append(f"{p}actor")
    return tuple(roles)


def _resolve_case(case: DropPublicationFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    fixture_kind = _fixture_kind(case, a)
    pub_ref = _pub_name(case, a, p)
    target_names = _target_names(case, a, p)
    fixture_pubs = _fixture_pubs(case, a, p)
    needs_sub = _needs_subscription(case, a)
    needs_second = _needs_pub2(a)

    setup: list[str] = []
    locus = "target.publication"

    # --- role fixtures (CREATE only; SET ROLE deferred to after the
    # publication fixture so they run as the superuser) ---
    effective = _effective_role(case, a, p)
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- the target publication fixture(s) (as superuser, before SET ROLE) ---
    if fixture_kind == "publication":
        for pub in fixture_pubs:
            setup.append(f"CREATE PUBLICATION {pub};")
    else:
        setup.append(
            "SELECT 1 AS target_publication_intentionally_absent;"
        )
        locus = "fixture.object_state"

    # --- subscription dependency fixture (as superuser, before SET ROLE) ---
    if needs_sub:
        setup.append(
            f"CREATE SUBSCRIPTION {p}sub "
            "CONNECTION 'host=localhost port=5432 dbname=pgcf' "
            f"PUBLICATION {pub_ref};"
        )
        locus = "fixture.dependency_state"

    # --- arm the non-superuser role (AFTER publication creation) -----------
    if effective:
        setup.append(f"SET ROLE {p}actor;")
    if_exists = "IF EXISTS " if _if_exists_present(case, a) else ""
    cascade = _cascade_clause(a)
    name_list = ", ".join(target_names)
    target = f"DROP PUBLICATION {if_exists}{name_list}"
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
    # Migrated to cleanup_bookend so every DROP carries IF EXISTS and
    # DROP OWNED BY is unreachable in pre-cleanup: the non-owner role
    # fixture is created by setup, so on a fresh database the role does
    # not exist yet at pre-cleanup time and DROP OWNED BY would crash
    # (ON_ERROR_STOP=1) before the target statement reaches execution.
    # Pre-cleanup drops roles via DROP ROLE IF EXISTS only; the post-target
    # cleanup runs DROP OWNED BY then DROP ROLE IF EXISTS once setup has
    # created the role.
    roles = _role_names(case, p, effective)
    specs: list[DropSpec] = []
    if needs_sub:
        specs.append(DropSpec("SUBSCRIPTION", f"{p}sub"))
    specs.append(DropSpec("PUBLICATION", pub_ref))
    if needs_second:
        specs.append(DropSpec("PUBLICATION", f"{p}pub2"))
    role_list = list(roles)
    pre_bookend = build_pre_cleanup(
        specs=tuple(specs),
        roles=role_list,
    )
    cln_bookend = build_cleanup(
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


def resolve_drop_publication_factor_witness(
    case: DropPublicationFactorCase | DropPublicationFactorExtensionCase,
    repository_root: Path,
) -> DropPublicationFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropPublicationFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_publication(sql: str) -> int:
    """Count the single credited DROP PUBLICATION inside the primary fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*DROP\s+PUBLICATION\b", region)
    )


def _header(case: DropPublicationFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP PUBLICATION {case.factor_key}={case.factor_value}",
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


def render_drop_publication_factor_case(
    case: DropPublicationFactorCase | DropPublicationFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP PUBLICATION regress program."""

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地发布和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP PUBLICATION。")
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


def generate_drop_publication_factor_programs(
    baseline_plan: DropPublicationFactorLoopPlan,
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
    case: DropPublicationFactorCase | DropPublicationFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_publication_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropPublicationFactorRenderError",
    "DropPublicationFactorWitness",
    "count_primary_drop_publication",
    "generate_drop_publication_factor_programs",
    "render_drop_publication_factor_case",
    "resolve_drop_publication_factor_witness",
]
