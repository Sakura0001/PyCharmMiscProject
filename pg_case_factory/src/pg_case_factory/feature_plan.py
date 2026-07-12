"""Semantic validation and dependency ordering for feature coverage plans."""

from __future__ import annotations

import itertools
import re
from typing import Optional

from .contracts import (
    CANONICAL_SCOPE_SOURCE_GROUPS,
    CANONICAL_SCOPE_SNAPSHOTS,
    CANONICAL_SCOPE_SELECTORS,
    ContractValidationError,
    CoveragePlan,
    FeatureManifest,
    TestPoint,
    inventory_value_equal,
)


def _criterion_values(criterion):
    return criterion if isinstance(criterion, list) else [criterion]


def _rule_matches(assignments, criteria) -> bool:
    return all(
        axis_id in assignments
        and any(
            inventory_value_equal(assignments[axis_id], candidate)
            for candidate in _criterion_values(criterion)
        )
        for axis_id, criterion in criteria.items()
    )


def _point_routes_harness(plan: CoveragePlan, point: TestPoint, harness_id: str) -> bool:
    """Return whether at least one concrete point assignment selects a harness."""

    if any(axis_id not in plan.axes for axis_id in point.core_axes):
        return False
    axes = [(axis_id, plan.axes[axis_id].values) for axis_id in point.core_axes]
    for values in itertools.product(*(axis_values for _, axis_values in axes)):
        assignments = {
            axis_id: value
            for (axis_id, _), value in zip(axes, values)
        }
        matching_rules = [
            rule
            for rule in point.execution_rules
            if _rule_matches(assignments, rule.when)
        ]
        if matching_rules:
            if any(
                rule.execution_profile == "external_isolated"
                and rule.execution_harness == harness_id
                for rule in matching_rules
            ):
                return True
        elif (
            point.default_execution_profile == "external_isolated"
            and point.default_execution_harness == harness_id
        ):
            return True
    return False


def validate_coverage_plan(
    plan: CoveragePlan,
    manifest: Optional[FeatureManifest] = None,
) -> None:
    """Validate references, axis values, and the test-point dependency DAG."""

    issues: list[str] = []
    points_by_id = {point.test_point_id: point for point in plan.test_points}
    known_axes = set(plan.axes)
    known_requirements = (
        {requirement.requirement_id for requirement in manifest.requirements}
        if manifest is not None
        else None
    )
    used_axes: set[str] = set()
    covered_requirements: set[str] = set()
    referenced_axes = {
        axis_id for point in plan.test_points for axis_id in point.core_axes
    }

    if manifest is not None and manifest.feature_id != plan.feature_id:
        issues.append(
            f"coverage plan feature_id {plan.feature_id} does not match manifest {manifest.feature_id}"
        )

    for axis_id, axis in plan.axes.items():
        if not axis.inventory_source.startswith("inline:"):
            continue
        feature_locators = [
            locator.removeprefix("feature:")
            for locator in axis.source_locators
            if locator.startswith("feature:")
        ]
        pg18_locators = [
            locator.removeprefix("pg18:")
            for locator in axis.source_locators
            if locator.startswith("pg18:")
        ]
        invalid_locators = [
            locator
            for locator in axis.source_locators
            if re.fullmatch(
                r"(?:feature:[A-Za-z0-9][A-Za-z0-9._-]*|pg18:[a-z0-9][a-z0-9._-]*)",
                locator,
            )
            is None
        ]
        if invalid_locators:
            issues.append(
                f"inline coverage axis {axis_id} has invalid source locator(s): "
                + ", ".join(invalid_locators)
            )
        if not feature_locators or not pg18_locators:
            issues.append(
                f"inline coverage axis {axis_id} requires both feature:<requirement-id> "
                "and pg18:<official-topic> source locators"
            )
        if known_requirements is not None:
            for requirement_id in feature_locators:
                if requirement_id not in known_requirements:
                    issues.append(
                        f"inline coverage axis {axis_id} references unknown feature locator {requirement_id}"
                    )

    # A canonical scope can only be marked complete by linking it to a real,
    # exercised axis backed by that scope's canonical inventory selector.  Keep
    # these semantic checks here (rather than in CoveragePlan.from_dict) so all
    # plan-reference errors are reported together.
    for scope_id, decision in plan.scope_decisions.items():
        if decision.status != "complete":
            continue
        unknown_axes = [axis_id for axis_id in decision.axes if axis_id not in plan.axes]
        for axis_id in unknown_axes:
            issues.append(f"scope decision {scope_id} references unknown axis {axis_id}")
        if unknown_axes:
            continue
        for axis_id in decision.axes:
            if axis_id not in referenced_axes:
                issues.append(
                    f"scope decision {scope_id} axis {axis_id} must be used by a test point"
                )
        sources = tuple(plan.axes[axis_id].inventory_source for axis_id in decision.axes)
        selector = CANONICAL_SCOPE_SELECTORS[scope_id]
        if sources not in CANONICAL_SCOPE_SOURCE_GROUPS[scope_id]:
            issues.append(
                f"scope decision {scope_id} requires canonical inventory source "
                f"group {CANONICAL_SCOPE_SOURCE_GROUPS[scope_id][0]} "
                f"(selector {selector})"
            )
        else:
            snapshots = tuple(
                (
                    plan.axes[axis_id].inventory_count,
                    plan.axes[axis_id].inventory_sha256,
                )
                for axis_id in decision.axes
            )
            if snapshots != CANONICAL_SCOPE_SNAPSHOTS[scope_id]:
                issues.append(
                    f"scope decision {scope_id} canonical inventory snapshot "
                    f"does not match the pinned PostgreSQL 18.4 provenance"
                )

    for risk_id, decision in plan.risk_decisions.items():
        if decision.status != "covered":
            continue
        selected_points = []
        for point_id in decision.test_points:
            point = points_by_id.get(point_id)
            if point is None:
                issues.append(
                    f"risk decision {risk_id} references unknown test point {point_id}"
                )
            else:
                selected_points.append(point)
        for axis_id in decision.axes:
            if axis_id not in known_axes:
                issues.append(
                    f"risk decision {risk_id} references unknown axis {axis_id}"
                )
                continue
            if selected_points and not any(
                axis_id in point.core_axes for point in selected_points
            ):
                issues.append(
                    f"risk decision {risk_id} axis {axis_id} is not exercised by its declared test points"
                )
        if decision.execution_harness is not None:
            if not selected_points:
                issues.append(
                    f"risk decision {risk_id} declares execution harness "
                    f"{decision.execution_harness} but has no valid declared test points "
                    "to route an obligation"
                )
            elif not any(
                _point_routes_harness(
                    plan,
                    point,
                    decision.execution_harness,
                )
                for point in selected_points
            ):
                issues.append(
                    f"risk decision {risk_id} declares execution harness "
                    f"{decision.execution_harness} but none of its declared test points "
                    "routes an obligation to that external harness"
                )

    for point in plan.test_points:
        used_axes.update(point.core_axes)
        covered_requirements.update(point.requirement_ids)
        if not point.requirement_ids:
            issues.append(f"test point {point.test_point_id} must reference at least one requirement")
        if not point.core_axes:
            issues.append(f"test point {point.test_point_id} must declare at least one core axis")
        if len(set(point.requirement_ids)) != len(point.requirement_ids):
            issues.append(f"test point {point.test_point_id} has duplicate requirement ids")
        if len(set(point.core_axes)) != len(point.core_axes):
            issues.append(f"test point {point.test_point_id} has duplicate core axes")
        if len(set(point.dependencies)) != len(point.dependencies):
            issues.append(f"test point {point.test_point_id} has duplicate dependencies")

        for requirement_id in point.requirement_ids:
            if known_requirements is not None and requirement_id not in known_requirements:
                issues.append(f"test point {point.test_point_id} references unknown requirement {requirement_id}")
        for axis_id in point.core_axes:
            if axis_id not in known_axes:
                issues.append(f"test point {point.test_point_id} references unknown core axis {axis_id}")
        for dependency in point.dependencies:
            if dependency == point.test_point_id:
                issues.append(f"test point {point.test_point_id} cannot depend on itself")
            elif dependency not in points_by_id:
                issues.append(f"test point {point.test_point_id} references unknown dependency {dependency}")

        for rule_index, rule in enumerate(point.classification_rules):
            for axis_id, criterion in rule.when.items():
                if axis_id not in point.core_axes:
                    issues.append(
                        f"test point {point.test_point_id} classification rule {rule_index} "
                        f"references non-core axis {axis_id}"
                    )
                    continue
                if axis_id not in plan.axes:
                    # The unknown core-axis error above already explains the
                    # root cause.  Avoid turning an invalid plan into a KeyError
                    # while collecting the remaining semantic issues.
                    continue
                allowed_values = plan.axes[axis_id].values
                for value in _criterion_values(criterion):
                    if not any(
                        inventory_value_equal(value, allowed)
                        for allowed in allowed_values
                    ):
                        issues.append(
                            f"test point {point.test_point_id} classification rule {rule_index} "
                            f"uses unknown value {value!r} for axis {axis_id}"
                        )

        for rule_index, rule in enumerate(point.execution_rules):
            for axis_id, criterion in rule.when.items():
                if axis_id not in point.core_axes:
                    issues.append(
                        f"test point {point.test_point_id} execution rule {rule_index} "
                        f"references non-core axis {axis_id}"
                    )
                    continue
                if axis_id not in plan.axes:
                    continue
                allowed_values = plan.axes[axis_id].values
                for value in _criterion_values(criterion):
                    if not any(
                        inventory_value_equal(value, allowed)
                        for allowed in allowed_values
                    ):
                        issues.append(
                            f"test point {point.test_point_id} execution rule {rule_index} "
                            f"uses unknown value {value!r} for axis {axis_id}"
                        )
        allowed_harnesses = {
            decision.execution_harness
            for decision in plan.risk_decisions.values()
            if decision.execution_harness is not None
            and point.test_point_id in decision.test_points
        }
        routed_harnesses = {
            rule.execution_harness
            for rule in point.execution_rules
            if rule.execution_profile == "external_isolated"
        }
        if point.default_execution_profile == "external_isolated":
            routed_harnesses.add(point.default_execution_harness)
        for harness_id in sorted(
            item for item in routed_harnesses if item is not None
        ):
            if harness_id not in allowed_harnesses:
                issues.append(
                    f"test point {point.test_point_id} routes to undeclared execution harness {harness_id}"
                )

    for axis_id in sorted(known_axes - used_axes):
        issues.append(f"coverage axis {axis_id} is not used by any test point")
    if known_requirements is not None:
        for requirement_id in sorted(known_requirements - covered_requirements):
            issues.append(f"feature requirement {requirement_id} is not covered by any test point")

    # Unknown dependencies are reported above; skip them during DFS so users get
    # one clean aggregate error rather than an implementation KeyError.
    visit_state: dict[str, int] = {}
    stack: list[str] = []
    cycle: list[str] = []

    def visit(point_id: str) -> bool:
        visit_state[point_id] = 1
        stack.append(point_id)
        for dependency in points_by_id[point_id].dependencies:
            if dependency not in points_by_id:
                continue
            state = visit_state.get(dependency, 0)
            if state == 0 and visit(dependency):
                return True
            if state == 1:
                start = stack.index(dependency)
                cycle.extend(stack[start:] + [dependency])
                return True
        stack.pop()
        visit_state[point_id] = 2
        return False

    for point in plan.test_points:
        if visit_state.get(point.test_point_id, 0) == 0 and visit(point.test_point_id):
            issues.append("dependency cycle: " + " -> ".join(cycle))
            break

    if issues:
        raise ContractValidationError(issues)


def topological_test_points(plan: CoveragePlan) -> tuple[TestPoint, ...]:
    """Return a stable topological ordering, preserving input order when possible."""

    validate_coverage_plan(plan)
    input_order = {point.test_point_id: index for index, point in enumerate(plan.test_points)}
    points_by_id = {point.test_point_id: point for point in plan.test_points}
    indegree = {point.test_point_id: len(point.dependencies) for point in plan.test_points}
    dependents: dict[str, list[str]] = {point.test_point_id: [] for point in plan.test_points}
    for point in plan.test_points:
        for dependency in point.dependencies:
            dependents[dependency].append(point.test_point_id)

    ready = sorted(
        (point_id for point_id, degree in indegree.items() if degree == 0),
        key=input_order.__getitem__,
    )
    ordered: list[TestPoint] = []
    while ready:
        point_id = ready.pop(0)
        ordered.append(points_by_id[point_id])
        for dependent in sorted(dependents[point_id], key=input_order.__getitem__):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                ready.append(dependent)
                ready.sort(key=input_order.__getitem__)

    # validate_coverage_plan already catches cycles; this is defensive for callers
    # mutating nested mappings after dataclass construction.
    if len(ordered) != len(plan.test_points):
        raise ContractValidationError("coverage plan dependency graph contains a cycle")
    return tuple(ordered)


__all__ = ["validate_coverage_plan", "topological_test_points"]
