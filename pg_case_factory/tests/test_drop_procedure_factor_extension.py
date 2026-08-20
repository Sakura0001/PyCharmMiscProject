"""Tests for the bounded DROP PROCEDURE post-coverage extension expander."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import unittest

import yaml

from pg_case_factory.drop_procedure_factor_extension import (
    DropProcedureFactorExtensionCase,
    DropProcedureFactorExtensionError,
    DropProcedureFactorExtensionPlan,
    build_drop_procedure_factor_extension_plan,
)
from pg_case_factory.drop_procedure_factor_loop import (
    _SFV_FAILURE_SQLSTATE,
    build_drop_procedure_factor_loop_plan,
)


ROOT = Path(__file__).resolve().parents[1]

_BASELINE_COUNT = 43
_EXTENSION_COUNT = 1896
_TOTAL_COUNT = _BASELINE_COUNT + _EXTENSION_COUNT  # 1939
_SUCCESS_EXTENSIONS = 720
_FAILURE_EXTENSIONS = 1176
_EXTENSION_MULTISET_SHA256 = (
    "ba06c48f359ac27737e254b565eccd90be29e639ccdd4ff75caf48d547114d65"
)

_PRIVILEGE_NEGATIVE = ("privilege_level", "non_owner_no_privilege")
_NOT_EXIST_NEGATIVE = (
    "target_procedure_not_exists",
    "without_IF_EXISTS_error",
)
_HAS_DEPENDENTS_VALUES = frozenset(
    {"has_dependents_restrict_blocks", "has_dependents_cascade_removes"}
)
_RESTRICT_VALUES = frozenset({"RESTRICT", "absent"})
_IF_EXISTS_OMITTED = "absent"

_CROSSED_AXES = {
    "statement_branch": ("branch_1",),
    "target_action": ("drop_procedure",),
    "privilege_level": (
        "non_owner_no_privilege",
        "superuser",
        "procedure_owner",
    ),
    "target_procedure_not_exists": (
        "without_IF_EXISTS_error",
        "with_IF_EXISTS_noop",
    ),
    "if_exists_clause": ("absent", "present"),
    "cascade_restrict_clause": ("CASCADE", "RESTRICT", "absent"),
    "dependent_objects": (
        "has_dependents_restrict_blocks",
        "has_dependents_cascade_removes",
        "no_dependencies",
    ),
    "procedure_name_shape": (
        "simple",
        "quoted",
        "reserved_word",
        "schema_qualified",
    ),
    "verification_mode": (
        "pg_proc_catalog_query",
        "information_schema_routines",
    ),
    "cleanup_mode": (
        "DROP_PROCEDURE_cascade",
        "DROP_PROCEDURE_if_exists_cascade",
        "no_cleanup_needed",
    ),
}

_HELD_CONSTANT = {
    "object_state": "exists",
    "schema_dependency": "schema_exists",
    "argtype_specification": "with_full_signature",
    "multiple_objects": "single_procedure",
    "target_procedure_different_type": "same_name_is_function",
    "permission_insufficient": "not_owner",
    "cascade_destroys_dependents": "cascade_removes_trigger",
    "identifier_length_exceeded": "over_63_chars",
}


def _privilege_failure_fires(a: dict[str, str]) -> bool:
    return a.get("privilege_level") == "non_owner_no_privilege"


def _not_exist_failure_fires(a: dict[str, str]) -> bool:
    return (
        a.get("target_procedure_not_exists") == "without_IF_EXISTS_error"
        and a.get("if_exists_clause") == _IF_EXISTS_OMITTED
    )


def _dependency_failure_fires(a: dict[str, str]) -> bool:
    return (
        a.get("dependent_objects") in _HAS_DEPENDENTS_VALUES
        and a.get("cascade_restrict_clause") in _RESTRICT_VALUES
    )


def _failure_unit_count(a: dict[str, str]) -> int:
    return (
        _privilege_failure_fires(a)
        + _not_exist_failure_fires(a)
        + _dependency_failure_fires(a)
    )


def _present_failure_pair(a: dict[str, str]) -> tuple[str, str] | None:
    if _privilege_failure_fires(a):
        return _PRIVILEGE_NEGATIVE
    if _not_exist_failure_fires(a):
        return _NOT_EXIST_NEGATIVE
    if _dependency_failure_fires(a):
        return ("dependent_objects", a["dependent_objects"])
    return None


class DropProcedureFactorExtensionPlanTest(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_drop_procedure_factor_extension_plan(ROOT)

    def test_builds_frozen_extension_count_with_no_truncation(self) -> None:
        self.assertIsInstance(self.plan, DropProcedureFactorExtensionPlan)
        self.assertEqual(_EXTENSION_COUNT, len(self.plan.cases))
        self.assertEqual(_EXTENSION_COUNT, self.plan.raw_combination_count)
        self.assertEqual(0, self.plan.dropped_count)

    def test_extension_multiset_sha256_is_frozen(self) -> None:
        self.assertEqual(
            _EXTENSION_MULTISET_SHA256,
            self.plan.extension_multiset_sha256,
        )

    def test_ordinals_continue_after_baseline(self) -> None:
        ordinals = [c.ordinal for c in self.plan.cases]
        self.assertEqual(
            list(range(_BASELINE_COUNT + 1, _TOTAL_COUNT + 1)), ordinals
        )
        first, last = self.plan.cases[0], self.plan.cases[-1]
        self.assertEqual(_BASELINE_COUNT + 1, first.ordinal)
        self.assertEqual(_TOTAL_COUNT, last.ordinal)
        self.assertEqual("DROPPROCEDURE00044", first.case_id)
        self.assertEqual(f"DROPPROCEDURE{_TOTAL_COUNT:05d}", last.case_id)

    def test_every_case_is_marked_extension_with_full_assignment(self) -> None:
        for case in self.plan.cases:
            self.assertIsInstance(case, DropProcedureFactorExtensionCase)
            self.assertTrue(case.is_extension, case.case_id)
            self.assertEqual(20, len(case.factor_assignment), case.case_id)
            keys = [k for k, _ in case.factor_assignment]
            self.assertEqual(len(keys), len(set(keys)), case.case_id)

    def test_outcome_split_matches_frozen_arithmetic(self) -> None:
        outcomes = Counter(case.outcome for case in self.plan.cases)
        self.assertEqual(_SUCCESS_EXTENSIONS, outcomes["success"])
        self.assertEqual(_FAILURE_EXTENSIONS, outcomes["expected_failure"])

    def test_at_most_one_failure_unit_per_case(self) -> None:
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            count = _failure_unit_count(a)
            self.assertLessEqual(count, 1, case.case_id)
            if case.outcome == "expected_failure":
                self.assertEqual(1, count, case.case_id)
            else:
                self.assertEqual(0, count, case.case_id)

    def test_expected_status_derived_from_present_failure_pair(self) -> None:
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            pair = _present_failure_pair(a)
            self.assertEqual(
                "failure" if pair is not None else "success",
                a["expected_status"],
                case.case_id,
            )

    def test_expected_sqlstate_matches_present_failure_pair(self) -> None:
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            pair = _present_failure_pair(a)
            if pair is None:
                self.assertEqual("00000", case.expected_sqlstate)
                self.assertIsNone(case.expected_failure_reason)
            else:
                sqlstate, reason = _SFV_FAILURE_SQLSTATE[pair]
                self.assertEqual(sqlstate, case.expected_sqlstate, case.case_id)
                self.assertEqual(reason, case.expected_failure_reason)

    def test_privilege_negative_fires_for_non_owner(self) -> None:
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            if a["privilege_level"] == "non_owner_no_privilege":
                self.assertEqual("expected_failure", case.outcome)
                self.assertEqual("42501", case.expected_sqlstate)

    def test_dependency_negative_fires_under_restrict(self) -> None:
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            if a["privilege_level"] == "non_owner_no_privilege":
                continue
            if _not_exist_failure_fires(a):
                continue
            if a["dependent_objects"] in _HAS_DEPENDENTS_VALUES:
                if a["cascade_restrict_clause"] == "CASCADE":
                    self.assertEqual("success", case.outcome, case.case_id)
                else:
                    self.assertEqual(
                        "expected_failure", case.outcome, case.case_id
                    )
                    self.assertEqual("2BP01", case.expected_sqlstate)

    def test_held_constant_factors_stay_at_baseline(self) -> None:
        for case in self.plan.cases:
            a = dict(case.factor_assignment)
            for factor, value in _HELD_CONSTANT.items():
                self.assertEqual(value, a[factor], (case.case_id, factor))

    def test_every_crossed_factor_value_is_witnessed(self) -> None:
        witnessed: dict[str, set[str]] = {f: set() for f in _CROSSED_AXES}
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
        ids = [c.derivation_id for c in self.plan.cases]
        self.assertEqual(_EXTENSION_COUNT, len(set(ids)))
        for case in self.plan.cases:
            self.assertTrue(case.derivation_id, case.case_id)
            self.assertTrue(case.derived_from_combination_group, case.case_id)
            self.assertTrue(case.derivation_reason, case.case_id)

    def test_plan_is_deterministic(self) -> None:
        again = build_drop_procedure_factor_extension_plan(ROOT)
        self.assertEqual(
            self.plan.extension_multiset_sha256,
            again.extension_multiset_sha256,
        )
        self.assertEqual(
            tuple(c.case_id for c in self.plan.cases),
            tuple(c.case_id for c in again.cases),
        )

    def test_extensions_do_not_collide_with_baseline_numbering(self) -> None:
        baseline = build_drop_procedure_factor_loop_plan(ROOT)
        baseline_ids = {c.case_id for c in baseline.cases}
        extension_ids = {c.case_id for c in self.plan.cases}
        self.assertEqual(0, len(baseline_ids & extension_ids))

    def test_derived_combinations_yaml_parses(self) -> None:
        doc = yaml.safe_load(self.plan.derived_combinations_yaml)
        self.assertIsInstance(doc, list)
        self.assertEqual(_EXTENSION_COUNT, len(doc))
        required = {
            "id", "title", "derived_from_combination_group",
            "derivation_reason", "factors", "expected_status_policy",
            "compatibility", "sql_shape", "verification", "cleanup",
        }
        for entry in doc:
            self.assertTrue(required.issubset(entry.keys()))


if __name__ == "__main__":
    unittest.main()
