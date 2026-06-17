import hashlib
import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from largeslb_fuzz import (
    Dsn,
    FIELD_SPECS,
    OperationPlan,
    OracleState,
    PayloadFactory,
    ReplicaVisibility,
    RowBefore,
    ScenarioGenerator,
    TransactionNotCommitted,
    classify_replica_visibility,
    is_retryable_txn_error,
    normalize_variable_rows,
)


class DsnTests(unittest.TestCase):
    def test_parse_mysql_url_and_redact_password(self):
        dsn = Dsn.parse("mysql://tester:p%40ss@127.0.0.1:3307/lslb?charset=utf8mb4")

        self.assertEqual(dsn.user, "tester")
        self.assertEqual(dsn.password, "p@ss")
        self.assertEqual(dsn.host, "127.0.0.1")
        self.assertEqual(dsn.port, 3307)
        self.assertEqual(dsn.database, "lslb")
        self.assertEqual(dsn.charset, "utf8mb4")
        self.assertNotIn("p@ss", dsn.redacted())
        self.assertIn("***", dsn.redacted())


class PayloadFactoryTests(unittest.TestCase):
    def test_payload_is_deterministic_and_exact_length(self):
        factory = PayloadFactory(seed=42)

        payload_a, sha_a = factory.make("op-1", 4096, salt="round-0")
        payload_b, sha_b = factory.make("op-1", 4096, salt="round-0")
        payload_c, sha_c = factory.make("op-1", 4096, salt="round-1")

        self.assertEqual(payload_a, payload_b)
        self.assertEqual(sha_a, sha_b)
        self.assertNotEqual(payload_a, payload_c)
        self.assertNotEqual(sha_a, sha_c)
        self.assertEqual(len(payload_a.encode("utf-8")), 4096)
        self.assertEqual(sha_a, hashlib.sha256(payload_a.encode("utf-8")).hexdigest())

    def test_binary_payload_is_deterministic_and_exact_length(self):
        factory = PayloadFactory(seed=42)

        payload, sha = factory.make_bytes("op-blob", 65536, salt="blob")

        self.assertIsInstance(payload, bytes)
        self.assertEqual(len(payload), 65536)
        self.assertEqual(sha, hashlib.sha256(payload).hexdigest())


class ScenarioGeneratorTests(unittest.TestCase):
    def test_generator_includes_large_cases_but_excludes_single_redo_over_2mb(self):
        rng = random.Random(7)
        generator = ScenarioGenerator(seed=7, bucket_count=16, rng=rng)

        plans = [generator.next_plan(worker_id=2, sequence=i) for i in range(300)]

        self.assertTrue(any(plan.total_payload_bytes > 2 * 1024 * 1024 for plan in plans))
        self.assertTrue(any(plan.kind == "small_fast_path" for plan in plans))
        self.assertTrue(any(plan.kind == "same_page_hot" for plan in plans))
        self.assertTrue(all(plan.payload_len < 2 * 1024 * 1024 for plan in plans))
        self.assertTrue(all(not plan.unsupported_single_redo for plan in plans))

    def test_generator_uses_session_prefix_to_avoid_op_id_reuse(self):
        generator = ScenarioGenerator(
            seed=7,
            bucket_count=16,
            rng=random.Random(7),
            op_prefix="run-7-session-a",
        )

        plan = generator.next_plan(worker_id=1, sequence=1)

        self.assertTrue(plan.op_id.startswith("run-7-session-a-w1-000000000001-"))

    def test_generator_covers_char_varchar_text_and_blob_targets(self):
        generator = ScenarioGenerator(seed=11, bucket_count=16, rng=random.Random(11))
        plans = [generator.next_plan(worker_id=0, sequence=i) for i in range(2000)]
        targets = {plan.target_field for plan in plans}

        self.assertTrue({"char_255", "varchar_16383"}.issubset(targets))
        self.assertTrue({"text_col", "mediumtext_col", "longtext_col"}.issubset(targets))
        self.assertTrue({"blob_col", "mediumblob_col", "longblob_col"}.issubset(targets))
        self.assertTrue(all(plan.payload_len <= FIELD_SPECS[plan.target_field].safe_max_len for plan in plans))
        self.assertTrue(all(not plan.unsupported_single_redo for plan in plans))


class OracleStateTests(unittest.TestCase):
    def test_apply_commit_tracks_final_state_for_repeated_updates(self):
        oracle = OracleState()
        plan = OperationPlan(
            op_id="run-1-w0-000001",
            kind="same_page_hot",
            worker_id=0,
            sequence=1,
            buckets=[3],
            rows_per_bucket=1,
            payload_len=32768,
            repeat_updates=5,
            checkpoint=False,
            target_field="longtext_col",
        )
        rows = [RowBefore(row_id=100, bucket=3, version=9)]

        oracle.apply_commit(
            plan=plan,
            rows=rows,
            final_payload_sha="abc123",
            final_payload_len=32768,
        )

        expected = oracle.expected_for_rows([100])
        self.assertEqual(expected[100].version, 14)
        self.assertEqual(expected[100].last_op_id, "run-1-w0-000001")
        self.assertEqual(expected[100].payload_sha, "abc123")
        self.assertEqual(expected[100].payload_len, 32768)
        self.assertEqual(expected[100].target_field, "longtext_col")


class ReplicaVisibilityTests(unittest.TestCase):
    def test_classifies_lag_consistency_and_half_visibility(self):
        self.assertEqual(
            classify_replica_visibility(checkpoint_visible=0, visible_rows=0, expected_rows=10),
            ReplicaVisibility.LAGGING,
        )
        self.assertEqual(
            classify_replica_visibility(checkpoint_visible=1, visible_rows=10, expected_rows=10),
            ReplicaVisibility.CONSISTENT,
        )
        self.assertEqual(
            classify_replica_visibility(checkpoint_visible=0, visible_rows=1, expected_rows=10),
            ReplicaVisibility.HALF_VISIBLE,
        )
        self.assertEqual(
            classify_replica_visibility(checkpoint_visible=1, visible_rows=9, expected_rows=10),
            ReplicaVisibility.HALF_VISIBLE,
        )


class TransactionClassificationTests(unittest.TestCase):
    def test_retryable_mysql_errors_are_classified_as_non_corruption_noise(self):
        self.assertTrue(is_retryable_txn_error(Exception(1213, "deadlock found")))
        self.assertTrue(is_retryable_txn_error(Exception(1205, "lock wait timeout exceeded")))
        self.assertFalse(is_retryable_txn_error(Exception(1062, "duplicate key")))

    def test_transaction_not_committed_carries_reason_without_being_data_failure(self):
        exc = TransactionNotCommitted("op-1", "rolled back after disconnect")

        self.assertEqual(exc.op_id, "op-1")
        self.assertIn("rolled back", str(exc))


class MetricNormalizationTests(unittest.TestCase):
    def test_normalizes_mysql_variable_rows_case_insensitively(self):
        rows = [
            {"Variable_name": "large_mtr", "Value": "7"},
            {"VARIABLE_NAME": "large_mtr_size", "VARIABLE_VALUE": "2097153"},
        ]

        self.assertEqual(
            normalize_variable_rows(rows),
            {"large_mtr": "7", "large_mtr_size": "2097153"},
        )


if __name__ == "__main__":
    unittest.main()
