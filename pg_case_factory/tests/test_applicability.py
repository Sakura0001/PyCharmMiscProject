from __future__ import annotations

import csv
import hashlib
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import yaml

from pg_case_factory.applicability import (
    LEDGER_COLUMNS,
    ApplicabilityValidationError,
    SHIPPED_UNIVERSE_COUNTS,
    UniverseCounts,
    applicability_axis_id,
    applicability_test_point_id,
    audit_universe_matrix_witness_coverage,
    compile_feature_applicability_plan,
    load_applicability_universe,
    load_feature_applicability_index,
    load_shipped_applicability_universe,
    reconcile_applicability_bindings,
    refresh_feature_applicability_index,
    scaffold_feature_applicability,
    stable_catalog_row_id,
)
from pg_case_factory.contracts import (
    REQUIRED_RISK_DECISIONS,
    inventory_values_sha256,
)


ROOT = Path(__file__).resolve().parents[1]
SHIPPED_LEDGER = (
    ROOT
    / "skills"
    / "pg-sql-generation"
    / "references"
    / "common"
    / "postgresql_18_4_factor_audit.tsv"
)


def _write_feature_and_base_plan(
    root: Path,
    *,
    feature_id: str = "feature-test",
    reserved_axis: bool = False,
    existing_harness: str | None = None,
) -> tuple[Path, Path]:
    source_path = root / "feature-document.md"
    source_path.write_text("# Feature\n\nPreserve PostgreSQL behavior.\n", encoding="utf-8")
    source_sha = hashlib.sha256(source_path.read_bytes()).hexdigest()
    manifest_path = root / "feature_manifest.yaml"
    _write_yaml(
        manifest_path,
        {
            "schema_version": 1,
            "kind": "feature_manifest",
            "feature_id": feature_id,
            "title": "Applicability compiler fixture",
            "compatibility_target": "postgresql-18.4",
            "source": {"path": source_path.name, "sha256": source_sha},
            "requirements": [
                {
                    "id": "REQ-001",
                    "description": "Preserve observable SQL behavior.",
                    "source": {"section": "Feature"},
                }
            ],
            "metadata": {"unresolved_questions": []},
        },
    )
    axis_id = (
        applicability_axis_id("test_statement") if reserved_axis else "baseline_axis"
    )
    plan_path = root / "base_plan.yaml"
    risk_decisions = {
        risk: {
            "status": "not_applicable",
            "reason": f"The compiler fixture does not exercise {risk} semantics.",
        }
        for risk in REQUIRED_RISK_DECISIONS
    }
    point = {
        "id": "TP-BASELINE",
        "title": "Compiler baseline",
        "requirement_ids": ["REQ-001"],
        "core_axes": [axis_id],
        "dependencies": [],
        "default_outcome": "success",
    }
    if existing_harness is not None:
        risk_decisions["concurrency"] = {
            "status": "covered",
            "axes": [axis_id],
            "test_points": ["TP-BASELINE"],
            "execution_harness": existing_harness,
        }
        point["default_execution_profile"] = "external_isolated"
        point["default_execution_harness"] = existing_harness
    _write_yaml(
        plan_path,
        {
            "schema_version": 1,
            "kind": "coverage_plan",
            "plan_id": "PLAN-APPLICABILITY-COMPILER",
            "feature_id": feature_id,
            "axes": {
                axis_id: {
                    "values": ["baseline"],
                    "inventory_source": "inline:compiler-baseline",
                    "coverage_mode": "complete",
                    "inventory_count": 1,
                    "inventory_sha256": inventory_values_sha256(["baseline"]),
                    "description": "Minimal executable baseline axis.",
                    "derivation": "Use the single compiler fixture baseline value.",
                    "source_locators": ["feature:REQ-001", "pg18:sql-select"],
                    "exclusion_policy": "No baseline value is excluded.",
                    "review_status": "semantic_reviewed",
                }
            },
            "scope_decisions": {
                scope: {
                    "status": "not_applicable",
                    "reason": f"The compiler fixture does not claim canonical {scope} scope.",
                }
                for scope in ("object", "relation", "table", "column_type")
            },
            "risk_decisions": risk_decisions,
            "test_points": [point],
        },
    )
    return manifest_path, plan_path


def _write_yaml(path: Path, document) -> None:
    path.write_text(
        yaml.safe_dump(document, allow_unicode=True, sort_keys=False, width=1000),
        encoding="utf-8",
    )


class ApplicabilityFixture:
    def __init__(self, root: Path, values=("alpha", "beta")):
        self.root = root
        self.values = tuple(values)
        self.statement_key = "test_statement"
        self.source_reference = "references/statements/ddl/table/test_statement.md"
        self.ledger_path = root / "ledger.tsv"
        rows = []
        for value in self.values:
            rows.append(
                {
                    "statement_key": self.statement_key,
                    "source_reference": self.source_reference,
                    "factor": "mode",
                    "tier": "T1",
                    "value": value,
                    "synopsis_change": "unchanged",
                    "document_change": "unchanged",
                    "review_status": "static_reviewed",
                    "catalog_readiness": "static_ready",
                    "factor_disposition": "inherited_unchanged",
                    "required_test_points": "",
                    "official_source_target": "https://www.postgresql.org/docs/18/sql-test.html",
                    "evidence": "sql-test:fixture",
                }
            )
        with self.ledger_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=LEDGER_COLUMNS, delimiter="\t")
            writer.writeheader()
            writer.writerows(rows)
        self.universe = load_applicability_universe(
            self.ledger_path,
            expected_counts=UniverseCounts(1, 1, len(self.values)),
        )
        self.matrix_path = (
            root
            / "skills"
            / "pg-sql-generation"
            / "references"
            / "combinations"
            / "ddl"
            / "table"
            / "test_statement.yaml"
        )
        self.matrix_path.parent.mkdir(parents=True)
        _write_yaml(
            self.matrix_path,
            {
                "schema_version": 1,
                "kind": "statement_combination_matrix",
                "statement": {
                    "key": self.statement_key,
                    "source_reference": self.source_reference,
                },
                "factor_contract": {
                    "factors": {
                        "mode": {
                            "required_values": list(self.values),
                        }
                    }
                },
                "combination_groups": [
                    {
                        "id": "group-all-modes",
                        "factors": {"mode": self.values[0]},
                        "expansion": {
                            "mode": {"mode": "explicit", "values": list(self.values)}
                        },
                    }
                ],
            },
        )
        self.matrix_relative = self.matrix_path.relative_to(root).as_posix()
        self.matrix_sha256 = hashlib.sha256(self.matrix_path.read_bytes()).hexdigest()
        self.bundle_root = root / "bundle"
        self.index_path = scaffold_feature_applicability(
            self.universe,
            self.bundle_root,
            feature_id="feature-test",
            universe_path="ledger.tsv",
        )
        self.review_path = self.bundle_root / "reviews" / "test_statement.yaml"

    def review_document(self):
        return yaml.safe_load(self.review_path.read_text(encoding="utf-8"))

    def save_review(self, document) -> None:
        _write_yaml(self.review_path, document)
        self.refresh()

    def refresh(self) -> None:
        refresh_feature_applicability_index(
            self.index_path,
            repository_root=self.root,
            expected_counts=UniverseCounts(1, 1, len(self.values)),
        )

    @staticmethod
    def covered_scope_decision():
        return {
            "status": "covered",
            "requirement_ids": ["REQ-001"],
            "source_locators": ["feature:REQ-001", "pg18:sql-test"],
        }

    def covered_value_decision(self, row_id: str, obligation_id: str):
        return {
            "status": "covered",
            "requirement_ids": ["REQ-001"],
            "source_locators": ["feature:REQ-001", "pg18:sql-test"],
            "planned_outcome": "success",
            "execution_profile": "basic_psql",
            "binding": {
                "test_point_id": "TP-SFV-TEST",
                "obligation_id": obligation_id,
            },
            "matrix_witness": {
                "path": self.matrix_relative,
                "sha256": self.matrix_sha256,
                "combination_group_id": "group-all-modes",
            },
        }

    def draft_covered_value_decision(
        self,
        *,
        outcome: str = "success",
        execution_profile: str = "basic_psql",
        execution_harness: str | None = None,
    ):
        decision = self.covered_value_decision("unused", "unused")
        decision.pop("binding")
        decision["planned_outcome"] = outcome
        decision["execution_profile"] = execution_profile
        if outcome == "expected_failure":
            decision["expected_failure_reason"] = (
                "PostgreSQL rejects the synthetic factor value in this execution context."
            )
        if execution_harness is not None:
            decision["execution_harness"] = execution_harness
        return decision

    @staticmethod
    def exclusion_reason():
        return {
            "id": "EXC-BETA",
            "text": "REQ-001 changes only the alpha branch; PostgreSQL beta semantics are outside the preserved feature boundary.",
            "requirement_ids": ["REQ-001"],
            "source_locators": ["feature:REQ-001", "pg18:sql-test"],
        }

    def make_complete(self):
        document = self.review_document()
        document["statement_decision"] = self.covered_scope_decision()
        factor = document["factors"][0]
        factor["factor_decision"] = self.covered_scope_decision()
        factor["values"][0]["decision"] = self.covered_value_decision(
            factor["values"][0]["row_id"],
            "obl-alpha",
        )
        if len(factor["values"]) > 1:
            for value in factor["values"][1:]:
                value["decision"] = {
                    "status": "justified_exclusion",
                    "reason_id": "EXC-BETA",
                }
            document["reasons"] = [self.exclusion_reason()]
        self.save_review(document)
        return load_feature_applicability_index(
            self.index_path,
            repository_root=self.root,
            known_requirement_ids={"REQ-001"},
            require_complete=True,
            expected_counts=UniverseCounts(1, 1, len(self.values)),
        )


class ApplicabilityUniverseTest(unittest.TestCase):
    def test_shipped_universe_is_exact_and_row_ids_are_stable(self):
        universe = load_shipped_applicability_universe(ROOT)
        self.assertEqual(universe.counts, SHIPPED_UNIVERSE_COUNTS)
        self.assertEqual(len(universe.row_by_id()), 9978)
        self.assertEqual(
            universe.semantic_sha256,
            "42707defa63ed63e2c15e6d0fa1cde04b93aef9b3c735d1149198b10eb6977fc",
        )
        first = universe.rows[0]
        self.assertEqual(first.row_id, "sfv-40b874ff56c99d3dd8aae9d6")
        self.assertEqual(
            first.row_id,
            stable_catalog_row_id(first.statement_key, first.factor, first.value),
        )

    def test_all_9978_rows_have_a_group_or_pg18_compatibility_witness(self):
        universe = load_shipped_applicability_universe(ROOT)
        report = audit_universe_matrix_witness_coverage(
            universe,
            repository_root=ROOT,
        )
        self.assertTrue(report.complete, report.to_dict())
        self.assertEqual(report.total_rows, 9978)
        self.assertEqual(report.covered_rows, 9978)
        self.assertEqual(report.combination_group_rows, 9968)
        self.assertEqual(report.pg18_compatibility_point_rows, 10)

    def test_ledger_rejects_duplicate_keys_and_non_ready_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = ApplicabilityFixture(Path(tmp), values=("alpha",))
            text = fixture.ledger_path.read_text(encoding="utf-8")
            data_line = text.splitlines()[1]
            fixture.ledger_path.write_text(text + data_line + "\n", encoding="utf-8")
            with self.assertRaisesRegex(
                ApplicabilityValidationError, "duplicate applicability ledger key"
            ):
                load_applicability_universe(fixture.ledger_path)

            lines = text.splitlines()
            columns = lines[0].split("\t")
            values = lines[1].split("\t")
            values[columns.index("catalog_readiness")] = "pending"
            fixture.ledger_path.write_text(
                "\t".join(columns) + "\n" + "\t".join(values) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ApplicabilityValidationError, "not static_ready"):
                load_applicability_universe(fixture.ledger_path)

    def test_ledger_rejects_unsafe_statement_keys_before_scaffolding_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = ApplicabilityFixture(Path(tmp), values=("alpha",))
            text = fixture.ledger_path.read_text(encoding="utf-8")
            fixture.ledger_path.write_text(
                text.replace("test_statement", "../escaped", 1),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ApplicabilityValidationError,
                "statement_key is not a portable lowercase identifier",
            ):
                load_applicability_universe(fixture.ledger_path)


class ApplicabilityScaffoldTest(unittest.TestCase):
    def test_shipped_scaffold_has_183_reviews_and_9978_pending_rows_within_budget(self):
        started = time.perf_counter()
        universe = load_shipped_applicability_universe(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            index = scaffold_feature_applicability(
                universe,
                Path(tmp) / "bundle",
                feature_id="performance-fixture",
                universe_path=SHIPPED_LEDGER.relative_to(ROOT).as_posix(),
            )
            loaded = load_feature_applicability_index(
                index,
                repository_root=ROOT,
                require_complete=False,
                expected_counts=SHIPPED_UNIVERSE_COUNTS,
            )
            self.assertEqual(len(loaded.reviews), 183)
            self.assertEqual(loaded.summary.pending, 9978)
            self.assertFalse(loaded.summary.complete)
            self.assertEqual(
                len(tuple((Path(tmp) / "bundle" / "reviews").glob("*.yaml"))),
                183,
            )
            with self.assertRaisesRegex(
                ApplicabilityValidationError, "review is incomplete"
            ):
                load_feature_applicability_index(
                    index,
                    repository_root=ROOT,
                    require_complete=True,
                    expected_counts=SHIPPED_UNIVERSE_COUNTS,
                )
        self.assertLess(time.perf_counter() - started, 12.0)

    def test_scaffold_never_overwrites_an_existing_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = ApplicabilityFixture(Path(tmp))
            with self.assertRaisesRegex(
                ApplicabilityValidationError, "destination already exists"
            ):
                scaffold_feature_applicability(
                    fixture.universe,
                    fixture.bundle_root,
                    feature_id="feature-test",
                    universe_path="ledger.tsv",
                )

    def test_refresh_changes_only_review_hash_and_then_validation_succeeds(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = ApplicabilityFixture(Path(tmp))
            index_before = yaml.safe_load(fixture.index_path.read_text(encoding="utf-8"))
            fixture.review_path.write_text(
                fixture.review_path.read_text(encoding="utf-8")
                + "# reviewer saved this pending statement\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ApplicabilityValidationError, "sha256 does not match"):
                load_feature_applicability_index(
                    fixture.index_path,
                    repository_root=fixture.root,
                )
            refresh_feature_applicability_index(
                fixture.index_path,
                repository_root=fixture.root,
                expected_counts=UniverseCounts(1, 1, 2),
            )
            index_after = yaml.safe_load(fixture.index_path.read_text(encoding="utf-8"))
            self.assertEqual(index_before["universe"], index_after["universe"])
            self.assertEqual(
                index_before["reviews"][0]["path"],
                index_after["reviews"][0]["path"],
            )
            loaded = load_feature_applicability_index(
                fixture.index_path,
                repository_root=fixture.root,
            )
            self.assertEqual(loaded.summary.pending, 2)


class ApplicabilitySchemaTest(unittest.TestCase):
    def mutate_review(self, fixture: ApplicabilityFixture, mutator):
        document = fixture.review_document()
        mutator(document)
        fixture.save_review(document)

    def test_missing_duplicate_unknown_and_wildcard_rows_fail_closed(self):
        mutations = (
            (
                "must contain exactly 2 rows",
                lambda doc: doc["factors"][0]["values"].pop(),
            ),
            (
                "must be canonical row",
                lambda doc: doc["factors"][0]["values"].__setitem__(
                    1, dict(doc["factors"][0]["values"][0])
                ),
            ),
            (
                "must be canonical row",
                lambda doc: doc["factors"][0]["values"][1].__setitem__(
                    "value", "unknown"
                ),
            ),
            (
                "unexpected default_decision",
                lambda doc: doc["factors"][0].__setitem__(
                    "default_decision", {"status": "covered"}
                ),
            ),
        )
        for expected, mutation in mutations:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as tmp:
                fixture = ApplicabilityFixture(Path(tmp))
                self.mutate_review(fixture, mutation)
                with self.assertRaisesRegex(ApplicabilityValidationError, expected):
                    load_feature_applicability_index(
                        fixture.index_path,
                        repository_root=fixture.root,
                    )

    def test_exclusion_requires_concrete_reason_and_requirement_locators(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = ApplicabilityFixture(Path(tmp))
            document = fixture.review_document()
            document["statement_decision"] = {
                "status": "justified_exclusion",
                "reason_id": "EXC-ALL",
            }
            factor = document["factors"][0]
            factor["factor_decision"] = {
                "status": "justified_exclusion",
                "reason_id": "EXC-ALL",
            }
            for value in factor["values"]:
                value["decision"] = {
                    "status": "justified_exclusion",
                    "reason_id": "EXC-ALL",
                }
            document["reasons"] = [
                {
                    "id": "EXC-ALL",
                    "text": "N/A",
                    "requirement_ids": ["REQ-001"],
                    "source_locators": ["feature:REQ-001"],
                }
            ]
            fixture.save_review(document)
            with self.assertRaisesRegex(ApplicabilityValidationError, "concrete exclusion reason"):
                load_feature_applicability_index(
                    fixture.index_path,
                    repository_root=fixture.root,
                    known_requirement_ids={"REQ-001"},
                )

            document["reasons"][0]["text"] = (
                "The feature has no user-visible contract for this statement family."
            )
            fixture.save_review(document)
            with self.assertRaisesRegex(ApplicabilityValidationError, "requires at least one pg18"):
                load_feature_applicability_index(
                    fixture.index_path,
                    repository_root=fixture.root,
                    known_requirement_ids={"REQ-001"},
                )

            document["reasons"][0]["source_locators"].append("pg18:sql-test")
            document["reasons"][0]["requirement_ids"] = ["REQ-UNKNOWN"]
            document["reasons"][0]["source_locators"][0] = "feature:REQ-UNKNOWN"
            fixture.save_review(document)
            with self.assertRaisesRegex(ApplicabilityValidationError, "unknown requirement"):
                load_feature_applicability_index(
                    fixture.index_path,
                    repository_root=fixture.root,
                    known_requirement_ids={"REQ-001"},
                )

    def test_matrix_sha_group_and_factor_value_witness_are_strict(self):
        variants = (
            (
                "sha256 does not match",
                lambda decision: decision["matrix_witness"].__setitem__(
                    "sha256", "0" * 64
                ),
            ),
            (
                "must identify exactly one coverage",
                lambda decision: decision["matrix_witness"].__setitem__(
                    "combination_group_id", "missing-group"
                ),
            ),
        )
        for expected, mutation in variants:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as tmp:
                fixture = ApplicabilityFixture(Path(tmp))
                document = fixture.review_document()
                document["statement_decision"] = fixture.covered_scope_decision()
                factor = document["factors"][0]
                factor["factor_decision"] = fixture.covered_scope_decision()
                factor["values"][0]["decision"] = fixture.covered_value_decision(
                    factor["values"][0]["row_id"], "obl-alpha"
                )
                factor["values"][1]["decision"] = {
                    "status": "justified_exclusion",
                    "reason_id": "EXC-BETA",
                }
                document["reasons"] = [fixture.exclusion_reason()]
                mutation(factor["values"][0]["decision"])
                fixture.save_review(document)
                with self.assertRaisesRegex(ApplicabilityValidationError, expected):
                    load_feature_applicability_index(
                        fixture.index_path,
                        repository_root=fixture.root,
                        known_requirement_ids={"REQ-001"},
                    )

    def test_matrix_witness_cannot_use_an_lookalike_combinations_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = ApplicabilityFixture(Path(tmp))
            outside = fixture.root / "other" / "combinations" / "test_statement.yaml"
            outside.parent.mkdir(parents=True)
            outside.write_bytes(fixture.matrix_path.read_bytes())
            document = fixture.review_document()
            document["statement_decision"] = fixture.covered_scope_decision()
            factor = document["factors"][0]
            factor["factor_decision"] = fixture.covered_scope_decision()
            covered = fixture.covered_value_decision(
                factor["values"][0]["row_id"], "obl-alpha"
            )
            covered["matrix_witness"]["path"] = outside.relative_to(
                fixture.root
            ).as_posix()
            factor["values"][0]["decision"] = covered
            factor["values"][1]["decision"] = {
                "status": "justified_exclusion",
                "reason_id": "EXC-BETA",
            }
            document["reasons"] = [fixture.exclusion_reason()]
            fixture.save_review(document)
            with self.assertRaisesRegex(
                ApplicabilityValidationError,
                "must identify a statement combination matrix under",
            ):
                load_feature_applicability_index(
                    fixture.index_path,
                    repository_root=fixture.root,
                    known_requirement_ids={"REQ-001"},
                )

    def test_pg18_coverage_witness_id_must_be_unique_across_groups_and_points(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = ApplicabilityFixture(Path(tmp))
            matrix = yaml.safe_load(fixture.matrix_path.read_text(encoding="utf-8"))
            matrix["pg18_compatibility"] = {
                "target_version": "18.4",
                "test_points": [
                    {
                        "id": "group-all-modes",
                        "affected_factors": ["mode"],
                        "affected_values": {"mode": ["alpha"]},
                        "sql": "SELECT 1;",
                        "oracle": "reference_parity",
                    }
                ],
            }
            _write_yaml(fixture.matrix_path, matrix)
            fixture.matrix_sha256 = hashlib.sha256(
                fixture.matrix_path.read_bytes()
            ).hexdigest()
            document = fixture.review_document()
            document["statement_decision"] = fixture.covered_scope_decision()
            factor = document["factors"][0]
            factor["factor_decision"] = fixture.covered_scope_decision()
            factor["values"][0]["decision"] = fixture.covered_value_decision(
                factor["values"][0]["row_id"], "obl-alpha"
            )
            factor["values"][1]["decision"] = {
                "status": "justified_exclusion",
                "reason_id": "EXC-BETA",
            }
            document["reasons"] = [fixture.exclusion_reason()]
            fixture.save_review(document)
            with self.assertRaisesRegex(
                ApplicabilityValidationError,
                "coverage witness ID is not unique",
            ):
                load_feature_applicability_index(
                    fixture.index_path,
                    repository_root=fixture.root,
                    known_requirement_ids={"REQ-001"},
                )

    def test_covered_route_requires_valid_profile_and_external_harness(self):
        variants = (
            (
                "execution_profile must be basic_psql or external_isolated",
                lambda decision: decision.__setitem__("execution_profile", "unknown"),
            ),
            (
                "execution_harness must be a non-empty",
                lambda decision: decision.__setitem__(
                    "execution_profile", "external_isolated"
                ),
            ),
            (
                "unexpected execution_harness",
                lambda decision: decision.__setitem__(
                    "execution_harness", "must-not-exist-for-basic"
                ),
            ),
        )
        for expected, mutation in variants:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as tmp:
                fixture = ApplicabilityFixture(Path(tmp))
                document = fixture.review_document()
                document["statement_decision"] = fixture.covered_scope_decision()
                factor = document["factors"][0]
                factor["factor_decision"] = fixture.covered_scope_decision()
                decision = fixture.covered_value_decision(
                    factor["values"][0]["row_id"], "obl-alpha"
                )
                mutation(decision)
                factor["values"][0]["decision"] = decision
                factor["values"][1]["decision"] = {
                    "status": "justified_exclusion",
                    "reason_id": "EXC-BETA",
                }
                document["reasons"] = [fixture.exclusion_reason()]
                fixture.save_review(document)
                with self.assertRaisesRegex(ApplicabilityValidationError, expected):
                    load_feature_applicability_index(
                        fixture.index_path,
                        repository_root=fixture.root,
                        known_requirement_ids={"REQ-001"},
                    )

    def test_same_matrix_is_loaded_once_for_multiple_covered_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = ApplicabilityFixture(Path(tmp))
            document = fixture.review_document()
            document["statement_decision"] = fixture.covered_scope_decision()
            factor = document["factors"][0]
            factor["factor_decision"] = fixture.covered_scope_decision()
            for index, value in enumerate(factor["values"]):
                value["decision"] = fixture.covered_value_decision(
                    value["row_id"], f"obl-{index}"
                )
            fixture.save_review(document)

            import pg_case_factory.applicability as applicability_module

            original = applicability_module._load_yaml
            matrix_loads = []

            def counted(path, location):
                if Path(path).resolve() == fixture.matrix_path.resolve():
                    matrix_loads.append(path)
                return original(path, location)

            with mock.patch.object(applicability_module, "_load_yaml", side_effect=counted):
                loaded = load_feature_applicability_index(
                    fixture.index_path,
                    repository_root=fixture.root,
                    known_requirement_ids={"REQ-001"},
                    require_complete=True,
                )
            self.assertEqual(loaded.summary.covered, 2)
            self.assertEqual(len(matrix_loads), 1)


class ApplicabilityCompilerTest(unittest.TestCase):
    def test_incremental_compile_preserves_binding_and_routes_every_row_explicitly(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = ApplicabilityFixture(root)
            manifest_path, base_plan_path = _write_feature_and_base_plan(root)
            output_path = root / "compiled_plan.yaml"

            document = fixture.review_document()
            first_value = document["factors"][0]["values"][0]
            first_value["decision"] = fixture.draft_covered_value_decision()
            fixture.save_review(document)

            draft = load_feature_applicability_index(
                fixture.index_path,
                repository_root=root,
                known_requirement_ids={"REQ-001"},
                draft=True,
            )
            self.assertEqual(draft.summary.covered, 1)
            self.assertEqual(draft.summary.unbound_covered, 1)
            with self.assertRaisesRegex(ApplicabilityValidationError, "missing binding"):
                load_feature_applicability_index(
                    fixture.index_path,
                    repository_root=root,
                    known_requirement_ids={"REQ-001"},
                    draft=False,
                )

            first_result = compile_feature_applicability_plan(
                manifest_path=manifest_path,
                base_plan_path=base_plan_path,
                index_path=fixture.index_path,
                output_path=output_path,
                repository_root=root,
                expected_counts=UniverseCounts(1, 1, 2),
            )
            self.assertEqual(first_result.generated_axis_ids, (applicability_axis_id("test_statement"),))
            self.assertEqual(
                first_result.generated_test_point_ids,
                (applicability_test_point_id("test_statement"),),
            )
            first_binding = first_result.applicability.covered_rows()[0][1].binding
            self.assertIsNotNone(first_binding)

            document = fixture.review_document()
            document["statement_decision"] = fixture.covered_scope_decision()
            factor = document["factors"][0]
            factor["factor_decision"] = fixture.covered_scope_decision()
            second_value = factor["values"][1]
            second_value["decision"] = fixture.draft_covered_value_decision(
                outcome="expected_failure",
                execution_profile="external_isolated",
                execution_harness="external-synthetic-harness",
            )
            fixture.save_review(document)

            second_result = compile_feature_applicability_plan(
                manifest_path=manifest_path,
                base_plan_path=base_plan_path,
                index_path=fixture.index_path,
                output_path=output_path,
                repository_root=root,
                expected_counts=UniverseCounts(1, 1, 2),
            )
            covered = second_result.applicability.covered_rows()
            self.assertEqual(len(covered), 2)
            self.assertEqual(covered[0][1].binding, first_binding)
            self.assertTrue(second_result.applicability.summary.complete)
            self.assertTrue(second_result.reconciliation.complete)

            point_id = applicability_test_point_id("test_statement")
            point_obligations = [
                obligation
                for obligation in second_result.obligations
                if obligation.test_point_id == point_id
            ]
            self.assertEqual(len(point_obligations), 2)
            by_row = {
                obligation.assignments[applicability_axis_id("test_statement")]: obligation
                for obligation in point_obligations
            }
            first_row = covered[0][0]
            second_row = covered[1][0]
            self.assertEqual(by_row[first_row.row_id].outcome, "success")
            self.assertEqual(
                by_row[first_row.row_id].execution_profile,
                "basic_psql",
            )
            self.assertEqual(by_row[second_row.row_id].outcome, "expected_failure")
            self.assertEqual(
                by_row[second_row.row_id].execution_profile,
                "external_isolated",
            )
            self.assertEqual(
                by_row[second_row.row_id].execution_harness,
                "external-synthetic-harness",
            )
            matching_risks = [
                decision
                for decision in second_result.plan.risk_decisions.values()
                if decision.execution_harness == "external-synthetic-harness"
            ]
            self.assertEqual(len(matching_risks), 1)
            self.assertIn(point_id, matching_risks[0].test_points)
            self.assertIn(
                applicability_axis_id("test_statement"),
                matching_risks[0].axes,
            )

    def test_fully_excluded_statement_generates_no_axis_or_point(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = ApplicabilityFixture(root)
            manifest_path, base_plan_path = _write_feature_and_base_plan(root)
            document = fixture.review_document()
            document["statement_decision"] = {
                "status": "justified_exclusion",
                "reason_id": "EXC-ALL",
            }
            factor = document["factors"][0]
            factor["factor_decision"] = {
                "status": "justified_exclusion",
                "reason_id": "EXC-ALL",
            }
            for value in factor["values"]:
                value["decision"] = {
                    "status": "justified_exclusion",
                    "reason_id": "EXC-ALL",
                }
            reason = fixture.exclusion_reason()
            reason["id"] = "EXC-ALL"
            document["reasons"] = [reason]
            fixture.save_review(document)
            result = compile_feature_applicability_plan(
                manifest_path=manifest_path,
                base_plan_path=base_plan_path,
                index_path=fixture.index_path,
                output_path=root / "compiled.yaml",
                repository_root=root,
                expected_counts=UniverseCounts(1, 1, 2),
            )
            self.assertEqual(result.generated_axis_ids, ())
            self.assertEqual(result.generated_test_point_ids, ())
            self.assertTrue(result.applicability.summary.complete)
            self.assertTrue(result.reconciliation.complete)
            self.assertEqual(result.applicability.summary.justified_exclusion, 2)

    def test_external_rows_merge_into_an_existing_harness_risk(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = ApplicabilityFixture(root)
            manifest_path, base_plan_path = _write_feature_and_base_plan(
                root,
                existing_harness="shared-external-harness",
            )
            document = fixture.review_document()
            value = document["factors"][0]["values"][0]
            value["decision"] = fixture.draft_covered_value_decision(
                execution_profile="external_isolated",
                execution_harness="shared-external-harness",
            )
            fixture.save_review(document)
            result = compile_feature_applicability_plan(
                manifest_path=manifest_path,
                base_plan_path=base_plan_path,
                index_path=fixture.index_path,
                output_path=root / "compiled.yaml",
                repository_root=root,
                expected_counts=UniverseCounts(1, 1, 2),
            )
            matching = [
                (risk_id, decision)
                for risk_id, decision in result.plan.risk_decisions.items()
                if decision.execution_harness == "shared-external-harness"
            ]
            self.assertEqual(len(matching), 1)
            self.assertEqual(matching[0][0], "concurrency")
            self.assertIn(
                applicability_axis_id("test_statement"),
                matching[0][1].axes,
            )
            self.assertIn(
                applicability_test_point_id("test_statement"),
                matching[0][1].test_points,
            )

    def test_compiler_rejects_reserved_base_axis_and_draft_evidence_gaps(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = ApplicabilityFixture(root)
            manifest_path, base_plan_path = _write_feature_and_base_plan(
                root,
                reserved_axis=True,
            )
            with self.assertRaisesRegex(
                ApplicabilityValidationError,
                "already contains reserved applicability axis",
            ):
                compile_feature_applicability_plan(
                    manifest_path=manifest_path,
                    base_plan_path=base_plan_path,
                    index_path=fixture.index_path,
                    output_path=root / "compiled.yaml",
                    repository_root=root,
                    expected_counts=UniverseCounts(1, 1, 2),
                )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = ApplicabilityFixture(root)
            document = fixture.review_document()
            decision = fixture.draft_covered_value_decision()
            decision["requirement_ids"] = ["REQ-UNKNOWN"]
            decision["source_locators"][0] = "feature:REQ-UNKNOWN"
            document["factors"][0]["values"][0]["decision"] = decision
            fixture.save_review(document)
            with self.assertRaisesRegex(ApplicabilityValidationError, "unknown requirement"):
                load_feature_applicability_index(
                    fixture.index_path,
                    repository_root=root,
                    known_requirement_ids={"REQ-001"},
                    draft=True,
                )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = ApplicabilityFixture(root)
            document = fixture.review_document()
            decision = fixture.draft_covered_value_decision()
            decision.pop("matrix_witness")
            document["factors"][0]["values"][0]["decision"] = decision
            fixture.save_review(document)
            with self.assertRaisesRegex(ApplicabilityValidationError, "missing matrix_witness"):
                load_feature_applicability_index(
                    fixture.index_path,
                    repository_root=root,
                    known_requirement_ids={"REQ-001"},
                    draft=True,
                )

    def test_shipped_partial_draft_compiles_one_row_with_9978_upper_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            universe = load_shipped_applicability_universe(ROOT)
            index_path = scaffold_feature_applicability(
                universe,
                work / "bundle",
                feature_id="shipped-partial",
                universe_path=SHIPPED_LEDGER.relative_to(ROOT).as_posix(),
            )
            review_path = work / "bundle" / "reviews" / "delete.yaml"
            review = yaml.safe_load(review_path.read_text(encoding="utf-8"))
            factor = next(
                item for item in review["factors"] if item["factor"] == "result_shape"
            )
            value = next(
                item
                for item in factor["values"]
                if item["value"] == "returning_old_new_aliases"
            )
            matrix_path = (
                ROOT
                / "skills"
                / "pg-sql-generation"
                / "references"
                / "combinations"
                / "dml"
                / "table"
                / "delete.yaml"
            )
            value["decision"] = {
                "status": "covered",
                "requirement_ids": ["REQ-001"],
                "source_locators": ["feature:REQ-001", "pg18:sql-delete"],
                "planned_outcome": "success",
                "execution_profile": "basic_psql",
                "matrix_witness": {
                    "path": matrix_path.relative_to(ROOT).as_posix(),
                    "sha256": hashlib.sha256(matrix_path.read_bytes()).hexdigest(),
                    "combination_group_id": "PG18-DELETE-RETURNING-ALIASES",
                },
            }
            _write_yaml(review_path, review)
            refresh_feature_applicability_index(
                index_path,
                repository_root=ROOT,
                expected_counts=SHIPPED_UNIVERSE_COUNTS,
            )
            manifest_path, base_plan_path = _write_feature_and_base_plan(
                work,
                feature_id="shipped-partial",
            )
            result = compile_feature_applicability_plan(
                manifest_path=manifest_path,
                base_plan_path=base_plan_path,
                index_path=index_path,
                output_path=work / "compiled.yaml",
                repository_root=ROOT,
                inventory_root=ROOT,
                expected_counts=SHIPPED_UNIVERSE_COUNTS,
            )
            self.assertEqual(result.canonical_upper_bound, 9978)
            self.assertEqual(result.applicability.summary.covered, 1)
            self.assertEqual(result.applicability.summary.pending, 9977)
            self.assertEqual(len(result.generated_axis_ids), 1)
            self.assertFalse(result.reconciliation.complete)


class ApplicabilityBindingTest(unittest.TestCase):
    def test_covered_rows_bind_unique_obligations_and_cases(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = ApplicabilityFixture(Path(tmp))
            applicability = fixture.make_complete()
            row, review = applicability.covered_rows()[0]
            axis = applicability_axis_id(row.statement_key)
            obligation = {
                "obligation_id": "obl-alpha",
                "test_point_id": "TP-SFV-TEST",
                "assignments": {axis: row.row_id},
                "outcome": "success",
                "execution_profile": "basic_psql",
                "execution_harness": None,
            }
            witness = review.matrix_witness
            self.assertIsNotNone(witness)
            case = {
                "case_id": "CASE-ALPHA",
                "obligation_id": "obl-alpha",
                "test_point_id": "TP-SFV-TEST",
                "outcome": "success",
                "execution_profile": "basic_psql",
                "execution_harness": None,
                "sql_sha256": "1" * 64,
                "metadata": {
                    "assignments": {axis: row.row_id},
                    "applicability_claim": {
                        "row_id": row.row_id,
                        "statement_key": row.statement_key,
                        "factor": row.factor,
                        "value": row.value,
                        "matrix_path": witness.path,
                        "matrix_sha256": witness.sha256,
                        "combination_group_id": witness.combination_group_id,
                    },
                },
            }
            planning = reconcile_applicability_bindings(
                applicability, [obligation]
            )
            self.assertTrue(planning.complete)
            self.assertFalse(planning.cases_checked)
            generated = reconcile_applicability_bindings(
                applicability,
                [obligation],
                cases=[case],
            )
            self.assertTrue(generated.complete)
            self.assertEqual(generated.matched_cases, 1)

            unrelated_obligation = {
                "obligation_id": "obl-other",
                "test_point_id": "TP-SFV-OTHER",
                "assignments": {"applicability_row__other": "sfv-other"},
                "outcome": "success",
                "execution_profile": "basic_psql",
                "execution_harness": None,
            }
            unrelated_case = {
                "case_id": "CASE-OTHER",
                "obligation_id": "obl-other",
                "test_point_id": "TP-SFV-OTHER",
                "outcome": "success",
                "execution_profile": "basic_psql",
                "execution_harness": None,
                "sql_sha256": "2" * 64,
                "metadata": {
                    "assignments": {"applicability_row__other": "sfv-other"},
                    "applicability_claim": {"row_id": "sfv-other"},
                },
            }
            scoped = reconcile_applicability_bindings(
                applicability,
                [obligation, unrelated_obligation],
                cases=[case, unrelated_case],
                test_point_id="TP-SFV-TEST",
            )
            self.assertTrue(scoped.complete)
            self.assertEqual(scoped.test_point_id, "TP-SFV-TEST")
            self.assertFalse(scoped.unexpected_obligation_ids)
            self.assertFalse(scoped.unexpected_case_ids)

            missing_case = reconcile_applicability_bindings(
                applicability,
                [obligation],
                cases=[],
            )
            self.assertFalse(missing_case.complete)
            self.assertEqual(
                missing_case.missing_case_obligation_ids,
                ("obl-alpha",),
            )

            wrong_obligation = dict(obligation)
            wrong_obligation["assignments"] = {axis: "sfv-wrong"}
            mismatch = reconcile_applicability_bindings(
                applicability,
                [wrong_obligation],
            )
            self.assertFalse(mismatch.complete)
            self.assertEqual(mismatch.mismatched_obligation_ids, ("obl-alpha",))

            wrong_route = dict(obligation)
            wrong_route["execution_profile"] = "external_isolated"
            wrong_route["execution_harness"] = "external-fixture"
            route_mismatch = reconcile_applicability_bindings(
                applicability,
                [wrong_route],
            )
            self.assertFalse(route_mismatch.complete)
            self.assertEqual(
                route_mismatch.mismatched_obligation_ids,
                ("obl-alpha",),
            )

            invalid_case_sha = dict(case)
            invalid_case_sha["sql_sha256"] = None
            invalid_case = reconcile_applicability_bindings(
                applicability,
                [obligation],
                cases=[invalid_case_sha],
            )
            self.assertFalse(invalid_case.complete)
            self.assertEqual(invalid_case.mismatched_case_ids, ("CASE-ALPHA",))

            wrong_case_route = dict(case)
            wrong_case_route["execution_profile"] = "external_isolated"
            wrong_case_route["execution_harness"] = "external-fixture"
            case_route_mismatch = reconcile_applicability_bindings(
                applicability,
                [obligation],
                cases=[wrong_case_route],
            )
            self.assertFalse(case_route_mismatch.complete)
            self.assertEqual(
                case_route_mismatch.mismatched_case_ids,
                ("CASE-ALPHA",),
            )

    def test_two_covered_rows_cannot_share_one_obligation(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = ApplicabilityFixture(Path(tmp))
            document = fixture.review_document()
            document["statement_decision"] = fixture.covered_scope_decision()
            factor = document["factors"][0]
            factor["factor_decision"] = fixture.covered_scope_decision()
            for value in factor["values"]:
                value["decision"] = fixture.covered_value_decision(
                    value["row_id"], "obl-shared"
                )
            fixture.save_review(document)
            with self.assertRaisesRegex(
                ApplicabilityValidationError, "must bind unique obligations"
            ):
                load_feature_applicability_index(
                    fixture.index_path,
                    repository_root=fixture.root,
                    known_requirement_ids={"REQ-001"},
                    require_complete=True,
                )

    def test_pending_parent_decision_prevents_reconciliation_completion(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = ApplicabilityFixture(Path(tmp))
            complete = fixture.make_complete()
            document = fixture.review_document()
            document["statement_decision"] = {"status": "pending"}
            fixture.save_review(document)
            partial = load_feature_applicability_index(
                fixture.index_path,
                repository_root=fixture.root,
                known_requirement_ids={"REQ-001"},
                require_complete=False,
            )
            row, _ = complete.covered_rows()[0]
            obligation = {
                "obligation_id": "obl-alpha",
                "test_point_id": "TP-SFV-TEST",
                "assignments": {applicability_axis_id(row.statement_key): row.row_id},
                "outcome": "success",
                "execution_profile": "basic_psql",
                "execution_harness": None,
            }
            report = reconcile_applicability_bindings(partial, [obligation])
            self.assertFalse(report.complete)
            self.assertEqual(report.pending_rows, 0)
            self.assertEqual(report.pending_statement_decisions, 1)


if __name__ == "__main__":
    unittest.main()
