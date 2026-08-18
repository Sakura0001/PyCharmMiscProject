from __future__ import annotations

import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import PurePosixPath
from typing import Any

from .artifacts import ArtifactBinding, build_artifact
from .errors import CoverageV2StateError
from .schema_registry import ArtifactSchemaRegistry


SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")


class PlanningState(str, Enum):
    DISCOVERED = "discovered"
    INPUTS_LOCKED = "inputs_locked"
    READINESS_PASSED = "readiness_passed"
    LEDGERS_ENUMERATED = "ledgers_enumerated"
    INTERACTION_UNIVERSE_FROZEN = "interaction_universe_frozen"
    PRODUCTS_PARTITIONED = "products_partitioned"
    ATOMS_COMPILED = "atoms_compiled"
    FIXTURES_PLANNED = "fixtures_planned"
    PACKING_FROZEN = "packing_frozen"
    MAPPING_FROZEN = "mapping_frozen"
    WITNESSES_BOUND = "witnesses_bound"
    LOCAL_PLAN_VALIDATED = "local_plan_validated"
    GLOBAL_HANDOFF_CLOSED = "global_handoff_closed"
    PLAN_APPROVED = "plan_approved"
    GENERATION_ALLOWED = "generation_allowed"
    GENERATING = "generating"
    GENERATED = "generated"
    STATICALLY_VALIDATED = "statically_validated"
    PACKAGED = "packaged"


class RuntimeState(str, Enum):
    NOT_RUN = "not_run"
    RUNNING = "running"
    RUNTIME_EXECUTED = "runtime_executed"
    RUNTIME_VERIFIED = "runtime_verified"
    RUNTIME_FAILED = "runtime_failed"


class Origin(str, Enum):
    NATIVE_V2 = "native_v2"
    LEGACY_IMPORT = "legacy_import"


@dataclass(frozen=True)
class FailureState:
    failed_stage: PlanningState
    reason: str
    retryable: bool


@dataclass(frozen=True)
class CoverageState:
    planning_state: PlanningState
    runtime_state: RuntimeState
    origin: Origin
    failure_state: FailureState | None
    package_semantic_sha256: str | None

    @classmethod
    def discovered(cls, *, origin: Origin) -> "CoverageState":
        if not isinstance(origin, Origin):
            raise CoverageV2StateError("coverage state origin must be frozen")
        return cls(
            planning_state=PlanningState.DISCOVERED,
            runtime_state=RuntimeState.NOT_RUN,
            origin=origin,
            failure_state=None,
            package_semantic_sha256=None,
        )


PLANNING_SEQUENCE = tuple(PlanningState)


PLANNING_EVIDENCE: Mapping[PlanningState, Counter[str]] = {
    PlanningState.INPUTS_LOCKED: Counter({"input-lock": 2}),
    PlanningState.READINESS_PASSED: Counter({"readiness": 1}),
    PlanningState.LEDGERS_ENUMERATED: Counter(
        {
            "source-universe": 1,
            "source-consumption": 1,
            "grammar-ledger": 1,
            "factor-obligation-ledger": 1,
            "applicability": 1,
            "na-ledger": 1,
            "risk-ledger": 1,
        }
    ),
    PlanningState.INTERACTION_UNIVERSE_FROZEN: Counter(
        {"canonical-intents": 1, "intent-axis-ledger": 1, "interaction-tuples": 1}
    ),
    PlanningState.PRODUCTS_PARTITIONED: Counter({"interaction-products": 1}),
    PlanningState.ATOMS_COMPILED: Counter({"atoms": 1}),
    PlanningState.FIXTURES_PLANNED: Counter({"fixture-plan": 1}),
    PlanningState.PACKING_FROZEN: Counter({"packing-plan": 1}),
    PlanningState.MAPPING_FROZEN: Counter({"subcase-mapping": 1}),
    PlanningState.WITNESSES_BOUND: Counter({"obligation-witness-index": 1}),
    PlanningState.LOCAL_PLAN_VALIDATED: Counter(
        {"plan-content-manifest": 1, "plan-validation": 1}
    ),
    PlanningState.GLOBAL_HANDOFF_CLOSED: Counter({"handoff-validation": 1}),
    PlanningState.PLAN_APPROVED: Counter({"approval": 1}),
    PlanningState.GENERATION_ALLOWED: Counter({"generation-contract": 1}),
    PlanningState.GENERATING: Counter({"shard-jobs": 1}),
    PlanningState.GENERATED: Counter(
        {"jobs-final-snapshot": 1, "schedule-manifest": 1}
    ),
    PlanningState.STATICALLY_VALIDATED: Counter(
        {
            "actual-factor-witness-report": 1,
            "actual-semantic-interaction-report": 1,
            "actual-handoff-validation": 1,
            "validation-report": 1,
            "regeneration-report": 1,
        }
    ),
    PlanningState.PACKAGED: Counter(
        {"package-manifest": 1, "final-validation": 1}
    ),
}


RUNTIME_EVIDENCE: Mapping[tuple[RuntimeState, RuntimeState], Counter[str]] = {
    (RuntimeState.NOT_RUN, RuntimeState.RUNNING): Counter(
        {"package-manifest": 1, "run-contract": 1}
    ),
    (RuntimeState.RUNNING, RuntimeState.RUNTIME_EXECUTED): Counter(
        {"execution-manifest": 1, "route-result": 1, "logs-manifest": 1}
    ),
    (RuntimeState.RUNTIME_EXECUTED, RuntimeState.RUNTIME_VERIFIED): Counter(
        {"runtime-validation": 1}
    ),
    (RuntimeState.RUNNING, RuntimeState.RUNTIME_FAILED): Counter(
        {"cleanup-summary": 1, "restore-summary": 1}
    ),
    (RuntimeState.RUNTIME_EXECUTED, RuntimeState.RUNTIME_FAILED): Counter(
        {"cleanup-summary": 1, "restore-summary": 1}
    ),
    (RuntimeState.RUNTIME_FAILED, RuntimeState.RUNNING): Counter(
        {"package-manifest": 1, "run-contract": 1, "clean-state-report": 1}
    ),
}


REQUIRED_SCHEMA_KINDS = frozenset(
    {
        "input-lock", "current-pointer", "statement-order", "generation-order", "progress",
        "source-universe", "source-consumption", "readiness", "catalog-oracle-allowlist",
        "grammar-ledger", "factor-obligation-ledger", "na-ledger", "risk-ledger",
        "applicability", "canonical-intents", "intent-axis-ledger", "interaction-products",
        "interaction-tuples", "atoms", "fixture-plan", "packing-plan", "subcase-mapping",
        "obligation-witness-index", "plan-content-manifest", "plan-validation",
        "selected-statement-revisions", "handoff-ledger", "handoff-validation", "approval",
        "generation-contract", "global-mapping", "global-batch-manifest",
        "selected-statement-packages", "global-mapping-index", "global-by-factor-manifest",
        "global-schedule-index", "global-payload-index", "global-validation", "global-package",
        "shard-assignment", "shard-jobs", "publish-candidate", "payload-manifest",
        "published-payload-index", "shard-validation-report", "jobs-final-snapshot",
        "schedule-manifest", "session-profile-manifest", "runner-operation-manifest",
        "multi-session-harness", "restart-external-manifest", "actual-factor-witness-report",
        "actual-semantic-interaction-report", "actual-handoff-validation",
        "semantic-validator-mutation-report", "validation-report", "regeneration-report",
        "package-manifest", "final-validation", "run-contract", "execution-manifest",
        "runtime-profile", "normalization-policy", "route-result", "logs-manifest",
        "clean-state-report", "cleanup-report", "restore-report", "cleanup-summary",
        "restore-summary", "two-run-comparison", "runtime-validation",
        "global-completion-report",
    }
)


REQUIRED_NON_SCHEMA_COMPONENTS = frozenset(
    {
        "statement-branch-consumer-catalog",
        "canonical-target-intent-catalog",
        "statement-check-order-catalog",
        "route-runner-registry",
        "semantic-extractor-registry",
        "catalog-oracle-allowlist",
        "semantic-validator-mutation-suite",
        "phase-aware-serial-runner",
        "parallel-runner",
        "multi-session-runner",
        "restart-external-runner",
        "coverage-v2-cli",
    }
)


def _validate_evidence(
    evidence: Sequence[ArtifactBinding],
    required: Counter[str],
) -> tuple[ArtifactBinding, ...]:
    if any(not isinstance(binding, ArtifactBinding) for binding in evidence):
        raise CoverageV2StateError("state evidence must be verified ArtifactBinding records")
    if len({binding.artifact_id for binding in evidence}) != len(evidence):
        raise CoverageV2StateError("state evidence contains duplicate artifact IDs")
    for binding in evidence:
        if binding.schema_version != 2:
            raise CoverageV2StateError("state evidence uses the wrong schema version")
        if SHA256_HEX.fullmatch(binding.byte_sha256) is None:
            raise CoverageV2StateError("state evidence byte SHA is invalid")
        if SHA256_HEX.fullmatch(binding.semantic_sha256) is None:
            raise CoverageV2StateError("state evidence semantic SHA is invalid")
    actual = Counter(binding.kind for binding in evidence)
    if actual != required:
        raise CoverageV2StateError(
            f"state evidence kind multiset differs: required={dict(required)}, actual={dict(actual)}"
        )
    return tuple(sorted(evidence, key=lambda item: item.artifact_id.encode("utf-8")))


def advance_planning_state(
    state: CoverageState,
    target: PlanningState,
    *,
    evidence: Sequence[ArtifactBinding],
) -> CoverageState:
    if state.failure_state is not None:
        raise CoverageV2StateError("failed state must be explicitly retried")
    try:
        current_index = PLANNING_SEQUENCE.index(state.planning_state)
        target_index = PLANNING_SEQUENCE.index(target)
    except ValueError as exc:  # pragma: no cover - enums make this defensive.
        raise CoverageV2StateError("planning state is not frozen") from exc
    if target_index != current_index + 1:
        raise CoverageV2StateError("planning transitions must advance exactly one edge")
    _validate_evidence(evidence, PLANNING_EVIDENCE[target])
    return replace(state, planning_state=target)


def record_failure(
    state: CoverageState,
    *,
    failed_stage: PlanningState,
    reason: str,
    retryable: bool,
) -> CoverageState:
    if state.failure_state is not None:
        raise CoverageV2StateError("an unresolved failure already exists")
    current_index = PLANNING_SEQUENCE.index(state.planning_state)
    if PLANNING_SEQUENCE.index(failed_stage) != current_index + 1:
        raise CoverageV2StateError("failure must identify the next unproven stage")
    if not isinstance(reason, str) or not reason:
        raise CoverageV2StateError("failure reason must be non-empty")
    return replace(
        state,
        failure_state=FailureState(failed_stage, reason, bool(retryable)),
    )


def retry_failure(
    state: CoverageState,
    *,
    evidence: Sequence[ArtifactBinding],
) -> CoverageState:
    failure = state.failure_state
    if failure is None or not failure.retryable:
        raise CoverageV2StateError("state has no retryable failure")
    cleared = replace(state, failure_state=None)
    return advance_planning_state(cleared, failure.failed_stage, evidence=evidence)


def advance_runtime_state(
    state: CoverageState,
    target: RuntimeState,
    *,
    evidence: Sequence[ArtifactBinding],
    package_semantic_sha256: str | None = None,
) -> CoverageState:
    if state.planning_state != PlanningState.PACKAGED:
        raise CoverageV2StateError("runtime cannot start before static package completion")
    edge = (state.runtime_state, target)
    if edge not in RUNTIME_EVIDENCE:
        raise CoverageV2StateError("runtime transition edge is not allowed")
    checked = _validate_evidence(evidence, RUNTIME_EVIDENCE[edge])
    package_sha = state.package_semantic_sha256
    if target == RuntimeState.RUNNING:
        if package_semantic_sha256 is None or SHA256_HEX.fullmatch(package_semantic_sha256) is None:
            raise CoverageV2StateError("runtime start must bind a package semantic SHA")
        package_binding = next(
            binding for binding in checked if binding.kind == "package-manifest"
        )
        if package_binding.semantic_sha256 != package_semantic_sha256:
            raise CoverageV2StateError("runtime package SHA differs from package evidence")
        package_sha = package_semantic_sha256
    elif package_semantic_sha256 is not None and package_semantic_sha256 != package_sha:
        raise CoverageV2StateError("runtime evidence refers to another package")
    return replace(state, runtime_state=target, package_semantic_sha256=package_sha)


def reset_runtime_for_package_drift(
    state: CoverageState,
    new_package_semantic_sha256: str,
) -> CoverageState:
    if SHA256_HEX.fullmatch(new_package_semantic_sha256) is None:
        raise CoverageV2StateError("new package semantic SHA is invalid")
    return replace(
        state,
        runtime_state=RuntimeState.NOT_RUN,
        package_semantic_sha256=new_package_semantic_sha256,
    )


class GenerationGuard:
    def __init__(self, state: CoverageState) -> None:
        self.state = state

    def assert_can_write(self, relative_path: str) -> None:
        pure = PurePosixPath(relative_path)
        is_generated_program = (
            pure.suffix in (".sql", ".spec", ".session") or "sessions" in pure.parts
        )
        if not is_generated_program:
            return
        allowed_index = PLANNING_SEQUENCE.index(PlanningState.GENERATION_ALLOWED)
        current_index = PLANNING_SEQUENCE.index(self.state.planning_state)
        if self.state.failure_state is not None or current_index < allowed_index:
            raise CoverageV2StateError("generation output is forbidden before generation_allowed")


def build_foundation_readiness(
    *,
    statement_key: str,
    registry: ArtifactSchemaRegistry,
    input_locks: Sequence[ArtifactBinding],
) -> dict[str, Any]:
    checked_locks = _validate_evidence(input_locks, Counter({"input-lock": 2}))
    implemented = registry.implemented_kinds
    missing_schema = {
        f"schema:{kind}" for kind in REQUIRED_SCHEMA_KINDS - implemented
    }
    missing = sorted(
        missing_schema | set(REQUIRED_NON_SCHEMA_COMPONENTS),
        key=lambda value: value.encode("utf-8"),
    )
    checks: list[dict[str, Any]] = []
    for kind in sorted(REQUIRED_SCHEMA_KINDS, key=lambda value: value.encode("utf-8")):
        binding = registry.bindings.get(kind)
        checks.append(
            {
                "component_id": f"schema:{kind}",
                "passed": binding is not None,
                "evidence_semantic_sha256": (
                    binding.semantic_sha256 if binding is not None else "0" * 64
                ),
            }
        )
    for component in sorted(
        REQUIRED_NON_SCHEMA_COMPONENTS, key=lambda value: value.encode("utf-8")
    ):
        checks.append(
            {
                "component_id": component,
                "passed": False,
                "evidence_semantic_sha256": "0" * 64,
            }
        )
    checks.sort(key=lambda row: row["component_id"].encode("utf-8"))
    document = build_artifact(
        artifact_id=f"READINESS-{statement_key}",
        kind="readiness",
        semantic_payload={
            "statement_key": statement_key,
            "passed": not missing,
            "checks": checks,
            "missing_components": missing,
            "implemented_schema_kinds": sorted(
                implemented, key=lambda value: value.encode("utf-8")
            ),
            "required_schema_kinds": sorted(
                REQUIRED_SCHEMA_KINDS, key=lambda value: value.encode("utf-8")
            ),
            "schema_registry_semantic_sha256": registry.semantic_sha256,
        },
        predecessors=checked_locks,
    )
    registry.validate(document)
    return document
