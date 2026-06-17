import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from largeslb_console import (
    FuzzLaunchConfig,
    LogBuffer,
    build_fuzz_command,
    collect_failures,
    summarize_failure,
)


class CommandBuilderTests(unittest.TestCase):
    def test_from_dict_preserves_boolean_checkbox_values(self):
        config = FuzzLaunchConfig.from_dict(
            {
                "primary_dsn": "mysql://u:p@127.0.0.1:3306/db",
                "readonly_dsn": "mysql://u:p@127.0.0.2:3306/db",
                "state_dir": "/tmp/lslb-console",
                "verbose": False,
                "init_only": True,
            }
        )

        self.assertIs(config.verbose, False)
        self.assertIs(config.init_only, True)

    def test_builds_fuzz_command_and_redacts_password(self):
        config = FuzzLaunchConfig(
            primary_dsn="mysql://tester:p%40ss@127.0.0.1:3306/lslb",
            readonly_dsn="mysql://ro:secret@127.0.0.2:3306/lslb",
            state_dir="/tmp/lslb-console",
            seed="20260525",
            workers="4",
            duration="72h",
            run_id="run-a",
            bucket_count="16",
            rows_per_bucket="2048",
            target_fields="char_255,longblob_col",
            readonly_check_rate="0.1",
            replica_timeout="300",
            replica_poll_interval="1",
            update_chunk_size="256",
            query_chunk_size="512",
            sleep_ms="10",
            engine_metric_interval="30",
            verbose=True,
            init_only=False,
        )

        command, redacted = build_fuzz_command(Path("/opt/largeslb_fuzz.py"), config)

        self.assertEqual(command[:2], ["python3", "-u"])
        self.assertIn("--primary-dsn", command)
        self.assertIn("mysql://tester:p%40ss@127.0.0.1:3306/lslb", command)
        self.assertIn("--verbose", command)
        self.assertIn("--target-fields", command)
        self.assertIn("char_255,longblob_col", command)
        self.assertIn("--engine-metric-interval", command)
        self.assertIn("30", command)
        self.assertNotIn("p@ss", " ".join(redacted))
        self.assertNotIn("secret", " ".join(redacted))
        self.assertIn("***", " ".join(redacted))


class FailureSummaryTests(unittest.TestCase):
    def test_summarizes_where_the_failure_happened(self):
        failure = {
            "kind": "primary_oracle_mismatch",
            "message": "primary row differs from Python oracle",
            "plan": {
                "op_id": "op-123",
                "kind": "same_page_hot",
                "target_field": "longblob_col",
                "payload_len": 1048576,
            },
            "details": {
                "row_id": 42,
                "mismatches": {
                    "payload_sha": {
                        "expected": "aaa",
                        "actual": "bbb",
                    }
                },
            },
            "extra": {
                "selected_rows": [{"row_id": 42, "bucket": 3, "version": 9}],
            },
        }

        summary = summarize_failure(Path("/tmp/failures/f1"), failure)

        self.assertEqual(summary["kind"], "primary_oracle_mismatch")
        self.assertEqual(summary["op_id"], "op-123")
        self.assertEqual(summary["scenario"], "same_page_hot")
        self.assertIn("row_id=42", summary["where"])
        self.assertIn("payload_sha", summary["where"])
        self.assertIn("target_field=longblob_col", summary["where"])
        self.assertIn("payload_len=1048576", summary["where"])

    def test_collect_failures_reads_newest_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "failures"
            first = root / "20260525T010101000000Z_primary"
            second = root / "20260525T020202000000Z_readonly"
            first.mkdir(parents=True)
            second.mkdir(parents=True)
            (first / "failure.json").write_text(
                json.dumps({"kind": "primary", "message": "first"}),
                encoding="utf-8",
            )
            (second / "failure.json").write_text(
                json.dumps({"kind": "readonly", "message": "second"}),
                encoding="utf-8",
            )

            failures = collect_failures(Path(tmp), limit=10)

            self.assertEqual([item["kind"] for item in failures], ["readonly", "primary"])


class LogBufferTests(unittest.TestCase):
    def test_marks_error_lines_as_anomalies(self):
        buffer = LogBuffer(limit=5)
        buffer.append("INFO normal line")
        buffer.append("ERROR fuzz failure saved path=/tmp/failure kind=readonly_half_visible")

        snapshot = buffer.snapshot()

        self.assertEqual(snapshot[-1]["level"], "ERROR")
        self.assertTrue(snapshot[-1]["anomaly"])


if __name__ == "__main__":
    unittest.main()
