from collections import Counter
from pathlib import Path
import unittest

from pg_case_factory.alter_text_search_configuration_factor_extension import (
    AlterTextSearchConfigurationFactorExtensionCase,
    AlterTextSearchConfigurationFactorExtensionError,
    AlterTextSearchConfigurationFactorExtensionPlan,
    _BASELINE_COUNT,
    _CAP,
    _CLEANUP_MODES,
    _VERIFICATION_MODES,
    build_alter_text_search_configuration_factor_extension_plan,
)

ROOT = Path(__file__).resolve().parents[1]


class AlterTextSearchConfigurationFactorExtensionPlanTest(unittest.TestCase):
    def test_extension_case_count_is_frozen(self) -> None:
        plan = build_alter_text_search_configuration_factor_extension_plan(ROOT)
        self.assertIsInstance(
            plan, AlterTextSearchConfigurationFactorExtensionPlan
        )
        self.assertEqual(4890, len(plan.cases))
        self.assertEqual(4890, plan.raw_combination_count)
        self.assertEqual(0, plan.dropped_count)

    def test_case_numbering_is_contiguous_after_baseline(self) -> None:
        plan = build_alter_text_search_configuration_factor_extension_plan(ROOT)
        ordinals = [c.ordinal for c in plan.cases]
        self.assertEqual(
            list(range(90, 4980)), ordinals
        )
        self.assertEqual(
            "ALTERTEXTSEARCHCONFIGURATION00090", plan.cases[0].case_id
        )
        self.assertEqual(
            "ALTERTEXTSEARCHCONFIGURATION04979", plan.cases[-1].case_id
        )
        self.assertEqual(
            "ALTERTEXTSEARCHCONFIGURATION00090.sql",
            plan.cases[0].sql_filename,
        )
        self.assertEqual(
            "ALTERTEXTSEARCHCONFIGURATION04979.sql",
            plan.cases[-1].sql_filename,
        )

    def test_outcome_counts_are_frozen(self) -> None:
        plan = build_alter_text_search_configuration_factor_extension_plan(ROOT)
        outcomes = Counter(c.outcome for c in plan.cases)
        self.assertEqual(1260, outcomes["success"])
        self.assertEqual(3630, outcomes["expected_failure"])

    def test_all_cases_are_marked_extension(self) -> None:
        plan = build_alter_text_search_configuration_factor_extension_plan(ROOT)
        self.assertTrue(all(c.is_extension for c in plan.cases))

    def test_every_case_has_derivation_record(self) -> None:
        plan = build_alter_text_search_configuration_factor_extension_plan(ROOT)
        for case in plan.cases:
            self.assertTrue(case.derivation_id)
            self.assertTrue(case.derived_from_combination_group)
            self.assertTrue(case.derivation_reason)

    def test_every_case_has_factor_assignment(self) -> None:
        plan = build_alter_text_search_configuration_factor_extension_plan(ROOT)
        for case in plan.cases:
            self.assertGreater(len(case.factor_assignment), 0)
            keys = [k for k, _ in case.factor_assignment]
            self.assertEqual(
                len(keys), len(set(keys)), case.case_id
            )

    def test_failure_cases_have_sqlstate_and_reason(self) -> None:
        plan = build_alter_text_search_configuration_factor_extension_plan(ROOT)
        for case in plan.cases:
            if case.outcome == "expected_failure":
                self.assertEqual(5, len(case.expected_sqlstate))
                self.assertIsNotNone(case.expected_failure_reason)
            else:
                self.assertEqual("00000", case.expected_sqlstate)

    def test_plan_is_deterministic(self) -> None:
        plan_a = build_alter_text_search_configuration_factor_extension_plan(ROOT)
        plan_b = build_alter_text_search_configuration_factor_extension_plan(ROOT)
        self.assertEqual(
            plan_a.extension_multiset_sha256,
            plan_b.extension_multiset_sha256,
        )
        self.assertEqual(
            tuple(c.case_id for c in plan_a.cases),
            tuple(c.case_id for c in plan_b.cases),
        )

    def test_frozen_extension_multiset_sha256(self) -> None:
        plan = build_alter_text_search_configuration_factor_extension_plan(ROOT)
        self.assertEqual(
            "bfb8aafa8132f22404e9a6bf2b744f336373e5b88d2b441489e2a94fecac2ed5",
            plan.extension_multiset_sha256,
        )

    def test_constants_are_frozen(self) -> None:
        self.assertEqual(89, _BASELINE_COUNT)
        self.assertEqual(20000, _CAP)
        self.assertEqual(
            ("catalog_query_pg_ts_config", "mapping_query", "error_assertion"),
            _VERIFICATION_MODES,
        )
        self.assertEqual(
            (
                "drop_mapping_revert",
                "revert_rename",
                "revert_owner",
                "drop_text_search_configuration",
                "role_cleanup",
            ),
            _CLEANUP_MODES,
        )

    def test_total_case_count_is_within_cap(self) -> None:
        plan = build_alter_text_search_configuration_factor_extension_plan(ROOT)
        total = _BASELINE_COUNT + len(plan.cases)
        self.assertLessEqual(total, _CAP)
        self.assertEqual(4979, total)


if __name__ == "__main__":
    unittest.main()
