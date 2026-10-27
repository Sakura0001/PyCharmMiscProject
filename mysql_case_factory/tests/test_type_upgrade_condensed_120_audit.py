from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from mysql_case_factory.type_upgrade_condensed_120_audit import audit_condensed_120_artifacts


def _generate(tmp_path: Path) -> Path:
    output = tmp_path / "condensed"
    tool = Path(__file__).parents[1] / "tools" / "generate_type_upgrade_condensed_120.py"
    subprocess.run(
        [sys.executable, str(tool), "--output", str(output)],
        check=True,
        cwd=Path(__file__).parents[1],
    )
    return output


def test_condensed_120_audit_accepts_structural_artifacts(tmp_path: Path) -> None:
    output = _generate(tmp_path)
    report = audit_condensed_120_artifacts(output, require_local=False)
    assert report["passed"] is True
    assert report["case_count"] == 120
    assert report["sql_file_count"] == 120
    assert report["expected_output_line_count"] == 240
    assert report["unique_case_ids"] is True
    assert report["sql_count_ok"] is True
    assert report["sql_case_ids_ok"] is True
    assert report["expected_output_ok"] is True
    assert report["sql_contract_ok"] is True
    assert report["artifact_hashes_ok"] is True
    assert report["usage_documented"] is True
    assert (output / "audit_report.json").exists()
    assert (output / "audit_summary.md").exists()


def test_condensed_120_audit_verifies_local_copy_evidence() -> None:
    root = Path(__file__).parents[1]
    output = root / "generated" / "type_upgrade_condensed_120_v1"
    report = audit_condensed_120_artifacts(output, require_local=True)
    assert report["passed"] is True
    assert report["local_metadata_ok"] is True
    assert report["local_copy_result_line_count"] == 224
    assert report["local_copy_pass_count"] == 224
    assert report["mysqld_version"].startswith("8.0.45")
