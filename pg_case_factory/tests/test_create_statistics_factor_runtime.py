"""Tests for create_statistics factor runtime module (no-DB construction)."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.pg_case_factory.create_statistics_factor_runtime import (
    CreateStatisticsRuntimeError,
    CreateStatisticsSuiteRun,
    build_create_statistics_runtime_case_set,
    compare_create_statistics_runs,
)

_REPO = Path(__file__).resolve().parents[1]


class TestCreateStatisticsFactorRuntime(unittest.TestCase):
    def setUp(self) -> None:
        self.cases, self.sql_paths = build_create_statistics_runtime_case_set(
            _REPO, _REPO
        )

    def test_case_set_count(self) -> None:
        self.assertEqual(2640, len(self.cases))

    def test_sql_paths_cover_all_cases(self) -> None:
        for case in self.cases:
            self.assertIn(case.case_id, self.sql_paths)

    def test_cases_sorted_by_ordinal(self) -> None:
        ordinals = [c.ordinal for c in self.cases]
        self.assertEqual(ordinals, sorted(ordinals))

    def test_compare_identical_runs(self) -> None:
        from src.pg_case_factory.create_statistics_factor_runtime import (
            CreateStatisticsCaseRuntimeResult,
        )
        result = CreateStatisticsCaseRuntimeResult(
            case_id="CREATESTATISTICS00001",
            sql_filename="CREATESTATISTICS00001.sql",
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
        run = CreateStatisticsSuiteRun(
            run_ordinal=1, cases=(result,)
        )
        cmp = compare_create_statistics_runs(run, run)
        self.assertTrue(cmp.passed)
        self.assertEqual(2, cmp.execution_count)

    def test_compare_detects_sqlstate_mismatch(self) -> None:
        from src.pg_case_factory.create_statistics_factor_runtime import (
            CreateStatisticsCaseRuntimeResult,
        )
        first = CreateStatisticsCaseRuntimeResult(
            case_id="CREATESTATISTICS00001",
            sql_filename="CREATESTATISTICS00001.sql",
            expected_sqlstate="42710",
            target_sqlstate="42710",
            exit_code=0, timed_out=False,
            normalized_stdout=b"", normalized_stderr=b"",
            boolean_oracle_failure_count=0,
            pre_clean=True, post_clean=True, cleanup_exit_code=0,
        )
        second = CreateStatisticsCaseRuntimeResult(
            case_id="CREATESTATISTICS00001",
            sql_filename="CREATESTATISTICS00001.sql",
            expected_sqlstate="42710",
            target_sqlstate="00000",
            exit_code=0, timed_out=False,
            normalized_stdout=b"", normalized_stderr=b"",
            boolean_oracle_failure_count=0,
            pre_clean=True, post_clean=True, cleanup_exit_code=0,
        )
        run1 = CreateStatisticsSuiteRun(run_ordinal=1, cases=(first,))
        run2 = CreateStatisticsSuiteRun(run_ordinal=2, cases=(second,))
        cmp = compare_create_statistics_runs(run1, run2)
        self.assertFalse(cmp.passed)
        self.assertIn("CREATESTATISTICS00001", cmp.sqlstate_mismatch_case_ids)

    def test_suite_run_rejects_bad_ordinal(self) -> None:
        with self.assertRaises(CreateStatisticsRuntimeError):
            CreateStatisticsSuiteRun(run_ordinal=3, cases=())

    def test_timeout_bounds(self) -> None:
        from src.pg_case_factory.create_statistics_factor_runtime import (
            CreateStatisticsPg18Runner,
        )
        with TemporaryDirectory() as tmp:
            with self.assertRaises(CreateStatisticsRuntimeError):
                CreateStatisticsPg18Runner(
                    bin_dir=Path(tmp), timeout_seconds=0
                )
            with self.assertRaises(CreateStatisticsRuntimeError):
                CreateStatisticsPg18Runner(
                    bin_dir=Path(tmp), timeout_seconds=301
                )


if __name__ == "__main__":
    unittest.main()
