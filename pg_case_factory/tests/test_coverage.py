from __future__ import annotations

import hashlib
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from pg_case_factory.contracts import (
    ContractValidationError,
    CaseManifest,
    CoveragePlan,
    REQUIRED_RISK_DECISIONS,
    inventory_values_sha256,
    load_coverage_plan,
)
from pg_case_factory.coverage import (
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
                    "inventory_source": "skills/pg-sql-generation/references/combinations/_shared/coverage_inventory.yaml#table_kinds.all_table_kinds",
                    "coverage_mode": "complete",
                    "inventory_count": len(table_values),
                    "inventory_sha256": inventory_values_sha256(table_values),
                },
                "column_type": {
                    "values": column_values,
                    "inventory_source": "skills/pg-sql-generation/references/common/pg18_type_catalog.md#structured_config.types",
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
            "execution_harness": "external-copy-stdin",
        }
        document["test_points"][0]["execution_rules"] = [
            {
                "when": {"table_kind": "heap"},
                "execution_profile": "external_isolated",
                "execution_harness": "external-copy-stdin",
            }
        ]
        plan = CoveragePlan.from_dict(document)
        obligation = next(
            item
            for item in expand_coverage_plan(plan)
            if item.assignments == {"table_kind": "heap", "column_type": "integer"}
        )
        self.assertEqual("external_isolated", obligation.execution_profile)
        self.assertEqual("external-copy-stdin", obligation.execution_harness)

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
                "execution_harness": "external-copy-stdin",
                "comparison": {
                    "mode": "exact_text",
                    "oracle": "upstream-postgresql-18.4",
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

            case_document["execution_profile"] = "basic_psql"
            case_document.pop("execution_harness")
            basic = reconcile_case_manifests(
                [obligation],
                [CaseManifest.from_dict(case_document)],
                artifact_root=root,
            )
            self.assertFalse(basic.complete)
            self.assertIn("CASE-EXTERNAL", basic.mismatched_case_ids)

    def test_external_copy_ingest_case_binds_payload_inside_its_only_sql_file(self):
        document = self.plan_document()
        document["risk_decisions"]["copy_protocol_ingest"] = {
            "status": "covered",
            "axes": ["table_kind"],
            "test_points": ["TP-READ"],
            "execution_harness": "external-copy-ingest",
        }
        document["test_points"][0]["execution_rules"] = [
            {
                "when": {"table_kind": "heap"},
                "execution_profile": "external_isolated",
                "execution_harness": "external-copy-ingest",
            }
        ]
        obligation = next(
            item
            for item in expand_coverage_plan(CoveragePlan.from_dict(document))
            if item.assignments == {"table_kind": "heap", "column_type": "integer"}
        )

        valid_sql = (
            "CREATE TEMP TABLE copy_bound(value integer);\n"
            "COPY copy_bound FROM STDIN;\n"
            "1\n"
            "\\.\n"
            "TABLE copy_bound;\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sql_path = root / "cases" / "sql" / "copy_bound.sql"
            sql_path.parent.mkdir(parents=True)
            sql_path.write_text(valid_sql, encoding="utf-8")
            case_document = {
                "schema_version": 1,
                "kind": "case_manifest",
                "case_id": "CASE-COPY-BOUND",
                "test_point_id": obligation.test_point_id,
                "obligation_id": obligation.obligation_id,
                "outcome": obligation.outcome,
                "sql_files": ["cases/sql/copy_bound.sql"],
                "sql_sha256": hashlib.sha256(valid_sql.encode("utf-8")).hexdigest(),
                "execution_profile": "external_isolated",
                "execution_harness": "external-copy-ingest",
                "comparison": {
                    "mode": "exact_text",
                    "oracle": "upstream-postgresql-18.4",
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

            tampered_payload_sql = valid_sql.replace("1\n\\.\n", "2\n\\.\n")
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

            external_file_sql = "COPY copy_bound FROM '/tmp/payload.csv';\n"
            sql_path.write_text(external_file_sql, encoding="utf-8")
            case_document["sql_sha256"] = hashlib.sha256(
                external_file_sql.encode("utf-8")
            ).hexdigest()
            rejected = reconcile_case_manifests(
                [obligation],
                [CaseManifest.from_dict(case_document)],
                artifact_root=root,
            )
            self.assertFalse(rejected.complete)
            self.assertEqual(1, len(rejected.unsafe_sql_files))
            self.assertIn("external payload files", rejected.unsafe_sql_files[0])

    def test_shipped_pg18_template_has_a_complete_truthful_ledger(self):
        root = Path(__file__).resolve().parents[1]
        template = (
            root
            / "skills"
            / "pg-sql-generation"
            / "assets"
            / "templates"
            / "coverage_plan_template.yaml"
        )
        plan = load_coverage_plan(template, inventory_root=root)
        obligations = expand_coverage_plan(plan, require_complete=True)
        report = reconcile_obligations(obligations)

        self.assertEqual(37, len(plan.axes))
        self.assertEqual(25, len(plan.test_points))
        self.assertEqual(3175, report.total)
        self.assertEqual(2787, report.success)
        self.assertEqual(153, report.expected_failure)
        self.assertEqual(235, report.justified_na)
        self.assertTrue(report.complete)
        self.assertEqual(
            Counter({"basic_psql": 2717, "external_isolated": 458}),
            Counter(item.execution_profile for item in obligations),
        )
        self.assertEqual(
            40,
            sum(
                item.execution_harness == "external-copy-ingest"
                for item in obligations
            ),
        )
        self.assertEqual(
            29,
            sum(
                item.execution_harness == "external-postgres-fdw"
                for item in obligations
            ),
        )
        self.assertEqual(
            "external-postgres-fdw",
            plan.risk_decisions["foreign_storage_integration"].execution_harness,
        )
        for axis in plan.axes.values():
            if axis.inventory_source.startswith("inline:"):
                self.assertIsNotNone(axis.derivation)
                self.assertTrue(axis.source_locators)
                self.assertIsNotNone(axis.exclusion_policy)
                self.assertIn(axis.review_status, {"source_derived", "semantic_reviewed"})

    def test_shipped_pg18_template_classifies_storage_sensitive_edges_truthfully(self):
        root = Path(__file__).resolve().parents[1]
        plan = load_coverage_plan(
            root
            / "skills"
            / "pg-sql-generation"
            / "assets"
            / "templates"
            / "coverage_plan_template.yaml",
            inventory_root=root,
        )
        obligations = expand_coverage_plan(plan, require_complete=True)

        def outcome(point_id: str, **assignments: str) -> str:
            matches = [
                item
                for item in obligations
                if item.test_point_id == point_id
                and dict(item.assignments) == assignments
            ]
            self.assertEqual(1, len(matches), (point_id, assignments))
            return matches[0].outcome

        self.assertEqual(
            "expected_failure",
            outcome(
                "TP-TABLE-SHAPES",
                relpersistence="unlogged",
                partition_role="partitioned_parent",
                partition_strategy="range",
                inheritance_role="none",
                table_access_method_selection="default",
            ),
        )
        self.assertEqual(
            "success",
            outcome(
                "TP-TABLE-SHAPES",
                relpersistence="unlogged",
                partition_role="partition_leaf",
                partition_strategy="range",
                inheritance_role="none",
                table_access_method_selection="default",
            ),
        )
        self.assertEqual(
            "success",
            outcome(
                "TP-TABLE-SHAPES",
                relpersistence="permanent",
                partition_role="non_partitioned",
                partition_strategy="none",
                inheritance_role="none",
                table_access_method_selection="extension_provided",
            ),
        )
        self.assertEqual(
            "success",
            outcome(
                "TP-USER-DEFINED-ARCHETYPE",
                user_defined_archetype="base_type",
            ),
        )
        self.assertEqual(
            "expected_failure",
            outcome(
                "TP-OPERATION-LIFECYCLE",
                operation="vacuum",
                transaction_context="explicit_commit",
            ),
        )
        self.assertEqual(
            "success",
            outcome(
                "TP-OPERATION-LIFECYCLE",
                operation="vacuum",
                transaction_context="autocommit",
            ),
        )
        self.assertEqual(
            "success",
            outcome(
                "TP-PRIVILEGE",
                privilege_context="insufficient_privilege",
                operation="vacuum",
            ),
        )
        self.assertEqual(
            "success",
            outcome(
                "TP-PRIVILEGE",
                privilege_context="insufficient_privilege",
                operation="analyze",
            ),
        )
        self.assertEqual(
            "expected_failure",
            outcome(
                "TP-PRIVILEGE",
                privilege_context="insufficient_privilege",
                operation="insert",
            ),
        )
        self.assertEqual(
            "justified_na",
            outcome(
                "TP-COLUMN-DATA-PROFILE",
                column_type="smallint",
                data_profile="wide_toast",
            ),
        )
        self.assertEqual(
            "success",
            outcome(
                "TP-COLUMN-DATA-PROFILE",
                column_type="text",
                data_profile="wide_toast",
            ),
        )
        self.assertEqual(
            "expected_failure",
            outcome(
                "TP-TOAST-STORAGE-SIZE",
                toastable_column_family="text_like",
                toast_storage_strategy="plain",
                toast_size_class="multi_chunk_value",
            ),
        )
        lz4 = next(
            item
            for item in obligations
            if item.test_point_id == "TP-TOAST-STORAGE-COMPRESSION"
            and item.assignments
            == {
                "toastable_column_family": "text_like",
                "toast_storage_strategy": "extended",
                "toast_compression": "lz4",
            }
        )
        self.assertEqual("external_isolated", lz4.execution_profile)
        self.assertEqual("external-toast-lz4", lz4.execution_harness)
        pglz = next(
            item
            for item in obligations
            if item.test_point_id == "TP-TOAST-STORAGE-COMPRESSION"
            and item.assignments
            == {
                "toastable_column_family": "text_like",
                "toast_storage_strategy": "extended",
                "toast_compression": "pglz",
            }
        )
        self.assertEqual("basic_psql", pglz.execution_profile)
        self.assertIsNone(pglz.execution_harness)

        def route(point_id: str, **assignments: str) -> tuple[str, str | None]:
            match = next(
                item
                for item in obligations
                if item.test_point_id == point_id
                and dict(item.assignments) == assignments
            )
            return match.execution_profile, match.execution_harness

        self.assertEqual(
            ("external_isolated", "external-superuser-object-lifecycle"),
            route("TP-OBJECT-LIFECYCLE", object_type="access_method"),
        )
        self.assertEqual(
            ("external_isolated", "external-cluster-role-db-admin"),
            route("TP-OBJECT-LIFECYCLE", object_type="database"),
        )
        self.assertEqual(
            ("external_isolated", "external-extension-object-lifecycle"),
            route("TP-OBJECT-LIFECYCLE", object_type="extension"),
        )
        self.assertEqual(
            ("external_isolated", "external-logical-replication"),
            route("TP-OBJECT-LIFECYCLE", object_type="subscription"),
        )
        self.assertEqual(
            ("external_isolated", "external-postgres-fdw"),
            route("TP-OBJECT-LIFECYCLE", object_type="foreign_table"),
        )
        self.assertEqual(
            ("basic_psql", None),
            route("TP-OBJECT-LIFECYCLE", object_type="table"),
        )
        self.assertEqual(
            ("external_isolated", "external-postgres-fdw"),
            route("TP-RELKIND-OBSERVABILITY", relkind="foreign_table"),
        )
        self.assertEqual(
            ("basic_psql", None),
            route("TP-RELKIND-OBSERVABILITY", relkind="partitioned_index"),
        )

    def test_shipped_pg18_template_routes_every_copy_protocol_case_fail_closed(self):
        root = Path(__file__).resolve().parents[1]
        plan = load_coverage_plan(
            root
            / "skills"
            / "pg-sql-generation"
            / "assets"
            / "templates"
            / "coverage_plan_template.yaml",
            inventory_root=root,
        )
        obligations = expand_coverage_plan(plan, require_complete=True)

        operation_copy_from = [
            item
            for item in obligations
            if item.assignments.get("operation") == "copy_from"
        ]
        operation_copy_to = [
            item
            for item in obligations
            if item.assignments.get("operation") == "copy_to"
        ]
        self.assertEqual(19, len(operation_copy_from))
        self.assertEqual(19, len(operation_copy_to))
        self.assertTrue(
            all(
                item.execution_profile == "external_isolated"
                and item.execution_harness == "external-copy-ingest"
                for item in operation_copy_from
            )
        )
        self.assertTrue(
            all(
                item.execution_profile == "basic_psql"
                and item.execution_harness is None
                for item in operation_copy_to
            )
        )

        option_obligations = [
            item
            for item in obligations
            if item.test_point_id == "TP-COPY-PG18-OPTIONS"
        ]
        self.assertEqual(28, len(option_obligations))
        self.assertEqual(
            {
                "to_force_quote_columns",
                "to_force_quote_all",
                "from_force_not_null_columns",
                "from_force_not_null_all",
                "from_force_null_columns",
                "from_force_null_all",
                "from_on_error_stop",
                "from_on_error_ignore_unlimited",
                "from_reject_limit_within",
                "from_reject_limit_max_bigint",
                "from_reject_limit_exceeded",
                "from_reject_limit_zero",
                "from_reject_limit_negative",
                "from_reject_limit_overflow",
                "from_reject_limit_without_ignore",
                "from_log_verbosity_default",
                "from_log_verbosity_verbose",
                "from_log_verbosity_silent",
                "from_log_verbosity_without_ignore",
                "from_on_error_ignore_binary",
                "from_force_quote_invalid_direction",
                "to_on_error_invalid_direction",
                "to_force_not_null_invalid_direction",
                "to_force_null_invalid_direction",
                "to_log_verbosity_verbose_noop",
                "from_force_not_null_text_invalid_format",
                "from_force_null_text_invalid_format",
                "to_force_quote_text_invalid_format",
            },
            {
                item.assignments["copy_pg18_option_case"]
                for item in option_obligations
            },
        )
        from_options = [
            item
            for item in option_obligations
            if str(item.assignments["copy_pg18_option_case"]).startswith("from_")
        ]
        to_options = [
            item
            for item in option_obligations
            if str(item.assignments["copy_pg18_option_case"]).startswith("to_")
        ]
        self.assertEqual(21, len(from_options))
        self.assertEqual(7, len(to_options))
        self.assertTrue(
            all(
                item.execution_profile == "external_isolated"
                and item.execution_harness == "external-copy-ingest"
                for item in from_options
            )
        )
        self.assertTrue(
            all(
                item.execution_profile == "basic_psql"
                and item.execution_harness is None
                for item in to_options
            )
        )
        self.assertEqual(
            Counter({"expected_failure": 14, "success": 14}),
            Counter(item.outcome for item in option_obligations),
        )
        self.assertEqual(
            {
                "from_on_error_stop",
                "from_reject_limit_exceeded",
                "from_reject_limit_zero",
                "from_reject_limit_negative",
                "from_reject_limit_overflow",
                "from_reject_limit_without_ignore",
                "from_on_error_ignore_binary",
                "from_force_quote_invalid_direction",
                "to_on_error_invalid_direction",
                "to_force_not_null_invalid_direction",
                "to_force_null_invalid_direction",
                "from_force_not_null_text_invalid_format",
                "from_force_null_text_invalid_format",
                "to_force_quote_text_invalid_format",
            },
            {
                item.assignments["copy_pg18_option_case"]
                for item in option_obligations
                if item.outcome == "expected_failure"
            },
        )
        self.assertEqual(
            "external-copy-ingest",
            plan.risk_decisions["copy_protocol_ingest"].execution_harness,
        )

    def test_shipped_pg18_template_targets_mvcc_crash_toast_and_schedule_intersections(self):
        root = Path(__file__).resolve().parents[1]
        plan = load_coverage_plan(
            root
            / "skills"
            / "pg-sql-generation"
            / "assets"
            / "templates"
            / "coverage_plan_template.yaml",
            inventory_root=root,
        )
        point_axes = {
            point.test_point_id: set(point.core_axes) for point in plan.test_points
        }
        point_requirements = {
            point.test_point_id: set(point.requirement_ids)
            for point in plan.test_points
        }
        self.assertEqual(
            {"read_path", "table_topology_class"},
            point_axes["TP-READ-PATH-TOPOLOGY"],
        )
        self.assertEqual(
            {"isolation_level", "snapshot_timing"},
            point_axes["TP-ISOLATION-SNAPSHOT"],
        )
        self.assertEqual(
            {"relpersistence", "wal_crash_phase"},
            point_axes["TP-WAL-CRASH-PERSISTENCE"],
        )
        self.assertEqual(
            {"partition_topology_class", "partition_dml_operation"},
            point_axes["TP-PARTITION-DML"],
        )
        self.assertEqual(
            {"table_topology_class", "operation"},
            point_axes["TP-TABLE-TOPOLOGY-OPERATION"],
        )
        self.assertEqual(
            {"copy_pg18_option_case"},
            point_axes["TP-COPY-PG18-OPTIONS"],
        )
        self.assertEqual(
            {"concurrency_schedule", "isolation_level", "concurrent_operation"},
            point_axes["TP-CONCURRENCY-SCHEDULE"],
        )
        self.assertEqual({"REQ-003"}, point_requirements["TP-PSEUDO-TYPE-REJECTION"])
        self.assertEqual({"REQ-003"}, point_requirements["TP-TYPMOD-BOUNDARY"])
        self.assertEqual({"REQ-001"}, point_requirements["TP-READ-PATH-TOPOLOGY"])
        self.assertEqual({"REQ-004"}, point_requirements["TP-WAL-CRASH-PERSISTENCE"])
        self.assertEqual({"REQ-005"}, point_requirements["TP-TOAST-STORAGE-SIZE"])
        self.assertEqual(
            {"REQ-003", "REQ-008"},
            point_requirements["TP-COPY-PG18-OPTIONS"],
        )
        self.assertEqual(
            {"REQ-002", "REQ-006"},
            point_requirements["TP-CONCURRENCY-SCHEDULE"],
        )

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
                    "execution_profile": "basic_psql",
                    "comparison": {
                        "mode": "exact_text",
                        "oracle": "upstream-postgresql-18.4",
                        "require_identical": True,
                    },
                    "cleanup": {"required": True, "idempotent": True},
                    "metadata": {"assignments": dict(obligation.assignments)},
                }
                if document["outcome"] == "expected_failure":
                    document["comparison"]["expected_sqlstate"] = "0A000"
                case_documents.append(document)

            from pg_case_factory.contracts import CaseManifest

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

        from pg_case_factory.contracts import CaseManifest

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
                "execution_profile": "basic_psql",
                "comparison": {
                    "mode": "exact_text",
                    "oracle": "upstream-postgresql-18.4",
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
