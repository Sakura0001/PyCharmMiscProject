from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any

from .canonical import canonical_json_bytes, sha256_hex
from .errors import CoverageV2ArtifactError, CoverageV2ContractError


ARTIFACT_DOMAIN = b"FSCR_ARTIFACT_V2\0"
SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
ENVELOPE_KEYS = frozenset(
    {
        "schema_version",
        "kind",
        "artifact_id",
        "predecessors",
        "semantic_payload",
        "semantic_sha256",
        "operational_metadata",
    }
)


class ManifestDomain(str, Enum):
    VALIDATED_PLAN = "FSCR_VALIDATED_PLAN_V2"


@dataclass(frozen=True)
class ArtifactBinding:
    artifact_id: str
    relative_path: str
    byte_sha256: str
    semantic_sha256: str
    kind: str
    schema_version: int


@dataclass(frozen=True)
class VerifiedArtifactGraph:
    bindings: Mapping[str, ArtifactBinding]


@dataclass(frozen=True)
class _ArtifactCandidate:
    relative_path: str
    raw_bytes: bytes
    document: Mapping[str, Any]


def _semantic_projection(document: Mapping[str, Any]) -> dict[str, Any]:
    required = (
        "schema_version",
        "kind",
        "artifact_id",
        "predecessors",
        "semantic_payload",
    )
    missing = [key for key in required if key not in document]
    if missing:
        raise CoverageV2ArtifactError(f"artifact semantic projection missing {missing}")
    return {key: document[key] for key in required}


def artifact_semantic_sha256(document: Mapping[str, Any]) -> str:
    try:
        payload = canonical_json_bytes(_semantic_projection(document))
    except CoverageV2ContractError as exc:
        raise CoverageV2ArtifactError(str(exc)) from exc
    return sha256_hex(ARTIFACT_DOMAIN + payload)


def _validate_envelope_shape(document: Mapping[str, Any]) -> None:
    if frozenset(document) != ENVELOPE_KEYS:
        raise CoverageV2ArtifactError("artifact envelope key set differs")
    if document["schema_version"] != 2:
        raise CoverageV2ArtifactError("artifact schema_version must equal 2")
    for key in ("kind", "artifact_id"):
        if not isinstance(document[key], str) or not document[key]:
            raise CoverageV2ArtifactError(f"artifact {key} must be a non-empty string")
    if not isinstance(document["semantic_payload"], dict):
        raise CoverageV2ArtifactError("artifact semantic_payload must be an object")
    if document["operational_metadata"] is not None and not isinstance(
        document["operational_metadata"], dict
    ):
        raise CoverageV2ArtifactError("artifact operational_metadata must be null or object")
    predecessors = document["predecessors"]
    if not isinstance(predecessors, dict):
        raise CoverageV2ArtifactError("artifact predecessors must be an object")
    for predecessor_id, semantic_sha in predecessors.items():
        if not isinstance(predecessor_id, str) or not predecessor_id:
            raise CoverageV2ArtifactError("predecessor ID must be a non-empty string")
        if not isinstance(semantic_sha, str) or SHA256_HEX.fullmatch(semantic_sha) is None:
            raise CoverageV2ArtifactError("predecessor semantic SHA must be lowercase SHA-256")
    semantic_sha = document["semantic_sha256"]
    if not isinstance(semantic_sha, str) or SHA256_HEX.fullmatch(semantic_sha) is None:
        raise CoverageV2ArtifactError("artifact semantic SHA must be lowercase SHA-256")


def build_artifact(
    *,
    artifact_id: str,
    kind: str,
    semantic_payload: Mapping[str, Any],
    predecessors: Sequence[ArtifactBinding],
    operational_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    predecessor_map: dict[str, str] = {}
    for binding in sorted(predecessors, key=lambda item: item.artifact_id.encode("utf-8")):
        if binding.artifact_id in predecessor_map:
            raise CoverageV2ArtifactError("artifact has duplicate predecessor ID")
        predecessor_map[binding.artifact_id] = binding.semantic_sha256
    document: dict[str, Any] = {
        "schema_version": 2,
        "kind": kind,
        "artifact_id": artifact_id,
        "predecessors": predecessor_map,
        "semantic_payload": dict(semantic_payload),
        "semantic_sha256": "0" * 64,
        "operational_metadata": (
            None if operational_metadata is None else dict(operational_metadata)
        ),
    }
    document["semantic_sha256"] = artifact_semantic_sha256(document)
    _validate_envelope_shape(document)
    artifact_bytes(document)
    return document


def artifact_bytes(document: Mapping[str, Any]) -> bytes:
    _validate_envelope_shape(document)
    try:
        return canonical_json_bytes(dict(document)) + b"\n"
    except CoverageV2ContractError as exc:
        raise CoverageV2ArtifactError(str(exc)) from exc


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CoverageV2ArtifactError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _safe_candidate_path(repository_root: Path, relative_path: str) -> Path:
    pure = PurePosixPath(relative_path)
    if pure.is_absolute() or not pure.parts or any(part in ("", ".", "..") for part in pure.parts):
        raise CoverageV2ArtifactError("artifact path must be a safe repository-relative path")
    root = repository_root.resolve(strict=True)
    candidate = root
    for part in pure.parts:
        candidate = candidate.joinpath(part)
        if candidate.is_symlink():
            raise CoverageV2ArtifactError("artifact path must not contain symlinks")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (FileNotFoundError, ValueError) as exc:
        raise CoverageV2ArtifactError("artifact path is missing or outside the root") from exc
    if not resolved.is_file():
        raise CoverageV2ArtifactError("artifact path must name a regular file")
    return resolved


def _read_candidate(repository_root: Path, relative_path: str) -> _ArtifactCandidate:
    path = _safe_candidate_path(repository_root, relative_path)
    raw_bytes = path.read_bytes()
    try:
        text = raw_bytes.decode("utf-8")
        document = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=lambda token: (_ for _ in ()).throw(
                CoverageV2ArtifactError(f"invalid JSON constant {token}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CoverageV2ArtifactError("artifact is not valid UTF-8 JSON") from exc
    if not isinstance(document, dict):
        raise CoverageV2ArtifactError("artifact root must be an object")
    _validate_envelope_shape(document)
    expected_bytes = artifact_bytes(document)
    if raw_bytes != expected_bytes:
        raise CoverageV2ArtifactError("artifact bytes are not canonical")
    return _ArtifactCandidate(relative_path, raw_bytes, document)


def _detect_cycle(documents: Mapping[str, Mapping[str, Any]]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(artifact_id: str) -> None:
        if artifact_id in visiting:
            raise CoverageV2ArtifactError("artifact predecessor graph contains a cycle")
        if artifact_id in visited:
            return
        visiting.add(artifact_id)
        predecessors = documents[artifact_id]["predecessors"]
        assert isinstance(predecessors, dict)
        for predecessor_id in predecessors:
            if predecessor_id not in documents:
                raise CoverageV2ArtifactError(
                    f"artifact predecessor {predecessor_id} is absent from current files"
                )
            visit(predecessor_id)
        visiting.remove(artifact_id)
        visited.add(artifact_id)

    for artifact_id in sorted(documents, key=lambda value: value.encode("utf-8")):
        visit(artifact_id)


def verify_declared_artifact_graph(
    repository_root: Path,
    relative_paths: Sequence[str],
) -> VerifiedArtifactGraph:
    candidates: dict[str, _ArtifactCandidate] = {}
    documents: dict[str, Mapping[str, Any]] = {}
    for relative_path in relative_paths:
        candidate = _read_candidate(repository_root, relative_path)
        artifact_id = candidate.document["artifact_id"]
        assert isinstance(artifact_id, str)
        if artifact_id in candidates:
            raise CoverageV2ArtifactError("duplicate artifact ID in current files")
        candidates[artifact_id] = candidate
        documents[artifact_id] = candidate.document

    _detect_cycle(documents)

    bindings: dict[str, ArtifactBinding] = {}
    for artifact_id, candidate in candidates.items():
        expected = artifact_semantic_sha256(candidate.document)
        if candidate.document["semantic_sha256"] != expected:
            raise CoverageV2ArtifactError("artifact semantic SHA differs from current content")
        bindings[artifact_id] = ArtifactBinding(
            artifact_id=artifact_id,
            relative_path=candidate.relative_path,
            byte_sha256=sha256_hex(candidate.raw_bytes),
            semantic_sha256=expected,
            kind=str(candidate.document["kind"]),
            schema_version=2,
        )

    for artifact_id, document in documents.items():
        predecessors = document["predecessors"]
        assert isinstance(predecessors, dict)
        for predecessor_id, expected_sha in predecessors.items():
            actual_sha = bindings[predecessor_id].semantic_sha256
            if actual_sha != expected_sha:
                raise CoverageV2ArtifactError(
                    f"artifact predecessor {predecessor_id} differs from current semantic SHA"
                )

    return VerifiedArtifactGraph(MappingProxyType(dict(bindings)))


def manifest_digest(
    domain: ManifestDomain,
    artifacts: Sequence[ArtifactBinding],
) -> str:
    if not isinstance(domain, ManifestDomain):
        raise CoverageV2ArtifactError("manifest digest domain is not frozen")
    seen: set[str] = set()
    records: list[dict[str, str]] = []
    for binding in artifacts:
        if not isinstance(binding.artifact_id, str) or not binding.artifact_id:
            raise CoverageV2ArtifactError("manifest artifact ID must be non-empty")
        if (
            not isinstance(binding.semantic_sha256, str)
            or SHA256_HEX.fullmatch(binding.semantic_sha256) is None
        ):
            raise CoverageV2ArtifactError(
                "manifest artifact semantic SHA must be lowercase SHA-256"
            )
        if binding.artifact_id in seen:
            raise CoverageV2ArtifactError("manifest has duplicate artifact ID")
        seen.add(binding.artifact_id)
        records.append(
            {
                "artifact_id": binding.artifact_id,
                "semantic_sha256": binding.semantic_sha256,
            }
        )
    records.sort(key=lambda item: item["artifact_id"].encode("utf-8"))
    return sha256_hex(
        domain.value.encode("ascii") + b"\0" + canonical_json_bytes(records)
    )
