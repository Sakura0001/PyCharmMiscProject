from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from mysql_case_factory.unique_ddl_expected_error_audit import audit_unique_ddl_error_artifacts


def _generate(tmp_path: Path) -> Path:
    output = tmp_path / "unique-ddl"
    tool = Path(__file__).parents[1] / "tools" / "generate_unique_ddl_expected_error.py"
    subprocess.run(
        [sys.executable, str(tool), "--output", str(output)],
        check=True,
        cwd=Path(__file__).parents[1],
    )
    return output


def test_unique_ddl_audit_accepts_structural_artifacts(tmp_path: Path) -> None:
    output = _generate(tmp_path)
    report = audit_unique_ddl_error_artifacts(output, require_local=False)
    assert report["passed"] is True
    assert report["case_count"] == 192
    assert report["smoke_case_count"] == 6
    assert report["ddl_form_count"] == 4
    assert report["shape_count"] == 6
    assert report["dml_type_count"] == 8
    assert report["unique_case_ids"] is True
    assert report["matrix_ok"] is True
    assert report["expected_codes_ok"] is True
    assert report["smoke_ok"] is True
    assert report["artifact_hashes_ok"] is True
    assert report["usage_documented"] is True
    assert (output / "audit_report.json").exists()
    assert (output / "audit_summary.md").exists()


def test_unique_ddl_audit_verifies_local_full_evidence() -> None:
    root = Path(__file__).parents[1]
    output = root / "generated" / "unique_ddl_expected_error_v1"
    report = audit_unique_ddl_error_artifacts(output, require_local=True)
    assert report["passed"] is True
    assert report["local_result_count"] == 192
    assert report["local_pass_count"] == 192
    assert report["local_overlap_count"] == 192
    assert report["local_duplicate_error_count"] == 192
    assert report["local_all_pass"] is True
    assert report["mysqld_version"].startswith("8.0.45")

    summary = json.loads((output / "local_summary.json").read_text(encoding="utf-8"))
    assert summary["all_pass"] is True
    assert summary["rows_per_shape"] == report["rows_per_shape"]
