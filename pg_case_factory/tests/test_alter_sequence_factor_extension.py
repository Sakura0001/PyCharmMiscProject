"""Tests for the bounded ALTER SEQUENCE post-coverage extension expander."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import unittest

import yaml

from pg_case_factory.alter_sequence_factor_extension import (
    AlterSequenceFactorExtensionCase,
    AlterSequenceFactorExtensionPlan,
    build_alter_sequence_factor_extension_plan,
    _failure_unit_count,
    _present_failure_pair,
    _privilege_cluster_fires,
    _owner_privilege_failure,
)
from pg_case_factory.alter_sequence_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_alter_sequence_factor_loop_plan,
)


ROOT = Path(__file__).resolve().parents[1]

_BASELINE_COUNT = 79
_EXTENSION_COUNT = 28512
_TOTAL_COUNT = _BASELINE_COUNT + _EXTENSION_COUNT  # 28591
_SUCCESS_EXTENSIONS = 16992
_FAILURE_EXTENSIONS = 11520

_CROSSED_BEHAVIOUR_NEGATIVES = frozenset(
    {
        ("new_owner_shape", "non_existing_role"),
        ("new_schema_name", "non_existing_schema"),
        ("owned_by_table_dependency", "different_owner"),
        ("owned_by_table_dependency", "different_schema"),
    }
)
_PRIVILEGE_CLUSTER_VALUES = frozenset({"non_owner"})
_SESSION_USER_ESCAPE = "SESSION_USER"
_OWNER_TARGET_REQUIRES_MEMBERSHIP = frozenset({"new_owner_role"})

_BRANCH_ALTER_PARAMETERS = "branch_alter_parameters"
_BRANCH_SET_LOGGED_UNLOGGED = "branch_set_logged_unlogged"
_BRANCH_OWNER = "branch_owner"
_BRANCH_RENAME = "branch_rename"
_BRANCH_SET_SCHEMA = "branch_set_schema"

_BRANCH_GRAMMAR = {
    _BRANCH_ALTER_PARAMETERS: _BRANCH_ALTER_PARAMETERS,
    _BRANCH_SET_LOGGED_UNLOGGED: _BRANCH_SET_LOGGED_UNLOGGED,
    _BRANCH_OWNER: _BRANCH_OWNER,
    _BRANCH_RENAME: _BRANCH_RENAME,
    _BRANCH_SET_SCHEMA: _BRANCH_SET_SCHEMA,
}
_BRANCH_FIXED_ACTION = {
    _BRANCH_ALTER_PARAMETERS: "alter_parameters",
    _BRANCH_SET_LOGGED_UNLOGGED: "set_logged_unlogged",
    _BRANCH_OWNER: "owner",
    _BRANCH_RENAME: "rename",
    _BRANCH_SET_SCHEMA: "set_schema",
}

_CROSSED_AXES = {
    "statement_branch": (
        _BRANCH_ALTER_PARAMETERS,
        _BRANCH_SET_LOGGED_UNLOGGED,
        _BRANCH_OWNER,
        _BRANCH_RENAME,
        _BRANCH_SET_SCHEMA,
    ),
    "alter_parameter_type": (
        "change_data_type", "change_increment", "change_minmax",
        "change_start", "restart_with", "change_cache",
        "change_cycle", "change_owned_by", "none_parameter",
    ),
    "logged_unlogged_clause": ("LOGGED", "UNLOGGED"),
    "role_specification": (
        "new_owner_role", "CURRENT_ROLE", "CURRENT_USER", "SESSION_USER",
    ),
    "if_exists_clause": ("absent", "present"),
    "sequence_name_shape": (
        "simple", "quoted", "reserved_word", "schema_qualified",
    ),
    "new_data_type": ("smallint", "integer", "bigint"),
    "new_owner_shape": ("existing_role", "non_existing_role"),
    "new_schema_name": ("existing_schema", "non_existing_schema"),
    "privilege_level": ("superuser", "sequence_owner", "non_owner"),
    "owned_by_table_dependency": (
        "same_owner_same_schema", "different_owner", "different_schema",
    ),
    "owner_change_privilege": ("can_SET_ROLE", "cannot_SET_ROLE"),
    "schema_privilege": ("has_CREATE", "no_CREATE"),
}


class AlterSequenceFactorExtensionPlanTest(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_alter_sequence_factor_extension_plan(ROOT)

    def test_builds_frozen_extension_count_with_no_truncation(self) -> None:
        self.assertIsInstance(self.plan, AlterSequenceFactorExtensionPlan)
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
        self.assertEqual("ALTERSEQUENCE00080", first.case_id)
        self.assertEqual(
            f"ALTERSEQUENCE{_TOTAL_COUNT:05d}", last.case_id
        )
        self.assertEqual("ALTERSEQUENCE00080.sql", first.sql_filename)
        self.assertEqual(
            f"ALTERSEQUENCE{_TOTAL_COUNT:05d}.sql", last.sql_filename
        )
        self.assertEqual("altersequence_00080_", first.object_prefix)
        self.assertEqual(
            f"altersequence_{_TOTAL_COUNT:05d}_", last.object_prefix
        )

    def test_every_case_is_marked_extension_with_full_assignment(self) -> None:
        for case in self.plan.cases:
            self.assertIsInstance(case, AlterSequenceFactorExtensionCase)
            self.assertTrue(case.is_extension, case.case_id)
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

    def test_session_user_escapes_privilege_boundary(self) -> None:
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            if a.get("role_specification") == _SESSION_USER_ESCAPE:
                if _failure_unit_count(a) == 0:
                    self.assertEqual("success", case.outcome, case.case_id)

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

    def test_every_crossed_factor_value_is_witnessed(self) -> None:
        witnessed: dict[str, set[str]] = {
            factor: set() for factor in _CROSSED_AXES
        }
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            for factor in _CROSSED_AXES:
                if factor in a:
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
        again = build_alter_sequence_factor_extension_plan(ROOT)
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
        baseline = build_alter_sequence_factor_loop_plan(ROOT)
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
