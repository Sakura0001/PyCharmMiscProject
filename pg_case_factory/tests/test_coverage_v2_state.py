from __future__ import annotations

import unittest

from pg_case_factory.coverage_v2.artifacts import ArtifactBinding
from pg_case_factory.coverage_v2.errors import CoverageV2StateError
from pg_case_factory.coverage_v2.schema_registry import ArtifactSchemaRegistry
from pg_case_factory.coverage_v2.state import (
    CoverageState,
    GenerationGuard,
    Origin,
    PLANNING_EVIDENCE,
    PLANNING_SEQUENCE,
    PlanningState,
    RUNTIME_EVIDENCE,
    RuntimeState,
    advance_planning_state,
    advance_runtime_state,
    build_foundation_readiness,
    record_failure,
    reset_runtime_for_package_drift,
    retry_failure,
)


def _binding(artifact_id: str, kind: str, digit: str = "1") -> ArtifactBinding:
    return ArtifactBinding(
        artifact_id=artifact_id,
        relative_path=f"evidence/{artifact_id}.json",
        byte_sha256=digit * 64,
        semantic_sha256=digit * 64,
        kind=kind,
        schema_version=2,
    )


class PlanningStateMachineTest(unittest.TestCase):
    def test_every_planning_edge_and_every_skip_are_locked(self) -> None:
        state = CoverageState.discovered(origin=Origin.NATIVE_V2)
        for target in PLANNING_SEQUENCE[1:]:
            required = PLANNING_EVIDENCE[target]
            evidence = tuple(
                _binding(
                    f"{target.value}-{kind}-{ordinal}",
                    kind,
                    f"{(ordinal % 15) + 1:x}",
                )
                for ordinal, kind in enumerate(required.elements(), start=1)
            )
            state = advance_planning_state(state, target, evidence=evidence)
            self.assertEqual(target, state.planning_state)

        for current_index, current in enumerate(PLANNING_SEQUENCE):
            state = CoverageState(
                planning_state=current,
                runtime_state=RuntimeState.NOT_RUN,
                origin=Origin.NATIVE_V2,
                failure_state=None,
                package_semantic_sha256=None,
            )
            for target_index, target in enumerate(PLANNING_SEQUENCE):
                if target_index == current_index + 1:
                    continue
                with self.subTest(current=current, rejected_target=target):
                    with self.assertRaises(CoverageV2StateError):
                        advance_planning_state(state, target, evidence=())

    def test_forward_edge_requires_exact_verified_evidence(self) -> None:
        discovered = CoverageState.discovered(origin=Origin.NATIVE_V2)
        global_lock = _binding("GLOBAL-LOCK", "input-lock", "1")
        local_lock = _binding("LOCAL-LOCK", "input-lock", "2")
        with self.assertRaises(CoverageV2StateError):
            advance_planning_state(
                discovered,
                PlanningState.INPUTS_LOCKED,
                evidence=(global_lock,),
            )
        with self.assertRaises(CoverageV2StateError):
            advance_planning_state(
                discovered,
                PlanningState.READINESS_PASSED,
                evidence=(global_lock, local_lock),
            )
        with self.assertRaises(CoverageV2StateError):
            advance_planning_state(
                discovered,
                PlanningState.INPUTS_LOCKED,
                evidence=(global_lock, local_lock, _binding("READY", "readiness")),
            )
        locked = advance_planning_state(
            discovered,
            PlanningState.INPUTS_LOCKED,
            evidence=(local_lock, global_lock),
        )
        self.assertEqual(PlanningState.INPUTS_LOCKED, locked.planning_state)

        with self.assertRaises(CoverageV2StateError):
            advance_planning_state(
                locked,
                PlanningState.READINESS_PASSED,
                evidence=(ArtifactBinding("R", "r", "x" * 64, "y" * 64, "readiness", 1),),
            )

    def test_failure_retry_and_generation_guard_are_fail_closed(self) -> None:
        discovered = CoverageState.discovered(origin=Origin.LEGACY_IMPORT)
        failed = record_failure(
            discovered,
            failed_stage=PlanningState.INPUTS_LOCKED,
            reason="local input drift",
            retryable=True,
        )
        self.assertEqual(PlanningState.DISCOVERED, failed.planning_state)
        self.assertIsNotNone(failed.failure_state)
        with self.assertRaises(CoverageV2StateError):
            retry_failure(failed, evidence=())
        retried = retry_failure(
            failed,
            evidence=(
                _binding("GLOBAL", "input-lock", "3"),
                _binding("LOCAL", "input-lock", "4"),
            ),
        )
        self.assertIsNone(retried.failure_state)
        self.assertEqual(PlanningState.INPUTS_LOCKED, retried.planning_state)

        for state in (discovered, retried):
            with self.subTest(state=state.planning_state):
                with self.assertRaises(CoverageV2StateError):
                    GenerationGuard(state).assert_can_write("abort_00001.sql")
                with self.assertRaises(CoverageV2StateError):
                    GenerationGuard(state).assert_can_write("abort.spec")
                with self.assertRaises(CoverageV2StateError):
                    GenerationGuard(state).assert_can_write("sessions/a.session")

        allowed = CoverageState(
            planning_state=PlanningState.GENERATION_ALLOWED,
            runtime_state=RuntimeState.NOT_RUN,
            origin=Origin.NATIVE_V2,
            failure_state=None,
            package_semantic_sha256=None,
        )
        GenerationGuard(allowed).assert_can_write("abort_00001.sql")

    def test_runtime_edges_bind_package_and_package_drift_resets_attempt(self) -> None:
        packaged = CoverageState(
            planning_state=PlanningState.PACKAGED,
            runtime_state=RuntimeState.NOT_RUN,
            origin=Origin.NATIVE_V2,
            failure_state=None,
            package_semantic_sha256=None,
        )
        package = _binding("PACKAGE", "package-manifest", "5")
        run_contract = _binding("RUN", "run-contract", "6")
        running = advance_runtime_state(
            packaged,
            RuntimeState.RUNNING,
            evidence=(package, run_contract),
            package_semantic_sha256=package.semantic_sha256,
        )
        self.assertEqual(RuntimeState.RUNNING, running.runtime_state)
        with self.assertRaises(CoverageV2StateError):
            advance_runtime_state(
                running,
                RuntimeState.RUNTIME_VERIFIED,
                evidence=(_binding("VALID", "runtime-validation", "7"),),
            )
        reset = reset_runtime_for_package_drift(running, "8" * 64)
        self.assertEqual(RuntimeState.NOT_RUN, reset.runtime_state)
        self.assertEqual("8" * 64, reset.package_semantic_sha256)

    def test_every_runtime_edge_and_every_unlisted_edge_are_locked(self) -> None:
        for edge, required in RUNTIME_EVIDENCE.items():
            source, target = edge
            evidence = tuple(
                _binding(
                    f"{source.value}-{target.value}-{kind}-{ordinal}",
                    kind,
                    f"{(ordinal % 15) + 1:x}",
                )
                for ordinal, kind in enumerate(required.elements(), start=1)
            )
            package = next(
                (item for item in evidence if item.kind == "package-manifest"),
                None,
            )
            state = CoverageState(
                planning_state=PlanningState.PACKAGED,
                runtime_state=source,
                origin=Origin.NATIVE_V2,
                failure_state=None,
                package_semantic_sha256=(
                    package.semantic_sha256 if package is not None else "f" * 64
                ),
            )
            advanced = advance_runtime_state(
                state,
                target,
                evidence=evidence,
                package_semantic_sha256=(
                    package.semantic_sha256 if target == RuntimeState.RUNNING else None
                ),
            )
            self.assertEqual(target, advanced.runtime_state)

        for source in RuntimeState:
            for target in RuntimeState:
                if (source, target) in RUNTIME_EVIDENCE:
                    continue
                state = CoverageState(
                    planning_state=PlanningState.PACKAGED,
                    runtime_state=source,
                    origin=Origin.NATIVE_V2,
                    failure_state=None,
                    package_semantic_sha256="f" * 64,
                )
                with self.subTest(source=source, rejected_target=target):
                    with self.assertRaises(CoverageV2StateError):
                        advance_runtime_state(state, target, evidence=())


class FoundationReadinessTest(unittest.TestCase):
    def test_partial_control_plane_never_claims_full_v2_readiness(self) -> None:
        registry = ArtifactSchemaRegistry.load_packaged()
        global_lock = _binding("GLOBAL-LOCK", "input-lock", "1")
        local_lock = _binding("LOCAL-LOCK", "input-lock", "2")
        document = build_foundation_readiness(
            statement_key="abort",
            registry=registry,
            input_locks=(global_lock, local_lock),
        )
        registry.validate(document)
        payload = document["semantic_payload"]
        self.assertFalse(payload["passed"])
        self.assertEqual(
            ["current-pointer", "input-lock", "readiness", "statement-order"],
            payload["implemented_schema_kinds"],
        )
        self.assertIn("schema:source-universe", payload["missing_components"])
        self.assertIn("semantic-extractor-registry", payload["missing_components"])


if __name__ == "__main__":
    unittest.main()
