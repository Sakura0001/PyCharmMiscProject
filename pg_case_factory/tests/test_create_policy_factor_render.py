"""Tests for create_policy factor render module."""

import re
import tempfile
import unittest
from pathlib import Path

from src.pg_case_factory.create_policy_factor_extension import (
    build_create_policy_factor_extension_plan,
)
from src.pg_case_factory.create_policy_factor_loop import (
    build_create_policy_factor_loop_plan,
)
from src.pg_case_factory.create_policy_factor_render import (
    count_primary_create_policy,
    generate_create_policy_factor_programs,
    render_create_policy_factor_case,
)

_REPO = Path(__file__).resolve().parents[1]


class TestCreatePolicyFactorRender(unittest.TestCase):
    def setUp(self) -> None:
        self.baseline = build_create_policy_factor_loop_plan(_REPO)
        self.extension = build_create_policy_factor_extension_plan(
            _REPO
        )
        self.out = Path(tempfile.mkdtemp())
        self.count = generate_create_policy_factor_programs(
            self.baseline, self.extension, self.out
        )

    def test_file_count(self) -> None:
        self.assertEqual(1017, self.count)

    def test_filename_numbering(self) -> None:
        files = sorted(f.name for f in self.out.iterdir())
        self.assertEqual(
            [f"CREATEPOLICY{i:05d}.sql" for i in range(1, 1018)],
            files,
        )

    def test_one_primary_target_per_file(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            self.assertEqual(
                1, count_primary_create_policy(sql)
            )

    def test_bookend_first_and_last_drop_table(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            lines = sql.split("\n")
            stmts: list[str] = []
            current: list[str] = []
            for line in lines:
                stripped = line.strip()
                if (
                    stripped.startswith("--")
                    or stripped.startswith("\\")
                ):
                    continue
                current.append(stripped)
                if stripped.endswith(";"):
                    stmts.append(" ".join(current))
                    current = []
            if current:
                stmts.append(" ".join(current))
            stmts = [s for s in stmts if s]
            self.assertTrue(
                re.match(
                    r"(?i)DROP\s+TABLE\s+IF\s+EXISTS",
                    stmts[0],
                ),
                msg=f"{f.name}: first stmt is not DROP TABLE",
            )
            self.assertTrue(
                re.match(
                    r"(?i)DROP\s+TABLE\s+IF\s+EXISTS",
                    stmts[-1],
                ),
                msg=f"{f.name}: last stmt is not DROP TABLE",
            )

    def test_every_catalog_query_has_order_by(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            for m in re.finditer(
                r"(?is)SELECT\s[^;]*?FROM\s+(?:pg_catalog|information_schema)\.\S+[^;]*;",
                sql,
            ):
                self.assertIn(
                    "ORDER BY", m.group(0).upper()
                )

    def test_primary_target_is_create_policy(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            region = sql.split(
                "-- primary-target-begin", 1
            )[1]
            region = region.split(
                "-- primary-target-end", 1
            )[0]
            self.assertRegex(
                region, r"(?im)CREATE\s+POLICY\b"
            )

    def test_witness_resolves(self) -> None:
        from src.pg_case_factory.create_policy_factor_render import (
            resolve_create_policy_factor_witness,
        )
        for case in self.baseline.cases[:3]:
            w = resolve_create_policy_factor_witness(
                case, _REPO
            )
            self.assertTrue(w.target_sql_fragment)
            self.assertTrue(w.semantic_locus)

    def test_deterministic_render(self) -> None:
        for case in self.baseline.cases[:5]:
            a = render_create_policy_factor_case(
                case, _REPO
            )
            b = render_create_policy_factor_case(
                case, _REPO
            )
            self.assertEqual(a, b)

    def test_header_fields(self) -> None:
        sql = (
            self.out / "CREATEPOLICY00001.sql"
        ).read_text()
        self.assertIn(
            "-- case_id: CREATEPOLICY00001", sql
        )
        self.assertIn("-- source_md:", sql)
        self.assertIn("-- factor_md:", sql)
        self.assertIn(
            "-- primary_obligation_id:", sql
        )
        self.assertIn("-- expected_outcome:", sql)
        self.assertIn("-- expected_sqlstate:", sql)

    def test_cleanup_section(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            self.assertIn(
                "-- 5. 清理全部本编号对象。", sql
            )

    def test_no_placeholder_leakage(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            self.assertNotIn("{", sql)
            self.assertNotIn("}", sql)

    def test_on_error_stop_management(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            self.assertIn(
                "\\set ON_ERROR_STOP on", sql
            )

    def test_setup_boundary_present(self) -> None:
        for f in sorted(self.out.iterdir()):
            sql = f.read_text()
            self.assertIn(
                "SELECT 1 AS setup_boundary;", sql
            )

    def test_cleanup_bookend_invariants(self) -> None:
        """Fix-A guard: DROP OWNED BY is unreachable in pre-cleanup (the
        actor role fixture is created by setup, so on a fresh database the
        role does not exist at pre-cleanup time and DROP OWNED BY would crash
        under ON_ERROR_STOP=1 before the target statement).  In cleanup,
        DROP OWNED BY must precede DROP ROLE IF EXISTS."""
        files = sorted(self.out.iterdir())
        self.assertGreater(len(files), 0)
        pre_drop_owned: list[str] = []
        cleanup_order_bad: list[str] = []
        for f in files:
            sql = f.read_text()
            if "cleanup-bookend: pre-cleanup-begin" not in sql:
                continue
            pre = sql.split(
                "cleanup-bookend: pre-cleanup-begin", 1
            )[1]
            pre = pre.split(
                "cleanup-bookend: pre-cleanup-end", 1
            )[0]
            if re.search(
                r"\bDROP\s+OWNED\s+BY\b", pre, re.IGNORECASE
            ):
                pre_drop_owned.append(f.name)
            cln = sql.split(
                "cleanup-bookend: cleanup-begin", 1
            )[1]
            cln = cln.split(
                "cleanup-bookend: cleanup-end", 1
            )[0]
            m_own = re.search(
                r"\bDROP\s+OWNED\s+BY\b", cln, re.IGNORECASE
            )
            m_role = re.search(
                r"\bDROP\s+ROLE\b", cln, re.IGNORECASE
            )
            if m_own and m_role and m_own.start() > m_role.start():
                cleanup_order_bad.append(f.name)
        self.assertEqual(
            [],
            pre_drop_owned,
            "DROP OWNED BY leaked into pre-cleanup",
        )
        self.assertEqual(
            [],
            cleanup_order_bad,
            "DROP OWNED BY after DROP ROLE in cleanup",
        )


if __name__ == "__main__":
    unittest.main()
