import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from largeslb_fuzz_extreme import (
    TWO_MB,
    ScenarioGenerator,
    burst_row_offset,
)


class Sub2MBurstScenarioTests(unittest.TestCase):
    def test_burst_plans_stay_under_2mb_and_target_one_bucket(self):
        generator = ScenarioGenerator(
            seed=17,
            bucket_count=8,
            rng=random.Random(17),
            target_fields=("longtext_col",),
            sub2m_concurrent_burst=True,
            sub2m_target_bytes=1835008,
        )

        plans = [generator.next_plan(worker_id=i, sequence=1) for i in range(8)]

        self.assertTrue(all(plan.kind == "sub2m_concurrent_burst" for plan in plans))
        self.assertTrue(all(plan.buckets == [0] for plan in plans))
        self.assertTrue(all(plan.repeat_updates == 1 for plan in plans))
        self.assertTrue(all(1572864 <= plan.total_payload_bytes < TWO_MB for plan in plans))
        self.assertTrue(all(not plan.unsupported_single_redo for plan in plans))

    def test_burst_row_offsets_are_disjoint_for_same_sequence(self):
        generator = ScenarioGenerator(
            seed=23,
            bucket_count=1,
            rng=random.Random(23),
            target_fields=("longtext_col",),
            sub2m_concurrent_burst=True,
            sub2m_target_bytes=1835008,
        )
        plans = [generator.next_plan(worker_id=i, sequence=3) for i in range(4)]

        ranges = [
            set(range(burst_row_offset(plan, bucket_row_count=1000, worker_count=4),
                      burst_row_offset(plan, bucket_row_count=1000, worker_count=4) + plan.rows_per_bucket))
            for plan in plans
        ]

        for index, current in enumerate(ranges):
            others = set().union(*(item for pos, item in enumerate(ranges) if pos != index))
            self.assertFalse(current & others)

    def test_burst_requires_non_binary_target_field(self):
        with self.assertRaises(ValueError):
            ScenarioGenerator(
                seed=31,
                bucket_count=1,
                rng=random.Random(31),
                target_fields=("longblob_col",),
                sub2m_concurrent_burst=True,
            )


if __name__ == "__main__":
    unittest.main()
