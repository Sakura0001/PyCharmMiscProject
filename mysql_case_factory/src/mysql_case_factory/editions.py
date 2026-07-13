from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml


class EditionValidationError(ValueError):
    """Raised when an edition manifest is incomplete, inconsistent, or unsafe."""


@dataclass(frozen=True)
class EditionInventory:
    kind: str
    path: str
    sha256: str
    count: int


@dataclass(frozen=True)
class Edition:
    root: Path
    edition_id: str
    target_version: str
    target_version_num: int
    review_state: str
    oracle_engine: str
    oracle_exact_patch: bool
    skill_name: str
    skill_root: Path
    inventories: tuple[EditionInventory, ...]


_ALIASES = {
    "8.0.22": "mysql_8_0_22",
    "80022": "mysql_8_0_22",
    "mysql-community-8.0.22": "mysql_8_0_22",
    "8.0.41": "mysql_8_0_41",
    "80041": "mysql_8_0_41",
    "mysql-community-8.0.41": "mysql_8_0_41",
}
_VERSIONS = {
    "mysql-community-8.0.22": ("8.0.22", 80022, "mysql_8_0_22"),
    "mysql-community-8.0.41": ("8.0.41", 80041, "mysql_8_0_41"),
}
_TOP_KEYS = {
    "schema_version",
    "kind",
    "edition_id",
    "target_version",
    "target_version_num",
    "review_state",
    "oracle",
    "skill",
    "inventories",
}
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _mapping(value: Any, *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise EditionValidationError(f"{field} must be a mapping")
    return value


def _unknown_keys(mapping: Mapping[str, Any], allowed: set[str], *, field: str) -> None:
    unknown = sorted(set(mapping) - allowed)
    if unknown:
        raise EditionValidationError(f"{field} unknown keys: {', '.join(unknown)}")


def _contained(base: Path, relative: str, *, field: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise EditionValidationError(f"{field} must be a nonempty relative path")
    base = base.resolve()
    candidate = (base / relative).resolve()
    if candidate != base and base not in candidate.parents:
        raise EditionValidationError(f"{field} must be contained in edition root")
    return candidate


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_edition(repository_root: Path | str, alias: str) -> Path:
    try:
        directory = _ALIASES[alias]
    except (KeyError, TypeError):
        raise EditionValidationError(f"unsupported edition: {alias!r}") from None
    return (Path(repository_root).resolve() / "editions" / directory).resolve()


def load_edition(
    edition_root: Path | str,
    *,
    repository_root: Path | str,
    verify_files: bool = True,
) -> Edition:
    root = Path(edition_root).resolve()
    repository = Path(repository_root).resolve()
    if root != repository and repository not in root.parents:
        raise EditionValidationError("edition root must be contained in repository root")
    manifest_path = root / "edition.yaml"
    try:
        payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise EditionValidationError(f"cannot load edition manifest: {exc}") from exc
    manifest = _mapping(payload, field="edition")
    _unknown_keys(manifest, _TOP_KEYS, field="edition")
    if manifest.get("schema_version") != 1:
        raise EditionValidationError("schema_version must be 1")
    if manifest.get("kind") != "mysql_case_factory_edition":
        raise EditionValidationError("kind must be mysql_case_factory_edition")

    edition_id = manifest.get("edition_id")
    if edition_id not in _VERSIONS:
        raise EditionValidationError(f"unsupported edition_id: {edition_id!r}")
    expected_version, expected_num, expected_directory = _VERSIONS[edition_id]
    target_version = manifest.get("target_version")
    target_version_num = manifest.get("target_version_num")
    if (target_version, target_version_num, root.name) != (
        expected_version,
        expected_num,
        expected_directory,
    ):
        raise EditionValidationError(
            "edition_id, target_version, target_version_num, and directory must agree"
        )

    review_state = manifest.get("review_state")
    if review_state not in {"draft", "complete"}:
        raise EditionValidationError("review_state must be draft or complete")

    oracle = _mapping(manifest.get("oracle"), field="oracle")
    _unknown_keys(oracle, {"engine", "exact_patch"}, field="oracle")
    if oracle.get("engine") != "mysql-community-server" or not isinstance(
        oracle.get("exact_patch"), bool
    ):
        raise EditionValidationError("oracle must select mysql-community-server exact_patch")

    skill = _mapping(manifest.get("skill"), field="skill")
    _unknown_keys(skill, {"name", "root"}, field="skill")
    skill_name = skill.get("name")
    if not isinstance(skill_name, str) or not skill_name:
        raise EditionValidationError("skill.name must be a nonempty string")
    skill_root = _contained(root, skill.get("root"), field="skill.root")

    raw_inventories = manifest.get("inventories")
    if not isinstance(raw_inventories, list):
        raise EditionValidationError("inventories must be a list")
    inventories: list[EditionInventory] = []
    seen_paths: set[str] = set()
    for index, item in enumerate(raw_inventories):
        inventory = _mapping(item, field=f"inventories[{index}]")
        _unknown_keys(inventory, {"kind", "path", "sha256", "count"}, field=f"inventories[{index}]")
        kind = inventory.get("kind")
        path_text = inventory.get("path")
        digest = inventory.get("sha256")
        count = inventory.get("count")
        if not isinstance(kind, str) or not kind:
            raise EditionValidationError(f"inventories[{index}].kind must be nonempty")
        path = _contained(root, path_text, field=f"inventories[{index}].path")
        if path_text in seen_paths:
            raise EditionValidationError(f"duplicate inventory path: {path_text}")
        seen_paths.add(path_text)
        if not isinstance(digest, str) or not _HEX64.fullmatch(digest):
            raise EditionValidationError(f"inventories[{index}].sha256 must be lowercase SHA-256")
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise EditionValidationError(f"inventories[{index}].count must be a nonnegative integer")
        if verify_files:
            if not path.is_file() or path.is_symlink():
                raise EditionValidationError(f"inventory must be a regular file: {path_text}")
            actual = _sha256(path)
            if actual != digest:
                raise EditionValidationError(
                    f"inventory sha256 mismatch for {path_text}: expected {digest}, got {actual}"
                )
        inventories.append(EditionInventory(kind=kind, path=path_text, sha256=digest, count=count))

    if verify_files and (not skill_root.is_dir() or skill_root.is_symlink()):
        raise EditionValidationError("skill.root must be an existing regular directory")

    return Edition(
        root=root,
        edition_id=edition_id,
        target_version=target_version,
        target_version_num=target_version_num,
        review_state=review_state,
        oracle_engine=oracle["engine"],
        oracle_exact_patch=oracle["exact_patch"],
        skill_name=skill_name,
        skill_root=skill_root,
        inventories=tuple(inventories),
    )
