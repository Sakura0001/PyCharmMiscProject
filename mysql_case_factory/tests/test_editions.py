from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml

from mysql_case_factory.editions import EditionValidationError, load_edition, resolve_edition


ROOT = Path(__file__).resolve().parents[1]


def test_loads_both_repository_editions() -> None:
    edition_22 = load_edition(
        ROOT / "editions" / "mysql_8_0_22",
        repository_root=ROOT,
        verify_files=False,
    )
    edition_41 = load_edition(
        ROOT / "editions" / "mysql_8_0_41",
        repository_root=ROOT,
        verify_files=False,
    )

    assert (edition_22.edition_id, edition_22.target_version, edition_22.target_version_num) == (
        "mysql-community-8.0.22",
        "8.0.22",
        80022,
    )
    assert (edition_41.edition_id, edition_41.target_version, edition_41.target_version_num) == (
        "mysql-community-8.0.41",
        "8.0.41",
        80041,
    )


@pytest.mark.parametrize(
    ("alias", "directory"),
    [
        ("8.0.22", "mysql_8_0_22"),
        ("80022", "mysql_8_0_22"),
        ("mysql-community-8.0.22", "mysql_8_0_22"),
        ("8.0.41", "mysql_8_0_41"),
        ("80041", "mysql_8_0_41"),
        ("mysql-community-8.0.41", "mysql_8_0_41"),
    ],
)
def test_resolves_only_closed_aliases(alias: str, directory: str) -> None:
    assert resolve_edition(ROOT, alias) == (ROOT / "editions" / directory).resolve()


@pytest.mark.parametrize("alias", ["8.0", "latest", "8041", "mysql-8.0.41", ""])
def test_rejects_rolling_or_ambiguous_aliases(alias: str) -> None:
    with pytest.raises(EditionValidationError, match="unsupported edition"):
        resolve_edition(ROOT, alias)


def _write_minimal_edition(root: Path, *, extra: dict[str, object] | None = None) -> Path:
    edition_root = root / "editions" / "mysql_8_0_22"
    skill_root = edition_root / "skills" / "mysql-8-0-22-sql-generation"
    skill_root.mkdir(parents=True)
    skill = skill_root / "SKILL.md"
    skill.write_text("# Test skill\n", encoding="utf-8")
    digest = hashlib.sha256(skill.read_bytes()).hexdigest()
    payload: dict[str, object] = {
        "schema_version": 1,
        "kind": "mysql_case_factory_edition",
        "edition_id": "mysql-community-8.0.22",
        "target_version": "8.0.22",
        "target_version_num": 80022,
        "review_state": "complete",
        "oracle": {"engine": "mysql-community-server", "exact_patch": True},
        "skill": {
            "name": "mysql-8-0-22-sql-generation",
            "root": "skills/mysql-8-0-22-sql-generation",
        },
        "inventories": [
            {
                "kind": "skill_entry",
                "path": "skills/mysql-8-0-22-sql-generation/SKILL.md",
                "sha256": digest,
                "count": 1,
            }
        ],
    }
    if extra:
        payload.update(extra)
    (edition_root / "edition.yaml").write_text(
        yaml.safe_dump(payload, sort_keys=False), encoding="utf-8"
    )
    return edition_root


def test_verifies_inventory_digest(tmp_path: Path) -> None:
    edition_root = _write_minimal_edition(tmp_path)
    loaded = load_edition(edition_root, repository_root=tmp_path, verify_files=True)
    assert loaded.inventories[0].count == 1

    skill = edition_root / "skills" / "mysql-8-0-22-sql-generation" / "SKILL.md"
    skill.write_text("changed\n", encoding="utf-8")
    with pytest.raises(EditionValidationError, match="sha256"):
        load_edition(edition_root, repository_root=tmp_path, verify_files=True)


def test_rejects_unknown_keys(tmp_path: Path) -> None:
    edition_root = _write_minimal_edition(tmp_path, extra={"future_flag": True})
    with pytest.raises(EditionValidationError, match="unknown keys.*future_flag"):
        load_edition(edition_root, repository_root=tmp_path, verify_files=False)


def test_rejects_path_escape(tmp_path: Path) -> None:
    edition_root = _write_minimal_edition(tmp_path)
    manifest = yaml.safe_load((edition_root / "edition.yaml").read_text(encoding="utf-8"))
    manifest["skill"]["root"] = "../../outside"
    (edition_root / "edition.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8"
    )
    with pytest.raises(EditionValidationError, match="contained"):
        load_edition(edition_root, repository_root=tmp_path, verify_files=False)


def test_rejects_directory_version_mismatch(tmp_path: Path) -> None:
    edition_root = _write_minimal_edition(tmp_path)
    manifest = yaml.safe_load((edition_root / "edition.yaml").read_text(encoding="utf-8"))
    manifest["target_version"] = "8.0.41"
    manifest["target_version_num"] = 80041
    (edition_root / "edition.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8"
    )
    with pytest.raises(EditionValidationError, match="edition_id.*target_version"):
        load_edition(edition_root, repository_root=tmp_path, verify_files=False)
