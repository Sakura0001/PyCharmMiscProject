from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from mysql_case_factory.artifact_store import (
    load_run_manifest,
    prepare_artifacts,
    prepare_run,
)


class ArtifactRunStoreTest(unittest.TestCase):
    def test_prepare_run_creates_scoped_layout_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            paths = prepare_run(
                runtime_root=root,
                run_id="feature-a-001",
                metadata={"target_version": "18.4", "git_sha": "abc123"},
                created_at="2026-07-12T00:00:00Z",
            )

            self.assertEqual(paths["run_root"], root / "artifacts" / "runs" / "feature-a-001")
            self.assertTrue(paths["reference_executions"].is_dir())
            self.assertTrue(paths["dut_executions"].is_dir())
            self.assertTrue(paths["regression_sql"].is_dir())
            manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
            self.assertEqual(manifest["run_id"], "feature-a-001")
            self.assertEqual(manifest["metadata"]["target_version"], "18.4")
            self.assertIsNone(manifest["metadata"]["execution_profile_sha256"])

    def test_run_manifest_cannot_downgrade_by_deleting_profile_binding_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_root = prepare_run(Path(tmp), "explicit-profile-null")["run_root"]
            manifest_path = run_root / "run.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertIn("execution_profile_sha256", manifest["metadata"])
            del manifest["metadata"]["execution_profile_sha256"]
            manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "explicitly present"):
                load_run_manifest(run_root)

    def test_prepare_run_refuses_path_traversal_and_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ValueError):
                prepare_run(root, "../escape")

            prepare_run(root, "stable-run")
            with self.assertRaises(FileExistsError):
                prepare_run(root, "stable-run")

            resumed = prepare_run(root, "stable-run", resume=True)
            self.assertTrue(resumed["manifest"].is_file())

    def test_legacy_prepare_artifacts_no_longer_clears_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sentinel = root / "artifacts" / "keep.txt"
            sentinel.parent.mkdir(parents=True)
            sentinel.write_text("keep", encoding="utf-8")

            prepare_artifacts(root)

            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_artifact_parent_symlinks_cannot_redirect_writes_or_clear_external_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside_tmp:
            root = Path(tmp)
            outside = Path(outside_tmp)
            sentinel = outside / "sentinel.txt"
            sentinel.write_text("keep", encoding="utf-8")
            (root / "artifacts").symlink_to(outside, target_is_directory=True)

            with self.assertRaisesRegex(ValueError, "symbolic link"):
                prepare_run(root, "redirected-run")
            with self.assertRaisesRegex(ValueError, "symbolic link"):
                prepare_artifacts(root, clear=True)
            self.assertEqual("keep", sentinel.read_text(encoding="utf-8"))
            self.assertFalse((outside / "runs").exists())

    def test_clear_refuses_nested_symlinks_before_deleting_anything(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside_tmp:
            root = Path(tmp)
            artifacts = root / "artifacts"
            artifacts.mkdir()
            local_sentinel = artifacts / "local.txt"
            local_sentinel.write_text("local", encoding="utf-8")
            outside_sentinel = Path(outside_tmp) / "outside.txt"
            outside_sentinel.write_text("outside", encoding="utf-8")
            (artifacts / "redirect").symlink_to(
                Path(outside_tmp),
                target_is_directory=True,
            )

            with self.assertRaisesRegex(ValueError, "containing symbolic links"):
                prepare_artifacts(root, clear=True)
            self.assertEqual("local", local_sentinel.read_text(encoding="utf-8"))
            self.assertEqual("outside", outside_sentinel.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
