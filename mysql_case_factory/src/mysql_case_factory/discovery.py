from __future__ import annotations

from pathlib import Path

from .artifact_store import asset_root
from .skill_loader import load_skill


def _normalize_text(text: str) -> str:
    return " ".join(text.lower().replace("_", " ").replace("-", " ").split())


def _read_object_metadata(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8").splitlines()[:12]
    metadata: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("-- "):
            continue
        body = stripped[3:]
        if ":" not in body:
            continue
        key, value = body.split(":", 1)
        metadata[key.strip()] = value.strip()
    return metadata


def list_object_templates(root: Path | None = None) -> list[dict]:
    repo_root = Path(root) if root is not None else asset_root()
    objects: list[dict] = []
    paths = list((repo_root / "objects").glob("**/*.sql"))
    paths.extend((repo_root / "skills").glob("*/assets/objects/**/*.sql"))
    paths.extend((repo_root / "assets" / "objects").glob("**/*.sql"))
    for path in sorted(dict.fromkeys(paths)):
        metadata = _read_object_metadata(path)
        object_key = metadata.get("object_key") or path.parent.name
        aliases = [item.strip() for item in metadata.get("aliases", "").split(",") if item.strip()]
        aliases.extend([object_key, object_key.replace("_", " ")])
        objects.append(
            {
                "object_key": object_key,
                "path": str(path),
                "category": path.parent.parent.name if path.parent.parent else "",
                "aliases": tuple(dict.fromkeys(aliases)),
            }
        )
    return objects


def list_statement_skills(root: Path | None = None) -> list[dict]:
    repo_root = Path(root) if root is not None else asset_root()
    skills: list[dict] = []
    paths = list((repo_root / "skills").glob("*/references/statements/**/*.md"))
    paths.extend((repo_root / "references" / "statements").glob("**/*.md"))
    for path in sorted(dict.fromkeys(paths)):
        if path.parent.name == "common":
            continue
        skill = load_skill(path)
        if skill["kind"] == "statement":
            skills.append(skill)
    return skills


def list_mainflow_skills(root: Path | None = None) -> list[dict]:
    repo_root = Path(root) if root is not None else asset_root()
    skills: list[dict] = []
    paths = list((repo_root / "skills").glob("*/references/mainflow/*.md"))
    paths.extend((repo_root / "references" / "mainflow").glob("*.md"))
    for path in sorted(dict.fromkeys(paths)):
        if path.parent.name == "common":
            continue
        skill = load_skill(path)
        if skill["kind"] == "mainflow":
            skills.append(skill)
    return skills


def _score_request(request_text: str, aliases: tuple[str, ...]) -> int:
    normalized = _normalize_text(request_text)
    score = 0
    for alias in aliases:
        normalized_alias = _normalize_text(alias)
        if normalized_alias and normalized_alias in normalized:
            score += max(1, len(normalized_alias))
    return score


def discover_request_candidates(request_text: str, root: Path | None = None) -> dict:
    object_candidates = sorted(
        (
            {
                **entry,
                "score": _score_request(request_text, entry["aliases"]),
            }
            for entry in list_object_templates(root)
        ),
        key=lambda item: (-item["score"], item["object_key"]),
    )
    skill_candidates = sorted(
        (
            {
                **entry,
                "score": _score_request(request_text, entry["statement"]["aliases"]),
            }
            for entry in list_statement_skills(root)
        ),
        key=lambda item: (-item["score"], item["statement"]["key"]),
    )
    return {
        "objects": object_candidates,
        "statement_skills": skill_candidates,
        "mainflow_skills": list_mainflow_skills(root),
    }
