from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load_tool(name: str):
    script = ROOT / "tools" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FeatureTestLoopToolsTest(unittest.TestCase):
    def write_yaml(self, root: Path, relative_path: str, data: dict) -> Path:
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        return path

    def sample_execution_report(self) -> dict:
        return {
            "schema_version": 1,
            "kind": "feature_execution_report",
            "feature": {"key": "sample_feature"},
            "runner": {"executor": ["fake-psql"]},
            "cases": [
                {
                    "case_id": "success_case",
                    "sql_path": "generated_sql/success.sql",
                    "expected_status": "success",
                    "observed_status": "success",
                    "status": "passed",
                    "exit_code": 0,
                    "stdout": "1 row",
                    "stderr": "",
                    "duration_ms": 3,
                },
                {
                    "case_id": "unexpected_failure",
                    "sql_path": "generated_sql/unexpected_failure.sql",
                    "expected_status": "success",
                    "observed_status": "failure",
                    "status": "failed",
                    "exit_code": 1,
                    "stdout": "",
                    "stderr": "ERROR: duplicate key\nSQLSTATE: 23505",
                    "observed_sqlstate": "23505",
                    "duration_ms": 4,
                },
                {
                    "case_id": "wrong_sqlstate",
                    "sql_path": "generated_sql/wrong_sqlstate.sql",
                    "expected_status": "failure",
                    "expected_sqlstate": "23503",
                    "observed_status": "failure",
                    "observed_sqlstate": "23505",
                    "status": "failed",
                    "exit_code": 1,
                    "stdout": "",
                    "stderr": "ERROR: duplicate key\nSQLSTATE: 23505",
                    "duration_ms": 5,
                },
                {
                    "case_id": "result_mismatch",
                    "sql_path": "generated_sql/result_mismatch.sql",
                    "expected_status": "success",
                    "observed_status": "success",
                    "status": "failed",
                    "exit_code": 0,
                    "stdout": "wrong rows",
                    "stderr": "",
                    "duration_ms": 6,
                    "oracle_result": {"status": "mismatch", "detail": "unordered multiset differs"},
                },
                {
                    "case_id": "plan_mismatch",
                    "sql_path": "generated_sql/plan_mismatch.sql",
                    "expected_status": "success",
                    "observed_status": "success",
                    "status": "failed",
                    "exit_code": 0,
                    "stdout": "rows ok",
                    "stderr": "",
                    "duration_ms": 7,
                    "plan_observation": {"status": "mismatch", "detail": "expected index scan"},
                },
                {
                    "case_id": "cleanup_failure",
                    "sql_path": "generated_sql/cleanup_failure.sql",
                    "expected_status": "success",
                    "observed_status": "success",
                    "status": "failed",
                    "exit_code": 0,
                    "stdout": "rows ok",
                    "stderr": "",
                    "duration_ms": 8,
                    "cleanup_status": "failed",
                },
            ],
        }

    def test_execution_report_audit_accepts_valid_report(self):
        audit = load_tool("audit_execution_report")
        report = self.sample_execution_report()

        result = audit.audit_report(report)

        self.assertTrue(result.passed, result.errors)
        self.assertEqual(result.case_count, 6)

    def test_execution_report_audit_rejects_missing_case_id(self):
        audit = load_tool("audit_execution_report")
        report = self.sample_execution_report()
        del report["cases"][0]["case_id"]

        result = audit.audit_report(report)

        self.assertFalse(result.passed)
        self.assertTrue(any("case_id is required" in error for error in result.errors))

    def test_failure_diagnosis_clusters_execution_results(self):
        diagnose = load_tool("diagnose_execution_failures")
        report = self.sample_execution_report()

        diagnosis = diagnose.diagnose_report(report)
        categories = {cluster["category"] for cluster in diagnosis["clusters"]}

        self.assertIn("unexpected_failure", categories)
        self.assertIn("sqlstate_mismatch", categories)
        self.assertIn("result_mismatch", categories)
        self.assertIn("plan_mismatch", categories)
        self.assertIn("cleanup_failure", categories)
        self.assertEqual(diagnosis["summary"]["failed_cases"], 5)

    def test_promotion_candidates_require_human_review_and_do_not_replace_baseline(self):
        diagnose = load_tool("diagnose_execution_failures")
        promote = load_tool("promote_execution_feedback")
        diagnosis = diagnose.diagnose_report(self.sample_execution_report())

        promotion = promote.build_promotion_candidates(diagnosis)

        self.assertEqual(promotion["kind"], "feedback_promotion_candidates")
        self.assertTrue(promotion["candidates"])
        self.assertTrue(all(candidate["requires_human_review"] for candidate in promotion["candidates"]))
        self.assertTrue(all(candidate["derived_extension"] for candidate in promotion["candidates"]))
        self.assertTrue(all(not candidate["counts_toward_required_baseline"] for candidate in promotion["candidates"]))

    def test_runner_executes_sql_files_with_fake_executor_and_writes_report(self):
        runner = load_tool("run_generated_sql")
        audit = load_tool("audit_execution_report")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sql_dir = root / "generated_sql"
            sql_dir.mkdir()
            (sql_dir / "001_success.sql").write_text(
                "-- case_id: success_case\n-- expected_status: success\nSELECT 1;\n",
                encoding="utf-8",
            )
            (sql_dir / "002_expected_failure.sql").write_text(
                "-- case_id: expected_failure\n-- expected_status: failure\n-- expected_sqlstate: 23505\nSELECT 'FAIL';\n",
                encoding="utf-8",
            )
            fake = root / "fake_psql.py"
            fake.write_text(
                textwrap.dedent(
                    """
                    import pathlib
                    import sys

                    sql = pathlib.Path(sys.argv[-1]).read_text()
                    if "FAIL" in sql:
                        print("ERROR: duplicate key", file=sys.stderr)
                        print("SQLSTATE: 23505", file=sys.stderr)
                        raise SystemExit(1)
                    print("ok")
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            os.chmod(fake, 0o755)

            report = runner.run_sql_directory(
                sql_dir=sql_dir,
                feature_key="runner_feature",
                executor=[sys.executable, str(fake)],
            )

            result = audit.audit_report(report)
            self.assertTrue(result.passed, result.errors)
            statuses = {case["case_id"]: case["status"] for case in report["cases"]}
            self.assertEqual(statuses["success_case"], "passed")
            self.assertEqual(statuses["expected_failure"], "expected_failure_matched")

    def test_audit_execution_report_cli_reports_clean_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_yaml(Path(tmp), "bad_report.yaml", {"kind": "feature_execution_report", "cases": [{}]})
            completed = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "audit_execution_report.py"), "--report", str(path)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("FAIL execution report audit", completed.stdout)
        self.assertNotIn("Traceback", completed.stdout)

    def test_feature_test_loop_runner_writes_iteration_artifacts(self):
        loop = load_tool("run_feature_test_loop")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sql_dir = root / "generated_sql"
            artifacts_dir = root / "evaluations"
            sql_dir.mkdir()
            (sql_dir / "001_success.sql").write_text(
                "-- case_id: success_case\n-- expected_status: success\nSELECT 1;\n",
                encoding="utf-8",
            )
            (sql_dir / "002_unexpected_failure.sql").write_text(
                "-- case_id: unexpected_failure\n-- expected_status: success\nSELECT 'FAIL';\n",
                encoding="utf-8",
            )
            fake = root / "fake_psql.py"
            fake.write_text(
                textwrap.dedent(
                    """
                    import pathlib
                    import sys

                    sql = pathlib.Path(sys.argv[-1]).read_text()
                    if "FAIL" in sql:
                        print("ERROR: duplicate key", file=sys.stderr)
                        print("SQLSTATE: 23505", file=sys.stderr)
                        raise SystemExit(1)
                    print("ok")
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            os.chmod(fake, 0o755)

            loop_report = loop.run_feature_test_loop(
                feature_key="loop_feature",
                sql_dir=sql_dir,
                artifacts_dir=artifacts_dir,
                executor=[sys.executable, str(fake)],
                max_iterations=2,
                stop_on_clean=False,
            )

            self.assertEqual(loop_report["kind"], "feature_test_loop_report")
            self.assertEqual(loop_report["summary"]["iterations"], 2)
            self.assertEqual(loop_report["summary"]["final_status"], "failures_detected")
            self.assertEqual(loop_report["summary"]["total_promotion_candidates"], 2)
            self.assertTrue((artifacts_dir / "loop_feature_iteration_001_execution_report.yaml").exists())
            self.assertTrue((artifacts_dir / "loop_feature_iteration_001_failure_diagnosis.yaml").exists())
            self.assertTrue((artifacts_dir / "loop_feature_iteration_001_promotion_candidates.yaml").exists())
            self.assertTrue((artifacts_dir / "loop_feature_loop_report.yaml").exists())


if __name__ == "__main__":
    unittest.main()
