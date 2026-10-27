from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

from mysql_case_factory.type_upgrade_condensed_120 import (
    CONDENSED_120_BATCH_ID,
    CONDENSED_120_CASE_PREFIX,
    CONDENSED_120_DATABASE,
    condensed_120_scenarios,
    render_condensed_case,
)


def test_batch_identity_and_exact_case_space() -> None:
    scenarios = condensed_120_scenarios()
    assert CONDENSED_120_BATCH_ID == "2026-10-27-type-upgrade-condensed-120-v1"
    assert CONDENSED_120_CASE_PREFIX == "TUCR"
    assert CONDENSED_120_DATABASE == "qa_type_upgrade_condensed_120"
    assert len(scenarios) == 120
    assert scenarios[0].case_id == "TUCR-000001"
    assert scenarios[-1].case_id == "TUCR-000120"
    assert [scenario.case_id for scenario in scenarios] == [
        f"TUCR-{number:06d}" for number in range(1, 121)
    ]


def test_category_counts_are_exact() -> None:
    categories = Counter(scenario.category for scenario in condensed_120_scenarios())
    assert categories == {
        "core": 76,
        "position": 2,
        "auto_increment": 6,
        "foreign_key": 8,
        "dependency": 9,
        "table_form": 10,
        "chain": 1,
        "multi_column": 4,
        "statistics": 4,
    }


def test_each_sql_case_contains_both_algorithms_and_reference_table() -> None:
    for scenario in condensed_120_scenarios():
        sql = render_condensed_case(scenario)
        assert "ALGORITHM=INPLACE, LOCK=NONE" in sql
        assert "ALGORITHM=INSTANT" in sql
        assert scenario.inplace_table in sql
        assert scenario.instant_table in sql
        assert scenario.reference_table in sql
        assert sql.count("-- INPLACE stable result") == 1
        assert sql.count("-- INSTANT stable result") == 1
        assert "SET SESSION" not in sql
        assert "SELECT *" not in sql


def test_zero_length_semantics_are_present() -> None:
    scenarios = {scenario.case_id: scenario for scenario in condensed_120_scenarios()}
    assert scenarios["TUCR-000037"].columns[0].source_type == "CHAR(0)"
    assert scenarios["TUCR-000043"].columns[0].source_type == "VARCHAR(0)"
    assert scenarios["TUCR-000049"].columns[0].source_type == "BINARY(0)"
    assert scenarios["TUCR-000055"].columns[0].source_type == "VARBINARY(0)"
    assert scenarios["TUCR-000069"].columns[0].source_type == "CHAR(0)"
    assert scenarios["TUCR-000069"].columns[0].target_type == "BINARY(1)"
    assert scenarios["TUCR-000070"].columns[0].source_type == "BINARY(0)"
    assert scenarios["TUCR-000070"].columns[0].target_type == "CHAR(1)"


def test_generator_writes_deterministic_120_files(tmp_path: Path) -> None:
    tool = Path(__file__).parents[1] / "tools" / "generate_type_upgrade_condensed_120.py"
    first = tmp_path / "first"
    second = tmp_path / "second"
    for output in (first, second):
        subprocess.run(
            [sys.executable, str(tool), "--output", str(output)],
            check=True,
            cwd=Path(__file__).parents[1],
        )

    manifest = json.loads((first / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["batch_id"] == CONDENSED_120_BATCH_ID
    assert manifest["case_count"] == 120
    assert manifest["sql_file_count"] == 120
    assert manifest["expected_output_line_count"] == 240
    assert manifest["materialization"] == "sql_directory"

    sql_files = list((first / "sql").glob("TUCR-*.sql"))
    assert len(sql_files) == 120
    expected_lines = (first / "expected_output.tsv").read_text(encoding="utf-8").splitlines()
    assert len(expected_lines) == 240
    assert all(line.endswith("\tPASS") for line in expected_lines)

    for name in ("manifest.json", "coverage.tsv", "expected_output.tsv", "README.md"):
        assert (first / name).read_bytes() == (second / name).read_bytes()
    for path in sql_files:
        assert path.read_bytes() == (second / "sql" / path.name).read_bytes()
