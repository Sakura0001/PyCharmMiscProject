"""Tests for the bounded ALTER PUBLICATION post-coverage extension expander."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import unittest

import yaml

from pg_case_factory.alter_publication_factor_extension import (
    AlterPublicationFactorExtensionCase,
    AlterPublicationFactorExtensionError,
    AlterPublicationFactorExtensionPlan,
    build_alter_publication_factor_extension_plan,
)
from pg_case_factory.alter_publication_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_alter_publication_factor_loop_plan,
)


ROOT = Path(__file__).resolve().parents[1]

_BASELINE_COUNT = 93
_EXTENSION_COUNT = 19458
_TOTAL_COUNT = _BASELINE_COUNT + _EXTENSION_COUNT  # 19551
_SUCCESS_EXTENSIONS = 5292
_FAILURE_EXTENSIONS = 14166

_CROSSED_BEHAVIOUR_NEGATIVES = frozenset(
    {
        ("publication_state", "non_existent"),
        ("publication_state", "exists_as_for_all_tables"),
        ("table_dependency", "table_not_exists"),
        ("schema_dependency", "schema_not_exists"),
        ("table_name_shape", "nonexistent_table"),
        ("schema_name_shape", "nonexistent_schema"),
        ("publication_name_shape", "non_existent_name"),
        ("new_owner_shape", "nonexistent_role"),
        ("new_name_shape", "existing_name_conflict"),
    }
)
_PRIVILEGE_CLUSTER_VALUES = frozenset({"non_owner_no_privilege"})
_OWNER_TARGET_REQUIRES_MEMBERSHIP = frozenset(
    {"explicit_role_name", "current_role_keyword", "current_user_keyword"}
)
_SESSION_USER_ESCAPE = "session_user_keyword"

_BRANCH_DROP = "branch_drop"
_TABLE_OPERATIONS = frozenset(
    {"add_table", "set_table", "drop_table"}
)
_SCHEMA_OPERATIONS = frozenset(
    {"add_tables_in_schema", "set_tables_in_schema", "drop_tables_in_schema"}
)

# GRM-axis modifiers are held constant at their canonical default across every
# extension case (they are covered one-per-value by the marginal baseline).
_HELD_CONSTANT = {
    "only_keyword": "absent",
    "star_marker": "absent",
    "object_list_cardinality": "one_object",
    "parameter_assignment_form": "equals_value",
    "cleanup_mode": "drop_publication",
    "expected_status": "success",
    "grammar_branch": "branch_add",
    "target_action": "add_object",
}

_CROSSED_AXES = {
    "statement_branch": (
        "branch_add",
        "branch_set_object",
        "branch_drop",
        "branch_set_parameter",
        "branch_owner_to",
        "branch_rename",
    ),
    "add_set_drop_operation": (
        "add_table",
        "add_tables_in_schema",
        "set_table",
        "set_tables_in_schema",
        "drop_table",
        "drop_tables_in_schema",
    ),
    "publication_parameter": (
        "publish_insert_only",
        "publish_all_operations",
        "publish_via_partition_root",
        "multiple_parameters",
    ),
    "owner_to_clause": (
        "explicit_role_name",
        "current_role_keyword",
        "current_user_keyword",
        "session_user_keyword",
    ),
    "column_filter": (
        "no_column_filter",
        "single_column_filter",
        "multiple_column_filter",
    ),
    "where_clause": ("no_where", "simple_where_condition"),
    "publication_name_shape": (
        "simple_name",
        "quoted_name",
        "non_existent_name",
    ),
    "table_name_shape": (
        "simple_name",
        "schema_qualified_name",
        "quoted_name",
        "nonexistent_table",
    ),
    "schema_name_shape": (
        "simple_name",
        "current_schema_keyword",
        "quoted_name",
        "nonexistent_schema",
    ),
    "new_name_shape": (
        "simple_name",
        "quoted_name",
        "existing_name_conflict",
    ),
    "new_owner_shape": ("existing_role", "nonexistent_role"),
    "executor_privilege": (
        "superuser",
        "owner_of_publication",
        "non_owner_no_privilege",
    ),
    "table_dependency": ("table_exists", "table_not_exists"),
    "schema_dependency": ("schema_exists", "schema_not_exists"),
    "verification_mode": (
        "pg_publication_catalog",
        "pg_publication_tables_catalog",
        "error_assertion",
    ),
}

_BRANCH_GRAMMAR = {
    "branch_add": "branch_add",
    "branch_set_object": "branch_set_object",
    "branch_drop": "branch_drop",
    "branch_set_parameter": "branch_set_parameter",
    "branch_owner_to": "branch_owner_to",
    "branch_rename": "branch_rename",
}
_BRANCH_FIXED_ACTION = {
    "branch_add": "add_object",
    "branch_set_object": "set_object",
    "branch_drop": "drop_object",
    "branch_set_parameter": "set_parameter",
    "branch_owner_to": "owner",
    "branch_rename": "rename",
}


def _owner_privilege_failure(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    if assignment.get("executor_privilege") != "owner_of_publication":
        return None
    target_action = assignment.get("target_action")
    if (
        target_action == "owner"
        and assignment.get("owner_to_clause")
        in _OWNER_TARGET_REQUIRES_MEMBERSHIP
    ):
        return ("owner_to_clause", "membership_required_under_owner")
    return None


def _privilege_cluster_fires(assignment: dict[str, str]) -> bool:
    level = assignment.get("executor_privilege")
    if level not in _PRIVILEGE_CLUSTER_VALUES:
        return False
    if assignment.get("owner_to_clause") == _SESSION_USER_ESCAPE:
        return False
    return True


def _is_table_op(assignment: dict[str, str]) -> bool:
    return assignment.get("add_set_drop_operation") in _TABLE_OPERATIONS


def _is_schema_op(assignment: dict[str, str]) -> bool:
    return assignment.get("add_set_drop_operation") in _SCHEMA_OPERATIONS


def _applicable_negative(
    factor: str, value: str, assignment: dict[str, str]
) -> bool:
    """Whether a crossed behaviour-negative actually fires for this case."""

    if assignment.get(factor) != value:
        return False
    branch = assignment.get("grammar_branch")
    # exists_as_for_all_tables only fails on the DROP branch; on ADD / SET
    # it is a valid success (the publication exists and is alterable).
    if (factor, value) == ("publication_state", "exists_as_for_all_tables"):
        return branch == _BRANCH_DROP
    # Table negatives only apply to TABLE operations; schema negatives only
    # to TABLES-IN-SCHEMA operations.
    if factor in ("table_dependency", "table_name_shape"):
        return _is_table_op(assignment)
    if factor in ("schema_dependency", "schema_name_shape"):
        return _is_schema_op(assignment)
    return True


def _failure_unit_count(assignment: dict[str, str]) -> int:
    cluster = 1 if _privilege_cluster_fires(assignment) else 0
    owner_priv = 1 if _owner_privilege_failure(assignment) else 0
    negatives = sum(
        1
        for pair in _CROSSED_BEHAVIOUR_NEGATIVES
        if _applicable_negative(pair[0], pair[1], assignment)
    )
    return cluster + owner_priv + negatives


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    pair = _owner_privilege_failure(assignment)
    if pair is not None:
        return pair
    if _privilege_cluster_fires(assignment):
        level = assignment.get("executor_privilege")
        return ("executor_privilege", level)
    for neg_factor, neg_value in _CROSSED_BEHAVIOUR_NEGATIVES:
        if _applicable_negative(neg_factor, neg_value, assignment):
            return (neg_factor, neg_value)
    return None


class AlterPublicationFactorExtensionPlanTest(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_alter_publication_factor_extension_plan(ROOT)

    def test_builds_frozen_extension_count_with_no_truncation(self) -> None:
        self.assertIsInstance(self.plan, AlterPublicationFactorExtensionPlan)
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
        self.assertEqual("ALTERPUBLICATION00094", first.case_id)
        self.assertEqual(
            f"ALTERPUBLICATION{_TOTAL_COUNT:05d}", last.case_id
        )
        self.assertEqual("ALTERPUBLICATION00094.sql", first.sql_filename)
        self.assertEqual(
            f"ALTERPUBLICATION{_TOTAL_COUNT:05d}.sql", last.sql_filename
        )
        self.assertEqual("alterpublication_00094_", first.object_prefix)
        self.assertEqual(
            f"alterpublication_{_TOTAL_COUNT:05d}_", last.object_prefix
        )

    def test_every_case_is_marked_extension_with_full_assignment(self) -> None:
        for case in self.plan.cases:
            self.assertIsInstance(case, AlterPublicationFactorExtensionCase)
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
        # SESSION_USER is a permitted no-op transfer (PG 18.4 allows even for
        # non-owners); the privilege boundary does not fire for it.
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            if a.get("owner_to_clause") == _SESSION_USER_ESCAPE:
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
        again = build_alter_publication_factor_extension_plan(ROOT)
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
        baseline = build_alter_publication_factor_loop_plan(ROOT)
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
