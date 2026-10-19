#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from mysql_case_factory.type_upgrade_primary_key_audit import audit_primary_key_artifacts


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit the TUCPK primary-key concurrency batch")
    parser.add_argument("--primary-key", type=Path, required=True)
    parser.add_argument("--skip-local", action="store_true")
    args = parser.parse_args()
    report = audit_primary_key_artifacts(args.primary_key, require_local=not args.skip_local)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
