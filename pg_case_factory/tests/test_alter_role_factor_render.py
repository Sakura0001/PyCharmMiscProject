from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from pg_case_factory.alter_role_factor_extension import (
    AlterRoleFactorExtensionCase,
    build_alter_role_factor_extension_plan,
)
from pg_case_factory.alter_role_factor_loop import (
    build_alter_role_factor_loop_plan,
)
from pg_case_factory.alter_role_factor_render import (
    AlterRoleFactorRenderError,
    count_primary_alter_role,
    generate_alter_role_factor_programs,
    render_alter_role_factor_case,
    resolve_alter_role_factor_witness,
)


ROOT = Path(__file__).resolve().parents[1]

_BASELINE_COUNT = 108
_EXTENSION_COUNT = 1635
_TOTAL = _BASELINE_COUNT + _EXTENSION_COUNT  # 1743

# The four frozen BEHAVIOR assertions (SUCCESS paths with state-checking
# oracles), frozen as an explicit set.
_FROZEN_BEHAVIOR_ASSERTIONS = frozenset(
    {
        ("rename_clears_password", "md5_password_cleared_on_rename"),
        ("rename_clears_password", "scram_password_preserved_on_rename"),
        ("password_security", "password_null_removes_password"),
        ("password_security", "plaintext_password_in_sql"),
    }
)


class AlterRoleFactorRenderTest(unittest.TestCase):
    def test_every_case_resolves_a_concrete_witness(self) -> None:
        plan = build_alter_role_factor_loop_plan(ROOT)
        self.assertEqual(_BASELINE_COUNT, len(plan.cases))
        for case in plan.cases:
            with self.subTest(case_id=case.case_id):
                witness = resolve_alter_role_factor_witness(case, ROOT)
                self.assertEqual(
                    case.primary_obligation_id,
                    witness.primary_obligation_id,
                )
                self.assertEqual(case.outcome, witness.outcome)
                self.assertEqual(
                    case.expected_sqlstate, witness.expected_sqlstate
                )
                self.assertTrue(witness.target_sql_fragment.strip())
                self.assertNotRegex(
                    witness.target_sql_fragment, r"\{[A-Za-z_]\w*\}"
                )
                self.assertTrue(
                    witness.target_sql_fragment.startswith("ALTER ROLE")
                )
                # setup_sql is legitimately empty for keyword targets
                # (ALL, CURRENT_ROLE), non-existent roles, and the bootstrap
                # superuser; the oracle is always present.
                self.assertTrue(witness.oracle_sql)
                self.assertTrue(witness.semantic_locus)

    def test_all_programs_are_complete_and_have_one_target(self) -> None:
        plan = build_alter_role_factor_loop_plan(ROOT)
        for case in plan.cases:
            with self.subTest(case_id=case.case_id):
                sql = render_alter_role_factor_case(case, ROOT)
                self.assertTrue(
                    sql.startswith("-- --------------------------------------------------------\n")
                )
                self.assertEqual(1, count_primary_alter_role(sql))
                self.assertIn(
                    f"-- primary_obligation_id: {case.primary_obligation_id}",
                    sql,
                )
                self.assertIn(f"-- case_id: {case.case_id}", sql)
                self.assertIn(f"-- expected_outcome: {case.outcome}", sql)
                self.assertIn(
                    f"-- expected_sqlstate: {case.expected_sqlstate}", sql
                )
                self.assertNotRegex(sql, r"\{[A-Za-z_]\w*\}")
                self.assertTrue(sql.endswith(";\n"))
                self.assertFalse(sql.endswith("\n\n"))

    def test_all_programs_are_deterministic_in_memory(self) -> None:
        plan = build_alter_role_factor_loop_plan(ROOT)
        first = [render_alter_role_factor_case(row, ROOT) for row in plan.cases]
        second = [render_alter_role_factor_case(row, ROOT) for row in plan.cases]
        self.assertEqual(first, second)
        self.assertEqual(_BASELINE_COUNT, len(first))

    def test_expected_failure_programs_capture_and_restore_error_mode(self) -> None:
        plan = build_alter_role_factor_loop_plan(ROOT)
        failures = [row for row in plan.cases if row.outcome == "expected_failure"]
        self.assertEqual(17, len(failures))
        for case in failures:
            with self.subTest(case_id=case.case_id):
                sql = render_alter_role_factor_case(case, ROOT)
                self.assertIn("\\set ON_ERROR_STOP off", sql)
                self.assertIn("\\set target_sqlstate :SQLSTATE", sql)
                self.assertIn(
                    f"SELECT :'target_sqlstate' = '{case.expected_sqlstate}'",
                    sql,
                )
                self.assertIn("\\set ON_ERROR_STOP on", sql)

    def test_success_programs_keep_error_stop_armed(self) -> None:
        plan = build_alter_role_factor_loop_plan(ROOT)
        successes = [row for row in plan.cases if row.outcome == "success"]
        self.assertEqual(91, len(successes))
        for case in successes:
            with self.subTest(case_id=case.case_id):
                sql = render_alter_role_factor_case(case, ROOT)
                self.assertIn("\\set ON_ERROR_STOP on", sql)
                self.assertNotIn("\\set ON_ERROR_STOP off", sql)

    def test_witness_fragments_are_present_in_rendered_bytes(self) -> None:
        plan = build_alter_role_factor_loop_plan(ROOT)
        for case in plan.cases:
            with self.subTest(case_id=case.case_id):
                sql = render_alter_role_factor_case(case, ROOT)
                witness = resolve_alter_role_factor_witness(case, ROOT)
                for fragment in witness.setup_sql:
                    self.assertIn(fragment.rstrip(), sql)
                for fragment in witness.oracle_sql:
                    self.assertIn(fragment.rstrip(), sql)
                for fragment in witness.cleanup_sql:
                    self.assertIn(fragment.rstrip(), sql)
                self.assertIn(witness.target_sql_fragment.rstrip(), sql)

    def test_transaction_witnesses_have_distinct_commit_and_rollback(self) -> None:
        plan = build_alter_role_factor_loop_plan(ROOT)
        rows = {row.factor_value: row for row in plan.cases if row.kind == "RISK"}
        self.assertEqual({"commit", "rollback"}, set(rows))
        commit_sql = render_alter_role_factor_case(rows["commit"], ROOT)
        rollback_sql = render_alter_role_factor_case(rows["rollback"], ROOT)
        self.assertIn("COMMIT;", commit_sql)
        self.assertIn("ROLLBACK;", rollback_sql)
        self.assertNotIn("ROLLBACK;", commit_sql)
        self.assertNotIn("COMMIT;", rollback_sql)

    def test_header_carries_huawei_and_factor_metadata(self) -> None:
        plan = build_alter_role_factor_loop_plan(ROOT)
        case = plan.cases[0]
        sql = render_alter_role_factor_case(case, ROOT)
        self.assertIn("版权所有(C)  2021-2030 华为技术有限公司", sql)
        self.assertIn("-- source_md:", sql)
        self.assertIn("-- factor_md:", sql)
        self.assertIn("-- description  : ALTER ROLE", sql)
        self.assertIn("-- FE           : PG18-STATEMENT-FACTOR-LOOP", sql)

    def test_catalog_relations_are_schema_qualified(self) -> None:
        plan = build_alter_role_factor_loop_plan(ROOT)
        for case in plan.cases:
            with self.subTest(case_id=case.case_id):
                sql = render_alter_role_factor_case(case, ROOT)
                # Every catalog reference must be schema-qualified.
                for bare in ("pg_roles", "pg_authid", "pg_settings"):
                    if bare in sql:
                        self.assertIn(
                            f"pg_catalog.{bare}", sql, (case.case_id, bare)
                        )

    def test_behavior_assertions_are_frozen_as_explicit_set(self) -> None:
        plan = build_alter_role_factor_loop_plan(ROOT)
        behavior_cases = [
            (c.factor_key, c.factor_value)
            for c in plan.cases
            if (c.factor_key, c.factor_value) in _FROZEN_BEHAVIOR_ASSERTIONS
        ]
        self.assertEqual(
            _FROZEN_BEHAVIOR_ASSERTIONS, frozenset(behavior_cases)
        )
        # Every BEHAVIOR case is a SUCCESS path (sqlstate 00000).
        for fk, fv in _FROZEN_BEHAVIOR_ASSERTIONS:
            case = next(
                c
                for c in plan.cases
                if c.factor_key == fk and c.factor_value == fv
            )
            self.assertEqual("success", case.outcome, case.case_id)
            self.assertEqual("00000", case.expected_sqlstate, case.case_id)

    def test_md5_password_cleared_on_rename_renders_correct_oracle(self) -> None:
        plan = build_alter_role_factor_loop_plan(ROOT)
        case = next(
            c
            for c in plan.cases
            if c.factor_key == "rename_clears_password"
            and c.factor_value == "md5_password_cleared_on_rename"
        )
        self.assertEqual("ALTERROLE0076", case.case_id)
        sql = render_alter_role_factor_case(case, ROOT)
        self.assertIn(
            "SELECT rolpassword IS NULL AS md5_password_cleared_on_rename",
            sql,
        )
        self.assertIn("pg_catalog.pg_authid", sql)

    def test_scram_password_preserved_on_rename_renders_correct_oracle(self) -> None:
        plan = build_alter_role_factor_loop_plan(ROOT)
        case = next(
            c
            for c in plan.cases
            if c.factor_key == "rename_clears_password"
            and c.factor_value == "scram_password_preserved_on_rename"
        )
        self.assertEqual("ALTERROLE0077", case.case_id)
        sql = render_alter_role_factor_case(case, ROOT)
        self.assertIn(
            "SELECT rolpassword IS NOT NULL "
            "AS scram_password_preserved_on_rename",
            sql,
        )
        self.assertIn("pg_catalog.pg_authid", sql)

    def test_password_null_removes_password_renders_correct_oracle(self) -> None:
        plan = build_alter_role_factor_loop_plan(ROOT)
        case = next(
            c
            for c in plan.cases
            if c.factor_key == "password_security"
            and c.factor_value == "password_null_removes_password"
        )
        self.assertEqual("ALTERROLE0057", case.case_id)
        sql = render_alter_role_factor_case(case, ROOT)
        self.assertIn("PASSWORD NULL", sql)
        self.assertIn(
            "SELECT rolpassword IS NULL AS password_null_removes_password",
            sql,
        )

    def test_self_password_only_is_a_success_path(self) -> None:
        plan = build_alter_role_factor_loop_plan(ROOT)
        case = next(
            c
            for c in plan.cases
            if c.factor_key == "privilege_requirement"
            and c.factor_value == "self_password_only"
        )
        self.assertEqual("success", case.outcome)
        sql = render_alter_role_factor_case(case, ROOT)
        self.assertIn("ALTER ROLE", sql)
        self.assertNotIn("\\set ON_ERROR_STOP off", sql)

    def test_bootstrap_superuser_property_is_immutable(self) -> None:
        plan = build_alter_role_factor_loop_plan(ROOT)
        case = next(
            c
            for c in plan.cases
            if c.factor_key == "privilege_insufficient"
            and c.factor_value == "bootstrap_superuser_property_change"
        )
        self.assertEqual("expected_failure", case.outcome)
        self.assertEqual("42501", case.expected_sqlstate)
        sql = render_alter_role_factor_case(case, ROOT)
        self.assertIn("ALTER ROLE", sql)
        self.assertIn("\\set ON_ERROR_STOP off", sql)


class AlterRoleExtensionRenderTest(unittest.TestCase):
    """Extension cases render through a byte-safe synthetic baseline case."""

    def setUp(self) -> None:
        self.extension_plan = build_alter_role_factor_extension_plan(ROOT)

    def _representative_subset(self) -> list[AlterRoleFactorExtensionCase]:
        seen: set[tuple[str, str]] = set()
        subset: list[AlterRoleFactorExtensionCase] = []
        for case in self.extension_plan.cases:
            a = dict(case.factor_assignment)
            key = (a["statement_branch"], case.outcome)
            if key in seen:
                continue
            seen.add(key)
            subset.append(case)
        return subset

    def test_extension_cases_render_complete_5_phase_program(self) -> None:
        for case in self._representative_subset():
            with self.subTest(case_id=case.case_id):
                sql = render_alter_role_factor_case(case, ROOT)
                self.assertTrue(
                    sql.startswith("-- --------------------------------------------------------\n")
                )
                self.assertEqual(1, count_primary_alter_role(sql))
                self.assertIn("-- primary-target-begin", sql)
                self.assertIn("-- primary-target-end", sql)
                self.assertIn(f"-- case_id: {case.case_id}", sql)
                self.assertIn(f"-- expected_outcome: {case.outcome}", sql)
                self.assertIn(
                    f"-- expected_sqlstate: {case.expected_sqlstate}", sql
                )
                self.assertIn("-- description  : ALTER ROLE", sql)
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
                sql = render_alter_role_factor_case(case, ROOT)
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
                sql = render_alter_role_factor_case(case, ROOT)
                self.assertNotIn("\\set ON_ERROR_STOP off", sql)

    def test_extension_witness_fragments_present_in_rendered_bytes(self) -> None:
        for case in self._representative_subset():
            with self.subTest(case_id=case.case_id):
                sql = render_alter_role_factor_case(case, ROOT)
                witness = resolve_alter_role_factor_witness(case, ROOT)
                self.assertEqual(case.derivation_id, witness.primary_obligation_id)
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
        first = [render_alter_role_factor_case(c, ROOT) for c in subset]
        second = [render_alter_role_factor_case(c, ROOT) for c in subset]
        self.assertEqual(first, second)

    def test_generator_writes_baseline_and_extension_files(self) -> None:
        baseline_plan = build_alter_role_factor_loop_plan(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "alter_role"
            count = generate_alter_role_factor_programs(
                baseline_plan, self.extension_plan, out
            )
            self.assertEqual(_BASELINE_COUNT + _EXTENSION_COUNT, count)
            files = sorted(out.glob("ALTERROLE*.sql"))
            self.assertEqual(_TOTAL, len(files))
            names = {f.name for f in files}
            self.assertEqual(_TOTAL, len(names))
            b0 = (out / baseline_plan.cases[0].sql_filename).read_text(
                encoding="utf-8"
            )
            self.assertEqual(1, count_primary_alter_role(b0))
            e0 = (out / self.extension_plan.cases[0].sql_filename).read_text(
                encoding="utf-8"
            )
            self.assertEqual(1, count_primary_alter_role(e0))


if __name__ == "__main__":
    unittest.main()
