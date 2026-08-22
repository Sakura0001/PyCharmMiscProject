#!/usr/bin/env python3
"""Per-package two-round PG18.4 verification for factor-regress SQL.

For a given statement_key, renders every (or a subset of) case to SQL, runs each
TWICE against a local PostgreSQL 18.4 server, and compares the two rounds via the
package's compare function. Prints the five regress buckets plus a per-case table.

This is the faithful "前后执行两次输出一致" (two-run identical-output) check the
regress framework requires, scoped to a single package for fast Phase-1+ iteration
without a full 855k-case re-run.

Usage:
  uv run python scripts/verify_package_pg18.py drop_collation            # all cases, package server
  uv run python scripts/verify_package_pg18.py drop_collation --subset DROPCOLLATION00001,DROPCOLLATION00002
  uv run python scripts/verify_package_pg18.py delete --start-worker      # spin a dedicated cluster
  uv run python scripts/verify_package_pg18.py delete --socket /tmp/sock --port 55489 --database pgcf_dc
"""

from __future__ import annotations

import argparse
import importlib
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
_SRC = ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

PG18_BIN_DEFAULT = Path("/tmp/pgcf-postgresql-18.4-install/bin")

_BUCKET_FIELDS = (
    ("transcript_mismatch_case_ids", "transcript"),
    ("structured_mismatch_case_ids", "structured"),
    ("sqlstate_mismatch_case_ids", "sqlstate"),
    ("cleanup_failure_case_ids", "cleanup"),
    ("execution_failure_case_ids", "execution"),
)


@dataclass(frozen=True)
class Package:
    """Lazy-resolved symbols for one statement_key, derived by naming convention."""

    key: str
    runner_cls: type
    compare_fn: Callable[..., Any]
    build_case_set: Callable[..., Any]
    build_plan: Callable[..., Any]
    render_case: Callable[..., Any]


def _camel(key: str) -> str:
    return key.title().replace("_", "")


def load_package(key: str) -> Package:
    """Import the runtime/loop/render symbols for ``key`` by naming convention."""
    camel = _camel(key)
    rt = importlib.import_module(f"pg_case_factory.{key}_factor_runtime")
    loop = importlib.import_module(f"pg_case_factory.{key}_factor_loop")
    render = importlib.import_module(f"pg_case_factory.{key}_factor_render")
    try:
        return Package(
            key=key,
            runner_cls=getattr(rt, f"{camel}Pg18Runner"),
            compare_fn=getattr(rt, f"compare_{key}_runs"),
            build_case_set=getattr(rt, f"build_{key}_runtime_case_set"),
            build_plan=getattr(loop, f"build_{key}_factor_loop_plan"),
            render_case=getattr(render, f"render_{key}_factor_case"),
        )
    except AttributeError as exc:
        raise SystemExit(
            f"package {key!r} does not expose the full factor_runtime contract ({exc}); "
            f"it may still use the legacy runtime path and needs migration first"
        ) from exc


def render_cases(
    package: Package, sql_dir: Path, subset: set[str] | None = None
) -> tuple[tuple[Any, ...], dict[str, Path]]:
    """Build the case set and write SQL. With a subset, render only those cases.

    Rendering is the expensive step (one file per case); for huge packages
    (create_aggregate ships ~18k extension cases) we avoid writing all of them
    when only a subset is verified. ``run_cases`` skips cases whose SQL is
    absent, so the unrendered ones are never executed.
    """
    cases, sql_paths = package.build_case_set(ROOT, sql_dir)
    targets = [c for c in cases if subset is None or c.case_id in subset]
    for case in targets:
        sql_paths[case.case_id].write_text(package.render_case(case, ROOT), encoding="utf-8")
    return cases, sql_paths


def _build_runner(package: Package, args: argparse.Namespace) -> Any:
    """Construct the package runner pointed at the requested server."""
    if args.start_worker:
        return _runner_from_worker(package, args)
    overrides: dict[str, Any] = {"bin_dir": Path(args.bin)}
    if args.socket:
        overrides["socket_dir"] = Path(args.socket)
    if args.port:
        overrides["port"] = int(args.port)
    if args.database:
        overrides["database"] = args.database
    if args.role:
        overrides["role"] = args.role
    return package.runner_cls(**overrides)


def _runner_from_worker(package: Package, args: argparse.Namespace) -> Any:
    from pg_case_factory.full_sql_runtime import (
        PostgresWorker,
        build_worker_configs,
    )

    runtime_root = Path(tempfile.mkdtemp(prefix="pgcf-verify-"))
    configs = build_worker_configs(runtime_root, Path(args.bin), workers=1, base_port=55720)
    worker = PostgresWorker(configs[0], timeout_seconds=60)
    worker.start()
    # Stash the worker on the runner so the caller can stop it; the runner ctor
    # does not take a worker, so we attach it as an attribute after construction.
    runner = package.runner_cls(
        bin_dir=Path(args.bin),
        socket_dir=worker.socket_dir,
        port=worker.config.port,
        database=worker.config.database,
        role=worker.config.role,
    )
    setattr(runner, "_verify_worker", worker)
    return runner


def _stop_runner(runner: Any) -> None:
    worker = getattr(runner, "_verify_worker", None)
    if worker is not None:
        worker.stop()


def run_two_rounds(
    package: Package, runner: Any, cases: tuple[Any, ...], sql_paths: dict[str, Path],
    subset: set[str] | None,
) -> tuple[Any, Any]:
    """Run every (selected) case twice and compare; return (comparison, run_01)."""
    selected = None if subset is None else tuple(sorted(subset))
    run_01 = runner.run_cases(cases, sql_paths, run_ordinal=1, selected_case_ids=selected)
    run_02 = runner.run_cases(cases, sql_paths, run_ordinal=2, selected_case_ids=selected)
    return package.compare_fn(run_01, run_02), run_01


def print_report(comparison: Any, run_01: Any) -> None:
    print(f"\npassed            : {comparison.passed}")
    print(f"execution_count   : {comparison.execution_count}")
    for attr, label in _BUCKET_FIELDS:
        ids = getattr(comparison, attr, ())
        sample = ", ".join(ids[:5]) + (" ..." if len(ids) > 5 else "")
        print(f"{label:<17} : {len(ids):>4}  {sample}")
    if comparison.issues:
        print("\nissues:")
        for issue in comparison.issues:
            print(f"  - {issue}")
    _print_per_case(run_01, comparison)


def _print_per_case(run: Any, comparison: Any) -> None:
    failing = set()
    for attr, _ in _BUCKET_FIELDS:
        failing.update(getattr(comparison, attr, ()))
    rows = [case for case in run.cases if case.case_id in failing]
    if not rows:
        print("\n(no per-case failures to tabulate)")
        return
    print("\nper-case failures:")
    header = (
        f"{'case_id':<26} {'exp':<8} {'tgt':<8} {'exit':>4} "
        f"{'oracle':>6} {'pre':>5} {'post':>5} {'cln_exit':>8}"
    )
    print(header)
    print("-" * len(header))
    for case in rows:
        print(
            f"{case.case_id:<26} {case.expected_sqlstate:<8} {case.target_sqlstate:<8} "
            f"{case.exit_code:>4} {case.boolean_oracle_failure_count:>6} "
            f"{str(case.pre_clean):>5} {str(case.post_clean):>5} {case.cleanup_exit_code:>8}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Per-package two-round PG18.4 factor-regress verifier")
    parser.add_argument("statement_key", help="e.g. drop_collation, delete, create_aggregate")
    parser.add_argument("--all", action="store_true", help="run every case (default when no --subset)")
    parser.add_argument("--subset", help="comma-separated case IDs to run")
    parser.add_argument(
        "--start-worker", action="store_true",
        help="spin a dedicated PostgresWorker (port 55720) instead of reusing a package server",
    )
    parser.add_argument("--bin", default=str(PG18_BIN_DEFAULT), help="PostgreSQL 18.4 bin dir")
    parser.add_argument("--socket", help="unix socket dir (overrides package default)")
    parser.add_argument("--port", help="port (overrides package default)")
    parser.add_argument("--database", help="database name (overrides package default)")
    parser.add_argument("--role", help="superuser role (overrides package default)")
    args = parser.parse_args(argv)

    if not Path(args.bin).is_dir():
        raise SystemExit(f"PostgreSQL bin dir not found: {args.bin}")

    package = load_package(args.statement_key)
    subset: set[str] | None = None
    if args.subset:
        subset = {token.strip() for token in args.subset.split(",") if token.strip()}
        if not subset:
            raise SystemExit("--subset must list at least one case ID")

    with tempfile.TemporaryDirectory(prefix="pgcf-verify-sql-") as sql_temp:
        sql_dir = Path(sql_temp)
        cases, sql_paths = render_cases(package, sql_dir, subset)
        if subset:
            unknown = subset - {case.case_id for case in cases}
            if unknown:
                raise SystemExit(f"unknown case IDs for {package.key}: {sorted(unknown)}")
        runner = _build_runner(package, args)
        try:
            comparison, run_01 = run_two_rounds(package, runner, cases, sql_paths, subset)
        finally:
            _stop_runner(runner)
        print_report(comparison, run_01)

    return 0 if comparison.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
