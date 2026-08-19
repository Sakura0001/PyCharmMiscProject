from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from pg_case_factory.alter_group_factor_render import (
    render_alter_group_factor_case,
)
from pg_case_factory.alter_group_factor_runtime import (
    AlterGroupCaseRuntimeResult,
    AlterGroupPg18Runner,
    AlterGroupSuiteRun,
    build_alter_group_runtime_case_set,
    compare_alter_group_runs,
)


ROOT = Path(__file__).resolve().parents[1]
PG18_BIN = Path("/tmp/pgcf-postgresql-18.4-install/bin")
PG18_SOCKET = Path("/tmp/pgcf-pg18-ag-sock-20260819")

# Six representative cases spanning every calibrated branch: add_user
# success, drop_user success with an admin-granted membership (the admin
# must be the grantor so it can revoke its own grant), rename success
# (CREATEROLE), a privilege-denied expected failure (the pre-granted
# membership survives the denial), a rename name conflict (42710), and a
# post-coverage extension whose oracle probes pg_authid (RESET ROLE before
# the oracle so the catalog is readable as superuser).
_REPRESENTATIVE_CASE_IDS = (
    "ALTERGROUP0001",
    "ALTERGROUP0002",
    "ALTERGROUP0003",
    "ALTERGROUP0021",
    "ALTERGROUP0025",
    "ALTERGROUP0064",
)


def _sample_case(stdout: bytes) -> AlterGroupCaseRuntimeResult:
    return AlterGroupCaseRuntimeResult(
        case_id="ALTERGROUP0001",
        sql_filename="ALTERGROUP0001.sql",
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


class AlterGroupFactorRuntimeTest(unittest.TestCase):
    def test_two_run_result_requires_identical_normalized_transcripts(self) -> None:
        identical = compare_alter_group_runs(
            AlterGroupSuiteRun(run_ordinal=1, cases=(_sample_case(b"ok\n"),)),
            AlterGroupSuiteRun(run_ordinal=2, cases=(_sample_case(b"ok\n"),)),
        )
        self.assertTrue(identical.passed, identical.issues)

        changed = compare_alter_group_runs(
            AlterGroupSuiteRun(run_ordinal=1, cases=(_sample_case(b"ok\n"),)),
            AlterGroupSuiteRun(
                run_ordinal=2,
                cases=(_sample_case(b"different\n"),),
            ),
        )
        self.assertFalse(changed.passed)
        self.assertEqual(
            ("ALTERGROUP0001",),
            changed.transcript_mismatch_case_ids,
        )

    @unittest.skipUnless(
        (PG18_BIN / "psql").is_file() and PG18_SOCKET.is_dir(),
        "local PostgreSQL 18.4 fixture is unavailable",
    )
    def test_six_representative_cases_execute_twice_on_pg18_4(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sql_dir = Path(temporary)
            cases, _discarded_paths = build_alter_group_runtime_case_set(
                ROOT, sql_dir
            )
            by_id = {case.case_id: case for case in cases}
            for case_id in _REPRESENTATIVE_CASE_IDS:
                self.assertIn(
                    case_id,
                    by_id,
                    f"representative case {case_id} is not in the built set",
                )
            selected = tuple(by_id[cid] for cid in _REPRESENTATIVE_CASE_IDS)
            self.assertEqual(
                6, len({case.case_id for case in selected})
            )

            paths = {}
            for case in selected:
                path = sql_dir / case.sql_filename
                path.write_text(
                    render_alter_group_factor_case(case, Path(".")),
                    encoding="utf-8",
                )
                paths[case.case_id] = path

            runner = AlterGroupPg18Runner()
            runner.verify_server()
            run_01 = runner.run_cases(selected, paths, run_ordinal=1)
            run_02 = runner.run_cases(selected, paths, run_ordinal=2)
            comparison = compare_alter_group_runs(run_01, run_02)

        self.assertTrue(comparison.passed, comparison.issues)
        self.assertEqual(12, comparison.execution_count)
        self.assertEqual((), comparison.transcript_mismatch_case_ids)
        self.assertEqual((), comparison.cleanup_failure_case_ids)
        self.assertEqual((), comparison.sqlstate_mismatch_case_ids)
        self.assertEqual((), comparison.execution_failure_case_ids)


if __name__ == "__main__":
    unittest.main()
