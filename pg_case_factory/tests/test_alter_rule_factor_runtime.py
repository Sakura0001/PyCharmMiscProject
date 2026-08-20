from __future__ import annotations

from pathlib import Path
import unittest

from pg_case_factory.alter_rule_factor_runtime import (
    AlterRuleCaseRuntimeResult,
    AlterRulePg18Runner,
    AlterRuleSuiteRun,
    AlterRuleTwoRunComparison,
    build_alter_rule_runtime_case_set,
    compare_alter_rule_runs,
)


ROOT = Path(__file__).resolve().parents[1]


def _sample_case(stdout: bytes) -> AlterRuleCaseRuntimeResult:
    return AlterRuleCaseRuntimeResult(
        case_id="ALTERRULE00001",
        sql_filename="ALTERRULE00001.sql",
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


class AlterRuleFactorRuntimeTest(unittest.TestCase):
    def test_two_run_result_requires_identical_normalized_transcripts(self) -> None:
        identical = compare_alter_rule_runs(
            AlterRuleSuiteRun(run_ordinal=1, cases=(_sample_case(b"ok\n"),)),
            AlterRuleSuiteRun(run_ordinal=2, cases=(_sample_case(b"ok\n"),)),
        )
        self.assertTrue(identical.passed, identical.issues)

        changed = compare_alter_rule_runs(
            AlterRuleSuiteRun(run_ordinal=1, cases=(_sample_case(b"ok\n"),)),
            AlterRuleSuiteRun(
                run_ordinal=2,
                cases=(_sample_case(b"different\n"),),
            ),
        )
        self.assertFalse(changed.passed)
        self.assertIn("ALTERRULE00001", changed.transcript_mismatch_case_ids)

    def test_sqlstate_mismatch_is_detected(self) -> None:
        expected = AlterRuleCaseRuntimeResult(
            case_id="ALTERRULE00001",
            sql_filename="ALTERRULE00001.sql",
            expected_sqlstate="42P01",
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
        result = compare_alter_rule_runs(
            AlterRuleSuiteRun(run_ordinal=1, cases=(expected,)),
            AlterRuleSuiteRun(run_ordinal=2, cases=(expected,)),
        )
        self.assertFalse(result.passed)
        self.assertIn("ALTERRULE00001", result.sqlstate_mismatch_case_ids)

    def test_run_ordinal_validation(self) -> None:
        with self.assertRaises(Exception):
            AlterRuleSuiteRun(run_ordinal=3, cases=())

    def test_runtime_case_set_combines_baseline_and_extension(self) -> None:
        import tempfile
        from pg_case_factory.alter_rule_factor_render import (
            generate_alter_rule_factor_programs,
        )
        from pg_case_factory.alter_rule_factor_loop import (
            build_alter_rule_factor_loop_plan,
        )
        from pg_case_factory.alter_rule_factor_extension import (
            build_alter_rule_factor_extension_plan,
        )
        plan = build_alter_rule_factor_loop_plan(ROOT)
        ext = build_alter_rule_factor_extension_plan(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            generate_alter_rule_factor_programs(plan, ext, Path(tmp))
            cases, sql_paths = build_alter_rule_runtime_case_set(
                ROOT, Path(tmp)
            )
            self.assertEqual(2142, len(cases))
            self.assertEqual(2142, len(sql_paths))


if __name__ == "__main__":
    unittest.main()
