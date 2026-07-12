from __future__ import annotations

import contextlib
import csv
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

from pg_case_factory.cli import main
from pg_case_factory.applicability import (
    DEFAULT_LEDGER_PATH,
    LEDGER_COLUMNS,
    UniverseCounts,
    load_applicability_universe,
    refresh_feature_applicability_index,
    scaffold_feature_applicability,
)
from pg_case_factory.contracts import REQUIRED_RISK_DECISIONS, inventory_values_sha256
from pg_case_factory.regression_style import (
    HuaweiSqlHeader,
    build_regression_batch_mapping,
    render_huawei_sql_header,
)


TINY_UNIVERSE_COUNTS = UniverseCounts(1, 1, 1)


def _write_plan(
    path: Path,
    *,
    feature_id: str = "feature_cli",
    requirement_id: str = "req_1",
) -> None:
    table_values = ["heap", "partitioned"]
    column_values = ["integer", "text"]
    inventory_path = (
        path.parent
        / "skills"
        / "pg-sql-generation"
        / "references"
        / "combinations"
        / "_shared"
        / "coverage_inventory.yaml"
    )
    inventory_path.parent.mkdir(parents=True, exist_ok=True)
    inventory_path.write_text(
        "table_kinds:\n  all_table_kinds: [heap, partitioned]\n",
        encoding="utf-8",
    )
    type_path = (
        path.parent
        / "skills"
        / "pg-sql-generation"
        / "references"
        / "common"
        / "pg18_type_catalog.md"
    )
    type_path.parent.mkdir(parents=True, exist_ok=True)
    type_path.write_text(
        "```yaml\nstructured_config:\n  types:\n    integer: {}\n    text: {}\n```\n",
        encoding="utf-8",
    )
    path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "kind": "coverage_plan",
                "plan_id": "plan_cli",
                "feature_id": feature_id,
                "axes": {
                    "table_kind": {
                        "values": table_values,
                        "inventory_source": "skills/pg-sql-generation/references/combinations/_shared/coverage_inventory.yaml#table_kinds.all_table_kinds",
                        "coverage_mode": "complete",
                        "inventory_count": len(table_values),
                        "inventory_sha256": inventory_values_sha256(table_values),
                    },
                    "column_type": {
                        "values": column_values,
                        "inventory_source": "skills/pg-sql-generation/references/common/pg18_type_catalog.md#structured_config.types",
                        "coverage_mode": "complete",
                        "inventory_count": len(column_values),
                        "inventory_sha256": inventory_values_sha256(column_values),
                    },
                },
                "scope_decisions": {
                    "object": {
                        "status": "not_applicable",
                        "reason": "The CLI fixture does not exercise generic SQL objects.",
                    },
                    "relation": {
                        "status": "not_applicable",
                        "reason": "The CLI fixture is intentionally table-specific.",
                    },
                    "table": {
                        "status": "not_applicable",
                        "reason": "The compact CLI fixture does not claim canonical table dimensions.",
                    },
                    "column_type": {
                        "status": "not_applicable",
                        "reason": "The compact CLI fixture does not claim the complete type universe.",
                    },
                },
                "risk_decisions": {
                    risk: (
                        {
                            "status": "covered",
                            "axes": ["table_kind", "column_type"],
                            "test_points": ["tp_create"],
                        }
                        if risk in {"syntax", "operation"}
                        else {
                            "status": "not_applicable",
                            "reason": f"The CLI fixture does not exercise {risk} semantics.",
                        }
                    )
                    for risk in REQUIRED_RISK_DECISIONS
                },
                "test_points": [
                    {
                        "id": "tp_create",
                        "title": "Create and query",
                        "requirement_ids": [requirement_id],
                        "core_axes": ["table_kind", "column_type"],
                        "dependencies": [],
                        "default_outcome": "success",
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _write_formal_support(
    root: Path,
    *,
    feature_id: str = "feature_cli",
    requirement_id: str = "req_1",
) -> tuple[Path, Path, Path]:
    """Create a one-row formal applicability fixture for CLI integration tests.

    Production formal runs always use the pinned 9,978-row universe.  These
    tests patch only the expected count while retaining the exact same schema,
    snapshot, atomic-publication, and reconciliation paths.
    """

    source = root / "feature.md"
    source.write_text("# Feature\n\nPreserve visible PostgreSQL behavior.\n", encoding="utf-8")
    manifest = root / "feature_manifest.yaml"
    manifest.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "kind": "feature_manifest",
                "feature_id": feature_id,
                "title": "Formal CLI fixture",
                "compatibility_target": "postgresql-18.4",
                "source": {
                    "path": source.name,
                    "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                },
                "requirements": [
                    {
                        "id": requirement_id,
                        "description": "Preserve visible PostgreSQL behavior.",
                        "source": {"section": "Feature"},
                    }
                ],
                "metadata": {"unresolved_questions": []},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    profile = root / "execution_profile.yaml"
    profile.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "kind": "execution_profile",
                "compatibility_target": "postgresql-18.4",
                "reference": {
                    "service": "pg18_reference",
                    "database": "regression",
                    "expected_system_identifier": "111111",
                    "expected_current_user": "regression_user",
                },
                "dut": {
                    "service": "storage_engine_dut",
                    "database": "regression",
                    "expected_system_identifier": "222222",
                    "expected_current_user": "regression_user",
                },
                "runner": {
                    "executable": "/opt/pg18/bin/psql",
                    "timeout_seconds": 47,
                    "stop_on_error": True,
                },
                "comparison": {
                    "mode": "exact_text",
                    "normalization": {
                        "drop_line_patterns": [],
                        "replacements": [],
                        "strip_trailing_whitespace": False,
                    },
                },
                "security": {
                    "credential_source": "external-libpq-service",
                    "persist_credentials": False,
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    ledger = root / DEFAULT_LEDGER_PATH
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LEDGER_COLUMNS, delimiter="\t")
        writer.writeheader()
        writer.writerow(
            {
                "statement_key": "test_statement",
                "source_reference": "references/statements/ddl/table/test_statement.md",
                "factor": "mode",
                "tier": "T1",
                "value": "baseline",
                "synopsis_change": "unchanged",
                "document_change": "unchanged",
                "review_status": "static_reviewed",
                "catalog_readiness": "static_ready",
                "factor_disposition": "inherited_unchanged",
                "required_test_points": "",
                "official_source_target": "https://www.postgresql.org/docs/18/sql-test.html",
                "evidence": "sql-test:fixture",
            }
        )
    universe = load_applicability_universe(
        ledger,
        expected_counts=TINY_UNIVERSE_COUNTS,
    )
    bundle = root / "feature_applicability"
    index = scaffold_feature_applicability(
        universe,
        bundle,
        feature_id=feature_id,
        universe_path=str(DEFAULT_LEDGER_PATH),
    )
    review_path = bundle / "reviews" / "test_statement.yaml"
    review = yaml.safe_load(review_path.read_text(encoding="utf-8"))
    exclusion = {"status": "justified_exclusion", "reason_id": "EXC-ALL"}
    review["statement_decision"] = dict(exclusion)
    review["factors"][0]["factor_decision"] = dict(exclusion)
    review["factors"][0]["values"][0]["decision"] = dict(exclusion)
    review["reasons"] = [
        {
            "id": "EXC-ALL",
            "text": (
                "The synthetic one-row applicability statement is outside this "
                "CLI fixture; the base plan remains independently executable."
            ),
            "requirement_ids": [requirement_id],
            "source_locators": [
                f"feature:{requirement_id}",
                "pg18:sql-test",
            ],
        }
    ]
    review_path.write_text(
        yaml.safe_dump(review, allow_unicode=True, sort_keys=False, width=1000),
        encoding="utf-8",
    )
    refresh_feature_applicability_index(
        index,
        repository_root=root,
        expected_counts=TINY_UNIVERSE_COUNTS,
    )
    return manifest, profile, index


class CliTests(unittest.TestCase):
    def _init_plan_run(
        self,
        root: Path,
        run_id: str = "job-gate",
        *,
        expected_failure: bool = False,
    ) -> Path:
        plan = root / "plan.yaml"
        _write_plan(plan)
        if expected_failure:
            document = yaml.safe_load(plan.read_text(encoding="utf-8"))
            document["test_points"][0]["default_outcome"] = "expected_failure"
            document["test_points"][0]["default_reason"] = (
                "The fixture intentionally exercises the upstream failure oracle."
            )
            plan.write_text(
                yaml.safe_dump(document, sort_keys=False),
                encoding="utf-8",
            )
        manifest, profile, applicability = _write_formal_support(root)
        self._formal_universe_counts = TINY_UNIVERSE_COUNTS
        code, stdout, stderr = self._invoke(
            [
                "run",
                "init",
                "--root",
                str(root),
                "--run-id",
                run_id,
                "--plan",
                str(plan),
                "--manifest",
                str(manifest),
                "--execution-profile",
                str(profile),
                "--applicability-index",
                str(applicability),
                "--inventory-root",
                str(root),
            ]
        )
        self.assertEqual(0, code, stderr)
        return Path(json.loads(stdout)["run_root"])

    def _write_run_cases(self, run_root: Path, limit: int | None = None) -> list[str]:
        obligations = json.loads(
            (run_root / "plans" / "coverage_obligations.json").read_text(
                encoding="utf-8"
            )
        )["obligations"]
        selected = obligations if limit is None else obligations[:limit]
        evidence: list[str] = []
        for index, obligation in enumerate(selected, 1):
            case_id = f"CASE-{index:03d}"
            sql_relative = f"cases/sql/{case_id}.sql"
            sql_content = render_huawei_sql_header(
                HuaweiSqlHeader(
                    author="00123456 Test Agent",
                    create_at="2026-07-13",
                    version="1.0",
                    description=f"Verify obligation {obligation['obligation_id']}",
                    fe="PG18-COMPAT",
                )
            ) + f"SELECT {index};\n"
            sql_path = run_root / sql_relative
            sql_path.write_text(sql_content, encoding="utf-8")
            manifest_relative = f"cases/manifests/{case_id}.yaml"
            manifest = {
                "schema_version": 1,
                "kind": "case_manifest",
                "case_id": case_id,
                "test_point_id": obligation["test_point_id"],
                "obligation_id": obligation["obligation_id"],
                "outcome": obligation["outcome"],
                "sql_files": [sql_relative],
                "sql_sha256": hashlib.sha256(sql_content.encode("utf-8")).hexdigest(),
                "execution_profile": "basic_psql",
                "comparison": {
                    "mode": "exact_text",
                    "oracle": "upstream-postgresql-18.4",
                    "require_identical": True,
                },
                "cleanup": {"required": True, "idempotent": True},
                "metadata": {"assignments": obligation["assignments"]},
            }
            if obligation["outcome"] == "expected_failure":
                manifest["comparison"]["expected_sqlstate"] = "0A000"
            (run_root / manifest_relative).write_text(
                yaml.safe_dump(manifest, sort_keys=False),
                encoding="utf-8",
            )
            evidence.extend((manifest_relative, sql_relative))
        return evidence

    def _point_obligations(self, run_root: Path) -> list[dict]:
        return [
            obligation
            for obligation in json.loads(
                (run_root / "plans/coverage_obligations.json").read_text(
                    encoding="utf-8"
                )
            )["obligations"]
            if obligation["test_point_id"] == "tp_create"
        ]

    def _write_audit_evidence(self, run_root: Path) -> list[str]:
        relative = "jobs/audits/tp_create.json"
        path = run_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "kind": "test_point_audit",
                    "plan_id": "plan_cli",
                    "feature_id": "feature_cli",
                    "test_point_id": "tp_create",
                    "status": "approved",
                    "obligation_ids": [
                        item["obligation_id"] for item in self._point_obligations(run_root)
                    ],
                    "unresolved_items": [],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return [relative]

    def _write_ready_evidence(
        self,
        run_root: Path,
        *,
        harness_ids: list[str] | None = None,
    ) -> list[str]:
        harness_ids = sorted(harness_ids or [])
        relative = "jobs/readiness/tp_create.json"
        path = run_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        obligations = self._point_obligations(run_root)
        path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "kind": "test_point_readiness",
                    "plan_id": "plan_cli",
                    "feature_id": "feature_cli",
                    "test_point_id": "tp_create",
                    "status": "ready",
                    "obligation_ids": [item["obligation_id"] for item in obligations],
                    "execution_profiles": sorted(
                        {
                            item["execution_profile"]
                            for item in obligations
                            if item["outcome"] != "justified_na"
                        }
                    ),
                    "execution_harnesses": harness_ids,
                    "blockers": [],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return [relative] + [
            f"jobs/harnesses/{harness_id}.json" for harness_id in harness_ids
        ]

    def _write_lint_evidence(self, run_root: Path) -> list[str]:
        relative = "jobs/lint/tp_create.json"
        path = run_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        cases = []
        for manifest_path in sorted((run_root / "cases/manifests").glob("*.yaml")):
            case = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
            manifest_relative = manifest_path.relative_to(run_root).as_posix()
            checks = (
                {
                    "regression_header": "passed",
                    "catalog_observability": "passed",
                    "sql_safety": "passed",
                }
                if case["execution_profile"] == "basic_psql"
                else {
                    "regression_header": "passed",
                    "catalog_observability": "passed",
                    "external_harness_contract": "passed",
                }
            )
            cases.append(
                {
                    "case_id": case["case_id"],
                    "obligation_id": case["obligation_id"],
                    "manifest_path": manifest_relative,
                    "manifest_sha256": hashlib.sha256(
                        manifest_path.read_bytes()
                    ).hexdigest(),
                    "sql_path": case["sql_files"][0],
                    "sql_sha256": case["sql_sha256"],
                    "checks": checks,
                }
            )
        path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "kind": "test_point_lint_report",
                    "plan_id": "plan_cli",
                    "feature_id": "feature_cli",
                    "test_point_id": "tp_create",
                    "status": "passed",
                    "errors": [],
                    "cases": cases,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return [relative]

    def _transition(
        self,
        run_root: Path,
        state: str,
        evidence: list[str],
    ) -> tuple[int, str, str]:
        arguments = [
            "run",
            "transition",
            str(run_root / "jobs" / "jobs.json"),
            "tp_create",
            state,
        ]
        for path in evidence:
            arguments.extend(("--evidence", path))
        return self._invoke(arguments)

    def test_run_init_copies_and_reverifies_the_feature_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = root / "plan.yaml"
            _write_plan(
                plan,
                feature_id="feature-copy",
                requirement_id="REQ-1",
            )
            manifest, profile, applicability = _write_formal_support(
                root,
                feature_id="feature-copy",
                requirement_id="REQ-1",
            )
            source = root / "feature.md"
            self._formal_universe_counts = TINY_UNIVERSE_COUNTS
            runtime = root / "runtime"
            code, stdout, stderr = self._invoke(
                [
                    "run",
                    "init",
                    "--root",
                    str(runtime),
                    "--run-id",
                    "feature-copy",
                    "--manifest",
                    str(manifest),
                    "--plan",
                    str(plan),
                    "--inventory-root",
                    str(root),
                    "--execution-profile",
                    str(profile),
                    "--applicability-index",
                    str(applicability),
                ]
            )

            self.assertEqual(0, code, stderr)
            payload = json.loads(stdout)
            copied_source = runtime / "artifacts" / "runs" / "feature-copy" / "inputs" / "feature.md"
            self.assertEqual(source.read_bytes(), copied_source.read_bytes())
            self.assertEqual(str(copied_source.resolve()), payload["feature_source"])

    def test_basic_differential_refuses_external_isolated_case_before_connecting(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_root = self._init_plan_run(Path(temporary), "external-case")
            self._write_run_cases(run_root)
            manifest_path = run_root / "cases" / "manifests" / "CASE-001.yaml"
            document = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
            document["execution_profile"] = "external_isolated"
            document["execution_harness"] = "external-copy-stdin"
            manifest_path.write_text(
                yaml.safe_dump(document, sort_keys=False),
                encoding="utf-8",
            )
            sql_path = run_root / document["sql_files"][0]

            with mock.patch("pg_case_factory.differential.subprocess.run") as run:
                code, stdout, stderr = self._invoke(
                    [
                        "run",
                        "differential",
                        str(sql_path),
                        "--run-root",
                        str(run_root),
                        "--case-id",
                        "CASE-001",
                        "--case-manifest",
                        str(manifest_path),
                        "--reference-service",
                        "pg18-reference",
                        "--reference-database",
                        "regression",
                        "--dut-service",
                        "dut",
                        "--dut-database",
                        "regression",
                    ]
                )

            self.assertEqual(2, code)
            self.assertEqual("", stdout)
            self.assertIn("requires external harness external-copy-stdin", stderr)
            run.assert_not_called()

    def test_formal_cli_binds_expected_failure_to_terminal_sqlstate(self):
        from pg_case_factory.differential import EndpointIdentity, ExecutionRecord

        for run_id, actual_sqlstate, expected_code in (
            ("oracle-injection", "22012", 1),
            ("oracle-valid", "0A000", 0),
        ):
            with self.subTest(actual_sqlstate=actual_sqlstate):
                with tempfile.TemporaryDirectory() as temporary:
                    run_root = self._init_plan_run(
                        Path(temporary),
                        run_id,
                        expected_failure=True,
                    )
                    for state, evidence in (
                        ("audited", self._write_audit_evidence(run_root)),
                        ("ready", self._write_ready_evidence(run_root)),
                    ):
                        transition_code, _, transition_error = self._transition(
                            run_root,
                            state,
                            evidence,
                        )
                        self.assertEqual(0, transition_code, transition_error)
                    generated = self._write_run_cases(run_root)
                    transition_code, _, transition_error = self._transition(
                        run_root,
                        "generated",
                        generated,
                    )
                    self.assertEqual(0, transition_code, transition_error)
                    transition_code, _, transition_error = self._transition(
                        run_root,
                        "linted",
                        self._write_lint_evidence(run_root),
                    )
                    self.assertEqual(0, transition_code, transition_error)
                    manifest_path = (
                        run_root / "cases" / "manifests" / "CASE-001.yaml"
                    )
                    manifest = yaml.safe_load(
                        manifest_path.read_text(encoding="utf-8")
                    )
                    sql_path = run_root / manifest["sql_files"][0]

                    def identity(target):
                        return EndpointIdentity(
                            target_name=target.name,
                            service=target.service,
                            database=target.database,
                            server_version_num=180004,
                            system_identifier=(
                                "111111" if target.name == "reference" else "222222"
                            ),
                            server_address="127.0.0.1",
                            server_port=(
                                "5432" if target.name == "reference" else "5433"
                            ),
                            current_user="regression_user",
                        )

                    def inspect(_runner, target):
                        return identity(target)

                    def run_content(
                        _runner,
                        content,
                        label,
                        target,
                        *,
                        stop_on_error=True,
                    ):
                        stderr = (
                            "psql:<stdin>:1: NOTICE:  0A000: injected expected code\n"
                            f"psql:<stdin>:2: ERROR:  {actual_sqlstate}: terminal error\n"
                        )
                        return ExecutionRecord(
                            target.name,
                            str(label),
                            3,
                            "",
                            stderr,
                            0.1,
                            endpoint_identity=identity(target).to_dict(),
                        )

                    with mock.patch(
                        "pg_case_factory.differential.PsqlRunner.inspect",
                        new=inspect,
                    ), mock.patch(
                        "pg_case_factory.differential.PsqlRunner.run_content",
                        new=run_content,
                    ):
                        code, stdout, stderr = self._invoke(
                            [
                                "run",
                                "differential",
                                str(sql_path),
                                "--run-root",
                                str(run_root),
                                "--case-id",
                                "CASE-001",
                                "--case-manifest",
                                str(manifest_path),
                            ]
                        )

                    self.assertEqual(expected_code, code, stderr)
                    payload = json.loads(stdout)
                    self.assertIs(expected_code == 0, payload["reference_oracle_valid"])
                    self.assertTrue(
                        payload["reference_determinism"]["deterministic"]
                    )
                    self.assertTrue(payload["dut_determinism"]["deterministic"])

    def _invoke(self, arguments: list[str]) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        counts = getattr(self, "_formal_universe_counts", None)
        count_patch = (
            mock.patch(
                "pg_case_factory.formal_run.SHIPPED_UNIVERSE_COUNTS",
                counts,
            )
            if counts is not None
            else contextlib.nullcontext()
        )
        with count_patch, contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main(arguments)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_plan_validate_and_expand_write_machine_readable_results(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = root / "plan.yaml"
            output = root / "obligations.json"
            _write_plan(plan)

            code, stdout, stderr = self._invoke(
                [
                    "plan",
                    "validate",
                    str(plan),
                    "--inventory-root",
                    str(root),
                ]
            )
            self.assertEqual(0, code, stderr)
            self.assertEqual("valid", json.loads(stdout)["status"])

            code, stdout, stderr = self._invoke(
                [
                    "plan",
                    "expand",
                    str(plan),
                    "--inventory-root",
                    str(root),
                    "--output",
                    str(output),
                    "--require-complete",
                ]
            )
            self.assertEqual(0, code, stderr)
            report = json.loads(stdout)
            self.assertEqual(4, report["reconciliation"]["total"])
            self.assertTrue(report["reconciliation"]["complete"])
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(4, len(payload["obligations"]))

    def test_run_init_creates_isolated_layout_and_one_job_per_test_point(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_root = self._init_plan_run(root, "feature-cli-001")
            self.assertTrue((run_root / "run.json").is_file())
            self.assertTrue((run_root / "plans" / "coverage_plan.yaml").is_file())
            self.assertTrue((run_root / "plans" / "coverage_obligations.json").is_file())
            jobs = json.loads((run_root / "jobs" / "jobs.json").read_text(encoding="utf-8"))
            self.assertEqual(["tp_create"], [job["job_id"] for job in jobs["jobs"]])

            code, stdout, stderr = self._invoke(
                ["run", "status", str(run_root / "jobs" / "jobs.json")]
            )
            self.assertEqual(0, code, stderr)
            self.assertEqual({"planned": 1}, json.loads(stdout)["states"])

    def test_run_next_returns_deterministic_context_and_never_dispatches_failed_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_root = self._init_plan_run(Path(temporary), "dispatch-next")
            jobs_path = run_root / "jobs/jobs.json"

            code, stdout, stderr = self._invoke(
                ["run", "next", "--jobs", str(jobs_path), "--limit", "1"]
            )

            self.assertEqual(0, code, stderr)
            payload = json.loads(stdout)
            self.assertEqual("dispatchable", payload["status"])
            self.assertEqual(1, payload["returned_count"])
            self.assertEqual("tp_create", payload["jobs"][0]["job"]["job_id"])
            self.assertEqual(4, len(payload["jobs"][0]["obligations"]))
            self.assertEqual(
                "tp_create", payload["jobs"][0]["test_point"]["id"]
            )

            code, stdout, stderr = self._invoke(
                [
                    "run",
                    "transition",
                    str(jobs_path),
                    "tp_create",
                    "failed",
                    "--error",
                    "child agent generation failed",
                ]
            )
            self.assertEqual(0, code, stderr)

            code, stdout, stderr = self._invoke(
                ["run", "next", "--jobs", str(jobs_path)]
            )
            self.assertEqual(1, code)
            self.assertEqual("", stderr)
            payload = json.loads(stdout)
            self.assertEqual("blocked", payload["status"])
            self.assertEqual(["tp_create"], payload["failed_job_ids"])

            code, stdout, stderr = self._invoke(
                ["run", "next", "--jobs", str(jobs_path), "--limit", "0"]
            )
            self.assertEqual(2, code)
            self.assertEqual("", stdout)
            self.assertIn("positive integer", stderr)

    def test_generated_transition_requires_every_executable_obligation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_root = self._init_plan_run(Path(temporary), "point-reconcile")
            code, _, stderr = self._transition(
                run_root,
                "audited",
                self._write_audit_evidence(run_root),
            )
            self.assertEqual(0, code, stderr)
            code, _, stderr = self._transition(
                run_root,
                "ready",
                self._write_ready_evidence(run_root),
            )
            self.assertEqual(0, code, stderr)

            one_case = self._write_run_cases(run_root, limit=1)
            code, stdout, stderr = self._transition(run_root, "generated", one_case)

            self.assertEqual(2, code)
            self.assertEqual("", stdout)
            self.assertIn("case reconciliation is incomplete", stderr)
            jobs = json.loads(
                (run_root / "jobs" / "jobs.json").read_text(encoding="utf-8")
            )
            self.assertEqual("ready", jobs["jobs"][0]["state"])

    def test_audit_and_lint_transitions_reject_arbitrary_self_reports(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_root = self._init_plan_run(Path(temporary), "strict-evidence")
            audit_relative = "jobs/audits/tp_create.json"
            audit_path = run_root / audit_relative
            audit_path.parent.mkdir(parents=True, exist_ok=True)
            audit_path.write_text('{"safe": true}\n', encoding="utf-8")

            code, stdout, stderr = self._transition(
                run_root, "audited", [audit_relative]
            )

            self.assertEqual(2, code)
            self.assertEqual("", stdout)
            self.assertIn("invalid test-point-audit schema", stderr)

            code, _, stderr = self._transition(
                run_root, "audited", self._write_audit_evidence(run_root)
            )
            self.assertEqual(0, code, stderr)
            code, _, stderr = self._transition(
                run_root, "ready", self._write_ready_evidence(run_root)
            )
            self.assertEqual(0, code, stderr)
            generated = self._write_run_cases(run_root)
            code, _, stderr = self._transition(run_root, "generated", generated)
            self.assertEqual(0, code, stderr)

            lint_relative = "jobs/lint/tp_create.json"
            lint_path = run_root / lint_relative
            lint_path.parent.mkdir(parents=True, exist_ok=True)
            lint_path.write_text('{"safe": true}\n', encoding="utf-8")
            code, stdout, stderr = self._transition(
                run_root, "linted", [lint_relative]
            )

            self.assertEqual(2, code)
            self.assertEqual("", stdout)
            self.assertIn("invalid test-point-lint schema", stderr)

    def test_ready_transition_requires_verified_external_harness(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = root / "plan.yaml"
            _write_plan(plan)
            document = yaml.safe_load(plan.read_text(encoding="utf-8"))
            document["risk_decisions"]["syntax"][
                "execution_harness"
            ] = "external-syntax-probe"
            document["test_points"][0]["default_execution_profile"] = (
                "external_isolated"
            )
            document["test_points"][0]["default_execution_harness"] = (
                "external-syntax-probe"
            )
            plan.write_text(
                yaml.safe_dump(document, sort_keys=False),
                encoding="utf-8",
            )
            manifest, profile, applicability = _write_formal_support(root)
            self._formal_universe_counts = TINY_UNIVERSE_COUNTS
            code, stdout, stderr = self._invoke(
                [
                    "run",
                    "init",
                    "--root",
                    str(root),
                    "--run-id",
                    "harness-gate",
                    "--plan",
                    str(plan),
                    "--manifest",
                    str(manifest),
                    "--execution-profile",
                    str(profile),
                    "--applicability-index",
                    str(applicability),
                    "--inventory-root",
                    str(root),
                ]
            )
            self.assertEqual(0, code, stderr)
            run_root = Path(json.loads(stdout)["run_root"])
            code, _, stderr = self._transition(
                run_root, "audited", self._write_audit_evidence(run_root)
            )
            self.assertEqual(0, code, stderr)

            ready_evidence = self._write_ready_evidence(
                run_root,
                harness_ids=["external-syntax-probe"],
            )
            code, stdout, stderr = self._transition(
                run_root,
                "ready",
                ready_evidence[:1],
            )
            self.assertEqual(2, code)
            self.assertEqual("", stdout)
            self.assertIn("external-syntax-probe.json", stderr)

            harness_relative = "jobs/harnesses/external-syntax-probe.json"
            (run_root / harness_relative).parent.mkdir(exist_ok=True)
            implementation_relative = (
                "jobs/harnesses/implementations/external-syntax-probe.py"
            )
            implementation_path = run_root / implementation_relative
            implementation_path.parent.mkdir(parents=True, exist_ok=True)
            implementation_path.write_text(
                "# deterministic external harness fixture\n",
                encoding="utf-8",
            )
            implementation = {
                "path": implementation_relative,
                "sha256": hashlib.sha256(
                    implementation_path.read_bytes()
                ).hexdigest(),
            }
            execution_profile_sha = json.loads(
                (run_root / "run.json").read_text(encoding="utf-8")
            )["metadata"]["execution_profile_sha256"]
            event_model = ["provision", "execute", "collect", "cleanup"]
            probe = {"command": "external-probe --check"}
            probe_fingerprint = hashlib.sha256(
                json.dumps(
                    {
                        "event_model": event_model,
                        "execution_profile_sha256": execution_profile_sha,
                        "implementation": implementation,
                        "probe": probe,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
            (run_root / harness_relative).write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "kind": "execution_harness_verification",
                        "harness_id": "external-syntax-probe",
                        "status": "ready",
                        "compatibility_target": "postgresql-18.4",
                        "execution_profile_sha256": execution_profile_sha,
                        "implementation": implementation,
                        "event_model": event_model,
                        "probe": probe,
                        "fingerprint": probe_fingerprint,
                        "verified_at": "2026-07-12T00:00:00Z",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            code, _, stderr = self._transition(
                run_root,
                "ready",
                ready_evidence + [implementation_relative],
            )
            self.assertEqual(0, code, stderr)

    def test_status_rejects_evidence_modified_after_transition(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_root = self._init_plan_run(Path(temporary), "tampered-evidence")
            audit_relative = self._write_audit_evidence(run_root)[0]
            audit = run_root / audit_relative
            code, _, stderr = self._transition(
                run_root,
                "audited",
                [audit_relative],
            )
            self.assertEqual(0, code, stderr)
            audit.write_text('{"reviewed": false}\n', encoding="utf-8")

            code, stdout, stderr = self._invoke(
                ["run", "status", str(run_root / "jobs" / "jobs.json")]
            )

            self.assertEqual(2, code)
            self.assertEqual("", stdout)
            self.assertIn("evidence was modified after transition", stderr)

    def test_reference_transition_rejects_empty_execution_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_root = self._init_plan_run(Path(temporary), "empty-execution")
            for state, evidence in (
                ("audited", self._write_audit_evidence(run_root)),
                ("ready", self._write_ready_evidence(run_root)),
            ):
                code, _, stderr = self._transition(
                    run_root,
                    state,
                    evidence,
                )
                self.assertEqual(0, code, stderr)
            generated = self._write_run_cases(run_root)
            code, _, stderr = self._transition(run_root, "generated", generated)
            self.assertEqual(0, code, stderr)
            code, _, stderr = self._transition(
                run_root,
                "linted",
                self._write_lint_evidence(run_root),
            )
            self.assertEqual(0, code, stderr)

            case_manifests = sorted((run_root / "cases" / "manifests").glob("*.yaml"))
            reference_evidence: list[str] = []
            for index, manifest_path in enumerate(case_manifests):
                case = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
                case_id = case["case_id"]
                record_relative = f"executions/reference/{case_id}.json"
                reference_evidence.append(record_relative)
                stdout = f"value-{index}\n"
                (run_root / f"executions/reference/{case_id}.stdout").write_text(
                    stdout,
                    encoding="utf-8",
                )
                (run_root / f"executions/reference/{case_id}.stderr").write_text(
                    "",
                    encoding="utf-8",
                )
                sql_file = run_root / case["sql_files"][0]
                record = {
                    "target_name": "reference",
                    "sql_file": str(sql_file.resolve()),
                    "returncode": 0,
                    "stdout": stdout,
                    "stderr": "",
                    "duration_seconds": 0.1,
                    "endpoint_identity": {
                        "target_name": "reference",
                        "service": "pg18_reference",
                        "database": "regression",
                        "server_version_num": 180004,
                        "system_identifier": "123456",
                        "server_address": "127.0.0.1",
                        "server_port": "5432",
                        "current_user": "regression_user",
                        "is_superuser": False,
                        "can_createdb": False,
                        "can_createrole": False,
                        "can_replication": False,
                        "can_bypassrls": False,
                        "dangerous_role_memberships": [],
                        "privileged_role_memberships": [],
                    },
                    "sql_sha256": case["sql_sha256"],
                    "execution_profile_sha256": None,
                }
                (run_root / record_relative).write_text(
                    "{}\n" if index == 0 else json.dumps(record) + "\n",
                    encoding="utf-8",
                )

            code, stdout, stderr = self._transition(
                run_root,
                "executed_reference",
                reference_evidence,
            )

            self.assertEqual(2, code)
            self.assertEqual("", stdout)
            self.assertIn("must be a non-empty JSON object", stderr)

    def test_difference_requires_bound_finding_and_package_closes_all_cases(self) -> None:
        from pg_case_factory.differential import (
            DifferentialExecutionResult,
            ExecutionRecord,
            attach_two_run_replay,
            compare_execution_records,
            write_differential_artifacts,
        )

        with tempfile.TemporaryDirectory() as temporary:
            run_root = self._init_plan_run(Path(temporary), "finding-package")
            for state, evidence in (
                ("audited", self._write_audit_evidence(run_root)),
                ("ready", self._write_ready_evidence(run_root)),
            ):
                code, _, stderr = self._transition(run_root, state, evidence)
                self.assertEqual(0, code, stderr)
            generated = self._write_run_cases(run_root)
            code, _, stderr = self._transition(run_root, "generated", generated)
            self.assertEqual(0, code, stderr)
            code, _, stderr = self._transition(
                run_root, "linted", self._write_lint_evidence(run_root)
            )
            self.assertEqual(0, code, stderr)

            manifests = [
                yaml.safe_load(path.read_text(encoding="utf-8"))
                for path in sorted((run_root / "cases" / "manifests").glob("*.yaml"))
            ]
            reference_evidence: list[str] = []
            dut_evidence: list[str] = []
            comparison_evidence: list[str] = []
            profile_sha256 = json.loads(
                (run_root / "run.json").read_text(encoding="utf-8")
            )["metadata"]["execution_profile_sha256"]
            for index, case in enumerate(manifests):
                case_id = case["case_id"]
                sql_path = (run_root / case["sql_files"][0]).resolve()

                def endpoint(side: str, system_identifier: str) -> dict:
                    return {
                        "target_name": side,
                        "service": (
                            "pg18_reference"
                            if side == "reference"
                            else "storage_engine_dut"
                        ),
                        "database": "regression",
                        "server_version_num": 180004,
                        "system_identifier": system_identifier,
                        "server_address": "127.0.0.1",
                        "server_port": "5432" if side == "reference" else "6432",
                        "current_user": "regression_user",
                        "is_superuser": False,
                        "can_createdb": False,
                        "can_createrole": False,
                        "can_replication": False,
                        "can_bypassrls": False,
                        "dangerous_role_memberships": [],
                        "privileged_role_memberships": [],
                    }

                reference = ExecutionRecord(
                    target_name="reference",
                    sql_file=str(sql_path),
                    returncode=0,
                    stdout=f"value-{index}\n",
                    stderr="",
                    duration_seconds=0.1,
                    endpoint_identity=endpoint("reference", "111111"),
                    sql_sha256=case["sql_sha256"],
                    execution_profile_sha256=profile_sha256,
                )
                dut = ExecutionRecord(
                    target_name="dut",
                    sql_file=str(sql_path),
                    returncode=0,
                    stdout=(
                        "observable-difference\n"
                        if index == 0
                        else reference.stdout
                    ),
                    stderr="",
                    duration_seconds=0.1,
                    endpoint_identity=endpoint("dut", "222222"),
                    sql_sha256=case["sql_sha256"],
                    execution_profile_sha256=profile_sha256,
                )
                result = DifferentialExecutionResult(
                    reference=reference,
                    dut=dut,
                    comparison=compare_execution_records(reference, dut),
                    expected_outcome="success",
                    expected_sqlstate=None,
                    reference_oracle_valid=True,
                    reference_oracle_error=None,
                    execution_profile_sha256=profile_sha256,
                )
                result = attach_two_run_replay(result, result)
                write_differential_artifacts(run_root, case_id, result)
                reference_evidence.append(f"executions/reference/{case_id}.json")
                dut_evidence.append(f"executions/dut/{case_id}.json")
                comparison_evidence.append(f"comparisons/{case_id}.json")

            for state, evidence in (
                ("executed_reference", reference_evidence),
                ("executed_dut", dut_evidence),
                ("compared", comparison_evidence),
            ):
                code, _, stderr = self._transition(run_root, state, evidence)
                self.assertEqual(0, code, stderr)

            code, stdout, stderr = self._transition(
                run_root,
                "triaged",
                comparison_evidence,
            )
            self.assertEqual(2, code)
            self.assertEqual("", stdout)
            self.assertIn("without findings", stderr)

            failed_case = manifests[0]
            failed_case_id = failed_case["case_id"]

            def binding(relative: str) -> dict:
                return {
                    "path": relative,
                    "sha256": hashlib.sha256((run_root / relative).read_bytes()).hexdigest(),
                }

            finding_relative = f"findings/FINDING-{failed_case_id}.yaml"
            finding = {
                "schema_version": 1,
                "kind": "differential_finding",
                "finding_id": f"FINDING-{failed_case_id}",
                "test_point_id": "tp_create",
                "obligation_id": failed_case["obligation_id"],
                "case_id": failed_case_id,
                "summary": "DUT output differs from upstream PostgreSQL 18.4.",
                "artifacts": {
                    "sql": binding(failed_case["sql_files"][0]),
                    "reference_execution": binding(
                        f"executions/reference/{failed_case_id}.json"
                    ),
                    "dut_execution": binding(
                        f"executions/dut/{failed_case_id}.json"
                    ),
                    "comparison": binding(f"comparisons/{failed_case_id}.json"),
                },
            }
            (run_root / finding_relative).write_text(
                yaml.safe_dump(finding, sort_keys=False),
                encoding="utf-8",
            )
            code, _, stderr = self._transition(
                run_root,
                "triaged",
                comparison_evidence + [finding_relative],
            )
            self.assertEqual(0, code, stderr)

            package_entries = []
            package_evidence: list[str] = []
            mapping = build_regression_batch_mapping(
                "PGT",
                [case["obligation_id"] for case in manifests],
            )
            for case, style in zip(manifests, mapping.cases):
                case_id = case["case_id"]
                regression_sql = f"regression/sql/{style.sql_filename}"
                regression_expected = (
                    f"regression/expected/{Path(style.sql_filename).stem}.out"
                )
                sql_bytes = (run_root / case["sql_files"][0]).read_bytes()
                (run_root / regression_sql).write_bytes(sql_bytes)
                comparison = json.loads(
                    (run_root / f"comparisons/{case_id}.json").read_text(
                        encoding="utf-8"
                    )
                )
                expected_text = comparison["comparison"]["normalized_reference"]
                (run_root / regression_expected).write_text(
                    expected_text,
                    encoding="utf-8",
                )
                package_entries.append(
                    {
                        "case_id": case_id,
                        "obligation_id": case["obligation_id"],
                        "case_ordinal": style.case_ordinal,
                        "object_prefix": style.object_prefix,
                        "sql_file": regression_sql,
                        "sql_sha256": hashlib.sha256(sql_bytes).hexdigest(),
                        "expected_file": regression_expected,
                        "expected_sha256": hashlib.sha256(
                            expected_text.encode("utf-8")
                        ).hexdigest(),
                    }
                )
                package_evidence.extend((regression_sql, regression_expected))
            package_relative = "regression/packages/tp_create.json"
            (run_root / package_relative).parent.mkdir(parents=True, exist_ok=True)
            (run_root / package_relative).write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "kind": "regression_package",
                        "test_point_id": "tp_create",
                        "batch_prefix": mapping.batch_prefix,
                        "number_width": mapping.number_width,
                        "mapping_sha256": mapping.sha256,
                        "cases": package_entries,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            code, _, stderr = self._transition(
                run_root,
                "packaged",
                [package_relative] + package_evidence,
            )
            self.assertEqual(0, code, stderr)

            comparison_path = run_root / comparison_evidence[0]
            comparison_path.write_text("{}\n", encoding="utf-8")
            code, stdout, stderr = self._invoke(
                ["run", "status", str(run_root / "jobs" / "jobs.json")]
            )
            self.assertEqual(2, code)
            self.assertEqual("", stdout)
            self.assertIn("evidence was modified after transition", stderr)

    def test_run_init_rejects_plan_changes_during_atomic_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = root / "plan.yaml"
            _write_plan(plan)
            manifest, profile, applicability = _write_formal_support(root)
            self._formal_universe_counts = TINY_UNIVERSE_COUNTS
            from pg_case_factory import formal_run as formal_run_module

            real_prepare_run = formal_run_module.prepare_run

            def mutate_after_parse(*args, **kwargs):
                changed = yaml.safe_load(plan.read_text(encoding="utf-8"))
                changed["test_points"][0]["title"] = "changed after parsing"
                plan.write_text(
                    yaml.safe_dump(changed, sort_keys=False),
                    encoding="utf-8",
                )
                return real_prepare_run(*args, **kwargs)

            with mock.patch(
                "pg_case_factory.formal_run.prepare_run",
                side_effect=mutate_after_parse,
            ):
                code, stdout, stderr = self._invoke(
                    [
                        "run",
                        "init",
                        "--root",
                        str(root),
                        "--run-id",
                        "plan-snapshot",
                        "--plan",
                        str(plan),
                        "--manifest",
                        str(manifest),
                        "--execution-profile",
                        str(profile),
                        "--applicability-index",
                        str(applicability),
                        "--inventory-root",
                        str(root),
                    ]
                )

            self.assertEqual(2, code)
            self.assertEqual("", stdout)
            self.assertIn("changed while being snapshotted", stderr)
            self.assertFalse(
                (root / "artifacts" / "runs" / "plan-snapshot").exists()
            )

    def test_status_rejects_tampered_run_manifest_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_root = self._init_plan_run(Path(temporary), "run-json-tamper")
            run_manifest = run_root / "run.json"
            document = json.loads(run_manifest.read_text(encoding="utf-8"))
            document["layout"]["comparisons"] = "../outside"
            run_manifest.write_text(json.dumps(document) + "\n", encoding="utf-8")

            code, stdout, stderr = self._invoke(
                ["run", "status", str(run_root / "jobs" / "jobs.json")]
            )

            self.assertEqual(2, code)
            self.assertEqual("", stdout)
            self.assertIn("layout must exactly match", stderr)

    def test_run_init_rejects_unclassified_obligations_before_creating_a_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = root / "plan.yaml"
            _write_plan(plan)
            document = yaml.safe_load(plan.read_text(encoding="utf-8"))
            document["test_points"][0].pop("default_outcome")
            plan.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
            manifest, profile, applicability = _write_formal_support(root)
            self._formal_universe_counts = TINY_UNIVERSE_COUNTS

            code, stdout, stderr = self._invoke(
                [
                    "run",
                    "init",
                    "--root",
                    str(root),
                    "--run-id",
                    "incomplete-plan",
                    "--plan",
                    str(plan),
                    "--manifest",
                    str(manifest),
                    "--execution-profile",
                    str(profile),
                    "--applicability-index",
                    str(applicability),
                    "--inventory-root",
                    str(root),
                ]
            )

            self.assertEqual(2, code)
            self.assertEqual("", stdout)
            self.assertIn("coverage plan has no executable obligations", stderr)
            self.assertFalse((root / "artifacts" / "runs" / "incomplete-plan").exists())

    def test_reconcile_cases_reports_missing_and_complete_ledgers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = root / "plan.yaml"
            obligations_path = root / "obligations.json"
            cases = root / "cases"
            cases.mkdir()
            _write_plan(plan)
            code, _, stderr = self._invoke(
                [
                    "plan",
                    "expand",
                    str(plan),
                    "--inventory-root",
                    str(root),
                    "--require-complete",
                    "--output",
                    str(obligations_path),
                ]
            )
            self.assertEqual(0, code, stderr)
            obligations = json.loads(obligations_path.read_text(encoding="utf-8"))["obligations"]

            def write_case(index: int, obligation: dict) -> None:
                sql_relative = f"sql/case_{index:03d}.sql"
                sql_path = root / sql_relative
                sql_path.parent.mkdir(parents=True, exist_ok=True)
                sql_content = f"SELECT {index};\n"
                sql_path.write_text(sql_content, encoding="utf-8")
                document = {
                    "schema_version": 1,
                    "kind": "case_manifest",
                    "case_id": f"CASE-{index:03d}",
                    "test_point_id": obligation["test_point_id"],
                    "obligation_id": obligation["obligation_id"],
                    "outcome": obligation["outcome"],
                    "sql_files": [sql_relative],
                    "sql_sha256": hashlib.sha256(
                        sql_content.encode("utf-8")
                    ).hexdigest(),
                    "execution_profile": "basic_psql",
                    "comparison": {
                        "mode": "exact_text",
                        "oracle": "upstream-postgresql-18.4",
                        "require_identical": True,
                    },
                    "cleanup": {"required": True, "idempotent": True},
                    "metadata": {"assignments": obligation["assignments"]},
                }
                if obligation["outcome"] == "expected_failure":
                    document["comparison"]["expected_sqlstate"] = "0A000"
                (cases / f"case_{index:03d}.yaml").write_text(
                    yaml.safe_dump(document, sort_keys=False),
                    encoding="utf-8",
                )

            for index, obligation in enumerate(obligations[:-1], 1):
                write_case(index, obligation)
            arguments = [
                "plan",
                "reconcile-cases",
                str(plan),
                "--cases",
                str(cases),
                "--artifact-root",
                str(root),
                "--inventory-root",
                str(root),
            ]
            code, stdout, stderr = self._invoke(arguments)
            self.assertEqual(1, code, stderr)
            self.assertFalse(json.loads(stdout)["reconciliation"]["complete"])

            write_case(len(obligations), obligations[-1])
            code, stdout, stderr = self._invoke(arguments)
            self.assertEqual(0, code, stderr)
            self.assertTrue(json.loads(stdout)["reconciliation"]["complete"])

    def test_compare_returns_nonzero_for_observable_difference_and_writes_diff(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reference = root / "reference.out"
            dut = root / "dut.out"
            output = root / "comparison.json"
            reference.write_text("value\n1\n", encoding="utf-8")
            dut.write_text("value\n2\n", encoding="utf-8")

            code, stdout, stderr = self._invoke(
                [
                    "run",
                    "compare",
                    str(reference),
                    str(dut),
                    "--output",
                    str(output),
                ]
            )
            self.assertEqual(1, code, stderr)
            result = json.loads(stdout)
            self.assertFalse(result["identical"])
            self.assertIn("-1", result["unified_diff"])
            self.assertEqual(result, json.loads(output.read_text(encoding="utf-8")))

    def test_contract_errors_are_concise_and_use_exit_code_two(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            invalid = Path(temporary) / "invalid.yaml"
            invalid.write_text("kind: coverage_plan\n", encoding="utf-8")
            code, stdout, stderr = self._invoke(["plan", "validate", str(invalid)])
            self.assertEqual(2, code)
            self.assertEqual("", stdout)
            self.assertIn("schema_version", stderr)

    def test_invalid_normalization_regex_is_reported_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reference = root / "reference.out"
            dut = root / "dut.out"
            reference.write_text("same\n", encoding="utf-8")
            dut.write_text("same\n", encoding="utf-8")

            code, stdout, stderr = self._invoke(
                ["run", "compare", str(reference), str(dut), "--drop-line", "("]
            )

            self.assertEqual(2, code)
            self.assertEqual("", stdout)
            self.assertIn("error:", stderr)
            self.assertNotIn("Traceback", stderr)


if __name__ == "__main__":
    unittest.main()
