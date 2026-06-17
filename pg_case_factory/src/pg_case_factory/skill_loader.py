from __future__ import annotations

import re
from pathlib import Path

import yaml


YAML_BLOCK_PATTERN = re.compile(r"```yaml\s*(.*?)```", re.DOTALL)
SQL_BLOCK_PATTERN = re.compile(r"```sql\s*(.*?)```", re.DOTALL)
TITLE_PATTERN = re.compile(r"^#\s*(?:技能：)?(.+?)\s*$", re.MULTILINE)


def _infer_statement_path_parts(path: Path) -> tuple[str, str]:
    parts = path.parts
    if "statements" not in parts:
        return "", path.parent.name

    statement_index = parts.index("statements")
    relative_parts = parts[statement_index + 1 :]
    if len(relative_parts) >= 3:
        return relative_parts[0], relative_parts[1]
    if len(relative_parts) >= 2:
        return "ddl", relative_parts[0]
    return "", path.parent.name


def _normalize_factor_doc(factors: dict, coverage_policy: dict) -> tuple[dict[str, tuple[str, ...]], dict[str, str], tuple[str, ...], tuple[str, ...]]:
    factor_values: dict[str, tuple[str, ...]] = {}
    factor_labels: dict[str, str] = {}
    important_factors: list[str] = []
    non_important_factors: list[str] = []

    for factor_name, factor_doc in factors.items():
        factor_doc = dict(factor_doc or {})
        factor_labels[str(factor_name)] = str(factor_doc.get("label") or factor_name)
        values: list[str] = []
        for item in list(factor_doc.get("values") or []):
            if isinstance(item, dict):
                values.append(str(item["key"]))
            else:
                values.append(str(item))
        factor_values[str(factor_name)] = tuple(values)
        importance = str(factor_doc.get("importance") or "").lower()
        if importance == "important":
            important_factors.append(str(factor_name))
        else:
            non_important_factors.append(str(factor_name))

    if coverage_policy.get("main_combination_axes"):
        important_factors = [str(item) for item in list(coverage_policy.get("main_combination_axes") or [])]
    if coverage_policy.get("non_main_factors"):
        non_important_factors = [str(item) for item in list(coverage_policy.get("non_main_factors") or [])]

    return factor_values, factor_labels, tuple(important_factors), tuple(non_important_factors)


def _fallback_statement_config(path: Path, raw_text: str) -> dict:
    category, domain = _infer_statement_path_parts(path)
    title_match = TITLE_PATTERN.search(raw_text)
    statement_name = str(title_match.group(1) if title_match else path.stem.replace("_", " ")).strip()
    statement_key = path.stem
    sql_match = SQL_BLOCK_PATTERN.search(raw_text)
    syntax = sql_match.group(1).strip() if sql_match else statement_name

    return {
        "kind": "statement",
        "category": category,
        "domain": domain,
        "skill_name": statement_key,
        "statement": {
            "key": statement_key,
            "name": statement_name,
            "aliases": [
                statement_key,
                statement_key.replace("_", " "),
                statement_name,
                statement_name.lower(),
            ],
            "purpose": "",
        },
        "syntax_templates": [syntax],
        "factor_layers": [
            {
                "tier": "T1",
                "name": "核心语义因子",
                "factors": ["statement_branch", "expected_status"],
            }
        ],
        "factors": {
            "statement_branch": {
                "label": "官方语法分支",
                "importance": "important",
                "values": ["default_branch"],
            },
            "expected_status": {
                "label": "预期结果",
                "importance": "important",
                "values": ["success", "failure"],
            },
        },
        "defaults": {"expected_status": "success"},
        "coverage_policy": {
            "main_combination_axes": ["statement_branch", "expected_status"],
            "non_main_factors": [],
            "python_expand_threshold": 200,
        },
        "rendering": {
            "statement_template": " ".join((syntax.splitlines()[0] if syntax else statement_name).split()),
            "verification_query_template": "",
            "factor_value_bindings": {},
        },
    }


def load_skill(path: Path) -> dict:
    raw_text = path.read_text(encoding="utf-8")
    match = YAML_BLOCK_PATTERN.search(raw_text)
    if not match and "statements" not in path.parts:
        raise ValueError(f"skill 文件中未找到结构化 YAML 配置块：{path}")

    parsed = yaml.safe_load(match.group(1)) if match else _fallback_statement_config(path, raw_text)
    parsed = parsed or {}
    config = dict(parsed.get("structured_config") or parsed)
    kind = str(config.get("kind") or "statement")
    inferred_category, inferred_domain = _infer_statement_path_parts(path)
    statement_doc = dict(config.get("statement") or {})
    coverage_policy = dict(config.get("coverage_policy") or {})
    factors = dict(config.get("factors") or {})
    factor_values, factor_labels, important_factors, non_important_factors = _normalize_factor_doc(
        factors,
        coverage_policy,
    )

    rendering_doc = dict(config.get("rendering") or {})
    factor_value_bindings = {
        str(name): {
            "factor": str(dict(spec).get("factor")),
            "values": {str(key): str(value) for key, value in dict(dict(spec).get("values") or {}).items()},
        }
        for name, spec in dict(rendering_doc.get("factor_value_bindings") or {}).items()
    }

    aliases = [str(item) for item in list(statement_doc.get("aliases") or config.get("aliases") or [])]
    statement_key = str(statement_doc.get("key") or config.get("statement_key") or path.stem)
    statement_name = str(statement_doc.get("name") or config.get("statement_name") or statement_key)
    if statement_key not in aliases:
        aliases.append(statement_key)
    if statement_name not in aliases:
        aliases.append(statement_name)

    return {
        "kind": kind,
        "category": str(config.get("category") or inferred_category),
        "skill_name": str(config.get("skill_name") or path.stem),
        "domain": str(config.get("domain") or inferred_domain),
        "path": str(path),
        "statement": {
            "key": statement_key,
            "name": statement_name,
            "purpose": str(statement_doc.get("purpose") or config.get("purpose") or ""),
            "aliases": tuple(dict.fromkeys(alias for alias in aliases if alias)),
        },
        "syntax_templates": tuple(str(item) for item in list(config.get("syntax_templates") or [])),
        "factor_layers": tuple(dict(item) for item in list(config.get("factor_layers") or [])),
        "factor_labels": factor_labels,
        "factor_values": factor_values,
        "important_factors": important_factors,
        "non_important_factors": non_important_factors,
        "defaults": {str(key): str(value) for key, value in dict(config.get("defaults") or {}).items()},
        "coverage_policy": coverage_policy,
        "python_expand_threshold": int(coverage_policy.get("python_expand_threshold") or config.get("python_expand_threshold") or 200),
        "rendering": {
            "statement_template": str(rendering_doc.get("statement_template") or ""),
            "verification_query_template": str(rendering_doc.get("verification_query_template") or ""),
            "factor_value_bindings": factor_value_bindings,
        },
        "structured_config": config,
        "raw_text": raw_text,
    }
