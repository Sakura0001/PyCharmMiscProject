from __future__ import annotations

import json
import hashlib
import tempfile
import unittest
from pathlib import Path

from pg_case_factory.artifact_store import prepare_run
from pg_case_factory.contracts import (
    CaseManifest,
    CoveragePlan,
    ExecutionProfile,
    REQUIRED_RISK_DECISIONS,
    execution_profile_sha256,
    inventory_values_sha256,
)
from pg_case_factory.differential import ExecutionRecord
from pg_case_factory.jobs import (
    DependencyNotReadyError,
    InvalidJobTransition,
    JobStore,
    _RunCoverageContext,
    _execution_record,
    _reference_oracle,
    select_dispatchable_jobs,
)


class JobStoreTest(unittest.TestCase):
    def transition(self, store: JobStore, job_id: str, state: str):
        evidence_path = f"evidence/{job_id}/{state}.json"
        return store.transition(
            job_id,
            state,
            evidence_paths=[evidence_path],
            evidence_sha256={evidence_path: "0" * 64},
        )

    def plan(self) -> CoveragePlan:
        return CoveragePlan.from_dict(
            {
                "schema_version": 1,
                "kind": "coverage_plan",
                "plan_id": "PLAN-JOBS",
                "feature_id": "feature-jobs",
                "axes": {
                    "operation": {
                        "values": ["read"],
                        "inventory_source": "inline:job-operation",
                        "coverage_mode": "complete",
                        "inventory_count": 1,
                        "inventory_sha256": inventory_values_sha256(["read"]),
                        "description": "Complete job-operation fixture axis.",
                        "derivation": "One operation is sufficient for state-machine tests.",
                        "source_locators": ["feature:REQ-001", "pg18:fixture"],
                        "exclusion_policy": "SQL semantics are outside this fixture.",
                        "review_status": "semantic_reviewed",
                    }
                },
                "scope_decisions": {
                    "object": {
                        "status": "not_applicable",
                        "reason": "Job persistence is independent of SQL object coverage.",
                    },
                    "relation": {
                        "status": "not_applicable",
                        "reason": "Job persistence is independent of relation coverage.",
                    },
                    "table": {
                        "status": "not_applicable",
                        "reason": "Job persistence is independent of table coverage.",
                    },
                    "column_type": {
                        "status": "not_applicable",
                        "reason": "Job persistence is independent of type coverage.",
                    },
                },
                "risk_decisions": {
                    risk: {
                        "status": "not_applicable",
                        "reason": f"Job persistence does not exercise {risk} semantics.",
                    }
                    for risk in REQUIRED_RISK_DECISIONS
                },
                "test_points": [
                    {
                        "id": "TP-001",
                        "title": "Prepare data",
                        "requirement_ids": ["REQ-001"],
                        "core_axes": ["operation"],
                        "dependencies": [],
                        "default_outcome": "success",
                    },
                    {
                        "id": "TP-002",
                        "title": "Read data",
                        "requirement_ids": ["REQ-001"],
                        "core_axes": ["operation"],
                        "dependencies": ["TP-001"],
                        "default_outcome": "success",
                    },
                ],
            }
        )

    def test_job_evidence_oracle_binds_the_terminating_error_sqlstate(self):
        case = CaseManifest.from_dict(
            {
                "schema_version": 1,
                "kind": "case_manifest",
                "case_id": "CASE-EXPECTED-FAILURE",
                "test_point_id": "TP-001",
                "obligation_id": "obl-expected-failure",
                "outcome": "expected_failure",
                "sql_files": ["cases/sql/case.sql"],
                "sql_sha256": "0" * 64,
                "execution_profile": "basic_psql",
                "comparison": {
                    "mode": "exact_text",
                    "oracle": "upstream-postgresql-18.4",
                    "require_identical": True,
                    "expected_sqlstate": "23505",
                },
                "cleanup": {"required": True, "idempotent": True},
            }
        )
        injected = ExecutionRecord(
            "reference",
            "/case.sql",
            3,
            "",
            (
                "psql:<stdin>:1: WARNING:  23505: injected expected code\n"
                "psql:<stdin>:2: ERROR:  22012: division by zero\n"
            ),
            0.1,
        )
        correct = ExecutionRecord(
            "reference",
            "/case.sql",
            3,
            "",
            "psql:<stdin>:1: ERROR:  23505: duplicate key\n",
            0.1,
        )

        invalid, error = _reference_oracle(case, injected)
        self.assertFalse(invalid)
        self.assertIn("22012, expected 23505", error)
        self.assertEqual((True, None), _reference_oracle(case, correct))

    def test_execution_gate_applies_route_privileges_and_run_profile_binding(self):
        profile = ExecutionProfile.from_dict(
            {
                "schema_version": 1,
                "kind": "execution_profile",
                "compatibility_target": "postgresql-18.4",
                "reference": {
                    "service": "pg18_reference",
                    "database": "regression",
                    "expected_system_identifier": "111111",
                    "expected_current_user": "regression_user",
                },
                "dut": {
                    "service": "storage_engine_dut",
                    "database": "regression",
                    "expected_system_identifier": "222222",
                    "expected_current_user": "regression_user",
                },
                "runner": {
                    "executable": "psql",
                    "timeout_seconds": 30,
                    "stop_on_error": True,
                },
                "comparison": {
                    "mode": "exact_text",
                    "normalization": {
                        "drop_line_patterns": [],
                        "replacements": [],
                        "strip_trailing_whitespace": False,
                    },
                },
                "security": {
                    "credential_source": "external-libpq-service",
                    "persist_credentials": False,
                },
            }
        )
        profile_digest = execution_profile_sha256(profile)

        with tempfile.TemporaryDirectory() as tmp:
            run_root = prepare_run(Path(tmp), "job-profile-binding")[
                "run_root"
            ].resolve(strict=True)
            sql_relative = "cases/sql/CASE-EXTERNAL.sql"
            sql_content = "SELECT 1;\n"
            sql_sha256 = hashlib.sha256(sql_content.encode("utf-8")).hexdigest()
            (run_root / sql_relative).write_text(sql_content, encoding="utf-8")
            external_case = CaseManifest.from_dict(
                {
                    "schema_version": 1,
                    "kind": "case_manifest",
                    "case_id": "CASE-EXTERNAL",
                    "test_point_id": "TP-001",
                    "obligation_id": "obl-external",
                    "outcome": "success",
                    "sql_files": [sql_relative],
                    "sql_sha256": sql_sha256,
                    "execution_profile": "external_isolated",
                    "execution_harness": "external-superuser",
                    "comparison": {
                        "mode": "exact_text",
                        "oracle": "upstream-postgresql-18.4",
                        "require_identical": True,
                    },
                    "cleanup": {"required": True, "idempotent": True},
                }
            )
            context = _RunCoverageContext(
                run_root=run_root,
                plan=self.plan(),
                obligations=(),
                cases=(external_case,),
                manifest_path_by_case_id={},
                execution_profile=profile,
                execution_profile_sha256=profile_digest,
            )
            record_relative = "executions/reference/CASE-EXTERNAL.json"
            stdout_relative = "executions/reference/CASE-EXTERNAL.stdout"
            stderr_relative = "executions/reference/CASE-EXTERNAL.stderr"
            (run_root / stdout_relative).write_text("1\n", encoding="utf-8")
            (run_root / stderr_relative).write_text("", encoding="utf-8")
            record = {
                "target_name": "reference",
                "sql_file": str((run_root / sql_relative).resolve()),
                "returncode": 0,
                "stdout": "1\n",
                "stderr": "",
                "duration_seconds": 0.1,
                "endpoint_identity": {
                    "target_name": "reference",
                    "service": "pg18_reference",
                    "database": "regression",
                    "server_version_num": 180004,
                    "system_identifier": "111111",
                    "server_address": "127.0.0.1",
                    "server_port": "5432",
                    "current_user": "regression_user",
                    "is_superuser": True,
                    "can_createdb": True,
                    "can_createrole": False,
                    "can_replication": False,
                    "can_bypassrls": False,
                    "dangerous_role_memberships": ["pg_execute_server_program"],
                    "privileged_role_memberships": ["privileged_parent"],
                },
                "sql_sha256": sql_sha256,
                "execution_profile_sha256": profile_digest,
            }
            record_path = run_root / record_relative
            record_path.write_text(json.dumps(record) + "\n", encoding="utf-8")
            (run_root / "executions/reference/CASE-EXTERNAL.replay.json").write_text(
                json.dumps(record) + "\n", encoding="utf-8"
            )
            (run_root / "executions/reference/CASE-EXTERNAL.replay.stdout").write_text(
                "1\n", encoding="utf-8"
            )
            (run_root / "executions/reference/CASE-EXTERNAL.replay.stderr").write_text(
                "", encoding="utf-8"
            )

            _, parsed = _execution_record(context, external_case, "reference")
            self.assertTrue(parsed.endpoint_identity["is_superuser"])
            self.assertEqual(profile_digest, parsed.execution_profile_sha256)

            basic_document = external_case.to_dict()
            basic_document["execution_profile"] = "basic_psql"
            basic_document.pop("execution_harness")
            basic_case = CaseManifest.from_dict(basic_document)
            with self.assertRaisesRegex(ValueError, "over-privileged"):
                _execution_record(context, basic_case, "reference")

            record["endpoint_identity"]["service"] = "wrong_service"
            record_path.write_text(json.dumps(record) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "immutable run execution profile"):
                _execution_record(context, external_case, "reference")

            record["endpoint_identity"]["service"] = "pg18_reference"
            record["endpoint_identity"]["system_identifier"] = "999999"
            record_path.write_text(json.dumps(record) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "immutable run execution profile"):
                _execution_record(context, external_case, "reference")

            record["endpoint_identity"]["system_identifier"] = "111111"
            record["execution_profile_sha256"] = "0" * 64
            record_path.write_text(json.dumps(record) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "immutable run profile"):
                _execution_record(context, external_case, "reference")

    def test_initialization_is_persistent_and_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "jobs.json"
            store = JobStore.initialize(path, self.plan())
            self.transition(store, "TP-001", "audited")

            resumed = JobStore.open(path)
            self.assertEqual(resumed.get("TP-001").state, "audited")
            self.assertEqual(resumed.get("TP-002").state, "planned")

            again = JobStore.initialize(path, self.plan())
            self.assertEqual(again.get("TP-001").state, "audited")

            raw = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(raw["plan_id"], "PLAN-JOBS")
            self.assertEqual(len(raw["jobs"]), 2)

    def test_stale_store_instances_do_not_overwrite_other_agent_updates(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "jobs.json"
            worker_a = JobStore.initialize(path, self.plan())
            worker_b = JobStore.open(path)

            self.transition(worker_a, "TP-001", "audited")
            self.transition(worker_b, "TP-002", "audited")

            persisted = JobStore.open(path)
            self.assertEqual("audited", persisted.get("TP-001").state)
            self.assertEqual("audited", persisted.get("TP-002").state)

    def test_only_declared_forward_transitions_are_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = JobStore.initialize(Path(tmp) / "jobs.json", self.plan())
            with self.assertRaisesRegex(ValueError, "requires non-empty evidence"):
                store.transition(
                    "TP-001",
                    "audited",
                    evidence_paths=[],
                    evidence_sha256={},
                )
            with self.assertRaisesRegex(InvalidJobTransition, "planned -> generated"):
                self.transition(store, "TP-001", "generated")

            expected_states = [
                "audited",
                "ready",
                "generated",
                "linted",
                "executed_reference",
                "executed_dut",
                "compared",
                "triaged",
                "packaged",
            ]
            for state in expected_states:
                self.transition(store, "TP-001", state)
            self.assertEqual(store.get("TP-001").state, "packaged")

            with self.assertRaisesRegex(InvalidJobTransition, "packaged -> triaged"):
                self.transition(store, "TP-001", "triaged")

    def test_dependency_must_be_packaged_before_dependent_job_becomes_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = JobStore.initialize(Path(tmp) / "jobs.json", self.plan())
            self.transition(store, "TP-002", "audited")
            with self.assertRaisesRegex(DependencyNotReadyError, "TP-001 is planned"):
                self.transition(store, "TP-002", "ready")

            for state in (
                "audited",
                "ready",
                "generated",
                "linted",
                "executed_reference",
                "executed_dut",
                "compared",
                "triaged",
                "packaged",
            ):
                self.transition(store, "TP-001", state)
            self.transition(store, "TP-002", "ready")
            self.assertEqual(store.get("TP-002").state, "ready")

    def test_dispatch_selection_is_plan_ordered_dependency_aware_and_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = JobStore.initialize(Path(tmp) / "jobs.json", self.plan())
            self.assertEqual(
                ["TP-001"],
                [record.job_id for record in select_dispatchable_jobs(store)],
            )
            self.transition(store, "TP-002", "audited")
            self.assertEqual(
                ["TP-001"],
                [record.job_id for record in select_dispatchable_jobs(store, limit=2)],
            )
            for state in (
                "audited",
                "ready",
                "generated",
                "linted",
                "executed_reference",
                "executed_dut",
                "compared",
                "triaged",
                "packaged",
            ):
                self.transition(store, "TP-001", state)
            self.assertEqual(
                ["TP-002"],
                [record.job_id for record in select_dispatchable_jobs(store)],
            )
            store.fail("TP-002", "child agent failed")
            self.assertEqual((), select_dispatchable_jobs(store))
            with self.assertRaisesRegex(ValueError, "positive integer"):
                select_dispatchable_jobs(store, limit=0)

    def test_failed_job_can_retry_from_its_last_successful_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "jobs.json"
            store = JobStore.initialize(path, self.plan())
            self.transition(store, "TP-001", "audited")
            store.fail("TP-001", "temporary model failure")

            failed = store.get("TP-001")
            self.assertEqual(failed.state, "failed")
            self.assertEqual(failed.resume_state, "audited")
            self.assertEqual(failed.last_error, "temporary model failure")

            JobStore.open(path).retry("TP-001")
            resumed = JobStore.open(path).get("TP-001")
            self.assertEqual(resumed.state, "audited")
            self.assertEqual(resumed.attempts, 2)
            self.assertIsNone(resumed.last_error)

    def test_corrupt_or_mismatched_store_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "jobs.json"
            path.write_text("{broken", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid job store JSON"):
                JobStore.open(path)

            path.unlink()
            JobStore.initialize(path, self.plan())
            other = self.plan().to_dict()
            other["plan_id"] = "PLAN-OTHER"
            with self.assertRaisesRegex(ValueError, "belongs to plan PLAN-JOBS"):
                JobStore.initialize(path, CoveragePlan.from_dict(other))

    def test_tampered_evidence_history_and_duplicate_json_keys_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "jobs.json"
            JobStore.initialize(path, self.plan())
            document = json.loads(path.read_text(encoding="utf-8"))
            document["jobs"][0]["state"] = "generated"
            document["jobs"][0]["evidence"] = {
                "generated": ["cases/case.sql"],
            }
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "evidence does not match progress state"):
                JobStore.open(path)

            path.write_text(
                '{"schema_version": 2, "schema_version": 2}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "duplicate JSON key schema_version"):
                JobStore.open(path)

    def test_resume_rejects_a_changed_plan_with_the_same_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "jobs.json"
            JobStore.initialize(path, self.plan())
            changed = self.plan().to_dict()
            changed["axes"]["operation"]["values"].append("write")
            changed["axes"]["operation"]["inventory_count"] = 2
            changed["axes"]["operation"]["inventory_sha256"] = inventory_values_sha256(
                ["read", "write"]
            )

            with self.assertRaisesRegex(ValueError, "coverage plan content changed"):
                JobStore.initialize(path, CoveragePlan.from_dict(changed))


if __name__ == "__main__":
    unittest.main()
