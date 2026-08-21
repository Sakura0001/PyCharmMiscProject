from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from pg_case_factory.full_sql_runtime import (
    CaseExecution,
    EVIDENCE_COMPATIBILITY,
    EVIDENCE_OBSERVATIONAL,
    EVIDENCE_STRICT,
    RuntimeManifestCase,
    compare_case_runs,
    compile_runtime_manifest,
    evaluate_case_execution,
)


STRICT_SQL = """-- case_id: STRICT0001
-- expected_outcome: success
-- expected_sqlstate: 00000
-- primary-target-begin
SELECT true;
-- primary-target-end
\\echo PGCF_TARGET_SQLSTATE=:SQLSTATE
SELECT :'SQLSTATE' = '00000' AS target_sqlstate_matches_expected;
-- 5. cleanup
"""


class RuntimeManifestTest(unittest.TestCase):
    def test_manifest_uses_sql_files_not_schedules_and_deduplicates_retained(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            current = root / "artifacts/regress/by-factor/ddl/example"
            current.mkdir(parents=True)
            (current / "STRICT0001.sql").write_text(STRICT_SQL)
            (current / "STRICT0002.sql").write_text(
                STRICT_SQL.replace("STRICT0001", "STRICT0002")
            )
            (current / "serial_schedule").write_text("test: STRICT0001\n")
            (current / "external_schedule").write_text("test: STRICT0002\n")

            retained = root / "artifacts/regress/cursor-factor-full-v1/sql"
            retained.mkdir(parents=True)
            legacy = """-- case_id: CUR00001
-- description  : Verify PostgreSQL 18.4 CLOSE with factors
-- factor expected_status=failure
CLOSE missing_cursor;
"""
            (retained / "CUR00001.sql").write_text(legacy)

            progress_path = root / "progress.json"
            progress_path.write_text(
                json.dumps(
                    {
                        "statements": {
                            "example": {
                                "status": "completed",
                                "package_path": str(current.relative_to(root)),
                                "sql_file_count": 2,
                            },
                            "close": {
                                "status": "retained_existing",
                                "package_path": "artifacts/regress/cursor-factor-full-v1",
                            },
                            "declare": {
                                "status": "retained_existing",
                                "package_path": "artifacts/regress/cursor-factor-full-v1",
                            },
                        }
                    }
                )
            )

            manifest = compile_runtime_manifest(root, progress_path)

        self.assertEqual(3, len(manifest))
        by_id = {case.case_id: case for case in manifest}
        self.assertEqual(EVIDENCE_STRICT, by_id["STRICT0001"].evidence_level)
        self.assertFalse(by_id["STRICT0001"].external)
        self.assertTrue(by_id["STRICT0002"].external)
        self.assertEqual(EVIDENCE_OBSERVATIONAL, by_id["CUR00001"].evidence_level)
        self.assertEqual("close", by_id["CUR00001"].statement_key)
        self.assertEqual("expected_failure", by_id["CUR00001"].expected_outcome)

    def test_compatibility_case_is_bound_to_plan_metadata_and_sql_sha(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            package = root / "artifacts/regress/by-factor/ddl/legacy"
            package.mkdir(parents=True)
            sql = """-- case_id: LEGACY0001
-- factor expected_status=failure
SELECT false AS target_sqlstate_matches;
"""
            sql_path = package / "LEGACY0001.sql"
            sql_path.write_text(sql)
            evidence = (
                root
                / "artifacts/intermediates/remaining-statement-factor-cycle/legacy"
            )
            evidence.mkdir(parents=True)
            (evidence / "plan.json").write_text(
                json.dumps(
                    {
                        "cases": [
                            {
                                "case_id": "LEGACY0001",
                                "sql_filename": "LEGACY0001.sql",
                                "object_prefix": "legacy_0001_",
                                "outcome": "expected_failure",
                                "derived_axes": {"expected_sqlstate": "42704"},
                            }
                        ]
                    }
                )
            )
            progress_path = root / "progress.json"
            progress_path.write_text(
                json.dumps(
                    {
                        "statements": {
                            "legacy": {
                                "status": "completed",
                                "package_path": str(package.relative_to(root)),
                                "sql_file_count": 1,
                            }
                        }
                    }
                )
            )

            [case] = compile_runtime_manifest(root, progress_path)

        self.assertEqual(EVIDENCE_COMPATIBILITY, case.evidence_level)
        self.assertEqual("expected_failure", case.expected_outcome)
        self.assertEqual("42704", case.expected_sqlstate)
        self.assertEqual(hashlib.sha256(sql.encode()).hexdigest(), case.sql_sha256)
        self.assertEqual("legacy_0001_", case.object_prefix)


class RuntimeEvaluationTest(unittest.TestCase):
    def manifest_case(
        self,
        *,
        evidence_level: str = EVIDENCE_STRICT,
        expected_outcome: str | None = "success",
        expected_sqlstate: str | None = "00000",
    ) -> RuntimeManifestCase:
        return RuntimeManifestCase(
            ordinal=1,
            statement_key="select",
            case_id="SELECT00001",
            sql_path="sql/SELECT00001.sql",
            sql_sha256="a" * 64,
            package_path="sql",
            evidence_level=evidence_level,
            expected_outcome=expected_outcome,
            expected_sqlstate=expected_sqlstate,
            object_prefix="select_00001_",
            external=False,
        )

    def execution(
        self,
        *,
        stdout: bytes = b"PGCF_TARGET_SQLSTATE=00000\nt\n",
        stderr: bytes = b"",
        exit_code: int = 0,
        timed_out: bool = False,
    ) -> CaseExecution:
        return CaseExecution(
            exit_code=exit_code,
            timed_out=timed_out,
            stdout=stdout,
            stderr=stderr,
            duration_ms=12,
        )

    def test_strict_contract_requires_exact_sqlstate_and_true_oracles(self) -> None:
        passed = evaluate_case_execution(
            self.manifest_case(), self.execution(), run_ordinal=1
        )
        wrong_state = evaluate_case_execution(
            self.manifest_case(),
            self.execution(stdout=b"PGCF_TARGET_SQLSTATE=42P01\nt\n"),
            run_ordinal=1,
        )
        false_oracle = evaluate_case_execution(
            self.manifest_case(),
            self.execution(stdout=b"PGCF_TARGET_SQLSTATE=00000\nf\n"),
            run_ordinal=1,
        )
        missing_state = evaluate_case_execution(
            self.manifest_case(),
            self.execution(stdout=b"t\n"),
            run_ordinal=1,
        )

        self.assertTrue(passed.passed)
        self.assertEqual("strict_pass", passed.classification)
        self.assertEqual("00000", passed.target_sqlstate)
        self.assertEqual("sqlstate_mismatch", wrong_state.classification)
        self.assertEqual("oracle_failure", false_oracle.classification)
        self.assertEqual("missing_target_sqlstate", missing_state.classification)

    def test_timeout_and_nonzero_exit_take_precedence(self) -> None:
        timed_out = evaluate_case_execution(
            self.manifest_case(),
            self.execution(exit_code=124, timed_out=True),
            run_ordinal=1,
        )
        failed = evaluate_case_execution(
            self.manifest_case(), self.execution(exit_code=2), run_ordinal=1
        )
        self.assertEqual("timeout", timed_out.classification)
        self.assertEqual("unexpected_psql_error", failed.classification)

    def test_compatibility_contract_does_not_claim_strict_sqlstate(self) -> None:
        result = evaluate_case_execution(
            self.manifest_case(
                evidence_level=EVIDENCE_COMPATIBILITY,
                expected_outcome="expected_failure",
                expected_sqlstate="42704",
            ),
            self.execution(stdout=b"t\nt\n", stderr=b"ERROR:  42704\n"),
            run_ordinal=1,
        )
        self.assertTrue(result.passed)
        self.assertEqual("compatibility_pass", result.classification)
        self.assertIsNone(result.target_sqlstate)

    def test_observational_failure_remains_not_strictly_judgeable(self) -> None:
        result = evaluate_case_execution(
            self.manifest_case(
                evidence_level=EVIDENCE_OBSERVATIONAL,
                expected_outcome="expected_failure",
                expected_sqlstate=None,
            ),
            self.execution(stdout=b"", stderr=b"ERROR:  34000\n"),
            run_ordinal=1,
        )
        mismatch = evaluate_case_execution(
            self.manifest_case(
                evidence_level=EVIDENCE_OBSERVATIONAL,
                expected_outcome="success",
                expected_sqlstate=None,
            ),
            self.execution(stderr=b"ERROR:  42P01\n"),
            run_ordinal=1,
        )
        self.assertTrue(result.passed)
        self.assertEqual("not_strictly_judgeable", result.classification)
        self.assertFalse(result.strictly_judgeable)
        self.assertEqual("observed_mismatch", mismatch.classification)

    def test_two_run_comparison_detects_normalized_transcript_drift(self) -> None:
        first = evaluate_case_execution(
            self.manifest_case(), self.execution(), run_ordinal=1
        )
        second = evaluate_case_execution(
            self.manifest_case(),
            self.execution(stdout=b"PGCF_TARGET_SQLSTATE=00000\nt\nextra\n"),
            run_ordinal=2,
        )
        comparison = compare_case_runs(first, second)
        self.assertFalse(comparison.passed)
        self.assertEqual("two_run_mismatch", comparison.classification)


if __name__ == "__main__":
    unittest.main()
