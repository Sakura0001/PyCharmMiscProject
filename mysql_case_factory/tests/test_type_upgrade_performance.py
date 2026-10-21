from __future__ import annotations

import gzip
import json
import subprocess
import sys
from pathlib import Path

from mysql_case_factory.type_upgrade_performance import (
    NOISE_COLUMNS,
    SCENARIOS,
    TYPE_PERFORMANCE_BATCH_ID,
    TYPE_PERFORMANCE_CASE_PREFIX,
    TYPE_PERFORMANCE_DATABASE,
    TYPE_PERFORMANCE_PROFILE,
    UPGRADE_COLUMNS,
    build_copy_source_sql,
    build_ddl_sql,
    build_full_scan_query,
    build_generate_source_sql,
    build_reference_table_sql,
    build_source_table_sql,
    type_performance_scenarios,
)


def test_batch_identity_and_scenario_space() -> None:
    assert TYPE_PERFORMANCE_BATCH_ID == "2026-10-21-type-upgrade-performance-v1"
    assert TYPE_PERFORMANCE_CASE_PREFIX == "TUCPF"
    assert TYPE_PERFORMANCE_DATABASE == "qa_type_upgrade_performance"
    assert TYPE_PERFORMANCE_PROFILE == "performance"
    assert SCENARIOS == (
        "source_baseline",
        "all_copy",
        "all_inplace",
        "all_instant",
        "mixed_inplace_first",
        "mixed_instant_first",
        "reference",
    )

    scenarios = type_performance_scenarios()
    assert len(scenarios) == 7
    assert [scenario.case_id for scenario in scenarios] == [
        "TUCPF-000001",
        "TUCPF-000002",
        "TUCPF-000003",
        "TUCPF-000004",
        "TUCPF-000005",
        "TUCPF-000006",
        "TUCPF-000007",
    ]


def test_all_upgradeable_type_families_are_covered() -> None:
    assert len(UPGRADE_COLUMNS) == 31
    prefixes = {column for column, _, _ in UPGRADE_COLUMNS}
    assert any(column.startswith("i_") for column in prefixes)
    assert any(column.startswith("dec_") for column in prefixes)
    assert any(column.startswith("bit_") for column in prefixes)
    assert any(column.startswith(("char_", "varchar_")) for column in prefixes)
    assert any(column.startswith(("binary_", "varbinary_")) for column in prefixes)
    assert any("text" in column for column in prefixes)
    assert any("blob" in column for column in prefixes)

    assert NOISE_COLUMNS == (
        ("noise_float", "FLOAT"),
        ("noise_double", "DOUBLE"),
        ("noise_date", "DATE"),
        ("noise_json", "JSON"),
    )


def test_source_and_reference_schemas_cover_all_columns() -> None:
    source_sql = build_source_table_sql()
    reference_sql = build_reference_table_sql()
    for column, source_type, target_type in UPGRADE_COLUMNS:
        assert f"`{column}` {source_type} NULL" in source_sql
        assert f"`{column}` {target_type} NULL" in reference_sql
    for column, noise_type in NOISE_COLUMNS:
        assert f"`{column}` {noise_type} NULL" in source_sql
        assert f"`{column}` {noise_type} NULL" in reference_sql
    assert "PRIMARY KEY(id)" in source_sql
    assert "KEY idx_i_int(`i_int`)" in source_sql
    assert "KEY idx_varchar_255(`varchar_255`)" in source_sql


def test_generate_sql_contains_boundary_and_large_values() -> None:
    sql = build_generate_source_sql(rows=12_000_000)
    assert "LIMIT 12000000" in sql
    assert "9223372036854775807" in sql
    assert "18446744073709551615" in sql
    assert "99999999999999999999.999999999999999999" in sql
    assert "REPEAT(UNHEX('01')" in sql
    assert "CAST(CONCAT('{\"n\":'," in sql


def test_copy_sql_copies_every_column() -> None:
    sql = build_copy_source_sql()
    for column, _, _ in UPGRADE_COLUMNS:
        assert f"`{column}`" in sql
    for column, _ in NOISE_COLUMNS:
        assert f"`{column}`" in sql


def test_full_scan_query_reads_every_upgradeable_column() -> None:
    sql = build_full_scan_query("tab_tucpf_candidate")
    assert sql.startswith("SELECT COUNT(*)")
    for column, _, _ in UPGRADE_COLUMNS:
        assert column in sql
    assert "SUM(LENGTH(noise_json))" in sql


def test_ddl_sql_covers_all_algorithms_and_mixed_scenarios() -> None:
    all_copy = build_ddl_sql("all_copy")
    assert len(all_copy) == 1
    assert "ALGORITHM=COPY" in all_copy[0]

    all_inplace = build_ddl_sql("all_inplace")
    assert len(all_inplace) == 1
    assert "ALGORITHM=INPLACE" in all_inplace[0]
    assert "LOCK=NONE" in all_inplace[0]

    all_instant = build_ddl_sql("all_instant")
    assert len(all_instant) == 1
    assert "ALGORITHM=INSTANT" in all_instant[0]

    mixed_inplace_first = build_ddl_sql("mixed_inplace_first")
    assert len(mixed_inplace_first) == 2
    assert "ALGORITHM=INPLACE" in mixed_inplace_first[0]
    assert "ALGORITHM=INSTANT" in mixed_inplace_first[1]

    mixed_instant_first = build_ddl_sql("mixed_instant_first")
    assert len(mixed_instant_first) == 2
    assert "ALGORITHM=INSTANT" in mixed_instant_first[0]
    assert "ALGORITHM=INPLACE" in mixed_instant_first[1]


def test_generator_writes_deterministic_artifacts(tmp_path: Path) -> None:
    tool = Path(__file__).parents[1] / "tools" / "generate_type_upgrade_performance.py"
    first = tmp_path / "first"
    second = tmp_path / "second"
    for output in (first, second):
        subprocess.run(
            [sys.executable, str(tool), "--output", str(output)],
            check=True,
            cwd=Path(__file__).parents[1],
        )

    manifest = json.loads((first / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["batch_id"] == TYPE_PERFORMANCE_BATCH_ID
    assert manifest["case_count"] == 7
    assert manifest["scenario_count"] == 7
    assert manifest["upgrade_column_count"] == 31
    assert manifest["noise_column_count"] == 4
    assert manifest["materialization"] == "virtual_runner"

    with gzip.open(first / "cases.jsonl.gz", "rt", encoding="utf-8") as handle:
        cases = [json.loads(line) for line in handle]
    assert len(cases) == 7
    assert all(case["case_id"].startswith("TUCPF-") for case in cases)

    for name in ("manifest.json", "cases.jsonl.gz", "coverage.tsv", "README.md"):
        assert (first / name).read_bytes() == (second / name).read_bytes()
