"""Immutable, fail-closed lifecycle for formal PostgreSQL compatibility runs.

The low-level :func:`artifact_store.prepare_run` helper intentionally remains
available for component tests.  A user-facing formal run is stricter: every
planning input is validated before publication, copied into one self-contained
snapshot, and bound by the fixed metadata schema in ``run.json``.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import shutil
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping

import yaml

from .applicability import (
    SHIPPED_UNIVERSE_COUNTS,
    FeatureApplicability,
    load_feature_applicability_index,
    reconcile_applicability_bindings,
)
from .artifact_store import (
    RUN_ID_PATTERN,
    load_run_execution_profile,
    load_run_manifest,
    prepare_run,
    write_json,
)
from .contracts import (
    CoveragePlan,
    ExecutionProfile,
    FeatureManifest,
    canonical_execution_profile_yaml,
    execution_profile_sha256,
    load_coverage_plan,
    load_execution_profile,
    load_feature_manifest,
    verify_feature_source,
)
from .coverage import CoverageObligation, expand_coverage_plan, reconcile_obligations


FORMAL_RUN_METADATA_KEYS = frozenset(
    {
        "formal_run",
        "compatibility_target",
        "feature_id",
        "plan_id",
        "obligation_count",
        "feature_manifest_sha256",
        "feature_source_sha256",
        "coverage_plan_sha256",
        "coverage_obligations_sha256",
        "applicability_index_sha256",
        "applicability_snapshot_manifest_sha256",
        "inventory_snapshot_manifest_sha256",
        "execution_profile_sha256",
    }
)
_SHA256 = __import__("re").compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class _Snapshot:
    source: Path
    payload: bytes
    sha256: str

    def reverify(self) -> None:
        if self.source.is_symlink() or not self.source.is_file():
            raise ValueError(f"formal input is no longer a regular file: {self.source}")
        current = self.source.read_bytes()
        if hashlib.sha256(current).hexdigest() != self.sha256 or current != self.payload:
            raise ValueError(f"formal input changed while being snapshotted: {self.source}")


@dataclass(frozen=True)
class FormalRunInputs:
    manifest: FeatureManifest
    plan: CoveragePlan
    execution_profile: ExecutionProfile
    applicability: FeatureApplicability
    obligations: tuple[CoverageObligation, ...]
    snapshots: tuple[_Snapshot, ...]
    manifest_snapshot: _Snapshot
    source_snapshot: _Snapshot
    plan_snapshot: bytes
    profile_snapshot: bytes
    applicability_index_snapshot: _Snapshot
    inventory_files: tuple[tuple[str, _Snapshot], ...]
    applicability_bundle_files: tuple[tuple[str, _Snapshot], ...]
    applicability_repository_files: tuple[tuple[str, _Snapshot], ...]


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_bytes(document: Mapping[str, Any]) -> bytes:
    return (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _yaml_bytes(document: Mapping[str, Any]) -> bytes:
    return yaml.safe_dump(
        dict(document), allow_unicode=True, sort_keys=False
    ).encode("utf-8")


def _read_snapshot(path: str | Path, location: str) -> _Snapshot:
    source = Path(path)
    if source.is_symlink() or not source.is_file():
        raise ValueError(f"{location} must be a regular non-symbolic-link file: {source}")
    try:
        resolved = source.resolve(strict=True)
        payload = source.read_bytes()
    except OSError as exc:
        raise ValueError(f"cannot read {location} {source}: {exc}") from exc
    return _Snapshot(resolved, payload, _sha256(payload))


def _portable_relative(value: str, location: str) -> PurePosixPath:
    if not value or "\\" in value:
        raise ValueError(f"{location} must be a portable relative path")
    relative = PurePosixPath(value)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ValueError(f"{location} must stay under its snapshot root")
    return relative


def _contained_snapshot(root: Path, relative: str, location: str) -> _Snapshot:
    portable = _portable_relative(relative, location)
    resolved_root = root.resolve(strict=True)
    candidate = root.joinpath(*portable.parts)
    if candidate.is_symlink():
        raise ValueError(f"{location} must not be a symbolic link: {candidate}")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(resolved_root)
    except (OSError, ValueError) as exc:
        raise ValueError(f"{location} escapes its declared root: {relative}") from exc
    return _read_snapshot(resolved, location)


def _require_resolved_questions(manifest: FeatureManifest) -> None:
    if "unresolved_questions" not in manifest.metadata:
        raise ValueError(
            "feature manifest metadata.unresolved_questions must be explicitly "
            "declared as an empty list before formal run init"
        )
    unresolved = manifest.metadata["unresolved_questions"]
    if not isinstance(unresolved, list):
        raise ValueError(
            "feature manifest metadata.unresolved_questions must be a list"
        )
    if unresolved:
        raise ValueError(
            "feature manifest has unresolved_questions; resolve and empty the list "
            "before formal run init"
        )


def _obligations_document(
    plan: CoveragePlan,
    obligations: Iterable[CoverageObligation],
) -> dict[str, Any]:
    materialized = tuple(obligations)
    reconciliation = reconcile_obligations(materialized)
    return {
        "schema_version": 1,
        "kind": "coverage_obligation_set",
        "plan_id": plan.plan_id,
        "feature_id": plan.feature_id,
        "obligations": [item.to_dict() for item in materialized],
        "reconciliation": reconciliation.to_dict(),
    }


def _inventory_snapshots(
    plan: CoveragePlan,
    inventory_root: Path,
) -> tuple[tuple[str, _Snapshot], ...]:
    entries: dict[str, _Snapshot] = {}
    for axis_id, axis in plan.axes.items():
        if axis.inventory_source.startswith("inline:"):
            continue
        source_path = axis.inventory_source.split("#", 1)[0]
        snapshot = _contained_snapshot(
            inventory_root,
            source_path,
            f"coverage axis {axis_id} inventory source",
        )
        previous = entries.setdefault(source_path, snapshot)
        if previous.sha256 != snapshot.sha256:
            raise ValueError(f"inventory source changed while reading: {source_path}")
    return tuple(sorted(entries.items()))


def _applicability_snapshots(
    applicability: FeatureApplicability,
    repository_root: Path,
) -> tuple[
    tuple[tuple[str, _Snapshot], ...],
    tuple[tuple[str, _Snapshot], ...],
]:
    index_root = applicability.index_path.parent.resolve(strict=True)
    bundle: dict[str, _Snapshot] = {
        "feature_applicability_index.yaml": _read_snapshot(
            applicability.index_path, "feature applicability index"
        )
    }
    for review in applicability.reviews:
        resolved = review.source_path.resolve(strict=True)
        try:
            relative = resolved.relative_to(index_root).as_posix()
        except ValueError as exc:
            raise ValueError("applicability review escapes the applicability bundle") from exc
        bundle[relative] = _read_snapshot(resolved, f"applicability review {relative}")

    repository = repository_root.resolve(strict=True)
    repository_entries: dict[str, _Snapshot] = {}
    ledger = applicability.universe.source_path.resolve(strict=True)
    try:
        ledger_relative = ledger.relative_to(repository).as_posix()
    except ValueError as exc:
        raise ValueError("applicability ledger escapes repository_root") from exc
    repository_entries[ledger_relative] = _read_snapshot(
        ledger, "applicability universe ledger"
    )
    for row, value_review in applicability.covered_rows():
        witness = value_review.matrix_witness
        if witness is None:
            raise ValueError(f"covered applicability row has no matrix witness: {row.row_id}")
        snapshot = _contained_snapshot(
            repository_root,
            witness.path,
            f"matrix witness for {row.row_id}",
        )
        if snapshot.sha256 != witness.sha256:
            raise ValueError(f"matrix witness SHA mismatch for {row.row_id}")
        previous = repository_entries.setdefault(witness.path, snapshot)
        if previous.sha256 != snapshot.sha256:
            raise ValueError(f"matrix witness changed while reading: {witness.path}")
    return tuple(sorted(bundle.items())), tuple(sorted(repository_entries.items()))


def load_formal_inputs(
    *,
    manifest_path: str | Path,
    plan_path: str | Path,
    execution_profile_path: str | Path,
    applicability_index_path: str | Path,
    source_root: str | Path | None,
    inventory_root: str | Path,
) -> FormalRunInputs:
    """Validate and materialize every input without creating a run directory."""

    manifest_file = Path(manifest_path)
    plan_file = Path(plan_path)
    profile_file = Path(execution_profile_path)
    index_file = Path(applicability_index_path)
    inventory_repository = Path(inventory_root).resolve(strict=True)

    manifest = load_feature_manifest(
        manifest_file, verify_source=True, source_root=source_root
    )
    _require_resolved_questions(manifest)
    source_file = verify_feature_source(
        manifest, manifest_file, source_root=source_root
    )
    profile = load_execution_profile(profile_file)
    plan = load_coverage_plan(
        plan_file, manifest=manifest, inventory_root=inventory_repository
    )
    requirements = {item.requirement_id for item in manifest.requirements}
    applicability = load_feature_applicability_index(
        index_file,
        repository_root=inventory_repository,
        known_requirement_ids=requirements,
        require_complete=True,
        expected_counts=SHIPPED_UNIVERSE_COUNTS,
        draft=False,
    )
    if applicability.feature_id != manifest.feature_id:
        raise ValueError("applicability feature_id does not match feature manifest")
    if plan.feature_id != manifest.feature_id:
        raise ValueError("coverage plan feature_id does not match feature manifest")
    obligations = expand_coverage_plan(plan, require_complete=True)
    applicability_report = reconcile_applicability_bindings(
        applicability, obligations
    )
    if not applicability_report.complete:
        raise ValueError(
            "coverage plan does not completely reconcile the applicability review: "
            + json.dumps(applicability_report.to_dict(), sort_keys=True)
        )

    manifest_snapshot = _read_snapshot(manifest_file, "feature manifest")
    source_snapshot = _read_snapshot(source_file, "feature source")
    if source_snapshot.sha256 != manifest.source["sha256"]:
        raise ValueError("feature source changed while formal inputs were loaded")
    plan_file_snapshot = _read_snapshot(plan_file, "coverage plan")
    profile_file_snapshot = _read_snapshot(profile_file, "execution profile")
    applicability_index_snapshot = _read_snapshot(
        index_file, "feature applicability index"
    )
    inventory_files = _inventory_snapshots(plan, inventory_repository)
    bundle_files, repository_files = _applicability_snapshots(
        applicability, inventory_repository
    )
    snapshots = tuple(
        {
            snapshot.source: snapshot
            for snapshot in (
                manifest_snapshot,
                source_snapshot,
                plan_file_snapshot,
                profile_file_snapshot,
                applicability_index_snapshot,
                *(item[1] for item in inventory_files),
                *(item[1] for item in bundle_files),
                *(item[1] for item in repository_files),
            )
        }.values()
    )
    # Re-load after byte capture.  This closes the load/read window: a changed
    # source can only make initialization fail, never publish mixed inputs.
    for snapshot in snapshots:
        snapshot.reverify()
    return FormalRunInputs(
        manifest=manifest,
        plan=plan,
        execution_profile=profile,
        applicability=applicability,
        obligations=tuple(obligations),
        snapshots=snapshots,
        manifest_snapshot=manifest_snapshot,
        source_snapshot=source_snapshot,
        plan_snapshot=_yaml_bytes(plan.to_dict()),
        profile_snapshot=canonical_execution_profile_yaml(profile).encode("utf-8"),
        applicability_index_snapshot=applicability_index_snapshot,
        inventory_files=inventory_files,
        applicability_bundle_files=bundle_files,
        applicability_repository_files=repository_files,
    )


def _snapshot_manifest(kind: str, files: Iterable[tuple[str, _Snapshot]]) -> bytes:
    entries = [
        {"path": path, "sha256": snapshot.sha256}
        for path, snapshot in sorted(files)
    ]
    return _json_bytes(
        {"schema_version": 1, "kind": kind, "files": entries}
    )


def _metadata(inputs: FormalRunInputs) -> tuple[dict[str, Any], bytes, bytes, bytes]:
    obligations_payload = _json_bytes(
        _obligations_document(inputs.plan, inputs.obligations)
    )
    inventory_manifest = _snapshot_manifest(
        "inventory_snapshot_manifest", inputs.inventory_files
    )
    applicability_manifest = _snapshot_manifest(
        "applicability_snapshot_manifest",
        (
            *((f"bundle/{path}", snap) for path, snap in inputs.applicability_bundle_files),
            *((f"repository/{path}", snap) for path, snap in inputs.applicability_repository_files),
        ),
    )
    metadata = {
        "formal_run": True,
        "compatibility_target": "PostgreSQL 18.4",
        "feature_id": inputs.manifest.feature_id,
        "plan_id": inputs.plan.plan_id,
        "obligation_count": len(inputs.obligations),
        "feature_manifest_sha256": _sha256(inputs.manifest_snapshot.payload),
        "feature_source_sha256": inputs.source_snapshot.sha256,
        "coverage_plan_sha256": _sha256(inputs.plan_snapshot),
        "coverage_obligations_sha256": _sha256(obligations_payload),
        "applicability_index_sha256": inputs.applicability_index_snapshot.sha256,
        "applicability_snapshot_manifest_sha256": _sha256(applicability_manifest),
        "inventory_snapshot_manifest_sha256": _sha256(inventory_manifest),
        "execution_profile_sha256": execution_profile_sha256(
            inputs.execution_profile
        ),
    }
    return metadata, obligations_payload, inventory_manifest, applicability_manifest


def _write_payload(root: Path, relative: str, payload: bytes) -> None:
    portable = _portable_relative(relative, "formal snapshot destination")
    destination = root.joinpath(*portable.parts)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_symlink():
        raise ValueError(f"formal snapshot destination is a symlink: {destination}")
    destination.write_bytes(payload)


@contextmanager
def _runs_lock(runs_root: Path):
    lock_path = runs_root / ".formal-runs.lock"
    descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def initialize_formal_run(
    runtime_root: str | Path,
    run_id: str,
    inputs: FormalRunInputs,
    *,
    resume: bool = False,
) -> dict[str, Path]:
    """Atomically publish or strictly resume a self-contained formal run."""

    if RUN_ID_PATTERN.fullmatch(run_id) is None:
        raise ValueError(f"invalid run_id: {run_id!r}")
    runtime = Path(runtime_root)
    if runtime.is_symlink():
        raise ValueError(f"runtime root must not be a symbolic link: {runtime}")
    runtime.mkdir(parents=True, exist_ok=True)
    artifacts = runtime / "artifacts"
    if artifacts.is_symlink():
        raise ValueError("artifacts root must not be a symbolic link")
    artifacts.mkdir(exist_ok=True)
    runs_root = artifacts / "runs"
    if runs_root.is_symlink():
        raise ValueError("runs root must not be a symbolic link")
    runs_root.mkdir(exist_ok=True)
    final_root = runs_root / run_id
    metadata, obligations_payload, inventory_manifest, applicability_manifest = _metadata(inputs)

    with _runs_lock(runs_root):
        if final_root.exists() or final_root.is_symlink():
            if not resume:
                raise FileExistsError(f"run already exists: {final_root}")
            validate_formal_run(final_root, expected_metadata=metadata)
            for snapshot in inputs.snapshots:
                snapshot.reverify()
            return {"run_root": final_root, "jobs": final_root / "jobs/jobs.json"}
        if resume:
            raise FileNotFoundError(f"cannot resume missing run: {final_root}")

        staging_parent = Path(
            tempfile.mkdtemp(prefix=f".{run_id}.staging-", dir=runs_root)
        )
        try:
            paths = prepare_run(staging_parent, run_id, metadata=metadata)
            stage_root = paths["run_root"]
            source_relative = _portable_relative(
                str(inputs.manifest.source["path"]), "feature source path"
            )
            if source_relative.as_posix() in {
                "feature_manifest.yaml",
                "execution_profile.yaml",
            }:
                raise ValueError("feature source path conflicts with a formal input filename")
            _write_payload(
                stage_root,
                "inputs/feature_manifest.yaml",
                inputs.manifest_snapshot.payload,
            )
            _write_payload(
                stage_root,
                f"inputs/{source_relative.as_posix()}",
                inputs.source_snapshot.payload,
            )
            _write_payload(
                stage_root,
                "inputs/execution_profile.yaml",
                inputs.profile_snapshot,
            )
            _write_payload(stage_root, "plans/coverage_plan.yaml", inputs.plan_snapshot)
            _write_payload(
                stage_root, "plans/coverage_obligations.json", obligations_payload
            )
            for relative, snapshot in inputs.inventory_files:
                _write_payload(
                    stage_root,
                    f"plans/inventory/repository/{relative}",
                    snapshot.payload,
                )
            _write_payload(
                stage_root,
                "plans/inventory/snapshot_manifest.json",
                inventory_manifest,
            )
            for relative, snapshot in inputs.applicability_bundle_files:
                _write_payload(
                    stage_root,
                    f"plans/applicability/bundle/{relative}",
                    snapshot.payload,
                )
            for relative, snapshot in inputs.applicability_repository_files:
                _write_payload(
                    stage_root,
                    f"plans/applicability/repository/{relative}",
                    snapshot.payload,
                )
            _write_payload(
                stage_root,
                "plans/applicability/snapshot_manifest.json",
                applicability_manifest,
            )
            from .jobs import JobStore

            JobStore.initialize(stage_root / "jobs/jobs.json", inputs.plan)
            validate_formal_run(stage_root, expected_metadata=metadata)
            for snapshot in inputs.snapshots:
                snapshot.reverify()
            os.replace(stage_root, final_root)
        finally:
            shutil.rmtree(staging_parent, ignore_errors=True)
    validate_formal_run(final_root, expected_metadata=metadata)
    return {"run_root": final_root, "jobs": final_root / "jobs/jobs.json"}


def _load_snapshot_manifest(path: Path, kind: str) -> tuple[tuple[str, str], ...]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"missing regular {kind}: {path}")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid {kind}: {path}") from exc
    if not isinstance(document, dict) or set(document) != {
        "schema_version", "kind", "files"
    }:
        raise ValueError(f"{kind} has an invalid schema")
    if document["schema_version"] != 1 or document["kind"] != kind:
        raise ValueError(f"{kind} identity is invalid")
    if not isinstance(document["files"], list):
        raise ValueError(f"{kind}.files must be a list")
    entries: list[tuple[str, str]] = []
    for index, raw in enumerate(document["files"]):
        if not isinstance(raw, dict) or set(raw) != {"path", "sha256"}:
            raise ValueError(f"{kind}.files[{index}] has an invalid schema")
        relative = raw["path"]
        digest = raw["sha256"]
        _portable_relative(relative, f"{kind}.files[{index}].path")
        if not isinstance(digest, str) or _SHA256.fullmatch(digest) is None:
            raise ValueError(f"{kind}.files[{index}].sha256 is invalid")
        entries.append((relative, digest))
    if entries != sorted(entries) or len(entries) != len(set(path for path, _ in entries)):
        raise ValueError(f"{kind}.files must be sorted and unique")
    return tuple(entries)


def _verify_manifest_files(
    root: Path,
    entries: Iterable[tuple[str, str]],
    *,
    allowed_prefix: str | None = None,
) -> None:
    expected: set[str] = set()
    for relative, digest in entries:
        if allowed_prefix is not None and not relative.startswith(allowed_prefix + "/"):
            raise ValueError(f"snapshot entry is outside {allowed_prefix}: {relative}")
        snapshot = _contained_snapshot(root, relative, "formal snapshot file")
        if snapshot.sha256 != digest:
            raise ValueError(f"formal snapshot digest mismatch: {relative}")
        expected.add(relative)
    scan_root = root / allowed_prefix if allowed_prefix is not None else root
    actual = {
        path.relative_to(root).as_posix()
        for path in scan_root.rglob("*")
        if path.is_file() or path.is_symlink()
    }
    if actual != expected:
        raise ValueError(
            f"formal snapshot file set differs under {allowed_prefix or '.'}: "
            f"missing={sorted(expected - actual)}, unexpected={sorted(actual - expected)}"
        )


def validate_formal_run(
    run_root: str | Path,
    *,
    expected_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Revalidate every immutable formal snapshot and cross-contract binding."""

    root = Path(run_root)
    run_document = load_run_manifest(root, expected_metadata=expected_metadata)
    metadata = run_document["metadata"]
    if metadata.get("formal_run") is not True or set(metadata) != FORMAL_RUN_METADATA_KEYS:
        raise ValueError("run.json metadata is not the fixed formal run schema")
    digest_keys = FORMAL_RUN_METADATA_KEYS - {
        "formal_run", "compatibility_target", "feature_id", "plan_id", "obligation_count"
    }
    for key in digest_keys:
        if not isinstance(metadata[key], str) or _SHA256.fullmatch(metadata[key]) is None:
            raise ValueError(f"run.json metadata.{key} must be a SHA-256")
    if metadata["compatibility_target"] != "PostgreSQL 18.4":
        raise ValueError("formal run compatibility_target must be PostgreSQL 18.4")

    inputs_root = root / "inputs"
    manifest_path = inputs_root / "feature_manifest.yaml"
    manifest_snapshot = _read_snapshot(manifest_path, "persisted feature manifest")
    if manifest_snapshot.sha256 != metadata["feature_manifest_sha256"]:
        raise ValueError("persisted feature manifest digest differs from run.json")
    manifest = load_feature_manifest(manifest_path, verify_source=True)
    _require_resolved_questions(manifest)
    source_path = verify_feature_source(manifest, manifest_path)
    source_snapshot = _read_snapshot(source_path, "persisted feature source")
    if source_snapshot.sha256 != metadata["feature_source_sha256"]:
        raise ValueError("persisted feature source digest differs from run.json")
    profile = load_run_execution_profile(root)
    if profile is None:
        raise ValueError("formal run must bind an execution profile")

    plan_path = root / "plans/coverage_plan.yaml"
    plan_snapshot = _read_snapshot(plan_path, "persisted coverage plan")
    if plan_snapshot.sha256 != metadata["coverage_plan_sha256"]:
        raise ValueError("persisted coverage plan digest differs from run.json")
    inventory_repo = root / "plans/inventory/repository"
    plan = load_coverage_plan(
        plan_path, manifest=manifest, inventory_root=inventory_repo
    )
    obligations = expand_coverage_plan(plan, require_complete=True)
    obligations_document = _obligations_document(plan, obligations)
    obligations_path = root / "plans/coverage_obligations.json"
    obligations_snapshot = _read_snapshot(
        obligations_path, "persisted coverage obligations"
    )
    if obligations_snapshot.sha256 != metadata["coverage_obligations_sha256"]:
        raise ValueError("persisted coverage obligation digest differs from run.json")
    if obligations_snapshot.payload != _json_bytes(obligations_document):
        raise ValueError("persisted coverage obligations differ from the persisted plan")

    inventory_manifest_path = root / "plans/inventory/snapshot_manifest.json"
    inventory_manifest_snapshot = _read_snapshot(
        inventory_manifest_path, "inventory snapshot manifest"
    )
    if inventory_manifest_snapshot.sha256 != metadata["inventory_snapshot_manifest_sha256"]:
        raise ValueError("inventory snapshot manifest digest differs from run.json")
    inventory_entries = _load_snapshot_manifest(
        inventory_manifest_path, "inventory_snapshot_manifest"
    )
    expected_inventory_paths = sorted(
        {
            axis.inventory_source.split("#", 1)[0]
            for axis in plan.axes.values()
            if not axis.inventory_source.startswith("inline:")
        }
    )
    if [path for path, _ in inventory_entries] != expected_inventory_paths:
        raise ValueError("inventory snapshot manifest does not match coverage plan sources")
    _verify_manifest_files(
        inventory_repo,
        inventory_entries,
    )

    applicability_root = root / "plans/applicability"
    bundle_root = applicability_root / "bundle"
    repository_root = applicability_root / "repository"
    index_path = bundle_root / "feature_applicability_index.yaml"
    index_snapshot = _read_snapshot(index_path, "persisted applicability index")
    if index_snapshot.sha256 != metadata["applicability_index_sha256"]:
        raise ValueError("persisted applicability index digest differs from run.json")
    applicability = load_feature_applicability_index(
        index_path,
        repository_root=repository_root,
        known_requirement_ids={item.requirement_id for item in manifest.requirements},
        require_complete=True,
        expected_counts=SHIPPED_UNIVERSE_COUNTS,
        draft=False,
    )
    applicability_manifest_path = applicability_root / "snapshot_manifest.json"
    applicability_manifest_snapshot = _read_snapshot(
        applicability_manifest_path, "applicability snapshot manifest"
    )
    if (
        applicability_manifest_snapshot.sha256
        != metadata["applicability_snapshot_manifest_sha256"]
    ):
        raise ValueError("applicability snapshot manifest digest differs from run.json")
    applicability_entries = _load_snapshot_manifest(
        applicability_manifest_path, "applicability_snapshot_manifest"
    )
    bundle_entries = tuple(
        (path.removeprefix("bundle/"), digest)
        for path, digest in applicability_entries
        if path.startswith("bundle/")
    )
    repository_entries = tuple(
        (path.removeprefix("repository/"), digest)
        for path, digest in applicability_entries
        if path.startswith("repository/")
    )
    if len(bundle_entries) + len(repository_entries) != len(applicability_entries):
        raise ValueError("applicability snapshot manifest contains an invalid root")
    _verify_manifest_files(bundle_root, bundle_entries)
    _verify_manifest_files(repository_root, repository_entries)
    report = reconcile_applicability_bindings(applicability, obligations)
    if not report.complete:
        raise ValueError(
            "persisted applicability bindings no longer reconcile: "
            + json.dumps(report.to_dict(), sort_keys=True)
        )

    if manifest.feature_id != metadata["feature_id"] or plan.feature_id != metadata["feature_id"]:
        raise ValueError("formal run feature identity differs across snapshots")
    if plan.plan_id != metadata["plan_id"]:
        raise ValueError("formal run plan identity differs from run.json")
    if len(obligations) != metadata["obligation_count"]:
        raise ValueError("formal run obligation count differs from run.json")
    return {
        "run": run_document,
        "manifest": manifest,
        "plan": plan,
        "profile": profile,
        "applicability": applicability,
        "obligations": obligations,
        "applicability_reconciliation": report,
    }


__all__ = [
    "FORMAL_RUN_METADATA_KEYS",
    "FormalRunInputs",
    "initialize_formal_run",
    "load_formal_inputs",
    "validate_formal_run",
]
