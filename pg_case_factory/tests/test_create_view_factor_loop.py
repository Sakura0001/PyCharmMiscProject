"""Tests for create_view factor_loop obligation ledger."""

import unittest
from pathlib import Path

from src.pg_case_factory.create_view_factor_loop import (
    build_create_view_factor_loop_plan,
    compile_create_view_factor_loop_obligations,
)

_REPO = Path(__file__).resolve().parents[1]


class TestCreateViewFactorLoop(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_create_view_factor_loop_plan(_REPO)

    def test_obligation_count(self) -> None:
        self.assertEqual(71, len(self.plan.obligations))

    def test_case_count(self) -> None:
        self.assertEqual(71, len(self.plan.cases))

    def test_delegated_count(self) -> None:
        self.assertEqual(0, len(self.plan.delegated))

    def test_kind_counts(self) -> None:
        from collections import Counter
        counts = Counter(o.kind for o in self.plan.obligations)
        self.assertEqual({"GRM": 1, "SFV": 70}, dict(counts))

    def test_frozen_multiset_sha256(self) -> None:
        self.assertEqual(
            "a636696d53257aaa0d9e0da3a74d59703b3675c5e7e75e13"
            "443aa1d703dd9436",
            self.plan.obligation_multiset_sha256,
        )

    def test_deterministic(self) -> None:
        other = build_create_view_factor_loop_plan(_REPO)
        self.assertEqual(
            self.plan.obligation_multiset_sha256,
            other.obligation_multiset_sha256,
        )

    def test_outcome_counts(self) -> None:
        from collections import Counter
        counts = Counter(c.outcome for c in self.plan.cases)
        self.assertEqual(
            {"success": 58, "expected_failure": 13},
            dict(counts),
        )

    def test_unique_case_ids(self) -> None:
        ids = [c.case_id for c in self.plan.cases]
        self.assertEqual(len(ids), len(set(ids)))

    def test_unique_filenames(self) -> None:
        names = [c.sql_filename for c in self.plan.cases]
        self.assertEqual(len(names), len(set(names)))

    def test_contiguous_ordinals(self) -> None:
        ordinals = [c.ordinal for c in self.plan.cases]
        self.assertEqual(list(range(1, 72)), ordinals)

    def test_object_prefix_format(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(
                case.object_prefix.startswith("createview_")
            )
            self.assertTrue(case.object_prefix.endswith("_"))

    def test_case_id_format(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(case.case_id.startswith("CREATEVIEW"))

    def test_execution_profile(self) -> None:
        for case in self.plan.cases:
            self.assertEqual("serial_sql", case.execution_profile)

    def test_compile_obligations_matches_plan(self) -> None:
        obligations = (
            compile_create_view_factor_loop_obligations(_REPO)
        )
        self.assertEqual(
            len(obligations), len(self.plan.obligations)
        )

    def test_recursive_consistency(self) -> None:
        for case in self.plan.cases:
            assign = dict(case.baseline_assignments)
            rc = assign.get("recursive_clause", "absent")
            cnl = assign.get("column_name_list", "absent")
            co = assign.get("check_option_clause", "absent")
            eb = assign.get("error_boundary", "none")
            if rc == "present":
                if eb == "recursive_without_column_list":
                    self.assertEqual("absent", cnl)
                else:
                    self.assertEqual(
                        "required_for_recursive", cnl
                    )
                if eb == "check_option_on_recursive":
                    self.assertNotEqual("absent", co)
                else:
                    self.assertEqual("absent", co)


if __name__ == "__main__":
    unittest.main()
