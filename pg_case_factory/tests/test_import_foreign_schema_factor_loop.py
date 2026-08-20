"""Tests for import_foreign_schema factor_loop obligation ledger."""

import unittest
from pathlib import Path

from src.pg_case_factory.import_foreign_schema_factor_loop import (
    build_import_foreign_schema_factor_loop_plan,
    compile_import_foreign_schema_factor_loop_obligations,
)

_REPO = Path(__file__).resolve().parents[1]


class TestImportForeignSchemaFactorLoop(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_import_foreign_schema_factor_loop_plan(
            _REPO
        )

    def test_obligation_count(self) -> None:
        self.assertEqual(57, len(self.plan.obligations))

    def test_case_count(self) -> None:
        self.assertEqual(57, len(self.plan.cases))

    def test_delegated_count(self) -> None:
        self.assertEqual(0, len(self.plan.delegated))

    def test_kind_counts(self) -> None:
        from collections import Counter
        counts = Counter(o.kind for o in self.plan.obligations)
        self.assertEqual({"GRM": 1, "SFV": 56}, dict(counts))

    def test_frozen_multiset_sha256(self) -> None:
        self.assertEqual(
            "0d28e34b16b0bcc84eeee9dff8c54babfa9f8f55"
            "8196ea4fcb41baa0269ca0af",
            self.plan.obligation_multiset_sha256,
        )

    def test_deterministic(self) -> None:
        other = build_import_foreign_schema_factor_loop_plan(
            _REPO
        )
        self.assertEqual(
            self.plan.obligation_multiset_sha256,
            other.obligation_multiset_sha256,
        )

    def test_outcome_counts(self) -> None:
        from collections import Counter
        counts = Counter(c.outcome for c in self.plan.cases)
        self.assertEqual(
            {"success": 56, "expected_failure": 1},
            dict(counts),
        )

    def test_unique_case_ids(self) -> None:
        ids = [c.case_id for c in self.plan.cases]
        self.assertEqual(len(ids), len(set(ids)))

    def test_unique_filenames(self) -> None:
        names = [c.sql_filename for c in self.plan.cases]
        self.assertEqual(len(names), len(set(names)))

    def test_contiguous_ordinals(self) -> None:
        ordinals = [c.ordinal for c in self.plan.cases]
        self.assertEqual(list(range(1, 58)), ordinals)

    def test_object_prefix_format(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(
                case.object_prefix.startswith(
                    "importforeignschema_"
                )
            )
            self.assertTrue(case.object_prefix.endswith("_"))

    def test_case_id_format(self) -> None:
        for case in self.plan.cases:
            self.assertTrue(
                case.case_id.startswith("IMPORTFOREIGNSCHEMA")
            )

    def test_execution_profile(self) -> None:
        for case in self.plan.cases:
            self.assertEqual("serial_sql", case.execution_profile)

    def test_compile_obligations_matches_plan(self) -> None:
        obligations = (
            compile_import_foreign_schema_factor_loop_obligations(
                _REPO
            )
        )
        self.assertEqual(
            len(obligations), len(self.plan.obligations)
        )

    def test_factor_value_count_matches_catalog(self) -> None:
        # UNIVERSAL INVARIANT: catalog_rows == fvc == factor_value_count.
        from src.pg_case_factory.applicability import (
            load_shipped_applicability_universe,
        )
        catalog_rows = load_shipped_applicability_universe(
            _REPO
        ).rows_for_statement("import_foreign_schema")
        sfv_count = sum(
            1 for o in self.plan.obligations if o.kind == "SFV"
        )
        self.assertEqual(len(catalog_rows), sfv_count)
        self.assertEqual(56, sfv_count)


if __name__ == "__main__":
    unittest.main()
