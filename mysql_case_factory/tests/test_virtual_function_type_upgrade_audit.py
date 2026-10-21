from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from mysql_case_factory.virtual_function_type_upgrade_audit import audit_virtual_function_artifacts


def _generate(tmp_path: Path) -> Path:
    output = tmp_path / "virtual-function"
    tool = Path(__file__).parents[1] / "tools" / "generate_virtual_function_type_upgrade.py"
    subprocess.run(
        [sys.executable, str(tool), "--output", str(output)],
        check=True,
        cwd=Path(__file__).parents[1],
    )
    return output


def test_virtual_function_audit_accepts_structural_artifacts(tmp_path: Path) -> None:
    output = _generate(tmp_path)
    report = audit_virtual_function_artifacts(output, require_local=False)
    assert report["passed"] is True
    assert report["case_count"] == 5_136
    assert report["transition_count"] == 107
    assert report["dependency_count"] == 4
    assert report["profile_counts"] == {
        "copy": 1_712,
        "inplace": 1_712,
        "instant": 1_712,
    }
    assert report["smoke_case_count"] == 84
    assert report["unique_case_ids"] is True
    assert report["matrix_ok"] is True
    assert report["smoke_ok"] is True
    assert report["artifact_hashes_ok"] is True
    assert report["usage_documented"] is True
    assert (output / "audit_report.json").exists()
    assert (output / "audit_summary.md").exists()


def test_virtual_function_audit_verifies_local_all_profile_evidence() -> None:
    root = Path(__file__).parents[1]
    output = root / "generated" / "virtual_function_type_upgrade_v1"
    report = audit_virtual_function_artifacts(output, require_local=True)
    assert report["passed"] is True
    assert report["local_metadata_ok"] is True
    assert report["local_result_counts"] == {
        "copy": 1_712,
        "inplace": 1_712,
        "instant": 1_712,
    }
    assert report["local_pass_counts"] == {
        "copy": 1_712,
        "inplace": 1_712,
        "instant": 1_712,
    }

    for profile in ("copy", "inplace", "instant"):
        summary = json.loads((output / f"{profile}_summary.json").read_text(encoding="utf-8"))
        assert summary["all_pass"] is True
        assert summary["profile"] == profile
        assert summary["mysqld_version"].startswith("8.0.45")
