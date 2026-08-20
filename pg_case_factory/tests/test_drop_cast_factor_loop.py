from collections import Counter
from pathlib import Path
import unittest

from pg_case_factory.drop_cast_factor_loop import (
    DropCastFactorCase,
    DropCastFactorLoopError,
    DropCastFactorLoopPlan,
    build_drop_cast_factor_loop_plan,
    compile_drop_cast_factor_loop_obligations,
)

ROOT = Path(__file__).resolve().parents[1]

# Frozen spec: GRM(1) + SFV(41) + RISK(2) = 44 ; INV is not applicable.
_OBLIGATION_COUNT = 44
_KIND_COUNTS = {"GRM": 1, "SFV": 41, "RISK": 2}
_FAILURE_COUNT = 6
_COVERED_COUNT = _OBLIGATION_COUNT - _FAILURE_COUNT  # 38
_OBLIGATION_MULTISET_SHA256 = (
    "5e3cc9e2e443595ebff87d4b00da16dba689cbe458b9b368038869e17e8bceae"
)


class DropCastFactorLoopLedgerTest(unittest.TestCase):
    def test_compiles_exact_required_obligation_bag(self) -> None:
        rows = compile_drop_cast_factor_loop_obligations(ROOT)
        self.assertEqual(_OBLIGATION_COUNT, len(rows))
        self.assertEqual(
            _KIND_COUNTS,
            Counter(row.kind for row in rows),
        )
        self.assertEqual(
            _OBLIGATION_COUNT, len({row.obligation_id for row in rows})
        )
        self.assertEqual(0, sum(row.kind == "INV" for row in rows))
        self.assertEqual(0, sum(row.disposition == "delegated" for row in rows))
        self.assertEqual(
            _OBLIGATION_COUNT,
            sum(
                row.disposition in {"covered", "expected_failure"}
                for row in rows
            ),
        )
        allowed = {"covered", "expected_failure", "delegated"}
        self.assertTrue(all(row.disposition in allowed for row in rows))

    def test_canonical_obligation_count_matches_inventory(self) -> None:
        rows = compile_drop_cast_factor_loop_obligations(ROOT)
        sfv = [row for row in rows if row.kind == "SFV"]
        self.assertEqual(41, len(sfv))
        seen: dict[tuple[str, str], int] = {}
        for row in sfv:
            seen[(row.factor_key, row.value)] = (
                seen.get((row.factor_key, row.value), 0) + 1
            )
        self.assertEqual(41, sum(seen.values()))
        self.assertEqual(41, len(seen))

    def test_expected_failure_dispositions_are_frozen(self) -> None:
        rows = compile_drop_cast_factor_loop_obligations(ROOT)
        failures = [
            (row.factor_key, row.value)
            for row in rows
            if row.disposition == "expected_failure"
        ]
        covered = sum(row.disposition == "covered" for row in rows)
        self.assertEqual(_FAILURE_COUNT, len(failures))
        self.assertEqual(_COVERED_COUNT, covered)
        self.assertEqual(len(failures), len(set(failures)))

    def test_obligation_multiset_sha256_is_frozen(self) -> None:
        plan = build_drop_cast_factor_loop_plan(ROOT)
        self.assertEqual(
            _OBLIGATION_MULTISET_SHA256,
            plan.obligation_multiset_sha256,
        )


class DropCastFactorLoopPlanTest(unittest.TestCase):
    def test_one_case_per_local_obligation_with_stable_numbering(self) -> None:
        plan = build_drop_cast_factor_loop_plan(ROOT)
        self.assertIsInstance(plan, DropCastFactorLoopPlan)
        self.assertEqual(0, len(plan.delegated))
        self.assertEqual(_OBLIGATION_COUNT, len(plan.cases))
        self.assertEqual(
            list(range(1, _OBLIGATION_COUNT + 1)),
            [row.ordinal for row in plan.cases],
        )
        self.assertEqual("DROPCAST00001", plan.cases[0].case_id)
        self.assertEqual(
            f"DROPCAST{_OBLIGATION_COUNT:05d}",
            plan.cases[-1].case_id,
        )
        self.assertEqual(
            "DROPCAST00001.sql", plan.cases[0].sql_filename
        )
        self.assertEqual(
            f"DROPCAST{_OBLIGATION_COUNT:05d}.sql",
            plan.cases[-1].sql_filename,
        )
        self.assertEqual(
            "dropcast_00001_", plan.cases[0].object_prefix
        )
        self.assertEqual(
            f"dropcast_{_OBLIGATION_COUNT:05d}_",
            plan.cases[-1].object_prefix,
        )
        self.assertEqual(
            _OBLIGATION_COUNT,
            len({row.primary_obligation_id for row in plan.cases}),
        )
        self.assertEqual(
            _OBLIGATION_COUNT,
            len({row.sql_filename for row in plan.cases}),
        )
        self.assertTrue(
            all(row.execution_profile == "serial_sql" for row in plan.cases)
        )

    def test_outcome_driven_by_disposition(self) -> None:
        plan = build_drop_cast_factor_loop_plan(ROOT)
        obligations = compile_drop_cast_factor_loop_obligations(ROOT)
        by_id = {row.obligation_id: row for row in obligations}
        for case in plan.cases:
            obligation = by_id[case.primary_obligation_id]
            if obligation.disposition == "expected_failure":
                self.assertEqual("expected_failure", case.outcome)
                self.assertEqual(5, len(case.expected_sqlstate))
                self.assertIsNotNone(case.expected_failure_reason)
            else:
                self.assertEqual("success", case.outcome)
                self.assertEqual("00000", case.expected_sqlstate)
                self.assertIsNone(case.expected_failure_reason)

    def test_baseline_has_one_primary_value_no_duplicates(self) -> None:
        plan = build_drop_cast_factor_loop_plan(ROOT)
        for case in plan.cases:
            primary_seen = sum(
                1
                for key, _ in case.baseline_assignments
                if key == case.factor_key
            )
            self.assertEqual(1, primary_seen, case.sql_filename)
            keys = [key for key, _ in case.baseline_assignments]
            self.assertEqual(len(keys), len(set(keys)), case.sql_filename)
            primary_value = next(
                value
                for key, value in case.baseline_assignments
                if key == case.factor_key
            )
            self.assertEqual(case.factor_value, primary_value)
            self.assertEqual(
                case.baseline_assignments,
                tuple(sorted(case.baseline_assignments)),
            )

    def test_sfv_obligation_ids_carry_row_id_one_to_one(self) -> None:
        plan = build_drop_cast_factor_loop_plan(ROOT)
        sfv_cases = [c for c in plan.cases if c.kind == "SFV"]
        self.assertEqual(41, len(sfv_cases))
        for case in sfv_cases:
            self.assertRegex(
                case.primary_obligation_id,
                r"^DCAST-SFV\|[^|]+\|[^|]+$",
                case.case_id,
            )


if __name__ == "__main__":
    unittest.main()
