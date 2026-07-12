from __future__ import annotations

import importlib.util
import sys
import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml


SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "audit_pg18_factor_compatibility.py"


def load_audit_module():
    spec = importlib.util.spec_from_file_location("audit_pg18_factor_compatibility", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_sgml(path: Path, ref_id: str, synopsis: str, body: str = "Stable behavior.") -> None:
    path.write_text(
        textwrap.dedent(
            f"""
            <refentry id="{ref_id}">
              <refnamediv><refname>CREATE WIDGET</refname></refnamediv>
              <refsynopsisdiv><synopsis>{synopsis}</synopsis></refsynopsisdiv>
              <refsect1><title>Description</title><para>{body}</para></refsect1>
            </refentry>
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )


def write_statement(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        textwrap.dedent(
            """
            # CREATE WIDGET

            ```yaml
            structured_config:
              kind: statement
              skill_name: create_widget
              official_source: https://www.postgresql.org/docs/18/sql-createwidget.html
              statement:
                key: create_widget
                name: CREATE WIDGET
              factor_layers:
                - tier: T1
                  factors: [mode]
              factors:
                mode:
                  label: mode
                  values:
                    - key: basic
                    - key: fast
              defaults:
                mode: basic
            ```
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )


def write_matrix(path: Path, test_points: list[str | dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    point_documents = []
    for item in test_points:
        overrides = {} if isinstance(item, str) else dict(item)
        point_id = item if isinstance(item, str) else str(overrides.pop("id"))
        omit_affected_values = bool(overrides.pop("omit_affected_values", False))
        point = {
            "id": point_id,
            "affected_factors": ["mode"],
            "sql": "CREATE WIDGET FAST;",
            "oracle": "reference_parity",
        }
        if not omit_affected_values:
            point["affected_values"] = {"mode": ["fast"]}
        point.update(overrides)
        point_documents.append(point)
    path.write_text(
        yaml.safe_dump(
            {
                "statement": {"key": "create_widget"},
                "pg18_compatibility": {
                    "target_version": "18.4",
                    "test_points": point_documents,
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def write_profile(path: Path, reviews: dict | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "kind": "postgresql_compatibility_profile",
                "baseline": {
                    "version": "16.4",
                    "docs_base": "https://www.postgresql.org/docs/16/",
                },
                "target": {
                    "version": "18.4",
                    "server_version_num": 180004,
                    "docs_base": "https://www.postgresql.org/docs/18/",
                },
                "policy": {"observable_compatibility": "strict"},
                "sgml_ref_aliases": {},
                "statement_reviews": reviews or {},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


class Pg18FactorCompatibilityAuditTest(unittest.TestCase):
    def make_fixture(self, synopsis_18: str, reviews: dict | None = None, test_points: list[str] | None = None):
        temp = TemporaryDirectory()
        root = Path(temp.name)
        statement = root / "skills/pg-sql-generation/references/statements/ddl/widget/create_widget.md"
        matrix = root / "skills/pg-sql-generation/references/combinations/ddl/widget/create_widget.yaml"
        profile = root / "skills/pg-sql-generation/references/common/compatibility_profile.yaml"
        sgml16 = root / "sgml16"
        sgml18 = root / "sgml18"
        sgml16.mkdir()
        sgml18.mkdir()
        write_statement(statement)
        write_matrix(matrix, test_points or [])
        write_profile(profile, reviews)
        write_sgml(sgml16 / "create_widget.sgml", "sql-createwidget", "CREATE WIDGET [ FAST ]")
        write_sgml(sgml18 / "create_widget.sgml", "sql-createwidget", synopsis_18)
        return temp, root, profile, sgml16, sgml18

    def test_unchanged_official_document_inherits_all_factor_values(self) -> None:
        audit = load_audit_module()
        temp, root, profile, sgml16, sgml18 = self.make_fixture("CREATE WIDGET [ FAST ]")
        with temp:
            result = audit.audit_repository(root, profile, sgml16, sgml18)

            self.assertTrue(result.passed, result.errors)
            self.assertEqual(result.statement_count, 1)
            self.assertEqual(result.factor_count, 1)
            self.assertEqual(result.value_count, 2)
            self.assertEqual(result.records[0].support_status, "static_reviewed")
            self.assertEqual(
                "https://www.postgresql.org/docs/16/sql-createwidget.html",
                result.records[0].official_source_baseline,
            )
            self.assertEqual(
                "https://www.postgresql.org/docs/18/sql-createwidget.html",
                result.records[0].official_source_target,
            )
            self.assertTrue(
                all(row.catalog_readiness == "static_ready" for row in result.ledger_rows)
            )

    def test_changed_synopsis_requires_review_and_matrix_test_point(self) -> None:
        audit = load_audit_module()
        reviews = {
            "create_widget": {
                "status": "synopsis_adapted",
                "reviewed_against": "18.4",
                "note": "FASTEST is new in PostgreSQL 18.",
                "affected_factors": {"mode": ["fast"]},
                "required_test_points": ["PG18-CREATE-WIDGET-FASTEST"],
            }
        }
        temp, root, profile, sgml16, sgml18 = self.make_fixture(
            "CREATE WIDGET [ FAST | FASTEST ]", reviews=reviews, test_points=[]
        )
        with temp:
            result = audit.audit_repository(root, profile, sgml16, sgml18)

            self.assertFalse(result.passed)
            self.assertTrue(any("missing PG18 test point" in item for item in result.errors))
            self.assertEqual(result.records[0].support_status, "pending_review")

    def test_changed_synopsis_with_reviewed_test_point_is_ready(self) -> None:
        audit = load_audit_module()
        reviews = {
            "create_widget": {
                "status": "synopsis_adapted",
                "reviewed_against": "18.4",
                "note": "FASTEST is new in PostgreSQL 18.",
                "affected_factors": {"mode": ["fast"]},
                "required_test_points": ["PG18-CREATE-WIDGET-FASTEST"],
            }
        }
        temp, root, profile, sgml16, sgml18 = self.make_fixture(
            "CREATE WIDGET [ FAST | FASTEST ]",
            reviews=reviews,
            test_points=["PG18-CREATE-WIDGET-FASTEST"],
        )
        with temp:
            result = audit.audit_repository(root, profile, sgml16, sgml18)

            self.assertTrue(result.passed, result.errors)
            self.assertEqual(result.changed_synopsis_count, 1)
            self.assertEqual(result.records[0].support_status, "synopsis_adapted")
            self.assertEqual(
                result.records[0].test_point_affected_values,
                {"PG18-CREATE-WIDGET-FASTEST": {"mode": ["fast"]}},
            )
            fast_row = next(row for row in result.ledger_rows if row.value == "fast")
            self.assertEqual(fast_row.factor_disposition, "adapted")
            self.assertEqual(
                fast_row.required_test_points,
                "PG18-CREATE-WIDGET-FASTEST",
            )
            basic_row = next(row for row in result.ledger_rows if row.value == "basic")
            self.assertEqual(basic_row.required_test_points, "")

    def test_changed_body_without_review_stays_pending_not_ready(self) -> None:
        audit = load_audit_module()
        temp, root, profile, sgml16, sgml18 = self.make_fixture("CREATE WIDGET [ FAST ]")
        with temp:
            write_sgml(sgml18 / "create_widget.sgml", "sql-createwidget", "CREATE WIDGET [ FAST ]", "Changed behavior.")
            result = audit.audit_repository(root, profile, sgml16, sgml18)

            self.assertFalse(result.passed)
            self.assertEqual(result.records[0].support_status, "pending_semantic_review")
            self.assertTrue(
                all(
                    row.catalog_readiness == "pending_static_review"
                    for row in result.ledger_rows
                )
            )

    def test_affected_factor_cannot_be_ready_without_a_reference_parity_point(self) -> None:
        audit = load_audit_module()
        reviews = {
            "create_widget": {
                "status": "semantic_reviewed",
                "reviewed_against": "18.4",
                "note": "The changed prose affects FAST mode.",
                "affected_factors": {"mode": ["fast"]},
                "required_test_points": [],
            }
        }
        temp, root, profile, sgml16, sgml18 = self.make_fixture(
            "CREATE WIDGET [ FAST ]",
            reviews=reviews,
        )
        with temp:
            write_sgml(
                sgml18 / "create_widget.sgml",
                "sql-createwidget",
                "CREATE WIDGET [ FAST ]",
                "Changed FAST behavior.",
            )
            result = audit.audit_repository(root, profile, sgml16, sgml18)

            self.assertFalse(result.passed)
            self.assertTrue(
                any("require at least one PG18" in error for error in result.errors),
                result.errors,
            )
            self.assertFalse(result.records[0].static_catalog_ready)

    def test_required_point_must_declare_affected_values(self) -> None:
        audit = load_audit_module()
        point_id = "PG18-CREATE-WIDGET-FASTEST"
        reviews = {
            "create_widget": {
                "status": "synopsis_adapted",
                "reviewed_against": "18.4",
                "note": "FASTEST is new in PostgreSQL 18.",
                "affected_factors": {"mode": ["fast"]},
                "required_test_points": [point_id],
            }
        }
        temp, root, profile, sgml16, sgml18 = self.make_fixture(
            "CREATE WIDGET [ FAST | FASTEST ]",
            reviews=reviews,
            test_points=[{"id": point_id, "omit_affected_values": True}],
        )
        with temp:
            result = audit.audit_repository(root, profile, sgml16, sgml18)

            self.assertFalse(result.passed)
            self.assertTrue(
                any("must declare a non-empty affected_values mapping" in error for error in result.errors),
                result.errors,
            )

    def test_unknown_affected_value_fails_closed(self) -> None:
        audit = load_audit_module()
        point_id = "PG18-CREATE-WIDGET-FASTEST"
        reviews = {
            "create_widget": {
                "status": "synopsis_adapted",
                "reviewed_against": "18.4",
                "note": "FASTEST is new in PostgreSQL 18.",
                "affected_factors": {"mode": ["fast"]},
                "required_test_points": [point_id],
            }
        }
        temp, root, profile, sgml16, sgml18 = self.make_fixture(
            "CREATE WIDGET [ FAST | FASTEST ]",
            reviews=reviews,
            test_points=[{"id": point_id, "affected_values": {"mode": ["fastest"]}}],
        )
        with temp:
            result = audit.audit_repository(root, profile, sgml16, sgml18)

            self.assertFalse(result.passed)
            self.assertTrue(
                any("references unknown affected values: mode=fastest" in error for error in result.errors),
                result.errors,
            )

    def test_unknown_affected_factor_fails_closed(self) -> None:
        audit = load_audit_module()
        point_id = "PG18-CREATE-WIDGET-FASTEST"
        reviews = {
            "create_widget": {
                "status": "synopsis_adapted",
                "reviewed_against": "18.4",
                "note": "FASTEST is new in PostgreSQL 18.",
                "affected_factors": {"mode": ["fast"]},
                "required_test_points": [point_id],
            }
        }
        temp, root, profile, sgml16, sgml18 = self.make_fixture(
            "CREATE WIDGET [ FAST | FASTEST ]",
            reviews=reviews,
            test_points=[
                {
                    "id": point_id,
                    "affected_factors": ["unknown_mode"],
                    "affected_values": {"unknown_mode": ["fast"]},
                }
            ],
        )
        with temp:
            result = audit.audit_repository(root, profile, sgml16, sgml18)

            self.assertFalse(result.passed)
            self.assertTrue(
                any("affected_values references unknown factor: unknown_mode" in error for error in result.errors),
                result.errors,
            )

    def test_required_point_union_must_cover_each_reviewed_value(self) -> None:
        audit = load_audit_module()
        point_id = "PG18-CREATE-WIDGET-FASTEST"
        reviews = {
            "create_widget": {
                "status": "synopsis_adapted",
                "reviewed_against": "18.4",
                "note": "Both modes are affected in PostgreSQL 18.",
                "affected_factors": {"mode": ["basic", "fast"]},
                "required_test_points": [point_id],
            }
        }
        temp, root, profile, sgml16, sgml18 = self.make_fixture(
            "CREATE WIDGET [ FAST | FASTEST ]",
            reviews=reviews,
            test_points=[point_id],
        )
        with temp:
            result = audit.audit_repository(root, profile, sgml16, sgml18)

            self.assertFalse(result.passed)
            self.assertTrue(
                any("mode=basic" in error and "no PG18 test point coverage" in error for error in result.errors),
                result.errors,
            )

    def test_required_point_union_can_split_values_across_points(self) -> None:
        audit = load_audit_module()
        basic_point = "PG18-CREATE-WIDGET-BASIC"
        fast_point = "PG18-CREATE-WIDGET-FAST"
        reviews = {
            "create_widget": {
                "status": "synopsis_adapted",
                "reviewed_against": "18.4",
                "note": "Both modes are covered separately.",
                "affected_factors": {"mode": ["basic", "fast"]},
                "required_test_points": [basic_point, fast_point],
            }
        }
        temp, root, profile, sgml16, sgml18 = self.make_fixture(
            "CREATE WIDGET [ FAST | FASTEST ]",
            reviews=reviews,
            test_points=[
                {
                    "id": basic_point,
                    "affected_values": {"mode": ["basic"]},
                    "sql": "CREATE WIDGET;",
                },
                {"id": fast_point, "affected_values": {"mode": ["fast"]}},
            ],
        )
        with temp:
            result = audit.audit_repository(root, profile, sgml16, sgml18)

            self.assertTrue(result.passed, result.errors)
            points_by_value = {
                row.value: row.required_test_points for row in result.ledger_rows
            }
            self.assertEqual(points_by_value["basic"], basic_point)
            self.assertEqual(points_by_value["fast"], fast_point)

    def test_empty_test_point_affected_value_list_fails_closed(self) -> None:
        audit = load_audit_module()
        point_id = "PG18-CREATE-WIDGET-ALL-MODES"
        reviews = {
            "create_widget": {
                "status": "synopsis_adapted",
                "reviewed_against": "18.4",
                "note": "The point executes both declared modes.",
                "affected_factors": {"mode": []},
                "required_test_points": [point_id],
            }
        }
        temp, root, profile, sgml16, sgml18 = self.make_fixture(
            "CREATE WIDGET [ FAST | FASTEST ]",
            reviews=reviews,
            test_points=[
                {
                    "id": point_id,
                    "affected_values": {"mode": []},
                    "sql": "CREATE WIDGET; CREATE WIDGET FAST;",
                }
            ],
        )
        with temp:
            result = audit.audit_repository(root, profile, sgml16, sgml18)

            self.assertFalse(result.passed)
            self.assertTrue(
                any("must be a non-empty explicit value list" in error for error in result.errors),
                result.errors,
            )

    def test_empty_review_list_means_all_values_but_points_still_list_each_value(self) -> None:
        audit = load_audit_module()
        basic_point = "PG18-CREATE-WIDGET-BASIC"
        fast_point = "PG18-CREATE-WIDGET-FAST"
        reviews = {
            "create_widget": {
                "status": "synopsis_adapted",
                "reviewed_against": "18.4",
                "note": "The review marks every declared mode affected.",
                "affected_factors": {"mode": []},
                "required_test_points": [basic_point, fast_point],
            }
        }
        temp, root, profile, sgml16, sgml18 = self.make_fixture(
            "CREATE WIDGET [ FAST | FASTEST ]",
            reviews=reviews,
            test_points=[
                {
                    "id": basic_point,
                    "affected_values": {"mode": ["basic"]},
                    "sql": "CREATE WIDGET;",
                },
                {"id": fast_point, "affected_values": {"mode": ["fast"]}},
            ],
        )
        with temp:
            result = audit.audit_repository(root, profile, sgml16, sgml18)

            self.assertTrue(result.passed, result.errors)

    def test_affected_factors_must_match_affected_value_keys(self) -> None:
        audit = load_audit_module()
        point_id = "PG18-CREATE-WIDGET-FASTEST"
        reviews = {
            "create_widget": {
                "status": "synopsis_adapted",
                "reviewed_against": "18.4",
                "note": "FASTEST is new in PostgreSQL 18.",
                "affected_factors": {"mode": ["fast"]},
                "required_test_points": [point_id],
            }
        }
        temp, root, profile, sgml16, sgml18 = self.make_fixture(
            "CREATE WIDGET [ FAST | FASTEST ]",
            reviews=reviews,
            test_points=[
                {
                    "id": point_id,
                    "affected_factors": [],
                    "affected_values": {"mode": ["fast"]},
                }
            ],
        )
        with temp:
            result = audit.audit_repository(root, profile, sgml16, sgml18)

            self.assertFalse(result.passed)
            self.assertTrue(
                any("affected_factors must exactly match affected_values keys" in error for error in result.errors),
                result.errors,
            )

    def test_generated_inventory_and_ledger_are_deterministic(self) -> None:
        audit = load_audit_module()
        temp, root, profile, sgml16, sgml18 = self.make_fixture("CREATE WIDGET [ FAST ]")
        with temp:
            result = audit.audit_repository(root, profile, sgml16, sgml18)
            inventory = audit.render_support_inventory(result, profile)
            ledger = audit.render_factor_ledger(result)

            self.assertEqual(inventory, audit.render_support_inventory(result, profile))
            self.assertEqual(ledger, audit.render_factor_ledger(result))
            parsed = yaml.safe_load(inventory)
            self.assertEqual(parsed["statements"][0]["factor_value_rows"], 2)
            self.assertEqual(parsed["statements"][0]["test_point_affected_values"], {})
            self.assertIn("statement_key\tsource_reference\tfactor\ttier\tvalue", ledger)

    def test_declared_sgml_provenance_rejects_a_different_source_tree(self) -> None:
        audit = load_audit_module()
        temp, root, profile, sgml16, sgml18 = self.make_fixture("CREATE WIDGET [ FAST ]")
        with temp:
            document = yaml.safe_load(profile.read_text(encoding="utf-8"))
            document["target"]["sgml_ref_file_count"] = 999
            document["target"]["sgml_ref_tree_sha256"] = "0" * 64
            profile.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "file count mismatch"):
                audit.audit_repository(root, profile, sgml16, sgml18)

    def test_committed_pg18_inventory_has_no_unreviewed_factor_values(self) -> None:
        root = SCRIPT.parents[1]
        inventory_path = (
            root
            / "skills"
            / "pg-sql-generation"
            / "references"
            / "common"
            / "statement_support_inventory.yaml"
        )
        ledger_path = (
            root
            / "skills"
            / "pg-sql-generation"
            / "references"
            / "common"
            / "postgresql_18_4_factor_audit.tsv"
        )

        inventory = yaml.safe_load(inventory_path.read_text(encoding="utf-8"))
        summary = inventory["summary"]
        self.assertEqual(summary["statements"], 183)
        self.assertEqual(summary["static_catalog_ready"], 183)
        self.assertEqual(summary["pending_static_review"], 0)
        self.assertEqual(summary["runtime_verified_statements"], 0)
        self.assertEqual(summary["statement_factor_pairs"], 3357)
        self.assertEqual(summary["statement_factor_value_rows"], 9978)

        ledger_lines = ledger_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(ledger_lines) - 1, summary["statement_factor_value_rows"])
        header = ledger_lines[0].split("\t")
        readiness_index = header.index("catalog_readiness")
        disposition_index = header.index("factor_disposition")
        point_index = header.index("required_test_points")
        for line in ledger_lines[1:]:
            columns = line.split("\t")
            self.assertEqual(columns[readiness_index], "static_ready")
            self.assertNotIn("pending", columns[disposition_index])
            if columns[disposition_index] == "adapted":
                self.assertTrue(columns[point_index])
            else:
                self.assertEqual(columns[point_index], "")


if __name__ == "__main__":
    unittest.main()
