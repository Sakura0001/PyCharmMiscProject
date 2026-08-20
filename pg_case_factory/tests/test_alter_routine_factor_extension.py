"""Tests for the bounded ALTER ROUTINE post-coverage extension expander."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import unittest

import yaml

from pg_case_factory.alter_routine_factor_extension import (
    AlterRoutineFactorExtensionCase,
    AlterRoutineFactorExtensionError,
    AlterRoutineFactorExtensionPlan,
    build_alter_routine_factor_extension_plan,
)
from pg_case_factory.alter_routine_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_alter_routine_factor_loop_plan,
)


ROOT = Path(__file__).resolve().parents[1]

_BASELINE_COUNT = 115
_EXTENSION_COUNT = 5440
_TOTAL_COUNT = _BASELINE_COUNT + _EXTENSION_COUNT  # 5555
_SUCCESS_EXTENSIONS = 1560
_FAILURE_EXTENSIONS = 3880

_CROSSED_BEHAVIOUR_NEGATIVES = frozenset(
    {
        ("routine_state", "non_existent"),
        ("new_name_shape", "existing_name_conflict"),
        ("schema_change", "nonexistent_schema"),
        ("extension_dependency", "depends_on_nonexistent_extension"),
    }
)
_PRIVILEGE_CLUSTER_VALUES = frozenset(
    {"non_owner_with_grant_option", "non_owner_no_privilege"}
)

_CROSSED_AXES = {
    "statement_branch": (
        "branch_action",
        "branch_rename",
        "branch_owner_to",
        "branch_set_schema",
        "branch_depends_on_extension",
    ),
    "target_action": (
        "security_invoker",
        "security_definer",
        "volatile",
        "set_config_parameter",
        "leakproof",
        "rename",
        "owner",
        "set_schema",
        "depends_on_extension",
    ),
    "routine_type": ("function", "procedure", "aggregate"),
    "routine_state": ("exists", "non_existent"),
    "executor_privilege": (
        "superuser",
        "owner_of_routine",
        "non_owner_with_grant_option",
        "non_owner_no_privilege",
    ),
    "restrict_clause": ("omitted", "restrict"),
    "new_name_shape": ("simple_name", "quoted_name", "existing_name_conflict"),
    "owner_to_shape": (
        "explicit_role_name",
        "current_role_keyword",
        "current_user_keyword",
        "session_user_keyword",
    ),
    "schema_change": ("existing_schema", "nonexistent_schema"),
    "extension_dependency": (
        "depends_on_existing_extension",
        "no_depends_removing_dependency",
        "depends_on_nonexistent_extension",
    ),
    "verification_mode": (
        "pg_proc_catalog",
        "pg_aggregate_catalog",
        "effect_query",
        "error_assertion",
    ),
    "cleanup_mode": (
        "drop_routine",
        "drop_function",
        "drop_procedure",
        "drop_aggregate",
        "reset_config_parameter",
    ),
}

_HELD_CONSTANT = {
    "action_list_cardinality": "one_action",
    "set_assignment_form": "to_value",
    "external_keyword": "omitted",
    "depends_polarity": "depends",
}

_BRANCH_GRAMMAR = {
    "branch_action": "branch_action_form",
    "branch_rename": "branch_rename",
    "branch_owner_to": "branch_owner",
    "branch_set_schema": "branch_set_schema",
    "branch_depends_on_extension": "branch_depends_extension",
}
_BRANCH_FIXED_ACTION = {
    "branch_rename": "rename",
    "branch_owner_to": "owner",
    "branch_set_schema": "set_schema",
    "branch_depends_on_extension": "depends_on_extension",
}


def _owner_target_requires_membership(
    routine_type: str, owner_to_shape: str
) -> bool:
    """Resolution-aware SESSION_USER escape (the key alter_routine gotcha).

    SESSION_USER escapes (False) for function/aggregate; requires membership
    (True) for procedure.  CURRENT_ROLE / CURRENT_USER always require
    membership.  explicit_role_name always requires membership.
    """
    if owner_to_shape == "explicit_role_name":
        return True
    if owner_to_shape in ("current_role_keyword", "current_user_keyword"):
        return True
    if owner_to_shape == "session_user_keyword":
        return routine_type == "procedure"
    return False


def _leakproof_wall_fires(assignment: dict[str, str]) -> bool:
    if assignment.get("target_action") != "leakproof":
        return False
    return assignment.get("executor_privilege") != "superuser"


def _owner_membership_wall_fires(assignment: dict[str, str]) -> bool:
    if assignment.get("executor_privilege") != "owner_of_routine":
        return False
    if assignment.get("target_action") != "owner":
        return False
    routine_type = assignment.get("routine_type", "function")
    owner_to_shape = assignment.get("owner_to_shape", "explicit_role_name")
    return _owner_target_requires_membership(routine_type, owner_to_shape)


def _privilege_cluster_fires(assignment: dict[str, str]) -> bool:
    level = assignment.get("executor_privilege")
    if level not in _PRIVILEGE_CLUSTER_VALUES:
        return False
    return True


def _failure_unit_count(assignment: dict[str, str]) -> int:
    cluster = 1 if _privilege_cluster_fires(assignment) else 0
    leakproof = 1 if _leakproof_wall_fires(assignment) else 0
    membership = 1 if _owner_membership_wall_fires(assignment) else 0
    negatives = sum(
        1
        for factor, value in _CROSSED_BEHAVIOUR_NEGATIVES
        if assignment.get(factor) == value
    )
    return cluster + leakproof + membership + negatives


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    if _leakproof_wall_fires(assignment):
        return ("target_action", "leakproof_under_routine_owner")
    if _owner_membership_wall_fires(assignment):
        return ("owner_to_shape", "membership_required_under_routine_owner")
    if _privilege_cluster_fires(assignment):
        level = assignment.get("executor_privilege")
        return ("executor_privilege", level)
    for neg_factor, neg_value in _CROSSED_BEHAVIOUR_NEGATIVES:
        if assignment.get(neg_factor) == neg_value:
            return (neg_factor, neg_value)
    return None


class AlterRoutineFactorExtensionPlanTest(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_alter_routine_factor_extension_plan(ROOT)

    def test_builds_frozen_extension_count_with_no_truncation(self) -> None:
        self.assertIsInstance(self.plan, AlterRoutineFactorExtensionPlan)
        self.assertEqual(_EXTENSION_COUNT, len(self.plan.cases))
        self.assertEqual(_EXTENSION_COUNT, self.plan.raw_combination_count)
        self.assertEqual(0, self.plan.dropped_count)

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
        self.assertEqual("ALTERROUTINE00116", first.case_id)
        self.assertEqual(f"ALTERROUTINE{_TOTAL_COUNT:05d}", last.case_id)
        self.assertEqual("ALTERROUTINE00116.sql", first.sql_filename)
        self.assertEqual(
            f"ALTERROUTINE{_TOTAL_COUNT:05d}.sql", last.sql_filename
        )
        self.assertEqual("alterroutine_00116_", first.object_prefix)
        self.assertEqual(
            f"alterroutine_{_TOTAL_COUNT:05d}_", last.object_prefix
        )

    def test_every_case_is_marked_extension_with_full_assignment(self) -> None:
        for case in self.plan.cases:
            self.assertIsInstance(case, AlterRoutineFactorExtensionCase)
            self.assertTrue(case.is_extension, case.case_id)
            self.assertEqual(23, len(case.factor_assignment), case.case_id)
            keys = [k for k, _ in case.factor_assignment]
            self.assertEqual(len(keys), len(set(keys)), case.case_id)
            self.assertEqual(
                tuple(sorted(case.factor_assignment)), case.factor_assignment
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

    def test_expected_sqlstate_matches_present_failure_pair(self) -> None:
        for case in self.plan.cases:
            assignment = dict(case.factor_assignment)
            pair = _present_failure_pair(assignment)
            if pair is None:
                self.assertEqual("success", case.outcome, case.case_id)
                self.assertEqual("00000", case.expected_sqlstate, case.case_id)
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

    def test_session_user_escapes_for_function_and_aggregate(self) -> None:
        # SESSION_USER escapes the membership wall for function/aggregate
        # (the key alter_routine gotcha — INVERTS alter_function where
        # SESSION_USER requires membership for functions).
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            if (
                a.get("owner_to_shape") == "session_user_keyword"
                and a.get("routine_type") in ("function", "aggregate")
                and a.get("executor_privilege") == "owner_of_routine"
                and a.get("target_action") == "owner"
            ):
                # The membership wall must not fire for function/aggregate.
                self.assertFalse(
                    _owner_membership_wall_fires(a), case.case_id
                )
                # If no other failure unit fires, the case is a success.
                if _failure_unit_count(a) == 0:
                    self.assertEqual("success", case.outcome, case.case_id)

    def test_session_user_requires_membership_for_procedure(self) -> None:
        # SESSION_USER requires membership for procedures (INVERTS
        # alter_procedure where SESSION_USER escapes for procedures).
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            if (
                a.get("owner_to_shape") == "session_user_keyword"
                and a.get("routine_type") == "procedure"
                and a.get("executor_privilege") == "owner_of_routine"
                and a.get("target_action") == "owner"
            ):
                self.assertEqual(
                    "expected_failure", case.outcome, case.case_id
                )

    def test_branch_grammar_and_consumer_action_are_consistent(self) -> None:
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            branch = a["statement_branch"]
            self.assertEqual(
                _BRANCH_GRAMMAR[branch], a["grammar_branch"], case.case_id
            )
            if branch == "branch_action":
                self.assertEqual(
                    a["target_action"], case.consumer_action_id, case.case_id
                )
            else:
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

    def test_derivation_records_are_complete_and_unique(self) -> None:
        ids = [case.derivation_id for case in self.plan.cases]
        self.assertEqual(_EXTENSION_COUNT, len(set(ids)))
        for case in self.plan.cases:
            self.assertTrue(case.derivation_id, case.case_id)
            self.assertTrue(case.derived_from_combination_group, case.case_id)
            self.assertTrue(case.derivation_reason, case.case_id)

    def test_plan_is_deterministic(self) -> None:
        again = build_alter_routine_factor_extension_plan(ROOT)
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
        baseline = build_alter_routine_factor_loop_plan(ROOT)
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
