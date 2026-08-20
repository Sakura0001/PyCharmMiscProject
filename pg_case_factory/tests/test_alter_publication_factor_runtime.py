from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from pg_case_factory.alter_publication_factor_loop import (
    build_alter_publication_factor_loop_plan,
)
from pg_case_factory.alter_publication_factor_render import (
    render_alter_publication_factor_case,
)
from pg_case_factory.alter_publication_factor_runtime import (
    AlterPublicationCaseRuntimeResult,
    AlterPublicationPg18Runner,
    AlterPublicationSuiteRun,
    build_alter_publication_runtime_case_set,
    compare_alter_publication_runs,
)


ROOT = Path(__file__).resolve().parents[1]
PG18_BIN = Path("/tmp/pgcf-postgresql-18.4-install/bin")
PG18_SOCKET = Path("/tmp/pgcf-pg18-ap-sock-20260820")
_BASELINE_COUNT = 93
_EXTENSION_COUNT = 19923
_TOTAL = _BASELINE_COUNT + _EXTENSION_COUNT  # 20016


def _sample_case(stdout: bytes) -> AlterPublicationCaseRuntimeResult:
    return AlterPublicationCaseRuntimeResult(
        case_id="ALTERPUBLICATION00001",
        sql_filename="ALTERPUBLICATION00001.sql",
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


class AlterPublicationFactorRuntimeTest(unittest.TestCase):
    def test_two_run_result_requires_identical_normalized_transcripts(
        self,
    ) -> None:
        identical = compare_alter_publication_runs(
            AlterPublicationSuiteRun(
                run_ordinal=1, cases=(_sample_case(b"ok\n"),)
            ),
            AlterPublicationSuiteRun(
                run_ordinal=2, cases=(_sample_case(b"ok\n"),)
            ),
        )
        self.assertTrue(identical.passed, identical.issues)

        changed = compare_alter_publication_runs(
            AlterPublicationSuiteRun(
                run_ordinal=1, cases=(_sample_case(b"ok\n"),)
            ),
            AlterPublicationSuiteRun(
                run_ordinal=2,
                cases=(_sample_case(b"different\n"),),
            ),
        )
        self.assertFalse(changed.passed)
        self.assertEqual(
            ("ALTERPUBLICATION00001",),
            changed.transcript_mismatch_case_ids,
        )

    def test_sqlstate_mismatch_is_detected(self) -> None:
        expected = _sample_case(b"ok\n")
        wrong_sqlstate = AlterPublicationCaseRuntimeResult(
            case_id="ALTERPUBLICATION00001",
            sql_filename="ALTERPUBLICATION00001.sql",
            expected_sqlstate="00000",
            target_sqlstate="42501",
            exit_code=0,
            timed_out=False,
            normalized_stdout=b"ok\n",
            normalized_stderr=b"",
            boolean_oracle_failure_count=0,
            pre_clean=True,
            post_clean=True,
            cleanup_exit_code=0,
        )
        comparison = compare_alter_publication_runs(
            AlterPublicationSuiteRun(
                run_ordinal=1, cases=(expected,)
            ),
            AlterPublicationSuiteRun(
                run_ordinal=2, cases=(wrong_sqlstate,)
            ),
        )
        self.assertFalse(comparison.passed)
        self.assertEqual(
            ("ALTERPUBLICATION00001",),
            comparison.sqlstate_mismatch_case_ids,
        )

    def test_cleanup_failure_is_detected(self) -> None:
        clean = _sample_case(b"ok\n")
        dirty = AlterPublicationCaseRuntimeResult(
            case_id="ALTERPUBLICATION00001",
            sql_filename="ALTERPUBLICATION00001.sql",
            expected_sqlstate="00000",
            target_sqlstate="00000",
            exit_code=0,
            timed_out=False,
            normalized_stdout=b"ok\n",
            normalized_stderr=b"",
            boolean_oracle_failure_count=0,
            pre_clean=True,
            post_clean=False,
            cleanup_exit_code=1,
        )
        comparison = compare_alter_publication_runs(
            AlterPublicationSuiteRun(
                run_ordinal=1, cases=(clean,)
            ),
            AlterPublicationSuiteRun(
                run_ordinal=2, cases=(dirty,)
            ),
        )
        self.assertFalse(comparison.passed)
        self.assertEqual(
            ("ALTERPUBLICATION00001",),
            comparison.cleanup_failure_case_ids,
        )

    def test_runtime_case_set_combines_baseline_and_extension(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sql_dir = Path(temporary)
            cases, sql_paths = build_alter_publication_runtime_case_set(
                ROOT, sql_dir
            )
            self.assertEqual(_TOTAL, len(cases))
            ordinals = [getattr(case, "ordinal") for case in cases]
            self.assertEqual(
                list(range(1, _TOTAL + 1)),
                ordinals,
                "ordinals must form a contiguous 1..19551 sequence",
            )
            self.assertEqual(1, ordinals[0])
            self.assertEqual(_TOTAL, ordinals[-1])
            self.assertFalse(getattr(cases[0], "is_extension", False))
            self.assertTrue(getattr(cases[-1], "is_extension", False))
            self.assertEqual(len(cases), len(sql_paths))
            case_ids = {case.case_id for case in cases}
            self.assertEqual(case_ids, set(sql_paths))
            for case in cases:
                path = sql_paths[case.case_id]
                self.assertEqual(sql_dir / case.sql_filename, path)
                self.assertEqual(case.sql_filename, path.name)

    def test_runner_timeout_bounds_are_enforced(self) -> None:
        with self.assertRaises(Exception):
            AlterPublicationPg18Runner(timeout_seconds=0)
        with self.assertRaises(Exception):
            AlterPublicationPg18Runner(timeout_seconds=301)

    def test_suite_run_rejects_invalid_ordinal(self) -> None:
        with self.assertRaises(Exception):
            AlterPublicationSuiteRun(run_ordinal=0, cases=())
        with self.assertRaises(Exception):
            AlterPublicationSuiteRun(run_ordinal=3, cases=())

    @unittest.skipUnless(
        (PG18_BIN / "psql").is_file() and PG18_SOCKET.is_dir(),
        "local PostgreSQL 18.4 fixture is unavailable",
    )
    def test_six_representative_cases_execute_twice_on_pg18_4(self) -> None:
        plan = build_alter_publication_factor_loop_plan(ROOT)

        def one(predicate):
            return next(case for case in plan.cases if predicate(case))

        selected = (
            plan.cases[0],
            one(lambda case: case.outcome == "expected_failure"),
            one(
                lambda case: case.factor_key == "publication_state"
                and case.factor_value == "exists_as_for_all_tables"
            ),
            one(
                lambda case: case.factor_key == "executor_privilege"
                and case.factor_value == "non_owner_no_privilege"
            ),
            one(
                lambda case: case.kind == "RISK"
                and case.factor_value == "rollback"
            ),
            one(
                lambda case: case.factor_key == "new_name_shape"
                and case.factor_value == "existing_name_conflict"
            ),
        )
        self.assertEqual(6, len({case.case_id for case in selected}))

        with tempfile.TemporaryDirectory() as temporary:
            sql_dir = Path(temporary)
            paths = {}
            for case in selected:
                path = sql_dir / case.sql_filename
                path.write_text(
                    render_alter_publication_factor_case(case, ROOT),
                    encoding="utf-8",
                )
                paths[case.case_id] = path

            runner = AlterPublicationPg18Runner()
            runner.verify_server()
            run_01 = runner.run_cases(selected, paths, run_ordinal=1)
            run_02 = runner.run_cases(selected, paths, run_ordinal=2)
            comparison = compare_alter_publication_runs(run_01, run_02)

        self.assertTrue(comparison.passed, comparison.issues)
        self.assertEqual(12, comparison.execution_count)
        self.assertEqual((), comparison.transcript_mismatch_case_ids)
        self.assertEqual((), comparison.cleanup_failure_case_ids)
        self.assertEqual((), comparison.sqlstate_mismatch_case_ids)


if __name__ == "__main__":
    unittest.main()
