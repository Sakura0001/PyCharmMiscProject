"""Tests for the bounded DROP LANGUAGE post-coverage extension expander.

The marginal factor-value-loop (``drop_language_factor_loop.py``) is the
frozen 35-case baseline (GRM 1 + SFV 32 + RISK 2).  This module's expander
adds the bounded post-coverage extension phase: cross-factor combinations
of the behaviour axes across the single official synopsis branch (at most one
failure-causing value per case, so attribution stays clean), with
``verification_mode`` crossed and ``cleanup_mode`` crossed so every declared
T6 value is exercised.  Each extension case carries a derivation record and
is marked ``is_extension = True``; it never replaces a required-baseline
obligation.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import unittest

import yaml

from pg_case_factory.drop_language_factor_extension import (
    DropLanguageFactorExtensionCase,
    DropLanguageFactorExtensionError,
    DropLanguageFactorExtensionPlan,
    build_drop_language_factor_extension_plan,
)
from pg_case_factory.drop_language_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_drop_language_factor_loop_plan,
)


ROOT = Path(__file__).resolve().parents[1]

_BASELINE_COUNT = 35
_EXTENSION_COUNT = 504
_TOTAL_COUNT = _BASELINE_COUNT + _EXTENSION_COUNT  # 539
_SUCCESS_EXTENSIONS = 192
_FAILURE_EXTENSIONS = 312
_EXTENSION_MULTISET_SHA256 = (
    "adb8b50d085f39908d5adec0b3e361821ebd5670923cd5c9a82caad6d1e7f6bb"
)

_PRIVILEGE_NEGATIVE = ("privilege_context", "non_owner")
_NOT_EXIST_NEGATIVE = ("target_object_state", "missing")
_DEPENDENCY_NEGATIVE_STATE = ("dependency_state", "has_dependents")
_DEPENDENCY_NEGATIVE_STATE_EWD = (
    "target_object_state",
    "exists_with_dependents",
)
_RESTRICT_VALUES = frozenset({"restrict_default", "restrict_explicit"})
_IF_EXISTS_OMITTED = "absent"

_CROSSED_AXES = {
    "statement_branch": ("branch_1",),
    "target_action": ("drop_language",),
    "privilege_context": ("non_owner", "owner", "superuser"),
    "target_object_state": ("exists", "missing", "exists_with_dependents"),
    "if_exists_clause": ("absent", "present"),
    "cascade_clause": ("cascade", "restrict_default", "restrict_explicit"),
    "dependency_state": ("has_dependents", "no_dependents"),
    "verification_mode": ("catalog_query", "effect_query", "error_assertion"),
    "cleanup_mode": ("drop_objects", "reset_state"),
}

_HELD_CONSTANT = {
    "cascade_behavior": "cascade_succeeds",
    "invalid_combination": "none",
    "name_shape": "plain_identifier",
    "ownership_boundary": "owner",
}

_BRANCH_GRAMMAR = {"branch_1": "branch_1"}
_BRANCH_FIXED_ACTION = {"branch_1": "drop_language"}


def _privilege_failure_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("privilege_context") == "non_owner"


def _not_exist_failure_fires(assignment: dict[str, str]) -> bool:
    return (
        assignment.get("target_object_state") == "missing"
        and assignment.get("if_exists_clause") == _IF_EXISTS_OMITTED
    )


def _dependency_failure_fires(assignment: dict[str, str]) -> bool:
    has_dependents = (
        assignment.get("dependency_state") == "has_dependents"
        or assignment.get("target_object_state") == "exists_with_dependents"
    )
    return (
        has_dependents
        and assignment.get("cascade_clause") in _RESTRICT_VALUES
    )


def _failure_unit_count(assignment: dict[str, str]) -> int:
    count = 0
    if _privilege_failure_fires(assignment):
        count += 1
    if _not_exist_failure_fires(assignment):
        count += 1
    if _dependency_failure_fires(assignment):
        count += 1
    return count


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    if _privilege_failure_fires(assignment):
        return _PRIVILEGE_NEGATIVE
    if _not_exist_failure_fires(assignment):
        return _NOT_EXIST_NEGATIVE
    if _dependency_failure_fires(assignment):
        if assignment.get("dependency_state") == "has_dependents":
            return _DEPENDENCY_NEGATIVE_STATE
        return _DEPENDENCY_NEGATIVE_STATE_EWD
    return None


class DropLanguageFactorExtensionPlanTest(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_drop_language_factor_extension_plan(ROOT)

    def test_builds_frozen_extension_count_with_no_truncation(self) -> None:
        self.assertIsInstance(self.plan, DropLanguageFactorExtensionPlan)
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
        self.assertEqual("DROPLANGUAGE00036", first.case_id)
        self.assertEqual(f"DROPLANGUAGE{_TOTAL_COUNT:05d}", last.case_id)
        self.assertEqual("DROPLANGUAGE00036.sql", first.sql_filename)
        self.assertEqual(
            f"DROPLANGUAGE{_TOTAL_COUNT:05d}.sql", last.sql_filename
        )
        self.assertEqual("droplanguage_00036_", first.object_prefix)
        self.assertEqual(
            f"droplanguage_{_TOTAL_COUNT:05d}_", last.object_prefix
        )

    def test_every_case_is_marked_extension_with_full_assignment(self) -> None:
        for case in self.plan.cases:
            self.assertIsInstance(case, DropLanguageFactorExtensionCase)
            self.assertTrue(case.is_extension, case.case_id)
            self.assertEqual(15, len(case.factor_assignment), case.case_id)
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
            if a["privilege_context"] == "non_owner":
                self.assertEqual(
                    "expected_failure", case.outcome, case.case_id
                )
                self.assertEqual(
                    "42501", case.expected_sqlstate, case.case_id
                )
                self.assertEqual(
                    "insufficient_language_privilege",
                    case.expected_failure_reason,
                    case.case_id,
                )

    def test_not_exist_negative_fires_without_if_exists(self) -> None:
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            if a["privilege_context"] == "non_owner":
                continue
            if (
                a["target_object_state"] == "missing"
                and a["if_exists_clause"] == "absent"
            ):
                self.assertEqual(
                    "expected_failure", case.outcome, case.case_id
                )
                self.assertEqual(
                    "42704", case.expected_sqlstate, case.case_id
                )

    def test_dependency_negative_fires_under_restrict(self) -> None:
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            if a["privilege_context"] == "non_owner":
                continue
            if (
                a["target_object_state"] == "missing"
                and a["if_exists_clause"] == "absent"
            ):
                continue
            has_dependents = (
                a["dependency_state"] == "has_dependents"
                or a["target_object_state"] == "exists_with_dependents"
            )
            if not has_dependents:
                continue
            if a["cascade_clause"] == "cascade":
                self.assertEqual("success", case.outcome, case.case_id)
            else:
                self.assertEqual(
                    "expected_failure", case.outcome, case.case_id
                )
                self.assertEqual(
                    "2BP01", case.expected_sqlstate, case.case_id
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
            vm_counts["catalog_query"],
        )
        self.assertEqual(
            _EXTENSION_COUNT // len(_CROSSED_AXES["cleanup_mode"]),
            cm_counts["drop_objects"],
        )

    def test_derivation_records_are_complete_and_unique(self) -> None:
        ids = [case.derivation_id for case in self.plan.cases]
        self.assertEqual(_EXTENSION_COUNT, len(set(ids)))
        for case in self.plan.cases:
            self.assertTrue(case.derivation_id, case.case_id)
            self.assertTrue(case.derived_from_combination_group, case.case_id)
            self.assertTrue(case.derivation_reason, case.case_id)

    def test_plan_is_deterministic(self) -> None:
        again = build_drop_language_factor_extension_plan(ROOT)
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
        baseline = build_drop_language_factor_loop_plan(ROOT)
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
