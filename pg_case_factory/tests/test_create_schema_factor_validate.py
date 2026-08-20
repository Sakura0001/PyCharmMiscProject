from pathlib import Path
import shutil
import tempfile
import unittest

from pg_case_factory.create_schema_factor_extension import (
    build_create_schema_factor_extension_plan,
)
from pg_case_factory.create_schema_factor_loop import (
    build_create_schema_factor_loop_plan,
)
from pg_case_factory.create_schema_factor_render import (
    generate_create_schema_factor_programs,
)
from pg_case_factory.create_schema_factor_validate import (
    CreateSchemaFactorProgramValidation,
    validate_create_schema_factor_programs,
)

ROOT = Path(__file__).resolve().parents[1]


class CreateSchemaFactorValidateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.mkdtemp(
            prefix="cschema_validate_"
        )
        out = Path(cls.tmp)
        bp = build_create_schema_factor_loop_plan(ROOT)
        ep = build_create_schema_factor_extension_plan(ROOT)
        cls.baseline_plan = bp
        cls.extension_plan = ep
        cls.count = generate_create_schema_factor_programs(
            bp, ep, out
        )
        cls.programs = {
            f.name: f.read_text(encoding="utf-8")
            for f in sorted(out.glob("*.sql"))
        }

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_validation_passes_for_all_files(self) -> None:
        result = validate_create_schema_factor_programs(
            self.baseline_plan,
            self.extension_plan,
            self.programs,
            ROOT,
        )
        self.assertIsInstance(
            result, CreateSchemaFactorProgramValidation
        )
        self.assertEqual(62, result.baseline_case_count)
        self.assertEqual(10530, result.extension_case_count)
        self.assertEqual(10592, result.sql_file_count)

    def test_no_missing_duplicate_or_unknown_cases(self) -> None:
        result = validate_create_schema_factor_programs(
            self.baseline_plan,
            self.extension_plan,
            self.programs,
            ROOT,
        )
        self.assertTrue(
            result.passed,
            msg="; ".join(result.issues),
        )
        self.assertEqual(0, len(result.missing_case_ids))
        self.assertEqual(0, len(result.duplicate_case_ids))
        self.assertEqual(0, len(result.unknown_obligation_ids))

    def test_no_semantic_witness_mismatches(self) -> None:
        result = validate_create_schema_factor_programs(
            self.baseline_plan,
            self.extension_plan,
            self.programs,
            ROOT,
        )
        self.assertEqual(
            0,
            len(result.semantic_witness_mismatch_case_ids),
        )

    def test_no_coverage_gaps(self) -> None:
        result = validate_create_schema_factor_programs(
            self.baseline_plan,
            self.extension_plan,
            self.programs,
            ROOT,
        )
        self.assertEqual(0, len(result.coverage_gaps))

    def test_records_cover_all_cases(self) -> None:
        result = validate_create_schema_factor_programs(
            self.baseline_plan,
            self.extension_plan,
            self.programs,
            ROOT,
        )
        self.assertEqual(10592, len(result.records))

    def test_to_dict_structure(self) -> None:
        result = validate_create_schema_factor_programs(
            self.baseline_plan,
            self.extension_plan,
            self.programs,
            ROOT,
        )
        d = result.to_dict()
        self.assertEqual(
            "create_schema_factor_program_validation",
            d["kind"],
        )
        self.assertTrue(d["passed"])
        self.assertEqual(62, d["baseline_case_count"])
        self.assertEqual(10530, d["extension_case_count"])


if __name__ == "__main__":
    unittest.main()
