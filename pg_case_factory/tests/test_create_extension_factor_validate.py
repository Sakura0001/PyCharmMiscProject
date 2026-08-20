from pathlib import Path
import unittest

from pg_case_factory.create_extension_factor_extension import (
    build_create_extension_factor_extension_plan,
)
from pg_case_factory.create_extension_factor_loop import (
    build_create_extension_factor_loop_plan,
)
from pg_case_factory.create_extension_factor_render import (
    render_create_extension_factor_case,
)
from pg_case_factory.create_extension_factor_validate import (
    CreateExtensionFactorProgramValidation,
    remove_primary_semantic_locus_but_keep_comments,
    validate_create_extension_factor_programs,
)

ROOT = Path(__file__).resolve().parents[1]


class CreateExtensionFactorValidateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = build_create_extension_factor_loop_plan(ROOT)
        cls.extension = (
            build_create_extension_factor_extension_plan(ROOT)
        )
        cls.all_cases = list(cls.baseline.cases) + list(
            cls.extension.cases
        )
        cls.programs = {
            case.sql_filename: render_create_extension_factor_case(
                case, ROOT
            )
            for case in cls.all_cases
        }

    def test_validation_passes_for_all_programs(self) -> None:
        report = validate_create_extension_factor_programs(
            self.baseline,
            self.extension,
            self.programs,
            ROOT,
        )
        self.assertTrue(report.passed, report.issues[:5])
        self.assertEqual(63, report.baseline_case_count)
        self.assertEqual(4320, report.extension_case_count)
        self.assertEqual(4383, report.sql_file_count)

    def test_no_missing_or_duplicate_cases(self) -> None:
        report = validate_create_extension_factor_programs(
            self.baseline,
            self.extension,
            self.programs,
            ROOT,
        )
        self.assertEqual(0, report.missing_case_count)
        self.assertEqual(0, report.duplicate_case_count)
        self.assertEqual(0, report.unknown_obligation_count)

    def test_no_semantic_witness_mismatches(self) -> None:
        report = validate_create_extension_factor_programs(
            self.baseline,
            self.extension,
            self.programs,
            ROOT,
        )
        self.assertEqual(
            0, report.semantic_witness_mismatch_count
        )

    def test_no_coverage_gaps(self) -> None:
        report = validate_create_extension_factor_programs(
            self.baseline,
            self.extension,
            self.programs,
            ROOT,
        )
        self.assertEqual(0, report.coverage_gap_count)

    def test_mutation_helper_detects_target_removal(self) -> None:
        case = self.baseline.cases[0]
        sql = self.programs[case.sql_filename]
        mutated = remove_primary_semantic_locus_but_keep_comments(
            sql, case
        )
        self.assertNotEqual(sql, mutated)
        self.assertIn("removed_primary_semantic_locus", mutated)

    def test_mutated_program_fails_validation(self) -> None:
        case = self.baseline.cases[0]
        sql = self.programs[case.sql_filename]
        mutated = remove_primary_semantic_locus_but_keep_comments(
            sql, case
        )
        mutated_programs = dict(self.programs)
        mutated_programs[case.sql_filename] = mutated
        report = validate_create_extension_factor_programs(
            self.baseline,
            self.extension,
            mutated_programs,
            ROOT,
        )
        self.assertFalse(report.passed)
        self.assertGreater(report.semantic_witness_mismatch_count, 0)

    def test_selected_case_ids_validation(self) -> None:
        selected = {
            self.baseline.cases[0].case_id,
            self.baseline.cases[1].case_id,
        }
        selected_filenames = {
            self.baseline.cases[0].sql_filename,
            self.baseline.cases[1].sql_filename,
        }
        selected_programs = {
            name: sql
            for name, sql in self.programs.items()
            if name in selected_filenames
        }
        report = validate_create_extension_factor_programs(
            self.baseline,
            self.extension,
            selected_programs,
            ROOT,
            selected_case_ids=selected,
        )
        self.assertTrue(report.passed, report.issues[:5])

    def test_to_dict_roundtrip(self) -> None:
        report = validate_create_extension_factor_programs(
            self.baseline,
            self.extension,
            self.programs,
            ROOT,
        )
        d = report.to_dict()
        self.assertEqual(
            "create_extension_actual_factor_witness_report",
            d["kind"],
        )
        self.assertTrue(d["passed"])


if __name__ == "__main__":
    unittest.main()
