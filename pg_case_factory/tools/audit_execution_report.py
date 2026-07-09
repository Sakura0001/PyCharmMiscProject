from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


ALLOWED_EXPECTED_STATUS = {"success", "failure"}
ALLOWED_OBSERVED_STATUS = {"success", "failure"}
ALLOWED_CASE_STATUS = {"passed", "failed", "expected_failure_matched", "skipped", "unsupported"}
REQUIRED_TOP_LEVEL_KEYS = ("schema_version", "kind", "feature", "runner", "cases")
REQUIRED_CASE_KEYS = ("case_id", "sql_path", "expected_status", "observed_status", "status", "exit_code")


@dataclass
class AuditResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    case_count: int = 0

    @property
    def passed(self) -> bool:
        return not self.errors


def load_yaml(path: Path) -> dict[str, Any]:
    parsed = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(parsed, dict):
        raise ValueError(f"{path}: report must be a mapping")
    return parsed


def audit_report(report: dict[str, Any]) -> AuditResult:
    result = AuditResult()

    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in report:
            result.errors.append(f"top-level field {key} is required")

    if report.get("kind") != "feature_execution_report":
        result.errors.append("kind must be feature_execution_report")

    feature = report.get("feature")
    if not isinstance(feature, dict) or not feature.get("key"):
        result.errors.append("feature.key is required")

    runner = report.get("runner")
    if not isinstance(runner, dict):
        result.errors.append("runner must be a mapping")

    cases = report.get("cases")
    if not isinstance(cases, list):
        result.errors.append("cases must be a list")
        return result

    seen_case_ids: set[str] = set()
    result.case_count = len(cases)
    for index, case in enumerate(cases):
        prefix = f"cases[{index}]"
        if not isinstance(case, dict):
            result.errors.append(f"{prefix}: case must be a mapping")
            continue
        for key in REQUIRED_CASE_KEYS:
            if key not in case or case.get(key) in ("", None):
                result.errors.append(f"{prefix}: {key} is required")

        case_id = str(case.get("case_id") or "")
        if case_id:
            if case_id in seen_case_ids:
                result.errors.append(f"{prefix}: duplicate case_id: {case_id}")
            seen_case_ids.add(case_id)

        expected_status = str(case.get("expected_status") or "")
        if expected_status and expected_status not in ALLOWED_EXPECTED_STATUS:
            result.errors.append(f"{prefix}: expected_status must be one of {sorted(ALLOWED_EXPECTED_STATUS)}")

        observed_status = str(case.get("observed_status") or "")
        if observed_status and observed_status not in ALLOWED_OBSERVED_STATUS:
            result.errors.append(f"{prefix}: observed_status must be one of {sorted(ALLOWED_OBSERVED_STATUS)}")

        status = str(case.get("status") or "")
        if status and status not in ALLOWED_CASE_STATUS:
            result.errors.append(f"{prefix}: status must be one of {sorted(ALLOWED_CASE_STATUS)}")

        exit_code = case.get("exit_code")
        if exit_code is not None and not isinstance(exit_code, int):
            result.errors.append(f"{prefix}: exit_code must be an integer")

        if expected_status == "failure" and case.get("expected_sqlstate") and observed_status == "failure":
            observed_sqlstate = str(case.get("observed_sqlstate") or "")
            if not observed_sqlstate:
                result.warnings.append(f"{prefix}: expected_sqlstate is declared but observed_sqlstate is empty")

    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit a feature execution report artifact.")
    parser.add_argument("--report", required=True, type=Path, help="feature_execution_report yaml path")
    args = parser.parse_args(argv)

    try:
        result = audit_report(load_yaml(args.report))
    except Exception as exc:  # noqa: BLE001 - CLI should report clean errors.
        print(f"ERROR: {exc}")
        return 1

    for warning in result.warnings:
        print(f"WARNING: {warning}")
    if result.passed:
        print(f"PASS execution report audit: cases={result.case_count}")
        return 0
    print(f"FAIL execution report audit: cases={result.case_count} errors={len(result.errors)}")
    for error in result.errors:
        print(f"ERROR: {error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
