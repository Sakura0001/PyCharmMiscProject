"""Tests for the bounded ALTER PROCEDURE post-coverage extension expander."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import unittest

import yaml

from pg_case_factory.alter_procedure_factor_extension import (
    AlterProcedureFactorExtensionCase,
    AlterProcedureFactorExtensionError,
    AlterProcedureFactorExtensionPlan,
    build_alter_procedure_factor_extension_plan,
)
from pg_case_factory.alter_procedure_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_alter_procedure_factor_loop_plan,
)


ROOT = Path(__file__).resolve().parents[1]

_BASELINE_COUNT = 94
_EXTENSION_COUNT = 13104
_TOTAL_COUNT = _BASELINE_COUNT + _EXTENSION_COUNT  # 13198
_SUCCESS_EXTENSIONS = 2520
_FAILURE_EXTENSIONS = 10584

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
_OWNER_TARGET_REQUIRES_MEMBERSHIP = frozenset({"new_owner_role"})
_SESSION_USER_ESCAPE = "SESSION_USER"

_CROSSED_AXES = {
    "statement_branch": (
        "branch_1",
        "branch_2",
        "branch_3",
        "branch_4",
        "branch_5",
    ),
    "target_action": (
        "security_invoker",
        "security_definer",
        "set_parameter",
        "reset_parameter",
        "reset_all",
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
    "procedure_name_shape": (
        "simple",
        "quoted",
        "reserved_word",
        "schema_qualified",
    ),
    "privilege_level": (
        "superuser",
        "procedure_owner",
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
        "DROP_PROCEDURE",
        "DROP_PROCEDURE_IF_EXISTS",
        "DROP_PROCEDURE_CASCADE",
    ),
}

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
    if assignment.get("privilege_level") != "procedure_owner":
        return None
    target_action = assignment.get("target_action")
    if (
        target_action == "owner"
        and assignment.get("owner_target") in _OWNER_TARGET_REQUIRES_MEMBERSHIP
    ):
        return ("owner_target", "membership_required_under_procedure_owner")
    return None


def _privilege_cluster_fires(assignment: dict[str, str]) -> bool:
    level = assignment.get("privilege_level")
    if level not in _PRIVILEGE_CLUSTER_VALUES:
        return False
    if assignment.get("owner_target") == _SESSION_USER_ESCAPE:
        return False
    return True


def _failure_unit_count(assignment: dict[str, str]) -> int:
    cluster = 1 if _privilege_cluster_fires(assignment) else 0
    owner_priv = 1 if _owner_privilege_failure(assignment) else 0
    # SESSION_USER wall (mirrors the module's ``_session_user_wall_fires``):
    # fires for an existing procedure AND for a schema-qualified target in a
    # private existing schema (USAGE denial precedes the existence lookup).
    session_user_wall = (
        assignment.get("owner_target") == _SESSION_USER_ESCAPE
        and assignment.get("privilege_level") != "superuser"
        and assignment.get("role_dependency") == "owner_role_exists"
        and (
            assignment.get("object_state") == "exists"
            or (
                assignment.get("object_state")
                in ("not_exists", "different_signature_exists")
                and assignment.get("procedure_name_shape") == "schema_qualified"
                and assignment.get("schema_target") == "schema_exists"
            )
        )
    )
    # When the wall fires on a not_exists / different_signature case it shadows
    # that behaviour negative (the schema-USAGE denial precedes the existence
    # check), so the negative is excluded to keep the unit count at 1.
    negatives = sum(
        1
        for pair in _CROSSED_BEHAVIOUR_NEGATIVES
        if assignment.get(pair[0]) == pair[1]
        and not (
            session_user_wall
            and pair[0] == "object_state"
            and pair[1] in ("not_exists", "different_signature_exists")
        )
    )
    return cluster + owner_priv + negatives + (1 if session_user_wall else 0)


def _present_failure_pair(
    assignment: dict[str, str],
) -> tuple[str, str] | None:
    pair = _owner_privilege_failure(assignment)
    if pair is not None:
        return pair
    if _privilege_cluster_fires(assignment):
        level = assignment.get("privilege_level")
        return ("privilege_level", level)
    # SESSION_USER owner-transfer wall (must mirror the module's
    # ``_session_user_wall_fires``): a non-superuser doing OWNER TO
    # SESSION_USER surfaces 42501 -- for an existing procedure (must-be-owner)
    # AND for a schema-qualified target in a private existing schema where the
    # non-superuser lacks USAGE, so PG denies the schema (42501) before the
    # existence/signature lookup that would otherwise surface 42883.  Keeping
    # this local copy in sync with the module is what the
    # ``test_expected_sqlstate_matches_present_failure_pair`` cross-check gates.
    if (
        assignment.get("owner_target") == _SESSION_USER_ESCAPE
        and assignment.get("privilege_level") != "superuser"
        and assignment.get("role_dependency") == "owner_role_exists"
        and (
            assignment.get("object_state") == "exists"
            or (
                assignment.get("object_state")
                in ("not_exists", "different_signature_exists")
                and assignment.get("procedure_name_shape") == "schema_qualified"
                and assignment.get("schema_target") == "schema_exists"
            )
        )
    ):
        return ("privilege_level", assignment.get("privilege_level"))
    for pair in _CROSSED_BEHAVIOUR_NEGATIVES:
        if assignment.get(pair[0]) == pair[1]:
            return pair
    return None


class AlterProcedureFactorExtensionPlanTest(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_alter_procedure_factor_extension_plan(ROOT)

    def test_builds_frozen_extension_count_with_no_truncation(self) -> None:
        self.assertIsInstance(self.plan, AlterProcedureFactorExtensionPlan)
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
        self.assertEqual("ALTERPROCEDURE00095", first.case_id)
        self.assertEqual(f"ALTERPROCEDURE{_TOTAL_COUNT:05d}", last.case_id)
        self.assertEqual("ALTERPROCEDURE00095.sql", first.sql_filename)
        self.assertEqual(
            f"ALTERPROCEDURE{_TOTAL_COUNT:05d}.sql", last.sql_filename
        )
        self.assertEqual("alterprocedure_00095_", first.object_prefix)
        self.assertEqual(
            f"alterprocedure_{_TOTAL_COUNT:05d}_", last.object_prefix
        )

    def test_every_case_is_marked_extension_with_full_assignment(self) -> None:
        for case in self.plan.cases:
            self.assertIsInstance(case, AlterProcedureFactorExtensionCase)
            self.assertTrue(case.is_extension, case.case_id)
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
        # SESSION_USER owner-transfer: only a superuser (transferring to itself)
        # completes OWNER TO SESSION_USER (the no-op escape).  A non-superuser
        # (procedure_owner or non_owner) doing OWNER TO SESSION_USER on an
        # EXISTING procedure surfaces 42501 (must be owner / must be a member of
        # the target role); a completely absent or signature-mismatched
        # procedure surfaces 42883 first (existence preempts privilege).
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            if a.get("owner_target") == _SESSION_USER_ESCAPE:
                if _failure_unit_count(a) == 0:
                    self.assertEqual("success", case.outcome, case.case_id)
                if (
                    a.get("privilege_level") != "superuser"
                    and a.get("object_state") == "exists"
                    and a.get("role_dependency") == "owner_role_exists"
                ):
                    self.assertEqual(
                        "42501", case.expected_sqlstate, case.case_id
                    )

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

    def test_derivation_records_are_complete_and_unique(self) -> None:
        ids = [case.derivation_id for case in self.plan.cases]
        self.assertEqual(_EXTENSION_COUNT, len(set(ids)))
        for case in self.plan.cases:
            self.assertTrue(case.derivation_id, case.case_id)
            self.assertTrue(case.derived_from_combination_group, case.case_id)
            self.assertTrue(case.derivation_reason, case.case_id)

    def test_plan_is_deterministic(self) -> None:
        again = build_alter_procedure_factor_extension_plan(ROOT)
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
        baseline = build_alter_procedure_factor_loop_plan(ROOT)
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
