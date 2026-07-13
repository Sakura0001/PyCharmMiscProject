from __future__ import annotations

import hashlib
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from mysql_case_factory.skill_packaging import package_skill, verify_skill_archive


def _write_skill(root: Path) -> Path:
    skill_root = root / "skills" / "mysql-8-0-22-sql-generation"
    (skill_root / "references" / "combinations" / "ddl" / "index").mkdir(
        parents=True, exist_ok=True
    )
    (skill_root / "references" / "statements" / "ddl" / "index").mkdir(
        parents=True, exist_ok=True
    )
    (skill_root / "SKILL.md").write_text("# skill\n", encoding="utf-8")
    (skill_root / "references" / "combinations" / "ddl" / "index" / "create_index.yaml").write_text(
        "kind: statement_combination_matrix\n", encoding="utf-8"
    )
    (skill_root / "references" / "statements" / "ddl" / "index" / "create_index.md").write_text(
        "# CREATE INDEX\n", encoding="utf-8"
    )
    (skill_root / ".DS_Store").write_bytes(b"noise")
    macos = skill_root / "__MACOSX"
    macos.mkdir()
    (macos / "._SKILL.md").write_bytes(b"noise")
    return skill_root


class SkillPackagingTest(unittest.TestCase):
    def test_package_rejects_a_profile_reference_outside_its_payload(self) -> None:
        with TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            skill_root = _write_skill(root)
            profile = skill_root / "references" / "common" / "compatibility_profile.yaml"
            profile.parent.mkdir(parents=True)
            profile.write_text(
                "official_evidence:\n"
                "  exact_source_hashes: references/common/inventory.yaml\n"
                "catalogs:\n"
                "  factor_value_ledger: ../outside.tsv\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "escapes the Skill"):
                package_skill(skill_root, root / "skill.zip")

    def test_package_is_reproducible_complete_and_clean(self) -> None:
        with TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            skill_root = _write_skill(root)
            first = root / "first.zip"
            second = root / "second.zip"

            first_manifest = package_skill(skill_root, first)
            second_manifest = package_skill(skill_root, second)

            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(
                hashlib.sha256(first.read_bytes()).hexdigest(),
                first_manifest["archive_sha256"],
            )
            self.assertEqual(first_manifest["files"], second_manifest["files"])
            with zipfile.ZipFile(first) as archive:
                names = archive.namelist()
                self.assertFalse(any("__MACOSX" in name for name in names))
                self.assertFalse(any(".DS_Store" in name for name in names))
                self.assertIn(
                    "mysql-8-0-22-sql-generation/references/combinations/ddl/index/create_index.yaml",
                    names,
                )
                self.assertIn("mysql-8-0-22-sql-generation/MANIFEST.sha256", names)
                self.assertTrue(
                    all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in archive.infolist())
                )

            verification = verify_skill_archive(first)
            self.assertTrue(verification["ok"], verification)
            self.assertTrue(verification["manifest_verified"])

    def test_existing_manifest_is_reserved_and_repackaging_is_idempotent(self) -> None:
        with TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            skill_root = _write_skill(root)
            source_manifest = skill_root / "MANIFEST.sha256"
            archive_path = root / "skills.zip"

            source_manifest.write_text("stale manifest\n", encoding="utf-8")
            first_result = package_skill(skill_root, archive_path)
            first_bytes = archive_path.read_bytes()

            source_manifest.write_text("different stale manifest\n", encoding="utf-8")
            second_result = package_skill(skill_root, archive_path)

            self.assertEqual(first_bytes, archive_path.read_bytes())
            self.assertEqual(first_result, second_result)
            self.assertFalse(
                any(record["path"].endswith("/MANIFEST.sha256") for record in first_result["files"])
            )
            with zipfile.ZipFile(archive_path) as archive:
                manifest_name = "mysql-8-0-22-sql-generation/MANIFEST.sha256"
                self.assertEqual(archive.namelist().count(manifest_name), 1)
                manifest_entries = archive.read(manifest_name).decode("utf-8").splitlines()
                self.assertFalse(any(line.endswith(f"  {manifest_name}") for line in manifest_entries))

            verification = verify_skill_archive(archive_path)
            self.assertTrue(verification["ok"], verification)
            self.assertTrue(verification["manifest_verified"])

    def test_verify_detects_payload_tampering(self) -> None:
        with TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            skill_root = _write_skill(root)
            original = root / "original.zip"
            tampered = root / "tampered.zip"
            package_skill(skill_root, original)

            with zipfile.ZipFile(original) as source, zipfile.ZipFile(tampered, "w") as target:
                for info in source.infolist():
                    data = source.read(info.filename)
                    if info.filename.endswith("/SKILL.md"):
                        data = b"# tampered\n"
                    target.writestr(info, data)

            result = verify_skill_archive(tampered)

            self.assertFalse(result["ok"])
            self.assertFalse(result["manifest_verified"])
            self.assertTrue(
                any("SHA256 mismatch" in error and error.endswith("/SKILL.md") for error in result["errors"]),
                result,
            )

    def test_verify_rejects_missing_matrix_and_macos_metadata(self) -> None:
        with TemporaryDirectory() as raw_dir:
            archive_path = Path(raw_dir) / "bad.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("mysql-8-0-22-sql-generation/SKILL.md", "# skill\n")
                archive.writestr("__MACOSX/._SKILL.md", "noise")

            result = verify_skill_archive(archive_path)

            self.assertFalse(result["ok"])
            self.assertTrue(any("__MACOSX" in error for error in result["errors"]))
            self.assertTrue(any("combination matrix" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
