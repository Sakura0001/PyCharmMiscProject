from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from pg_case_factory.alter_language_factor_loop import (
    build_alter_language_factor_loop_plan,
)
from pg_case_factory.alter_language_factor_render import (
    render_alter_language_factor_case,
)
from pg_case_factory.alter_language_factor_runtime import (
    AlterLanguageCaseRuntimeResult,
    AlterLanguagePg18Runner,
    AlterLanguageSuiteRun,
    PG18_BIN,
    PG18_SOCKET,
    build_alter_language_runtime_case_set,
    compare_alter_language_runs,
)


ROOT = Path(__file__).resolve().parents[1]
_BASELINE_COUNT = 42
_EXTENSION_COUNT = 600
_TOTAL = _BASELINE_COUNT + _EXTENSION_COUNT


def _sample_case(stdout: bytes) -> AlterLanguageCaseRuntimeResult:
    return AlterLanguageCaseRuntimeResult(
        case_id="ALTERLANGUAGE00001",
        sql_filename="ALTERLANGUAGE00001.sql",
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


class AlterLanguageFactorRuntimeTest(unittest.TestCase):
    def test_two_run_result_requires_identical_normalized_transcripts(self) -> None:
        identical = compare_alter_language_runs(
            AlterLanguageSuiteRun(run_ordinal=1, cases=(_sample_case(b"ok\n"),)),
            AlterLanguageSuiteRun(run_ordinal=2, cases=(_sample_case(b"ok\n"),)),
        )
        self.assertTrue(identical.passed, identical.issues)

        changed = compare_alter_language_runs(
            AlterLanguageSuiteRun(run_ordinal=1, cases=(_sample_case(b"ok\n"),)),
            AlterLanguageSuiteRun(
                run_ordinal=2,
                cases=(_sample_case(b"different\n"),),
            ),
        )
        self.assertFalse(changed.passed)
        self.assertEqual(
            ("ALTERLANGUAGE00001",),
            changed.transcript_mismatch_case_ids,
        )

    def test_runtime_case_set_combines_baseline_and_extension(self) -> None:
        # The case-set combiner must merge the frozen 42-case baseline with
        # the bounded 600-case extension into a single ordinal-sorted
        # sequence and map every case to its SQL file path.  This is a pure
        # structural contract (no cluster, no SQL files required on disk).
        with tempfile.TemporaryDirectory() as temporary:
            sql_dir = Path(temporary)
            cases, sql_paths = build_alter_language_runtime_case_set(
                ROOT, sql_dir
            )
            self.assertEqual(_TOTAL, len(cases))
            ordinals = [getattr(case, "ordinal") for case in cases]
            self.assertEqual(
                list(range(1, _TOTAL + 1)),
                ordinals,
                "ordinals must form a contiguous 1..642 sequence",
            )
            self.assertEqual(1, ordinals[0])
            self.assertEqual(_TOTAL, ordinals[-1])
            # baseline (ordinal 1) is not an extension; last (642) is.
            self.assertFalse(getattr(cases[0], "is_extension", False))
            self.assertTrue(getattr(cases[-1], "is_extension", False))
            self.assertEqual(len(cases), len(sql_paths))
            case_ids = {case.case_id for case in cases}
            self.assertEqual(case_ids, set(sql_paths))
            for case in cases:
                path = sql_paths[case.case_id]
                self.assertEqual(sql_dir / case.sql_filename, path)
                self.assertEqual(case.sql_filename, path.name)

    @unittest.skipUnless(
        (PG18_BIN / "psql").is_file() and PG18_SOCKET.is_dir(),
        "local PostgreSQL 18.4 fixture is unavailable",
    )
    def test_six_representative_cases_execute_twice_on_pg18_4(self) -> None:
        plan = build_alter_language_factor_loop_plan(ROOT)

        def one(predicate):
            return next(case for case in plan.cases if predicate(case))

        selected = (
            plan.cases[0],
            one(lambda case: case.outcome == "expected_failure"),
            one(
                lambda case: case.factor_key == "target_object_state"
                and case.factor_value == "missing"
            ),
            one(
                lambda case: case.factor_key == "privilege_context"
                and case.factor_value == "non_owner"
            ),
            one(
                lambda case: case.kind == "RISK"
                and case.factor_value == "rollback"
            ),
            one(
                lambda case: case.factor_key == "rename_conflict"
                and case.factor_value == "new_name_conflict"
            ),
        )
        self.assertEqual(6, len({case.case_id for case in selected}))

        with tempfile.TemporaryDirectory() as temporary:
            sql_dir = Path(temporary)
            paths = {}
            for case in selected:
                path = sql_dir / case.sql_filename
                path.write_text(
                    render_alter_language_factor_case(case, ROOT),
                    encoding="utf-8",
                )
                paths[case.case_id] = path

            runner = AlterLanguagePg18Runner()
            runner.verify_server()
            run_01 = runner.run_cases(selected, paths, run_ordinal=1)
            run_02 = runner.run_cases(selected, paths, run_ordinal=2)
            comparison = compare_alter_language_runs(run_01, run_02)

        self.assertTrue(comparison.passed, comparison.issues)
        self.assertEqual(12, comparison.execution_count)
        self.assertEqual((), comparison.transcript_mismatch_case_ids)
        self.assertEqual((), comparison.cleanup_failure_case_ids)
        self.assertEqual((), comparison.sqlstate_mismatch_case_ids)


if __name__ == "__main__":
    unittest.main()
