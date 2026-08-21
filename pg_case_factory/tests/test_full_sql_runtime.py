from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pg_case_factory.full_sql_runtime import (
    _start_workers,
    CaseExecution,
    EVIDENCE_COMPATIBILITY,
    EVIDENCE_OBSERVATIONAL,
    EVIDENCE_STRICT,
    RuntimeManifestCase,
    PostgresWorker,
    WorkerConfig,
    calibration_cases,
    build_worker_configs,
    load_runtime_manifest,
    partition_cases,
    report_runtime_results,
    run_case_pair,
    write_runtime_manifest,
    compare_case_runs,
    compile_runtime_manifest,
    evaluate_case_execution,
)


STRICT_SQL = """-- case_id: STRICT0001
-- expected_outcome: success
-- expected_sqlstate: 00000
-- primary-target-begin
SELECT true;
-- primary-target-end
\\echo PGCF_TARGET_SQLSTATE=:SQLSTATE
SELECT :'SQLSTATE' = '00000' AS target_sqlstate_matches_expected;
-- 5. cleanup
"""


class RuntimeManifestTest(unittest.TestCase):
    def test_manifest_uses_sql_files_not_schedules_and_deduplicates_retained(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            current = root / "artifacts/regress/by-factor/ddl/example"
            current.mkdir(parents=True)
            (current / "STRICT0001.sql").write_text(STRICT_SQL)
            (current / "STRICT0002.sql").write_text(
                STRICT_SQL.replace("STRICT0001", "STRICT0002")
            )
            (current / "serial_schedule").write_text("test: STRICT0001\n")
            (current / "external_schedule").write_text("test: STRICT0002\n")

            retained = root / "artifacts/regress/cursor-factor-full-v1/sql"
            retained.mkdir(parents=True)
            legacy = """-- case_id: CUR00001
-- description  : Verify PostgreSQL 18.4 CLOSE with factors
-- factor expected_status=failure
CLOSE missing_cursor;
"""
            (retained / "CUR00001.sql").write_text(legacy)

            progress_path = root / "progress.json"
            progress_path.write_text(
                json.dumps(
                    {
                        "statements": {
                            "example": {
                                "status": "completed",
                                "package_path": str(current.relative_to(root)),
                                "sql_file_count": 2,
                            },
                            "close": {
                                "status": "retained_existing",
                                "package_path": "artifacts/regress/cursor-factor-full-v1",
                            },
                            "declare": {
                                "status": "retained_existing",
                                "package_path": "artifacts/regress/cursor-factor-full-v1",
                            },
                        }
                    }
                )
            )

            manifest = compile_runtime_manifest(root, progress_path)

        self.assertEqual(3, len(manifest))
        by_id = {case.case_id: case for case in manifest}
        self.assertEqual(EVIDENCE_STRICT, by_id["STRICT0001"].evidence_level)
        self.assertFalse(by_id["STRICT0001"].external)
        self.assertTrue(by_id["STRICT0002"].external)
        self.assertEqual(EVIDENCE_OBSERVATIONAL, by_id["CUR00001"].evidence_level)
        self.assertEqual("close", by_id["CUR00001"].statement_key)
        self.assertEqual("expected_failure", by_id["CUR00001"].expected_outcome)

    def test_compatibility_case_is_bound_to_plan_metadata_and_sql_sha(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            package = root / "artifacts/regress/by-factor/ddl/legacy"
            package.mkdir(parents=True)
            sql = """-- case_id: LEGACY0001
-- factor expected_status=failure
SELECT false AS target_sqlstate_matches;
"""
            sql_path = package / "LEGACY0001.sql"
            sql_path.write_text(sql)
            evidence = (
                root
                / "artifacts/intermediates/remaining-statement-factor-cycle/legacy"
            )
            evidence.mkdir(parents=True)
            (evidence / "plan.json").write_text(
                json.dumps(
                    {
                        "cases": [
                            {
                                "case_id": "LEGACY0001",
                                "sql_filename": "LEGACY0001.sql",
                                "object_prefix": "legacy_0001_",
                                "outcome": "expected_failure",
                                "derived_axes": {"expected_sqlstate": "42704"},
                            }
                        ]
                    }
                )
            )
            progress_path = root / "progress.json"
            progress_path.write_text(
                json.dumps(
                    {
                        "statements": {
                            "legacy": {
                                "status": "completed",
                                "package_path": str(package.relative_to(root)),
                                "sql_file_count": 1,
                            }
                        }
                    }
                )
            )

            [case] = compile_runtime_manifest(root, progress_path)

        self.assertEqual(EVIDENCE_COMPATIBILITY, case.evidence_level)
        self.assertEqual("expected_failure", case.expected_outcome)
        self.assertEqual("42704", case.expected_sqlstate)
        self.assertEqual(hashlib.sha256(sql.encode()).hexdigest(), case.sql_sha256)
        self.assertEqual("legacy_0001_", case.object_prefix)


class RuntimeEvaluationTest(unittest.TestCase):
    def manifest_case(
        self,
        *,
        evidence_level: str = EVIDENCE_STRICT,
        expected_outcome: str | None = "success",
        expected_sqlstate: str | None = "00000",
    ) -> RuntimeManifestCase:
        return RuntimeManifestCase(
            ordinal=1,
            statement_key="select",
            case_id="SELECT00001",
            sql_path="sql/SELECT00001.sql",
            sql_sha256="a" * 64,
            package_path="sql",
            evidence_level=evidence_level,
            expected_outcome=expected_outcome,
            expected_sqlstate=expected_sqlstate,
            object_prefix="select_00001_",
            external=False,
        )

    def execution(
        self,
        *,
        stdout: bytes = b"PGCF_TARGET_SQLSTATE=00000\nt\n",
        stderr: bytes = b"",
        exit_code: int = 0,
        timed_out: bool = False,
    ) -> CaseExecution:
        return CaseExecution(
            exit_code=exit_code,
            timed_out=timed_out,
            stdout=stdout,
            stderr=stderr,
            duration_ms=12,
        )

    def test_strict_contract_requires_exact_sqlstate_and_true_oracles(self) -> None:
        passed = evaluate_case_execution(
            self.manifest_case(), self.execution(), run_ordinal=1
        )
        wrong_state = evaluate_case_execution(
            self.manifest_case(),
            self.execution(stdout=b"PGCF_TARGET_SQLSTATE=42P01\nt\n"),
            run_ordinal=1,
        )
        false_oracle = evaluate_case_execution(
            self.manifest_case(),
            self.execution(stdout=b"PGCF_TARGET_SQLSTATE=00000\nf\n"),
            run_ordinal=1,
        )
        missing_state = evaluate_case_execution(
            self.manifest_case(),
            self.execution(stdout=b"t\n"),
            run_ordinal=1,
        )

        self.assertTrue(passed.passed)
        self.assertEqual("strict_pass", passed.classification)
        self.assertEqual("00000", passed.target_sqlstate)
        self.assertEqual("sqlstate_mismatch", wrong_state.classification)
        self.assertEqual("oracle_failure", false_oracle.classification)
        self.assertEqual("missing_target_sqlstate", missing_state.classification)

    def test_timeout_and_nonzero_exit_take_precedence(self) -> None:
        timed_out = evaluate_case_execution(
            self.manifest_case(),
            self.execution(exit_code=124, timed_out=True),
            run_ordinal=1,
        )
        failed = evaluate_case_execution(
            self.manifest_case(), self.execution(exit_code=2), run_ordinal=1
        )
        self.assertEqual("timeout", timed_out.classification)
        self.assertEqual("unexpected_psql_error", failed.classification)

    def test_compatibility_contract_does_not_claim_strict_sqlstate(self) -> None:
        result = evaluate_case_execution(
            self.manifest_case(
                evidence_level=EVIDENCE_COMPATIBILITY,
                expected_outcome="expected_failure",
                expected_sqlstate="42704",
            ),
            self.execution(stdout=b"t\nt\n", stderr=b"ERROR:  42704\n"),
            run_ordinal=1,
        )
        self.assertTrue(result.passed)
        self.assertEqual("compatibility_pass", result.classification)
        self.assertIsNone(result.target_sqlstate)

    def test_observational_failure_remains_not_strictly_judgeable(self) -> None:
        result = evaluate_case_execution(
            self.manifest_case(
                evidence_level=EVIDENCE_OBSERVATIONAL,
                expected_outcome="expected_failure",
                expected_sqlstate=None,
            ),
            self.execution(stdout=b"", stderr=b"ERROR:  34000\n"),
            run_ordinal=1,
        )
        mismatch = evaluate_case_execution(
            self.manifest_case(
                evidence_level=EVIDENCE_OBSERVATIONAL,
                expected_outcome="success",
                expected_sqlstate=None,
            ),
            self.execution(stderr=b"ERROR:  42P01\n"),
            run_ordinal=1,
        )
        self.assertTrue(result.passed)
        self.assertEqual("not_strictly_judgeable", result.classification)
        self.assertFalse(result.strictly_judgeable)
        self.assertEqual("observed_mismatch", mismatch.classification)

    def test_two_run_comparison_detects_normalized_transcript_drift(self) -> None:
        first = evaluate_case_execution(
            self.manifest_case(), self.execution(), run_ordinal=1
        )
        second = evaluate_case_execution(
            self.manifest_case(),
            self.execution(stdout=b"PGCF_TARGET_SQLSTATE=00000\nt\nextra\n"),
            run_ordinal=2,
        )
        comparison = compare_case_runs(first, second)
        self.assertFalse(comparison.passed)
        self.assertEqual("two_run_mismatch", comparison.classification)

    def test_compatibility_normalizes_recreated_user_object_oids(self) -> None:
        case = self.manifest_case(
            evidence_level=EVIDENCE_COMPATIBILITY,
            expected_outcome="success",
            expected_sqlstate="00000",
        )
        first = evaluate_case_execution(
            case,
            self.execution(stdout=b"16446|legacy_object|16443|t\n"),
            run_ordinal=1,
        )
        second = evaluate_case_execution(
            case,
            self.execution(stdout=b"16450|legacy_object|16447|t\n"),
            run_ordinal=2,
        )
        comparison = compare_case_runs(first, second)
        self.assertTrue(comparison.passed)
        self.assertEqual(first.normalized_stdout, second.normalized_stdout)


class PostgresWorkerTest(unittest.TestCase):
    def test_start_failure_stops_each_started_worker_once(self) -> None:
        created = []

        class FakeWorker:
            def __init__(self, config, *, timeout_seconds: int) -> None:
                self.index = len(created)
                self.stop_calls = 0
                created.append(self)

            def start(self) -> None:
                if self.index == 1:
                    raise RuntimeError("startup failed")

            def stop(self) -> None:
                self.stop_calls += 1

        configs = (object(), object())
        with (
            patch(
                "pg_case_factory.full_sql_runtime.build_worker_configs",
                return_value=configs,
            ),
            patch("pg_case_factory.full_sql_runtime.PostgresWorker", FakeWorker),
            self.assertRaises(RuntimeError),
        ):
            _start_workers(
                output_root=Path("/runtime"),
                bin_dir=Path("/pg/bin"),
                worker_count=2,
                base_port=55720,
                timeout_seconds=30,
            )

        self.assertEqual(1, created[0].stop_calls)
        self.assertEqual(0, created[1].stop_calls)

    def test_worker_configs_are_isolated_and_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            configs = build_worker_configs(
                Path(raw), Path("/tmp/pg18/bin"), workers=4, base_port=55720
            )
            self.assertEqual(4, len(configs))
            self.assertEqual(4, len({config.port for config in configs}))
            self.assertEqual(4, len({config.worker_root for config in configs}))
            with self.assertRaises(ValueError):
                build_worker_configs(
                    Path(raw), Path("/tmp/pg18/bin"), workers=5
                )

    def test_psql_command_uses_private_socket_and_pg18_contract(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            config = WorkerConfig(
                worker_id=1,
                bin_dir=Path("/tmp/pg18/bin"),
                worker_root=Path(raw) / "worker-01",
                port=55720,
            )
            worker = PostgresWorker(config, timeout_seconds=30)
            command = worker.psql_command(Path("/repo/CASE0001.sql"))
        self.assertIn(str(worker.socket_dir), command)
        self.assertIn("55720", command)
        self.assertIn("VERBOSITY=sqlstate", command)
        self.assertIn("ON_ERROR_STOP=1", command)
        self.assertNotIn("127.0.0.1", command)

    def test_socket_path_stays_below_postgres_unix_socket_limit(self) -> None:
        long_root = Path("/Users/example") / ("very-long-runtime-segment-" * 8)
        worker = PostgresWorker(
            WorkerConfig(
                worker_id=4,
                bin_dir=Path("/tmp/pg18/bin"),
                worker_root=long_root,
                port=55723,
            )
        )
        socket_file = worker.socket_dir / ".s.PGSQL.55723"
        self.assertLessEqual(len(str(socket_file)), 103)

    def test_server_environment_routes_dblink_back_to_same_worker(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            worker = PostgresWorker(
                WorkerConfig(
                    worker_id=2,
                    bin_dir=Path("/tmp/pg18/bin"),
                    worker_root=Path(raw) / "worker-02",
                    port=55721,
                )
            )
            environment = worker.server_environment()
        self.assertEqual(str(worker.socket_dir), environment["PGHOST"])
        self.assertEqual("55721", environment["PGPORT"])
        self.assertEqual("pgcf_superuser", environment["PGUSER"])

    def test_execute_converts_subprocess_timeout_to_bounded_result(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            config = WorkerConfig(
                worker_id=1,
                bin_dir=Path("/tmp/pg18/bin"),
                worker_root=Path(raw) / "worker-01",
                port=55720,
            )
            worker = PostgresWorker(config, timeout_seconds=7)
            timeout = __import__("subprocess").TimeoutExpired(
                ["psql"], 7, output=b"partial", stderr=b"late"
            )
            with patch("pg_case_factory.full_sql_runtime.subprocess.run", side_effect=timeout):
                execution = worker.execute(Path("/repo/CASE0001.sql"))
        self.assertTrue(execution.timed_out)
        self.assertEqual(124, execution.exit_code)
        self.assertEqual(b"partial", execution.stdout)
        self.assertEqual(b"late", execution.stderr)

    def test_rebuild_archives_log_and_removes_old_cluster_generation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            worker = PostgresWorker(
                WorkerConfig(
                    worker_id=1,
                    bin_dir=Path("/tmp/pg18/bin"),
                    worker_root=Path(raw) / "worker-01",
                    port=55720,
                )
            )
            old_root = worker.generation_root
            old_root.mkdir(parents=True)
            worker.log_path.write_text("diagnostic")
            with patch.object(worker, "start") as start:
                worker.rebuild()
            archived = worker.config.worker_root / "rebuild-logs/generation-0001.log"
            self.assertFalse(old_root.exists())
            self.assertEqual("diagnostic", archived.read_text())
            self.assertEqual(2, worker.generation)
            start.assert_called_once_with()


class RuntimeBatchingTest(unittest.TestCase):
    def manifest_case(
        self,
        ordinal: int,
        *,
        statement: str = "select",
        outcome: str = "success",
        external: bool = False,
    ) -> RuntimeManifestCase:
        return RuntimeManifestCase(
            ordinal=ordinal,
            statement_key=statement,
            case_id=f"CASE{ordinal:05d}",
            sql_path=f"sql/CASE{ordinal:05d}.sql",
            sql_sha256=f"{ordinal:064x}",
            package_path="sql",
            evidence_level=EVIDENCE_STRICT,
            expected_outcome=outcome,
            expected_sqlstate="00000" if outcome == "success" else "42704",
            object_prefix=f"case_{ordinal:05d}_",
            external=external,
        )

    def test_manifest_jsonl_round_trip_and_batch_partition(self) -> None:
        cases = tuple(self.manifest_case(index) for index in range(1, 6))
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "manifest.jsonl"
            write_runtime_manifest(path, cases)
            loaded = load_runtime_manifest(path)
        self.assertEqual(cases, loaded)
        self.assertEqual([2, 2, 1], [len(batch) for batch in partition_cases(cases, 2)])
        self.assertEqual([[1, 2], [3, 4], [5]], [[c.ordinal for c in b] for b in partition_cases(cases, 2)])

    def test_calibration_selects_success_failure_and_all_external(self) -> None:
        cases = (
            self.manifest_case(1, statement="select", outcome="success"),
            self.manifest_case(2, statement="select", outcome="expected_failure"),
            self.manifest_case(3, statement="select", outcome="success", external=True),
            self.manifest_case(4, statement="insert", outcome="success"),
            self.manifest_case(5, statement="insert", outcome="success", external=True),
        )
        selected = calibration_cases(cases)
        self.assertEqual({1, 2, 3, 4, 5}, {case.ordinal for case in selected})

    def test_run_case_pair_executes_twice_and_preserves_failure_transcript(self) -> None:
        class FakeWorker:
            def __init__(self) -> None:
                self.calls = 0
                self.rebuilds = 0

            def execute(self, path: Path) -> CaseExecution:
                self.calls += 1
                return CaseExecution(
                    exit_code=2,
                    timed_out=False,
                    stdout=b"PGCF_TARGET_SQLSTATE=42P01\nf\n",
                    stderr=b"psql:/repo/case.sql:4: ERROR:  42P01\n",
                    duration_ms=1,
                )

            def rebuild(self) -> None:
                self.rebuilds += 1

        worker = FakeWorker()
        case = self.manifest_case(1)
        pair = run_case_pair(worker, Path("/repo"), case)
        self.assertEqual(2, worker.calls)
        self.assertGreaterEqual(worker.rebuilds, 1)
        self.assertFalse(pair["comparison"]["passed"])
        self.assertIn("stdout", pair["run_01"])
        self.assertIn("stderr", pair["run_02"])

    def test_sql_script_error_does_not_rebuild_healthy_unique_prefix_worker(self) -> None:
        class FakeWorker:
            def __init__(self) -> None:
                self.rebuilds = 0

            def execute(self, path: Path) -> CaseExecution:
                return CaseExecution(
                    exit_code=3,
                    timed_out=False,
                    stdout=b"",
                    stderr=b"psql:/repo/case.sql:4: ERROR:  42704\n",
                    duration_ms=1,
                )

            def rebuild(self) -> None:
                self.rebuilds += 1

        worker = FakeWorker()
        pair = run_case_pair(worker, Path("/repo"), self.manifest_case(1))
        self.assertEqual(0, worker.rebuilds)
        self.assertEqual("unexpected_psql_error", pair["comparison"]["classification"])

    def test_report_audits_manifest_pairs_and_writes_statement_and_sqlstate_summaries(self) -> None:
        cases = (
            self.manifest_case(1, statement="select", outcome="success"),
            self.manifest_case(
                2, statement="insert", outcome="expected_failure"
            ),
        )
        passed = {
            "schema_version": 1,
            "case": cases[0].to_dict(),
            "run_01": {
                "target_sqlstate": "00000",
                "error_sqlstates": [],
                "duration_ms": 2,
            },
            "run_02": {
                "target_sqlstate": "00000",
                "error_sqlstates": [],
                "duration_ms": 3,
            },
            "comparison": {
                "classification": "strict_pass",
                "passed": True,
                "transcript_matches": True,
                "structured_matches": True,
            },
        }
        failed = {
            "schema_version": 1,
            "case": cases[1].to_dict(),
            "run_01": {
                "target_sqlstate": "42P01",
                "error_sqlstates": ["42P01"],
                "duration_ms": 5,
            },
            "run_02": {
                "target_sqlstate": "42P01",
                "error_sqlstates": ["42P01"],
                "duration_ms": 7,
            },
            "comparison": {
                "classification": "sqlstate_mismatch",
                "passed": False,
                "transcript_matches": True,
                "structured_matches": True,
            },
        }
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw)
            write_runtime_manifest(output / "manifest.jsonl", cases)
            (output / "checkpoint.json").write_text(
                json.dumps(
                    {
                        "server_version_num": 180004,
                        "total_cases": 2,
                        "completed_cases": 2,
                        "completed_executions": 4,
                        "batch_count": 1,
                        "completed_batches": 1,
                    }
                )
            )
            results = output / "results"
            results.mkdir()
            (results / "batch-00001.jsonl").write_text(
                "\n".join(json.dumps(record) for record in (passed, failed))
                + "\n"
            )

            summary = report_runtime_results(output)

            self.assertTrue(summary["integrity"]["complete"])
            self.assertEqual(2, summary["integrity"]["paired_case_count"])
            self.assertEqual(4, summary["integrity"]["execution_count"])
            self.assertEqual(
                {"strict_pass": 1, "sqlstate_mismatch": 1},
                summary["classifications"],
            )
            statement_summary = json.loads(
                (output / "reports/statement-summary.json").read_text()
            )
            sqlstate_summary = json.loads(
                (output / "reports/sqlstate-summary.json").read_text()
            )

        self.assertEqual(1, statement_summary["statements"]["insert"]["not_passed_count"])
        self.assertEqual(
            1,
            sqlstate_summary["expected_to_actual"]["42704"]["42P01"],
        )


if __name__ == "__main__":
    unittest.main()
