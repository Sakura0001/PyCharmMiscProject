from __future__ import annotations

import hashlib
import tempfile
import unittest
from collections import Counter
from dataclasses import replace
from pathlib import Path

from mysql_case_factory.contracts import (
    ContractValidationError,
    CaseManifest,
    CoveragePlan,
    REQUIRED_RISK_DECISIONS,
    inventory_values_sha256,
    load_coverage_plan,
)
from mysql_case_factory.coverage import (
    CoverageCompilation,
    CoverageConditionProof,
    CoverageContractProof,
    CoverageError,
    CoverageInteractionRequirement,
    assignment_set_sha256,
    compile_coverage_plan,
    expand_coverage_plan,
    prove_coverage_contract,
    reconcile_case_manifests,
    reconcile_obligations,
    stable_obligation_id,
)
from mysql_case_factory.feature_plan import validate_coverage_plan
from mysql_case_factory.planning_contracts import FactorDecision


class CoverageExpansionTest(unittest.TestCase):
    def plan_document(self) -> dict:
        table_values = ["heap", "foreign", "external"]
        column_values = ["integer", "text"]
        return {
            "schema_version": 1,
            "kind": "coverage_plan",
            "plan_id": "PLAN-1",
            "feature_id": "feature-1",
            "axes": {
                "table_kind": {
                    "values": table_values,
                    "inventory_source": "skills/mysql-8-0-22-sql-generation/references/combinations/_shared/coverage_inventory.yaml#table_kinds.all_table_kinds",
                    "coverage_mode": "complete",
                    "inventory_count": len(table_values),
                    "inventory_sha256": inventory_values_sha256(table_values),
                },
                "column_type": {
                    "values": column_values,
                    "inventory_source": "skills/mysql-8-0-22-sql-generation/references/common/mysql8022_type_catalog.md#structured_config.types",
                    "coverage_mode": "complete",
                    "inventory_count": len(column_values),
                    "inventory_sha256": inventory_values_sha256(column_values),
                },
            },
            "scope_decisions": {
                "object": {
                    "status": "not_applicable",
                    "reason": "The unit test models table storage only.",
                },
                "relation": {
                    "status": "not_applicable",
                    "reason": "Non-table relation kinds are outside this unit fixture.",
                },
                "table": {
                    "status": "not_applicable",
                    "reason": "The compact expansion fixture does not claim canonical table dimensions.",
                },
                "column_type": {
                    "status": "not_applicable",
                    "reason": "The compact expansion fixture does not claim the complete type universe.",
                },
            },
            "risk_decisions": {
                risk: (
                    {
                        "status": "covered",
                        "axes": ["table_kind", "column_type"],
                        "test_points": ["TP-READ"],
                    }
                    if risk in {"operation", "data_profile"}
                    else {
                        "status": "not_applicable",
                        "reason": f"The expansion fixture does not exercise {risk} semantics.",
                    }
                )
                for risk in REQUIRED_RISK_DECISIONS
            },
            "test_points": [
                {
                    "id": "TP-READ",
                    "title": "Read every relevant storage shape",
                    "requirement_ids": ["REQ-1"],
                    "core_axes": ["table_kind", "column_type"],
                    "dependencies": [],
                    "classification_rules": [
                        {
                            "when": {"table_kind": "foreign"},
                            "outcome": "expected_failure",
                            "reason": "The operation is unsupported for foreign tables.",
                        },
                        {
                            "when": {"table_kind": "external"},
                            "outcome": "justified_na",
                            "reason": "External storage bypasses the changed storage layer.",
                        },
                    ],
                    "default_outcome": "success",
                }
            ],
        }

    def test_core_axes_expand_to_the_complete_cartesian_product(self):
        plan = CoveragePlan.from_dict(self.plan_document())
        obligations = expand_coverage_plan(plan)

        self.assertEqual(len(obligations), 6)
        assignments = {tuple(sorted(item.assignments.items())) for item in obligations}
        self.assertEqual(
            assignments,
            {
                (("column_type", "integer"), ("table_kind", "heap")),
                (("column_type", "text"), ("table_kind", "heap")),
                (("column_type", "integer"), ("table_kind", "foreign")),
                (("column_type", "text"), ("table_kind", "foreign")),
                (("column_type", "integer"), ("table_kind", "external")),
                (("column_type", "text"), ("table_kind", "external")),
            },
        )

        report = reconcile_obligations(obligations)
        self.assertEqual(report.total, 6)
        self.assertEqual(report.success, 2)
        self.assertEqual(report.expected_failure, 2)
        self.assertEqual(report.justified_na, 2)
        self.assertEqual(report.missing, 0)
        self.assertTrue(report.complete)

    def test_execution_routing_is_part_of_each_obligation_and_case_binding(self):
        document = self.plan_document()
        document["risk_decisions"]["external_copy"] = {
            "status": "covered",
            "axes": ["table_kind"],
            "test_points": ["TP-READ"],
            "execution_harness": "external-load-data-ingest",
        }
        document["test_points"][0]["execution_rules"] = [
            {
                "when": {"table_kind": "heap"},
                "execution_profile": "external_isolated",
                "execution_harness": "external-load-data-ingest",
            }
        ]
        plan = CoveragePlan.from_dict(document)
        obligation = next(
            item
            for item in expand_coverage_plan(plan)
            if item.assignments == {"table_kind": "heap", "column_type": "integer"}
        )
        self.assertEqual("external_isolated", obligation.execution_profile)
        self.assertEqual("external-load-data-ingest", obligation.execution_harness)

        sql_content = "COPY routed_case FROM STDIN;\n1\n\\.\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sql_path = root / "cases" / "sql" / "routed.sql"
            sql_path.parent.mkdir(parents=True)
            sql_path.write_text(sql_content, encoding="utf-8")
            case_document = {
                "schema_version": 1,
                "kind": "case_manifest",
                "case_id": "CASE-EXTERNAL",
                "test_point_id": obligation.test_point_id,
                "obligation_id": obligation.obligation_id,
                "outcome": obligation.outcome,
                "sql_files": ["cases/sql/routed.sql"],
                "sql_sha256": hashlib.sha256(sql_content.encode("utf-8")).hexdigest(),
                "execution_profile": "external_isolated",
                "execution_harness": "external-load-data-ingest",
                "comparison": {
                    "mode": "exact_text",
                    "oracle": "upstream-mysql-community-8.0.22",
                    "require_identical": True,
                },
                "cleanup": {"required": True, "idempotent": True},
                "metadata": {"assignments": dict(obligation.assignments)},
            }
            external = reconcile_case_manifests(
                [obligation],
                [CaseManifest.from_dict(case_document)],
                artifact_root=root,
            )
            self.assertTrue(external.complete, external)

            case_document["execution_profile"] = "basic_mysql"
            case_document.pop("execution_harness")
            basic = reconcile_case_manifests(
                [obligation],
                [CaseManifest.from_dict(case_document)],
                artifact_root=root,
            )
            self.assertFalse(basic.complete)
            self.assertIn("CASE-EXTERNAL", basic.mismatched_case_ids)

    def test_external_load_data_case_is_delegated_to_the_named_harness(self):
        document = self.plan_document()
        document["risk_decisions"]["load_data_ingest"] = {
            "status": "covered",
            "axes": ["table_kind"],
            "test_points": ["TP-READ"],
            "execution_harness": "external-load-data-ingest",
        }
        document["test_points"][0]["execution_rules"] = [
            {
                "when": {"table_kind": "heap"},
                "execution_profile": "external_isolated",
                "execution_harness": "external-load-data-ingest",
            }
        ]
        obligation = next(
            item
            for item in expand_coverage_plan(CoveragePlan.from_dict(document))
            if item.assignments == {"table_kind": "heap", "column_type": "integer"}
        )

        valid_sql = (
            "CREATE TEMPORARY TABLE load_bound(value integer);\n"
            "LOAD DATA LOCAL INFILE 'payload.csv' INTO TABLE load_bound;\n"
            "SELECT value FROM load_bound ORDER BY value;\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sql_path = root / "cases" / "sql" / "load_bound.sql"
            sql_path.parent.mkdir(parents=True)
            sql_path.write_text(valid_sql, encoding="utf-8")
            case_document = {
                "schema_version": 1,
                "kind": "case_manifest",
                "case_id": "CASE-LOAD-BOUND",
                "test_point_id": obligation.test_point_id,
                "obligation_id": obligation.obligation_id,
                "outcome": obligation.outcome,
                "sql_files": ["cases/sql/load_bound.sql"],
                "sql_sha256": hashlib.sha256(valid_sql.encode("utf-8")).hexdigest(),
                "execution_profile": "external_isolated",
                "execution_harness": "external-load-data-ingest",
                "comparison": {
                    "mode": "exact_text",
                    "oracle": "upstream-mysql-community-8.0.22",
                    "require_identical": True,
                },
                "cleanup": {"required": True, "idempotent": True},
                "metadata": {"assignments": dict(obligation.assignments)},
            }
            complete = reconcile_case_manifests(
                [obligation],
                [CaseManifest.from_dict(case_document)],
                artifact_root=root,
            )
            self.assertTrue(complete.complete, complete)

            tampered_payload_sql = valid_sql.replace("payload.csv", "other.csv")
            sql_path.write_text(tampered_payload_sql, encoding="utf-8")
            tampered = reconcile_case_manifests(
                [obligation],
                [CaseManifest.from_dict(case_document)],
                artifact_root=root,
            )
            self.assertFalse(tampered.complete)
            self.assertTrue(
                any("SQL SHA256 does not match" in item for item in tampered.unsafe_sql_files)
            )

            case_document["sql_sha256"] = hashlib.sha256(
                tampered_payload_sql.encode("utf-8")
            ).hexdigest()
            delegated = reconcile_case_manifests(
                [obligation],
                [CaseManifest.from_dict(case_document)],
                artifact_root=root,
            )
            self.assertTrue(delegated.complete, delegated)


    def test_obligation_ids_are_stable_and_unique(self):
        plan = CoveragePlan.from_dict(self.plan_document())
        first = expand_coverage_plan(plan)
        second = expand_coverage_plan(plan)

        self.assertEqual([item.obligation_id for item in first], [item.obligation_id for item in second])
        self.assertEqual(len({item.obligation_id for item in first}), len(first))

        other_document = self.plan_document()
        other_document["plan_id"] = "PLAN-2"
        other = expand_coverage_plan(CoveragePlan.from_dict(other_document))
        self.assertNotEqual(first[0].obligation_id, other[0].obligation_id)

    def test_unclassified_combinations_are_reported_as_missing(self):
        document = self.plan_document()
        point = document["test_points"][0]
        point.pop("default_outcome")
        obligations = expand_coverage_plan(CoveragePlan.from_dict(document))
        report = reconcile_obligations(obligations)

        self.assertEqual(report.expected_failure, 2)
        self.assertEqual(report.justified_na, 2)
        self.assertEqual(report.missing, 2)
        self.assertFalse(report.complete)

        with self.assertRaisesRegex(CoverageError, "2 coverage obligations are unclassified"):
            expand_coverage_plan(CoveragePlan.from_dict(document), require_complete=True)

    def test_non_success_classification_requires_a_reason(self):
        document = self.plan_document()
        del document["test_points"][0]["classification_rules"][0]["reason"]
        with self.assertRaisesRegex(CoverageError, "expected_failure classification requires a reason"):
            expand_coverage_plan(CoveragePlan.from_dict(document))

    def test_conflicting_rules_are_rejected_instead_of_using_rule_order(self):
        document = self.plan_document()
        document["test_points"][0]["classification_rules"].append(
            {
                "when": {"column_type": "integer"},
                "outcome": "success",
            }
        )
        with self.assertRaisesRegex(CoverageError, "matches conflicting classification rules"):
            expand_coverage_plan(CoveragePlan.from_dict(document))

    def test_classification_values_use_yaml_type_identity(self):
        document = self.plan_document()
        document["axes"]["table_kind"]["values"] = [1]
        document["axes"]["table_kind"]["inventory_count"] = 1
        document["axes"]["table_kind"]["inventory_sha256"] = inventory_values_sha256([1])
        document["test_points"][0]["classification_rules"] = [
            {
                "when": {"table_kind": True},
                "outcome": "expected_failure",
                "reason": "A boolean must not match an integer inventory value.",
            }
        ]
        with self.assertRaisesRegex(ContractValidationError, "unknown value True"):
            expand_coverage_plan(CoveragePlan.from_dict(document))

    def test_generated_cases_reconcile_against_non_na_obligations(self):
        import hashlib
        import tempfile

        plan = CoveragePlan.from_dict(self.plan_document())
        obligations = expand_coverage_plan(plan)
        executable = [item for item in obligations if item.outcome != "justified_na"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sql").mkdir()
            case_documents = []
            for index, obligation in enumerate(executable, 1):
                sql_content = f"SELECT {index};\n"
                (root / "sql" / f"case_{index:03d}.sql").write_text(
                    sql_content,
                    encoding="utf-8",
                )
                document = {
                    "schema_version": 1,
                    "kind": "case_manifest",
                    "case_id": f"CASE-{index:03d}",
                    "test_point_id": obligation.test_point_id,
                    "obligation_id": obligation.obligation_id,
                    "outcome": obligation.outcome,
                    "sql_files": [f"sql/case_{index:03d}.sql"],
                    "sql_sha256": hashlib.sha256(sql_content.encode("utf-8")).hexdigest(),
                    "execution_profile": "basic_mysql",
                    "comparison": {
                        "mode": "exact_text",
                        "oracle": "upstream-mysql-community-8.0.22",
                        "require_identical": True,
                    },
                    "cleanup": {"required": True, "idempotent": True},
                    "metadata": {"assignments": dict(obligation.assignments)},
                }
                if document["outcome"] == "expected_failure":
                    document["comparison"]["expected_sqlstate"] = "0A000"
                case_documents.append(document)

            from mysql_case_factory.contracts import CaseManifest

            cases = [CaseManifest.from_dict(document) for document in case_documents]
            complete = reconcile_case_manifests(
                obligations,
                cases,
                artifact_root=root,
            )
            self.assertTrue(complete.complete)
            self.assertEqual(complete.missing_case_ids, ())

            unverified = reconcile_case_manifests(obligations, cases)
            self.assertFalse(unverified.complete)
            self.assertIn("artifact_root is required", unverified.unsafe_sql_files[0])

            incomplete = reconcile_case_manifests(
                obligations,
                cases[:-1],
                artifact_root=root,
            )
            self.assertFalse(incomplete.complete)
            self.assertEqual(len(incomplete.missing_case_ids), 1)

    def test_case_reconciliation_checks_assignment_and_materialized_safe_sql(self):
        import hashlib
        import tempfile
        from pathlib import Path

        from mysql_case_factory.contracts import CaseManifest

        plan = CoveragePlan.from_dict(self.plan_document())
        obligation = next(
            item
            for item in expand_coverage_plan(plan)
            if item.outcome == "success"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sql_path = root / "cases" / "sql" / "case.sql"
            sql_path.parent.mkdir(parents=True)
            sql_content = "SELECT 1;\n"
            document = {
                "schema_version": 1,
                "kind": "case_manifest",
                "case_id": "CASE-SAFE",
                "test_point_id": obligation.test_point_id,
                "obligation_id": obligation.obligation_id,
                "outcome": obligation.outcome,
                "sql_files": ["cases/sql/case.sql"],
                "sql_sha256": hashlib.sha256(sql_content.encode("utf-8")).hexdigest(),
                "execution_profile": "basic_mysql",
                "comparison": {
                    "mode": "exact_text",
                    "oracle": "upstream-mysql-community-8.0.22",
                    "require_identical": True,
                },
                "cleanup": {"required": True, "idempotent": True},
                "metadata": {"assignments": dict(obligation.assignments)},
            }
            case = CaseManifest.from_dict(document)

            missing = reconcile_case_manifests([obligation], [case], artifact_root=root)
            self.assertFalse(missing.complete)
            self.assertEqual(1, len(missing.missing_sql_files))

            sql_path.write_text(sql_content, encoding="utf-8")
            complete = reconcile_case_manifests([obligation], [case], artifact_root=root)
            self.assertTrue(complete.complete, complete)

            document["metadata"]["assignments"] = {"table_kind": "wrong"}
            wrong = reconcile_case_manifests(
                [obligation],
                [CaseManifest.from_dict(document)],
                artifact_root=root,
            )
            self.assertFalse(wrong.complete)
            self.assertEqual(("CASE-SAFE",), wrong.mismatched_case_ids)

            document["metadata"]["assignments"] = dict(obligation.assignments)
            sql_path.write_text("\\! env\n", encoding="utf-8")
            unsafe = reconcile_case_manifests(
                [obligation],
                [CaseManifest.from_dict(document)],
                artifact_root=root,
            )
            self.assertFalse(unsafe.complete)
            self.assertEqual(1, len(unsafe.unsafe_sql_files))

    def test_unclassified_obligation_prevents_case_reconciliation_from_claiming_complete(self):
        document = self.plan_document()
        document["test_points"][0].pop("default_outcome")
        obligations = expand_coverage_plan(CoveragePlan.from_dict(document))

        report = reconcile_case_manifests(obligations, [])
        self.assertFalse(report.complete)
        self.assertGreater(len(report.missing_case_ids), 0)

    def test_all_na_plan_cannot_self_certify_without_an_executable_oracle(self):
        document = self.plan_document()
        point = document["test_points"][0]
        point["classification_rules"] = []
        point["default_outcome"] = "justified_na"
        point["default_reason"] = "A reason alone cannot replace every executable oracle."
        plan = CoveragePlan.from_dict(document)
        obligations = expand_coverage_plan(plan)

        self.assertFalse(reconcile_obligations(obligations).complete)
        self.assertFalse(reconcile_case_manifests(obligations, []).complete)
        with self.assertRaisesRegex(CoverageError, "no executable obligations"):
            expand_coverage_plan(plan, require_complete=True)


class ExactCoverageContractProofTest(unittest.TestCase):
    SHA = "a" * 64

    def plan_document(
        self,
        *,
        policy: str = "full_cross",
        expected_counts: dict | None = None,
    ) -> dict:
        document = CoverageExpansionTest().plan_document()
        document["test_points"][0]["classification_rules"][0]["source"] = (
            "knowledge/mysql/error/unsupported-foreign"
        )
        document["test_points"][0]["classification_rules"][1]["source"] = (
            "knowledge/mysql/scope/external-storage"
        )
        document["test_points"][0]["coverage_contract"] = {
            "combination_policy": policy,
            "primary_axes": (
                ["table_kind", "column_type"]
                if policy != "conditional_cross"
                else ["table_kind"]
            ),
            "condition_axes": [] if policy != "conditional_cross" else ["column_type"],
            "expected_counts": expected_counts
            or {
                "total": 6,
                "success": 2,
                "expected_failure": 2,
                "justified_na": 2,
            },
        }
        return document

    def interaction(
        self,
        *,
        interaction_id: str = "interaction.table-type",
        target_suite_id: str = "TP-READ",
        required_factor_ids: tuple[str, ...] = ("table_kind", "column_type"),
        selector_factor_ids: tuple[str, ...] = (),
        reference_factor_ids: tuple[str, ...] = (),
        policy: str = "full_cross",
    ) -> CoverageInteractionRequirement:
        return CoverageInteractionRequirement(
            interaction_id=interaction_id,
            target_suite_id=target_suite_id,
            required_factor_ids=required_factor_ids,
            selector_factor_ids=selector_factor_ids,
            reference_factor_ids=reference_factor_ids,
            combination_policy=policy,
            source="knowledge/feature-impact.yaml#interactions",
            source_sha256="d" * 64,
        )

    def factor_decision(
        self,
        plan: CoveragePlan,
        factor_id: str,
        *,
        owner: str = "TP-READ",
        strategy: str = "full_cross",
        dependencies: list[str] | None = None,
    ) -> FactorDecision:
        axis = plan.axes[factor_id]
        return FactorDecision.from_dict(
            {
                "schema_version": 1,
                "kind": "factor_decision",
                "factor_id": factor_id,
                "domain": "data_and_type",
                "status": "covered",
                "trigger_path": ["requirement.REQ-1", f"factor.{factor_id}"],
                "edition_applicability": {
                    "mysql_8_0_22": "applicable",
                    "mysql_8_0_41": "applicable",
                },
                "combination_strategy": strategy,
                "dependencies": dependencies or [],
                "exclusions": [],
                "owning_suite_id": owner,
                "review_state": "reviewed",
                "inventory_source": axis.inventory_source,
                "inventory_sha256": axis.inventory_sha256,
                "provenance": {
                    "producer_role": "factor_association",
                    "input_artifacts": [
                        {"path": "feature.md", "sha256": self.SHA}
                    ],
                    "output_sha256": "b" * 64,
                    "policy_sha256": "c" * 64,
                    "created_at": "2026-07-15T00:00:00Z",
                },
            }
        )

    def decisions(
        self,
        plan: CoveragePlan,
        *,
        owner: str = "TP-READ",
        strategy: str = "full_cross",
    ) -> tuple[FactorDecision, FactorDecision]:
        return (
            self.factor_decision(
                plan,
                "table_kind",
                owner=owner,
                strategy=strategy,
            ),
            self.factor_decision(
                plan,
                "column_type",
                owner=owner,
                strategy=strategy,
                dependencies=["table_kind"],
            ),
        )

    def test_full_cross_compilation_proves_exact_sets_digests_counts_and_ownership(self):
        plan = CoveragePlan.from_dict(self.plan_document())
        obligations = expand_coverage_plan(plan)

        compilation = compile_coverage_plan(
            plan,
            self.decisions(plan),
            obligations,
            (self.interaction(),),
        )

        self.assertIsInstance(compilation, CoverageCompilation)
        self.assertTrue(compilation.complete)
        self.assertEqual(compilation.obligations, obligations)
        self.assertEqual(len(compilation.contract_proofs), 1)
        proof = compilation.contract_proofs[0]
        self.assertIsInstance(proof, CoverageContractProof)
        self.assertTrue(proof.complete)
        self.assertEqual(proof.theoretical_count, 6)
        self.assertEqual(proof.actual_count, 6)
        self.assertEqual(proof.theoretical_sha256, proof.actual_sha256)
        self.assertEqual(proof.outcome_counts["success"], 2)
        self.assertEqual(len(proof.condition_proofs), 1)
        self.assertIsInstance(proof.condition_proofs[0], CoverageConditionProof)
        self.assertEqual(proof.condition_proofs[0].condition_assignment, {})
        self.assertEqual(
            compilation.interaction_source_sha256_by_id,
            {"interaction.table-type": "d" * 64},
        )
        backward_compatible = compile_coverage_plan(
            plan,
            self.decisions(plan),
            obligations,
        )
        self.assertTrue(backward_compatible.complete)
        self.assertEqual(backward_compatible.interaction_source_sha256_by_id, {})

    def test_missing_assignment_plus_duplicate_is_rejected_even_when_count_is_unchanged(self):
        plan = CoveragePlan.from_dict(self.plan_document())
        obligations = list(expand_coverage_plan(plan))
        obligations[0] = obligations[1]

        with self.assertRaisesRegex(CoverageError, "duplicate semantic assignment"):
            prove_coverage_contract(plan, plan.test_points[0], obligations)

    def test_same_count_axis_replacement_is_not_accepted(self):
        plan = CoveragePlan.from_dict(self.plan_document())
        obligations = list(expand_coverage_plan(plan))
        replacement = {**obligations[0].assignments, "table_kind": "replacement"}
        obligations[0] = replace(
            obligations[0],
            assignments=replacement,
            obligation_id=stable_obligation_id(
                "TP-READ", replacement, plan_id=plan.plan_id
            ),
        )

        with self.assertRaisesRegex(CoverageError, "unknown value.*replacement"):
            prove_coverage_contract(plan, plan.test_points[0], obligations)

    def test_external_interaction_rejects_coordinated_axis_split_without_dependencies(self):
        document = self.plan_document()
        original = document["test_points"][0]
        document["test_points"] = [
            {
                **original,
                "title": "Table shapes",
                "core_axes": ["table_kind"],
                "classification_rules": original["classification_rules"],
                "coverage_contract": {
                    "combination_policy": "full_cross",
                    "primary_axes": ["table_kind"],
                    "condition_axes": [],
                    "expected_counts": {
                        "total": 3,
                        "success": 1,
                        "expected_failure": 1,
                        "justified_na": 1,
                    },
                },
            },
            {
                "id": "TP-TYPE",
                "title": "Column types",
                "requirement_ids": ["REQ-1"],
                "core_axes": ["column_type"],
                "dependencies": [],
                "default_outcome": "success",
                "coverage_contract": {
                    "combination_policy": "full_cross",
                    "primary_axes": ["column_type"],
                    "condition_axes": [],
                    "expected_counts": {
                        "total": 2,
                        "success": 2,
                        "expected_failure": 0,
                        "justified_na": 0,
                    },
                },
            },
        ]
        for risk in document["risk_decisions"].values():
            if risk["status"] == "covered":
                risk["test_points"] = ["TP-READ", "TP-TYPE"]
        plan = CoveragePlan.from_dict(document)
        decisions = (
            self.factor_decision(plan, "table_kind", owner="TP-READ"),
            self.factor_decision(
                plan,
                "column_type",
                owner="TP-TYPE",
                dependencies=[],
            ),
        )

        with self.assertRaisesRegex(
            CoverageError,
            "interaction interaction.table-type.*required factors.*one target suite",
        ):
            compile_coverage_plan(
                plan,
                decisions,
                expand_coverage_plan(plan),
                (self.interaction(),),
            )

    def test_pairwise_policy_cannot_be_upgraded_to_a_completeness_proof(self):
        plan = CoveragePlan.from_dict(self.plan_document(policy="pairwise"))

        with self.assertRaisesRegex(CoverageError, "pairwise.*cannot prove exact completeness"):
            compile_coverage_plan(
                plan,
                self.decisions(plan, strategy="pairwise"),
                expand_coverage_plan(plan),
                (self.interaction(policy="pairwise"),),
            )

    def test_forged_expected_counts_and_outcomes_are_rejected(self):
        forged = CoveragePlan.from_dict(
            self.plan_document(
                expected_counts={
                    "total": 6,
                    "success": 3,
                    "expected_failure": 1,
                    "justified_na": 2,
                }
            )
        )
        with self.assertRaisesRegex(CoverageError, "expected outcome counts"):
            compile_coverage_plan(
                forged,
                self.decisions(forged),
                expand_coverage_plan(forged),
                (self.interaction(),),
            )

        document = self.plan_document()
        document["test_points"][0]["coverage_contract"]["expected_counts"] = {
            "total": 5,
            "success": 1,
            "expected_failure": 2,
            "justified_na": 2,
        }
        wrong_total = CoveragePlan.from_dict(document)
        with self.assertRaisesRegex(ContractValidationError, "expected total 5.*Cartesian size 6"):
            validate_coverage_plan(wrong_total)

        plan = CoveragePlan.from_dict(self.plan_document())
        obligations = list(expand_coverage_plan(plan))
        obligations[0] = replace(
            obligations[0],
            outcome="expected_failure",
            reason="Forged outcome.",
        )
        with self.assertRaisesRegex(CoverageError, "outcome/reason/source does not match"):
            prove_coverage_contract(plan, plan.test_points[0], obligations)

    def test_conditional_cross_proves_each_condition_tuple_without_offsets(self):
        plan = CoveragePlan.from_dict(self.plan_document(policy="conditional_cross"))
        proof = prove_coverage_contract(
            plan,
            plan.test_points[0],
            expand_coverage_plan(plan),
        )
        self.assertEqual(len(proof.condition_proofs), 2)
        self.assertEqual(
            {item.condition_assignment["column_type"] for item in proof.condition_proofs},
            {"integer", "text"},
        )
        self.assertTrue(all(item.theoretical_count == 3 for item in proof.condition_proofs))

        obligations = list(expand_coverage_plan(plan))
        obligations.pop(0)
        with self.assertRaisesRegex(CoverageError, "condition.*integer.*missing 1"):
            prove_coverage_contract(plan, plan.test_points[0], obligations)

    def test_contracted_non_success_classifications_require_and_propagate_sources(self):
        document = self.plan_document()
        del document["test_points"][0]["classification_rules"][0]["source"]
        missing_rule_source = CoveragePlan.from_dict(document)
        with self.assertRaisesRegex(
            ContractValidationError,
            "contracted.*expected_failure.*source",
        ):
            validate_coverage_plan(missing_rule_source)

        plan = CoveragePlan.from_dict(self.plan_document())
        foreign = next(
            item
            for item in expand_coverage_plan(plan)
            if item.assignments["table_kind"] == "foreign"
        )
        self.assertEqual(
            foreign.source,
            "knowledge/mysql/error/unsupported-foreign",
        )
        self.assertEqual(
            foreign.to_dict()["source"],
            "knowledge/mysql/error/unsupported-foreign",
        )
        forged = [
            replace(item, source="knowledge/forged") if item == foreign else item
            for item in expand_coverage_plan(plan)
        ]
        with self.assertRaisesRegex(
            CoverageError,
            "outcome/reason/source does not match",
        ):
            prove_coverage_contract(plan, plan.test_points[0], forged)

        default_document = self.plan_document()
        point = default_document["test_points"][0]
        point["classification_rules"] = []
        point["default_outcome"] = "justified_na"
        point["default_reason"] = "The contracted fixture is intentionally excluded."
        point["coverage_contract"]["expected_counts"] = {
            "total": 6,
            "success": 0,
            "expected_failure": 0,
            "justified_na": 6,
        }
        missing_default_source = CoveragePlan.from_dict(default_document)
        with self.assertRaisesRegex(
            ContractValidationError,
            "default justified_na.*default_source",
        ):
            validate_coverage_plan(missing_default_source)
        default_document["test_points"][0]["default_source"] = (
            "knowledge/mysql/scope/default-exclusion"
        )
        sourced_default = CoveragePlan.from_dict(default_document)
        self.assertTrue(
            all(
                item.source == "knowledge/mysql/scope/default-exclusion"
                for item in expand_coverage_plan(sourced_default)
            )
        )

    def test_legacy_non_success_without_source_keeps_v1_shape_and_ids(self):
        legacy = CoveragePlan.from_dict(CoverageExpansionTest().plan_document())
        obligations = expand_coverage_plan(legacy)
        non_success = next(item for item in obligations if item.outcome == "expected_failure")
        self.assertIsNone(non_success.source)
        self.assertNotIn("source", non_success.to_dict())
        self.assertNotIn(
            "source",
            legacy.to_dict()["test_points"][0]["classification_rules"][0],
        )
        self.assertEqual(
            non_success.obligation_id,
            stable_obligation_id(
                non_success.test_point_id,
                non_success.assignments,
                plan_id=legacy.plan_id,
            ),
        )

    def conditional_plan_document(self) -> dict:
        document = self.plan_document()
        algorithm_values = ["instant", "inplace"]
        document["axes"]["algorithm"] = {
            "values": algorithm_values,
            "inventory_source": (
                "skills/mysql-8-0-22-sql-generation/references/combinations/"
                "_shared/coverage_inventory.yaml#algorithms"
            ),
            "coverage_mode": "complete",
            "inventory_count": len(algorithm_values),
            "inventory_sha256": inventory_values_sha256(algorithm_values),
        }
        document["test_points"].append(
            {
                "id": "TP-COND",
                "title": "Algorithm by selected table shape",
                "requirement_ids": ["REQ-1"],
                "core_axes": ["algorithm", "table_kind"],
                "dependencies": ["TP-READ"],
                "default_outcome": "success",
                "coverage_contract": {
                    "combination_policy": "conditional_cross",
                    "primary_axes": ["algorithm"],
                    "condition_axes": ["table_kind"],
                    "expected_counts": {
                        "total": 6,
                        "success": 6,
                        "expected_failure": 0,
                        "justified_na": 0,
                    },
                },
            }
        )
        return document

    def conditional_interaction(self) -> CoverageInteractionRequirement:
        return self.interaction(
            interaction_id="interaction.algorithm-by-table",
            target_suite_id="TP-COND",
            required_factor_ids=("algorithm",),
            selector_factor_ids=("table_kind",),
            policy="conditional_cross",
        )

    def test_conditional_suite_reuses_owned_factor_only_as_bound_selector(self):
        plan = CoveragePlan.from_dict(self.conditional_plan_document())
        table, column = self.decisions(plan)
        algorithm = self.factor_decision(
            plan,
            "algorithm",
            owner="TP-COND",
            strategy="conditional_cross",
        )
        interactions = (self.interaction(), self.conditional_interaction())

        compilation = compile_coverage_plan(
            plan,
            (table, column, algorithm),
            expand_coverage_plan(plan),
            interactions,
        )
        self.assertTrue(compilation.complete)
        self.assertEqual(compilation.factor_owner_by_id["table_kind"], "TP-READ")
        self.assertEqual(compilation.factor_owner_by_id["algorithm"], "TP-COND")

        with self.assertRaisesRegex(CoverageError, "unapproved factor reuse.*table_kind"):
            compile_coverage_plan(
                plan,
                (table, column, algorithm),
                expand_coverage_plan(plan),
                (self.interaction(),),
            )

        duplicate_owner = self.factor_decision(
            plan,
            "table_kind",
            owner="TP-COND",
            strategy="conditional_cross",
        )
        with self.assertRaisesRegex(CoverageError, "duplicate factor decision table_kind"):
            compile_coverage_plan(
                plan,
                (table, duplicate_owner, column, algorithm),
                expand_coverage_plan(plan),
                interactions,
            )

        pretending_owner = self.factor_decision(
            plan,
            "table_kind",
            owner="TP-COND",
            strategy="conditional_cross",
        )
        with self.assertRaisesRegex(
            CoverageError,
            "selector/reference factor table_kind cannot be owned by target suite TP-COND",
        ):
            compile_coverage_plan(
                plan,
                (pretending_owner, column, algorithm),
                expand_coverage_plan(plan),
                (self.conditional_interaction(), self.interaction()),
            )

    def test_interaction_contract_is_strict_and_digest_bound(self):
        interaction = self.interaction()
        self.assertEqual(
            CoverageInteractionRequirement.from_dict(interaction.to_dict()),
            interaction,
        )
        for changes, message in (
            ({"interaction_id": "bad id"}, "stable"),
            ({"source": ""}, "source"),
            ({"source_sha256": "a" * 63}, "source_sha256"),
            ({"selector_factor_ids": ("table_kind",)}, "overlap"),
        ):
            values = {
                "interaction_id": interaction.interaction_id,
                "target_suite_id": interaction.target_suite_id,
                "required_factor_ids": interaction.required_factor_ids,
                "selector_factor_ids": interaction.selector_factor_ids,
                "reference_factor_ids": interaction.reference_factor_ids,
                "combination_policy": interaction.combination_policy,
                "source": interaction.source,
                "source_sha256": interaction.source_sha256,
                **changes,
            }
            with self.assertRaisesRegex(CoverageError, message):
                CoverageInteractionRequirement(**values)

    def test_duplicate_factor_decisions_wrong_ids_and_bindings_fail_closed(self):
        plan = CoveragePlan.from_dict(self.plan_document())
        table, column = self.decisions(plan)
        with self.assertRaisesRegex(CoverageError, "duplicate factor decision table_kind"):
            compile_coverage_plan(
                plan,
                (table, table, column),
                expand_coverage_plan(plan),
                (self.interaction(),),
            )

        obligations = list(expand_coverage_plan(plan))
        obligations[0] = replace(obligations[0], obligation_id="obl-wrong-id")
        with self.assertRaisesRegex(CoverageError, "obligation id.*does not match"):
            prove_coverage_contract(plan, plan.test_points[0], obligations)

        wrong_owner = self.factor_decision(plan, "table_kind", owner="TP-OTHER")
        with self.assertRaisesRegex(CoverageError, "owning suite TP-OTHER.*TP-READ"):
            compile_coverage_plan(
                plan,
                (wrong_owner, column),
                expand_coverage_plan(plan),
                (self.interaction(),),
            )

        wrong_inventory_document = table.to_dict()
        wrong_inventory_document["inventory_sha256"] = "d" * 64
        wrong_inventory = FactorDecision.from_dict(wrong_inventory_document)
        with self.assertRaisesRegex(CoverageError, "inventory binding"):
            compile_coverage_plan(
                plan,
                (wrong_inventory, column),
                expand_coverage_plan(plan),
                (self.interaction(),),
            )

    def test_contract_axes_must_exactly_match_core_axes(self):
        document = self.plan_document()
        document["test_points"][0]["coverage_contract"]["primary_axes"] = [
            "table_kind"
        ]
        plan = CoveragePlan.from_dict(document)
        with self.assertRaisesRegex(ContractValidationError, "contract axes.*core_axes"):
            validate_coverage_plan(plan)

    def test_assignment_digest_is_order_independent_and_type_safe(self):
        bool_digest = assignment_set_sha256([{"value": True}])
        int_digest = assignment_set_sha256([{"value": 1}])
        self.assertNotEqual(bool_digest, int_digest)
        self.assertEqual(
            assignment_set_sha256([{"a": 1}, {"a": 2}]),
            assignment_set_sha256([{"a": 2}, {"a": 1}]),
        )
        with self.assertRaisesRegex(CoverageError, "duplicate semantic assignment"):
            assignment_set_sha256([{"a": 1}, {"a": 1}])

    def test_contracted_points_require_decisions_and_legacy_never_self_certifies(self):
        plan = CoveragePlan.from_dict(self.plan_document())
        with self.assertRaisesRegex(CoverageError, "requires factor decisions"):
            compile_coverage_plan(
                plan,
                (),
                expand_coverage_plan(plan),
                (self.interaction(),),
            )

        legacy = CoveragePlan.from_dict(CoverageExpansionTest().plan_document())
        compilation = compile_coverage_plan(legacy, (), expand_coverage_plan(legacy))
        self.assertFalse(compilation.complete)
        self.assertEqual(compilation.contract_proofs, ())


if __name__ == "__main__":
    unittest.main()
