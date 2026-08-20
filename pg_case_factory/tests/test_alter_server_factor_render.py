from __future__ import annotations

from pathlib import Path
import unittest

from pg_case_factory.alter_server_factor_extension import (
    AlterServerFactorExtensionCase,
    build_alter_server_factor_extension_plan,
)
from pg_case_factory.alter_server_factor_loop import (
    build_alter_server_factor_loop_plan,
)
from pg_case_factory.alter_server_factor_render import (
    AlterServerFactorRenderError,
    count_primary_alter_server,
    generate_alter_server_factor_programs,
    render_alter_server_factor_case,
    resolve_alter_server_factor_witness,
)

ROOT = Path(__file__).resolve().parents[1]

_BASELINE_COUNT = 53
_EXTENSION_COUNT = 2286
_TOTAL = _BASELINE_COUNT + _EXTENSION_COUNT  # 2339


class AlterServerFactorRenderTest(unittest.TestCase):
    def test_every_case_resolves_a_concrete_witness(self) -> None:
        plan = build_alter_server_factor_loop_plan(ROOT)
        self.assertEqual(_BASELINE_COUNT, len(plan.cases))
        for case in plan.cases:
            with self.subTest(case_id=case.case_id):
                witness = resolve_alter_server_factor_witness(case, ROOT)
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
                    witness.target_sql_fragment.startswith("ALTER SERVER")
                )
                self.assertTrue(witness.setup_sql)
                self.assertTrue(witness.oracle_sql)
                self.assertTrue(witness.cleanup_sql)
                self.assertTrue(witness.semantic_locus)

    def test_all_programs_are_complete_and_have_one_target(self) -> None:
        plan = build_alter_server_factor_loop_plan(ROOT)
        ext = build_alter_server_factor_extension_plan(ROOT)
        for case in plan.cases:
            with self.subTest(case_id=case.case_id):
                sql = render_alter_server_factor_case(case, ROOT)
                self.assertEqual(1, count_primary_alter_server(sql))
                self.assertIn("-- primary-target-begin", sql)
                self.assertIn("-- primary-target-end", sql)
                self.assertIn("ALTER SERVER", sql)
                self.assertNotIn("{", sql)
                self.assertNotIn("}", sql)
                self.assertTrue(sql.endswith("\n"))
        for case in ext.cases[:50]:
            with self.subTest(case_id=case.case_id):
                sql = render_alter_server_factor_case(case, ROOT)
                self.assertEqual(1, count_primary_alter_server(sql))
                self.assertNotIn("{", sql)
                self.assertNotIn("}", sql)

    def test_schema_qualified_catalog_oracles(self) -> None:
        plan = build_alter_server_factor_loop_plan(ROOT)
        ext = build_alter_server_factor_extension_plan(ROOT)
        for case in list(plan.cases) + list(ext.cases[:200]):
            with self.subTest(case_id=case.case_id):
                sql = render_alter_server_factor_case(case, ROOT)
                # Catalog oracles must schema-qualify pg_foreign_server or
                # pg_foreign_data_wrapper (both exempt from prefix), or
                # use an error_assertion probe for failure cases.
                self.assertTrue(
                    "pg_catalog.pg_foreign_server" in sql
                    or "pg_catalog.pg_foreign_data_wrapper" in sql
                    or "target_sqlstate_matches_expected" in sql,
                    f"no schema-qualified catalog oracle in "
                    f"{case.case_id}",
                )

    def test_keyword_owner_transfer_oracle_is_present(self) -> None:
        plan = build_alter_server_factor_loop_plan(ROOT)
        ext = build_alter_server_factor_extension_plan(ROOT)
        found = False
        for case in list(plan.cases) + list(ext.cases):
            a = (
                dict(case.factor_assignment)
                if hasattr(case, "factor_assignment")
                else dict(case.baseline_assignments)
            )
            if a.get("owner_to_shape") != "session_user_keyword":
                continue
            if case.outcome != "success":
                continue
            found = True
            with self.subTest(case_id=case.case_id):
                sql = render_alter_server_factor_case(case, ROOT)
                self.assertIn("OWNER TO SESSION_USER", sql)
                self.assertIn("ALTER SERVER", sql)
        self.assertTrue(
            found, "no SESSION_USER keyword success case found"
        )

    def test_fdw_validator_function_for_invalid_option(self) -> None:
        ext = build_alter_server_factor_extension_plan(ROOT)
        found = False
        for case in ext.cases:
            a = dict(case.factor_assignment)
            if (
                a.get("option_key_value_shape")
                != "invalid_option_rejected_by_validator"
            ):
                continue
            if a.get("server_state") == "non_existent":
                continue
            found = True
            with self.subTest(case_id=case.case_id):
                sql = render_alter_server_factor_case(case, ROOT)
                self.assertIn("CREATE OR REPLACE FUNCTION", sql)
                self.assertIn("invalid_option", sql)
            break
        self.assertTrue(found, "no invalid_option extension case")

    def test_generate_programs_writes_all_files(self) -> None:
        import tempfile

        plan = build_alter_server_factor_loop_plan(ROOT)
        ext = build_alter_server_factor_extension_plan(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            count = generate_alter_server_factor_programs(
                plan, ext, Path(tmp)
            )
            self.assertEqual(_TOTAL, count)


if __name__ == "__main__":
    unittest.main()
