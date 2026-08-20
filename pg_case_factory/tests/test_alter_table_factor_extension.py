"""Tests for the bounded ALTER TABLE post-coverage extension expander."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import unittest

import yaml

from pg_case_factory.alter_table_factor_extension import (
    AlterTableFactorExtensionCase,
    AlterTableFactorExtensionPlan,
    build_alter_table_factor_extension_plan,
    _failure_unit_count,
    _present_failure_pair,
    _privilege_cluster_fires,
    _owner_privilege_failure,
)
from pg_case_factory.alter_table_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_alter_table_factor_loop_plan,
)


ROOT = Path(__file__).resolve().parents[1]

_BASELINE_COUNT = 207
_EXTENSION_COUNT = 4340
_TOTAL_COUNT = _BASELINE_COUNT + _EXTENSION_COUNT  # 4547
_SUCCESS_EXTENSIONS = 1560
_FAILURE_EXTENSIONS = 2780

_CROSSED_BEHAVIOUR_NEGATIVES = frozenset(
    {
        ("new_name_shape", "duplicate"),
        ("schema_dependency", "schema_not_exists"),
        ("role_dependency", "owner_role_not_exists"),
    }
)
_PRIVILEGE_CLUSTER_VALUES = frozenset({"non_owner_no_privilege"})
_SESSION_USER_ESCAPE = "current_role_variants"
_OWNER_TARGET_REQUIRES_MEMBERSHIP = frozenset({"owner_role_exists"})

_BRANCH_1_ACTION = "branch_1_action"
_BRANCH_2_RENAME_COLUMN = "branch_2_rename_column"
_BRANCH_4_RENAME_TABLE = "branch_4_rename_table"
_BRANCH_5_SET_SCHEMA = "branch_5_set_schema"

_CONSUMER_BRANCH = {
    "add_column": _BRANCH_1_ACTION,
    "drop_column": _BRANCH_1_ACTION,
    "alter_column_type": _BRANCH_1_ACTION,
    "owner_to": _BRANCH_1_ACTION,
    "rename_column": _BRANCH_2_RENAME_COLUMN,
    "rename_table": _BRANCH_4_RENAME_TABLE,
    "set_schema": _BRANCH_5_SET_SCHEMA,
}

_CROSSED_AXES = {
    "if_exists_clause": ("absent", "present"),
    "if_not_exists_clause": ("absent", "present"),
    "cascade_restrict": ("CASCADE", "RESTRICT", "absent"),
    "table_name_shape": (
        "simple", "quoted", "schema_qualified",
    ),
    "column_type_conversion": (
        "compatible_no_using",
        "compatible_with_collation",
        "incompatible_with_using",
    ),
    "role_dependency": (
        "current_role_variants",
        "owner_role_exists",
        "owner_role_not_exists",
    ),
    "new_name_shape": ("simple", "quoted", "duplicate"),
    "schema_dependency": ("schema_exists", "schema_not_exists"),
    "privilege_level": (
        "superuser", "table_owner", "non_owner_no_privilege",
    ),
    "verification_mode": (
        "pg_class_catalog_query",
        "pg_attribute_query",
        "pg_constraint_query",
        "information_schema_query",
        "SELECT_inspection",
    ),
    "cleanup_mode": (
        "DROP_TABLE_IF_EXISTS",
        "DROP_TABLE_CASCADE",
        "ALTER_TABLE_REVERT",
        "RESET_STATE",
    ),
}


class AlterTableFactorExtensionPlanTest(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_alter_table_factor_extension_plan(ROOT)

    def test_builds_frozen_extension_count_with_no_truncation(self) -> None:
        self.assertIsInstance(self.plan, AlterTableFactorExtensionPlan)
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
        self.assertEqual("ALTERTABLE00208", first.case_id)
        self.assertEqual(
            f"ALTERTABLE{_TOTAL_COUNT:05d}", last.case_id
        )
        self.assertEqual("ALTERTABLE00208.sql", first.sql_filename)
        self.assertEqual(
            f"ALTERTABLE{_TOTAL_COUNT:05d}.sql", last.sql_filename
        )
        self.assertEqual("altertable_00208_", first.object_prefix)
        self.assertEqual(
            f"altertable_{_TOTAL_COUNT:05d}_", last.object_prefix
        )

    def test_every_case_is_marked_extension_with_full_assignment(self) -> None:
        for case in self.plan.cases:
            self.assertIsInstance(case, AlterTableFactorExtensionCase)
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
            if a.get("role_dependency") == _SESSION_USER_ESCAPE:
                if _failure_unit_count(a) == 0:
                    self.assertEqual("success", case.outcome, case.case_id)

    def test_branch_grammar_and_consumer_action_are_consistent(self) -> None:
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            consumer = a.get("target_action", "")
            if consumer in _CONSUMER_BRANCH:
                expected_branch = _CONSUMER_BRANCH[consumer]
                self.assertEqual(
                    expected_branch, a["statement_branch"], case.case_id
                )
                self.assertEqual(
                    expected_branch, a["grammar_branch"], case.case_id
                )
                self.assertEqual(
                    consumer, case.consumer_action_id, case.case_id
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
        again = build_alter_table_factor_extension_plan(ROOT)
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
        baseline = build_alter_table_factor_loop_plan(ROOT)
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
