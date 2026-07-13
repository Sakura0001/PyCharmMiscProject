from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from mysql_case_factory.matrix_generation import (
    generate_matrix_for_reference,
    load_statement_reference,
)


def generate_all(skill_root: Path, *, overwrite: bool) -> tuple[int, int]:
    skill_root = skill_root.resolve()
    statements_root = skill_root / "references" / "statements"
    combinations_root = skill_root / "references" / "combinations"
    if not statements_root.is_dir():
        raise ValueError(f"statement root does not exist: {statements_root}")
    created = 0
    replaced = 0
    for reference in sorted(statements_root.rglob("*.md")):
        relative = reference.relative_to(statements_root).with_suffix(".yaml")
        destination = combinations_root / relative
        if destination.exists() and not overwrite:
            continue
        matrix = generate_matrix_for_reference(
            reference,
            load_statement_reference(reference),
            skill_root=skill_root,
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        existed = destination.exists()
        destination.write_text(
            yaml.safe_dump(matrix, sort_keys=False, allow_unicode=True, width=120),
            encoding="utf-8",
        )
        replaced += int(existed)
        created += int(not existed)
    return created, replaced


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate closed statement matrices for one MySQL edition.")
    parser.add_argument("--skill-root", type=Path, required=True)
    parser.add_argument("--overwrite", action="store_true")
    arguments = parser.parse_args()
    created, replaced = generate_all(arguments.skill_root, overwrite=arguments.overwrite)
    print(f"generated matrices: created={created} replaced={replaced}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
