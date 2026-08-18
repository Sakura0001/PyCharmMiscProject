from __future__ import annotations

import copy
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from importlib import resources
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

from .artifacts import validate_artifact_envelope
from .canonical import canonical_json_bytes, sha256_hex
from .errors import CoverageV2ArtifactError, CoverageV2SchemaError


SCHEMA_DOMAIN = b"FSCR_SCHEMA_V2\0"
REGISTRY_DOMAIN = b"FSCR_SCHEMA_REGISTRY_V2\0"
REGISTRY_KEYS = frozenset({"schema_version", "kind", "schemas"})
REGISTRY_ROW_KEYS = frozenset({"kind", "resource_name", "schema_version"})
DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"


@dataclass(frozen=True)
class SchemaBinding:
    kind: str
    resource_name: str
    schema_version: int
    byte_sha256: str
    semantic_sha256: str


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CoverageV2SchemaError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _load_json(raw: bytes, label: str) -> dict[str, Any]:
    try:
        document = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=lambda token: (_ for _ in ()).throw(
                CoverageV2SchemaError(f"invalid JSON constant {token}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CoverageV2SchemaError(f"{label} is not valid UTF-8 JSON") from exc
    if not isinstance(document, dict):
        raise CoverageV2SchemaError(f"{label} root must be an object")
    return document


def _safe_resource_name(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise CoverageV2SchemaError("schema resource_name must be non-empty")
    pure = PurePosixPath(value)
    if pure.is_absolute() or len(pure.parts) != 1 or pure.parts[0] in (".", ".."):
        raise CoverageV2SchemaError("schema resource_name must be a safe package filename")
    if pure.suffix != ".json":
        raise CoverageV2SchemaError("schema resource_name must end in .json")
    return value


def _walk_refs(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "$ref" and (not isinstance(child, str) or not child.startswith("#")):
                raise CoverageV2SchemaError("schema must not use remote or external references")
            _walk_refs(child)
    elif isinstance(value, list):
        for child in value:
            _walk_refs(child)


def _validate_schema_contract(kind: str, document: Mapping[str, Any]) -> None:
    if document.get("$schema") != DRAFT_2020_12:
        raise CoverageV2SchemaError("schema must declare JSON Schema Draft 2020-12")
    if document.get("type") != "object" or document.get("additionalProperties") is not False:
        raise CoverageV2SchemaError("artifact schema envelope must reject unknown fields")
    properties = document.get("properties")
    if not isinstance(properties, dict):
        raise CoverageV2SchemaError("artifact schema properties must be an object")
    if properties.get("kind") != {"const": kind}:
        raise CoverageV2SchemaError("artifact schema kind const differs from registry")
    if properties.get("schema_version") != {"const": 2}:
        raise CoverageV2SchemaError("artifact schema version const must equal 2")
    semantic_payload = properties.get("semantic_payload")
    if (
        not isinstance(semantic_payload, dict)
        or semantic_payload.get("type") != "object"
        or semantic_payload.get("additionalProperties") is not False
    ):
        raise CoverageV2SchemaError("semantic payload schema must reject unknown fields")
    _walk_refs(document)
    try:
        Draft202012Validator.check_schema(document)
    except SchemaError as exc:
        raise CoverageV2SchemaError(f"invalid schema for {kind}: {exc.message}") from exc


class ArtifactSchemaRegistry:
    def __init__(
        self,
        *,
        registry_document: Mapping[str, Any],
        schemas: Mapping[str, Mapping[str, Any]],
        bindings: Mapping[str, SchemaBinding],
    ) -> None:
        self._registry_document = copy.deepcopy(dict(registry_document))
        self._schemas = MappingProxyType(
            {kind: copy.deepcopy(dict(schema)) for kind, schema in schemas.items()}
        )
        self._bindings = MappingProxyType(dict(bindings))
        registry_projection = {
            "registry": self._registry_document,
            "schemas": [
                {
                    "kind": binding.kind,
                    "semantic_sha256": binding.semantic_sha256,
                }
                for binding in sorted(
                    bindings.values(), key=lambda item: item.kind.encode("utf-8")
                )
            ],
        }
        self._semantic_sha256 = sha256_hex(
            REGISTRY_DOMAIN + canonical_json_bytes(registry_projection)
        )

    @classmethod
    def load_packaged(cls) -> "ArtifactSchemaRegistry":
        package_root = resources.files("pg_case_factory.coverage_v2.schemas")

        def read_resource(name: str) -> bytes:
            resource = package_root.joinpath(name)
            try:
                return resource.read_bytes()
            except FileNotFoundError as exc:
                raise CoverageV2SchemaError(f"schema resource {name!r} is missing") from exc

        return cls._load(read_resource)

    @classmethod
    def load_directory(cls, directory: Path) -> "ArtifactSchemaRegistry":
        root = directory.resolve(strict=True)

        def read_resource(name: str) -> bytes:
            safe = _safe_resource_name(name)
            path = root.joinpath(safe)
            if path.is_symlink():
                raise CoverageV2SchemaError("schema resource must not be a symlink")
            try:
                resolved = path.resolve(strict=True)
                resolved.relative_to(root)
            except (FileNotFoundError, ValueError) as exc:
                raise CoverageV2SchemaError(f"schema resource {name!r} is missing") from exc
            if not resolved.is_file():
                raise CoverageV2SchemaError("schema resource must be a regular file")
            return resolved.read_bytes()

        return cls._load(read_resource)

    @classmethod
    def _load(cls, read_resource: Callable[[str], bytes]) -> "ArtifactSchemaRegistry":
        raw_registry = read_resource("registry.json")
        registry = _load_json(raw_registry, "schema registry")
        if frozenset(registry) != REGISTRY_KEYS:
            raise CoverageV2SchemaError("schema registry key set differs")
        if registry["schema_version"] != 2 or registry["kind"] != "artifact-schema-registry":
            raise CoverageV2SchemaError("schema registry identity differs")
        rows = registry["schemas"]
        if not isinstance(rows, list) or not rows:
            raise CoverageV2SchemaError("schema registry must contain schema rows")

        schemas: dict[str, Mapping[str, Any]] = {}
        bindings: dict[str, SchemaBinding] = {}
        resource_names: set[str] = set()
        previous_kind: bytes | None = None
        for row in rows:
            if not isinstance(row, dict) or frozenset(row) != REGISTRY_ROW_KEYS:
                raise CoverageV2SchemaError("schema registry row key set differs")
            kind = row["kind"]
            if not isinstance(kind, str) or not kind:
                raise CoverageV2SchemaError("schema registry kind must be non-empty")
            if previous_kind is not None and kind.encode("utf-8") <= previous_kind:
                raise CoverageV2SchemaError("schema registry rows must be unique UTF-8 sorted")
            previous_kind = kind.encode("utf-8")
            resource_name = _safe_resource_name(row["resource_name"])
            if resource_name in resource_names:
                raise CoverageV2SchemaError("schema resource is registered more than once")
            resource_names.add(resource_name)
            if row["schema_version"] != 2:
                raise CoverageV2SchemaError("schema registry row version must equal 2")
            raw_schema = read_resource(resource_name)
            schema = _load_json(raw_schema, resource_name)
            _validate_schema_contract(kind, schema)
            schemas[kind] = schema
            bindings[kind] = SchemaBinding(
                kind=kind,
                resource_name=resource_name,
                schema_version=2,
                byte_sha256=sha256_hex(raw_schema),
                semantic_sha256=sha256_hex(
                    SCHEMA_DOMAIN + canonical_json_bytes(schema)
                ),
            )
        return cls(registry_document=registry, schemas=schemas, bindings=bindings)

    @property
    def implemented_kinds(self) -> frozenset[str]:
        return frozenset(self._schemas)

    @property
    def bindings(self) -> Mapping[str, SchemaBinding]:
        return self._bindings

    @property
    def registry_document(self) -> dict[str, Any]:
        return copy.deepcopy(self._registry_document)

    @property
    def semantic_sha256(self) -> str:
        return self._semantic_sha256

    def validate(self, document: Mapping[str, Any]) -> None:
        try:
            validate_artifact_envelope(document)
        except CoverageV2ArtifactError as exc:
            raise CoverageV2SchemaError(str(exc)) from exc
        kind = document.get("kind")
        if not isinstance(kind, str) or kind not in self._schemas:
            raise CoverageV2SchemaError(f"artifact kind {kind!r} is not registered")
        validator = Draft202012Validator(self._schemas[kind])
        errors = sorted(validator.iter_errors(document), key=lambda item: list(item.path))
        if errors:
            error: ValidationError = errors[0]
            path = "/".join(str(part) for part in error.absolute_path)
            location = f" at {path}" if path else ""
            raise CoverageV2SchemaError(
                f"artifact {kind!r} violates schema{location}: {error.message}"
            )
