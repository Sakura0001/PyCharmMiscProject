from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from mysql_case_factory.inplace_unique_conflict_audit import audit_inplace_unique_artifacts


def _generate(tmp_path: Path) -> Path:
    output = tmp_path / "inplace-unique"
    tool = Path(__file__).parents[1] / "tools" / "generate_inplace_unique_conflict.py"
    subprocess.run(
        [sys.executable, str(tool), "--output", str(output)],
        check=True,
        cwd=Path(__file__).parents[1],
    )
    return output


def test_inplace_unique_audit_accepts_structural_artifacts(tmp_path: Path) -> None:
    output = _generate(tmp_path)
    report = audit_inplace_unique_artifacts(output, require_local=False)
    assert report["passed"] is True
    assert report["operation_count"] == 12
    assert report["scenario_count"] == 2_304
    assert report["profile_counts"] == {
        "copy": 2_304,
        "inplace": 2_304,
        "instant": 2_304,
    }
    assert report["smoke_case_count"] == 12
    assert report["unique_operations"] is True
    assert report["unique_smoke_ids"] is True
    assert report["ddl_sql_ok"] is True
    assert report["forbidden_tokens_absent"] is True
    assert report["usage_documented"] is True
    assert (output / "audit_report.json").exists()
    assert (output / "audit_summary.md").exists()


def test_inplace_unique_audit_verifies_local_copy_smoke_evidence() -> None:
    root = Path(__file__).parents[1]
    output = root / "generated" / "inplace_unique_conflict_v1"
    report = audit_inplace_unique_artifacts(output, require_local=True)
    assert report["passed"] is True
    assert report["local_all_pass"] is True
    assert report["local_result_count"] == 12
    assert report["local_result_counts"] == {"PASS": 12}
    assert report["local_overlap_count"] == 12
    assert report["local_conflict_count"] == 12
    assert report["local_profile"] == "copy"
    assert report["mysqld_version"].startswith("8.0.45")

    local_summary = json.loads((output / "local_summary.json").read_text(encoding="utf-8"))
    assert local_summary["all_pass"] is True
    assert local_summary["profile"] == "copy"
