"""Deterministic expansion and accounting of declared coverage obligations."""

from __future__ import annotations

import hashlib
import itertools
import json
import re
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
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
    source: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.assignments, Mapping):
            raise CoverageError("coverage obligation assignments must be a mapping")
        copied = dict(self.assignments)
        for axis_id, value in copied.items():
            if not isinstance(axis_id, str) or not axis_id:
                raise CoverageError(
                    "coverage obligation assignment keys must be non-empty strings"
                )
            if type(value) not in (type(None), bool, int, float, str):
                raise CoverageError(
                    "coverage obligation assignment values must be YAML scalars"
                )
        object.__setattr__(
            self,
            "assignments",
            MappingProxyType(copied),
        )

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
        if self.source is not None:
            document["source"] = self.source
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


_STABLE_COVERAGE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class CoverageInteractionRequirement:
    """Upstream, digest-bound assertion that factors must interact in one suite.

    The requirement is deliberately supplied independently from the coverage
    plan.  ``source_sha256`` binds the impact/knowledge artifact that owns the
    complete interaction list, so editing the plan and factor decisions
    together cannot erase a required cross without changing upstream evidence.
    Required factors are owned by the target suite.  Selector/reference
    factors are owned elsewhere and may only be reused by this explicit grant.
    """

    interaction_id: str
    target_suite_id: str
    required_factor_ids: tuple[str, ...]
    selector_factor_ids: tuple[str, ...]
    reference_factor_ids: tuple[str, ...]
    combination_policy: str
    source: str
    source_sha256: str

    def __post_init__(self) -> None:
        for value, location in (
            (self.interaction_id, "interaction_id"),
            (self.target_suite_id, "target_suite_id"),
        ):
            if not isinstance(value, str) or _STABLE_COVERAGE_ID.fullmatch(value) is None:
                raise CoverageError(
                    f"coverage interaction {location} must be a stable identifier"
                )
        for values, location, required in (
            (self.required_factor_ids, "required_factor_ids", True),
            (self.selector_factor_ids, "selector_factor_ids", False),
            (self.reference_factor_ids, "reference_factor_ids", False),
        ):
            if type(values) is not tuple or (required and not values):
                qualifier = "a non-empty tuple" if required else "a tuple"
                raise CoverageError(
                    f"coverage interaction {location} must be {qualifier}"
                )
            if len(values) != len(set(values)):
                raise CoverageError(
                    f"coverage interaction {location} contains duplicates"
                )
            for factor_id in values:
                if (
                    not isinstance(factor_id, str)
                    or _STABLE_COVERAGE_ID.fullmatch(factor_id) is None
                ):
                    raise CoverageError(
                        f"coverage interaction {location} must contain stable factor ids"
                    )
        groups = (
            set(self.required_factor_ids),
            set(self.selector_factor_ids),
            set(self.reference_factor_ids),
        )
        if groups[0] & groups[1] or groups[0] & groups[2] or groups[1] & groups[2]:
            raise CoverageError(
                "coverage interaction factor roles overlap"
            )
        if self.combination_policy not in {
            "full_cross",
            "conditional_cross",
            "boundary",
            "negative",
            "representative",
            "pairwise",
        }:
            raise CoverageError(
                "coverage interaction combination_policy is unsupported"
            )
        if not isinstance(self.source, str) or not self.source.strip():
            raise CoverageError("coverage interaction source must be non-empty")
        if (
            not isinstance(self.source_sha256, str)
            or _SHA256.fullmatch(self.source_sha256) is None
        ):
            raise CoverageError(
                "coverage interaction source_sha256 must be a lowercase SHA-256"
            )

    @classmethod
    def from_dict(
        cls,
        raw: Mapping[str, Any],
    ) -> "CoverageInteractionRequirement":
        if not isinstance(raw, Mapping):
            raise CoverageError("coverage interaction must be a mapping")
        expected = {
            "interaction_id",
            "target_suite_id",
            "required_factor_ids",
            "selector_factor_ids",
            "reference_factor_ids",
            "combination_policy",
            "source",
            "source_sha256",
        }
        missing = sorted(expected - set(raw))
        extra = sorted(str(key) for key in set(raw) - expected)
        if missing or extra:
            raise CoverageError(
                f"coverage interaction keys mismatch; missing={missing!r}, extra={extra!r}"
            )
        factor_lists: dict[str, tuple[str, ...]] = {}
        for key in (
            "required_factor_ids",
            "selector_factor_ids",
            "reference_factor_ids",
        ):
            value = raw[key]
            if not isinstance(value, Sequence) or isinstance(
                value, (str, bytes, bytearray)
            ):
                raise CoverageError(
                    f"coverage interaction {key} must be a sequence"
                )
            factor_lists[key] = tuple(value)
        return cls(
            interaction_id=raw["interaction_id"],
            target_suite_id=raw["target_suite_id"],
            required_factor_ids=factor_lists["required_factor_ids"],
            selector_factor_ids=factor_lists["selector_factor_ids"],
            reference_factor_ids=factor_lists["reference_factor_ids"],
            combination_policy=raw["combination_policy"],
            source=raw["source"],
            source_sha256=raw["source_sha256"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "interaction_id": self.interaction_id,
            "target_suite_id": self.target_suite_id,
            "required_factor_ids": list(self.required_factor_ids),
            "selector_factor_ids": list(self.selector_factor_ids),
            "reference_factor_ids": list(self.reference_factor_ids),
            "combination_policy": self.combination_policy,
            "source": self.source,
            "source_sha256": self.source_sha256,
        }


def interaction_set_sha256(
    interactions: Iterable[CoverageInteractionRequirement],
) -> str:
    """Hash the complete interaction manifest as an order-insensitive set.

    Every field participates, including the upstream source locator and its
    digest.  The expected digest must come from the independently frozen
    impact/knowledge output rather than from the coverage plan being checked.
    """

    records: list[str] = []
    for interaction in interactions:
        if not isinstance(interaction, CoverageInteractionRequirement):
            raise CoverageError(
                "interaction set must contain CoverageInteractionRequirement objects"
            )
        records.append(
            json.dumps(
                interaction.to_dict(),
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
    if len(records) != len(set(records)):
        raise CoverageError("interaction set contains a duplicate full record")
    payload = json.dumps(
        sorted(records),
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


_PROOF_FACTORY_ACTIVE: ContextVar[bool] = ContextVar(
    "mysql_case_factory_coverage_proof_factory",
    default=False,
)
_OUTCOME_COUNT_KEYS = {
    "total",
    "success",
    "expected_failure",
    "justified_na",
}


def _construct_proof(contract_type, **kwargs):
    """Construct a proof object only while its invariant gate is active."""

    token = _PROOF_FACTORY_ACTIVE.set(True)
    try:
        return contract_type(**kwargs)
    finally:
        _PROOF_FACTORY_ACTIVE.reset(token)


def _require_proof_factory(type_name: str) -> None:
    if not _PROOF_FACTORY_ACTIVE.get():
        raise CoverageError(
            f"{type_name} must be created by the internal proof factory"
        )


def _validated_stable_ids(
    values: Any,
    location: str,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if type(values) is not tuple or (not allow_empty and not values):
        qualifier = "an immutable tuple" if allow_empty else "a non-empty tuple"
        raise CoverageError(f"{location} must be {qualifier}")
    if len(values) != len(set(values)):
        raise CoverageError(f"{location} contains duplicates")
    for value in values:
        if not isinstance(value, str) or _STABLE_COVERAGE_ID.fullmatch(value) is None:
            raise CoverageError(f"{location} contains an invalid stable id")
    return values


def _validated_digest(value: Any, location: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise CoverageError(f"{location} must be a lowercase SHA-256")
    return value


def _validated_outcome_counts(
    value: Any,
    location: str,
    expected_total: int,
) -> Mapping[str, int]:
    if not isinstance(value, Mapping) or set(value) != _OUTCOME_COUNT_KEYS:
        raise CoverageError(f"{location} must contain exact outcome count keys")
    copied = dict(value)
    if any(type(item) is not int or item < 0 for item in copied.values()):
        raise CoverageError(f"{location} values must be non-negative integers")
    if copied["total"] != expected_total:
        raise CoverageError(f"{location}.total does not match proof count")
    if copied["total"] != (
        copied["success"]
        + copied["expected_failure"]
        + copied["justified_na"]
    ):
        raise CoverageError(f"{location} outcome accounting is inconsistent")
    return MappingProxyType(copied)


def _validated_string_mapping(
    value: Any,
    location: str,
    *,
    value_is_digest: bool = False,
) -> Mapping[str, str]:
    if not isinstance(value, Mapping):
        raise CoverageError(f"{location} must be a mapping")
    copied = dict(value)
    for key, item in copied.items():
        if not isinstance(key, str) or _STABLE_COVERAGE_ID.fullmatch(key) is None:
            raise CoverageError(f"{location} has an invalid key")
        if not isinstance(item, str) or not item:
            raise CoverageError(f"{location}.{key} must be a non-empty string")
        if value_is_digest:
            _validated_digest(item, f"{location}.{key}")
        elif _STABLE_COVERAGE_ID.fullmatch(item) is None:
            raise CoverageError(f"{location}.{key} must be a stable id")
    return MappingProxyType(copied)


def _validated_positive_int_mapping(
    value: Any,
    location: str,
) -> Mapping[str, int]:
    if not isinstance(value, Mapping):
        raise CoverageError(f"{location} must be a mapping")
    copied = dict(value)
    for key, item in copied.items():
        if not isinstance(key, str) or _STABLE_COVERAGE_ID.fullmatch(key) is None:
            raise CoverageError(f"{location} has an invalid key")
        if type(item) is not int or item < 1:
            raise CoverageError(f"{location}.{key} must be a positive integer")
    return MappingProxyType(copied)


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

    def __post_init__(self) -> None:
        _require_proof_factory(type(self).__name__)
        if not isinstance(self.condition_assignment, Mapping):
            raise CoverageError("condition proof assignment must be a mapping")
        condition_copy = dict(self.condition_assignment)
        for axis_id, value in condition_copy.items():
            if (
                not isinstance(axis_id, str)
                or _STABLE_COVERAGE_ID.fullmatch(axis_id) is None
                or type(value) not in (type(None), bool, int, float, str)
            ):
                raise CoverageError("condition proof assignment is not canonical")
        primary_axes = _validated_stable_ids(
            self.primary_axes,
            "condition proof primary_axes",
        )
        for value, location in (
            (self.theoretical_count, "condition proof theoretical_count"),
            (self.actual_count, "condition proof actual_count"),
        ):
            if type(value) is not int or value < 1:
                raise CoverageError(f"{location} must be a positive integer")
        theoretical_sha256 = _validated_digest(
            self.theoretical_sha256,
            "condition proof theoretical_sha256",
        )
        actual_sha256 = _validated_digest(
            self.actual_sha256,
            "condition proof actual_sha256",
        )
        expected_counts = _validated_outcome_counts(
            self.expected_outcome_counts,
            "condition proof expected_outcome_counts",
            self.theoretical_count,
        )
        actual_counts = _validated_outcome_counts(
            self.outcome_counts,
            "condition proof outcome_counts",
            self.actual_count,
        )
        for values, location in (
            (self.missing_assignments, "condition proof missing_assignments"),
            (self.unexpected_assignments, "condition proof unexpected_assignments"),
        ):
            if type(values) is not tuple or any(
                not isinstance(item, str) for item in values
            ):
                raise CoverageError(f"{location} must be an immutable string tuple")
            if values:
                raise CoverageError(f"{location} must be empty for a proof")
        if (
            self.theoretical_count != self.actual_count
            or theoretical_sha256 != actual_sha256
            or dict(expected_counts) != dict(actual_counts)
        ):
            raise CoverageError("condition proof invariants are incomplete")
        object.__setattr__(
            self,
            "condition_assignment",
            MappingProxyType(condition_copy),
        )
        object.__setattr__(self, "primary_axes", primary_axes)
        object.__setattr__(self, "expected_outcome_counts", expected_counts)
        object.__setattr__(self, "outcome_counts", actual_counts)

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

    def __post_init__(self) -> None:
        _require_proof_factory(type(self).__name__)
        if (
            not isinstance(self.test_point_id, str)
            or _STABLE_COVERAGE_ID.fullmatch(self.test_point_id) is None
        ):
            raise CoverageError("contract proof test_point_id must be stable")
        if self.combination_policy not in ("full_cross", "conditional_cross"):
            raise CoverageError("contract proof combination_policy is not exact")
        primary_axes = _validated_stable_ids(
            self.primary_axes,
            "contract proof primary_axes",
        )
        condition_axes = _validated_stable_ids(
            self.condition_axes,
            "contract proof condition_axes",
            allow_empty=True,
        )
        if set(primary_axes) & set(condition_axes):
            raise CoverageError("contract proof axes overlap")
        if self.combination_policy == "full_cross" and condition_axes:
            raise CoverageError("full_cross proof cannot contain condition axes")
        if self.combination_policy == "conditional_cross" and not condition_axes:
            raise CoverageError("conditional_cross proof requires condition axes")
        all_axes = primary_axes + condition_axes
        inventory_counts = _validated_positive_int_mapping(
            self.axis_inventory_counts,
            "contract proof axis_inventory_counts",
        )
        inventory_digests = _validated_string_mapping(
            self.axis_inventory_sha256,
            "contract proof axis_inventory_sha256",
            value_is_digest=True,
        )
        if set(inventory_counts) != set(all_axes) or set(inventory_digests) != set(
            all_axes
        ):
            raise CoverageError("contract proof inventory bindings do not match axes")
        cartesian_count = 1
        for axis_id in all_axes:
            cartesian_count *= inventory_counts[axis_id]
        for value, location in (
            (self.theoretical_count, "contract proof theoretical_count"),
            (self.actual_count, "contract proof actual_count"),
        ):
            if type(value) is not int or value < 1:
                raise CoverageError(f"{location} must be a positive integer")
        if self.theoretical_count != cartesian_count:
            raise CoverageError(
                "contract proof theoretical_count does not match inventory product"
            )
        theoretical_sha256 = _validated_digest(
            self.theoretical_sha256,
            "contract proof theoretical_sha256",
        )
        actual_sha256 = _validated_digest(
            self.actual_sha256,
            "contract proof actual_sha256",
        )
        expected_counts = _validated_outcome_counts(
            self.expected_outcome_counts,
            "contract proof expected_outcome_counts",
            self.theoretical_count,
        )
        actual_counts = _validated_outcome_counts(
            self.outcome_counts,
            "contract proof outcome_counts",
            self.actual_count,
        )
        if type(self.condition_proofs) is not tuple or not self.condition_proofs:
            raise CoverageError("contract proof condition_proofs must be non-empty")
        if any(
            not isinstance(item, CoverageConditionProof) or not item.complete
            for item in self.condition_proofs
        ):
            raise CoverageError("contract proof contains a malformed condition proof")
        condition_keys = [
            _assignment_key(item.condition_assignment)
            for item in self.condition_proofs
        ]
        if len(condition_keys) != len(set(condition_keys)):
            raise CoverageError("contract proof contains duplicate condition assignments")
        for item in self.condition_proofs:
            if item.primary_axes != primary_axes or set(item.condition_assignment) != set(
                condition_axes
            ):
                raise CoverageError("condition proof axes do not match contract proof")
        primary_count = 1
        for axis_id in primary_axes:
            primary_count *= inventory_counts[axis_id]
        expected_condition_count = 1
        for axis_id in condition_axes:
            expected_condition_count *= inventory_counts[axis_id]
        if len(self.condition_proofs) != expected_condition_count or any(
            item.theoretical_count != primary_count
            for item in self.condition_proofs
        ):
            raise CoverageError(
                "condition proof cardinalities do not match inventory bindings"
            )
        if sum(item.theoretical_count for item in self.condition_proofs) != self.theoretical_count:
            raise CoverageError("condition proof counts do not reconcile to contract proof")
        for outcome in _OUTCOME_COUNT_KEYS:
            if outcome == "total":
                continue
            if sum(
                item.expected_outcome_counts[outcome]
                for item in self.condition_proofs
            ) != expected_counts[outcome]:
                raise CoverageError(
                    "condition proof outcome counts do not reconcile to contract proof"
                )
        for values, location in (
            (self.missing_assignments, "contract proof missing_assignments"),
            (self.unexpected_assignments, "contract proof unexpected_assignments"),
        ):
            if type(values) is not tuple or any(
                not isinstance(item, str) for item in values
            ):
                raise CoverageError(f"{location} must be an immutable string tuple")
            if values:
                raise CoverageError(f"{location} must be empty for a proof")
        if (
            self.theoretical_count != self.actual_count
            or theoretical_sha256 != actual_sha256
            or dict(expected_counts) != dict(actual_counts)
        ):
            raise CoverageError("contract proof invariants are incomplete")
        object.__setattr__(self, "primary_axes", primary_axes)
        object.__setattr__(self, "condition_axes", condition_axes)
        object.__setattr__(self, "axis_inventory_counts", inventory_counts)
        object.__setattr__(self, "axis_inventory_sha256", inventory_digests)
        object.__setattr__(self, "expected_outcome_counts", expected_counts)
        object.__setattr__(self, "outcome_counts", actual_counts)

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
    interaction_source_sha256_by_id: Mapping[str, str]
    expected_interaction_set_sha256: Optional[str]
    actual_interaction_set_sha256: Optional[str]
    interaction_manifest_reconciled: bool

    def __post_init__(self) -> None:
        _require_proof_factory(type(self).__name__)
        if type(self.obligations) is not tuple or any(
            not isinstance(item, CoverageObligation) for item in self.obligations
        ):
            raise CoverageError("coverage compilation obligations must be a typed tuple")
        obligation_ids = [item.obligation_id for item in self.obligations]
        if len(obligation_ids) != len(set(obligation_ids)):
            raise CoverageError("coverage compilation contains duplicate obligation ids")
        if any(
            not isinstance(item, str) or not item
            for item in obligation_ids
        ):
            raise CoverageError("coverage compilation has an invalid obligation id")
        if len({item.plan_id for item in self.obligations}) > 1:
            raise CoverageError("coverage compilation obligations span multiple plans")
        if type(self.contract_proofs) is not tuple or any(
            not isinstance(item, CoverageContractProof) or not item.complete
            for item in self.contract_proofs
        ):
            raise CoverageError("coverage compilation contract_proofs are malformed")
        proof_ids = [item.test_point_id for item in self.contract_proofs]
        if len(proof_ids) != len(set(proof_ids)):
            raise CoverageError("coverage compilation contains duplicate point proofs")
        legacy_ids = _validated_stable_ids(
            self.legacy_test_point_ids,
            "coverage compilation legacy_test_point_ids",
            allow_empty=True,
        )
        if set(proof_ids) & set(legacy_ids):
            raise CoverageError("coverage compilation proof and legacy point ids overlap")
        known_point_ids = set(proof_ids) | set(legacy_ids)
        if any(
            obligation.test_point_id not in known_point_ids
            for obligation in self.obligations
        ):
            raise CoverageError(
                "coverage compilation obligation references an unproved point"
            )
        factor_owners = _validated_string_mapping(
            self.factor_owner_by_id,
            "coverage compilation factor_owner_by_id",
        )
        interaction_sources = _validated_string_mapping(
            self.interaction_source_sha256_by_id,
            "coverage compilation interaction_source_sha256_by_id",
            value_is_digest=True,
        )
        if type(self.interaction_manifest_reconciled) is not bool:
            raise CoverageError(
                "coverage compilation interaction_manifest_reconciled must be bool"
            )
        if self.contract_proofs:
            expected_owned_factors = {
                axis_id
                for proof in self.contract_proofs
                for axis_id in proof.primary_axes
            }
            if set(factor_owners) != expected_owned_factors:
                raise CoverageError(
                    "coverage compilation factor owners do not match primary factors"
                )
            if len(interaction_sources) != len(self.contract_proofs):
                raise CoverageError(
                    "coverage compilation interaction records do not reconcile to proofs"
                )
            for proof in self.contract_proofs:
                if sum(
                    obligation.test_point_id == proof.test_point_id
                    for obligation in self.obligations
                ) != proof.actual_count:
                    raise CoverageError(
                        "coverage compilation obligation counts do not match proofs"
                    )
            expected_digest = _validated_digest(
                self.expected_interaction_set_sha256,
                "coverage compilation expected_interaction_set_sha256",
            )
            actual_digest = _validated_digest(
                self.actual_interaction_set_sha256,
                "coverage compilation actual_interaction_set_sha256",
            )
            if (
                expected_digest != actual_digest
                or not self.interaction_manifest_reconciled
                or not interaction_sources
                or not factor_owners
            ):
                raise CoverageError("coverage compilation proof bundle is incomplete")
        else:
            expected_digest = self.expected_interaction_set_sha256
            actual_digest = self.actual_interaction_set_sha256
            if (
                expected_digest is not None
                or actual_digest is not None
                or interaction_sources
                or factor_owners
            ):
                raise CoverageError(
                    "legacy coverage compilation cannot contain v2 proof bindings"
                )
        object.__setattr__(self, "legacy_test_point_ids", legacy_ids)
        object.__setattr__(self, "factor_owner_by_id", factor_owners)
        object.__setattr__(
            self,
            "interaction_source_sha256_by_id",
            interaction_sources,
        )

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
            and self.interaction_manifest_reconciled
            and self.expected_interaction_set_sha256 is not None
            and self.actual_interaction_set_sha256
            == self.expected_interaction_set_sha256
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "obligations": [item.to_dict() for item in self.obligations],
            "contract_proofs": [item.to_dict() for item in self.contract_proofs],
            "legacy_test_point_ids": list(self.legacy_test_point_ids),
            "factor_owner_by_id": dict(self.factor_owner_by_id),
            "interaction_source_sha256_by_id": dict(
                self.interaction_source_sha256_by_id
            ),
            "expected_interaction_set_sha256": self.expected_interaction_set_sha256,
            "actual_interaction_set_sha256": self.actual_interaction_set_sha256,
            "interaction_manifest_reconciled": self.interaction_manifest_reconciled,
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


def _canonical_validated_plan(plan: CoveragePlan) -> CoveragePlan:
    """Reparse a plan so mutable nested state cannot bypass constructors.

    ``validate_coverage_plan`` checks cross references, while the canonical
    parser independently recomputes every axis count and inventory digest.
    Both proof boundaries call this helper before consulting any plan field.
    """

    if not isinstance(plan, CoveragePlan):
        raise CoverageError("coverage proof requires a CoveragePlan")
    canonical = CoveragePlan.from_dict(plan.to_dict())
    validate_coverage_plan(canonical)
    return canonical


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

    supplied_point = point
    plan = _canonical_validated_plan(plan)
    matching_points = tuple(
        candidate
        for candidate in plan.test_points
        if candidate.test_point_id == supplied_point.test_point_id
    )
    if (
        len(matching_points) != 1
        or matching_points[0].to_dict() != supplied_point.to_dict()
    ):
        raise CoverageError(
            f"test point {supplied_point.test_point_id} is not the validated point "
            f"from plan {plan.plan_id}"
        )
    point = matching_points[0]
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

        expected_outcome, expected_reason, expected_source = _classify(
            point, obligation.assignments
        )
        if (
            obligation.outcome != expected_outcome
            or obligation.reason != expected_reason
            or obligation.source != expected_source
        ):
            raise CoverageError(
                f"obligation {obligation.obligation_id} outcome/reason/source does not match "
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
            _construct_proof(
                CoverageConditionProof,
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

    proof = _construct_proof(
        CoverageContractProof,
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


def _normalize_interaction_requirements(
    interaction_requirements: Sequence[CoverageInteractionRequirement]
    | Mapping[str, CoverageInteractionRequirement],
) -> tuple[CoverageInteractionRequirement, ...]:
    if isinstance(interaction_requirements, Mapping):
        interactions = tuple(interaction_requirements.values())
        mismatched_keys = sorted(
            str(key)
            for key, interaction in interaction_requirements.items()
            if not isinstance(interaction, CoverageInteractionRequirement)
            or key != interaction.interaction_id
        )
        if mismatched_keys:
            raise CoverageError(
                "interaction requirement mapping keys must equal interaction_id: "
                + ", ".join(mismatched_keys)
            )
    elif isinstance(interaction_requirements, Sequence) and not isinstance(
        interaction_requirements, (str, bytes, bytearray)
    ):
        interactions = tuple(interaction_requirements)
    else:
        raise CoverageError(
            "interaction_requirements must be a sequence or mapping"
        )
    if any(
        not isinstance(item, CoverageInteractionRequirement)
        for item in interactions
    ):
        raise CoverageError(
            "interaction_requirements must contain CoverageInteractionRequirement objects"
        )
    seen: set[str] = set()
    for interaction in interactions:
        if interaction.interaction_id in seen:
            raise CoverageError(
                f"duplicate coverage interaction {interaction.interaction_id}"
            )
        seen.add(interaction.interaction_id)
    return interactions


def compile_coverage_plan(
    plan: CoveragePlan,
    factor_decisions: Sequence[FactorDecision] | Mapping[str, FactorDecision],
    obligations: Optional[Iterable[CoverageObligation]] = None,
    interaction_requirements: Sequence[CoverageInteractionRequirement]
    | Mapping[str, CoverageInteractionRequirement] = (),
    expected_interaction_set_sha256: Optional[str] = None,
) -> CoverageCompilation:
    """Bind upstream interactions, factor ownership, and exact v2 proofs.

    Interaction requirements come from the independently digest-bound impact
    or knowledge artifact.  The coverage plan is only a consumer of that list;
    it cannot make a required multi-factor interaction disappear by editing its
    own suites and factor dependencies in concert.
    """

    plan = _canonical_validated_plan(plan)
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
    interactions = _normalize_interaction_requirements(interaction_requirements)
    if not contracted:
        if interactions or expected_interaction_set_sha256 is not None:
            raise CoverageError(
                "legacy coverage plan cannot consume v2 interaction requirements"
            )
        return _construct_proof(
            CoverageCompilation,
            obligations=actual,
            contract_proofs=(),
            legacy_test_point_ids=legacy_ids,
            factor_owner_by_id={},
            interaction_source_sha256_by_id={},
            expected_interaction_set_sha256=None,
            actual_interaction_set_sha256=None,
            interaction_manifest_reconciled=True,
        )
    if not decisions:
        raise CoverageError("contracted coverage plan requires factor decisions")
    if not interactions or expected_interaction_set_sha256 is None:
        raise CoverageError(
            "contracted coverage plan requires a complete interaction manifest "
            "and expected_interaction_set_sha256"
        )
    if (
        not isinstance(expected_interaction_set_sha256, str)
        or _SHA256.fullmatch(expected_interaction_set_sha256) is None
    ):
        raise CoverageError(
            "expected_interaction_set_sha256 must be a lowercase SHA-256"
        )
    actual_interaction_digest = interaction_set_sha256(interactions)
    if actual_interaction_digest != expected_interaction_set_sha256:
        raise CoverageError(
            "interaction manifest digest does not match expected "
            "interaction set digest"
        )

    decision_by_factor = {item.factor_id: item for item in decisions}
    contracted_by_id = {point.test_point_id: point for point in contracted}
    suite_binding_counts: dict[str, int] = {}
    for interaction in interactions:
        suite_binding_counts[interaction.target_suite_id] = (
            suite_binding_counts.get(interaction.target_suite_id, 0) + 1
        )
    contracted_suite_ids = set(contracted_by_id)
    missing_suite_ids = sorted(
        suite_id
        for suite_id in contracted_suite_ids
        if suite_binding_counts.get(suite_id, 0) == 0
    )
    extra_suite_ids = sorted(set(suite_binding_counts) - contracted_suite_ids)
    duplicate_suite_ids = sorted(
        suite_id
        for suite_id, count in suite_binding_counts.items()
        if count > 1
    )
    if missing_suite_ids:
        raise CoverageError(
            "interaction manifest missing contracted suite "
            + ", ".join(missing_suite_ids)
        )
    if extra_suite_ids:
        raise CoverageError(
            "interaction manifest has extra suite " + ", ".join(extra_suite_ids)
        )
    if duplicate_suite_ids:
        raise CoverageError(
            "interaction manifest has duplicate suite binding "
            + ", ".join(duplicate_suite_ids)
        )
    axes_in_contracts = {
        axis_id
        for point in contracted
        for axis_id in (
            point.coverage_contract.primary_axes
            + point.coverage_contract.condition_axes
        )
    }
    for axis_id in sorted(axes_in_contracts):
        decision = decision_by_factor.get(axis_id)
        if decision is None:
            raise CoverageError(f"contracted factor {axis_id} has no factor decision")
        if decision.status != "covered" or decision.review_state != "reviewed":
            raise CoverageError(
                f"contracted factor {axis_id} requires a reviewed covered decision"
            )
        axis = plan.axes[axis_id]
        if (
            decision.inventory_source != axis.inventory_source
            or decision.inventory_sha256 != axis.inventory_sha256
        ):
            raise CoverageError(
                f"factor {axis_id} inventory binding does not match coverage axis"
            )

    owner_by_factor = {
        decision.factor_id: decision.owning_suite_id
        for decision in decisions
        if decision.status == "covered"
    }
    interactions_by_target: dict[str, list[CoverageInteractionRequirement]] = {}
    for interaction in interactions:
        point = contracted_by_id.get(interaction.target_suite_id)
        if point is None:
            raise CoverageError(
                f"interaction {interaction.interaction_id} target suite "
                f"{interaction.target_suite_id} is not a contracted suite"
            )
        contract = point.coverage_contract
        assert contract is not None
        if interaction.combination_policy != contract.combination_policy:
            raise CoverageError(
                f"interaction {interaction.interaction_id} policy "
                f"{interaction.combination_policy} does not match target suite "
                f"policy {contract.combination_policy}"
            )
        non_owners = (
            interaction.selector_factor_ids + interaction.reference_factor_ids
        )
        if (
            interaction.required_factor_ids != contract.primary_axes
            or non_owners != contract.condition_axes
        ):
            raise CoverageError(
                f"interaction {interaction.interaction_id} required factors and "
                "selector/reference factors must match one target suite contract"
            )
        for factor_id in interaction.required_factor_ids + non_owners:
            decision = decision_by_factor.get(factor_id)
            if decision is None:
                raise CoverageError(
                    f"interaction {interaction.interaction_id} references factor "
                    f"{factor_id} without a factor decision"
                )
        for factor_id in interaction.required_factor_ids:
            owner = owner_by_factor.get(factor_id)
            if owner != interaction.target_suite_id:
                raise CoverageError(
                    f"factor {factor_id} owning suite {owner} does not match "
                    f"contracted suite {interaction.target_suite_id}; interaction "
                    f"{interaction.interaction_id} required factors must be owned "
                    "by one target suite"
                )
        for factor_id in non_owners:
            if owner_by_factor.get(factor_id) == interaction.target_suite_id:
                raise CoverageError(
                    f"selector/reference factor {factor_id} cannot be owned by "
                    f"target suite {interaction.target_suite_id}"
                )
        interactions_by_target.setdefault(point.test_point_id, []).append(interaction)

    # Ownership credit comes only from FactorDecision.owning_suite_id.  An
    # occurrence in another suite is legal only as a separately authorized
    # selector/reference and never changes the owner map.
    for point in contracted:
        contract = point.coverage_contract
        assert contract is not None
        target_interactions = interactions_by_target.get(point.test_point_id, [])
        if len(target_interactions) != 1:
            # Reconciliation above is intentionally repeated defensively at
            # the point of use: no contracted suite is ever proved against an
            # implicit or ambiguous interaction record.
            raise CoverageError(
                f"suite {point.test_point_id} must match exactly one "
                "coverage interaction"
            )
        allowed_references = {
            factor_id
            for interaction in target_interactions
            for factor_id in (
                interaction.selector_factor_ids
                + interaction.reference_factor_ids
            )
        }
        for axis_id in contract.primary_axes + contract.condition_axes:
            owner = owner_by_factor.get(axis_id)
            if owner != point.test_point_id and axis_id not in allowed_references:
                raise CoverageError(
                    f"unapproved factor reuse in suite {point.test_point_id}: {axis_id}"
                )

    # Every covered decision owns exactly one factor in the primary axes of its
    # declared suite.  Merely appearing as a selector cannot confer ownership.
    for decision in decisions:
        if decision.status != "covered":
            continue
        owner_point = contracted_by_id.get(decision.owning_suite_id)
        if owner_point is None:
            raise CoverageError(
                f"factor {decision.factor_id} owning suite "
                f"{decision.owning_suite_id} is not a contracted suite"
            )
        owner_contract = owner_point.coverage_contract
        assert owner_contract is not None
        if decision.factor_id not in owner_contract.primary_axes:
            raise CoverageError(
                f"factor {decision.factor_id} cannot claim ownership in suite "
                f"{decision.owning_suite_id}; it is not a required primary factor"
            )
        if decision.combination_strategy != owner_contract.combination_policy:
            raise CoverageError(
                f"factor {decision.factor_id} policy {decision.combination_strategy} "
                f"does not match owner suite policy "
                f"{owner_contract.combination_policy}"
            )

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
    return _construct_proof(
        CoverageCompilation,
        obligations=actual,
        contract_proofs=proofs,
        legacy_test_point_ids=legacy_ids,
        factor_owner_by_id=owner_by_factor,
        interaction_source_sha256_by_id={
            interaction.interaction_id: interaction.source_sha256
            for interaction in interactions
        },
        expected_interaction_set_sha256=expected_interaction_set_sha256,
        actual_interaction_set_sha256=actual_interaction_digest,
        interaction_manifest_reconciled=True,
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
) -> tuple[Optional[str], Optional[str], Optional[str]]:
    matching = [rule for rule in point.classification_rules if _matches(assignments, rule.when)]
    if len(matching) > 1:
        classifications = {
            (rule.outcome, rule.reason, rule.source) for rule in matching
        }
        if len(classifications) > 1:
            raise CoverageError(
                f"test point {point.test_point_id} assignment {dict(assignments)!r} "
                "matches conflicting classification rules"
            )
    if matching:
        outcome = matching[0].outcome
        reason = matching[0].reason
        source = matching[0].source
    else:
        outcome = point.default_outcome
        reason = point.default_reason
        source = point.default_source

    if outcome is not None and outcome not in COVERAGE_OUTCOMES:
        raise CoverageError(
            f"test point {point.test_point_id} has unsupported outcome {outcome!r}"
        )
    if outcome in ("expected_failure", "justified_na") and not reason:
        raise CoverageError(f"{outcome} classification requires a reason")
    if (
        point.coverage_contract is not None
        and outcome in ("expected_failure", "justified_na")
        and not source
    ):
        raise CoverageError(
            f"contracted {outcome} classification requires a source"
        )
    return outcome, reason, source


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
        outcome, reason, source = _classify(point, assignments)
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
                source=source,
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
    "CoverageInteractionRequirement",
    "interaction_set_sha256",
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
