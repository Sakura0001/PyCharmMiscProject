from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import yaml


YAML_BLOCK_PATTERN = re.compile(r"```yaml\s*(.*?)```", re.DOTALL)
EXPECTED_SOURCE_CATALOG = "references/common/mysql80_factor_catalog.md"
REQUIRED_MAPPING_ENTRY_FIELDS = (
    "catalog_factor",
    "local_factor",
    "target_tier",
    "coverage_role",
    "value_policy",
    "reason",
)
ALLOWED_COVERAGE_ROLES = {
    "main_axis",
    "representative_or_main",
    "representative",
    "rotate_attach",
    "audit_only",
}
ALLOWED_VALUE_POLICIES = {
    "reuse_catalog_values",
    "statement_specific_subset",
    "statement_specific_override",
}


@dataclass
class AuditResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    mapped_count: int = 0
    excluded_count: int = 0

    @property
    def passed(self) -> bool:
        return not self.errors


def _load_structured_config(path: Path) -> dict:
    raw_text = path.read_text(encoding="utf-8")
    match = YAML_BLOCK_PATTERN.search(raw_text)
    if not match:
        raise ValueError(f"{path}: no fenced yaml block found")

    parsed = yaml.safe_load(match.group(1))
    if parsed is None:
        parsed = {}
    if not isinstance(parsed, Mapping):
        raise ValueError(f"{path}: structured yaml must be a mapping")

    if "structured_config" in parsed:
        structured_config = parsed["structured_config"]
        if not isinstance(structured_config, Mapping):
            raise ValueError(f"{path}: structured_config must be a mapping")
        config = dict(structured_config)
    else:
        config = dict(parsed)
    if not config:
        raise ValueError(f"{path}: empty structured config")
    return config


def _catalog_factor_paths(catalog_config: dict) -> set[str]:
    paths: set[str] = set()
    object_domains = dict(catalog_config.get("object_domains") or {})
    for domain_key, domain_doc in object_domains.items():
        domain_doc = dict(domain_doc or {})
        normalized_domain_key = str(domain_doc.get("key") or domain_key)
        factor_groups = dict(domain_doc.get("factor_groups") or {})
        for group_key, group_doc in factor_groups.items():
            group_doc = dict(group_doc or {})
            normalized_group_key = str(group_doc.get("key") or group_key)
            factors = dict(group_doc.get("factors") or {})
            for factor_key, factor_doc in factors.items():
                factor_doc = dict(factor_doc or {})
                normalized_factor_key = str(factor_doc.get("key") or factor_key)
                paths.add(f"{normalized_domain_key}.{normalized_group_key}.{normalized_factor_key}")
    return paths


def _catalog_domains(catalog_config: dict) -> set[str]:
    domains: set[str] = set()
    for domain_key, domain_doc in dict(catalog_config.get("object_domains") or {}).items():
        domain_doc = dict(domain_doc or {})
        domains.add(str(domain_doc.get("key") or domain_key))
    return domains


def _catalog_values(catalog_config: dict) -> dict[str, set[str]]:
    values_by_factor: dict[str, set[str]] = {}
    object_domains = dict(catalog_config.get("object_domains") or {})
    for domain_key, domain_doc in object_domains.items():
        domain_doc = dict(domain_doc or {})
        normalized_domain_key = str(domain_doc.get("key") or domain_key)
        factor_groups = dict(domain_doc.get("factor_groups") or {})
        for group_key, group_doc in factor_groups.items():
            group_doc = dict(group_doc or {})
            normalized_group_key = str(group_doc.get("key") or group_key)
            factors = dict(group_doc.get("factors") or {})
            for factor_key, factor_doc in factors.items():
                factor_doc = dict(factor_doc or {})
                normalized_factor_key = str(factor_doc.get("key") or factor_key)
                factor_path = f"{normalized_domain_key}.{normalized_group_key}.{normalized_factor_key}"
                values_by_factor[factor_path] = {
                    str(dict(item).get("key"))
                    for item in list(factor_doc.get("values") or [])
                    if isinstance(item, dict) and dict(item).get("key")
                }
    return values_by_factor


def _factor_tiers(statement_config: dict) -> dict[str, str]:
    tiers: dict[str, str] = {}
    for layer in list(statement_config.get("factor_layers") or []):
        layer = dict(layer or {})
        tier = str(layer.get("tier") or "")
        for factor in list(layer.get("factors") or []):
            tiers[str(factor)] = tier
    return tiers


def _statement_factor_names(statement_config: dict) -> set[str]:
    return {str(name) for name in dict(statement_config.get("factors") or {}).keys()}


def _coverage_sets(statement_config: dict) -> tuple[set[str], set[str]]:
    coverage_policy = dict(statement_config.get("coverage_policy") or {})
    main_axes = {str(item) for item in list(coverage_policy.get("main_combination_axes") or [])}
    non_main = {str(item) for item in list(coverage_policy.get("non_main_factors") or [])}
    return main_axes, non_main


def _mapping_entries(mapping: dict) -> Iterable[tuple[str, dict]]:
    for item in list(mapping.get("imported_factors") or []):
        yield "imported_factors", dict(item or {})
    for item in list(mapping.get("promoted_factors") or []):
        yield "promoted_factors", dict(item or {})


def _text_field(data: dict, field_name: str) -> str:
    return str(data.get(field_name) or "").strip()


def _validate_required_mapping_fields(result: AuditResult, prefix: str, entry: dict) -> None:
    for field_name in REQUIRED_MAPPING_ENTRY_FIELDS:
        if not _text_field(entry, field_name):
            result.errors.append(f"{prefix}: {field_name} is required")


def _validate_mapping_entry(
    result: AuditResult,
    statement_path: Path,
    section: str,
    entry: dict,
    catalog_paths: set[str],
    catalog_values: dict[str, set[str]],
    factor_names: set[str],
    factor_tiers: dict[str, str],
    main_axes: set[str],
    non_main: set[str],
) -> None:
    catalog_factor = _text_field(entry, "catalog_factor")
    local_factor = _text_field(entry, "local_factor")
    target_tier = _text_field(entry, "target_tier")
    coverage_role = _text_field(entry, "coverage_role")
    value_policy = _text_field(entry, "value_policy")
    prefix = f"{statement_path}: {section}: {catalog_factor or '<missing catalog_factor>'}"

    _validate_required_mapping_fields(result, prefix, entry)

    if catalog_factor and catalog_factor not in catalog_paths:
        result.errors.append(f"{prefix}: catalog factor is not defined")
    if not local_factor:
        result.mapped_count += 1
        return
    if local_factor not in factor_names:
        result.errors.append(f"{prefix}: local factor is not defined: {local_factor}")

    actual_tier = factor_tiers.get(local_factor)
    if target_tier and actual_tier and target_tier != actual_tier:
        result.errors.append(f"{prefix}: target_tier {target_tier} does not match factor_layers tier {actual_tier} for {local_factor}")
    if target_tier and local_factor in factor_names and local_factor not in factor_tiers:
        result.errors.append(f"{prefix}: local factor {local_factor} is not listed in factor_layers")

    if coverage_role and coverage_role not in ALLOWED_COVERAGE_ROLES:
        result.errors.append(f"{prefix}: unsupported coverage_role {coverage_role}")
    if value_policy and value_policy not in ALLOWED_VALUE_POLICIES:
        result.errors.append(f"{prefix}: unsupported value_policy {value_policy}")

    if coverage_role == "main_axis" and local_factor not in main_axes:
        result.errors.append(f"{prefix}: main_axis factor must be listed in main_combination_axes: {local_factor}")
    if coverage_role == "rotate_attach" and local_factor not in non_main:
        result.errors.append(f"{prefix}: rotate_attach factor must be listed in non_main_factors: {local_factor}")
    if coverage_role == "representative_or_main" and local_factor not in main_axes and local_factor not in non_main:
        result.errors.append(f"{prefix}: representative_or_main factor must be in main_combination_axes or non_main_factors: {local_factor}")
    if coverage_role == "representative" and local_factor not in main_axes and local_factor not in non_main:
        result.warnings.append(f"{prefix}: representative factor is not listed in coverage_policy: {local_factor}")

    selected_values = [str(item) for item in list(entry.get("selected_values") or [])]
    if value_policy == "statement_specific_subset" and not selected_values:
        result.errors.append(f"{prefix}: statement_specific_subset requires selected_values")
    if selected_values and catalog_factor in catalog_values:
        unknown_values = sorted(set(selected_values) - catalog_values[catalog_factor])
        if unknown_values:
            result.errors.append(f"{prefix}: selected_values not found in catalog: {', '.join(unknown_values)}")

    result.mapped_count += 1


def _validate_statement_mapping(
    result: AuditResult,
    statement_path: Path,
    statement_config: dict,
    catalog_domains: set[str],
    catalog_paths: set[str],
    catalog_values: dict[str, set[str]],
) -> None:
    mapping = dict(statement_config.get("factor_catalog_mapping") or {})
    if not mapping:
        return

    source_catalog = _text_field(mapping, "source_catalog")
    if not source_catalog:
        result.errors.append(f"{statement_path}: factor_catalog_mapping.source_catalog is required")
    elif source_catalog != EXPECTED_SOURCE_CATALOG:
        result.errors.append(
            f"{statement_path}: factor_catalog_mapping.source_catalog must be {EXPECTED_SOURCE_CATALOG}: {source_catalog}"
        )

    object_domain = str(mapping.get("object_domain") or "")
    if object_domain not in catalog_domains:
        result.errors.append(f"{statement_path}: factor_catalog_mapping.object_domain is not in catalog: {object_domain}")

    factor_names = _statement_factor_names(statement_config)
    factor_tiers = _factor_tiers(statement_config)
    main_axes, non_main = _coverage_sets(statement_config)

    for section, entry in _mapping_entries(mapping):
        _validate_mapping_entry(
            result,
            statement_path,
            section,
            entry,
            catalog_paths,
            catalog_values,
            factor_names,
            factor_tiers,
            main_axes,
            non_main,
        )

    for item in list(mapping.get("excluded_factors") or []):
        item = dict(item or {})
        catalog_factor = str(item.get("catalog_factor") or "")
        reason = str(item.get("reason") or "").strip()
        prefix = f"{statement_path}: excluded_factors: {catalog_factor or '<missing catalog_factor>'}"
        if catalog_factor not in catalog_paths:
            result.errors.append(f"{prefix}: catalog factor is not defined")
        if not reason:
            result.errors.append(f"{prefix}: reason is required")
        result.excluded_count += 1


def audit_paths(catalog_path: Path, statement_paths: list[Path]) -> AuditResult:
    result = AuditResult()
    catalog_config = _load_structured_config(catalog_path)
    catalog_paths = _catalog_factor_paths(catalog_config)
    catalog_domains = _catalog_domains(catalog_config)
    catalog_values = _catalog_values(catalog_config)

    if not catalog_paths:
        result.errors.append(f"{catalog_path}: catalog contains no factors")

    for statement_path in statement_paths:
        statement_config = _load_structured_config(statement_path)
        _validate_statement_mapping(
            result,
            statement_path,
            statement_config,
            catalog_domains,
            catalog_paths,
            catalog_values,
        )

    return result


def _default_statement_paths(root: Path) -> list[Path]:
    return sorted((root / "skills" / "mysql-sql-generation" / "references" / "statements").glob("**/*.md"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit MySQL 8.0.22 factor catalog mappings in statement references.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="mysql_case_factory project root",
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=None,
        help="factor catalog path; defaults to skills/mysql-sql-generation/references/common/mysql80_factor_catalog.md",
    )
    parser.add_argument(
        "statements",
        nargs="*",
        type=Path,
        help="statement reference files to audit; defaults to all statement references",
    )
    args = parser.parse_args(argv)

    root = args.root.resolve()
    catalog_path = args.catalog or root / "skills" / "mysql-sql-generation" / "references" / "common" / "mysql80_factor_catalog.md"
    statement_paths = args.statements or _default_statement_paths(root)
    try:
        result = audit_paths(catalog_path, [path.resolve() for path in statement_paths])
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}")
        print("FAIL factor catalog mapping audit: mapped=0 excluded=0 errors=1")
        return 1

    for warning in result.warnings:
        print(f"WARNING: {warning}")
    for error in result.errors:
        print(f"ERROR: {error}")

    if result.passed:
        print(f"PASS factor catalog mapping audit: mapped={result.mapped_count} excluded={result.excluded_count}")
        return 0

    print(f"FAIL factor catalog mapping audit: mapped={result.mapped_count} excluded={result.excluded_count} errors={len(result.errors)}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
