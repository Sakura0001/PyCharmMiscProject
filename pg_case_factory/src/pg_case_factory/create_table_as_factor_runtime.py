"""Runtime case-set combiner for CREATE TABLE AS factor regress.

Combines the frozen baseline (86 cases) and bounded extension cases into a
single ordered case set ready for two-run PG18.4 differential execution.

NOT executed in the no-DB phase: the no-DB ledger only emits and validates
SQL programs.  Runtime execution is invoked from a later phase that has a
live PG18.4 instance, so this module is deliberately side-effect-free and
constructs its inputs from the frozen plans.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Any, Mapping

from .create_table_as_factor_extension import (
    build_create_table_as_factor_extension_plan,
)
from .create_table_as_factor_loop import (
    build_create_table_as_factor_loop_plan,
)

PG18_BIN = "/usr/lib/postgresql/18/bin"
PG18_SOCKET = "/var/run/postgresql"
PG18_PORT = "5180"


@dataclass(frozen=True)
class CreateTableAsRuntimeCase:
    case_id: str
    sql_filename: str
    object_prefix: str
    outcome: str
    expected_sqlstate: str
    expected_failure_reason: str | None
    is_extension: bool
    primary_obligation_id: str


@dataclass(frozen=True)
class CreateTableAsRuntimeCaseSet:
    cases: tuple[CreateTableAsRuntimeCase, ...]
    baseline_case_count: int
    extension_case_count: int
    total_case_count: int
    case_id_multiset_sha256: str


@dataclass(frozen=True)
class CreateTableAsCaseRuntimeResult:
    case_id: str
    sql_filename: str
    exit_code: int
    target_sqlstate: str | None
    stderr_excerpt: str
    passed: bool


@dataclass(frozen=True)
class CreateTableAsSuiteRun:
    run_label: str
    results: tuple[CreateTableAsCaseRuntimeResult, ...]
    pass_count: int
    fail_count: int


@dataclass(frozen=True)
class CreateTableAsTwoRunComparison:
    run_a: CreateTableAsSuiteRun
    run_b: CreateTableAsSuiteRun
    matching_case_ids: tuple[str, ...]
    divergent_case_ids: tuple[str, ...]
    stable: bool


def _sha256_multiset(case_ids: tuple[str, ...]) -> str:
    import hashlib
    import json
    digest = hashlib.sha256(
        b"create-table-as-runtime-case-set-v1\n"
    )
    for case_id in sorted(case_ids):
        digest.update(
            json.dumps(
                {"case_id": case_id},
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        digest.update(b"\n")
    return digest.hexdigest()


def build_create_table_as_runtime_case_set(
    repository_root: Path,
) -> CreateTableAsRuntimeCaseSet:
    """Combine baseline + extension into one ordered runtime case set."""

    root = Path(repository_root).resolve(strict=True)
    baseline = build_create_table_as_factor_loop_plan(root)
    extension = build_create_table_as_factor_extension_plan(root)
    cases: list[CreateTableAsRuntimeCase] = []
    for case in baseline.cases:
        cases.append(
            CreateTableAsRuntimeCase(
                case_id=case.case_id,
                sql_filename=case.sql_filename,
                object_prefix=case.object_prefix,
                outcome=case.outcome,
                expected_sqlstate=case.expected_sqlstate,
                expected_failure_reason=(
                    case.expected_failure_reason
                ),
                is_extension=False,
                primary_obligation_id=(
                    case.primary_obligation_id
                ),
            )
        )
    for case in extension.cases:
        cases.append(
            CreateTableAsRuntimeCase(
                case_id=case.case_id,
                sql_filename=case.sql_filename,
                object_prefix=case.object_prefix,
                outcome=case.outcome,
                expected_sqlstate=case.expected_sqlstate,
                expected_failure_reason=(
                    case.expected_failure_reason
                ),
                is_extension=True,
                primary_obligation_id=(
                    case.derivation_id
                ),
            )
        )
    case_ids = tuple(c.case_id for c in cases)
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("runtime case_id collision")
    return CreateTableAsRuntimeCaseSet(
        cases=tuple(cases),
        baseline_case_count=len(baseline.cases),
        extension_case_count=len(extension.cases),
        total_case_count=len(cases),
        case_id_multiset_sha256=_sha256_multiset(case_ids),
    )


class CreateTableAsPg18Runner:
    """Run CREATE TABLE AS regress programs against a PG18.4 instance."""

    def __init__(
        self,
        pg18_bin: str = PG18_BIN,
        pg18_socket: str = PG18_SOCKET,
        pg18_port: str = PG18_PORT,
    ) -> None:
        self._pg18_bin = pg18_bin
        self._pg18_socket = pg18_socket
        self._pg18_port = pg18_port

    def _psql(self) -> str:
        return f"{self._pg18_bin}/psql"

    def run_case(
        self,
        case: CreateTableAsRuntimeCase,
        sql_text: str,
        run_label: str,
    ) -> CreateTableAsCaseRuntimeResult:
        """Execute one SQL program against PG18.4 and capture results."""

        if not sql_text:
            raise ValueError(
                f"empty SQL for case {case.case_id}"
            )
        cmd = [
            self._psql(),
            "-h",
            self._pg18_socket,
            "-p",
            self._pg18_port,
            "-v",
            "ON_ERROR_STOP=1",
            "-f",
            "/dev/stdin",
        ]
        try:
            proc = subprocess.run(
                cmd,
                input=sql_text.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60,
            )
        except (
            subprocess.TimeoutExpired,
            FileNotFoundError,
        ) as exc:
            return CreateTableAsCaseRuntimeResult(
                case_id=case.case_id,
                sql_filename=case.sql_filename,
                exit_code=-1,
                target_sqlstate=None,
                stderr_excerpt=str(exc)[:200],
                passed=False,
            )
        stderr_excerpt = (
            proc.stderr.decode("utf-8", "replace")[:200]
            if proc.stderr
            else ""
        )
        target_sqlstate = (
            _extract_sqlstate(stderr_excerpt)
            if proc.returncode != 0
            else "00000"
        )
        if case.outcome == "success":
            passed = proc.returncode == 0
        else:
            passed = (
                proc.returncode != 0
                and (
                    case.expected_sqlstate == "00000"
                    or target_sqlstate == case.expected_sqlstate
                )
            )
        return CreateTableAsCaseRuntimeResult(
            case_id=case.case_id,
            sql_filename=case.sql_filename,
            exit_code=proc.returncode,
            target_sqlstate=target_sqlstate,
            stderr_excerpt=stderr_excerpt,
            passed=passed,
        )

    def run_suite(
        self,
        case_set: CreateTableAsRuntimeCaseSet,
        programs: Mapping[str, str],
        run_label: str,
    ) -> CreateTableAsSuiteRun:
        """Execute the full case set and return a suite run."""

        results: list[CreateTableAsCaseRuntimeResult] = []
        for case in case_set.cases:
            sql_text = programs.get(case.sql_filename, "")
            if not sql_text:
                results.append(
                    CreateTableAsCaseRuntimeResult(
                        case_id=case.case_id,
                        sql_filename=case.sql_filename,
                        exit_code=-1,
                        target_sqlstate=None,
                        stderr_excerpt="missing program",
                        passed=False,
                    )
                )
                continue
            results.append(
                self.run_case(case, sql_text, run_label)
            )
        pass_count = sum(1 for r in results if r.passed)
        return CreateTableAsSuiteRun(
            run_label=run_label,
            results=tuple(results),
            pass_count=pass_count,
            fail_count=len(results) - pass_count,
        )


def _extract_sqlstate(stderr_excerpt: str) -> str | None:
    import re
    match = re.search(r"SQLSTATE\s+(\w{5})", stderr_excerpt)
    if match:
        return match.group(1)
    return None


def compare_create_table_as_runs(
    run_a: CreateTableAsSuiteRun,
    run_b: CreateTableAsSuiteRun,
) -> CreateTableAsTwoRunComparison:
    """Compare two suite runs by case_id."""

    results_a = {r.case_id: r for r in run_a.results}
    results_b = {r.case_id: r for r in run_b.results}
    common = sorted(set(results_a) & set(results_b))
    matching: list[str] = []
    divergent: list[str] = []
    for case_id in common:
        a = results_a[case_id]
        b = results_b[case_id]
        if (
            a.passed == b.passed
            and a.exit_code == b.exit_code
            and a.target_sqlstate == b.target_sqlstate
        ):
            matching.append(case_id)
        else:
            divergent.append(case_id)
    stable = not divergent and len(common) == len(results_a)
    return CreateTableAsTwoRunComparison(
        run_a=run_a,
        run_b=run_b,
        matching_case_ids=tuple(matching),
        divergent_case_ids=tuple(divergent),
        stable=stable,
    )


__all__ = [
    "PG18_BIN",
    "PG18_SOCKET",
    "PG18_PORT",
    "CreateTableAsRuntimeCase",
    "CreateTableAsRuntimeCaseSet",
    "CreateTableAsCaseRuntimeResult",
    "CreateTableAsSuiteRun",
    "CreateTableAsTwoRunComparison",
    "CreateTableAsPg18Runner",
    "build_create_table_as_runtime_case_set",
    "compare_create_table_as_runs",
]
