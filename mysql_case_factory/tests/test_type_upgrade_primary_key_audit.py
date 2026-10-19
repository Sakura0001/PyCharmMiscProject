from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from mysql_case_factory.type_upgrade_primary_key_audit import audit_primary_key_artifacts


def _generate(tmp_path: Path) -> Path:
    output = tmp_path / "primary-key"
    tool = Path(__file__).parents[1] / "tools" / "generate_type_upgrade_primary_key.py"
    subprocess.run(
        [sys.executable, str(tool), "--output", str(output)],
        check=True,
        cwd=Path(__file__).parents[1],
    )
    return output


def test_primary_key_audit_accepts_structural_artifacts(tmp_path: Path) -> None:
    output = _generate(tmp_path)
    report = audit_primary_key_artifacts(output, require_local=False)
    assert report["passed"] is True
    assert report["transition_count"] == 107
    assert report["scenario_count"] == 946_944
    assert report["profile_counts"] == {
        "copy": 946_944,
        "inplace": 946_944,
        "instant": 946_944,
    }
    assert report["smoke_case_count"] == 107
    assert report["smoke_case_prefix"] == "TUCPKS"
    assert report["parent_case_id_overlap_count"] == 0
    assert report["forbidden_types_absent"] is True
    assert report["char_varchar_instant_matrix_ok"] is True
    assert report["text_blob_prefix_matrix_ok"] is True
    assert report["usage_documented"] is True
    assert (output / "audit_report.json").exists()
    assert (output / "audit_summary.md").exists()


def test_primary_key_audit_verifies_local_smoke_and_during_evidence() -> None:
    root = Path(__file__).parents[1]
    output = root / "generated" / "type_upgrade_primary_key_concurrency_v1"
    report = audit_primary_key_artifacts(output, require_local=True)
    assert report["passed"] is True
    assert report["local_all_pass"] is True
    assert report["local_result_count"] == 107
    assert report["local_result_counts"] == {"PASS": 107}
    assert report["during_all_pass"] is True
    assert report["during_result_count"] == 10
    assert report["during_overlap_count"] == 10
    assert report["across_all_pass"] is True
    assert report["pre_during_post_all_pass"] is True
    assert report["retry_all_pass"] is True
    assert report["retry_source_range_retries"] >= 1
    assert report["multi_row_all_pass"] is True
    assert report["multi_row_result_count"] == 2
    assert report["strict_post_all_pass"] is True
    assert report["strict_post_result_count"] == 3
    assert report["strict_post_overlap_count"] == 0
    assert report["expected_reject_all_pass"] is True
    assert report["expected_reject_result_count"] == 1

    local_summary = json.loads((output / "local_summary.json").read_text(encoding="utf-8"))
    assert local_summary["all_pass"] is True
    assert local_summary["mysqld_version"].startswith("8.0.45")
