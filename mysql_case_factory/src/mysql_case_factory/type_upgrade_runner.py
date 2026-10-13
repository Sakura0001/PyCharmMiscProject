"""Runner for the generated MySQL type-upgrade consistency cases."""

from __future__ import annotations

import argparse
import gzip
import json
import os
import shutil
import signal
import socket
import subprocess
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from pathlib import Path
from typing import Any, Protocol, Sequence

from mysql_case_factory.type_upgrade_consistency import (
    TYPE_UPGRADE_BATCH_ID,
    TYPE_UPGRADE_BATCH_KIND,
    TypeUpgradeCase,
    effective_sql_mode,
    suite_manifest,
)


class CaseOutcome(str, Enum):
    PASS = "PASS"
    FAIL_DDL = "FAIL_DDL"
    FAIL_SETUP = "FAIL_SETUP"
    FAIL_POST_DML = "FAIL_POST_DML"
    FAIL_ORACLE = "FAIL_ORACLE"
    FAIL_CRASH = "FAIL_CRASH"
    BLOCKED = "BLOCKED"


@dataclass
class CaseResult:
    case_id: str
    batch_id: str
    batch_kind: str
    profile: str
    outcome: CaseOutcome
    error: str | None = None
    errno: int | None = None
    sqlstate: str | None = None
    elapsed_ms: int = 0

    def to_json(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "batch_id": self.batch_id,
            "batch_kind": self.batch_kind,
            "profile": self.profile,
            "outcome": self.outcome.value,
            "error": self.error,
            "errno": self.errno,
            "sqlstate": self.sqlstate,
            "elapsed_ms": self.elapsed_ms,
        }


class Connection(Protocol):
    def execute(self, sql: str) -> None: ...

    def fetchone(self) -> Sequence[Any]: ...


def _error_metadata(error: Exception) -> tuple[int | None, str | None]:
    args = getattr(error, "args", ())
    code = getattr(error, "code", None)
    if args and isinstance(args[0], int):
        code = args[0]
    elif args and isinstance(args[0], str):
        prefix = args[0].strip().lstrip("(").split(",", 1)[0].strip()
        if prefix.isdigit():
            code = int(prefix)
    state = getattr(error, "sqlstate", None)
    if not state and args and len(args) > 1 and isinstance(args[1], str) and len(args[1]) >= 5 and args[1][0].isdigit():
        state = args[1][:5]
    return code if isinstance(code, int) else None, state


def _is_connection_loss(error: Exception) -> bool:
    code, _ = _error_metadata(error)
    message = str(error).lower()
    return code in {2006, 2013} or "lost connection" in message or "server has gone away" in message


def execute_case(case: TypeUpgradeCase, connection: Connection, profile: str) -> CaseResult:
    started = time.monotonic()
    result_error: str | None = None
    errno: int | None = None
    sqlstate: str | None = None
    outcome = CaseOutcome.PASS
    ddl_error: BaseException | None = None

    try:
        connection.execute(f"SET SESSION sql_mode='{effective_sql_mode(case.sql_mode)}'")
        for statement in case.cleanup_sql:
            connection.execute(statement)
        for statement in case.setup_sql:
            connection.execute(statement)

        try:
            connection.execute(case.ddl_sql.replace("${ALGORITHM}", profile.upper()))
        except Exception as error:  # PyMySQL exceptions are dynamic.
            ddl_error = error

        if ddl_error is not None and _is_connection_loss(ddl_error):
            outcome = CaseOutcome.FAIL_CRASH
            result_error = str(ddl_error)
            errno, sqlstate = _error_metadata(ddl_error)
        elif case.expected_outcome == "success" and ddl_error is not None:
            outcome = CaseOutcome.FAIL_DDL
            result_error = str(ddl_error)
            errno, sqlstate = _error_metadata(ddl_error)
        elif case.expected_outcome == "reject" and ddl_error is None:
            outcome = CaseOutcome.FAIL_DDL
            result_error = "expected reject, but DDL succeeded"
        elif case.expected_outcome == "reject" and ddl_error is not None:
            result_error = str(ddl_error)
            errno, sqlstate = _error_metadata(ddl_error)

        if outcome is CaseOutcome.PASS and case.expected_outcome == "success":
            for statement in case.post_ddl_sql:
                try:
                    connection.execute(statement)
                except Exception as error:
                    if _is_connection_loss(error):
                        outcome = CaseOutcome.FAIL_CRASH
                    else:
                        outcome = CaseOutcome.FAIL_POST_DML
                    result_error = f"post-DDL statement failed: {error}"
                    errno, sqlstate = _error_metadata(error)
                    break
            for statement in case.invalid_post_ddl_sql:
                try:
                    connection.execute(statement)
                except Exception:
                    continue
                outcome = CaseOutcome.FAIL_POST_DML
                result_error = "invalid post-DDL statement unexpectedly succeeded"
                break

        if outcome is CaseOutcome.PASS:
            for check_no, statement in enumerate(case.verify_sql, 1):
                try:
                    connection.execute(statement)
                    row = connection.fetchone()
                except Exception as error:
                    outcome = CaseOutcome.FAIL_CRASH if _is_connection_loss(error) else CaseOutcome.FAIL_ORACLE
                    result_error = f"verification {check_no} raised: {error}"
                    errno, sqlstate = _error_metadata(error)
                    break
                if not row or row[0] != "OK":
                    outcome = CaseOutcome.FAIL_ORACLE
                    result_error = f"verification {check_no} returned {row[0] if row else 'no row'}, expected OK"
                    break
    except Exception as error:
        if outcome is CaseOutcome.PASS:
            outcome = CaseOutcome.FAIL_SETUP
        result_error = result_error or str(error)
        errno, sqlstate = _error_metadata(error)
    finally:
        try:
            for statement in case.cleanup_sql:
                connection.execute(statement)
            connection.execute("SET SESSION sql_mode=DEFAULT")
        except Exception as error:
            if outcome is CaseOutcome.PASS:
                outcome = CaseOutcome.FAIL_SETUP
                result_error = f"cleanup failed: {error}"

    elapsed_ms = int((time.monotonic() - started) * 1000)
    return CaseResult(
        case_id=case.case_id,
        batch_id=case.batch_id,
        batch_kind=case.batch_kind,
        profile=profile,
        outcome=outcome,
        error=result_error if outcome is not CaseOutcome.PASS else result_error,
        errno=errno,
        sqlstate=sqlstate,
        elapsed_ms=elapsed_ms,
    )


class LocalMySQLServer:
    """Start and stop an isolated local MySQL 8.0.45 server."""

    def __init__(
        self,
        mysqld: str = "/opt/homebrew/opt/mysql@8.0/bin/mysqld",
        base_dir: Path | None = None,
    ) -> None:
        self.mysqld = mysqld
        self.base_dir = base_dir or Path(tempfile.mkdtemp(prefix="type-upgrade-mysql-"))
        self.data_dir = self.base_dir / "data"
        self.socket_path = self.base_dir / "mysql.sock"
        self.pid_file = self.base_dir / "mysqld.pid"
        self.error_log = self.base_dir / "mysqld.err"
        self.process: subprocess.Popen[bytes] | None = None
        self._owns_directory = base_dir is None

    def start(self, timeout: float = 60.0) -> None:
        if not Path(self.mysqld).exists():
            raise FileNotFoundError(f"MySQL server not found: {self.mysqld}")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        common = [
            self.mysqld,
            "--no-defaults",
            f"--datadir={self.data_dir}",
            f"--socket={self.socket_path}",
            f"--pid-file={self.pid_file}",
            f"--log-error={self.error_log}",
            "--skip-networking",
            "--innodb-buffer-pool-size=64M",
        ]
        if not any(self.data_dir.iterdir()):
            subprocess.run([*common, "--initialize-insecure"], check=True, timeout=timeout)
        self.process = subprocess.Popen(
            [*common, "--lower-case-table-names=2"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise RuntimeError(f"mysqld exited during startup: {self.error_log.read_text(errors='replace')}")
            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as probe:
                    probe.connect(str(self.socket_path))
                    return
            except OSError:
                time.sleep(0.2)
        raise TimeoutError(f"MySQL server did not become ready: {self.error_log}")

    def stop(self, timeout: float = 30.0) -> None:
        if self.process is None:
            return
        if self.process.poll() is None:
            self.process.send_signal(signal.SIGTERM)
            try:
                self.process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=timeout)
        self.process = None
        if self._owns_directory:
            shutil.rmtree(self.base_dir, ignore_errors=True)

    def __enter__(self) -> "LocalMySQLServer":
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.stop()


def _load_cases(path: Path) -> dict[str, TypeUpgradeCase]:
    cases: dict[str, TypeUpgradeCase] = {}
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            payload = json.loads(line)
            cases[payload["case_id"]] = TypeUpgradeCase(
                case_id=payload["case_id"],
                batch_id=payload["batch_id"],
                batch_kind=payload["batch_kind"],
                cluster=payload["cluster"],
                family=payload["family"],
                source_type=payload["source_type"],
                target_type=payload["target_type"],
                expected_outcome=payload["expected_outcome"],
                data_profile=payload["data_profile"],
                column_attribute=payload["column_attribute"],
                index_profile=payload["index_profile"],
                foreign_key_profile=payload["foreign_key_profile"],
                dependency_profile=payload["dependency_profile"],
                table_form=payload["table_form"],
                sql_mode=payload["sql_mode"],
                charset=payload["charset"],
                collation=payload["collation"],
                seed_values=tuple(payload["seed_values"]),
                post_ddl_values=tuple(payload["post_ddl_values"]),
                invalid_values=tuple(payload["invalid_values"]),
                reason=payload["reason"],
                setup_sql=tuple(payload["setup_sql"]),
                ddl_sql=payload["ddl_sql"],
                post_ddl_sql=tuple(payload["post_ddl_sql"]),
                invalid_post_ddl_sql=tuple(payload["invalid_post_ddl_sql"]),
                verify_sql=tuple(payload["verify_sql"]),
                cleanup_sql=tuple(payload["cleanup_sql"]),
            )
    return cases


def select_cases(
    all_cases: dict[str, TypeUpgradeCase],
    case_ids: set[str] | None,
    limit: int | None,
) -> list[TypeUpgradeCase]:
    if not all_cases:
        raise ValueError("case input is empty")
    if limit is not None and limit < 1:
        raise ValueError("limit must be a positive integer")
    selected = list(all_cases.values())
    if case_ids:
        unknown = case_ids - set(all_cases)
        if unknown:
            raise ValueError(f"Unknown case IDs: {', '.join(sorted(unknown))}")
        selected = [case for case in selected if case.case_id in case_ids]
    if limit is not None:
        selected = selected[:limit]
    return selected


def verify_case_artifacts(cases_path: Path) -> dict[str, Any]:
    manifest_path = cases_path.with_name("manifest.json")
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifact_name = cases_path.name
    artifacts = manifest.get("artifacts", {})
    if artifact_name not in artifacts:
        raise ValueError(f"manifest does not record cases artifact: {artifact_name}")
    payload = cases_path.read_bytes()
    expected = artifacts[artifact_name]
    actual_hash = sha256(payload).hexdigest()
    if actual_hash != expected.get("sha256") or len(payload) != expected.get("bytes"):
        raise ValueError(f"cases artifact integrity check failed: {artifact_name}")
    cases = _load_cases(cases_path)
    if len(cases) != manifest.get("case_count"):
        raise ValueError("manifest case count does not match cases.jsonl.gz")
    copy_manifest = manifest.get("profiles", {}).get("copy", {})
    computed = suite_manifest(list(cases.values()), "copy")
    if computed["sha256"] != copy_manifest.get("sha256"):
        raise ValueError("case manifest SHA-256 does not match cases payload")
    if manifest.get("batch_id") != TYPE_UPGRADE_BATCH_ID or manifest.get("batch_kind") != TYPE_UPGRADE_BATCH_KIND:
        raise ValueError("manifest batch identity does not match this new-merge suite")
    return {
        "batch_id": manifest["batch_id"],
        "batch_kind": manifest["batch_kind"],
        "case_count": len(cases),
        "case_manifest_sha256": copy_manifest["sha256"],
        "cases_artifact_sha256": actual_hash,
        "cases_artifact_bytes": len(payload),
    }


def run_local(
    cases_path: Path,
    results_path: Path,
    summary_path: Path,
    *,
    limit: int | None = None,
    case_ids: set[str] | None = None,
    keep_server: bool = False,
    mysqld: str = "/opt/homebrew/opt/mysql@8.0/bin/mysqld",
) -> dict[str, Any]:
    try:
        import pymysql
    except ImportError as error:
        raise RuntimeError("PyMySQL is required for the local runner; install '.[runner]'") from error

    artifact_metadata = verify_case_artifacts(cases_path)
    all_cases = _load_cases(cases_path)
    selected = select_cases(all_cases, case_ids, limit)

    server = LocalMySQLServer(mysqld=mysqld)
    results: list[CaseResult] = []
    started_at = datetime.now(timezone.utc).isoformat()
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
                if not server_version.startswith("8.0.45"):
                    raise RuntimeError(f"expected MySQL 8.0.45, got {server_version}")
                cursor.execute("DROP DATABASE IF EXISTS qa_type_upgrade")
                cursor.execute("CREATE DATABASE qa_type_upgrade CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci")
                cursor.execute("USE qa_type_upgrade")
                # The protocol methods map directly to execute/fetchone.
                adapter = _CursorAdapter(cursor)
                for case in selected:
                    result = execute_case(case, adapter, "copy")
                    results.append(result)
                    if result.outcome is not CaseOutcome.PASS and result.outcome is not CaseOutcome.BLOCKED:
                        # Stop at first failure to preserve evidence and avoid cascading dirty state.
                        break
        finally:
            connection.close()
    finally:
        server.stop()

    counts: dict[str, int] = {}
    for result in results:
        counts[result.outcome.value] = counts.get(result.outcome.value, 0) + 1
    summary = {
        "format_version": 1,
        "profile": "copy",
        "batch_id": artifact_metadata["batch_id"],
        "batch_kind": artifact_metadata["batch_kind"],
        "case_manifest_sha256": artifact_metadata["case_manifest_sha256"],
        "cases_artifact_sha256": artifact_metadata["cases_artifact_sha256"],
        "cases_artifact_bytes": artifact_metadata["cases_artifact_bytes"],
        "artifact_integrity_verified": True,
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "selected_count": len(selected),
        "executed_count": len(results),
        "counts": counts,
        "all_pass": bool(selected) and len(results) == len(selected) and counts.get("PASS", 0) == len(selected),
        "mysqld_version": server_version,
        "stopped_early": len(results) != len(selected),
    }
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with results_path.open("w", encoding="utf-8", newline="\n") as handle:
        for result in results:
            handle.write(json.dumps(result.to_json(), sort_keys=True, separators=(",", ":")) + "\n")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def render_summary_markdown(summary: dict[str, Any]) -> str:
    result = "ALL PASS" if summary.get("all_pass") else "FAIL OR INCOMPLETE"
    counts = ", ".join(f"{key}: {value}" for key, value in sorted(summary.get("counts", {}).items())) or "none"
    stopped = "yes" if summary.get("stopped_early") else "no"
    manifest = summary.get("case_manifest_sha256", "not recorded")
    return (
        "# MySQL type-upgrade COPY local verification\n\n"
        f"**Result:** {result}\n\n"
        f"- **Profile:** {summary.get('profile', 'copy')}\n"
        f"- **Batch ID:** `{summary.get('batch_id', 'unknown')}`\n"
        f"- **Batch kind:** {summary.get('batch_kind', 'unknown')}\n"
        f"- **Selected cases:** {summary.get('selected_count', 0)}\n"
        f"- **Executed cases:** {summary.get('executed_count', 0)}\n"
        f"- **Outcome counts:** {counts}\n"
        f"- **Stopped early:** {stopped}\n"
        f"- **MySQL version:** {summary.get('mysqld_version', 'unknown')}\n"
        f"- **Case manifest SHA-256:** `{manifest}`\n"
    )


class _CursorAdapter:
    def __init__(self, cursor: Any) -> None:
        self.cursor = cursor

    def execute(self, sql: str) -> None:
        self.cursor.execute(sql)

    def fetchone(self) -> Sequence[Any]:
        return self.cursor.fetchone()
