"""Tests for import_foreign_schema factor runtime module."""

import tempfile
import unittest
from pathlib import Path

from src.pg_case_factory.import_foreign_schema_factor_runtime import (
    MAX_PARALLELISM,
    PER_FILE_TIMEOUT_SECONDS,
    PG18_BIN,
    PG18_DATABASE,
    PG18_PORT,
    PG18_SOCKET,
    PG18_SUPERUSER,
    ImportForeignSchemaPg18Runner,
    ImportForeignSchemaRuntimeError,
    ImportForeignSchemaSuiteRun,
    build_import_foreign_schema_runtime_case_set,
    compare_import_foreign_schema_runs,
)

_REPO = Path(__file__).resolve().parents[1]


class TestImportForeignSchemaFactorRuntime(unittest.TestCase):
    def test_constants_distinct_from_deallocate(self) -> None:
        self.assertNotEqual(PG18_PORT, 55617)
        self.assertNotEqual(PG18_DATABASE, "pgcf_dealloc")

    def test_frozen_constants(self) -> None:
        self.assertEqual(PG18_PORT, 55618)
        self.assertEqual(PG18_DATABASE, "pgcf_importfs")
        self.assertEqual(
            PG18_SOCKET,
            Path("/tmp/pgcf-pg18-importfs-sock-20260820"),
        )
        self.assertEqual(PG18_SUPERUSER, "pgcf_superuser")
        self.assertEqual(MAX_PARALLELISM, 1)
        self.assertEqual(PER_FILE_TIMEOUT_SECONDS, 30)

    def test_case_set_count(self) -> None:
        sql_dir = Path(tempfile.mkdtemp())
        from src.pg_case_factory.import_foreign_schema_factor_extension import (
            build_import_foreign_schema_factor_extension_plan,
        )
        from src.pg_case_factory.import_foreign_schema_factor_loop import (
            build_import_foreign_schema_factor_loop_plan,
        )
        from src.pg_case_factory.import_foreign_schema_factor_render import (
            generate_import_foreign_schema_factor_programs,
        )
        bp = build_import_foreign_schema_factor_loop_plan(_REPO)
        ep = build_import_foreign_schema_factor_extension_plan(
            _REPO
        )
        generate_import_foreign_schema_factor_programs(
            bp, ep, sql_dir
        )
        cases, paths = build_import_foreign_schema_runtime_case_set(
            _REPO, sql_dir
        )
        self.assertEqual(633, len(cases))
        self.assertEqual(633, len(paths))

    def test_sorted_by_ordinal(self) -> None:
        sql_dir = Path(tempfile.mkdtemp())
        from src.pg_case_factory.import_foreign_schema_factor_extension import (
            build_import_foreign_schema_factor_extension_plan,
        )
        from src.pg_case_factory.import_foreign_schema_factor_loop import (
            build_import_foreign_schema_factor_loop_plan,
        )
        from src.pg_case_factory.import_foreign_schema_factor_render import (
            generate_import_foreign_schema_factor_programs,
        )
        bp = build_import_foreign_schema_factor_loop_plan(_REPO)
        ep = build_import_foreign_schema_factor_extension_plan(
            _REPO
        )
        generate_import_foreign_schema_factor_programs(
            bp, ep, sql_dir
        )
        cases, _ = build_import_foreign_schema_runtime_case_set(
            _REPO, sql_dir
        )
        ordinals = [c.ordinal for c in cases]
        self.assertEqual(ordinals, sorted(ordinals))

    def test_runner_construction(self) -> None:
        runner = ImportForeignSchemaPg18Runner()
        self.assertEqual(runner.port, PG18_PORT)
        self.assertEqual(runner.database, PG18_DATABASE)

    def test_timeout_validation(self) -> None:
        with self.assertRaises(ImportForeignSchemaRuntimeError):
            ImportForeignSchemaPg18Runner(timeout_seconds=0)
        with self.assertRaises(ImportForeignSchemaRuntimeError):
            ImportForeignSchemaPg18Runner(timeout_seconds=301)

    def test_base_command_includes_verbosity_sqlstate(
        self,
    ) -> None:
        runner = ImportForeignSchemaPg18Runner()
        cmd = runner._base_command()
        self.assertIn("VERBOSITY=sqlstate", cmd)
        self.assertIn("ON_ERROR_STOP=1", cmd)

    def test_cleanup_command_disables_on_error_stop(
        self,
    ) -> None:
        runner = ImportForeignSchemaPg18Runner()
        cmd = runner._cleanup_command()
        self.assertIn("ON_ERROR_STOP=0", cmd)
        self.assertNotIn("ON_ERROR_STOP=1", cmd)

    def test_suite_run_rejects_invalid_ordinal(self) -> None:
        with self.assertRaises(ImportForeignSchemaRuntimeError):
            ImportForeignSchemaSuiteRun(run_ordinal=0, cases=())
        with self.assertRaises(ImportForeignSchemaRuntimeError):
            ImportForeignSchemaSuiteRun(run_ordinal=3, cases=())


if __name__ == "__main__":
    unittest.main()
