"""Byte-contract render tests for ALTER OPERATOR factor-loop SQL."""

from __future__ import annotations

import unittest
from pathlib import Path

from pg_case_factory.alter_operator_factor_extension import (
    build_alter_operator_factor_extension_plan,
)
from pg_case_factory.alter_operator_factor_loop import (
    build_alter_operator_factor_loop_plan,
)
from pg_case_factory.alter_operator_factor_render import (
    AlterOperatorFactorRenderError,
    count_primary_alter_operator,
    generate_alter_operator_factor_programs,
    render_alter_operator_factor_case,
    resolve_alter_operator_factor_witness,
)

ROOT = Path(__file__).resolve().parents[1]

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"


class AlterOperatorFactorRenderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.baseline = build_alter_operator_factor_loop_plan(ROOT)
        self.extension = build_alter_operator_factor_extension_plan(ROOT)

    def _render(self, case) -> str:
        return render_alter_operator_factor_case(case)

    def test_baseline_case_has_single_primary_target(self) -> None:
        sql = self._render(self.baseline.cases[0])
        self.assertEqual(count_primary_alter_operator(sql), 1)

    def test_extension_failure_case_renders(self) -> None:
        fail_case = next(
            c for c in self.extension.cases if c.outcome == "expected_failure"
        )
        sql = self._render(fail_case)
        self.assertEqual(count_primary_alter_operator(sql), 1)

    def test_no_placeholder_leakage(self) -> None:
        for case in self.baseline.cases[:8]:
            sql = self._render(case)
            self.assertNotIn("{", sql)
            self.assertNotIn("}", sql)

    def test_five_section_structure(self) -> None:
        sql = self._render(self.baseline.cases[0])
        self.assertIn("-- 1. 预清理本编号对象。", sql)
        self.assertIn("\\set ON_ERROR_STOP on", sql)
        self.assertIn("-- 2. 构造本编号对象与角色。", sql)
        self.assertIn(_PRIMARY_BEGIN, sql)
        self.assertIn(_PRIMARY_END, sql)
        self.assertIn("\\set target_sqlstate :SQLSTATE", sql)
        self.assertIn("\\echo PGCF_TARGET_SQLSTATE=", sql)
        self.assertIn("-- 4. 断言与目录审计。", sql)
        self.assertIn("-- 5. 清理全部本编号对象。", sql)

    def test_sqlstate_oracle_present(self) -> None:
        sql = self._render(self.baseline.cases[0])
        self.assertIn(
            "AS target_sqlstate_matches_expected;",
            sql,
        )

    def test_header_fields_present(self) -> None:
        sql = self._render(self.baseline.cases[0])
        self.assertIn("-- case_id: ALTEROPERATOR00001", sql)
        self.assertIn("-- primary_obligation_id:", sql)
        self.assertIn("-- expected_outcome:", sql)
        self.assertIn("-- expected_sqlstate:", sql)

    def test_witness_loci_nonempty(self) -> None:
        case = self.baseline.cases[0]
        witness = resolve_alter_operator_factor_witness(case)
        self.assertTrue(witness.setup_sql)
        self.assertTrue(witness.oracle_sql)
        self.assertTrue(witness.cleanup_sql)
        self.assertTrue(witness.semantic_locus)

    def test_deterministic_render(self) -> None:
        sql_a = self._render(self.baseline.cases[0])
        sql_b = self._render(self.baseline.cases[0])
        self.assertEqual(sql_a, sql_b)

    def test_generate_programs_to_disk(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            count = generate_alter_operator_factor_programs(
                self.baseline, self.extension, Path(td)
            )
            self.assertEqual(count, 63 + 2292)

    def test_escape_sqlstate_rejects_invalid(self) -> None:
        with self.assertRaises(AlterOperatorFactorRenderError):
            from pg_case_factory.alter_operator_factor_render import (
                _escape_sqlstate,
            )

            _escape_sqlstate("bad")


if __name__ == "__main__":
    unittest.main()
