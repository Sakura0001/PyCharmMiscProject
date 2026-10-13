#!/usr/bin/env python3
"""Run generated type-upgrade cases against an isolated local MySQL 8.0.45 server."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mysql_case_factory.type_upgrade_runner import run_local


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cases",
        type=Path,
        default=Path(__file__).parents[1] / "generated" / "type_upgrade_consistency" / "cases.jsonl.gz",
    )
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--limit", type=int, help="run only the first N cases")
    parser.add_argument("--case-id", action="append", default=[], help="run only these case IDs; repeatable")
    parser.add_argument("--mysqld", default="/opt/homebrew/opt/mysql@8.0/bin/mysqld")
    parser.add_argument("--keep-server", action="store_true", help="unsupported placeholder kept for API symmetry")
    args = parser.parse_args(argv)
    if args.keep_server:
        parser.error("--keep-server is not supported for the local isolated runner")

    summary = run_local(
        args.cases,
        args.results,
        args.summary,
        limit=args.limit,
        case_ids=set(args.case_id),
        mysqld=args.mysqld,
    )
    from mysql_case_factory.type_upgrade_runner import render_summary_markdown

    args.summary.with_suffix(".md").write_text(render_summary_markdown(summary), encoding="utf-8")
    print(
        f"executed={summary['executed_count']} selected={summary['selected_count']} "
        f"all_pass={summary['all_pass']} stopped_early={summary['stopped_early']}"
    )
    return 0 if summary["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
