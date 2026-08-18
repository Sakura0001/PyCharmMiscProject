from __future__ import annotations

import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from pg_case_factory.coverage_v2.artifacts import build_artifact
from pg_case_factory.coverage_v2.errors import CoverageV2RevisionError
from pg_case_factory.coverage_v2.revisions import RevisionStore
from pg_case_factory.coverage_v2.schema_registry import ArtifactSchemaRegistry


RUN_ID = "fscr-pg18_4-0123456789abcdef"


def _pointer(revision_id: str) -> dict[str, object]:
    return build_artifact(
        artifact_id="CURRENT-abort",
        kind="current-pointer",
        semantic_payload={
            "run_id": RUN_ID,
            "statement_key": "abort",
            "revision_id": revision_id,
            "plan_content_root_sha256": None,
            "validated_plan_root_sha256": None,
            "active_global_revision_id": None,
            "approval_semantic_sha256": None,
            "generation_contract_root_sha256": None,
            "planning_state": "inputs_locked",
            "runtime_state": "not_run",
            "origin": "native_v2",
            "failure_state": None,
        },
        predecessors=(),
    )


class RevisionStoreTest(unittest.TestCase):
    def test_allocates_monotonic_ids_and_publishes_exactly_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = RevisionStore(Path(directory), run_id=RUN_ID, statement_key="abort")
            first = store.allocate_revision_id()
            second = store.allocate_revision_id()
            self.assertEqual(("r0001", "r0002"), (first, second))
            staging = store.create_staging(first)
            staging.joinpath("plan-validation.json").write_bytes(b"validated\n")
            published = store.publish_revision(first)
            self.assertEqual(
                store.statement_root.joinpath("plan-revisions", first),
                published,
            )
            self.assertTrue(published.joinpath("plan-validation.json").is_file())
            self.assertFalse(staging.exists())
            with self.assertRaises(CoverageV2RevisionError):
                store.publish_revision(first)

    def test_concurrent_allocations_are_unique_and_contiguous(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = RevisionStore(Path(directory), run_id=RUN_ID, statement_key="abort")
            with ThreadPoolExecutor(max_workers=8) as pool:
                values = list(pool.map(lambda _: store.allocate_revision_id(), range(24)))
            self.assertEqual(24, len(set(values)))
            self.assertEqual(
                [f"r{index:04d}" for index in range(1, 25)],
                sorted(values),
            )

    def test_current_pointer_is_atomic_current_and_revalidated_on_read(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = RevisionStore(root, run_id=RUN_ID, statement_key="abort")
            revision_id = store.allocate_revision_id()
            store.create_staging(revision_id).joinpath("input-lock.json").write_text(
                "locked\n", encoding="utf-8"
            )
            store.publish_revision(revision_id)
            document = _pointer(revision_id)
            store.write_current(document)
            current = store.read_current(ArtifactSchemaRegistry.load_packaged())
            self.assertEqual(document, current)
            self.assertFalse(any(store.statement_root.glob(".current.json.*.tmp")))

            changed = json.loads(store.current_path.read_text(encoding="utf-8"))
            changed["semantic_payload"]["planning_state"] = "packaged"
            store.current_path.write_text(json.dumps(changed), encoding="utf-8")
            with self.assertRaises(CoverageV2RevisionError):
                store.read_current(ArtifactSchemaRegistry.load_packaged())

    def test_pointer_to_missing_or_wrong_statement_revision_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = RevisionStore(Path(directory), run_id=RUN_ID, statement_key="abort")
            with self.assertRaises(CoverageV2RevisionError):
                store.write_current(_pointer("r0001"))

            revision_id = store.allocate_revision_id()
            store.publish_revision(revision_id)
            wrong_statement = _pointer(revision_id)
            wrong_statement["semantic_payload"]["statement_key"] = "commit"
            with self.assertRaises(CoverageV2RevisionError):
                store.write_current(wrong_statement)


if __name__ == "__main__":
    unittest.main()
