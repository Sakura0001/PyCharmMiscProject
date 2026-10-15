from __future__ import annotations

import gzip
import json
import subprocess
import sys
from pathlib import Path

from mysql_case_factory.type_upgrade_pipeline import (
    PIPELINE_BATCH_ID,
    PIPELINE_BATCH_KIND,
    PIPELINE_CASE_PREFIX,
    PIPELINE_PROFILES,
    PIPELINE_ROW_COUNT,
    generate_pipeline_cases,
    pipeline_manifest,
    render_pipeline_case,
    write_pipeline_artifacts,
)


def test_pipeline_batch_identity_and_scale() -> None:
    assert PIPELINE_BATCH_ID == "2026-10-15-type-upgrade-pipeline-v1"
    assert PIPELINE_BATCH_KIND == "pipeline_condensed_batch"
    assert PIPELINE_CASE_PREFIX == "TUCP"
    assert PIPELINE_PROFILES == ("copy", "inplace", "instant")
    assert PIPELINE_ROW_COUNT == 192

    cases = generate_pipeline_cases()
    assert len(cases) == 50
    assert len({case.case_id for case in cases}) == 50
    assert all(case.case_id.startswith("TUCP-") for case in cases)
    assert all(case.batch_id == PIPELINE_BATCH_ID for case in cases)


def test_pipeline_scenarios_cover_core_factor_families() -> None:
    cases = generate_pipeline_cases()
    families = {case.family for case in cases}
    assert {
        "integer",
        "decimal",
        "character",
        "binary",
        "bit",
        "foreign_key",
        "dependency",
        "statistics",
        "table_form",
    } <= families

    bit_cases = [case for case in cases if case.family == "bit"]
    assert len(bit_cases) >= 10
    assert any(case.source_type == "BIT(63)" and case.target_type == "BIT(64)" for case in bit_cases)

    index_profiles = {case.index_profile for case in cases}
    assert {
        "secondary",
        "unique",
        "composite",
        "prefix",
        "descending",
        "functional",
        "primary",
    } <= index_profiles

    assert any(case.chained for case in cases)
    assert any(case.multi_column for case in cases)
    assert any(case.foreign_key_action for case in cases)
    assert any(case.stats_profile for case in cases)
    assert any(case.partition_form != "ordinary" for case in cases)
    assert any(case.engine != "InnoDB" for case in cases)
    assert any(case.dependency_profile == "view_trigger_function_procedure" for case in cases)


def test_pipeline_rendering_is_pipeline_safe_and_deterministic() -> None:
    cases = generate_pipeline_cases()
    rendered = [render_pipeline_case(case, "copy") for case in cases]
    assert rendered == [render_pipeline_case(case, "copy") for case in generate_pipeline_cases()]

    forbidden = (
        "FLOAT",
        "DOUBLE",
        "REAL",
        " DATE",
        "TIME",
        "DATETIME",
        "TIMESTAMP",
        "YEAR",
        "ENUM",
        "SET(",
        "JSON",
        "POINT",
        "LINESTRING",
        "POLYGON",
        "FULLTEXT",
        "SPATIAL",
        "VECTOR",
    )
    for case, sql in zip(cases, rendered, strict=True):
        sql = sql.split("-- @@@EXPECTED@@@")[0]
        lines = sql.splitlines()
        assert 220 <= len(lines) <= 520, (case.case_id, len(lines))
        assert "SET SESSION" not in sql
        assert "SET GLOBAL" not in sql
        assert "DELIMITER" not in sql
        assert not any(token in sql.upper() for token in forbidden), case.case_id

        executable = [line.strip() for line in lines if line.strip() and not line.lstrip().startswith("--")]
        assert executable[0].startswith("DROP TABLE IF EXISTS tab_tucp_")
        assert executable[-1].startswith("DROP TABLE IF EXISTS tab_tucp_")
        assert f"ALGORITHM=COPY" in sql
        assert sql.count("-- CASE_ID: ") == 1
        assert sql.count("-- BATCH_ID: ") == 1
        assert sql.count("-- PROFILE: copy") == 1

    table_names: set[str] = set()
    for sql in rendered:
        for line in sql.splitlines():
            stripped = line.strip()
            if stripped.startswith("CREATE TABLE "):
                table_name = stripped.split()[2]
                assert table_name not in table_names, table_name
                table_names.add(table_name)
    assert len(table_names) >= 100


def test_pipeline_expected_output_is_stable_across_profiles() -> None:
    cases = generate_pipeline_cases()
    for case in cases:
        outputs = [render_pipeline_case(case, profile).split("@@@EXPECTED@@@")[1] for profile in PIPELINE_PROFILES]
        assert len(set(outputs)) == 1
        expected_lines = outputs[0].strip().splitlines()
        assert expected_lines
        assert all(line.endswith("|OK") or "\tanalyze\tstatus\tOK" in line for line in expected_lines)
        assert all("FAIL" not in line for line in expected_lines)


def test_pipeline_generator_writes_deterministic_artifacts(tmp_path: Path) -> None:
    tool = Path(__file__).parents[1] / "tools" / "generate_type_upgrade_pipeline.py"
    first = tmp_path / "first"
    second = tmp_path / "second"
    for output in (first, second):
        subprocess.run(
            [sys.executable, str(tool), "--output", str(output)],
            check=True,
            cwd=Path(__file__).parents[1],
        )

    for profile in PIPELINE_PROFILES:
        first_files = sorted((first / profile).glob("*.sql"))
        second_files = sorted((second / profile).glob("*.sql"))
        assert len(first_files) == 50
        assert len(second_files) == 50
        assert [path.read_bytes() for path in first_files] == [path.read_bytes() for path in second_files]

    manifest = json.loads((first / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["batch_id"] == PIPELINE_BATCH_ID
    assert manifest["case_count"] == 50
    assert manifest["profile_counts"] == {profile: 50 for profile in PIPELINE_PROFILES}
    assert manifest["forbidden_types_absent"] is True
    assert manifest["artifacts_sha256"]

    with gzip.open(first / "cases.jsonl.gz", "rt", encoding="utf-8") as handle:
        payloads = [json.loads(line) for line in handle]
    assert len(payloads) == 50
    assert all(payload["batch_id"] == PIPELINE_BATCH_ID for payload in payloads)

    write_pipeline_artifacts(second)
    assert (first / "expected_output.tsv").read_bytes() == (second / "expected_output.tsv").read_bytes()


def test_pipeline_rendering_avoids_known_mysql_8_compatibility_traps() -> None:
    cases = generate_pipeline_cases()
    by_id = {case.case_id: case for case in cases}

    memory_sql = render_pipeline_case(by_id["TUCP-000018"], "copy").split("-- @@@EXPECTED@@@")[0]
    assert "wide_col MEDIUMTEXT" not in memory_sql
    assert "ENGINE=MEMORY" in memory_sql

    functional_sql = render_pipeline_case(by_id["TUCP-000006"], "copy").split("-- @@@EXPECTED@@@")[0]
    assert "CAST(target_col AS CHAR(32))" in functional_sql

    long_prefixes = {"TUCP-000021": 191, "TUCP-000022": 63, "TUCP-000028": 191}
    for case_id, prefix_length in long_prefixes.items():
        sql = render_pipeline_case(by_id[case_id], "copy").split("-- @@@EXPECTED@@@")[0]
        assert f"target_col({prefix_length})" in sql, case_id

    binary_prefix = by_id["TUCP-000023"].scenario
    assert binary_prefix.source_type == "BINARY(16)"
    assert binary_prefix.target_type == "BINARY(32)"

    for case_id in ("TUCP-000040", "TUCP-000041", "TUCP-000042", "TUCP-000043"):
        sql = render_pipeline_case(by_id[case_id], "copy").split("-- @@@EXPECTED@@@")[0]
        assert "FOREIGN KEY (target_col)" not in sql
        assert "FOREIGN KEY (fk_col)" in sql
        assert f"KEY idx_tucp_{case_id[-3:]}_fk (fk_col)" in sql

    partition_sql = render_pipeline_case(by_id["TUCP-000049"], "copy").split("-- @@@EXPECTED@@@")[0]
    create_line = next(line for line in partition_sql.splitlines() if line.startswith("CREATE TABLE "))
    assert create_line.index("ENGINE=InnoDB") < create_line.index("PARTITION BY RANGE")



def test_partition_statistics_sql_has_balanced_concat_arguments() -> None:
    cases = generate_pipeline_cases()
    case = next(case for case in cases if case.case_id == "TUCP-000049")
    sql = render_pipeline_case(case, "copy").split("-- @@@EXPECTED@@@")[0]
    assert "expected.suffix)" in sql
    assert "expected.suffix')" not in sql


def test_tinytext_boundary_values_stay_within_byte_limit() -> None:
    cases = generate_pipeline_cases()
    case = next(case for case in cases if case.case_id == "TUCP-000022")
    sql = render_pipeline_case(case, "copy").split("-- @@@EXPECTED@@@")[0]
    insert_lines = [line for line in sql.splitlines() if line.startswith("INSERT INTO tab_tucp_022_")]
    assert insert_lines
    assert all("中" not in line for line in insert_lines)


def test_pipeline_sql_has_no_blank_line_at_eof() -> None:
    cases = generate_pipeline_cases()
    for case in cases:
        sql = render_pipeline_case(case, "copy").split("-- @@@EXPECTED@@@")[0]
        assert sql.endswith(";\n"), case.case_id
        assert not sql.endswith("\n\n"), case.case_id
        assert 413 <= len(sql.splitlines()) <= 426, case.case_id
