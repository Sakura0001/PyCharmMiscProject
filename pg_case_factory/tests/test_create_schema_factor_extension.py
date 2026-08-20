from collections import Counter
from pathlib import Path
import unittest

from pg_case_factory.create_schema_factor_extension import (
    CreateSchemaFactorExtensionCase,
    CreateSchemaFactorExtensionPlan,
    build_create_schema_factor_extension_plan,
)

ROOT = Path(__file__).resolve().parents[1]


class CreateSchemaFactorExtensionPlanTest(unittest.TestCase):
    def test_extension_case_count_is_frozen(self) -> None:
        plan = build_create_schema_factor_extension_plan(ROOT)
        self.assertIsInstance(
            plan, CreateSchemaFactorExtensionPlan
        )
        self.assertEqual(10530, len(plan.cases))
        self.assertEqual(10530, plan.raw_combination_count)
        self.assertEqual(0, plan.dropped_combination_count)

    def test_case_numbering_is_contiguous_after_baseline(self) -> None:
        plan = build_create_schema_factor_extension_plan(ROOT)
        ordinals = [case.ordinal for case in plan.cases]
        self.assertEqual(
            list(range(63, 63 + len(plan.cases))),
            ordinals,
        )
        self.assertEqual(63, ordinals[0])
        self.assertEqual(10592, ordinals[-1])
        self.assertEqual(
            "CREATESCHEMA00063", plan.cases[0].case_id
        )
        self.assertEqual(
            "CREATESCHEMA10592", plan.cases[-1].case_id
        )
        self.assertEqual(
            "CREATESCHEMA00063.sql",
            plan.cases[0].sql_filename,
        )
        self.assertEqual(
            "CREATESCHEMA10592.sql",
            plan.cases[-1].sql_filename,
        )
        self.assertEqual(
            "createschema_00063_",
            plan.cases[0].object_prefix,
        )
        self.assertEqual(
            "createschema_10592_",
            plan.cases[-1].object_prefix,
        )

    def test_outcome_counts_are_frozen(self) -> None:
        plan = build_create_schema_factor_extension_plan(ROOT)
        outcomes = Counter(c.outcome for c in plan.cases)
        self.assertEqual(2916, outcomes["success"])
        self.assertEqual(7614, outcomes["expected_failure"])

    def test_all_cases_are_marked_extension(self) -> None:
        plan = build_create_schema_factor_extension_plan(ROOT)
        for case in plan.cases:
            self.assertIsInstance(
                case, CreateSchemaFactorExtensionCase
            )
            self.assertTrue(case.is_extension)

    def test_every_case_has_derivation_record(self) -> None:
        plan = build_create_schema_factor_extension_plan(ROOT)
        for case in plan.cases:
            self.assertTrue(case.derivation_id)
            self.assertTrue(case.derived_from_combination_group)
            self.assertTrue(case.derivation_reason)

    def test_every_case_has_factor_assignment(self) -> None:
        plan = build_create_schema_factor_extension_plan(ROOT)
        for case in plan.cases:
            self.assertGreaterEqual(len(case.factor_assignment), 1)
            keys = [k for k, _ in case.factor_assignment]
            self.assertEqual(
                len(keys), len(set(keys)), case.case_id
            )

    def test_failure_cases_have_sqlstate_and_reason(self) -> None:
        plan = build_create_schema_factor_extension_plan(ROOT)
        for case in plan.cases:
            if case.outcome == "expected_failure":
                self.assertEqual(5, len(case.expected_sqlstate))
                self.assertIsNotNone(
                    case.expected_failure_reason
                )
            else:
                self.assertEqual("00000", case.expected_sqlstate)

    def test_no_duplicate_case_ids(self) -> None:
        plan = build_create_schema_factor_extension_plan(ROOT)
        ids = [case.case_id for case in plan.cases]
        self.assertEqual(len(ids), len(set(ids)))

    def test_frozen_multiset_sha256(self) -> None:
        plan = build_create_schema_factor_extension_plan(ROOT)
        self.assertEqual(
            "63ae5e9293e36a9dd1ba767279278a8492ac516031dd894788e4c2291c154759",
            plan.extension_multiset_sha256,
        )

    def test_plan_is_deterministic(self) -> None:
        plan = build_create_schema_factor_extension_plan(ROOT)
        again = build_create_schema_factor_extension_plan(ROOT)
        self.assertEqual(
            plan.extension_multiset_sha256,
            again.extension_multiset_sha256,
        )
        self.assertEqual(
            tuple(c.case_id for c in plan.cases),
            tuple(c.case_id for c in again.cases),
        )


if __name__ == "__main__":
    unittest.main()
