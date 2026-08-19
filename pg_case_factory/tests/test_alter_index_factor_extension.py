"""Tests for the bounded ALTER INDEX post-coverage extension expander.

The marginal factor-value-loop (``alter_index_factor_loop.py``) is the frozen
87-case baseline (GRM 21 + SFV 66, 73 success + 14 expected_failure).
This module's expander adds the bounded post-coverage extension phase:
cross-factor combinations of the positive (success-path) T1-T4 behaviour
axes across the nine ALTER INDEX branches, with ``verification_mode`` and
``cleanup_mode`` crossed so every declared T6 value is exercised.  Each
extension case carries a derivation record and is marked ``is_extension =
True``; it never replaces a required-baseline obligation.

The extension crosses only the success-path values of each behaviour axis
(failure / no-op markers stay one-per-value in the marginal baseline), so
attribution stays clean and every extension outcome is ``success``.  The
shared evaluator's storage-validity condition is resolved correctly because
the extension supplies the method-valid concrete storage parameter the
grammar's shape axes abstract.
"""

from __future__ import annotations

import unittest
from collections import Counter
from pathlib import Path

from pg_case_factory.alter_index_factor_extension import (
    AlterIndexFactorExtensionCase,
    AlterIndexFactorExtensionError,
    AlterIndexFactorExtensionPlan,
    build_alter_index_factor_extension_plan,
)
from pg_case_factory.alter_index_factor_loop import (
    build_alter_index_factor_loop_plan,
)


ROOT = Path(__file__).resolve().parents[1]

_BASELINE_COUNT = 87
_EXTENSION_COUNT = 6786
_TOTAL_COUNT = _BASELINE_COUNT + _EXTENSION_COUNT  # 6873
# Frozen to the empirical expander output (positive-axis x T6 cross, no
# cap truncation, all success-path outcomes).
_EXTENSION_SHA256 = (
    "aff7acd9af139d32c1b3de220145ef2e3903209d2ce54754af0b558430f23c37"
)
_EXPECTED_ACTIONS = frozenset(
    {
        "rename",
        "set_tablespace",
        "set_storage",
        "reset_storage",
        "set_statistics",
        "depends_on_extension",
        "no_depends_on_extension",
        "attach_partition",
        "all_in_tablespace",
    }
)


class AlterIndexFactorExtensionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_alter_index_factor_extension_plan(ROOT)

    def test_plan_type_and_case_kinds(self) -> None:
        self.assertIsInstance(self.plan, AlterIndexFactorExtensionPlan)
        self.assertTrue(self.plan.cases)
        for case in self.plan.cases:
            self.assertIsInstance(case, AlterIndexFactorExtensionCase)
            self.assertTrue(case.is_extension)

    def test_frozen_extension_count(self) -> None:
        self.assertEqual(_EXTENSION_COUNT, len(self.plan.cases))

    def test_no_cap_truncation(self) -> None:
        self.assertEqual(self.plan.raw_combination_count, len(self.plan.cases))
        self.assertEqual(0, self.plan.dropped_count)

    def test_extension_multiset_sha256_is_frozen(self) -> None:
        self.assertEqual(_EXTENSION_SHA256, self.plan.extension_multiset_sha256)

    def test_ordinals_continue_after_baseline(self) -> None:
        ordinals = [case.ordinal for case in self.plan.cases]
        self.assertEqual(_BASELINE_COUNT + 1, ordinals[0])
        self.assertEqual(_TOTAL_COUNT, ordinals[-1])
        self.assertEqual(
            list(range(_BASELINE_COUNT + 1, _TOTAL_COUNT + 1)), ordinals
        )

    def test_case_ids_are_five_digit_alterindex(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(case.case_id.startswith("ALTERINDEX"))
            self.assertEqual(case.sql_filename, f"{case.case_id}.sql")
            self.assertEqual(
                case.object_prefix, f"alterindex_{case.ordinal:05d}_"
            )

    def test_derivation_ids_are_well_formed(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(case.derivation_id.startswith("AI-EXT|"))
            parts = case.derivation_id.split("|")
            self.assertEqual(5, len(parts))
            self.assertEqual(f"AI-EXT|{case.ordinal:05d}", f"{parts[0]}|{parts[1]}")
            self.assertEqual(case.consumer_action_id, parts[2])
            self.assertIn(parts[3], {"catalog_query", "meta_command", "parameter_check"})
            self.assertIn(
                parts[4], {"drop_index", "reset_parameter", "detach_partition"}
            )

    def test_all_outcomes_are_success_path(self) -> None:
        # The extension crosses only success-path values, so every outcome is
        # success with the neutral sqlstate and no failure reason.
        self.assertEqual(
            {"success": _EXTENSION_COUNT},
            Counter(c.outcome for c in self.plan.cases),
        )
        for case in self.plan.cases:
            self.assertEqual("00000", case.expected_sqlstate)
            self.assertIsNone(case.expected_failure_reason)

    def test_all_nine_branches_are_covered(self) -> None:
        self.assertEqual(
            _EXPECTED_ACTIONS,
            {c.consumer_action_id for c in self.plan.cases},
        )

    def test_factor_assignments_include_storage_parameter_for_storage_branches(
        self,
    ) -> None:
        # The storage branches carry the method-valid concrete storage
        # parameter so the shared evaluator resolves the positive cross.
        for case in self.plan.cases:
            if case.consumer_action_id in {"set_storage", "reset_storage"}:
                keys = {k for k, _ in case.factor_assignment}
                self.assertIn("storage_parameter", keys)

    def test_derived_combinations_yaml_is_emitted(self) -> None:
        self.assertTrue(self.plan.derived_combinations_yaml.strip())
        self.assertIn("AI-EXT|", self.plan.derived_combinations_yaml)

    def test_baseline_plan_is_untouched_by_extension_build(self) -> None:
        # The extension must not alter the frozen marginal ledger.
        baseline = build_alter_index_factor_loop_plan(ROOT)
        self.assertEqual(_BASELINE_COUNT, len(baseline.cases))


if __name__ == "__main__":
    unittest.main()
