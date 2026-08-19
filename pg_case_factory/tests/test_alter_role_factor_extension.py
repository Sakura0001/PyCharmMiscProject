"""Tests for the bounded ALTER ROLE post-coverage extension expander."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import unittest

import yaml

from pg_case_factory.alter_role_factor_extension import (
    AlterRoleFactorExtensionCase,
    AlterRoleFactorExtensionError,
    AlterRoleFactorExtensionPlan,
    build_alter_role_factor_extension_plan,
)
from pg_case_factory.alter_role_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_alter_role_factor_loop_plan,
)


ROOT = Path(__file__).resolve().parents[1]

_BASELINE_COUNT = 108
_EXTENSION_COUNT = 1635
_TOTAL_COUNT = _BASELINE_COUNT + _EXTENSION_COUNT  # 1743
_SUCCESS_EXTENSIONS = 540
_FAILURE_EXTENSIONS = 1095

# The crossed behaviour-negative pair (the only non-privilege failure that
# is crossed in the extension).  All T5 negatives are owned one-per-value
# by the baseline and are never crossed here.
_CROSSED_BEHAVIOUR_NEGATIVES = frozenset(
    {
        ("new_name_shape", "existing_name_conflict"),
    }
)
_PRIVILEGE_FAILURE_LEVELS = frozenset(
    {"createrole_without_admin_option", "ordinary_role_other"}
)

# privilege_level values crossed in the extension.  ordinary_role_self is
# the self-password SUCCESS path and is excluded (owned one-per-value by the
# baseline).
_CROSSED_PRIVILEGE_LEVELS = (
    "superuser",
    "createrole_without_admin_option",
    "ordinary_role_other",
)

_SAFE_ROLE_NAME_SHAPES = ("simple_name", "quoted_name", "reserved_word_name")

_BRANCH_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "branch_1_with_option": {
        "role_name_shape": _SAFE_ROLE_NAME_SHAPES,
        "privilege_level": _CROSSED_PRIVILEGE_LEVELS,
    },
    "branch_2_rename": {
        "new_name_shape": (
            "simple_name",
            "quoted_name",
            "reserved_word_name",
            "existing_name_conflict",
        ),
        "privilege_level": _CROSSED_PRIVILEGE_LEVELS,
    },
    "branch_3_set_value": {
        "config_parameter_behavior": (
            "set_value",
            "set_default",
            "set_from_current",
        ),
        "database_name_shape": (
            "existing_database",
            "non_existent_database",
            "omitted_no_database_clause",
        ),
        "role_name_shape": ("simple_name", "all_keyword"),
        "privilege_level": _CROSSED_PRIVILEGE_LEVELS,
    },
    "branch_4_set_from_current": {
        "database_name_shape": (
            "existing_database",
            "non_existent_database",
            "omitted_no_database_clause",
        ),
        "privilege_level": _CROSSED_PRIVILEGE_LEVELS,
    },
    "branch_5_reset_parameter": {
        "database_name_shape": (
            "existing_database",
            "non_existent_database",
            "omitted_no_database_clause",
        ),
        "privilege_level": _CROSSED_PRIVILEGE_LEVELS,
    },
    "branch_6_reset_all": {
        "database_name_shape": (
            "existing_database",
            "non_existent_database",
            "omitted_no_database_clause",
        ),
        "role_name_shape": ("simple_name", "all_keyword"),
        "privilege_level": _CROSSED_PRIVILEGE_LEVELS,
    },
}

# Flatten all crossed factor -> union of values across branches.
_CROSSED_FACTORS: dict[str, set[str]] = {}
for _axes in _BRANCH_AXES.values():
    for _factor, _values in _axes.items():
        _CROSSED_FACTORS.setdefault(_factor, set()).update(_values)

_VERIFICATION_MODES = (
    "pg_roles_catalog",
    "pg_settings_catalog",
    "pg_authid_catalog",
    "effect_query",
    "error_assertion",
)
_CLEANUP_MODES = (
    "reset_config_parameter",
    "drop_role",
    "revert_attribute_change",
)


def _privilege_fires(assignment: dict[str, str]) -> bool:
    return assignment.get("privilege_level") in _PRIVILEGE_FAILURE_LEVELS


def _failure_unit_count(assignment: dict[str, str]) -> int:
    cluster = 1 if _privilege_fires(assignment) else 0
    negatives = sum(
        1
        for pair in _CROSSED_BEHAVIOUR_NEGATIVES
        if assignment.get(pair[0]) == pair[1]
    )
    return cluster + negatives


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    if _privilege_fires(assignment):
        return ("privilege_level", assignment["privilege_level"])
    for pair in _CROSSED_BEHAVIOUR_NEGATIVES:
        if assignment.get(pair[0]) == pair[1]:
            return pair
    return None


class AlterRoleFactorExtensionPlanTest(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_alter_role_factor_extension_plan(ROOT)

    def test_builds_frozen_extension_count_with_no_truncation(self) -> None:
        self.assertIsInstance(self.plan, AlterRoleFactorExtensionPlan)
        self.assertEqual(_EXTENSION_COUNT, len(self.plan.cases))
        self.assertEqual(_EXTENSION_COUNT, self.plan.raw_combination_count)
        self.assertEqual(0, self.plan.dropped_count)

    def test_ordinals_continue_after_baseline_with_four_digit_scheme(
        self,
    ) -> None:
        ordinals = [case.ordinal for case in self.plan.cases]
        self.assertEqual(
            list(range(_BASELINE_COUNT + 1, _TOTAL_COUNT + 1)), ordinals
        )
        first, last = self.plan.cases[0], self.plan.cases[-1]
        self.assertEqual(_BASELINE_COUNT + 1, first.ordinal)
        self.assertEqual(_TOTAL_COUNT, last.ordinal)
        self.assertEqual("ALTERROLE0109", first.case_id)
        self.assertEqual(f"ALTERROLE{_TOTAL_COUNT:04d}", last.case_id)
        self.assertEqual("ALTERROLE0109.sql", first.sql_filename)
        self.assertEqual(
            f"ALTERROLE{_TOTAL_COUNT:04d}.sql", last.sql_filename
        )
        self.assertEqual("alterrole_0109_", first.object_prefix)
        self.assertEqual(
            f"alterrole_{_TOTAL_COUNT:04d}_", last.object_prefix
        )

    def test_every_case_is_marked_extension_with_full_assignment(self) -> None:
        for case in self.plan.cases:
            self.assertIsInstance(case, AlterRoleFactorExtensionCase)
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

    def test_every_crossed_factor_value_is_witnessed(self) -> None:
        witnessed: dict[str, set[str]] = {
            factor: set() for factor in _CROSSED_FACTORS
        }
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            for factor in _CROSSED_FACTORS:
                if factor in a:
                    witnessed[factor].add(a[factor])
        for factor, values in _CROSSED_FACTORS.items():
            self.assertTrue(
                values.issubset(witnessed[factor]),
                f"factor {factor}: missing {values - witnessed[factor]}",
            )

    def test_verification_and_cleanup_modes_are_all_witnessed(self) -> None:
        seen_v: set[str] = set()
        seen_c: set[str] = set()
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            seen_v.add(a["verification_mode"])
            seen_c.add(a["cleanup_mode"])
        self.assertEqual(set(_VERIFICATION_MODES), seen_v)
        self.assertEqual(set(_CLEANUP_MODES), seen_c)

    def test_derivation_records_are_complete_and_unique(self) -> None:
        ids = [case.derivation_id for case in self.plan.cases]
        self.assertEqual(_EXTENSION_COUNT, len(set(ids)))
        for case in self.plan.cases:
            self.assertTrue(case.derivation_id, case.case_id)
            self.assertTrue(case.derived_from_combination_group, case.case_id)
            self.assertTrue(case.derivation_reason, case.case_id)

    def test_plan_is_deterministic(self) -> None:
        again = build_alter_role_factor_extension_plan(ROOT)
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
        baseline = build_alter_role_factor_loop_plan(ROOT)
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
