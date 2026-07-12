from __future__ import annotations

from pathlib import Path
from string import Formatter
from typing import Any

from ._documents import as_mapping, factor_value_keys, load_statement_documents
from .models import AuditReport
from ..renderer import BUILTIN_NAME_CONTEXT_FIELDS


def template_fields(template: str) -> tuple[set[str], str | None]:
    fields: set[str] = set()
    if not template:
        return fields, None
    try:
        for _, field_name, _, _ in Formatter().parse(template):
            if field_name is None:
                continue
            normalized = field_name.split(".", 1)[0].split("[", 1)[0]
            if normalized:
                fields.add(normalized)
    except ValueError as exc:
        return set(), str(exc)
    return fields, None


def _canonical_binding(spec: Any) -> bool:
    binding = as_mapping(spec)
    return bool(binding) and "factor" in binding and "values" in binding


def audit_placeholders(root: Path | str) -> AuditReport:
    root = Path(root)
    documents, report = load_statement_documents(root)
    checked_templates = 0
    for document in documents:
        factors = as_mapping(document.config.get("factors"))
        rendering = as_mapping(document.config.get("rendering"))
        bindings = as_mapping(rendering.get("factor_value_bindings"))

        canonical_bindings: set[str] = set()
        legacy_bindings: set[str] = set()
        for placeholder, raw_spec in bindings.items():
            placeholder = str(placeholder)
            if not _canonical_binding(raw_spec):
                legacy_bindings.add(placeholder)
                report.warning(
                    "placeholder.legacy_binding",
                    f"binding {placeholder!r} uses the legacy direct value-map shape",
                    path=document.path,
                    root=root,
                )
                continue
            canonical_bindings.add(placeholder)
            spec = as_mapping(raw_spec)
            factor_name = str(spec.get("factor") or "")
            if factor_name not in factors:
                report.error(
                    "placeholder.unknown_factor",
                    f"binding {placeholder!r} references undefined factor {factor_name!r}",
                    path=document.path,
                    root=root,
                )
                continue
            values = as_mapping(spec.get("values"))
            if not values:
                report.error(
                    "placeholder.empty_values",
                    f"binding {placeholder!r} must contain a non-empty values mapping",
                    path=document.path,
                    root=root,
                )
                continue
            missing_values = sorted(factor_value_keys(factors[factor_name]) - {str(key) for key in values})
            if missing_values:
                report.warning(
                    "placeholder.incomplete_binding",
                    f"binding {placeholder!r} does not map factor values: {', '.join(missing_values)}",
                    path=document.path,
                    root=root,
                )

        all_fields: set[str] = set()
        for template_name in ("statement_template", "verification_query_template"):
            template = str(rendering.get(template_name) or "")
            if not template:
                continue
            checked_templates += 1
            fields, error = template_fields(template)
            if error:
                report.error(
                    "placeholder.invalid_template",
                    f"{template_name} is not a valid Python format template: {error}",
                    path=document.path,
                    root=root,
                )
                continue
            all_fields.update(fields)

        for field_name in sorted(
            all_fields - canonical_bindings - legacy_bindings - BUILTIN_NAME_CONTEXT_FIELDS
        ):
            report.warning(
                "placeholder.unresolved",
                f"template placeholder has no declared binding or resolver: {field_name}",
                path=document.path,
                root=root,
            )
        for binding_name in sorted(set(bindings) - all_fields):
            report.warning(
                "placeholder.unused_binding",
                f"binding is not used by a rendering template: {binding_name}",
                path=document.path,
                root=root,
            )

    report.summary["template_count"] = checked_templates
    return report
