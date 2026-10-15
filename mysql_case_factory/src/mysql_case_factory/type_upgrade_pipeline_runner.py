"""Local exact-output runner for the condensed type-upgrade pipeline batch."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mysql_case_factory.type_upgrade_pipeline import PIPELINE_DATABASE, PIPELINE_PROFILES
from mysql_case_factory.type_upgrade_runner import LocalMySQLServer


@dataclass(frozen=True)
class ExecutionResult:
    case_id: str
    outcome: str
    error: str | None = None
    elapsed_ms: int = 0

    def to_json(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "outcome": self.outcome,
            "error": self.error,
            "elapsed_ms": self.elapsed_ms,
        }


def _is_connection_loss(stderr: str) -> bool:
    lowered = stderr.lower()
    return "lost connection" in lowered or "server has gone away" in lowered or "error 2013" in lowered


def classify_execution(
    returncode: int,
    stdout: str,
    expected: str,
    stderr: str,
) -> ExecutionResult:
    if _is_connection_loss(stderr):
        return ExecutionResult("unknown", "FAIL_CRASH", stderr.strip()[:4000] or "MySQL connection lost")
    if returncode != 0:
        return ExecutionResult("unknown", "FAIL_SQL", stderr.strip()[:4000] or f"mysql exited with {returncode}")
    if stderr.strip():
        return ExecutionResult("unknown", "FAIL_SQL", stderr.strip()[:4000])
    if stdout != expected:
        expected_lines = len(expected.splitlines())
        actual_lines = len(stdout.splitlines())
        return ExecutionResult(
            "unknown",
            "FAIL_OUTPUT",
            f"exact output mismatch: expected {expected_lines} line(s), actual {actual_lines} line(s)",
        )
    return ExecutionResult("unknown", "PASS")


def _mysql_command(mysql: str, socket_path: Path) -> list[str]:
    return [
        mysql,
        "--no-defaults",
        f"--socket={socket_path}",
        "--user=root",
        "--batch",
        "--raw",
        "--skip-column-names",
        "--binary-mode",
        "--force",
        PIPELINE_DATABASE,
    ]


def run_local(
    cases_dir: Path,
    results_path: Path,
    summary_path: Path,
    *,
    profile: str = "copy",
    mysqld: str = "/opt/homebrew/opt/mysql@8.0/bin/mysqld",
    mysql: str = "/opt/homebrew/opt/mysql@8.0/bin/mysql",
) -> dict[str, Any]:
    if profile not in PIPELINE_PROFILES:
        raise ValueError(f"unsupported profile: {profile}")
    try:
        import pymysql
    except ImportError as error:
        raise RuntimeError("PyMySQL is required; install '.[runner]'") from error

    manifest_path = cases_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("batch_id") != "2026-10-15-type-upgrade-pipeline-v1":
        raise RuntimeError(f"unexpected batch manifest: {manifest_path}")
    sql_files = sorted((cases_dir / profile).glob("TUCP-*.sql"))
    if len(sql_files) != manifest.get("case_count"):
        raise RuntimeError(f"expected {manifest.get('case_count')} SQL files, found {len(sql_files)}")

    started_at = datetime.now(timezone.utc).isoformat()
    server = LocalMySQLServer(mysqld=mysqld)
    results: list[ExecutionResult] = []
    server_version = "unknown"
    try:
        server.start()
        connection = pymysql.connect(
            user="root",
            unix_socket=str(server.socket_path),
            autocommit=True,
            charset="utf8mb4",
        )
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT VERSION()")
                server_version = str(cursor.fetchone()[0])
                cursor.execute(f"DROP DATABASE IF EXISTS {PIPELINE_DATABASE}")
                cursor.execute(
                    f"CREATE DATABASE {PIPELINE_DATABASE} "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"
                )
        finally:
            connection.close()

        command = _mysql_command(mysql, server.socket_path)
        for sql_path in sql_files:
            case_id = sql_path.stem
            expected_path = cases_dir / "expected" / f"{case_id}.tsv"
            expected = expected_path.read_text(encoding="utf-8")
            started = time.monotonic()
            try:
                completed = subprocess.run(
                    command,
                    input=sql_path.read_bytes(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=180,
                    check=False,
                )
                stdout = completed.stdout.decode("utf-8", errors="replace")
                stderr = completed.stderr.decode("utf-8", errors="replace")
                result = classify_execution(completed.returncode, stdout, expected, stderr)
            except subprocess.TimeoutExpired as error:
                result = ExecutionResult(case_id, "FAIL_TIMEOUT", f"mysql timed out after {error.timeout}s")
            results.append(
                ExecutionResult(
                    case_id=case_id,
                    outcome=result.outcome,
                    error=result.error,
                    elapsed_ms=int((time.monotonic() - started) * 1000),
                )
            )

        # The internal pipeline consumes one profile as one SQL stream. Verify that
        # concatenated stdout is also byte-identical with expected_output.tsv.
        combined_started = time.monotonic()
        combined_sql = b"".join(path.read_bytes() for path in sql_files)
        combined_expected = (cases_dir / "expected_output.tsv").read_text(encoding="utf-8")
        try:
            combined = subprocess.run(
                command,
                input=combined_sql,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=300,
                check=False,
            )
            combined_result = classify_execution(
                combined.returncode,
                combined.stdout.decode("utf-8", errors="replace"),
                combined_expected,
                combined.stderr.decode("utf-8", errors="replace"),
            )
            results.append(
                ExecutionResult(
                    "COMBINED_OUTPUT",
                    combined_result.outcome,
                    combined_result.error,
                    int((time.monotonic() - combined_started) * 1000),
                )
            )
        except subprocess.TimeoutExpired as error:
            results.append(
                ExecutionResult(
                    "COMBINED_OUTPUT",
                    "FAIL_TIMEOUT",
                    f"mysql timed out after {error.timeout}s",
                    int((time.monotonic() - combined_started) * 1000),
                )
            )

        connection = pymysql.connect(
            user="root",
            unix_socket=str(server.socket_path),
            autocommit=True,
            charset="utf8mb4",
            database=PIPELINE_DATABASE,
        )
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) FROM information_schema.TABLES "
                    "WHERE table_schema=DATABASE() AND table_name LIKE 'tab_tucp_%'"
                )
                leftover_tables = int(cursor.fetchone()[0])
                cursor.execute(
                    "SELECT COUNT(*) FROM information_schema.ROUTINES "
                    "WHERE routine_schema=DATABASE() AND routine_name LIKE '%tucp_%'"
                )
                leftover_routines = int(cursor.fetchone()[0])
        finally:
            connection.close()
        cleanup_ok = leftover_tables == 0 and leftover_routines == 0
        cleanup_error = None if cleanup_ok else f"leftover tables={leftover_tables}, routines={leftover_routines}"
        results.append(
            ExecutionResult(
                "FINAL_CLEANUP",
                "PASS" if cleanup_ok else "FAIL_CLEANUP",
                cleanup_error,
            )
        )
    finally:
        server.stop()

    counts: dict[str, int] = {}
    for result in results:
        counts[result.outcome] = counts.get(result.outcome, 0) + 1
    all_pass = bool(results) and counts.get("PASS", 0) == len(results)
    summary = {
        "format_version": 1,
        "batch_id": manifest["batch_id"],
        "batch_kind": manifest["batch_kind"],
        "profile": profile,
        "selected_count": len(sql_files),
        "executed_count": len(sql_files),
        "counts": counts,
        "all_pass": all_pass,
        "mysqld_version": server_version,
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
    }
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with results_path.open("w", encoding="utf-8", newline="\n") as handle:
        for result in results:
            handle.write(json.dumps(result.to_json(), sort_keys=True, separators=(",", ":")) + "\n")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_path.with_suffix(".md").write_text(render_summary_markdown(summary), encoding="utf-8")
    return summary


def render_summary_markdown(summary: dict[str, Any]) -> str:
    counts = ", ".join(f"{key}: {value}" for key, value in sorted(summary.get("counts", {}).items())) or "none"
    return (
        "# Type-upgrade condensed pipeline local verification\n\n"
        f"**Result:** {'ALL PASS' if summary.get('all_pass') else 'FAIL OR INCOMPLETE'}\n\n"
        f"- **Batch ID:** `{summary.get('batch_id')}`\n"
        f"- **Profile:** `{summary.get('profile')}`\n"
        f"- **Selected cases:** {summary.get('selected_count')}\n"
        f"- **Executed cases:** {summary.get('executed_count')}\n"
        f"- **Outcome counts:** {counts}\n"
        f"- **MySQL version:** {summary.get('mysqld_version')}\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the condensed type-upgrade pipeline against local MySQL 8.0.45")
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--profile", choices=PIPELINE_PROFILES, default="copy")
    parser.add_argument("--mysqld", default="/opt/homebrew/opt/mysql@8.0/bin/mysqld")
    parser.add_argument("--mysql", default="/opt/homebrew/opt/mysql@8.0/bin/mysql")
    args = parser.parse_args()
    summary = run_local(
        args.cases,
        args.results,
        args.summary,
        profile=args.profile,
        mysqld=args.mysqld,
        mysql=args.mysql,
    )
    print(render_summary_markdown(summary))


if __name__ == "__main__":
    main()
