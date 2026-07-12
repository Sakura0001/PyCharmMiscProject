from __future__ import annotations

import json
import hashlib
import subprocess
import tempfile
import unittest
import os
from pathlib import Path
from unittest.mock import patch

from pg_case_factory.artifact_store import prepare_run
from pg_case_factory.differential import (
    DifferentialExecutionResult,
    EndpointIdentity,
    ExecutionRecord,
    NormalizationProfile,
    PsqlRunner,
    PsqlTarget,
    attach_two_run_replay,
    compare_execution_records,
    compare_outputs,
    execute_differential,
    normalize_output,
    parse_verbose_terminal_diagnostics,
    validate_basic_endpoint_identity,
    validate_comparable_endpoint_pair,
    validate_endpoint_identity,
    write_differential_artifacts,
)


def _session_stdout(
    user_stdout: str,
    *,
    system_identifier: str = "7654321",
    current_user: str = "regression_user",
) -> str:
    identity = {
        "server_version_num": 180004,
        "system_identifier": system_identifier,
        "server_address": "127.0.0.1",
        "server_port": "5432",
        "current_user": current_user,
        "is_superuser": False,
        "can_createdb": False,
        "can_createrole": False,
        "can_replication": False,
        "can_bypassrls": False,
        "pg_read_server_files": False,
        "pg_write_server_files": False,
        "pg_execute_server_program": False,
        "privileged_role_memberships": [],
    }
    return (
        "__PG_CASE_FACTORY_ENDPOINT_V2__"
        + json.dumps(identity, separators=(",", ":"))
        + "\n"
        + user_stdout
    )


class DifferentialTest(unittest.TestCase):
    def test_two_run_replay_compares_each_endpoint_without_normalization(self) -> None:
        reference = ExecutionRecord("reference", "/case.sql", 0, "same\n", "", 0.1)
        dut = ExecutionRecord("dut", "/case.sql", 0, "same\n", "", 0.1)
        first = DifferentialExecutionResult(
            reference,
            dut,
            compare_execution_records(reference, dut),
        )
        deterministic = attach_two_run_replay(first, first)
        self.assertTrue(deterministic.passed)
        self.assertTrue(deterministic.reference_determinism["deterministic"])

        changed_reference = ExecutionRecord(
            "reference", "/case.sql", 0, "changed\n", "", 0.2
        )
        replay = DifferentialExecutionResult(
            changed_reference,
            dut,
            compare_execution_records(changed_reference, dut),
        )
        nondeterministic = attach_two_run_replay(first, replay)
        self.assertFalse(nondeterministic.passed)
        self.assertEqual(
            ["stdout"], nondeterministic.reference_determinism["differences"]
        )

    def test_normalization_removes_configured_nondeterminism(self) -> None:
        profile = NormalizationProfile(
            drop_line_patterns=(r"^Time: ",),
            replacements=((r"OID=\d+", "OID=<normalized>"),),
            strip_trailing_whitespace=True,
        )
        raw = "OID=123  \r\nTime: 1.2 ms\r\nvalue   \r\n"

        self.assertEqual(normalize_output(raw, profile), "OID=<normalized>\nvalue\n")

    def test_compare_outputs_returns_stable_diff(self) -> None:
        result = compare_outputs("a\n", "b\n", NormalizationProfile())

        self.assertFalse(result.identical)
        self.assertIn("--- reference", result.unified_diff)
        self.assertIn("+b", result.unified_diff)
        self.assertNotEqual(result.reference_sha256, result.dut_sha256)

    def test_default_comparison_preserves_trailing_space_and_final_newline(self) -> None:
        self.assertFalse(compare_outputs("value \n", "value\n").identical)
        self.assertFalse(compare_outputs("value\n", "value").identical)
        normalized = compare_outputs(
            "value \n",
            "value\n",
            NormalizationProfile(strip_trailing_whitespace=True),
        )
        self.assertTrue(normalized.identical)
        self.assertTrue(normalized.normalization_profile["strip_trailing_whitespace"])

    def test_psql_runner_uses_service_without_persisting_password(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sql_path = Path(tmp) / "case.sql"
            sql_path.write_text("SELECT 1;\n", encoding="utf-8")
            runner = PsqlRunner(executable="/usr/bin/psql", timeout_seconds=10)
            target = PsqlTarget(name="reference", service="pg18_reference", database="regression")
            completed = subprocess.CompletedProcess([], 0, _session_stdout("one\n"), "")

            with patch.dict(
                os.environ,
                {
                    "PGHOST": "wrong-host",
                    "PGUSER": "wrong-user",
                    "PGPASSWORD": "local-secret",
                    "PGCLIENTENCODING": "LATIN1",
                },
            ):
                with patch("pg_case_factory.differential.subprocess.run", return_value=completed) as run:
                    record = runner.run(sql_path, target)

            command = run.call_args.args[0]
            environment = run.call_args.kwargs["env"]
            self.assertIn("-X", command)
            self.assertIn("regression", command)
            self.assertEqual("-", command[command.index("-f") + 1])
            wrapped_input = run.call_args.kwargs["input"]
            self.assertIn("pg_control_system", wrapped_input)
            self.assertTrue(wrapped_input.endswith("SELECT 1;\n"))
            self.assertEqual(environment["PGSERVICE"], "pg18_reference")
            self.assertEqual(environment["PGCLIENTENCODING"], "UTF8")
            self.assertNotIn("PGHOST", environment)
            self.assertNotIn("PGUSER", environment)
            self.assertNotIn("PGPASSWORD", environment)
            self.assertNotIn("PGPASSWORD", record.to_dict())
            self.assertEqual(record.stdout, "one\n")
            self.assertEqual("7654321", record.endpoint_identity["system_identifier"])

    def test_target_rejects_database_conninfo_that_could_persist_secrets(self) -> None:
        for database in (
            "postgresql://user:secret@localhost/db",
            "host=localhost password=secret dbname=db",
        ):
            with self.subTest(database=database), self.assertRaisesRegex(
                ValueError,
                "bare database name",
            ):
                PsqlTarget("reference", "pg18_reference", database)

    def test_endpoint_preflight_parses_version_and_system_identity_without_password(self) -> None:
        runner = PsqlRunner(executable="/usr/bin/psql", timeout_seconds=10)
        target = PsqlTarget("reference", "pg18_reference", "regression")
        completed = subprocess.CompletedProcess(
            [],
            0,
            (
                "180004\t7654321\t127.0.0.1\t5432\tregression_user\t"
                "f\tf\tf\tf\tf\tf\tf\tf\t[]\n"
            ),
            "",
        )
        with patch.dict(os.environ, {"PGPASSWORD": "must-not-leak"}):
            with patch(
                "pg_case_factory.differential.subprocess.run",
                return_value=completed,
            ) as run:
                identity = runner.inspect(target)

        self.assertEqual(180004, identity.server_version_num)
        self.assertEqual("7654321", identity.system_identifier)
        self.assertEqual("regression_user", identity.current_user)
        self.assertNotIn("PGPASSWORD", run.call_args.kwargs["env"])

    def test_basic_runner_rejects_privileged_endpoint_roles(self) -> None:
        privileged = EndpointIdentity(
            "reference",
            "pg18_reference",
            "regression",
            180004,
            "7654321",
            "127.0.0.1",
            "5432",
            "regression_user",
            dangerous_role_memberships=("pg_execute_server_program",),
        )

        # The durable PG18 identity contract is route-neutral.  Least
        # privilege is a separate policy owned by the basic runner.
        validate_endpoint_identity(privileged)
        with self.assertRaisesRegex(ValueError, "over-privileged"):
            validate_basic_endpoint_identity(privileged)

        for field_name in (
            "can_createdb",
            "can_createrole",
            "can_replication",
            "can_bypassrls",
        ):
            with self.subTest(field_name=field_name), self.assertRaisesRegex(
                ValueError, "over-privileged"
            ):
                validate_basic_endpoint_identity(
                    EndpointIdentity(
                        "reference",
                        "pg18_reference",
                        "regression",
                        180004,
                        "7654321",
                        "127.0.0.1",
                        "5432",
                        "regression_user",
                        **{field_name: True},
                    )
                )
        with self.assertRaisesRegex(ValueError, "over-privileged"):
            validate_basic_endpoint_identity(
                EndpointIdentity(
                    "reference",
                    "pg18_reference",
                    "regression",
                    180004,
                    "7654321",
                    "127.0.0.1",
                    "5432",
                    "regression_user",
                    privileged_role_memberships=("role_with_createdb",),
                )
            )

        with self.assertRaisesRegex(ValueError, "invalid system identifier"):
            validate_endpoint_identity(
                EndpointIdentity(
                    "reference",
                    "pg18_reference",
                    "regression",
                    180004,
                    123,  # type: ignore[arg-type]
                    "127.0.0.1",
                    "5432",
                    "regression_user",
                )
            )

    def test_external_differential_accepts_privileged_pg18_pair_and_binds_profile(self) -> None:
        digest = "a" * 64

        class PrivilegedRunner:
            def inspect(self, target):
                return EndpointIdentity(
                    target.name,
                    target.service,
                    target.database,
                    180004,
                    "111" if target.name == "reference" else "222",
                    "127.0.0.1",
                    "5432",
                    "regression_user",
                    is_superuser=True,
                    dangerous_role_memberships=("pg_execute_server_program",),
                )

            def run(self, sql_path, target, *, stop_on_error=True):
                return ExecutionRecord(
                    target.name,
                    str(sql_path),
                    0,
                    "same\n",
                    "",
                    0.1,
                )

        reference = PrivilegedRunner().inspect(
            PsqlTarget("reference", "reference", "regression")
        )
        dut = PrivilegedRunner().inspect(PsqlTarget("dut", "dut", "regression"))
        validate_comparable_endpoint_pair(reference, dut)
        with self.assertRaisesRegex(ValueError, "over-privileged"):
            validate_comparable_endpoint_pair(
                reference,
                dut,
                require_basic_privileges=True,
            )

        with self.assertRaisesRegex(ValueError, "over-privileged"):
            execute_differential(
                "/case.sql",
                PsqlTarget("reference", "reference", "regression"),
                PsqlTarget("dut", "dut", "regression"),
                runner=PrivilegedRunner(),
            )

        with tempfile.TemporaryDirectory() as tmp:
            sql_path = Path(tmp) / "copy-program.sql"
            sql_content = "COPY t FROM PROGRAM 'approved-helper';\n"
            sql_path.write_text(sql_content, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "system_identifier does not match"):
                execute_differential(
                    sql_path,
                    PsqlTarget("reference", "reference", "regression"),
                    PsqlTarget("dut", "dut", "regression"),
                    runner=PrivilegedRunner(),
                    execution_profile="external_isolated",
                    execution_profile_sha256=digest,
                    expected_sql_sha256=hashlib.sha256(
                        sql_content.encode("utf-8")
                    ).hexdigest(),
                    expected_reference_system_identifier="999",
                    expected_dut_system_identifier="222",
                    expected_current_user="regression_user",
                )
            result = execute_differential(
                sql_path,
                PsqlTarget("reference", "reference", "regression"),
                PsqlTarget("dut", "dut", "regression"),
                runner=PrivilegedRunner(),
                execution_profile="external_isolated",
                execution_profile_sha256=digest,
                expected_sql_sha256=hashlib.sha256(
                    sql_content.encode("utf-8")
                ).hexdigest(),
                expected_reference_system_identifier="111",
                expected_dut_system_identifier="222",
                expected_current_user="regression_user",
            )

        self.assertTrue(result.passed)
        self.assertEqual(digest, result.execution_profile_sha256)
        self.assertEqual(digest, result.reference.execution_profile_sha256)
        self.assertEqual(digest, result.dut.execution_profile_sha256)
        self.assertEqual(digest, result.to_dict()["execution_profile_sha256"])

    def test_differential_rejects_same_logical_or_physical_endpoint(self) -> None:
        with self.assertRaisesRegex(ValueError, "same service/database"):
            execute_differential(
                "/case.sql",
                PsqlTarget("reference", "same", "regression"),
                PsqlTarget("dut", "same", "regression"),
                runner=object(),
            )

        class SameClusterRunner:
            def inspect(self, target):
                return EndpointIdentity(
                    target.name,
                    target.service,
                    target.database,
                    180004,
                    "7654321",
                    "127.0.0.1",
                    "5432",
                    "regression_user",
                )

            def run(self, *args, **kwargs):  # pragma: no cover - preflight must stop first
                raise AssertionError("run must not be reached")

        with self.assertRaisesRegex(ValueError, "same PostgreSQL system identifier"):
            execute_differential(
                "/case.sql",
                PsqlTarget("reference", "reference", "regression"),
                PsqlTarget("dut", "dut", "regression"),
                runner=SameClusterRunner(),
            )

    def test_differential_rejects_non_18_4_endpoint(self) -> None:
        class WrongVersionRunner:
            def inspect(self, target):
                version = 180003 if target.name == "reference" else 180004
                return EndpointIdentity(
                    target.name,
                    target.service,
                    target.database,
                    version,
                    target.name,
                    "127.0.0.1",
                    "5432",
                    "regression_user",
                )

            def run(self, *args, **kwargs):  # pragma: no cover - preflight must stop first
                raise AssertionError("run must not be reached")

        with self.assertRaisesRegex(ValueError, "expected 180004"):
            execute_differential(
                "/case.sql",
                PsqlTarget("reference", "reference", "regression"),
                PsqlTarget("dut", "dut", "regression"),
                runner=WrongVersionRunner(),
            )

    def test_differential_requires_matching_database_and_current_user(self) -> None:
        class IdentityRunner:
            def __init__(self, *, dut_user="regression_user"):
                self.dut_user = dut_user

            def inspect(self, target):
                return EndpointIdentity(
                    target.name,
                    target.service,
                    target.database,
                    180004,
                    "111" if target.name == "reference" else "222",
                    "127.0.0.1",
                    "5432",
                    (
                        self.dut_user
                        if target.name == "dut"
                        else "regression_user"
                    ),
                )

            def run(self, *args, **kwargs):  # pragma: no cover - preflight rejects
                raise AssertionError("run must not be reached")

        with self.assertRaisesRegex(ValueError, "same database name"):
            execute_differential(
                "/case.sql",
                PsqlTarget("reference", "reference", "reference_db"),
                PsqlTarget("dut", "dut", "dut_db"),
                runner=IdentityRunner(),
            )
        with self.assertRaisesRegex(ValueError, "same current_user"):
            execute_differential(
                "/case.sql",
                PsqlTarget("reference", "reference", "regression"),
                PsqlTarget("dut", "dut", "regression"),
                runner=IdentityRunner(dut_user="different_user"),
            )

    def test_differential_binds_identity_to_the_actual_execution_session(self) -> None:
        reference_target = PsqlTarget("reference", "reference", "regression")
        dut_target = PsqlTarget("dut", "dut", "regression")

        class RoutedRunner:
            def inspect(self, target):
                return EndpointIdentity(
                    target.name,
                    target.service,
                    target.database,
                    180004,
                    "111" if target.name == "reference" else "222",
                    "127.0.0.1",
                    "5432",
                    "regression_user",
                )

            def run(self, sql_path, target, *, stop_on_error=True):
                preflight = self.inspect(target)
                if target.name == "reference":
                    preflight = EndpointIdentity(
                        target.name,
                        target.service,
                        target.database,
                        180004,
                        "333",
                        "127.0.0.1",
                        "5432",
                        "regression_user",
                    )
                return ExecutionRecord(
                    target.name,
                    str(sql_path),
                    0,
                    "same\n",
                    "",
                    0.1,
                    endpoint_identity=preflight.to_dict(),
                )

        with self.assertRaisesRegex(ValueError, "execution-session identity"):
            execute_differential(
                "/case.sql",
                reference_target,
                dut_target,
                runner=RoutedRunner(),
            )

    def test_differential_rejects_endpoint_postflight_drift(self) -> None:
        class DriftingRunner:
            def __init__(self):
                self.counts = {"reference": 0, "dut": 0}

            def inspect(self, target):
                self.counts[target.name] += 1
                system_identifier = "111" if target.name == "reference" else "222"
                if target.name == "reference" and self.counts[target.name] > 1:
                    system_identifier = "333"
                return EndpointIdentity(
                    target.name,
                    target.service,
                    target.database,
                    180004,
                    system_identifier,
                    "127.0.0.1",
                    "5432",
                    "regression_user",
                )

            def run(self, sql_path, target, *, stop_on_error=True):
                return ExecutionRecord(target.name, str(sql_path), 0, "same\n", "", 0.1)

        with self.assertRaisesRegex(ValueError, "changed between preflight and postflight"):
            execute_differential(
                "/case.sql",
                PsqlTarget("reference", "reference", "regression"),
                PsqlTarget("dut", "dut", "regression"),
                runner=DriftingRunner(),
            )

    def test_psql_runner_rejects_meta_commands_before_spawning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sql_path = Path(tmp) / "unsafe.sql"
            sql_path.write_text("SELECT 1; \\! env\n", encoding="utf-8")
            runner = PsqlRunner(executable="/usr/bin/psql")
            with patch("pg_case_factory.differential.subprocess.run") as run:
                with self.assertRaisesRegex(ValueError, "psql meta commands"):
                    runner.run(
                        sql_path,
                        PsqlTarget("reference", "pg18_reference", "regression"),
                    )
            run.assert_not_called()

    def test_differential_execution_compares_return_code_stdout_and_stderr(self) -> None:
        class FakeRunner:
            def __init__(self) -> None:
                self.records = [
                    ExecutionRecord("reference", "/case.sql", 0, "same\n", "", 0.1),
                    ExecutionRecord("dut", "/case.sql", 1, "same\n", "boom\n", 0.2),
                ]

            def run(self, sql_path, target, *, stop_on_error=False):
                return self.records.pop(0)

        result = execute_differential(
            "/case.sql",
            PsqlTarget("reference", "pg18_reference", "regression"),
            PsqlTarget("dut", "pg18_dut", "regression"),
            runner=FakeRunner(),
        )

        self.assertFalse(result.comparison.identical)
        self.assertIn("returncode: 0", result.comparison.normalized_reference)
        self.assertIn("returncode: 1", result.comparison.normalized_dut)
        self.assertIn("boom", result.comparison.unified_diff)

    def test_reference_outcome_is_an_oracle_not_merely_equal_output(self) -> None:
        class PairRunner:
            def __init__(self, records):
                self.records = list(records)

            def run(self, sql_path, target, *, stop_on_error=True):
                return self.records.pop(0)

        same_error = (
            ExecutionRecord("reference", "/case.sql", 1, "", "ERROR:  23505: duplicate\n", 0.1),
            ExecutionRecord("dut", "/case.sql", 1, "", "ERROR:  23505: duplicate\n", 0.1),
        )
        success_case = execute_differential(
            "/case.sql",
            PsqlTarget("reference", "pg18_reference", "regression"),
            PsqlTarget("dut", "pg18_dut", "regression"),
            runner=PairRunner(same_error),
            expected_outcome="success",
        )
        self.assertTrue(success_case.comparison.identical)
        self.assertFalse(success_case.passed)

        expected_failure = execute_differential(
            "/case.sql",
            PsqlTarget("reference", "pg18_reference", "regression"),
            PsqlTarget("dut", "pg18_dut", "regression"),
            runner=PairRunner(same_error),
            expected_outcome="expected_failure",
            expected_sqlstate="23505",
        )
        self.assertTrue(expected_failure.passed)

        same_success = (
            ExecutionRecord("reference", "/case.sql", 0, "ok\n", "", 0.1),
            ExecutionRecord("dut", "/case.sql", 0, "ok\n", "", 0.1),
        )
        wrong_failure = execute_differential(
            "/case.sql",
            PsqlTarget("reference", "pg18_reference", "regression"),
            PsqlTarget("dut", "pg18_dut", "regression"),
            runner=PairRunner(same_success),
            expected_outcome="expected_failure",
            expected_sqlstate="23505",
        )
        self.assertFalse(wrong_failure.passed)

    def test_expected_failure_oracle_ignores_notice_sqlstate_injection(self) -> None:
        class PairRunner:
            def __init__(self) -> None:
                stderr = (
                    "psql:<stdin>:1: NOTICE:  23505: injected expected code\n"
                    "psql:<stdin>:2: ERROR:  22012: division by zero\n"
                    "LOCATION:  int4div, int.c:869\n"
                )
                self.records = [
                    ExecutionRecord("reference", "/case.sql", 3, "", stderr, 0.1),
                    ExecutionRecord("dut", "/case.sql", 3, "", stderr, 0.1),
                ]

            def run(self, sql_path, target, *, stop_on_error=True):
                return self.records.pop(0)

        result = execute_differential(
            "/case.sql",
            PsqlTarget("reference", "pg18_reference", "regression"),
            PsqlTarget("dut", "pg18_dut", "regression"),
            runner=PairRunner(),
            expected_outcome="expected_failure",
            expected_sqlstate="23505",
        )

        self.assertTrue(result.comparison.identical)
        self.assertFalse(result.reference_oracle_valid)
        self.assertFalse(result.passed)
        self.assertIn("22012, expected 23505", result.reference_oracle_error)

    def test_verbose_terminal_diagnostic_parser_rejects_nonterminal_severities(self) -> None:
        stderr = (
            "psql:<stdin>:1: WARNING:  23505: warning injection\n"
            "psql:<stdin>:2: FATAL:  57P01: terminating connection\n"
        )

        self.assertEqual(
            (("FATAL", "57P01"),),
            parse_verbose_terminal_diagnostics(stderr),
        )

    def test_builtin_runner_interface_uses_one_immutable_sql_snapshot_for_both_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sql_path = Path(tmp) / "case.sql"
            sql_path.write_bytes(b"SELECT 1;\r\n")

            class SnapshotRunner:
                def __init__(self):
                    self.contents = []

                def run_content(self, content, label, target, *, stop_on_error=True):
                    self.contents.append(content)
                    if len(self.contents) == 1:
                        sql_path.write_bytes(b"SELECT 2;\n")
                    return ExecutionRecord(
                        target.name,
                        str(label),
                        0,
                        "same\n",
                        "",
                        0.1,
                    )

            runner = SnapshotRunner()
            result = execute_differential(
                sql_path,
                PsqlTarget("reference", "pg18_reference", "regression"),
                PsqlTarget("dut", "pg18_dut", "regression"),
                runner=runner,
            )

            self.assertEqual(["SELECT 1;\r\n", "SELECT 1;\r\n"], runner.contents)
            self.assertEqual(result.reference.sql_sha256, result.dut.sql_sha256)
            self.assertEqual(
                hashlib.sha256(b"SELECT 1;\r\n").hexdigest(),
                result.reference.sql_sha256,
            )

    def test_expected_sql_hash_is_checked_after_snapshot_before_any_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sql_path = Path(tmp) / "case.sql"
            sql_path.write_text("SELECT 2;\n", encoding="utf-8")

            class SnapshotRunner:
                def __init__(self):
                    self.calls = 0

                def run_content(self, content, label, target, *, stop_on_error=True):
                    self.calls += 1
                    raise AssertionError("hash mismatch must stop before execution")

            runner = SnapshotRunner()
            with self.assertRaisesRegex(ValueError, "immutable SQL snapshot SHA256 mismatch"):
                execute_differential(
                    sql_path,
                    PsqlTarget("reference", "pg18_reference", "regression"),
                    PsqlTarget("dut", "pg18_dut", "regression"),
                    runner=runner,
                    expected_sql_sha256=hashlib.sha256(
                        b"SELECT 1;\n"
                    ).hexdigest(),
                )
            self.assertEqual(0, runner.calls)

    def test_normalization_cannot_erase_return_code_or_stream_boundaries(self) -> None:
        reference = ExecutionRecord("reference", "/case.sql", 0, "same\n", "", 0.1)
        dut = ExecutionRecord("dut", "/case.sql", 1, "same\n", "", 0.1)
        profile = NormalizationProfile(drop_line_patterns=(r"^returncode:.*$",))

        result = compare_execution_records(reference, dut, profile)

        self.assertFalse(result.identical)
        self.assertIn("returncode: 0", result.normalized_reference)
        self.assertIn("returncode: 1", result.normalized_dut)

    def test_execution_comparison_preserves_final_newlines_and_stream_boundaries(self) -> None:
        no_newline = ExecutionRecord("reference", "/case.sql", 0, "value", "", 0.1)
        newline = ExecutionRecord("dut", "/case.sql", 0, "value\n", "", 0.1)
        self.assertFalse(compare_execution_records(no_newline, newline).identical)

        reference = ExecutionRecord(
            "reference",
            "/case.sql",
            0,
            "x\n--- stderr ---\ny\n",
            "z\n",
            0.1,
        )
        dut = ExecutionRecord(
            "dut",
            "/case.sql",
            0,
            "x\n",
            "y\n--- stderr ---\nz\n",
            0.1,
        )
        self.assertFalse(compare_execution_records(reference, dut).identical)

    def test_differential_artifacts_are_scoped_and_case_ids_cannot_traverse(self) -> None:
        reference = ExecutionRecord("reference", "/case.sql", 0, "one\n", "", 0.1)
        dut = ExecutionRecord("dut", "/case.sql", 0, "one\n", "", 0.2)

        class FakeRunner:
            def __init__(self):
                self.records = [reference, dut]

            def run(self, sql_path, target, *, stop_on_error=False):
                return self.records.pop(0)

        result = execute_differential(
            "/case.sql",
            PsqlTarget("reference", "pg18_reference", "regression"),
            PsqlTarget("dut", "pg18_dut", "regression"),
            runner=FakeRunner(),
        )
        with tempfile.TemporaryDirectory() as tmp:
            run_root = prepare_run(Path(tmp), "differential-artifacts")["run_root"]
            paths = write_differential_artifacts(run_root, "case-001", result)

            self.assertTrue(paths["comparison"].is_file())
            self.assertEqual("one\n", paths["reference_stdout"].read_text(encoding="utf-8"))
            with self.assertRaises(FileExistsError):
                write_differential_artifacts(run_root, "case-001", result)
            write_differential_artifacts(run_root, "case-001", result, overwrite=True)
            with self.assertRaisesRegex(ValueError, "case_id"):
                write_differential_artifacts(run_root, "../escape", result)

    def test_artifact_writer_rejects_result_bound_to_another_run_profile(self) -> None:
        reference = ExecutionRecord(
            "reference",
            "/case.sql",
            0,
            "one\n",
            "",
            0.1,
            execution_profile_sha256="a" * 64,
        )
        dut = ExecutionRecord(
            "dut",
            "/case.sql",
            0,
            "one\n",
            "",
            0.1,
            execution_profile_sha256="a" * 64,
        )
        result = execute_differential(
            "/case.sql",
            PsqlTarget("reference", "pg18_reference", "regression"),
            PsqlTarget("dut", "pg18_dut", "regression"),
            runner=type(
                "BoundRunner",
                (),
                {
                    "records": [reference, dut],
                    "run": lambda self, sql_path, target, stop_on_error=True: self.records.pop(0),
                },
            )(),
            execution_profile_sha256="a" * 64,
        )
        with tempfile.TemporaryDirectory() as tmp:
            run_root = prepare_run(Path(tmp), "unprofiled-run")["run_root"]
            with self.assertRaisesRegex(ValueError, "does not match the run"):
                write_differential_artifacts(run_root, "case-001", result)

    def test_differential_artifacts_reject_an_intermediate_symlink_escape(self) -> None:
        reference = ExecutionRecord("reference", "/case.sql", 0, "one\n", "", 0.1)
        dut = ExecutionRecord("dut", "/case.sql", 0, "one\n", "", 0.1)

        class FakeRunner:
            def __init__(self):
                self.records = [reference, dut]

            def run(self, sql_path, target, *, stop_on_error=False):
                return self.records.pop(0)

        result = execute_differential(
            "/case.sql",
            PsqlTarget("reference", "pg18_reference", "regression"),
            PsqlTarget("dut", "pg18_dut", "regression"),
            runner=FakeRunner(),
        )
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            run_root = prepare_run(Path(tmp), "symlink-artifacts")["run_root"]
            reference_root = run_root / "executions" / "reference"
            reference_root.rmdir()
            reference_root.symlink_to(
                Path(outside),
                target_is_directory=True,
            )

            with self.assertRaisesRegex(ValueError, "symbolic link"):
                write_differential_artifacts(run_root, "case-001", result)
            self.assertEqual([], list(Path(outside).iterdir()))

    def test_partial_differential_artifacts_are_recoverable_before_completion_marker(self) -> None:
        result = execute_differential(
            "/case.sql",
            PsqlTarget("reference", "pg18_reference", "regression"),
            PsqlTarget("dut", "pg18_dut", "regression"),
            runner=type(
                "PairRunner",
                (),
                {
                    "records": [
                        ExecutionRecord("reference", "/case.sql", 0, "one\n", "", 0.1),
                        ExecutionRecord("dut", "/case.sql", 0, "one\n", "", 0.1),
                    ],
                    "run": lambda self, sql_path, target, stop_on_error=True: self.records.pop(0),
                },
            )(),
        )
        with tempfile.TemporaryDirectory() as tmp:
            run_root = prepare_run(Path(tmp), "partial-artifacts")["run_root"]
            partial = run_root / "executions" / "reference" / "case-001.json"
            partial.write_text('{"partial": true}\n', encoding="utf-8")

            paths = write_differential_artifacts(run_root, "case-001", result)

            self.assertTrue(paths["comparison"].is_file())
            self.assertNotIn("partial", paths["reference_record"].read_text(encoding="utf-8"))
            self.assertEqual([], list((run_root / "comparisons" / ".staging").iterdir()))

    def test_differential_artifacts_reject_counterfeit_run_json(self) -> None:
        reference = ExecutionRecord("reference", "/case.sql", 0, "one\n", "", 0.1)
        result = type(
            "Result",
            (),
            {
                "reference": reference,
                "dut": reference,
                "comparison": compare_execution_records(reference, reference),
                "to_dict": lambda self: {},
            },
        )()
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp) / "fake-run"
            run_root.mkdir()
            (run_root / "run.json").write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid schema"):
                write_differential_artifacts(run_root, "case-001", result)


if __name__ == "__main__":
    unittest.main()
