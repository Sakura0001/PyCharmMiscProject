from __future__ import annotations

from pathlib import Path
import unittest

from pg_case_factory.alter_statistics_factor_runtime import (
    AlterStatisticsCaseRuntimeResult,
    AlterStatisticsPg18Runner,
    AlterStatisticsSuiteRun,
    AlterStatisticsTwoRunComparison,
    build_alter_statistics_runtime_case_set,
    compare_alter_statistics_runs,
)


ROOT = Path(__file__).resolve().parents[1]


def _sample_case(stdout: bytes) -> AlterStatisticsCaseRuntimeResult:
    return AlterStatisticsCaseRuntimeResult(
        case_id="ALTERSTATISTICS00001",
        sql_filename="ALTERSTATISTICS00001.sql",
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


class AlterStatisticsFactorRuntimeTest(unittest.TestCase):
    def test_two_run_result_requires_identical_normalized_transcripts(
        self,
    ) -> None:
        identical = compare_alter_statistics_runs(
            AlterStatisticsSuiteRun(
                run_ordinal=1, cases=(_sample_case(b"ok\n"),)
            ),
            AlterStatisticsSuiteRun(
                run_ordinal=2, cases=(_sample_case(b"ok\n"),)
            ),
        )
        self.assertTrue(identical.passed, identical.issues)

        changed = compare_alter_statistics_runs(
            AlterStatisticsSuiteRun(
                run_ordinal=1, cases=(_sample_case(b"ok\n"),)
            ),
            AlterStatisticsSuiteRun(
                run_ordinal=2,
                cases=(_sample_case(b"different\n"),),
            ),
        )
        self.assertFalse(changed.passed)
        self.assertIn(
            "ALTERSTATISTICS00001",
            changed.transcript_mismatch_case_ids,
        )

    def test_sqlstate_mismatch_is_detected(self) -> None:
        expected = AlterStatisticsCaseRuntimeResult(
            case_id="ALTERSTATISTICS00001",
            sql_filename="ALTERSTATISTICS00001.sql",
            expected_sqlstate="42704",
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
        result = compare_alter_statistics_runs(
            AlterStatisticsSuiteRun(run_ordinal=1, cases=(expected,)),
            AlterStatisticsSuiteRun(run_ordinal=2, cases=(expected,)),
        )
        self.assertFalse(result.passed)
        self.assertIn(
            "ALTERSTATISTICS00001", result.sqlstate_mismatch_case_ids
        )

    def test_run_ordinal_validation(self) -> None:
        with self.assertRaises(Exception):
            AlterStatisticsSuiteRun(run_ordinal=3, cases=())

    def test_runtime_case_set_combines_baseline_and_extension(
        self,
    ) -> None:
        import tempfile

        from pg_case_factory.alter_statistics_factor_extension import (
            build_alter_statistics_factor_extension_plan,
        )
        from pg_case_factory.alter_statistics_factor_loop import (
            build_alter_statistics_factor_loop_plan,
        )
        from pg_case_factory.alter_statistics_factor_render import (
            generate_alter_statistics_factor_programs,
        )

        plan = build_alter_statistics_factor_loop_plan(ROOT)
        ext = build_alter_statistics_factor_extension_plan(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            generate_alter_statistics_factor_programs(plan, ext, Path(tmp))
            cases, sql_paths = build_alter_statistics_runtime_case_set(
                ROOT, Path(tmp)
            )
            self.assertEqual(1460, len(cases))
            self.assertEqual(1460, len(sql_paths))


if __name__ == "__main__":
    unittest.main()
