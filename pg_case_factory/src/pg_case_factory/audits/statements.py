from __future__ import annotations

from pathlib import Path

from ._documents import as_list, as_mapping, factor_value_keys, load_statement_documents
from .models import AuditReport


def audit_statement_references(root: Path | str) -> AuditReport:
    root = Path(root)
    documents, report = load_statement_documents(root)
    paths_by_key: dict[str, list[Path]] = {}
    aliases_by_normalized_value: dict[str, list[tuple[str, Path]]] = {}
    statement_root = root / "skills" / "pg-sql-generation" / "references" / "statements"

    for document in documents:
        config = document.config
        path = document.path
        if config.get("kind") != "statement":
            report.error(
                "statement.invalid_kind",
                "structured_config.kind must be statement",
                path=path,
                root=root,
            )

        statement = as_mapping(config.get("statement"))
        key = str(statement.get("key") or "").strip()
        name = str(statement.get("name") or "").strip()
        if not key:
            report.error("statement.missing_key", "statement.key is required", path=path, root=root)
        else:
            paths_by_key.setdefault(key, []).append(path)
            if path.stem != key:
                report.error(
                    "statement.path_key_mismatch",
                    f"statement.key {key!r} must match filename {path.stem!r}",
                    path=path,
                    root=root,
                )
        if not name:
            report.error("statement.missing_name", "statement.name is required", path=path, root=root)

        try:
            relative_parts = path.relative_to(statement_root).parts
        except ValueError:
            relative_parts = ()
        if len(relative_parts) >= 3:
            expected_category, expected_domain = relative_parts[:2]
            if str(config.get("category") or "") != expected_category:
                report.error(
                    "statement.category_path_mismatch",
                    f"category must match path segment {expected_category!r}",
                    path=path,
                    root=root,
                )
            if str(config.get("domain") or "") != expected_domain:
                report.error(
                    "statement.domain_path_mismatch",
                    f"domain must match path segment {expected_domain!r}",
                    path=path,
                    root=root,
                )
        if key and str(config.get("skill_name") or "") != key:
            report.error(
                "statement.skill_name_mismatch",
                f"skill_name must equal statement.key {key!r}",
                path=path,
                root=root,
            )

        aliases = as_list(statement.get("aliases"))
        if not aliases:
            report.error(
                "statement.missing_aliases",
                "statement.aliases must contain at least one discovery alias",
                path=path,
                root=root,
            )
        for alias in aliases:
            normalized_alias = " ".join(str(alias).casefold().replace("_", " ").split())
            if normalized_alias:
                aliases_by_normalized_value.setdefault(normalized_alias, []).append((key, path))

        factors = as_mapping(config.get("factors"))
        factor_names = {str(item) for item in factors}
        if not factors:
            report.error(
                "statement.missing_factors",
                "statement must declare at least one factor",
                path=path,
                root=root,
            )
        for factor_name, factor_doc in factors.items():
            if not factor_value_keys(factor_doc):
                report.error(
                    "statement.factor_without_values",
                    f"factor {factor_name} must declare at least one value",
                    path=path,
                    root=root,
                )

        layered_factors: list[str] = []
        for layer in as_list(config.get("factor_layers")):
            for factor in as_list(as_mapping(layer).get("factors")):
                factor_key = str(factor)
                layered_factors.append(factor_key)
                if factor_key not in factor_names:
                    report.error(
                        "statement.unknown_layer_factor",
                        f"factor_layers references undefined factor: {factor_key}",
                        path=path,
                        root=root,
                    )
        for factor_name in sorted(factor_names - set(layered_factors)):
            report.warning(
                "statement.unlayered_factor",
                f"factor is not assigned to a T1-T6 layer: {factor_name}",
                path=path,
                root=root,
            )
        seen: set[str] = set()
        for factor_name in layered_factors:
            if factor_name in seen:
                report.error(
                    "statement.duplicate_layer_factor",
                    f"factor appears in more than one factor layer: {factor_name}",
                    path=path,
                    root=root,
                )
            seen.add(factor_name)

        coverage = as_mapping(config.get("coverage_policy"))
        coverage_factors = [
            str(item)
            for field in ("main_combination_axes", "non_main_factors")
            for item in as_list(coverage.get(field))
        ]
        for factor_name in coverage_factors:
            if factor_name not in factor_names:
                report.error(
                    "statement.unknown_coverage_factor",
                    f"coverage_policy references undefined factor: {factor_name}",
                    path=path,
                    root=root,
                )
        duplicate_coverage = sorted(
            set(as_list(coverage.get("main_combination_axes")))
            & set(as_list(coverage.get("non_main_factors")))
        )
        for factor_name in duplicate_coverage:
            report.error(
                "statement.ambiguous_coverage_factor",
                f"factor is both a main axis and a non-main factor: {factor_name}",
                path=path,
                root=root,
            )

        for factor_name, default_value in as_mapping(config.get("defaults")).items():
            normalized_name = str(factor_name)
            if normalized_name not in factor_names:
                report.error(
                    "statement.unknown_default_factor",
                    f"defaults references undefined factor: {normalized_name}",
                    path=path,
                    root=root,
                )
                continue
            values = factor_value_keys(factors[normalized_name])
            if str(default_value) not in values:
                report.error(
                    "statement.invalid_default_value",
                    f"default {normalized_name}={default_value!s} is not a declared factor value",
                    path=path,
                    root=root,
                )

    for key, paths in sorted(paths_by_key.items()):
        if len(paths) > 1:
            locations = ", ".join(path.relative_to(root).as_posix() for path in paths)
            for path in paths:
                report.error(
                    "statement.duplicate_key",
                    f"statement.key {key!r} is duplicated: {locations}",
                    path=path,
                    root=root,
                )

    for alias, entries in sorted(aliases_by_normalized_value.items()):
        statement_keys = sorted({key for key, _ in entries if key})
        if len(statement_keys) <= 1:
            continue
        locations = ", ".join(statement_keys)
        for _, path in dict.fromkeys(entries):
            report.warning(
                "statement.ambiguous_alias",
                f"normalized alias {alias!r} resolves to multiple statements: {locations}",
                path=path,
                root=root,
            )

    report.summary["statement_count"] = len(documents)
    return report
