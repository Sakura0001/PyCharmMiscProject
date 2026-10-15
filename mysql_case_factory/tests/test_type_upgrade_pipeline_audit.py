from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from mysql_case_factory.type_upgrade_pipeline_audit import audit_pipeline_artifacts


def _generate(tmp_path: Path) -> Path:
    output = tmp_path / "pipeline"
    tool = Path(__file__).parents[1] / "tools" / "generate_type_upgrade_pipeline.py"
    subprocess.run([sys.executable, str(tool), "--output", str(output)], check=True, cwd=Path(__file__).parents[1])
    return output


def test_pipeline_audit_accepts_deterministic_structural_artifacts(tmp_path: Path) -> None:
    output = _generate(tmp_path)
    report = audit_pipeline_artifacts(output, parent_case_paths=(), require_local=False)
    assert report["passed"] is True
    assert report["case_count"] == 50
    assert report["profile_counts"] == {"copy": 50, "inplace": 50, "instant": 50}
    assert report["unique_table_count"] >= 100
    assert report["unique_index_count"] >= 50
    assert report["index_naming_ok"] is True
    assert report["parent_case_id_overlap_count"] == 0
    assert report["forbidden_types_absent"] is True
    assert report["semantic_coverage_ok"] is True
    assert (output / "audit_report.json").exists()
    assert (output / "audit_summary.md").exists()


def test_pipeline_audit_verifies_local_copy_evidence_and_parent_isolation() -> None:
    root = Path(__file__).parents[1]
    output = root / "generated" / "type_upgrade_pipeline_v1"
    parents = [
        root / "generated" / "type_upgrade_consistency" / "cases.jsonl.gz",
        root / "generated" / "type_upgrade_consistency_extension_v1" / "cases.jsonl.gz",
        root / "generated" / "type_upgrade_statistics_v1" / "cases.jsonl.gz",
    ]
    report = audit_pipeline_artifacts(output, parent_case_paths=parents, require_local=True)
    assert report["passed"] is True
    assert report["local_all_pass"] is True
    assert report["local_result_count"] == 52
    assert report["local_result_counts"] == {"PASS": 52}
    assert report["parent_case_id_overlap_count"] == 0

    summary = json.loads((output / "local_summary.json").read_text(encoding="utf-8"))
    assert summary["all_pass"] is True
    assert summary["mysqld_version"].startswith("8.0.45")
