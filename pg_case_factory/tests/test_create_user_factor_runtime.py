"""Tests for create_user factor runtime module."""

import unittest
from pathlib import Path

from src.pg_case_factory.create_user_factor_runtime import (
    MAX_PARALLELISM,
    PER_FILE_TIMEOUT_SECONDS,
    PG18_BIN,
    PG18_DATABASE,
    PG18_PORT,
    PG18_SOCKET,
    PG18_SUPERUSER,
    CreateUserPg18Runner,
    CreateUserRuntimeError,
    CreateUserSuiteRun,
    build_create_user_runtime_case_set,
    compare_create_user_runs,
)

_REPO = Path(__file__).resolve().parents[1]


class TestCreateUserFactorRuntime(unittest.TestCase):
    def test_constants_distinct_from_create_group_and_role(self) -> None:
        self.assertNotEqual(PG18_PORT, 55602)
        self.assertNotEqual(PG18_DATABASE, "pgcf_cgrp")
        self.assertNotEqual(PG18_PORT, 55603)
        self.assertNotEqual(PG18_DATABASE, "pgcf_crole")

    def test_frozen_constants(self) -> None:
        self.assertEqual(PG18_PORT, 55608)
        self.assertEqual(PG18_DATABASE, "pgcf_cuser")
        self.assertEqual(PG18_SOCKET, Path("/tmp/pgcf-pg18-cuser-sock-20260820"))
        self.assertEqual(PG18_SUPERUSER, "pgcf_superuser")
        self.assertEqual(MAX_PARALLELISM, 1)
        self.assertEqual(PER_FILE_TIMEOUT_SECONDS, 30)

    def test_case_set_count(self) -> None:
        import tempfile
        sql_dir = Path(tempfile.mkdtemp())
        from src.pg_case_factory.create_user_factor_extension import (
            build_create_user_factor_extension_plan,
        )
        from src.pg_case_factory.create_user_factor_loop import (
            build_create_user_factor_loop_plan,
        )
        from src.pg_case_factory.create_user_factor_render import (
            generate_create_user_factor_programs,
        )
        bp = build_create_user_factor_loop_plan(_REPO)
        ep = build_create_user_factor_extension_plan(_REPO)
        generate_create_user_factor_programs(bp, ep, sql_dir)
        cases, paths = build_create_user_runtime_case_set(_REPO, sql_dir)
        self.assertEqual(1674, len(cases))
        self.assertEqual(1674, len(paths))

    def test_sorted_by_ordinal(self) -> None:
        import tempfile
        sql_dir = Path(tempfile.mkdtemp())
        from src.pg_case_factory.create_user_factor_extension import (
            build_create_user_factor_extension_plan,
        )
        from src.pg_case_factory.create_user_factor_loop import (
            build_create_user_factor_loop_plan,
        )
        from src.pg_case_factory.create_user_factor_render import (
            generate_create_user_factor_programs,
        )
        bp = build_create_user_factor_loop_plan(_REPO)
        ep = build_create_user_factor_extension_plan(_REPO)
        generate_create_user_factor_programs(bp, ep, sql_dir)
        cases, _ = build_create_user_runtime_case_set(_REPO, sql_dir)
        ordinals = [c.ordinal for c in cases]
        self.assertEqual(ordinals, sorted(ordinals))

    def test_runner_construction(self) -> None:
        runner = CreateUserPg18Runner()
        self.assertEqual(runner.port, PG18_PORT)
        self.assertEqual(runner.database, PG18_DATABASE)

    def test_timeout_validation(self) -> None:
        with self.assertRaises(CreateUserRuntimeError):
            CreateUserPg18Runner(timeout_seconds=0)
        with self.assertRaises(CreateUserRuntimeError):
            CreateUserPg18Runner(timeout_seconds=301)

    def test_base_command_includes_verbosity_sqlstate(self) -> None:
        runner = CreateUserPg18Runner()
        cmd = runner._base_command()
        self.assertIn("VERBOSITY=sqlstate", cmd)
        self.assertIn("ON_ERROR_STOP=1", cmd)

    def test_cleanup_command_disables_on_error_stop(self) -> None:
        runner = CreateUserPg18Runner()
        cmd = runner._cleanup_command()
        self.assertIn("ON_ERROR_STOP=0", cmd)
        self.assertNotIn("ON_ERROR_STOP=1", cmd)

    def test_suite_run_rejects_invalid_ordinal(self) -> None:
        with self.assertRaises(CreateUserRuntimeError):
            CreateUserSuiteRun(run_ordinal=0, cases=())
        with self.assertRaises(CreateUserRuntimeError):
            CreateUserSuiteRun(run_ordinal=3, cases=())


if __name__ == "__main__":
    unittest.main()
