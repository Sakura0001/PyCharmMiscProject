"""Tests for create_collation factor runtime module."""

import unittest
from dataclasses import dataclass
from pathlib import Path

from src.pg_case_factory.create_collation_factor_runtime import (
    MAX_PARALLELISM,
    PER_FILE_TIMEOUT_SECONDS,
    PG18_BIN,
    PG18_DATABASE,
    PG18_PORT,
    PG18_SOCKET,
    PG18_SUPERUSER,
    CreateCollationPg18Runner,
    CreateCollationRuntimeError,
    CreateCollationSuiteRun,
    build_create_collation_runtime_case_set,
    compare_create_collation_runs,
)

_REPO = Path(__file__).resolve().parents[1]


class TestCreateCollationFactorRuntime(unittest.TestCase):
    def test_constants_distinct_from_alter_subscription(self) -> None:
        self.assertNotEqual(PG18_PORT, 55498)
        self.assertNotEqual(PG18_DATABASE, "pgcf_asub")

    def test_frozen_constants(self) -> None:
        self.assertEqual(PG18_PORT, 55499)
        self.assertEqual(PG18_DATABASE, "pgcf_ccol")
        self.assertEqual(PG18_SOCKET, Path("/tmp/pgcf-pg18-ccol-sock-20260820"))
        self.assertEqual(PG18_SUPERUSER, "pgcf_superuser")
        self.assertEqual(MAX_PARALLELISM, 1)
        self.assertEqual(PER_FILE_TIMEOUT_SECONDS, 30)

    def test_case_set_count(self) -> None:
        import tempfile
        sql_dir = Path(tempfile.mkdtemp())
        from src.pg_case_factory.create_collation_factor_extension import (
            build_create_collation_factor_extension_plan,
        )
        from src.pg_case_factory.create_collation_factor_loop import (
            build_create_collation_factor_loop_plan,
        )
        from src.pg_case_factory.create_collation_factor_render import (
            generate_create_collation_factor_programs,
        )
        bp = build_create_collation_factor_loop_plan(_REPO)
        ep = build_create_collation_factor_extension_plan(_REPO)
        generate_create_collation_factor_programs(bp, ep, sql_dir)
        cases, paths = build_create_collation_runtime_case_set(_REPO, sql_dir)
        self.assertEqual(1135, len(cases))
        self.assertEqual(1135, len(paths))

    def test_sorted_by_ordinal(self) -> None:
        import tempfile
        sql_dir = Path(tempfile.mkdtemp())
        from src.pg_case_factory.create_collation_factor_extension import (
            build_create_collation_factor_extension_plan,
        )
        from src.pg_case_factory.create_collation_factor_loop import (
            build_create_collation_factor_loop_plan,
        )
        from src.pg_case_factory.create_collation_factor_render import (
            generate_create_collation_factor_programs,
        )
        bp = build_create_collation_factor_loop_plan(_REPO)
        ep = build_create_collation_factor_extension_plan(_REPO)
        generate_create_collation_factor_programs(bp, ep, sql_dir)
        cases, _ = build_create_collation_runtime_case_set(_REPO, sql_dir)
        ordinals = [c.ordinal for c in cases]
        self.assertEqual(ordinals, sorted(ordinals))

    def test_runner_construction(self) -> None:
        runner = CreateCollationPg18Runner()
        self.assertEqual(runner.port, PG18_PORT)
        self.assertEqual(runner.database, PG18_DATABASE)

    def test_timeout_validation(self) -> None:
        with self.assertRaises(CreateCollationRuntimeError):
            CreateCollationPg18Runner(timeout_seconds=0)
        with self.assertRaises(CreateCollationRuntimeError):
            CreateCollationPg18Runner(timeout_seconds=301)

    def test_base_command_includes_verbosity_sqlstate(self) -> None:
        runner = CreateCollationPg18Runner()
        cmd = runner._base_command()
        self.assertIn("VERBOSITY=sqlstate", cmd)
        self.assertIn("ON_ERROR_STOP=1", cmd)

    def test_cleanup_command_disables_on_error_stop(self) -> None:
        runner = CreateCollationPg18Runner()
        cmd = runner._cleanup_command()
        self.assertIn("ON_ERROR_STOP=0", cmd)
        self.assertNotIn("ON_ERROR_STOP=1", cmd)

    def test_suite_run_rejects_invalid_ordinal(self) -> None:
        with self.assertRaises(CreateCollationRuntimeError):
            CreateCollationSuiteRun(run_ordinal=0, cases=())
        with self.assertRaises(CreateCollationRuntimeError):
            CreateCollationSuiteRun(run_ordinal=3, cases=())


if __name__ == "__main__":
    unittest.main()
