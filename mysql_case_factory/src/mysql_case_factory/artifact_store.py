from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path

import yaml


ARTIFACT_SUBDIRS = (
    "generated_programs",
    "generated_sql",
    "test_plans",
    "evaluations",
    "intermediates",
)

RUN_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
RUN_SUBDIRS = {
    "inputs": "inputs",
    "plans": "plans",
    "jobs": "jobs",
    "case_manifests": "cases/manifests",
    "generated_sql": "cases/sql",
    "reference_executions": "executions/reference",
    "dut_executions": "executions/dut",
    "comparisons": "comparisons",
    "findings": "findings",
    "regression_sql": "regression/sql",
    "regression_expected": "regression/expected",
}
EXECUTION_PROFILE_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _unique_json_object(pairs):
    document = {}
    for key, value in pairs:
        if key in document:
            raise ValueError(f"duplicate JSON key {key}")
        document[key] = value
    return document


def _validate_created_at(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("run.json created_at must be a non-empty timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("run.json created_at must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError("run.json created_at must include a timezone")
    return value


def load_run_manifest(
    run_root: Path | str,
    *,
    expected_run_id: str | None = None,
    expected_metadata: Mapping[str, object] | None = None,
) -> dict:
    """Load and fail-closed validate an initialized run and its fixed layout."""

    root = Path(run_root)
    if root.is_symlink():
        raise ValueError(f"run root must not be a symbolic link: {root}")
    try:
        resolved_root = root.resolve(strict=True)
    except OSError as exc:
        raise ValueError(f"cannot resolve run root {root}: {exc}") from exc
    if not resolved_root.is_dir():
        raise ValueError(f"run root is not a directory: {root}")

    manifest_path = root / "run.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise ValueError(f"run root has no regular run.json: {root}")
    try:
        document = json.loads(
            manifest_path.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_json_object,
        )
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid run.json: {manifest_path}: {exc}") from exc
    except OSError as exc:
        raise ValueError(f"cannot read run.json {manifest_path}: {exc}") from exc
    if not isinstance(document, dict):
        raise ValueError("run.json root must be an object")
    expected_keys = {"schema_version", "run_id", "created_at", "metadata", "layout"}
    if set(document) != expected_keys:
        missing = sorted(expected_keys - set(document))
        unexpected = sorted(set(document) - expected_keys)
        details = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if unexpected:
            details.append("unexpected " + ", ".join(unexpected))
        raise ValueError("run.json has an invalid schema: " + "; ".join(details))
    if document["schema_version"] != 1:
        raise ValueError(
            f"unsupported run.json schema_version {document['schema_version']!r}"
        )
    run_id = document["run_id"]
    if not isinstance(run_id, str) or not RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError(f"run.json has an invalid run_id: {run_id!r}")
    if run_id != root.name:
        raise ValueError(
            f"run.json run_id {run_id!r} does not match directory {root.name!r}"
        )
    if expected_run_id is not None and run_id != expected_run_id:
        raise ValueError(
            f"run.json belongs to run {run_id!r}, not {expected_run_id!r}"
        )
    _validate_created_at(document["created_at"])
    metadata = document["metadata"]
    if not isinstance(metadata, dict):
        raise ValueError("run.json metadata must be an object")
    if "execution_profile_sha256" not in metadata:
        raise ValueError(
            "run.json metadata.execution_profile_sha256 must be explicitly "
            "present as null or a 64-character lowercase SHA-256"
        )
    profile_digest = metadata["execution_profile_sha256"]
    if profile_digest is not None and (
        not isinstance(profile_digest, str)
        or EXECUTION_PROFILE_SHA256_PATTERN.fullmatch(profile_digest) is None
    ):
        raise ValueError(
            "run.json metadata.execution_profile_sha256 must be null or a "
            "64-character lowercase SHA-256"
        )
    if "formal_run" in metadata:
        from .formal_run import FORMAL_RUN_METADATA_KEYS

        if metadata.get("formal_run") is not True or set(metadata) != FORMAL_RUN_METADATA_KEYS:
            raise ValueError("run.json metadata does not match the fixed formal run schema")
    if expected_metadata is not None and metadata != dict(expected_metadata):
        raise ValueError(
            "persisted run metadata differs from the supplied manifest/plan; "
            "create a new run"
        )
    layout = document["layout"]
    if not isinstance(layout, dict) or layout != RUN_SUBDIRS:
        raise ValueError("run.json layout must exactly match the supported run layout")

    for key, relative_path in RUN_SUBDIRS.items():
        relative = Path(relative_path)
        current = root
        for part in relative.parts:
            current = current / part
            if current.is_symlink():
                raise ValueError(
                    f"run.json layout {key} contains a symbolic link: {current}"
                )
        try:
            resolved = current.resolve(strict=True)
            resolved.relative_to(resolved_root)
        except FileNotFoundError as exc:
            raise ValueError(f"run.json layout directory is missing: {current}") from exc
        except (OSError, ValueError) as exc:
            raise ValueError(
                f"run.json layout directory escapes its run root: {current}"
            ) from exc
        if not resolved.is_dir():
            raise ValueError(f"run.json layout path is not a directory: {current}")
    return document


def load_run_execution_profile(run_root: Path | str):
    """Load the run-bound execution profile and verify its immutable snapshot.

    A profile is active only when its canonical semantic digest is present in
    ``run.json``.  A manually copied file is rejected instead of becoming an
    unaudited source of connection settings.
    """

    from .contracts import (
        canonical_execution_profile_yaml,
        execution_profile_sha256,
        load_execution_profile,
    )

    root = Path(run_root)
    manifest = load_run_manifest(root)
    resolved_root = root.resolve(strict=True)
    expected_digest = manifest["metadata"]["execution_profile_sha256"]
    profile_path = root / RUN_SUBDIRS["inputs"] / "execution_profile.yaml"
    if expected_digest is None:
        if profile_path.exists() or profile_path.is_symlink():
            raise ValueError(
                "run has an unbound inputs/execution_profile.yaml; create a new run "
                "with run init --execution-profile"
            )
        return None
    if not isinstance(expected_digest, str) or not EXECUTION_PROFILE_SHA256_PATTERN.fullmatch(
        expected_digest
    ):
        # load_run_manifest already validates this.  Keep this guard local so
        # callers cannot accidentally weaken the profile loader in isolation.
        raise ValueError("run-bound execution profile digest is invalid")
    if profile_path.is_symlink() or not profile_path.is_file():
        raise ValueError(
            "run-bound execution profile must be a regular, non-symbolic-link file"
        )
    try:
        resolved_profile = profile_path.resolve(strict=True)
        resolved_profile.relative_to(resolved_root)
    except (OSError, ValueError) as exc:
        raise ValueError("run-bound execution profile escapes the run root") from exc
    profile = load_execution_profile(resolved_profile)
    actual_digest = execution_profile_sha256(profile)
    if actual_digest != expected_digest:
        raise ValueError(
            "persisted execution profile digest differs from run.json metadata; "
            "create a new run"
        )
    try:
        persisted_text = resolved_profile.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"cannot read persisted execution profile: {exc}") from exc
    if persisted_text != canonical_execution_profile_yaml(profile):
        raise ValueError(
            "persisted execution profile is not the canonical immutable snapshot; "
            "create a new run"
        )
    return profile


def asset_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _prepare_runtime_root(runtime_root: Path | str) -> Path:
    root = Path(runtime_root)
    if root.is_symlink():
        raise ValueError(f"runtime root must not be a symbolic link: {root}")
    root.mkdir(parents=True, exist_ok=True)
    if not root.is_dir():
        raise ValueError(f"runtime root is not a directory: {root}")
    return root


def prepare_artifacts(runtime_root: Path | None = None, clear: bool = False) -> dict[str, Path]:
    root = _prepare_runtime_root(
        Path(runtime_root) if runtime_root is not None else asset_root()
    )
    artifacts_root = ensure_contained_directory(root, "artifacts")

    if clear:
        symlinks = sorted(
            (path for path in artifacts_root.rglob("*") if path.is_symlink()),
            key=str,
        )
        if symlinks:
            raise ValueError(
                "refusing to clear artifacts containing symbolic links: "
                + ", ".join(str(path) for path in symlinks)
            )
        for child in list(artifacts_root.iterdir()):
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()

    paths = {"artifacts_root": artifacts_root}
    for name in ARTIFACT_SUBDIRS:
        path = ensure_contained_directory(artifacts_root, name)
        paths[name] = path
    return paths


def prepare_run(
    runtime_root: Path | None,
    run_id: str,
    metadata: dict | None = None,
    *,
    resume: bool = False,
    created_at: str | None = None,
) -> dict[str, Path]:
    """Create or resume an isolated, append-friendly artifact run.

    A run ID is a logical identifier, never a path.  Existing runs are not
    overwritten unless the caller explicitly asks to resume them.
    """

    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError(f"invalid run_id: {run_id!r}")

    normalized_metadata = dict(metadata or {})
    normalized_metadata.setdefault("execution_profile_sha256", None)

    root = _prepare_runtime_root(
        Path(runtime_root) if runtime_root is not None else asset_root()
    )
    artifacts_root = ensure_contained_directory(root, "artifacts")
    runs_root = ensure_contained_directory(artifacts_root, "runs")
    run_root = runs_root / run_id
    manifest_path = run_root / "run.json"

    if run_root.exists():
        if run_root.is_symlink():
            raise ValueError(f"run root must not be a symbolic link: {run_root}")
        if not resume:
            raise FileExistsError(f"run already exists: {run_root}")
        if not manifest_path.is_file():
            raise ValueError(f"existing run has no manifest: {run_root}")
        load_run_manifest(
            run_root,
            expected_run_id=run_id,
            expected_metadata=normalized_metadata,
        )
    else:
        run_root.mkdir(parents=True, exist_ok=False)

    paths: dict[str, Path] = {
        "artifacts_root": artifacts_root,
        "runs_root": runs_root,
        "run_root": run_root,
        "manifest": manifest_path,
    }
    for key, relative_path in RUN_SUBDIRS.items():
        path = ensure_contained_directory(run_root, relative_path)
        paths[key] = path

    if not manifest_path.exists():
        manifest = {
            "schema_version": 1,
            "run_id": run_id,
            "created_at": created_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "metadata": normalized_metadata,
            "layout": {key: str(path.relative_to(run_root)) for key, path in paths.items() if key in RUN_SUBDIRS},
        }
        write_json(manifest_path, manifest)
    load_run_manifest(
        run_root,
        expected_run_id=run_id,
        expected_metadata=normalized_metadata,
    )
    return paths


def ensure_contained_directory(root: Path | str, relative_path: Path | str) -> Path:
    """Create a run subdirectory without following intermediate symlinks."""

    base = Path(root)
    if base.is_symlink():
        raise ValueError(f"directory root must not be a symbolic link: {base}")
    base.mkdir(parents=True, exist_ok=True)
    resolved_base = base.resolve(strict=True)
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"directory path must stay under {base}: {relative_path}")
    current = base
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"run directory contains a symbolic link: {current}")
        current.mkdir(exist_ok=True)
        if not current.is_dir():
            raise ValueError(f"run directory component is not a directory: {current}")
    resolved = current.resolve(strict=True)
    try:
        resolved.relative_to(resolved_base)
    except ValueError as exc:
        raise ValueError(f"run directory escapes its root: {current}") from exc
    return current


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def write_json(path: Path, content: dict) -> None:
    write_text(path, json.dumps(content, ensure_ascii=False, indent=2) + "\n")


def write_yaml(path: Path, content: dict) -> None:
    write_text(path, yaml.safe_dump(content, allow_unicode=True, sort_keys=False))
