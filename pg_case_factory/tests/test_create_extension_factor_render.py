from pathlib import Path
import unittest

from pg_case_factory.create_extension_factor_extension import (
    build_create_extension_factor_extension_plan,
)
from pg_case_factory.create_extension_factor_loop import (
    build_create_extension_factor_loop_plan,
)
from pg_case_factory.create_extension_factor_render import (
    count_primary_create_extension,
    render_create_extension_factor_case,
    resolve_create_extension_factor_witness,
)

ROOT = Path(__file__).resolve().parents[1]


class CreateExtensionFactorRenderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = build_create_extension_factor_loop_plan(ROOT)
        cls.ext = build_create_extension_factor_extension_plan(ROOT)
        cls.all_cases = list(cls.loop.cases) + list(cls.ext.cases)

    def test_renders_all_cases_without_error(self) -> None:
        for case in self.all_cases:
            sql = render_create_extension_factor_case(case, ROOT)
            self.assertIsInstance(sql, str)
            self.assertTrue(sql.endswith("\n"))

    def test_primary_target_cardinality_is_one(self) -> None:
        for case in self.all_cases:
            sql = render_create_extension_factor_case(case, ROOT)
            self.assertEqual(
                1,
                count_primary_create_extension(sql),
                f"primary count != 1 for {case.case_id}",
            )

    def test_no_placeholder_leakage(self) -> None:
        for case in self.all_cases:
            sql = render_create_extension_factor_case(case, ROOT)
            self.assertNotIn("{", sql)
            self.assertNotIn("}", sql)

    def test_re_render_is_deterministic(self) -> None:
        for case in self.all_cases[:50]:
            first = render_create_extension_factor_case(case, ROOT)
            second = render_create_extension_factor_case(case, ROOT)
            self.assertEqual(first, second)

    def test_header_contains_required_traces(self) -> None:
        case = self.loop.cases[0]
        sql = render_create_extension_factor_case(case, ROOT)
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
            sql = render_create_extension_factor_case(case, ROOT)
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
            sql = render_create_extension_factor_case(case, ROOT)
            from_clauses = re.findall(
                r"FROM\s+(\"[^\"]+\")", sql, re.IGNORECASE
            )
            self.assertEqual(
                [],
                from_clauses,
                f"quoted identifier in FROM for {case.case_id}",
            )

    def test_bookend_when_table_creating(self) -> None:
        import re

        for case in self.all_cases:
            sql = render_create_extension_factor_case(case, ROOT)
            has_create_table = bool(
                re.search(r"(?im)^\s*CREATE\s+TABLE\b", sql)
            )
            if has_create_table:
                stmts = [
                    s.strip()
                    for s in sql.split(";")
                    if s.strip()
                    and not all(
                        l.strip().startswith(("--", "\\"))
                        for l in s.split("\n")
                    )
                ]
                if stmts:
                    first = stmts[0].lstrip().split("\n")[-1].strip()
                    last = stmts[-1].lstrip().split("\n")[-1].strip()
                    self.assertTrue(
                        first.upper().startswith(
                            "DROP TABLE IF EXISTS"
                        ),
                        f"bookend first mismatch for {case.case_id}: "
                        f"{first[:60]}",
                    )
                    self.assertTrue(
                        last.upper().startswith(
                            "DROP TABLE IF EXISTS"
                        ),
                        f"bookend last mismatch for {case.case_id}: "
                        f"{last[:60]}",
                    )

    def test_witness_resolution_succeeds(self) -> None:
        case = self.loop.cases[0]
        witness = resolve_create_extension_factor_witness(
            case, ROOT
        )
        self.assertTrue(witness.target_sql_fragment)
        self.assertEqual(case.outcome, witness.outcome)
        self.assertEqual(
            case.expected_sqlstate, witness.expected_sqlstate
        )


if __name__ == "__main__":
    unittest.main()
