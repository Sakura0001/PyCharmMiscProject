#!/usr/bin/env python3
"""Generate deterministic SQL type-upgrade consistency artifacts."""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from hashlib import sha256
from collections import Counter
from pathlib import Path

from mysql_case_factory.type_upgrade_consistency import (
    FORBIDDEN_TYPE_TOKENS,
    TYPE_UPGRADE_BATCH_ID,
    TYPE_UPGRADE_BATCH_KIND,
    TYPE_UPGRADE_CASE_PREFIX,
    generate_cases,
    render_suite,
    suite_manifest,
)


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def _write_gzip(path: Path, text: str) -> None:
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            compressed.write(text.encode("utf-8"))


def generate(output: Path) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    cases = generate_cases()

    cases_path = output / "cases.jsonl.gz"
    with cases_path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with __import__("io").TextIOWrapper(compressed, encoding="utf-8", newline="\n") as handle:
                for case in cases:
                    handle.write(json.dumps(case.to_json(), sort_keys=True, separators=(",", ":"), ensure_ascii=False))
                    handle.write("\n")

    manifests = {}
    for profile in ("copy", "inplace", "instant"):
        _write_gzip(output / f"{profile}_suite.sql.gz", render_suite(cases, profile))
        manifests[profile] = suite_manifest(cases, profile)

    clusters = Counter(case.cluster for case in cases)
    families = Counter(case.family for case in cases)
    attributes = Counter(case.column_attribute for case in cases)
    indexes = Counter(case.index_profile for case in cases)
    foreign_keys = Counter(case.foreign_key_profile for case in cases)
    dependencies = Counter(case.dependency_profile for case in cases)
    table_forms = Counter(case.table_form for case in cases)
    sql_modes = Counter(case.sql_mode for case in cases)

    lines = [
        "factor_type\tfactor_value\tcase_count",
        *(f"cluster\t{key}\t{value}" for key, value in sorted(clusters.items())),
        *(f"family\t{key}\t{value}" for key, value in sorted(families.items())),
        *(f"column_attribute\t{key}\t{value}" for key, value in sorted(attributes.items())),
        *(f"index_profile\t{key}\t{value}" for key, value in sorted(indexes.items())),
        *(f"foreign_key_profile\t{key}\t{value}" for key, value in sorted(foreign_keys.items())),
        *(f"dependency_profile\t{key}\t{value}" for key, value in sorted(dependencies.items())),
        *(f"table_form\t{key}\t{value}" for key, value in sorted(table_forms.items())),
        *(f"sql_mode\t{key}\t{value}" for key, value in sorted(sql_modes.items())),
    ]
    _write_text(output / "coverage.tsv", "\n".join(lines) + "\n")
    readme = (
        "# Type-upgrade consistency batch\n\n"
        f"BATCH_ID: {TYPE_UPGRADE_BATCH_ID}\n"
        f"BATCH_KIND: {TYPE_UPGRADE_BATCH_KIND.upper()}\n"
        f"CASE_COUNT: {len(cases)}\n"
        f"CASE_PREFIX: {TYPE_UPGRADE_CASE_PREFIX}\n\n"
        "This batch is separate from previous DDL verification cases.\n"
        "It was merged into `codex/ddl-verify-20260919` as a new type-upgrade consistency suite.\n"
    )
    _write_text(output / "README.md", readme)

    artifact_names = (
        "cases.jsonl.gz",
        "copy_suite.sql.gz",
        "inplace_suite.sql.gz",
        "instant_suite.sql.gz",
        "coverage.tsv",
        "README.md",
    )
    artifacts = {
        name: {
            "sha256": sha256((output / name).read_bytes()).hexdigest(),
            "bytes": (output / name).stat().st_size,
        }
        for name in artifact_names
    }

    manifest = {
        "format_version": 1,
        "batch_id": TYPE_UPGRADE_BATCH_ID,
        "batch_kind": TYPE_UPGRADE_BATCH_KIND,
        "case_id_prefix": TYPE_UPGRADE_CASE_PREFIX,
        "case_count": len(cases),
        "profiles": manifests,
        "forbidden_type_tokens": list(FORBIDDEN_TYPE_TOKENS),
        "forbidden_types_absent": all(
            token not in json.dumps([case.to_json() for case in cases], ensure_ascii=False)
            for token in FORBIDDEN_TYPE_TOKENS
        ),
        "artifacts": artifacts,
    }
    _write_text(output / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="output directory")
    args = parser.parse_args(argv)
    manifest = generate(args.output)
    print(
        f"generated {manifest['case_count']} cases; "
        f"forbidden_types_absent={manifest['forbidden_types_absent']}; output={args.output}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
