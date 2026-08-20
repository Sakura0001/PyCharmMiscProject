"""Tests for the bounded DROP CAST post-coverage extension expander.

The marginal factor-value-loop (``drop_cast_factor_loop.py``) is the
frozen 44-case baseline (GRM 1 + SFV 41 + RISK 2).  This module's expander
adds the bounded post-coverage extension phase: cross-factor combinations
of the positive T1-T4 behaviour axes across the single official synopsis
branch (at most one failure-causing value per case, so attribution stays
clean), with ``verification_mode`` crossed and ``cleanup_mode`` crossed so
every declared T6 value is exercised.  Each extension case carries a
derivation record and is marked ``is_extension = True``; it never replaces
a required-baseline obligation.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import unittest

import yaml

from pg_case_factory.drop_cast_factor_extension import (
    DropCastFactorExtensionCase,
    DropCastFactorExtensionError,
    DropCastFactorExtensionPlan,
    build_drop_cast_factor_extension_plan,
)
from pg_case_factory.drop_cast_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_drop_cast_factor_loop_plan,
)


ROOT = Path(__file__).resolve().parents[1]

_BASELINE_COUNT = 44
_EXTENSION_COUNT = 96
_TOTAL_COUNT = _BASELINE_COUNT + _EXTENSION_COUNT  # 140
_SUCCESS_EXTENSIONS = 48
_FAILURE_EXTENSIONS = 48
_EXTENSION_MULTISET_SHA256 = (
    "342f8d7b211f387dce6ca2b7af68e1fdb3c25664f2c254cce2a641fc1ec2e07e"
)

# The privilege boundary (privilege_level=non_owner) is the only crossed
# behaviour negative; it is counted as a single unit.
_PRIVILEGE_NEGATIVE = ("privilege_level", "non_owner")

_CROSSED_AXES = {
    "statement_branch": ("branch_1",),
    "target_action": ("drop_cast",),
    "source_type_shape": ("plain_type", "schema_qualified_type"),
    "target_type_shape": ("plain_type", "schema_qualified_type"),
    "if_exists_clause": ("absent", "present"),
    "cascade_restrict": ("RESTRICT_default", "RESTRICT_explicit", "CASCADE"),
    "privilege_level": ("type_owner_source", "non_owner"),
    "verification_mode": (
        "pg_cast_catalog_query",
        "pg_cast_removed_assertion",
    ),
    "cleanup_mode": (
        "DROP_CAST_IF_EXISTS",
    ),
}

_HELD_CONSTANT = {
    "object_state": "already_exists",
    "nonexistent_cast": "without_if_exists",
    "insufficient_privilege": "owns_no_type",
    "type_ownership": "owns_source",
    "source_type": "custom_type",
    "target_type": "custom_type",
    "reverse_direction_cast": "reverse_still_exists",
}

_BRANCH_GRAMMAR = {"branch_1": "branch_1"}
_BRANCH_FIXED_ACTION = {"branch_1": "drop_cast"}


def _failure_unit_count(assignment: dict[str, str]) -> int:
    count = 0
    if assignment.get("privilege_level") == "non_owner":
        count += 1
    return count


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    if assignment.get("privilege_level") == "non_owner":
        return _PRIVILEGE_NEGATIVE
    return None


class DropCastFactorExtensionPlanTest(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_drop_cast_factor_extension_plan(ROOT)

    def test_builds_frozen_extension_count_with_no_truncation(self) -> None:
        self.assertIsInstance(self.plan, DropCastFactorExtensionPlan)
        self.assertEqual(_EXTENSION_COUNT, len(self.plan.cases))
        self.assertEqual(_EXTENSION_COUNT, self.plan.raw_combination_count)
        self.assertEqual(0, self.plan.dropped_count)

    def test_extension_multiset_sha256_is_frozen(self) -> None:
        self.assertEqual(
            _EXTENSION_MULTISET_SHA256,
            self.plan.extension_multiset_sha256,
        )

    def test_ordinals_continue_after_baseline_with_five_digit_scheme(
        self,
    ) -> None:
        ordinals = [case.ordinal for case in self.plan.cases]
        self.assertEqual(
            list(range(_BASELINE_COUNT + 1, _TOTAL_COUNT + 1)), ordinals
        )
        first, last = self.plan.cases[0], self.plan.cases[-1]
        self.assertEqual(_BASELINE_COUNT + 1, first.ordinal)
        self.assertEqual(_TOTAL_COUNT, last.ordinal)
        self.assertEqual("DROPCAST00045", first.case_id)
        self.assertEqual(f"DROPCAST{_TOTAL_COUNT:05d}", last.case_id)
        self.assertEqual("DROPCAST00045.sql", first.sql_filename)
        self.assertEqual(
            f"DROPCAST{_TOTAL_COUNT:05d}.sql", last.sql_filename
        )
        self.assertEqual("dropcast_00045_", first.object_prefix)
        self.assertEqual(
            f"dropcast_{_TOTAL_COUNT:05d}_", last.object_prefix
        )

    def test_every_case_is_marked_extension_with_full_assignment(self) -> None:
        for case in self.plan.cases:
            self.assertIsInstance(case, DropCastFactorExtensionCase)
            self.assertTrue(case.is_extension, case.case_id)
            self.assertEqual(18, len(case.factor_assignment), case.case_id)
            keys = [k for k, _ in case.factor_assignment]
            self.assertEqual(len(keys), len(set(keys)), case.case_id)
            self.assertEqual(
                tuple(sorted(case.factor_assignment)),
                case.factor_assignment,
            )

    def test_outcome_split_matches_frozen_arithmetic(self) -> None:
        outcomes = Counter(case.outcome for case in self.plan.cases)
        self.assertEqual(_SUCCESS_EXTENSIONS, outcomes["success"])
        self.assertEqual(_FAILURE_EXTENSIONS, outcomes["expected_failure"])
        self.assertEqual(_EXTENSION_COUNT, sum(outcomes.values()))

    def test_at_most_one_failure_unit_per_case(self) -> None:
        for case in self.plan.cases:
            assignment = dict(case.factor_assignment)
            count = _failure_unit_count(assignment)
            self.assertLessEqual(count, 1, case.case_id)
            if case.outcome == "expected_failure":
                self.assertEqual(1, count, case.case_id)
            else:
                self.assertEqual(0, count, case.case_id)

    def test_expected_status_is_derived_from_present_failure_pair(self) -> None:
        for case in self.plan.cases:
            assignment = dict(case.factor_assignment)
            pair = _present_failure_pair(assignment)
            self.assertEqual(
                "failure" if pair is not None else "success",
                assignment["expected_status"],
                case.case_id,
            )

    def test_expected_sqlstate_matches_present_failure_pair(self) -> None:
        for case in self.plan.cases:
            assignment = dict(case.factor_assignment)
            pair = _present_failure_pair(assignment)
            if pair is None:
                self.assertEqual("success", case.outcome, case.case_id)
                self.assertEqual(
                    "00000", case.expected_sqlstate, case.case_id
                )
                self.assertIsNone(
                    case.expected_failure_reason, case.case_id
                )
            else:
                self.assertEqual(
                    "expected_failure", case.outcome, case.case_id
                )
                sqlstate, reason = _SFV_FAILURE_SQLSTATE[pair]
                self.assertEqual(
                    sqlstate, case.expected_sqlstate, case.case_id
                )
                self.assertEqual(
                    reason, case.expected_failure_reason, case.case_id
                )

    def test_privilege_negative_fires_for_non_owner(self) -> None:
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            if a["privilege_level"] == "non_owner":
                self.assertEqual(
                    "expected_failure", case.outcome, case.case_id
                )
                self.assertEqual(
                    "42501", case.expected_sqlstate, case.case_id
                )
                self.assertEqual(
                    "insufficient_cast_privilege",
                    case.expected_failure_reason,
                    case.case_id,
                )

    def test_branch_grammar_and_consumer_action_are_consistent(self) -> None:
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            branch = a["statement_branch"]
            self.assertEqual(
                _BRANCH_GRAMMAR[branch], a["grammar_branch"], case.case_id
            )
            self.assertEqual(
                _BRANCH_FIXED_ACTION[branch],
                a["target_action"],
                case.case_id,
            )
            self.assertEqual(
                _BRANCH_FIXED_ACTION[branch],
                case.consumer_action_id,
                case.case_id,
            )

    def test_held_constant_factors_stay_at_baseline(self) -> None:
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            for factor, value in _HELD_CONSTANT.items():
                self.assertEqual(value, a[factor], (case.case_id, factor))

    def test_every_crossed_factor_value_is_witnessed(self) -> None:
        witnessed: dict[str, set[str]] = {
            factor: set() for factor in _CROSSED_AXES
        }
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            for factor in _CROSSED_AXES:
                witnessed[factor].add(a[factor])
        for factor, values in _CROSSED_AXES.items():
            self.assertEqual(
                set(values),
                witnessed[factor],
                f"factor {factor}: missing {set(values) - witnessed[factor]}",
            )

    def test_verification_and_cleanup_modes_are_both_crossed(self) -> None:
        vm_counts: Counter[str] = Counter()
        cm_counts: Counter[str] = Counter()
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            vm_counts[a["verification_mode"]] += 1
            cm_counts[a["cleanup_mode"]] += 1
        self.assertEqual(
            set(_CROSSED_AXES["verification_mode"]), set(vm_counts)
        )
        self.assertEqual(
            set(_CROSSED_AXES["cleanup_mode"]), set(cm_counts)
        )
        self.assertEqual(
            _EXTENSION_COUNT // len(_CROSSED_AXES["verification_mode"]),
            vm_counts["pg_cast_catalog_query"],
        )
        self.assertEqual(
            _EXTENSION_COUNT // len(_CROSSED_AXES["cleanup_mode"]),
            cm_counts["DROP_CAST_IF_EXISTS"],
        )

    def test_derivation_records_are_complete_and_unique(self) -> None:
        ids = [case.derivation_id for case in self.plan.cases]
        self.assertEqual(_EXTENSION_COUNT, len(set(ids)))
        for case in self.plan.cases:
            self.assertTrue(case.derivation_id, case.case_id)
            self.assertTrue(case.derived_from_combination_group, case.case_id)
            self.assertTrue(case.derivation_reason, case.case_id)

    def test_plan_is_deterministic(self) -> None:
        again = build_drop_cast_factor_extension_plan(ROOT)
        self.assertEqual(
            self.plan.extension_multiset_sha256,
            again.extension_multiset_sha256,
        )
        self.assertEqual(
            tuple(c.case_id for c in self.plan.cases),
            tuple(c.case_id for c in again.cases),
        )
        for left, right in zip(self.plan.cases, again.cases):
            self.assertEqual(left.factor_assignment, right.factor_assignment)

    def test_extensions_do_not_collide_with_baseline_numbering(self) -> None:
        baseline = build_drop_cast_factor_loop_plan(ROOT)
        baseline_ids = {c.case_id for c in baseline.cases}
        extension_ids = {c.case_id for c in self.plan.cases}
        self.assertEqual(0, len(baseline_ids & extension_ids))
        self.assertEqual(_BASELINE_COUNT, len(baseline_ids))
        self.assertEqual(_EXTENSION_COUNT, len(extension_ids))

    def test_derived_combinations_yaml_parses_with_required_fields(
        self,
    ) -> None:
        doc = yaml.safe_load(self.plan.derived_combinations_yaml)
        self.assertIsInstance(doc, list)
        self.assertEqual(_EXTENSION_COUNT, len(doc))
        required = {
            "id",
            "title",
            "derived_from_combination_group",
            "derivation_reason",
            "factors",
            "expected_status_policy",
            "compatibility",
            "sql_shape",
            "verification",
            "cleanup",
        }
        for entry in doc:
            self.assertTrue(required.issubset(entry.keys()), entry.keys())


if __name__ == "__main__":
    unittest.main()
