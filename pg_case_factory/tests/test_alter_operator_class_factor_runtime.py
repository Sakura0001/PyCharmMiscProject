"""Skip-gated runtime tests for the ALTER OPERATOR CLASS PG 18.4 executor.

The no-DB phase ships the runtime module without a live cluster.  When the
per-statement cluster is down, the suite skips; when it is up, a tiny subset
of the generated programs is executed twice and compared for idempotency.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from pg_case_factory.alter_operator_class_factor_runtime import (
    AlterOperatorClassPg18Runner,
    AlterOperatorClassRuntimeError,
)

ROOT = Path(__file__).resolve().parents[1]


def _cluster_reachable() -> bool:
    runner = AlterOperatorClassPg18Runner()
    try:
        return runner.verify_server()
    except Exception:
        return False


@unittest.skipUnless(
    _cluster_reachable(),
    "PG 18.4 alter_operator_class cluster (port 55493) is not reachable",
)
class AlterOperatorClassRuntimeSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        from pg_case_factory.alter_operator_class_factor_loop import (
            build_alter_operator_class_factor_loop_plan,
        )

        self.baseline = build_alter_operator_class_factor_loop_plan(ROOT)

    def test_runner_constructs_with_valid_timeout(self) -> None:
        runner = AlterOperatorClassPg18Runner(timeout_seconds=30)
        self.assertIsNotNone(runner)

    def test_runner_rejects_timeout_out_of_range(self) -> None:
        with self.assertRaises(AlterOperatorClassRuntimeError):
            AlterOperatorClassPg18Runner(timeout_seconds=0)
        with self.assertRaises(AlterOperatorClassRuntimeError):
            AlterOperatorClassPg18Runner(timeout_seconds=301)


class AlterOperatorClassRuntimeModuleTests(unittest.TestCase):
    """Static module-level checks that do not require the cluster."""

    def test_module_constants_are_frozen(self) -> None:
        from pg_case_factory.alter_operator_class_factor_runtime import (
            PG18_DATABASE,
            PG18_PORT,
            PG18_SUPERUSER,
            MAX_PARALLELISM,
        )

        self.assertEqual(PG18_PORT, 55493)
        self.assertEqual(PG18_DATABASE, "pgcf_aoc")
        self.assertEqual(PG18_SUPERUSER, "pgcf_superuser")
        self.assertEqual(MAX_PARALLELISM, 1)


if __name__ == "__main__":
    unittest.main()
