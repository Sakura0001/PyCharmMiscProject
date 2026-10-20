#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from mysql_case_factory.inplace_unique_conflict_audit import audit_inplace_unique_artifacts


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit the TUCUI INPLACE unique-conflict batch")
    parser.add_argument("--inplace-unique", type=Path, required=True)
    parser.add_argument("--skip-local", action="store_true")
    args = parser.parse_args()
    report = audit_inplace_unique_artifacts(
        args.inplace_unique,
        require_local=not args.skip_local,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
