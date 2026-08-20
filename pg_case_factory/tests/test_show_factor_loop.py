"""Tests for show factor_loop obligation ledger."""

import unittest
from pathlib import Path

from src.pg_case_factory.show_factor_loop import (
    build_show_factor_loop_plan,
    compile_show_factor_loop_obligations,
)

_REPO = Path(__file__).resolve().parents[1]


class TestShowFactorLoop(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_show_factor_loop_plan(_REPO)

    def test_obligation_count(self) -> None:
        self.assertEqual(44, len(self.plan.obligations))

    def test_case_count(self) -> None:
        self.assertEqual(44, len(self.plan.cases))

    def test_delegated_count(self) -> None:
        self.assertEqual(0, len(self.plan.delegated))

    def test_kind_counts(self) -> None:
        from collections import Counter
        counts = Counter(o.kind for o in self.plan.obligations)
        self.assertEqual({"GRM": 1, "SFV": 43}, dict(counts))

    def test_factor_value_count(self) -> None:
        from src.pg_case_factory.show_factor_loop import (
            _FACTOR_VALUE_COUNT,
        )
        self.assertEqual(43, _FACTOR_VALUE_COUNT)

    def test_frozen_multiset_sha256(self) -> None:
        self.assertEqual(
            "ab092d0b56f3ac90b3f5c3e5f156ed04aad2adbe5e7b9a5c"
            "6675e2f55c4799a1",
            self.plan.obligation_multiset_sha256,
        )

    def test_deterministic(self) -> None:
        other = build_show_factor_loop_plan(_REPO)
        self.assertEqual(
            self.plan.obligation_multiset_sha256,
            other.obligation_multiset_sha256,
        )

    def test_outcome_counts(self) -> None:
        from collections import Counter
        counts = Counter(c.outcome for c in self.plan.cases)
        self.assertEqual(
            {"success": 41, "expected_failure": 3},
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
        self.assertEqual(list(range(1, 45)), ordinals)

    def test_object_prefix_format(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(
                case.object_prefix.startswith("show_")
            )
            self.assertTrue(case.object_prefix.endswith("_"))

    def test_case_id_format(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(case.case_id.startswith("SHOW"))

    def test_execution_profile(self) -> None:
        for case in self.plan.cases:
            self.assertEqual("serial_sql", case.execution_profile)

    def test_compile_obligations_matches_plan(self) -> None:
        obligations = compile_show_factor_loop_obligations(
            _REPO
        )
        self.assertEqual(
            len(obligations), len(self.plan.obligations)
        )

    def test_failure_sqlstate_is_25001(self) -> None:
        for case in self.plan.cases:
            if case.outcome == "expected_failure":
                self.assertEqual("25001", case.expected_sqlstate)
            else:
                self.assertEqual("00000", case.expected_sqlstate)

    def test_catalog_rows_match_fvc(self) -> None:
        from src.pg_case_factory.applicability import (
            load_shipped_applicability_universe,
        )
        from src.pg_case_factory.show_factor_loop import (
            _CANONICAL_FACTOR_VALUES,
            _FACTOR_VALUE_COUNT,
        )
        universe = load_shipped_applicability_universe(_REPO)
        catalog_rows = len(
            universe.rows_for_statement("show")
        )
        self.assertEqual(catalog_rows, _FACTOR_VALUE_COUNT)
        ledger = {
            (r.factor, r.value)
            for r in universe.rows_for_statement("show")
        }
        self.assertEqual(set(_CANONICAL_FACTOR_VALUES), ledger)


if __name__ == "__main__":
    unittest.main()
