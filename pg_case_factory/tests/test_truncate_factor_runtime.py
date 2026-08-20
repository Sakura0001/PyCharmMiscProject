from pathlib import Path
import unittest

from pg_case_factory.truncate_factor_runtime import (
    MAX_PARALLELISM,
    PER_FILE_TIMEOUT_SECONDS,
    PG18_BIN,
    PG18_DATABASE,
    PG18_PORT,
    PG18_SOCKET,
    PG18_SUPERUSER,
    TruncateCaseRuntimeResult,
    TruncatePg18Runner,
    TruncateRuntimeError,
    TruncateSuiteRun,
    TruncateTwoRunComparison,
    build_truncate_runtime_case_set,
    compare_truncate_runs,
)

ROOT = Path(__file__).resolve().parents[1]


class TruncateRuntimeConstantsTest(unittest.TestCase):
    def test_constants_are_distinct_from_delete(self) -> None:
        self.assertNotEqual(PG18_PORT, 55500)
        self.assertNotEqual(PG18_DATABASE, "pgcf_delete")
        self.assertNotEqual(
            PG18_SOCKET.name, "pgcf-pg18-delete-sock-20260820"
        )

    def test_constants_are_frozen(self) -> None:
        self.assertEqual(55501, PG18_PORT)
        self.assertEqual("pgcf_truncate", PG18_DATABASE)
        self.assertEqual("pgcf_superuser", PG18_SUPERUSER)
        self.assertEqual(1, MAX_PARALLELISM)
        self.assertEqual(30, PER_FILE_TIMEOUT_SECONDS)


class TruncateRuntimeCaseSetTest(unittest.TestCase):
    def test_case_set_has_5813_cases(self) -> None:
        sql_dir = Path("/tmp/truncate_probe_leaf")
        if not sql_dir.is_dir():
            self.skipTest("probe leaf directory not found")
        cases, sql_paths = build_truncate_runtime_case_set(
            ROOT, sql_dir
        )
        self.assertEqual(5813, len(cases))
        self.assertEqual(5813, len(sql_paths))
        for case in cases:
            self.assertIn(case.case_id, sql_paths)

    def test_case_set_is_sorted_by_ordinal(self) -> None:
        sql_dir = Path("/tmp/truncate_probe_leaf")
        if not sql_dir.is_dir():
            self.skipTest("probe leaf directory not found")
        cases, _ = build_truncate_runtime_case_set(ROOT, sql_dir)
        ordinals = [c.ordinal for c in cases]
        self.assertEqual(ordinals, sorted(ordinals))
        self.assertEqual(1, ordinals[0])
        self.assertEqual(5813, ordinals[-1])


class TruncateRunnerConstructionTest(unittest.TestCase):
    def test_runner_constructs_with_defaults(self) -> None:
        runner = TruncatePg18Runner()
        self.assertEqual(PG18_PORT, runner.port)
        self.assertEqual(PG18_DATABASE, runner.database)
        self.assertEqual(PG18_SOCKET, runner.socket_dir)

    def test_runner_rejects_invalid_timeout(self) -> None:
        with self.assertRaises(TruncateRuntimeError):
            TruncatePg18Runner(timeout_seconds=0)
        with self.assertRaises(TruncateRuntimeError):
            TruncatePg18Runner(timeout_seconds=301)

    def test_base_command_includes_sqlstate_verbosity(self) -> None:
        runner = TruncatePg18Runner()
        cmd = runner._base_command()
        self.assertIn("-v", cmd)
        idx = cmd.index("-v")
        self.assertEqual("VERBOSITY=sqlstate", cmd[idx + 1])

    def test_cleanup_command_disables_on_error_stop(self) -> None:
        runner = TruncatePg18Runner()
        cleanup = runner._cleanup_command()
        self.assertIn("ON_ERROR_STOP=0", cleanup)
        self.assertNotIn("ON_ERROR_STOP=1", cleanup)

    def test_clean_probe_checks_pg_class(self) -> None:
        runner = TruncatePg18Runner()
        query = runner._clean_probe.__code__.co_consts
        joined = " ".join(str(c) for c in query if isinstance(c, str))
        self.assertIn("pg_class", joined)


class TruncateComparisonTest(unittest.TestCase):
    def _make_result(
        self, case_id: str = "TRUNCATE00001"
    ) -> TruncateCaseRuntimeResult:
        return TruncateCaseRuntimeResult(
            case_id=case_id,
            sql_filename=f"{case_id}.sql",
            expected_sqlstate="00000",
            target_sqlstate="00000",
            exit_code=0,
            timed_out=False,
            normalized_stdout=b"PGCF_TARGET_SQLSTATE=00000\n",
            normalized_stderr=b"",
            boolean_oracle_failure_count=0,
            pre_clean=True,
            post_clean=True,
            cleanup_exit_code=0,
        )

    def test_comparison_passes_on_identical_runs(self) -> None:
        case = self._make_result()
        run1 = TruncateSuiteRun(run_ordinal=1, cases=(case,))
        run2 = TruncateSuiteRun(run_ordinal=2, cases=(case,))
        result = compare_truncate_runs(run1, run2)
        self.assertTrue(result.passed)
        self.assertEqual(2, result.execution_count)

    def test_comparison_fails_on_sqlstate_mismatch(self) -> None:
        case = TruncateCaseRuntimeResult(
            case_id="TRUNCATE00001",
            sql_filename="TRUNCATE00001.sql",
            expected_sqlstate="00000",
            target_sqlstate="42P01",
            exit_code=0,
            timed_out=False,
            normalized_stdout=b"PGCF_TARGET_SQLSTATE=42P01\n",
            normalized_stderr=b"",
            boolean_oracle_failure_count=0,
            pre_clean=True,
            post_clean=True,
            cleanup_exit_code=0,
        )
        run1 = TruncateSuiteRun(run_ordinal=1, cases=(case,))
        run2 = TruncateSuiteRun(run_ordinal=2, cases=(case,))
        result = compare_truncate_runs(run1, run2)
        self.assertFalse(result.passed)
        self.assertIn("TRUNCATE00001", result.sqlstate_mismatch_case_ids)

    def test_suite_run_rejects_invalid_ordinal(self) -> None:
        with self.assertRaises(TruncateRuntimeError):
            TruncateSuiteRun(run_ordinal=3, cases=())


if __name__ == "__main__":
    unittest.main()
