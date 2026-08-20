from pathlib import Path
import unittest

from pg_case_factory.create_schema_factor_runtime import (
    CreateSchemaPg18Runner,
    CreateSchemaRuntimeError,
    MAX_PARALLELISM,
    PER_FILE_TIMEOUT_SECONDS,
    PG18_BIN,
    PG18_DATABASE,
    PG18_PORT,
    PG18_SOCKET,
    PG18_SUPERUSER,
    build_create_schema_runtime_case_set,
    compare_create_schema_runs,
)
from pg_case_factory.create_schema_factor_runtime import (
    CreateSchemaCaseRuntimeResult,
    CreateSchemaSuiteRun,
    CreateSchemaTwoRunComparison,
)

ROOT = Path(__file__).resolve().parents[1]


class CreateSchemaRuntimeConstantsTest(unittest.TestCase):
    def test_constants_are_distinct_from_other_statements(self) -> None:
        self.assertNotEqual(PG18_PORT, 55498)
        self.assertNotEqual(PG18_DATABASE, "pgcf_asub")

    def test_constants_are_frozen(self) -> None:
        self.assertEqual(55499, PG18_PORT)
        self.assertEqual("pgcf_csch", PG18_DATABASE)
        self.assertEqual("pgcf_superuser", PG18_SUPERUSER)
        self.assertEqual(1, MAX_PARALLELISM)
        self.assertEqual(30, PER_FILE_TIMEOUT_SECONDS)


class CreateSchemaRuntimeCaseSetTest(unittest.TestCase):
    def test_case_set_has_10592_cases(self) -> None:
        cases, sql_paths = build_create_schema_runtime_case_set(
            ROOT, Path("/tmp/csch_runtime_test")
        )
        self.assertEqual(10592, len(cases))
        self.assertEqual(10592, len(sql_paths))

    def test_case_set_is_sorted_by_ordinal(self) -> None:
        cases, _ = build_create_schema_runtime_case_set(
            ROOT, Path("/tmp/csch_runtime_test")
        )
        ordinals = [c.ordinal for c in cases]
        self.assertEqual(ordinals, sorted(ordinals))
        self.assertEqual(1, ordinals[0])
        self.assertEqual(10592, ordinals[-1])


class CreateSchemaRunnerConstructionTest(unittest.TestCase):
    def test_runner_constructs_with_defaults(self) -> None:
        runner = CreateSchemaPg18Runner()
        self.assertEqual(PG18_PORT, runner.port)
        self.assertEqual(PG18_DATABASE, runner.database)
        self.assertEqual(PG18_SOCKET, runner.socket_dir)

    def test_runner_rejects_invalid_timeout(self) -> None:
        with self.assertRaises(CreateSchemaRuntimeError):
            CreateSchemaPg18Runner(timeout_seconds=0)
        with self.assertRaises(CreateSchemaRuntimeError):
            CreateSchemaPg18Runner(timeout_seconds=301)


class CreateSchemaCompareRunsTest(unittest.TestCase):
    def _make_result(
        self,
        case_id: str = "CREATESCHEMA00001",
        sqlstate: str = "00000",
    ) -> CreateSchemaCaseRuntimeResult:
        return CreateSchemaCaseRuntimeResult(
            case_id=case_id,
            sql_filename=f"{case_id}.sql",
            expected_sqlstate=sqlstate,
            target_sqlstate=sqlstate,
            exit_code=0,
            timed_out=False,
            normalized_stdout=b"",
            normalized_stderr=b"",
            boolean_oracle_failure_count=0,
            pre_clean=True,
            post_clean=True,
            cleanup_exit_code=0,
        )

    def test_identical_runs_pass(self) -> None:
        r = self._make_result()
        run1 = CreateSchemaSuiteRun(
            run_ordinal=1, cases=(r,)
        )
        run2 = CreateSchemaSuiteRun(
            run_ordinal=2, cases=(r,)
        )
        cmp = compare_create_schema_runs(run1, run2)
        self.assertIsInstance(cmp, CreateSchemaTwoRunComparison)
        self.assertTrue(cmp.passed)
        self.assertEqual(2, cmp.execution_count)

    def test_sqlstate_mismatch_is_detected(self) -> None:
        r1 = self._make_result(sqlstate="00000")
        r1 = CreateSchemaCaseRuntimeResult(
            **{
                **r1.__dict__,
                "target_sqlstate": "42501",
            }
        )
        run1 = CreateSchemaSuiteRun(
            run_ordinal=1, cases=(r1,)
        )
        run2 = CreateSchemaSuiteRun(
            run_ordinal=2, cases=(r1,)
        )
        cmp = compare_create_schema_runs(run1, run2)
        self.assertFalse(cmp.passed)


if __name__ == "__main__":
    unittest.main()
