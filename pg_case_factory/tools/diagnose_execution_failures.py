from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path) -> dict[str, Any]:
    parsed = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(parsed, dict):
        raise ValueError(f"{path}: report must be a mapping")
    return parsed


def classify_case(case: dict[str, Any]) -> tuple[str, str] | None:
    if case.get("cleanup_status") == "failed":
        return "cleanup_failure", "cleanup_status=failed"

    oracle_result = case.get("oracle_result")
    if isinstance(oracle_result, dict) and oracle_result.get("status") == "mismatch":
        return "result_mismatch", str(oracle_result.get("detail") or "oracle result mismatch")

    plan_observation = case.get("plan_observation")
    if isinstance(plan_observation, dict) and plan_observation.get("status") == "mismatch":
        return "plan_mismatch", str(plan_observation.get("detail") or "plan observation mismatch")

    expected = str(case.get("expected_status") or "")
    observed = str(case.get("observed_status") or "")
    if expected == "success" and observed == "failure":
        return "unexpected_failure", str(case.get("observed_sqlstate") or case.get("stderr") or "unexpected failure")
    if expected == "failure" and observed == "success":
        return "unexpected_success", "expected failure but statement succeeded"
    if expected == "failure" and observed == "failure":
        expected_sqlstate = str(case.get("expected_sqlstate") or "")
        observed_sqlstate = str(case.get("observed_sqlstate") or "")
        if expected_sqlstate and observed_sqlstate and expected_sqlstate != observed_sqlstate:
            return "sqlstate_mismatch", f"expected {expected_sqlstate}, observed {observed_sqlstate}"

    if case.get("status") == "failed":
        return "unclassified_failure", "case status is failed without a more specific diagnosis"
    return None


def diagnose_report(report: dict[str, Any]) -> dict[str, Any]:
    feature = dict(report.get("feature") or {})
    clusters_by_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    cases = list(report.get("cases") or [])
    for case in cases:
        if not isinstance(case, dict):
            continue
        classification = classify_case(case)
        if classification is None:
            continue
        category, reason = classification
        clusters_by_key[(category, reason)].append(
            {
                "case_id": str(case.get("case_id") or ""),
                "sql_path": str(case.get("sql_path") or ""),
                "expected_status": str(case.get("expected_status") or ""),
                "observed_status": str(case.get("observed_status") or ""),
                "observed_sqlstate": str(case.get("observed_sqlstate") or ""),
            }
        )

    clusters = [
        {
            "category": category,
            "reason": reason,
            "case_count": len(cluster_cases),
            "cases": cluster_cases,
        }
        for (category, reason), cluster_cases in sorted(clusters_by_key.items())
    ]
    failed_cases = sum(cluster["case_count"] for cluster in clusters)
    return {
        "schema_version": 1,
        "kind": "failure_diagnosis_report",
        "feature": {"key": str(feature.get("key") or "unknown_feature")},
        "summary": {
            "total_cases": len(cases),
            "failed_cases": failed_cases,
            "cluster_count": len(clusters),
        },
        "clusters": clusters,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Diagnose a feature execution report.")
    parser.add_argument("--report", required=True, type=Path, help="feature_execution_report yaml path")
    parser.add_argument("--output", type=Path, help="failure diagnosis yaml output path")
    args = parser.parse_args(argv)

    try:
        diagnosis = diagnose_report(load_yaml(args.report))
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}")
        return 1

    output = yaml.safe_dump(diagnosis, sort_keys=False, allow_unicode=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    print(
        f"PASS failure diagnosis: clusters={diagnosis['summary']['cluster_count']} failed_cases={diagnosis['summary']['failed_cases']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
