"""Render complete PostgreSQL 18.4 DROP TEXT SEARCH DICTIONARY factor-loop regress programs.

Every planned obligation becomes one self-contained, deterministic SQL file.
The file is assembled from a single :func:`_resolve_case` plan so that the
byte-level witness validator (which re-renders and compares) can never diverge
from the bytes actually written.

The oracle queries are catalog-audit-compliant: a top-level
``SELECT count(*) <op> AS alias FROM pg_catalog.pg_ts_dict WHERE dictname =
'...' ORDER BY count(*) LIMIT 1`` never nests a ``FROM`` inside an
``EXISTS`` subquery, so ``audit_catalog_observability`` accepts it.  The probe
column is the real ``pg_ts_dict.dictname`` column (verified against PG 18.4).
The no-DB tickoff does not execute this probe, so a wrong column would pass all
static gates yet be a permanent latent runtime bug; the column is verified.

DROP TEXT SEARCH DICTIONARY is table-less: no CREATE TABLE is ever emitted, so
the bookend gate (first + last ``;``-stmt must be ``DROP TABLE IF EXISTS``)
is not applicable.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .cleanup_bookend import DropSpec, build_cleanup, build_pre_cleanup
from .drop_text_search_dictionary_factor_extension import (
    DropTextSearchDictionaryFactorExtensionCase,
)
from .drop_text_search_dictionary_factor_loop import (
    DropTextSearchDictionaryFactorCase,
    DropTextSearchDictionaryFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/text_search_dictionary/"
    "drop_text_search_dictionary.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/text_search_dictionary/"
    "drop_text_search_dictionary.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-21"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_BRANCH_1 = "branch_1"

_ABSENT_DICT_PRIMARIES = frozenset(
    {
        ("expected_status", "failure"),
        ("object_state", "absent"),
        ("dict_name_shape", "non_existent_name"),
        ("error_type", "non_existent_without_if_exists"),
    }
)

_DEPENDENCY_PRIMARIES = frozenset(
    {
        ("dependency_context", "config_using_dict"),
        ("dependency_status", "has_config_dependencies"),
        ("error_type", "dependent_object_exists"),
    }
)

# For an extension SUCCESS case the synthetic primary must be a neutral success
# primary whose helpers fall through to the assignment; the dictionary always
# exists in extensions (object_state held at exists) unless object_state=absent
# or dict_name_shape=non_existent_name.
_BRANCH_NEUTRAL_SUCCESS = ("object_state", "exists")


def _synthetic_case(
    ext: DropTextSearchDictionaryFactorExtensionCase,
) -> DropTextSearchDictionaryFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    from .drop_text_search_dictionary_factor_extension import (
        _present_failure_pair,
    )

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key, factor_value = _BRANCH_NEUTRAL_SUCCESS
    return DropTextSearchDictionaryFactorCase(
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
    case: DropTextSearchDictionaryFactorCase
    | DropTextSearchDictionaryFactorExtensionCase,
) -> DropTextSearchDictionaryFactorCase:
    if isinstance(case, DropTextSearchDictionaryFactorExtensionCase):
        return _synthetic_case(case)
    return case


class DropTextSearchDictionaryFactorRenderError(ValueError):
    """Raised when a DROP TEXT SEARCH DICTIONARY case cannot be rendered."""


@dataclass(frozen=True)
class DropTextSearchDictionaryFactorWitness:
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


def _baseline(case: DropTextSearchDictionaryFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _dict_created(case: DropTextSearchDictionaryFactorCase, a: dict[str, str]) -> bool:
    """Whether a dictionary fixture must be created."""

    if a.get("object_state") == "absent":
        return False
    if a.get("dict_name_shape") == "non_existent_name":
        return False
    return True


def _dict_ref(case: DropTextSearchDictionaryFactorCase, a: dict[str, str], p: str) -> str:
    """The dictionary name as referenced inside the DROP and CREATE."""

    shape = a.get("dict_name_shape", "simple_id")
    if shape == "schema_qualified_id":
        return f"public.{p}dict"
    if shape == "quoted_id":
        return f'"{p}qdict"'
    if shape == "reserved_word_id":
        return f'"{p}rwdict"'
    if shape == "non_existent_name":
        return f"{p}nodict"
    return f"{p}dict"


def _dict_probe(case: DropTextSearchDictionaryFactorCase, a: dict[str, str], p: str) -> str:
    """The bare dictname (no quotes/schema) for the catalog probe."""

    shape = a.get("dict_name_shape", "simple_id")
    if shape == "quoted_id":
        return f"{p}qdict"
    if shape == "reserved_word_id":
        return f"{p}rwdict"
    if shape == "non_existent_name":
        return f"{p}nodict"
    return f"{p}dict"


def _if_exists_present(case: DropTextSearchDictionaryFactorCase, a: dict[str, str]) -> bool:
    return a.get("if_exists_clause") == "present"


def _cascade_clause(a: dict[str, str]) -> str:
    cascade = a.get("cascade_restrict", "default_restrict")
    if cascade == "explicit_cascade":
        return "CASCADE"
    if cascade == "explicit_restrict":
        return "RESTRICT"
    return ""  # default_restrict: RESTRICT is the default


def _effective_role(
    case: DropTextSearchDictionaryFactorCase, a: dict[str, str], p: str
) -> str:
    """The session role under which the target DROP runs."""

    if a.get("authorization_path") == "non_owner":
        return f"{p}actor"
    return ""


def _needs_dependent(
    case: DropTextSearchDictionaryFactorCase, a: dict[str, str]
) -> bool:
    """Whether a dependent text search configuration fixture must be created."""

    if case.kind == "EXT":
        if not _dict_created(case, a):
            return False
        return a.get("dependency_context") == "config_using_dict"
    if (case.factor_key, case.factor_value) in _DEPENDENCY_PRIMARIES:
        return True
    if not _dict_created(case, a):
        return False
    return a.get("dependency_context") == "config_using_dict"


def _dict_absent_after(
    case: DropTextSearchDictionaryFactorCase, a: dict[str, str]
) -> bool:
    """Whether the target dictionary is absent AFTER the target statement."""

    if case.kind == "RISK":
        return case.factor_value == "commit"
    if not _dict_created(case, a):
        return True
    if case.outcome == "success":
        return True
    return False


def _probe_select(
    case: DropTextSearchDictionaryFactorCase, a: dict[str, str], p: str
) -> str:
    dict_probe = _dict_probe(case, a, p)
    absent = _dict_absent_after(case, a)
    comparator = "= 0" if absent else "> 0"
    alias = "dict_absent" if absent else "dict_present"
    return (
        f"SELECT count(*) {comparator} AS {alias} "
        "FROM pg_catalog.pg_ts_dict "
        f"WHERE dictname = '{dict_probe}' "
        "ORDER BY count(*) LIMIT 1;"
    )


def _role_names(
    case: DropTextSearchDictionaryFactorCase, p: str, effective: str
) -> tuple[str, ...]:
    roles: list[str] = []
    if effective == f"{p}actor":
        roles.append(f"{p}actor")
    return tuple(roles)


def _resolve_case(case: DropTextSearchDictionaryFactorCase) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    dict_ref = _dict_ref(case, a, p)
    dict_created = _dict_created(case, a)
    needs_dep = _needs_dependent(case, a)

    setup: list[str] = []
    locus = "target.dictionary"

    # --- role fixtures (CREATE only; SET ROLE deferred to after the dict) ---
    effective = _effective_role(case, a, p)
    if effective:
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"

    # --- the dictionary fixture (as superuser, before SET ROLE) ---
    if dict_created:
        setup.append(
            f"CREATE TEXT SEARCH DICTIONARY {dict_ref} (TEMPLATE = simple);"
        )
        if locus == "target.dictionary":
            locus = "fixture.dictionary"

    # --- dependent configuration fixture (as superuser, before SET ROLE) ----
    if needs_dep:
        setup.append(
            f"CREATE TEXT SEARCH CONFIGURATION {p}cfg (COPY = simple);"
        )
        setup.append(
            f"ALTER TEXT SEARCH CONFIGURATION {p}cfg "
            f"ALTER MAPPING FOR asciiword WITH {dict_ref};"
        )
        locus = "fixture.dependency_state"

    # --- arm the non-superuser role (AFTER dictionary creation) ------------
    if effective:
        setup.append(f"SET ROLE {p}actor;")
    if_exists = "IF EXISTS " if _if_exists_present(case, a) else ""
    cascade = _cascade_clause(a)
    target = f"DROP TEXT SEARCH DICTIONARY {if_exists}{dict_ref}"
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
    # DROP OWNED BY is unreachable in pre-cleanup: the actor role is
    # created by setup, so on a fresh database the role does not exist
    # yet at pre-cleanup time and DROP OWNED BY would crash
    # (ON_ERROR_STOP=1) before the target statement reaches execution.
    # Pre-cleanup drops roles via DROP ROLE IF EXISTS only; the post-target
    # cleanup runs DROP OWNED BY then DROP ROLE IF EXISTS once setup has
    # created the role.
    roles = _role_names(case, p, effective)
    role_list = list(roles)
    specs: list[DropSpec] = []
    if needs_dep:
        specs.append(DropSpec("TEXT SEARCH CONFIGURATION", f"{p}cfg"))
    specs.append(DropSpec("TEXT SEARCH DICTIONARY", dict_ref))
    pre_bookend = build_pre_cleanup(specs=tuple(specs), roles=role_list)
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


def resolve_drop_text_search_dictionary_factor_witness(
    case: DropTextSearchDictionaryFactorCase
    | DropTextSearchDictionaryFactorExtensionCase,
    repository_root: Path,
) -> DropTextSearchDictionaryFactorWitness:
    """Return the byte-level witness fragments for one case."""

    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return DropTextSearchDictionaryFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_drop_text_search_dictionary(sql: str) -> int:
    """Count the single credited DROP TEXT SEARCH DICTIONARY inside the fence."""

    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(r"(?im)^\s*DROP\s+TEXT\s+SEARCH\s+DICTIONARY\b", region)
    )


def _header(case: DropTextSearchDictionaryFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : DROP TEXT SEARCH DICTIONARY {case.factor_key}={case.factor_value}",
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


def render_drop_text_search_dictionary_factor_case(
    case: DropTextSearchDictionaryFactorCase
    | DropTextSearchDictionaryFactorExtensionCase,
    repository_root: Path,
) -> str:
    """Render one complete, deterministic DROP TEXT SEARCH DICTIONARY regress program."""

    rc = _as_render_case(case)
    resolved = _resolve_case(rc)
    lines: list[str] = list(_header(rc))
    lines.append("-- 1. 清理本编号对象，保证脚本可重复执行。")
    lines.extend(resolved.pre_cleanup_lines)
    lines.append("\\set ON_ERROR_STOP on")
    lines.append("-- 2. 创建完整本地字典和因子专用夹具。")
    lines.extend(resolved.setup_lines)
    if resolved.on_error_off:
        lines.append("\\set ON_ERROR_STOP off")
    lines.append("-- 3. 执行唯一获得覆盖信用的 DROP TEXT SEARCH DICTIONARY。")
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


def generate_drop_text_search_dictionary_factor_programs(
    baseline_plan: DropTextSearchDictionaryFactorLoopPlan,
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
    case: DropTextSearchDictionaryFactorCase
    | DropTextSearchDictionaryFactorExtensionCase,
    out: Path,
) -> None:
    text = render_drop_text_search_dictionary_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


__all__ = [
    "DropTextSearchDictionaryFactorRenderError",
    "DropTextSearchDictionaryFactorWitness",
    "count_primary_drop_text_search_dictionary",
    "generate_drop_text_search_dictionary_factor_programs",
    "render_drop_text_search_dictionary_factor_case",
    "resolve_drop_text_search_dictionary_factor_witness",
]
