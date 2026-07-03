from __future__ import annotations

import json
import shutil
from pathlib import Path

import yaml


ARTIFACT_SUBDIRS = (
    "generated_programs",
    "generated_sql",
    "test_plans",
    "evaluations",
    "intermediates",
)


def asset_root() -> Path:
    return Path(__file__).resolve().parents[2]


def prepare_artifacts(runtime_root: Path | None = None, clear: bool = True) -> dict[str, Path]:
    root = Path(runtime_root) if runtime_root is not None else asset_root()
    artifacts_root = root / "artifacts"
    artifacts_root.mkdir(parents=True, exist_ok=True)

    if clear:
        for child in list(artifacts_root.iterdir()):
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()

    paths = {"artifacts_root": artifacts_root}
    for name in ARTIFACT_SUBDIRS:
        path = artifacts_root / name
        path.mkdir(parents=True, exist_ok=True)
        paths[name] = path
    return paths


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, content: dict) -> None:
    write_text(path, json.dumps(content, ensure_ascii=False, indent=2) + "\n")


def write_yaml(path: Path, content: dict) -> None:
    write_text(path, yaml.safe_dump(content, allow_unicode=True, sort_keys=False))
