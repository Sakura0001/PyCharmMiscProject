"""Tests for the unified ALTER GROUP factor renderer.

The renderer serves both the frozen 59-case baseline
(:class:`AlterGroupFactorCase`) and the bounded 3,564-case post-coverage
extension (:class:`AlterGroupFactorExtensionCase`) through a common
adapter.  These tests assert the byte-level 5-phase contract, primary
fence cardinality, ON_ERROR_STOP toggling, determinism, and
style-validator compliance -- not PostgreSQL semantics (calibrated later
on the isolated PG18.4 cluster by the runtime double-run).
"""

from __future__ import annotations

from pathlib import Path
import unittest

from pg_case_factory.alter_group_factor_extension import (
    build_alter_group_factor_extension_plan,
)
from pg_case_factory.alter_group_factor_loop import (
    AlterGroupFactorCase,
    build_alter_group_factor_loop_plan,
)
from pg_case_factory.alter_group_factor_render import (
    AlterGroupFactorRenderError,
    AlterGroupFactorWitness,
    AlterGroupRenderCase,
    count_primary_alter_group,
    generate_alter_group_factor_programs,
    render_alter_group_factor_case,
    resolve_alter_group_factor_witness,
)


ROOT = Path(__file__).resolve().parents[1]
_OUT = ROOT / "artifacts" / "regress" / "by-factor" / "ddl" / "group" / "alter_group"


class AlterGroupRenderCaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.baseline = build_alter_group_factor_loop_plan(ROOT)
        self.extension = build_alter_group_factor_extension_plan(ROOT)

    def _sample(self, index: int = 0) -> AlterGroupFactorCase:
        return self.baseline.cases[index]

    def test_adapter_normalises_both_case_types(self) -> None:
        rc = AlterGroupRenderCase.from_case(self._sample())
        self.assertEqual("ALTERGROUP0001", rc.case_id)
        self.assertFalse(rc.is_extension)
        self.assertEqual(23, len(rc.assignment))
        rc_ext = AlterGroupRenderCase.from_case(self.extension.cases[0])
        self.assertTrue(rc_ext.is_extension)
        self.assertEqual("ALTERGROUP0060", rc_ext.case_id)
        self.assertEqual(23, len(rc_ext.assignment))

    def test_render_produces_full_five_phase_byte_contract(self) -> None:
        case = self._sample()
        sql = render_alter_group_factor_case(case, ROOT)
        self.assertTrue(sql.startswith("-- ----"))
        self.assertIn("版权所有", sql)
        self.assertIn("-- author       : codex", sql)
        self.assertIn(f"-- case_id: {case.case_id}", sql)
        self.assertIn("-- source_md:", sql)
        self.assertIn("-- factor_md:", sql)
        self.assertIn("-- primary_obligation_id:", sql)
        self.assertIn(f"-- expected_outcome: {case.outcome}", sql)
        self.assertIn(f"-- expected_sqlstate: {case.expected_sqlstate}", sql)
        self.assertIn("-- 1. 清理本编号对象", sql)
        self.assertIn("\\set ON_ERROR_STOP on", sql)
        self.assertIn("-- 2. 创建完整本地角色和因子专用夹具。", sql)
        self.assertIn("-- primary-target-begin", sql)
        self.assertIn("-- primary-target-end", sql)
        self.assertIn("\\set target_sqlstate :SQLSTATE", sql)
        self.assertIn("\\echo PGCF_TARGET_SQLSTATE=:target_sqlstate", sql)
        self.assertIn("-- 4. 验证 SQLSTATE", sql)
        self.assertIn("-- 5. 清理全部本编号对象。", sql)
        self.assertTrue(sql.endswith(";\n"))

    def test_primary_fence_contains_exactly_one_alter_group(self) -> None:
        for case in self.baseline.cases[:6]:
            sql = render_alter_group_factor_case(case, ROOT)
            self.assertEqual(1, count_primary_alter_group(sql), case.case_id)
        for case in self.extension.cases[:6]:
            sql = render_alter_group_factor_case(case, ROOT)
            self.assertEqual(1, count_primary_alter_group(sql), case.case_id)

    def test_on_error_stop_toggling_for_expected_failure(self) -> None:
        failure = next(
            c for c in self.extension.cases if c.outcome == "expected_failure"
        )
        sql = render_alter_group_factor_case(failure, ROOT)
        # off before the target, on after
        off = [i for i, line in enumerate(sql.splitlines()) if "ON_ERROR_STOP off" in line]
        on_after = sql.split("-- primary-target-end", 1)[1]
        self.assertEqual(1, len(off))
        self.assertIn("\\set ON_ERROR_STOP on", on_after)

    def test_success_cases_do_not_toggle_off(self) -> None:
        success = next(
            c for c in self.extension.cases if c.outcome == "success"
        )
        sql = render_alter_group_factor_case(success, ROOT)
        self.assertNotIn("ON_ERROR_STOP off", sql)

    def test_no_placeholder_leakage(self) -> None:
        for case in list(self.baseline.cases[:3]) + list(self.extension.cases[:3]):
            sql = render_alter_group_factor_case(case, ROOT)
            self.assertNotIn("{", sql, case.case_id)
            self.assertNotIn("}", sql, case.case_id)
            self.assertNotIn("placeholder", sql.lower(), case.case_id)

    def test_render_is_deterministic(self) -> None:
        for case in list(self.baseline.cases[:3]) + list(self.extension.cases[:3]):
            self.assertEqual(
                render_alter_group_factor_case(case, ROOT),
                render_alter_group_factor_case(case, ROOT),
                case.case_id,
            )

    def test_witness_resolver_returns_complete_fragments(self) -> None:
        case = self._sample()
        witness = resolve_alter_group_factor_witness(case, ROOT)
        self.assertIsInstance(witness, AlterGroupFactorWitness)
        self.assertEqual(case.primary_obligation_id, witness.primary_obligation_id)
        self.assertTrue(witness.target_sql_fragment)
        self.assertTrue(witness.setup_sql)
        self.assertTrue(witness.oracle_sql)
        self.assertTrue(witness.cleanup_sql)
        self.assertIn("ALTER GROUP", witness.target_sql_fragment)

    def test_object_prefix_isolation_per_case(self) -> None:
        for case in self.baseline.cases[:3]:
            sql = render_alter_group_factor_case(case, ROOT)
            self.assertIn(case.object_prefix, sql)

    def test_target_statement_matches_consumer_action(self) -> None:
        for case in self.baseline.cases:
            witness = resolve_alter_group_factor_witness(case, ROOT)
            if case.consumer_action_id == "add_user":
                self.assertIn("ADD USER", witness.target_sql_fragment)
            elif case.consumer_action_id == "drop_user":
                self.assertIn("DROP USER", witness.target_sql_fragment)
            else:
                self.assertIn("RENAME TO", witness.target_sql_fragment)


class AlterGroupGenerateProgramsTest(unittest.TestCase):
    def test_generates_contiguous_files_for_baseline_and_extensions(self) -> None:
        baseline = build_alter_group_factor_loop_plan(ROOT)
        extension = build_alter_group_factor_extension_plan(ROOT)
        count = generate_alter_group_factor_programs(
            baseline, extension, _OUT
        )
        expected = len(baseline.cases) + len(extension.cases)
        self.assertEqual(expected, count)
        # contiguous 4-digit filenames ALTERGROUP0001..N
        names = sorted(p.name for p in _OUT.glob("ALTERGROUP*.sql"))
        self.assertEqual(expected, len(names))
        self.assertEqual("ALTERGROUP0001.sql", names[0])
        self.assertEqual(
            f"ALTERGROUP{expected:04d}.sql", names[-1]
        )

    def test_every_file_has_one_primary_alter_group(self) -> None:
        for path in list(_OUT.glob("ALTERGROUP*.sql"))[:20]:
            sql = path.read_text(encoding="utf-8")
            self.assertEqual(1, count_primary_alter_group(sql), path.name)


class AlterGroupCalibratedSemanticsTest(unittest.TestCase):
    """Renderer semantics pinned by the PG18.4 runtime double-run.

    These assertions encode the live-cluster calibration: the missing-group
    fixture must omit the group, a successful rename needs CREATEROLE (group
    admin alone yields 42501), and the membership/rename oracles must assert
    the *expected post-target* state rather than an unconditional EXISTS.
    """

    def setUp(self) -> None:
        self.baseline = build_alter_group_factor_loop_plan(ROOT)

    def _by_id(self, case_id: str) -> AlterGroupFactorCase:
        for case in self.baseline.cases:
            if case.case_id == case_id:
                return case
        raise AssertionError(f"missing baseline case {case_id}")

    def test_nonexistent_group_fixture_omits_the_group(self) -> None:
        sql = render_alter_group_factor_case(self._by_id("ALTERGROUP0031"), ROOT)
        # group must NOT be created -> target finds it missing -> 42704
        self.assertNotIn("CREATE ROLE altergroup_0031_grp;", sql)
        self.assertIn("ALTER GROUP altergroup_0031_grp ADD USER", sql)

    def test_nonexistent_user_fixture_omits_the_user(self) -> None:
        sql = render_alter_group_factor_case(self._by_id("ALTERGROUP0033"), ROOT)
        self.assertNotIn("CREATE ROLE altergroup_0033_usr;", sql)
        self.assertIn("ALTER GROUP altergroup_0033_grp ADD USER", sql)

    def test_rename_success_grants_createrole(self) -> None:
        sql = render_alter_group_factor_case(self._by_id("ALTERGROUP0003"), ROOT)
        # ALTER GROUP ... RENAME ~= ALTER ROLE ... RENAME needs CREATEROLE
        self.assertIn("ALTER ROLE altergroup_0003_admin CREATEROLE;", sql)

    def test_add_user_success_membership_oracle_asserts_present(self) -> None:
        sql = render_alter_group_factor_case(self._by_id("ALTERGROUP0001"), ROOT)
        self.assertIn("SELECT EXISTS(", sql)
        self.assertIn("AS membership_present;", sql)
        self.assertNotIn("membership_absent", sql)

    def test_drop_user_success_membership_oracle_asserts_absent(self) -> None:
        # ALTERGROUP0013 = drop_non_member_user=non_member -> success 00000
        sql = render_alter_group_factor_case(self._by_id("ALTERGROUP0013"), ROOT)
        self.assertIn("SELECT NOT EXISTS(", sql)
        self.assertIn("AS membership_absent;", sql)

    def test_rename_name_conflict_oracle_probes_source(self) -> None:
        # ALTERGROUP0025 = new_name_shape=duplicate_name -> 42710; the
        # source group survives the failed rename, so assert it exists.
        sql = render_alter_group_factor_case(self._by_id("ALTERGROUP0025"), ROOT)
        self.assertIn("AS rename_source_exists;", sql)
        self.assertIn("WHERE rolname = 'altergroup_0025_grp'", sql)


if __name__ == "__main__":
    unittest.main()
