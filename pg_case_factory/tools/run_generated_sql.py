from __future__ import annotations

import argparse
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


METADATA_PATTERN = re.compile(r"^\s*--\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*?)\s*$")
SQLSTATE_PATTERN = re.compile(r"SQLSTATE:\s*([0-9A-Z]{5})")
DEFAULT_EXECUTOR = ["psql", "-X", "-v", "ON_ERROR_STOP=1", "-f", "{sql}"]


def _sql_files(sql_dir: Path) -> list[Path]:
    return sorted(path for path in sql_dir.glob("**/*.sql") if path.is_file())


def _metadata(sql_path: Path) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in sql_path.read_text(encoding="utf-8").splitlines()[:20]:
        match = METADATA_PATTERN.match(line)
        if match:
            metadata[match.group(1)] = match.group(2)
    return metadata


def _command(executor: list[str], sql_path: Path) -> list[str]:
    if any("{sql}" in part for part in executor):
        return [part.replace("{sql}", str(sql_path)) for part in executor]
    return [*executor, str(sql_path)]


def _observed_sqlstate(stderr: str) -> str:
    match = SQLSTATE_PATTERN.search(stderr)
    return match.group(1) if match else ""


def _case_status(expected_status: str, observed_status: str, expected_sqlstate: str, observed_sqlstate: str) -> str:
    if expected_status == "success" and observed_status == "success":
        return "passed"
    if expected_status == "failure" and observed_status == "failure":
        if not expected_sqlstate or expected_sqlstate == observed_sqlstate:
            return "expected_failure_matched"
    return "failed"


def run_sql_file(sql_path: Path, executor: list[str]) -> dict[str, Any]:
    metadata = _metadata(sql_path)
    expected_status = metadata.get("expected_status", "success")
    expected_sqlstate = metadata.get("expected_sqlstate", "")
    case_id = metadata.get("case_id", sql_path.stem)
    start = time.monotonic()
    completed = subprocess.run(
        _command(executor, sql_path),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    duration_ms = int((time.monotonic() - start) * 1000)
    observed_status = "success" if completed.returncode == 0 else "failure"
    observed_sqlstate = _observed_sqlstate(completed.stderr)
    return {
        "case_id": case_id,
        "sql_path": sql_path.as_posix(),
        "expected_status": expected_status,
        "expected_sqlstate": expected_sqlstate,
        "observed_status": observed_status,
        "observed_sqlstate": observed_sqlstate,
        "status": _case_status(expected_status, observed_status, expected_sqlstate, observed_sqlstate),
        "exit_code": int(completed.returncode),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "duration_ms": duration_ms,
    }


def run_sql_directory(sql_dir: Path, feature_key: str, executor: list[str] | None = None) -> dict[str, Any]:
    sql_dir = Path(sql_dir)
    if not sql_dir.exists():
        raise ValueError(f"SQL directory does not exist: {sql_dir}")
    command = list(executor or DEFAULT_EXECUTOR)
    cases = [run_sql_file(path, command) for path in _sql_files(sql_dir)]
    return {
        "schema_version": 1,
        "kind": "feature_execution_report",
        "feature": {"key": feature_key},
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "runner": {
            "executor": command,
            "sql_dir": sql_dir.as_posix(),
        },
        "summary": {
            "case_count": len(cases),
            "failed_cases": sum(1 for case in cases if case["status"] == "failed"),
            "expected_failure_matched": sum(1 for case in cases if case["status"] == "expected_failure_matched"),
        },
        "cases": cases,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run generated SQL files and write a feature execution report.")
    parser.add_argument("--sql-dir", required=True, type=Path, help="directory containing generated .sql files")
    parser.add_argument("--feature", required=True, help="feature key for the report")
    parser.add_argument("--output", type=Path, help="feature_execution_report yaml output path")
    parser.add_argument(
        "--executor",
        nargs="+",
        default=DEFAULT_EXECUTOR,
        help="executor command. Use {sql} placeholder or the sql path is appended.",
    )
    args = parser.parse_args(argv)

    try:
        report = run_sql_directory(args.sql_dir, args.feature, args.executor)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}")
        return 1

    output_text = yaml.safe_dump(report, sort_keys=False, allow_unicode=True)
    output_path = args.output or Path("artifacts") / "evaluations" / f"{args.feature}_execution_report.yaml"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output_text, encoding="utf-8")
    failed = report["summary"]["failed_cases"]
    if failed:
        print(f"FAIL generated SQL execution: cases={report['summary']['case_count']} failed={failed}")
        return 1
    print(f"PASS generated SQL execution: cases={report['summary']['case_count']} failed=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
