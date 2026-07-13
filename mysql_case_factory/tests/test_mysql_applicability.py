from __future__ import annotations

from pathlib import Path

from mysql_case_factory.applicability import (
    applicability_axis_id,
    load_edition_applicability_universe,
    stable_catalog_row_id,
)


ROOT = Path(__file__).resolve().parents[1]


def test_applicability_ids_are_stable_and_mysql_neutral() -> None:
    assert stable_catalog_row_id("create_table", "table_kind", "temporary") == stable_catalog_row_id(
        "create_table", "table_kind", "temporary"
    )
    assert stable_catalog_row_id("create_table", "table_kind", "temporary").startswith("sfv-")
    assert applicability_axis_id("create_table") == "applicability_row__create_table"


def test_applicability_ids_reject_unsafe_statement_keys() -> None:
    try:
        applicability_axis_id("../escape")
    except ValueError as exc:
        assert "statement key" in str(exc)
    else:
        raise AssertionError("unsafe statement key was accepted")


def test_each_edition_loads_its_own_closed_applicability_universe() -> None:
    universe_22 = load_edition_applicability_universe(ROOT / "editions/mysql_8_0_22")
    universe_41 = load_edition_applicability_universe(ROOT / "editions/mysql_8_0_41")
    assert universe_22.counts.statements == universe_41.counts.statements == 112
    assert universe_22.counts.statement_factor_values == 1365
    assert universe_41.counts.statement_factor_values == 1389
    assert universe_22.semantic_sha256 != universe_41.semantic_sha256
