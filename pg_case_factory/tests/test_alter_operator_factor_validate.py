"""Byte-witness and conservation validation tests for ALTER OPERATOR."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pg_case_factory.alter_operator_factor_extension import (
    build_alter_operator_factor_extension_plan,
)
from pg_case_factory.alter_operator_factor_loop import (
    build_alter_operator_factor_loop_plan,
)
from pg_case_factory.alter_operator_factor_render import (
    generate_alter_operator_factor_programs,
    render_alter_operator_factor_case,
)
from pg_case_factory.alter_operator_factor_validate import (
    AlterOperatorFactorProgramValidation,
    remove_primary_semantic_locus_but_keep_comments,
    validate_alter_operator_factor_programs,
)

ROOT = Path(__file__).resolve().parents[1]


class AlterOperatorFactorValidateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.baseline = build_alter_operator_factor_loop_plan(ROOT)
        self.extension = build_alter_operator_factor_extension_plan(ROOT)
        self.tmp = tempfile.mkdtemp()
        self.out_dir = Path(self.tmp)
        generate_alter_operator_factor_programs(
            self.baseline, self.extension, self.out_dir
        )
        self.programs = {
            f.name: f.read_text(encoding="utf-8")
            for f in sorted(self.out_dir.glob("*.sql"))
        }

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_validation_passes(self) -> None:
        result = validate_alter_operator_factor_programs(
            self.baseline, self.extension, self.programs, ROOT
        )
        self.assertTrue(
            result.passed, msg=f"issues: {result.issues[:5]}"
        )
        self.assertEqual(result.baseline_case_count, 63)
        self.assertEqual(result.extension_case_count, 2292)
        self.assertEqual(result.sql_file_count, 2355)

    def test_no_coverage_gaps(self) -> None:
        result = validate_alter_operator_factor_programs(
            self.baseline, self.extension, self.programs, ROOT
        )
        self.assertEqual(result.coverage_gaps, ())

    def test_no_missing_or_duplicate_cases(self) -> None:
        result = validate_alter_operator_factor_programs(
            self.baseline, self.extension, self.programs, ROOT
        )
        self.assertEqual(result.missing_case_ids, ())
        self.assertEqual(result.duplicate_case_ids, ())
        self.assertEqual(result.unknown_obligation_ids, ())

    def test_no_semantic_witness_mismatches(self) -> None:
        result = validate_alter_operator_factor_programs(
            self.baseline, self.extension, self.programs, ROOT
        )
        self.assertEqual(result.semantic_witness_mismatch_case_ids, ())

    def test_validation_to_dict_has_required_fields(self) -> None:
        result = validate_alter_operator_factor_programs(
            self.baseline, self.extension, self.programs, ROOT
        )
        payload = result.to_dict()
        self.assertEqual(payload["kind"], "alter_operator_actual_factor_witness_report")
        self.assertEqual(payload["baseline_case_count"], 63)
        self.assertEqual(payload["extension_case_count"], 2292)
        self.assertTrue(payload["sql_sha256"])

    def test_selected_subset_validation(self) -> None:
        ids = {self.baseline.cases[0].case_id, self.baseline.cases[5].case_id}
        subset = {
            f: sql
            for f, sql in self.programs.items()
            if f.startswith("ALTEROPERATOR0000")
            or f.startswith("ALTEROPERATOR0006")
        }
        result = validate_alter_operator_factor_programs(
            self.baseline, self.extension, subset, ROOT, selected_case_ids=ids
        )
        self.assertTrue(result.passed, msg=f"issues: {result.issues[:5]}")

    def test_missing_program_detected(self) -> None:
        filename = self.baseline.cases[0].sql_filename
        reduced = {k: v for k, v in self.programs.items() if k != filename}
        result = validate_alter_operator_factor_programs(
            self.baseline, self.extension, reduced, ROOT
        )
        self.assertFalse(result.passed)

    def test_tampered_program_detected(self) -> None:
        filename = self.baseline.cases[0].sql_filename
        tampered = dict(self.programs)
        tampered[filename] = tampered[filename].replace(
            "ALTER OPERATOR", "SELECT true AS noop"
        )
        result = validate_alter_operator_factor_programs(
            self.baseline, self.extension, tampered, ROOT
        )
        self.assertFalse(result.passed)

    def test_remove_primary_locus_helper(self) -> None:
        case = self.baseline.cases[0]
        sql = render_alter_operator_factor_case(case)
        self.assertIn(f"-- case_id: {case.case_id}", sql)
        mutated = remove_primary_semantic_locus_but_keep_comments(sql, case)
        self.assertIn("removed_primary_semantic_locus", mutated)


if __name__ == "__main__":
    unittest.main()
