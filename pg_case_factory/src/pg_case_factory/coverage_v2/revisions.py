from __future__ import annotations

import fcntl
import json
import os
import re
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .artifacts import artifact_bytes, artifact_semantic_sha256
from .errors import CoverageV2ArtifactError, CoverageV2RevisionError
from .schema_registry import ArtifactSchemaRegistry


RUN_ID = re.compile(r"^fscr-pg18_4-[0-9a-f]{16}$")
STATEMENT_KEY = re.compile(r"^[a-z][a-z0-9_]*$")
REVISION_ID = re.compile(r"^r([0-9]{4,})$")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CoverageV2RevisionError(f"duplicate current-pointer key {key!r}")
        result[key] = value
    return result


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _fsync_tree(root: Path) -> None:
    if root.is_symlink() or not root.is_dir():
        raise CoverageV2RevisionError("revision staging path must be a real directory")
    directories: list[Path] = []
    for directory, child_directories, filenames in os.walk(root):
        current = Path(directory)
        directories.append(current)
        for name in child_directories:
            if current.joinpath(name).is_symlink():
                raise CoverageV2RevisionError("revision staging tree must not contain symlinks")
        for name in filenames:
            path = current.joinpath(name)
            if path.is_symlink() or not path.is_file():
                raise CoverageV2RevisionError(
                    "revision staging tree must contain only regular files"
                )
            descriptor = os.open(path, os.O_RDONLY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
    for directory in reversed(directories):
        _fsync_directory(directory)


class RevisionStore:
    def __init__(self, root: Path, *, run_id: str, statement_key: str) -> None:
        if RUN_ID.fullmatch(run_id) is None:
            raise CoverageV2RevisionError("invalid V2 run ID")
        if STATEMENT_KEY.fullmatch(statement_key) is None:
            raise CoverageV2RevisionError("invalid statement key")
        self.root = root
        self.run_id = run_id
        self.statement_key = statement_key
        self.statement_root = root.joinpath(run_id, statement_key)
        self.planning_root = self.statement_root.joinpath(".planning")
        self.revisions_root = self.statement_root.joinpath("plan-revisions")
        self.current_path = self.statement_root.joinpath("current.json")
        self.lock_path = self.statement_root.joinpath(".revision.lock")
        self.planning_root.mkdir(parents=True, exist_ok=True)
        self.revisions_root.mkdir(parents=True, exist_ok=True)

    def _revision_numbers(self) -> list[int]:
        numbers: list[int] = []
        for parent in (self.planning_root, self.revisions_root):
            for child in parent.iterdir():
                match = REVISION_ID.fullmatch(child.name)
                if match is not None:
                    numbers.append(int(match.group(1)))
        return numbers

    def allocate_revision_id(self) -> str:
        descriptor = os.open(self.lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            number = max(self._revision_numbers(), default=0) + 1
            revision_id = f"r{number:04d}"
            self.planning_root.joinpath(revision_id).mkdir()
            _fsync_directory(self.planning_root)
            return revision_id
        except FileExistsError as exc:  # Defensive fail-closed guard around reservation.
            raise CoverageV2RevisionError("revision reservation collided") from exc
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)

    def _validate_revision_id(self, revision_id: str) -> None:
        if REVISION_ID.fullmatch(revision_id) is None:
            raise CoverageV2RevisionError("invalid statement revision ID")

    def create_staging(self, revision_id: str) -> Path:
        self._validate_revision_id(revision_id)
        staging = self.planning_root.joinpath(revision_id)
        final = self.revisions_root.joinpath(revision_id)
        if final.exists():
            raise CoverageV2RevisionError("published revision is immutable")
        if not staging.is_dir() or staging.is_symlink():
            raise CoverageV2RevisionError("revision was not allocated in this store")
        return staging

    def publish_revision(self, revision_id: str) -> Path:
        self._validate_revision_id(revision_id)
        staging = self.planning_root.joinpath(revision_id)
        final = self.revisions_root.joinpath(revision_id)
        if final.exists():
            raise CoverageV2RevisionError("published revision already exists")
        if not staging.is_dir() or staging.is_symlink():
            raise CoverageV2RevisionError("revision staging directory is missing")
        if os.stat(staging.parent).st_dev != os.stat(final.parent).st_dev:
            raise CoverageV2RevisionError("revision publication must stay on one filesystem")
        _fsync_tree(staging)
        try:
            os.rename(staging, final)
        except FileExistsError as exc:
            raise CoverageV2RevisionError("published revision must not be overwritten") from exc
        _fsync_directory(self.revisions_root)
        return final

    def _validate_pointer_identity(self, document: Mapping[str, Any]) -> str:
        payload = document.get("semantic_payload")
        if not isinstance(payload, dict):
            raise CoverageV2RevisionError("current pointer semantic payload is missing")
        if payload.get("run_id") != self.run_id:
            raise CoverageV2RevisionError("current pointer run ID differs from store")
        if payload.get("statement_key") != self.statement_key:
            raise CoverageV2RevisionError("current pointer statement differs from store")
        revision_id = payload.get("revision_id")
        if not isinstance(revision_id, str) or REVISION_ID.fullmatch(revision_id) is None:
            raise CoverageV2RevisionError("current pointer revision ID is invalid")
        target = self.revisions_root.joinpath(revision_id)
        if not target.is_dir() or target.is_symlink():
            raise CoverageV2RevisionError("current pointer target revision is not published")
        return revision_id

    def write_current(self, pointer_document: Mapping[str, Any]) -> None:
        registry = ArtifactSchemaRegistry.load_packaged()
        try:
            registry.validate(pointer_document)
        except CoverageV2ArtifactError as exc:
            raise CoverageV2RevisionError(str(exc)) from exc
        expected_sha = artifact_semantic_sha256(pointer_document)
        if pointer_document.get("semantic_sha256") != expected_sha:
            raise CoverageV2RevisionError("current pointer semantic SHA differs")
        self._validate_pointer_identity(pointer_document)
        raw = artifact_bytes(pointer_document)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".current.json.", suffix=".tmp", dir=self.statement_root
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.current_path)
            _fsync_directory(self.statement_root)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise

    def read_current(
        self,
        registry: ArtifactSchemaRegistry,
    ) -> Mapping[str, Any]:
        try:
            raw = self.current_path.read_bytes()
        except FileNotFoundError as exc:
            raise CoverageV2RevisionError("current pointer is missing") from exc
        try:
            document = json.loads(
                raw.decode("utf-8"),
                object_pairs_hook=_reject_duplicate_keys,
                parse_constant=lambda token: (_ for _ in ()).throw(
                    CoverageV2RevisionError(f"invalid JSON constant {token}")
                ),
            )
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CoverageV2RevisionError("current pointer is not UTF-8 JSON") from exc
        if not isinstance(document, dict):
            raise CoverageV2RevisionError("current pointer root must be an object")
        try:
            registry.validate(document)
        except CoverageV2ArtifactError as exc:
            raise CoverageV2RevisionError(str(exc)) from exc
        if raw != artifact_bytes(document):
            raise CoverageV2RevisionError("current pointer bytes are not canonical")
        if document.get("semantic_sha256") != artifact_semantic_sha256(document):
            raise CoverageV2RevisionError("current pointer semantic SHA differs")
        self._validate_pointer_identity(document)
        return document
