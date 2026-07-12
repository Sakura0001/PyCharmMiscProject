from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pg_case_factory.skill_packaging import package_skill, verify_skill_archive


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build or verify a deterministic Codex skill archive.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    package_parser = subparsers.add_parser("package", help="package one skill directory")
    package_parser.add_argument(
        "--skill-root",
        type=Path,
        default=ROOT / "skills" / "pg-sql-generation",
    )
    package_parser.add_argument("--output", type=Path, default=ROOT / "skills.zip")
    verify_parser = subparsers.add_parser("verify", help="verify an existing skill archive")
    verify_parser.add_argument("archive", type=Path, nargs="?", default=ROOT / "skills.zip")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "package":
        result = package_skill(args.skill_root, args.output)
    else:
        result = verify_skill_archive(args.archive)
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
