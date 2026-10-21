from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from mysql_case_factory.type_upgrade_performance_audit import audit_type_performance_artifacts


def _generate(tmp_path: Path) -> Path:
    output = tmp_path / "performance"
    tool = Path(__file__).parents[1] / "tools" / "generate_type_upgrade_performance.py"
    subprocess.run(
        [sys.executable, str(tool), "--output", str(output)],
        check=True,
        cwd=Path(__file__).parents[1],
    )
    return output


def test_type_performance_audit_accepts_structural_artifacts(tmp_path: Path) -> None:
    output = _generate(tmp_path)
    report = audit_type_performance_artifacts(output, require_local=False)
    assert report["passed"] is True
    assert report["case_count"] == 7
    assert report["scenario_count"] == 7
    assert report["upgrade_column_count"] == 31
    assert report["noise_column_count"] == 4
    assert report["unique_case_ids"] is True
    assert report["scenario_ok"] is True
    assert report["coverage_ok"] is True
    assert report["type_families_ok"] is True
    assert report["artifact_hashes_ok"] is True
    assert report["usage_documented"] is True
    assert (output / "audit_report.json").exists()
    assert (output / "audit_summary.md").exists()


def test_type_performance_audit_verifies_local_evidence() -> None:
    root = Path(__file__).parents[1]
    output = root / "generated" / "type_upgrade_performance_v1"
    report = audit_type_performance_artifacts(output, require_local=True)
    assert report["passed"] is True
    assert report["local_result_count"] == 3
    assert report["local_pass_count"] == 3
    assert report["local_all_pass"] is True
    assert report["local_metadata_ok"] is True
    assert report["mysqld_version"].startswith("8.0.45")
