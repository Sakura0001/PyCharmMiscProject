from pathlib import Path
import re
import unittest

from pg_case_factory.create_foreign_data_wrapper_factor_extension import (
    build_create_foreign_data_wrapper_factor_extension_plan,
)
from pg_case_factory.create_foreign_data_wrapper_factor_loop import (
    build_create_foreign_data_wrapper_factor_loop_plan,
)
from pg_case_factory.create_foreign_data_wrapper_factor_render import (
    count_primary_create_foreign_data_wrapper,
    render_create_foreign_data_wrapper_factor_case,
    resolve_create_foreign_data_wrapper_factor_witness,
)

ROOT = Path(__file__).resolve().parents[1]


class CreateForeignDataWrapperFactorRenderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = (
            build_create_foreign_data_wrapper_factor_loop_plan(ROOT)
        )
        cls.ext = (
            build_create_foreign_data_wrapper_factor_extension_plan(ROOT)
        )
        cls.all_cases = list(cls.loop.cases) + list(cls.ext.cases)

    def test_cleanup_bookend_invariants(self) -> None:
        """Fix-A guard: DROP OWNED BY is unreachable in pre-cleanup (the
        actor role fixture is created by setup, so on a fresh database the
        role does not exist at pre-cleanup time and DROP OWNED BY would
        crash under ON_ERROR_STOP=1 before the target statement).  In
        cleanup, DROP OWNED BY must precede DROP ROLE IF EXISTS."""
        self.assertGreater(len(self.all_cases), 0)
        pre_drop_owned: list[str] = []
        cleanup_order_bad: list[str] = []
        for case in self.all_cases:
            text = render_create_foreign_data_wrapper_factor_case(
                case, ROOT
            )
            if "cleanup-bookend: pre-cleanup-begin" not in text:
                continue
            pre = text.split("cleanup-bookend: pre-cleanup-begin", 1)[1]
            pre = pre.split("cleanup-bookend: pre-cleanup-end", 1)[0]
            if re.search(r"\bDROP\s+OWNED\s+BY\b", pre, re.IGNORECASE):
                pre_drop_owned.append(case.case_id)
            cln = text.split("cleanup-bookend: cleanup-begin", 1)[1]
            cln = cln.split("cleanup-bookend: cleanup-end", 1)[0]
            m_own = re.search(r"\bDROP\s+OWNED\s+BY\b", cln, re.IGNORECASE)
            m_role = re.search(r"\bDROP\s+ROLE\b", cln, re.IGNORECASE)
            if m_own and m_role and m_own.start() > m_role.start():
                cleanup_order_bad.append(case.case_id)
        self.assertEqual([], pre_drop_owned, "DROP OWNED BY leaked into pre-cleanup")
        self.assertEqual([], cleanup_order_bad, "DROP OWNED BY after DROP ROLE in cleanup")

    def test_renders_all_cases_without_error(self) -> None:
        for case in self.all_cases:
            sql = render_create_foreign_data_wrapper_factor_case(
                case, ROOT
            )
            self.assertIsInstance(sql, str)
            self.assertTrue(sql.endswith("\n"))

    def test_primary_target_cardinality_is_one(self) -> None:
        for case in self.all_cases:
            sql = render_create_foreign_data_wrapper_factor_case(
                case, ROOT
            )
            self.assertEqual(
                1,
                count_primary_create_foreign_data_wrapper(sql),
                f"primary count != 1 for {case.case_id}",
            )

    def test_no_placeholder_leakage(self) -> None:
        for case in self.all_cases:
            sql = render_create_foreign_data_wrapper_factor_case(
                case, ROOT
            )
            self.assertNotIn("{", sql)
            self.assertNotIn("}", sql)

    def test_re_render_is_deterministic(self) -> None:
        for case in self.all_cases[:50]:
            first = render_create_foreign_data_wrapper_factor_case(
                case, ROOT
            )
            second = render_create_foreign_data_wrapper_factor_case(
                case, ROOT
            )
            self.assertEqual(first, second)

    def test_header_contains_required_traces(self) -> None:
        case = self.loop.cases[0]
        sql = render_create_foreign_data_wrapper_factor_case(
            case, ROOT
        )
        self.assertIn(f"-- case_id: {case.case_id}", sql)
        self.assertIn(
            f"-- primary_obligation_id: {case.primary_obligation_id}",
            sql,
        )
        self.assertIn(
            f"-- expected_outcome: {case.outcome}", sql
        )
        self.assertIn(
            f"-- expected_sqlstate: {case.expected_sqlstate}", sql
        )

    def test_catalog_queries_have_order_by(self) -> None:
        import re

        for case in self.all_cases:
            sql = render_create_foreign_data_wrapper_factor_case(
                case, ROOT
            )
            stmts = [
                s.strip() + ";"
                for s in sql.split(";")
                if s.strip()
            ]
            for stmt in stmts:
                if re.search(
                    r"(?im)^\s*SELECT\b.*\bFROM\s+pg_catalog\b",
                    stmt,
                    re.IGNORECASE | re.DOTALL,
                ):
                    self.assertIn(
                        "ORDER BY",
                        stmt.upper(),
                        f"missing ORDER BY in catalog query for "
                        f"{case.case_id}: {stmt[:80]}",
                    )

    def test_no_quoted_identifiers_in_from_join(self) -> None:
        import re

        for case in self.all_cases:
            sql = render_create_foreign_data_wrapper_factor_case(
                case, ROOT
            )
            from_clauses = re.findall(
                r"FROM\s+(\"[^\"]+\")", sql, re.IGNORECASE
            )
            self.assertEqual(
                [],
                from_clauses,
                f"quoted identifier in FROM for {case.case_id}",
            )

    def test_no_create_table_bookend_exempt(self) -> None:
        import re

        for case in self.all_cases:
            sql = render_create_foreign_data_wrapper_factor_case(
                case, ROOT
            )
            has_create_table = bool(
                re.search(r"(?im)^\s*CREATE\s+TABLE\b", sql)
            )
            self.assertFalse(
                has_create_table,
                f"CREATE TABLE found in table-less case "
                f"{case.case_id}",
            )

    def test_no_or_replace(self) -> None:
        for case in self.all_cases:
            sql = render_create_foreign_data_wrapper_factor_case(
                case, ROOT
            )
            self.assertNotIn(
                "OR REPLACE",
                sql.upper(),
                f"OR REPLACE found in {case.case_id}",
            )

    def test_witness_resolution_succeeds(self) -> None:
        case = self.loop.cases[0]
        witness = (
            resolve_create_foreign_data_wrapper_factor_witness(
                case, ROOT
            )
        )
        self.assertTrue(witness.target_sql_fragment)
        self.assertEqual(case.outcome, witness.outcome)
        self.assertEqual(
            case.expected_sqlstate, witness.expected_sqlstate
        )


if __name__ == "__main__":
    unittest.main()
