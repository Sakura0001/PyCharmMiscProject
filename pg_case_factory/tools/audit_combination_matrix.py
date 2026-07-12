from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import yaml


YAML_BLOCK_PATTERN = re.compile(r"```yaml\s*(.*?)```", re.DOTALL)
REFERENCES_ROOT = Path("skills/pg-sql-generation/references")
STATEMENTS_ROOT = REFERENCES_ROOT / "statements"
COMBINATIONS_ROOT = REFERENCES_ROOT / "combinations"
SHARED_SCHEMA = COMBINATIONS_ROOT / "_shared" / "statement_combination_matrix_schema.yaml"
TYPE_CATALOG = REFERENCES_ROOT / "common" / "pg18_type_catalog.md"
COMPLETE_COLUMN_TYPE_SELECTORS = (
    "structured_config.types",
    "structured_config.concrete_builtin_types.values",
    "structured_config.auto_array_types.element_types",
    "structured_config.pseudo_types.values",
    "structured_config.declaration_aliases.mappings",
    "structured_config.typmod_declarations.values",
    "structured_config.user_defined_archetypes.values",
)


DEFAULT_SCHEMA = {
    "required_top_level_keys": [
        "schema_version",
        "kind",
        "statement",
        "execution_contract",
        "post_coverage_extension_policy",
        "coverage_scope",
        "factor_contract",
        "dynamic_inputs",
        "combination_groups",
        "audit_rules",
    ],
    "execution_contract_required_keys": [
        "required_matrix_is_baseline",
        "no_inference_before_required_coverage_passes",
        "runner_must_complete_required_matrix_first",
        "allow_post_coverage_extension_inference",
        "extension_combinations_must_be_marked",
        "extension_combinations_must_record_derivation",
        "extension_combinations_must_not_replace_required_coverage",
        "success_and_failure_both_allowed",
        "all_success_and_failure_reasons_must_be_declared",
        "required_coverage_sql_templates_must_come_from_combination_groups",
        "extension_sql_templates_must_be_recorded_in_artifacts",
    ],
    "coverage_scope_required_keys": [
        "target_object_coverage",
        "target_relation_coverage",
        "table_coverage",
        "column_type_coverage",
    ],
    "coverage_scope_item_required_keys": ["required", "coverage_mode", "decision_reason"],
    "factor_contract_required_keys": [
        "source_reference_must_define_all_factors",
        "matrix_must_cover_required_factor_values",
        "factors",
    ],
    "factor_entry_required_keys": ["tier", "coverage_role", "required_values", "coverage_requirement"],
    "combination_group_required_keys": [
        "id",
        "title",
        "lifecycle_role",
        "expected_status_policy",
        "factors",
        "expansion",
        "compatibility",
        "sql_shape",
        "verification",
        "cleanup",
    ],
    "compatibility_required_keys": ["resolver", "success_when", "failure_when", "default_failure_reason"],
    "sql_shape_required_keys": ["template"],
    "verification_required_keys": ["required"],
    "cleanup_required_keys": ["required"],
    "allowed_expected_status_policies": ["fixed"],
    "allowed_coverage_modes": ["not_applicable", "explicit", "exhaustive", "representative", "conditional"],
    "allowed_lifecycle_roles": ["setup", "target_statement", "verification", "cleanup", "negative_control"],
    "audit_rules_required_keys": [
        "require_all_required_top_level_keys",
        "require_declared_coverage_scope",
        "require_declared_factor_values",
        "require_expected_failure_reasons",
        "require_post_coverage_extension_policy",
        "forbid_extension_before_required_coverage_passes",
        "forbid_extension_counting_toward_required_coverage",
    ],
}


@dataclass
class AuditResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    matrix_count: int = 0
    group_count: int = 0
    complete_column_scope_count: int = 0
    partial_column_scope_count: int = 0
    exhaustive_object_relation_table_scope_count: int = 0
    partial_object_relation_table_scope_count: int = 0

    @property
    def passed(self) -> bool:
        return not self.errors

    def extend(self, other: "AuditResult") -> None:
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.matrix_count += other.matrix_count
        self.group_count += other.group_count
        self.complete_column_scope_count += other.complete_column_scope_count
        self.partial_column_scope_count += other.partial_column_scope_count
        self.exhaustive_object_relation_table_scope_count += other.exhaustive_object_relation_table_scope_count
        self.partial_object_relation_table_scope_count += other.partial_object_relation_table_scope_count


def _load_markdown_yaml(path: Path) -> dict[str, Any]:
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


def _load_yaml_file(path: Path) -> dict[str, Any]:
    parsed = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(parsed, Mapping):
        raise ValueError(f"{path}: yaml must be a mapping")
    return dict(parsed)


def _load_schema(root: Path) -> dict[str, Any]:
    path = root / SHARED_SCHEMA
    if not path.exists():
        return dict(DEFAULT_SCHEMA)
    schema = _load_yaml_file(path)
    merged = dict(DEFAULT_SCHEMA)
    merged.update(schema)
    return merged


def _default_matrix_paths(root: Path) -> list[Path]:
    combinations_root = root / COMBINATIONS_ROOT
    if not combinations_root.exists():
        return []
    return sorted(
        path
        for path in combinations_root.glob("**/*.yaml")
        if "_shared" not in path.relative_to(combinations_root).parts
    )


def _statement_paths(root: Path) -> list[Path]:
    statements_root = root / STATEMENTS_ROOT
    if not statements_root.exists():
        return []
    return sorted(statements_root.glob("**/*.md"))


def _relative_reference(root: Path, path: Path) -> str:
    try:
        rel = path.resolve().relative_to(root.resolve())
        if rel.parts[:4] == ("skills", "pg-sql-generation", "references", "statements"):
            return str(Path("references") / Path(*rel.parts[3:]))
    except ValueError:
        pass
    return path.as_posix()


def _statement_key(config: Mapping[str, Any]) -> str:
    statement = config.get("statement") or {}
    if isinstance(statement, Mapping):
        return str(statement.get("key") or "")
    return ""


def _load_statements(
    root: Path,
) -> tuple[
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, list[Path]],
]:
    by_key: dict[str, dict[str, Any]] = {}
    by_reference: dict[str, dict[str, Any]] = {}
    paths_by_key: dict[str, list[Path]] = {}
    for path in _statement_paths(root):
        config = _load_markdown_yaml(path)
        key = _statement_key(config)
        if key:
            by_key[key] = config
            paths_by_key.setdefault(key, []).append(path)
        ref = _relative_reference(root, path)
        by_reference[ref] = config
        try:
            by_reference[str(path.resolve().relative_to(root.resolve()))] = config
        except ValueError:
            pass
    return by_key, by_reference, paths_by_key


def _as_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _as_sequence(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _resolve_selector(document: Mapping[str, Any], selector: str) -> Any:
    selected: Any = document
    components = selector.split(".")
    if components and components[0] == "structured_config":
        components = components[1:]
    for component in components:
        selected = _as_mapping(selected).get(component)
    return selected


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _value_key(value: Any) -> str:
    if isinstance(value, Mapping):
        return _text(value.get("key"))
    return _text(value)


def _statement_factor_values(statement_config: Mapping[str, Any]) -> dict[str, set[str]]:
    values_by_factor: dict[str, set[str]] = {}
    for factor_name, factor_doc in _as_mapping(statement_config.get("factors")).items():
        values = set()
        for item in _as_sequence(_as_mapping(factor_doc).get("values")):
            key = _value_key(item)
            if key:
                values.add(key)
        values_by_factor[str(factor_name)] = values
    return values_by_factor


def _add_missing_keys(result: AuditResult, path: Path, context: str, data: Mapping[str, Any], required: Iterable[str]) -> None:
    for key in required:
        if key not in data:
            result.errors.append(f"{path}: {context} missing required key: {key}")


def _validate_matrix_shape(result: AuditResult, path: Path, matrix: Mapping[str, Any], schema: Mapping[str, Any]) -> None:
    _add_missing_keys(result, path, "matrix", matrix, _as_sequence(schema.get("required_top_level_keys")))
    if matrix.get("kind") != "statement_combination_matrix":
        result.errors.append(f"{path}: kind must be statement_combination_matrix")

    statement = _as_mapping(matrix.get("statement"))
    _add_missing_keys(result, path, "statement", statement, _as_sequence(schema.get("statement_required_keys")))

    execution_contract = _as_mapping(matrix.get("execution_contract"))
    _add_missing_keys(
        result,
        path,
        "execution_contract",
        execution_contract,
        _as_sequence(schema.get("execution_contract_required_keys")),
    )
    for key in _as_sequence(schema.get("execution_contract_boolean_keys")):
        if key in execution_contract and not isinstance(execution_contract[key], bool):
            result.errors.append(f"{path}: execution_contract.{key} must be boolean")

    coverage_scope = _as_mapping(matrix.get("coverage_scope"))
    _add_missing_keys(result, path, "coverage_scope", coverage_scope, _as_sequence(schema.get("coverage_scope_required_keys")))
    allowed_modes = {str(item) for item in _as_sequence(schema.get("allowed_coverage_modes"))}
    for coverage_name, coverage_doc in coverage_scope.items():
        coverage_doc = _as_mapping(coverage_doc)
        _add_missing_keys(
            result,
            path,
            f"coverage_scope.{coverage_name}",
            coverage_doc,
            _as_sequence(schema.get("coverage_scope_item_required_keys")),
        )
        mode = coverage_doc.get("coverage_mode")
        if mode and str(mode) not in allowed_modes:
            result.errors.append(f"{path}: coverage_scope.{coverage_name} has unsupported coverage_mode: {mode}")

    factor_contract = _as_mapping(matrix.get("factor_contract"))
    _add_missing_keys(result, path, "factor_contract", factor_contract, _as_sequence(schema.get("factor_contract_required_keys")))
    for factor_name, factor_doc in _as_mapping(factor_contract.get("factors")).items():
        _add_missing_keys(
            result,
            path,
            f"factor_contract.factors.{factor_name}",
            _as_mapping(factor_doc),
            _as_sequence(schema.get("factor_entry_required_keys")),
        )

    _validate_dynamic_inputs(result, path, _as_mapping(matrix.get("dynamic_inputs")), schema)

    allowed_status_policies = {str(item) for item in _as_sequence(schema.get("allowed_expected_status_policies"))}
    allowed_lifecycle_roles = {str(item) for item in _as_sequence(schema.get("allowed_lifecycle_roles"))}
    for group in _as_sequence(matrix.get("combination_groups")):
        group_doc = _as_mapping(group)
        group_id = group_doc.get("id") or "<missing id>"
        result.group_count += 1
        _add_missing_keys(
            result,
            path,
            f"combination_groups.{group_id}",
            group_doc,
            _as_sequence(schema.get("combination_group_required_keys")),
        )
        status_policy = group_doc.get("expected_status_policy")
        if status_policy and str(status_policy) not in allowed_status_policies:
            result.errors.append(f"{path}: {group_id}: unsupported expected_status_policy: {status_policy}")
        lifecycle_role = group_doc.get("lifecycle_role")
        if lifecycle_role and str(lifecycle_role) not in allowed_lifecycle_roles:
            result.errors.append(f"{path}: {group_id}: unsupported lifecycle_role: {lifecycle_role}")
        _add_missing_keys(result, path, f"{group_id}.compatibility", _as_mapping(group_doc.get("compatibility")), _as_sequence(schema.get("compatibility_required_keys")))
        _add_missing_keys(result, path, f"{group_id}.sql_shape", _as_mapping(group_doc.get("sql_shape")), _as_sequence(schema.get("sql_shape_required_keys")))
        _add_missing_keys(result, path, f"{group_id}.verification", _as_mapping(group_doc.get("verification")), _as_sequence(schema.get("verification_required_keys")))
        _add_missing_keys(result, path, f"{group_id}.cleanup", _as_mapping(group_doc.get("cleanup")), _as_sequence(schema.get("cleanup_required_keys")))

    audit_rules = _as_mapping(matrix.get("audit_rules"))
    _add_missing_keys(result, path, "audit_rules", audit_rules, _as_sequence(schema.get("audit_rules_required_keys")))


def _validate_dynamic_inputs(result: AuditResult, path: Path, dynamic_inputs: Mapping[str, Any], schema: Mapping[str, Any]) -> None:
    required_keys = _as_sequence(schema.get("dynamic_input_required_keys"))
    for input_name, input_doc in dynamic_inputs.items():
        _add_missing_keys(result, path, f"dynamic_inputs.{input_name}", _as_mapping(input_doc), required_keys)


def _matrix_statement_config(
    matrix: Mapping[str, Any],
    statements_by_reference: Mapping[str, dict[str, Any]],
) -> dict[str, Any] | None:
    statement = _as_mapping(matrix.get("statement"))
    source_reference = _text(statement.get("source_reference"))
    return statements_by_reference.get(source_reference)


def _baseline_groups(matrix: Mapping[str, Any]) -> list[dict[str, Any]]:
    groups = []
    for group in _as_sequence(matrix.get("combination_groups")):
        group_doc = _as_mapping(group)
        if group_doc.get("derived_extension") is True:
            continue
        groups.append(group_doc)
    return groups


def _factor_axis_name(axis_name: str, statement_factors: set[str]) -> str | None:
    if axis_name in statement_factors:
        return axis_name
    if axis_name.endswith("s") and axis_name[:-1] in statement_factors:
        return axis_name[:-1]
    return None


def _record_expansion_coverage(
    covered_values: dict[str, set[str]],
    group: Mapping[str, Any],
    statement_factors: set[str],
) -> None:
    for axis_name, axis_doc in _as_mapping(group.get("expansion")).items():
        axis_doc = _as_mapping(axis_doc)
        if str(axis_name) == "statement_branch" and isinstance(axis_doc.get("values"), Mapping):
            for value in _as_mapping(axis_doc.get("values")).values():
                covered_values.setdefault("statement_branch", set()).add(_text(value))
            continue

        factor_name = _factor_axis_name(str(axis_name), statement_factors)
        if factor_name and factor_name in covered_values:
            for value in _as_sequence(axis_doc.get("values")):
                covered_values[factor_name].add(_text(value))
            continue


def _validate_factors_against_statement(
    result: AuditResult,
    path: Path,
    matrix: Mapping[str, Any],
    statement_config: Mapping[str, Any],
) -> None:
    statement_values = _statement_factor_values(statement_config)
    statement_factors = set(statement_values)
    factor_contract = _as_mapping(matrix.get("factor_contract"))
    contract_factors = _as_mapping(factor_contract.get("factors"))

    if factor_contract.get("source_reference_must_define_all_factors") is not True:
        result.errors.append(
            f"{path}: factor_contract.source_reference_must_define_all_factors must be true"
        )
    if factor_contract.get("matrix_must_cover_required_factor_values") is not True:
        result.errors.append(
            f"{path}: factor_contract.matrix_must_cover_required_factor_values must be true"
        )

    for factor_name in sorted(statement_factors - {str(name) for name in contract_factors}):
        result.errors.append(
            f"{path}: factor contract missing statement factor: {factor_name}"
        )

    for factor_name, factor_doc in contract_factors.items():
        factor_name = str(factor_name)
        if factor_name not in statement_factors:
            result.errors.append(f"{path}: unknown factor: {factor_name}")
            continue
        factor_doc = _as_mapping(factor_doc)
        required_values = {
            _text(value)
            for value in _as_sequence(factor_doc.get("required_values"))
            if _text(value)
        }
        for value in sorted(required_values):
            value_key = _text(value)
            if value_key and value_key not in statement_values[factor_name]:
                result.errors.append(f"{path}: unknown factor value: {factor_name}={value_key}")
        coverage_requirement = factor_doc.get("coverage_requirement")
        if coverage_requirement in ("all_values", "all_declared_values"):
            for value_key in sorted(statement_values[factor_name] - required_values):
                result.errors.append(
                    f"{path}: coverage_requirement={coverage_requirement} missing declared factor value: "
                    f"{factor_name}={value_key}"
                )

    covered_values: dict[str, set[str]] = {str(factor_name): set() for factor_name in contract_factors}
    for group in _baseline_groups(matrix):
        group_id = group.get("id") or "<missing id>"
        for factor_name, value in _as_mapping(group.get("factors")).items():
            factor_name = str(factor_name)
            value_key = _text(value)
            if factor_name not in statement_factors:
                result.errors.append(f"{path}: {group_id}: unknown factor: {factor_name}")
                continue
            if value_key and value_key not in statement_values[factor_name]:
                result.errors.append(f"{path}: {group_id}: unknown factor value: {factor_name}={value_key}")
            if factor_name in covered_values and value_key:
                covered_values[factor_name].add(value_key)
        _record_expansion_coverage(covered_values, group, statement_factors)

    for factor_name, factor_doc in contract_factors.items():
        factor_name = str(factor_name)
        factor_doc = _as_mapping(factor_doc)
        required_values = {
            _text(value)
            for value in _as_sequence(factor_doc.get("required_values"))
            if _text(value)
        }
        if (
            factor_doc.get("coverage_requirement") in ("all_values", "all_declared_values")
            and factor_name in statement_values
        ):
            required_values.update(statement_values[factor_name])
        for value_key in sorted(required_values - covered_values.get(factor_name, set())):
            result.errors.append(
                f"{path}: required factor value not covered: {factor_name}={value_key}"
            )


def _group_expected_status(group: Mapping[str, Any]) -> str:
    factors = _as_mapping(group.get("factors"))
    return _text(factors.get("expected_status") or group.get("default_expected_status"))


def _validate_failure_reasons(result: AuditResult, path: Path, matrix: Mapping[str, Any]) -> None:
    for group in _as_sequence(matrix.get("combination_groups")):
        group_doc = _as_mapping(group)
        if _group_expected_status(group_doc) != "failure":
            continue
        reasons = [str(item).strip() for item in _as_sequence(group_doc.get("expected_failure_reasons")) if str(item).strip()]
        compatibility = _as_mapping(group_doc.get("compatibility"))
        default_reason = str(compatibility.get("default_failure_reason") or "").strip()
        failure_when = _as_sequence(compatibility.get("failure_when"))
        has_failure_when_reason = any(
            str(_as_mapping(item).get("reason") or "").strip()
            for item in failure_when
            if isinstance(item, Mapping)
        )
        if not reasons and not default_reason and not has_failure_when_reason:
            result.errors.append(f"{path}: {group_doc.get('id') or '<missing id>'}: failure group must declare reason")


def _validate_column_type_catalog(result: AuditResult, root: Path, path: Path, matrix: Mapping[str, Any]) -> None:
    column_coverage = _as_mapping(_as_mapping(matrix.get("coverage_scope")).get("column_type_coverage"))
    if column_coverage.get("required") is not True:
        return
    inventory_source = str(column_coverage.get("inventory_source") or "")
    type_catalog_path = root / TYPE_CATALOG
    if inventory_source != "references/common/pg18_type_catalog.md" or not type_catalog_path.exists():
        result.errors.append(f"{path}: column_type_coverage requires pg18_type_catalog")
        return
    try:
        type_catalog = _load_markdown_yaml(type_catalog_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        result.errors.append(f"{path}: cannot load pg18_type_catalog: {exc}")
        return
    coverage_mode = str(column_coverage.get("coverage_mode") or "")
    if coverage_mode == "exhaustive":
        error_count = len(result.errors)
        required_dimensions = {
            str(item)
            for item in _as_sequence(column_coverage.get("required_type_dimensions"))
        }
        expected_dimensions = set(COMPLETE_COLUMN_TYPE_SELECTORS)
        if required_dimensions != expected_dimensions:
            missing = sorted(expected_dimensions - required_dimensions)
            unexpected = sorted(required_dimensions - expected_dimensions)
            detail = []
            if missing:
                detail.append("missing " + ", ".join(missing))
            if unexpected:
                detail.append("unexpected " + ", ".join(unexpected))
            result.errors.append(
                f"{path}: exhaustive column_type_coverage must declare all seven canonical dimensions"
                + (" (" + "; ".join(detail) + ")" if detail else "")
            )
        for selector in sorted(required_dimensions & expected_dimensions):
            selected = _resolve_selector(type_catalog, selector)
            if not selected:
                result.errors.append(
                    f"{path}: exhaustive column dimension is empty or unresolved: {selector}"
                )
        if column_coverage.get("expansion_mode") not in {"exhaustive", "expand_every_type"}:
            result.errors.append(f"{path}: exhaustive column_type_coverage must expand every type")
        if column_coverage.get("require_each_type_success_or_failure") is not True:
            result.errors.append(
                f"{path}: exhaustive column_type_coverage must classify every type as success or failure"
            )
        expansion_sources = {
            str(_as_mapping(axis).get("source") or "")
            for group in _baseline_groups(matrix)
            for axis in _as_mapping(group.get("expansion")).values()
            if _as_mapping(axis).get("mode") == "exhaustive"
        }
        expected_sources = {
            f"references/common/pg18_type_catalog.md#{selector}"
            for selector in expected_dimensions
        }
        missing_sources = sorted(expected_sources - expansion_sources)
        if missing_sources:
            result.errors.append(
                f"{path}: exhaustive column_type_coverage is missing direct inventory expansion(s): "
                + ", ".join(missing_sources)
            )
        if len(result.errors) == error_count:
            result.complete_column_scope_count += 1
    elif coverage_mode in {"representative", "conditional", "explicit"}:
        required_type_set = str(column_coverage.get("required_type_set") or "")
        type_set = _as_mapping(
            _as_mapping(type_catalog.get("type_sets")).get(required_type_set)
        )
        if not required_type_set or not type_set:
            result.errors.append(
                f"{path}: partial column_type_coverage must name a type set from pg18_type_catalog"
            )
        elif type_set.get("readiness") != "ready":
            result.errors.append(f"{path}: column type set {required_type_set} is not ready")
        if type_set.get("canonical") is False:
            result.warnings.append(
                f"{path}: deprecated non-canonical column type selector {required_type_set}"
            )
        result.partial_column_scope_count += 1
        result.warnings.append(
            f"{path}: partial column-type coverage ({coverage_mode}); it cannot satisfy an exhaustive feature-plan obligation"
        )
    else:
        result.errors.append(
            f"{path}: required column_type_coverage has incompatible coverage_mode {coverage_mode!r}"
        )


def _validate_object_relation_table_scope_evidence(
    result: AuditResult,
    root: Path,
    path: Path,
    matrix: Mapping[str, Any],
) -> None:
    coverage_scope = _as_mapping(matrix.get("coverage_scope"))
    specifications = (
        (
            "target_object_coverage",
            "required_object_kinds",
            {"object_kinds.all_object_kinds", "sql_object_types.all_sql_object_types"},
            "sql_object_types.all_sql_object_types",
        ),
        (
            "target_relation_coverage",
            "required_relation_kinds",
            {"relation_kinds.all_relation_kinds", "relation_kinds.all_pg18_relkinds"},
            "relation_kinds.all_pg18_relkinds",
        ),
        (
            "table_coverage",
            "required_table_kinds",
            {"table_kinds.all_table_kinds"},
            None,
        ),
    )
    inventory_path = (
        root
        / "skills"
        / "pg-sql-generation"
        / "references"
        / "combinations"
        / "_shared"
        / "coverage_inventory.yaml"
    )
    try:
        inventory = _load_yaml_file(inventory_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        result.errors.append(f"{path}: cannot load shared coverage inventory: {exc}")
        return

    for scope_name, inventory_field, accepted_selectors, canonical_selector in specifications:
        scope = _as_mapping(coverage_scope.get(scope_name))
        if scope.get("required") is not True:
            continue
        inventory_source = str(scope.get("inventory_source") or "")
        prefix = "references/combinations/_shared/coverage_inventory.yaml#"
        selector = inventory_source.removeprefix(prefix) if inventory_source.startswith(prefix) else ""
        if selector not in accepted_selectors:
            result.errors.append(
                f"{path}: required {scope_name} inventory_source must select one of: "
                + ", ".join(
                    prefix + item for item in sorted(accepted_selectors)
                )
            )
        values = _as_sequence(scope.get(inventory_field))
        if not values:
            result.errors.append(f"{path}: required {scope_name} must declare {inventory_field}")
        selected = _resolve_selector(inventory, selector) if selector else None
        allowed_values = {str(item) for item in _as_sequence(selected)}
        unknown_values = sorted({str(item) for item in values} - allowed_values)
        if unknown_values:
            result.errors.append(
                f"{path}: {scope_name}.{inventory_field} contains values outside canonical inventory: "
                + ", ".join(unknown_values)
            )
        mode = str(scope.get("coverage_mode") or "")
        if mode == "exhaustive":
            error_count = len(result.errors)
            if canonical_selector is None or selector != canonical_selector:
                result.errors.append(
                    f"{path}: exhaustive {scope_name} must use a canonical PostgreSQL 18.4 inventory selector"
                )
            declared_values = {str(item) for item in values}
            missing_values = sorted(allowed_values - declared_values)
            if missing_values:
                result.errors.append(
                    f"{path}: exhaustive {scope_name}.{inventory_field} omits canonical values: "
                    + ", ".join(missing_values)
                )
            expected_source = f"coverage_scope.{scope_name}.{inventory_field}"
            has_inventory_expansion = any(
                _as_mapping(axis).get("mode") == "exhaustive"
                and _as_mapping(axis).get("source") == expected_source
                for group in _baseline_groups(matrix)
                for axis in _as_mapping(group.get("expansion")).values()
            )
            if not has_inventory_expansion:
                result.errors.append(
                    f"{path}: exhaustive {scope_name} has no exhaustive group expansion sourced from {inventory_field}"
                )
            if len(result.errors) == error_count:
                result.exhaustive_object_relation_table_scope_count += 1
        elif mode in {"representative", "conditional"}:
            result.partial_object_relation_table_scope_count += 1
            result.warnings.append(
                f"{path}: partial {scope_name} ({mode}); it cannot satisfy an exhaustive feature-plan obligation"
            )
        elif mode != "explicit":
            result.errors.append(
                f"{path}: required {scope_name} has incompatible coverage_mode {mode!r}"
            )


def _validate_extension_policy(result: AuditResult, path: Path, matrix: Mapping[str, Any], schema: Mapping[str, Any]) -> None:
    execution_contract = _as_mapping(matrix.get("execution_contract"))
    policy = _as_mapping(matrix.get("post_coverage_extension_policy"))
    if execution_contract.get("allow_post_coverage_extension_inference") is True and not policy:
        result.errors.append(f"{path}: post_coverage_extension_policy is required when extension inference is enabled")
        return

    required_policy_keys = _as_sequence(schema.get("post_coverage_extension_policy_required_keys"))
    _add_missing_keys(result, path, "post_coverage_extension_policy", policy, required_policy_keys)

    expected_output = _as_mapping(schema.get("post_coverage_extension_policy_required_values")).get("output_location")
    if expected_output and policy.get("output_location") != expected_output:
        result.errors.append(f"{path}: post_coverage_extension_policy.output_location must be {expected_output}")

    required_fields = {str(item) for item in _as_sequence(schema.get("derived_extension_required_fields"))}
    declared_fields = {str(item) for item in _as_sequence(policy.get("required_fields"))}
    missing_fields = sorted(required_fields - declared_fields)
    if missing_fields:
        result.errors.append(f"{path}: post_coverage_extension_policy.required_fields missing: {', '.join(missing_fields)}")

    audit_rules = _as_mapping(matrix.get("audit_rules"))
    if audit_rules.get("forbid_extension_counting_toward_required_coverage") is True:
        for group in _as_sequence(matrix.get("combination_groups")):
            group_doc = _as_mapping(group)
            if group_doc.get("derived_extension") is True:
                result.errors.append(f"{path}: {group_doc.get('id') or '<missing id>'}: extension coverage cannot satisfy required coverage")


def audit_matrices(root: Path, matrix_paths: list[Path] | None = None) -> AuditResult:
    root = root.resolve()
    result = AuditResult()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"root does not exist or is not a directory: {root}")

    schema = _load_schema(root)
    statement_paths = _statement_paths(root)
    statements_by_key, statements_by_reference, statement_paths_by_key = _load_statements(root)
    auditing_complete_repository = matrix_paths is None
    selected_matrix_paths = (
        _default_matrix_paths(root) if matrix_paths is None else matrix_paths
    )
    paths = [
        path if path.is_absolute() else root / path
        for path in selected_matrix_paths
    ]

    if not statement_paths:
        result.errors.append(
            f"{root / STATEMENTS_ROOT}: statement reference directory is missing or empty"
        )
    if not paths:
        result.errors.append(
            f"{root / COMBINATIONS_ROOT}: combination matrix directory is missing or empty"
        )
    for key, duplicate_paths in sorted(statement_paths_by_key.items()):
        if len(duplicate_paths) > 1:
            result.errors.append(
                f"duplicate statement reference key {key}: "
                + ", ".join(str(path) for path in duplicate_paths)
            )

    matrix_paths_by_key: dict[str, list[Path]] = {}

    for matrix_path in paths:
        matrix_path = matrix_path.resolve()
        if "_shared" in matrix_path.parts:
            continue
        matrix = _load_yaml_file(matrix_path)
        result.matrix_count += 1
        _validate_matrix_shape(result, matrix_path, matrix, schema)
        matrix_statement = _as_mapping(matrix.get("statement"))
        matrix_key = _text(matrix_statement.get("key"))
        source_reference = _text(matrix_statement.get("source_reference"))
        if not matrix_key:
            result.errors.append(f"{matrix_path}: statement.key must be a non-empty string")
        else:
            matrix_paths_by_key.setdefault(matrix_key, []).append(matrix_path)
        statement_config = _matrix_statement_config(matrix, statements_by_reference)
        if statement_config is None:
            result.errors.append(
                f"{matrix_path}: statement.source_reference is not defined in statement references: "
                f"{source_reference or '<missing>'}"
            )
        else:
            source_key = _statement_key(statement_config)
            if matrix_key != source_key:
                result.errors.append(
                    f"{matrix_path}: statement.key {matrix_key!r} does not match "
                    f"source_reference statement.key {source_key!r}"
                )
            _validate_factors_against_statement(result, matrix_path, matrix, statement_config)
        _validate_failure_reasons(result, matrix_path, matrix)
        _validate_object_relation_table_scope_evidence(result, root, matrix_path, matrix)
        _validate_column_type_catalog(result, root, matrix_path, matrix)
        _validate_extension_policy(result, matrix_path, matrix, schema)

    for key, duplicate_paths in sorted(matrix_paths_by_key.items()):
        if len(duplicate_paths) > 1:
            result.errors.append(
                f"duplicate combination matrix statement key {key}: "
                + ", ".join(str(path) for path in duplicate_paths)
            )

    if auditing_complete_repository:
        statement_keys = set(statements_by_key)
        matrix_keys = set(matrix_paths_by_key)
        for key in sorted(statement_keys - matrix_keys):
            result.errors.append(f"statement reference has no combination matrix: {key}")
        for key in sorted(matrix_keys - statement_keys):
            result.errors.append(f"combination matrix has no statement reference: {key}")

    return result


def audit_root(root: Path) -> AuditResult:
    return audit_matrices(root, matrix_paths=None)


def audit_matrix(root: Path, matrix_path: Path) -> AuditResult:
    return audit_matrices(root, matrix_paths=[matrix_path])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit PostgreSQL 18.4 statement combination matrices.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="pg_case_factory project root")
    parser.add_argument("matrices", nargs="*", type=Path, help="matrix files to audit; defaults to all matrices")
    args = parser.parse_args(argv)

    try:
        result = audit_matrices(args.root, args.matrices or None)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}")
        print("FAIL combination matrix audit: matrices=0 groups=0 errors=1")
        return 1

    for warning in result.warnings:
        print(f"WARNING: {warning}")
    for error in result.errors:
        print(f"ERROR: {error}")

    if result.passed:
        print(
            f"PASS static declaration audit: matrices={result.matrix_count} groups={result.group_count} "
            f"column_scopes_exhaustive_validated={result.complete_column_scope_count} "
            f"column_scopes_partial_declared={result.partial_column_scope_count} "
            f"other_scopes_exhaustive_validated={result.exhaustive_object_relation_table_scope_count} "
            f"other_scopes_partial_declared={result.partial_object_relation_table_scope_count} "
            "rendered_sql_verified=0 runtime_verified=0"
        )
        return 0

    print(f"FAIL combination matrix audit: matrices={result.matrix_count} groups={result.group_count} errors={len(result.errors)}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
