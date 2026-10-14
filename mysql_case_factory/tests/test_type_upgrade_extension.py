from __future__ import annotations

import gzip
import json
import subprocess
import sys
from pathlib import Path

from mysql_case_factory.type_upgrade_extension import (
    EXTENSION_BATCH_ID,
    EXTENSION_BATCH_KIND,
    EXTENSION_CASE_PREFIX,
    PARENT_BATCH_ID,
    extension_manifest,
    generate_extension_cases,
    render_extension_suite,
)


P0_GAPS = {
    "GAP-DATA-BEHAVIOR",
    "GAP-INDEX-PK",
    "GAP-DDL-MULTI-COLUMN",
    "GAP-FK-ACTION",
    "GAP-QUERY-ORACLE",
}


def test_extension_batch_identity_is_separate_from_baseline() -> None:
    assert EXTENSION_BATCH_ID == "2026-10-13-type-upgrade-consistency-extension-v1"
    assert EXTENSION_BATCH_KIND == "extension"
    assert PARENT_BATCH_ID == "2026-10-13-type-upgrade-consistency"
    assert EXTENSION_CASE_PREFIX == "TUCX"


def test_extension_cases_have_gap_metadata_and_unique_ids() -> None:
    cases = generate_extension_cases()

    assert cases
    assert len({case.case_id for case in cases}) == len(cases)
    assert all(case.case_id.startswith("TUCX-") for case in cases)
    assert all(case.batch_id == EXTENSION_BATCH_ID for case in cases)
    assert all(case.batch_kind == EXTENSION_BATCH_KIND for case in cases)
    assert all(case.parent_batch_id == PARENT_BATCH_ID for case in cases)
    assert all(case.priority == "P0" for case in cases)
    assert all(case.gap_id in P0_GAPS for case in cases)
    assert all(case.coverage_tags for case in cases)
    assert P0_GAPS == {case.gap_id for case in cases}


def test_extension_generation_is_deterministic() -> None:
    first = generate_extension_cases()
    second = generate_extension_cases()
    assert [case.to_json() for case in first] == [case.to_json() for case in second]


def test_extension_manifest_and_suites_use_extension_identity() -> None:
    cases = generate_extension_cases()
    manifest = extension_manifest(cases, "copy")

    assert manifest["batch_id"] == EXTENSION_BATCH_ID
    assert manifest["batch_kind"] == EXTENSION_BATCH_KIND
    assert manifest["parent_batch_id"] == PARENT_BATCH_ID
    assert manifest["case_id_prefix"] == EXTENSION_CASE_PREFIX
    assert manifest["case_count"] == len(cases)
    assert set(manifest["gap_counts"]) == P0_GAPS

    copy_sql = render_extension_suite(cases, "copy")
    inplace_sql = render_extension_suite(cases, "inplace")
    instant_sql = render_extension_suite(cases, "instant")
    assert copy_sql.count(f"-- BATCH_ID: {EXTENSION_BATCH_ID}") == len(cases)
    assert inplace_sql.count(f"-- BATCH_ID: {EXTENSION_BATCH_ID}") == len(cases)
    assert instant_sql.count(f"-- BATCH_ID: {EXTENSION_BATCH_ID}") == len(cases)


def test_extension_generator_writes_deterministic_artifacts(tmp_path: Path) -> None:
    tool = Path(__file__).parents[1] / "tools" / "generate_type_upgrade_extension.py"
    first = tmp_path / "first"
    second = tmp_path / "second"
    for output in (first, second):
        subprocess.run(
            [sys.executable, str(tool), "--output", str(output)],
            check=True,
            cwd=Path(__file__).parents[1],
        )

    required = {
        "cases.jsonl.gz",
        "copy_suite.sql.gz",
        "inplace_suite.sql.gz",
        "instant_suite.sql.gz",
        "manifest.json",
        "coverage.tsv",
        "README.md",
    }
    assert required <= {path.name for path in first.iterdir()}
    assert (first / "cases.jsonl.gz").read_bytes() == (second / "cases.jsonl.gz").read_bytes()
    assert (first / "copy_suite.sql.gz").read_bytes() == (second / "copy_suite.sql.gz").read_bytes()

    manifest = json.loads((first / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["batch_id"] == EXTENSION_BATCH_ID
    assert manifest["parent_batch_id"] == PARENT_BATCH_ID
    assert manifest["case_count"] > 0

    with gzip.open(first / "cases.jsonl.gz", "rt", encoding="utf-8") as handle:
        payloads = [json.loads(line) for line in handle]
    assert all(payload["batch_id"] == EXTENSION_BATCH_ID for payload in payloads)
    assert all(payload["parent_batch_id"] == PARENT_BATCH_ID for payload in payloads)
    assert all(payload["case_id"].startswith("TUCX-") for payload in payloads)


def test_orphan_insert_uses_deleted_parent_value_not_target_boundary() -> None:
    cases = generate_extension_cases()
    case = next(case for case in cases if case.reason == "P0 foreign-key action: orphan_insert")
    binary_case = next(
        case
        for case in cases
        if case.reason == "P0 foreign-key action: orphan_insert" and case.family == "binary"
    )

    assert any(statement.startswith("DELETE FROM tuc_ref_") and "WHERE id=1 OR target_col=" in statement for statement in case.post_ddl_sql)
    assert any(statement.startswith("DELETE FROM tuc_algo_") for statement in case.post_ddl_sql)
    assert not any("INSERT INTO tucx_fk_child_ref_" in statement for statement in case.post_ddl_sql)
    assert all(statement.split("VALUES (", 1)[1].startswith("2000,") for statement in case.invalid_post_ddl_sql)
    assert binary_case.invalid_post_ddl_sql[0].split("VALUES (", 1)[1].startswith("2000,x'00'")


def test_fk_update_actions_use_value_different_from_padded_old_key() -> None:
    cases = generate_extension_cases()
    case = next(
        item
        for item in cases
        if item.reason == "P0 foreign-key action: update_restrict"
        and item.family == "binary"
        and item.source_type == "BINARY(1)"
        and item.target_type == "BINARY(2)"
    )
    updates = [statement for statement in case.invalid_post_ddl_sql if statement.startswith("UPDATE ")]
    assert updates
    assert all("SET target_col=x'0102'" in statement for statement in updates)


def test_prefix_order_query_cases_only_use_prefixable_families() -> None:
    cases = generate_extension_cases()
    prefix_cases = [case for case in cases if case.reason.endswith("prefix_order")]
    assert prefix_cases
    assert all(case.family in {"character", "binary"} for case in prefix_cases)
    assert all(
        case.source_type.endswith(("TEXT", "BLOB"))
        or int(case.source_type.split("(", 1)[1].split(")", 1)[0]) > 1
        for case in prefix_cases
    )
