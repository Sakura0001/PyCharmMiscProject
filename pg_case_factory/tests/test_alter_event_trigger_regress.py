from __future__ import annotations

import re
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from pg_case_factory.remaining_statement_regress import (
    build_statement_regress_plan,
    generate_statement_regress_package,
    render_statement_regress_case,
)
from pg_case_factory.statement_factor_cycle import discover_statement_factor_cycle


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class AlterEventTriggerRegressPlanTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.plan = build_statement_regress_plan(
            discover_statement_factor_cycle(REPOSITORY_ROOT), "alter_event_trigger"
        )

    def test_exact_conditional_products(self) -> None:
        self.assertEqual(159, len(self.plan.cases))
        self.assertEqual(
            {
                "state_transition_product": 96,
                "owner_target_product": 14,
                "rename_state_product": 12,
                "missing_trigger_product": 6,
                "privilege_truth_product": 12,
                "trigger_function_state_product": 1,
                "transactional_rollback_product": 6,
                "parser_boundary_product": 12,
            },
            Counter(case.case_group for case in self.plan.cases),
        )
        self.assertEqual(tuple(range(1, 160)), tuple(c.ordinal for c in self.plan.cases))
        self.assertEqual(159, len({c.case_id for c in self.plan.cases}))

    def test_all_56_values_have_unique_real_witnesses(self) -> None:
        self.assertEqual(56, len(self.plan.factor_decisions))
        cases = {case.case_id: case for case in self.plan.cases}
        for row in self.plan.factor_decisions:
            self.assertNotEqual("justified_na", row.disposition)
            self.assertTrue(row.case_ids, row.row_id)
            for case_id in row.case_ids:
                self.assertIn(f"{row.factor}={row.value}", cases[case_id].factor_values)
        for case in self.plan.cases:
            keys = [token.split("=", 1)[0] for token in case.factor_values]
            self.assertEqual(len(keys), len(set(keys)), case.case_id)

    def test_state_product_is_full_cartesian(self) -> None:
        rows = [c for c in self.plan.cases if c.case_group == "state_transition_product"]
        self.assertEqual(
            96,
            len({(
                c.derived_axes["branch"], c.derived_axes["current_state"],
                c.derived_axes["session_role"], c.derived_axes["trigger_name_shape"],
            ) for c in rows}),
        )


class AlterEventTriggerRegressRendererTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.plan = build_statement_regress_plan(
            discover_statement_factor_cycle(REPOSITORY_ROOT), "alter_event_trigger"
        )

    def test_every_case_has_one_phase_8_target_and_real_oracles(self) -> None:
        for case in self.plan.cases:
            sql = render_statement_regress_case(self.plan, case)
            primary = sql.split("-- 8. Primary target statement", 1)[1].split(
                "-- 9. SQLSTATE and primary-result oracle", 1
            )[0]
            self.assertEqual(1, len(re.findall(r"(?m)^ALTER\s+EVENT\s+TRIGGER\b", primary)))
            self.assertIn("expected_SQLSTATE", sql)
            self.assertIn("pg_catalog.pg_event_trigger", sql)
            self.assertIn("cleanup_complete", sql)
            self.assertNotIn("CREATE TABLE", sql)
            self.assertNotRegex(sql, r"\{[A-Za-z_][A-Za-z0-9_]*\}")
            self.assertTrue(sql.endswith("\n"))
            self.assertFalse(sql.endswith("\n\n"))

    def test_state_cases_execute_trigger_function_semantics(self) -> None:
        sql = "\n".join(render_statement_regress_case(self.plan, c) for c in self.plan.cases)
        self.assertIn("RETURNS event_trigger", sql)
        self.assertIn("session_replication_role", sql)
        self.assertIn("event_trigger_fired_matches", sql)
        self.assertIn("ENABLE REPLICA", sql)
        self.assertIn("ENABLE ALWAYS", sql)


class AlterEventTriggerRegressPublicationTest(unittest.TestCase):
    def test_generate_validate_and_regenerate_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            first = generate_statement_regress_package(
                REPOSITORY_ROOT, "alter_event_trigger",
                output_dir=root / "first", evidence_dir=root / "first-evidence",
            )
            second = generate_statement_regress_package(
                REPOSITORY_ROOT, "alter_event_trigger",
                output_dir=root / "second", evidence_dir=root / "second-evidence",
            )
            self.assertEqual(159, first.sql_file_count)
            self.assertEqual(first.sql_sha256, second.sql_sha256)
            for relative in first.sql_sha256:
                self.assertEqual((root / "first" / relative).read_bytes(), (root / "second" / relative).read_bytes())
            for relative in ("plan.json", "coverage.json", "package.json", "validation.json"):
                self.assertEqual((root / "first-evidence" / relative).read_bytes(), (root / "second-evidence" / relative).read_bytes())


if __name__ == "__main__":
    unittest.main()
