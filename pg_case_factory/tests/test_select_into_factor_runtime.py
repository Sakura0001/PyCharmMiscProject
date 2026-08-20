from pathlib import Path
import unittest

from pg_case_factory.select_into_factor_runtime import (
    MAX_PARALLELISM,
    PG18_BIN,
    PG18_DATABASE,
    PG18_PORT,
    PG18_SOCKET,
    PG18_SUPERUSER,
    PER_FILE_TIMEOUT_SECONDS,
    SelectIntoCaseRuntimeResult,
    SelectIntoPg18Runner,
    SelectIntoRuntimeError,
    SelectIntoSuiteRun,
    SelectIntoTwoRunComparison,
    build_select_into_runtime_case_set,
    compare_select_into_runs,
)

ROOT = Path(__file__).resolve().parents[1]


class SelectIntoRuntimeConstantsTest(unittest.TestCase):
    def test_constants_are_frozen(self) -> None:
        self.assertEqual(55622, PG18_PORT)
        self.assertEqual("pgcf_select_into", PG18_DATABASE)
        self.assertEqual("pgcf_superuser", PG18_SUPERUSER)
        self.assertEqual(1, MAX_PARALLELISM)
        self.assertEqual(30, PER_FILE_TIMEOUT_SECONDS)

    def test_port_is_not_5432(self) -> None:
        # Must not collide with the user's PG16 on 5432.
        self.assertNotEqual(5432, PG18_PORT)

    def test_socket_is_distinct(self) -> None:
        self.assertEqual(
            "/tmp/pgcf-pg18-select-into-sock-20260821",
            str(PG18_SOCKET),
        )


class SelectIntoRuntimeCaseSetTest(unittest.TestCase):
    def test_case_set_has_867_cases(self) -> None:
        sql_dir = Path("/tmp/select_into_probe_leaf")
        if not sql_dir.is_dir():
            self.skipTest("probe leaf directory not found")
        cases, sql_paths = build_select_into_runtime_case_set(
            ROOT, sql_dir
        )
        self.assertEqual(867, len(cases))
        self.assertEqual(867, len(sql_paths))
        for case in cases:
            self.assertIn(case.case_id, sql_paths)

    def test_case_set_is_sorted_by_ordinal(self) -> None:
        sql_dir = Path("/tmp/select_into_probe_leaf")
        if not sql_dir.is_dir():
            self.skipTest("probe leaf directory not found")
        cases, _ = build_select_into_runtime_case_set(
            ROOT, sql_dir
        )
        ordinals = [c.ordinal for c in cases]
        self.assertEqual(ordinals, sorted(ordinals))
        self.assertEqual(1, ordinals[0])
        self.assertEqual(867, ordinals[-1])


class SelectIntoRunnerConstructionTest(unittest.TestCase):
    def test_runner_constructs_with_defaults(self) -> None:
        runner = SelectIntoPg18Runner()
        self.assertEqual(PG18_PORT, runner.port)
        self.assertEqual(PG18_DATABASE, runner.database)
        self.assertEqual(PG18_SOCKET, runner.socket_dir)

    def test_runner_rejects_invalid_timeout(self) -> None:
        with self.assertRaises(SelectIntoRuntimeError):
            SelectIntoPg18Runner(timeout_seconds=0)
        with self.assertRaises(SelectIntoRuntimeError):
            SelectIntoPg18Runner(timeout_seconds=301)

    def test_base_command_includes_sqlstate_verbosity(
        self,
    ) -> None:
        runner = SelectIntoPg18Runner()
        cmd = runner._base_command()
        self.assertIn("-v", cmd)
        idx = cmd.index("-v")
        self.assertEqual("VERBOSITY=sqlstate", cmd[idx + 1])

    def test_cleanup_command_disables_on_error_stop(
        self,
    ) -> None:
        runner = SelectIntoPg18Runner()
        cleanup = runner._cleanup_command()
        self.assertIn("ON_ERROR_STOP=0", cleanup)
        self.assertNotIn("ON_ERROR_STOP=1", cleanup)


if __name__ == "__main__":
    unittest.main()
