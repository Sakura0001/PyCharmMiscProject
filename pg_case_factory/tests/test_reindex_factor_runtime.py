from pathlib import Path
import unittest

from pg_case_factory.reindex_factor_runtime import (
    ReindexCaseRuntimeResult,
    ReindexRuntimeError,
    ReindexPg18Runner,
    ReindexSuiteRun,
    ReindexTwoRunComparison,
    PG18_BIN,
    PG18_PORT,
    PG18_SOCKET,
    PG18_DATABASE,
    PG18_SUPERUSER,
    PER_FILE_TIMEOUT_SECONDS,
    MAX_PARALLELISM,
    build_reindex_runtime_case_set,
    compare_reindex_runs,
)

ROOT = Path(__file__).resolve().parents[1]


class ReindexRuntimeConstantsTest(unittest.TestCase):
    def test_constants_are_frozen(self) -> None:
        self.assertEqual(55501, PG18_PORT)
        self.assertEqual("pgcf_reindex", PG18_DATABASE)
        self.assertEqual("pgcf_reindex_superuser", PG18_SUPERUSER)
        self.assertEqual(30, PER_FILE_TIMEOUT_SECONDS)
        self.assertEqual(1, MAX_PARALLELISM)


class ReindexRuntimeCaseSetTest(unittest.TestCase):
    def test_builds_case_set_from_repository(self) -> None:
        import tempfile
        tmp = Path(tempfile.mkdtemp(prefix="reindex_rt_"))
        try:
            cases, sql_paths = build_reindex_runtime_case_set(
                ROOT, tmp
            )
            self.assertGreater(len(cases), 0)
            self.assertEqual(len(cases), len(sql_paths))
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)


class ReindexTwoRunComparisonTest(unittest.TestCase):
    def test_comparison_detects_mismatch(self) -> None:
        r1 = ReindexCaseRuntimeResult(
            case_id="REINDEX00001",
            sql_filename="REINDEX00001.sql",
            expected_sqlstate="00000",
            target_sqlstate="00000",
            exit_code=0,
            timed_out=False,
            normalized_stdout=b"t\n",
            normalized_stderr=b"",
            boolean_oracle_failure_count=0,
            pre_clean=True,
            post_clean=True,
            cleanup_exit_code=0,
        )
        r2 = ReindexCaseRuntimeResult(
            case_id="REINDEX00001",
            sql_filename="REINDEX00001.sql",
            expected_sqlstate="00000",
            target_sqlstate="42P01",
            exit_code=0,
            timed_out=False,
            normalized_stdout=b"t\n",
            normalized_stderr=b"",
            boolean_oracle_failure_count=0,
            pre_clean=True,
            post_clean=True,
            cleanup_exit_code=0,
        )
        run1 = ReindexSuiteRun(
            run_ordinal=1, cases=(r1,)
        )
        run2 = ReindexSuiteRun(
            run_ordinal=2, cases=(r2,)
        )
        comparison = compare_reindex_runs(run1, run2)
        self.assertIsInstance(comparison, ReindexTwoRunComparison)
        self.assertFalse(comparison.passed)
        self.assertIn("REINDEX00001", comparison.sqlstate_mismatch_case_ids)

    def test_comparison_passes_on_identical_runs(self) -> None:
        r1 = ReindexCaseRuntimeResult(
            case_id="REINDEX00001",
            sql_filename="REINDEX00001.sql",
            expected_sqlstate="00000",
            target_sqlstate="00000",
            exit_code=0,
            timed_out=False,
            normalized_stdout=b"t\n",
            normalized_stderr=b"",
            boolean_oracle_failure_count=0,
            pre_clean=True,
            post_clean=True,
            cleanup_exit_code=0,
        )
        run1 = ReindexSuiteRun(
            run_ordinal=1, cases=(r1,)
        )
        run2 = ReindexSuiteRun(
            run_ordinal=2, cases=(r1,)
        )
        comparison = compare_reindex_runs(run1, run2)
        self.assertTrue(comparison.passed)


class ReindexPg18RunnerTest(unittest.TestCase):
    def test_runner_rejects_invalid_timeout(self) -> None:
        with self.assertRaises(ReindexRuntimeError):
            ReindexPg18Runner(timeout_seconds=0)
        with self.assertRaises(ReindexRuntimeError):
            ReindexPg18Runner(timeout_seconds=301)


if __name__ == "__main__":
    unittest.main()
