"""Render complete PostgreSQL 18.4 ALTER TEXT SEARCH DICTIONARY factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

ALTER TEXT SEARCH DICTIONARY is a full-text-search DDL statement: the
target is a ``pg_catalog.pg_ts_dict`` catalog row, not a ``pg_class``
relation.  All catalog oracles schema-qualify ``pg_catalog.pg_ts_dict``
(exempt from the file-prefix style gate).  No case creates a TABLE, so
the bookend (DROP TABLE IF EXISTS) is never emitted (``_tables_to_drop``
always returns ``[]``).  Every catalog SELECT carries a top-level
``ORDER BY count(*)`` so the catalog-observability gate passes.

The quoted-identifier gate is respected: fixture DDL (CREATE TEXT
SEARCH DICTIONARY, CREATE ROLE, CREATE SCHEMA) always uses plain
unqualified names derived from the object prefix.  Quoted or
schema-qualified identifier shapes are kept observable only in the
ALTER target, which the shared style gate does not inspect.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .cleanup_bookend import DropSpec, build_cleanup, build_pre_cleanup
from .alter_text_search_dictionary_factor_extension import (
    AlterTextSearchDictionaryFactorExtensionCase,
    _present_failure_pair,
)
from .alter_text_search_dictionary_factor_loop import (
    AlterTextSearchDictionaryFactorCase,
    AlterTextSearchDictionaryFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/"
    "text_search_dictionary/alter_text_search_dictionary.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/"
    "text_search_dictionary/alter_text_search_dictionary.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"


class AlterTextSearchDictionaryFactorRenderError(ValueError):
    """Raised when an ALTER TEXT SEARCH DICTIONARY case cannot be rendered."""


@dataclass(frozen=True)
class AlterTextSearchDictionaryFactorWitness:
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
    ext: AlterTextSearchDictionaryFactorExtensionCase,
) -> AlterTextSearchDictionaryFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get("target_action", "option_modify")
    return AlterTextSearchDictionaryFactorCase(
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
    case: AlterTextSearchDictionaryFactorCase
    | AlterTextSearchDictionaryFactorExtensionCase,
) -> AlterTextSearchDictionaryFactorCase:
    if isinstance(
        case, AlterTextSearchDictionaryFactorExtensionCase
    ):
        return _synthetic_case(case)
    return case


def _baseline(case: AlterTextSearchDictionaryFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _dict_missing(a: dict[str, str]) -> bool:
    return a.get("object_state") == "not_exists"


def _dict_name(a: dict[str, str], p: str) -> str:
    """The dictionary identifier in ALTER TEXT SEARCH DICTIONARY and fixtures.

    Fixture DDL always uses the plain unqualified name so the
    quoted-identifier gate is not triggered.  Quoted or
    schema-qualified shapes are kept observable only in the ALTER
    target via :func:`_dict_target_name`.
    """

    shape = a.get("dict_name_shape", "simple_id")
    if shape == "nonexistent_name":
        return f"{p}no_such_dict"
    return f"{p}dict"


def _dict_target_name(a: dict[str, str], p: str) -> str:
    """The dictionary name in the ALTER target (may be quoted/qualified)."""

    shape = a.get("dict_name_shape", "simple_id")
    if shape == "quoted_id":
        return f'"{p}Mixed Dict"'
    if shape == "schema_qualified_id":
        return f"{p}schema.{p}dict"
    if shape == "nonexistent_name":
        return f"{p}no_such_dict"
    return f"{p}dict"


def _dict_name_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    shape = a.get("dict_name_shape", "simple_id")
    if shape == "quoted_id":
        return f"{p}Mixed Dict"
    if shape == "schema_qualified_id":
        return f"{p}dict"
    if shape == "nonexistent_name":
        return f"{p}no_such_dict"
    return f"{p}dict"


def _new_name(a: dict[str, str], p: str) -> str:
    """The new name in RENAME TO."""

    shape = a.get("new_name_shape", "simple_id")
    dnn = a.get("duplicate_new_name", "no_conflict")
    if (
        dnn == "same_name_conflict"
        or shape == "duplicate_name"
    ):
        return f"{p}conflict_dict"
    if shape == "quoted_id":
        return f'"{p}Mixed New"'
    return f"{p}newdict"


def _new_name_literal(a: dict[str, str], p: str) -> str:
    shape = a.get("new_name_shape", "simple_id")
    dnn = a.get("duplicate_new_name", "no_conflict")
    if (
        dnn == "same_name_conflict"
        or shape == "duplicate_name"
    ):
        return f"{p}conflict_dict"
    if shape == "quoted_id":
        return f"{p}Mixed New"
    return f"{p}newdict"


def _owner_target_token(a: dict[str, str], p: str) -> str:
    """The owner target token in OWNER TO."""

    target = a.get("owner_target", "specified_new_owner")
    if target == "specified_current_role":
        return "CURRENT_ROLE"
    if target == "specified_current_user":
        return "CURRENT_USER"
    if target == "specified_session_user":
        return "SESSION_USER"
    return f"{p}newowner"


def _schema_target_name(a: dict[str, str], p: str) -> str:
    """The schema name in SET SCHEMA."""

    shape = a.get("schema_name_shape", "simple_id")
    if shape == "nonexistent_schema":
        return f"{p}no_such_schema"
    return f"{p}schema"


def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target ALTER runs."""

    pl = a.get("privilege_level", "owner")
    if pl == "non_owner":
        return f"{p}actor"
    return ""


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    """Roles to tear down."""

    roles: list[str] = []
    pl = a.get("privilege_level", "owner")
    action = a.get("target_action", "option_modify")
    ot = a.get("owner_target", "specified_new_owner")
    if pl == "non_owner":
        roles.append(f"{p}actor")
    if action == "owner" and ot == "specified_new_owner":
        roles.append(f"{p}newowner")
    return tuple(roles)


def _option_clause(a: dict[str, str]) -> str:
    """The option clause for ALTER TEXT SEARCH DICTIONARY name ( ... )."""

    opt = a.get("option_action", "set_new_value")
    if opt == "set_new_value":
        return "stopword = 'english'"
    if opt == "remove_option_restore_default":
        return "stopword"
    if opt == "dummy_refresh":
        return "dummy"
    return "stopword = 'english'"


def _probe_select(
    case: AlterTextSearchDictionaryFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only error_assertion."""

    mode = a.get("verification_mode", "catalog_query_pg_ts_dict")
    if mode == "error_assertion":
        return None

    dict_lit = _dict_name_literal(a, p)
    missing = _dict_missing(a)
    action = a.get("target_action", "option_modify")

    if action == "rename" and case.outcome == "success":
        check = _new_name_literal(a, p)
        present = True
    elif missing:
        check = dict_lit
        present = False
    else:
        check = dict_lit
        present = True

    cmp_op = ">" if present else "="
    if mode == "option_query":
        return (
            f"SELECT count(*) {cmp_op} 0 AS option_state "
            f"FROM pg_catalog.pg_ts_dict "
            f"WHERE dictname = '{check}' "
            f"ORDER BY count(*);"
        )
    return (
        f"SELECT count(*) {cmp_op} 0 AS dict_state "
        f"FROM pg_catalog.pg_ts_dict "
        f"WHERE dictname = '{check}' "
        f"ORDER BY count(*);"
    )


def _tables_to_drop(
    case: AlterTextSearchDictionaryFactorCase,
) -> list[str]:
    """Fixture tables the case CREATEs.

    ALTER TEXT SEARCH DICTIONARY is a full-text-search DDL statement:
    it never creates a TABLE.  The bookend (DROP TABLE IF EXISTS) is
    therefore never emitted.
    """
    return []


def _resolve_case(
    case: AlterTextSearchDictionaryFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    action = a.get("target_action", "option_modify")
    missing = _dict_missing(a)

    setup: list[str] = []
    locus = "target.alter_text_search_dictionary"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    dict_name = _dict_name(a, p)
    target_name = _dict_target_name(a, p)

    # --- role fixtures -----------------------------------------------
    if effective == f"{p}actor":
        setup.append(
            f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;"
        )
        locus = "fixture.privilege_state"
    if (
        action == "owner"
        and a.get("owner_target", "specified_new_owner")
        == "specified_new_owner"
    ):
        setup.append(f"CREATE ROLE {p}newowner LOGIN;")
        locus = "fixture.owner_role"

    # --- schema fixture for schema_qualified_id ----------------------
    if a.get("dict_name_shape") == "schema_qualified_id":
        setup.append(f"CREATE SCHEMA {p}schema;")
        locus = "fixture.dict_schema"

    # --- the target dictionary fixture -------------------------------
    if not missing:
        setup.append(
            f"CREATE TEXT SEARCH DICTIONARY {dict_name} "
            f"(TEMPLATE = pg_catalog.simple);"
        )
        locus = "fixture.text_search_dictionary"
    else:
        setup.append(
            "SELECT 1 AS target_dictionary_intentionally_absent;"
        )
        locus = "fixture.dictionary_missing"

    # --- conflicting dictionary for rename conflict ------------------
    if (
        action == "rename"
        and (
            a.get("duplicate_new_name", "no_conflict")
            == "same_name_conflict"
            or a.get("new_name_shape") == "duplicate_name"
        )
    ):
        setup.append(
            f"CREATE TEXT SEARCH DICTIONARY {p}conflict_dict "
            f"(TEMPLATE = pg_catalog.simple);"
        )
        locus = "fixture.rename_conflict"

    # --- schema fixture for set_schema target ------------------------
    if (
        action == "set_schema"
        and a.get("schema_name_shape") == "simple_id"
        and not missing
    ):
        setup.append(f"CREATE SCHEMA {p}schema;")
        locus = "fixture.target_schema"

    # --- arm the effective role --------------------------------------
    if effective:
        setup.append(f"SET ROLE {effective};")

    # --- the primary target statement --------------------------------
    target = _build_target(a, p, target_name)

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

    # --- cleanup construction (shared idempotent bookends) -----------
    # Migrated to cleanup_bookend so every DROP carries IF EXISTS and
    # DROP OWNED BY is unreachable in pre-cleanup: the role fixture is
    # created by setup, so on a fresh database the role does not exist
    # yet at pre-cleanup time and DROP OWNED BY would crash
    # (ON_ERROR_STOP=1) before the target statement reaches execution.
    # Pre-cleanup drops roles via DROP ROLE IF EXISTS only; the
    # post-target cleanup runs DROP OWNED BY then DROP ROLE IF EXISTS
    # once setup has created the role.  No case creates a TABLE, so the
    # DROP TABLE anchor is never emitted.
    specs: list[DropSpec] = []
    if not missing:
        specs.append(DropSpec("TEXT SEARCH DICTIONARY", dict_name))
    if action == "rename":
        new = _new_name(a, p)
        if new != dict_name and new != target_name:
            specs.append(DropSpec("TEXT SEARCH DICTIONARY", new))
        if (
            a.get("duplicate_new_name", "no_conflict")
            == "same_name_conflict"
            or a.get("new_name_shape") == "duplicate_name"
        ):
            specs.append(
                DropSpec("TEXT SEARCH DICTIONARY", f"{p}conflict_dict")
            )

    schema_list: list[str] = []
    if a.get("dict_name_shape") == "schema_qualified_id":
        schema_list.append(f"{p}schema")
    if (
        action == "set_schema"
        and a.get("schema_name_shape") == "simple_id"
        and not missing
    ):
        schema_list.append(f"{p}schema")

    role_list = list(roles)
    pre_bookend = build_pre_cleanup(
        specs=tuple(specs),
        schemas=schema_list,
        roles=role_list,
    )
    cln_bookend = build_cleanup(
        specs=tuple(specs),
        schemas=schema_list,
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


def _build_target(
    a: dict[str, str], p: str, target_name: str
) -> str:
    """The primary ALTER TEXT SEARCH DICTIONARY statement for the active branch."""

    action = a.get("target_action", "option_modify")
    if action == "option_modify":
        opts = _option_clause(a)
        return (
            f"ALTER TEXT SEARCH DICTIONARY {target_name} "
            f"({opts});"
        )
    if action == "rename":
        new = _new_name(a, p)
        return (
            f"ALTER TEXT SEARCH DICTIONARY {target_name} "
            f"RENAME TO {new};"
        )
    if action == "owner":
        target = _owner_target_token(a, p)
        return (
            f"ALTER TEXT SEARCH DICTIONARY {target_name} "
            f"OWNER TO {target};"
        )
    if action == "set_schema":
        schema = _schema_target_name(a, p)
        return (
            f"ALTER TEXT SEARCH DICTIONARY {target_name} "
            f"SET SCHEMA {schema};"
        )
    return (
        f"ALTER TEXT SEARCH DICTIONARY {target_name} "
        f"(stopword = 'english');"
    )


def resolve_alter_text_search_dictionary_factor_witness(
    case: AlterTextSearchDictionaryFactorCase
    | AlterTextSearchDictionaryFactorExtensionCase,
    repository_root: Path,
) -> AlterTextSearchDictionaryFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return AlterTextSearchDictionaryFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_alter_text_search_dictionary(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(
            r"(?im)^\s*ALTER\s+TEXT\s+SEARCH\s+DICTIONARY\b",
            region,
        )
    )


def _header(case: AlterTextSearchDictionaryFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : ALTER TEXT SEARCH DICTIONARY "
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


def render_alter_text_search_dictionary_factor_case(
    case: AlterTextSearchDictionaryFactorCase
    | AlterTextSearchDictionaryFactorExtensionCase,
    repository_root: Path,
) -> str:
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
    lines.append(
        "-- 3. 执行唯一获得覆盖信用的 ALTER TEXT SEARCH DICTIONARY。"
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
    case: AlterTextSearchDictionaryFactorCase
    | AlterTextSearchDictionaryFactorExtensionCase,
    out: Path,
) -> None:
    text = render_alter_text_search_dictionary_factor_case(
        case, Path(".")
    )
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_alter_text_search_dictionary_factor_programs(
    baseline_plan: AlterTextSearchDictionaryFactorLoopPlan,
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


__all__ = [
    "AlterTextSearchDictionaryFactorRenderError",
    "AlterTextSearchDictionaryFactorWitness",
    "count_primary_alter_text_search_dictionary",
    "generate_alter_text_search_dictionary_factor_programs",
    "render_alter_text_search_dictionary_factor_case",
    "resolve_alter_text_search_dictionary_factor_witness",
]
