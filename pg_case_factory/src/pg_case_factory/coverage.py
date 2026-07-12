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
    execution_profile: str = "basic_psql"
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
                validate_sql_for_external_copy_ingest,
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
                    if case.execution_profile == "basic_psql":
                        validate_sql_for_basic_runner(sql_content)
                    elif case.execution_harness == "external-copy-ingest":
                        validate_sql_for_external_copy_ingest(sql_content)
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
    "CaseReconciliation",
    "stable_obligation_id",
    "expand_test_point",
    "expand_coverage_plan",
    "reconcile_obligations",
    "reconcile_case_manifests",
]
