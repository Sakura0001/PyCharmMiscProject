from __future__ import annotations

import hashlib
import tempfile
import textwrap
import unittest
from pathlib import Path

import yaml

from mysql_case_factory.contracts import (
    ContractValidationError,
    REQUIRED_RISK_DECISIONS,
    inventory_values_sha256,
    load_case_manifest,
    load_coverage_plan,
    load_feature_manifest,
)


def _risk_decisions() -> dict:
    decisions = {
        risk: {
            "status": "not_applicable",
            "reason": f"The contract fixture does not exercise {risk} semantics.",
        }
        for risk in REQUIRED_RISK_DECISIONS
    }
    decisions["syntax"] = {
        "status": "covered",
        "axes": ["table_kind"],
        "test_points": ["TP-001"],
    }
    decisions["operation"] = {
        "status": "covered",
        "axes": ["table_kind", "column_type"],
        "test_points": ["TP-001"],
    }
    return decisions
from mysql_case_factory.feature_plan import topological_test_points


class FeatureContractTest(unittest.TestCase):
    def write_yaml(self, root: Path, name: str, document: dict) -> Path:
        path = root / name
        path.write_text(
            yaml.safe_dump(document, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        return path

    def feature_document(self) -> dict:
        return {
            "schema_version": 1,
            "kind": "feature_manifest",
            "feature_id": "remote-storage-read",
            "title": "Remote storage read path",
            "compatibility_target": "mysql-community-8.0.22",
            "source": {"path": "feature.md", "sha256": "a" * 64},
            "requirements": [
                {
                    "id": "REQ-001",
                    "description": "Committed rows remain observable.",
                    "source": {"section": "3.2", "line": 86},
                },
                {
                    "id": "REQ-002",
                    "description": "Rollback leaves no visible rows.",
                    "source": {"section": "3.3", "line": 101},
                },
            ],
        }

    def coverage_document(self) -> dict:
        table_values = ["heap", "partition_leaf"]
        column_values = ["integer", "text"]
        return {
            "schema_version": 1,
            "kind": "coverage_plan",
            "plan_id": "PLAN-REMOTE-READ",
            "feature_id": "remote-storage-read",
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
                    "reason": "The feature changes table storage, not every SQL object kind.",
                },
                "relation": {
                    "status": "not_applicable",
                    "reason": "The feature document is scoped specifically to tables.",
                },
                "table": {
                    "status": "not_applicable",
                    "reason": "The compact contract fixture does not claim canonical table-shape coverage.",
                },
                "column_type": {
                    "status": "not_applicable",
                    "reason": "The compact fixture does not claim the complete MySQL8022.4 type universe.",
                },
            },
            "risk_decisions": _risk_decisions(),
            "test_points": [
                {
                    "id": "TP-001",
                    "title": "Committed read",
                    "requirement_ids": ["REQ-001"],
                    "core_axes": ["table_kind", "column_type"],
                    "dependencies": [],
                    "default_outcome": "success",
                },
                {
                    "id": "TP-002",
                    "title": "Rollback read",
                    "requirement_ids": ["REQ-002"],
                    "core_axes": ["table_kind"],
                    "dependencies": ["TP-001"],
                    "default_outcome": "success",
                },
            ],
        }

    def case_document(self) -> dict:
        return {
            "schema_version": 1,
            "kind": "case_manifest",
            "case_id": "CASE-001",
            "test_point_id": "TP-001",
            "obligation_id": "obl-tp-001-0123456789ab",
            "outcome": "success",
            "sql_files": ["sql/case_001.sql"],
            "sql_sha256": "b4e0497804e46e0a0b0b8c31975b062152d551bac49c3c2e80932567b4085dcd",
            "execution_profile": "basic_mysql",
            "comparison": {
                "mode": "exact_text",
                "oracle": "upstream-mysql-community-8.0.22",
                "require_identical": True,
            },
            "cleanup": {"required": True, "idempotent": True},
        }

    def test_loads_and_validates_all_yaml_contracts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = load_feature_manifest(
                self.write_yaml(root, "feature.yaml", self.feature_document())
            )
            plan = load_coverage_plan(
                self.write_yaml(root, "plan.yaml", self.coverage_document()),
                manifest=manifest,
            )
            case = load_case_manifest(
                self.write_yaml(root, "case.yaml", self.case_document())
            )

        self.assertEqual(manifest.feature_id, "remote-storage-read")
        self.assertEqual([point.test_point_id for point in topological_test_points(plan)], ["TP-001", "TP-002"])
        self.assertEqual(case.outcome, "success")

    def test_duplicate_requirement_ids_are_rejected(self):
        document = self.feature_document()
        document["requirements"].append(dict(document["requirements"][0]))
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_yaml(Path(tmp), "feature.yaml", document)
            with self.assertRaisesRegex(ContractValidationError, "duplicate requirement id REQ-001"):
                load_feature_manifest(path)

    def test_contract_mapping_keys_must_be_strings(self):
        document = self.feature_document()
        document[1] = "integer keys must not be silently stringified"
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_yaml(Path(tmp), "numeric-key.yaml", document)
            with self.assertRaisesRegex(
                ContractValidationError,
                "mapping keys must be strings",
            ):
                load_feature_manifest(path)

    def test_metadata_rejects_implicit_yaml_dates_before_job_persistence(self):
        document = self.feature_document()
        document["metadata"] = {"reviewed_at": "2026-07-12"}
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_yaml(Path(tmp), "quoted-date.yaml", document)
            self.assertEqual(
                "2026-07-12",
                load_feature_manifest(path).metadata["reviewed_at"],
            )
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "reviewed_at: '2026-07-12'",
                    "reviewed_at: 2026-07-12",
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ContractValidationError,
                "JSON-compatible values",
            ):
                load_feature_manifest(path)

    def test_case_manifest_binds_the_exact_sql_digest(self):
        document = self.case_document()
        del document["sql_sha256"]
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ContractValidationError, "sql_sha256"):
                load_case_manifest(self.write_yaml(Path(tmp), "case.yaml", document))

    def test_case_execution_profile_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            external = self.case_document()
            external["execution_profile"] = "external_isolated"
            with self.assertRaisesRegex(
                ContractValidationError,
                "requires a stable execution_harness",
            ):
                load_case_manifest(self.write_yaml(root, "external.yaml", external))

            external["execution_harness"] = "external-load-data-ingest"
            loaded = load_case_manifest(
                self.write_yaml(root, "external-valid.yaml", external)
            )
            self.assertEqual("external-load-data-ingest", loaded.execution_harness)

            basic = self.case_document()
            basic["execution_harness"] = "must-not-be-silently-ignored"
            with self.assertRaisesRegex(
                ContractValidationError,
                "basic_mysql route must not declare execution_harness",
            ):
                load_case_manifest(self.write_yaml(root, "basic.yaml", basic))

    def test_feature_source_hash_target_and_requirement_locators_are_mandatory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing_hash = self.feature_document()
            del missing_hash["source"]["sha256"]
            with self.assertRaisesRegex(ContractValidationError, "source.sha256"):
                load_feature_manifest(
                    self.write_yaml(root, "missing-source-hash.yaml", missing_hash)
                )

            wrong_target = self.feature_document()
            wrong_target["compatibility_target"] = "postgresql-16.4"
            with self.assertRaisesRegex(ContractValidationError, "mysql-community-8.0.22"):
                load_feature_manifest(
                    self.write_yaml(root, "wrong-target.yaml", wrong_target)
                )

            missing_locator = self.feature_document()
            missing_locator["requirements"][0]["source"] = {}
            with self.assertRaisesRegex(ContractValidationError, "source must contain a locator"):
                load_feature_manifest(
                    self.write_yaml(root, "missing-locator.yaml", missing_locator)
                )

            fake_locator = self.feature_document()
            fake_locator["requirements"][0]["source"] = {"unrelated": "value"}
            with self.assertRaisesRegex(ContractValidationError, "at least one of"):
                load_feature_manifest(
                    self.write_yaml(root, "fake-locator.yaml", fake_locator)
                )

    def test_preserved_feature_source_is_contained_and_hash_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content = b"# feature\nexact source bytes\n"
            (root / "feature.md").write_bytes(content)
            document = self.feature_document()
            document["source"]["sha256"] = hashlib.sha256(content).hexdigest()
            manifest_path = self.write_yaml(root, "feature.yaml", document)

            manifest = load_feature_manifest(manifest_path, verify_source=True)
            self.assertEqual(manifest.source["path"], "feature.md")

            (root / "feature.md").write_bytes(content + b"changed\n")
            with self.assertRaisesRegex(ContractValidationError, "SHA-256 mismatch"):
                load_feature_manifest(manifest_path, verify_source=True)

            escaping = self.feature_document()
            escaping["source"]["path"] = "../feature.md"
            with self.assertRaisesRegex(ContractValidationError, "must be relative"):
                load_feature_manifest(self.write_yaml(root, "escape.yaml", escaping))

    def test_duplicate_test_point_ids_are_rejected(self):
        document = self.coverage_document()
        document["test_points"].append(dict(document["test_points"][0]))
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_yaml(Path(tmp), "plan.yaml", document)
            with self.assertRaisesRegex(ContractValidationError, "duplicate test point id TP-001"):
                load_coverage_plan(path)

    def test_missing_dependency_is_rejected(self):
        document = self.coverage_document()
        document["test_points"][1]["dependencies"] = ["TP-MISSING"]
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_yaml(Path(tmp), "plan.yaml", document)
            with self.assertRaisesRegex(ContractValidationError, "unknown dependency TP-MISSING"):
                load_coverage_plan(path)

    def test_dependency_cycle_is_rejected_with_cycle_path(self):
        document = self.coverage_document()
        document["test_points"][0]["dependencies"] = ["TP-002"]
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_yaml(Path(tmp), "plan.yaml", document)
            with self.assertRaisesRegex(ContractValidationError, r"dependency cycle: .*TP-001.*TP-002"):
                load_coverage_plan(path)

    def test_unknown_requirement_and_axis_are_rejected_against_manifest(self):
        coverage = self.coverage_document()
        coverage["test_points"][0]["requirement_ids"] = ["REQ-MISSING"]
        coverage["test_points"][0]["core_axes"] = ["table_kind", "missing_axis"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = load_feature_manifest(self.write_yaml(root, "feature.yaml", self.feature_document()))
            path = self.write_yaml(root, "plan.yaml", coverage)
            with self.assertRaises(ContractValidationError) as caught:
                load_coverage_plan(path, manifest=manifest)

        message = str(caught.exception)
        self.assertIn("unknown requirement REQ-MISSING", message)
        self.assertIn("unknown core axis missing_axis", message)

    def test_axes_require_a_complete_named_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing_source = self.coverage_document()
            del missing_source["axes"]["table_kind"]["inventory_source"]
            path = self.write_yaml(root, "missing-source.yaml", missing_source)
            with self.assertRaisesRegex(ContractValidationError, "inventory_source"):
                load_coverage_plan(path)

            sampled = self.coverage_document()
            sampled["axes"]["column_type"]["coverage_mode"] = "sampled"
            path = self.write_yaml(root, "sampled.yaml", sampled)
            with self.assertRaisesRegex(
                ContractValidationError, "coverage_mode must be complete"
            ):
                load_coverage_plan(path)

    def test_every_requirement_and_declared_axis_must_be_used(self):
        manifest_document = self.feature_document()
        manifest_document["requirements"].append(
            {
                "id": "REQ-UNUSED",
                "description": "This requirement must not disappear from coverage.",
                "source": {"section": "4.1"},
            }
        )
        coverage = self.coverage_document()
        coverage["axes"]["unused_axis"] = {
            "values": ["value"],
            "inventory_source": "inline:unused-axis",
            "coverage_mode": "complete",
            "inventory_count": 1,
            "inventory_sha256": inventory_values_sha256(["value"]),
            "description": "Complete unused fixture axis.",
            "derivation": "One semantic fixture value.",
            "source_locators": ["feature:REQ-001", "mysql8022:fixture"],
            "exclusion_policy": "No fixture value is excluded.",
            "review_status": "semantic_reviewed",
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = load_feature_manifest(
                self.write_yaml(root, "feature.yaml", manifest_document)
            )
            path = self.write_yaml(root, "plan.yaml", coverage)
            with self.assertRaises(ContractValidationError) as caught:
                load_coverage_plan(path, manifest=manifest)

        message = str(caught.exception)
        self.assertIn("requirement REQ-UNUSED is not covered", message)
        self.assertIn("axis unused_axis is not used", message)

    def test_wrong_kind_and_non_mapping_yaml_are_rejected_cleanly(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wrong = self.feature_document()
            wrong["kind"] = "coverage_plan"
            wrong_path = self.write_yaml(root, "wrong.yaml", wrong)
            with self.assertRaisesRegex(ContractValidationError, "kind must be feature_manifest"):
                load_feature_manifest(wrong_path)

            sequence_path = root / "sequence.yaml"
            sequence_path.write_text(textwrap.dedent("""
                - not
                - a
                - mapping
            """).strip() + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ContractValidationError, "YAML root must be a mapping"):
                load_feature_manifest(sequence_path)

    def test_duplicate_yaml_mapping_keys_are_rejected_instead_of_silently_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "duplicate.yaml"
            path.write_text(
                textwrap.dedent(
                    """
                    schema_version: 1
                    kind: feature_manifest
                    feature_id: first
                    feature_id: silently-overwritten-without-a-strict-loader
                    title: Duplicate key
                    compatibility_target: mysql-community-8.0.22
                    source: {path: feature.md}
                    requirements:
                      - id: REQ-001
                        description: Example
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ContractValidationError, "duplicate YAML key feature_id"):
                load_feature_manifest(path)

    def test_axis_snapshot_count_and_digest_are_mandatory_and_exact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for field in ("inventory_count", "inventory_sha256"):
                document = self.coverage_document()
                del document["axes"]["table_kind"][field]
                with self.subTest(field=field):
                    with self.assertRaisesRegex(ContractValidationError, field):
                        load_coverage_plan(self.write_yaml(root, f"missing-{field}.yaml", document))

            wrong_count = self.coverage_document()
            wrong_count["axes"]["table_kind"]["inventory_count"] = 1
            with self.assertRaisesRegex(ContractValidationError, "inventory_count.*does not match"):
                load_coverage_plan(self.write_yaml(root, "wrong-count.yaml", wrong_count))

            wrong_digest = self.coverage_document()
            wrong_digest["axes"]["table_kind"]["inventory_sha256"] = "0" * 64
            with self.assertRaisesRegex(ContractValidationError, "inventory_sha256.*does not match"):
                load_coverage_plan(self.write_yaml(root, "wrong-digest.yaml", wrong_digest))

    def test_axis_inventory_source_syntax_and_canonical_digest_are_strict(self):
        self.assertNotEqual(
            inventory_values_sha256([True, 1]),
            inventory_values_sha256([1, True]),
        )
        self.assertNotEqual(
            inventory_values_sha256([True]),
            inventory_values_sha256([1]),
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for source in ("inline:", "inventory.yaml", "#selector", "inventory.yaml#"):
                document = self.coverage_document()
                document["axes"]["table_kind"]["inventory_source"] = source
                with self.subTest(source=source):
                    with self.assertRaisesRegex(ContractValidationError, "inventory_source"):
                        load_coverage_plan(
                            self.write_yaml(
                                root,
                                f"bad-source-{len(source)}-{source.count('#')}.yaml",
                                document,
                            )
                        )

    def test_inline_inventory_requires_independent_provenance_fields(self):
        document = self.coverage_document()
        document["axes"]["table_kind"]["inventory_source"] = (
            "inline:feature-local-table-kinds"
        )
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(
                ContractValidationError,
                "inline inventories require description, derivation",
            ):
                load_coverage_plan(self.write_yaml(Path(tmp), "inline.yaml", document))

    def test_inline_inventory_requires_feature_and_mysql8022_source_locators(self):
        document = self.coverage_document()
        axis = document["axes"]["table_kind"]
        axis.update(
            {
                "inventory_source": "inline:feature-local-table-kinds",
                "description": "Fixture semantic classes.",
                "derivation": "Derived from a feature requirement.",
                "source_locators": ["feature:REQ-001"],
                "exclusion_policy": "No declared fixture class is excluded.",
                "review_status": "semantic_reviewed",
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(
                ContractValidationError,
                "requires both feature:<requirement-id> and mysql8022:<official-topic>",
            ):
                load_coverage_plan(self.write_yaml(Path(tmp), "inline.yaml", document))

    def test_all_four_scope_decisions_are_mandatory_and_exact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = self.coverage_document()
            del missing["scope_decisions"]["relation"]
            with self.assertRaisesRegex(ContractValidationError, "scope_decisions.*relation"):
                load_coverage_plan(self.write_yaml(root, "missing-scope.yaml", missing))

            extra = self.coverage_document()
            extra["scope_decisions"]["index"] = {
                "status": "not_applicable",
                "reason": "Not a required canonical scope.",
            }
            with self.assertRaisesRegex(ContractValidationError, "scope_decisions.*index"):
                load_coverage_plan(self.write_yaml(root, "extra-scope.yaml", extra))

    def test_all_mandatory_risk_decisions_and_covered_references_are_validated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = self.coverage_document()
            del missing["risk_decisions"]["maintenance"]
            with self.assertRaisesRegex(ContractValidationError, "risk_decisions.*maintenance"):
                load_coverage_plan(self.write_yaml(root, "missing-risk.yaml", missing))

            unknown = self.coverage_document()
            unknown["risk_decisions"]["syntax"]["test_points"] = ["TP-MISSING"]
            with self.assertRaisesRegex(ContractValidationError, "unknown test point TP-MISSING"):
                load_coverage_plan(self.write_yaml(root, "unknown-risk-point.yaml", unknown))

            unexercised = self.coverage_document()
            unexercised["risk_decisions"]["syntax"]["axes"] = ["column_type"]
            unexercised["risk_decisions"]["syntax"]["test_points"] = ["TP-002"]
            with self.assertRaisesRegex(ContractValidationError, "not exercised"):
                load_coverage_plan(self.write_yaml(root, "unexercised-risk.yaml", unexercised))

            extended = self.coverage_document()
            extended["risk_decisions"]["wal_flush_boundary"] = {
                "status": "covered",
                "axes": ["table_kind"],
                "test_points": ["TP-001"],
                "execution_harness": "external-crash-recovery",
            }
            extended["test_points"][0]["execution_rules"] = [
                {
                    "when": {"table_kind": "heap"},
                    "execution_profile": "external_isolated",
                    "execution_harness": "external-crash-recovery",
                }
            ]
            loaded = load_coverage_plan(
                self.write_yaml(root, "feature-specific-risk.yaml", extended)
            )
            self.assertIn("wal_flush_boundary", loaded.risk_decisions)

    def test_execution_harness_requires_nonempty_valid_declared_test_points(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            axes_only = self.coverage_document()
            axes_only["risk_decisions"]["external_probe"] = {
                "status": "covered",
                "axes": ["table_kind"],
                "test_points": [],
                "execution_harness": "external-probe",
            }
            with self.assertRaisesRegex(
                ContractValidationError,
                "covered risks require non-empty axes and test_points",
            ):
                load_coverage_plan(self.write_yaml(root, "axes-only-risk.yaml", axes_only))

            invalid_point = self.coverage_document()
            invalid_point["risk_decisions"]["external_probe"] = {
                "status": "covered",
                "axes": ["table_kind"],
                "test_points": ["TP-MISSING"],
                "execution_harness": "external-probe",
            }
            with self.assertRaisesRegex(
                ContractValidationError,
                r"external-probe.*no valid declared test points",
            ):
                load_coverage_plan(
                    self.write_yaml(root, "invalid-point-risk.yaml", invalid_point)
                )

    def test_not_applicable_scope_requires_a_reason(self):
        document = self.coverage_document()
        del document["scope_decisions"]["relation"]["reason"]
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_yaml(Path(tmp), "missing-reason.yaml", document)
            with self.assertRaisesRegex(ContractValidationError, "relation.*reason"):
                load_coverage_plan(path)

    def test_complete_scope_requires_used_axis_and_canonical_inventory_selector(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake = self.coverage_document()
            fake["axes"]["relation_kind"] = {
                "values": ["table"],
                "inventory_source": "inline:fake-relation-inventory",
                "coverage_mode": "complete",
                "inventory_count": 1,
                "inventory_sha256": inventory_values_sha256(["table"]),
                "description": "Counterfeit relation inventory.",
                "derivation": "Deliberately incomplete fixture.",
                "source_locators": ["feature:REQ-001", "mysql8022:fixture"],
                "exclusion_policy": "No declared fixture value is excluded.",
                "review_status": "semantic_reviewed",
            }
            fake["scope_decisions"]["relation"] = {
                "status": "complete",
                "axis": "relation_kind",
            }
            fake["test_points"][0]["core_axes"].append("relation_kind")
            with self.assertRaisesRegex(ContractValidationError, "relation.*canonical inventory source"):
                load_coverage_plan(self.write_yaml(root, "fake-relation.yaml", fake))

            unused = self.coverage_document()
            unused["axes"]["object_kind"] = {
                "values": ["table"],
                "inventory_source": "skills/mysql-8-0-22-sql-generation/references/combinations/_shared/coverage_inventory.yaml#sql_object_types.all_sql_object_types",
                "coverage_mode": "complete",
                "inventory_count": 1,
                "inventory_sha256": inventory_values_sha256(["table"]),
            }
            unused["scope_decisions"]["object"] = {
                "status": "complete",
                "axis": "object_kind",
            }
            with self.assertRaisesRegex(ContractValidationError, "object.*used by a test point"):
                load_coverage_plan(self.write_yaml(root, "unused-object.yaml", unused))

    def test_case_manifest_allows_only_executable_outcomes(self):
        document = self.case_document()
        document["outcome"] = "skipped"
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_yaml(Path(tmp), "case.yaml", document)
            with self.assertRaisesRegex(
                ContractValidationError,
                "outcome must be success or expected_failure",
            ):
                load_case_manifest(path)

            document["outcome"] = "justified_na"
            with self.assertRaisesRegex(
                ContractValidationError,
                "justified_na obligations do not generate cases",
            ):
                load_case_manifest(self.write_yaml(Path(tmp), "na-case.yaml", document))

    def test_case_comparison_and_cleanup_are_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            document = self.case_document()
            document["comparison"] = {
                "mode": "normalized_text",
                "oracle": "upstream-mysql-community-8.0.22",
                "require_identical": True,
                "normalization": {
                    "drop_line_patterns": [],
                    "replacements": [],
                    "strip_trailing_whitespace": False,
                },
                "reason": "No effective rule is deliberately invalid.",
            }
            with self.assertRaisesRegex(ContractValidationError, "must be exact_text"):
                load_case_manifest(self.write_yaml(root, "empty-normalization.yaml", document))

            document = self.case_document()
            document["cleanup"]["idempotent"] = False
            with self.assertRaisesRegex(ContractValidationError, "cleanup.idempotent must be true"):
                load_case_manifest(self.write_yaml(root, "unsafe-cleanup.yaml", document))


if __name__ == "__main__":
    unittest.main()
