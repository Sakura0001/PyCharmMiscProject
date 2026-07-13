from __future__ import annotations

import itertools
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml


_YAML_BLOCK = re.compile(r"```yaml\s*(.*?)```", re.DOTALL)


def load_statement_reference(path: Path | str) -> dict[str, Any]:
    source = Path(path)
    match = _YAML_BLOCK.search(source.read_text(encoding="utf-8"))
    if match is None:
        raise ValueError(f"statement reference has no YAML block: {source}")
    document = yaml.safe_load(match.group(1)) or {}
    if not isinstance(document, Mapping):
        raise ValueError(f"statement reference YAML must be a mapping: {source}")
    config = document.get("structured_config", document)
    if not isinstance(config, Mapping):
        raise ValueError(f"structured_config must be a mapping: {source}")
    return dict(config)


def _values(factor: Any, name: str) -> list[str]:
    if not isinstance(factor, Mapping) or not isinstance(factor.get("values"), list):
        raise ValueError(f"factor {name} must declare a values list")
    result: list[str] = []
    for item in factor["values"]:
        value = item.get("key") if isinstance(item, Mapping) else item
        if not isinstance(value, (str, int, float, bool)) or str(value) == "":
            raise ValueError(f"factor {name} contains an invalid value")
        result.append(str(value).lower() if isinstance(value, bool) else str(value))
    if not result or len(result) != len(set(result)):
        raise ValueError(f"factor {name} values must be nonempty and unique")
    return result


def _slug(*parts: str) -> str:
    value = "__".join(parts).lower()
    return re.sub(r"[^a-z0-9_]+", "_", value).strip("_")[:180]


def _expected_status(assignments: Mapping[str, str], defaults: Mapping[str, str]) -> str:
    value = assignments.get("expected_status", defaults.get("expected_status", "success")).lower()
    if value in {"failure", "expected_failure", "invalid", "error", "denied", "unsupported"}:
        return "failure"
    return "success"


def generate_matrix_for_reference(
    reference_path: Path | str,
    config: Mapping[str, Any],
    *,
    skill_root: Path | str,
) -> dict[str, Any]:
    reference = Path(reference_path).resolve()
    root = Path(skill_root).resolve()
    try:
        relative_reference = reference.relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError("statement reference must be contained in skill root") from exc
    statement = config.get("statement")
    factors = config.get("factors")
    if not isinstance(statement, Mapping) or not isinstance(factors, Mapping) or not factors:
        raise ValueError("statement reference must define statement and factors")
    statement_key = str(statement.get("key") or "")
    statement_name = str(statement.get("name") or statement_key).strip()
    category = str(config.get("category") or "unknown")
    domain = str(config.get("domain") or "unknown")
    if not statement_key or not statement_name:
        raise ValueError("statement reference must define statement key and name")

    values_by_factor = {str(name): _values(document, str(name)) for name, document in factors.items()}
    defaults_raw = config.get("defaults") if isinstance(config.get("defaults"), Mapping) else {}
    defaults = {
        name: str(defaults_raw.get(name, values[0]))
        for name, values in values_by_factor.items()
    }
    policy = config.get("coverage_policy") if isinstance(config.get("coverage_policy"), Mapping) else {}
    main_axes = [str(item) for item in policy.get("main_combination_axes", [])]
    if not main_axes:
        main_axes = list(values_by_factor)
    if any(name not in values_by_factor for name in main_axes):
        raise ValueError(f"{statement_key} coverage policy names an unknown main factor")
    non_main = [name for name in values_by_factor if name not in main_axes]

    tier_by_factor: dict[str, str] = {}
    layers = config.get("factor_layers") if isinstance(config.get("factor_layers"), list) else []
    for layer in layers:
        if not isinstance(layer, Mapping):
            continue
        tier = str(layer.get("tier") or "T3")
        for factor_name in layer.get("factors", []):
            tier_by_factor[str(factor_name)] = tier

    rendering = config.get("rendering") if isinstance(config.get("rendering"), Mapping) else {}
    sql_template = str(
        rendering.get("statement_template")
        or rendering.get("sql_template")
        or statement_name
    )

    groups: list[dict[str, Any]] = []

    def add_group(group_id: str, assignments: Mapping[str, str], *, supplemental: bool) -> None:
        complete = dict(defaults)
        complete.update(assignments)
        status = _expected_status(complete, defaults)
        failure_reason = "declared_expected_failure" if status == "failure" else ""
        groups.append(
            {
                "id": group_id,
                "title": f"{statement_name} {'supplemental factor' if supplemental else 'required combination'}",
                "lifecycle_role": "negative_control" if status == "failure" else "target_statement",
                "expected_status_policy": "fixed",
                "default_expected_status": status,
                "expected_failure_reasons": [failure_reason] if failure_reason else [],
                "derived_extension": False,
                "factors": complete,
                "expansion": {
                    "mode": "one_factor_at_a_time" if supplemental else "complete_cartesian",
                    "axes": list(assignments),
                },
                "compatibility": {
                    "resolver": "declared_matrix",
                    "success_when": ["declared reference combination"] if status == "success" else [],
                    "failure_when": ["declared expected failure"] if status == "failure" else [],
                    "default_failure_reason": failure_reason,
                },
                "sql_shape": {"template": sql_template},
                "verification": {"required": False, "mode": "statement_reference", "sql": None},
                "cleanup": {"required": True, "steps": [{"sql": "-- cleanup is defined by the lifecycle plan"}]},
            }
        )

    for combination in itertools.product(*(values_by_factor[name] for name in main_axes)):
        assignments = dict(zip(main_axes, combination))
        add_group(_slug("required", *(f"{name}_{value}" for name, value in assignments.items())), assignments, supplemental=False)
    for factor_name in non_main:
        for value in values_by_factor[factor_name]:
            add_group(_slug("supplemental", factor_name, value), {factor_name: value}, supplemental=True)

    factor_contract = {
        name: {
            "tier": tier_by_factor.get(name, "T3"),
            "coverage_role": "main_axis" if name in main_axes else "rotate_attach",
            "required_values": values,
            "coverage_requirement": "all_values",
        }
        for name, values in values_by_factor.items()
    }
    not_applicable = {
        "required": False,
        "coverage_mode": "not_applicable",
        "decision_reason": "Statement matrices cover syntax factors; feature coverage plans own object inventories.",
    }
    return {
        "schema_version": 1,
        "kind": "statement_combination_matrix",
        "statement": {
            "key": statement_key,
            "name": statement_name,
            "category": category,
            "domain": domain,
            "source_reference": relative_reference,
        },
        "execution_contract": {
            "required_matrix_is_baseline": True,
            "no_inference_before_required_coverage_passes": True,
            "runner_must_complete_required_matrix_first": True,
            "allow_post_coverage_extension_inference": False,
            "extension_combinations_must_be_marked": True,
            "extension_combinations_must_record_derivation": True,
            "extension_combinations_must_not_replace_required_coverage": True,
            "success_and_failure_both_allowed": True,
            "all_success_and_failure_reasons_must_be_declared": True,
            "required_coverage_sql_templates_must_come_from_combination_groups": True,
            "extension_sql_templates_must_be_recorded_in_artifacts": True,
        },
        "post_coverage_extension_policy": {
            "enabled": False,
            "allowed_after_audit_verdict": "required_coverage_passed",
            "output_location": "artifacts/intermediates/<task_slug>/derived_extension_combinations.yaml",
            "required_fields": [
                "id", "title", "derived_from_combination_group", "derivation_reason",
                "factors", "expected_status_policy", "compatibility", "sql_shape",
                "verification", "cleanup",
            ],
            "guardrails": ["Required coverage cannot be replaced by inferred combinations."],
        },
        "coverage_scope": {
            "target_object_coverage": dict(not_applicable),
            "target_relation_coverage": dict(not_applicable),
            "table_coverage": dict(not_applicable),
            "column_type_coverage": dict(not_applicable),
        },
        "factor_contract": {
            "source_reference_must_define_all_factors": True,
            "matrix_must_cover_required_factor_values": True,
            "factors": factor_contract,
        },
        "dynamic_inputs": {},
        "combination_groups": groups,
        "audit_rules": {
            "require_all_required_top_level_keys": True,
            "require_declared_coverage_scope": True,
            "require_declared_factor_values": True,
            "require_expected_failure_reasons": True,
            "require_post_coverage_extension_policy": True,
            "forbid_extension_before_required_coverage_passes": True,
            "forbid_extension_counting_toward_required_coverage": True,
        },
    }
