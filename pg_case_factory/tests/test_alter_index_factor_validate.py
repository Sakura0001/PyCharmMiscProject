"""Tests for the actual-byte ALTER INDEX factor-loop coverage validator.

The validator re-renders the canonical bytes for every case (frozen 772-case
baseline + 6,786-case bounded extension = 7,558 programs) and compares them
exactly against the on-disk SQL.  It fails closed on byte drift, header
mismatch, primary-target cardinality != 1, placeholder leakage,
missing/duplicate/unknown cases, or an extension case lacking a derivation
record, and it gates that every required factor value is still witnessed
across ``baseline ∪ extension`` (conservation).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pg_case_factory.alter_index_factor_extension import (
    build_alter_index_factor_extension_plan,
)
from pg_case_factory.alter_index_factor_loop import (
    build_alter_index_factor_loop_plan,
)
from pg_case_factory.alter_index_factor_render import (
    generate_alter_index_factor_programs,
    render_alter_index_factor_case,
)
from pg_case_factory.alter_index_factor_validate import (
    AlterIndexFactorProgramValidation,
    remove_primary_semantic_locus_but_keep_comments,
    validate_alter_index_factor_programs,
)


ROOT = Path(__file__).resolve().parents[1]

_BASELINE_COUNT = 772
_EXTENSION_COUNT = 6786
_TOTAL_COUNT = _BASELINE_COUNT + _EXTENSION_COUNT  # 7558


class AlterIndexFactorValidateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.baseline = build_alter_index_factor_loop_plan(ROOT)
        self.extension = build_alter_index_factor_extension_plan(ROOT)

    def _generate_and_validate(self) -> AlterIndexFactorProgramValidation:
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            generate_alter_index_factor_programs(
                self.baseline, self.extension, out
            )
            programs = {
                path.name: path.read_bytes()
                for path in out.iterdir()
                if path.suffix == ".sql"
            }
            return validate_alter_index_factor_programs(
                self.baseline, self.extension, programs, ROOT
            )

    def test_full_two_plan_validation_passes(self) -> None:
        report = self._generate_and_validate()
        self.assertTrue(report.passed, report.issues)
        self.assertEqual(_BASELINE_COUNT, report.baseline_case_count)
        self.assertEqual(_EXTENSION_COUNT, report.extension_case_count)
        self.assertEqual(_TOTAL_COUNT, report.sql_file_count)

    def test_conservation_no_coverage_gaps(self) -> None:
        # Every required factor value must still be witnessed across the
        # baseline ∪ extension union (conservation).
        report = self._generate_and_validate()
        self.assertEqual(0, report.coverage_gap_count)
        self.assertEqual((), report.coverage_gaps)

    def test_no_missing_duplicate_or_unknown_cases(self) -> None:
        report = self._generate_and_validate()
        self.assertEqual(0, report.missing_case_count)
        self.assertEqual(0, report.duplicate_case_count)
        self.assertEqual(0, report.unknown_obligation_count)
        self.assertEqual(
            0, report.semantic_witness_mismatch_count
        )

    def test_sql_sha256_index_covers_all_programs(self) -> None:
        report = self._generate_and_validate()
        self.assertEqual(_TOTAL_COUNT, len(report.sql_sha256))
        for digest in report.sql_sha256.values():
            self.assertEqual(64, len(digest))

    def test_byte_drift_is_detected(self) -> None:
        # Mutating the primary target while keeping trace comments must
        # strip credit (the byte comparison + cardinality gate fire).
        case = self.extension.cases[0]
        sql = render_alter_index_factor_case(case, ROOT)
        mutated = remove_primary_semantic_locus_but_keep_comments(sql, case)
        programs = {case.sql_filename: mutated.encode("utf-8")}
        report = validate_alter_index_factor_programs(
            self.baseline,
            self.extension,
            programs,
            ROOT,
            selected_case_ids={case.case_id},
        )
        self.assertFalse(report.passed)
        self.assertEqual(1, report.semantic_witness_mismatch_count)

    def test_missing_program_is_detected(self) -> None:
        report = validate_alter_index_factor_programs(
            self.baseline, self.extension, {}, ROOT
        )
        self.assertFalse(report.passed)
        self.assertEqual(_TOTAL_COUNT, report.missing_case_count)


if __name__ == "__main__":
    unittest.main()
