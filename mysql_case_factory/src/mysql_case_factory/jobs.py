"""Durable state machine for one independently resumable job per test point."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Optional, Sequence

import fcntl
import yaml

from .artifact_store import load_run_execution_profile, load_run_manifest
from .contracts import (
    CaseManifest,
    CoveragePlan,
    ExecutionProfile,
    load_case_manifest,
    load_coverage_plan,
)
from .coverage import expand_coverage_plan, reconcile_case_manifests
from .differential import (
    EndpointIdentity,
    ExecutionRecord,
    NormalizationProfile,
    compare_execution_records,
    validate_comparable_endpoint_pair,
    validate_expected_failure_oracle,
    validate_basic_endpoint_identity,
    validate_endpoint_identity,
)
from .feature_plan import validate_coverage_plan
from .sql_safety import (
    validate_sql_for_basic_runner,
    validate_sql_for_external_copy_ingest,
)
from .regression_style import (
    ExecutionTranscript,
    audit_complete_table_script,
    audit_catalog_observability,
    build_regression_batch_mapping,
    compare_two_run_transcripts,
    validate_huawei_sql_header,
)


JOB_STATES = (
    "planned",
    "audited",
    "ready",
    "generated",
    "linted",
    "executed_reference",
    "executed_dut",
    "compared",
    "triaged",
    "packaged",
    "failed",
)

FORWARD_TRANSITIONS = {
    "planned": "audited",
    "audited": "ready",
    "ready": "generated",
    "generated": "linted",
    "linted": "executed_reference",
    "executed_reference": "executed_dut",
    "executed_dut": "compared",
    "compared": "triaged",
    "triaged": "packaged",
}
EVIDENCE_STATES = tuple(FORWARD_TRANSITIONS.values())
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class InvalidJobTransition(ValueError):
    """Raised when a caller attempts to skip or reverse a lifecycle state."""


class DependencyNotReadyError(InvalidJobTransition):
    """Raised when a dependent job is made ready before its prerequisites."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _plan_digest(plan: CoveragePlan) -> str:
    encoded = json.dumps(
        plan.to_dict(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _unique_json_object(pairs):
    document = {}
    for key, value in pairs:
        if key in document:
            raise ValueError(f"duplicate JSON key {key}")
        document[key] = value
    return document


def _validate_evidence_path(path: str, location: str) -> None:
    if "\\" in path:
        raise ValueError(f"{location} must use portable forward slashes")
    portable = PurePosixPath(path)
    if portable.is_absolute() or ".." in portable.parts or not portable.parts:
        raise ValueError(f"{location} must stay under the run root")


@contextmanager
def _exclusive_store_lock(path: Path):
    """Serialize read-modify-write cycles across agents/processes."""

    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_name(f".{path.name}.lock")
    with lock_path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@dataclass(frozen=True)
class JobRecord:
    job_id: str
    title: str
    dependencies: tuple[str, ...]
    state: str = "planned"
    attempts: int = 1
    resume_state: Optional[str] = None
    last_error: Optional[str] = None
    updated_at: str = ""
    evidence: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    evidence_sha256: Mapping[str, Mapping[str, str]] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any], location: str = "job") -> "JobRecord":
        if not isinstance(raw, Mapping):
            raise ValueError(f"{location} must be a mapping")
        expected_keys = {
            "job_id",
            "title",
            "dependencies",
            "state",
            "attempts",
            "resume_state",
            "last_error",
            "updated_at",
            "evidence",
            "evidence_sha256",
        }
        if set(raw) != expected_keys:
            raise ValueError(f"{location} has an invalid job-record schema")
        job_id = raw.get("job_id")
        title = raw.get("title")
        state = raw.get("state")
        dependencies = raw.get("dependencies", [])
        attempts = raw.get("attempts", 1)
        if not isinstance(job_id, str) or not job_id:
            raise ValueError(f"{location}.job_id must be a non-empty string")
        if not isinstance(title, str) or not title:
            raise ValueError(f"{location}.title must be a non-empty string")
        if state not in JOB_STATES:
            raise ValueError(f"{location}.state is invalid: {state!r}")
        if not isinstance(dependencies, list) or any(
            not isinstance(item, str) or not item for item in dependencies
        ):
            raise ValueError(f"{location}.dependencies must be a string list")
        if not isinstance(attempts, int) or isinstance(attempts, bool) or attempts < 1:
            raise ValueError(f"{location}.attempts must be a positive integer")
        resume_state = raw.get("resume_state")
        if resume_state is not None and resume_state not in FORWARD_TRANSITIONS:
            raise ValueError(f"{location}.resume_state is invalid: {resume_state!r}")
        last_error = raw.get("last_error")
        if last_error is not None and not isinstance(last_error, str):
            raise ValueError(f"{location}.last_error must be a string or null")
        updated_at = raw.get("updated_at", "")
        if not isinstance(updated_at, str):
            raise ValueError(f"{location}.updated_at must be a string")
        if state == "failed" and resume_state is None:
            raise ValueError(f"{location}.resume_state is required for failed jobs")
        if state != "failed" and resume_state is not None:
            raise ValueError(f"{location}.resume_state is only valid for failed jobs")
        raw_evidence = raw.get("evidence", {})
        if not isinstance(raw_evidence, Mapping):
            raise ValueError(f"{location}.evidence must be an object")
        evidence: dict[str, tuple[str, ...]] = {}
        for evidence_state, paths in raw_evidence.items():
            if evidence_state not in JOB_STATES or evidence_state in ("planned", "failed"):
                raise ValueError(
                    f"{location}.evidence has invalid state {evidence_state!r}"
                )
            if not isinstance(paths, list) or not paths or any(
                not isinstance(path, str) or not path.strip() for path in paths
            ):
                raise ValueError(
                    f"{location}.evidence.{evidence_state} must be a non-empty string list"
                )
            if len(paths) != len(set(paths)):
                raise ValueError(
                    f"{location}.evidence.{evidence_state} contains duplicate paths"
                )
            for index, path in enumerate(paths):
                _validate_evidence_path(
                    path,
                    f"{location}.evidence.{evidence_state}[{index}]",
                )
            evidence[str(evidence_state)] = tuple(paths)
        raw_evidence_sha256 = raw.get("evidence_sha256", {})
        if not isinstance(raw_evidence_sha256, Mapping):
            raise ValueError(f"{location}.evidence_sha256 must be an object")
        evidence_sha256: dict[str, dict[str, str]] = {}
        for evidence_state, path_digests in raw_evidence_sha256.items():
            if evidence_state not in evidence:
                raise ValueError(
                    f"{location}.evidence_sha256 has unexpected state {evidence_state!r}"
                )
            if not isinstance(path_digests, Mapping):
                raise ValueError(
                    f"{location}.evidence_sha256.{evidence_state} must be an object"
                )
            if set(path_digests) != set(evidence[evidence_state]):
                raise ValueError(
                    f"{location}.evidence_sha256.{evidence_state} must cover exactly its evidence paths"
                )
            normalized_digests: dict[str, str] = {}
            for path, digest in path_digests.items():
                if not isinstance(path, str) or not isinstance(digest, str) or not SHA256_PATTERN.fullmatch(digest):
                    raise ValueError(
                        f"{location}.evidence_sha256.{evidence_state} contains an invalid SHA256"
                    )
                normalized_digests[path] = digest
            evidence_sha256[str(evidence_state)] = normalized_digests
        progress_state = resume_state if state == "failed" else state
        expected_evidence = (
            set(EVIDENCE_STATES[: EVIDENCE_STATES.index(progress_state) + 1])
            if progress_state in EVIDENCE_STATES
            else set()
        )
        if set(evidence) != expected_evidence:
            missing = sorted(expected_evidence - set(evidence))
            unexpected = sorted(set(evidence) - expected_evidence)
            details = []
            if missing:
                details.append("missing " + ", ".join(missing))
            if unexpected:
                details.append("unexpected " + ", ".join(unexpected))
            raise ValueError(
                f"{location}.evidence does not match progress state {progress_state}: "
                + "; ".join(details)
            )
        if set(evidence_sha256) != expected_evidence:
            raise ValueError(
                f"{location}.evidence_sha256 does not match progress state {progress_state}"
            )
        return cls(
            job_id=job_id,
            title=title,
            dependencies=tuple(dependencies),
            state=state,
            attempts=attempts,
            resume_state=resume_state,
            last_error=last_error,
            updated_at=updated_at,
            evidence=evidence,
            evidence_sha256=evidence_sha256,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "title": self.title,
            "dependencies": list(self.dependencies),
            "state": self.state,
            "attempts": self.attempts,
            "resume_state": self.resume_state,
            "last_error": self.last_error,
            "updated_at": self.updated_at,
            "evidence": {
                state: list(paths) for state, paths in self.evidence.items()
            },
            "evidence_sha256": {
                state: dict(path_digests)
                for state, path_digests in self.evidence_sha256.items()
            },
        }


class JobStore:
    """A JSON-backed job registry with atomic state transitions."""

    schema_version = 3

    def __init__(
        self,
        path: Path,
        plan_id: str,
        feature_id: str,
        plan_digest: str,
        jobs: Mapping[str, JobRecord],
    ):
        self.path = path
        self.plan_id = plan_id
        self.feature_id = feature_id
        self.plan_digest = plan_digest
        self._jobs = dict(jobs)

    @classmethod
    def initialize(cls, path: str | Path, plan: CoveragePlan) -> "JobStore":
        """Create a store or resume it without overwriting completed work."""

        validate_coverage_plan(plan)
        target = Path(path)
        expected_digest = _plan_digest(plan)
        if target.exists():
            store = cls.open(target)
            if store.plan_id != plan.plan_id:
                raise ValueError(
                    f"job store belongs to plan {store.plan_id}, not {plan.plan_id}"
                )
            if store.feature_id != plan.feature_id:
                raise ValueError(
                    f"job store belongs to feature {store.feature_id}, not {plan.feature_id}"
                )
            if store.plan_digest != expected_digest:
                raise ValueError(
                    "coverage plan content changed; create a new run instead of resuming this job store"
                )
            plan_points = {point.test_point_id: point for point in plan.test_points}
            removed = sorted(set(store._jobs) - set(plan_points))
            if removed:
                raise ValueError(
                    "coverage plan removed persisted jobs: " + ", ".join(removed)
                )
            changed = False
            for job_id, record in store._jobs.items():
                point = plan_points[job_id]
                if record.dependencies != point.dependencies:
                    raise ValueError(f"persisted dependencies changed for job {job_id}")
            for point in plan.test_points:
                if point.test_point_id not in store._jobs:
                    store._jobs[point.test_point_id] = JobRecord(
                        job_id=point.test_point_id,
                        title=point.title,
                        dependencies=point.dependencies,
                        updated_at=_now(),
                    )
                    changed = True
            if changed:
                store._persist()
            return store

        jobs = {
            point.test_point_id: JobRecord(
                job_id=point.test_point_id,
                title=point.title,
                dependencies=point.dependencies,
                updated_at=_now(),
            )
            for point in plan.test_points
        }
        store = cls(target, plan.plan_id, plan.feature_id, expected_digest, jobs)
        store._persist()
        return store

    @classmethod
    def open(cls, path: str | Path) -> "JobStore":
        target = Path(path)
        try:
            raw = json.loads(
                target.read_text(encoding="utf-8"),
                object_pairs_hook=_unique_json_object,
            )
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid job store JSON: {target}: {exc}") from exc
        except OSError as exc:
            raise ValueError(f"cannot read job store {target}: {exc}") from exc
        if not isinstance(raw, dict):
            raise ValueError("job store root must be an object")
        expected_keys = {
            "schema_version",
            "kind",
            "plan_id",
            "feature_id",
            "plan_digest",
            "jobs",
        }
        if set(raw) != expected_keys:
            raise ValueError("job store root has an invalid schema")
        if raw.get("schema_version") != cls.schema_version:
            raise ValueError(f"unsupported job store schema_version {raw.get('schema_version')!r}")
        if raw.get("kind") != "test_point_job_store":
            raise ValueError("job store kind must be test_point_job_store")
        plan_id = raw.get("plan_id")
        feature_id = raw.get("feature_id")
        plan_digest = raw.get("plan_digest")
        if not isinstance(plan_id, str) or not plan_id:
            raise ValueError("job store plan_id must be a non-empty string")
        if not isinstance(feature_id, str) or not feature_id:
            raise ValueError("job store feature_id must be a non-empty string")
        if (
            not isinstance(plan_digest, str)
            or len(plan_digest) != 64
            or any(character not in "0123456789abcdef" for character in plan_digest)
        ):
            raise ValueError("job store plan_digest must be a SHA256 hex digest")
        job_documents = raw.get("jobs")
        if not isinstance(job_documents, list):
            raise ValueError("job store jobs must be a list")
        records = [
            JobRecord.from_dict(item, f"jobs[{index}]")
            for index, item in enumerate(job_documents)
        ]
        jobs = {record.job_id: record for record in records}
        if len(jobs) != len(records):
            raise ValueError("job store contains duplicate job ids")
        for record in records:
            for dependency in record.dependencies:
                if dependency not in jobs:
                    raise ValueError(
                        f"job {record.job_id} references missing persisted dependency {dependency}"
                    )
        return cls(target, plan_id, feature_id, plan_digest, jobs)

    def get(self, job_id: str) -> JobRecord:
        try:
            return self._jobs[job_id]
        except KeyError as exc:
            raise KeyError(f"unknown job {job_id}") from exc

    def list(self) -> tuple[JobRecord, ...]:
        return tuple(self._jobs.values())

    def transition(
        self,
        job_id: str,
        target_state: str,
        *,
        evidence_paths: tuple[str, ...] | list[str],
        evidence_sha256: Mapping[str, str],
    ) -> JobRecord:
        normalized_evidence = tuple(evidence_paths)
        if not normalized_evidence or any(
            not isinstance(path, str) or not path.strip()
            for path in normalized_evidence
        ):
            raise ValueError(
                f"job transition to {target_state} requires non-empty evidence paths"
            )
        if len(normalized_evidence) != len(set(normalized_evidence)):
            raise ValueError("job transition evidence contains duplicate paths")
        for index, path in enumerate(normalized_evidence):
            _validate_evidence_path(path, f"job transition evidence[{index}]")
        if not isinstance(evidence_sha256, Mapping) or set(evidence_sha256) != set(normalized_evidence):
            raise ValueError(
                "job transition evidence_sha256 must cover exactly the evidence paths"
            )
        normalized_sha256: dict[str, str] = {}
        for path, digest in evidence_sha256.items():
            if not isinstance(path, str) or not isinstance(digest, str) or not SHA256_PATTERN.fullmatch(digest):
                raise ValueError("job transition evidence_sha256 contains an invalid SHA256")
            normalized_sha256[path] = digest
        with _exclusive_store_lock(self.path):
            current = self._reload_locked()
            record = current.get(job_id)
            expected = FORWARD_TRANSITIONS.get(record.state)
            if target_state != expected:
                raise InvalidJobTransition(
                    f"invalid job transition {record.state} -> {target_state} for {job_id}"
                )
            if target_state == "ready":
                blocking = [
                    (dependency, current.get(dependency).state)
                    for dependency in record.dependencies
                    if current.get(dependency).state != "packaged"
                ]
                if blocking:
                    details = ", ".join(
                        f"{dependency} is {state}" for dependency, state in blocking
                    )
                    raise DependencyNotReadyError(
                        f"job {job_id} dependencies are not packaged: {details}"
                    )
            evidence = dict(record.evidence)
            evidence[target_state] = normalized_evidence
            evidence_digests = {
                state: dict(path_digests)
                for state, path_digests in record.evidence_sha256.items()
            }
            evidence_digests[target_state] = normalized_sha256
            updated = replace(
                record,
                state=target_state,
                resume_state=None,
                last_error=None,
                updated_at=_now(),
                evidence=evidence,
                evidence_sha256=evidence_digests,
            )
            current._jobs[job_id] = updated
            current._persist_unlocked()
            self._jobs = current._jobs
            return updated

    def fail(self, job_id: str, error: str) -> JobRecord:
        if not isinstance(error, str) or not error.strip():
            raise ValueError("job failure error must be a non-empty string")
        with _exclusive_store_lock(self.path):
            current = self._reload_locked()
            record = current.get(job_id)
            if record.state in ("failed", "packaged"):
                raise InvalidJobTransition(
                    f"invalid job transition {record.state} -> failed for {job_id}"
                )
            updated = replace(
                record,
                state="failed",
                resume_state=record.state,
                last_error=error.strip(),
                updated_at=_now(),
            )
            current._jobs[job_id] = updated
            current._persist_unlocked()
            self._jobs = current._jobs
            return updated

    def retry(self, job_id: str) -> JobRecord:
        with _exclusive_store_lock(self.path):
            current = self._reload_locked()
            record = current.get(job_id)
            if record.state != "failed" or record.resume_state is None:
                raise InvalidJobTransition(
                    f"invalid job transition {record.state} -> retry for {job_id}"
                )
            updated = replace(
                record,
                state=record.resume_state,
                attempts=record.attempts + 1,
                resume_state=None,
                last_error=None,
                updated_at=_now(),
            )
            current._jobs[job_id] = updated
            current._persist_unlocked()
            self._jobs = current._jobs
            return updated

    def _reload_locked(self) -> "JobStore":
        current = self.open(self.path)
        if (
            current.plan_id != self.plan_id
            or current.feature_id != self.feature_id
            or current.plan_digest != self.plan_digest
        ):
            raise ValueError("job store identity changed while this process was running")
        return current

    def _document(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": "test_point_job_store",
            "plan_id": self.plan_id,
            "feature_id": self.feature_id,
            "plan_digest": self.plan_digest,
            "jobs": [record.to_dict() for record in self._jobs.values()],
        }

    def _persist(self) -> None:
        with _exclusive_store_lock(self.path):
            self._persist_unlocked()

    def _persist_unlocked(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            self._document(),
            ensure_ascii=False,
            indent=2,
            sort_keys=False,
        ) + "\n"
        temporary_path: Optional[Path] = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=str(self.path.parent),
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
                temporary_path = Path(handle.name)
            os.replace(str(temporary_path), str(self.path))
            temporary_path = None
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink()
                except FileNotFoundError:
                    pass


def _run_root_for_store(store: JobStore) -> Path:
    jobs_path = store.path.resolve(strict=True)
    if jobs_path.name != "jobs.json" or jobs_path.parent.name != "jobs":
        raise ValueError(
            "job store must be the jobs/jobs.json file of an initialized run"
        )
    run_root = jobs_path.parent.parent
    from .formal_run import validate_formal_run

    formal = validate_formal_run(run_root)
    run_manifest = formal["run"]
    metadata = run_manifest["metadata"]
    if metadata.get("plan_id") != store.plan_id:
        raise ValueError("run.json plan_id does not match the job store")
    if metadata.get("feature_id") != store.feature_id:
        raise ValueError("run.json feature_id does not match the job store")
    return run_root.resolve(strict=True)


def _resolved_run_file(run_root: Path, relative_path: str) -> Path:
    _validate_evidence_path(relative_path, "run artifact path")
    portable = PurePosixPath(relative_path)
    current = run_root
    for part in portable.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"run artifact must not be a symbolic link: {relative_path}")
    try:
        resolved = current.resolve(strict=True)
        resolved.relative_to(run_root)
    except FileNotFoundError as exc:
        raise ValueError(f"run artifact does not exist: {relative_path}") from exc
    except (OSError, ValueError) as exc:
        raise ValueError(f"run artifact escapes the run root: {relative_path}") from exc
    if not resolved.is_file():
        raise ValueError(f"run artifact is not a regular file: {relative_path}")
    return resolved


def calculate_evidence_sha256(
    jobs_path: str | Path,
    evidence_paths: Sequence[str],
) -> dict[str, str]:
    """Fingerprint immutable transition evidence using run-relative paths."""

    store = JobStore.open(jobs_path)
    run_root = _run_root_for_store(store)
    return {
        path: hashlib.sha256(_resolved_run_file(run_root, path).read_bytes()).hexdigest()
        for path in evidence_paths
    }


def _load_json_object(path: Path, location: str) -> dict[str, Any]:
    try:
        document = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_json_object,
        )
    except json.JSONDecodeError as exc:
        raise ValueError(f"{location} is invalid JSON: {exc}") from exc
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"cannot read {location}: {exc}") from exc
    if not isinstance(document, dict) or not document:
        raise ValueError(f"{location} must be a non-empty JSON object")
    return document


class _UniqueKeySafeLoader(yaml.SafeLoader):
    pass


def _construct_unique_yaml_mapping(loader, node, deep=False):
    loader.flatten_mapping(node)
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            raise ValueError("YAML evidence mapping keys must be strings")
        if key in mapping:
            raise ValueError(f"duplicate YAML key {key}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeySafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_yaml_mapping,
)


def _load_yaml_object(path: Path, location: str) -> dict[str, Any]:
    try:
        document = yaml.load(path.read_text(encoding="utf-8"), Loader=_UniqueKeySafeLoader)
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ValueError(f"cannot read {location}: {exc}") from exc
    if not isinstance(document, dict) or not document:
        raise ValueError(f"{location} must be a non-empty YAML object")
    return document


@dataclass(frozen=True)
class _RunCoverageContext:
    run_root: Path
    plan: CoveragePlan
    obligations: tuple[Any, ...]
    cases: tuple[CaseManifest, ...]
    manifest_path_by_case_id: Mapping[str, str]
    execution_profile: ExecutionProfile | None
    execution_profile_sha256: str | None
    applicability: Any = None


def _load_run_coverage_context(store: JobStore) -> _RunCoverageContext:
    jobs_path = store.path.resolve(strict=True)
    if jobs_path.name != "jobs.json" or jobs_path.parent.name != "jobs":
        raise ValueError(
            "job store must be the jobs/jobs.json file of an initialized run"
        )
    run_root = jobs_path.parent.parent
    from .formal_run import validate_formal_run

    formal = validate_formal_run(run_root)
    run_manifest = formal["run"]
    if run_manifest["metadata"].get("plan_id") != store.plan_id:
        raise ValueError("run.json plan_id does not match the job store")
    if run_manifest["metadata"].get("feature_id") != store.feature_id:
        raise ValueError("run.json feature_id does not match the job store")
    execution_profile = formal["profile"]
    execution_profile_digest = run_manifest["metadata"]["execution_profile_sha256"]
    plan_path = run_root / "plans" / "coverage_plan.yaml"
    if plan_path.is_symlink() or not plan_path.is_file():
        raise ValueError("initialized run has no regular plans/coverage_plan.yaml")
    plan = formal["plan"]
    if plan.plan_id != store.plan_id or plan.feature_id != store.feature_id:
        raise ValueError("persisted coverage plan identity does not match the job store")
    if _plan_digest(plan) != store.plan_digest:
        raise ValueError("persisted coverage plan digest does not match the job store")
    obligations = formal["obligations"]

    manifests_root = run_root / "cases" / "manifests"
    manifest_paths = sorted(
        path
        for pattern in ("*.yaml", "*.yml")
        for path in manifests_root.rglob(pattern)
        if path.is_file() or path.is_symlink()
    )
    cases: list[CaseManifest] = []
    path_by_case_id: dict[str, str] = {}
    known_points = {point.test_point_id for point in plan.test_points}
    for path in manifest_paths:
        relative = path.relative_to(run_root).as_posix()
        resolved = _resolved_run_file(run_root, relative)
        case = load_case_manifest(resolved)
        if case.case_id in path_by_case_id:
            raise ValueError(f"duplicate case_id across run manifests: {case.case_id}")
        if case.test_point_id not in known_points:
            raise ValueError(
                f"case {case.case_id} belongs to unknown test point {case.test_point_id}"
            )
        cases.append(case)
        path_by_case_id[case.case_id] = relative
    return _RunCoverageContext(
        run_root=run_root,
        plan=plan,
        obligations=obligations,
        cases=tuple(cases),
        manifest_path_by_case_id=path_by_case_id,
        execution_profile=execution_profile,
        execution_profile_sha256=execution_profile_digest,
        applicability=formal["applicability"],
    )


def _require_exact_paths(
    actual: Sequence[str],
    expected: set[str],
    location: str,
) -> None:
    actual_set = set(actual)
    if actual_set == expected and len(actual) == len(expected):
        return
    missing = sorted(expected - actual_set)
    unexpected = sorted(actual_set - expected)
    details = []
    if missing:
        details.append("missing " + ", ".join(missing))
    if unexpected:
        details.append("unexpected " + ", ".join(unexpected))
    raise ValueError(f"{location} must cover the exact artifact set: " + "; ".join(details))


def _point_cases(
    context: _RunCoverageContext,
    job_id: str,
) -> tuple[tuple[Any, ...], tuple[CaseManifest, ...]]:
    obligations = tuple(
        obligation
        for obligation in context.obligations
        if obligation.test_point_id == job_id
    )
    cases = tuple(case for case in context.cases if case.test_point_id == job_id)
    report = reconcile_case_manifests(
        obligations,
        cases,
        artifact_root=context.run_root,
    )
    if not report.complete:
        raise ValueError(
            f"job {job_id} case reconciliation is incomplete: "
            + json.dumps(report.to_dict(), ensure_ascii=False, sort_keys=True)
        )
    from .applicability import reconcile_applicability_bindings

    if context.applicability is not None and job_id.startswith("TP-SFV-"):
        applicability_report = reconcile_applicability_bindings(
            context.applicability,
            context.obligations,
            cases=context.cases,
            test_point_id=job_id,
        )
        if not applicability_report.complete:
            raise ValueError(
                f"job {job_id} applicability case reconciliation is incomplete: "
                + json.dumps(applicability_report.to_dict(), sort_keys=True)
            )
    allowed_harnesses = {
        decision.execution_harness
        for decision in context.plan.risk_decisions.values()
        if decision.execution_harness is not None
        and job_id in decision.test_points
    }
    for case in cases:
        if (
            case.execution_profile == "external_isolated"
            and case.execution_harness not in allowed_harnesses
        ):
            raise ValueError(
                f"case {case.case_id} external harness {case.execution_harness!r} "
                f"is not declared by a covered risk for job {job_id}"
            )
    return obligations, cases


def _execution_record(
    context: _RunCoverageContext,
    case: CaseManifest,
    side: str,
) -> tuple[dict[str, Any], ExecutionRecord]:
    relative = f"executions/{side}/{case.case_id}.json"
    document = _load_json_object(
        _resolved_run_file(context.run_root, relative),
        relative,
    )
    expected_keys = {
        "target_name",
        "sql_file",
        "returncode",
        "stdout",
        "stderr",
        "duration_seconds",
        "endpoint_identity",
        "sql_sha256",
        "execution_profile_sha256",
    }
    if set(document) != expected_keys:
        raise ValueError(f"{relative} has an invalid execution-record schema")
    if document["target_name"] != side:
        raise ValueError(f"{relative} does not belong to target {side}")
    if not isinstance(document["returncode"], int) or isinstance(document["returncode"], bool):
        raise ValueError(f"{relative}.returncode must be an integer")
    if not isinstance(document["stdout"], str) or not isinstance(document["stderr"], str):
        raise ValueError(f"{relative} stdout/stderr must be strings")
    duration = document["duration_seconds"]
    if (
        not isinstance(duration, (int, float))
        or isinstance(duration, bool)
        or not math.isfinite(float(duration))
        or duration < 0
    ):
        raise ValueError(f"{relative}.duration_seconds must be finite and non-negative")
    sql_relative = case.sql_files[0]
    sql_path = _resolved_run_file(context.run_root, sql_relative)
    declared_sql_file = document["sql_file"]
    if not isinstance(declared_sql_file, str) or not declared_sql_file:
        raise ValueError(f"{relative}.sql_file must be a non-empty string")
    declared_path = Path(declared_sql_file)
    if not declared_path.is_absolute():
        declared_path = context.run_root / declared_path
    try:
        resolved_declared_path = declared_path.resolve(strict=True)
    except OSError as exc:
        raise ValueError(f"{relative}.sql_file cannot be resolved") from exc
    if resolved_declared_path != sql_path:
        raise ValueError(f"{relative}.sql_file does not belong to case {case.case_id}")
    if document["sql_sha256"] != case.sql_sha256:
        raise ValueError(f"{relative}.sql_sha256 does not match the case manifest")
    if document["execution_profile_sha256"] != context.execution_profile_sha256:
        raise ValueError(
            f"{relative}.execution_profile_sha256 does not match the immutable run profile"
        )

    identity_document = document["endpoint_identity"]
    identity_keys = {
        "target_name",
        "login_path",
        "database",
        "server_version",
        "server_version_num",
        "server_uuid",
        "server_hostname",
        "server_port",
        "current_user",
        "version_comment",
        "granted_global_privileges",
    }
    if not isinstance(identity_document, dict) or set(identity_document) != identity_keys:
        raise ValueError(f"{relative}.endpoint_identity has an invalid schema")
    privileges = identity_document["granted_global_privileges"]
    if not isinstance(privileges, list) or any(not isinstance(item, str) for item in privileges):
        raise ValueError(
            f"{relative}.endpoint_identity.granted_global_privileges must be a string list"
        )
    identity_string_keys = (
        "target_name",
        "login_path",
        "database",
        "server_version",
        "server_uuid",
        "server_hostname",
        "current_user",
        "version_comment",
    )
    if any(
        not isinstance(identity_document[key], str)
        for key in identity_string_keys
    ):
        raise ValueError(f"{relative}.endpoint_identity string fields are invalid")
    if (
        not isinstance(identity_document["server_version_num"], int)
        or isinstance(identity_document["server_version_num"], bool)
        or not isinstance(identity_document["server_port"], int)
        or isinstance(identity_document["server_port"], bool)
    ):
        raise ValueError(f"{relative}.endpoint_identity scalar fields are invalid")
    try:
        identity = EndpointIdentity(
            target_name=identity_document["target_name"],
            login_path=identity_document["login_path"],
            database=identity_document["database"],
            server_version=identity_document["server_version"],
            server_version_num=identity_document["server_version_num"],
            server_uuid=identity_document["server_uuid"],
            server_hostname=identity_document["server_hostname"],
            server_port=identity_document["server_port"],
            current_user=identity_document["current_user"],
            version_comment=identity_document["version_comment"],
            granted_global_privileges=tuple(privileges),
        )
        expected_version_num = (
            context.execution_profile.target_version_num
            if context.execution_profile is not None
            else None
        )
        validate_endpoint_identity(identity, expected_version_num=expected_version_num)
        if case.execution_profile == "basic_mysql":
            validate_basic_endpoint_identity(
                identity,
                expected_version_num=expected_version_num,
            )
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{relative} has an invalid endpoint identity: {exc}") from exc
    if identity.target_name != side:
        raise ValueError(f"{relative} endpoint identity does not belong to {side}")
    if context.execution_profile is not None:
        expected_endpoint = (
            context.execution_profile.reference
            if side == "reference"
            else context.execution_profile.dut
        )
        if (
            identity.login_path != expected_endpoint.login_path
            or identity.database != expected_endpoint.database
            or identity.server_uuid
            != expected_endpoint.expected_server_uuid
            or identity.current_user != expected_endpoint.expected_current_user
        ):
            raise ValueError(
                f"{relative} endpoint login_path/database/server_uuid/current_user "
                "does not match the immutable run execution profile"
            )

    for suffix, key in (("stdout", "stdout"), ("stderr", "stderr")):
        raw_relative = f"executions/{side}/{case.case_id}.{suffix}"
        try:
            raw_content = _resolved_run_file(context.run_root, raw_relative).read_text(
                encoding="utf-8"
            )
        except UnicodeError as exc:
            raise ValueError(f"{raw_relative} must be valid UTF-8") from exc
        if raw_content != document[key]:
            raise ValueError(f"{raw_relative} does not match {relative}")
    record = ExecutionRecord(
        target_name=document["target_name"],
        sql_file=document["sql_file"],
        returncode=document["returncode"],
        stdout=document["stdout"],
        stderr=document["stderr"],
        duration_seconds=float(duration),
        endpoint_identity=identity_document,
        sql_sha256=document["sql_sha256"],
        execution_profile_sha256=document["execution_profile_sha256"],
    )
    _, replay_report = _replay_record(context, case, side, document)
    if replay_report["deterministic"] is not True:
        raise ValueError(
            f"executions/{side}/{case.case_id}.replay.json is nondeterministic: "
            + ", ".join(replay_report["differences"])
        )
    return document, record


def _replay_record(
    context: _RunCoverageContext,
    case: CaseManifest,
    side: str,
    primary: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    relative = f"executions/{side}/{case.case_id}.replay.json"
    document = _load_json_object(
        _resolved_run_file(context.run_root, relative), relative
    )
    expected_keys = {
        "target_name",
        "sql_file",
        "returncode",
        "stdout",
        "stderr",
        "duration_seconds",
        "endpoint_identity",
        "sql_sha256",
        "execution_profile_sha256",
    }
    if set(document) != expected_keys:
        raise ValueError(f"{relative} has an invalid replay execution schema")
    if (
        not isinstance(document["returncode"], int)
        or isinstance(document["returncode"], bool)
        or not isinstance(document["stdout"], str)
        or not isinstance(document["stderr"], str)
        or not isinstance(document["duration_seconds"], (int, float))
        or isinstance(document["duration_seconds"], bool)
        or not math.isfinite(float(document["duration_seconds"]))
        or document["duration_seconds"] < 0
    ):
        raise ValueError(f"{relative} has invalid replay execution values")
    for key in (
        "target_name",
        "sql_file",
        "endpoint_identity",
        "sql_sha256",
        "execution_profile_sha256",
    ):
        if document[key] != primary[key]:
            raise ValueError(f"{relative}.{key} differs from the first run")
    for suffix, key in (("stdout", "stdout"), ("stderr", "stderr")):
        raw_relative = f"executions/{side}/{case.case_id}.replay.{suffix}"
        try:
            raw_content = _resolved_run_file(
                context.run_root, raw_relative
            ).read_text(encoding="utf-8")
        except UnicodeError as exc:
            raise ValueError(f"{raw_relative} must be valid UTF-8") from exc
        if raw_content != document[key]:
            raise ValueError(f"{raw_relative} does not match {relative}")
    report = compare_two_run_transcripts(
        ExecutionTranscript(
            primary["returncode"],
            primary["stdout"].encode("utf-8"),
            primary["stderr"].encode("utf-8"),
        ),
        ExecutionTranscript(
            document["returncode"],
            document["stdout"].encode("utf-8"),
            document["stderr"].encode("utf-8"),
        ),
    ).to_dict()
    return document, report


def _comparison_document(
    context: _RunCoverageContext,
    case: CaseManifest,
) -> tuple[dict[str, Any], bool]:
    relative = f"comparisons/{case.case_id}.json"
    document = _load_json_object(
        _resolved_run_file(context.run_root, relative),
        relative,
    )
    expected_keys = {
        "reference",
        "dut",
        "comparison",
        "expected_outcome",
        "expected_sqlstate",
        "reference_oracle_valid",
        "reference_oracle_error",
        "execution_profile_sha256",
        "reference_replay",
        "dut_replay",
        "reference_determinism",
        "dut_determinism",
        "passed",
    }
    if set(document) != expected_keys:
        raise ValueError(f"{relative} has an invalid comparison schema")
    reference_document, reference = _execution_record(context, case, "reference")
    dut_document, dut = _execution_record(context, case, "dut")
    reference_replay, reference_determinism = _replay_record(
        context, case, "reference", reference_document
    )
    dut_replay, dut_determinism = _replay_record(
        context, case, "dut", dut_document
    )
    validate_comparable_endpoint_pair(
        EndpointIdentity(
            **{
                **reference.endpoint_identity,
                "granted_global_privileges": tuple(
                    reference.endpoint_identity["granted_global_privileges"]
                ),
            }
        ),
        EndpointIdentity(
            **{
                **dut.endpoint_identity,
                "granted_global_privileges": tuple(
                    dut.endpoint_identity["granted_global_privileges"]
                ),
            }
        ),
        require_basic_privileges=case.execution_profile == "basic_mysql",
        expected_version_num=context.execution_profile.target_version_num,
    )
    if document["execution_profile_sha256"] != context.execution_profile_sha256:
        raise ValueError(
            f"{relative}.execution_profile_sha256 does not match the immutable run profile"
        )
    if document["reference"] != reference_document or document["dut"] != dut_document:
        raise ValueError(f"{relative} execution snapshots do not match their evidence JSON")
    if (
        document["reference_replay"] != reference_replay
        or document["dut_replay"] != dut_replay
        or document["reference_determinism"] != reference_determinism
        or document["dut_determinism"] != dut_determinism
    ):
        raise ValueError(f"{relative} replay/determinism evidence does not recompute exactly")
    recomputed = compare_execution_records(
        reference,
        dut,
        NormalizationProfile(),
    ).to_dict()
    canonical_recomputed = json.loads(json.dumps(recomputed, ensure_ascii=False))
    if document["comparison"] != canonical_recomputed:
        raise ValueError(f"{relative} comparison content does not recompute exactly")
    if document["expected_outcome"] != case.outcome:
        raise ValueError(f"{relative} expected_outcome does not match the case")
    expected_sqlstate = case.comparison.get("expected_sqlstate")
    if document["expected_sqlstate"] != expected_sqlstate:
        raise ValueError(f"{relative} expected_sqlstate does not match the case")
    oracle_valid, oracle_error = _reference_oracle(case, reference)
    passed = (
        oracle_valid
        and bool(recomputed["identical"])
        and reference_determinism["deterministic"] is True
        and dut_determinism["deterministic"] is True
    )
    if (
        document["reference_oracle_valid"] is not oracle_valid
        or document["reference_oracle_error"] != oracle_error
        or document["passed"] is not passed
    ):
        raise ValueError(f"{relative} has an invalid oracle/pass result")
    diff_relative = f"comparisons/{case.case_id}.diff"
    try:
        diff_content = _resolved_run_file(context.run_root, diff_relative).read_text(
            encoding="utf-8"
        )
    except UnicodeError as exc:
        raise ValueError(f"{diff_relative} must be valid UTF-8") from exc
    if diff_content != recomputed["unified_diff"]:
        raise ValueError(f"{diff_relative} does not match {relative}")
    return document, passed


def _reference_oracle(
    case: CaseManifest,
    reference: ExecutionRecord,
) -> tuple[bool, str | None]:
    """Recompute the upstream outcome oracle from immutable execution evidence."""

    if case.outcome == "success":
        oracle_valid = reference.returncode == 0
        return (
            oracle_valid,
            None
            if oracle_valid
            else "reference execution failed although the case outcome is success",
        )
    return validate_expected_failure_oracle(
        reference.returncode,
        reference.stderr,
        case.comparison.get("expected_sqlstate"),
    )


def _artifact_binding(
    document: Mapping[str, Any],
    key: str,
    expected_path: str,
    run_root: Path,
    location: str,
) -> None:
    binding = document.get(key)
    if not isinstance(binding, Mapping) or set(binding) != {"path", "sha256"}:
        raise ValueError(f"{location}.artifacts.{key} must contain path and sha256")
    if binding.get("path") != expected_path:
        raise ValueError(f"{location}.artifacts.{key}.path has the wrong owner")
    digest = binding.get("sha256")
    if not isinstance(digest, str) or not SHA256_PATTERN.fullmatch(digest):
        raise ValueError(f"{location}.artifacts.{key}.sha256 is invalid")
    actual = hashlib.sha256(_resolved_run_file(run_root, expected_path).read_bytes()).hexdigest()
    if actual != digest:
        raise ValueError(f"{location}.artifacts.{key}.sha256 does not match its file")


def _validate_triage(
    context: _RunCoverageContext,
    job_id: str,
    cases: Sequence[CaseManifest],
    evidence_paths: Sequence[str],
) -> None:
    comparison_paths = {f"comparisons/{case.case_id}.json" for case in cases}
    finding_paths = {
        path
        for path in evidence_paths
        if path.startswith("findings/") and PurePosixPath(path).suffix.lower() in {".yaml", ".yml"}
    }
    _require_exact_paths(
        evidence_paths,
        comparison_paths | finding_paths,
        f"job {job_id} triaged evidence",
    )
    failed_cases: set[str] = set()
    case_by_id = {case.case_id: case for case in cases}
    for case in cases:
        _, passed = _comparison_document(context, case)
        if not passed:
            failed_cases.add(case.case_id)
    finding_case_ids: set[str] = set()
    finding_ids: set[str] = set()
    for finding_path in finding_paths:
        document = _load_yaml_object(
            _resolved_run_file(context.run_root, finding_path),
            finding_path,
        )
        if document.get("schema_version") != 1 or document.get("kind") != "differential_finding":
            raise ValueError(f"{finding_path} has an invalid finding schema")
        finding_id = document.get("finding_id")
        case_id = document.get("case_id")
        if not isinstance(finding_id, str) or not finding_id or finding_id in finding_ids:
            raise ValueError(f"{finding_path} has an invalid or duplicate finding_id")
        if case_id not in failed_cases or case_id in finding_case_ids:
            raise ValueError(f"{finding_path} does not belong to one unmatched failing case")
        case = case_by_id[case_id]
        if (
            document.get("test_point_id") != job_id
            or document.get("obligation_id") != case.obligation_id
            or not isinstance(document.get("summary"), str)
            or not document["summary"].strip()
        ):
            raise ValueError(f"{finding_path} does not match its case/test point")
        artifacts = document.get("artifacts")
        if not isinstance(artifacts, Mapping) or set(artifacts) != {
            "sql",
            "reference_execution",
            "dut_execution",
            "comparison",
        }:
            raise ValueError(f"{finding_path}.artifacts has an invalid schema")
        _artifact_binding(artifacts, "sql", case.sql_files[0], context.run_root, finding_path)
        _artifact_binding(
            artifacts,
            "reference_execution",
            f"executions/reference/{case_id}.json",
            context.run_root,
            finding_path,
        )
        _artifact_binding(
            artifacts,
            "dut_execution",
            f"executions/dut/{case_id}.json",
            context.run_root,
            finding_path,
        )
        _artifact_binding(
            artifacts,
            "comparison",
            f"comparisons/{case_id}.json",
            context.run_root,
            finding_path,
        )
        finding_ids.add(finding_id)
        finding_case_ids.add(case_id)
    if finding_case_ids != failed_cases:
        missing = sorted(failed_cases - finding_case_ids)
        raise ValueError(
            f"job {job_id} has differential failures without findings: {', '.join(missing)}"
        )


def _validate_package(
    context: _RunCoverageContext,
    job_id: str,
    cases: Sequence[CaseManifest],
    evidence_paths: Sequence[str],
) -> None:
    package_path = f"regression/packages/{job_id}.json"
    if package_path not in evidence_paths:
        raise ValueError(
            f"job {job_id} packaged evidence requires {package_path}"
        )
    document = _load_json_object(
        _resolved_run_file(context.run_root, package_path),
        package_path,
    )
    if set(document) != {
        "schema_version",
        "kind",
        "test_point_id",
        "batch_prefix",
        "number_width",
        "mapping_sha256",
        "cases",
    } or (
        document["schema_version"] != 1
        or document["kind"] != "regression_package"
        or document["test_point_id"] != job_id
        or not isinstance(document["cases"], list)
    ):
        raise ValueError(f"{package_path} has an invalid regression package schema")
    case_by_id = {case.case_id: case for case in cases}
    case_by_obligation = {case.obligation_id: case for case in cases}
    ordered_cases = [
        case_by_obligation[obligation.obligation_id]
        for obligation in context.obligations
        if obligation.test_point_id == job_id
        and obligation.outcome != "justified_na"
    ]
    try:
        mapping = build_regression_batch_mapping(
            document["batch_prefix"],
            [case.obligation_id for case in ordered_cases],
            minimum_width=document["number_width"],
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{package_path} has an invalid regression mapping: {exc}") from exc
    if document["mapping_sha256"] != mapping.sha256:
        raise ValueError(f"{package_path}.mapping_sha256 does not match its mapping")
    style_by_obligation = {
        style.obligation_id: style for style in mapping.cases
    }
    entry_case_ids: set[str] = set()
    artifact_paths: set[str] = {package_path}
    for index, entry in enumerate(document["cases"]):
        location = f"{package_path}.cases[{index}]"
        if not isinstance(entry, Mapping):
            raise ValueError(f"{location} must be an object")
        if set(entry) != {
            "case_id",
            "obligation_id",
            "case_ordinal",
            "object_prefix",
            "sql_file",
            "sql_sha256",
            "expected_file",
            "expected_sha256",
        }:
            raise ValueError(f"{location} has an invalid regression case schema")
        case_id = entry.get("case_id")
        if case_id not in case_by_id or case_id in entry_case_ids:
            raise ValueError(f"{location}.case_id is unknown or duplicate")
        case = case_by_id[case_id]
        style = style_by_obligation.get(case.obligation_id)
        if style is None or (
            entry["obligation_id"] != case.obligation_id
            or entry["case_ordinal"] != style.case_ordinal
            or entry["object_prefix"] != style.object_prefix
        ):
            raise ValueError(f"{location} does not match the stable regression mapping")
        sql_file = entry.get("sql_file")
        sql_sha256 = entry.get("sql_sha256")
        expected_file = entry.get("expected_file")
        expected_sha256 = entry.get("expected_sha256")
        if (
            not isinstance(sql_file, str)
            or sql_file != f"regression/sql/{style.sql_filename}"
            or not isinstance(expected_file, str)
            or expected_file
            != f"regression/expected/{Path(style.sql_filename).stem}.out"
            or not isinstance(sql_sha256, str)
            or not SHA256_PATTERN.fullmatch(sql_sha256)
            or not isinstance(expected_sha256, str)
            or not SHA256_PATTERN.fullmatch(expected_sha256)
        ):
            raise ValueError(f"{location} has invalid regression artifact bindings")
        regression_sql = _resolved_run_file(context.run_root, sql_file)
        if hashlib.sha256(regression_sql.read_bytes()).hexdigest() != sql_sha256:
            raise ValueError(f"{location}.sql_sha256 does not match its file")
        if sql_sha256 != case.sql_sha256:
            raise ValueError(f"{location}.sql_sha256 does not match the source case")
        try:
            regression_sql_text = regression_sql.read_text(encoding="utf-8")
        except UnicodeError as exc:
            raise ValueError(f"{location}.sql_file must be UTF-8") from exc
        validate_huawei_sql_header(regression_sql_text)
        catalog_report = audit_catalog_observability(regression_sql_text)
        if not catalog_report.passed:
            raise ValueError(f"{location}.sql_file has unstable catalog output")
        if re.search(r"\bCREATE\s+(?:(?:TEMP|TEMPORARY|UNLOGGED)\s+)?TABLE\b", regression_sql_text, re.IGNORECASE):
            table_report = audit_complete_table_script(
                regression_sql_text,
                expected_object_prefix=style.object_prefix,
            )
            if not table_report.passed:
                raise ValueError(
                    f"{location}.sql_file is not a complete table script: "
                    + json.dumps(table_report.to_dict(), sort_keys=True)
                )
        expected_path = _resolved_run_file(context.run_root, expected_file)
        expected_bytes = expected_path.read_bytes()
        if hashlib.sha256(expected_bytes).hexdigest() != expected_sha256:
            raise ValueError(f"{location}.expected_sha256 does not match its file")
        try:
            expected_text = expected_bytes.decode("utf-8")
        except UnicodeError as exc:
            raise ValueError(f"{location}.expected_file must be UTF-8") from exc
        comparison, _ = _comparison_document(context, case)
        if (
            expected_text != comparison["comparison"]["normalized_reference"]
            or expected_sha256 != comparison["comparison"]["reference_sha256"]
        ):
            raise ValueError(f"{location}.expected_file is not the upstream exact transcript")
        entry_case_ids.add(case_id)
        artifact_paths.update((sql_file, expected_file))
    if entry_case_ids != set(case_by_id):
        raise ValueError(f"{package_path} does not package every case for job {job_id}")
    _require_exact_paths(
        evidence_paths,
        artifact_paths,
        f"job {job_id} packaged evidence",
    )


def _validate_required_harnesses(
    context: _RunCoverageContext,
    job_id: str,
    evidence_paths: Sequence[str],
) -> None:
    harness_ids = {
        decision.execution_harness
        for decision in context.plan.risk_decisions.values()
        if decision.execution_harness is not None
        and job_id in decision.test_points
    }
    if not harness_ids:
        return
    for harness_id in harness_ids:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", harness_id):
            raise ValueError(f"job {job_id} references an invalid execution harness id")
    expected_paths = {
        f"jobs/harnesses/{harness_id}.json" for harness_id in harness_ids
    }
    missing_paths = expected_paths - set(evidence_paths)
    if missing_paths:
        raise ValueError(
            f"job {job_id} ready harness evidence is missing: "
            + ", ".join(sorted(missing_paths))
        )
    expected_keys = {
        "schema_version",
        "kind",
        "harness_id",
        "status",
        "compatibility_target",
        "execution_profile_sha256",
        "implementation",
        "event_model",
        "probe",
        "fingerprint",
        "verified_at",
    }
    for harness_id in sorted(harness_ids):
        relative = f"jobs/harnesses/{harness_id}.json"
        document = _load_json_object(
            _resolved_run_file(context.run_root, relative),
            relative,
        )
        if set(document) != expected_keys:
            raise ValueError(f"{relative} has an invalid harness-verification schema")
        if (
            document["schema_version"] != 1
            or document["kind"] != "execution_harness_verification"
            or document["harness_id"] != harness_id
            or document["status"] != "ready"
            or document["compatibility_target"]
            != context.execution_profile.compatibility_target
            or document["execution_profile_sha256"]
            != context.execution_profile_sha256
            or not isinstance(document["implementation"], Mapping)
            or set(document["implementation"]) != {"path", "sha256"}
            or not isinstance(document["event_model"], list)
            or not document["event_model"]
            or any(
                not isinstance(event, str) or not event.strip()
                for event in document["event_model"]
            )
            or len(document["event_model"]) != len(set(document["event_model"]))
            or not isinstance(document["probe"], Mapping)
            or not document["probe"]
            or not isinstance(document["fingerprint"], str)
            or not SHA256_PATTERN.fullmatch(document["fingerprint"])
            or not isinstance(document["verified_at"], str)
            or not document["verified_at"].strip()
        ):
            raise ValueError(f"{relative} does not prove that harness {harness_id} is ready")
        implementation = document["implementation"]
        expected_implementation_prefix = (
            f"jobs/harnesses/implementations/{harness_id}."
        )
        if (
            not isinstance(implementation["path"], str)
            or not implementation["path"].startswith(expected_implementation_prefix)
            or not isinstance(implementation["sha256"], str)
            or not SHA256_PATTERN.fullmatch(implementation["sha256"])
        ):
            raise ValueError(f"{relative}.implementation binding is invalid")
        implementation_path = _resolved_run_file(
            context.run_root, implementation["path"]
        )
        if hashlib.sha256(implementation_path.read_bytes()).hexdigest() != implementation["sha256"]:
            raise ValueError(f"{relative}.implementation.sha256 does not match its file")
        probe_fingerprint = hashlib.sha256(
            json.dumps(
                {
                    "event_model": document["event_model"],
                    "execution_profile_sha256": document[
                        "execution_profile_sha256"
                    ],
                    "implementation": document["implementation"],
                    "probe": document["probe"],
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        if document["fingerprint"] != probe_fingerprint:
            raise ValueError(f"{relative}.fingerprint does not match its probe payload")
        try:
            verified_at = datetime.fromisoformat(
                document["verified_at"].replace("Z", "+00:00")
            )
        except ValueError as exc:
            raise ValueError(f"{relative}.verified_at must be an ISO-8601 timestamp") from exc
        if verified_at.tzinfo is None:
            raise ValueError(f"{relative}.verified_at must include a timezone")


def _point_obligation_ids(
    context: _RunCoverageContext,
    job_id: str,
) -> list[str]:
    return [
        obligation.obligation_id
        for obligation in context.obligations
        if obligation.test_point_id == job_id
    ]


def _validate_audit_evidence(
    context: _RunCoverageContext,
    job_id: str,
    evidence_paths: Sequence[str],
) -> None:
    relative = f"jobs/audits/{job_id}.json"
    _require_exact_paths(evidence_paths, {relative}, f"job {job_id} audited evidence")
    document = _load_json_object(
        _resolved_run_file(context.run_root, relative), relative
    )
    expected_keys = {
        "schema_version",
        "kind",
        "plan_id",
        "feature_id",
        "test_point_id",
        "status",
        "obligation_ids",
        "unresolved_items",
    }
    if set(document) != expected_keys:
        raise ValueError(f"{relative} has an invalid test-point-audit schema")
    if (
        document["schema_version"] != 1
        or document["kind"] != "test_point_audit"
        or document["plan_id"] != context.plan.plan_id
        or document["feature_id"] != context.plan.feature_id
        or document["test_point_id"] != job_id
        or document["status"] != "approved"
        or document["obligation_ids"] != _point_obligation_ids(context, job_id)
        or document["unresolved_items"] != []
    ):
        raise ValueError(
            f"{relative} does not prove an approved, fully resolved test-point audit"
        )


def _validate_ready_evidence(
    context: _RunCoverageContext,
    job_id: str,
    evidence_paths: Sequence[str],
) -> None:
    relative = f"jobs/readiness/{job_id}.json"
    harness_ids = sorted(
        {
            decision.execution_harness
            for decision in context.plan.risk_decisions.values()
            if decision.execution_harness is not None
            and job_id in decision.test_points
        }
    )
    harness_record_paths = {
        f"jobs/harnesses/{harness_id}.json" for harness_id in harness_ids
    }
    implementation_paths: set[str] = set()
    for harness_record_path in sorted(harness_record_paths):
        harness_document = _load_json_object(
            _resolved_run_file(context.run_root, harness_record_path),
            harness_record_path,
        )
        implementation = harness_document.get("implementation")
        if not isinstance(implementation, Mapping) or not isinstance(
            implementation.get("path"), str
        ):
            raise ValueError(
                f"{harness_record_path}.implementation must bind a run file"
            )
        implementation_paths.add(implementation["path"])
    expected_paths = {relative} | harness_record_paths | implementation_paths
    _require_exact_paths(evidence_paths, expected_paths, f"job {job_id} ready evidence")
    document = _load_json_object(
        _resolved_run_file(context.run_root, relative), relative
    )
    expected_keys = {
        "schema_version",
        "kind",
        "plan_id",
        "feature_id",
        "test_point_id",
        "status",
        "obligation_ids",
        "execution_profiles",
        "execution_harnesses",
        "blockers",
    }
    if set(document) != expected_keys:
        raise ValueError(f"{relative} has an invalid test-point-readiness schema")
    profiles = sorted(
        {
            obligation.execution_profile
            for obligation in context.obligations
            if obligation.test_point_id == job_id
            and obligation.outcome != "justified_na"
        }
    )
    if (
        document["schema_version"] != 1
        or document["kind"] != "test_point_readiness"
        or document["plan_id"] != context.plan.plan_id
        or document["feature_id"] != context.plan.feature_id
        or document["test_point_id"] != job_id
        or document["status"] != "ready"
        or document["obligation_ids"] != _point_obligation_ids(context, job_id)
        or document["execution_profiles"] != profiles
        or document["execution_harnesses"] != harness_ids
        or document["blockers"] != []
    ):
        raise ValueError(
            f"{relative} does not prove exact, blocker-free test-point readiness"
        )
    _validate_required_harnesses(context, job_id, evidence_paths)


def _lint_checks_for_case(context: _RunCoverageContext, case: CaseManifest) -> dict[str, str]:
    sql_path = _resolved_run_file(context.run_root, case.sql_files[0])
    try:
        sql_text = sql_path.read_text(encoding="utf-8")
    except UnicodeError as exc:
        raise ValueError(f"{case.sql_files[0]} must be valid UTF-8") from exc
    validate_huawei_sql_header(sql_text)
    catalog_report = audit_catalog_observability(sql_text)
    if not catalog_report.passed:
        raise ValueError(
            f"{case.sql_files[0]} has unstable catalog observability: "
            + json.dumps(catalog_report.to_dict(), sort_keys=True)
        )
    common_checks = {
        "regression_header": "passed",
        "catalog_observability": "passed",
    }
    if case.execution_profile == "basic_mysql":
        validate_sql_for_basic_runner(sql_text)
        return {**common_checks, "sql_safety": "passed"}
    if case.execution_harness == "external-copy-ingest":
        validate_sql_for_external_copy_ingest(sql_text)
        return {**common_checks, "external_copy_payload": "passed"}
    return {**common_checks, "external_harness_contract": "passed"}


def _validate_lint_evidence(
    context: _RunCoverageContext,
    job_id: str,
    cases: Sequence[CaseManifest],
    evidence_paths: Sequence[str],
) -> None:
    relative = f"jobs/lint/{job_id}.json"
    _require_exact_paths(evidence_paths, {relative}, f"job {job_id} linted evidence")
    document = _load_json_object(
        _resolved_run_file(context.run_root, relative), relative
    )
    if set(document) != {
        "schema_version",
        "kind",
        "plan_id",
        "feature_id",
        "test_point_id",
        "status",
        "errors",
        "cases",
    }:
        raise ValueError(f"{relative} has an invalid test-point-lint schema")
    expected_cases: list[dict[str, Any]] = []
    for case in sorted(cases, key=lambda item: item.case_id):
        manifest_path = context.manifest_path_by_case_id[case.case_id]
        sql_path = case.sql_files[0]
        expected_cases.append(
            {
                "case_id": case.case_id,
                "obligation_id": case.obligation_id,
                "manifest_path": manifest_path,
                "manifest_sha256": hashlib.sha256(
                    _resolved_run_file(context.run_root, manifest_path).read_bytes()
                ).hexdigest(),
                "sql_path": sql_path,
                "sql_sha256": case.sql_sha256,
                "checks": _lint_checks_for_case(context, case),
            }
        )
    if (
        document["schema_version"] != 1
        or document["kind"] != "test_point_lint_report"
        or document["plan_id"] != context.plan.plan_id
        or document["feature_id"] != context.plan.feature_id
        or document["test_point_id"] != job_id
        or document["status"] != "passed"
        or document["errors"] != []
        or document["cases"] != expected_cases
    ):
        raise ValueError(
            f"{relative} does not prove exact, error-free generated case linting"
        )


def validate_job_artifacts(
    store: JobStore,
    job_id: str,
    *,
    candidate_state: str | None = None,
    candidate_paths: Sequence[str] = (),
    candidate_sha256: Mapping[str, str] | None = None,
    _context: _RunCoverageContext | None = None,
) -> None:
    """Revalidate a job's full point ledger and every persisted evidence snapshot."""

    record = store.get(job_id)
    evidence = {state: tuple(paths) for state, paths in record.evidence.items()}
    evidence_sha256 = {
        state: dict(path_digests)
        for state, path_digests in record.evidence_sha256.items()
    }
    progress_state = record.resume_state if record.state == "failed" else record.state
    if candidate_state is not None:
        if candidate_state != FORWARD_TRANSITIONS.get(record.state):
            raise InvalidJobTransition(
                f"invalid job transition {record.state} -> {candidate_state} for {job_id}"
            )
        if candidate_sha256 is None or set(candidate_sha256) != set(candidate_paths):
            raise ValueError("candidate evidence SHA256 set is incomplete")
        evidence[candidate_state] = tuple(candidate_paths)
        evidence_sha256[candidate_state] = dict(candidate_sha256)
        progress_state = candidate_state

    context = _context or _load_run_coverage_context(store)
    for state, paths in evidence.items():
        path_digests = evidence_sha256.get(state, {})
        if set(path_digests) != set(paths):
            raise ValueError(f"job {job_id} {state} evidence SHA256 ledger is incomplete")
        for path in paths:
            actual = hashlib.sha256(
                _resolved_run_file(context.run_root, path).read_bytes()
            ).hexdigest()
            if actual != path_digests[path]:
                raise ValueError(
                    f"job {job_id} {state} evidence was modified after transition: {path}"
                )

    if progress_state in EVIDENCE_STATES:
        progress_index = EVIDENCE_STATES.index(progress_state)
        if progress_index >= EVIDENCE_STATES.index("audited"):
            _validate_audit_evidence(context, job_id, evidence["audited"])
        if progress_index >= EVIDENCE_STATES.index("ready"):
            _validate_ready_evidence(context, job_id, evidence["ready"])

    if progress_state not in EVIDENCE_STATES or EVIDENCE_STATES.index(progress_state) < EVIDENCE_STATES.index("generated"):
        return
    _, cases = _point_cases(context, job_id)
    generated_paths = {
        context.manifest_path_by_case_id[case.case_id]
        for case in cases
    } | {case.sql_files[0] for case in cases}
    _require_exact_paths(
        evidence["generated"],
        generated_paths,
        f"job {job_id} generated evidence",
    )

    if EVIDENCE_STATES.index(progress_state) >= EVIDENCE_STATES.index("linted"):
        _validate_lint_evidence(
            context,
            job_id,
            cases,
            evidence["linted"],
        )

    if EVIDENCE_STATES.index(progress_state) >= EVIDENCE_STATES.index("executed_reference"):
        expected = {f"executions/reference/{case.case_id}.json" for case in cases}
        _require_exact_paths(
            evidence["executed_reference"],
            expected,
            f"job {job_id} reference execution evidence",
        )
        for case in cases:
            _execution_record(context, case, "reference")
    if EVIDENCE_STATES.index(progress_state) >= EVIDENCE_STATES.index("executed_dut"):
        expected = {f"executions/dut/{case.case_id}.json" for case in cases}
        _require_exact_paths(
            evidence["executed_dut"],
            expected,
            f"job {job_id} DUT execution evidence",
        )
        for case in cases:
            _execution_record(context, case, "dut")
    if EVIDENCE_STATES.index(progress_state) >= EVIDENCE_STATES.index("compared"):
        expected = {f"comparisons/{case.case_id}.json" for case in cases}
        _require_exact_paths(
            evidence["compared"],
            expected,
            f"job {job_id} comparison evidence",
        )
        for case in cases:
            _comparison_document(context, case)
    if EVIDENCE_STATES.index(progress_state) >= EVIDENCE_STATES.index("triaged"):
        _validate_triage(context, job_id, cases, evidence["triaged"])
    if EVIDENCE_STATES.index(progress_state) >= EVIDENCE_STATES.index("packaged"):
        _validate_package(context, job_id, cases, evidence["packaged"])

    if candidate_state == "packaged" and all(
        other.job_id == job_id or other.state == "packaged"
        for other in store.list()
    ):
        report = reconcile_case_manifests(
            context.obligations,
            context.cases,
            artifact_root=context.run_root,
        )
        if not report.complete:
            raise ValueError(
                "final run-level case reconciliation is incomplete: "
                + json.dumps(report.to_dict(), ensure_ascii=False, sort_keys=True)
            )
        from .applicability import reconcile_applicability_bindings

        if context.applicability is not None:
            applicability_report = reconcile_applicability_bindings(
                context.applicability,
                context.obligations,
                cases=context.cases,
            )
            if not applicability_report.complete:
                raise ValueError(
                    "final run-level applicability case reconciliation is incomplete: "
                    + json.dumps(applicability_report.to_dict(), sort_keys=True)
                )


def validate_store_artifacts(store: JobStore) -> None:
    """Fail status checks when any prior evidence or run binding was altered."""

    context = _load_run_coverage_context(store)
    for record in store.list():
        validate_job_artifacts(store, record.job_id, _context=context)


def select_dispatchable_jobs(
    store: JobStore,
    *,
    limit: int = 1,
) -> tuple[JobRecord, ...]:
    """Return resumable jobs in persisted plan order.

    Failed jobs require an explicit retry and are never silently dispatched.
    Dependencies must be fully packaged before their consumer is returned.
    """

    if type(limit) is not int or limit < 1:
        raise ValueError("dispatch limit must be a positive integer")
    records = store.list()
    by_id = {record.job_id: record for record in records}
    dispatchable = [
        record
        for record in records
        if record.state not in {"packaged", "failed"}
        and all(
            by_id[dependency].state == "packaged"
            for dependency in record.dependencies
        )
    ]
    return tuple(dispatchable[:limit])


__all__ = [
    "JOB_STATES",
    "FORWARD_TRANSITIONS",
    "InvalidJobTransition",
    "DependencyNotReadyError",
    "JobRecord",
    "JobStore",
    "calculate_evidence_sha256",
    "validate_job_artifacts",
    "validate_store_artifacts",
    "select_dispatchable_jobs",
]
