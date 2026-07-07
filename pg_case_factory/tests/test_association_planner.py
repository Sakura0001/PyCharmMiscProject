from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pg_case_factory.association_planner import (
    build_factor_profiles,
    infer_semantic_tags,
    load_markdown_yaml,
    load_yaml_file,
    plan_associations,
)


def test_load_yaml_helpers_return_mapping_configs(tmp_path):
    yaml_path = tmp_path / "matrix.yaml"
    yaml_path.write_text("kind: statement_combination_matrix\nstatement:\n  key: demo\n", encoding="utf-8")
    markdown_path = tmp_path / "statement.md"
    markdown_path.write_text(
        """
        # Demo

        ```yaml
        structured_config:
          kind: statement
          statement:
            key: demo
        ```
        """,
        encoding="utf-8",
    )

    assert load_yaml_file(yaml_path)["statement"]["key"] == "demo"
    assert load_markdown_yaml(markdown_path) == {
        "kind": "statement",
        "statement": {"key": "demo"},
    }


def test_public_api_exports_from_package():
    import pg_case_factory

    assert pg_case_factory.infer_semantic_tags is infer_semantic_tags
    assert pg_case_factory.build_factor_profiles is build_factor_profiles
    assert pg_case_factory.plan_associations is plan_associations


def test_infer_semantic_tags_for_column_type_factor():
    tags = infer_semantic_tags(
        "data_type",
        {"label": "列数据类型", "values": ["integer", "jsonb"]},
    )

    assert "column_type" in tags
    assert "method_compatibility_sensitive" in tags


def test_infer_semantic_tags_for_transaction_factor():
    tags = infer_semantic_tags(
        "concurrently",
        {"label": "CONCURRENTLY", "values": ["false", "true"]},
    )

    assert "transaction_sensitive" in tags
    assert "locking_sensitive" in tags


def test_build_factor_profiles_includes_values_labels_and_semantic_tags():
    profiles = build_factor_profiles(
        {
            "factors": {
                "expected_status": {"label": "预期结果", "values": ["success", "failure"]},
                "data_profile": {"label": "数据分布", "values": ["empty", "duplicates"]},
            }
        }
    )

    assert profiles["expected_status"]["label"] == "预期结果"
    assert profiles["expected_status"]["values"] == ("success", "failure")
    assert "negative_control" in profiles["expected_status"]["semantic_tags"]
    assert "data_profile" in profiles["data_profile"]["semantic_tags"]


def test_plan_associations_generates_generic_scenario_families_from_source_facts():
    statement_config = {
        "statement": {"key": "example_statement", "name": "EXAMPLE STATEMENT"},
        "factors": {
            "target_relation_kind": {"label": "目标关系类型", "values": ["table", "view"]},
            "data_type": {"label": "列数据类型", "values": ["integer", "jsonb"]},
            "data_profile": {"label": "数据分布", "values": ["empty", "duplicates"]},
            "concurrently": {"label": "CONCURRENTLY", "values": ["false", "true"]},
            "statistics_state": {"label": "统计信息状态", "values": ["fresh", "stale"]},
            "dependency_state": {"label": "依赖对象状态", "values": ["present", "dropped"]},
            "expected_status": {"label": "预期结果", "values": ["success", "failure"]},
        },
    }
    matrix_config = {
        "coverage_scope": {
            "target_relation_coverage": {
                "required": True,
                "coverage_mode": "representative",
                "required_kinds": ["ordinary_table", "partitioned_table"],
            },
            "column_type_coverage": {
                "required": True,
                "coverage_mode": "representative",
                "required_type_set": "planner_fixture_types",
            },
        },
        "factor_contract": {
            "factors": {
                "method": {
                    "tier": "T1",
                    "coverage_role": "main_axis",
                    "required_values": ["btree", "hash"],
                    "coverage_requirement": "all_values",
                }
            }
        },
        "combination_groups": [
            {
                "id": "reject_view",
                "default_expected_status": "failure",
                "factors": {"expected_status": "failure"},
            }
        ],
    }
    type_catalog_config = {
        "type_sets": {
            "planner_fixture_types": {
                "types": ["integer", "jsonb"],
            }
        },
        "types": {
            "integer": {"type_category": "numeric", "declaration_sql": "INTEGER"},
            "jsonb": {"type_category": "json", "declaration_sql": "JSONB"},
        },
    }
    coverage_inventory = {
        "negative_controls": [
            {"id": "unsupported_relation", "reason": "relation kind is unsupported"}
        ]
    }

    plan = plan_associations(
        statement_config=statement_config,
        matrix_config=matrix_config,
        type_catalog_config=type_catalog_config,
        coverage_inventory=coverage_inventory,
    )

    assert plan["kind"] == "factor_association_plan"
    assert plan["target_statement"] == {
        "key": "example_statement",
        "name": "EXAMPLE STATEMENT",
    }
    assert plan["association_model"]["mode"] == "hybrid_rule_first"
    assert set(plan["factor_profiles"]) == set(statement_config["factors"])

    family_ids = {family["id"] for family in plan["scenario_families"]}
    assert {
        "relation_kind_matrix",
        "column_type_matrix",
        "data_profile_matrix",
        "schema_mutation_lifecycle",
        "transaction_concurrency_matrix",
        "optimizer_statistics_matrix",
        "negative_control_matrix",
    }.issubset(family_ids)
    for family in plan["scenario_families"]:
        assert family["trigger_facts"]["sources"], family["id"]

    column_family = next(
        family for family in plan["scenario_families"] if family["id"] == "column_type_matrix"
    )
    assert column_family["trigger_facts"]["types"] == ["integer", "jsonb"]
    assert column_family["trigger_facts"]["sources"] == [
        "combination_matrix.coverage_scope.column_type_coverage",
        "type_catalog.type_sets.planner_fixture_types",
    ]
    assert column_family["lifecycle"] == ["setup", "target_statement", "verification", "cleanup"]
    assert column_family["why"]

    obligation_ids = {obligation["id"] for obligation in plan["coverage_obligations"]}
    assert "cover_column_type_matrix" in obligation_ids
    assert "cover_negative_control_matrix" in obligation_ids
    assert "cover_factor_contract_method" in obligation_ids


def test_plan_associations_uses_statement_only_relation_and_type_factors_without_matrix():
    plan = plan_associations(
        statement_config={
            "statement": {"key": "new_statement", "name": "NEW STATEMENT"},
            "factors": {
                "target_relation_kind": {
                    "label": "目标关系类型",
                    "values": ["regular_table", "plain_view"],
                },
                "data_type": {
                    "label": "列数据类型",
                    "values": ["integer", "jsonb"],
                },
            },
        }
    )

    families = {family["id"]: family for family in plan["scenario_families"]}
    assert families["relation_kind_matrix"]["trigger_facts"]["factors"] == ["target_relation_kind"]
    assert families["relation_kind_matrix"]["trigger_facts"]["sources"] == [
        "statement_reference.factors.target_relation_kind",
    ]
    assert families["column_type_matrix"]["trigger_facts"]["factors"] == ["data_type"]
    assert families["column_type_matrix"]["trigger_facts"]["sources"] == [
        "statement_reference.factors.data_type",
    ]


def test_plan_associations_turns_factor_contract_into_baseline_obligations():
    plan = plan_associations(
        statement_config={
            "statement": {"key": "contract_statement", "name": "CONTRACT STATEMENT"},
            "factors": {
                "method": {"label": "method", "values": ["btree", "hash"]},
                "expected_status": {"label": "预期结果", "values": ["success", "failure"]},
            },
        },
        matrix_config={
            "factor_contract": {
                "factors": {
                    "method": {
                        "tier": "T1",
                        "coverage_role": "main_axis",
                        "required_values": ["btree", "hash"],
                        "coverage_requirement": "all_values",
                    }
                }
            }
        },
    )

    method_obligation = next(
        obligation
        for obligation in plan["coverage_obligations"]
        if obligation["id"] == "cover_factor_contract_method"
    )
    assert method_obligation["required_values"] == ["btree", "hash"]
    assert method_obligation["source"] == "combination_matrix.factor_contract.factors.method"
