"""Tests for notify factor_loop obligation ledger."""

import unittest
from pathlib import Path

from src.pg_case_factory.notify_factor_loop import (
    build_notify_factor_loop_plan,
    compile_notify_factor_loop_obligations,
)

_REPO = Path(__file__).resolve().parents[1]


class TestNotifyFactorLoop(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_notify_factor_loop_plan(_REPO)

    def test_obligation_count(self) -> None:
        self.assertEqual(42, len(self.plan.obligations))

    def test_case_count(self) -> None:
        self.assertEqual(42, len(self.plan.cases))

    def test_delegated_count(self) -> None:
        self.assertEqual(0, len(self.plan.delegated))

    def test_kind_counts(self) -> None:
        from collections import Counter
        counts = Counter(o.kind for o in self.plan.obligations)
        self.assertEqual({"GRM": 1, "SFV": 41}, dict(counts))

    def test_factor_value_count(self) -> None:
        from src.pg_case_factory.notify_factor_loop import (
            _FACTOR_VALUE_COUNT,
        )
        self.assertEqual(41, _FACTOR_VALUE_COUNT)

    def test_frozen_multiset_sha256(self) -> None:
        self.assertEqual(
            "1fe0e1c84c1cafbee13a5dfa87e8d0f445"
            "ed977f45d53935e37e2de061c60186",
            self.plan.obligation_multiset_sha256,
        )

    def test_deterministic(self) -> None:
        other = build_notify_factor_loop_plan(_REPO)
        self.assertEqual(
            self.plan.obligation_multiset_sha256,
            other.obligation_multiset_sha256,
        )

    def test_outcome_counts(self) -> None:
        from collections import Counter
        counts = Counter(c.outcome for c in self.plan.cases)
        self.assertEqual(
            {"success": 40, "expected_failure": 2},
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
        self.assertEqual(list(range(1, 43)), ordinals)

    def test_object_prefix_format(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(
                case.object_prefix.startswith("notify_")
            )
            self.assertTrue(case.object_prefix.endswith("_"))

    def test_case_id_format(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(case.case_id.startswith("NOTIFY"))

    def test_execution_profile(self) -> None:
        for case in self.plan.cases:
            self.assertEqual("serial_sql", case.execution_profile)

    def test_compile_obligations_matches_plan(self) -> None:
        obligations = compile_notify_factor_loop_obligations(
            _REPO
        )
        self.assertEqual(
            len(obligations), len(self.plan.obligations)
        )

    def test_failure_sqlstates(self) -> None:
        valid_failure_sqlstates = {"42601", "08P01"}
        for case in self.plan.cases:
            if case.outcome == "expected_failure":
                self.assertIn(
                    case.expected_sqlstate,
                    valid_failure_sqlstates,
                )
            else:
                self.assertEqual("00000", case.expected_sqlstate)


if __name__ == "__main__":
    unittest.main()
