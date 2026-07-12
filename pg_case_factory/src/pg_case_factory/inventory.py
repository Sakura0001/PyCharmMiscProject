"""Resolve and verify immutable coverage-inventory snapshots.

An inventory source is either ``inline:<name>`` for a feature-local,
non-canonical axis, or ``<path>#<selector>`` for a repository inventory.  File
sources are always resolved beneath an explicit root and are compared with the
axis snapshot by ordered, type-aware canonical bytes.  A plan therefore cannot
claim complete coverage while quietly listing only a subset of its source.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping, Sequence, Union

import yaml

from .contracts import (
    ContractValidationError,
    CoveragePlan,
    _SCALAR_TYPES,
    _UniqueKeySafeLoader,
    _inventory_values_payload,
    inventory_values_sha256,
)


_MARKDOWN_YAML_FENCE = re.compile(
    r"(?ms)^[ \t]*(?P<fence>`{3,}|~{3,})(?:yaml|yml)"
    r"(?:[ \t]+[^\r\n]*)?[ \t]*\r?\n"
    r"(?P<body>.*?)"
    r"^[ \t]*(?P=fence)[ \t]*$"
)
_MISSING = object()


def _load_yaml(text: str, location: str) -> Any:
    try:
        return yaml.load(text, Loader=_UniqueKeySafeLoader)
    except ContractValidationError:
        raise
    except yaml.YAMLError as exc:
        raise ContractValidationError(f"invalid YAML inventory {location}: {exc}") from exc


def _split_source(inventory_source: str) -> tuple[str, tuple[str, ...]]:
    if inventory_source.count("#") != 1:
        raise ContractValidationError(
            "inventory source must use <path>#<selector> with exactly one #"
        )
    source_path, selector = inventory_source.split("#", 1)
    if not source_path.strip():
        raise ContractValidationError("inventory source path must not be empty")
    if not selector.strip():
        raise ContractValidationError("inventory source selector must not be empty")
    parts = tuple(selector.split("."))
    if any(not part or part.strip() != part for part in parts):
        raise ContractValidationError(
            f"inventory selector {selector!r} must be dot-separated non-empty keys"
        )
    return source_path, parts


def _contained_source_path(inventory_root: Union[str, Path], source_path: str) -> Path:
    root = Path(inventory_root).expanduser()
    try:
        resolved_root = root.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ContractValidationError(
            f"cannot resolve inventory_root {root}: {exc}"
        ) from exc
    if not resolved_root.is_dir():
        raise ContractValidationError(f"inventory_root is not a directory: {resolved_root}")

    unresolved = Path(source_path)
    candidate = unresolved if unresolved.is_absolute() else resolved_root / unresolved
    try:
        resolved = candidate.resolve(strict=False)
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise ContractValidationError(
            f"inventory source is outside inventory_root: {source_path}"
        ) from exc
    except (OSError, RuntimeError) as exc:
        raise ContractValidationError(
            f"cannot resolve inventory source {source_path}: {exc}"
        ) from exc

    if not resolved.exists():
        raise ContractValidationError(f"inventory source does not exist: {source_path}")
    if not resolved.is_file():
        raise ContractValidationError(f"inventory source is not a file: {source_path}")
    return resolved


def _select(document: Any, selector: Sequence[str]) -> Any:
    selected = document
    for part in selector:
        if not isinstance(selected, Mapping) or part not in selected:
            return _MISSING
        selected = selected[part]
    return selected


def _read_source_documents(path: Path) -> tuple[Any, ...]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ContractValidationError(f"cannot read inventory source {path}: {exc}") from exc

    suffix = path.suffix.lower()
    if suffix in (".yaml", ".yml"):
        return (_load_yaml(text, str(path)),)
    if suffix in (".md", ".markdown"):
        matches = tuple(_MARKDOWN_YAML_FENCE.finditer(text))
        if not matches:
            raise ContractValidationError(
                f"Markdown inventory source has no fenced YAML document: {path}"
            )
        return tuple(
            _load_yaml(match.group("body"), f"{path} YAML fence {index}")
            for index, match in enumerate(matches, start=1)
        )
    raise ContractValidationError(
        f"unsupported inventory source format {path.suffix or '<none>'}: {path}"
    )


def _inventory_values(selected: Any, source: str) -> tuple[Any, ...]:
    # A mapping inventory denotes its keys (for example the type keys in
    # structured_config.types); a sequence inventory denotes its items.
    if isinstance(selected, Mapping):
        values = tuple(selected.keys())
    elif isinstance(selected, Sequence) and not isinstance(selected, (str, bytes)):
        values = tuple(selected)
    else:
        raise ContractValidationError(
            f"resolved inventory {source} must be a sequence or mapping"
        )
    if not values:
        raise ContractValidationError(f"resolved inventory {source} must not be empty")
    if any(type(value) not in _SCALAR_TYPES for value in values):
        raise ContractValidationError(
            f"resolved inventory {source} must contain only YAML scalars"
        )
    # Reuse the contract's canonical encoder both as a scalar validation guard
    # and to keep resolver and snapshot hashing semantics identical.
    _inventory_values_payload(values)
    return values


def resolve_inventory_values(
    inventory_source: str,
    inventory_root: Union[str, Path],
) -> tuple[Any, ...]:
    """Resolve one ``<path>#<selector>`` source to ordered scalar values.

    YAML selectors may resolve to a sequence or mapping.  Mapping keys become
    the inventory values in source order.  Inline sources have no external
    inventory and are intentionally rejected by this low-level resolver.
    """

    if not isinstance(inventory_source, str) or not inventory_source.strip():
        raise ContractValidationError("inventory source must be a non-empty string")
    if inventory_source.startswith("inline:"):
        raise ContractValidationError(
            "inline inventory sources do not resolve to repository inventories"
        )
    source_path, selector = _split_source(inventory_source)
    path = _contained_source_path(inventory_root, source_path)
    matches = []
    for document in _read_source_documents(path):
        selected = _select(document, selector)
        if selected is not _MISSING:
            matches.append(selected)
    dotted_selector = ".".join(selector)
    if not matches:
        raise ContractValidationError(
            f"inventory selector {dotted_selector!r} was not found in {source_path}"
        )
    if len(matches) != 1:
        raise ContractValidationError(
            f"inventory selector {dotted_selector!r} is ambiguous in {source_path}"
        )
    return _inventory_values(matches[0], inventory_source)


def verify_inventory_sources(
    plan: CoveragePlan,
    inventory_root: Union[str, Path],
) -> None:
    """Verify every axis snapshot against its external inventory source.

    ``inline:`` is accepted only for axes that are not the evidence for one of
    the four canonical scope decisions.  External inventories must match the
    declared value order, scalar types, count, and SHA-256 exactly.
    """

    canonical_axes = {
        axis_id
        for decision in plan.scope_decisions.values()
        if decision.status == "complete"
        for axis_id in decision.axes
    }
    issues: list[str] = []
    for axis_id, axis in plan.axes.items():
        source = axis.inventory_source
        if source.startswith("inline:"):
            if not source.removeprefix("inline:").strip():
                issues.append(
                    f"coverage axis {axis_id} inline inventory source must have a name"
                )
            if axis_id in canonical_axes:
                issues.append(
                    f"coverage axis {axis_id} cannot use inline inventory for a canonical scope"
                )
            continue
        try:
            resolved = resolve_inventory_values(source, inventory_root)
        except ContractValidationError as exc:
            issues.extend(
                f"coverage axis {axis_id}: {issue}" for issue in exc.issues
            )
            continue

        resolved_count = len(resolved)
        resolved_sha256 = inventory_values_sha256(resolved)
        if (
            _inventory_values_payload(resolved) != _inventory_values_payload(axis.values)
            or resolved_count != axis.inventory_count
            or resolved_sha256 != axis.inventory_sha256
        ):
            issues.append(
                f"coverage axis {axis_id} does not exactly match resolved inventory "
                f"{source} (resolved count={resolved_count}, sha256={resolved_sha256}; "
                f"declared count={axis.inventory_count}, sha256={axis.inventory_sha256})"
            )

    if issues:
        raise ContractValidationError(issues)


__all__ = ["resolve_inventory_values", "verify_inventory_sources"]
