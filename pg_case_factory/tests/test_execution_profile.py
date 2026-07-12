from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

from pg_case_factory.cli import main
from pg_case_factory.contracts import (
    ContractValidationError,
    canonical_execution_profile_yaml,
    execution_profile_sha256,
    load_execution_profile,
)
from pg_case_factory.artifact_store import load_run_execution_profile, prepare_run


def _profile_document() -> dict:
    return {
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
    }


class ExecutionProfileTest(unittest.TestCase):
    def _invoke(self, arguments: list[str]) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        # Most tests in this module exercise profile parsing and differential
        # settings in isolation.  Their run is deliberately a low-level
        # component fixture; formal snapshot/gate integration has dedicated
        # coverage in test_formal_run.py.
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr), mock.patch(
            "pg_case_factory.cli.validate_formal_run", return_value={}
        ), mock.patch("pg_case_factory.cli._validate_differential_job_gate"):
            code = main(arguments)
        return code, stdout.getvalue(), stderr.getvalue()

    def _write_profile(self, root: Path, document: dict | None = None) -> Path:
        path = root / "execution-profile.yaml"
        path.write_text(
            yaml.safe_dump(document or _profile_document(), sort_keys=False),
            encoding="utf-8",
        )
        return path

    def _init_run(
        self,
        root: Path,
        run_id: str,
        *,
        profile: Path | None,
    ) -> Path:
        digest = None
        if profile is not None:
            parsed = load_execution_profile(profile)
            digest = execution_profile_sha256(parsed)
        paths = prepare_run(
            root,
            run_id,
            metadata={"execution_profile_sha256": digest},
        )
        if profile is not None:
            (paths["inputs"] / "execution_profile.yaml").write_text(
                canonical_execution_profile_yaml(parsed), encoding="utf-8"
            )
        return paths["run_root"]

    def _write_case(self, run_root: Path, case_id: str = "CASE-001") -> tuple[Path, Path]:
        sql_relative = f"cases/sql/{case_id}.sql"
        sql_path = run_root / sql_relative
        sql_content = "SELECT 1;\n"
        sql_path.write_text(sql_content, encoding="utf-8")
        manifest_path = run_root / "cases" / "manifests" / f"{case_id}.yaml"
        manifest_path.write_text(
            yaml.safe_dump(
                {
                    "schema_version": 1,
                    "kind": "case_manifest",
                    "case_id": case_id,
                    "test_point_id": "TP-001",
                    "obligation_id": "obl-tp-001-0123456789ab",
                    "outcome": "success",
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
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        return sql_path, manifest_path

    def _successful_runner_patches(self, observations: list[tuple]):
        from pg_case_factory.differential import EndpointIdentity, ExecutionRecord

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
                server_port="5432" if target.name == "reference" else "5433",
                current_user="regression_user",
            )

        def inspect(runner, target):
            observations.append(
                ("inspect", runner.executable, runner.timeout_seconds, target)
            )
            return identity(target)

        def run_content(runner, content, label, target, *, stop_on_error=True):
            observations.append(
                (
                    "run",
                    runner.executable,
                    runner.timeout_seconds,
                    target,
                    stop_on_error,
                )
            )
            return ExecutionRecord(
                target_name=target.name,
                sql_file=str(label),
                returncode=0,
                stdout="1\n",
                stderr="",
                duration_seconds=0.1,
                endpoint_identity=identity(target).to_dict(),
            )

        return (
            mock.patch("pg_case_factory.differential.PsqlRunner.inspect", new=inspect),
            mock.patch(
                "pg_case_factory.differential.PsqlRunner.run_content",
                new=run_content,
            ),
        )

    def test_strict_contract_has_one_canonical_form_and_digest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = self._write_profile(Path(temporary))
            profile = load_execution_profile(path)

        self.assertEqual("pg18_reference", profile.reference.service)
        self.assertEqual("regression", profile.dut.database)
        self.assertEqual(64, len(execution_profile_sha256(profile)))
        self.assertEqual(
            _profile_document(),
            yaml.safe_load(canonical_execution_profile_yaml(profile)),
        )
        repository_template = (
            Path(__file__).resolve().parents[1]
            / "skills"
            / "pg-sql-generation"
            / "assets"
            / "templates"
            / "execution_profile_template.yaml"
        )
        template_profile = load_execution_profile(repository_template)
        self.assertEqual("postgresql-18.4", template_profile.compatibility_target)
        self.assertEqual(
            template_profile.reference.database,
            template_profile.dut.database,
        )

    def test_contract_rejects_nonformal_or_credential_bearing_profiles(self) -> None:
        mutations = []

        document = copy.deepcopy(_profile_document())
        document["compatibility_target"] = "postgresql-18.3"
        mutations.append((document, "postgresql-18.4"))

        document = copy.deepcopy(_profile_document())
        document["reference"]["password"] = "must-not-enter-artifacts"
        mutations.append((document, "unexpected password"))

        document = copy.deepcopy(_profile_document())
        document["dut"]["database"] = "other_database"
        mutations.append((document, "database names must be identical"))

        document = copy.deepcopy(_profile_document())
        document["dut"]["service"] = document["reference"]["service"]
        mutations.append((document, "different libpq services"))

        document = copy.deepcopy(_profile_document())
        document["reference"]["expected_system_identifier"] = "0"
        mutations.append((document, "positive decimal string"))

        document = copy.deepcopy(_profile_document())
        document["dut"]["expected_system_identifier"] = document["reference"][
            "expected_system_identifier"
        ]
        mutations.append((document, "system identifiers must be different"))

        document = copy.deepcopy(_profile_document())
        document["dut"]["expected_current_user"] = "different_user"
        mutations.append((document, "expected current_user must be identical"))

        document = copy.deepcopy(_profile_document())
        document["reference"]["expected_current_user"] = "bad\nuser"
        mutations.append((document, "without control characters"))

        document = copy.deepcopy(_profile_document())
        document["runner"]["stop_on_error"] = False
        mutations.append((document, "stop_on_error must be true"))

        document = copy.deepcopy(_profile_document())
        document["comparison"]["normalization"]["drop_line_patterns"] = ["NOTICE"]
        mutations.append((document, "drop_line_patterns must be empty"))

        document = copy.deepcopy(_profile_document())
        document["security"]["credential_source"] = "inline-environment"
        mutations.append((document, "external-libpq-service"))

        document = copy.deepcopy(_profile_document())
        document["security"]["persist_credentials"] = True
        mutations.append((document, "persist_credentials must be false"))

        for index, (invalid, message) in enumerate(mutations):
            with self.subTest(index=index, message=message), tempfile.TemporaryDirectory() as temporary:
                path = self._write_profile(Path(temporary), invalid)
                with self.assertRaisesRegex(ContractValidationError, message):
                    load_execution_profile(path)

    def test_low_level_profile_snapshot_loader_requires_the_same_digest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profile_path = self._write_profile(root)
            profile = load_execution_profile(profile_path)
            run_root = self._init_run(root, "profile-resume", profile=profile_path)
            snapshot = run_root / "inputs" / "execution_profile.yaml"
            run_manifest = json.loads(
                (run_root / "run.json").read_text(encoding="utf-8")
            )

            self.assertEqual(
                canonical_execution_profile_yaml(profile),
                snapshot.read_text(encoding="utf-8"),
            )
            self.assertEqual(
                execution_profile_sha256(profile),
                run_manifest["metadata"]["execution_profile_sha256"],
            )

            changed = _profile_document()
            changed["runner"]["timeout_seconds"] = 48
            snapshot.write_text(
                yaml.safe_dump(changed, sort_keys=False), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "digest differs"):
                load_run_execution_profile(run_root)

    def test_run_init_rejects_unresolved_feature_questions_before_creating_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "feature.md"
            source.write_text("# feature\n", encoding="utf-8")
            manifest = root / "feature.yaml"
            manifest.write_text(
                yaml.safe_dump(
                    {
                        "schema_version": 1,
                        "kind": "feature_manifest",
                        "feature_id": "unresolved-feature",
                        "title": "Unresolved feature",
                        "compatibility_target": "postgresql-18.4",
                        "source": {
                            "path": "feature.md",
                            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                        },
                        "requirements": [
                            {
                                "id": "REQ-001",
                                "description": "Preserve visible behavior.",
                                "source": {"section": "1"},
                            }
                        ],
                        "metadata": {
                            "unresolved_questions": ["Which fixture is approved?"]
                        },
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            code, stdout, stderr = self._invoke(
                [
                    "run",
                    "init",
                    "--root",
                    str(root),
                    "--run-id",
                    "must-not-exist",
                    "--manifest",
                    str(manifest),
                    "--plan",
                    str(root / "unused-plan.yaml"),
                    "--execution-profile",
                    str(root / "unused-profile.yaml"),
                    "--applicability-index",
                    str(root / "unused-applicability.yaml"),
                ]
            )

            self.assertEqual(2, code)
            self.assertEqual("", stdout)
            self.assertIn("has unresolved_questions", stderr)
            self.assertFalse(
                (root / "artifacts" / "runs" / "must-not-exist").exists()
            )

            document = yaml.safe_load(manifest.read_text(encoding="utf-8"))
            document["metadata"]["unresolved_questions"] = "not-a-list"
            manifest.write_text(
                yaml.safe_dump(document, sort_keys=False),
                encoding="utf-8",
            )
            code, stdout, stderr = self._invoke(
                [
                    "run",
                    "init",
                    "--root",
                    str(root),
                    "--run-id",
                    "invalid-question-shape",
                    "--manifest",
                    str(manifest),
                    "--plan",
                    str(root / "unused-plan.yaml"),
                    "--execution-profile",
                    str(root / "unused-profile.yaml"),
                    "--applicability-index",
                    str(root / "unused-applicability.yaml"),
                ]
            )
            self.assertEqual(2, code)
            self.assertEqual("", stdout)
            self.assertIn("must be a list", stderr)
            self.assertFalse(
                (root / "artifacts" / "runs" / "invalid-question-shape").exists()
            )

            document.pop("metadata")
            manifest.write_text(
                yaml.safe_dump(document, sort_keys=False),
                encoding="utf-8",
            )
            code, stdout, stderr = self._invoke(
                [
                    "run",
                    "init",
                    "--root",
                    str(root),
                    "--run-id",
                    "missing-question-decision",
                    "--manifest",
                    str(manifest),
                    "--plan",
                    str(root / "unused-plan.yaml"),
                    "--execution-profile",
                    str(root / "unused-profile.yaml"),
                    "--applicability-index",
                    str(root / "unused-applicability.yaml"),
                ]
            )
            self.assertEqual(2, code)
            self.assertEqual("", stdout)
            self.assertIn("must be explicitly declared", stderr)
            self.assertFalse(
                (root / "artifacts" / "runs" / "missing-question-decision").exists()
            )

    def test_formal_differential_uses_run_profile_and_rejects_conflicting_flags(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_root = self._init_run(
                root,
                "profile-differential",
                profile=self._write_profile(root),
            )
            sql_path, manifest_path = self._write_case(run_root)
            observations: list[tuple] = []
            inspect_patch, run_patch = self._successful_runner_patches(observations)
            with inspect_patch, run_patch:
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

            self.assertEqual(0, code, stderr)
            self.assertEqual(
                "run_execution_profile",
                json.loads(stdout)["configuration_source"],
            )
            digest = execution_profile_sha256(load_execution_profile(
                run_root / "inputs" / "execution_profile.yaml"
            ))
            self.assertEqual(digest, json.loads(stdout)["execution_profile_sha256"])
            for relative in (
                "executions/reference/CASE-001.json",
                "executions/dut/CASE-001.json",
                "comparisons/CASE-001.json",
            ):
                artifact = json.loads((run_root / relative).read_text(encoding="utf-8"))
                self.assertEqual(digest, artifact["execution_profile_sha256"])
            run_observations = [item for item in observations if item[0] == "run"]
            self.assertEqual(4, len(run_observations))
            self.assertEqual(
                {"pg18_reference", "storage_engine_dut"},
                {item[3].service for item in run_observations},
            )
            self.assertEqual(
                {"pg18_reference": 2, "storage_engine_dut": 2},
                {
                    service: sum(
                        item[3].service == service for item in run_observations
                    )
                    for service in ("pg18_reference", "storage_engine_dut")
                },
            )
            self.assertTrue(
                all(
                    item[1:3] == ("/opt/pg18/bin/psql", 47) and item[4] is True
                    for item in run_observations
                )
            )

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
                    "--timeout",
                    "48",
                ]
            )
            self.assertEqual(2, code)
            self.assertEqual("", stdout)
            self.assertIn("conflict", stderr)
            self.assertIn("--timeout", stderr)

    def test_legacy_direct_flags_still_work_without_a_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_root = self._init_run(root, "legacy-flags", profile=None)
            sql_path, manifest_path = self._write_case(run_root)
            observations: list[tuple] = []
            inspect_patch, run_patch = self._successful_runner_patches(observations)
            with inspect_patch, run_patch:
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
                        "legacy_reference",
                        "--reference-database",
                        "regression",
                        "--dut-service",
                        "legacy_dut",
                        "--dut-database",
                        "regression",
                        "--psql",
                        "legacy-psql",
                        "--timeout",
                        "61",
                    ]
                )

            self.assertEqual(0, code, stderr)
            self.assertEqual("direct_flags", json.loads(stdout)["configuration_source"])
            self.assertIsNone(json.loads(stdout)["execution_profile_sha256"])
            for relative in (
                "executions/reference/CASE-001.json",
                "executions/dut/CASE-001.json",
                "comparisons/CASE-001.json",
            ):
                artifact = json.loads((run_root / relative).read_text(encoding="utf-8"))
                self.assertIsNone(artifact["execution_profile_sha256"])
            self.assertTrue(
                all(
                    item[1:3] == ("legacy-psql", 61)
                    for item in observations
                )
            )

    def test_formal_differential_rechecks_profile_settings_inside_case_lock(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_root = self._init_run(
                root,
                "profile-lock-recheck",
                profile=self._write_profile(root),
            )
            sql_path, manifest_path = self._write_case(run_root)
            stable = {
                "reference_service": "pg18_reference",
                "reference_database": "regression",
                "dut_service": "storage_engine_dut",
                "dut_database": "regression",
                "psql": "/opt/pg18/bin/psql",
                "timeout": 47,
                "execution_profile_sha256": "a" * 64,
                "source": "run_execution_profile",
            }
            changed = {**stable, "execution_profile_sha256": "b" * 64}

            with mock.patch(
                "pg_case_factory.cli._resolve_formal_differential_settings",
                side_effect=(stable, changed),
            ), mock.patch("pg_case_factory.differential.PsqlRunner.inspect") as inspect:
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

            self.assertEqual(2, code)
            self.assertEqual("", stdout)
            self.assertIn("changed before differential execution", stderr)
            inspect.assert_not_called()
            self.assertFalse((run_root / "comparisons" / "CASE-001.json").exists())

    def test_formal_differential_rechecks_case_manifest_inside_case_lock(self) -> None:
        from pg_case_factory import cli as cli_module

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_root = self._init_run(
                root,
                "case-lock-recheck",
                profile=self._write_profile(root),
            )
            sql_path, manifest_path = self._write_case(run_root)
            real_resolver = cli_module._resolve_formal_case_inputs
            calls = 0

            def replace_after_first_read(*args, **kwargs):
                nonlocal calls
                resolved = real_resolver(*args, **kwargs)
                calls += 1
                if calls == 1:
                    document = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
                    document["metadata"] = {"replaced_after_initial_read": True}
                    manifest_path.write_text(
                        yaml.safe_dump(document, sort_keys=False),
                        encoding="utf-8",
                    )
                return resolved

            with mock.patch(
                "pg_case_factory.cli._resolve_formal_case_inputs",
                side_effect=replace_after_first_read,
            ), mock.patch("pg_case_factory.differential.PsqlRunner.inspect") as inspect:
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

            self.assertEqual(2, code)
            self.assertEqual("", stdout)
            self.assertIn("case manifest/SQL binding changed", stderr)
            inspect.assert_not_called()

    def test_formal_differential_rejects_profile_endpoint_anchor_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            document = _profile_document()
            document["reference"]["expected_system_identifier"] = "333333"
            run_root = self._init_run(
                root,
                "profile-anchor-drift",
                profile=self._write_profile(root, document),
            )
            sql_path, manifest_path = self._write_case(run_root)
            observations: list[tuple] = []
            inspect_patch, run_patch = self._successful_runner_patches(observations)
            with inspect_patch, run_patch:
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

            self.assertEqual(2, code)
            self.assertEqual("", stdout)
            self.assertIn("system_identifier does not match", stderr)
            self.assertEqual([], [item for item in observations if item[0] == "run"])

    def test_run_profile_symlink_escape_is_rejected_before_connection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary, tempfile.TemporaryDirectory() as outside:
            root = Path(temporary)
            source_profile = self._write_profile(root)
            run_root = self._init_run(root, "profile-escape", profile=source_profile)
            sql_path, manifest_path = self._write_case(run_root)
            snapshot = run_root / "inputs" / "execution_profile.yaml"
            snapshot.unlink()
            outside_profile = self._write_profile(Path(outside))
            snapshot.symlink_to(outside_profile)

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
                    ]
                )

            self.assertEqual(2, code)
            self.assertEqual("", stdout)
            self.assertIn("non-symbolic-link", stderr)
            run.assert_not_called()

    def test_run_profile_rejects_formatting_and_semantic_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_profile = self._write_profile(root)
            run_root = self._init_run(root, "profile-tamper", profile=source_profile)
            snapshot = run_root / "inputs" / "execution_profile.yaml"
            canonical = snapshot.read_text(encoding="utf-8")

            snapshot.write_text("# unauthorized edit\n" + canonical, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "canonical immutable snapshot"):
                load_run_execution_profile(run_root)

            changed = yaml.safe_load(canonical)
            changed["runner"]["timeout_seconds"] = 48
            snapshot.write_text(
                yaml.safe_dump(changed, sort_keys=False),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "digest differs"):
                load_run_execution_profile(run_root)

    def test_manually_copied_unbound_profile_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_root = self._init_run(root, "unbound-profile", profile=None)
            (run_root / "inputs" / "execution_profile.yaml").write_text(
                yaml.safe_dump(_profile_document(), sort_keys=False),
                encoding="utf-8",
            )
            sql_path, manifest_path = self._write_case(run_root)

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
                    "legacy_reference",
                    "--reference-database",
                    "regression",
                    "--dut-service",
                    "legacy_dut",
                    "--dut-database",
                    "regression",
                ]
            )

            self.assertEqual(2, code)
            self.assertEqual("", stdout)
            self.assertIn("unbound inputs/execution_profile.yaml", stderr)


if __name__ == "__main__":
    unittest.main()
