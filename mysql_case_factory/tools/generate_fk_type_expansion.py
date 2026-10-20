#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from mysql_case_factory.fk_type_expansion import write_fk_expansion_artifacts


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the TUCFK FK type-expansion batch")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = write_fk_expansion_artifacts(args.output)
    print(f"wrote {manifest['case_count']} scenarios to {args.output}")


if __name__ == "__main__":
    main()
