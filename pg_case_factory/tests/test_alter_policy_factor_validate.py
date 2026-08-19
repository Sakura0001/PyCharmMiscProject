from __future__ import annotations

from pathlib import Path
import unittest

from pg_case_factory.alter_policy_factor_extension import (
    build_alter_policy_factor_extension_plan,
)
from pg_case_factory.alter_policy_factor_loop import (
    build_alter_policy_factor_loop_plan,
)
from pg_case_factory.alter_policy_factor_render import (
    render_alter_policy_factor_case,
)
from pg_case_factory.alter_policy_factor_validate import (
    AlterPolicyFactorProgramValidation,
    remove_primary_semantic_locus_but_keep_comments,
    validate_alter_policy_factor_programs,
)


ROOT = Path(__file__).resolve().parents[1]

_BASELINE_COUNT = 72
_EXTENSION_COUNT = 13032
_TOTAL = _BASELINE_COUNT + _EXTENSION_COUNT

# Module-level cache so the 13104-program render happens once across tests.
_FULL_CACHE: tuple[dict[str, str], object, object] | None = None


def _full_programs() -> tuple[dict[str, str], object, object]:
    global _FULL_CACHE
    if _FULL_CACHE is None:
        baseline_plan = build_alter_policy_factor_loop_plan(ROOT)
        extension_plan = build_alter_policy_factor_extension_plan(ROOT)
        programs: dict[str, str] = {}
        for case in baseline_plan.cases:
            programs[case.sql_filename] = (
                render_alter_policy_factor_case(case, ROOT)
            )
        for case in extension_plan.cases:
            programs[case.sql_filename] = (
                render_alter_policy_factor_case(case, ROOT)
            )
        _FULL_CACHE = (programs, baseline_plan, extension_plan)
    return _FULL_CACHE


def _subset_programs(
    baseline_plan: object, extension_plan: object, n: int = 2
) -> tuple[dict[str, str], set[str]]:
    chosen: list[object] = list(baseline_plan.cases[:n]) + list(
        extension_plan.cases[:n]
    )
    programs = {
        c.sql_filename: render_alter_policy_factor_case(c, ROOT)
        for c in chosen
    }
    selected = {c.case_id for c in chosen}
    return programs, selected


class AlterPolicyFactorValidateTest(unittest.TestCase):
    def test_full_program_set_is_conserved(self) -> None:
        programs, baseline_plan, extension_plan = _full_programs()
        report = validate_alter_policy_factor_programs(
            baseline_plan, extension_plan, programs, ROOT
        )
        self.assertIsInstance(
            report, AlterPolicyFactorProgramValidation
        )
        self.assertTrue(report.passed, report.issues)
        self.assertEqual(_BASELINE_COUNT, report.baseline_case_count)
        self.assertEqual(_EXTENSION_COUNT, report.extension_case_count)
        self.assertEqual(_TOTAL, report.sql_file_count)
        self.assertEqual(0, report.missing_case_count)
        self.assertEqual(0, report.duplicate_case_count)
        self.assertEqual(0, report.unknown_obligation_count)
        self.assertEqual(0, report.semantic_witness_mismatch_count)
        self.assertEqual(0, report.coverage_gap_count)

    def test_missing_program_is_reported(self) -> None:
        baseline_plan = build_alter_policy_factor_loop_plan(ROOT)
        extension_plan = build_alter_policy_factor_extension_plan(ROOT)
        programs, selected = _subset_programs(
            baseline_plan, extension_plan
        )
        removed = next(iter(programs))
        del programs[removed]
        report = validate_alter_policy_factor_programs(
            baseline_plan,
            extension_plan,
            programs,
            ROOT,
            selected_case_ids=selected,
        )
        self.assertFalse(report.passed)
        self.assertEqual(1, report.missing_case_count)

    def test_unknown_program_is_reported(self) -> None:
        programs, baseline_plan, extension_plan = _full_programs()
        # 99999 is outside the 00001-13104 case range, so it is genuinely
        # unknown.
        extra = "ALTERPOLICY99999.sql"
        programs = {
            **programs,
            extra: (
                "-- --------------------------------------------------------\n"
                "-- case_id: ALTERPOLICY99999\n"
                "-- primary_obligation_id: AP-BOGUS|unknown\n"
                "-- expected_outcome: success\n"
                "-- expected_sqlstate: 00000\n"
                "-- primary-target-begin\n"
                "ALTER POLICY bogus_policy ON bogus_table RENAME TO bogus;\n"
                "-- primary-target-end\n"
                "SELECT 1;\n"
            ),
        }
        report = validate_alter_policy_factor_programs(
            baseline_plan, extension_plan, programs, ROOT
        )
        self.assertFalse(report.passed)
        self.assertGreaterEqual(report.unknown_obligation_count, 1)

    def test_trace_comments_alone_receive_no_credit(self) -> None:
        baseline_plan = build_alter_policy_factor_loop_plan(ROOT)
        extension_plan = build_alter_policy_factor_extension_plan(ROOT)
        programs, selected = _subset_programs(
            baseline_plan, extension_plan
        )
        target_case = next(
            row for row in baseline_plan.cases if row.outcome == "success"
        )
        target_program = render_alter_policy_factor_case(target_case, ROOT)
        programs[target_case.sql_filename] = (
            remove_primary_semantic_locus_but_keep_comments(
                target_program, target_case
            )
        )
        selected = selected | {target_case.case_id}
        report = validate_alter_policy_factor_programs(
            baseline_plan,
            extension_plan,
            programs,
            ROOT,
            selected_case_ids=selected,
        )
        self.assertFalse(report.passed)
        self.assertIn(
            target_case.case_id,
            report.semantic_witness_mismatch_case_ids,
        )

    def test_selected_subset_validates_only_those_cases(self) -> None:
        baseline_plan = build_alter_policy_factor_loop_plan(ROOT)
        extension_plan = build_alter_policy_factor_extension_plan(ROOT)
        programs, selected = _subset_programs(
            baseline_plan, extension_plan
        )
        report = validate_alter_policy_factor_programs(
            baseline_plan,
            extension_plan,
            programs,
            ROOT,
            selected_case_ids=selected,
        )
        self.assertTrue(report.passed, report.issues)
        self.assertEqual(4, report.sql_file_count)

    def test_extension_records_carry_derivation_identity(self) -> None:
        # Every extension case must carry a derivation record or the byte
        # witness fails closed on extension_derivation_record_missing.
        programs, baseline_plan, extension_plan = _full_programs()
        report = validate_alter_policy_factor_programs(
            baseline_plan,
            extension_plan,
            programs,
            ROOT,
            selected_case_ids={extension_plan.cases[0].case_id},
        )
        self.assertTrue(report.passed, report.issues)
        rec = next(r for r in report.records if r["is_extension"])
        self.assertTrue(rec["semantic_witness_passed"])
        self.assertTrue(rec["primary_obligation_id"].startswith("AP-EXT|"))

    def test_validation_report_is_json_serialisable(self) -> None:
        programs, baseline_plan, extension_plan = _full_programs()
        report = validate_alter_policy_factor_programs(
            baseline_plan,
            extension_plan,
            programs,
            ROOT,
            selected_case_ids={
                baseline_plan.cases[0].case_id,
                extension_plan.cases[0].case_id,
            },
        )
        import json

        blob = json.dumps(report.to_dict())
        self.assertIn("alter_policy_actual_factor_witness_report", blob)
        self.assertIn("marginal_baseline_plus_bounded_extension_v1", blob)


if __name__ == "__main__":
    unittest.main()
