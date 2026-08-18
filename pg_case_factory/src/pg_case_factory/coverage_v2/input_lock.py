from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Literal, cast

import yaml

from .artifacts import (
    artifact_semantic_sha256,
    build_artifact,
    verify_declared_artifact_graph,
)
from .canonical import canonical_json_bytes, sha256_hex
from .errors import (
    CoverageV2ArtifactError,
    CoverageV2ContractError,
    CoverageV2InputLockError,
)
from .schema_registry import ArtifactSchemaRegistry


DecoderId = Literal["raw-v1", "utf8-text-v1", "json-v1", "yaml-v1"]
DECODER_IDS = frozenset({"raw-v1", "utf8-text-v1", "json-v1", "yaml-v1"})
INPUT_SEMANTIC_DOMAIN = b"FSCR_INPUT_SEMANTIC_V2\0"
INPUT_MULTISET_DOMAIN = b"FSCR_INPUT_MULTISET_V2\0"
RUN_ID = re.compile(r"^fscr-pg18_4-([0-9a-f]{16})$")


@dataclass(frozen=True)
class InputSpec:
    relative_path: str
    version: str
    semantic_decoder_id: DecoderId

    def __post_init__(self) -> None:
        _safe_relative_path(self.relative_path)
        if not isinstance(self.version, str) or not self.version:
            raise CoverageV2InputLockError("input version must be a non-empty string")
        if self.semantic_decoder_id not in DECODER_IDS:
            raise CoverageV2InputLockError("input semantic decoder is not frozen")


@dataclass(frozen=True)
class InputBinding:
    relative_path: str
    version: str
    semantic_decoder_id: DecoderId
    byte_sha256: str
    semantic_sha256: str

    def as_record(self) -> dict[str, Any]:
        return {
            "relative_path": self.relative_path,
            "version": self.version,
            "semantic_decoder_id": self.semantic_decoder_id,
            "byte_sha256": self.byte_sha256,
            "semantic_sha256": self.semantic_sha256,
        }


class _UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(
    loader: _UniqueKeyLoader,
    node: yaml.nodes.MappingNode,
    deep: bool = False,
) -> dict[Any, Any]:
    loader.flatten_mapping(node)
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in result
        except TypeError as exc:
            raise CoverageV2InputLockError("YAML mapping key is not scalar") from exc
        if duplicate:
            raise CoverageV2InputLockError(f"duplicate YAML key {key!r}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CoverageV2InputLockError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _safe_relative_path(value: str) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        raise CoverageV2InputLockError("input path must be a non-empty string")
    pure = PurePosixPath(value)
    if pure.is_absolute() or any(part in ("", ".", "..") for part in pure.parts):
        raise CoverageV2InputLockError("input path must be safe and repository-relative")
    return pure


def _resolve_input(repository_root: Path, relative_path: str) -> Path:
    pure = _safe_relative_path(relative_path)
    try:
        root = repository_root.resolve(strict=True)
    except FileNotFoundError as exc:
        raise CoverageV2InputLockError("repository root is missing") from exc
    candidate = root
    for part in pure.parts:
        candidate = candidate.joinpath(part)
        if candidate.is_symlink():
            raise CoverageV2InputLockError("input path must not contain symlinks")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (FileNotFoundError, ValueError) as exc:
        raise CoverageV2InputLockError("input path is missing or outside repository root") from exc
    if not resolved.is_file():
        raise CoverageV2InputLockError("input path must name a regular file")
    return resolved


def _decoded_semantic_bytes(raw: bytes, decoder_id: DecoderId) -> bytes:
    try:
        if decoder_id == "raw-v1":
            payload = raw
        elif decoder_id == "utf8-text-v1":
            payload = canonical_json_bytes(raw.decode("utf-8"))
        elif decoder_id == "json-v1":
            value = json.loads(
                raw.decode("utf-8"),
                object_pairs_hook=_reject_duplicate_json_keys,
                parse_constant=lambda token: (_ for _ in ()).throw(
                    CoverageV2InputLockError(f"invalid JSON constant {token}")
                ),
            )
            payload = canonical_json_bytes(value)
        elif decoder_id == "yaml-v1":
            value = yaml.load(raw.decode("utf-8"), Loader=_UniqueKeyLoader)
            payload = canonical_json_bytes(value)
        else:  # pragma: no cover - InputSpec rejects this before dispatch.
            raise CoverageV2InputLockError("input semantic decoder is not frozen")
    except (UnicodeDecodeError, json.JSONDecodeError, yaml.YAMLError) as exc:
        raise CoverageV2InputLockError(
            f"input cannot be decoded with {decoder_id}"
        ) from exc
    except CoverageV2ContractError as exc:
        raise CoverageV2InputLockError(
            f"decoded {decoder_id} input is not canonical JSON data"
        ) from exc
    return decoder_id.encode("ascii") + b"\0" + payload


def _bind_input(repository_root: Path, spec: InputSpec) -> InputBinding:
    raw = _resolve_input(repository_root, spec.relative_path).read_bytes()
    return InputBinding(
        relative_path=spec.relative_path,
        version=spec.version,
        semantic_decoder_id=spec.semantic_decoder_id,
        byte_sha256=sha256_hex(raw),
        semantic_sha256=sha256_hex(
            INPUT_SEMANTIC_DOMAIN
            + _decoded_semantic_bytes(raw, spec.semantic_decoder_id)
        ),
    )


def _multiset_sha256(bindings: Sequence[InputBinding]) -> str:
    records = [binding.as_record() for binding in bindings]
    return sha256_hex(INPUT_MULTISET_DOMAIN + canonical_json_bytes(records))


def freeze_input_lock(
    repository_root: Path,
    *,
    scope: str,
    input_specs: Sequence[InputSpec],
) -> dict[str, Any]:
    if scope not in ("global", "local"):
        raise CoverageV2InputLockError("input lock scope must be global or local")
    if not input_specs:
        raise CoverageV2InputLockError("input lock must bind at least one input")
    ordered = sorted(input_specs, key=lambda item: item.relative_path.encode("utf-8"))
    if len({item.relative_path for item in ordered}) != len(ordered):
        raise CoverageV2InputLockError("input lock contains duplicate paths")
    bindings = tuple(_bind_input(repository_root, spec) for spec in ordered)
    document = build_artifact(
        artifact_id=f"INPUT-LOCK-{scope}",
        kind="input-lock",
        semantic_payload={
            "scope": scope,
            "inputs": [binding.as_record() for binding in bindings],
            "input_count": len(bindings),
            "input_multiset_sha256": _multiset_sha256(bindings),
        },
        predecessors=(),
    )
    ArtifactSchemaRegistry.load_packaged().validate(document)
    return document


def _binding_from_record(value: Any) -> InputBinding:
    if not isinstance(value, dict):
        raise CoverageV2InputLockError("input lock row must be an object")
    try:
        return InputBinding(
            relative_path=value["relative_path"],
            version=value["version"],
            semantic_decoder_id=cast(DecoderId, value["semantic_decoder_id"]),
            byte_sha256=value["byte_sha256"],
            semantic_sha256=value["semantic_sha256"],
        )
    except (KeyError, TypeError) as exc:
        raise CoverageV2InputLockError("input lock row is malformed") from exc


def verify_input_lock(
    repository_root: Path,
    document: Mapping[str, Any],
) -> tuple[InputBinding, ...]:
    registry = ArtifactSchemaRegistry.load_packaged()
    try:
        registry.validate(document)
    except CoverageV2ArtifactError as exc:
        raise CoverageV2InputLockError(str(exc)) from exc
    expected_artifact_sha = artifact_semantic_sha256(document)
    if document["semantic_sha256"] != expected_artifact_sha:
        raise CoverageV2InputLockError("input lock semantic SHA differs from content")
    payload = document["semantic_payload"]
    assert isinstance(payload, dict)
    declared = tuple(_binding_from_record(row) for row in payload["inputs"])
    if tuple(sorted(declared, key=lambda item: item.relative_path.encode("utf-8"))) != declared:
        raise CoverageV2InputLockError("input lock rows are not UTF-8 path sorted")
    if len({item.relative_path for item in declared}) != len(declared):
        raise CoverageV2InputLockError("input lock contains duplicate paths")
    if payload["input_count"] != len(declared):
        raise CoverageV2InputLockError("input lock count differs")
    if payload["input_multiset_sha256"] != _multiset_sha256(declared):
        raise CoverageV2InputLockError("input lock multiset SHA differs")
    current = tuple(
        _bind_input(
            repository_root,
            InputSpec(
                binding.relative_path,
                binding.version,
                binding.semantic_decoder_id,
            ),
        )
        for binding in declared
    )
    if current != declared:
        raise CoverageV2InputLockError("input lock differs from current bytes")
    return declared


def global_input_root(document: Mapping[str, Any]) -> str:
    payload = document.get("semantic_payload")
    if document.get("kind") != "input-lock" or not isinstance(payload, dict):
        raise CoverageV2InputLockError("global input root requires an input-lock artifact")
    if payload.get("scope") != "global":
        raise CoverageV2InputLockError("global input root requires global scope")
    expected = artifact_semantic_sha256(document)
    if document.get("semantic_sha256") != expected:
        raise CoverageV2InputLockError("global input lock semantic SHA differs")
    return expected


def run_id_for_global_input_lock(document: Mapping[str, Any]) -> str:
    return f"fscr-pg18_4-{global_input_root(document)[:16]}"


def assert_run_id_available(
    runs_root: Path,
    run_id: str,
    full_root_sha256: str,
) -> None:
    match = RUN_ID.fullmatch(run_id)
    if match is None or match.group(1) != full_root_sha256[:16]:
        raise CoverageV2InputLockError("run ID differs from complete global input root")
    run_path = runs_root.joinpath(run_id)
    if not run_path.exists():
        return
    relative = f"{run_id}/global/global-input-lock.json"
    try:
        graph = verify_declared_artifact_graph(runs_root, (relative,))
    except CoverageV2ArtifactError as exc:
        raise CoverageV2InputLockError("run ID collision has no valid global input lock") from exc
    binding = next(iter(graph.bindings.values()))
    if binding.kind != "input-lock" or binding.semantic_sha256 != full_root_sha256:
        raise CoverageV2InputLockError("run ID prefix collision with another global input root")
