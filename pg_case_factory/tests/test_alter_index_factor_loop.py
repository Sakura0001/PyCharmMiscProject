from __future__ import annotations

from collections import Counter
from pathlib import Path
import unittest

from pg_case_factory.alter_index_factor_loop import (
    AlterIndexFactorLoopError,
    AlterIndexFactorLoopPlan,
    build_alter_index_factor_loop_plan,
    compile_alter_index_factor_loop_obligations,
)
from pg_case_factory.alter_index_regress import (
    EXPECTED_SQLSTATE_BY_REASON,
    load_alter_index_grammar_actions,
    load_alter_index_grammar_axes,
    load_alter_index_type_witnesses,
)

ROOT = Path(__file__).resolve().parents[1]

# Frozen marginal ledger totals (alter_index combination matrix).
_EXPECTED_CASE_COUNT = 87
_EXPECTED_OBLIGATION_KINDS = {"GRM": 21, "SFV": 66}
_EXPECTED_OUTCOME_SPLIT = {"success": 73, "expected_failure": 14}
_EXPECTED_MULTISET_SHA256 = (
    "e5653b9c43e72cbd863a1a5ae9315a376823dc1d64fdafb70f5bcaef70fd5084"
)
_EXPECTED_BRANCHES = (
    "all_in_tablespace",
    "attach_partition",
    "depends_on_extension",
    "no_depends_on_extension",
    "rename",
    "reset_storage",
    "set_statistics",
    "set_storage",
    "set_tablespace",
)


class AlterIndexRegressGrammarTest(unittest.TestCase):
    def test_grammar_action_and_axis_ledger_is_frozen(self) -> None:
        actions = load_alter_index_grammar_actions(ROOT)
        axes = load_alter_index_grammar_axes(ROOT)
        # 10 combination groups expand to 21 (group x branch) actions across
        # the 9 canonical ALTER INDEX branches; every axis action is a known
        # action.
        self.assertEqual(21, len(actions))
        self.assertEqual(9, len({a.action_id for a in actions}))
        self.assertEqual(_EXPECTED_BRANCHES, tuple(sorted({a.action_id for a in actions})))
        for axis in axes:
            self.assertIn(axis.action_id, {a.action_id for a in actions})

    def test_type_witnesses_load_without_drift(self) -> None:
        witnesses = load_alter_index_type_witnesses(ROOT)
        self.assertTrue(witnesses)
        # representative types are branch-scoped; no per-type expectations.
        for witness in witnesses:
            self.assertEqual("pg18", witness.selector_id)
            self.assertEqual((), witness.index_capabilities)


class AlterIndexFactorLoopLedgerTest(unittest.TestCase):
    def test_compiles_exact_required_obligation_bag(self) -> None:
        rows = compile_alter_index_factor_loop_obligations(ROOT)
        # GRM(21 grammar action skeletons) + SFV(66 canonical matrix factor
        # values) = 87 ; INV is not applicable (column coverage is conditional,
        # owned by CREATE INDEX) and RISK is realized as expected-failure SFV
        # values.  SFV obligations are 1:1 with the applicability matrix row_ids
        # so the shared conservation contract credits each row exactly once.
        self.assertEqual(_EXPECTED_CASE_COUNT, len(rows))
        self.assertEqual(
            _EXPECTED_OBLIGATION_KINDS,
            Counter(row.kind for row in rows),
        )
        self.assertEqual(_EXPECTED_CASE_COUNT, len({row.obligation_id for row in rows}))
        self.assertEqual(0, sum(row.disposition == "delegated" for row in rows))
        self.assertEqual(
            _EXPECTED_CASE_COUNT,
            sum(row.disposition in {"covered", "expected_failure"} for row in rows),
        )
        allowed = {"covered", "expected_failure", "delegated"}
        self.assertTrue(all(row.disposition in allowed for row in rows))
        # ordinals are assigned 1..N at compile time.
        self.assertEqual(
            list(range(1, _EXPECTED_CASE_COUNT + 1)),
            [row.ordinal for row in rows],
        )

    def test_factor_value_coverage_is_complete(self) -> None:
        plan = build_alter_index_factor_loop_plan(ROOT)
        from pg_case_factory.alter_index_regress import _load_combination_matrix

        factors = _load_combination_matrix(str(ROOT))["factor_contract"]["factors"]
        witnessed: dict[str, set[str]] = {}
        for case in plan.cases:
            bindings = dict(case.baseline_assignments)
            bindings[case.factor_key] = case.factor_value
            for key, value in bindings.items():
                witnessed.setdefault(key, set()).add(str(value))
        for factor_key, spec in factors.items():
            required = {str(v) for v in spec.get("required_values", [])}
            with self.subTest(factor=factor_key):
                self.assertEqual(
                    set(),
                    required - witnessed.get(factor_key, set()),
                    f"unwitnessed required values for {factor_key}",
                )
        # no synthetic factors leak outside the contract.
        self.assertEqual(set(factors), set(witnessed))

    def test_one_case_per_local_obligation_with_stable_numbering(self) -> None:
        plan = build_alter_index_factor_loop_plan(ROOT)
        self.assertIsInstance(plan, AlterIndexFactorLoopPlan)
        self.assertEqual(0, len(plan.delegated))
        self.assertEqual(_EXPECTED_CASE_COUNT, len(plan.cases))
        self.assertEqual(
            list(range(1, _EXPECTED_CASE_COUNT + 1)),
            [row.ordinal for row in plan.cases],
        )
        self.assertEqual("ALTERINDEX00001", plan.cases[0].case_id)
        self.assertEqual("ALTERINDEX00087", plan.cases[-1].case_id)
        self.assertEqual("ALTERINDEX00001.sql", plan.cases[0].sql_filename)
        self.assertEqual("ALTERINDEX00087.sql", plan.cases[-1].sql_filename)
        self.assertEqual("alterindex_00001_", plan.cases[0].object_prefix)
        self.assertEqual("alterindex_00087_", plan.cases[-1].object_prefix)
        self.assertEqual(
            _EXPECTED_CASE_COUNT,
            len({row.primary_obligation_id for row in plan.cases}),
        )
        self.assertEqual(
            _EXPECTED_CASE_COUNT,
            len({row.sql_filename for row in plan.cases}),
        )
        self.assertTrue(
            all(row.execution_profile == "same_session_multiphase" for row in plan.cases)
        )
        # every case maps back to exactly one compiled obligation.
        obligations = compile_alter_index_factor_loop_obligations(ROOT)
        obligation_ids = {row.obligation_id for row in obligations}
        self.assertEqual(
            obligation_ids,
            {row.primary_obligation_id for row in plan.cases},
        )

    def test_outcome_split_and_disposition_drives_case_outcome(self) -> None:
        plan = build_alter_index_factor_loop_plan(ROOT)
        self.assertEqual(
            _EXPECTED_OUTCOME_SPLIT,
            Counter(row.outcome for row in plan.cases),
        )
        for case in plan.cases:
            with self.subTest(case_id=case.case_id):
                if case.outcome == "expected_failure":
                    self.assertEqual("expected_failure", case.outcome)
                    self.assertRegex(case.expected_sqlstate, r"^[0-9A-Z]{5}$")
                    self.assertNotEqual("00000", case.expected_sqlstate)
                    self.assertTrue(case.expected_failure_reason)
                else:
                    self.assertIn(case.outcome, {"success", "no_op"})
                    self.assertEqual("00000", case.expected_sqlstate)
                    self.assertIsNone(case.expected_failure_reason)

    def test_expected_failure_sqlstate_maps_to_declared_reason(self) -> None:
        plan = build_alter_index_factor_loop_plan(ROOT)
        for case in plan.cases:
            if case.outcome != "expected_failure":
                continue
            with self.subTest(case_id=case.case_id):
                reason = case.expected_failure_reason
                self.assertIn(
                    reason,
                    EXPECTED_SQLSTATE_BY_REASON,
                    f"reason {reason!r} has no sqlstate mapping",
                )
                self.assertEqual(
                    EXPECTED_SQLSTATE_BY_REASON[reason],
                    case.expected_sqlstate,
                )

    def test_baseline_has_one_primary_value_no_duplicates_sorted(self) -> None:
        plan = build_alter_index_factor_loop_plan(ROOT)
        for case in plan.cases:
            with self.subTest(case_id=case.case_id):
                keys = [key for key, _ in case.baseline_assignments]
                self.assertEqual(len(keys), len(set(keys)), case.sql_filename)
                primary_seen = sum(1 for key, _ in case.baseline_assignments if key == case.factor_key)
                self.assertEqual(1, primary_seen, case.sql_filename)
                primary_value = next(
                    value for key, value in case.baseline_assignments if key == case.factor_key
                )
                self.assertEqual(case.factor_value, primary_value)
                # every baseline is sorted by factor key for determinism.
                self.assertEqual(
                    case.baseline_assignments,
                    tuple(sorted(case.baseline_assignments)),
                )
                # every case records its branch.
                self.assertIn(("statement_branch", case.consumer_action_id), case.baseline_assignments)

    def test_all_nine_branches_are_witnessed(self) -> None:
        plan = build_alter_index_factor_loop_plan(ROOT)
        branches = {case.consumer_action_id for case in plan.cases}
        self.assertEqual(set(_EXPECTED_BRANCHES), branches)

    def test_case_plan_is_byte_stable_in_memory(self) -> None:
        first = build_alter_index_factor_loop_plan(ROOT)
        second = build_alter_index_factor_loop_plan(ROOT)
        self.assertEqual(first, second)
        self.assertEqual(_EXPECTED_MULTISET_SHA256, first.obligation_multiset_sha256)

    def test_no_duplicate_obligation_ids(self) -> None:
        rows = compile_alter_index_factor_loop_obligations(ROOT)
        ids = [row.obligation_id for row in rows]
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()
