from pathlib import Path
import unittest

from pg_case_factory.create_foreign_data_wrapper_factor_runtime import (
    CreateForeignDataWrapperCaseRuntimeResult,
    CreateForeignDataWrapperPg18Runner,
    CreateForeignDataWrapperRuntimeError,
    CreateForeignDataWrapperSuiteRun,
    CreateForeignDataWrapperTwoRunComparison,
    MAX_PARALLELISM,
    PER_FILE_TIMEOUT_SECONDS,
    PG18_DATABASE,
    PG18_PORT,
    PG18_SOCKET,
    build_create_foreign_data_wrapper_runtime_case_set,
    compare_create_foreign_data_wrapper_runs,
)

ROOT = Path(__file__).resolve().parents[1]


class CreateForeignDataWrapperRuntimeConstantsTest(unittest.TestCase):
    def test_frozen_socket_path(self) -> None:
        self.assertEqual(
            Path("/tmp/pgcf-pg18-cfdw-sock-20260820"),
            PG18_SOCKET,
        )

    def test_frozen_port(self) -> None:
        self.assertEqual(55544, PG18_PORT)

    def test_frozen_database(self) -> None:
        self.assertEqual("pgcf_cfdw", PG18_DATABASE)

    def test_timeout_bounds(self) -> None:
        self.assertGreater(PER_FILE_TIMEOUT_SECONDS, 0)
        self.assertLessEqual(PER_FILE_TIMEOUT_SECONDS, 300)

    def test_max_parallelism_is_serial(self) -> None:
        self.assertEqual(1, MAX_PARALLELISM)


class CreateForeignDataWrapperRuntimeCaseSetTest(unittest.TestCase):
    def test_case_set_combines_baseline_and_extension(self) -> None:
        cases, sql_paths = (
            build_create_foreign_data_wrapper_runtime_case_set(
                ROOT, ROOT / "tmp_runtime_sql"
            )
        )
        self.assertEqual(2650, len(cases))
        self.assertEqual(2650, len(sql_paths))
        ordinals = [c.ordinal for c in cases]
        self.assertEqual(ordinals, sorted(ordinals))
        self.assertEqual(1, ordinals[0])
        self.assertEqual(2650, ordinals[-1])


class CreateForeignDataWrapperRuntimeComparisonTest(unittest.TestCase):
    def _make_result(
        self,
        case_id: str,
        sqlstate: str = "00000",
        expected: str = "00000",
        exit_code: int = 0,
    ) -> CreateForeignDataWrapperCaseRuntimeResult:
        return CreateForeignDataWrapperCaseRuntimeResult(
            case_id=case_id,
            sql_filename=f"{case_id}.sql",
            expected_sqlstate=expected,
            target_sqlstate=sqlstate,
            exit_code=exit_code,
            timed_out=False,
            normalized_stdout=b"",
            normalized_stderr=b"",
            boolean_oracle_failure_count=0,
            pre_clean=True,
            post_clean=True,
            cleanup_exit_code=0,
        )

    def test_identical_runs_pass(self) -> None:
        run1 = CreateForeignDataWrapperSuiteRun(
            run_ordinal=1,
            cases=(
                self._make_result("CFDW001"),
                self._make_result("CFDW002"),
            ),
        )
        run2 = CreateForeignDataWrapperSuiteRun(
            run_ordinal=2,
            cases=(
                self._make_result("CFDW001"),
                self._make_result("CFDW002"),
            ),
        )
        comparison = compare_create_foreign_data_wrapper_runs(
            run1, run2
        )
        self.assertTrue(comparison.passed)
        self.assertEqual(0, len(comparison.issues))

    def test_sqlstate_mismatch_fails(self) -> None:
        run1 = CreateForeignDataWrapperSuiteRun(
            run_ordinal=1,
            cases=(
                self._make_result("CFDW001", sqlstate="42710"),
            ),
        )
        run2 = CreateForeignDataWrapperSuiteRun(
            run_ordinal=2,
            cases=(
                self._make_result("CFDW001", sqlstate="42710"),
            ),
        )
        comparison = compare_create_foreign_data_wrapper_runs(
            run1, run2
        )
        self.assertFalse(comparison.passed)
        self.assertEqual(
            ("CFDW001",),
            comparison.sqlstate_mismatch_case_ids,
        )


class CreateForeignDataWrapperRunnerValidationTest(unittest.TestCase):
    def test_invalid_timeout_raises(self) -> None:
        with self.assertRaises(CreateForeignDataWrapperRuntimeError):
            CreateForeignDataWrapperPg18Runner(timeout_seconds=0)

    def test_timeout_too_large_raises(self) -> None:
        with self.assertRaises(CreateForeignDataWrapperRuntimeError):
            CreateForeignDataWrapperPg18Runner(timeout_seconds=301)

    def test_run_ordinal_must_be_1_or_2(self) -> None:
        with self.assertRaises(CreateForeignDataWrapperRuntimeError):
            CreateForeignDataWrapperSuiteRun(run_ordinal=3, cases=())


if __name__ == "__main__":
    unittest.main()
