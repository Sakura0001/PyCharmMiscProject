"""Tests for the bounded ALTER INDEX PG18.4 runtime.

The runtime is DB-bound and serial.  These tests exercise the pure structural
contracts (case-set combiner, two-run comparison, runner construction) that
need no cluster.  The live double-run is gated behind a real PG18.4 server and
is skipped when the frozen psql binary is absent -- the downstream Fork-C
phase performs the actual two-run calibration.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pg_case_factory.alter_index_factor_runtime import (
    AlterIndexCaseRuntimeResult,
    AlterIndexPg18Runner,
    AlterIndexRuntimeError,
    AlterIndexSuiteRun,
    MAX_PARALLELISM,
    PG18_BIN,
    PG18_DATABASE,
    PG18_PORT,
    PG18_SOCKET,
    build_alter_index_runtime_case_set,
    compare_alter_index_runs,
)


ROOT = Path(__file__).resolve().parents[1]

_BASELINE_COUNT = 772
_EXTENSION_COUNT = 6786
_TOTAL = _BASELINE_COUNT + _EXTENSION_COUNT  # 7558


def _sample_case(stdout: bytes) -> AlterIndexCaseRuntimeResult:
    return AlterIndexCaseRuntimeResult(
        case_id="ALTERINDEX00001",
        sql_filename="ALTERINDEX00001.sql",
        expected_sqlstate="00000",
        target_sqlstate="00000",
        exit_code=0,
        timed_out=False,
        normalized_stdout=stdout,
        normalized_stderr=b"",
        boolean_oracle_failure_count=0,
        pre_clean=True,
        post_clean=True,
        cleanup_exit_code=0,
    )


def _server_available() -> bool:
    # The psql binary alone is not enough: the frozen alter_index cluster
    # (socket + port 55487) is only up once the Fork-C double-run phase has
    # started it.  Gate on the live socket file so Fork B skips cleanly.
    socket_file = PG18_SOCKET / f".s.PGSQL.{PG18_PORT}"
    return (PG18_BIN / "psql").is_file() and socket_file.exists()


class AlterIndexFactorRuntimeTest(unittest.TestCase):
    def test_two_run_result_requires_identical_normalized_transcripts(
        self,
    ) -> None:
        identical = compare_alter_index_runs(
            AlterIndexSuiteRun(run_ordinal=1, cases=(_sample_case(b"ok\n"),)),
            AlterIndexSuiteRun(run_ordinal=2, cases=(_sample_case(b"ok\n"),)),
        )
        self.assertTrue(identical.passed, identical.issues)

        changed = compare_alter_index_runs(
            AlterIndexSuiteRun(run_ordinal=1, cases=(_sample_case(b"ok\n"),)),
            AlterIndexSuiteRun(
                run_ordinal=2,
                cases=(_sample_case(b"different\n"),),
            ),
        )
        self.assertFalse(changed.passed)
        self.assertEqual(
            ("ALTERINDEX00001",),
            changed.transcript_mismatch_case_ids,
        )

    def test_sqlstate_mismatch_is_detected(self) -> None:
        mismatch = _sample_case(b"ok\n")
        object.__setattr__(mismatch, "expected_sqlstate", "42P01")
        report = compare_alter_index_runs(
            AlterIndexSuiteRun(run_ordinal=1, cases=(mismatch,)),
            AlterIndexSuiteRun(run_ordinal=2, cases=(mismatch,)),
        )
        self.assertFalse(report.passed)
        self.assertEqual(("ALTERINDEX00001",), report.sqlstate_mismatch_case_ids)

    def test_suite_run_rejects_bad_ordinal(self) -> None:
        with self.assertRaises(AlterIndexRuntimeError):
            AlterIndexSuiteRun(run_ordinal=3, cases=())

    def test_runtime_case_set_combines_baseline_and_extension(self) -> None:
        # The case-set combiner must merge the frozen 772-case baseline with
        # the bounded 6,786-case extension into a single ordinal-sorted
        # sequence and map every case to its SQL file path.  This is a pure
        # structural contract (no cluster, no SQL files required on disk).
        with tempfile.TemporaryDirectory() as temporary:
            sql_dir = Path(temporary)
            cases, sql_paths = build_alter_index_runtime_case_set(
                ROOT, sql_dir
            )
            self.assertEqual(_TOTAL, len(cases))
            ordinals = [getattr(case, "ordinal") for case in cases]
            self.assertEqual(
                list(range(1, _TOTAL + 1)), ordinals
            )
            self.assertEqual(_TOTAL, len(sql_paths))
            for case in cases:
                self.assertEqual(
                    sql_paths[case.case_id],
                    sql_dir / case.sql_filename,
                )

    def test_runtime_is_serial_db_bound(self) -> None:
        self.assertEqual(1, MAX_PARALLELISM)
        self.assertEqual("pgcf_ai", PG18_DATABASE)
        self.assertEqual(55487, PG18_PORT)

    def test_runner_timeout_bounds(self) -> None:
        with self.assertRaises(AlterIndexRuntimeError):
            AlterIndexPg18Runner(timeout_seconds=0)
        with self.assertRaises(AlterIndexRuntimeError):
            AlterIndexPg18Runner(timeout_seconds=301)

    @unittest.skipUnless(
        _server_available(), "PG18.4 psql binary not present"
    )
    def test_verify_server_when_available(self) -> None:
        # Gated: only runs when the frozen PG18.4 install exists.  Fork B
        # ships this as a skip; the Fork-C double-run phase exercises it live.
        runner = AlterIndexPg18Runner()
        version = runner.verify_server()
        self.assertTrue(180004 <= version < 180005)


if __name__ == "__main__":
    unittest.main()
