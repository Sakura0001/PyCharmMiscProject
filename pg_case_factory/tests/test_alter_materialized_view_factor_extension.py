"""Tests for the bounded ALTER MATERIALIZED VIEW post-coverage extension expander.

The marginal factor-value-loop (``alter_materialized_view_factor_loop.py``) is
the frozen 61-case baseline (GRM 6 + SFV 53 + RISK 2).  This module's expander
adds the bounded post-coverage extension phase: cross-factor combinations of
the positive T1-T4 behaviour axes across the single ``branch_action`` synopsis
branch (at most one failure-causing value per case, so attribution stays
clean), with ``verification_mode`` crossed and ``cleanup_mode`` crossed so
every declared T6 value is exercised.  Each extension case carries a derivation
record and is marked ``is_extension = True``; it never replaces a
required-baseline obligation.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import unittest

import yaml

from pg_case_factory.alter_materialized_view_factor_extension import (
    AlterMaterializedViewFactorExtensionCase,
    AlterMaterializedViewFactorExtensionError,
    AlterMaterializedViewFactorExtensionPlan,
    build_alter_materialized_view_factor_extension_plan,
)
from pg_case_factory.alter_materialized_view_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_alter_materialized_view_factor_loop_plan,
)


ROOT = Path(__file__).resolve().parents[1]

_BASELINE_COUNT = 61
_EXTENSION_COUNT = 8424
_TOTAL_COUNT = _BASELINE_COUNT + _EXTENSION_COUNT  # 8485
_SUCCESS_EXTENSIONS = 3924
_FAILURE_EXTENSIONS = 4500
_EXTENSION_MULTISET_SHA256 = (
    "b30bf50ef955b9a7ca8245b87ca4899ba4f4c51ada0bcdc5a863b059836ca1ec"
)

# Behaviour-negative (factor, value) pairs that are CROSSED in extensions.
# target_object_state=missing is a failure only when if_exists_clause=absent
# (handled separately via _target_missing_fires, not counted unconditionally
# here).  The privilege cluster (insufficient_privilege) is counted as a single
# unit via _PRIVILEGE_CLUSTER_VALUES and is therefore not duplicated here.
_CROSSED_BEHAVIOUR_NEGATIVES = frozenset(
    {
        ("target_object_state", "wrong_object_type"),
        ("new_owner_shape", "missing_role"),
    }
)
_PRIVILEGE_CLUSTER_VALUES = frozenset({"insufficient_privilege"})

# Crossed axes.  Every value here must be witnessed somewhere in the
# extension plan.  alter_action_type and target_action are tied 1:1
# (target_action := alter_action_type), so both carry the same twelve values.
_CROSSED_AXES = {
    "alter_action_type": (
        "set_statistics",
        "set_attribute_option",
        "reset_attribute_option",
        "set_storage",
        "set_compression",
        "cluster_on",
        "set_without_cluster",
        "set_access_method",
        "set_tablespace",
        "set_storage_parameter",
        "reset_storage_parameter",
        "owner_to",
    ),
    "target_action": (
        "set_statistics",
        "set_attribute_option",
        "reset_attribute_option",
        "set_storage",
        "set_compression",
        "cluster_on",
        "set_without_cluster",
        "set_access_method",
        "set_tablespace",
        "set_storage_parameter",
        "reset_storage_parameter",
        "owner_to",
    ),
    "new_owner_shape": (
        "plain_role",
        "current_role",
        "current_user",
        "session_user",
        "missing_role",
    ),
    "target_object_state": ("exists", "missing", "wrong_object_type"),
    "privilege_context": (
        "owner",
        "granted_role",
        "insufficient_privilege",
    ),
    "if_exists_clause": ("absent", "present"),
    "name_shape": (
        "plain_identifier",
        "schema_qualified",
        "quoted_identifier",
    ),
    "column_name_shape": ("plain_identifier", "quoted_identifier"),
    "verification_mode": ("catalog_query", "effect_query", "error_assertion"),
    "cleanup_mode": ("drop_objects", "reset_state"),
}

# Factors held at baseline value across all extensions (the baseline owns their
# negative counterparts one-per-value; they are never crossed here).
_HELD_CONSTANT = {
    "statement_branch": "branch_action",
    "grammar_branch": "branch_action",
    "dependency_state": "ready",
    "extension_state": "extension_exists",
    "invalid_combination": "none",
    "ownership_boundary": "owner",
}


def _privilege_boundary_fires(assignment: dict[str, str]) -> bool:
    """Whether the must_be_owner_of_materialized_view check actually fires.

    SESSION_USER resolves to the session user (the superuser that owns every
    test materialized view), making OWNER TO SESSION_USER a no-op transfer that
    PG 18.4 allows even for non-owners; the boundary does not fire there.
    """

    return assignment.get("new_owner_shape") != "session_user"


def _target_missing_fires(assignment: dict[str, str]) -> bool:
    """target_object_state=missing is a failure only without IF EXISTS."""

    return (
        assignment.get("target_object_state") == "missing"
        and assignment.get("if_exists_clause") == "absent"
    )


def _if_exists_missing_noop(assignment: dict[str, str]) -> bool:
    """Whether IF EXISTS short-circuits a missing target to a no-op success.

    Mirrors the module: ALTER MATERIALIZED VIEW IF EXISTS on a missing mview
    never reaches the privilege/role/object-type checks (PG 18.4 emits a 01000
    NOTICE, 00000), so no failure pair is attributable.  This governs only the
    *disposition* (expected_sqlstate) — the failure-unit count (potential
    failures) is unchanged, so the at-most-one filter and frozen case count are
    stable; a no-op success may therefore carry a non-zero failure-unit count
    (a masked would-be failure).
    """

    return (
        assignment.get("target_object_state") == "missing"
        and assignment.get("if_exists_clause") == "present"
    )


def _failure_unit_count(assignment: dict[str, str]) -> int:
    """Privilege cluster (1) + behaviour negatives; must stay at most one."""

    level = assignment.get("privilege_context")
    cluster = (
        1
        if level in _PRIVILEGE_CLUSTER_VALUES
        and _privilege_boundary_fires(assignment)
        else 0
    )
    negatives = sum(
        1
        for factor, value in _CROSSED_BEHAVIOUR_NEGATIVES
        if assignment.get(factor) == value
    )
    if _target_missing_fires(assignment):
        negatives += 1
    return cluster + negatives


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    """Return the single attributable failure pair, or None for success.

    Mirrors the module's attribution order: privilege cluster (when the
    boundary fires), then wrong_object_type, then target_missing (only
    without IF EXISTS), then missing_role.  IF EXISTS on a missing target
    short-circuits to a no-op success (no failure pair).
    """

    if _if_exists_missing_noop(assignment):
        return None
    level = assignment.get("privilege_context")
    if (
        level in _PRIVILEGE_CLUSTER_VALUES
        and _privilege_boundary_fires(assignment)
    ):
        return ("privilege_context", level)
    if assignment.get("target_object_state") == "wrong_object_type":
        return ("target_object_state", "wrong_object_type")
    if _target_missing_fires(assignment):
        return ("target_object_state", "missing")
    if assignment.get("new_owner_shape") == "missing_role":
        return ("new_owner_shape", "missing_role")
    return None


class AlterMaterializedViewFactorExtensionPlanTest(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_alter_materialized_view_factor_extension_plan(ROOT)

    def test_builds_frozen_extension_count_with_no_truncation(self) -> None:
        self.assertIsInstance(self.plan, AlterMaterializedViewFactorExtensionPlan)
        self.assertEqual(_EXTENSION_COUNT, len(self.plan.cases))
        # raw product == kept count => no silent truncation
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
        self.assertEqual("ALTERMATERIALIZEDVIEW00062", first.case_id)
        self.assertEqual(
            f"ALTERMATERIALIZEDVIEW{_TOTAL_COUNT:05d}", last.case_id
        )
        self.assertEqual(
            "ALTERMATERIALIZEDVIEW00062.sql", first.sql_filename
        )
        self.assertEqual(
            f"ALTERMATERIALIZEDVIEW{_TOTAL_COUNT:05d}.sql",
            last.sql_filename,
        )
        self.assertEqual(
            "altermaterializedview_00062_", first.object_prefix
        )
        self.assertEqual(
            f"altermaterializedview_{_TOTAL_COUNT:05d}_",
            last.object_prefix,
        )

    def test_every_case_is_marked_extension_with_full_assignment(self) -> None:
        for case in self.plan.cases:
            self.assertIsInstance(
                case, AlterMaterializedViewFactorExtensionCase
            )
            self.assertTrue(case.is_extension, case.case_id)
            # 17 keys: 15 _BASELINE_DEFAULTS + verification_mode (crossed) +
            # cleanup_mode (crossed).  The T5 negatives are absent because
            # they are owned one-per-value by the marginal baseline.
            self.assertEqual(17, len(case.factor_assignment), case.case_id)
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
            elif _if_exists_missing_noop(assignment):
                # IF EXISTS on a missing target is a no-op success, but it may
                # still carry a masked failure-unit (e.g. insufficient_privilege
                # would fire without the no-op); the disposition (pair=None, not
                # the potential count) is the source of truth for the outcome.
                self.assertLessEqual(count, 1, case.case_id)
            else:
                # The privilege-cluster term is gated on the boundary
                # actually firing, so insufficient_privilege + SESSION_USER
                # (owner_to) has count=0 and is a no-op success.  Because the
                # failure-unit conditions are exactly the present-failure
                # conditions, every non-no-op success case has count=0.
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

    def test_privilege_cluster_fires_only_for_insufficient_privilege(
        self,
    ) -> None:
        # The single insufficient_privilege value models the
        # must_be_owner_of_materialized_view (42501) boundary.  owner and
        # granted_role are both success privilege contexts.
        witnessed_levels = {
            dict(c.factor_assignment)["privilege_context"]
            for c in self.plan.cases
        }
        self.assertTrue(
            _PRIVILEGE_CLUSTER_VALUES.issubset(witnessed_levels)
        )
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            if a["privilege_context"] in _PRIVILEGE_CLUSTER_VALUES:
                if _privilege_boundary_fires(a) and not _if_exists_missing_noop(a):
                    self.assertEqual(
                        "expected_failure", case.outcome, case.case_id
                    )
                    self.assertEqual(
                        "42501", case.expected_sqlstate, case.case_id
                    )
                else:
                    # Two sub-cases short-circuit to success without a 42501:
                    # (1) SESSION_USER resolves to the session user (the
                    # owner), making OWNER TO a no-op that PG allows even for
                    # non-owners, so the privilege boundary does not fire and
                    # a 42501 failure is impossible; (2) IF EXISTS on a
                    # missing target never reaches the privilege check (no-op
                    # success), so even a boundary that would otherwise fire
                    # is masked.  In both, a 42501 failure is impossible.
                    self.assertNotEqual(
                        "42501", case.expected_sqlstate, case.case_id
                    )

    def test_new_owner_shape_only_crossed_for_owner_to(self) -> None:
        # new_owner_shape is only relevant for the owner_to action; for the
        # other eleven alter_action_type values it stays at plain_role, so
        # missing_role is never attributable where OWNER TO is not rendered.
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            if a["alter_action_type"] != "owner_to":
                self.assertEqual(
                    "plain_role", a["new_owner_shape"], case.case_id
                )

    def test_branch_grammar_and_consumer_action_are_consistent(self) -> None:
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            self.assertEqual("branch_action", a["statement_branch"], case.case_id)
            self.assertEqual("branch_action", a["grammar_branch"], case.case_id)
            self.assertEqual(
                a["alter_action_type"], a["target_action"], case.case_id
            )
            self.assertEqual(
                a["alter_action_type"], case.consumer_action_id, case.case_id
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
        # full T6 cross with no truncation => each value appears evenly
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
            self.assertTrue(case.derivation_id.startswith("AMV-EXT|"))

    def test_plan_is_deterministic(self) -> None:
        again = build_alter_materialized_view_factor_extension_plan(ROOT)
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
        baseline = build_alter_materialized_view_factor_loop_plan(ROOT)
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
