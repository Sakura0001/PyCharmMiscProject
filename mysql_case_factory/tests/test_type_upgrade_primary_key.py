from __future__ import annotations

import gzip
import json
import subprocess
import sys
from pathlib import Path

from mysql_case_factory.type_upgrade_primary_key import (
    PRIMARY_KEY_BATCH_ID,
    PRIMARY_KEY_BATCH_KIND,
    PRIMARY_KEY_CASE_PREFIX,
    PRIMARY_KEY_DATABASE,
    PRIMARY_KEY_PROFILES,
    iter_primary_key_scenarios,
    primary_key_transitions,
    smoke_primary_key_scenarios,
)


def test_primary_key_batch_identity_and_transition_scale() -> None:
    assert PRIMARY_KEY_BATCH_ID == "2026-10-19-type-upgrade-primary-key-concurrency-v1"
    assert PRIMARY_KEY_BATCH_KIND == "primary_key_concurrency_extension"
    assert PRIMARY_KEY_CASE_PREFIX == "TUCPK"
    assert PRIMARY_KEY_DATABASE == "qa_type_upgrade_primary_key"
    assert PRIMARY_KEY_PROFILES == ("copy", "inplace", "instant")

    transitions = primary_key_transitions()
    assert len(transitions) == 107
    counts: dict[str, int] = {}
    for transition in transitions:
        counts[transition.family] = counts.get(transition.family, 0) + 1
    assert counts == {
        "integer": 45,
        "decimal": 14,
        "bit": 10,
        "character": 12,
        "binary": 14,
        "text": 6,
        "blob": 6,
    }


def test_primary_key_type_matrix_contains_required_boundaries() -> None:
    transitions = primary_key_transitions()
    sources = {transition.source_type for transition in transitions}
    targets = {transition.target_type for transition in transitions}

    assert {
        "TINYINT",
        "TINYINT UNSIGNED",
        "SMALLINT",
        "SMALLINT UNSIGNED",
        "MEDIUMINT",
        "MEDIUMINT UNSIGNED",
        "INT",
        "INT UNSIGNED",
        "BIGINT",
    } <= sources
    assert "BIGINT UNSIGNED" in targets

    assert {
        "DECIMAL(1,0)",
        "DECIMAL(64,0)",
        "DECIMAL(63,30)",
        "NUMERIC(18,6)",
        "BIT(1)",
        "BIT(63)",
        "CHAR(16)",
        "CHAR(255)",
        "VARCHAR(16)",
        "VARCHAR(255)",
        "VARCHAR(2047)",
        "BINARY(16)",
        "BINARY(255)",
        "VARBINARY(2047)",
        "TINYTEXT",
        "MEDIUMTEXT",
        "LONGTEXT",
        "TINYBLOB",
        "MEDIUMBLOB",
        "LONGBLOB",
    } <= sources | targets

    assert any(t.source_type == "INT" and t.target_type == "BIGINT" for t in transitions)
    assert any(t.source_type == "VARCHAR(255)" and t.target_type == "VARCHAR(256)" for t in transitions)
    assert any(t.source_type == "CHAR(255)" and t.target_type == "VARCHAR(256)" for t in transitions)
    assert any(t.source_type == "TINYTEXT" and t.target_type == "TEXT" for t in transitions)
    assert any(t.source_type == "MEDIUMBLOB" and t.target_type == "LONGBLOB" for t in transitions)


def test_primary_key_scenario_space_is_exact_lazy_and_deterministic() -> None:
    scenarios = iter_primary_key_scenarios()
    first = next(scenarios)
    assert first.case_id == "TUCPK-000001"
    assert not first.smoke
    assert first.insert_style in {
        "omit_pk_explicit_columns",
        "null_pk_positional",
        "insert_select_omit_pk",
        "multi_row_omit_pk",
    }

    count = 0
    last = None
    for scenario in iter_primary_key_scenarios():
        last = scenario
        count += 1
    assert count == 946_944
    assert last is not None
    assert last.case_id == "TUCPK-946944"

    assert [s.case_id for s in smoke_primary_key_scenarios()] == [
        s.case_id for s in smoke_primary_key_scenarios()
    ]


def test_unsigned_integer_ranges_use_unsigned_maxima() -> None:
    from mysql_case_factory.type_upgrade_primary_key_runner import _integer_range

    assert _integer_range("TINYINT UNSIGNED") == (0, 255)
    assert _integer_range("SMALLINT UNSIGNED") == (0, 65535)
    assert _integer_range("MEDIUMINT UNSIGNED") == (0, 16777215)
    assert _integer_range("INT UNSIGNED") == (0, 4294967295)
    assert _integer_range("BIGINT UNSIGNED") == (0, 18446744073709551615)


def test_primary_key_algorithm_expectations_and_pk_prefix_semantics() -> None:
    for scenario in iter_primary_key_scenarios():
        if scenario.family == "character":
            if scenario.length_boundary in {"pre_256", "post_256"}:
                assert scenario.instant_expected is False
            else:
                assert scenario.length_boundary == "cross_256"
                assert scenario.instant_expected is True
        else:
            assert scenario.instant_expected is True
        assert scenario.inplace_expected is True

        if scenario.family in {"text", "blob"}:
            assert scenario.pk_prefix_length == 32
        else:
            assert scenario.pk_prefix_length is None

        if scenario.family == "integer":
            assert scenario.auto_increment is True
        else:
            assert scenario.auto_increment is False


def test_primary_key_smoke_has_one_scenario_per_transition_and_known_bug_path() -> None:
    smoke = smoke_primary_key_scenarios()
    assert len(smoke) == 107
    assert len({scenario.transition_key for scenario in smoke}) == 107
    assert all(scenario.phase == "during_ddl" for scenario in smoke)
    assert all(scenario.workers == 4 for scenario in smoke)
    assert all(scenario.row_format == "DYNAMIC" for scenario in smoke)
    assert all(scenario.key_shape == "single_pk" for scenario in smoke)
    assert all(scenario.case_id.startswith("TUCPKS-") for scenario in smoke)

    integer_smoke = [scenario for scenario in smoke if scenario.family == "integer"]
    assert integer_smoke
    assert all(scenario.insert_style == "omit_pk_explicit_columns" for scenario in integer_smoke)


def test_primary_key_generator_writes_deterministic_virtual_artifacts(tmp_path: Path) -> None:
    tool = Path(__file__).parents[1] / "tools" / "generate_type_upgrade_primary_key.py"
    first = tmp_path / "first"
    second = tmp_path / "second"
    for output in (first, second):
        subprocess.run(
            [sys.executable, str(tool), "--output", str(output)],
            check=True,
            cwd=Path(__file__).parents[1],
        )

    manifest = json.loads((first / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["batch_id"] == PRIMARY_KEY_BATCH_ID
    assert manifest["scenario_count"] == 946_944
    assert manifest["transition_count"] == 107
    assert manifest["profile_counts"] == {profile: 946_944 for profile in PRIMARY_KEY_PROFILES}
    assert manifest["smoke_case_count"] == 107
    assert manifest["materialization"] == "virtual_lazy_runner"
    assert manifest["forbidden_types_absent"] is True

    with gzip.open(first / "smoke_cases.jsonl.gz", "rt", encoding="utf-8") as handle:
        smoke = [json.loads(line) for line in handle]
    assert len(smoke) == 107
    assert all(case["case_id"].startswith("TUCPKS-") for case in smoke)

    for name in ("manifest.json", "smoke_cases.jsonl.gz", "coverage.tsv", "README.md"):
        assert (first / name).read_bytes() == (second / name).read_bytes()
