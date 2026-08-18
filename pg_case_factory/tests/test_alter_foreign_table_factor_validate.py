from __future__ import annotations

from pathlib import Path
import unittest

from pg_case_factory.alter_foreign_table_factor_loop import (
    build_alter_foreign_table_factor_loop_plan,
)
from pg_case_factory.alter_foreign_table_factor_render import (
    render_alter_foreign_table_factor_case,
)
from pg_case_factory.alter_foreign_table_factor_validate import (
    remove_primary_semantic_locus_but_keep_comments,
    validate_alter_foreign_table_factor_programs,
)


ROOT = Path(__file__).resolve().parents[1]


class AlterForeignTableFactorProgramValidationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.plan = build_alter_foreign_table_factor_loop_plan(ROOT)
        cls.programs = {
            case.sql_filename: render_alter_foreign_table_factor_case(
                cls.plan,
                case,
                ROOT,
            )
            for case in cls.plan.cases
        }

    def test_final_program_bytes_conserve_every_local_obligation(self) -> None:
        report = validate_alter_foreign_table_factor_programs(
            self.plan,
            self.programs,
            ROOT,
        )

        self.assertTrue(report.passed, report.issues)
        self.assertEqual(1_817, report.decision_count)
        self.assertEqual(1_805, report.sql_file_count)
        self.assertEqual(12, report.delegated_count)
        self.assertEqual(0, report.missing_obligation_count)
        self.assertEqual(0, report.duplicate_obligation_count)
        self.assertEqual(0, report.unknown_obligation_count)
        self.assertEqual(0, report.semantic_witness_mismatch_count)
        self.assertEqual(
            {case.primary_obligation_id for case in self.plan.cases},
            set(report.actual_primary_obligation_ids),
        )
        self.assertEqual(1_805, len(report.sql_sha256))

    def test_comment_only_factor_credit_is_rejected(self) -> None:
        case = self.plan.cases[0]
        mutated = remove_primary_semantic_locus_but_keep_comments(
            self.programs[case.sql_filename],
            case,
        )

        report = validate_alter_foreign_table_factor_programs(
            self.plan,
            {case.sql_filename: mutated},
            ROOT,
            selected_case_ids={case.case_id},
        )

        self.assertFalse(report.passed)
        self.assertEqual(1, report.semantic_witness_mismatch_count)
        self.assertIn(case.case_id, report.semantic_witness_mismatch_case_ids)
        self.assertEqual(1, report.missing_obligation_count)


if __name__ == "__main__":
    unittest.main()
