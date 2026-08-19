"""Tests for the ALTER INDEX factor-loop regress program renderer.

Every planned case (marginal baseline or bounded extension) must render to one
self-contained, deterministic SQL file whose credited primary ALTER INDEX has
cardinality exactly one, whose five byte-contract sections are present, and
whose re-render is byte-identical (so the witness validator can never diverge
from the bytes actually written).
"""

from __future__ import annotations

import unittest
from pathlib import Path

from pg_case_factory.alter_index_factor_extension import (
    AlterIndexFactorExtensionCase,
    build_alter_index_factor_extension_plan,
)
from pg_case_factory.alter_index_factor_loop import (
    AlterIndexFactorCase,
    build_alter_index_factor_loop_plan,
)
from pg_case_factory.alter_index_factor_render import (
    AlterIndexFactorRenderError,
    count_primary_alter_index,
    render_alter_index_factor_case,
    resolve_alter_index_factor_witness,
)


ROOT = Path(__file__).resolve().parents[1]

_PRIMARY_BEGIN = "-- primary-target-begin"
_PRIMARY_END = "-- primary-target-end"


class AlterIndexFactorRenderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.baseline = build_alter_index_factor_loop_plan(ROOT)
        self.extension = build_alter_index_factor_extension_plan(ROOT)

    def _sample_per_action(self) -> list[object]:
        seen: set[str] = set()
        samples: list[object] = []
        for case in list(self.baseline.cases) + list(self.extension.cases):
            if case.consumer_action_id not in seen:
                seen.add(case.consumer_action_id)
                samples.append(case)
        return samples

    def test_baseline_case_renders_byte_stable(self) -> None:
        case = self.baseline.cases[0]
        first = render_alter_index_factor_case(case, ROOT)
        second = render_alter_index_factor_case(case, ROOT)
        self.assertEqual(first, second)

    def test_extension_case_renders_byte_stable(self) -> None:
        case = self.extension.cases[0]
        first = render_alter_index_factor_case(case, ROOT)
        second = render_alter_index_factor_case(case, ROOT)
        self.assertEqual(first, second)

    def test_each_action_has_exactly_one_credited_primary(self) -> None:
        for case in self._sample_per_action():
            sql = render_alter_index_factor_case(case, ROOT)
            self.assertEqual(
                1,
                count_primary_alter_index(sql),
                f"{case.case_id} ({case.consumer_action_id})",
            )

    def test_five_byte_contract_sections_present(self) -> None:
        for case in self._sample_per_action():
            sql = render_alter_index_factor_case(case, ROOT)
            self.assertIn("-- 1. 清理本编号对象", sql)
            self.assertIn("-- 2. 创建完整本地索引", sql)
            self.assertIn("-- 3. 执行唯一获得覆盖信用", sql)
            self.assertIn("-- 4. 验证 SQLSTATE", sql)
            self.assertIn("-- 5. 清理全部本编号对象", sql)
            self.assertEqual(1, sql.count(_PRIMARY_BEGIN))
            self.assertEqual(1, sql.count(_PRIMARY_END))

    def test_no_placeholder_leakage(self) -> None:
        for case in self._sample_per_action():
            sql = render_alter_index_factor_case(case, ROOT)
            self.assertNotIn("{", sql)
            self.assertNotIn("}", sql)

    def test_target_sqlstate_echo_present(self) -> None:
        for case in self._sample_per_action():
            sql = render_alter_index_factor_case(case, ROOT)
            self.assertIn("PGCF_TARGET_SQLSTATE=:target_sqlstate", sql)
            self.assertIn("target_sqlstate_matches_expected", sql)

    def test_header_carries_case_identity(self) -> None:
        case = self.extension.cases[0]
        sql = render_alter_index_factor_case(case, ROOT)
        self.assertIn(f"-- case_id: {case.case_id}", sql)
        self.assertIn(
            f"-- expected_outcome: {case.outcome}", sql
        )
        self.assertIn(
            f"-- expected_sqlstate: {case.expected_sqlstate}", sql
        )

    def test_witness_fragments_match_rendered_program(self) -> None:
        # The witness target fragment must be the bytes inside the primary
        # fence, so the validator's byte comparison is grounded.
        for case in self._sample_per_action():
            sql = render_alter_index_factor_case(case, ROOT)
            witness = resolve_alter_index_factor_witness(case, ROOT)
            region = sql.split(_PRIMARY_BEGIN, 1)[1].split(_PRIMARY_END, 1)[
                0
            ].strip()
            self.assertEqual(witness.target_sql_fragment, region)

    def test_renders_both_case_kinds_without_error(self) -> None:
        # Smoke-render a baseline failure, baseline success, and an extension
        # success to prove both case kinds route through the renderer.
        baseline_fail = next(
            c for c in self.baseline.cases if c.outcome == "expected_failure"
        )
        baseline_ok = next(
            c for c in self.baseline.cases if c.outcome == "success"
        )
        ext_ok = self.extension.cases[0]
        self.assertIsInstance(baseline_fail, AlterIndexFactorCase)
        self.assertIsInstance(ext_ok, AlterIndexFactorExtensionCase)
        for case in (baseline_fail, baseline_ok, ext_ok):
            sql = render_alter_index_factor_case(case, ROOT)
            self.assertTrue(sql.strip())

    def test_unknown_action_raises(self) -> None:
        bad = AlterIndexFactorCase(
            ordinal=99999,
            case_id="ALTERINDEX99999",
            sql_filename="ALTERINDEX99999.sql",
            object_prefix="alterindex_99999_",
            primary_obligation_id="AI-GRM|bad|bogus_action|statement_branch|bogus_action",
            kind="GRM",
            factor_key="statement_branch",
            factor_value="bogus_action",
            consumer_action_id="bogus_action",
            outcome="success",
            expected_sqlstate="00000",
            expected_failure_reason=None,
            baseline_assignments=(
                ("object_state", "exists"),
                ("statement_branch", "bogus_action"),
            ),
            execution_profile="same_session_multiphase",
        )
        with self.assertRaises(AlterIndexFactorRenderError):
            render_alter_index_factor_case(bad, ROOT)


if __name__ == "__main__":
    unittest.main()
