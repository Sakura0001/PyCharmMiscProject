"""Tests for the bounded ALTER FUNCTION post-coverage extension expander.

The marginal factor-value-loop (``alter_function_factor_loop.py``) is the
frozen 123-case baseline (GRM 36 + SFV 85 + RISK 2).  This module's expander
adds the bounded post-coverage extension phase: cross-factor combinations of
the positive T1-T4 behaviour axes across the five official synopsis
branches (at most one failure-causing value per case, so attribution stays
clean), with ``verification_mode`` crossed and ``cleanup_mode`` rotated so
every declared T6 value is exercised.  Each extension case carries a
derivation record and is marked ``is_extension = True``; it never replaces a
required-baseline obligation.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import unittest

import yaml

from pg_case_factory.alter_function_factor_extension import (
    AlterFunctionFactorExtensionCase,
    AlterFunctionFactorExtensionError,
    AlterFunctionFactorExtensionPlan,
    build_alter_function_factor_extension_plan,
)
from pg_case_factory.alter_function_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_alter_function_factor_loop_plan,
)


ROOT = Path(__file__).resolve().parents[1]

_BASELINE_COUNT = 123
# Calibration after the PG18.4 double-run: DEPENDS ON EXTENSION does NOT
# require superuser (function_owner succeeds -> 00000), so branch_5 x
# function_owner stays success.  Two real privilege walls fire only under a
# non-superuser function owner: LEAKPROOF (42501, only superuser can define a
# leakproof function) and OWNER TO a role the owner is not a member of
# (new_owner_role / SESSION_USER -> 42501, must be able to SET ROLE).  Their
# co-occurrence with a behaviour-negative is excluded by the at-most-one rule
# (the shadowed negative is never reached); the kept exists-pairings carry
# 42501 as the sole failure unit.  No truncation (raw == kept); the
# exclusions are at-most-one attributions, not a cap.  Counts below are
# frozen to the empirical expander output.
_EXTENSION_COUNT = 13140
_TOTAL_COUNT = _BASELINE_COUNT + _EXTENSION_COUNT  # 13263
_SUCCESS_EXTENSIONS = 2664
_FAILURE_EXTENSIONS = 10476

# Behaviour-negative (factor, value) pairs that are CROSSED in extensions.
# The privilege cluster (privilege_level=non_owner_*) is counted as a single
# unit, so neither member is duplicated here.
_CROSSED_BEHAVIOUR_NEGATIVES = frozenset(
    {
        ("object_state", "not_exists"),
        ("object_state", "different_signature_exists"),
        ("argtype_specification", "with_partial_signature"),
        ("configuration_parameter_shape", "invalid_parameter"),
        ("rename_target", "duplicate_name"),
        ("owner_target", "nonexistent_role"),
        ("schema_target", "schema_not_exists"),
        ("schema_target", "pg_catalog_reserved"),
        ("schema_target", "information_schema_reserved"),
        ("extension_target", "extension_not_exists"),
        ("schema_dependency", "target_schema_not_exists"),
        ("schema_dependency", "reserved_schema"),
        ("role_dependency", "owner_role_not_exists"),
        ("extension_dependency", "extension_not_installed"),
    }
)
_PRIVILEGE_CLUSTER_VALUES = frozenset(
    {"non_owner_with_alter", "non_owner_no_privilege"}
)
# Mirrors the expander: under a non-superuser function owner, LEAKPROOF
# (requires superuser) and OWNER TO a role the owner is not a member of
# (new_owner_role / SESSION_USER) surface 42501 before the action takes
# effect, shadowing any co-occurring behaviour-negative; attributed first by
# _present_failure_pair.  Co-occurrence with a behaviour-negative is excluded
# by the at-most-one rule.
_ACTION_REQUIRES_SUPERUSER = frozenset({"leakproof"})
_OWNER_TARGET_REQUIRES_MEMBERSHIP = frozenset({"new_owner_role", "SESSION_USER"})

# Crossed axes (the union of all per-branch crossed axes).  Every value here
# must be witnessed somewhere in the extension plan.
_CROSSED_AXES = {
    "statement_branch": (
        "branch_1",
        "branch_2",
        "branch_3",
        "branch_4",
        "branch_5",
    ),
    "target_action": (
        "called_on_null_input",
        "immutable",
        "volatile",
        "leakproof",
        "security_definer",
        "set_parameter",
        "rename",
        "owner",
        "set_schema",
        "depends_on_extension",
    ),
    "object_state": (
        "exists",
        "not_exists",
        "different_signature_exists",
    ),
    "argtype_specification": (
        "with_full_signature",
        "with_partial_signature",
        "without_signature",
    ),
    "function_name_shape": (
        "simple",
        "quoted",
        "reserved_word",
        "schema_qualified",
    ),
    "privilege_level": (
        "superuser",
        "function_owner",
        "non_owner_with_alter",
        "non_owner_no_privilege",
    ),
    "restrict_clause": ("present", "absent"),
    "configuration_parameter_shape": ("valid_parameter", "invalid_parameter"),
    "new_name_shape": ("simple", "quoted", "reserved_word"),
    "rename_target": (
        "simple",
        "quoted",
        "reserved_word",
        "duplicate_name",
    ),
    "owner_target": (
        "new_owner_role",
        "CURRENT_ROLE",
        "CURRENT_USER",
        "SESSION_USER",
        "nonexistent_role",
    ),
    "role_dependency": ("owner_role_exists", "owner_role_not_exists"),
    "schema_target": (
        "schema_exists",
        "schema_not_exists",
        "pg_catalog_reserved",
        "information_schema_reserved",
    ),
    "schema_dependency": (
        "target_schema_exists",
        "target_schema_not_exists",
        "reserved_schema",
    ),
    "extension_target": (
        "extension_exists",
        "extension_not_exists",
        "NO_DEPENDS",
    ),
    "extension_dependency": (
        "extension_installed",
        "extension_not_installed",
    ),
    "verification_mode": (
        "pg_proc_catalog_query",
        "information_schema_routines",
        "pg_get_functiondef",
    ),
    "cleanup_mode": (
        "DROP_FUNCTION",
        "DROP_FUNCTION_IF_EXISTS",
        "DROP_FUNCTION_CASCADE",
    ),
}

# Factors held at baseline value across all extensions (the baseline owns
# their negative counterparts one-per-value; they are never crossed here).
_HELD_CONSTANT = {
    "action_list_cardinality": "one_action",
    "set_assignment_form": "to_value",
    "external_keyword": "omitted",
    "depends_polarity": "depends",
}

_BRANCH_GRAMMAR = {
    "branch_1": "branch_action_form",
    "branch_2": "branch_rename",
    "branch_3": "branch_owner",
    "branch_4": "branch_set_schema",
    "branch_5": "branch_depends_extension",
}
_BRANCH_FIXED_ACTION = {
    "branch_2": "rename",
    "branch_3": "owner",
    "branch_4": "set_schema",
    "branch_5": "depends_on_extension",
}


def _owner_privilege_failure(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """The privilege-wall (factor, value) pair firing here, else None.

    Mirrors the expander: under a non-superuser function owner, LEAKPROOF
    (requires superuser) and OWNER TO a role the owner is not a member of
    (new_owner_role / SESSION_USER) hit 42501 before the action takes effect,
    shadowing any co-occurring behaviour-negative.  Only ``function_owner``
    is reachable: the non_owner cluster already attributes 42501
    (must_be_owner) and superuser passes both checks, so neither adds this
    unit.
    """

    if assignment.get("privilege_level") != "function_owner":
        return None
    target_action = assignment.get("target_action")
    if target_action in _ACTION_REQUIRES_SUPERUSER:
        return ("target_action", "leakproof_under_function_owner")
    if (
        target_action == "owner"
        and assignment.get("owner_target") in _OWNER_TARGET_REQUIRES_MEMBERSHIP
    ):
        return ("owner_target", "membership_required_under_function_owner")
    return None


def _failure_unit_count(assignment: dict[str, str]) -> int:
    """Privilege cluster (1) + owner-privilege wall (1) + behaviour negatives.

    The privilege cluster (non_owner_*) and the owner-privilege wall
    (function_owner + LEAKPROOF / role-membership) are mutually exclusive --
    a case has exactly one privilege_level -- so the two never double-count.
    """

    cluster = (
        1
        if assignment.get("privilege_level") in _PRIVILEGE_CLUSTER_VALUES
        else 0
    )
    owner_priv = 1 if _owner_privilege_failure(assignment) else 0
    negatives = sum(
        1
        for pair in _CROSSED_BEHAVIOUR_NEGATIVES
        if assignment.get(pair[0]) == pair[1]
    )
    return cluster + owner_priv + negatives


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success.

    The owner-privilege wall (LEAKPROOF / role-membership) fires before the
    action takes effect, so it is attributed first when present (it shadows
    any co-occurring behaviour-negative, which the at-most-one rule
    excludes).
    """

    pair = _owner_privilege_failure(assignment)
    if pair is not None:
        return pair
    level = assignment.get("privilege_level")
    if level in _PRIVILEGE_CLUSTER_VALUES:
        return ("privilege_level", level)
    for pair in _CROSSED_BEHAVIOUR_NEGATIVES:
        if assignment.get(pair[0]) == pair[1]:
            return pair
    return None


class AlterFunctionFactorExtensionPlanTest(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_alter_function_factor_extension_plan(ROOT)

    def test_builds_frozen_extension_count_with_no_truncation(self) -> None:
        self.assertIsInstance(self.plan, AlterFunctionFactorExtensionPlan)
        self.assertEqual(_EXTENSION_COUNT, len(self.plan.cases))
        # raw product == kept count => no silent truncation
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
        self.assertEqual("ALTERFUNCTION00124", first.case_id)
        self.assertEqual(f"ALTERFUNCTION{_TOTAL_COUNT:05d}", last.case_id)
        self.assertEqual("ALTERFUNCTION00124.sql", first.sql_filename)
        self.assertEqual(
            f"ALTERFUNCTION{_TOTAL_COUNT:05d}.sql", last.sql_filename
        )
        self.assertEqual("alterfunction_00124_", first.object_prefix)
        self.assertEqual(
            f"alterfunction_{_TOTAL_COUNT:05d}_", last.object_prefix
        )

    def test_every_case_is_marked_extension_with_full_assignment(self) -> None:
        for case in self.plan.cases:
            self.assertIsInstance(case, AlterFunctionFactorExtensionCase)
            self.assertTrue(case.is_extension, case.case_id)
            # 24 keys: 20 _BASELINE_DEFAULTS + verification/cleanup crossed
            self.assertEqual(24, len(case.factor_assignment), case.case_id)
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

    def test_expected_status_is_derived_from_failure_unit(self) -> None:
        for case in self.plan.cases:
            assignment = dict(case.factor_assignment)
            count = _failure_unit_count(assignment)
            self.assertEqual(
                "failure" if count == 1 else "success",
                assignment["expected_status"],
                case.case_id,
            )

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

    def test_privilege_cluster_collapses_two_non_owner_levels(self) -> None:
        # Both non-owner privilege levels model the same must_be_owner
        # (42501) boundary and must never co-occur with another failure.
        seen_levels = {c for c in _PRIVILEGE_CLUSTER_VALUES}
        witnessed_levels = {
            dict(c.factor_assignment)["privilege_level"]
            for c in self.plan.cases
        }
        self.assertTrue(seen_levels.issubset(witnessed_levels))
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            if a["privilege_level"] in _PRIVILEGE_CLUSTER_VALUES:
                self.assertEqual(
                    "expected_failure", case.outcome, case.case_id
                )
                self.assertEqual("42501", case.expected_sqlstate, case.case_id)

    def test_branch_grammar_and_consumer_action_are_consistent(self) -> None:
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            branch = a["statement_branch"]
            self.assertEqual(
                _BRANCH_GRAMMAR[branch], a["grammar_branch"], case.case_id
            )
            if branch == "branch_1":
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

    def test_reserved_schema_never_paired_with_superuser(self) -> None:
        # gotcha #4: reserved-schema SET SCHEMA surfaces 42501 only under a
        # non-superuser owner; the superuser pairing is semantically invalid.
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            reserved = a.get("schema_target") in {
                "pg_catalog_reserved",
                "information_schema_reserved",
            } or a.get("schema_dependency") == "reserved_schema"
            if reserved:
                self.assertNotEqual(
                    "superuser", a["privilege_level"], case.case_id
                )

    def test_invalid_parameter_only_for_set_reset_actions(self) -> None:
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            if a.get("configuration_parameter_shape") == "invalid_parameter":
                self.assertIn(
                    a["target_action"],
                    {"set_parameter", "reset_parameter", "reset_all"},
                    case.case_id,
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
        # full T6 cross with no truncation => each value appears evenly
        self.assertEqual(
            _EXTENSION_COUNT // len(_CROSSED_AXES["verification_mode"]),
            vm_counts["pg_proc_catalog_query"],
        )
        self.assertEqual(
            _EXTENSION_COUNT // len(_CROSSED_AXES["cleanup_mode"]),
            cm_counts["DROP_FUNCTION_IF_EXISTS"],
        )

    def test_derivation_records_are_complete_and_unique(self) -> None:
        ids = [case.derivation_id for case in self.plan.cases]
        self.assertEqual(_EXTENSION_COUNT, len(set(ids)))
        for case in self.plan.cases:
            self.assertTrue(case.derivation_id, case.case_id)
            self.assertTrue(case.derived_from_combination_group, case.case_id)
            self.assertTrue(case.derivation_reason, case.case_id)

    def test_plan_is_deterministic(self) -> None:
        again = build_alter_function_factor_extension_plan(ROOT)
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
        baseline = build_alter_function_factor_loop_plan(ROOT)
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
