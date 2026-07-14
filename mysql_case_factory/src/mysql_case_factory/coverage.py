"""Deterministic expansion and accounting of declared coverage obligations."""

from __future__ import annotations

import hashlib
import itertools
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence

from .contracts import (
    COVERAGE_OUTCOMES,
    CaseManifest,
    CoveragePlan,
    TestPoint,
    inventory_value_equal,
)
from .feature_plan import validate_coverage_plan
from .planning_contracts import FactorDecision


class CoverageError(ValueError):
    """Raised when a plan cannot be expanded without ambiguity."""


@dataclass(frozen=True)
class CoverageObligation:
    obligation_id: str
    plan_id: str
    test_point_id: str
    assignments: Mapping[str, Any]
    outcome: Optional[str]
    reason: Optional[str] = None
    execution_profile: str = "basic_mysql"
    execution_harness: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        document: dict[str, Any] = {
            "obligation_id": self.obligation_id,
            "plan_id": self.plan_id,
            "test_point_id": self.test_point_id,
            "assignments": dict(self.assignments),
            "outcome": self.outcome,
            "execution_profile": self.execution_profile,
        }
        if self.reason is not None:
            document["reason"] = self.reason
        if self.execution_harness is not None:
            document["execution_harness"] = self.execution_harness
        return document


@dataclass(frozen=True)
class CoverageReconciliation:
    total: int
    success: int
    expected_failure: int
    justified_na: int
    missing: int
    missing_obligation_ids: tuple[str, ...]

    @property
    def executable(self) -> int:
        return self.success + self.expected_failure

    @property
    def complete(self) -> bool:
        return self.executable > 0 and self.missing == 0 and self.total == (
            self.success + self.expected_failure + self.justified_na
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "success": self.success,
            "expected_failure": self.expected_failure,
            "justified_na": self.justified_na,
            "executable": self.executable,
            "missing": self.missing,
            "complete": self.complete,
            "missing_obligation_ids": list(self.missing_obligation_ids),
        }


@dataclass(frozen=True)
class CoverageConditionProof:
    """Exact primary-assignment proof for one frozen condition tuple."""

    condition_assignment: Mapping[str, Any]
    primary_axes: tuple[str, ...]
    theoretical_count: int
    actual_count: int
    theoretical_sha256: str
    actual_sha256: str
    expected_outcome_counts: Mapping[str, int]
    outcome_counts: Mapping[str, int]
    missing_assignments: tuple[str, ...] = ()
    unexpected_assignments: tuple[str, ...] = ()

    @property
    def complete(self) -> bool:
        return (
            self.theoretical_count == self.actual_count
            and self.theoretical_sha256 == self.actual_sha256
            and dict(self.expected_outcome_counts) == dict(self.outcome_counts)
            and not self.missing_assignments
            and not self.unexpected_assignments
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "condition_assignment": dict(self.condition_assignment),
            "primary_axes": list(self.primary_axes),
            "theoretical_count": self.theoretical_count,
            "actual_count": self.actual_count,
            "theoretical_sha256": self.theoretical_sha256,
            "actual_sha256": self.actual_sha256,
            "expected_outcome_counts": dict(self.expected_outcome_counts),
            "outcome_counts": dict(self.outcome_counts),
            "missing_assignments": list(self.missing_assignments),
            "unexpected_assignments": list(self.unexpected_assignments),
            "complete": self.complete,
        }


@dataclass(frozen=True)
class CoverageContractProof:
    """A successful exact-set and outcome proof for one contracted point."""

    test_point_id: str
    combination_policy: str
    primary_axes: tuple[str, ...]
    condition_axes: tuple[str, ...]
    axis_inventory_counts: Mapping[str, int]
    axis_inventory_sha256: Mapping[str, str]
    theoretical_count: int
    actual_count: int
    theoretical_sha256: str
    actual_sha256: str
    expected_outcome_counts: Mapping[str, int]
    outcome_counts: Mapping[str, int]
    condition_proofs: tuple[CoverageConditionProof, ...]
    missing_assignments: tuple[str, ...] = ()
    unexpected_assignments: tuple[str, ...] = ()

    @property
    def complete(self) -> bool:
        return (
            self.theoretical_count == self.actual_count
            and self.theoretical_sha256 == self.actual_sha256
            and dict(self.expected_outcome_counts) == dict(self.outcome_counts)
            and not self.missing_assignments
            and not self.unexpected_assignments
            and bool(self.condition_proofs)
            and all(item.complete for item in self.condition_proofs)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "test_point_id": self.test_point_id,
            "combination_policy": self.combination_policy,
            "primary_axes": list(self.primary_axes),
            "condition_axes": list(self.condition_axes),
            "axis_inventory_counts": dict(self.axis_inventory_counts),
            "axis_inventory_sha256": dict(self.axis_inventory_sha256),
            "theoretical_count": self.theoretical_count,
            "actual_count": self.actual_count,
            "theoretical_sha256": self.theoretical_sha256,
            "actual_sha256": self.actual_sha256,
            "expected_outcome_counts": dict(self.expected_outcome_counts),
            "outcome_counts": dict(self.outcome_counts),
            "condition_proofs": [item.to_dict() for item in self.condition_proofs],
            "missing_assignments": list(self.missing_assignments),
            "unexpected_assignments": list(self.unexpected_assignments),
            "complete": self.complete,
        }


@dataclass(frozen=True)
class CoverageCompilation:
    """Coverage obligations plus every proof needed to claim completeness."""

    obligations: tuple[CoverageObligation, ...]
    contract_proofs: tuple[CoverageContractProof, ...]
    legacy_test_point_ids: tuple[str, ...]
    factor_owner_by_id: Mapping[str, str]

    @property
    def proofs(self) -> tuple[CoverageContractProof, ...]:
        """Backward-friendly short name for callers rendering proof bundles."""

        return self.contract_proofs

    @property
    def complete(self) -> bool:
        # An uncontracted v1 point may still be expanded and executed, but it
        # can never be silently promoted into a v2 mathematical proof.
        return (
            bool(self.contract_proofs)
            and not self.legacy_test_point_ids
            and all(item.complete for item in self.contract_proofs)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "obligations": [item.to_dict() for item in self.obligations],
            "contract_proofs": [item.to_dict() for item in self.contract_proofs],
            "legacy_test_point_ids": list(self.legacy_test_point_ids),
            "factor_owner_by_id": dict(self.factor_owner_by_id),
            "complete": self.complete,
        }


@dataclass(frozen=True)
class CaseReconciliation:
    required_cases: int
    matched_cases: int
    missing_case_ids: tuple[str, ...]
    unexpected_case_ids: tuple[str, ...]
    mismatched_case_ids: tuple[str, ...]
    missing_sql_files: tuple[str, ...] = ()
    unsafe_sql_files: tuple[str, ...] = ()

    @property
    def complete(self) -> bool:
        return not (
            self.missing_case_ids
            or self.unexpected_case_ids
            or self.mismatched_case_ids
            or self.missing_sql_files
            or self.unsafe_sql_files
        ) and self.required_cases > 0 and self.required_cases == self.matched_cases

    def to_dict(self) -> dict[str, Any]:
        return {
            "required_cases": self.required_cases,
            "matched_cases": self.matched_cases,
            "missing_obligation_ids": list(self.missing_case_ids),
            "unexpected_case_ids": list(self.unexpected_case_ids),
            "mismatched_case_ids": list(self.mismatched_case_ids),
            "missing_sql_files": list(self.missing_sql_files),
            "unsafe_sql_files": list(self.unsafe_sql_files),
            "complete": self.complete,
        }


def _canonical_value(value: Any) -> Any:
    # Axis values are contract-limited to YAML scalars.  Explicit type tags avoid
    # collisions between values such as True and 1 when producing stable IDs.
    return {"type": type(value).__name__, "value": value}


def stable_obligation_id(
    test_point_id: str,
    assignments: Mapping[str, Any],
    plan_id: Optional[str] = None,
) -> str:
    """Create an order-independent obligation identifier from its semantic key."""

    payload = {
        "plan_id": plan_id,
        "test_point_id": test_point_id,
        "assignments": {
            axis_id: _canonical_value(assignments[axis_id])
            for axis_id in sorted(assignments)
        },
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()[:12]
    prefix = re.sub(r"[^a-z0-9]+", "-", test_point_id.lower()).strip("-") or "point"
    return f"obl-{prefix}-{digest}"


def _assignment_key(assignments: Mapping[str, Any]) -> str:
    if not isinstance(assignments, Mapping):
        raise CoverageError("coverage assignment must be a mapping")
    canonical: dict[str, Any] = {}
    for axis_id, value in assignments.items():
        if not isinstance(axis_id, str) or not axis_id:
            raise CoverageError("coverage assignment axis ids must be non-empty strings")
        if type(value) not in (type(None), bool, int, float, str):
            raise CoverageError(
                f"coverage assignment {axis_id} contains unsupported scalar type "
                f"{type(value).__name__}"
            )
        canonical[axis_id] = _canonical_value(value)
    try:
        return json.dumps(
            canonical,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise CoverageError(f"coverage assignment is not canonical JSON: {exc}") from exc


def assignment_set_sha256(assignments: Iterable[Mapping[str, Any]]) -> str:
    """Hash a semantic assignment *set* with YAML-scalar type identity.

    Input order is deliberately irrelevant.  Duplicates are an error rather
    than being collapsed, because collapsing could hide a missing assignment
    behind a repeated one while preserving the declared row count.
    """

    keys = [_assignment_key(item) for item in assignments]
    if len(keys) != len(set(keys)):
        raise CoverageError("coverage contains a duplicate semantic assignment")
    encoded = json.dumps(
        sorted(keys),
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _axis_product_assignments(
    plan: CoveragePlan,
    axis_ids: Sequence[str],
) -> tuple[dict[str, Any], ...]:
    axes = [(axis_id, plan.axes[axis_id].values) for axis_id in axis_ids]
    return tuple(
        {
            axis_id: value
            for (axis_id, _), value in zip(axes, values)
        }
        for values in itertools.product(*(axis_values for _, axis_values in axes))
    )


def _project_assignment(
    assignments: Mapping[str, Any],
    axis_ids: Sequence[str],
) -> dict[str, Any]:
    return {axis_id: assignments[axis_id] for axis_id in axis_ids}


def _assignment_outcome_counts(
    obligations: Iterable[CoverageObligation],
) -> dict[str, int]:
    materialized = tuple(obligations)
    return {
        "total": len(materialized),
        "success": sum(item.outcome == "success" for item in materialized),
        "expected_failure": sum(
            item.outcome == "expected_failure" for item in materialized
        ),
        "justified_na": sum(item.outcome == "justified_na" for item in materialized),
    }


def _theoretical_outcome_counts(
    point: TestPoint,
    assignments: Iterable[Mapping[str, Any]],
) -> dict[str, int]:
    outcomes = [_classify(point, item)[0] for item in assignments]
    missing = sum(item not in COVERAGE_OUTCOMES for item in outcomes)
    if missing:
        raise CoverageError(
            f"test point {point.test_point_id} has {missing} unclassified "
            "theoretical assignments"
        )
    return {
        "total": len(outcomes),
        "success": sum(item == "success" for item in outcomes),
        "expected_failure": sum(item == "expected_failure" for item in outcomes),
        "justified_na": sum(item == "justified_na" for item in outcomes),
    }


def _condition_label(condition: Mapping[str, Any]) -> str:
    if not condition:
        return "{}"
    return repr(dict(condition))


def prove_coverage_contract(
    plan: CoveragePlan,
    point: TestPoint,
    obligations: Iterable[CoverageObligation],
) -> CoverageContractProof:
    """Prove one coverage contract from independent theoretical and actual sets.

    The theoretical side is built only from the frozen axis inventories.  The
    actual side is built only from the supplied obligations.  No declared
    count or generated list is allowed to stand in for set equality.
    """

    validate_coverage_plan(plan)
    matching_points = tuple(
        candidate
        for candidate in plan.test_points
        if candidate.test_point_id == point.test_point_id
    )
    if len(matching_points) != 1 or matching_points[0] != point:
        raise CoverageError(
            f"test point {point.test_point_id} is not the validated point from plan {plan.plan_id}"
        )
    contract = point.coverage_contract
    if contract is None:
        raise CoverageError(
            f"test point {point.test_point_id} has no coverage contract to prove"
        )
    if contract.combination_policy not in ("full_cross", "conditional_cross"):
        raise CoverageError(
            f"coverage policy {contract.combination_policy} cannot prove exact completeness"
        )

    axis_ids = contract.primary_axes + contract.condition_axes
    theoretical = _axis_product_assignments(plan, axis_ids)
    actual = tuple(obligations)
    actual_assignment_keys = [_assignment_key(item.assignments) for item in actual]
    if len(actual_assignment_keys) != len(set(actual_assignment_keys)):
        raise CoverageError(
            f"test point {point.test_point_id} contains a duplicate semantic assignment"
        )

    expected_axis_keys = set(axis_ids)
    seen_obligation_ids: set[str] = set()
    for obligation in actual:
        if obligation.plan_id != plan.plan_id:
            raise CoverageError(
                f"obligation {obligation.obligation_id} plan id {obligation.plan_id} "
                f"does not match {plan.plan_id}"
            )
        if obligation.test_point_id != point.test_point_id:
            raise CoverageError(
                f"obligation {obligation.obligation_id} belongs to test point "
                f"{obligation.test_point_id}, not {point.test_point_id}"
            )
        assignment_keys = set(obligation.assignments)
        if assignment_keys != expected_axis_keys:
            missing = sorted(expected_axis_keys - assignment_keys)
            extra = sorted(assignment_keys - expected_axis_keys)
            raise CoverageError(
                f"obligation {obligation.obligation_id} assignment keys do not match "
                f"the contract; missing={missing!r}, extra={extra!r}"
            )
        for axis_id in axis_ids:
            value = obligation.assignments[axis_id]
            if not any(
                inventory_value_equal(value, allowed)
                for allowed in plan.axes[axis_id].values
            ):
                raise CoverageError(
                    f"obligation {obligation.obligation_id} uses unknown value "
                    f"{value!r} for axis {axis_id}"
                )
        expected_id = stable_obligation_id(
            point.test_point_id,
            obligation.assignments,
            plan_id=plan.plan_id,
        )
        if obligation.obligation_id != expected_id:
            raise CoverageError(
                f"obligation id {obligation.obligation_id} does not match stable id {expected_id}"
            )
        if obligation.obligation_id in seen_obligation_ids:
            raise CoverageError(
                f"test point {point.test_point_id} contains duplicate obligation id "
                f"{obligation.obligation_id}"
            )
        seen_obligation_ids.add(obligation.obligation_id)

        expected_outcome, expected_reason = _classify(point, obligation.assignments)
        if obligation.outcome != expected_outcome or obligation.reason != expected_reason:
            raise CoverageError(
                f"obligation {obligation.obligation_id} outcome/reason does not match "
                "the plan classification"
            )
        expected_profile, expected_harness = _execution_route(
            point, obligation.assignments
        )
        if (
            obligation.execution_profile != expected_profile
            or obligation.execution_harness != expected_harness
        ):
            raise CoverageError(
                f"obligation {obligation.obligation_id} execution route does not "
                "match the plan"
            )

    theoretical_by_key = {_assignment_key(item): item for item in theoretical}
    actual_by_key = {
        _assignment_key(item.assignments): dict(item.assignments) for item in actual
    }

    condition_assignments = (
        _axis_product_assignments(plan, contract.condition_axes)
        if contract.condition_axes
        else ({},)
    )
    condition_proofs: list[CoverageConditionProof] = []
    for condition in condition_assignments:
        theoretical_for_condition = tuple(
            item
            for item in theoretical
            if all(
                inventory_value_equal(item[axis_id], value)
                for axis_id, value in condition.items()
            )
        )
        actual_for_condition = tuple(
            item
            for item in actual
            if all(
                inventory_value_equal(item.assignments[axis_id], value)
                for axis_id, value in condition.items()
            )
        )
        theoretical_primary = tuple(
            _project_assignment(item, contract.primary_axes)
            for item in theoretical_for_condition
        )
        actual_primary = tuple(
            _project_assignment(item.assignments, contract.primary_axes)
            for item in actual_for_condition
        )
        theoretical_primary_keys = {
            _assignment_key(item) for item in theoretical_primary
        }
        actual_primary_keys = {_assignment_key(item) for item in actual_primary}
        missing = tuple(sorted(theoretical_primary_keys - actual_primary_keys))
        unexpected = tuple(sorted(actual_primary_keys - theoretical_primary_keys))
        if missing or unexpected:
            raise CoverageError(
                f"condition {_condition_label(condition)} missing {len(missing)} "
                f"assignment(s) and has {len(unexpected)} unexpected assignment(s)"
            )
        condition_proofs.append(
            # Per-condition outcomes are classified independently from the
            # supplied obligations, just like the assignment set itself.
            CoverageConditionProof(
                condition_assignment=dict(condition),
                primary_axes=contract.primary_axes,
                theoretical_count=len(theoretical_primary),
                actual_count=len(actual_primary),
                theoretical_sha256=assignment_set_sha256(theoretical_primary),
                actual_sha256=assignment_set_sha256(actual_primary),
                expected_outcome_counts=_theoretical_outcome_counts(
                    point, theoretical_for_condition
                ),
                outcome_counts=_assignment_outcome_counts(actual_for_condition),
            )
        )

    missing_keys = tuple(sorted(set(theoretical_by_key) - set(actual_by_key)))
    unexpected_keys = tuple(sorted(set(actual_by_key) - set(theoretical_by_key)))
    if missing_keys or unexpected_keys:
        raise CoverageError(
            f"test point {point.test_point_id} exact assignment set mismatch: "
            f"missing {len(missing_keys)}, unexpected {len(unexpected_keys)}"
        )

    theoretical_counts = _theoretical_outcome_counts(point, theoretical)
    expected_counts = contract.expected_counts.to_dict()
    if theoretical_counts != expected_counts:
        raise CoverageError(
            f"test point {point.test_point_id} expected outcome counts {expected_counts!r} "
            f"do not match independently classified counts {theoretical_counts!r}"
        )
    actual_counts = _assignment_outcome_counts(actual)
    if actual_counts != expected_counts:
        raise CoverageError(
            f"test point {point.test_point_id} actual outcome counts {actual_counts!r} "
            f"do not match expected outcome counts {expected_counts!r}"
        )
    if actual_counts["success"] + actual_counts["expected_failure"] == 0:
        raise CoverageError(
            f"test point {point.test_point_id} has no executable oracle obligations"
        )

    proof = CoverageContractProof(
        test_point_id=point.test_point_id,
        combination_policy=contract.combination_policy,
        primary_axes=contract.primary_axes,
        condition_axes=contract.condition_axes,
        axis_inventory_counts={
            axis_id: plan.axes[axis_id].inventory_count for axis_id in axis_ids
        },
        axis_inventory_sha256={
            axis_id: plan.axes[axis_id].inventory_sha256 for axis_id in axis_ids
        },
        theoretical_count=len(theoretical),
        actual_count=len(actual),
        theoretical_sha256=assignment_set_sha256(theoretical),
        actual_sha256=assignment_set_sha256(item.assignments for item in actual),
        expected_outcome_counts=expected_counts,
        outcome_counts=actual_counts,
        condition_proofs=tuple(condition_proofs),
        missing_assignments=missing_keys,
        unexpected_assignments=unexpected_keys,
    )
    if not proof.complete:  # Defensive: never return a partial proof object.
        raise CoverageError(
            f"test point {point.test_point_id} coverage proof is incomplete"
        )
    return proof


def _normalize_factor_decisions(
    factor_decisions: Sequence[FactorDecision] | Mapping[str, FactorDecision],
) -> tuple[FactorDecision, ...]:
    if isinstance(factor_decisions, Mapping):
        decisions = tuple(factor_decisions.values())
        mismatched_keys = sorted(
            str(key)
            for key, decision in factor_decisions.items()
            if not isinstance(decision, FactorDecision)
            or key != decision.factor_id
        )
        if mismatched_keys:
            raise CoverageError(
                "factor_decisions mapping keys must equal factor_id: "
                + ", ".join(mismatched_keys)
            )
    elif isinstance(factor_decisions, Sequence) and not isinstance(
        factor_decisions, (str, bytes, bytearray)
    ):
        decisions = tuple(factor_decisions)
    else:
        raise CoverageError("factor_decisions must be a sequence or mapping")
    if any(not isinstance(item, FactorDecision) for item in decisions):
        raise CoverageError("factor_decisions must contain FactorDecision objects")
    seen: set[str] = set()
    for decision in decisions:
        if decision.factor_id in seen:
            raise CoverageError(
                f"duplicate factor decision {decision.factor_id}"
            )
        seen.add(decision.factor_id)
    return decisions


def compile_coverage_plan(
    plan: CoveragePlan,
    factor_decisions: Sequence[FactorDecision] | Mapping[str, FactorDecision],
    obligations: Optional[Iterable[CoverageObligation]] = None,
) -> CoverageCompilation:
    """Bind factor ownership and compile exact proofs for every v2 point."""

    validate_coverage_plan(plan)
    actual = (
        tuple(expand_coverage_plan(plan))
        if obligations is None
        else tuple(obligations)
    )
    known_points = {point.test_point_id for point in plan.test_points}
    for obligation in actual:
        if not isinstance(obligation, CoverageObligation):
            raise CoverageError("obligations must contain CoverageObligation objects")
        if obligation.test_point_id not in known_points:
            raise CoverageError(
                f"obligation {obligation.obligation_id} references unknown test point "
                f"{obligation.test_point_id}"
            )
        if obligation.plan_id != plan.plan_id:
            raise CoverageError(
                f"obligation {obligation.obligation_id} references plan "
                f"{obligation.plan_id}, not {plan.plan_id}"
            )

    contracted = tuple(
        point for point in plan.test_points if point.coverage_contract is not None
    )
    legacy_ids = tuple(
        point.test_point_id
        for point in plan.test_points
        if point.coverage_contract is None
    )
    decisions = _normalize_factor_decisions(factor_decisions)
    if not contracted:
        return CoverageCompilation(actual, (), legacy_ids, {})
    if not decisions:
        raise CoverageError("contracted coverage plan requires factor decisions")

    decision_by_factor = {item.factor_id: item for item in decisions}
    owner_by_factor: dict[str, str] = {}
    axes_in_contracts: set[str] = set()
    for point in contracted:
        contract = point.coverage_contract
        assert contract is not None
        for axis_id in contract.primary_axes + contract.condition_axes:
            if axis_id in axes_in_contracts:
                raise CoverageError(
                    f"factor {axis_id} has two owning suites in the coverage plan"
                )
            axes_in_contracts.add(axis_id)
            decision = decision_by_factor.get(axis_id)
            if decision is None:
                raise CoverageError(
                    f"contracted factor {axis_id} has no factor decision"
                )
            if decision.status != "covered" or decision.review_state != "reviewed":
                raise CoverageError(
                    f"contracted factor {axis_id} requires a reviewed covered decision"
                )
            if decision.owning_suite_id != point.test_point_id:
                raise CoverageError(
                    f"factor {axis_id} owning suite {decision.owning_suite_id} "
                    f"does not match contracted suite {point.test_point_id}"
                )
            if decision.combination_strategy != contract.combination_policy:
                raise CoverageError(
                    f"factor {axis_id} policy {decision.combination_strategy} does not "
                    f"match suite policy {contract.combination_policy}"
                )
            axis = plan.axes[axis_id]
            if (
                decision.inventory_source != axis.inventory_source
                or decision.inventory_sha256 != axis.inventory_sha256
            ):
                raise CoverageError(
                    f"factor {axis_id} inventory binding does not match coverage axis"
                )
            owner_by_factor[axis_id] = point.test_point_id

    extra_covered = [
        item.factor_id
        for item in decisions
        if item.status == "covered" and item.factor_id not in axes_in_contracts
    ]
    if extra_covered:
        raise CoverageError(
            "covered factor decisions are not owned by a contracted suite: "
            + ", ".join(sorted(extra_covered))
        )

    for decision in decisions:
        for dependency_id in decision.dependencies:
            dependency = decision_by_factor.get(dependency_id)
            if dependency is None:
                raise CoverageError(
                    f"factor {decision.factor_id} references missing dependency "
                    f"decision {dependency_id}"
                )
            if (
                decision.combination_strategy == "full_cross"
                and dependency.combination_strategy == "full_cross"
                and decision.owning_suite_id != dependency.owning_suite_id
            ):
                raise CoverageError(
                    f"dependent full_cross factors {decision.factor_id} and "
                    f"{dependency_id} must use the same owning suite"
                )

    proofs = tuple(
        prove_coverage_contract(
            plan,
            point,
            tuple(
                item for item in actual if item.test_point_id == point.test_point_id
            ),
        )
        for point in contracted
    )
    return CoverageCompilation(
        obligations=actual,
        contract_proofs=proofs,
        legacy_test_point_ids=legacy_ids,
        factor_owner_by_id=owner_by_factor,
    )


def _matches(assignments: Mapping[str, Any], criteria: Mapping[str, Any]) -> bool:
    for axis_id, criterion in criteria.items():
        candidates = criterion if isinstance(criterion, list) else [criterion]
        if axis_id not in assignments or not any(
            inventory_value_equal(assignments[axis_id], candidate)
            for candidate in candidates
        ):
            return False
    return True


def _classify(
    point: TestPoint,
    assignments: Mapping[str, Any],
) -> tuple[Optional[str], Optional[str]]:
    matching = [rule for rule in point.classification_rules if _matches(assignments, rule.when)]
    if len(matching) > 1:
        classifications = {(rule.outcome, rule.reason) for rule in matching}
        if len(classifications) > 1:
            raise CoverageError(
                f"test point {point.test_point_id} assignment {dict(assignments)!r} "
                "matches conflicting classification rules"
            )
    if matching:
        outcome = matching[0].outcome
        reason = matching[0].reason
    else:
        outcome = point.default_outcome
        reason = point.default_reason

    if outcome is not None and outcome not in COVERAGE_OUTCOMES:
        raise CoverageError(
            f"test point {point.test_point_id} has unsupported outcome {outcome!r}"
        )
    if outcome in ("expected_failure", "justified_na") and not reason:
        raise CoverageError(f"{outcome} classification requires a reason")
    return outcome, reason


def _execution_route(
    point: TestPoint,
    assignments: Mapping[str, Any],
) -> tuple[str, Optional[str]]:
    matching = [rule for rule in point.execution_rules if _matches(assignments, rule.when)]
    if len(matching) > 1:
        routes = {
            (rule.execution_profile, rule.execution_harness)
            for rule in matching
        }
        if len(routes) > 1:
            raise CoverageError(
                f"test point {point.test_point_id} assignment {dict(assignments)!r} "
                "matches conflicting execution routing rules"
            )
    if matching:
        return matching[0].execution_profile, matching[0].execution_harness
    return point.default_execution_profile, point.default_execution_harness


def expand_test_point(plan: CoveragePlan, point: TestPoint) -> tuple[CoverageObligation, ...]:
    """Expand one point over the complete Cartesian product of its core axes."""

    axes = [(axis_id, plan.axes[axis_id].values) for axis_id in point.core_axes]
    obligations: list[CoverageObligation] = []
    for values in itertools.product(*(axis_values for _, axis_values in axes)):
        assignments = {
            axis_id: value
            for (axis_id, _), value in zip(axes, values)
        }
        outcome, reason = _classify(point, assignments)
        execution_profile, execution_harness = _execution_route(point, assignments)
        obligations.append(
            CoverageObligation(
                obligation_id=stable_obligation_id(
                    point.test_point_id,
                    assignments,
                    plan_id=plan.plan_id,
                ),
                plan_id=plan.plan_id,
                test_point_id=point.test_point_id,
                assignments=assignments,
                outcome=outcome,
                reason=reason,
                execution_profile=execution_profile,
                execution_harness=execution_harness,
            )
        )
    return tuple(obligations)


def expand_coverage_plan(
    plan: CoveragePlan,
    require_complete: bool = False,
) -> tuple[CoverageObligation, ...]:
    """Expand every declared core axis; never sample or rotate values."""

    validate_coverage_plan(plan)
    obligations = tuple(
        obligation
        for point in plan.test_points
        for obligation in expand_test_point(plan, point)
    )
    ids = [obligation.obligation_id for obligation in obligations]
    if len(ids) != len(set(ids)):
        raise CoverageError("coverage expansion produced duplicate obligation ids")
    if require_complete:
        report = reconcile_obligations(obligations)
        if not report.complete:
            if report.executable == 0:
                raise CoverageError("coverage plan has no executable obligations")
            raise CoverageError(f"{report.missing} coverage obligations are unclassified")
    return obligations


def reconcile_obligations(
    obligations: Iterable[CoverageObligation],
) -> CoverageReconciliation:
    """Prove ``required = success + expected_failure + justified_na``."""

    materialized = tuple(obligations)
    ids = [item.obligation_id for item in materialized]
    if len(ids) != len(set(ids)):
        raise CoverageError("cannot reconcile duplicate obligation ids")
    success = sum(item.outcome == "success" for item in materialized)
    expected_failure = sum(item.outcome == "expected_failure" for item in materialized)
    justified_na = sum(item.outcome == "justified_na" for item in materialized)
    missing_ids = tuple(
        item.obligation_id
        for item in materialized
        if item.outcome not in COVERAGE_OUTCOMES
    )
    return CoverageReconciliation(
        total=len(materialized),
        success=success,
        expected_failure=expected_failure,
        justified_na=justified_na,
        missing=len(missing_ids),
        missing_obligation_ids=missing_ids,
    )


def reconcile_case_manifests(
    obligations: Sequence[CoverageObligation],
    cases: Sequence[CaseManifest],
    artifact_root: str | Path | None = None,
) -> CaseReconciliation:
    """Check that each executable obligation has one matching, materialized case."""

    obligation_by_id = {item.obligation_id: item for item in obligations}
    if len(obligation_by_id) != len(obligations):
        raise CoverageError("cannot reconcile duplicate obligation ids")

    case_ids: set[str] = set()
    case_by_obligation: dict[str, CaseManifest] = {}
    duplicate_case_ids: list[str] = []
    unexpected_case_ids: list[str] = []
    mismatched_case_ids: list[str] = []
    missing_sql_files: list[str] = []
    unsafe_sql_files: list[str] = []
    sql_path_owner: dict[str, str] = {}
    sql_hash_owner: dict[str, str] = {}
    resolved_root = Path(artifact_root).resolve(strict=True) if artifact_root is not None else None
    if resolved_root is None:
        unsafe_sql_files.append("artifact_root is required to verify materialized SQL")
    for case in cases:
        if case.case_id in case_ids:
            duplicate_case_ids.append(case.case_id)
            continue
        case_ids.add(case.case_id)
        obligation = obligation_by_id.get(case.obligation_id)
        if (
            obligation is None
            or obligation.outcome == "justified_na"
            or case.obligation_id in case_by_obligation
        ):
            unexpected_case_ids.append(case.case_id)
            continue
        case_by_obligation[case.obligation_id] = case
        declared_assignments = case.metadata.get("assignments")
        if (
            case.test_point_id != obligation.test_point_id
            or case.outcome != obligation.outcome
            or case.execution_profile != obligation.execution_profile
            or case.execution_harness != obligation.execution_harness
            or not isinstance(declared_assignments, Mapping)
            or {
                key: _canonical_value(value)
                for key, value in declared_assignments.items()
            }
            != {
                key: _canonical_value(value)
                for key, value in obligation.assignments.items()
            }
        ):
            mismatched_case_ids.append(case.case_id)
        if resolved_root is not None:
            from .sql_safety import (
                UnsafeSqlError,
                validate_sql_for_basic_runner,
            )

            for sql_file in case.sql_files:
                candidate = resolved_root / sql_file
                try:
                    if candidate.is_symlink():
                        raise ValueError("SQL file must not be a symbolic link")
                    resolved = candidate.resolve(strict=True)
                    resolved.relative_to(resolved_root)
                except (FileNotFoundError, OSError):
                    missing_sql_files.append(f"{case.case_id}:{sql_file}")
                    continue
                except ValueError:
                    unsafe_sql_files.append(
                        f"{case.case_id}:{sql_file}: path escapes the run root"
                    )
                    continue
                if not resolved.is_file():
                    missing_sql_files.append(f"{case.case_id}:{sql_file}")
                    continue
                portable_path = resolved.relative_to(resolved_root).as_posix()
                previous_path_owner = sql_path_owner.get(portable_path)
                if previous_path_owner is not None and previous_path_owner != case.case_id:
                    mismatched_case_ids.extend((previous_path_owner, case.case_id))
                    unsafe_sql_files.append(
                        f"{case.case_id}:{sql_file}: SQL path is reused by {previous_path_owner}"
                    )
                else:
                    sql_path_owner[portable_path] = case.case_id
                try:
                    sql_bytes = resolved.read_bytes()
                    sql_content = sql_bytes.decode("utf-8")
                    if case.execution_profile == "basic_mysql":
                        validate_sql_for_basic_runner(sql_content)
                except (OSError, UnicodeError, UnsafeSqlError) as exc:
                    unsafe_sql_files.append(f"{case.case_id}:{sql_file}: {exc}")
                    continue
                actual_sha256 = hashlib.sha256(sql_bytes).hexdigest()
                if actual_sha256 != case.sql_sha256:
                    mismatched_case_ids.append(case.case_id)
                    unsafe_sql_files.append(
                        f"{case.case_id}:{sql_file}: SQL SHA256 does not match the case manifest"
                    )
                previous_hash_owner = sql_hash_owner.get(actual_sha256)
                if previous_hash_owner is not None and previous_hash_owner != case.case_id:
                    mismatched_case_ids.extend((previous_hash_owner, case.case_id))
                    unsafe_sql_files.append(
                        f"{case.case_id}:{sql_file}: SQL content is reused by {previous_hash_owner}"
                    )
                else:
                    sql_hash_owner[actual_sha256] = case.case_id

    unexpected_case_ids.extend(duplicate_case_ids)
    required = tuple(
        item for item in obligations if item.outcome in ("success", "expected_failure")
    )
    missing_executable = tuple(
        item.obligation_id
        for item in required
        if item.obligation_id not in case_by_obligation
    )
    unclassified = tuple(
        item.obligation_id
        for item in obligations
        if item.outcome not in COVERAGE_OUTCOMES
    )
    missing = missing_executable + unclassified
    matched = sum(
        item.obligation_id in case_by_obligation
        and case_by_obligation[item.obligation_id].case_id not in mismatched_case_ids
        for item in required
    )
    return CaseReconciliation(
        required_cases=len(required),
        matched_cases=matched,
        missing_case_ids=missing,
        unexpected_case_ids=tuple(unexpected_case_ids),
        mismatched_case_ids=tuple(dict.fromkeys(mismatched_case_ids)),
        missing_sql_files=tuple(dict.fromkeys(missing_sql_files)),
        unsafe_sql_files=tuple(dict.fromkeys(unsafe_sql_files)),
    )


__all__ = [
    "CoverageError",
    "CoverageObligation",
    "CoverageReconciliation",
    "CoverageConditionProof",
    "CoverageContractProof",
    "CoverageCompilation",
    "CaseReconciliation",
    "stable_obligation_id",
    "assignment_set_sha256",
    "prove_coverage_contract",
    "compile_coverage_plan",
    "expand_test_point",
    "expand_coverage_plan",
    "reconcile_obligations",
    "reconcile_case_manifests",
]
