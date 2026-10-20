from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from mysql_case_factory.fk_type_expansion_audit import audit_fk_type_expansion_artifacts


def _generate(tmp_path: Path) -> Path:
    output = tmp_path / "fk"
    tool = Path(__file__).parents[1] / "tools" / "generate_fk_type_expansion.py"
    subprocess.run(
        [sys.executable, str(tool), "--output", str(output)],
        check=True,
        cwd=Path(__file__).parents[1],
    )
    return output


def test_fk_type_expansion_audit_accepts_structural_artifacts(tmp_path: Path) -> None:
    output = _generate(tmp_path)
    report = audit_fk_type_expansion_artifacts(output, require_local=False)
    assert report["passed"] is True
    assert report["case_count"] == 568
    assert report["transition_count"] == 71
    assert report["profile_counts"] == {"inplace": 284, "instant": 284}
    assert report["family_counts"] == {
        "integer": 176,
        "character": 112,
        "binary": 96,
        "decimal": 80,
        "bit": 104,
    }
    assert report["unique_case_ids"] is True
    assert report["coverage_ok"] is True
    assert report["expected_output_ok"] is True
    assert report["sql_oracle_ok"] is True
    assert report["artifact_hashes_ok"] is True
    assert report["usage_documented"] is True
    assert (output / "audit_report.json").exists()
    assert (output / "audit_summary.md").exists()
