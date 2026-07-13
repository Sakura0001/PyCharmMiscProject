"""Command-line control plane for feature coverage and differential runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path, PurePosixPath
from typing import Any, Sequence

from .artifact_store import (
    load_run_execution_profile,
    write_json,
)
from .applicability import reconcile_applicability_bindings
from .contracts import (
    ContractValidationError,
    execution_profile_sha256,
    load_case_manifest,
    load_coverage_plan,
    load_feature_manifest,
)
from .coverage import (
    CoverageError,
    expand_coverage_plan,
    reconcile_case_manifests,
    reconcile_obligations,
)
from .differential import (
    NormalizationProfile,
    MysqlRunner,
    MysqlTarget,
    attach_two_run_replay,
    compare_outputs,
    execute_differential,
    reserve_differential_artifacts,
    validate_basic_endpoint_identity,
    write_differential_artifacts,
)
from .jobs import (
    JobStore,
    calculate_evidence_sha256,
    select_dispatchable_jobs,
    validate_job_artifacts,
    validate_store_artifacts,
)
from .formal_run import (
    initialize_formal_run,
    load_formal_inputs,
    validate_formal_run,
)
from .editions import load_edition, resolve_edition


def _emit(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False))


def _edition_version_num(alias: str) -> int:
    return 80041 if alias in {"8.0.41", "80041", "mysql-community-8.0.41"} else 80022


def _manifest_from_argument(path: str | None, source_root: str | None = None):
    return (
        load_feature_manifest(
            path,
            verify_source=True,
            source_root=source_root,
        )
        if path
        else None
    )


def _plan_applicability(
    arguments: argparse.Namespace,
    manifest: Any,
    obligations: Sequence[Any],
    *,
    cases: Sequence[Any] | None = None,
):
    index = getattr(arguments, "applicability_index", None)
    if index is None:
        return None
    if manifest is None:
        raise ValueError("--manifest is required with --applicability-index")
    from .applicability import load_feature_applicability_index

    repository_root = getattr(arguments, "applicability_repository_root", None)
    if repository_root is None:
        repository_root = arguments.inventory_root
    applicability = load_feature_applicability_index(
        index,
        repository_root=repository_root,
        known_requirement_ids={item.requirement_id for item in manifest.requirements},
        require_complete=True,
        expected_compatibility_target=manifest.compatibility_target,
        draft=False,
    )
    if applicability.feature_id != manifest.feature_id:
        raise ValueError("applicability feature_id does not match feature manifest")
    report = reconcile_applicability_bindings(
        applicability,
        obligations,
        cases=cases,
    )
    if not report.complete:
        raise ValueError(
            "applicability reconciliation is incomplete: "
            + json.dumps(report.to_dict(), sort_keys=True)
        )
    return report


def _cmd_plan_validate(arguments: argparse.Namespace) -> int:
    manifest = _manifest_from_argument(arguments.manifest, arguments.source_root)
    plan = load_coverage_plan(
        arguments.plan,
        manifest=manifest,
        inventory_root=arguments.inventory_root,
    )
    obligations = expand_coverage_plan(plan, require_complete=True)
    applicability = _plan_applicability(arguments, manifest, obligations)
    payload = {
            "status": "valid",
            "plan_id": plan.plan_id,
            "feature_id": plan.feature_id,
            "axis_count": len(plan.axes),
            "test_point_count": len(plan.test_points),
        }
    if applicability is not None:
        payload["applicability"] = applicability.to_dict()
    _emit(payload)
    return 0


def _cmd_plan_expand(arguments: argparse.Namespace) -> int:
    manifest = _manifest_from_argument(arguments.manifest, arguments.source_root)
    plan = load_coverage_plan(
        arguments.plan,
        manifest=manifest,
        inventory_root=arguments.inventory_root,
    )
    obligations = expand_coverage_plan(plan, require_complete=arguments.require_complete)
    reconciliation = reconcile_obligations(obligations)
    applicability = _plan_applicability(arguments, manifest, obligations)
    payload = {
        "schema_version": 1,
        "kind": "coverage_obligation_set",
        "plan_id": plan.plan_id,
        "feature_id": plan.feature_id,
        "obligations": [item.to_dict() for item in obligations],
        "reconciliation": reconciliation.to_dict(),
    }
    if applicability is not None:
        payload["applicability"] = applicability.to_dict()
    if arguments.output:
        write_json(Path(arguments.output), payload)
    _emit(
        {
            "plan_id": plan.plan_id,
            "output": str(Path(arguments.output).resolve()) if arguments.output else None,
            "reconciliation": reconciliation.to_dict(),
        }
    )
    return 0 if reconciliation.complete or not arguments.require_complete else 1


def _load_case_manifests(path: str | Path):
    source = Path(path)
    if source.is_file():
        paths = [source]
    elif source.is_dir():
        paths = sorted(
            item
            for pattern in ("*.yaml", "*.yml")
            for item in source.rglob(pattern)
            if item.is_file()
        )
    else:
        raise FileNotFoundError(source)
    if not paths:
        raise ValueError(f"no case manifest YAML files found under {source}")
    return tuple(load_case_manifest(path) for path in paths)


def _cmd_plan_reconcile_cases(arguments: argparse.Namespace) -> int:
    manifest = _manifest_from_argument(arguments.manifest, arguments.source_root)
    plan = load_coverage_plan(
        arguments.plan,
        manifest=manifest,
        inventory_root=arguments.inventory_root,
    )
    obligations = expand_coverage_plan(plan, require_complete=True)
    cases = _load_case_manifests(arguments.cases)
    report = reconcile_case_manifests(
        obligations,
        cases,
        artifact_root=arguments.artifact_root,
    )
    applicability = _plan_applicability(
        arguments, manifest, obligations, cases=cases
    )
    payload = {
        "plan_id": plan.plan_id,
        "feature_id": plan.feature_id,
        "case_manifest_count": len(cases),
        "reconciliation": report.to_dict(),
    }
    if applicability is not None:
        payload["applicability"] = applicability.to_dict()
    if arguments.output:
        write_json(Path(arguments.output), payload)
    _emit(payload)
    return 0 if report.complete else 1


def _cmd_run_init(arguments: argparse.Namespace) -> int:
    inputs = load_formal_inputs(
        manifest_path=arguments.manifest,
        plan_path=arguments.plan,
        execution_profile_path=arguments.execution_profile,
        applicability_index_path=arguments.applicability_index,
        source_root=arguments.source_root,
        inventory_root=arguments.inventory_root,
    )
    paths = initialize_formal_run(
        Path(arguments.root),
        arguments.run_id,
        inputs,
        resume=arguments.resume,
    )
    root = paths["run_root"]
    report = reconcile_applicability_bindings(
        inputs.applicability, inputs.obligations
    )
    source_relative = PurePosixPath(str(inputs.manifest.source["path"]))
    _emit(
        {
            "run_id": arguments.run_id,
            "run_root": str(root.resolve()),
            "resumed": bool(arguments.resume),
            "manifest": str((root / "inputs/feature_manifest.yaml").resolve()),
            "feature_source": str(
                (root / "inputs" / Path(*source_relative.parts)).resolve()
            ),
            "execution_profile": str(
                (root / "inputs/execution_profile.yaml").resolve()
            ),
            "plan": str((root / "plans/coverage_plan.yaml").resolve()),
            "obligations": str(
                (root / "plans/coverage_obligations.json").resolve()
            ),
            "applicability_index": str(
                (
                    root
                    / "plans/applicability/bundle/feature_applicability_index.yaml"
                ).resolve()
            ),
            "jobs": str(paths["jobs"].resolve()),
            "job_count": len(inputs.plan.test_points),
            "obligation_count": len(inputs.obligations),
            "reconciliation": reconcile_obligations(
                inputs.obligations
            ).to_dict(),
            "applicability": report.to_dict(),
        }
    )
    return 0


def _cmd_run_status(arguments: argparse.Namespace) -> int:
    jobs_file = Path(arguments.jobs).resolve(strict=True)
    validate_formal_run(jobs_file.parent.parent)
    store = JobStore.open(arguments.jobs)
    validate_store_artifacts(store)
    records = store.list()
    _emit(
        {
            "plan_id": store.plan_id,
            "feature_id": store.feature_id,
            "states": dict(sorted(Counter(record.state for record in records).items())),
            "jobs": [record.to_dict() for record in records],
        }
    )
    return 0


def _cmd_run_next(arguments: argparse.Namespace) -> int:
    if arguments.limit < 1:
        raise ValueError("--limit must be a positive integer")
    jobs_file = Path(arguments.jobs).resolve(strict=True)
    formal = validate_formal_run(jobs_file.parent.parent)
    store = JobStore.open(jobs_file)
    validate_store_artifacts(store)
    all_dispatchable = select_dispatchable_jobs(
        store,
        limit=max(1, len(store.list())),
    )
    selected = all_dispatchable[: arguments.limit]
    obligations_by_point: dict[str, list[dict[str, Any]]] = {}
    for obligation in formal["obligations"]:
        obligations_by_point.setdefault(obligation.test_point_id, []).append(
            obligation.to_dict()
        )
    point_by_id = {
        point.test_point_id: point for point in formal["plan"].test_points
    }
    jobs = []
    for record in selected:
        point = point_by_id[record.job_id]
        jobs.append(
            {
                "job": record.to_dict(),
                "test_point": point.to_dict(),
                "obligations": obligations_by_point.get(record.job_id, []),
                "run_root": str(jobs_file.parent.parent),
                "jobs_path": str(jobs_file),
            }
        )
    records = store.list()
    if jobs:
        status = "dispatchable"
    elif records and all(record.state == "packaged" for record in records):
        status = "complete"
    else:
        status = "blocked"
    _emit(
        {
            "status": status,
            "plan_id": store.plan_id,
            "feature_id": store.feature_id,
            "available_count": len(all_dispatchable),
            "returned_count": len(jobs),
            "jobs": jobs,
            "failed_job_ids": [
                record.job_id for record in records if record.state == "failed"
            ],
        }
    )
    return 1 if status == "blocked" else 0


_EVIDENCE_ROOTS = {
    "audited": {"plans", "jobs"},
    "ready": {"plans", "jobs"},
    "generated": {"cases"},
    "linted": {"jobs"},
    "executed_reference": {"executions"},
    "executed_dut": {"executions"},
    "compared": {"comparisons"},
    "triaged": {"findings", "comparisons", "jobs"},
    "packaged": {"regression", "jobs"},
}


def _validated_transition_evidence(
    jobs_path: str | Path,
    state: str,
    raw_paths: Sequence[str],
) -> tuple[str, ...]:
    if not raw_paths:
        raise ValueError(f"transition to {state} requires --evidence")
    jobs_file = Path(jobs_path).resolve(strict=True)
    if jobs_file.parent.name != "jobs":
        raise ValueError("job store must be located under an initialized run jobs/ directory")
    run_root = jobs_file.parent.parent
    normalized: list[str] = []
    allowed_roots = _EVIDENCE_ROOTS[state]
    for raw_path in raw_paths:
        if "\\" in raw_path:
            raise ValueError(f"evidence path must use portable separators: {raw_path}")
        relative = PurePosixPath(raw_path)
        if relative.is_absolute() or ".." in relative.parts or not relative.parts:
            raise ValueError(f"evidence path must stay under the run root: {raw_path}")
        if relative.parts[0] not in allowed_roots:
            raise ValueError(
                f"evidence for {state} must be under: {', '.join(sorted(allowed_roots))}"
            )
        if relative.as_posix() == "jobs/jobs.json":
            raise ValueError(
                "jobs/jobs.json is mutable control state and cannot be transition evidence"
            )
        candidate = (run_root / Path(*relative.parts)).resolve(strict=True)
        try:
            candidate.relative_to(run_root)
        except ValueError as exc:
            raise ValueError(f"evidence path escapes the run root: {raw_path}") from exc
        if not candidate.is_file():
            raise ValueError(f"evidence path is not a regular file: {raw_path}")
        normalized.append(relative.as_posix())
    if len(normalized) != len(set(normalized)):
        raise ValueError("transition evidence contains duplicate paths")
    if state == "generated":
        suffixes = {PurePosixPath(path).suffix.lower() for path in normalized}
        if ".sql" not in suffixes or not suffixes.intersection({".yaml", ".yml"}):
            raise ValueError(
                "generated evidence must include at least one SQL file and one case manifest"
            )
    if state == "executed_reference" and not any(
        path.startswith("executions/reference/") and path.endswith(".json")
        for path in normalized
    ):
        raise ValueError("executed_reference evidence must include a reference execution JSON")
    if state == "executed_dut" and not any(
        path.startswith("executions/dut/") and path.endswith(".json")
        for path in normalized
    ):
        raise ValueError("executed_dut evidence must include a DUT execution JSON")
    if state == "compared" and not any(path.endswith(".json") for path in normalized):
        raise ValueError("compared evidence must include a comparison JSON")
    return tuple(normalized)


def _cmd_run_transition(arguments: argparse.Namespace) -> int:
    jobs_file = Path(arguments.jobs).resolve(strict=True)
    validate_formal_run(jobs_file.parent.parent)
    store = JobStore.open(arguments.jobs)
    validate_store_artifacts(store)
    if arguments.state == "failed":
        if arguments.evidence:
            raise ValueError("failed transitions use --error, not --evidence")
        record = store.fail(arguments.job_id, arguments.error or "unspecified failure")
    elif arguments.state == "retry":
        if arguments.evidence:
            raise ValueError("retry does not accept --evidence")
        record = store.retry(arguments.job_id)
    else:
        evidence = _validated_transition_evidence(
            arguments.jobs,
            arguments.state,
            arguments.evidence,
        )
        evidence_sha256 = calculate_evidence_sha256(arguments.jobs, evidence)
        validate_job_artifacts(
            store,
            arguments.job_id,
            candidate_state=arguments.state,
            candidate_paths=evidence,
            candidate_sha256=evidence_sha256,
        )
        if calculate_evidence_sha256(arguments.jobs, evidence) != evidence_sha256:
            raise ValueError("transition evidence changed while it was being validated")
        record = store.transition(
            arguments.job_id,
            arguments.state,
            evidence_paths=evidence,
            evidence_sha256=evidence_sha256,
        )
    _emit(record.to_dict())
    return 0


def _cmd_run_execute(arguments: argparse.Namespace) -> int:
    target = MysqlTarget(
        name=arguments.target_name,
        login_path=arguments.login_path,
        database=arguments.database,
    )
    runner = MysqlRunner(
        executable=arguments.mysql,
        timeout_seconds=arguments.timeout,
        expected_version_num=_edition_version_num(arguments.edition),
    )
    identity = runner.inspect(target)
    validate_basic_endpoint_identity(
        identity,
        expected_version_num=_edition_version_num(arguments.edition),
    )
    record = runner.run(
        arguments.sql,
        target,
        stop_on_error=arguments.stop_on_error,
    )
    post_identity = runner.inspect(target)
    validate_basic_endpoint_identity(
        post_identity,
        expected_version_num=_edition_version_num(arguments.edition),
    )
    if post_identity != identity:
        raise ValueError(
            f"{identity.target_name} endpoint identity changed between preflight and postflight"
        )
    record = replace(record, endpoint_identity=identity.to_dict())
    payload = record.to_dict()
    if arguments.output:
        write_json(Path(arguments.output), payload)
    _emit(payload)
    return 0 if record.returncode == 0 else 1


def _cmd_run_compare(arguments: argparse.Namespace) -> int:
    replacements = tuple(tuple(pair) for pair in arguments.replace)
    profile = NormalizationProfile(
        drop_line_patterns=tuple(arguments.drop_line),
        replacements=replacements,
        strip_trailing_whitespace=arguments.strip_trailing_whitespace,
    )
    reference = Path(arguments.reference).read_text(encoding="utf-8")
    dut = Path(arguments.dut).read_text(encoding="utf-8")
    result = compare_outputs(reference, dut, profile)
    payload = result.to_dict()
    if arguments.output:
        write_json(Path(arguments.output), payload)
    _emit(payload)
    return 0 if result.identical else 1


def _resolve_formal_differential_settings(
    arguments: argparse.Namespace,
    run_root: Path,
) -> dict[str, Any]:
    """Resolve connection settings from the immutable profile or legacy flags."""

    profile = load_run_execution_profile(run_root)
    if profile is not None:
        expected = {
            "reference_login_path": profile.reference.login_path,
            "reference_database": profile.reference.database,
            "dut_login_path": profile.dut.login_path,
            "dut_database": profile.dut.database,
            "mysql": profile.runner.executable,
            "timeout": profile.runner.timeout_seconds,
            "expected_reference_server_uuid": (
                profile.reference.expected_server_uuid
            ),
            "expected_dut_server_uuid": profile.dut.expected_server_uuid,
            "expected_current_user": profile.reference.expected_current_user,
            "expected_version_num": profile.target_version_num,
        }
        flag_names = {
            "reference_login_path": "--reference-login-path",
            "reference_database": "--reference-database",
            "dut_login_path": "--dut-login-path",
            "dut_database": "--dut-database",
            "mysql": "--mysql",
            "timeout": "--timeout",
        }
        conflicts = [
            flag
            for name, flag in flag_names.items()
            if getattr(arguments, name) is not None
            and getattr(arguments, name) != expected[name]
        ]
        if conflicts:
            raise ValueError(
                "direct differential flags conflict with the immutable run execution "
                "profile: " + ", ".join(conflicts)
            )
        return {
            **expected,
            "execution_profile_sha256": execution_profile_sha256(profile),
            "source": "run_execution_profile",
        }

    required = {
        "reference_login_path": "--reference-login-path",
        "reference_database": "--reference-database",
        "dut_login_path": "--dut-login-path",
        "dut_database": "--dut-database",
    }
    missing = [flag for name, flag in required.items() if getattr(arguments, name) is None]
    if missing:
        raise ValueError(
            "run has no bound execution profile; supply direct connection flags: "
            + ", ".join(missing)
        )
    timeout = arguments.timeout if arguments.timeout is not None else 300
    if type(timeout) is not int or timeout <= 0:
        raise ValueError("--timeout must be a positive integer")
    mysql = arguments.mysql if arguments.mysql is not None else "mysql"
    if not isinstance(mysql, str) or not mysql.strip():
        raise ValueError("--mysql must be a non-empty executable name or path")
    return {
        "reference_login_path": arguments.reference_login_path,
        "reference_database": arguments.reference_database,
        "dut_login_path": arguments.dut_login_path,
        "dut_database": arguments.dut_database,
        "mysql": mysql,
        "timeout": timeout,
        "expected_reference_server_uuid": None,
        "expected_dut_server_uuid": None,
        "expected_current_user": None,
        "expected_version_num": _edition_version_num(arguments.edition),
        "execution_profile_sha256": None,
        "source": "direct_flags",
    }


def _resolve_formal_case_inputs(
    run_root: Path,
    case_manifest_path: Path,
    case_id: str,
    supplied_sql_path: str | Path,
):
    """Reload and bind one formal case to its immutable in-run SQL file."""

    expected_manifest_root = (run_root / "cases" / "manifests").resolve(strict=True)
    if case_manifest_path.is_symlink() or not case_manifest_path.is_file():
        raise ValueError("case manifest must be a regular non-symbolic-link file")
    resolved_manifest = case_manifest_path.resolve(strict=True)
    try:
        resolved_manifest.relative_to(expected_manifest_root)
    except ValueError as exc:
        raise ValueError(
            "case manifest must be inside the current run cases/manifests"
        ) from exc
    case = load_case_manifest(resolved_manifest)
    if case.case_id != case_id:
        raise ValueError(
            f"case manifest id {case.case_id} does not match --case-id {case_id}"
        )

    current = run_root
    for part in PurePosixPath(case.sql_files[0]).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("case SQL must not contain symbolic-link components")
    expected_sql = current.resolve(strict=True)
    try:
        expected_sql.relative_to(run_root)
    except ValueError as exc:
        raise ValueError("case SQL escapes the current run") from exc
    if not expected_sql.is_file():
        raise ValueError("case SQL must be a regular file")
    supplied_sql = Path(supplied_sql_path).resolve(strict=True)
    if supplied_sql != expected_sql:
        raise ValueError(
            f"SQL argument does not match the case manifest: {supplied_sql} != {expected_sql}"
        )
    actual_sql_sha256 = hashlib.sha256(expected_sql.read_bytes()).hexdigest()
    if actual_sql_sha256 != case.sql_sha256:
        raise ValueError(
            f"case SQL SHA256 mismatch: declared {case.sql_sha256}, "
            f"actual {actual_sql_sha256}"
        )
    return case, expected_sql


def _validate_differential_job_gate(
    run_root: Path,
    case: Any,
) -> None:
    """Require a fully reconciled, linted job before either endpoint sees SQL."""

    jobs_path = run_root / "jobs/jobs.json"
    store = JobStore.open(jobs_path)
    validate_store_artifacts(store)
    record = store.get(case.test_point_id)
    if record.state != "linted":
        raise ValueError(
            f"formal differential requires job {record.job_id} to be exactly linted; "
            f"current state is {record.state}"
        )
    generated = set(record.evidence.get("generated", ()))
    if case.sql_files[0] not in generated:
        raise ValueError(
            f"case {case.case_id} SQL is not bound by the job generated evidence"
        )
    manifest_candidates = {
        path
        for path in generated
        if path.startswith("cases/manifests/")
        and PurePosixPath(path).suffix.lower() in {".yaml", ".yml"}
    }
    if not any(
        (run_root / path).is_file()
        and load_case_manifest(run_root / path).case_id == case.case_id
        for path in manifest_candidates
    ):
        raise ValueError(
            f"case {case.case_id} manifest is not bound by the job generated evidence"
        )


def _cmd_run_differential(arguments: argparse.Namespace) -> int:
    run_root = Path(arguments.run_root).resolve(strict=True)
    validate_formal_run(run_root)
    case_manifest_path = Path(arguments.case_manifest)
    case, expected_sql = _resolve_formal_case_inputs(
        run_root,
        case_manifest_path,
        arguments.case_id,
        arguments.sql,
    )
    if case.execution_profile != "basic_mysql":
        raise ValueError(
            f"case {case.case_id} requires external harness {case.execution_harness}; "
            "the basic run differential command must not execute it"
        )
    _validate_differential_job_gate(run_root, case)
    settings = _resolve_formal_differential_settings(arguments, run_root)
    profile = NormalizationProfile()
    runner = MysqlRunner(
        executable=settings["mysql"],
        timeout_seconds=settings["timeout"],
        expected_version_num=settings["expected_version_num"],
    )
    with reserve_differential_artifacts(
        run_root,
        arguments.case_id,
        overwrite=arguments.overwrite,
    ) as reservation:
        # The first resolution is needed to choose the runner configuration,
        # but the profile is an external file relative to this process.  Once
        # the case lock is held, re-load it and require byte-for-byte semantic
        # settings equality before either endpoint receives SQL.
        locked_settings = _resolve_formal_differential_settings(arguments, run_root)
        if locked_settings != settings:
            raise ValueError(
                "run execution profile/settings changed before differential execution"
            )
        locked_case, locked_sql = _resolve_formal_case_inputs(
            run_root,
            case_manifest_path,
            arguments.case_id,
            arguments.sql,
        )
        if locked_case != case or locked_sql != expected_sql:
            raise ValueError(
                "case manifest/SQL binding changed before differential execution"
            )
        _validate_differential_job_gate(run_root, locked_case)
        case = locked_case
        expected_sql = locked_sql
        reference_target = MysqlTarget(
            name="reference",
            login_path=settings["reference_login_path"],
            database=settings["reference_database"],
        )
        dut_target = MysqlTarget(
            name="dut",
            login_path=settings["dut_login_path"],
            database=settings["dut_database"],
        )
        execution_arguments = {
            "runner": runner,
            "profile": profile,
            "stop_on_error": True,
            "expected_outcome": case.outcome,
            "expected_sqlstate": case.comparison.get("expected_sqlstate"),
            "expected_sql_sha256": case.sql_sha256,
            "execution_profile": case.execution_profile,
            "execution_profile_sha256": locked_settings[
                "execution_profile_sha256"
            ],
            "expected_reference_server_uuid": locked_settings[
                "expected_reference_server_uuid"
            ],
            "expected_dut_server_uuid": locked_settings[
                "expected_dut_server_uuid"
            ],
            "expected_current_user": locked_settings["expected_current_user"],
            "expected_version_num": locked_settings["expected_version_num"],
        }
        first_result = execute_differential(
            expected_sql,
            reference_target,
            dut_target,
            **execution_arguments,
        )
        replay_result = execute_differential(
            expected_sql,
            reference_target,
            dut_target,
            **execution_arguments,
        )
        result = attach_two_run_replay(first_result, replay_result)
        paths = write_differential_artifacts(
            run_root,
            arguments.case_id,
            result,
            overwrite=arguments.overwrite,
            reservation=reservation,
        )
    _emit(
        {
            "case_id": arguments.case_id,
            "configuration_source": settings["source"],
            "execution_profile_sha256": result.execution_profile_sha256,
            "passed": result.passed,
            "reference_oracle_valid": result.reference_oracle_valid,
            "reference_oracle_error": result.reference_oracle_error,
            "identical": result.comparison.identical,
            "reference_returncode": result.reference.returncode,
            "dut_returncode": result.dut.returncode,
            "reference_determinism": result.reference_determinism,
            "dut_determinism": result.dut_determinism,
            "comparison": str(paths["comparison"].resolve()),
            "diff": str(paths["diff"].resolve()),
        }
    )
    return 0 if result.passed else 1


def _cmd_doctor(arguments: argparse.Namespace) -> int:
    repository_root = Path(arguments.root).resolve()
    edition_root = resolve_edition(repository_root, arguments.edition)
    edition = load_edition(
        edition_root,
        repository_root=repository_root,
        verify_files=False,
    )
    _emit(
        {
            "status": "ok",
            "edition_id": edition.edition_id,
            "target_version": edition.target_version,
            "target_version_num": edition.target_version_num,
            "review_state": edition.review_state,
            "edition_root": str(edition.root),
        }
    )
    return 0


def _cmd_skill_package(arguments: argparse.Namespace) -> int:
    from .skill_packaging import package_skill

    _emit(package_skill(Path(arguments.skill_root), Path(arguments.output)))
    return 0


def _cmd_skill_verify(arguments: argparse.Namespace) -> int:
    from .skill_packaging import verify_skill_archive

    report = verify_skill_archive(Path(arguments.archive))
    _emit(report)
    return 0 if report.get("ok") else 1


def _cmd_applicability_scaffold(arguments: argparse.Namespace) -> int:
    from .applicability import (
        load_edition_applicability_universe,
        scaffold_feature_applicability,
    )

    repository_root = Path(arguments.repository_root).resolve()
    edition_root = resolve_edition(repository_root, arguments.edition)
    edition = load_edition(
        edition_root,
        repository_root=repository_root,
        verify_files=True,
    )
    universe = load_edition_applicability_universe(edition_root)
    index = scaffold_feature_applicability(
        universe,
        arguments.output,
        feature_id=arguments.feature_id,
        universe_path=universe.source_path.relative_to(repository_root).as_posix(),
        compatibility_target=edition.edition_id,
    )
    _emit(
        {
            "status": "scaffolded",
            "index": str(index.resolve()),
            "summary": {
                "statements": universe.counts.statements,
                "statement_factor_pairs": universe.counts.statement_factor_pairs,
                "statement_factor_values": universe.counts.statement_factor_values,
                "pending": universe.counts.statement_factor_values,
            },
        }
    )
    return 0


def _cmd_applicability_refresh(arguments: argparse.Namespace) -> int:
    from .applicability import refresh_feature_applicability_index

    refreshed = refresh_feature_applicability_index(
        arguments.index,
        repository_root=arguments.repository_root,
        expected_counts=None,
    )
    _emit({"status": "refreshed", "index": str(refreshed)})
    return 0


def _cmd_applicability_validate(arguments: argparse.Namespace) -> int:
    from .applicability import load_feature_applicability_index

    manifest = _manifest_from_argument(arguments.manifest, arguments.source_root)
    requirement_ids = (
        {item.requirement_id for item in manifest.requirements}
        if manifest is not None
        else None
    )
    applicability = load_feature_applicability_index(
        arguments.index,
        repository_root=arguments.repository_root,
        known_requirement_ids=requirement_ids,
        require_complete=arguments.require_complete,
        expected_compatibility_target=(
            manifest.compatibility_target
            if manifest is not None
            else load_edition(
                resolve_edition(Path(arguments.repository_root), arguments.edition),
                repository_root=Path(arguments.repository_root),
                verify_files=False,
            ).edition_id
        ),
        draft=arguments.draft,
    )
    if manifest is not None and applicability.feature_id != manifest.feature_id:
        raise ValueError("applicability feature_id does not match feature manifest")
    _emit(
        {
            "status": "valid",
            "feature_id": applicability.feature_id,
            "index": str(applicability.index_path),
            "summary": applicability.summary.to_dict(),
        }
    )
    return 0


def _cmd_applicability_compile(arguments: argparse.Namespace) -> int:
    from .applicability import compile_feature_applicability_plan

    result = compile_feature_applicability_plan(
        manifest_path=arguments.manifest,
        base_plan_path=arguments.base_plan,
        index_path=arguments.index,
        output_path=arguments.output,
        repository_root=arguments.repository_root,
        source_root=arguments.source_root,
        inventory_root=arguments.inventory_root,
    )
    _emit(
        {
            "status": "compiled",
            "plan": str(result.output_path),
            "feature_id": result.plan.feature_id,
            "plan_id": result.plan.plan_id,
            "obligation_count": len(result.obligations),
            "generated_axis_ids": list(result.generated_axis_ids),
            "generated_test_point_ids": list(result.generated_test_point_ids),
            "canonical_upper_bound": result.canonical_upper_bound,
            "applicability": result.reconciliation.to_dict(),
        }
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mysql-case",
        description="MySQL 8.0.22/8.0.41 feature coverage and differential test control plane",
    )
    parser.add_argument(
        "--edition",
        choices=("8.0.22", "80022", "mysql-community-8.0.22", "8.0.41", "80041", "mysql-community-8.0.41"),
        help="exact MySQL Community Server edition",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    doctor = commands.add_parser("doctor", help="audit repository integrity and capabilities")
    doctor.add_argument("--root", default=".")
    doctor.set_defaults(handler=_cmd_doctor)

    plan = commands.add_parser("plan", help="validate and expand coverage plans")
    plan_commands = plan.add_subparsers(dest="plan_command", required=True)
    validate = plan_commands.add_parser("validate")
    validate.add_argument("plan")
    validate.add_argument("--manifest")
    validate.add_argument(
        "--source-root",
        help="root for feature_manifest.source.path (defaults to the manifest directory)",
    )
    validate.add_argument("--inventory-root", default=".")
    validate.add_argument("--applicability-index")
    validate.add_argument("--applicability-repository-root")
    validate.set_defaults(handler=_cmd_plan_validate)
    expand = plan_commands.add_parser("expand")
    expand.add_argument("plan")
    expand.add_argument("--manifest")
    expand.add_argument(
        "--source-root",
        help="root for feature_manifest.source.path (defaults to the manifest directory)",
    )
    expand.add_argument("--inventory-root", default=".")
    expand.add_argument("--applicability-index")
    expand.add_argument("--applicability-repository-root")
    expand.add_argument("--output")
    expand.add_argument("--require-complete", action="store_true")
    expand.set_defaults(handler=_cmd_plan_expand)
    reconcile = plan_commands.add_parser(
        "reconcile-cases",
        help="prove one case manifest exists for every executable obligation",
    )
    reconcile.add_argument("plan")
    reconcile.add_argument("--cases", required=True)
    reconcile.add_argument("--artifact-root", required=True)
    reconcile.add_argument("--manifest")
    reconcile.add_argument(
        "--source-root",
        help="root for feature_manifest.source.path (defaults to the manifest directory)",
    )
    reconcile.add_argument("--inventory-root", default=".")
    reconcile.add_argument("--applicability-index")
    reconcile.add_argument("--applicability-repository-root")
    reconcile.add_argument("--output")
    reconcile.set_defaults(handler=_cmd_plan_reconcile_cases)

    applicability = commands.add_parser(
        "applicability",
        help="scaffold, review, validate, and compile the MySQL selected edition factor universe",
    )
    applicability_commands = applicability.add_subparsers(
        dest="applicability_command", required=True
    )
    applicability_scaffold = applicability_commands.add_parser("scaffold")
    applicability_scaffold.add_argument("--repository-root", default=".")
    applicability_scaffold.add_argument("--feature-id", required=True)
    applicability_scaffold.add_argument("--output", required=True)
    applicability_scaffold.set_defaults(handler=_cmd_applicability_scaffold)
    applicability_refresh = applicability_commands.add_parser("refresh")
    applicability_refresh.add_argument("index")
    applicability_refresh.add_argument("--repository-root", default=".")
    applicability_refresh.set_defaults(handler=_cmd_applicability_refresh)
    applicability_validate = applicability_commands.add_parser("validate")
    applicability_validate.add_argument("index")
    applicability_validate.add_argument("--repository-root", default=".")
    applicability_validate.add_argument("--manifest")
    applicability_validate.add_argument("--source-root")
    applicability_validate.add_argument("--require-complete", action="store_true")
    applicability_validate.add_argument("--draft", action="store_true")
    applicability_validate.set_defaults(handler=_cmd_applicability_validate)
    applicability_compile = applicability_commands.add_parser("compile")
    applicability_compile.add_argument("--manifest", required=True)
    applicability_compile.add_argument("--base-plan", required=True)
    applicability_compile.add_argument("--index", required=True)
    applicability_compile.add_argument("--output", required=True)
    applicability_compile.add_argument("--repository-root", default=".")
    applicability_compile.add_argument("--source-root")
    applicability_compile.add_argument("--inventory-root")
    applicability_compile.set_defaults(handler=_cmd_applicability_compile)

    run = commands.add_parser("run", help="manage durable runs and execute comparisons")
    run_commands = run.add_subparsers(dest="run_command", required=True)
    initialize = run_commands.add_parser("init")
    initialize.add_argument("--root", default=".")
    initialize.add_argument("--run-id", required=True)
    initialize.add_argument("--plan", required=True)
    initialize.add_argument("--manifest", required=True)
    initialize.add_argument(
        "--source-root",
        help="root for feature_manifest.source.path (defaults to the manifest directory)",
    )
    initialize.add_argument("--inventory-root", default=".")
    initialize.add_argument(
        "--execution-profile",
        required=True,
        help=(
            "validated work-file to snapshot as inputs/execution_profile.yaml; "
            "required again with --resume when the run is profile-bound"
        ),
    )
    initialize.add_argument(
        "--applicability-index",
        required=True,
        help="complete compiled feature applicability index to snapshot",
    )
    initialize.add_argument("--resume", action="store_true")
    initialize.set_defaults(handler=_cmd_run_init)
    status = run_commands.add_parser("status")
    status.add_argument("jobs")
    status.set_defaults(handler=_cmd_run_status)
    next_job = run_commands.add_parser(
        "next",
        help="return the next dependency-ready test-point jobs in plan order",
    )
    next_job.add_argument("--jobs", required=True)
    next_job.add_argument("--limit", type=int, default=1)
    next_job.set_defaults(handler=_cmd_run_next)
    transition = run_commands.add_parser("transition")
    transition.add_argument("jobs")
    transition.add_argument("job_id")
    transition.add_argument(
        "state",
        choices=(
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
            "retry",
        ),
    )
    transition.add_argument("--error")
    transition.add_argument(
        "--evidence",
        action="append",
        default=[],
        help="run-root-relative evidence file; repeat for multiple files",
    )
    transition.set_defaults(handler=_cmd_run_transition)
    execute = run_commands.add_parser("execute")
    execute.add_argument("sql")
    execute.add_argument("--target-name", required=True)
    execute.add_argument("--login-path", required=True)
    execute.add_argument("--database", required=True)
    execute.add_argument("--mysql", default="mysql")
    execute.add_argument("--timeout", type=int, default=300)
    execute.add_argument(
        "--stop-on-error",
        action="store_true",
        default=True,
        help=argparse.SUPPRESS,
    )
    execute.add_argument(
        "--continue-on-error",
        dest="stop_on_error",
        action="store_false",
        help="low-level diagnostic mode only; formal differential cases always stop on errors",
    )
    execute.add_argument("--output")
    execute.set_defaults(handler=_cmd_run_execute)
    compare = run_commands.add_parser("compare")
    compare.add_argument("reference")
    compare.add_argument("dut")
    compare.add_argument("--drop-line", action="append", default=[])
    compare.add_argument("--replace", nargs=2, action="append", default=[])
    compare.add_argument("--strip-trailing-whitespace", action="store_true")
    compare.add_argument(
        "--keep-trailing-whitespace",
        dest="strip_trailing_whitespace",
        action="store_false",
        default=False,
        help=argparse.SUPPRESS,
    )
    compare.add_argument("--output")
    compare.set_defaults(handler=_cmd_run_compare)
    differential = run_commands.add_parser(
        "differential",
        help="execute one SQL file on MySQL selected edition and the DUT, then compare",
    )
    differential.add_argument("sql")
    differential.add_argument("--run-root", required=True)
    differential.add_argument("--case-id", required=True)
    differential.add_argument("--case-manifest", required=True)
    differential.add_argument(
        "--reference-login-path",
        help="legacy/direct mode; otherwise read from the run execution profile",
    )
    differential.add_argument(
        "--reference-database",
        help="legacy/direct mode; otherwise read from the run execution profile",
    )
    differential.add_argument(
        "--dut-login-path",
        help="legacy/direct mode; otherwise read from the run execution profile",
    )
    differential.add_argument(
        "--dut-database",
        help="legacy/direct mode; otherwise read from the run execution profile",
    )
    differential.add_argument(
        "--mysql",
        help="legacy/direct mode; defaults to mysql when no run profile is bound",
    )
    differential.add_argument(
        "--timeout",
        type=int,
        help="legacy/direct mode; defaults to 300 when no run profile is bound",
    )
    differential.add_argument("--overwrite", action="store_true")
    differential.set_defaults(handler=_cmd_run_differential)

    skill = commands.add_parser("skill", help="package or verify the Codex skill")
    skill_commands = skill.add_subparsers(dest="skill_command", required=True)
    package = skill_commands.add_parser("package")
    package.add_argument("--skill-root", required=True)
    package.add_argument("--output", required=True)
    package.set_defaults(handler=_cmd_skill_package)
    verify = skill_commands.add_parser("verify")
    verify.add_argument("archive")
    verify.set_defaults(handler=_cmd_skill_verify)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        arguments = parser.parse_args(list(argv) if argv is not None else None)
        if arguments.edition is None:
            raise ValueError("--edition is required; use 8.0.22 or 8.0.41")
        return int(arguments.handler(arguments))
    except SystemExit as exc:
        # Keep the library entry point testable while argparse still prints its
        # normal actionable usage error to stderr.  The console script raises
        # SystemExit(main()), so process behavior remains unchanged.
        return int(exc.code or 0)
    except (
        ContractValidationError,
        CoverageError,
        FileExistsError,
        FileNotFoundError,
        KeyError,
        OSError,
        re.error,
        TypeError,
        ValueError,
        subprocess.SubprocessError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _dedicated_main(edition: str, argv: Sequence[str] | None) -> int:
    values = list(argv) if argv is not None else sys.argv[1:]
    if "--edition" in values:
        index = values.index("--edition")
        supplied = values[index + 1] if index + 1 < len(values) else ""
        expected_root = resolve_edition(Path.cwd(), edition).name
        try:
            supplied_root = resolve_edition(Path.cwd(), supplied).name
        except ValueError:
            supplied_root = ""
        if supplied_root != expected_root:
            print(
                f"error: --edition {supplied!r} conflicts with dedicated {edition} entry point",
                file=sys.stderr,
            )
            return 2
        return main(values)
    return main(["--edition", edition, *values])


def main_8022(argv: Sequence[str] | None = None) -> int:
    return _dedicated_main("8.0.22", argv)


def main_8041(argv: Sequence[str] | None = None) -> int:
    return _dedicated_main("8.0.41", argv)


if __name__ == "__main__":
    raise SystemExit(main())
