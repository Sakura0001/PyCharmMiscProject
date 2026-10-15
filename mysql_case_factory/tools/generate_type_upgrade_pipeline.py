#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from mysql_case_factory.type_upgrade_pipeline import write_pipeline_artifacts


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the condensed type-upgrade pipeline SQL batch")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = write_pipeline_artifacts(args.output)
    print(
        f"wrote {manifest['case_count']} cases to {args.output} "
        f"for profiles: {', '.join(manifest['profiles'])}"
    )


if __name__ == "__main__":
    main()
