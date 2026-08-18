from __future__ import annotations

import json
import tempfile
import unittest
from importlib import resources
from pathlib import Path

from pg_case_factory.coverage_v2.artifacts import build_artifact
from pg_case_factory.coverage_v2.errors import CoverageV2SchemaError
from pg_case_factory.coverage_v2.schema_registry import ArtifactSchemaRegistry


def _input_lock_document() -> dict[str, object]:
    return build_artifact(
        artifact_id="LOCK-1",
        kind="input-lock",
        semantic_payload={
            "scope": "global",
            "inputs": [
                {
                    "relative_path": "catalog.yaml",
                    "version": "catalog-v1",
                    "semantic_decoder_id": "yaml-v1",
                    "byte_sha256": "1" * 64,
                    "semantic_sha256": "2" * 64,
                }
            ],
            "input_count": 1,
            "input_multiset_sha256": "3" * 64,
        },
        predecessors=(),
    )


def _current_pointer_document() -> dict[str, object]:
    return build_artifact(
        artifact_id="CURRENT-ABORT",
        kind="current-pointer",
        semantic_payload={
            "run_id": "fscr-pg18_4-0123456789abcdef",
            "statement_key": "abort",
            "revision_id": "r0001",
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


def _readiness_document() -> dict[str, object]:
    return build_artifact(
        artifact_id="READY-ABORT",
        kind="readiness",
        semantic_payload={
            "statement_key": "abort",
            "passed": False,
            "checks": [
                {
                    "component_id": "schema-registry",
                    "passed": True,
                    "evidence_semantic_sha256": "4" * 64,
                }
            ],
            "missing_components": ["semantic-extractor-registry"],
            "implemented_schema_kinds": [
                "current-pointer",
                "input-lock",
                "readiness",
            ],
            "required_schema_kinds": [
                "current-pointer",
                "input-lock",
                "readiness",
                "source-universe",
            ],
            "schema_registry_semantic_sha256": "5" * 64,
        },
        predecessors=(),
    )


class PackagedSchemaRegistryTest(unittest.TestCase):
    def test_positive_documents_validate_and_package_resources_are_readable(self) -> None:
        registry = ArtifactSchemaRegistry.load_packaged()
        self.assertEqual(
            frozenset(
                {"input-lock", "current-pointer", "readiness", "statement-order"}
            ),
            registry.implemented_kinds,
        )
        for document in (
            _input_lock_document(),
            _current_pointer_document(),
            _readiness_document(),
        ):
            registry.validate(document)
        package_root = resources.files("pg_case_factory.coverage_v2.schemas")
        self.assertTrue(package_root.joinpath("registry.json").read_bytes())
        envelope = json.loads(
            package_root.joinpath("artifact-envelope.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(False, envelope["additionalProperties"])
        self.assertEqual(2, envelope["properties"]["schema_version"]["const"])
        self.assertEqual(registry.implemented_kinds, frozenset(registry.bindings))
        for binding in registry.bindings.values():
            self.assertEqual(2, binding.schema_version)
            self.assertEqual(64, len(binding.byte_sha256))
            self.assertEqual(64, len(binding.semantic_sha256))

    def test_unknown_extra_missing_wrong_version_and_wrong_kind_fail_closed(self) -> None:
        registry = ArtifactSchemaRegistry.load_packaged()
        valid = _input_lock_document()

        extra = dict(valid)
        extra["unexpected"] = True
        with self.assertRaises(CoverageV2SchemaError):
            registry.validate(extra)

        missing_payload_field = _input_lock_document()
        del missing_payload_field["semantic_payload"]["inputs"]  # type: ignore[index]
        with self.assertRaises(CoverageV2SchemaError):
            registry.validate(missing_payload_field)

        extra_payload_field = _input_lock_document()
        extra_payload_field["semantic_payload"]["unexpected"] = True  # type: ignore[index]
        with self.assertRaises(CoverageV2SchemaError):
            registry.validate(extra_payload_field)

        wrong_version = dict(valid)
        wrong_version["schema_version"] = 1
        with self.assertRaises(CoverageV2SchemaError):
            registry.validate(wrong_version)

        unknown = build_artifact(
            artifact_id="UNKNOWN",
            kind="unknown-v2-kind",
            semantic_payload={},
            predecessors=(),
        )
        with self.assertRaises(CoverageV2SchemaError):
            registry.validate(unknown)

        wrong_kind = _input_lock_document()
        wrong_kind["kind"] = "readiness"
        with self.assertRaises(CoverageV2SchemaError):
            registry.validate(wrong_kind)

    def test_registry_rejects_unsafe_paths_and_non_strict_schemas(self) -> None:
        packaged = ArtifactSchemaRegistry.load_packaged()
        registry_document = packaged.registry_document
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for unsafe in ("/tmp/schema.json", "../schema.json"):
                with self.subTest(unsafe=unsafe):
                    changed = json.loads(json.dumps(registry_document))
                    changed["schemas"][0]["resource_name"] = unsafe
                    root.joinpath("registry.json").write_text(
                        json.dumps(changed), encoding="utf-8"
                    )
                    with self.assertRaises(CoverageV2SchemaError):
                        ArtifactSchemaRegistry.load_directory(root)

            changed = json.loads(json.dumps(registry_document))
            first = changed["schemas"][0]
            first["resource_name"] = "loose.schema.json"
            root.joinpath("registry.json").write_text(json.dumps(changed), encoding="utf-8")
            root.joinpath("loose.schema.json").write_text(
                json.dumps(
                    {
                        "$schema": "https://json-schema.org/draft/2020-12/schema",
                        "type": "object",
                        "additionalProperties": True,
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(CoverageV2SchemaError):
                ArtifactSchemaRegistry.load_directory(root)


if __name__ == "__main__":
    unittest.main()
