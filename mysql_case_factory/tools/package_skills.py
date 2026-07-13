from __future__ import annotations

import argparse
import hashlib
import tempfile
from pathlib import Path

from mysql_case_factory.editions import load_edition
from mysql_case_factory.skill_packaging import package_skill, verify_skill_archive


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and verify both edition skill archives.")
    parser.add_argument("--output-directory", type=Path)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    temporary = tempfile.TemporaryDirectory() if args.output_directory is None else None
    output = Path(temporary.name) if temporary is not None else args.output_directory
    output.mkdir(parents=True, exist_ok=True)
    try:
        for directory in ("mysql_8_0_22", "mysql_8_0_41"):
            edition = load_edition(root / "editions" / directory, repository_root=root, verify_files=True)
            first = output / f"{directory}.zip"
            second = output / f"{directory}.repeat.zip"
            package_skill(edition.skill_root, first)
            package_skill(edition.skill_root, second)
            if hashlib.sha256(first.read_bytes()).digest() != hashlib.sha256(second.read_bytes()).digest():
                raise ValueError(f"{edition.edition_id} archive is not deterministic")
            verification = verify_skill_archive(first)
            if not verification.get("ok"):
                raise ValueError(f"{edition.edition_id} archive verification failed: {verification}")
            print(f"PASS {edition.edition_id}: files={verification.get('file_count')}")
            if args.verify_only or temporary is not None:
                second.unlink(missing_ok=True)
    finally:
        if temporary is not None:
            temporary.cleanup()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
