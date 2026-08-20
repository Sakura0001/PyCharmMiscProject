from pathlib import Path
import shutil
import tempfile
import unittest

from pg_case_factory.select_into_factor_extension import (
    build_select_into_factor_extension_plan,
)
from pg_case_factory.select_into_factor_loop import (
    build_select_into_factor_loop_plan,
)
from pg_case_factory.select_into_factor_render import (
    generate_select_into_factor_programs,
    render_select_into_factor_case,
)
from pg_case_factory.validate_select_into import (
    SelectIntoFactorProgramValidation,
    remove_primary_semantic_locus_but_keep_comments,
    validate_select_into_factor_programs,
)

ROOT = Path(__file__).resolve().parents[1]


class SelectIntoFactorValidateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = (
            build_select_into_factor_loop_plan(ROOT)
        )
        cls.extension = (
            build_select_into_factor_extension_plan(ROOT)
        )
        cls.tmp = Path(
            tempfile.mkdtemp(prefix="select_into_validate_")
        )
        generate_select_into_factor_programs(
            cls.baseline, cls.extension, cls.tmp
        )
        cls.programs = {}
        for f in sorted(cls.tmp.glob("*.sql")):
            cls.programs[f.name] = f.read_text()

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_validation_passes_for_all_867_files(self) -> None:
        result = validate_select_into_factor_programs(
            self.baseline, self.extension, self.programs, ROOT
        )
        self.assertIsInstance(
            result, SelectIntoFactorProgramValidation
        )
        self.assertTrue(result.passed)
        self.assertEqual(57, result.baseline_case_count)
        self.assertEqual(810, result.extension_case_count)
        self.assertEqual(867, result.sql_file_count)

    def test_no_missing_duplicate_or_unknown_cases(self) -> None:
        result = validate_select_into_factor_programs(
            self.baseline, self.extension, self.programs, ROOT
        )
        self.assertEqual(0, result.missing_case_count)
        self.assertEqual(0, result.duplicate_case_count)
        self.assertEqual(0, result.unknown_obligation_count)

    def test_no_semantic_witness_mismatches(self) -> None:
        result = validate_select_into_factor_programs(
            self.baseline, self.extension, self.programs, ROOT
        )
        self.assertEqual(
            0, result.semantic_witness_mismatch_count
        )

    def test_no_coverage_gaps(self) -> None:
        result = validate_select_into_factor_programs(
            self.baseline, self.extension, self.programs, ROOT
        )
        self.assertEqual(0, result.coverage_gap_count)

    def test_records_cover_all_cases(self) -> None:
        result = validate_select_into_factor_programs(
            self.baseline, self.extension, self.programs, ROOT
        )
        self.assertEqual(867, len(result.records))

    def test_sha256_dictionary_is_complete(self) -> None:
        result = validate_select_into_factor_programs(
            self.baseline, self.extension, self.programs, ROOT
        )
        self.assertEqual(867, len(result.sql_sha256))
        for filename, sha in result.sql_sha256.items():
            self.assertEqual(64, len(sha))

    def test_mutation_helper_replaces_target(self) -> None:
        case = self.baseline.cases[0]
        sql = render_select_into_factor_case(case, ROOT)
        mutated = (
            remove_primary_semantic_locus_but_keep_comments(
                sql, case
            )
        )
        self.assertIn(
            "SELECT true AS removed_primary_semantic_locus;",
            mutated,
        )

    def test_mutation_breaks_validation(self) -> None:
        case = self.baseline.cases[0]
        sql = render_select_into_factor_case(case, ROOT)
        mutated = (
            remove_primary_semantic_locus_but_keep_comments(
                sql, case
            )
        )
        programs = {**self.programs, case.sql_filename: mutated}
        result = validate_select_into_factor_programs(
            self.baseline,
            self.extension,
            programs,
            ROOT,
            selected_case_ids={case.case_id},
        )
        self.assertFalse(result.passed)


if __name__ == "__main__":
    unittest.main()
