"""Tests for create_table factor validate module."""

import tempfile
import unittest
from pathlib import Path

from src.pg_case_factory.create_table_factor_extension import (
    build_create_table_factor_extension_plan,
)
from src.pg_case_factory.create_table_factor_loop import (
    build_create_table_factor_loop_plan,
)
from src.pg_case_factory.create_table_factor_render import (
    generate_create_table_factor_programs,
)
from src.pg_case_factory.create_table_factor_validate import (
    remove_primary_semantic_locus_but_keep_comments,
    validate_create_table_factor_programs,
)

_REPO = Path(__file__).resolve().parents[1]


class TestCreateTableFactorValidate(unittest.TestCase):
    def setUp(self) -> None:
        self.baseline = build_create_table_factor_loop_plan(_REPO)
        self.extension = build_create_table_factor_extension_plan(_REPO)
        self.out = Path(tempfile.mkdtemp())
        generate_create_table_factor_programs(
            self.baseline, self.extension, self.out
        )
        self.programs = {
            f.name: f.read_text()
            for f in self.out.iterdir()
            if f.suffix == ".sql"
        }

    def test_validation_passes_for_all_files(self) -> None:
        report = validate_create_table_factor_programs(
            self.baseline, self.extension, self.programs, _REPO
        )
        self.assertTrue(report.passed, msg="; ".join(report.issues))
        self.assertEqual(0, report.missing_case_count)
        self.assertEqual(0, report.duplicate_case_count)
        self.assertEqual(0, report.unknown_obligation_count)
        self.assertEqual(0, report.semantic_witness_mismatch_count)
        self.assertEqual(0, report.coverage_gap_count)

    def test_baseline_case_count(self) -> None:
        report = validate_create_table_factor_programs(
            self.baseline, self.extension, self.programs, _REPO
        )
        self.assertEqual(188, report.baseline_case_count)
        self.assertEqual(5760, report.extension_case_count)
        self.assertEqual(5948, report.sql_file_count)

    def test_records_cover_all_cases(self) -> None:
        report = validate_create_table_factor_programs(
            self.baseline, self.extension, self.programs, _REPO
        )
        self.assertEqual(5948, len(report.records))

    def test_sha256_dictionary_complete(self) -> None:
        report = validate_create_table_factor_programs(
            self.baseline, self.extension, self.programs, _REPO
        )
        self.assertEqual(5948, len(report.sql_sha256))

    def test_validation_fails_on_tampered_file(self) -> None:
        filename = "CREATETABLE00001.sql"
        original = self.programs[filename]
        tampered = original.replace(
            "createtable_00001_col", "tampered_col"
        )
        self.programs[filename] = tampered
        report = validate_create_table_factor_programs(
            self.baseline, self.extension, self.programs, _REPO
        )
        self.assertFalse(report.passed)
        self.assertGreater(report.semantic_witness_mismatch_count, 0)

    def test_selected_case_ids_validates_subset(self) -> None:
        selected = {"CREATETABLE00001", "CREATETABLE00189"}
        report = validate_create_table_factor_programs(
            self.baseline, self.extension, self.programs, _REPO,
            selected_case_ids=selected,
        )
        self.assertTrue(report.passed)
        self.assertEqual(2, len(report.records))

    def test_mutation_helper(self) -> None:
        filename = "CREATETABLE00001.sql"
        sql = self.programs[filename]
        case = self.baseline.cases[0]
        mutated = remove_primary_semantic_locus_but_keep_comments(
            sql, case
        )
        report = validate_create_table_factor_programs(
            self.baseline, self.extension,
            {**self.programs, filename: mutated},
            _REPO,
        )
        self.assertFalse(report.passed)
        self.assertGreater(report.semantic_witness_mismatch_count, 0)

    def test_to_dict_structure(self) -> None:
        report = validate_create_table_factor_programs(
            self.baseline, self.extension, self.programs, _REPO
        )
        d = report.to_dict()
        self.assertTrue(d["passed"])
        self.assertEqual(1, d["schema_version"])
        self.assertEqual(
            "create_table_actual_factor_witness_report", d["kind"]
        )


if __name__ == "__main__":
    unittest.main()
