from __future__ import annotations

import csv
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_CASE_COUNT = 5_136
EXPECTED_TRANSITION_COUNT = 107
EXPECTED_DEPENDENCY_COUNT = 4
EXPECTED_PROFILE_COUNTS = {"copy": 1_712, "inplace": 1_712, "instant": 1_712}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl_gzip(path: Path) -> list[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_virtual_function_artifacts(output: Path, *, require_local: bool = True) -> dict[str, Any]:
    manifest = _load_json(output / "manifest.json")
    cases = _load_jsonl_gzip(output / "cases.jsonl.gz")
    smoke = _load_jsonl_gzip(output / "smoke_cases.jsonl.gz")
    with (output / "coverage.tsv").open(encoding="utf-8", newline="") as handle:
        coverage = list(csv.DictReader(handle, delimiter="\t"))

    case_ids = [case["case_id"] for case in cases]
    unique_case_ids = len(case_ids) == len(set(case_ids)) == EXPECTED_CASE_COUNT
    prefix_ok = all(case_id.startswith("TUCVF-") for case_id in case_ids)
    dependencies = {case["dependency_mode"] for case in cases}
    profiles = {case["algorithm"] for case in cases}
    transitions = {
        (case["family"], case["source_type"], case["target_type"]) for case in cases
    }
    matrix_ok = (
        len(dependencies) == EXPECTED_DEPENDENCY_COUNT
        and profiles == set(EXPECTED_PROFILE_COUNTS)
        and len(transitions) == EXPECTED_TRANSITION_COUNT
        and len(coverage) == EXPECTED_CASE_COUNT
    )
    smoke_ok = len(smoke) == 84 and {
        case["dependency_mode"] for case in smoke
    } == dependencies

    artifact_hashes_ok = all(
        (output / relative_path).is_file() and _sha256(output / relative_path) == digest
        for relative_path, digest in manifest.get("artifacts_sha256", {}).items()
    )

    readme = (output / "README.md").read_text(encoding="utf-8")
    usage_documented = all(
        token in readme
        for token in (
            "run_virtual_function_type_upgrade.py",
            "--profile copy",
            "--profile inplace",
            "--profile instant",
            "--all",
            "--smoke",
        )
    )

    local_profile_results = {}
    local_profile_summaries = {}
    local_metadata_ok = True
    if require_local:
        for profile in EXPECTED_PROFILE_COUNTS:
            results = _load_jsonl(output / f"{profile}_results.jsonl")
            summary_path = output / f"{profile}_summary.json"
            summary = _load_json(summary_path) if summary_path.exists() else {}
            local_profile_results[profile] = results
            local_profile_summaries[profile] = summary
            local_metadata_ok = local_metadata_ok and (
                summary.get("all_pass") is True
                and summary.get("profile") == profile
                and summary.get("selected_count") == EXPECTED_PROFILE_COUNTS[profile]
                and len(results) == EXPECTED_PROFILE_COUNTS[profile]
                and all(result.get("classification") == "PASS" for result in results)
                and str(summary.get("mysqld_version", "")).startswith("8.0.45")
            )

    passed = bool(
        manifest.get("batch_id") == "2026-10-20-virtual-function-type-upgrade-v1"
        and manifest.get("batch_kind") == "virtual_function_type_upgrade"
        and manifest.get("case_count") == EXPECTED_CASE_COUNT
        and manifest.get("transition_count") == EXPECTED_TRANSITION_COUNT
        and manifest.get("dependency_mode_count") == EXPECTED_DEPENDENCY_COUNT
        and manifest.get("profile_counts") == EXPECTED_PROFILE_COUNTS
        and manifest.get("smoke_case_count") == 84
        and manifest.get("materialization") == "virtual_runner"
        and unique_case_ids
        and prefix_ok
        and matrix_ok
        and smoke_ok
        and artifact_hashes_ok
        and usage_documented
        and local_metadata_ok
    )

    report: dict[str, Any] = {
        "passed": passed,
        "batch_id": manifest.get("batch_id"),
        "batch_kind": manifest.get("batch_kind"),
        "case_count": len(cases),
        "transition_count": len(transitions),
        "dependency_count": len(dependencies),
        "profile_counts": manifest.get("profile_counts"),
        "smoke_case_count": len(smoke),
        "unique_case_ids": unique_case_ids,
        "case_prefix_ok": prefix_ok,
        "matrix_ok": matrix_ok,
        "smoke_ok": smoke_ok,
        "artifact_hashes_ok": artifact_hashes_ok,
        "usage_documented": usage_documented,
        "local_required": require_local,
        "local_metadata_ok": local_metadata_ok,
        "local_result_counts": {
            profile: len(results) for profile, results in local_profile_results.items()
        },
        "local_pass_counts": {
            profile: sum(1 for result in results if result.get("classification") == "PASS")
            for profile, results in local_profile_results.items()
        },
    }
    (output / "audit_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary = f"""# Virtual/function type-upgrade audit

**Result:** {'PASS' if passed else 'FAIL'}

- **Batch ID:** `{manifest.get('batch_id')}`
- **Cases:** {len(cases)}
- **Transitions:** {len(transitions)}
- **Dependency modes:** {len(dependencies)}
- **Profiles:** {', '.join(EXPECTED_PROFILE_COUNTS)}
- **Local COPY:** {report['local_pass_counts'].get('copy', 0)}/{report['local_result_counts'].get('copy', 0)} PASS
- **Local INPLACE:** {report['local_pass_counts'].get('inplace', 0)}/{report['local_result_counts'].get('inplace', 0)} PASS
- **Local INSTANT:** {report['local_pass_counts'].get('instant', 0)}/{report['local_result_counts'].get('instant', 0)} PASS
"""
    (output / "audit_summary.md").write_text(summary, encoding="utf-8")
    return report
