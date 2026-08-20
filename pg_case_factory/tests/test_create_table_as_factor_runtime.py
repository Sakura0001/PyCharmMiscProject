"""Tests for create_table_as factor runtime module."""

import unittest
from pathlib import Path

from src.pg_case_factory.create_table_as_factor_runtime import (
    PG18_BIN,
    PG18_PORT,
    PG18_SOCKET,
    CreateTableAsPg18Runner,
    CreateTableAsSuiteRun,
    build_create_table_as_runtime_case_set,
    compare_create_table_as_runs,
)

_REPO = Path(__file__).resolve().parents[1]


class TestCreateTableAsFactorRuntime(unittest.TestCase):
    def test_frozen_constants(self) -> None:
        self.assertEqual(PG18_PORT, "5180")
        self.assertEqual(
            PG18_SOCKET, "/var/run/postgresql"
        )
        self.assertEqual(
            PG18_BIN, "/usr/lib/postgresql/18/bin"
        )

    def test_case_set_count(self) -> None:
        cs = build_create_table_as_runtime_case_set(_REPO)
        self.assertEqual(86, cs.baseline_case_count)
        self.assertEqual(3975, cs.extension_case_count)
        self.assertEqual(4061, cs.total_case_count)

    def test_case_set_deterministic_sha(self) -> None:
        cs = build_create_table_as_runtime_case_set(_REPO)
        other = build_create_table_as_runtime_case_set(_REPO)
        self.assertEqual(
            cs.case_id_multiset_sha256,
            other.case_id_multiset_sha256,
        )

    def test_sorted_by_ordinal(self) -> None:
        cs = build_create_table_as_runtime_case_set(_REPO)
        ordinals = [c.case_id for c in cs.cases]
        self.assertEqual(ordinals, sorted(ordinals))

    def test_runner_construction(self) -> None:
        runner = CreateTableAsPg18Runner()
        self.assertEqual(runner._pg18_port, PG18_PORT)
        self.assertEqual(runner._pg18_socket, PG18_SOCKET)

    def test_compare_identical_runs(self) -> None:
        cs = build_create_table_as_runtime_case_set(_REPO)
        result = type(
            "R", (), {"case_id": "x", "sql_filename": "x.sql",
                       "exit_code": 0, "target_sqlstate": "00000",
                       "stderr_excerpt": "", "passed": True}
        )()
        run_a = CreateTableAsSuiteRun(
            run_label="a", results=(result,), pass_count=1,
            fail_count=0,
        )
        run_b = CreateTableAsSuiteRun(
            run_label="b", results=(result,), pass_count=1,
            fail_count=0,
        )
        cmp = compare_create_table_as_runs(run_a, run_b)
        self.assertTrue(cmp.stable)
        self.assertEqual((), cmp.divergent_case_ids)


if __name__ == "__main__":
    unittest.main()
