from __future__ import annotations

import hashlib
from pathlib import Path

from mysql_case_factory.editions import load_edition
from mysql_case_factory.skill_packaging import package_skill, verify_skill_archive


ROOT = Path(__file__).resolve().parents[1]


def test_each_edition_packages_reproducibly(tmp_path: Path) -> None:
    for directory in ("mysql_8_0_22", "mysql_8_0_41"):
        edition = load_edition(ROOT / "editions" / directory, repository_root=ROOT, verify_files=True)
        first = tmp_path / f"{directory}-first.zip"
        second = tmp_path / f"{directory}-second.zip"
        package_skill(edition.skill_root, first)
        package_skill(edition.skill_root, second)
        assert hashlib.sha256(first.read_bytes()).digest() == hashlib.sha256(second.read_bytes()).digest()
        assert verify_skill_archive(first)["ok"] is True
