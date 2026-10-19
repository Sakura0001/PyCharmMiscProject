#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from mysql_case_factory.type_upgrade_primary_key import write_primary_key_artifacts


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the TUCPK primary-key concurrency batch metadata")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = write_primary_key_artifacts(args.output)
    print(
        f"wrote {manifest['transition_count']} transitions and "
        f"{manifest['scenario_count']} virtual scenarios to {args.output}"
    )


if __name__ == "__main__":
    main()
