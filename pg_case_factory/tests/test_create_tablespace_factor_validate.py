from pathlib import Path
import shutil
import tempfile
import unittest

from pg_case_factory.create_tablespace_factor_extension import (
    build_create_tablespace_factor_extension_plan,
)
from pg_case_factory.create_tablespace_factor_loop import (
    build_create_tablespace_factor_loop_plan,
)
from pg_case_factory.create_tablespace_factor_render import (
    generate_create_tablespace_factor_programs,
    render_create_tablespace_factor_case,
)
from pg_case_factory.create_tablespace_factor_validate import (
    CreateTablespaceFactorProgramValidation,
    remove_primary_semantic_locus_but_keep_comments,
    validate_create_tablespace_factor_programs,
)

ROOT = Path(__file__).resolve().parents[1]


class CreateTablespaceFactorValidateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = build_create_tablespace_factor_loop_plan(ROOT)
        cls.extension = build_create_tablespace_factor_extension_plan(
            ROOT
        )
        cls.tmp = Path(tempfile.mkdtemp(prefix="ctsp_validate_"))
        generate_create_tablespace_factor_programs(
            cls.baseline, cls.extension, cls.tmp
        )
        cls.programs = {}
        for f in sorted(cls.tmp.glob("*.sql")):
            cls.programs[f.name] = f.read_text()

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_validation_passes_for_all_4567_files(self) -> None:
        result = validate_create_tablespace_factor_programs(
            self.baseline, self.extension, self.programs, ROOT
        )
        self.assertIsInstance(
            result, CreateTablespaceFactorProgramValidation
        )
        self.assertTrue(result.passed)
        self.assertEqual(67, result.baseline_case_count)
        self.assertEqual(4500, result.extension_case_count)
        self.assertEqual(4567, result.sql_file_count)

    def test_no_missing_duplicate_or_unknown_cases(self) -> None:
        result = validate_create_tablespace_factor_programs(
            self.baseline, self.extension, self.programs, ROOT
        )
        self.assertEqual(0, result.missing_case_count)
        self.assertEqual(0, result.duplicate_case_count)
        self.assertEqual(0, result.unknown_obligation_count)
        self.assertEqual(
            0, result.semantic_witness_mismatch_count
        )

    def test_no_coverage_gaps(self) -> None:
        result = validate_create_tablespace_factor_programs(
            self.baseline, self.extension, self.programs, ROOT
        )
        self.assertEqual(0, result.coverage_gap_count)

    def test_to_dict_has_expected_schema(self) -> None:
        result = validate_create_tablespace_factor_programs(
            self.baseline, self.extension, self.programs, ROOT
        )
        d = result.to_dict()
        self.assertEqual(1, d["schema_version"])
        self.assertEqual(
            "create_tablespace_actual_factor_witness_report",
            d["kind"],
        )
        self.assertTrue(d["passed"])
        self.assertEqual(4567, d["sql_file_count"])

    def test_selected_case_ids_validation(self) -> None:
        result = validate_create_tablespace_factor_programs(
            self.baseline,
            self.extension,
            self.programs,
            ROOT,
            selected_case_ids={"CREATETABLESPACE00001"},
        )
        self.assertTrue(result.passed)
        self.assertEqual(1, len(result.records))

    def test_tampered_program_fails_validation(self) -> None:
        tampered = dict(self.programs)
        case = self.baseline.cases[0]
        original = tampered[case.sql_filename]
        tampered[case.sql_filename] = original.replace(
            "CREATE TABLESPACE", "REMOVED_TARGET", 1
        )
        result = validate_create_tablespace_factor_programs(
            self.baseline, self.extension, tampered, ROOT
        )
        self.assertFalse(result.passed)

    def test_missing_program_fails_validation(self) -> None:
        partial = dict(self.programs)
        del partial["CREATETABLESPACE00001.sql"]
        result = validate_create_tablespace_factor_programs(
            self.baseline, self.extension, partial, ROOT
        )
        self.assertFalse(result.passed)

    def test_remove_primary_locus_helper(self) -> None:
        case = self.baseline.cases[0]
        sql = render_create_tablespace_factor_case(case, ROOT)
        modified = (
            remove_primary_semantic_locus_but_keep_comments(
                sql, case
            )
        )
        self.assertIn("removed_primary_semantic_locus", modified)
        result = validate_create_tablespace_factor_programs(
            self.baseline,
            self.extension,
            {case.sql_filename: modified},
            ROOT,
            selected_case_ids={case.case_id},
        )
        self.assertFalse(result.passed)


if __name__ == "__main__":
    unittest.main()
