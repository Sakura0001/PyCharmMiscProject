from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from mysql_case_factory.type_upgrade_boundary_audit import audit_boundary_artifacts


def _generate(tmp_path: Path) -> Path:
    output = tmp_path / "boundary"
    tool = Path(__file__).parents[1] / "tools" / "generate_type_upgrade_boundary.py"
    subprocess.run(
        [sys.executable, str(tool), "--output", str(output)],
        check=True,
        cwd=Path(__file__).parents[1],
    )
    return output


def test_boundary_audit_accepts_structural_artifacts(tmp_path: Path) -> None:
    output = _generate(tmp_path)
    report = audit_boundary_artifacts(output, parent_case_paths=(), require_local=False)
    assert report["passed"] is True
    assert report["case_count"] == 750
    assert report["profile_counts"] == {"copy": 750, "inplace": 750, "instant": 750}
    assert report["category_counts"] == {
        "zero_core": 512,
        "zero_cross": 112,
        "decimal_max": 64,
        "variable_max": 20,
        "variable_overflow": 10,
        "alias_normalization": 32,
    }
    assert report["parent_case_id_overlap_count"] == 0
    assert report["unique_table_count"] >= 750
    assert report["forbidden_types_absent"] is True
    assert report["two_stage_with_intermediate_insert"] is True
    assert report["semantic_coverage_ok"] is True
    assert (output / "audit_report.json").exists()
    assert (output / "audit_summary.md").exists()


def test_boundary_audit_verifies_local_copy_and_parent_isolation() -> None:
    root = Path(__file__).parents[1]
    output = root / "generated" / "type_upgrade_boundary_v1"
    parents = [
        root / "generated" / "type_upgrade_consistency" / "cases.jsonl.gz",
        root / "generated" / "type_upgrade_consistency_extension_v1" / "cases.jsonl.gz",
        root / "generated" / "type_upgrade_statistics_v1" / "cases.jsonl.gz",
        root / "generated" / "type_upgrade_pipeline_v1" / "cases.jsonl.gz",
    ]
    report = audit_boundary_artifacts(output, parent_case_paths=parents, require_local=True)
    assert report["passed"] is True
    assert report["local_all_pass"] is True
    assert report["local_result_count"] == 752
    assert report["local_result_counts"] == {"PASS": 752}
    assert report["parent_case_id_overlap_count"] == 0

    summary = json.loads((output / "local_summary.json").read_text(encoding="utf-8"))
    assert summary["all_pass"] is True
    assert summary["mysqld_version"].startswith("8.0.45")
