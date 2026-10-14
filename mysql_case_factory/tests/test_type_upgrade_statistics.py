from __future__ import annotations

import gzip
import json
import subprocess
import sys
from pathlib import Path

from mysql_case_factory.type_upgrade_statistics import (
    STATISTICS_BATCH_ID,
    STATISTICS_BATCH_KIND,
    STATISTICS_CASE_PREFIX,
    STATISTICS_PARENT_BATCH_ID,
    generate_statistics_cases,
    statistics_manifest,
    render_statistics_suite,
)


def test_statistics_batch_identity_is_separate() -> None:
    assert STATISTICS_BATCH_ID == "2026-10-14-type-upgrade-statistics-and-chain-v1"
    assert STATISTICS_BATCH_KIND == "statistics_and_chain_extension"
    assert STATISTICS_PARENT_BATCH_ID == "2026-10-13-type-upgrade-consistency-extension-v1"
    assert STATISTICS_CASE_PREFIX == "TUCS"


def test_statistics_cases_cover_system_tables_explain_partitions_and_chain() -> None:
    cases = generate_statistics_cases()

    assert cases
    assert len({case.case_id for case in cases}) == len(cases)
    assert all(case.case_id.startswith("TUCS-") for case in cases)
    assert all(case.batch_id == STATISTICS_BATCH_ID for case in cases)
    assert all(case.batch_kind == STATISTICS_BATCH_KIND for case in cases)
    assert all(case.parent_batch_id == STATISTICS_PARENT_BATCH_ID for case in cases)

    joined_setup = " ".join(" ".join(case.setup_sql) for case in cases)
    joined_stats = " ".join(
        " ".join(case.stats_pre_analyze_sql + case.stats_post_analyze_sql)
        for case in cases
    )
    joined_analyze = " ".join(" ".join(case.analyze_sql) for case in cases)
    joined_plans = " ".join(sql for case in cases for sql, _ in case.query_plans)

    for token in (
        "mysql.innodb_table_stats",
        "mysql.innodb_index_stats",
        "information_schema.STATISTICS",
        "information_schema.TABLES",
        "information_schema.PARTITIONS",
    ):
        assert token in joined_stats

    assert "ANALYZE TABLE" in joined_analyze
    assert "EXPLAIN FORMAT=JSON" in joined_plans

    partition_cases = [case for case in cases if case.table_form != "ordinary"]
    assert {"range_partition", "list_partition", "hash_partition", "key_partition"} <= {
        case.table_form for case in partition_cases
    }

    chain_cases = [case for case in cases if case.pre_ddl_sql]
    assert chain_cases
    assert any(
        "MODIFY target_col INT" in case.pre_ddl_sql[0]
        and "MODIFY target_col BIGINT" in case.ddl_sql
        for case in chain_cases
    )

    duplicate_cases = [case for case in cases if case.expected_outcome == "reject" and case.pre_ddl_sql == ()]
    assert duplicate_cases
    assert any(case.ddl_sql.count("MODIFY target_col") == 2 for case in duplicate_cases)


def test_statistics_generation_is_deterministic_and_manifest_is_consistent() -> None:
    first = generate_statistics_cases()
    second = generate_statistics_cases()
    assert [case.to_json() for case in first] == [case.to_json() for case in second]

    manifest = statistics_manifest(first, "copy")
    assert manifest["batch_id"] == STATISTICS_BATCH_ID
    assert manifest["batch_kind"] == STATISTICS_BATCH_KIND
    assert manifest["parent_batch_id"] == STATISTICS_PARENT_BATCH_ID
    assert manifest["case_id_prefix"] == STATISTICS_CASE_PREFIX
    assert manifest["case_count"] == len(first)
    assert manifest["gap_counts"]

    suite = render_statistics_suite(first, "copy")
    assert suite.count(f"-- BATCH_ID: {STATISTICS_BATCH_ID}") == len(first)


def test_statistics_generator_writes_deterministic_artifacts(tmp_path: Path) -> None:
    tool = Path(__file__).parents[1] / "tools" / "generate_type_upgrade_statistics.py"
    first = tmp_path / "first"
    second = tmp_path / "second"
    for output in (first, second):
        subprocess.run(
            [sys.executable, str(tool), "--output", str(output)],
            check=True,
            cwd=Path(__file__).parents[1],
        )

    required = {
        "cases.jsonl.gz",
        "copy_suite.sql.gz",
        "inplace_suite.sql.gz",
        "instant_suite.sql.gz",
        "manifest.json",
        "coverage.tsv",
        "README.md",
    }
    assert required <= {path.name for path in first.iterdir()}
    assert (first / "cases.jsonl.gz").read_bytes() == (second / "cases.jsonl.gz").read_bytes()
    assert (first / "copy_suite.sql.gz").read_bytes() == (second / "copy_suite.sql.gz").read_bytes()

    manifest = json.loads((first / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["batch_id"] == STATISTICS_BATCH_ID
    assert manifest["parent_batch_id"] == STATISTICS_PARENT_BATCH_ID

    with gzip.open(first / "cases.jsonl.gz", "rt", encoding="utf-8") as handle:
        payloads = [json.loads(line) for line in handle]
    assert all(payload["case_id"].startswith("TUCS-") for payload in payloads)
    assert all(payload["batch_id"] == STATISTICS_BATCH_ID for payload in payloads)


def test_partition_cases_use_partition_statistics_not_base_table_only() -> None:
    cases = generate_statistics_cases()
    partition_cases = [case for case in cases if case.table_form != "ordinary"]
    assert partition_cases
    for case in partition_cases:
        first_table_check = case.stats_pre_analyze_sql[0]
        assert "#p#%" in first_table_check
        assert "expected.suffix" in first_table_check
        assert "CONCAT(" in first_table_check


def test_all_declared_statistics_gap_ids_have_cases() -> None:
    from mysql_case_factory.type_upgrade_statistics import STATS_GAPS

    cases = generate_statistics_cases()
    counts = {gap: sum(case.gap_id == gap for case in cases) for gap in STATS_GAPS}
    assert all(count > 0 for count in counts.values())


def test_statistics_oracle_is_strong_for_nonempty_tables_and_indexes() -> None:
    cases = generate_statistics_cases()
    ordinary = [case for case in cases if case.table_form == "ordinary" and case.gap_id.startswith("GAP-STATS-")]
    assert ordinary
    for case in ordinary:
        table_checks = [sql for sql in case.stats_pre_analyze_sql if "mysql.innodb_table_stats" in sql]
        index_checks = [sql for sql in case.stats_pre_analyze_sql if "mysql.innodb_index_stats" in sql]
        assert any("n_rows > 0" in sql for sql in table_checks)
        assert any("sum_of_other_index_sizes > 0" in sql for sql in table_checks)
        assert any("index_name='PRIMARY'" in sql for sql in index_checks)
        expected_index = {
            "secondary": "idx_target",
            "unique": "uk_target",
            "composite": "idx_composite",
            "prefix": "idx_prefix",
            "descending": "idx_desc",
        }.get(case.index_profile, "idx_target")
        assert any(f"index_name='{expected_index}'" in sql for sql in index_checks)
        assert any("stat_value >= 0" in sql for sql in index_checks)
        assert any("sample_size >= 0" in sql for sql in index_checks)


def test_partition_oracle_checks_every_partition_and_index() -> None:
    cases = generate_statistics_cases()
    partition_cases = [case for case in cases if case.table_form != "ordinary"]
    assert partition_cases
    for case in partition_cases:
        table_checks = [sql for sql in case.stats_pre_analyze_sql if "mysql.innodb_table_stats" in sql]
        index_checks = [sql for sql in case.stats_pre_analyze_sql if "mysql.innodb_index_stats" in sql]
        assert any("CONCAT(" in sql and "expected.suffix" in sql for sql in table_checks + index_checks)
        assert any("index_name='PRIMARY'" in sql for sql in index_checks)
        expected_index = {
            "secondary": "idx_target",
            "unique": "uk_target",
            "composite": "idx_composite",
            "prefix": "idx_prefix",
            "descending": "idx_desc",
        }.get(case.index_profile, "idx_target")
        assert any(f"index_name='{expected_index}'" in sql for sql in index_checks)
        assert any("stat_value >= 0" in sql for sql in index_checks)
