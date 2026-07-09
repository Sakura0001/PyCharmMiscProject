from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml


TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from audit_execution_report import audit_report  # noqa: E402
from diagnose_execution_failures import diagnose_report  # noqa: E402
from promote_execution_feedback import build_promotion_candidates  # noqa: E402
from run_generated_sql import DEFAULT_EXECUTOR, run_sql_directory  # noqa: E402


def _safe_name(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return safe.strip("_") or "feature"


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _audit_result_to_dict(result: Any) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "execution_report_audit",
        "passed": bool(result.passed),
        "case_count": int(result.case_count),
        "errors": list(result.errors),
        "warnings": list(result.warnings),
    }


def _iteration_status(audit_data: dict[str, Any], diagnosis: dict[str, Any] | None) -> str:
    if not audit_data["passed"]:
        return "audit_failed"
    if diagnosis and diagnosis["summary"]["failed_cases"]:
        return "failures_detected"
    return "clean"


def run_feature_test_loop(
    feature_key: str,
    sql_dir: Path,
    artifacts_dir: Path = Path("artifacts/evaluations"),
    executor: list[str] | None = None,
    max_iterations: int = 1,
    stop_on_clean: bool = True,
) -> dict[str, Any]:
    if max_iterations < 1:
        raise ValueError("max_iterations must be >= 1")

    command = list(executor or DEFAULT_EXECUTOR)
    prefix = _safe_name(feature_key)
    artifacts_dir = Path(artifacts_dir)
    iterations: list[dict[str, Any]] = []

    for iteration in range(1, max_iterations + 1):
        iteration_tag = f"{prefix}_iteration_{iteration:03d}"
        execution_report_path = artifacts_dir / f"{iteration_tag}_execution_report.yaml"
        audit_report_path = artifacts_dir / f"{iteration_tag}_execution_audit.yaml"
        diagnosis_path = artifacts_dir / f"{iteration_tag}_failure_diagnosis.yaml"
        promotion_path = artifacts_dir / f"{iteration_tag}_promotion_candidates.yaml"

        execution_report = run_sql_directory(sql_dir=sql_dir, feature_key=feature_key, executor=command)
        _write_yaml(execution_report_path, execution_report)

        audit = audit_report(execution_report)
        audit_data = _audit_result_to_dict(audit)
        _write_yaml(audit_report_path, audit_data)

        diagnosis: dict[str, Any] | None = None
        promotion: dict[str, Any] | None = None
        if audit.passed:
            diagnosis = diagnose_report(execution_report)
            promotion = build_promotion_candidates(diagnosis)
            _write_yaml(diagnosis_path, diagnosis)
            _write_yaml(promotion_path, promotion)

        status = _iteration_status(audit_data, diagnosis)
        iterations.append(
            {
                "iteration": iteration,
                "status": status,
                "execution_report_path": execution_report_path.as_posix(),
                "audit_report_path": audit_report_path.as_posix(),
                "failure_diagnosis_path": diagnosis_path.as_posix() if diagnosis else "",
                "promotion_candidates_path": promotion_path.as_posix() if promotion else "",
                "case_count": int(execution_report["summary"]["case_count"]),
                "failed_cases": int(diagnosis["summary"]["failed_cases"]) if diagnosis else 0,
                "promotion_candidates": len(promotion["candidates"]) if promotion else 0,
            }
        )

        if status == "audit_failed" or (stop_on_clean and status == "clean"):
            break

    final_status = iterations[-1]["status"] if iterations else "not_run"
    loop_report = {
        "schema_version": 1,
        "kind": "feature_test_loop_report",
        "feature": {"key": feature_key},
        "loop_config": {
            "sql_dir": Path(sql_dir).as_posix(),
            "artifacts_dir": artifacts_dir.as_posix(),
            "executor": command,
            "max_iterations": max_iterations,
            "stop_on_clean": stop_on_clean,
        },
        "summary": {
            "iterations": len(iterations),
            "final_status": final_status,
            "total_failed_cases": sum(item["failed_cases"] for item in iterations),
            "total_promotion_candidates": sum(item["promotion_candidates"] for item in iterations),
        },
        "iterations": iterations,
    }
    _write_yaml(artifacts_dir / f"{prefix}_loop_report.yaml", loop_report)
    return loop_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run generated SQL through a feature test loop.")
    parser.add_argument("--sql-dir", required=True, type=Path, help="directory containing generated .sql files")
    parser.add_argument("--feature", required=True, help="feature key for the loop report")
    parser.add_argument(
        "--artifacts-dir",
        type=Path,
        default=Path("artifacts/evaluations"),
        help="directory for execution, audit, diagnosis, promotion, and loop reports",
    )
    parser.add_argument("--max-iterations", type=int, default=1, help="maximum loop iterations to execute")
    parser.add_argument(
        "--no-stop-on-clean",
        action="store_true",
        help="continue to max_iterations even when an iteration is clean",
    )
    parser.add_argument(
        "--executor",
        nargs="+",
        help="executor command. Use {sql} placeholder or the sql path is appended.",
    )
    args = parser.parse_args(argv)

    try:
        report = run_feature_test_loop(
            feature_key=args.feature,
            sql_dir=args.sql_dir,
            artifacts_dir=args.artifacts_dir,
            executor=args.executor,
            max_iterations=args.max_iterations,
            stop_on_clean=not args.no_stop_on_clean,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}")
        return 1

    summary = report["summary"]
    print(
        "PASS feature test loop:"
        f" iterations={summary['iterations']}"
        f" final_status={summary['final_status']}"
        f" promotion_candidates={summary['total_promotion_candidates']}"
    )
    return 0 if summary["final_status"] == "clean" else 1


if __name__ == "__main__":
    raise SystemExit(main())
