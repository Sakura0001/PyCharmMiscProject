from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from pg_case_factory.alter_policy_factor_extension import (
    AlterPolicyFactorExtensionCase,
    build_alter_policy_factor_extension_plan,
)
from pg_case_factory.alter_policy_factor_loop import (
    build_alter_policy_factor_loop_plan,
)
from pg_case_factory.alter_policy_factor_render import (
    AlterPolicyFactorRenderError,
    count_primary_alter_policy,
    generate_alter_policy_factor_programs,
    render_alter_policy_factor_case,
    resolve_alter_policy_factor_witness,
)


ROOT = Path(__file__).resolve().parents[1]

_BASELINE_COUNT = 72
_EXTENSION_COUNT = 13032
_TOTAL = _BASELINE_COUNT + _EXTENSION_COUNT


class AlterPolicyFactorRenderTest(unittest.TestCase):
    def test_every_case_resolves_a_concrete_witness(self) -> None:
        plan = build_alter_policy_factor_loop_plan(ROOT)
        self.assertEqual(_BASELINE_COUNT, len(plan.cases))
        for case in plan.cases:
            with self.subTest(case_id=case.case_id):
                witness = resolve_alter_policy_factor_witness(case, ROOT)
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
                # Every primary target (including the transaction-control
                # RISK cases, whose COMMIT/ROLLBACK lives in the assert
                # section rather than the primary fence) is an ALTER POLICY
                # statement.
                self.assertTrue(
                    witness.target_sql_fragment.startswith("ALTER POLICY"),
                    case.case_id,
                )
                self.assertTrue(witness.setup_sql)
                self.assertTrue(witness.oracle_sql)
                self.assertTrue(witness.cleanup_sql)
                self.assertTrue(witness.semantic_locus)

    def test_all_programs_are_complete_and_have_one_target(self) -> None:
        plan = build_alter_policy_factor_loop_plan(ROOT)
        for case in plan.cases:
            with self.subTest(case_id=case.case_id):
                sql = render_alter_policy_factor_case(case, ROOT)
                self.assertTrue(
                    sql.startswith("-- --------------------------------------------------------\n")
                )
                self.assertEqual(1, count_primary_alter_policy(sql))
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
        plan = build_alter_policy_factor_loop_plan(ROOT)
        first = [
            render_alter_policy_factor_case(row, ROOT) for row in plan.cases
        ]
        second = [
            render_alter_policy_factor_case(row, ROOT) for row in plan.cases
        ]
        self.assertEqual(first, second)
        self.assertEqual(_BASELINE_COUNT, len(first))

    def test_expected_failure_programs_capture_and_restore_error_mode(
        self,
    ) -> None:
        plan = build_alter_policy_factor_loop_plan(ROOT)
        failures = [
            row for row in plan.cases if row.outcome == "expected_failure"
        ]
        self.assertEqual(16, len(failures))
        for case in failures:
            with self.subTest(case_id=case.case_id):
                sql = render_alter_policy_factor_case(case, ROOT)
                self.assertIn("\\set ON_ERROR_STOP off", sql)
                self.assertIn("\\set target_sqlstate :SQLSTATE", sql)
                self.assertIn(
                    f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}'",
                    sql,
                )
                self.assertIn("\\set ON_ERROR_STOP on", sql)

    def test_success_programs_keep_error_stop_armed(self) -> None:
        plan = build_alter_policy_factor_loop_plan(ROOT)
        successes = [
            row for row in plan.cases if row.outcome == "success"
        ]
        self.assertEqual(56, len(successes))
        for case in successes:
            with self.subTest(case_id=case.case_id):
                sql = render_alter_policy_factor_case(case, ROOT)
                self.assertIn("\\set ON_ERROR_STOP on", sql)
                # success path never disarms error stop around the target
                self.assertNotIn("\\set ON_ERROR_STOP off", sql)

    def test_witness_fragments_are_present_in_rendered_bytes(self) -> None:
        plan = build_alter_policy_factor_loop_plan(ROOT)
        for case in plan.cases:
            with self.subTest(case_id=case.case_id):
                sql = render_alter_policy_factor_case(case, ROOT)
                witness = resolve_alter_policy_factor_witness(case, ROOT)
                for fragment in witness.setup_sql:
                    self.assertIn(fragment.rstrip(), sql)
                for fragment in witness.oracle_sql:
                    self.assertIn(fragment.rstrip(), sql)
                for fragment in witness.cleanup_sql:
                    self.assertIn(fragment.rstrip(), sql)
                self.assertIn(witness.target_sql_fragment.rstrip(), sql)

    def test_transaction_witnesses_have_distinct_commit_and_rollback(
        self,
    ) -> None:
        plan = build_alter_policy_factor_loop_plan(ROOT)
        rows = {
            row.factor_value: row for row in plan.cases if row.kind == "RISK"
        }
        self.assertEqual({"commit", "rollback"}, set(rows))
        commit_sql = render_alter_policy_factor_case(rows["commit"], ROOT)
        rollback_sql = render_alter_policy_factor_case(rows["rollback"], ROOT)
        self.assertIn("COMMIT;", commit_sql)
        self.assertIn("ROLLBACK;", rollback_sql)
        self.assertNotIn("ROLLBACK;", commit_sql)
        self.assertNotIn("COMMIT;", rollback_sql)

    def test_oracle_uses_polname_and_pg_policy_catalog(self) -> None:
        # Every catalog_query_pg_policy / rls_behavior_test baseline oracle
        # SELECT is a top-level
        # ``SELECT count(*) <op> 0 AS <alias> FROM pg_catalog.pg_policy
        # WHERE polname = '...' ORDER BY count(*) LIMIT 1``
        # never a ``SELECT EXISTS(SELECT 1 FROM ...)`` subquery, and it must
        # use the real pg_policy column name ``polname`` (NOT the plausible
        # but wrong ``policyname``).  Success cases probe presence
        # (``count(*) > 0 AS catalog_policy_present``); target-absent
        # expected_failure cases probe absence (``count(*) = 0 AS
        # catalog_policy_absent``).  The single error_assertion baseline
        # case carries only the sqlstate oracle (no count probe) and is
        # intentionally excluded from the count-regex assertion.
        plan = build_alter_policy_factor_loop_plan(ROOT)
        for case in plan.cases:
            with self.subTest(case_id=case.case_id):
                sql = render_alter_policy_factor_case(case, ROOT)
                self.assertNotIn("EXISTS (SELECT 1", sql)
                self.assertNotIn("EXISTS(SELECT 1", sql)
                # the latent bug was probing the wrong column name; guard it
                self.assertNotIn("policyname", sql)
                if (
                    dict(case.baseline_assignments).get("verification_mode")
                    == "error_assertion"
                ):
                    self.assertNotIn("ORDER BY count(*)", sql)
                    continue
                self.assertRegex(
                    sql,
                    r"SELECT count\(\*\) [=><]+ 0 AS \w+ "
                    r"FROM pg_catalog\.pg_policy WHERE polname",
                )
                self.assertIn("ORDER BY count(*)", sql)

    def test_primary_fence_is_unique_and_brackets_target(self) -> None:
        plan = build_alter_policy_factor_loop_plan(ROOT)
        for case in plan.cases:
            with self.subTest(case_id=case.case_id):
                sql = render_alter_policy_factor_case(case, ROOT)
                self.assertEqual(1, sql.count("-- primary-target-begin"))
                self.assertEqual(1, sql.count("-- primary-target-end"))
                self.assertEqual(1, count_primary_alter_policy(sql))


class AlterPolicyExtensionRenderTest(unittest.TestCase):
    """Extension cases render through a byte-safe synthetic baseline case."""

    def setUp(self) -> None:
        self.extension_plan = build_alter_policy_factor_extension_plan(ROOT)

    def _representative_subset(
        self,
    ) -> list[AlterPolicyFactorExtensionCase]:
        # One case per (branch, outcome) pair so every branch x outcome
        # combination is exercised without rendering all 13032 programs.
        # ALTER POLICY has two branches (branch_rename, branch_modify), so
        # this yields four cases.
        seen: set[tuple[str, str]] = set()
        subset: list[AlterPolicyFactorExtensionCase] = []
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
                sql = render_alter_policy_factor_case(case, ROOT)
                self.assertTrue(
                    sql.startswith("-- --------------------------------------------------------\n")
                )
                self.assertEqual(1, count_primary_alter_policy(sql))
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
                self.assertIn("-- description  : ALTER POLICY", sql)
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
                sql = render_alter_policy_factor_case(case, ROOT)
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
                sql = render_alter_policy_factor_case(case, ROOT)
                self.assertNotIn("\\set ON_ERROR_STOP off", sql)

    def test_extension_witness_fragments_present_in_rendered_bytes(self) -> None:
        for case in self._representative_subset():
            with self.subTest(case_id=case.case_id):
                sql = render_alter_policy_factor_case(case, ROOT)
                witness = resolve_alter_policy_factor_witness(case, ROOT)
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
        first = [
            render_alter_policy_factor_case(c, ROOT) for c in subset
        ]
        second = [
            render_alter_policy_factor_case(c, ROOT) for c in subset
        ]
        self.assertEqual(first, second)

    def test_generator_writes_baseline_and_extension_files(self) -> None:
        baseline_plan = build_alter_policy_factor_loop_plan(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "alter_policy"
            count = generate_alter_policy_factor_programs(
                baseline_plan, self.extension_plan, out
            )
            self.assertEqual(_TOTAL, count)
            files = sorted(out.glob("ALTERPOLICY*.sql"))
            self.assertEqual(_TOTAL, len(files))
            # baseline + extension numbering does not collide
            names = {f.name for f in files}
            self.assertEqual(_TOTAL, len(names))
            # spot-check first baseline + first extension files
            b0 = (
                out / baseline_plan.cases[0].sql_filename
            ).read_text(encoding="utf-8")
            self.assertEqual(1, count_primary_alter_policy(b0))
            e0 = (
                out / self.extension_plan.cases[0].sql_filename
            ).read_text(encoding="utf-8")
            self.assertEqual(1, count_primary_alter_policy(e0))


if __name__ == "__main__":
    unittest.main()
