from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

from pg_case_factory.applicability import load_shipped_applicability_universe

from .artifacts import ArtifactBinding, build_artifact
from .errors import CoverageV2InventoryError
from .input_lock import InputSpec


INVENTORY_PATH = Path(
    "skills/pg-sql-generation/references/common/statement_support_inventory.yaml"
)
FACTOR_AUDIT_PATH = Path(
    "skills/pg-sql-generation/references/common/postgresql_18_4_factor_audit.tsv"
)
DESIGN_PATH = Path(
    "docs/superpowers/specs/2026-08-12-full-statement-regress-coverage-generation-design.md"
)
SKILL_ROOT = Path("skills/pg-sql-generation")


class _UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(
    loader: _UniqueKeyLoader,
    node: yaml.nodes.MappingNode,
    deep: bool = False,
) -> dict[Any, Any]:
    loader.flatten_mapping(node)
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in result
        except TypeError as exc:
            raise CoverageV2InventoryError("inventory YAML key is not scalar") from exc
        if duplicate:
            raise CoverageV2InventoryError(f"duplicate inventory YAML key {key!r}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def _load_yaml(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise CoverageV2InventoryError(f"{label} is missing")
    try:
        value = yaml.load(path.read_text(encoding="utf-8"), Loader=_UniqueKeyLoader)
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise CoverageV2InventoryError(f"cannot read {label}") from exc
    if not isinstance(value, dict):
        raise CoverageV2InventoryError(f"{label} root must be a mapping")
    return value


def _safe_relative(value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise CoverageV2InventoryError(f"{label} must be non-empty")
    pure = PurePosixPath(value)
    if pure.is_absolute() or any(part in ("", ".", "..") for part in pure.parts):
        raise CoverageV2InventoryError(f"{label} must be repository-relative")
    return Path(*pure.parts)


@dataclass(frozen=True)
class StatementInventoryEntry:
    ordinal: int
    statement_key: str
    reference_path: str
    matrix_path: str
    factor_count: int
    factor_value_count: int

    def as_record(self) -> dict[str, Any]:
        return {
            "ordinal": self.ordinal,
            "statement_key": self.statement_key,
            "reference_path": self.reference_path,
            "matrix_path": self.matrix_path,
            "factor_count": self.factor_count,
            "factor_value_count": self.factor_value_count,
        }


@dataclass(frozen=True)
class StatementInventory:
    repository_root: Path
    inventory_byte_sha256: str
    universe_semantic_sha256: str
    entries: tuple[StatementInventoryEntry, ...]

    @property
    def statement_keys(self) -> tuple[str, ...]:
        return tuple(entry.statement_key for entry in self.entries)

    @property
    def factor_count(self) -> int:
        return sum(entry.factor_count for entry in self.entries)

    @property
    def factor_value_count(self) -> int:
        return sum(entry.factor_value_count for entry in self.entries)


def discover_statement_inventory(repository_root: Path) -> StatementInventory:
    root = repository_root.resolve(strict=True)
    inventory_path = root.joinpath(INVENTORY_PATH)
    document = _load_yaml(inventory_path, "statement support inventory")
    if document.get("schema_version") != 1 or document.get("kind") != "statement_support_inventory":
        raise CoverageV2InventoryError("statement support inventory identity differs")
    rows = document.get("statements")
    if not isinstance(rows, list) or len(rows) != 183:
        raise CoverageV2InventoryError("statement support inventory must contain 183 rows")
    universe = load_shipped_applicability_universe(root)
    entries: list[StatementInventoryEntry] = []
    seen: set[str] = set()
    for ordinal, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise CoverageV2InventoryError("statement inventory row must be a mapping")
        key = row.get("statement_key")
        if not isinstance(key, str) or not key or key in seen:
            raise CoverageV2InventoryError("statement inventory key is missing or duplicated")
        seen.add(key)
        source = _safe_relative(row.get("source_reference"), f"{key}.source_reference")
        if source.parts[:2] != ("references", "statements") or source.suffix != ".md":
            raise CoverageV2InventoryError("statement source reference path is not canonical")
        reference = SKILL_ROOT.joinpath(source)
        matrix_source = Path("references", "combinations", *source.parts[2:]).with_suffix(
            ".yaml"
        )
        matrix = SKILL_ROOT.joinpath(matrix_source)
        if not root.joinpath(reference).is_file() or not root.joinpath(matrix).is_file():
            raise CoverageV2InventoryError(f"{key} reference or matrix is missing")
        matrix_document = _load_yaml(root.joinpath(matrix), f"{key} matrix")
        statement = matrix_document.get("statement")
        if not isinstance(statement, dict) or statement.get("key") != key:
            raise CoverageV2InventoryError(f"{key} matrix identity differs")
        statement_rows = universe.rows_for_statement(key)
        factor_count = row.get("factor_count")
        factor_value_count = row.get("factor_value_rows")
        actual_factor_count = len({item.factor for item in statement_rows})
        if factor_count != actual_factor_count or factor_value_count != len(statement_rows):
            raise CoverageV2InventoryError(f"{key} inventory counts differ from universe")
        entries.append(
            StatementInventoryEntry(
                ordinal=ordinal,
                statement_key=key,
                reference_path=reference.as_posix(),
                matrix_path=matrix.as_posix(),
                factor_count=actual_factor_count,
                factor_value_count=len(statement_rows),
            )
        )
    if tuple(universe.statement_keys) != tuple(entry.statement_key for entry in entries):
        raise CoverageV2InventoryError("inventory order differs from applicability universe")
    if (len(entries), sum(x.factor_count for x in entries), sum(x.factor_value_count for x in entries)) != (
        183,
        3357,
        9978,
    ):
        raise CoverageV2InventoryError("canonical inventory totals differ")
    return StatementInventory(
        repository_root=root,
        inventory_byte_sha256=hashlib.sha256(inventory_path.read_bytes()).hexdigest(),
        universe_semantic_sha256=universe.semantic_sha256,
        entries=tuple(entries),
    )


def build_statement_order_artifact(
    inventory: StatementInventory,
    *,
    global_input_lock: ArtifactBinding | None = None,
) -> dict[str, Any]:
    predecessors = () if global_input_lock is None else (global_input_lock,)
    return build_artifact(
        artifact_id="STATEMENT-ORDER-pg18_4",
        kind="statement-order",
        semantic_payload={
            "inventory_byte_sha256": inventory.inventory_byte_sha256,
            "universe_semantic_sha256": inventory.universe_semantic_sha256,
            "statement_count": len(inventory.entries),
            "factor_count": inventory.factor_count,
            "factor_value_count": inventory.factor_value_count,
            "statements": [entry.as_record() for entry in inventory.entries],
        },
        predecessors=predecessors,
    )


def _decoder_for(path: Path) -> str:
    if path.suffix == ".json":
        return "json-v1"
    if path.suffix in (".yaml", ".yml"):
        return "yaml-v1"
    return "raw-v1"


def _version_for(path: Path) -> str:
    text = path.as_posix()
    if "/schemas/" in text:
        return "coverage-v2-schema-v2"
    if text.startswith("src/pg_case_factory/coverage_v2/"):
        return "coverage-v2-code-v1"
    if "/references/statements/" in text:
        return "pg18.4-statement-reference-v1"
    if "/references/combinations/" in text:
        return "statement-combination-matrix-v1"
    if "/references/common/" in text:
        return "pg18.4-common-catalog-v1"
    if text.startswith("docs/superpowers/specs/"):
        return "full-statement-coverage-v2-spec"
    return "repository-input-v1"


def compile_global_input_specs(
    repository_root: Path,
    inventory: StatementInventory,
) -> tuple[InputSpec, ...]:
    root = repository_root.resolve(strict=True)
    paths: set[Path] = {INVENTORY_PATH, FACTOR_AUDIT_PATH, DESIGN_PATH, Path("pyproject.toml"), Path("uv.lock")}
    paths.update(Path(entry.reference_path) for entry in inventory.entries)
    paths.update(Path(entry.matrix_path) for entry in inventory.entries)
    common_root = root.joinpath("skills/pg-sql-generation/references/common")
    paths.update(path.relative_to(root) for path in common_root.iterdir() if path.is_file())
    coverage_root = root.joinpath("src/pg_case_factory/coverage_v2")
    paths.update(
        path.relative_to(root)
        for path in coverage_root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix in (".py", ".json")
    )
    source_root = root.joinpath("src/pg_case_factory")
    paths.update(
        path.relative_to(root)
        for path in source_root.glob("*_regress.py")
        if path.is_file()
    )
    skill_path = Path("skills/pg-sql-generation/SKILL.md")
    if root.joinpath(skill_path).is_file():
        paths.add(skill_path)
    ordered = sorted(paths, key=lambda item: item.as_posix().encode("utf-8"))
    for path in ordered:
        if not root.joinpath(path).is_file():
            raise CoverageV2InventoryError(f"global input is missing: {path.as_posix()}")
    return tuple(
        InputSpec(
            relative_path=path.as_posix(),
            version=_version_for(path),
            semantic_decoder_id=_decoder_for(path),  # type: ignore[arg-type]
        )
        for path in ordered
    )
