#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from mysql_case_factory.unique_ddl_expected_error import write_unique_ddl_error_artifacts


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the TUCUD unique-DDL expected-error batch metadata")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rows", type=int, default=200_000)
    args = parser.parse_args()
    manifest = write_unique_ddl_error_artifacts(args.output, rows=args.rows)
    print(
        f"wrote {manifest['case_count']} scenarios and "
        f"{manifest['smoke_case_count']} smoke cases to {args.output}"
    )


if __name__ == "__main__":
    main()
