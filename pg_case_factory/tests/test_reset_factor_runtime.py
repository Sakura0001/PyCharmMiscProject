"""Tests for reset factor runtime module."""

import unittest
from pathlib import Path

from src.pg_case_factory.reset_factor_runtime import (
    MAX_PARALLELISM,
    PER_FILE_TIMEOUT_SECONDS,
    PG18_BIN,
    PG18_DATABASE,
    PG18_PORT,
    PG18_SOCKET,
    PG18_SUPERUSER,
    ResetPg18Runner,
    ResetRuntimeError,
    ResetSuiteRun,
    build_reset_runtime_case_set,
    compare_reset_runs,
)

_REPO = Path(__file__).resolve().parents[1]


class TestResetFactorRuntime(unittest.TestCase):
    def test_constants_distinct_from_create_operator(self) -> None:
        self.assertNotEqual(PG18_PORT, 55606)
        self.assertNotEqual(PG18_DATABASE, "pgcf_cop")

    def test_constants_distinct_from_discard(self) -> None:
        self.assertNotEqual(PG18_PORT, 55618)
        self.assertNotEqual(PG18_DATABASE, "pgcf_discard")

    def test_frozen_constants(self) -> None:
        self.assertEqual(PG18_PORT, 55620)
        self.assertEqual(PG18_DATABASE, "pgcf_reset")
        self.assertEqual(
            PG18_SOCKET,
            Path("/tmp/pgcf-pg18-reset-sock-20260821"),
        )
        self.assertEqual(PG18_SUPERUSER, "pgcf_superuser")
        self.assertEqual(MAX_PARALLELISM, 1)
        self.assertEqual(PER_FILE_TIMEOUT_SECONDS, 30)

    def test_case_set_count(self) -> None:
        import tempfile
        sql_dir = Path(tempfile.mkdtemp())
        from src.pg_case_factory.reset_factor_extension import (
            build_reset_factor_extension_plan,
        )
        from src.pg_case_factory.reset_factor_loop import (
            build_reset_factor_loop_plan,
        )
        from src.pg_case_factory.reset_factor_render import (
            generate_reset_factor_programs,
        )
        bp = build_reset_factor_loop_plan(_REPO)
        ep = build_reset_factor_extension_plan(_REPO)
        generate_reset_factor_programs(bp, ep, sql_dir)
        cases, paths = build_reset_runtime_case_set(
            _REPO, sql_dir
        )
        self.assertEqual(4266, len(cases))
        self.assertEqual(4266, len(paths))

    def test_sorted_by_ordinal(self) -> None:
        import tempfile
        sql_dir = Path(tempfile.mkdtemp())
        from src.pg_case_factory.reset_factor_extension import (
            build_reset_factor_extension_plan,
        )
        from src.pg_case_factory.reset_factor_loop import (
            build_reset_factor_loop_plan,
        )
        from src.pg_case_factory.reset_factor_render import (
            generate_reset_factor_programs,
        )
        bp = build_reset_factor_loop_plan(_REPO)
        ep = build_reset_factor_extension_plan(_REPO)
        generate_reset_factor_programs(bp, ep, sql_dir)
        cases, _ = build_reset_runtime_case_set(
            _REPO, sql_dir
        )
        ordinals = [c.ordinal for c in cases]
        self.assertEqual(ordinals, sorted(ordinals))

    def test_runner_construction(self) -> None:
        runner = ResetPg18Runner()
        self.assertEqual(runner.port, PG18_PORT)
        self.assertEqual(runner.database, PG18_DATABASE)

    def test_timeout_validation(self) -> None:
        with self.assertRaises(ResetRuntimeError):
            ResetPg18Runner(timeout_seconds=0)
        with self.assertRaises(ResetRuntimeError):
            ResetPg18Runner(timeout_seconds=301)

    def test_base_command_includes_verbosity_sqlstate(
        self,
    ) -> None:
        runner = ResetPg18Runner()
        cmd = runner._base_command()
        self.assertIn("VERBOSITY=sqlstate", cmd)
        self.assertIn("ON_ERROR_STOP=1", cmd)

    def test_cleanup_command_disables_on_error_stop(
        self,
    ) -> None:
        runner = ResetPg18Runner()
        cmd = runner._cleanup_command()
        self.assertIn("ON_ERROR_STOP=0", cmd)
        self.assertNotIn("ON_ERROR_STOP=1", cmd)

    def test_suite_run_rejects_invalid_ordinal(self) -> None:
        with self.assertRaises(ResetRuntimeError):
            ResetSuiteRun(run_ordinal=0, cases=())
        with self.assertRaises(ResetRuntimeError):
            ResetSuiteRun(run_ordinal=3, cases=())

    def test_compare_runs_passes_for_identical(self) -> None:
        result = ResetSuiteRun(
            run_ordinal=1, cases=()
        )
        other = ResetSuiteRun(run_ordinal=2, cases=())
        comparison = compare_reset_runs(result, other)
        self.assertTrue(comparison.passed)


if __name__ == "__main__":
    unittest.main()
