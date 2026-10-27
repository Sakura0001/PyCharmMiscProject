#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from mysql_case_factory.type_upgrade_condensed_120 import write_condensed_120_artifacts


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the 120-file TUCR condensed SQL batch")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = write_condensed_120_artifacts(args.output)
    print(
        f"wrote {manifest['sql_file_count']} SQL files and "
        f"{manifest['expected_output_line_count']} expected result rows to {args.output}"
    )


if __name__ == "__main__":
    main()
