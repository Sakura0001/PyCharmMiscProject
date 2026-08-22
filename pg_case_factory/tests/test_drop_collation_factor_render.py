from __future__ import annotations

from pathlib import Path
import re
import shutil
import tempfile
import unittest

from pg_case_factory.drop_collation_factor_extension import (
    DropCollationFactorExtensionCase,
    build_drop_collation_factor_extension_plan,
)
from pg_case_factory.drop_collation_factor_loop import (
    build_drop_collation_factor_loop_plan,
)
from pg_case_factory.drop_collation_factor_render import (
    count_primary_drop_collation,
    generate_drop_collation_factor_programs,
    render_drop_collation_factor_case,
    resolve_drop_collation_factor_witness,
)


ROOT = Path(__file__).resolve().parents[1]

_BASELINE_COUNT = 30
_EXTENSION_COUNT = 336
_TOTAL = _BASELINE_COUNT + _EXTENSION_COUNT


class DropCollationFactorRenderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = build_drop_collation_factor_loop_plan(ROOT)
        cls.extension = build_drop_collation_factor_extension_plan(ROOT)
        cls.tmp = Path(tempfile.mkdtemp(prefix="drop_collation_render_"))
        cls.count = generate_drop_collation_factor_programs(
            cls.baseline, cls.extension, cls.tmp
        )

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_cleanup_bookend_invariants(self) -> None:
        """Fix-A guard: DROP OWNED BY is unreachable in pre-cleanup (the
        granted_role fixture is created by setup, so on a fresh database the
        role does not exist at pre-cleanup time and DROP OWNED BY would crash
        under ON_ERROR_STOP=1 before the target statement).  In cleanup,
        DROP OWNED BY must precede DROP ROLE IF EXISTS."""
        files = sorted(self.tmp.glob("*.sql"))
        self.assertGreater(len(files), 0)
        pre_drop_owned: list[str] = []
        cleanup_order_bad: list[str] = []
        for f in files:
            text = f.read_text()
            if "cleanup-bookend: pre-cleanup-begin" not in text:
                continue
            pre = text.split("cleanup-bookend: pre-cleanup-begin", 1)[1]
            pre = pre.split("cleanup-bookend: pre-cleanup-end", 1)[0]
            if re.search(r"\bDROP\s+OWNED\s+BY\b", pre, re.IGNORECASE):
                pre_drop_owned.append(f.name)
            cln = text.split("cleanup-bookend: cleanup-begin", 1)[1]
            cln = cln.split("cleanup-bookend: cleanup-end", 1)[0]
            m_own = re.search(r"\bDROP\s+OWNED\s+BY\b", cln, re.IGNORECASE)
            m_role = re.search(r"\bDROP\s+ROLE\b", cln, re.IGNORECASE)
            if m_own and m_role and m_own.start() > m_role.start():
                cleanup_order_bad.append(f.name)
        self.assertEqual([], pre_drop_owned, "DROP OWNED BY leaked into pre-cleanup")
        self.assertEqual([], cleanup_order_bad, "DROP OWNED BY after DROP ROLE in cleanup")

    def test_every_case_resolves_a_concrete_witness(self) -> None:
        plan = build_drop_collation_factor_loop_plan(ROOT)
        self.assertEqual(_BASELINE_COUNT, len(plan.cases))
        for case in plan.cases:
            with self.subTest(case_id=case.case_id):
                witness = resolve_drop_collation_factor_witness(case, ROOT)
                self.assertEqual(
                    case.primary_obligation_id,
                    witness.primary_obligation_id,
                )
                self.assertEqual(case.outcome, witness.outcome)
                self.assertEqual(
                    case.expected_sqlstate, witness.expected_sqlstate
                )
                self.assertTrue(witness.target_sql_fragment.strip())
                # no unresolved template placeholders leak into the target
                self.assertNotRegex(
                    witness.target_sql_fragment, r"\{[A-Za-z_]\w*\}"
                )
                self.assertTrue(
                    witness.target_sql_fragment.startswith("DROP COLLATION")
                )
                self.assertTrue(witness.setup_sql)
                self.assertTrue(witness.oracle_sql)
                self.assertTrue(witness.cleanup_sql)
                self.assertTrue(witness.semantic_locus)

    def test_all_programs_are_complete_and_have_one_target(self) -> None:
        plan = build_drop_collation_factor_loop_plan(ROOT)
        for case in plan.cases:
            with self.subTest(case_id=case.case_id):
                sql = render_drop_collation_factor_case(case, ROOT)
                self.assertTrue(
                    sql.startswith("-- --------------------------------------------------------\n")
                )
                self.assertEqual(1, count_primary_drop_collation(sql))
                self.assertIn(
                    f"-- primary_obligation_id: {case.primary_obligation_id}",
                    sql,
                )
                self.assertIn(f"-- case_id: {case.case_id}", sql)
                self.assertIn(
                    f"-- expected_outcome: {case.outcome}", sql
                )
                self.assertIn(
                    f"-- expected_sqlstate: {case.expected_sqlstate}", sql
                )
                self.assertNotRegex(sql, r"\{[A-Za-z_]\w*\}")
                self.assertTrue(sql.endswith(";\n"))
                self.assertFalse(sql.endswith("\n\n"))

    def test_all_programs_are_deterministic_in_memory(self) -> None:
        plan = build_drop_collation_factor_loop_plan(ROOT)
        first = [
            render_drop_collation_factor_case(row, ROOT) for row in plan.cases
        ]
        second = [
            render_drop_collation_factor_case(row, ROOT) for row in plan.cases
        ]
        self.assertEqual(first, second)
        self.assertEqual(_BASELINE_COUNT, len(first))

    def test_expected_failure_programs_capture_and_restore_error_mode(self) -> None:
        plan = build_drop_collation_factor_loop_plan(ROOT)
        failures = [
            row for row in plan.cases if row.outcome == "expected_failure"
        ]
        self.assertEqual(8, len(failures))
        for case in failures:
            with self.subTest(case_id=case.case_id):
                sql = render_drop_collation_factor_case(case, ROOT)
                self.assertIn("\\set ON_ERROR_STOP off", sql)
                self.assertIn("\\set target_sqlstate :SQLSTATE", sql)
                self.assertIn(
                    f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}'",
                    sql,
                )
                self.assertIn("\\set ON_ERROR_STOP on", sql)

    def test_success_programs_keep_error_stop_armed(self) -> None:
        plan = build_drop_collation_factor_loop_plan(ROOT)
        successes = [row for row in plan.cases if row.outcome == "success"]
        self.assertEqual(22, len(successes))
        for case in successes:
            with self.subTest(case_id=case.case_id):
                sql = render_drop_collation_factor_case(case, ROOT)
                self.assertIn("\\set ON_ERROR_STOP on", sql)
                # success path never disarms error stop around the target
                self.assertNotIn("\\set ON_ERROR_STOP off", sql)

    def test_witness_fragments_are_present_in_rendered_bytes(self) -> None:
        plan = build_drop_collation_factor_loop_plan(ROOT)
        for case in plan.cases:
            with self.subTest(case_id=case.case_id):
                sql = render_drop_collation_factor_case(case, ROOT)
                witness = resolve_drop_collation_factor_witness(case, ROOT)
                for fragment in witness.setup_sql:
                    self.assertIn(fragment.rstrip(), sql)
                for fragment in witness.oracle_sql:
                    self.assertIn(fragment.rstrip(), sql)
                for fragment in witness.cleanup_sql:
                    self.assertIn(fragment.rstrip(), sql)
                self.assertIn(witness.target_sql_fragment.rstrip(), sql)

    def test_transaction_witnesses_have_distinct_commit_and_rollback(self) -> None:
        plan = build_drop_collation_factor_loop_plan(ROOT)
        rows = {
            row.factor_value: row
            for row in plan.cases
            if row.kind == "RISK"
        }
        self.assertEqual({"commit", "rollback"}, set(rows))
        commit_sql = render_drop_collation_factor_case(rows["commit"], ROOT)
        rollback_sql = render_drop_collation_factor_case(rows["rollback"], ROOT)
        self.assertIn("COMMIT;", commit_sql)
        self.assertIn("ROLLBACK;", rollback_sql)
        self.assertNotIn("ROLLBACK;", commit_sql)
        self.assertNotIn("COMMIT;", rollback_sql)

    def test_oracle_is_catalog_audit_compliant(self) -> None:
        # Every oracle SELECT must be a top-level
        # ``SELECT count(*) <op> AS alias FROM pg_catalog.pg_collation
        # WHERE... ORDER BY count(*)`` never a ``SELECT EXISTS(...)``
        # subquery.
        plan = build_drop_collation_factor_loop_plan(ROOT)
        for case in plan.cases:
            with self.subTest(case_id=case.case_id):
                sql = render_drop_collation_factor_case(case, ROOT)
                self.assertNotIn("EXISTS (SELECT 1", sql)
                self.assertNotIn("EXISTS(SELECT 1", sql)
                self.assertRegex(
                    sql,
                    r"SELECT count\(\*\) [=><]+ 0 AS \w+ "
                    r"FROM pg_catalog\.pg_collation",
                )
                # the boolean oracle always ends with ORDER BY count(*)
                self.assertIn("ORDER BY count(*)", sql)

    def test_primary_fence_is_unique_and_brackets_target(self) -> None:
        plan = build_drop_collation_factor_loop_plan(ROOT)
        for case in plan.cases:
            with self.subTest(case_id=case.case_id):
                sql = render_drop_collation_factor_case(case, ROOT)
                self.assertEqual(1, sql.count("-- primary-target-begin"))
                self.assertEqual(1, sql.count("-- primary-target-end"))
                self.assertEqual(1, count_primary_drop_collation(sql))


class DropCollationExtensionRenderTest(unittest.TestCase):
    """Extension cases render through a byte-safe synthetic baseline case."""

    def setUp(self) -> None:
        self.extension_plan = build_drop_collation_factor_extension_plan(ROOT)

    def _representative_subset(
        self,
    ) -> list[DropCollationFactorExtensionCase]:
        # One case per (branch, outcome) pair so every branch x outcome
        # combination is exercised without rendering all 336 programs.
        seen: set[tuple[str, str]] = set()
        subset: list[DropCollationFactorExtensionCase] = []
        for case in self.extension_plan.cases:
            a = dict(case.factor_assignment)
            key = (a["grammar_branch"], case.outcome)
            if key in seen:
                continue
            seen.add(key)
            subset.append(case)
        return subset

    def test_extension_cases_render_complete_5_phase_program(self) -> None:
        for case in self._representative_subset():
            with self.subTest(case_id=case.case_id):
                sql = render_drop_collation_factor_case(case, ROOT)
                self.assertTrue(
                    sql.startswith("-- --------------------------------------------------------\n")
                )
                self.assertEqual(1, count_primary_drop_collation(sql))
                self.assertIn("-- primary-target-begin", sql)
                self.assertIn("-- primary-target-end", sql)
                self.assertIn(f"-- case_id: {case.case_id}", sql)
                self.assertIn(
                    f"-- expected_outcome: {case.outcome}", sql
                )
                self.assertIn(
                    f"-- expected_sqlstate: {case.expected_sqlstate}", sql
                )
                # the synthetic primary is carried in the description header
                self.assertIn("-- description  : DROP COLLATION", sql)
                self.assertNotRegex(sql, r"\{[A-Za-z_]\w*\}")
                self.assertTrue(sql.endswith(";\n"))
                self.assertFalse(sql.endswith("\n\n"))

    def test_extension_failure_programs_disarm_error_stop_around_target(
        self,
    ) -> None:
        for case in self._representative_subset():
            if case.outcome != "expected_failure":
                continue
            with self.subTest(case_id=case.case_id):
                sql = render_drop_collation_factor_case(case, ROOT)
                self.assertIn("\\set ON_ERROR_STOP off", sql)
                self.assertIn("\\set target_sqlstate :SQLSTATE", sql)
                self.assertIn(
                    f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}'",
                    sql,
                )
                self.assertIn("\\set ON_ERROR_STOP on", sql)

    def test_extension_success_programs_keep_error_stop_armed(self) -> None:
        for case in self._representative_subset():
            if case.outcome != "success":
                continue
            with self.subTest(case_id=case.case_id):
                sql = render_drop_collation_factor_case(case, ROOT)
                self.assertNotIn("\\set ON_ERROR_STOP off", sql)

    def test_extension_witness_fragments_present_in_rendered_bytes(self) -> None:
        for case in self._representative_subset():
            with self.subTest(case_id=case.case_id):
                sql = render_drop_collation_factor_case(case, ROOT)
                witness = resolve_drop_collation_factor_witness(case, ROOT)
                self.assertEqual(
                    case.derivation_id, witness.primary_obligation_id
                )
                self.assertEqual(case.outcome, witness.outcome)
                self.assertEqual(
                    case.expected_sqlstate, witness.expected_sqlstate
                )
                for fragment in witness.setup_sql:
                    self.assertIn(fragment.rstrip(), sql)
                for fragment in witness.oracle_sql:
                    self.assertIn(fragment.rstrip(), sql)
                for fragment in witness.cleanup_sql:
                    self.assertIn(fragment.rstrip(), sql)
                self.assertIn(witness.target_sql_fragment.rstrip(), sql)

    def test_extension_renders_are_deterministic(self) -> None:
        subset = self._representative_subset()
        first = [render_drop_collation_factor_case(c, ROOT) for c in subset]
        second = [render_drop_collation_factor_case(c, ROOT) for c in subset]
        self.assertEqual(first, second)

    def test_generator_writes_baseline_and_extension_files(self) -> None:
        baseline_plan = build_drop_collation_factor_loop_plan(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "drop_collation"
            count = generate_drop_collation_factor_programs(
                baseline_plan, self.extension_plan, out
            )
            self.assertEqual(_TOTAL, count)
            files = sorted(out.glob("DROPCOLLATION*.sql"))
            self.assertEqual(_TOTAL, len(files))
            # baseline + extension numbering does not collide
            names = {f.name for f in files}
            self.assertEqual(_TOTAL, len(names))
            # spot-check first baseline + first extension files
            b0 = (out / baseline_plan.cases[0].sql_filename).read_text(
                encoding="utf-8"
            )
            self.assertEqual(1, count_primary_drop_collation(b0))
            e0 = (
                out / self.extension_plan.cases[0].sql_filename
            ).read_text(encoding="utf-8")
            self.assertEqual(1, count_primary_drop_collation(e0))


if __name__ == "__main__":
    unittest.main()
