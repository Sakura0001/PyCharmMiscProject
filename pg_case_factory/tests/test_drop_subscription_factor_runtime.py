from pathlib import Path
import unittest

from pg_case_factory.drop_subscription_factor_runtime import (
    DropSubscriptionCaseRuntimeResult,
    DropSubscriptionPg18Runner,
    DropSubscriptionRuntimeError,
    DropSubscriptionSuiteRun,
    DropSubscriptionTwoRunComparison,
    MAX_PARALLELISM,
    PER_FILE_TIMEOUT_SECONDS,
    PG18_BIN,
    PG18_DATABASE,
    PG18_PORT,
    PG18_SOCKET,
    PG18_SUPERUSER,
    build_drop_subscription_runtime_case_set,
    compare_drop_subscription_runs,
)

ROOT = Path(__file__).resolve().parents[1]


class DropSubscriptionRuntimeConstantsTest(unittest.TestCase):
    def test_constants_are_distinct_from_call(self) -> None:
        self.assertNotEqual(PG18_PORT, 55499)
        self.assertNotEqual(PG18_DATABASE, "pgcf_call")
        self.assertNotEqual(
            PG18_SOCKET.name, "pgcf-pg18-call-sock-20260820"
        )

    def test_constants_are_frozen(self) -> None:
        self.assertEqual(55503, PG18_PORT)
        self.assertEqual("pgcf_ds", PG18_DATABASE)
        self.assertEqual("pgcf_superuser", PG18_SUPERUSER)
        self.assertEqual(1, MAX_PARALLELISM)
        self.assertEqual(30, PER_FILE_TIMEOUT_SECONDS)


class DropSubscriptionRuntimeCaseSetTest(unittest.TestCase):
    def test_case_set_has_1188_cases(self) -> None:
        sql_dir = Path("/tmp/dropsubscription_probe_leaf")
        if not sql_dir.is_dir():
            self.skipTest("probe leaf directory not found")
        cases, sql_paths = build_drop_subscription_runtime_case_set(
            ROOT, sql_dir
        )
        self.assertEqual(1188, len(cases))
        self.assertEqual(1188, len(sql_paths))
        for case in cases:
            self.assertIn(case.case_id, sql_paths)

    def test_case_set_is_sorted_by_ordinal(self) -> None:
        sql_dir = Path("/tmp/dropsubscription_probe_leaf")
        if not sql_dir.is_dir():
            self.skipTest("probe leaf directory not found")
        cases, _ = build_drop_subscription_runtime_case_set(ROOT, sql_dir)
        ordinals = [c.ordinal for c in cases]
        self.assertEqual(ordinals, sorted(ordinals))
        self.assertEqual(1, ordinals[0])
        self.assertEqual(1188, ordinals[-1])


class DropSubscriptionRunnerConstructionTest(unittest.TestCase):
    def test_runner_constructs_with_defaults(self) -> None:
        runner = DropSubscriptionPg18Runner()
        self.assertEqual(PG18_PORT, runner.port)
        self.assertEqual(PG18_DATABASE, runner.database)
        self.assertEqual(PG18_SOCKET, runner.socket_dir)

    def test_runner_rejects_invalid_timeout(self) -> None:
        with self.assertRaises(DropSubscriptionRuntimeError):
            DropSubscriptionPg18Runner(timeout_seconds=0)
        with self.assertRaises(DropSubscriptionRuntimeError):
            DropSubscriptionPg18Runner(timeout_seconds=301)

    def test_base_command_includes_sqlstate_verbosity(self) -> None:
        runner = DropSubscriptionPg18Runner()
        cmd = runner._base_command()
        self.assertIn("-v", cmd)
        idx = cmd.index("-v")
        self.assertEqual("VERBOSITY=sqlstate", cmd[idx + 1])

    def test_cleanup_command_disables_on_error_stop(self) -> None:
        runner = DropSubscriptionPg18Runner()
        cleanup = runner._cleanup_command()
        self.assertIn("ON_ERROR_STOP=0", cleanup)
        self.assertNotIn("ON_ERROR_STOP=1", cleanup)

    def test_clean_probe_checks_pg_subscription(self) -> None:
        runner = DropSubscriptionPg18Runner()
        query = runner._clean_probe.__code__.co_consts
        joined = " ".join(str(c) for c in query if isinstance(c, str))
        self.assertIn("pg_subscription", joined)


class DropSubscriptionComparisonTest(unittest.TestCase):
    def _make_result(
        self, case_id: str = "DROPSUBSCRIPTION00001"
    ) -> DropSubscriptionCaseRuntimeResult:
        return DropSubscriptionCaseRuntimeResult(
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
        run1 = DropSubscriptionSuiteRun(run_ordinal=1, cases=(case,))
        run2 = DropSubscriptionSuiteRun(run_ordinal=2, cases=(case,))
        result = compare_drop_subscription_runs(run1, run2)
        self.assertTrue(result.passed)
        self.assertEqual(2, result.execution_count)

    def test_comparison_fails_on_sqlstate_mismatch(self) -> None:
        case = DropSubscriptionCaseRuntimeResult(
            case_id="DROPSUBSCRIPTION00001",
            sql_filename="DROPSUBSCRIPTION00001.sql",
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
        run1 = DropSubscriptionSuiteRun(run_ordinal=1, cases=(case,))
        run2 = DropSubscriptionSuiteRun(run_ordinal=2, cases=(case,))
        result = compare_drop_subscription_runs(run1, run2)
        self.assertFalse(result.passed)
        self.assertIn("DROPSUBSCRIPTION00001", result.sqlstate_mismatch_case_ids)

    def test_suite_run_rejects_invalid_ordinal(self) -> None:
        with self.assertRaises(DropSubscriptionRuntimeError):
            DropSubscriptionSuiteRun(run_ordinal=3, cases=())


if __name__ == "__main__":
    unittest.main()
