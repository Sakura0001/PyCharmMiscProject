from collections import Counter
from pathlib import Path
import unittest

from pg_case_factory.alter_function_factor_loop import (
    AlterFunctionFactorLoopError,
    compile_alter_function_factor_loop_obligations,
)
from pg_case_factory.alter_function_regress import (
    load_alter_function_grammar_actions,
    load_alter_function_grammar_axes,
)

ROOT = Path(__file__).resolve().parents[1]


class AlterFunctionRegressGrammarTest(unittest.TestCase):
    def test_grammar_action_and_axis_ledger_is_frozen(self) -> None:
        actions = load_alter_function_grammar_actions()
        axes = load_alter_function_grammar_axes()
        self.assertEqual(23, len(actions))
        self.assertEqual(6, len(axes))
        self.assertEqual(13, sum(len(axis.values) for axis in axes))
        # every axis action is either the outer sentinel or a known action
        action_ids = {action.action_id for action in actions}
        for axis in axes:
            if not axis.action_id.startswith("__outer_"):
                self.assertIn(axis.action_id, action_ids)


class AlterFunctionFactorLoopLedgerTest(unittest.TestCase):
    def test_compiles_exact_required_obligation_bag(self) -> None:
        rows = compile_alter_function_factor_loop_obligations(ROOT)
        # GRM(36) + SFV(85) + RISK(2) = 123 ; INV is not applicable.
        self.assertEqual(123, len(rows))
        self.assertEqual(
            {"GRM": 36, "SFV": 85, "RISK": 2},
            Counter(row.kind for row in rows),
        )
        self.assertEqual(123, len({row.obligation_id for row in rows}))
        self.assertEqual(0, sum(row.kind == "INV" for row in rows))
        self.assertEqual(0, sum(row.disposition == "delegated" for row in rows))
        self.assertEqual(
            123,
            sum(row.disposition in {"covered", "expected_failure"} for row in rows),
        )
        allowed = {"covered", "expected_failure", "delegated"}
        self.assertTrue(all(row.disposition in allowed for row in rows))

    def test_canonical_obligation_count_matches_inventory(self) -> None:
        rows = compile_alter_function_factor_loop_obligations(ROOT)
        sfv = [row for row in rows if row.kind == "SFV"]
        self.assertEqual(85, len(sfv))
        # every canonical factor value has exactly one SFV obligation
        seen: dict[tuple[str, str], int] = {}
        for row in sfv:
            seen[(row.factor_key, row.value)] = (
                seen.get((row.factor_key, row.value), 0) + 1
            )
        self.assertEqual(85, sum(seen.values()))
        self.assertEqual(85, len(seen))

    def test_expected_failure_dispositions_are_frozen(self) -> None:
        rows = compile_alter_function_factor_loop_obligations(ROOT)
        failures = [
            (row.factor_key, row.value)
            for row in rows
            if row.disposition == "expected_failure"
        ]
        covered = sum(row.disposition == "covered" for row in rows)
        # 24 canonical values reach the PG target check and are rejected;
        # the remaining 61 SFV + 36 GRM + 2 RISK = 99 are covered.
        self.assertEqual(24, len(failures))
        self.assertEqual(99, covered)
        # no duplicate failure obligation
        self.assertEqual(len(failures), len(set(failures)))
        # without_signature and over_63_chars are NOT failures (legal / truncated)
        self.assertNotIn(("argtype_specification", "without_signature"), failures)
        self.assertNotIn(("identifier_length_exceeded", "over_63_chars"), failures)


if __name__ == "__main__":
    unittest.main()
