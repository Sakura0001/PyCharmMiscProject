from __future__ import annotations

import hashlib
import re
import zipfile
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any

import yaml


FIXED_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
MANIFEST_NAME = "MANIFEST.sha256"
IGNORED_NAMES = {".DS_Store"}
IGNORED_PARTS = {"__MACOSX", "__pycache__"}
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
COMPATIBILITY_PROFILE = PurePosixPath(
    "references/common/compatibility_profile.yaml"
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _ignored(path: Path) -> bool:
    if any(part in IGNORED_PARTS for part in path.parts):
        return True
    if path.name == MANIFEST_NAME:
        return True
    if path.name in IGNORED_NAMES or path.name.startswith("._"):
        return True
    return path.suffix in {".pyc", ".pyo"}


def _source_files(skill_root: Path, output_path: Path) -> list[Path]:
    files: list[Path] = []
    for path in skill_root.rglob("*"):
        if not path.is_file() or _ignored(path.relative_to(skill_root)):
            continue
        if path.resolve() == output_path.resolve():
            continue
        if path.is_symlink():
            raise ValueError(f"skill package does not allow symlinked files: {path}")
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(skill_root).as_posix())


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(filename=name, date_time=FIXED_ZIP_TIMESTAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    return info


def _profile_references(data: bytes, location: str) -> tuple[str, ...]:
    """Return portable Skill-root-relative files declared by the PG profile."""

    try:
        document = yaml.safe_load(data.decode("utf-8")) or {}
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ValueError(f"invalid compatibility profile {location}: {exc}") from exc
    if not isinstance(document, Mapping):
        raise ValueError(f"compatibility profile {location} must be a mapping")
    references: list[Any] = []
    evidence = document.get("official_evidence") or {}
    catalogs = document.get("catalogs") or {}
    if not isinstance(evidence, Mapping) or not isinstance(catalogs, Mapping):
        raise ValueError(
            f"compatibility profile {location} official_evidence/catalogs must be mappings"
        )
    references.append(evidence.get("exact_source_hashes"))
    references.extend(catalogs.values())
    normalized: list[str] = []
    for raw_reference in references:
        if not isinstance(raw_reference, str) or not raw_reference:
            raise ValueError(
                f"compatibility profile {location} contains an empty or non-string file reference"
            )
        if "\\" in raw_reference:
            raise ValueError(
                f"compatibility profile {location} contains a non-portable file reference: "
                f"{raw_reference}"
            )
        relative = PurePosixPath(raw_reference)
        if relative.is_absolute() or ".." in relative.parts or not relative.parts:
            raise ValueError(
                f"compatibility profile {location} file reference escapes the Skill: "
                f"{raw_reference}"
            )
        normalized.append(relative.as_posix())
    return tuple(dict.fromkeys(normalized))


def _validate_profile_sources(skill_root: Path) -> None:
    profile_path = skill_root / COMPATIBILITY_PROFILE
    if not profile_path.exists():
        return
    if not profile_path.is_file() or profile_path.is_symlink():
        raise ValueError(
            f"compatibility profile must be a regular file: {profile_path}"
        )
    for relative in _profile_references(
        profile_path.read_bytes(),
        COMPATIBILITY_PROFILE.as_posix(),
    ):
        current = skill_root
        for part in PurePosixPath(relative).parts:
            current = current / part
            if current.is_symlink():
                raise ValueError(
                    "compatibility profile references a symlinked Skill path: "
                    f"{relative}"
                )
        candidate = current
        if not candidate.is_file():
            raise ValueError(
                "compatibility profile references a missing Skill file: "
                f"{relative}"
            )
        try:
            candidate.resolve(strict=True).relative_to(skill_root)
        except (OSError, ValueError) as exc:
            raise ValueError(
                "compatibility profile references a file outside the Skill: "
                f"{relative}"
            ) from exc


def package_skill(skill_root: Path | str, output_path: Path | str) -> dict[str, Any]:
    skill_root = Path(skill_root).resolve()
    output_path = Path(output_path).resolve()
    if not skill_root.is_dir():
        raise ValueError(f"skill root does not exist or is not a directory: {skill_root}")
    if not (skill_root / "SKILL.md").is_file():
        raise ValueError(f"skill root has no SKILL.md: {skill_root}")
    _validate_profile_sources(skill_root)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    prefix = skill_root.name
    file_records: list[dict[str, Any]] = []
    payloads: list[tuple[str, bytes]] = []
    for path in _source_files(skill_root, output_path):
        relative = path.relative_to(skill_root).as_posix()
        archive_name = f"{prefix}/{relative}"
        data = path.read_bytes()
        digest = _sha256(data)
        payloads.append((archive_name, data))
        file_records.append({"path": archive_name, "sha256": digest, "size": len(data)})

    manifest_name = f"{prefix}/{MANIFEST_NAME}"
    manifest_data = "".join(
        f"{record['sha256']}  {record['path']}\n" for record in file_records
    ).encode("utf-8")
    with zipfile.ZipFile(output_path, "w") as archive:
        for archive_name, data in payloads:
            archive.writestr(_zip_info(archive_name), data)
        archive.writestr(_zip_info(manifest_name), manifest_data)

    archive_digest = _sha256(output_path.read_bytes())
    return {
        "archive": str(output_path),
        "archive_sha256": archive_digest,
        "file_count": len(file_records),
        "files": file_records,
        "manifest": manifest_name,
    }


def _safe_archive_name(name: str) -> bool:
    if "\\" in name:
        return False
    path = PurePosixPath(name)
    return not path.is_absolute() and ".." not in path.parts and bool(path.parts)


def _parse_manifest(data: bytes, errors: list[str]) -> dict[str, str]:
    entries: dict[str, str] = {}
    try:
        lines = data.decode("utf-8").splitlines()
    except UnicodeDecodeError:
        errors.append("MANIFEST.sha256 is not valid UTF-8")
        return entries
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            digest, name = line.split("  ", 1)
        except ValueError:
            errors.append(f"MANIFEST.sha256 line {line_number} has invalid syntax")
            continue
        if not SHA256_PATTERN.fullmatch(digest):
            errors.append(f"MANIFEST.sha256 line {line_number} has invalid SHA256")
            continue
        if name in entries:
            errors.append(f"MANIFEST.sha256 contains duplicate path: {name}")
            continue
        entries[name] = digest
    return entries


def verify_skill_archive(archive_path: Path | str) -> dict[str, Any]:
    archive_path = Path(archive_path)
    errors: list[str] = []
    warnings: list[str] = []
    manifest_verified = False
    file_count = 0
    entries: list[str] = []

    if not archive_path.is_file():
        return {
            "ok": False,
            "errors": [f"archive does not exist: {archive_path}"],
            "warnings": [],
            "archive_sha256": "",
            "file_count": 0,
            "manifest_verified": False,
            "entries": [],
        }

    archive_digest = _sha256(archive_path.read_bytes())
    try:
        with zipfile.ZipFile(archive_path) as archive:
            infos = archive.infolist()
            entries = [info.filename for info in infos]
            file_count = len(infos)
            duplicates = sorted({name for name in entries if entries.count(name) > 1})
            for name in duplicates:
                errors.append(f"archive contains duplicate entry: {name}")
            for info in infos:
                if not _safe_archive_name(info.filename):
                    errors.append(f"archive contains unsafe path: {info.filename}")
                parts = PurePosixPath(info.filename).parts
                if "__MACOSX" in parts or any(part.startswith("._") for part in parts):
                    errors.append(f"archive contains forbidden macOS metadata: {info.filename}")
                if info.filename.endswith("/.DS_Store") or info.filename == ".DS_Store":
                    errors.append(f"archive contains forbidden .DS_Store: {info.filename}")
                if info.date_time != FIXED_ZIP_TIMESTAMP:
                    errors.append(f"archive entry has non-deterministic timestamp: {info.filename}")

            skill_files = [name for name in entries if name.endswith("/SKILL.md")]
            if not skill_files:
                errors.append("archive contains no skill SKILL.md")
            matrix_files = [
                name
                for name in entries
                if "/references/combinations/" in name and name.endswith((".yaml", ".yml"))
            ]
            if not matrix_files:
                errors.append("archive contains no statement combination matrix")

            profile_names = [
                name
                for name in entries
                if name.endswith(f"/{COMPATIBILITY_PROFILE.as_posix()}")
            ]
            if len(profile_names) > 1:
                errors.append("archive contains multiple compatibility profiles")
            elif profile_names:
                profile_name = profile_names[0]
                prefix = profile_name.removesuffix(
                    COMPATIBILITY_PROFILE.as_posix()
                )
                try:
                    declared_references = _profile_references(
                        archive.read(profile_name),
                        profile_name,
                    )
                except ValueError as exc:
                    errors.append(str(exc))
                else:
                    for relative in declared_references:
                        archive_reference = f"{prefix}{relative}"
                        if archive_reference not in entries:
                            errors.append(
                                "compatibility profile references an absent archive entry: "
                                f"{archive_reference}"
                            )

            manifest_names = [name for name in entries if name.endswith(f"/{MANIFEST_NAME}")]
            if len(manifest_names) != 1:
                errors.append("archive must contain exactly one MANIFEST.sha256")
            else:
                manifest_name = manifest_names[0]
                manifest_entries = _parse_manifest(archive.read(manifest_name), errors)
                expected_names = {name for name in entries if name != manifest_name}
                if set(manifest_entries) != expected_names:
                    missing = sorted(expected_names - set(manifest_entries))
                    extra = sorted(set(manifest_entries) - expected_names)
                    if missing:
                        errors.append(f"MANIFEST.sha256 is missing entries: {', '.join(missing)}")
                    if extra:
                        errors.append(f"MANIFEST.sha256 lists absent entries: {', '.join(extra)}")
                for name in sorted(expected_names & set(manifest_entries)):
                    actual = _sha256(archive.read(name))
                    if actual != manifest_entries[name]:
                        errors.append(f"SHA256 mismatch for archive entry: {name}")
                manifest_verified = not any("MANIFEST" in error or "SHA256 mismatch" in error for error in errors)
    except (OSError, zipfile.BadZipFile) as exc:
        errors.append(f"invalid skill archive: {exc}")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "archive_sha256": archive_digest,
        "file_count": file_count,
        "manifest_verified": manifest_verified,
        "entries": entries,
    }
