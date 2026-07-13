from __future__ import annotations

import hashlib
import tempfile
import unittest
from collections import Counter
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
    CoverageError,
    expand_coverage_plan,
    reconcile_case_manifests,
    reconcile_obligations,
)


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


if __name__ == "__main__":
    unittest.main()
