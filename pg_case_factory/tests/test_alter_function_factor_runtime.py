from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from pg_case_factory.alter_function_factor_loop import (
    build_alter_function_factor_loop_plan,
)
from pg_case_factory.alter_function_factor_render import (
    render_alter_function_factor_case,
)
from pg_case_factory.alter_function_factor_runtime import (
    AlterFunctionCaseRuntimeResult,
    AlterFunctionPg18Runner,
    AlterFunctionSuiteRun,
    compare_alter_function_runs,
)


ROOT = Path(__file__).resolve().parents[1]
PG18_BIN = Path("/tmp/pgcf-postgresql-18.4-install/bin")
PG18_SOCKET = Path("/tmp/pgcf-pg18-af-sock-20260819")


def _sample_case(stdout: bytes) -> AlterFunctionCaseRuntimeResult:
    return AlterFunctionCaseRuntimeResult(
        case_id="ALTERFUNCTION0001",
        sql_filename="ALTERFUNCTION0001.sql",
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


class AlterFunctionFactorRuntimeTest(unittest.TestCase):
    def test_two_run_result_requires_identical_normalized_transcripts(self) -> None:
        identical = compare_alter_function_runs(
            AlterFunctionSuiteRun(run_ordinal=1, cases=(_sample_case(b"ok\n"),)),
            AlterFunctionSuiteRun(run_ordinal=2, cases=(_sample_case(b"ok\n"),)),
        )
        self.assertTrue(identical.passed, identical.issues)

        changed = compare_alter_function_runs(
            AlterFunctionSuiteRun(run_ordinal=1, cases=(_sample_case(b"ok\n"),)),
            AlterFunctionSuiteRun(
                run_ordinal=2,
                cases=(_sample_case(b"different\n"),),
            ),
        )
        self.assertFalse(changed.passed)
        self.assertEqual(
            ("ALTERFUNCTION0001",),
            changed.transcript_mismatch_case_ids,
        )

    @unittest.skipUnless(
        (PG18_BIN / "psql").is_file() and PG18_SOCKET.is_dir(),
        "local PostgreSQL 18.4 fixture is unavailable",
    )
    def test_six_representative_cases_execute_twice_on_pg18_4(self) -> None:
        plan = build_alter_function_factor_loop_plan(ROOT)

        def one(predicate):
            return next(case for case in plan.cases if predicate(case))

        selected = (
            plan.cases[0],
            one(lambda case: case.outcome == "expected_failure"),
            one(
                lambda case: case.factor_key == "object_state"
                and case.factor_value == "different_signature_exists"
            ),
            one(
                lambda case: case.factor_key == "privilege_level"
                and case.factor_value == "non_owner_no_privilege"
            ),
            one(
                lambda case: case.kind == "RISK"
                and case.factor_value == "rollback"
            ),
            one(
                lambda case: case.factor_key == "rename_target"
                and case.factor_value == "duplicate_name"
            ),
        )
        self.assertEqual(6, len({case.case_id for case in selected}))

        with tempfile.TemporaryDirectory() as temporary:
            sql_dir = Path(temporary)
            paths = {}
            for case in selected:
                path = sql_dir / case.sql_filename
                path.write_text(
                    render_alter_function_factor_case(plan, case, ROOT),
                    encoding="utf-8",
                )
                paths[case.case_id] = path

            runner = AlterFunctionPg18Runner()
            runner.verify_server()
            run_01 = runner.run_cases(selected, paths, run_ordinal=1)
            run_02 = runner.run_cases(selected, paths, run_ordinal=2)
            comparison = compare_alter_function_runs(run_01, run_02)

        self.assertTrue(comparison.passed, comparison.issues)
        self.assertEqual(12, comparison.execution_count)
        self.assertEqual((), comparison.transcript_mismatch_case_ids)
        self.assertEqual((), comparison.cleanup_failure_case_ids)
        self.assertEqual((), comparison.sqlstate_mismatch_case_ids)


if __name__ == "__main__":
    unittest.main()
