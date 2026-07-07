from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Optional

import yaml


YAML_BLOCK_PATTERN = re.compile(r"```yaml\s*(.*?)```", re.DOTALL)

TAG_ORDER = (
    "column_type",
    "method_compatibility_sensitive",
    "relation_kind",
    "data_profile",
    "schema_mutation",
    "dependency_state",
    "privilege_environment",
    "transaction_sensitive",
    "locking_sensitive",
    "optimizer_sensitive",
    "negative_control",
    "oracle",
)


def load_markdown_yaml(path: Path) -> dict:
    """Load the first fenced yaml block from a markdown reference."""
    raw_text = path.read_text(encoding="utf-8")
    match = YAML_BLOCK_PATTERN.search(raw_text)
    if not match:
        raise ValueError(f"{path}: no fenced yaml block found")
    parsed = yaml.safe_load(match.group(1)) or {}
    if not isinstance(parsed, Mapping):
        raise ValueError(f"{path}: fenced yaml block must be a mapping")
    config = parsed.get("structured_config", parsed)
    if not isinstance(config, Mapping):
        raise ValueError(f"{path}: structured_config must be a mapping")
    return dict(config)


def load_yaml_file(path: Path) -> dict:
    """Load a yaml file as a mapping."""
    parsed = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(parsed, Mapping):
        raise ValueError(f"{path}: yaml must be a mapping")
    return dict(parsed)


def infer_semantic_tags(factor_name: str, factor_doc: dict) -> tuple[str, ...]:
    """Infer stable semantic tags from factor metadata."""
    doc = _as_mapping(factor_doc)
    name = str(factor_name)
    label = str(doc.get("label") or "")
    values = [_value_key(value) for value in _as_sequence(doc.get("values"))]
    text = _search_text([name, label, *values])
    tags: set[str] = set()

    if _has_any(
        text,
        (
            "data_type",
            "column_type",
            "type_name",
            "type_category",
            "col_type",
            "数据类型",
            "列类型",
            "integer",
            "jsonb",
            "uuid",
        ),
    ):
        tags.add("column_type")
        tags.add("method_compatibility_sensitive")

    if _has_any(
        text,
        (
            "relation_kind",
            "target_relation",
            "table_kind",
            "object_kind",
            "target_object",
            "relation_type",
            "关系类型",
            "对象类型",
            "table",
            "view",
            "sequence",
            "foreign_table",
            "partitioned_table",
        ),
    ):
        tags.add("relation_kind")

    if _has_any(
        text,
        (
            "data_profile",
            "data_size",
            "row_count",
            "cardinality",
            "null",
            "duplicate",
            "duplicates",
            "empty",
            "large",
            "small",
            "数据分布",
            "数据量",
            "空值",
            "重复",
        ),
    ):
        tags.add("data_profile")

    if _has_any(
        text,
        (
            "schema_mutation",
            "lifecycle",
            "schema_state",
            "object_state",
            "altered",
            "renamed",
            "dropped",
            "recreated",
            "attach",
            "detach",
            "模式变更",
            "生命周期",
        ),
    ):
        tags.add("schema_mutation")

    if _has_any(
        text,
        (
            "dependency",
            "dependent",
            "referenced",
            "constraint_state",
            "依赖",
            "引用",
        ),
    ):
        tags.add("dependency_state")

    if _has_any(
        text,
        (
            "privilege",
            "permission",
            "owner",
            "role",
            "authorization",
            "grant",
            "revoke",
            "权限",
            "所有者",
            "角色",
        ),
    ):
        tags.add("privilege_environment")

    if _has_any(
        text,
        (
            "transaction",
            "concurrently",
            "concurrent",
            "isolation",
            "autocommit",
            "commit",
            "rollback",
            "savepoint",
            "事务",
            "并发",
        ),
    ):
        tags.add("transaction_sensitive")

    if _has_any(
        text,
        (
            "lock",
            "locking",
            "concurrently",
            "concurrent",
            "blocking",
            "deadlock",
            "锁",
            "阻塞",
        ),
    ):
        tags.add("locking_sensitive")

    if _has_any(
        text,
        (
            "optimizer",
            "statistics",
            "stats",
            "analyze",
            "planner",
            "plan",
            "cost",
            "selectivity",
            "scan",
            "统计信息",
            "优化器",
            "执行计划",
        ),
    ):
        tags.add("optimizer_sensitive")

    if _has_any(
        text,
        (
            "expected_status",
            "expected_result",
            "failure",
            "error",
            "invalid",
            "unsupported",
            "negative",
            "sqlstate",
            "预期结果",
            "失败",
            "错误",
        ),
    ):
        tags.add("negative_control")

    if _has_any(
        text,
        (
            "oracle",
            "verification",
            "verify",
            "expected_sqlstate",
            "expected_error",
            "assertion",
            "校验",
            "断言",
        ),
    ):
        tags.add("oracle")

    return tuple(tag for tag in TAG_ORDER if tag in tags)


def build_factor_profiles(statement_config: dict) -> dict[str, dict]:
    """Return factor profiles keyed by local factor name."""
    config = _as_mapping(statement_config)
    factors = _as_mapping(config.get("factors"))
    labels = _as_mapping(config.get("factor_labels"))
    values_by_factor = _as_mapping(config.get("factor_values"))

    factor_names = [str(name) for name in factors]
    for name in labels:
        if str(name) not in factor_names:
            factor_names.append(str(name))
    for name in values_by_factor:
        if str(name) not in factor_names:
            factor_names.append(str(name))

    profiles: dict[str, dict] = {}
    for factor_name in factor_names:
        factor_doc = _as_mapping(factors.get(factor_name))
        label = str(factor_doc.get("label") or labels.get(factor_name) or factor_name)
        values = _factor_values(factor_doc, values_by_factor.get(factor_name))
        semantic_tags = infer_semantic_tags(factor_name, {"label": label, "values": values})
        profiles[factor_name] = {
            "name": factor_name,
            "label": label,
            "values": tuple(values),
            "semantic_tags": semantic_tags,
        }
    return profiles


def plan_associations(
    *,
    statement_config: dict,
    matrix_config: Optional[dict] = None,
    type_catalog_config: Optional[dict] = None,
    coverage_inventory: Optional[dict] = None,
) -> dict:
    """Return an association plan with scenario_families and coverage_obligations."""
    statement_doc = _statement_doc(statement_config, matrix_config)
    factor_profiles = build_factor_profiles(statement_config)
    matrix = _as_mapping(matrix_config)
    coverage_scope = _as_mapping(matrix.get("coverage_scope"))
    type_catalog = _as_mapping(type_catalog_config)
    inventory = _as_mapping(coverage_inventory)

    scenario_families: list[dict] = []

    tagged_factors = _factor_names_by_tag(factor_profiles)

    relation_facts = _relation_coverage_facts(coverage_scope)
    if not relation_facts:
        relation_facts = _statement_factor_facts(factor_profiles, tagged_factors, "relation_kind")
    if relation_facts:
        scenario_families.append(
            _scenario_family(
                "relation_kind_matrix",
                "Relation/object coverage matrix",
                "relation_kind",
                relation_facts,
                "Cover required and negative relation/object kinds declared by the matrix.",
            )
        )

    column_facts = _column_type_coverage_facts(coverage_scope, type_catalog)
    if not column_facts:
        column_facts = _statement_factor_facts(factor_profiles, tagged_factors, "column_type")
    if column_facts:
        scenario_families.append(
            _scenario_family(
                "column_type_matrix",
                "Column type compatibility matrix",
                "column_type",
                column_facts,
                "Cover declared column type sets and type catalog compatibility metadata.",
            )
        )

    if tagged_factors.get("transaction_sensitive") or tagged_factors.get("locking_sensitive"):
        transaction_factors = _unique(
            tagged_factors.get("transaction_sensitive", [])
            + tagged_factors.get("locking_sensitive", [])
        )
        scenario_families.append(
            _scenario_family(
                "transaction_concurrency_matrix",
                "Transaction and concurrency matrix",
                "transaction_concurrency",
                _tagged_factor_facts(transaction_factors),
                "Cover transaction-sensitive and locking-sensitive behavior.",
            )
        )

    if tagged_factors.get("optimizer_sensitive"):
        scenario_families.append(
            _scenario_family(
                "optimizer_statistics_matrix",
                "Optimizer and statistics matrix",
                "optimizer_statistics",
                _tagged_factor_facts(tagged_factors["optimizer_sensitive"]),
                "Cover optimizer, statistics, and planner-state-sensitive behavior.",
            )
        )

    lifecycle_factors = _unique(
        tagged_factors.get("dependency_state", []) + tagged_factors.get("schema_mutation", [])
    )
    if lifecycle_factors:
        scenario_families.append(
            _scenario_family(
                "schema_mutation_lifecycle",
                "Schema mutation lifecycle",
                "lifecycle_mutation",
                _tagged_factor_facts(lifecycle_factors),
                "Cover setup, mutation, target statement, verification, and cleanup flows.",
            )
        )

    if tagged_factors.get("data_profile"):
        scenario_families.append(
            _scenario_family(
                "data_profile_matrix",
                "Data profile matrix",
                "data_profile",
                _tagged_factor_facts(tagged_factors["data_profile"]),
                "Cover data size, NULL, duplicate, and distribution-sensitive behavior.",
            )
        )

    negative_facts = _negative_control_facts(matrix, inventory, tagged_factors)
    if negative_facts:
        scenario_families.append(
            _scenario_family(
                "negative_control_matrix",
                "Negative control matrix",
                "negative_control",
                negative_facts,
                "Cover declared failure and negative inventory paths.",
            )
        )

    coverage_obligations = [_coverage_obligation(family) for family in scenario_families]
    coverage_obligations.extend(_factor_contract_obligations(matrix))

    return {
        "kind": "factor_association_plan",
        "target_statement": statement_doc,
        "association_model": {
            "mode": "hybrid_rule_first",
            "source_priority": ["statement_config", "matrix_config", "type_catalog_config", "coverage_inventory"],
        },
        "factor_profiles": factor_profiles,
        "scenario_families": scenario_families,
        "coverage_obligations": coverage_obligations,
        "quality_gates": [
            {
                "id": "source_fact_traceability",
                "description": "Every scenario family records source_facts used by deterministic rules.",
            },
            {
                "id": "required_before_extensions",
                "description": "Derived extensions must not replace required baseline matrix coverage.",
            },
        ],
    }


def _as_mapping(value: Any) -> dict:
    return dict(value) if isinstance(value, Mapping) else {}


def _as_sequence(value: Any) -> list:
    if isinstance(value, (list, tuple)):
        return list(value)
    return []


def _value_key(value: Any) -> str:
    if isinstance(value, Mapping):
        return str(value.get("key") or value.get("type_key") or value.get("id") or "")
    if value is None:
        return ""
    return str(value)


def _search_text(parts: list[str]) -> str:
    return " ".join(part.lower() for part in parts if part)


def _has_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle.lower() in text for needle in needles)


def _factor_values(factor_doc: dict, fallback: Any) -> list[str]:
    raw_values = factor_doc.get("values")
    if raw_values is None:
        raw_values = fallback
    return [value for value in (_value_key(item) for item in _as_sequence(raw_values)) if value]


def _statement_doc(statement_config: dict, matrix_config: Optional[dict]) -> dict:
    statement = _as_mapping(_as_mapping(statement_config).get("statement"))
    matrix_statement = _as_mapping(_as_mapping(matrix_config).get("statement"))
    key = str(statement.get("key") or matrix_statement.get("key") or "")
    name = str(statement.get("name") or matrix_statement.get("name") or key)
    return {"key": key, "name": name}


def _factor_names_by_tag(factor_profiles: dict[str, dict]) -> dict[str, list[str]]:
    by_tag: dict[str, list[str]] = {}
    for factor_name, profile in factor_profiles.items():
        for tag in _as_sequence(_as_mapping(profile).get("semantic_tags")):
            by_tag.setdefault(str(tag), []).append(str(factor_name))
    return by_tag


def _relation_coverage_facts(coverage_scope: dict) -> dict:
    relation_facts: dict[str, Any] = {}
    sources: list[str] = []
    for coverage_name in ("target_relation_coverage", "table_coverage", "target_object_coverage"):
        coverage = _as_mapping(coverage_scope.get(coverage_name))
        required_kinds = _coverage_values(coverage, ("required_relation_kinds", "required_table_kinds", "required_object_kinds", "required_kinds"))
        negative_kinds = _coverage_values(coverage, ("negative_relation_kinds", "negative_table_kinds", "negative_object_kinds", "negative_kinds"))
        if _is_required_or_negative(coverage, required_kinds, negative_kinds):
            source = f"combination_matrix.coverage_scope.{coverage_name}"
            sources.append(source)
            relation_facts[coverage_name] = {
                "source": source,
                "required": bool(coverage.get("required")),
                "coverage_mode": str(coverage.get("coverage_mode") or ""),
                "required_kinds": required_kinds,
                "negative_kinds": negative_kinds,
            }
    if sources:
        relation_facts["sources"] = sources
    return relation_facts


def _column_type_coverage_facts(coverage_scope: dict, type_catalog: dict) -> dict:
    coverage = _as_mapping(coverage_scope.get("column_type_coverage"))
    required_types = _coverage_values(coverage, ("required_types", "types"))
    type_set_name = str(coverage.get("required_type_set") or "")
    if not required_types and type_set_name:
        required_types = _type_set_members(type_catalog, type_set_name)
    if not _is_required_or_negative(coverage, required_types, []):
        return {}
    return {
        "sources": _column_type_sources(type_set_name),
        "required": bool(coverage.get("required")),
        "coverage_mode": str(coverage.get("coverage_mode") or ""),
        "required_type_set": type_set_name,
        "types": required_types,
        "type_categories": _type_categories(type_catalog, required_types),
    }


def _statement_factor_facts(factor_profiles: dict[str, dict], tagged_factors: dict[str, list[str]], tag: str) -> dict:
    factors = tagged_factors.get(tag, [])
    if not factors:
        return {}
    values_by_factor = {
        factor: list(_as_sequence(_as_mapping(factor_profiles.get(factor)).get("values")))
        for factor in factors
    }
    return {
        "sources": [f"statement_reference.factors.{factor}" for factor in factors],
        "factors": factors,
        "values_by_factor": values_by_factor,
    }


def _tagged_factor_facts(factors: list[str]) -> dict:
    return {
        "sources": [f"statement_reference.factors.{factor}" for factor in factors],
        "factors": factors,
    }


def _column_type_sources(type_set_name: str) -> list[str]:
    sources = ["combination_matrix.coverage_scope.column_type_coverage"]
    if type_set_name:
        sources.append(f"type_catalog.type_sets.{type_set_name}")
    return sources


def _coverage_values(coverage: dict, keys: tuple[str, ...]) -> list[str]:
    for key in keys:
        values = [value for value in (_value_key(item) for item in _as_sequence(coverage.get(key))) if value]
        if values:
            return values
    return []


def _is_required_or_negative(coverage: dict, required_values: list[str], negative_values: list[str]) -> bool:
    return bool(coverage.get("required") or required_values or negative_values)


def _type_set_members(type_catalog: dict, type_set_name: str) -> list[str]:
    type_sets = _as_mapping(type_catalog.get("type_sets"))
    type_set = _as_mapping(type_sets.get(type_set_name))
    explicit_types = [value for value in (_value_key(item) for item in _as_sequence(type_set.get("types"))) if value]
    if explicit_types:
        return explicit_types
    if type_set and type_set.get("include_pseudo_types") is True:
        return list(_as_mapping(type_catalog.get("types"))) + _as_sequence(_as_mapping(type_catalog.get("pseudo_types")).get("values"))
    if type_set:
        return list(_as_mapping(type_catalog.get("types")))
    return []


def _type_categories(type_catalog: dict, type_names: list[str]) -> dict[str, str]:
    types = _as_mapping(type_catalog.get("types"))
    categories: dict[str, str] = {}
    for type_name in type_names:
        type_doc = _as_mapping(types.get(type_name))
        if type_doc.get("type_category"):
            categories[type_name] = str(type_doc["type_category"])
    return categories


def _negative_control_facts(matrix: dict, coverage_inventory: dict, tagged_factors: dict[str, list[str]]) -> dict:
    failure_groups = []
    for group in _as_sequence(matrix.get("combination_groups")):
        group_doc = _as_mapping(group)
        factors = _as_mapping(group_doc.get("factors"))
        if str(group_doc.get("default_expected_status") or "").lower() == "failure" or str(factors.get("expected_status") or "").lower() == "failure":
            failure_groups.append(str(group_doc.get("id") or f"failure_group_{len(failure_groups) + 1}"))

    inventory_negatives: dict[str, Any] = {}
    for key, value in coverage_inventory.items():
        if "negative" in str(key).lower() or "failure" in str(key).lower():
            inventory_negatives[str(key)] = value

    negative_factors = tagged_factors.get("negative_control", [])
    if not failure_groups and not inventory_negatives and not negative_factors:
        return {}
    return {
        "sources": _negative_control_sources(failure_groups, inventory_negatives, negative_factors),
        "failure_groups": failure_groups,
        "inventory_keys": list(inventory_negatives),
        "factors": negative_factors,
    }


def _negative_control_sources(failure_groups: list[str], inventory_negatives: dict, negative_factors: list[str]) -> list[str]:
    sources: list[str] = []
    if failure_groups:
        sources.append("combination_matrix.combination_groups")
    sources.extend(f"coverage_inventory.{key}" for key in inventory_negatives)
    sources.extend(f"statement_reference.factors.{factor}" for factor in negative_factors)
    return _unique(sources)


def _scenario_family(family_id: str, title: str, family_type: str, source_facts: dict, obligation: str) -> dict:
    return {
        "id": family_id,
        "title": title,
        "family_type": family_type,
        "origin": "deterministic_rule",
        "derived_extension": False,
        "trigger_facts": source_facts,
        "coverage_tags": [family_type],
        "lifecycle": ["setup", "target_statement", "verification", "cleanup"],
        "oracle": {"mode": "declared_matrix_or_statement_reference"},
        "cleanup": {"required": True},
        "why": obligation,
    }


def _coverage_obligation(family: dict) -> dict:
    family_id = str(family["id"])
    return {
        "id": f"cover_{family_id}",
        "scenario_family": family_id,
        "required": True,
        "trigger_facts": family["trigger_facts"],
    }


def _factor_contract_obligations(matrix: dict) -> list[dict]:
    obligations: list[dict] = []
    factor_contract = _as_mapping(matrix.get("factor_contract"))
    for factor_name, factor_doc in _as_mapping(factor_contract.get("factors")).items():
        factor_name = str(factor_name)
        factor_doc = _as_mapping(factor_doc)
        obligations.append(
            {
                "id": f"cover_factor_contract_{factor_name}",
                "source": f"combination_matrix.factor_contract.factors.{factor_name}",
                "factor": factor_name,
                "required": True,
                "tier": str(factor_doc.get("tier") or ""),
                "coverage_role": str(factor_doc.get("coverage_role") or ""),
                "required_values": [
                    value
                    for value in (_value_key(item) for item in _as_sequence(factor_doc.get("required_values")))
                    if value
                ],
                "coverage_requirement": str(factor_doc.get("coverage_requirement") or ""),
            }
        )
    return obligations


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
