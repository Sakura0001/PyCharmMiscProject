from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pg_case_factory.coverage_v2.artifacts import artifact_bytes
from pg_case_factory.coverage_v2.errors import CoverageV2InputLockError
from pg_case_factory.coverage_v2.input_lock import (
    InputSpec,
    assert_run_id_available,
    freeze_input_lock,
    global_input_root,
    run_id_for_global_input_lock,
    verify_input_lock,
)
from pg_case_factory.coverage_v2.schema_registry import ArtifactSchemaRegistry


class InputLockTest(unittest.TestCase):
    def _write_inputs(self, root: Path) -> tuple[InputSpec, ...]:
        root.joinpath("z.json").write_text('{"b":2,"a":1}\n', encoding="utf-8")
        root.joinpath("a.yaml").write_text("name: abort\ncount: 1\n", encoding="utf-8")
        root.joinpath("m.txt").write_text("PostgreSQL 18.4\n", encoding="utf-8")
        return (
            InputSpec("z.json", "json-contract-v1", "json-v1"),
            InputSpec("a.yaml", "statement-catalog-v1", "yaml-v1"),
            InputSpec("m.txt", "official-source-v1", "utf8-text-v1"),
        )

    def test_freeze_verify_order_root_and_run_id_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            specs = self._write_inputs(root)
            document = freeze_input_lock(root, scope="global", input_specs=specs)
            ArtifactSchemaRegistry.load_packaged().validate(document)
            payload = document["semantic_payload"]
            self.assertEqual(
                ["a.yaml", "m.txt", "z.json"],
                [row["relative_path"] for row in payload["inputs"]],
            )
            self.assertEqual(3, payload["input_count"])
            self.assertNotIn("input_root_sha256", payload)
            self.assertEqual(document["semantic_sha256"], global_input_root(document))
            self.assertEqual(
                f"fscr-pg18_4-{document['semantic_sha256'][:16]}",
                run_id_for_global_input_lock(document),
            )
            first = verify_input_lock(root, document)
            second_document = freeze_input_lock(
                root, scope="global", input_specs=tuple(reversed(specs))
            )
            second = verify_input_lock(root, second_document)
            self.assertEqual(document, second_document)
            self.assertEqual(first, second)

    def test_current_byte_drift_and_input_spec_tampering_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            specs = self._write_inputs(root)
            document = freeze_input_lock(root, scope="global", input_specs=specs)
            root.joinpath("a.yaml").write_text("name: changed\ncount: 1\n", encoding="utf-8")
            with self.assertRaisesRegex(CoverageV2InputLockError, "current bytes"):
                verify_input_lock(root, document)

            restored = freeze_input_lock(root, scope="global", input_specs=specs)
            restored["semantic_payload"]["inputs"][0]["version"] = "tampered"
            with self.assertRaises(CoverageV2InputLockError):
                verify_input_lock(root, restored)

    def test_duplicate_keys_unsafe_paths_symlinks_and_invalid_utf8_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            invalid: list[tuple[str, bytes, str]] = [
                ("duplicate.yaml", b"a: 1\na: 2\n", "yaml-v1"),
                ("duplicate.json", b'{"a":1,"a":2}', "json-v1"),
                ("invalid.txt", b"\xff", "utf8-text-v1"),
            ]
            for name, raw, decoder in invalid:
                with self.subTest(name=name):
                    root.joinpath(name).write_bytes(raw)
                    with self.assertRaises(CoverageV2InputLockError):
                        freeze_input_lock(
                            root,
                            scope="local",
                            input_specs=(InputSpec(name, "v1", decoder),),  # type: ignore[arg-type]
                        )

            root.joinpath("target.yaml").write_text("a: 1\n", encoding="utf-8")
            root.joinpath("link.yaml").symlink_to(root.joinpath("target.yaml"))
            for path in ("link.yaml", "../outside.yaml", "/tmp/outside.yaml"):
                with self.subTest(path=path):
                    with self.assertRaises(CoverageV2InputLockError):
                        freeze_input_lock(
                            root,
                            scope="local",
                            input_specs=(InputSpec(path, "v1", "yaml-v1"),),
                        )

    def test_run_id_prefix_collision_fails_closed_and_same_root_is_reusable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            specs = self._write_inputs(root)
            document = freeze_input_lock(root, scope="global", input_specs=specs)
            run_id = run_id_for_global_input_lock(document)
            runs_root = root.joinpath("runs")
            lock_path = runs_root.joinpath(run_id, "global", "global-input-lock.json")
            lock_path.parent.mkdir(parents=True)
            lock_path.write_bytes(artifact_bytes(document))
            assert_run_id_available(runs_root, run_id, global_input_root(document))

            root.joinpath("a.yaml").write_text("name: collision\ncount: 2\n", encoding="utf-8")
            collision = freeze_input_lock(root, scope="global", input_specs=specs)
            lock_path.write_bytes(artifact_bytes(collision))
            with self.assertRaisesRegex(CoverageV2InputLockError, "collision"):
                assert_run_id_available(
                    runs_root,
                    run_id,
                    global_input_root(document),
                )


if __name__ == "__main__":
    unittest.main()
