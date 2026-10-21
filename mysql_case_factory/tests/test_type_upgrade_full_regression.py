from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
FULL = ROOT / "generated" / "type_upgrade_full_regression"

EXPECTED_BATCHES = {
    "generated/type_upgrade_consistency": ("TUC", 8270),
    "generated/type_upgrade_consistency_extension_v1": ("TUCX", 13721),
    "generated/type_upgrade_statistics_v1": ("TUCS", 47),
    "generated/type_upgrade_pipeline_v1": ("TUCP", 50),
    "generated/type_upgrade_boundary_v1": ("TUCZ", 750),
    "generated/type_upgrade_primary_key_concurrency_v1": ("TUCPK", 946944),
    "generated/inplace_unique_conflict_v1": ("TUCUI", 2304),
    "generated/fk_type_expansion_v1": ("TUCFK", 568),
    "generated/unique_ddl_expected_error_v1": ("TUCUD", 192),
    "generated/virtual_function_type_upgrade_v1": ("TUCVF", 5136),
}


def _inventory() -> list[dict[str, str]]:
    with (FULL / "inventory.tsv").open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def test_full_regression_manifest_totals_and_policy() -> None:
    manifest = json.loads((FULL / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["regression_id"] == "2026-10-15-type-upgrade-full-regression-v1"
    assert manifest["policy"] == "MANDATORY_ALL_BATCHES_ALL_PROFILES"
    assert manifest["required"] is True
    assert manifest["selective_regression_allowed"] is False
    assert manifest["expected_output_may_be_rewritten_after_execution"] is False
    assert manifest["batch_count"] == 10
    assert manifest["case_count"] == 977982
    assert manifest["profile_execution_count"] == 2932994
    assert manifest["execution_stream_count"] == 27
    assert manifest["sql_artifact_count"] == 2411
    assert manifest["profiles"] == ["copy", "inplace", "instant"]


def test_full_regression_inventory_contains_every_batch_and_profile() -> None:
    rows = _inventory()
    assert len(rows) == 27
    assert [int(row["order"]) for row in rows] == list(range(1, 28))
    assert {row["profile"] for row in rows} == {"copy", "inplace", "instant"}
    assert {row["prefix"] for row in rows} == {"TUC", "TUCX", "TUCS", "TUCP", "TUCZ", "TUCPK", "TUCUI", "TUCFK", "TUCUD", "TUCVF"}
    assert sum(int(row["case_count"]) for row in rows) == 2932994

    for directory, (prefix, count) in EXPECTED_BATCHES.items():
        batch_rows = [row for row in rows if row["prefix"] == prefix]
        expected_profiles = {"inplace"} if prefix == "TUCUD" else ({"inplace", "instant"} if prefix == "TUCFK" else {"copy", "inplace", "instant"})
        assert len(batch_rows) == len(expected_profiles)
        assert all(int(row["case_count"]) == count for row in batch_rows)
        assert {row["profile"] for row in batch_rows} == expected_profiles
        assert all((ROOT / row["artifact"]).exists() or list(ROOT.glob(row["artifact"])) for row in batch_rows)
        batch_manifest = json.loads((ROOT / directory / "manifest.json").read_text(encoding="utf-8"))
        assert batch_manifest["case_id_prefix"] == prefix
        assert batch_manifest["case_count"] == count


def test_full_regression_inventory_is_complete_and_artifacts_exist() -> None:
    manifest_directories = {
        path.parent.relative_to(ROOT).as_posix()
        for path in (ROOT / "generated").glob("*/manifest.json")
        if path.parent.name != "type_upgrade_full_regression"
    }
    assert manifest_directories == set(EXPECTED_BATCHES)

    sql_count = sum(
        1
        for path in ROOT.glob("generated/**/*")
        if path.is_file() and (path.suffix == ".sql" or path.name.endswith(".sql.gz"))
    )
    assert sql_count == 2411

    for row in _inventory():
        if row["artifact_kind"] == "compressed_suite":
            assert (ROOT / row["artifact"]).is_file()
            assert row["output_policy"] == "NO_FAIL"
            assert row["stderr_policy"] == "PLANNED_NEGATIVE_ERRORS_ALLOWED"
        elif row["artifact_kind"] == "virtual_runner":
            assert (ROOT / row["artifact"]).is_file()
            assert row["output_policy"] == "RUNNER_ALL_PASS"
            assert row["stderr_policy"] == "RUNNER_EVIDENCE"
            assert row["expected_output"] == "-"
        else:
            assert row["artifact_kind"] == "sql_directory"
            assert list(ROOT.glob(row["artifact"]))
            assert row["output_policy"] == "EXACT_DIFF"
            assert row["stderr_policy"] == "MUST_BE_EMPTY"
            assert (ROOT / row["expected_output"]).is_file()


def test_full_regression_policy_is_documented_in_readme_and_docs() -> None:
    root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
    doc = (ROOT / "docs" / "type_upgrade_full_regression.md").read_text(encoding="utf-8")
    artifact_readme = (FULL / "README.md").read_text(encoding="utf-8")

    for text in (root_readme, doc, artifact_readme):
        assert "Selective regression" in text or "selective regression" in text
        assert "27 execution streams" in text or "27 execution units" in text
        assert "977,982" in text
        assert "2,932,994" in text
        for prefix in ("TUC", "TUCX", "TUCS", "TUCP", "TUCZ", "TUCPK", "TUCUI", "TUCFK", "TUCUD", "TUCVF"):
            assert prefix in text

    assert "docs/type_upgrade_full_regression.md" in root_readme
    assert "generated/type_upgrade_full_regression/inventory.tsv" in root_readme
    assert "generated/type_upgrade_full_regression/manifest.json" in root_readme
