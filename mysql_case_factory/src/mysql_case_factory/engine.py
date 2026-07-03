from __future__ import annotations

from pathlib import Path

from .artifact_store import asset_root, prepare_artifacts, write_json, write_text, write_yaml
from .discovery import discover_request_candidates, list_mainflow_skills, list_object_templates, list_statement_skills
from .renderer import build_bindings, build_name_context, compose_sql_script, render_object_template, render_statement
from .skill_loader import load_skill


def load_statement_skill(skill_path: str | Path) -> dict:
    skill = load_skill(Path(skill_path))
    if skill["kind"] != "statement":
        raise ValueError(f"不是 statement skill: {skill_path}")
    return skill


def load_mainflow_skill(skill_path: str | Path) -> dict:
    skill = load_skill(Path(skill_path))
    if skill["kind"] != "mainflow":
        raise ValueError(f"不是 mainflow skill: {skill_path}")
    return skill


__all__ = [
    "asset_root",
    "prepare_artifacts",
    "write_text",
    "write_json",
    "write_yaml",
    "list_object_templates",
    "list_statement_skills",
    "list_mainflow_skills",
    "discover_request_candidates",
    "load_statement_skill",
    "load_mainflow_skill",
    "build_bindings",
    "build_name_context",
    "render_object_template",
    "render_statement",
    "compose_sql_script",
]
