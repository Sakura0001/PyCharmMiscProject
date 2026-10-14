"""Independent TUCX extension for high-risk type-upgrade interactions.

This module deliberately does not mutate the verified TUC baseline.  It emits a
separate extension batch with parent-batch linkage and P0 gap metadata.
"""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from itertools import count
from typing import Any, Sequence

from mysql_case_factory.type_upgrade_consistency import (
    FORBIDDEN_TYPE_TOKENS,
    TYPE_UPGRADE_BATCH_ID,
    TypeTransition,
    TypeUpgradeCase,
    _all_positive_transitions,
    _build_case,
    _column_definition,
    _data_check,
    _fk_check,
    _index_check,
    _schema_check,
    build_factor_catalog,
    render_suite,
)


EXTENSION_BATCH_ID = "2026-10-13-type-upgrade-consistency-extension-v1"
EXTENSION_BATCH_KIND = "extension"
EXTENSION_CASE_PREFIX = "TUCX"
PARENT_BATCH_ID = TYPE_UPGRADE_BATCH_ID

P0_GAPS: tuple[str, ...] = (
    "GAP-DATA-BEHAVIOR",
    "GAP-INDEX-PK",
    "GAP-DDL-MULTI-COLUMN",
    "GAP-FK-ACTION",
    "GAP-QUERY-ORACLE",
)


def _representative_transitions() -> tuple[TypeTransition, ...]:
    catalog = build_factor_catalog()
    positive = _all_positive_transitions(catalog)

    def find(family: str, source: str, target: str) -> TypeTransition:
        return next(
            item
            for item in positive
            if item.family == family and item.source_type == source and item.target_type == target
        )

    return (
        find("integer", "INT", "BIGINT"),
        find("decimal", "DECIMAL(4,2)", "DECIMAL(5,2)"),
        find("character", "VARCHAR(31)", "VARCHAR(32)"),
        find("binary", "VARBINARY(31)", "VARBINARY(32)"),
        find("bit", "BIT(8)", "BIT(16)"),
    )


def _anchor_transitions() -> tuple[TypeTransition, ...]:
    return _all_positive_transitions(build_factor_catalog())


def _is_large_object(transition: TypeTransition) -> bool:
    return transition.source_type.endswith(("TEXT", "BLOB")) or transition.target_type.endswith(("TEXT", "BLOB"))


def _target_length(transition: TypeTransition) -> int | None:
    type_name = transition.target_type
    if "(" not in type_name:
        return None
    return int(type_name.split("(", 1)[1].split(")", 1)[0])


def _target_key_bytes(transition: TypeTransition) -> int | None:
    if _is_large_object(transition):
        return None
    if transition.family == "character":
        length = _target_length(transition)
        if length is None:
            return None
        multiplier = {"latin1": 1, "ascii": 1, "utf8mb3": 3, "utf8mb4": 4}.get(transition.charset or "utf8mb4", 1)
        return length * multiplier
    if transition.family == "binary":
        return _target_length(transition)
    return 0


def _prefix_order_supported(transition: TypeTransition) -> bool:
    if transition.family not in {"character", "binary"}:
        return False
    if _is_large_object(transition):
        return True
    if "(" not in transition.source_type:
        return False
    return int(transition.source_type.split("(", 1)[1].split(")", 1)[0]) > 1


def _full_target_key_supported(transition: TypeTransition) -> bool:
    key_bytes = _target_key_bytes(transition)
    return key_bytes is not None and key_bytes <= 2816


def _mark(
    case: TypeUpgradeCase,
    case_no: int,
    gap_id: str,
    coverage_tags: Sequence[str],
    interaction_rank: int,
) -> TypeUpgradeCase:
    return replace(
        case,
        case_id=f"{EXTENSION_CASE_PREFIX}-{case_no:06d}",
        batch_id=EXTENSION_BATCH_ID,
        batch_kind=EXTENSION_BATCH_KIND,
        parent_batch_id=PARENT_BATCH_ID,
        priority="P0",
        gap_id=gap_id,
        coverage_tags=tuple(coverage_tags),
        interaction_rank=interaction_rank,
    )


def _unique_seed_values(transition: TypeTransition) -> tuple[str, ...]:
    if transition.family == "character":
        return ("'a'", "'b'", "'c'", "'d'")
    if transition.family == "binary":
        values = tuple(value for value in transition.seed_values if value != "NULL")
        unique_values: list[str] = []
        for value in values:
            if value not in unique_values:
                unique_values.append(value)
        return tuple(unique_values[:4])
    if transition.family == "bit":
        width = int(transition.source_type[4:-1])
        count = min(4, 1 << width)
        return tuple(f"b'{value:0{width}b}'" for value in range(count))
    values = tuple(value for value in transition.seed_values if value != "NULL")
    unique: list[str] = []
    for value in values:
        if value not in unique:
            unique.append(value)
    if len(unique) < 2:
        unique.extend(("1", "2", "3", "4"))
    return tuple(unique[:4])


def _equivalent_values(transition: TypeTransition) -> tuple[str, str]:
    if transition.family == "character":
        return ("'a'", "'A'")
    if transition.family == "binary":
        return ("x'01'", "x'0100'")
    if transition.family == "bit":
        return ("b'1'", "b'01'")
    return ("1", "1")


def _data_profile_case(
    case_no: int,
    transition: TypeTransition,
    profile: str,
) -> TypeUpgradeCase:
    attribute = "not_null_default" if profile == "default_omission" else "nullable"
    if profile == "duplicate_conflict":
        index_profile = "unique"
    else:
        index_profile = "secondary" if _full_target_key_supported(transition) else "prefix"
    case = _build_case(
        case_no,
        cluster="extension_data_behavior",
        transition=transition,
        data_profile=profile,
        attribute=attribute,
        index_profile=index_profile,
    )
    ref_table = f"tuc_ref_{case_no}"
    algo_table = f"tuc_algo_{case_no}"
    post_value = transition.post_values[0] if transition.post_values else transition.seed_values[0]
    seed_value = case.seed_values[0]

    if profile == "post_target_boundary":
        post_sql = case.post_ddl_sql
    elif profile == "default_omission":
        post_sql = (
            f"INSERT INTO {ref_table} (id,part_key,canary_int,canary_varchar,canary_varbinary,canary_decimal) "
            "VALUES (300,0,300,'default',x'09',300.0000)",
            f"INSERT INTO {algo_table} (id,part_key,canary_int,canary_varchar,canary_varbinary,canary_decimal) "
            "VALUES (300,0,300,'default',x'09',300.0000)",
        )
    elif profile == "collation_equivalent":
        left, right = _equivalent_values(transition)
        post_sql = (
            f"INSERT INTO {ref_table} (id,target_col,part_key,canary_int,canary_varchar,canary_varbinary,canary_decimal) VALUES (300,{left},0,300,'eq-a',x'09',300.0000),(301,{right},1,301,'eq-b',x'09',301.0000)",
            f"INSERT INTO {algo_table} (id,target_col,part_key,canary_int,canary_varchar,canary_varbinary,canary_decimal) VALUES (300,{left},0,300,'eq-a',x'09',300.0000),(301,{right},1,301,'eq-b',x'09',301.0000)",
        )
    elif profile == "update_old_to_new":
        post_sql = (
            f"UPDATE {ref_table} SET target_col={post_value} WHERE id=1",
            f"UPDATE {algo_table} SET target_col={post_value} WHERE id=1",
        )
    elif profile == "delete_reinsert":
        post_sql = (
            f"DELETE FROM {ref_table} WHERE id=1",
            f"INSERT INTO {ref_table} (id,target_col,part_key,canary_int,canary_varchar,canary_varbinary,canary_decimal) VALUES (1,{seed_value},0,1,'reinsert',x'09',1.0000)",
            f"DELETE FROM {algo_table} WHERE id=1",
            f"INSERT INTO {algo_table} (id,target_col,part_key,canary_int,canary_varchar,canary_varbinary,canary_decimal) VALUES (1,{seed_value},0,1,'reinsert',x'09',1.0000)",
        )
    elif profile == "commit_ledger":
        post_sql = (
            "START TRANSACTION",
            f"INSERT INTO {ref_table} (id,target_col,part_key,canary_int,canary_varchar,canary_varbinary,canary_decimal) VALUES (300,{post_value},0,300,'commit',x'09',300.0000)",
            "COMMIT",
            "START TRANSACTION",
            f"INSERT INTO {algo_table} (id,target_col,part_key,canary_int,canary_varchar,canary_varbinary,canary_decimal) VALUES (300,{post_value},0,300,'commit',x'09',300.0000)",
            "COMMIT",
        )
    elif profile == "rollback_ledger":
        post_sql = (
            "START TRANSACTION",
            f"INSERT INTO {ref_table} (id,target_col,part_key,canary_int,canary_varchar,canary_varbinary,canary_decimal) VALUES (301,{post_value},1,301,'rollback',x'09',301.0000)",
            "ROLLBACK",
            "START TRANSACTION",
            f"INSERT INTO {algo_table} (id,target_col,part_key,canary_int,canary_varchar,canary_varbinary,canary_decimal) VALUES (301,{post_value},1,301,'rollback',x'09',301.0000)",
            "ROLLBACK",
        )
    else:  # duplicate_conflict
        post_sql = ()
        invalid_sql = (
            f"INSERT INTO {ref_table} (id,target_col,part_key,canary_int,canary_varchar,canary_varbinary,canary_decimal) VALUES (302,{seed_value},0,302,'dup',x'09',302.0000)",
            f"INSERT INTO {algo_table} (id,target_col,part_key,canary_int,canary_varchar,canary_varbinary,canary_decimal) VALUES (302,{seed_value},0,302,'dup',x'09',302.0000)",
        )
        case = replace(case, invalid_post_ddl_sql=invalid_sql)

    if profile != "duplicate_conflict":
        case = replace(case, invalid_post_ddl_sql=())

    case = replace(case, post_ddl_sql=post_sql, reason=f"P0 data behavior: {profile}")
    return _mark(case, case_no, "GAP-DATA-BEHAVIOR", ("DATA", profile.upper()), 2)


def _pk_post_values(transition: TypeTransition) -> tuple[str, ...]:
    if transition.family == "character":
        length = int(transition.target_type.split("(", 1)[1].split(")", 1)[0])
        return (f"'{'e' * length}'", f"'{'f' * length}'")
    if transition.family == "binary":
        length = int(transition.target_type.split("(", 1)[1].split(")", 1)[0])
        return (f"x'{'05' * length}'", f"x'{'06' * length}'")
    if transition.family == "bit":
        width = int(transition.target_type[4:-1])
        return (f"b'{('101' * width)[:width]}'", f"b'{('110' * width)[:width]}'")
    return tuple(value for value in transition.post_values if value != "NULL")[:2]


def _pk_case(case_no: int, transition: TypeTransition, shape: str) -> TypeUpgradeCase:
    old_table = f"tucx_pk_old_{case_no}"
    ref_table = f"tucx_pk_ref_{case_no}"
    algo_table = f"tucx_pk_algo_{case_no}"
    source_col = _column_definition(transition.source_type, "not_null_default", transition.charset, transition.collation, transition.family)
    target_col = _column_definition(transition.target_type, "not_null_default", transition.charset, transition.collation, transition.family)

    primary_key = {
        "single": "PRIMARY KEY (target_col), UNIQUE KEY uk_id (id)",
        "first": "PRIMARY KEY (target_col,id,part_key)",
        "middle": "PRIMARY KEY (id,target_col,part_key)",
        "last": "PRIMARY KEY (id,part_key,target_col)",
        "overlap": "PRIMARY KEY (id), UNIQUE KEY uk_target (target_col), KEY idx_target (target_col), KEY idx_desc (target_col DESC)",
    }[shape]
    common_tail = (
        "part_key INT NOT NULL DEFAULT 0, canary_int BIGINT NOT NULL DEFAULT 7, "
        "canary_varchar VARCHAR(64) NOT NULL DEFAULT 'canary', "
        "canary_varbinary VARBINARY(64) NOT NULL DEFAULT x'00', "
        "canary_decimal DECIMAL(20,4) NOT NULL DEFAULT 12.5000"
    )

    def create(table: str, coldef: str) -> str:
        return f"CREATE TABLE {table} (id BIGINT NOT NULL, target_col {coldef}, {common_tail}, {primary_key}, KEY idx_query (target_col))"

    seed_values = _unique_seed_values(transition)
    post_values = _pk_post_values(transition) or seed_values[:2]
    setup = [create(old_table, source_col), create(ref_table, target_col), create(algo_table, source_col)]
    for table in (old_table, ref_table, algo_table):
        rows = []
        for idx, value in enumerate(seed_values, 1):
            rows.append(f"({idx},{value},{idx%4},{idx},'pk',x'0a',{idx}.0000)")
        setup.append(
            f"INSERT INTO {table} (id,target_col,part_key,canary_int,canary_varchar,canary_varbinary,canary_decimal) VALUES {','.join(rows)}"
        )

    ddl = f"ALTER TABLE {algo_table} MODIFY target_col {target_col}, ALGORITHM=${{ALGORITHM}}"
    post = []
    for table in (ref_table, algo_table):
        rows = []
        for offset, value in enumerate(post_values, 100):
            rows.append(f"({offset},{value},{offset%4},{offset},'post-pk',x'0b',{offset}.0000)")
        if rows:
            post.append(
                f"INSERT INTO {table} (id,target_col,part_key,canary_int,canary_varchar,canary_varbinary,canary_decimal) VALUES {','.join(rows)}"
            )

    verify = (_schema_check(ref_table, algo_table), _data_check(ref_table, algo_table, transition.family), _index_check(ref_table, algo_table))
    cleanup = (f"DROP TABLE IF EXISTS {algo_table}", f"DROP TABLE IF EXISTS {ref_table}", f"DROP TABLE IF EXISTS {old_table}")
    return TypeUpgradeCase(
        case_id=f"{EXTENSION_CASE_PREFIX}-{case_no:06d}",
        batch_id=EXTENSION_BATCH_ID,
        batch_kind=EXTENSION_BATCH_KIND,
        cluster="extension_index_pk",
        family=transition.family,
        source_type=transition.source_type,
        target_type=transition.target_type,
        expected_outcome="success",
        data_profile="post_target_boundary",
        column_attribute="not_null_default",
        index_profile=f"pk_{shape}",
        foreign_key_profile="none",
        dependency_profile="none",
        table_form="ordinary",
        sql_mode="STRICT_ALL_TABLES",
        charset=transition.charset,
        collation=transition.collation,
        seed_values=seed_values,
        post_ddl_values=tuple(post_values),
        invalid_values=transition.invalid_values,
        reason=f"P0 target-column primary key shape: {shape}",
        setup_sql=tuple(setup),
        ddl_sql=ddl,
        post_ddl_sql=tuple(post),
        invalid_post_ddl_sql=(),
        verify_sql=verify,
        cleanup_sql=cleanup,
        parent_batch_id=PARENT_BATCH_ID,
        priority="P0",
        gap_id="GAP-INDEX-PK",
        coverage_tags=("INDEX", "PRIMARY_KEY", shape.upper()),
        interaction_rank=2,
    )


def _query_value_expr(family: str) -> str:
    if family == "character":
        return "HEX(CAST(target_col AS BINARY))"
    if family == "binary":
        return "HEX(target_col)"
    if family == "bit":
        return "BIN(target_col)"
    return "CAST(target_col AS CHAR)"


def _ordered_by_id_check(ref_table: str, algo_table: str, family: str) -> str:
    expr = _query_value_expr(family)
    return (
        "SELECT CASE WHEN "
        f"(SELECT GROUP_CONCAT(id, ':', {expr} ORDER BY id SEPARATOR '|') FROM {ref_table}) "
        f"<=> (SELECT GROUP_CONCAT(id, ':', {expr} ORDER BY id SEPARATOR '|') FROM {algo_table}) "
        "THEN 'OK' ELSE 'FAIL' END"
    )


def _ordered_by_target_check(ref_table: str, algo_table: str, family: str, descending: bool) -> str:
    expr = _query_value_expr(family)
    direction = "DESC" if descending else "ASC"
    return (
        "SELECT CASE WHEN "
        f"(SELECT GROUP_CONCAT(id, ':', {expr} ORDER BY target_col {direction}, id {direction} SEPARATOR '|') FROM {ref_table}) "
        f"<=> (SELECT GROUP_CONCAT(id, ':', {expr} ORDER BY target_col {direction}, id {direction} SEPARATOR '|') FROM {algo_table}) "
        "THEN 'OK' ELSE 'FAIL' END"
    )


def _query_case(case_no: int, transition: TypeTransition, mode: str) -> TypeUpgradeCase:
    index_profile = {
        "secondary_scan": "secondary",
        "unique_scan": "unique",
        "unique_conflict": "unique",
        "prefix_order": "prefix",
        "descending_order": "descending",
    }[mode]
    index_name = {
        "secondary_scan": "idx_target",
        "unique_scan": "uk_target",
        "unique_conflict": "uk_target",
        "prefix_order": "idx_prefix",
        "descending_order": "idx_desc",
    }[mode]

    case = _build_case(
        case_no,
        cluster="extension_query_oracle",
        transition=transition,
        data_profile="post_target_boundary",
        attribute="nullable",
        index_profile=index_profile,
    )
    ref_table = f"tuc_ref_{case_no}"
    algo_table = f"tuc_algo_{case_no}"

    forced_index_check = (
        "SELECT CASE WHEN NOT EXISTS ("
        f"((SELECT id,target_col FROM {ref_table} FORCE INDEX({index_name})) "
        f"EXCEPT (SELECT id,target_col FROM {algo_table} FORCE INDEX({index_name}))) "
        "UNION ALL "
        f"((SELECT id,target_col FROM {algo_table} FORCE INDEX({index_name})) "
        f"EXCEPT (SELECT id,target_col FROM {ref_table} FORCE INDEX({index_name}))) "
        "LIMIT 1) THEN 'OK' ELSE 'FAIL' END"
    )
    verify = [
        _ordered_by_id_check(ref_table, algo_table, transition.family),
        forced_index_check,
    ]
    if mode == "prefix_order":
        verify.append(_ordered_by_target_check(ref_table, algo_table, transition.family, descending=False))
    if mode == "descending_order":
        verify.append(_ordered_by_target_check(ref_table, algo_table, transition.family, descending=True))

    query_plans = (
        (
            f"EXPLAIN FORMAT=JSON SELECT id FROM {ref_table} FORCE INDEX({index_name}) WHERE target_col IS NOT NULL",
            index_name,
        ),
        (
            f"EXPLAIN FORMAT=JSON SELECT id FROM {algo_table} FORCE INDEX({index_name}) WHERE target_col IS NOT NULL",
            index_name,
        ),
    )

    invalid_sql = ()
    if mode == "unique_conflict":
        seed_value = case.seed_values[0]
        invalid_sql = (
            f"INSERT INTO {ref_table} (id,target_col,part_key,canary_int,canary_varchar,canary_varbinary,canary_decimal) VALUES (400,{seed_value},0,400,'query-dup',x'0c',400.0000)",
            f"INSERT INTO {algo_table} (id,target_col,part_key,canary_int,canary_varchar,canary_varbinary,canary_decimal) VALUES (400,{seed_value},0,400,'query-dup',x'0c',400.0000)",
        )

    case = replace(
        case,
        verify_sql=(*case.verify_sql, *verify),
        query_plans=query_plans,
        invalid_post_ddl_sql=invalid_sql,
        reason=f"P0 query oracle: {mode}",
    )
    return _mark(case, case_no, "GAP-QUERY-ORACLE", ("QUERY", mode.upper()), 2)


def _multi_column_case(
    case_no: int,
    transitions: Sequence[TypeTransition],
    shape: str,
    expected_outcome: str = "success",
) -> TypeUpgradeCase:
    old_table = f"tucx_multi_old_{case_no}"
    ref_table = f"tucx_multi_ref_{case_no}"
    algo_table = f"tucx_multi_algo_{case_no}"
    column_count = {"two_same": 2, "three_same": 3, "five_mixed": 5, "composite_members": 2, "atomic_reject": 2}[shape]
    selected = list(transitions[:column_count])

    def columns(target: bool) -> list[str]:
        result = ["id BIGINT NOT NULL"]
        for idx, transition in enumerate(selected, 1):
            type_name = transition.target_type if target else transition.source_type
            definition = _column_definition(type_name, "nullable", transition.charset, transition.collation, transition.family)
            result.append(f"target_{idx} {definition}")
        result.extend(
            [
                "part_key INT NOT NULL DEFAULT 0",
                "canary_int BIGINT NOT NULL DEFAULT 7",
                "canary_varchar VARCHAR(64) NOT NULL DEFAULT 'canary'",
                "canary_varbinary VARBINARY(64) NOT NULL DEFAULT x'00'",
                "canary_decimal DECIMAL(20,4) NOT NULL DEFAULT 12.5000",
            ]
        )
        result.append("PRIMARY KEY (id)")
        if shape == "composite_members":
            result.append("KEY idx_composite_members (target_1,target_2)")
        return result

    def create(table: str, target: bool) -> str:
        return f"CREATE TABLE {table} ({', '.join(columns(target))})"

    setup = [create(old_table, False), create(ref_table, expected_outcome == "success"), create(algo_table, False)]
    seed_values = [_unique_seed_values(item)[0] for item in selected]
    post_values = [(item.post_values[0] if item.post_values else _unique_seed_values(item)[0]) for item in selected]
    seed_names = ",".join(f"target_{idx}" for idx in range(1, len(selected) + 1))
    post_names = seed_names
    for table in (old_table, ref_table, algo_table):
        setup.append(
            f"INSERT INTO {table} (id,{seed_names},part_key,canary_int,canary_varchar,canary_varbinary,canary_decimal) "
            f"VALUES (1,{','.join(seed_values)},0,1,'multi',x'0d',1.0000)"
        )

    if expected_outcome == "success":
        modify_columns = []
        for idx, transition in enumerate(selected, 1):
            definition = _column_definition(transition.target_type, "nullable", transition.charset, transition.collation, transition.family)
            modify_columns.append(f"MODIFY target_{idx} {definition}")
        ddl = f"ALTER TABLE {algo_table} {', '.join(modify_columns)}, ALGORITHM=${{ALGORITHM}}"
        post = []
        for table in (ref_table, algo_table):
            post.append(
                f"INSERT INTO {table} (id,{post_names},part_key,canary_int,canary_varchar,canary_varbinary,canary_decimal) "
                f"VALUES (100,{','.join(post_values)},0,100,'multi-post',x'0e',100.0000)"
            )
    else:
        safe = selected[0]
        unsafe_source = "BIGINT"
        unsafe_target = "INT"
        unsafe_value = "9223372036854775807"
        setup.append(
            f"UPDATE {old_table} SET target_2={unsafe_value} WHERE id=1"
        )
        setup.append(
            f"UPDATE {ref_table} SET target_2={unsafe_value} WHERE id=1"
        )
        setup.append(
            f"UPDATE {algo_table} SET target_2={unsafe_value} WHERE id=1"
        )
        safe_definition = _column_definition(safe.target_type, "nullable", safe.charset, safe.collation, safe.family)
        ddl = (
            f"ALTER TABLE {algo_table} MODIFY target_1 {safe_definition}, "
            f"MODIFY target_2 {unsafe_target} NULL, ALGORITHM=${{ALGORITHM}}"
        )
        post = ()

    data_columns = ",".join([f"target_{idx}" for idx in range(1, len(selected) + 1)])
    data_check = (
        f"SELECT CASE WHEN NOT EXISTS ("
        f"(SELECT id,{data_columns},part_key,canary_int,canary_varchar,canary_varbinary,canary_decimal FROM {ref_table} "
        f"EXCEPT SELECT id,{data_columns},part_key,canary_int,canary_varchar,canary_varbinary,canary_decimal FROM {algo_table}) "
        f"UNION ALL "
        f"(SELECT id,{data_columns},part_key,canary_int,canary_varchar,canary_varbinary,canary_decimal FROM {algo_table} "
        f"EXCEPT SELECT id,{data_columns},part_key,canary_int,canary_varchar,canary_varbinary,canary_decimal FROM {ref_table}) "
        "LIMIT 1) THEN 'OK' ELSE 'FAIL' END"
    )
    verify = (_schema_check(ref_table, algo_table), data_check)
    if shape == "composite_members":
        verify = (*verify, _index_check(ref_table, algo_table))
    cleanup = (
        f"DROP TABLE IF EXISTS {algo_table}",
        f"DROP TABLE IF EXISTS {ref_table}",
        f"DROP TABLE IF EXISTS {old_table}",
    )
    family = selected[0].family if len(selected) == 1 else "mixed"
    return TypeUpgradeCase(
        case_id=f"{EXTENSION_CASE_PREFIX}-{case_no:06d}",
        batch_id=EXTENSION_BATCH_ID,
        batch_kind=EXTENSION_BATCH_KIND,
        cluster="extension_multi_column",
        family=family,
        source_type=selected[0].source_type,
        target_type=selected[0].target_type,
        expected_outcome=expected_outcome,
        data_profile="multi_column",
        column_attribute="nullable",
        index_profile="composite" if shape == "composite_members" else "none",
        foreign_key_profile="none",
        dependency_profile="none",
        table_form="ordinary",
        sql_mode="STRICT_ALL_TABLES",
        charset=selected[0].charset,
        collation=selected[0].collation,
        seed_values=tuple(seed_values),
        post_ddl_values=tuple(post_values),
        invalid_values=("9223372036854775807",) if expected_outcome == "reject" else (),
        reason=f"P0 multi-column ALTER shape: {shape}",
        setup_sql=tuple(setup),
        ddl_sql=ddl,
        post_ddl_sql=tuple(post),
        invalid_post_ddl_sql=(),
        verify_sql=verify,
        cleanup_sql=cleanup,
        parent_batch_id=PARENT_BATCH_ID,
        priority="P0",
        gap_id="GAP-DDL-MULTI-COLUMN",
        coverage_tags=("DDL", "MULTI_COLUMN", shape.upper()),
        interaction_rank=2,
    )


def _fk_update_value(transition: TypeTransition, seed_value: str) -> str:
    if transition.family == "binary":
        length = _target_length(transition) or 2
        hex_digits = ("0102" * length)[: length * 2]
        return f"x'{hex_digits}'"
    if transition.family == "character":
        length = _target_length(transition) or 2
        return f"'{'z' * length}'"
    if transition.family == "bit":
        width = int(transition.target_type[4:-1])
        if width == 1:
            return "b'1'" if seed_value == "b'0'" else "b'0'"
        return f"b'{('1100' * width)[:width]}'"
    if transition.family == "decimal":
        return "1" if seed_value not in {"1", "1.0"} else "2"
    return "43"


def _fk_type(transition: TypeTransition) -> str:
    result = transition.target_type
    if transition.family == "character" and transition.charset:
        result += f" CHARACTER SET {transition.charset} COLLATE {transition.collation}"
    return result


def _fk_child_check(ref_table: str, algo_table: str) -> str:
    return (
        f"SELECT CASE WHEN NOT EXISTS ("
        f"(SELECT id,parent_id FROM {ref_table} EXCEPT SELECT id,parent_id FROM {algo_table}) "
        f"UNION ALL (SELECT id,parent_id FROM {algo_table} EXCEPT SELECT id,parent_id FROM {ref_table}) LIMIT 1) "
        "THEN 'OK' ELSE 'FAIL' END"
    )


def _fk_action_case(case_no: int, transition: TypeTransition, action: str) -> TypeUpgradeCase:
    case = _build_case(
        case_no,
        cluster="extension_fk_action",
        transition=transition,
        data_profile="post_target_boundary",
        attribute="nullable",
        index_profile="secondary",
    )
    ref_main = f"tuc_ref_{case_no}"
    algo_main = f"tuc_algo_{case_no}"
    ref_child = f"tucx_fk_child_ref_{case_no}"
    algo_child = f"tucx_fk_child_algo_{case_no}"
    ref_level2 = f"tucx_fk_level2_ref_{case_no}"
    algo_level2 = f"tucx_fk_level2_algo_{case_no}"
    fk_type = _fk_type(transition)
    seed_value = _unique_seed_values(transition)[0]
    update_value = _fk_update_value(transition, seed_value)

    on_delete = "RESTRICT"
    on_update = "RESTRICT"
    if action == "delete_cascade":
        on_delete = "CASCADE"
    elif action == "delete_set_null":
        on_delete = "SET NULL"
    elif action == "update_cascade":
        on_update = "CASCADE"
    elif action == "update_set_null":
        on_update = "SET NULL"
    elif action == "delete_no_action":
        on_delete = "NO ACTION"
    elif action == "update_no_action":
        on_update = "NO ACTION"
    elif action == "two_level":
        on_delete = "CASCADE"
        on_update = "CASCADE"

    nullable = "NULL" if action in {"delete_set_null", "update_set_null"} else "NOT NULL"
    post: list[str] = []
    invalid: list[str] = []

    for main, child in ((ref_main, ref_child), (algo_main, algo_child)):
        post.extend(
            [
                f"CREATE TABLE {child} (id BIGINT NOT NULL PRIMARY KEY, parent_id {fk_type} {nullable}, part_key INT NOT NULL, KEY idx_parent (parent_id))",
                f"ALTER TABLE {child} ADD CONSTRAINT fk_action_{child} FOREIGN KEY (parent_id) REFERENCES {main} (target_col) ON DELETE {on_delete} ON UPDATE {on_update}",
            ]
        )
        if action != "orphan_insert":
            post.append(
                f"INSERT INTO {child} (id,parent_id,part_key) SELECT id+1000,target_col,part_key FROM {main} WHERE id=1"
            )

    if action == "orphan_insert":
        post.extend((f"DELETE FROM {ref_main} WHERE id=1 OR target_col={seed_value}", f"DELETE FROM {algo_main} WHERE id=1 OR target_col={seed_value}"))
        invalid.extend(
            (
                f"INSERT INTO {ref_child} (id,parent_id,part_key) VALUES (2000,{seed_value},0)",
                f"INSERT INTO {algo_child} (id,parent_id,part_key) VALUES (2000,{seed_value},0)",
            )
        )
    elif action == "delete_cascade":
        post.extend((f"DELETE FROM {ref_main} WHERE id=1 OR target_col={seed_value}", f"DELETE FROM {algo_main} WHERE id=1 OR target_col={seed_value}"))
    elif action == "delete_set_null":
        post.extend((f"DELETE FROM {ref_main} WHERE id=1 OR target_col={seed_value}", f"DELETE FROM {algo_main} WHERE id=1 OR target_col={seed_value}"))
    elif action in {"delete_restrict", "delete_no_action"}:
        invalid.extend((f"DELETE FROM {ref_main} WHERE id=1", f"DELETE FROM {algo_main} WHERE id=1"))
    elif action in {"update_cascade", "update_set_null"}:
        post.extend(
            (
                f"UPDATE {ref_main} SET target_col={update_value} WHERE id=1",
                f"UPDATE {algo_main} SET target_col={update_value} WHERE id=1",
            )
        )
    elif action in {"update_restrict", "update_no_action"}:
        invalid.extend(
            (
                f"UPDATE {ref_main} SET target_col={update_value} WHERE id=1",
                f"UPDATE {algo_main} SET target_col={update_value} WHERE id=1",
            )
        )
    elif action == "two_level":
        for child, level2 in ((ref_child, ref_level2), (algo_child, algo_level2)):
            post.extend(
                [
                    f"CREATE TABLE {level2} (id BIGINT NOT NULL PRIMARY KEY, parent_id {fk_type} NOT NULL, part_key INT NOT NULL, KEY idx_parent (parent_id))",
                    f"ALTER TABLE {level2} ADD CONSTRAINT fk_level2_{level2} FOREIGN KEY (parent_id) REFERENCES {child} (parent_id) ON DELETE CASCADE ON UPDATE CASCADE",
                    f"INSERT INTO {level2} (id,parent_id,part_key) SELECT id+2000,parent_id,part_key FROM {child}",
                ]
            )
        post.extend(
            (
                f"UPDATE {ref_main} SET target_col={update_value} WHERE id=1",
                f"UPDATE {algo_main} SET target_col={update_value} WHERE id=1",
            )
        )

    verify = [*case.verify_sql, _fk_child_check(ref_child, algo_child), _fk_check(ref_child, algo_child)]
    if action == "two_level":
        verify.extend((_fk_child_check(ref_level2, algo_level2), _fk_check(ref_level2, algo_level2)))
    cleanup = [
        f"DROP TABLE IF EXISTS {algo_level2}",
        f"DROP TABLE IF EXISTS {ref_level2}",
        f"DROP TABLE IF EXISTS {algo_child}",
        f"DROP TABLE IF EXISTS {ref_child}",
        *case.cleanup_sql,
    ]
    case = replace(
        case,
        post_ddl_sql=tuple(post),
        invalid_post_ddl_sql=tuple(invalid),
        verify_sql=tuple(verify),
        cleanup_sql=tuple(cleanup),
        reason=f"P0 foreign-key action: {action}",
    )
    return _mark(case, case_no, "GAP-FK-ACTION", ("FOREIGN_KEY", action.upper()), 2)


def generate_extension_cases() -> list[TypeUpgradeCase]:
    anchors = _anchor_transitions()
    representatives = _representative_transitions()
    cases: list[TypeUpgradeCase] = []
    case_counter = count(1)

    data_profiles = (
        "post_target_boundary",
        "default_omission",
        "collation_equivalent",
        "duplicate_conflict",
        "update_old_to_new",
        "delete_reinsert",
        "commit_ledger",
        "rollback_ledger",
    )
    for transition in anchors:
        profiles = data_profiles
        if _is_large_object(transition):
            profiles = tuple(
                profile
                for profile in data_profiles
                if profile not in {"default_omission", "duplicate_conflict"}
            )
        for profile in profiles:
            if profile == "duplicate_conflict" and not _full_target_key_supported(transition):
                continue
            cases.append(_data_profile_case(next(case_counter), transition, profile))

    for transition in anchors:
        if not _full_target_key_supported(transition):
            continue
        for shape in ("single", "first", "middle", "last", "overlap"):
            cases.append(_pk_case(next(case_counter), transition, shape))

    for transition in anchors:
        if not _full_target_key_supported(transition):
            modes = ("prefix_order",)
        else:
            modes = [
                "secondary_scan",
                "unique_scan",
                "unique_conflict",
                "descending_order",
            ]
            if _prefix_order_supported(transition):
                modes.append("prefix_order")
        for mode in modes:
            cases.append(_query_case(next(case_counter), transition, mode))

    for transition in anchors:
        cases.append(_multi_column_case(next(case_counter), (transition, transition), "two_same"))
        cases.append(_multi_column_case(next(case_counter), (transition,) * 3, "three_same"))
        if _full_target_key_supported(transition) and (
            (_target_key_bytes(transition) or 0) * 2 <= 2816
        ):
            cases.append(_multi_column_case(next(case_counter), (transition, transition), "composite_members"))
    cases.append(_multi_column_case(next(case_counter), representatives, "five_mixed"))

    unsafe_transition = TypeTransition(
        family="integer",
        source_type="BIGINT",
        target_type="INT",
        positive=False,
        seed_values=("9223372036854775807",),
        post_values=(),
        invalid_values=("9223372036854775807",),
        reason="BIGINT to INT narrowing with out-of-range data",
    )
    cases.append(
        _multi_column_case(
            next(case_counter),
            (representatives[0], unsafe_transition),
            "atomic_reject",
            expected_outcome="reject",
        )
    )

    fk_actions = (
        "orphan_insert",
        "delete_cascade",
        "delete_set_null",
        "delete_restrict",
        "delete_no_action",
        "update_cascade",
        "update_set_null",
        "update_restrict",
        "update_no_action",
        "two_level",
    )
    for transition in anchors:
        if transition.family not in {"integer", "character", "binary"}:
            continue
        if not _full_target_key_supported(transition):
            continue
        for action in fk_actions:
            cases.append(_fk_action_case(next(case_counter), transition, action))

    return cases


def render_extension_suite(cases: Sequence[TypeUpgradeCase], profile: str) -> str:
    if profile not in {"copy", "inplace", "instant"}:
        raise ValueError(f"unsupported profile: {profile}")
    return render_suite(cases, profile)


def extension_manifest(cases: Sequence[TypeUpgradeCase], profile: str) -> dict[str, Any]:
    if profile not in {"copy", "inplace", "instant"}:
        raise ValueError(f"unsupported profile: {profile}")
    payload = json_dumps(cases)
    digest = sha256(payload.encode("utf-8")).hexdigest()
    gap_counts: dict[str, int] = {}
    family_counts: dict[str, int] = {}
    cluster_counts: dict[str, int] = {}
    for case in cases:
        if case.gap_id is None:
            raise ValueError("extension case missing gap_id")
        gap_counts[case.gap_id] = gap_counts.get(case.gap_id, 0) + 1
        family_counts[case.family] = family_counts.get(case.family, 0) + 1
        cluster_counts[case.cluster] = cluster_counts.get(case.cluster, 0) + 1
    forbidden_absent = all(token not in payload for token in FORBIDDEN_TYPE_TOKENS)
    return {
        "profile": profile,
        "batch_id": EXTENSION_BATCH_ID,
        "batch_kind": EXTENSION_BATCH_KIND,
        "parent_batch_id": PARENT_BATCH_ID,
        "case_id_prefix": EXTENSION_CASE_PREFIX,
        "case_count": len(cases),
        "sha256": digest,
        "gap_counts": gap_counts,
        "families": family_counts,
        "clusters": cluster_counts,
        "forbidden_types_absent": forbidden_absent,
    }


def json_dumps(cases: Sequence[TypeUpgradeCase]) -> str:
    import json

    return json.dumps([case.to_json() for case in cases], sort_keys=True, separators=(",", ":"), ensure_ascii=False)
