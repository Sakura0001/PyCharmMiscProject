"""Tests for create_statistics factor_validate byte-level witness."""

import tempfile
import unittest
from pathlib import Path

from src.pg_case_factory.create_statistics_factor_extension import (
    build_create_statistics_factor_extension_plan,
)
from src.pg_case_factory.create_statistics_factor_loop import (
    build_create_statistics_factor_loop_plan,
)
from src.pg_case_factory.create_statistics_factor_render import (
    generate_create_statistics_factor_programs,
    render_create_statistics_factor_case,
)
from src.pg_case_factory.create_statistics_factor_validate import (
    remove_primary_semantic_locus_but_keep_comments,
    validate_create_statistics_factor_programs,
)

_REPO = Path(__file__).resolve().parents[1]


class TestCreateStatisticsFactorValidate(unittest.TestCase):
    def setUp(self) -> None:
        self.baseline = build_create_statistics_factor_loop_plan(_REPO)
        self.extension = build_create_statistics_factor_extension_plan(_REPO)
        self.out = Path(tempfile.mkdtemp())
        generate_create_statistics_factor_programs(
            self.baseline, self.extension, self.out
        )
        self.programs = {
            f.name: f.read_text()
            for f in sorted(self.out.iterdir())
            if f.suffix == ".sql"
        }

    def test_passes_on_canonical_programs(self) -> None:
        r = validate_create_statistics_factor_programs(
            self.baseline, self.extension, self.programs, _REPO
        )
        self.assertTrue(r.passed, msg=r.issues[:5])

    def test_byte_counts(self) -> None:
        r = validate_create_statistics_factor_programs(
            self.baseline, self.extension, self.programs, _REPO
        )
        self.assertEqual(56, r.baseline_case_count)
        self.assertEqual(2584, r.extension_case_count)
        self.assertEqual(0, r.missing_case_count)
        self.assertEqual(0, r.duplicate_case_count)
        self.assertEqual(0, r.unknown_obligation_count)
        self.assertEqual(0, r.semantic_witness_mismatch_count)
        self.assertEqual(0, r.coverage_gap_count)

    def test_missing_program_detected(self) -> None:
        del self.programs["CREATESTATISTICS00001.sql"]
        r = validate_create_statistics_factor_programs(
            self.baseline, self.extension, self.programs, _REPO
        )
        self.assertFalse(r.passed)
        self.assertGreater(r.missing_case_count, 0)

    def test_drift_detected(self) -> None:
        case = self.baseline.cases[0]
        sql = render_create_statistics_factor_case(case, _REPO)
        mutated = remove_primary_semantic_locus_but_keep_comments(
            sql, case
        )
        self.programs[case.sql_filename] = mutated
        r = validate_create_statistics_factor_programs(
            self.baseline, self.extension, self.programs, _REPO
        )
        self.assertFalse(r.passed)
        self.assertGreater(r.semantic_witness_mismatch_count, 0)

    def test_selected_subset(self) -> None:
        ids = {"CREATESTATISTICS00001", "CREATESTATISTICS00056"}
        r = validate_create_statistics_factor_programs(
            self.baseline, self.extension, self.programs, _REPO,
            selected_case_ids=ids,
        )
        self.assertTrue(r.passed, msg=r.issues[:5])

    def test_to_dict_structure(self) -> None:
        r = validate_create_statistics_factor_programs(
            self.baseline, self.extension, self.programs, _REPO
        )
        d = r.to_dict()
        self.assertEqual("create_statistics_actual_factor_witness_report", d["kind"])
        self.assertTrue(d["passed"])


if __name__ == "__main__":
    unittest.main()
