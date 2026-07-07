#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pg_case_factory.association_planner import (  # noqa: E402
    load_markdown_yaml,
    load_yaml_file,
    plan_associations,
)


REFERENCES_ROOT = Path("skills/pg-sql-generation/references")
STATEMENTS_ROOT = REFERENCES_ROOT / "statements"
COMBINATIONS_ROOT = REFERENCES_ROOT / "combinations"
TYPE_CATALOG = REFERENCES_ROOT / "common" / "pg16_type_catalog.md"
COVERAGE_INVENTORY = COMBINATIONS_ROOT / "_shared" / "coverage_inventory.yaml"


class CliError(Exception):
    """Expected CLI failure without traceback."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan factor associations for a statement.")
    parser.add_argument("--root", default=".", help="Repository root to scan.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--statement", help="Statement key, such as create_index.")
    source.add_argument("--matrix", help="Combination matrix path.")
    parser.add_argument("--output", help="Output YAML path.")
    args = parser.parse_args(argv)

    try:
        root = Path(args.root).resolve()
        statement_config, matrix_config, statement_key = _load_inputs(
            root=root,
            statement_key=args.statement,
            matrix_arg=args.matrix,
        )
        type_catalog_config = _load_optional_markdown(root / TYPE_CATALOG)
        coverage_inventory = _load_optional_yaml(root / COVERAGE_INVENTORY)

        plan = plan_associations(
            statement_config=statement_config,
            matrix_config=matrix_config,
            type_catalog_config=type_catalog_config,
            coverage_inventory=coverage_inventory,
        )
        output_path = _output_path(root, statement_key, args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            yaml.safe_dump(plan, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        families = len(plan.get("scenario_families") or [])
        obligations = len(plan.get("coverage_obligations") or [])
        print(
            f"PASS factor association plan: statement={statement_key} "
            f"families={families} obligations={obligations}"
        )
        return 0
    except CliError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


def _load_inputs(
    *,
    root: Path,
    statement_key: str | None,
    matrix_arg: str | None,
) -> tuple[dict[str, Any], dict[str, Any] | None, str]:
    if matrix_arg:
        matrix_path = _resolve_path(root, matrix_arg)
        try:
            matrix_config = load_yaml_file(matrix_path)
        except Exception as exc:  # noqa: BLE001 - hide traceback for CLI load errors.
            raise CliError(f"failed to load matrix {matrix_path}: {exc}") from exc
        matrix_statement_key = _statement_key(matrix_config)
        if not matrix_statement_key:
            raise CliError(f"{matrix_path}: matrix statement.key is required")
        statement_path, statement_config = _find_statement(root, matrix_statement_key)
        return statement_config, matrix_config, matrix_statement_key

    assert statement_key is not None
    statement_path, statement_config = _find_statement(root, statement_key)
    matrix_path, matrix_config = _find_matrix(root, statement_key, required=False)
    return statement_config, matrix_config, statement_key


def _find_statement(root: Path, statement_key: str) -> tuple[Path, dict[str, Any]]:
    matches: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted((root / STATEMENTS_ROOT).glob("**/*.md")):
        config = load_markdown_yaml(path)
        if _statement_key(config) == statement_key:
            matches.append((path, config))
    if not matches:
        raise CliError(f"statement not found: {statement_key}")
    if len(matches) > 1:
        paths = ", ".join(str(path) for path, _ in matches)
        raise CliError(f"multiple statement references for {statement_key}: {paths}")
    return matches[0]


def _find_matrix(root: Path, statement_key: str, required: bool = True) -> tuple[Path | None, dict[str, Any] | None]:
    matches: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted((root / COMBINATIONS_ROOT).glob("**/*.yaml")):
        if "_shared" in path.relative_to(root / COMBINATIONS_ROOT).parts:
            continue
        config = load_yaml_file(path)
        if _statement_key(config) == statement_key:
            matches.append((path, config))
    if not matches:
        if not required:
            return None, None
        raise CliError(f"matrix not found for statement: {statement_key}")
    if len(matches) > 1:
        paths = ", ".join(str(path) for path, _ in matches)
        raise CliError(f"multiple matrices for {statement_key}: {paths}")
    return matches[0]


def _statement_key(config: dict[str, Any]) -> str:
    statement = config.get("statement")
    if not isinstance(statement, dict):
        return ""
    return str(statement.get("key") or "")


def _load_optional_markdown(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return load_markdown_yaml(path)


def _load_optional_yaml(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return load_yaml_file(path)


def _resolve_path(root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return root / path


def _output_path(root: Path, statement_key: str, raw_path: str | None) -> Path:
    if raw_path:
        return _resolve_path(root, raw_path)
    return root / "artifacts" / "intermediates" / f"{statement_key}_association_plan.yaml"


if __name__ == "__main__":
    raise SystemExit(main())
