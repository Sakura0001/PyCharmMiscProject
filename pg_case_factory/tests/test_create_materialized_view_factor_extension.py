from collections import Counter
from pathlib import Path
import unittest

from pg_case_factory.create_materialized_view_factor_extension import (
    CreateMaterializedViewFactorExtensionCase,
    CreateMaterializedViewFactorExtensionPlan,
    build_create_materialized_view_factor_extension_plan,
)

ROOT = Path(__file__).resolve().parents[1]


class CreateMaterializedViewFactorExtensionPlanTest(unittest.TestCase):
    def test_frozen_case_count_and_cap(self) -> None:
        plan = build_create_materialized_view_factor_extension_plan(ROOT)
        self.assertEqual(12864, len(plan.cases))
        self.assertEqual(0, plan.dropped_count)
        self.assertEqual(12864, plan.raw_combination_count)

    def test_frozen_multiset_sha256(self) -> None:
        plan = build_create_materialized_view_factor_extension_plan(ROOT)
        self.assertEqual(
            "bc0bd39e0a1e6c841180e7733492830437920b5c8be0678b75c59a7461f9753e",
            plan.extension_multiset_sha256,
        )

    def test_outcome_counts_are_frozen(self) -> None:
        plan = build_create_materialized_view_factor_extension_plan(ROOT)
        outcomes = Counter(c.outcome for c in plan.cases)
        self.assertEqual(12288, outcomes["success"])
        self.assertEqual(576, outcomes["expected_failure"])

    def test_ordinal_and_filename_continuity(self) -> None:
        plan = build_create_materialized_view_factor_extension_plan(ROOT)
        first = plan.cases[0]
        last = plan.cases[-1]
        # Baseline ends at 48; first extension is ordinal 49.
        self.assertEqual(49, first.ordinal)
        self.assertEqual(49 + 12864 - 1, last.ordinal)
        self.assertEqual(
            f"CREATEMATERIALIZEDVIEW{49:05d}", first.case_id
        )
        self.assertEqual(
            f"CREATEMATERIALIZEDVIEW{49 + 12864 - 1:05d}",
            last.case_id,
        )
        self.assertTrue(
            all(c.case_id.endswith(f"{c.ordinal:05d}") for c in plan.cases)
        )
        self.assertTrue(
            all(
                c.object_prefix
                == f"creatematerializedview_{c.ordinal:05d}_"
                for c in plan.cases
            )
        )

    def test_extension_cases_carry_derivation_records(self) -> None:
        plan = build_create_materialized_view_factor_extension_plan(ROOT)
        for case in plan.cases:
            self.assertTrue(case.is_extension)
            self.assertTrue(case.derivation_id)
            self.assertTrue(case.derived_from_combination_group)
            self.assertTrue(case.derivation_reason)

    def test_unique_case_ids_and_filenames(self) -> None:
        plan = build_create_materialized_view_factor_extension_plan(ROOT)
        ids = [c.case_id for c in plan.cases]
        files = [c.sql_filename for c in plan.cases]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(files), len(set(files)))

    def test_factor_assignment_has_no_duplicate_keys(self) -> None:
        plan = build_create_materialized_view_factor_extension_plan(ROOT)
        for case in plan.cases:
            keys = [k for k, _ in case.factor_assignment]
            self.assertEqual(len(keys), len(set(keys)))

    def test_at_most_one_failure_attribution_per_case(self) -> None:
        plan = build_create_materialized_view_factor_extension_plan(ROOT)
        neg_values = {
            ("target_object_state", "exists"),
            ("target_object_state", "exists_conflict"),
            ("dependency_state", "missing_dependency"),
            ("query_source_state", "source_table_missing"),
            ("privilege_context", "insufficient_privilege"),
            ("constraint_boundary", "security_restricted_operation"),
        }
        for case in plan.cases:
            present = {
                (k, v) for k, v in case.factor_assignment
                if (k, v) in neg_values
            }
            if case.outcome == "expected_failure":
                # Exactly one negative axis carries the failure pair.
                self.assertEqual(1, len(present), case.case_id)
            else:
                # Success cases carry no failure-causing value pair.
                self.assertEqual(0, len(present), case.case_id)

    def test_plan_is_deterministic(self) -> None:
        plan = build_create_materialized_view_factor_extension_plan(ROOT)
        again = build_create_materialized_view_factor_extension_plan(ROOT)
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
