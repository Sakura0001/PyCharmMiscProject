from pathlib import Path
import shutil
import tempfile
import unittest

from pg_case_factory.vacuum_factor_extension import (
    build_vacuum_factor_extension_plan,
)
from pg_case_factory.vacuum_factor_loop import (
    build_vacuum_factor_loop_plan,
)
from pg_case_factory.vacuum_factor_render import (
    generate_vacuum_factor_programs,
    render_vacuum_factor_case,
)
from pg_case_factory.validate_vacuum import (
    VacuumFactorProgramValidation,
    remove_primary_semantic_locus_but_keep_comments,
    validate_vacuum_factor_programs,
)

ROOT = Path(__file__).resolve().parents[1]


class VacuumFactorValidateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = build_vacuum_factor_loop_plan(ROOT)
        cls.extension = build_vacuum_factor_extension_plan(ROOT)
        cls.tmp = Path(tempfile.mkdtemp(prefix="vacuum_validate_"))
        generate_vacuum_factor_programs(
            cls.baseline, cls.extension, cls.tmp
        )
        cls.programs = {}
        for f in sorted(cls.tmp.glob("*.sql")):
            cls.programs[f.name] = f.read_text()

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_validate_module_is_named_validate_vacuum(self) -> None:
        import pg_case_factory.validate_vacuum as mod

        self.assertEqual(mod.__name__, "pg_case_factory.validate_vacuum")
        self.assertTrue(
            mod.__file__.endswith("validate_vacuum.py"),
            mod.__file__,
        )

    def test_validation_passes_for_all_1415_files(self) -> None:
        result = validate_vacuum_factor_programs(
            self.baseline, self.extension, self.programs, ROOT
        )
        self.assertIsInstance(
            result, VacuumFactorProgramValidation
        )
        self.assertTrue(result.passed)
        self.assertEqual(47, result.baseline_case_count)
        self.assertEqual(1368, result.extension_case_count)
        self.assertEqual(1415, result.sql_file_count)

    def test_no_missing_duplicate_or_unknown_cases(self) -> None:
        result = validate_vacuum_factor_programs(
            self.baseline, self.extension, self.programs, ROOT
        )
        self.assertEqual(0, result.missing_case_count)
        self.assertEqual(0, result.duplicate_case_count)
        self.assertEqual(0, result.unknown_obligation_count)

    def test_no_semantic_witness_mismatches(self) -> None:
        result = validate_vacuum_factor_programs(
            self.baseline, self.extension, self.programs, ROOT
        )
        self.assertEqual(0, result.semantic_witness_mismatch_count)

    def test_no_coverage_gaps(self) -> None:
        result = validate_vacuum_factor_programs(
            self.baseline, self.extension, self.programs, ROOT
        )
        self.assertEqual(0, result.coverage_gap_count)

    def test_records_cover_all_cases(self) -> None:
        result = validate_vacuum_factor_programs(
            self.baseline, self.extension, self.programs, ROOT
        )
        self.assertEqual(1415, len(result.records))

    def test_sha256_dictionary_is_complete(self) -> None:
        result = validate_vacuum_factor_programs(
            self.baseline, self.extension, self.programs, ROOT
        )
        self.assertEqual(1415, len(result.sql_sha256))
        for filename, sha in result.sql_sha256.items():
            self.assertEqual(64, len(sha))

    def test_mutation_helper_replaces_target(self) -> None:
        case = self.baseline.cases[0]
        sql = render_vacuum_factor_case(case, ROOT)
        mutated = (
            remove_primary_semantic_locus_but_keep_comments(sql, case)
        )
        self.assertIn("removed_primary_semantic_locus", mutated)
        self.assertIn(f"-- case_id: {case.case_id}", mutated)

    def test_mutation_helper_rejects_missing_case_trace(self) -> None:
        case = self.baseline.cases[0]
        sql = "SELECT 1;"
        with self.assertRaises(ValueError):
            remove_primary_semantic_locus_but_keep_comments(sql, case)

    def test_validation_fails_on_tampered_file(self) -> None:
        case = self.baseline.cases[0]
        sql = render_vacuum_factor_case(case, ROOT)
        tampered = sql.replace("VACUUM", "VACUUMBOGUS", 1)
        programs = dict(self.programs)
        programs[case.sql_filename] = tampered
        result = validate_vacuum_factor_programs(
            self.baseline, self.extension, programs, ROOT
        )
        self.assertFalse(result.passed)
        self.assertGreater(result.semantic_witness_mismatch_count, 0)

    def test_selected_case_ids_validates_subset(self) -> None:
        selected = {"VACUUM00001", "VACUUM00002"}
        result = validate_vacuum_factor_programs(
            self.baseline,
            self.extension,
            self.programs,
            ROOT,
            selected_case_ids=selected,
        )
        self.assertTrue(result.passed)
        self.assertEqual(2, len(result.records))


if __name__ == "__main__":
    unittest.main()
