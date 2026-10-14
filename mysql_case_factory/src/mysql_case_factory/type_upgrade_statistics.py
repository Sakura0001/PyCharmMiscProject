"""Independent TUCS statistics and chained type-upgrade cases."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from itertools import count, cycle
from typing import Any, Sequence

from mysql_case_factory.type_upgrade_consistency import (
    TypeTransition,
    TypeUpgradeCase,
    _build_case,
    render_suite,
)
from mysql_case_factory.type_upgrade_extension import _representative_transitions


STATISTICS_BATCH_ID = "2026-10-14-type-upgrade-statistics-and-chain-v1"
STATISTICS_BATCH_KIND = "statistics_and_chain_extension"
STATISTICS_PARENT_BATCH_ID = "2026-10-13-type-upgrade-consistency-extension-v1"
STATISTICS_CASE_PREFIX = "TUCS"

STATS_GAPS: tuple[str, ...] = (
    "GAP-STATS-TABLE",
    "GAP-STATS-INDEX",
    "GAP-STATS-INFORMATION-SCHEMA",
    "GAP-STATS-EXPLAIN",
    "GAP-STATS-PARTITION",
    "GAP-CHAIN-UPGRADE",
    "GAP-DUPLICATE-MODIFY",
)


def _mark(
    case: TypeUpgradeCase,
    case_no: int,
    gap_id: str,
    coverage_tags: Sequence[str],
) -> TypeUpgradeCase:
    return replace(
        case,
        case_id=f"{STATISTICS_CASE_PREFIX}-{case_no:06d}",
        batch_id=STATISTICS_BATCH_ID,
        batch_kind=STATISTICS_BATCH_KIND,
        parent_batch_id=STATISTICS_PARENT_BATCH_ID,
        priority="P0",
        gap_id=gap_id,
        coverage_tags=tuple(coverage_tags),
        interaction_rank=2,
    )


def _table_stats_check(table: str) -> str:
    return (
        "SELECT CASE WHEN EXISTS ("
        "SELECT 1 FROM mysql.innodb_table_stats "
        f"WHERE database_name=DATABASE() AND table_name='{table}' "
        "AND n_rows > 0 AND clustered_index_size > 0 AND sum_of_other_index_sizes > 0"
        ") THEN 'OK' ELSE 'FAIL' END"
    )


def _index_stats_check(table: str, expected_index: str) -> str:
    return (
        "SELECT CASE WHEN "
        "EXISTS ("
        "SELECT 1 FROM mysql.innodb_index_stats "
        f"WHERE database_name=DATABASE() AND table_name='{table}' AND index_name='PRIMARY' "
        "AND stat_name IN ('n_diff_pfx01','n_leaf_pages','size') "
        "AND stat_value >= 0 AND (sample_size IS NULL OR sample_size >= 0)"
        ") AND EXISTS ("
        "SELECT 1 FROM mysql.innodb_index_stats "
        f"WHERE database_name=DATABASE() AND table_name='{table}' AND index_name='{expected_index}' "
        "AND stat_name IN ('n_diff_pfx01','n_leaf_pages','size') "
        "AND stat_value >= 0 AND (sample_size IS NULL OR sample_size >= 0)"
        ") AND NOT EXISTS ("
        "SELECT 1 FROM mysql.innodb_index_stats "
        f"WHERE database_name=DATABASE() AND table_name='{table}' "
        "AND (stat_value < 0 OR sample_size < 0)"
        ") THEN 'OK' ELSE 'FAIL' END"
    )


def _information_schema_statistics_check(table: str) -> str:
    return (
        "SELECT CASE WHEN EXISTS ("
        "SELECT 1 FROM information_schema.STATISTICS "
        f"WHERE table_schema=DATABASE() AND table_name='{table}' "
        "AND cardinality > 0"
        ") THEN 'OK' ELSE 'FAIL' END"
    )


def _information_schema_tables_check(table: str) -> str:
    return (
        "SELECT CASE WHEN EXISTS ("
        "SELECT 1 FROM information_schema.TABLES "
        f"WHERE table_schema=DATABASE() AND table_name='{table}' "
        "AND table_rows >= 0 AND data_length >= 0 AND index_length >= 0"
        ") THEN 'OK' ELSE 'FAIL' END"
    )


def _expected_partitions_sql(partition_count: int) -> str:
    parts = ["SELECT 'p0' AS suffix"]
    parts.extend(f"UNION SELECT 'p{index}'" for index in range(1, partition_count))
    return " ".join(parts)


def _partition_table_stats_check(table: str, partition_count: int) -> str:
    return (
        "SELECT CASE WHEN NOT EXISTS ("
        "SELECT expected.suffix FROM ("
        f"{_expected_partitions_sql(partition_count)}"
        ") AS expected "
        "WHERE NOT EXISTS ("
        "SELECT 1 FROM mysql.innodb_table_stats "
        f"WHERE database_name=DATABASE() AND table_name=CONCAT('{table}', '#p#', expected.suffix)"
        ")"
        ") AND NOT EXISTS ("
        "SELECT 1 FROM mysql.innodb_table_stats "
        f"WHERE database_name=DATABASE() AND table_name LIKE '{table}#p#%' "
        "AND (n_rows < 0 OR clustered_index_size < 0 OR sum_of_other_index_sizes < 0)"
        ") THEN 'OK' ELSE 'FAIL' END"
    )


def _partition_index_stats_check(table: str, partition_count: int, expected_index: str) -> str:
    return (
        "SELECT CASE WHEN NOT EXISTS ("
        "SELECT expected.suffix FROM ("
        f"{_expected_partitions_sql(partition_count)}"
        ") AS expected "
        "WHERE NOT EXISTS ("
        "SELECT 1 FROM mysql.innodb_index_stats "
        f"WHERE database_name=DATABASE() AND table_name=CONCAT('{table}', '#p#', expected.suffix) "
        "AND index_name='PRIMARY' AND stat_name IN ('n_diff_pfx01','n_leaf_pages','size') "
        "AND stat_value >= 0 AND (sample_size IS NULL OR sample_size >= 0)"
        ")"
        ") AND NOT EXISTS ("
        "SELECT expected.suffix FROM ("
        f"{_expected_partitions_sql(partition_count)}"
        ") AS expected "
        "WHERE NOT EXISTS ("
        "SELECT 1 FROM mysql.innodb_index_stats "
        f"WHERE database_name=DATABASE() AND table_name=CONCAT('{table}', '#p#', expected.suffix) "
        f"AND index_name='{expected_index}' AND stat_name IN ('n_diff_pfx01','n_leaf_pages','size') "
        "AND stat_value >= 0 AND (sample_size IS NULL OR sample_size >= 0)"
        ")"
        ") AND NOT EXISTS ("
        "SELECT 1 FROM mysql.innodb_index_stats "
        f"WHERE database_name=DATABASE() AND table_name LIKE '{table}#p#%' "
        "AND (stat_value < 0 OR sample_size < 0)"
        ") THEN 'OK' ELSE 'FAIL' END"
    )


def _partition_count_check(table: str, partition_count: int) -> str:
    return (
        "SELECT CASE WHEN ("
        "SELECT COUNT(*) FROM information_schema.PARTITIONS "
        f"WHERE table_schema=DATABASE() AND table_name='{table}'"
        f") >= {partition_count} THEN 'OK' ELSE 'FAIL' END"
    )


def _expected_index_name(index_profile: str) -> str:
    return {
        "secondary": "idx_target",
        "unique": "uk_target",
        "composite": "idx_composite",
        "prefix": "idx_prefix",
        "descending": "idx_desc",
    }.get(index_profile, "idx_target")


def _stats_case(
    case_no: int,
    transition: TypeTransition,
    index_profile: str,
    table_form: str = "ordinary",
    partition_count: int = 1,
    gap_id: str = "GAP-STATS-EXPLAIN",
) -> TypeUpgradeCase:
    case = _build_case(
        case_no,
        cluster="statistics_and_chain",
        transition=transition,
        data_profile="post_target_boundary",
        attribute="nullable",
        index_profile=index_profile,
        table_form=table_form,
    )
    ref_table = f"tuc_ref_{case_no}"
    algo_table = f"tuc_algo_{case_no}"
    expected_index = _expected_index_name(index_profile)

    if table_form == "ordinary":
        stats_checks = [
            _table_stats_check(ref_table),
            _table_stats_check(algo_table),
            _index_stats_check(ref_table, expected_index),
            _index_stats_check(algo_table, expected_index),
            _information_schema_statistics_check(ref_table),
            _information_schema_statistics_check(algo_table),
            _information_schema_tables_check(ref_table),
            _information_schema_tables_check(algo_table),
        ]
    else:
        stats_checks = [
            _partition_table_stats_check(ref_table, partition_count),
            _partition_table_stats_check(algo_table, partition_count),
            _partition_index_stats_check(ref_table, partition_count, expected_index),
            _partition_index_stats_check(algo_table, partition_count, expected_index),
            _information_schema_statistics_check(ref_table),
            _information_schema_statistics_check(algo_table),
            _information_schema_tables_check(ref_table),
            _information_schema_tables_check(algo_table),
            _partition_count_check(ref_table, partition_count),
            _partition_count_check(algo_table, partition_count),
        ]

    query_plans = (
        (
            f"EXPLAIN FORMAT=JSON SELECT id FROM {ref_table} FORCE INDEX({expected_index}) WHERE target_col IS NOT NULL",
            expected_index,
        ),
        (
            f"EXPLAIN FORMAT=JSON SELECT id FROM {algo_table} FORCE INDEX({expected_index}) WHERE target_col IS NOT NULL",
            expected_index,
        ),
    )

    case = replace(
        case,
        stats_pre_analyze_sql=tuple(stats_checks),
        analyze_sql=(f"ANALYZE TABLE {ref_table}", f"ANALYZE TABLE {algo_table}"),
        stats_post_analyze_sql=tuple(stats_checks),
        query_plans=query_plans,
        reason=f"P0 statistics coverage: {transition.family}/{index_profile}/{table_form}",
    )
    return _mark(case, case_no, gap_id, ("STATISTICS", transition.family.upper(), index_profile.upper(), table_form.upper()))


def _chain_case(case_no: int, transition: TypeTransition, index_profile: str) -> TypeUpgradeCase:
    case = _stats_case(case_no, transition, index_profile)
    algo_table = f"tuc_algo_{case_no}"
    pre_ddl = (
        f"ALTER TABLE {algo_table} MODIFY target_col INT NULL, ALGORITHM=${{ALGORITHM}}",
    )
    case = replace(
        case,
        pre_ddl_sql=pre_ddl,
        reason="P0 consecutive upgrade: SMALLINT -> INT -> BIGINT",
    )
    return _mark(case, case_no, "GAP-CHAIN-UPGRADE", ("CHAIN", "SMALLINT", "INT", "BIGINT", index_profile.upper()))


def _duplicate_modify_case(case_no: int, transition: TypeTransition) -> TypeUpgradeCase:
    case = _build_case(
        case_no,
        cluster="statistics_and_chain",
        transition=transition,
        data_profile="boundary",
        attribute="nullable",
        index_profile="secondary",
    )
    algo_table = f"tuc_algo_{case_no}"
    ddl = (
        f"ALTER TABLE {algo_table} MODIFY target_col INT NULL, "
        f"MODIFY target_col BIGINT NULL, ALGORITHM=${{ALGORITHM}}"
    )
    case = replace(
        case,
        expected_outcome="reject",
        ddl_sql=ddl,
        post_ddl_sql=(),
        invalid_post_ddl_sql=(),
        stats_pre_analyze_sql=(),
        analyze_sql=(),
        stats_post_analyze_sql=(),
        query_plans=(),
        reason="P0 duplicate MODIFY for the same column must reject atomically",
    )
    return _mark(case, case_no, "GAP-DUPLICATE-MODIFY", ("DDL", "DUPLICATE_MODIFY", "ATOMIC_REJECT"))


def generate_statistics_cases() -> list[TypeUpgradeCase]:
    representatives = _representative_transitions()
    integer = next(item for item in representatives if item.family == "integer")
    smallint_to_bigint = TypeTransition(
        family="integer",
        source_type="SMALLINT",
        target_type="BIGINT",
        positive=True,
        seed_values=("-32768", "-1", "0", "32767"),
        post_values=("32768", "2147483647", "-2147483648"),
        invalid_values=("9223372036854775808",),
        reason="SMALLINT to BIGINT chained upgrade",
    )
    duplicate_transition = TypeTransition(
        family="integer",
        source_type="SMALLINT",
        target_type="BIGINT",
        positive=False,
        seed_values=("-32768", "-1", "0", "32767"),
        post_values=(),
        invalid_values=("32768",),
        reason="duplicate MODIFY negative case",
    )

    cases: list[TypeUpgradeCase] = []
    case_counter = count(1)
    ordinary_stats_gaps = cycle(
        (
            "GAP-STATS-TABLE",
            "GAP-STATS-INDEX",
            "GAP-STATS-INFORMATION-SCHEMA",
            "GAP-STATS-EXPLAIN",
        )
    )

    for transition in representatives:
        profiles = ["secondary", "unique", "composite", "descending"]
        if transition.family in {"character", "binary"}:
            profiles.append("prefix")
        for profile in profiles:
            cases.append(
                _stats_case(
                    next(case_counter),
                    transition,
                    profile,
                    gap_id=next(ordinary_stats_gaps),
                )
            )

    partition_forms = (
        ("range_partition", 2),
        ("list_partition", 2),
        ("hash_partition", 4),
        ("key_partition", 4),
    )
    for table_form, partition_count in partition_forms:
        for transition in representatives:
            cases.append(
                _stats_case(
                    next(case_counter),
                    transition,
                    "secondary",
                    table_form=table_form,
                    partition_count=partition_count,
                    gap_id="GAP-STATS-PARTITION",
                )
            )

    for profile in ("secondary", "unique", "composite", "descending"):
        cases.append(_chain_case(next(case_counter), smallint_to_bigint, profile))

    cases.append(_duplicate_modify_case(next(case_counter), duplicate_transition))
    return cases


def render_statistics_suite(cases: Sequence[TypeUpgradeCase], profile: str) -> str:
    if profile not in {"copy", "inplace", "instant"}:
        raise ValueError(f"unsupported profile: {profile}")
    return render_suite(cases, profile)


def statistics_manifest(cases: Sequence[TypeUpgradeCase], profile: str) -> dict[str, Any]:
    if profile not in {"copy", "inplace", "instant"}:
        raise ValueError(f"unsupported profile: {profile}")
    import json

    payload = json.dumps(
        [case.to_json() for case in cases],
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    gap_counts: dict[str, int] = {}
    family_counts: dict[str, int] = {}
    for case in cases:
        if case.gap_id is None:
            raise ValueError("statistics case missing gap_id")
        gap_counts[case.gap_id] = gap_counts.get(case.gap_id, 0) + 1
        family_counts[case.family] = family_counts.get(case.family, 0) + 1
    return {
        "profile": profile,
        "batch_id": STATISTICS_BATCH_ID,
        "batch_kind": STATISTICS_BATCH_KIND,
        "parent_batch_id": STATISTICS_PARENT_BATCH_ID,
        "case_id_prefix": STATISTICS_CASE_PREFIX,
        "case_count": len(cases),
        "sha256": sha256(payload.encode("utf-8")).hexdigest(),
        "gap_counts": gap_counts,
        "families": family_counts,
    }
