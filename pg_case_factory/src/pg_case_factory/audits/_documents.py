from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from yaml.constructor import ConstructorError

from .models import AuditReport


YAML_BLOCK_PATTERN = re.compile(r"```yaml\s*(.*?)```", re.DOTALL)


class UniqueKeySafeLoader(yaml.SafeLoader):
    """SafeLoader variant that refuses silently overwritten YAML mapping keys."""


def _construct_unique_mapping(
    loader: UniqueKeySafeLoader,
    node: yaml.MappingNode,
    deep: bool = False,
) -> dict[Any, Any]:
    loader.flatten_mapping(node)
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as exc:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "found an unhashable mapping key",
                key_node.start_mark,
            ) from exc
        if duplicate:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeySafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


@dataclass(frozen=True)
class StatementDocument:
    path: Path
    config: dict[str, Any]
    raw_text: str

    @property
    def key(self) -> str:
        statement = self.config.get("statement")
        if isinstance(statement, Mapping):
            return str(statement.get("key") or "")
        return ""


def statement_paths(root: Path) -> list[Path]:
    base = root / "skills" / "pg-sql-generation" / "references" / "statements"
    return sorted(base.glob("**/*.md")) if base.exists() else []


def load_statement_documents(root: Path) -> tuple[list[StatementDocument], AuditReport]:
    report = AuditReport()
    documents: list[StatementDocument] = []
    for path in statement_paths(root):
        raw_text = path.read_text(encoding="utf-8")
        match = YAML_BLOCK_PATTERN.search(raw_text)
        if not match:
            report.error(
                "statement.missing_structured_config",
                "statement reference has no fenced YAML structured_config",
                path=path,
                root=root,
            )
            continue
        try:
            parsed = yaml.load(match.group(1), Loader=UniqueKeySafeLoader) or {}
        except yaml.YAMLError as exc:
            report.error(
                "statement.invalid_yaml",
                f"statement reference YAML cannot be parsed: {exc}",
                path=path,
                root=root,
            )
            continue
        if not isinstance(parsed, Mapping):
            report.error(
                "statement.invalid_structured_config",
                "statement YAML root must be a mapping",
                path=path,
                root=root,
            )
            continue
        config = parsed.get("structured_config", parsed)
        if not isinstance(config, Mapping):
            report.error(
                "statement.invalid_structured_config",
                "structured_config must be a mapping",
                path=path,
                root=root,
            )
            continue
        documents.append(StatementDocument(path=path, config=dict(config), raw_text=raw_text))
    return documents, report


def as_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def as_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def factor_value_keys(factor_doc: Any) -> set[str]:
    values: set[str] = set()
    for value in as_list(as_mapping(factor_doc).get("values")):
        if isinstance(value, Mapping):
            key = value.get("key")
        else:
            key = value
        if key is not None and str(key):
            values.add(str(key))
    return values
