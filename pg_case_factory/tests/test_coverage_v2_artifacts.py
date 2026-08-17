from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from pg_case_factory.coverage_v2.artifacts import (
    ArtifactBinding,
    ManifestDomain,
    artifact_bytes,
    artifact_semantic_sha256,
    build_artifact,
    manifest_digest,
    verify_declared_artifact_graph,
)
from pg_case_factory.coverage_v2.errors import CoverageV2ArtifactError


class ArtifactEnvelopeTest(unittest.TestCase):
    def test_fixed_semantic_hash_excludes_operational_metadata(self) -> None:
        document = build_artifact(
            artifact_id="ART-1",
            kind="input-lock",
            semantic_payload={"inputs": []},
            predecessors=(),
            operational_metadata={"attempt": 9},
        )
        self.assertEqual(
            "70a44df23b65bc837e757a637e7047b74541dbe30ea9616a77caa4714be34cb5",
            document["semantic_sha256"],
        )
        changed = dict(document)
        changed["operational_metadata"] = {"attempt": 10}
        self.assertEqual(
            document["semantic_sha256"],
            artifact_semantic_sha256(changed),
        )
        self.assertNotEqual(artifact_bytes(document), artifact_bytes(changed))

    def test_manifest_digest_has_a_fixed_domain_and_rejects_duplicates(self) -> None:
        bindings = (
            ArtifactBinding("B", "b.json", "b" * 64, "2" * 64, "kind-b", 2),
            ArtifactBinding("A", "a.json", "a" * 64, "1" * 64, "kind-a", 2),
        )
        self.assertEqual(
            "93a2d62a66b4d9cc7ccbe214c0a9e69794dd584593b86ceb73deb44e78bada0f",
            manifest_digest(ManifestDomain.VALIDATED_PLAN, bindings),
        )
        with self.assertRaises(CoverageV2ArtifactError):
            manifest_digest(ManifestDomain.VALIDATED_PLAN, (bindings[0], bindings[0]))
        with self.assertRaises(CoverageV2ArtifactError):
            manifest_digest("CALLER_CHOSEN", bindings)  # type: ignore[arg-type]
        malformed = (
            ArtifactBinding("", "bad-id.json", "c" * 64, "3" * 64, "bad", 2),
            ArtifactBinding("C", "bad-sha.json", "c" * 64, "not-a-sha", "bad", 2),
        )
        for binding in malformed:
            with self.subTest(binding=binding):
                with self.assertRaises(CoverageV2ArtifactError):
                    manifest_digest(ManifestDomain.VALIDATED_PLAN, (binding,))


class DeclaredArtifactGraphTest(unittest.TestCase):
    def _write(self, root: Path, name: str, document: dict[str, object]) -> None:
        root.joinpath(name).write_bytes(artifact_bytes(document))

    def test_current_files_pass_and_stale_predecessor_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parent = build_artifact(
                artifact_id="A",
                kind="input-lock",
                semantic_payload={"version": 1},
                predecessors=(),
            )
            parent_binding = ArtifactBinding(
                "A", "a.json", "0" * 64,
                str(parent["semantic_sha256"]), "input-lock", 2,
            )
            child = build_artifact(
                artifact_id="B",
                kind="plan-validation",
                semantic_payload={"passed": True},
                predecessors=(parent_binding,),
            )
            self._write(root, "a.json", parent)
            self._write(root, "b.json", child)
            graph = verify_declared_artifact_graph(root, ("b.json", "a.json"))
            self.assertEqual({"A", "B"}, set(graph.bindings))

            replacement = build_artifact(
                artifact_id="A",
                kind="input-lock",
                semantic_payload={"version": 2},
                predecessors=(),
            )
            self._write(root, "a.json", replacement)
            with self.assertRaisesRegex(CoverageV2ArtifactError, "predecessor"):
                verify_declared_artifact_graph(root, ("a.json", "b.json"))

    def test_cycle_is_reported_before_stale_semantic_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            a = build_artifact(
                artifact_id="A",
                kind="kind-a",
                semantic_payload={},
                predecessors=(),
            )
            b = build_artifact(
                artifact_id="B",
                kind="kind-b",
                semantic_payload={},
                predecessors=(),
            )
            a["predecessors"] = {"B": str(b["semantic_sha256"])}
            b["predecessors"] = {"A": str(a["semantic_sha256"])}
            self._write(root, "a.json", a)
            self._write(root, "b.json", b)
            with self.assertRaisesRegex(CoverageV2ArtifactError, "cycle"):
                verify_declared_artifact_graph(root, ("a.json", "b.json"))

    def test_duplicate_json_key_missing_file_and_symlink_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            root.joinpath("duplicate.json").write_text(
                '{"schema_version":2,"schema_version":2}',
                encoding="utf-8",
            )
            with self.assertRaises(CoverageV2ArtifactError):
                verify_declared_artifact_graph(root, ("duplicate.json",))
            root.joinpath("nan.json").write_text('{"value":NaN}', encoding="utf-8")
            with self.assertRaisesRegex(CoverageV2ArtifactError, "invalid JSON constant"):
                verify_declared_artifact_graph(root, ("nan.json",))
            canonical = build_artifact(
                artifact_id="FLOAT",
                kind="input-lock",
                semantic_payload={},
                predecessors=(),
            )
            canonical["operational_metadata"] = {"finite_float": 1.5}
            root.joinpath("float.json").write_text(json.dumps(canonical), encoding="utf-8")
            with self.assertRaises(CoverageV2ArtifactError):
                verify_declared_artifact_graph(root, ("float.json",))
            pretty = build_artifact(
                artifact_id="PRETTY",
                kind="input-lock",
                semantic_payload={},
                predecessors=(),
            )
            root.joinpath("pretty.json").write_text(
                json.dumps(pretty, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(CoverageV2ArtifactError, "not canonical"):
                verify_declared_artifact_graph(root, ("pretty.json",))
            with self.assertRaises(CoverageV2ArtifactError):
                verify_declared_artifact_graph(root, ("missing.json",))

            target = root.joinpath("target.json")
            target.write_text(json.dumps({}), encoding="utf-8")
            root.joinpath("link.json").symlink_to(target)
            with self.assertRaises(CoverageV2ArtifactError):
                verify_declared_artifact_graph(root, ("link.json",))


if __name__ == "__main__":
    unittest.main()
