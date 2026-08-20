from pathlib import Path
import unittest

from pg_case_factory.create_tablespace_factor_runtime import (
    CreateTablespaceCaseRuntimeResult,
    CreateTablespaceRuntimeError,
    CreateTablespaceSuiteRun,
    CreateTablespaceTwoRunComparison,
    PG18_DATABASE,
    PG18_PORT,
    compare_create_tablespace_runs,
    build_create_tablespace_runtime_case_set,
)

ROOT = Path(__file__).resolve().parents[1]


class CreateTablespaceRuntimeConstructionTest(unittest.TestCase):
    def test_case_set_combines_baseline_and_extension(self) -> None:
        cases, sql_paths = (
            build_create_tablespace_runtime_case_set(ROOT, ROOT)
        )
        self.assertGreaterEqual(len(cases), 4567)
        self.assertEqual(len(cases), len(sql_paths))

    def test_cases_are_sorted_by_ordinal(self) -> None:
        cases, _ = build_create_tablespace_runtime_case_set(
            ROOT, ROOT
        )
        ordinals = [getattr(c, "ordinal") for c in cases]
        self.assertEqual(ordinals, sorted(ordinals))

    def test_sql_paths_map_case_id_to_filename(self) -> None:
        cases, sql_paths = (
            build_create_tablespace_runtime_case_set(ROOT, ROOT)
        )
        for case in cases:
            path = sql_paths[case.case_id]
            self.assertEqual(path.name, case.sql_filename)


class CreateTablespaceRuntimeComparisonTest(unittest.TestCase):
    def _make_result(
        self,
        case_id: str = "CREATETABLESPACE00001",
        sqlstate: str = "00000",
        exit_code: int = 0,
    ) -> CreateTablespaceCaseRuntimeResult:
        return CreateTablespaceCaseRuntimeResult(
            case_id=case_id,
            sql_filename=f"{case_id}.sql",
            expected_sqlstate=sqlstate,
            target_sqlstate=sqlstate,
            exit_code=exit_code,
            timed_out=False,
            normalized_stdout=b"PGCF_TARGET_SQLSTATE=00000\n",
            normalized_stderr=b"",
            boolean_oracle_failure_count=0,
            pre_clean=True,
            post_clean=True,
            cleanup_exit_code=0,
        )

    def test_identical_runs_pass(self) -> None:
        result = self._make_result()
        run1 = CreateTablespaceSuiteRun(
            run_ordinal=1, cases=(result,)
        )
        run2 = CreateTablespaceSuiteRun(
            run_ordinal=2, cases=(result,)
        )
        comparison = compare_create_tablespace_runs(run1, run2)
        self.assertIsInstance(
            comparison, CreateTablespaceTwoRunComparison
        )
        self.assertTrue(comparison.passed)
        self.assertEqual(0, len(comparison.issues))

    def test_sqlstate_mismatch_detected(self) -> None:
        r1 = self._make_result(sqlstate="00000")
        r2 = self._make_result(sqlstate="42710")
        run1 = CreateTablespaceSuiteRun(
            run_ordinal=1, cases=(r1,)
        )
        run2 = CreateTablespaceSuiteRun(
            run_ordinal=2, cases=(r2,)
        )
        comparison = compare_create_tablespace_runs(run1, run2)
        self.assertFalse(comparison.passed)
        self.assertGreater(len(comparison.issues), 0)

    def test_run_ordinal_validation(self) -> None:
        with self.assertRaises(CreateTablespaceRuntimeError):
            CreateTablespaceSuiteRun(
                run_ordinal=3, cases=()
            )


class CreateTablespaceRuntimeConstantsTest(unittest.TestCase):
    def test_frozen_constants(self) -> None:
        self.assertEqual(55499, PG18_PORT)
        self.assertEqual("pgcf_ctsp", PG18_DATABASE)


if __name__ == "__main__":
    unittest.main()
