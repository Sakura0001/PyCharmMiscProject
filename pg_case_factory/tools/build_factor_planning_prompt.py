from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml


REFERENCES_ROOT = Path("skills/pg-sql-generation/references")
STATEMENTS_ROOT = REFERENCES_ROOT / "statements"
COMBINATIONS_ROOT = REFERENCES_ROOT / "combinations"
CONTRACT_PATH = REFERENCES_ROOT / "mainflow" / "plan_factor_association_from_statement.md"
FACTOR_POLICY_PATH = REFERENCES_ROOT / "common" / "factor_policy.md"
COVERAGE_INVENTORY_PATH = COMBINATIONS_ROOT / "_shared" / "coverage_inventory.yaml"
TYPE_CATALOG_PATH = REFERENCES_ROOT / "common" / "pg16_type_catalog.md"
YAML_BLOCK_PATTERN = re.compile(r"```yaml\s*(.*?)```", re.DOTALL)


def _load_markdown_yaml(path: Path) -> dict[str, Any]:
    raw_text = path.read_text(encoding="utf-8")
    match = YAML_BLOCK_PATTERN.search(raw_text)
    if not match:
        return {}
    parsed = yaml.safe_load(match.group(1)) or {}
    if not isinstance(parsed, Mapping):
        return {}
    config = parsed.get("structured_config", parsed)
    return dict(config) if isinstance(config, Mapping) else {}


def _statement_identity(path: Path) -> dict[str, Any]:
    config = _load_markdown_yaml(path)
    statement_doc = dict(config.get("statement") or {})
    aliases = [str(item) for item in list(statement_doc.get("aliases") or [])]
    statement_key = str(statement_doc.get("key") or config.get("skill_name") or path.stem)
    statement_name = str(statement_doc.get("name") or statement_key)
    aliases.extend([statement_key, statement_name, path.stem])
    return {
        "path": path,
        "config": config,
        "key": statement_key,
        "name": statement_name,
        "aliases": tuple(dict.fromkeys(alias.lower() for alias in aliases if alias)),
    }


def _resolve_statement(root: Path, statement_key: str) -> dict[str, Any]:
    wanted = statement_key.lower()
    candidates = []
    for path in sorted((root / STATEMENTS_ROOT).glob("**/*.md")):
        identity = _statement_identity(path)
        if wanted == identity["key"].lower() or wanted in identity["aliases"]:
            candidates.append(identity)

    if not candidates:
        raise ValueError(f"statement reference not found for {statement_key!r}")
    exact = [item for item in candidates if wanted == item["key"].lower()]
    matches = exact or candidates
    if len(matches) > 1:
        rels = ", ".join(_relative_path(root, item["path"]) for item in matches)
        raise ValueError(f"statement reference is ambiguous for {statement_key!r}: {rels}")
    return matches[0]


def _relative_path(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _resolve_matrix(root: Path, statement: dict[str, Any]) -> Path | None:
    config = dict(statement.get("config") or {})
    category = str(config.get("category") or "")
    domain = str(config.get("domain") or "")
    statement_key = str(statement["key"])
    direct = root / COMBINATIONS_ROOT / category / domain / f"{statement_key}.yaml"
    if category and domain and direct.exists():
        return direct

    matches = sorted((root / COMBINATIONS_ROOT).glob(f"**/{statement_key}.yaml"))
    if not matches:
        return None
    if len(matches) > 1:
        rels = ", ".join(_relative_path(root, item) for item in matches)
        raise ValueError(f"combination matrix is ambiguous for {statement_key!r}: {rels}")
    return matches[0]


def _existing_required_paths(root: Path, statement_path: Path, matrix_path: Path | None) -> list[str]:
    paths = [
        CONTRACT_PATH,
        statement_path.relative_to(root),
    ]
    if matrix_path is not None:
        paths.append(matrix_path.relative_to(root))
    paths.extend(
        [
            FACTOR_POLICY_PATH,
            COVERAGE_INVENTORY_PATH,
            TYPE_CATALOG_PATH,
        ]
    )
    return [path.as_posix() for path in paths]


def _statement_specific_guidance(statement: dict[str, Any]) -> str:
    statement_key = str(statement["key"]).lower()
    if statement_key != "insert":
        return "请使用中文回答，路径、factor key 和 YAML key 保持英文。"

    return """请使用中文回答，路径、factor key 和 YAML key 保持英文。

For INSERT, the impact chain must be at least this rich:
语法形式 -> 目标对象 -> 输入数据来源 -> 列映射 -> 数据类型转换 -> 默认值/生成值 -> 约束校验 -> 分区/继承/路由 -> 触发器/规则/RLS -> 索引/冲突处理 -> 事务/并发 -> 存储/WAL/复制 -> 返回值与可观测结果

For INSERT, include factor-trigger examples with this level of specificity:
- 如果看到目标对象是分区表 => 必须联想到 partition key、路由、default partition、无匹配分区、trigger 修改 key、分区唯一约束。
- 如果看到 unique/primary key => 必须联想到重复插入、ON CONFLICT、并发冲突、partial/expression index、DO UPDATE 二次约束。
- 如果列里有 identity/generated/default => 必须联想到省略列、显式插入、OVERRIDING、RETURNING、rollback 后 sequence 行为。
- 如果有 FK/deferrable => 必须联想到父表是否存在、事务提交时失败、并发删除父行、savepoint 行为。
"""


def build_prompt(root: Path | str, statement_key: str) -> str:
    repo_root = Path(root).resolve()
    statement = _resolve_statement(repo_root, statement_key)
    statement_path = Path(statement["path"])
    matrix_path = _resolve_matrix(repo_root, statement)
    required_paths = _existing_required_paths(repo_root, statement_path, matrix_path)
    matrix_line = _relative_path(repo_root, matrix_path) if matrix_path else "NO_MATCHING_MATRIX_FOUND"
    statement_guidance = _statement_specific_guidance(statement)

    return f"""You are a clean-context subagent working in this repository:
{repo_root}

Task: create a factor-association planning answer for PostgreSQL {statement["name"]}.

Do not generate SQL.
Do not modify files, delete files, stage changes, commit, or push.
Do not output a generic test checklist. The answer must be a factor-association map.

Read these repository files before answering:
{chr(10).join(f"- {path}" for path in required_paths)}

The mandatory planning contract is:
- {CONTRACT_PATH.as_posix()}

Statement reference:
- {_relative_path(repo_root, statement_path)}

Combination matrix:
- {matrix_line}

Required answer shape:
1. Start with an impact chain that explains how this statement moves from syntax form to target object, inputs, dependencies, execution path, errors, and observable result.
2. List prioritized factor dimensions with concrete values and boundaries.
3. Write factor-to-factor trigger rules in the form: "if this factor/fact is seen, must expand to these related factors".
4. Build scenario families from those trigger rules, including lifecycle ordering, negative cases, cleanup, and verification oracles.
5. Add source attribution for catalog facts, statement reference facts, combination matrix obligations, coverage inventory facts, type catalog facts, and derived extensions.
6. End with a YAML association graph. Each graph node must include factor, when_seen, must_expand_to, oracle, sources, and origin.

Use these exact concepts in the answer so downstream agents can validate the output:
- impact chain
- factor dimensions
- factor-to-factor trigger rules
- scenario families
- oracle / verification
- source attribution
- catalog facts
- derived extensions
- YAML association graph

The target quality bar is a senior PostgreSQL SQL testing expert: explain not just what to test, but why each factor forces related coverage.

Statement-specific guidance:
{statement_guidance}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a clean-context subagent prompt for factor-association planning.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="pg_case_factory project root")
    parser.add_argument("--statement", required=True, help="statement key, for example insert")
    args = parser.parse_args(argv)

    try:
        print(build_prompt(args.root, args.statement))
    except Exception as exc:  # noqa: BLE001 - CLI should report clean errors.
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
