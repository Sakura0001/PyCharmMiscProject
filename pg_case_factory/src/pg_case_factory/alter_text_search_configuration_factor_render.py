"""Render complete PostgreSQL 18.4 ALTER TEXT SEARCH CONFIGURATION factor-loop programs.

Every planned obligation becomes one self-contained, deterministic SQL
file assembled from a single :func:`_resolve_case` plan so the
byte-level witness validator (which re-renders and compares) can never
diverge from the bytes actually written.

ALTER TEXT SEARCH CONFIGURATION is a text-search DDL statement: the
target is a ``pg_catalog.pg_ts_config`` catalog row, not a ``pg_class``
relation.  All catalog oracles schema-qualify ``pg_catalog.pg_ts_config``
/ ``pg_catalog.pg_ts_config_map`` (exempt from the file-prefix style
gate).  No case creates a TABLE, so the bookend (DROP TABLE IF EXISTS) is
never emitted (``_tables_to_drop`` always returns ``[]``).  Every
catalog SELECT carries a top-level ``ORDER BY count(*)`` so the
catalog-observability gate passes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .alter_text_search_configuration_factor_extension import (
    AlterTextSearchConfigurationFactorExtensionCase,
    _present_failure_pair,
)
from .alter_text_search_configuration_factor_loop import (
    AlterTextSearchConfigurationFactorCase,
    AlterTextSearchConfigurationFactorLoopPlan,
)

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"

_DOC_SOURCE = (
    "skills/pg-sql-generation/references/statements/ddl/"
    "text_search_configuration/alter_text_search_configuration.md"
)
_FACTOR_SOURCE = (
    "skills/pg-sql-generation/references/combinations/ddl/"
    "text_search_configuration/alter_text_search_configuration.yaml"
)
_AUTHOR = "codex"
_CREATE_AT = "2026-08-20"
_VERSION = "1.0"
_FE = "PG18-STATEMENT-FACTOR-LOOP"

_VALID_TOKEN = "word"
_NOT_MAPPED_TOKEN = "host"
_INVALID_TOKEN = "bogus_tok"
_TS_PARSER = "default"
_TS_TEMPLATE = "simple"


class AlterTextSearchConfigurationFactorRenderError(ValueError):
    """Raised when an ALTER TEXT SEARCH CONFIGURATION case cannot be rendered."""


@dataclass(frozen=True)
class AlterTextSearchConfigurationFactorWitness:
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
    ext: AlterTextSearchConfigurationFactorExtensionCase,
) -> AlterTextSearchConfigurationFactorCase:
    """Build a byte-safe baseline-shaped case from an extension case."""

    assignment = dict(ext.factor_assignment)
    pair = _present_failure_pair(assignment)
    if pair is not None:
        factor_key, factor_value = pair
    else:
        factor_key = "target_action"
        factor_value = assignment.get("target_action", "rename")
    return AlterTextSearchConfigurationFactorCase(
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
    case: AlterTextSearchConfigurationFactorCase
    | AlterTextSearchConfigurationFactorExtensionCase,
) -> AlterTextSearchConfigurationFactorCase:
    if isinstance(
        case, AlterTextSearchConfigurationFactorExtensionCase
    ):
        return _synthetic_case(case)
    return case


def _baseline(case: AlterTextSearchConfigurationFactorCase) -> dict[str, str]:
    return dict(case.baseline_assignments)


def _config_missing(a: dict[str, str]) -> bool:
    return a.get("object_state") == "not_exists"


def _config_name(a: dict[str, str], p: str) -> str:
    """The configuration identifier in ALTER TEXT SEARCH CONFIGURATION."""

    shape = a.get("config_name_shape", "simple_id")
    if shape == "schema_qualified_id":
        return f"public.{p}cfg"
    if shape == "quoted_id":
        return f'"{p}qcfg"'
    if shape == "reserved_word_as_name":
        return f'"{p}select"'
    if shape == "nonexistent_name":
        return f"{p}nosuchcfg"
    return f"{p}cfg"


def _config_name_literal(a: dict[str, str], p: str) -> str:
    """The unquoted catalog string literal for oracle queries."""

    shape = a.get("config_name_shape", "simple_id")
    if shape == "schema_qualified_id":
        return f"{p}cfg"
    if shape == "quoted_id":
        return f"{p}qcfg"
    if shape == "reserved_word_as_name":
        return f"{p}select"
    if shape == "nonexistent_name":
        return f"{p}nosuchcfg"
    return f"{p}cfg"


def _new_name(a: dict[str, str], p: str) -> str:
    """The new name in RENAME TO."""

    shape = a.get("new_name_shape", "simple_id")
    dnn = a.get("duplicate_new_name", "no_conflict")
    if shape == "duplicate_name" or dnn == "same_name_conflict":
        return f"{p}conflictcfg"
    if shape == "quoted_id":
        return f'"{p}qnewcfg"'
    return f"{p}newcfg"


def _new_name_literal(a: dict[str, str], p: str) -> str:
    shape = a.get("new_name_shape", "simple_id")
    dnn = a.get("duplicate_new_name", "no_conflict")
    if shape == "duplicate_name" or dnn == "same_name_conflict":
        return f"{p}conflictcfg"
    if shape == "quoted_id":
        return f"{p}qnewcfg"
    return f"{p}newcfg"


def _owner_target(a: dict[str, str], p: str) -> str:
    """The owner target token in OWNER TO."""

    target = a.get("owner_target", "specified_new_owner")
    if target == "specified_current_role":
        return "CURRENT_ROLE"
    if target == "specified_current_user":
        return "CURRENT_USER"
    if target == "specified_session_user":
        return "SESSION_USER"
    return f"{p}newowner"


def _target_dictionary(a: dict[str, str], p: str) -> str:
    """The dictionary name referenced in ADD/ALTER MAPPING WITH."""

    shape = a.get("dictionary_name_shape", "simple_id")
    if shape == "schema_qualified_id":
        return f"public.{p}dict"
    if shape == "nonexistent_name":
        return f"{p}nosuchdict"
    return f"{p}dict"


def _token_type(a: dict[str, str]) -> str:
    """The token type in FOR clause."""

    ttns = a.get("token_type_name_shape", "valid_token_type")
    if ttns == "invalid_token_type":
        return _INVALID_TOKEN
    tte = a.get("token_type_existence", "token_type_mapped")
    if tte == "token_type_not_mapped":
        return _NOT_MAPPED_TOKEN
    return _VALID_TOKEN


def _role_names(a: dict[str, str], p: str) -> tuple[str, ...]:
    """Roles to tear down."""

    roles: list[str] = []
    pl = a.get("privilege_level", "owner")
    action = a.get("target_action", "rename")
    ot = a.get("owner_target", "specified_new_owner")
    re_ = a.get("role_existence", "role_exists")
    if pl == "non_owner":
        roles.append(f"{p}actor")
    if action == "owner" and ot == "specified_new_owner":
        roles.append(f"{p}newowner")
    return tuple(roles)


def _effective_role(a: dict[str, str], p: str) -> str:
    """The session role under which the target ALTER runs."""

    pl = a.get("privilege_level", "owner")
    if pl == "non_owner":
        return f"{p}actor"
    return ""


def _needs_pre_mapping(a: dict[str, str]) -> bool:
    """Whether the fixture config needs a pre-existing mapping."""

    action = a.get("target_action", "rename")
    tte = a.get("token_type_existence", "token_type_mapped")
    if action in ("alter_mapping", "alter_mapping_replace",
                   "alter_mapping_for_replace"):
        return True
    if action == "drop_mapping" and tte == "token_type_mapped":
        return True
    return False


def _needs_dictionary_fixture(a: dict[str, str]) -> bool:
    """Whether a text search dictionary fixture is needed."""

    action = a.get("target_action", "rename")
    de = a.get("dictionary_existence", "dictionary_exists")
    if action in ("add_mapping", "alter_mapping"):
        return de == "dictionary_exists"
    if action in ("alter_mapping_replace", "alter_mapping_for_replace"):
        return de == "dictionary_exists"
    return False


def _probe_select(
    case: AlterTextSearchConfigurationFactorCase,
    a: dict[str, str],
    p: str,
) -> str | None:
    """Catalog-audit oracle, or None for sqlstate-only error_assertion."""

    mode = a.get("verification_mode", "catalog_query_pg_ts_config")
    if mode == "error_assertion":
        return None

    action = a.get("target_action", "rename")
    missing = _config_missing(a)

    if action == "rename" and case.outcome == "success":
        check = _new_name_literal(a, p)
        present = True
    elif missing:
        check = _config_name_literal(a, p)
        present = False
    else:
        check = _config_name_literal(a, p)
        present = True

    cmp_op = ">" if present else "="
    if (
        mode == "mapping_query"
        and action in (
            "add_mapping", "alter_mapping",
            "alter_mapping_replace",
            "alter_mapping_for_replace",
            "drop_mapping",
        )
    ):
        return (
            f"SELECT count(*) {cmp_op} 0 AS mapping_state "
            f"FROM pg_catalog.pg_ts_config_map "
            f"WHERE mapcfg = (SELECT oid FROM "
            f"pg_catalog.pg_ts_config "
            f"WHERE cfgname = '{check}') "
            f"ORDER BY count(*);"
        )
    return (
        f"SELECT count(*) {cmp_op} 0 AS config_state "
        f"FROM pg_catalog.pg_ts_config "
        f"WHERE cfgname = '{check}' "
        f"ORDER BY count(*);"
    )


def _tables_to_drop(
    case: AlterTextSearchConfigurationFactorCase,
) -> list[str]:
    """Fixture tables the case CREATEs.

    ALTER TEXT SEARCH CONFIGURATION is a text-search DDL statement: it
    never creates a TABLE.  The bookend (DROP TABLE IF EXISTS) is
    therefore never emitted.
    """
    return []


def _resolve_case(
    case: AlterTextSearchConfigurationFactorCase,
) -> _CasePlan:
    a = _baseline(case)
    p = case.object_prefix
    action = a.get("target_action", "rename")
    missing = _config_missing(a)

    setup: list[str] = []
    locus = "target.alter_text_search_configuration"

    effective = _effective_role(a, p)
    roles = _role_names(a, p)
    cfg = _config_name(a, p)

    # --- role fixtures -----------------------------------------------
    if effective == f"{p}actor":
        setup.append(f"CREATE ROLE {p}actor LOGIN NOSUPERUSER;")
        locus = "fixture.privilege_state"
    if (
        action == "owner"
        and a.get("owner_target", "specified_new_owner")
        == "specified_new_owner"
        and a.get("role_existence", "role_exists") == "role_exists"
    ):
        setup.append(f"CREATE ROLE {p}newowner LOGIN;")
        locus = "fixture.owner_role"

    # --- schema fixture (set_schema) ---------------------------------
    if action == "set_schema":
        se = a.get("schema_existence", "schema_exists")
        if se == "schema_exists":
            setup.append(f"CREATE SCHEMA {p}schema;")
            locus = "fixture.target_schema"

    # --- the target configuration fixture ----------------------------
    if not missing:
        setup.append(
            f"CREATE TEXT SEARCH CONFIGURATION {cfg} "
            f"(parser = {_TS_PARSER});"
        )
        locus = "fixture.configuration"
    else:
        setup.append(
            "SELECT 1 AS target_config_intentionally_absent;"
        )
        locus = "fixture.configuration_missing"

    # --- dictionary fixtures -----------------------------------------
    if _needs_dictionary_fixture(a):
        setup.append(
            f"CREATE TEXT SEARCH DICTIONARY {p}dict "
            f"(template = {_TS_TEMPLATE});"
        )
        locus = "fixture.dictionary"
    if action in ("alter_mapping_replace",
                  "alter_mapping_for_replace"):
        if a.get("dictionary_existence") == "dictionary_exists":
            setup.append(
                f"CREATE TEXT SEARCH DICTIONARY {p}olddict "
                f"(template = {_TS_TEMPLATE});"
            )
            setup.append(
                f"CREATE TEXT SEARCH DICTIONARY {p}newdict "
                f"(template = {_TS_TEMPLATE});"
            )
            setup.append(
                f"ALTER TEXT SEARCH CONFIGURATION {cfg} "
                f"ADD MAPPING FOR {_VALID_TOKEN} WITH {p}olddict;"
            )
            locus = "fixture.replace_mapping"
    elif _needs_pre_mapping(a):
        if a.get("dictionary_existence") == "dictionary_exists":
            setup.append(
                f"CREATE TEXT SEARCH DICTIONARY {p}dict "
                f"(template = {_TS_TEMPLATE});"
            )
            setup.append(
                f"ALTER TEXT SEARCH CONFIGURATION {cfg} "
                f"ADD MAPPING FOR {_VALID_TOKEN} WITH {p}dict;"
            )
            locus = "fixture.pre_mapping"

    # --- conflicting config for rename conflict ----------------------
    if (
        action == "rename"
        and a.get("duplicate_new_name", "no_conflict")
        == "same_name_conflict"
    ):
        setup.append(
            f"CREATE TEXT SEARCH CONFIGURATION {p}conflictcfg "
            f"(parser = {_TS_PARSER});"
        )
        locus = "fixture.rename_conflict"

    # --- arm the effective role --------------------------------------
    if effective:
        setup.append(f"SET ROLE {effective};")

    # --- the primary target statement --------------------------------
    target = _build_target(a, p, cfg)

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
    configs_to_drop: list[str] = []
    if not missing:
        configs_to_drop.append(cfg)
    if action == "rename":
        new = _new_name(a, p)
        if new != cfg:
            configs_to_drop.append(new)
        if (
            a.get("duplicate_new_name", "no_conflict")
            == "same_name_conflict"
        ):
            configs_to_drop.append(f"{p}conflictcfg")
    if action == "set_schema":
        se = a.get("schema_existence", "schema_exists")
        if se == "schema_exists" and not missing:
            configs_to_drop.append(f"{p}schema.{p}cfg")

    dicts_to_drop: list[str] = []
    if _needs_dictionary_fixture(a) or _needs_pre_mapping(a):
        dicts_to_drop.append(f"{p}dict")
    if action in ("alter_mapping_replace",
                  "alter_mapping_for_replace"):
        if a.get("dictionary_existence") == "dictionary_exists":
            dicts_to_drop.append(f"{p}olddict")
            dicts_to_drop.append(f"{p}newdict")

    schemas_to_drop: list[str] = []
    if action == "set_schema":
        se = a.get("schema_existence", "schema_exists")
        if se == "schema_exists":
            schemas_to_drop.append(f"{p}schema")

    role_drops = [
        statement
        for role in roles
        for statement in (
            f"DROP OWNED BY {role} CASCADE;",
            f"DROP ROLE IF EXISTS {role};",
        )
    ]

    config_drops = [
        f"DROP TEXT SEARCH CONFIGURATION IF EXISTS {name};"
        for name in configs_to_drop
    ]
    dict_drops = [
        f"DROP TEXT SEARCH DICTIONARY IF EXISTS {name};"
        for name in dicts_to_drop
    ]
    schema_drops = [
        f"DROP SCHEMA IF EXISTS {name} CASCADE;"
        for name in schemas_to_drop
    ]

    # pre-cleanup: configs, dicts, schemas, roles
    pre_cleanup: list[str] = []
    pre_cleanup.extend(config_drops)
    pre_cleanup.extend(dict_drops)
    pre_cleanup.extend(schema_drops)
    pre_cleanup.extend(role_drops)
    if not pre_cleanup:
        pre_cleanup.append("SELECT 1 AS residual_check_no_objects;")

    # cleanup: RESET ROLE, configs, dicts, schemas, roles
    cleanup: list[str] = []
    if effective:
        cleanup.append("RESET ROLE;")
    cleanup.extend(config_drops)
    cleanup.extend(dict_drops)
    cleanup.extend(schema_drops)
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


def _build_target(
    a: dict[str, str], p: str, cfg: str
) -> str:
    """The primary ALTER TEXT SEARCH CONFIGURATION statement for the active branch."""

    action = a.get("target_action", "rename")
    tok = _token_type(a)
    if action == "add_mapping":
        d = _target_dictionary(a, p)
        return (
            f"ALTER TEXT SEARCH CONFIGURATION {cfg} "
            f"ADD MAPPING FOR {tok} WITH {d};"
        )
    if action == "alter_mapping":
        d = _target_dictionary(a, p)
        return (
            f"ALTER TEXT SEARCH CONFIGURATION {cfg} "
            f"ALTER MAPPING FOR {tok} WITH {d};"
        )
    if action == "alter_mapping_replace":
        return (
            f"ALTER TEXT SEARCH CONFIGURATION {cfg} "
            f"ALTER MAPPING REPLACE {p}olddict WITH {p}newdict;"
        )
    if action == "alter_mapping_for_replace":
        return (
            f"ALTER TEXT SEARCH CONFIGURATION {cfg} "
            f"ALTER MAPPING FOR {tok} REPLACE {p}olddict "
            f"WITH {p}newdict;"
        )
    if action == "drop_mapping":
        iec = a.get("if_exists_clause", "omitted")
        if_exists = " IF EXISTS" if iec == "present" else ""
        return (
            f"ALTER TEXT SEARCH CONFIGURATION {cfg} "
            f"DROP MAPPING{if_exists} FOR {tok};"
        )
    if action == "rename":
        new = _new_name(a, p)
        return (
            f"ALTER TEXT SEARCH CONFIGURATION {cfg} "
            f"RENAME TO {new};"
        )
    if action == "owner":
        target = _owner_target(a, p)
        return (
            f"ALTER TEXT SEARCH CONFIGURATION {cfg} "
            f"OWNER TO {target};"
        )
    if action == "set_schema":
        se = a.get("schema_existence", "schema_exists")
        if se == "schema_not_exists":
            schema_name = f"{p}nosuchschema"
        else:
            schema_name = f"{p}schema"
        return (
            f"ALTER TEXT SEARCH CONFIGURATION {cfg} "
            f"SET SCHEMA {schema_name};"
        )
    return f"ALTER TEXT SEARCH CONFIGURATION {cfg} RENAME TO {p}newcfg;"


def resolve_alter_text_search_configuration_factor_witness(
    case: AlterTextSearchConfigurationFactorCase
    | AlterTextSearchConfigurationFactorExtensionCase,
    repository_root: Path,
) -> AlterTextSearchConfigurationFactorWitness:
    rc = _as_render_case(case)
    plan = _resolve_case(rc)
    return AlterTextSearchConfigurationFactorWitness(
        primary_obligation_id=rc.primary_obligation_id,
        target_sql_fragment=plan.target_fragment,
        outcome=rc.outcome,
        expected_sqlstate=rc.expected_sqlstate,
        setup_sql=plan.setup_lines,
        oracle_sql=plan.assert_lines,
        cleanup_sql=plan.cleanup_lines,
        semantic_locus=plan.semantic_locus,
    )


def count_primary_alter_text_search_configuration(sql: str) -> int:
    if sql.count(_PRIMARY_BEGIN) != 1 or sql.count(_PRIMARY_END) != 1:
        return 0
    before_end, _ = sql.split(_PRIMARY_END, 1)
    if _PRIMARY_BEGIN not in before_end:
        return 0
    region = before_end.split(_PRIMARY_BEGIN, 1)[1]
    return len(
        re.findall(
            r"(?im)^\s*ALTER\s+TEXT\s+SEARCH\s+CONFIGURATION\b",
            region,
        )
    )


def _header(case: AlterTextSearchConfigurationFactorCase) -> list[str]:
    return [
        "-- --------------------------------------------------------",
        "-- 版权所有(C)  2021-2030 华为技术有限公司",
        "--",
        "-- --",
        f"-- author       : {_AUTHOR}",
        f"-- create at    : {_CREATE_AT}",
        f"-- version      : {_VERSION}",
        f"-- description  : ALTER TEXT SEARCH CONFIGURATION "
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


def render_alter_text_search_configuration_factor_case(
    case: AlterTextSearchConfigurationFactorCase
    | AlterTextSearchConfigurationFactorExtensionCase,
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
    lines.append("-- 3. 执行唯一获得覆盖信度的 ALTER TEXT SEARCH CONFIGURATION。")
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
    case: AlterTextSearchConfigurationFactorCase
    | AlterTextSearchConfigurationFactorExtensionCase,
    out: Path,
) -> None:
    text = render_alter_text_search_configuration_factor_case(case, Path("."))
    rc = _as_render_case(case)
    (out / rc.sql_filename).write_text(text, encoding="utf-8")


def generate_alter_text_search_configuration_factor_programs(
    baseline_plan: AlterTextSearchConfigurationFactorLoopPlan,
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
    "AlterTextSearchConfigurationFactorRenderError",
    "AlterTextSearchConfigurationFactorWitness",
    "count_primary_alter_text_search_configuration",
    "generate_alter_text_search_configuration_factor_programs",
    "render_alter_text_search_configuration_factor_case",
    "resolve_alter_text_search_configuration_factor_witness",
]
