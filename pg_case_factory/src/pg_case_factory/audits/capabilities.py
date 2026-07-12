from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from ._documents import as_mapping, factor_value_keys, load_statement_documents
from .models import AuditReport, CapabilityRecord
from .placeholders import template_fields
from ..renderer import BUILTIN_NAME_CONTEXT_FIELDS


CAPABILITY_LEVELS = ("reference_only", "renderable", "executable", "runtime_verified")


def _is_canonical_binding(value: Any) -> bool:
    binding = as_mapping(value)
    return "factor" in binding and isinstance(binding.get("values"), Mapping) and bool(binding.get("values"))


def _load_inventory(root: Path, report: AuditReport) -> dict[str, dict[str, Any]]:
    path = (
        root
        / "skills"
        / "pg-sql-generation"
        / "references"
        / "common"
        / "statement_support_inventory.yaml"
    )
    if not path.exists():
        return {}
    try:
        parsed = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        report.error(
            "capability.invalid_inventory",
            f"statement support inventory cannot be parsed: {exc}",
            path=path,
            root=root,
        )
        return {}
    if not isinstance(parsed, Mapping):
        report.error(
            "capability.invalid_inventory",
            "statement support inventory must be a mapping",
            path=path,
            root=root,
        )
        return {}
    entries = parsed.get("statements", {})
    if isinstance(entries, list):
        return {
            str(item.get("statement_key")): dict(item)
            for item in entries
            if isinstance(item, Mapping) and item.get("statement_key")
        }
    if isinstance(entries, Mapping):
        return {str(key): as_mapping(value) for key, value in entries.items()}
    return {}


def _derived_renderable(config: dict[str, Any]) -> tuple[bool, list[str]]:
    rendering = as_mapping(config.get("rendering"))
    statement_template = str(rendering.get("statement_template") or "")
    if not statement_template:
        return False, ["missing statement_template"]

    fields: set[str] = set()
    reasons: list[str] = []
    for template_name in ("statement_template", "verification_query_template"):
        template = str(rendering.get(template_name) or "")
        if not template:
            continue
        template_field_names, error = template_fields(template)
        if error:
            reasons.append(f"invalid {template_name}: {error}")
            continue
        fields.update(template_field_names)

    bindings = as_mapping(rendering.get("factor_value_bindings"))
    factors = as_mapping(config.get("factors"))
    invalid_bindings = sorted(
        str(binding_name)
        for binding_name, binding in bindings.items()
        if not _is_canonical_binding(binding)
    )
    if invalid_bindings:
        reasons.append(f"legacy or invalid bindings: {', '.join(invalid_bindings)}")

    incomplete_bindings: list[str] = []
    unresolved_binding_fields: set[str] = set()
    available_fields = set(BUILTIN_NAME_CONTEXT_FIELDS)
    for binding_name, raw_binding in bindings.items():
        if not _is_canonical_binding(raw_binding):
            continue
        binding = as_mapping(raw_binding)
        factor_name = str(binding.get("factor") or "")
        if factor_name not in factors:
            incomplete_bindings.append(str(binding_name))
            continue
        mapped_values = {str(value) for value in as_mapping(binding.get("values"))}
        if factor_value_keys(factors[factor_name]) - mapped_values:
            incomplete_bindings.append(str(binding_name))
        for raw_value in as_mapping(binding.get("values")).values():
            nested_fields, error = template_fields(str(raw_value))
            if error:
                reasons.append(f"invalid binding template {binding_name}: {error}")
                continue
            unresolved_binding_fields.update(nested_fields - available_fields)
        available_fields.add(str(binding_name))
    if incomplete_bindings:
        reasons.append(f"incomplete bindings: {', '.join(sorted(incomplete_bindings))}")
    if unresolved_binding_fields:
        reasons.append(
            "unresolved binding placeholders: " + ", ".join(sorted(unresolved_binding_fields))
        )

    unresolved = sorted(fields - available_fields)
    if unresolved:
        reasons.append(f"unresolved placeholders: {', '.join(unresolved)}")
    return not reasons, reasons


def audit_capabilities(root: Path | str) -> AuditReport:
    root = Path(root)
    documents, report = load_statement_documents(root)
    inventory = _load_inventory(root, report)
    records: list[CapabilityRecord] = []
    known_keys = {document.key for document in documents if document.key}

    for unknown_key in sorted(set(inventory) - known_keys):
        report.error(
            "capability.unknown_statement",
            f"support inventory references unknown statement: {unknown_key}",
        )

    for document in documents:
        key = document.key or document.path.stem
        renderable, reasons = _derived_renderable(document.config)
        level = "renderable" if renderable else "reference_only"
        evidence: tuple[str, ...] = ()
        explicit = inventory.get(key, {})
        explicit_level = str(explicit.get("level") or explicit.get("support_level") or "")
        explicit_evidence = explicit.get("evidence") or []
        if isinstance(explicit_evidence, str):
            explicit_evidence = [explicit_evidence]
        evidence = tuple(str(item) for item in explicit_evidence if str(item).strip())
        if explicit_level:
            if explicit_level not in CAPABILITY_LEVELS:
                report.error(
                    "capability.invalid_level",
                    f"unsupported capability level {explicit_level!r} for {key}",
                    path=document.path,
                    root=root,
                )
            elif explicit_level in {"executable", "runtime_verified"} and not evidence:
                report.error(
                    "capability.missing_evidence",
                    f"{explicit_level} capability for {key} requires evidence",
                    path=document.path,
                    root=root,
                )
            elif explicit_level == "renderable" and not renderable:
                report.error(
                    "capability.overstated_level",
                    f"inventory marks {key} renderable but static rendering prerequisites are not met",
                    path=document.path,
                    root=root,
                )
            else:
                level = explicit_level
                reasons = [str(item) for item in explicit.get("reasons") or reasons]
        records.append(
            CapabilityRecord(
                statement_key=key,
                level=level,
                path=document.path.relative_to(root).as_posix(),
                reasons=tuple(reasons),
                evidence=evidence,
            )
        )

    report.capabilities = sorted(records, key=lambda item: item.statement_key)
    counts = {level: 0 for level in CAPABILITY_LEVELS}
    for record in records:
        counts[record.level] += 1
    report.summary["capability_counts"] = counts
    return report
