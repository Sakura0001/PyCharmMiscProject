from __future__ import annotations

from pathlib import Path
import unittest

from pg_case_factory.alter_function_factor_loop import (
    build_alter_function_factor_loop_plan,
)
from pg_case_factory.alter_function_factor_render import (
    render_alter_function_factor_case,
)
from pg_case_factory.alter_function_factor_validate import (
    AlterFunctionFactorProgramValidation,
    remove_primary_semantic_locus_but_keep_comments,
    validate_alter_function_factor_programs,
)


ROOT = Path(__file__).resolve().parents[1]


def _render_all() -> tuple[dict[str, str], object]:
    plan = build_alter_function_factor_loop_plan(ROOT)
    programs: dict[str, str] = {}
    for case in plan.cases:
        programs[case.sql_filename] = render_alter_function_factor_case(
            plan, case, ROOT
        )
    return programs, plan


class AlterFunctionFactorValidateTest(unittest.TestCase):
    def test_full_program_set_is_conserved(self) -> None:
        programs, plan = _render_all()
        report = validate_alter_function_factor_programs(
            plan, programs, ROOT
        )
        self.assertIsInstance(
            report, AlterFunctionFactorProgramValidation
        )
        self.assertTrue(report.passed, report.issues)
        self.assertEqual(123, report.decision_count)
        self.assertEqual(123, report.sql_file_count)
        self.assertEqual(0, report.delegated_count)
        self.assertEqual(0, report.missing_obligation_count)
        self.assertEqual(0, report.duplicate_obligation_count)
        self.assertEqual(0, report.unknown_obligation_count)
        self.assertEqual(0, report.semantic_witness_mismatch_count)

    def test_missing_program_is_reported(self) -> None:
        programs, plan = _render_all()
        removed = plan.cases[5].sql_filename
        del programs[removed]
        report = validate_alter_function_factor_programs(
            plan, programs, ROOT
        )
        self.assertFalse(report.passed)
        self.assertEqual(1, report.missing_obligation_count)
        self.assertEqual(
            plan.cases[5].primary_obligation_id,
            report.missing_obligation_ids[0],
        )

    def test_unknown_program_is_reported(self) -> None:
        programs, plan = _render_all()
        extra = "ALTERFUNCTION9999.sql"
        programs[extra] = (
            "-- --------------------------------------------------------\n"
            "-- case_id: ALTERFUNCTION9999\n"
            "-- primary_obligation_id: AF-BOGUS|unknown\n"
            "-- expected_outcome: success\n"
            "-- expected_sqlstate: 00000\n"
            "-- primary-target-begin\n"
            "ALTER FUNCTION bogus() VOLATILE;\n"
            "-- primary-target-end\n"
            "SELECT 1;\n"
        )
        report = validate_alter_function_factor_programs(
            plan, programs, ROOT
        )
        self.assertFalse(report.passed)
        self.assertGreaterEqual(report.unknown_obligation_count, 1)

    def test_trace_comments_alone_receive_no_credit(self) -> None:
        programs, plan = _render_all()
        target_case = next(
            row for row in plan.cases if row.outcome == "success"
        )
        original = programs[target_case.sql_filename]
        programs[target_case.sql_filename] = (
            remove_primary_semantic_locus_but_keep_comments(
                original, target_case
            )
        )
        report = validate_alter_function_factor_programs(
            plan, programs, ROOT
        )
        self.assertFalse(report.passed)
        self.assertIn(
            target_case.case_id,
            report.semantic_witness_mismatch_case_ids,
        )
        # the mutated case is no longer credited -> it becomes missing
        self.assertEqual(1, report.missing_obligation_count)

    def test_selected_subset_validates_only_those_cases(self) -> None:
        programs, plan = _render_all()
        chosen = [plan.cases[0], plan.cases[40]]
        selected = {row.case_id for row in chosen}
        subset = {row.sql_filename: programs[row.sql_filename] for row in chosen}
        report = validate_alter_function_factor_programs(
            plan, subset, ROOT, selected_case_ids=selected
        )
        self.assertTrue(report.passed, report.issues)
        self.assertEqual(2, report.sql_file_count)

    def test_validation_report_is_json_serialisable(self) -> None:
        programs, plan = _render_all()
        report = validate_alter_function_factor_programs(
            plan, programs, ROOT
        )
        import json

        blob = json.dumps(report.to_dict())
        self.assertIn("alter_function_actual_factor_witness_report", blob)


if __name__ == "__main__":
    unittest.main()
