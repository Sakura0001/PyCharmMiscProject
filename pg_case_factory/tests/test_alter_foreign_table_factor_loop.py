from __future__ import annotations

from collections import Counter
from pathlib import Path
import unittest

from pg_case_factory.alter_foreign_table_factor_loop import (
    compile_alter_foreign_table_factor_loop_obligations,
)


ROOT = Path(__file__).resolve().parents[1]


class AlterForeignTableFactorLoopLedgerTest(unittest.TestCase):
    def test_compiles_exact_required_obligation_bag(self) -> None:
        rows = compile_alter_foreign_table_factor_loop_obligations(ROOT)
        self.assertEqual(1_817, len(rows))
        self.assertEqual(
            {"GRM": 136, "SFV": 103, "INV": 1_576, "RISK": 2},
            Counter(row.kind for row in rows),
        )
        self.assertEqual(1_817, len({row.obligation_id for row in rows}))
        self.assertEqual(12, sum(row.disposition == "delegated" for row in rows))
        self.assertEqual(
            1_805,
            sum(
                row.disposition in {"covered", "expected_failure"}
                for row in rows
            ),
        )


if __name__ == "__main__":
    unittest.main()
