#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from mysql_case_factory.type_upgrade_performance import write_type_performance_artifacts


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the TUCPF type-upgrade performance batch metadata")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = write_type_performance_artifacts(args.output)
    print(f"wrote {manifest['case_count']} scenarios to {args.output}")


if __name__ == "__main__":
    main()
