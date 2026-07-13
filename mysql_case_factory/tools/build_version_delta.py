from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

import yaml

from mysql_case_factory.version_delta import (
    CHANGED_STATEMENT_SOURCES,
    DELTA_COLUMNS,
    _factor_rows,
)


def build(edition_8022: Path, edition_8041: Path, output: Path) -> dict[str, int]:
    rows_22 = _factor_rows(edition_8022.resolve())
    rows_41 = _factor_rows(edition_8041.resolve())
    counts = {"added": 0, "changed": 0, "removed": 0, "unchanged": 0}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=DELTA_COLUMNS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for key in sorted(set(rows_22) | set(rows_41)):
            row_22 = rows_22.get(key)
            row_41 = rows_41.get(key)
            if row_22 is None:
                disposition = "added"
            elif row_41 is None:
                disposition = "removed"
            elif key[0] in CHANGED_STATEMENT_SOURCES:
                disposition = "changed"
            else:
                disposition = "unchanged"
            counts[disposition] += 1
            source_row = row_41 or row_22
            official_locator = (
                CHANGED_STATEMENT_SOURCES[key[0]]
                if disposition != "unchanged"
                else source_row["official_source_target"]
            )
            notes = {
                "added": "Factor/value is available in 8.0.41 and absent from the 8.0.22 edition.",
                "removed": "Factor/value is absent from 8.0.41 after release-note review.",
                "changed": "Statement semantics or syntax changed in the cited intervening release.",
                "unchanged": "No statement factor/value change was identified in the 8.0.23-8.0.41 release boundary review.",
            }[disposition]
            writer.writerow(
                {
                    "statement_key": key[0],
                    "factor": key[1],
                    "value": key[2],
                    "disposition": disposition,
                    "source_8_0_22": row_22["source_reference"] if row_22 else "",
                    "source_8_0_41": row_41["source_reference"] if row_41 else "",
                    "official_locator": official_locator,
                    "review_status": "static_reviewed",
                    "notes": notes,
                }
            )
    manifest_path = edition_8041.resolve() / "edition.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    inventories = [
        item for item in manifest.get("inventories", []) if item.get("kind") != "version_delta"
    ]
    inventories.append(
        {
            "kind": "version_delta",
            "path": output.resolve().relative_to(edition_8041.resolve()).as_posix(),
            "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "count": sum(counts.values()),
        }
    )
    manifest["inventories"] = inventories
    manifest_path.write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True, width=120),
        encoding="utf-8",
    )
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the closed 8.0.22-to-8.0.41 factor delta.")
    parser.add_argument("--edition-8022", type=Path, required=True)
    parser.add_argument("--edition-8041", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    counts = build(args.edition_8022, args.edition_8041, args.output)
    print(" ".join(f"{key}={value}" for key, value in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
