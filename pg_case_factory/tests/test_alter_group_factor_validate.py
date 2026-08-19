"""Tests for the ALTER GROUP factor-suite byte-level validator.

The validator re-renders the canonical bytes for every case (baseline +
extension) and compares them exactly against the on-disk SQL, enforces
baseline conservation (missing/duplicate/unknown == 0), the extension
derivation gate, the no-placeholder rule, and primary-target cardinality
== 1.  It fails closed on any drift.
"""

from __future__ import annotations

import copy
from pathlib import Path
import unittest

from pg_case_factory.alter_group_factor_extension import (
    build_alter_group_factor_extension_plan,
)
from pg_case_factory.alter_group_factor_loop import (
    build_alter_group_factor_loop_plan,
)
from pg_case_factory.alter_group_factor_render import (
    generate_alter_group_factor_programs,
    render_alter_group_factor_case,
)
from pg_case_factory.alter_group_factor_validate import (
    AlterGroupFactorProgramValidation,
    validate_alter_group_factor_programs,
)


ROOT = Path(__file__).resolve().parents[1]
_OUT = ROOT / "artifacts" / "regress" / "by-factor" / "ddl" / "group" / "alter_group"


def _build_programs() -> dict[str, str]:
    baseline = build_alter_group_factor_loop_plan(ROOT)
    extension = build_alter_group_factor_extension_plan(ROOT)
    generate_alter_group_factor_programs(baseline, extension, _OUT)
    programs: dict[str, str] = {}
    for path in _OUT.glob("ALTERGROUP*.sql"):
        programs[path.name] = path.read_text(encoding="utf-8")
    return programs


class AlterGroupFactorValidateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = build_alter_group_factor_loop_plan(ROOT)
        cls.extension = build_alter_group_factor_extension_plan(ROOT)
        cls.programs = _build_programs()

    def _selected(self, n: int = 4) -> set[str]:
        ids = {c.case_id for c in self.baseline.cases[:2]}
        ids |= {c.case_id for c in self.extension.cases[: n - 2]}
        return ids

    def _cases_for(self, selected: set[str] | None):
        cases = list(self.baseline.cases) + list(self.extension.cases)
        if selected is None:
            return cases
        return [c for c in cases if c.case_id in selected]

    def test_full_suite_passes_with_zero_drift(self) -> None:
        report = validate_alter_group_factor_programs(
            self.baseline, self.extension, self.programs, ROOT
        )
        self.assertIsInstance(report, AlterGroupFactorProgramValidation)
        self.assertTrue(report.passed, report.issues[:5])
        self.assertEqual(0, report.missing_case_count)
        self.assertEqual(0, report.duplicate_case_count)
        self.assertEqual(0, report.semantic_witness_mismatch_count)
        self.assertEqual(0, report.unknown_obligation_count)
        self.assertEqual(0, report.coverage_gap_count)
        self.assertEqual(
            len(self.baseline.cases) + len(self.extension.cases),
            report.sql_file_count,
        )

    def test_byte_mutation_is_detected(self) -> None:
        selected = self._selected(4)
        cases = self._cases_for(selected)
        mutated = dict(self.programs)
        target_file = cases[0].sql_filename
        mutated[target_file] = mutated[target_file].replace(
            "ALTER GROUP", "ALTER ROLE", 1
        )
        report = validate_alter_group_factor_programs(
            self.baseline, self.extension, mutated, ROOT,
            selected_case_ids=selected,
        )
        self.assertFalse(report.passed)
        self.assertGreater(report.semantic_witness_mismatch_count, 0)

    def test_missing_program_is_detected(self) -> None:
        selected = self._selected(4)
        cases = self._cases_for(selected)
        mutated = dict(self.programs)
        del mutated[cases[1].sql_filename]
        report = validate_alter_group_factor_programs(
            self.baseline, self.extension, mutated, ROOT,
            selected_case_ids=selected,
        )
        self.assertFalse(report.passed)
        self.assertGreater(report.missing_case_count, 0)

    def test_placeholder_leakage_fails_closed(self) -> None:
        selected = self._selected(4)
        cases = self._cases_for(selected)
        mutated = dict(self.programs)
        target_file = cases[0].sql_filename
        mutated[target_file] = mutated[target_file].replace(
            "ALTER GROUP", "ALTER GROUP {placeholder}", 1
        )
        report = validate_alter_group_factor_programs(
            self.baseline, self.extension, mutated, ROOT,
            selected_case_ids=selected,
        )
        self.assertFalse(report.passed)

    def test_primary_fence_cardinality_is_enforced(self) -> None:
        selected = self._selected(4)
        cases = self._cases_for(selected)
        mutated = dict(self.programs)
        target_file = cases[0].sql_filename
        # remove the begin fence so the primary region is unbounded
        mutated[target_file] = mutated[target_file].replace(
            "-- primary-target-begin\n", "", 1
        )
        report = validate_alter_group_factor_programs(
            self.baseline, self.extension, mutated, ROOT,
            selected_case_ids=selected,
        )
        self.assertFalse(report.passed)

    def test_coverage_gates_every_required_factor_value(self) -> None:
        report = validate_alter_group_factor_programs(
            self.baseline, self.extension, self.programs, ROOT
        )
        self.assertEqual(0, report.coverage_gap_count)

    def test_extensions_carry_derivation_records(self) -> None:
        for case in self.extension.cases[:20]:
            self.assertTrue(case.is_extension)
            self.assertTrue(case.derivation_id)
            self.assertTrue(case.derived_from_combination_group)
            self.assertTrue(case.derivation_reason)

    def test_re_render_matches_disk_bytes_exactly(self) -> None:
        for case in list(self.baseline.cases[:3]) + list(
            self.extension.cases[:3]
        ):
            expected = render_alter_group_factor_case(case, ROOT)
            actual = self.programs[case.sql_filename]
            self.assertEqual(expected, actual, case.case_id)


if __name__ == "__main__":
    unittest.main()
