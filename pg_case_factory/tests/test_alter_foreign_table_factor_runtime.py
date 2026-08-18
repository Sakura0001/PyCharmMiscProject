from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from pg_case_factory.alter_foreign_table_factor_loop import (
    build_alter_foreign_table_factor_loop_plan,
)
from pg_case_factory.alter_foreign_table_factor_render import (
    render_alter_foreign_table_factor_case,
)
from pg_case_factory.alter_foreign_table_factor_runtime import (
    AlterForeignTableCaseRuntimeResult,
    AlterForeignTableSuiteRun,
    AlterForeignTablePg18Runner,
    compare_alter_foreign_table_runs,
)


ROOT = Path(__file__).resolve().parents[1]
PG18_BIN = Path("/tmp/pgcf-postgresql-18.4-install/bin")
PG18_SOCKET = Path("/tmp/pgcf-pg18-aft-sock-20260818")


def _sample_case(stdout: bytes) -> AlterForeignTableCaseRuntimeResult:
    return AlterForeignTableCaseRuntimeResult(
        case_id="ALTERFOREIGNTABLE0001",
        sql_filename="ALTERFOREIGNTABLE0001.sql",
        expected_sqlstate="00000",
        target_sqlstate="00000",
        exit_code=0,
        timed_out=False,
        normalized_stdout=stdout,
        normalized_stderr=b"",
        boolean_oracle_failure_count=0,
        pre_clean=True,
        post_clean=True,
        cleanup_exit_code=0,
    )


class AlterForeignTableFactorRuntimeTest(unittest.TestCase):
    def test_two_run_result_requires_identical_normalized_transcripts(self) -> None:
        identical = compare_alter_foreign_table_runs(
            AlterForeignTableSuiteRun(run_ordinal=1, cases=(_sample_case(b"ok\n"),)),
            AlterForeignTableSuiteRun(run_ordinal=2, cases=(_sample_case(b"ok\n"),)),
        )
        self.assertTrue(identical.passed, identical.issues)

        changed = compare_alter_foreign_table_runs(
            AlterForeignTableSuiteRun(run_ordinal=1, cases=(_sample_case(b"ok\n"),)),
            AlterForeignTableSuiteRun(
                run_ordinal=2,
                cases=(_sample_case(b"different\n"),),
            ),
        )
        self.assertFalse(changed.passed)
        self.assertEqual(
            ("ALTERFOREIGNTABLE0001",),
            changed.transcript_mismatch_case_ids,
        )

    @unittest.skipUnless(
        (PG18_BIN / "psql").is_file() and PG18_SOCKET.is_dir(),
        "local PostgreSQL 18.4 fixture is unavailable",
    )
    def test_six_representative_cases_execute_twice_on_pg18_4(self) -> None:
        plan = build_alter_foreign_table_factor_loop_plan(ROOT)

        def one(predicate):
            return next(case for case in plan.cases if predicate(case))

        selected = (
            plan.cases[0],
            one(lambda case: case.outcome == "expected_failure"),
            one(
                lambda case: case.factor_key == "column_name_shape"
                and case.factor_value == "quoted_mixed_case_identifier"
            ),
            one(
                lambda case: case.factor_key == "data_type_and_typmod"
                and case.factor_value.endswith("::integer")
                and case.outcome == "success"
            ),
            one(
                lambda case: case.factor_key == "partition_key_role"
                and case.factor_value != "not_partition_key"
            ),
            one(
                lambda case: case.kind == "RISK"
                and case.factor_value == "rollback"
            ),
        )
        self.assertEqual(6, len({case.case_id for case in selected}))

        with tempfile.TemporaryDirectory() as temporary:
            sql_dir = Path(temporary)
            paths = {}
            for case in selected:
                path = sql_dir / case.sql_filename
                path.write_text(
                    render_alter_foreign_table_factor_case(plan, case, ROOT),
                    encoding="utf-8",
                )
                paths[case.case_id] = path

            runner = AlterForeignTablePg18Runner()
            runner.verify_server()
            run_01 = runner.run_cases(selected, paths, run_ordinal=1)
            run_02 = runner.run_cases(selected, paths, run_ordinal=2)
            comparison = compare_alter_foreign_table_runs(run_01, run_02)

        self.assertTrue(comparison.passed, comparison.issues)
        self.assertEqual(12, comparison.execution_count)
        self.assertEqual((), comparison.transcript_mismatch_case_ids)
        self.assertEqual((), comparison.cleanup_failure_case_ids)
        self.assertEqual((), comparison.sqlstate_mismatch_case_ids)


if __name__ == "__main__":
    unittest.main()
