from pathlib import Path
import unittest

from pg_case_factory.create_event_trigger_factor_runtime import (
    CreateEventTriggerCaseRuntimeResult,
    CreateEventTriggerPg18Runner,
    CreateEventTriggerRuntimeError,
    CreateEventTriggerSuiteRun,
    CreateEventTriggerTwoRunComparison,
    MAX_PARALLELISM,
    PER_FILE_TIMEOUT_SECONDS,
    PG18_BIN,
    PG18_DATABASE,
    PG18_PORT,
    PG18_SOCKET,
    PG18_SUPERUSER,
    build_create_event_trigger_runtime_case_set,
    compare_create_event_trigger_runs,
)

ROOT = Path(__file__).resolve().parents[1]


class CreateEventTriggerRuntimeConstantsTest(unittest.TestCase):
    def test_constants_are_distinct_from_checkpoint(self) -> None:
        self.assertNotEqual(PG18_PORT, 55499)
        self.assertNotEqual(PG18_DATABASE, "pgcf_ckpt")
        self.assertNotEqual(
            PG18_SOCKET.name,
            "pgcf-pg18-ckpt-sock-20260820",
        )

    def test_constants_are_frozen(self) -> None:
        self.assertEqual(55541, PG18_PORT)
        self.assertEqual("pgcf_evttrig", PG18_DATABASE)
        self.assertEqual("pgcf_superuser", PG18_SUPERUSER)
        self.assertEqual(1, MAX_PARALLELISM)
        self.assertEqual(30, PER_FILE_TIMEOUT_SECONDS)


class CreateEventTriggerRuntimeCaseSetTest(unittest.TestCase):
    def test_case_set_has_6542_cases(self) -> None:
        sql_dir = Path("/tmp/create_event_trigger_probe_leaf")
        if not sql_dir.is_dir():
            self.skipTest("probe leaf directory not found")
        cases, sql_paths = (
            build_create_event_trigger_runtime_case_set(
                ROOT, sql_dir
            )
        )
        self.assertEqual(6542, len(cases))
        self.assertEqual(6542, len(sql_paths))
        for case in cases:
            self.assertIn(case.case_id, sql_paths)

    def test_case_set_is_sorted_by_ordinal(self) -> None:
        sql_dir = Path("/tmp/create_event_trigger_probe_leaf")
        if not sql_dir.is_dir():
            self.skipTest("probe leaf directory not found")
        cases, _ = (
            build_create_event_trigger_runtime_case_set(
                ROOT, sql_dir
            )
        )
        ordinals = [c.ordinal for c in cases]
        self.assertEqual(ordinals, sorted(ordinals))
        self.assertEqual(1, ordinals[0])
        self.assertEqual(6542, ordinals[-1])


class CreateEventTriggerRunnerConstructionTest(unittest.TestCase):
    def test_runner_constructs_with_defaults(self) -> None:
        runner = CreateEventTriggerPg18Runner()
        self.assertEqual(PG18_PORT, runner.port)
        self.assertEqual(PG18_DATABASE, runner.database)
        self.assertEqual(PG18_SOCKET, runner.socket_dir)

    def test_runner_rejects_invalid_timeout(self) -> None:
        with self.assertRaises(CreateEventTriggerRuntimeError):
            CreateEventTriggerPg18Runner(timeout_seconds=0)
        with self.assertRaises(CreateEventTriggerRuntimeError):
            CreateEventTriggerPg18Runner(timeout_seconds=301)

    def test_base_command_includes_sqlstate_verbosity(self) -> None:
        runner = CreateEventTriggerPg18Runner()
        cmd = runner._base_command()
        self.assertIn("-v", cmd)
        idx = cmd.index("-v")
        self.assertEqual("VERBOSITY=sqlstate", cmd[idx + 1])

    def test_cleanup_command_disables_on_error_stop(self) -> None:
        runner = CreateEventTriggerPg18Runner()
        cleanup = runner._cleanup_command()
        self.assertIn("ON_ERROR_STOP=0", cleanup)
        self.assertNotIn("ON_ERROR_STOP=1", cleanup)

    def test_clean_probe_checks_pg_proc_and_event_trigger(
        self,
    ) -> None:
        runner = CreateEventTriggerPg18Runner()
        query = runner._clean_probe.__code__.co_consts
        joined = " ".join(
            str(c) for c in query if isinstance(c, str)
        )
        self.assertIn("pg_proc", joined)
        self.assertIn("pg_roles", joined)
        self.assertIn("pg_event_trigger", joined)


class CreateEventTriggerComparisonTest(unittest.TestCase):
    def _make_result(
        self, case_id: str = "CREATEEVENTTRIGGER00001"
    ) -> CreateEventTriggerCaseRuntimeResult:
        return CreateEventTriggerCaseRuntimeResult(
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
        run1 = CreateEventTriggerSuiteRun(
            run_ordinal=1, cases=(case,)
        )
        run2 = CreateEventTriggerSuiteRun(
            run_ordinal=2, cases=(case,)
        )
        result = compare_create_event_trigger_runs(run1, run2)
        self.assertTrue(result.passed)
        self.assertEqual(2, result.execution_count)

    def test_comparison_fails_on_sqlstate_mismatch(self) -> None:
        case = CreateEventTriggerCaseRuntimeResult(
            case_id="CREATEEVENTTRIGGER00001",
            sql_filename="CREATEEVENTTRIGGER00001.sql",
            expected_sqlstate="00000",
            target_sqlstate="42501",
            exit_code=0,
            timed_out=False,
            normalized_stdout=b"PGCF_TARGET_SQLSTATE=42501\n",
            normalized_stderr=b"",
            boolean_oracle_failure_count=0,
            pre_clean=True,
            post_clean=True,
            cleanup_exit_code=0,
        )
        run1 = CreateEventTriggerSuiteRun(
            run_ordinal=1, cases=(case,)
        )
        run2 = CreateEventTriggerSuiteRun(
            run_ordinal=2, cases=(case,)
        )
        result = compare_create_event_trigger_runs(run1, run2)
        self.assertFalse(result.passed)
        self.assertIn(
            "CREATEEVENTTRIGGER00001",
            result.sqlstate_mismatch_case_ids,
        )

    def test_suite_run_rejects_invalid_ordinal(self) -> None:
        with self.assertRaises(CreateEventTriggerRuntimeError):
            CreateEventTriggerSuiteRun(run_ordinal=3, cases=())


if __name__ == "__main__":
    unittest.main()
