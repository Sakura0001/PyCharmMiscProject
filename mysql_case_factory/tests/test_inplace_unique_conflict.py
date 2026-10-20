from __future__ import annotations

import gzip
import json
import subprocess
import sys
from pathlib import Path

from mysql_case_factory.inplace_unique_conflict import (
    INPLACE_UNIQUE_BATCH_ID,
    INPLACE_UNIQUE_BATCH_KIND,
    INPLACE_UNIQUE_CASE_PREFIX,
    INPLACE_UNIQUE_DATABASE,
    INPLACE_UNIQUE_PROFILES,
    inplace_unique_operations,
    iter_inplace_unique_scenarios,
    smoke_inplace_unique_scenarios,
)


def test_inplace_unique_batch_identity_and_operation_scale() -> None:
    assert INPLACE_UNIQUE_BATCH_ID == "2026-10-20-inplace-ddl-unique-conflict-v1"
    assert INPLACE_UNIQUE_BATCH_KIND == "inplace_unique_conflict_extension"
    assert INPLACE_UNIQUE_CASE_PREFIX == "TUCUI"
    assert INPLACE_UNIQUE_DATABASE == "qa_inplace_unique_conflict"
    assert INPLACE_UNIQUE_PROFILES == ("copy", "inplace", "instant")

    operations = inplace_unique_operations()
    assert len(operations) == 12
    assert len({operation.operation_id for operation in operations}) == 12
    assert {
        "add_index",
        "drop_index",
        "add_unique",
        "drop_unique",
        "rename_index",
        "add_column",
        "drop_column",
        "rename_column",
        "add_foreign_key",
        "drop_foreign_key",
        "drop_check",
        "drop_generated",
    } == {operation.operation_id for operation in operations}


def test_inplace_unique_operation_sql_uses_inplace_and_lock_none() -> None:
    for operation in inplace_unique_operations():
        assert "ALGORITHM=INPLACE" in operation.ddl_sql
        assert "LOCK=NONE" in operation.ddl_sql
        assert "MODIFY" not in operation.ddl_sql.upper()
        assert "CHANGE" not in operation.ddl_sql.upper()


def test_inplace_unique_scenario_space_is_exact_lazy_and_deterministic() -> None:
    scenarios = iter_inplace_unique_scenarios()
    first = next(scenarios)
    assert first.case_id == "TUCUI-000001"
    assert first.operation_id == "add_index"

    count = 0
    last = None
    for scenario in iter_inplace_unique_scenarios():
        last = scenario
        count += 1
    assert count == 2_304
    assert last is not None
    assert last.case_id == "TUCUI-002304"

    assert [s.case_id for s in smoke_inplace_unique_scenarios()] == [
        s.case_id for s in smoke_inplace_unique_scenarios()
    ]


def test_inplace_unique_factor_matrix_is_complete() -> None:
    scenarios = list(iter_inplace_unique_scenarios())
    assert {s.conflict_surface for s in scenarios} == {
        "existing_unique",
        "new_unique",
        "composite_unique",
        "nullable_unique",
    }
    assert {s.conflict_pattern for s in scenarios} == {
        "seed_duplicate",
        "concurrent_duplicate",
        "semantic_collision",
        "boundary_duplicate",
    }
    assert {s.phase for s in scenarios} == {
        "during_ddl",
        "before_and_during_ddl",
        "across_ddl_transaction",
    }
    assert {s.workers for s in scenarios} == {4, 16}
    assert {s.data_state for s in scenarios} == {"normal", "boundary"}


def test_inplace_unique_smoke_has_one_scenario_per_operation() -> None:
    smoke = smoke_inplace_unique_scenarios()
    assert len(smoke) == 12
    assert len({s.operation_id for s in smoke}) == 12
    assert all(s.conflict_surface == "existing_unique" for s in smoke)
    assert all(s.conflict_pattern == "seed_duplicate" for s in smoke)
    assert all(s.phase == "during_ddl" for s in smoke)
    assert all(s.workers == 4 for s in smoke)
    assert all(s.data_state == "normal" for s in smoke)


def test_inplace_unique_generator_writes_deterministic_artifacts(tmp_path: Path) -> None:
    tool = Path(__file__).parents[1] / "tools" / "generate_inplace_unique_conflict.py"
    first = tmp_path / "first"
    second = tmp_path / "second"
    for output in (first, second):
        subprocess.run(
            [sys.executable, str(tool), "--output", str(output)],
            check=True,
            cwd=Path(__file__).parents[1],
        )

    manifest = json.loads((first / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["batch_id"] == INPLACE_UNIQUE_BATCH_ID
    assert manifest["operation_count"] == 12
    assert manifest["scenario_count"] == 2_304
    assert manifest["smoke_case_count"] == 12
    assert manifest["profile_counts"] == {
        profile: 2_304 for profile in INPLACE_UNIQUE_PROFILES
    }
    assert manifest["materialization"] == "virtual_lazy_runner"
    assert manifest["forbidden_types_absent"] is True

    with gzip.open(first / "smoke_cases.jsonl.gz", "rt", encoding="utf-8") as handle:
        smoke = [json.loads(line) for line in handle]
    assert len(smoke) == 12
    assert all(case["case_id"].startswith("TUCUI-") for case in smoke)

    for name in ("manifest.json", "smoke_cases.jsonl.gz", "coverage.tsv", "README.md"):
        assert (first / name).read_bytes() == (second / name).read_bytes()
