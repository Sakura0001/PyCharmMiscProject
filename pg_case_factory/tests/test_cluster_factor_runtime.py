from pathlib import Path
import unittest

from pg_case_factory.cluster_factor_runtime import (
    ClusterCaseRuntimeResult,
    ClusterPg18Runner,
    ClusterRuntimeError,
    ClusterSuiteRun,
    ClusterTwoRunComparison,
    MAX_PARALLELISM,
    PER_FILE_TIMEOUT_SECONDS,
    PG18_BIN,
    PG18_DATABASE,
    PG18_PORT,
    PG18_SOCKET,
    PG18_SUPERUSER,
    build_cluster_runtime_case_set,
    compare_cluster_runs,
)

ROOT = Path(__file__).resolve().parents[1]


class ClusterRuntimeConstantsTest(unittest.TestCase):
    def test_constants_are_distinct_from_alter_subscription(self) -> None:
        self.assertNotEqual(PG18_PORT, 55498)
        self.assertNotEqual(PG18_DATABASE, "pgcf_asub")
        self.assertNotEqual(
            PG18_SOCKET.name, "pgcf-pg18-asub-sock-20260820"
        )

    def test_constants_are_frozen(self) -> None:
        self.assertEqual(55499, PG18_PORT)
        self.assertEqual("pgcf_cluster", PG18_DATABASE)
        self.assertEqual("pgcf_cluster_superuser", PG18_SUPERUSER)
        self.assertEqual(1, MAX_PARALLELISM)
        self.assertEqual(30, PER_FILE_TIMEOUT_SECONDS)


class ClusterRuntimeCaseSetTest(unittest.TestCase):
    def test_case_set_has_4919_cases(self) -> None:
        sql_dir = Path("/tmp/cluster_probe_leaf")
        if not sql_dir.is_dir():
            self.skipTest("probe leaf directory not found")
        cases, sql_paths = build_cluster_runtime_case_set(
            ROOT, sql_dir
        )
        self.assertEqual(4919, len(cases))
        self.assertEqual(4919, len(sql_paths))
        for case in cases:
            self.assertIn(case.case_id, sql_paths)

    def test_case_set_is_sorted_by_ordinal(self) -> None:
        sql_dir = Path("/tmp/cluster_probe_leaf")
        if not sql_dir.is_dir():
            self.skipTest("probe leaf directory not found")
        cases, _ = build_cluster_runtime_case_set(ROOT, sql_dir)
        ordinals = [c.ordinal for c in cases]
        self.assertEqual(ordinals, sorted(ordinals))
        self.assertEqual(1, ordinals[0])
        self.assertEqual(4919, ordinals[-1])


class ClusterRunnerConstructionTest(unittest.TestCase):
    def test_runner_constructs_with_defaults(self) -> None:
        runner = ClusterPg18Runner()
        self.assertEqual(PG18_PORT, runner.port)
        self.assertEqual(PG18_DATABASE, runner.database)
        self.assertEqual(PG18_SOCKET, runner.socket_dir)

    def test_runner_rejects_invalid_timeout(self) -> None:
        with self.assertRaises(ClusterRuntimeError):
            ClusterPg18Runner(timeout_seconds=0)
        with self.assertRaises(ClusterRuntimeError):
            ClusterPg18Runner(timeout_seconds=301)

    def test_base_command_includes_sqlstate_verbosity(self) -> None:
        runner = ClusterPg18Runner()
        cmd = runner._base_command()
        self.assertIn("-v", cmd)
        idx = cmd.index("-v")
        self.assertEqual("VERBOSITY=sqlstate", cmd[idx + 1])

    def test_cleanup_command_disables_on_error_stop(self) -> None:
        runner = ClusterPg18Runner()
        cleanup = runner._cleanup_command()
        self.assertIn("ON_ERROR_STOP=0", cleanup)
        self.assertNotIn("ON_ERROR_STOP=1", cleanup)

    def test_clean_probe_checks_pg_class_not_subscription(self) -> None:
        runner = ClusterPg18Runner()
        query = runner._clean_probe.__code__.co_consts
        joined = " ".join(str(c) for c in query if isinstance(c, str))
        self.assertIn("pg_class", joined)
        self.assertNotIn("pg_subscription", joined)


class ClusterComparisonTest(unittest.TestCase):
    def _make_result(
        self, case_id: str = "CLUSTER00001"
    ) -> ClusterCaseRuntimeResult:
        return ClusterCaseRuntimeResult(
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
        run1 = ClusterSuiteRun(run_ordinal=1, cases=(case,))
        run2 = ClusterSuiteRun(run_ordinal=2, cases=(case,))
        result = compare_cluster_runs(run1, run2)
        self.assertTrue(result.passed)
        self.assertEqual(2, result.execution_count)

    def test_comparison_fails_on_sqlstate_mismatch(self) -> None:
        case = ClusterCaseRuntimeResult(
            case_id="CLUSTER00001",
            sql_filename="CLUSTER00001.sql",
            expected_sqlstate="00000",
            target_sqlstate="42704",
            exit_code=0,
            timed_out=False,
            normalized_stdout=b"PGCF_TARGET_SQLSTATE=42704\n",
            normalized_stderr=b"",
            boolean_oracle_failure_count=0,
            pre_clean=True,
            post_clean=True,
            cleanup_exit_code=0,
        )
        run1 = ClusterSuiteRun(run_ordinal=1, cases=(case,))
        run2 = ClusterSuiteRun(run_ordinal=2, cases=(case,))
        result = compare_cluster_runs(run1, run2)
        self.assertFalse(result.passed)
        self.assertIn(
            "CLUSTER00001", result.sqlstate_mismatch_case_ids
        )

    def test_suite_run_rejects_invalid_ordinal(self) -> None:
        with self.assertRaises(ClusterRuntimeError):
            ClusterSuiteRun(run_ordinal=3, cases=())


if __name__ == "__main__":
    unittest.main()
