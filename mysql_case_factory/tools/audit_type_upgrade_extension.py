#!/usr/bin/env python3
"""Audit the TUC baseline and TUCX extension artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mysql_case_factory.type_upgrade_extension_audit import audit_extension


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--extension", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    result = audit_extension(args.baseline, args.extension, args.report_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
