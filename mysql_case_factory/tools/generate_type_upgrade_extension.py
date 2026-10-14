#!/usr/bin/env python3
"""Generate deterministic artifacts for the TUCX type-upgrade extension batch."""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from collections import Counter
from hashlib import sha256
from pathlib import Path

from mysql_case_factory.type_upgrade_consistency import FORBIDDEN_TYPE_TOKENS
from mysql_case_factory.type_upgrade_extension import (
    EXTENSION_BATCH_ID,
    EXTENSION_BATCH_KIND,
    EXTENSION_CASE_PREFIX,
    PARENT_BATCH_ID,
    extension_manifest,
    generate_extension_cases,
    json_dumps,
    render_extension_suite,
)


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def _write_gzip(path: Path, text: str) -> None:
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            compressed.write(text.encode("utf-8"))


def generate(output: Path) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    cases = generate_extension_cases()

    cases_path = output / "cases.jsonl.gz"
    with cases_path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with __import__("io").TextIOWrapper(compressed, encoding="utf-8", newline="\n") as handle:
                for case in cases:
                    handle.write(json.dumps(case.to_json(), sort_keys=True, separators=(",", ":"), ensure_ascii=False))
                    handle.write("\n")

    manifests = {}
    for profile in ("copy", "inplace", "instant"):
        _write_gzip(output / f"{profile}_suite.sql.gz", render_extension_suite(cases, profile))
        manifests[profile] = extension_manifest(cases, profile)

    gap_counts = Counter(case.gap_id for case in cases if case.gap_id is not None)
    family_counts = Counter(case.family for case in cases)
    cluster_counts = Counter(case.cluster for case in cases)
    priority_counts = Counter(case.priority for case in cases if case.priority is not None)
    interaction_counts = Counter(case.interaction_rank for case in cases if case.interaction_rank is not None)
    coverage_lines = [
        "factor_type\tfactor_value\tcase_count",
        *(f"gap_id\t{key}\t{value}" for key, value in sorted(gap_counts.items())),
        *(f"family\t{key}\t{value}" for key, value in sorted(family_counts.items())),
        *(f"cluster\t{key}\t{value}" for key, value in sorted(cluster_counts.items())),
        *(f"priority\t{key}\t{value}" for key, value in sorted(priority_counts.items())),
        *(f"interaction_rank\t{key}\t{value}" for key, value in sorted(interaction_counts.items())),
    ]
    _write_text(output / "coverage.tsv", "\n".join(coverage_lines) + "\n")

    readme = (
        "# Type-upgrade consistency extension v1\n\n"
        f"BATCH_ID: {EXTENSION_BATCH_ID}\n"
        f"BATCH_KIND: {EXTENSION_BATCH_KIND.upper()}\n"
        f"PARENT_BATCH_ID: {PARENT_BATCH_ID}\n"
        f"CASE_COUNT: {len(cases)}\n"
        f"CASE_PREFIX: {EXTENSION_CASE_PREFIX}\n\n"
        "This is an independent extension batch. Do not mix it with the verified `TUC` baseline.\n"
        "`TUC` is the 8,270-case baseline; `TUCX` is this extension batch.\n\n"
        "## Internal AI execution instructions\n\n"
        "1. Verify `manifest.json` first. The parent batch, extension batch, case count, profile\n"
        "   counts, and artifact hashes must match.\n"
        "2. Execute only `TUCX-` cases carrying this extension batch ID. Do not execute or merge\n"
        "   results with `TUC-` baseline cases.\n"
        "3. Run `COPY` locally only as the MySQL 8.0.45 oracle. Internal PASS must come from\n"
        "   separate `INPLACE` and `INSTANT` executions.\n"
        "4. Negative cases may intentionally return SQL errors. Use `mysql --force`, preserve stderr,\n"
        "   and continue through planned rejects.\n"
        "5. A server crash, assertion, signal, or MySQL 2013 is `FAIL_CRASH`; never classify it as\n"
        "   an expected negative result.\n"
        "6. On failure, stop, preserve stdout/stderr and the nearest `-- CASE_ID`, and report batch\n"
        "   ID, profile, case ID, gap ID, SQL, error, and terminal state.\n\n"
        "Example:\n\n"
        "```bash\n"
        "gunzip -c inplace_suite.sql.gz > inplace_suite.sql\n"
        "gunzip -c instant_suite.sql.gz > instant_suite.sql\n\n"
        "mysql --login-path=internal_qa --batch --raw --force qa_type_upgrade_extension \\\n"
        "  < inplace_suite.sql > inplace.results.tsv 2> inplace.errors.log\n\n"
        "mysql --login-path=internal_qa --batch --raw --force qa_type_upgrade_extension \\\n"
        "  < instant_suite.sql > instant.results.tsv 2> instant.errors.log\n\n"
        "grep -n $'\\tFAIL\\t\\|^FAIL\\b' inplace.results.tsv instant.results.tsv || true\n"
        "```\n"
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
        "batch_id": EXTENSION_BATCH_ID,
        "batch_kind": EXTENSION_BATCH_KIND,
        "parent_batch_id": PARENT_BATCH_ID,
        "case_id_prefix": EXTENSION_CASE_PREFIX,
        "case_count": len(cases),
        "profiles": manifests,
        "forbidden_type_tokens": list(FORBIDDEN_TYPE_TOKENS),
        "forbidden_types_absent": all(
            token not in json_dumps(cases) for token in FORBIDDEN_TYPE_TOKENS
        ),
        "artifacts": artifacts,
    }
    _write_text(output / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    manifest = generate(args.output)
    print(
        f"generated {manifest['case_count']} extension cases; "
        f"forbidden_types_absent={manifest['forbidden_types_absent']}; output={args.output}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
