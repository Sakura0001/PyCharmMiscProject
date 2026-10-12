from __future__ import annotations

import json
from pathlib import Path

import pytest

from mysql_case_factory.type_upgrade_consistency import (
    FORBIDDEN_TYPE_TOKENS,
    build_factor_catalog,
    generate_cases,
    render_suite,
    suite_manifest,
)


def test_factor_catalog_has_required_type_families_and_bit_widths() -> None:
    catalog = build_factor_catalog()

    integer_sources = {item.source_type for item in catalog.integer_transitions}
    assert {"TINYINT", "SMALLINT", "MEDIUMINT", "INT", "BIGINT"} <= integer_sources
    assert any(
        item.source_type == "SMALLINT" and item.target_type == "INT"
        for item in catalog.integer_transitions
    )
    assert any(
        item.source_type == "INT" and item.target_type == "BIGINT"
        for item in catalog.integer_transitions
    )

    assert len(catalog.bit_transitions) >= 20
    assert {1, 8, 11, 16, 31, 32, 33, 48, 63, 64} <= {
        item.source_width for item in catalog.bit_transitions
    } | {item.target_width for item in catalog.bit_transitions}

    assert len({item.scale for item in catalog.decimal_transitions}) >= 5
    assert all(item.target_type.endswith(f",{item.target_scale})") for item in catalog.decimal_transitions)

    assert any(
        item.source_type == "VARCHAR(255)" and item.target_type == "VARCHAR(256)"
        for item in catalog.character_transitions
    )
    assert any(
        item.source_type == "VARBINARY(255)" and item.target_type == "VARBINARY(256)"
        for item in catalog.binary_transitions
    )


def test_factor_catalog_excludes_removed_type_families() -> None:
    catalog = build_factor_catalog()
    serialized = json.dumps(catalog.to_json(), ensure_ascii=False)
    for token in FORBIDDEN_TYPE_TOKENS:
        assert token not in serialized


def test_generated_cases_are_unique_deterministic_and_bounded() -> None:
    first = generate_cases()
    second = generate_cases()

    assert 5_000 <= len(first) <= 100_000
    assert [case.case_id for case in first] == [case.case_id for case in second]
    assert len({case.case_id for case in first}) == len(first)
    assert first[0].case_id < first[-1].case_id
    assert all(case.expected_outcome in {"success", "reject"} for case in first)
    assert any(case.expected_outcome == "reject" for case in first)


def test_generated_cases_cover_required_factors_and_no_removed_types() -> None:
    cases = generate_cases()
    serialized = json.dumps([case.to_json() for case in cases], ensure_ascii=False)
    for token in FORBIDDEN_TYPE_TOKENS:
        assert token not in serialized

    clusters = {case.cluster for case in cases}
    assert {
        "integer_base",
        "decimal_base",
        "character_base",
        "binary_base",
        "bit_base",
        "column_attribute",
        "index",
        "foreign_key",
        "dependency",
        "table_form",
        "sql_mode",
    } <= clusters

    assert any("SMALLINT" in case.source_type and "INT" in case.target_type for case in cases)
    assert any("VARCHAR(255)" in case.source_type and "VARCHAR(256)" in case.target_type for case in cases)
    assert any("VARBINARY(255)" in case.source_type for case in cases)
    assert any("BIT(11)" in case.source_type and "BIT(64)" in case.target_type for case in cases)
    assert any(case.index_profile != "none" for case in cases)
    assert any(case.foreign_key_profile != "none" for case in cases)
    assert any(case.dependency_profile != "none" for case in cases)
    assert any(case.table_form != "ordinary" for case in cases)
    assert any(case.sql_mode != "STRICT_ALL_TABLES" for case in cases)


def test_render_suite_replaces_algorithm_and_contains_cleanup() -> None:
    cases = generate_cases()[:3]
    copy_sql = render_suite(cases, "copy")
    inplace_sql = render_suite(cases, "inplace")
    instant_sql = render_suite(cases, "instant")

    assert "ALGORITHM=COPY" in copy_sql
    assert "ALGORITHM=INPLACE" in inplace_sql
    assert "ALGORITHM=INSTANT" in instant_sql
    assert "ALGORITHM=${ALGORITHM}" not in copy_sql
    assert "DROP TABLE IF EXISTS" in copy_sql
    assert "SET foreign_key_checks=ON" in copy_sql


def test_suite_manifest_is_deterministic_and_profiles_match(tmp_path: Path) -> None:
    cases = generate_cases()
    manifest = suite_manifest(cases, "copy")
    repeat = suite_manifest(generate_cases(), "copy")

    assert manifest["profile"] == "copy"
    assert manifest["case_count"] == len(cases)
    assert manifest["sha256"] == repeat["sha256"]
    assert manifest["clusters"]
    assert manifest["forbidden_types_absent"] is True


def test_generate_type_upgrade_cases_tool_writes_deterministic_artifacts(tmp_path: Path) -> None:
    import subprocess
    import sys

    tool = Path(__file__).parents[1] / "tools" / "generate_type_upgrade_cases.py"
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
    }
    assert required <= {path.name for path in first.iterdir()}
    assert (first / "cases.jsonl.gz").read_bytes() == (second / "cases.jsonl.gz").read_bytes()
    assert (first / "copy_suite.sql.gz").read_bytes() == (second / "copy_suite.sql.gz").read_bytes()
    import gzip

    with gzip.open(first / "copy_suite.sql.gz", "rt", encoding="utf-8") as handle:
        copy_sql = handle.read()
    with gzip.open(first / "inplace_suite.sql.gz", "rt", encoding="utf-8") as handle:
        inplace_sql = handle.read()
    with gzip.open(first / "instant_suite.sql.gz", "rt", encoding="utf-8") as handle:
        instant_sql = handle.read()
    assert "ALGORITHM=COPY" in copy_sql
    assert "ALGORITHM=INPLACE" in inplace_sql
    assert "ALGORITHM=INSTANT" in instant_sql


def test_generated_cases_materialize_advanced_factors_in_sql() -> None:
    cases = generate_cases()
    by_attribute = {
        (case.family, case.column_attribute): case for case in cases if case.column_attribute in {"auto_increment", "first"}
    }
    assert ("integer", "auto_increment") in by_attribute
    assert any("AUTO_INCREMENT" in " ".join(case.setup_sql) for case in cases if case.column_attribute == "auto_increment")
    assert any("FIRST" in case.ddl_sql for case in cases if case.column_attribute == "first")

    assert any(case.index_profile == "functional" for case in cases)
    assert any(
        case.index_profile == "functional" and "((" in " ".join(case.setup_sql)
        for case in cases
    )
    assert any(case.index_profile == "generated" for case in cases)
    assert any(
        case.index_profile == "generated" and "GENERATED ALWAYS AS" in " ".join(case.setup_sql)
        for case in cases
    )

    fk_cases = [case for case in cases if case.foreign_key_profile != "none"]
    assert fk_cases
    assert all("FOREIGN KEY" in " ".join(case.post_ddl_sql) for case in fk_cases)
    assert all("REFERENCES" in " ".join(case.post_ddl_sql) for case in fk_cases)
    assert all("FOREIGN KEY" not in " ".join(case.setup_sql) for case in fk_cases)
    assert any("ON DELETE CASCADE" in " ".join(case.post_ddl_sql) for case in fk_cases)
    assert any("ON DELETE SET NULL" in " ".join(case.post_ddl_sql) for case in fk_cases)

    dependency_cases = [case for case in cases if case.dependency_profile != "none"]
    assert any("CREATE VIEW" in " ".join(case.setup_sql) for case in dependency_cases)
    assert any("CREATE TRIGGER" in " ".join(case.setup_sql) for case in dependency_cases)
    assert any("CREATE FUNCTION" in " ".join(case.setup_sql) for case in dependency_cases)
    assert any("CREATE PROCEDURE" in " ".join(case.setup_sql) for case in dependency_cases)
    assert any("PREPARE" in " ".join(case.post_ddl_sql) for case in dependency_cases)


def test_ddl_sql_has_separator_before_algorithm_clause() -> None:
    cases = generate_cases()
    assert all(", ALGORITHM=${ALGORITHM}" in case.ddl_sql for case in cases)


def test_unsigned_integer_seed_values_never_include_negative_values() -> None:
    catalog = build_factor_catalog()
    for transition in catalog.integer_transitions:
        if "UNSIGNED" in transition.source_type:
            assert "-1" not in transition.seed_values, transition


def test_decimal_boundary_values_fit_declared_precision() -> None:
    from mysql_case_factory.type_upgrade_consistency import _decimal_value

    assert _decimal_value(1, 0, 1) == "9"
    assert _decimal_value(1, 0, -1) == "-9"
    assert _decimal_value(4, 2, 1) == "99.99"
    assert _decimal_value(4, 2, -1) == "-99.99"


def test_character_column_definition_places_charset_before_nullability() -> None:
    from mysql_case_factory.type_upgrade_consistency import _column_definition

    definition = _column_definition("CHAR(1)", "nullable", "latin1", "latin1_swedish_ci", "character")
    assert definition == "CHAR(1) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL"


def test_char_types_do_not_exceed_mysql_maximum_length() -> None:
    catalog = build_factor_catalog()
    for transition in catalog.character_transitions:
        for type_name in (transition.source_type, transition.target_type):
            if type_name.startswith("CHAR("):
                length = int(type_name[5:-1])
                assert length <= 255, transition


def test_text_and_blob_columns_do_not_receive_constant_defaults() -> None:
    from mysql_case_factory.type_upgrade_consistency import _column_definition

    text = _column_definition("TINYTEXT", "not_null_default", "latin1", "latin1_swedish_ci", "character")
    blob = _column_definition("TINYBLOB", "not_null_default", None, None, "binary")
    assert "DEFAULT" not in text
    assert "DEFAULT" not in blob


def test_text_and_blob_invalid_values_respect_target_maximum() -> None:
    catalog = build_factor_catalog()
    for transition in (*catalog.character_transitions, *catalog.binary_transitions):
        if transition.target_type in {"LONGTEXT", "LONGBLOB"}:
            assert not transition.invalid_values, transition
        elif transition.target_type in {"MEDIUMTEXT", "MEDIUMBLOB"}:
            assert any("17000000" in value for value in transition.invalid_values), transition


def test_binary_literals_include_closing_quote() -> None:
    from mysql_case_factory.type_upgrade_consistency import _binary_values

    values = _binary_values(2)
    assert values[0] == "x'0000'"
    assert values[1] == "x'ffff'"
    assert values[-1] == "x'00ff'"


def test_binary_types_do_not_exceed_mysql_maximum_fixed_length() -> None:
    catalog = build_factor_catalog()
    for transition in catalog.binary_transitions:
        for type_name in (transition.source_type, transition.target_type):
            if type_name.startswith("BINARY("):
                length = int(type_name[7:-1])
                assert length <= 255, transition


def test_negative_transition_reference_table_keeps_old_type() -> None:
    cases = [case for case in generate_cases() if case.expected_outcome == "reject"]
    for case in cases:
        create_ref = next(statement for statement in case.setup_sql if statement.startswith("CREATE TABLE tuc_ref_"))
        assert case.source_type in create_ref, case


def test_negative_integer_transitions_always_narrow_type_rank() -> None:
    from mysql_case_factory.type_upgrade_consistency import _INTEGER_RANKS

    catalog = build_factor_catalog()
    for transition in catalog.integer_transitions:
        if not transition.positive:
            source = transition.source_type.split(" ")[0]
            target = transition.target_type.split(" ")[0]
            assert _INTEGER_RANKS[source] > _INTEGER_RANKS[target] or "UNSIGNED" in transition.target_type, transition


def test_all_decimal_cases_preserve_scale() -> None:
    catalog = build_factor_catalog()
    assert all(item.target_scale == item.scale for item in catalog.decimal_transitions)


def test_first_attribute_is_only_used_in_modify_ddl_not_create_table() -> None:
    cases = [case for case in generate_cases() if case.column_attribute == "first"]
    assert cases
    for case in cases:
        assert "FIRST" in case.ddl_sql
        assert all("FIRST" not in statement for statement in case.setup_sql if statement.startswith("CREATE TABLE")), case


def test_first_clause_is_not_duplicated_in_modify_ddl() -> None:
    for case in generate_cases():
        if case.column_attribute == "first":
            assert case.ddl_sql.count("FIRST") == 1, case


def test_first_attribute_reference_table_also_places_target_column_first() -> None:
    for case in generate_cases():
        if case.column_attribute == "first":
            create_ref = next(statement for statement in case.setup_sql if statement.startswith("CREATE TABLE tuc_ref_"))
            assert create_ref.index("target_col") < create_ref.index("id BIGINT"), case


def test_first_attribute_does_not_implicitly_change_nullability() -> None:
    from mysql_case_factory.type_upgrade_consistency import _column_definition

    definition = _column_definition("INT", "first", None, None, "integer")
    assert " NULL" in definition
    assert "NOT NULL" not in definition


def test_comment_and_invisible_attributes_do_not_implicitly_change_nullability() -> None:
    from mysql_case_factory.type_upgrade_consistency import _column_definition

    for attribute in ("comment", "invisible"):
        definition = _column_definition("INT", attribute, None, None, "integer")
        assert " NULL" in definition
        assert "NOT NULL" not in definition


def test_functional_index_expression_has_bounded_key_length() -> None:
    from mysql_case_factory.type_upgrade_consistency import _index_definitions

    indexes = _index_definitions("functional", "integer", "BIGINT")
    assert indexes == ("KEY idx_functional ((MD5(CAST(target_col AS CHAR))))",)


def test_generated_decimal_helper_column_uses_maximum_supported_precision() -> None:
    from mysql_case_factory.type_upgrade_consistency import _setup_statements

    case = next(case for case in generate_cases() if case.family == "decimal" and case.index_profile == "generated")
    assert any("DECIMAL(65,0) GENERATED ALWAYS AS" in statement for statement in case.setup_sql)


def test_unique_character_index_seed_and_post_values_are_collation_distinct() -> None:
    cases = [
        case
        for case in generate_cases()
        if case.family == "character" and case.index_profile == "unique"
    ]
    assert cases
    for case in cases:
        assert len({value.removeprefix("'").removesuffix("'").lower() for value in case.seed_values if value != "NULL"}) == len(
            [value for value in case.seed_values if value != "NULL"]
        ), case
        assert len({value.removeprefix("'").removesuffix("'").lower() for value in case.post_ddl_values if value != "NULL"}) == len(
            [value for value in case.post_ddl_values if value != "NULL"]
        ), case


def test_unique_character_index_full_key_fits_mysql_limit() -> None:
    bytes_per_char = {"latin1": 1, "ascii": 1, "utf8mb3": 3, "utf8mb4": 4}
    for case in generate_cases():
        if case.family == "character" and case.index_profile == "unique":
            source_length = int(case.source_type.split("(")[1].split(")")[0]) if "(" in case.source_type else 65535
            target_length = int(case.target_type.split("(")[1].split(")")[0]) if "(" in case.target_type else 65535
            multiplier = bytes_per_char[case.charset or "utf8mb4"]
            assert max(source_length, target_length) * multiplier <= 3072, case


def test_composite_character_index_including_helpers_fits_key_limit() -> None:
    bytes_per_char = {"latin1": 1, "ascii": 1, "utf8mb3": 3, "utf8mb4": 4}
    for case in generate_cases():
        if case.family == "character" and case.index_profile == "composite":
            target_length = int(case.target_type.split("(")[1].split(")")[0]) if "(" in case.target_type else 65535
            assert target_length * bytes_per_char[case.charset or "utf8mb4"] + 64 <= 3072, case


def test_unique_binary_index_post_values_do_not_collide_with_padded_seed_values() -> None:
    cases = [case for case in generate_cases() if case.family == "binary" and case.index_profile == "unique"]
    assert cases
    for case in cases:
        assert not any(value.startswith(("x'00", "x'ff", "x'01", "x'ab")) for value in case.post_ddl_values if value != "NULL"), case


def test_unique_bit_index_seed_and_post_values_are_distinct() -> None:
    cases = [case for case in generate_cases() if case.family == "bit" and case.index_profile == "unique"]
    assert cases
    for case in cases:
        seed = {value for value in case.seed_values if value != "NULL"}
        post = {value for value in case.post_ddl_values if value != "NULL"}
        assert len(seed) == len([value for value in case.seed_values if value != "NULL"]), case
        assert len(post) == len([value for value in case.post_ddl_values if value != "NULL"]), case
        assert not seed & post, case


def test_foreign_key_child_columns_use_upgraded_type() -> None:
    for case in generate_cases():
        if case.foreign_key_profile in {"parent", "cascade", "set_null", "restrict", "no_action"}:
            child_create = next(
                statement for statement in case.post_ddl_sql if statement.startswith("CREATE TABLE tuc_fk_child_algo_")
            )
            assert case.target_type in child_create, case


def test_foreign_key_reference_and_algorithm_sides_use_matching_initial_types() -> None:
    for case in generate_cases():
        if case.foreign_key_profile in {"parent", "cascade", "set_null", "restrict", "no_action"}:
            ref_child = next(s for s in case.post_ddl_sql if s.startswith("CREATE TABLE tuc_fk_child_ref_"))
            algo_child = next(s for s in case.post_ddl_sql if s.startswith("CREATE TABLE tuc_fk_child_algo_"))
            assert case.target_type in ref_child, case
            assert case.target_type in algo_child, case
        if case.foreign_key_profile == "child":
            ref_parent = next(s for s in case.post_ddl_sql if s.startswith("CREATE TABLE tuc_fk_parent_ref_"))
            algo_parent = next(s for s in case.post_ddl_sql if s.startswith("CREATE TABLE tuc_fk_parent_algo_"))
            assert case.target_type in ref_parent, case
            assert case.target_type in algo_parent, case


def test_child_foreign_key_cleanup_drops_referencing_table_before_parent() -> None:
    for case in generate_cases():
        if case.foreign_key_profile == "child":
            parent_drops = [
                index for index, statement in enumerate(case.cleanup_sql) if "tuc_fk_parent_algo_" in statement
            ]
            algo_drop = next(index for index, statement in enumerate(case.cleanup_sql) if statement == "DROP TABLE IF EXISTS tuc_algo_" + case.case_id.split("-")[-1].lstrip("0") or f"tuc_algo_{int(case.case_id.split('-')[-1])}" in statement)
            assert parent_drops[0] > algo_drop, case


def test_self_reference_parent_id_is_added_after_type_upgrade() -> None:
    for case in generate_cases():
        if case.foreign_key_profile == "self_reference":
            assert all("parent_id" not in statement for statement in case.setup_sql if statement.startswith("CREATE TABLE")), case
            assert any("ADD COLUMN parent_id" in statement for statement in case.post_ddl_sql), case


def test_character_foreign_key_columns_use_matching_charset_and_collation() -> None:
    for case in generate_cases():
        if case.family == "character" and case.foreign_key_profile != "none":
            joined = " ".join(case.post_ddl_sql)
            assert f"CHARACTER SET {case.charset}" in joined, case
            assert f"COLLATE {case.collation}" in joined, case


def test_foreign_key_child_inserts_skip_null_parent_values() -> None:
    for case in generate_cases():
        if case.foreign_key_profile in {"parent", "cascade", "set_null", "restrict", "no_action", "composite", "child"}:
            inserts = [s for s in case.post_ddl_sql if s.startswith("INSERT INTO tuc_fk_")]
            assert inserts
            assert all("WHERE target_col IS NOT NULL" in statement for statement in inserts), case
            if case.foreign_key_profile != "child":
                assert all("parent_id" not in statement or "NOT NULL" not in statement.split("parent_id", 1)[1].split(",", 1)[0] for statement in case.post_ddl_sql if statement.startswith("CREATE TABLE")), case


def test_dependency_view_exposes_all_columns_used_by_data_oracle() -> None:
    for case in generate_cases():
        if case.dependency_profile == "view":
            assert any("CREATE VIEW" in statement and "SELECT id, target_col, part_key" in statement for statement in case.setup_sql), case


def test_function_result_oracle_compares_value_columns() -> None:
    for case in generate_cases():
        if case.dependency_profile == "function_read":
            function_check = next(statement for statement in case.verify_sql if "tuc_fn_result_ref_" in statement)
            assert "r.value" in function_check and "a.value" in function_check, case
            assert "r.op" not in function_check, case


def test_procedure_write_uses_type_literal_instead_of_invalid_cast() -> None:
    for case in generate_cases():
        if case.dependency_profile == "procedure_write":
            procedure = next(statement for statement in case.setup_sql if statement.startswith("CREATE PROCEDURE"))
            assert "CAST(p_value AS" not in procedure, case
            assert "VALUES (p_id, " in procedure, case


def test_prepared_statement_embeds_type_literal_without_invalid_cast() -> None:
    for case in generate_cases():
        if case.dependency_profile == "prepared_statement":
            prepare = next(statement for statement in case.post_ddl_sql if statement.startswith("PREPARE "))
            assert "CAST(@tuc_value" not in prepare, case
            assert "VALUES (302, ?" in prepare, case


def test_function_result_table_allows_null_target_values() -> None:
    for case in generate_cases():
        if case.dependency_profile == "function_read":
            create = next(statement for statement in case.setup_sql if statement.startswith("CREATE TABLE tuc_fn_result_ref_"))
            assert "value MEDIUMTEXT NULL" in create, case


def test_dependency_cluster_does_not_create_overlong_full_key_indexes() -> None:
    bytes_per_char = {"latin1": 1, "ascii": 1, "utf8mb3": 3, "utf8mb4": 4}
    for case in generate_cases():
        if case.cluster == "dependency" and case.family == "character":
            length = int(case.target_type.split("(")[1].split(")")[0]) if "(" in case.target_type else 65535
            if length * bytes_per_char[case.charset or "utf8mb4"] > 2816:
                assert case.index_profile == "prefix", case


def test_trigger_audit_columns_can_hold_long_text_values() -> None:
    for case in generate_cases():
        if case.dependency_profile in {"trigger_insert", "trigger_update"}:
            create = next(statement for statement in case.setup_sql if statement.startswith("CREATE TABLE tuc_audit_ref_"))
            assert "old_value MEDIUMTEXT" in create, case
            assert "new_value MEDIUMTEXT" in create, case


def test_function_return_and_result_columns_can_hold_long_text_values() -> None:
    for case in generate_cases():
        if case.dependency_profile == "function_read":
            function = next(statement for statement in case.setup_sql if statement.startswith("CREATE FUNCTION tuc_fn_ref_"))
            create = next(statement for statement in case.setup_sql if statement.startswith("CREATE TABLE tuc_fn_result_ref_"))
            assert "RETURNS MEDIUMTEXT" in function, case
            assert "value MEDIUMTEXT" in create, case


def test_procedure_parameter_can_hold_long_text_values() -> None:
    for case in generate_cases():
        if case.dependency_profile == "procedure_write":
            procedure = next(statement for statement in case.setup_sql if statement.startswith("CREATE PROCEDURE"))
            assert "p_value MEDIUMTEXT" in procedure, case


def test_temporary_table_oracle_uses_persistent_snapshots() -> None:
    for case in generate_cases():
        if case.table_form == "temporary":
            joined_post = " ".join(case.post_ddl_sql)
            assert "CREATE TABLE tuc_meta_ref_" in joined_post, case
            assert "CREATE TABLE tuc_meta_algo_" in joined_post, case
            assert "CREATE TABLE tuc_data_ref_" in joined_post, case
            assert "CREATE TABLE tuc_data_algo_" in joined_post, case
            schema_check = case.verify_sql[0]
            data_check = case.verify_sql[1]
            assert "tuc_meta_ref_" in schema_check and "tuc_meta_algo_" in schema_check, case
            assert "tuc_data_ref_" in data_check and "tuc_data_algo_" in data_check, case


def test_partitioned_tables_primary_key_includes_partition_key() -> None:
    partition_forms = {"range_partition", "list_partition", "hash_partition", "key_partition"}
    for case in generate_cases():
        if case.table_form in partition_forms:
            create_algo = next(statement for statement in case.setup_sql if statement.startswith("CREATE TABLE tuc_algo_"))
            assert "PRIMARY KEY (id,part_key)" in create_algo, case


def test_instant_history_reference_table_has_history_column() -> None:
    for case in generate_cases():
        if case.table_form == "instant_history":
            assert any("ALTER TABLE tuc_ref_" in statement and "instant_history_col" in statement for statement in case.setup_sql), case
            assert any("ALTER TABLE tuc_algo_" in statement and "ALGORITHM=INSTANT" in statement for statement in case.setup_sql), case


def test_pad_char_mode_only_applies_to_same_character_kind_transitions() -> None:
    for case in generate_cases():
        if case.sql_mode == "PAD_CHAR_TO_FULL_LENGTH":
            assert case.family != "character" or (case.source_type.startswith("CHAR") and case.target_type.startswith("CHAR")) or (case.source_type.startswith("VARCHAR") and case.target_type.startswith("VARCHAR")), case


def test_manifest_records_compressed_artifact_hashes_and_sizes() -> None:
    import hashlib

    tool_output = Path(__file__).parents[1] / "generated" / "type_upgrade_consistency"
    manifest = json.loads((tool_output / "manifest.json").read_text(encoding="utf-8"))
    assert "artifacts" in manifest
    for name in (
        "cases.jsonl.gz",
        "copy_suite.sql.gz",
        "inplace_suite.sql.gz",
        "instant_suite.sql.gz",
        "coverage.tsv",
    ):
        payload = (tool_output / name).read_bytes()
        assert manifest["artifacts"][name]["sha256"] == hashlib.sha256(payload).hexdigest()
        assert manifest["artifacts"][name]["bytes"] == len(payload)


def test_expression_defaults_are_materialized() -> None:
    cases = [case for case in generate_cases() if case.column_attribute == "expression_default"]
    assert cases
    assert all("DEFAULT (" in " ".join(case.setup_sql) for case in cases), cases[0]
    assert all("DEFAULT (" in case.ddl_sql for case in cases), cases[0]


def test_all_six_trigger_timing_and_event_combinations_exist() -> None:
    expected = {
        "trigger_before_insert",
        "trigger_after_insert",
        "trigger_before_update",
        "trigger_after_update",
        "trigger_before_delete",
        "trigger_after_delete",
    }
    actual = {case.dependency_profile for case in generate_cases()}
    assert expected <= actual
    for profile in expected:
        cases = [case for case in generate_cases() if case.dependency_profile == profile]
        assert cases
        assert all("CREATE TRIGGER" in " ".join(case.setup_sql) for case in cases)
        assert all("tuc_audit_ref_" in " ".join(case.verify_sql) for case in cases)


def test_multi_level_foreign_key_chain_is_materialized() -> None:
    cases = [case for case in generate_cases() if case.foreign_key_profile == "multi_level"]
    assert cases
    for case in cases:
        post_sql = " ".join(case.post_ddl_sql)
        assert post_sql.count("FOREIGN KEY") >= 4, case
        assert "tuc_fk_level1_ref_" in post_sql and "tuc_fk_level2_ref_" in post_sql, case
        assert "tuc_fk_level1_algo_" in post_sql and "tuc_fk_level2_algo_" in post_sql, case
        cleanup = list(case.cleanup_sql)
        level2 = next(index for index, statement in enumerate(cleanup) if "tuc_fk_level2_algo_" in statement)
        level1 = next(index for index, statement in enumerate(cleanup) if "tuc_fk_level1_algo_" in statement)
        algo = next(index for index, statement in enumerate(cleanup) if "tuc_algo_" in statement)
        assert level2 < level1 < algo, case


def test_numeric_spelling_is_covered() -> None:
    cases = [case for case in generate_cases() if case.family == "decimal"]
    assert any(case.source_type.startswith("NUMERIC(") for case in cases)
    assert any(case.target_type.startswith("NUMERIC(") for case in cases)
    assert any(case.source_type.startswith("DECIMAL(") and case.target_type.startswith("NUMERIC(") for case in cases)
    assert any(case.source_type.startswith("NUMERIC(") and case.target_type.startswith("DECIMAL(") for case in cases)


def test_index_and_foreign_key_oracles_compare_full_definitions() -> None:
    cases = generate_cases()
    index_case = next(case for case in cases if case.index_profile != "none")
    assert any("information_schema.statistics" in statement for statement in index_case.verify_sql)

    fk_case = next(case for case in cases if case.foreign_key_profile != "none")
    fk_verify = " ".join(fk_case.verify_sql)
    for token in (
        "information_schema.referential_constraints",
        "information_schema.key_column_usage",
        "constraint_name",
        "referenced_column_name",
        "delete_rule",
        "update_rule",
    ):
        assert token in fk_verify, token


def test_prefix_indexes_use_a_length_strictly_smaller_than_source_column() -> None:
    for case in generate_cases():
        if case.index_profile == "prefix":
            create = next(statement for statement in case.setup_sql if statement.startswith("CREATE TABLE tuc_algo_"))
            assert "target_col(" in create, case
            if case.source_type.startswith(("CHAR(", "VARCHAR(", "BINARY(", "VARBINARY(")):
                source_length = int(case.source_type.split("(", 1)[1].split(")", 1)[0])
                assert source_length > 1, case
                prefix_length = int(create.split("target_col(", 1)[1].split(")", 1)[0])
                assert prefix_length < source_length, case


def test_foreign_key_oracle_compares_actual_constraint_tables() -> None:
    cases = generate_cases()
    parent_case = next(
        case for case in cases if case.foreign_key_profile in {"parent", "cascade", "set_null", "restrict", "no_action"}
    )
    parent_fk_checks = [statement for statement in parent_case.verify_sql if "referential_constraints" in statement]
    assert parent_fk_checks
    assert any("tuc_fk_child_ref_" in statement and "tuc_fk_child_algo_" in statement for statement in parent_fk_checks), parent_case
    assert any(
        "tuc_fk_child_ref_" in statement and "tuc_fk_child_algo_" in statement
        for statement in parent_case.verify_sql
        if "information_schema.statistics" in statement
    ), parent_case

    multi_case = next(case for case in cases if case.foreign_key_profile == "multi_level")
    multi_fk_checks = [statement for statement in multi_case.verify_sql if "referential_constraints" in statement]
    assert multi_fk_checks
    assert any("tuc_fk_level1_ref_" in statement and "tuc_fk_level1_algo_" in statement for statement in multi_fk_checks), multi_case
    assert any("tuc_fk_level2_ref_" in statement and "tuc_fk_level2_algo_" in statement for statement in multi_fk_checks), multi_case
    assert any("referenced_column_name" in statement and "ordinal_position" in statement for statement in multi_fk_checks), multi_case
    assert any(
        "tuc_fk_level1_ref_" in statement and "tuc_fk_level1_algo_" in statement
        for statement in multi_case.verify_sql
        if "information_schema.statistics" in statement
    ), multi_case
    assert any(
        "tuc_fk_level2_ref_" in statement and "tuc_fk_level2_algo_" in statement
        for statement in multi_case.verify_sql
        if "information_schema.statistics" in statement
    ), multi_case
