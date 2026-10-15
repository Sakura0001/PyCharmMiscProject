#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from mysql_case_factory.type_upgrade_pipeline_audit import audit_pipeline_artifacts


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit the condensed type-upgrade pipeline artifacts")
    parser.add_argument("--pipeline", type=Path, required=True)
    parser.add_argument(
        "--parent",
        action="append",
        type=Path,
        default=[],
        help="Parent cases.jsonl.gz; repeat for every parent batch",
    )
    parser.add_argument("--skip-local", action="store_true")
    args = parser.parse_args()
    report = audit_pipeline_artifacts(args.pipeline, parent_case_paths=args.parent, require_local=not args.skip_local)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
