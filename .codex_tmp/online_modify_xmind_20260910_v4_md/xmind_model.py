"""Read the source XMind workbook and expose its ordered topic model."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re
from typing import Any, Iterator
import zipfile


_SCENE_ID_PATTERN = re.compile(r"\[(SC\d{2})\b")
_SCENE_HEADER_PATTERN = re.compile(r"\[(SC\d{2})\s*·\s*(P[012])\]")
_EXPECTED_SCENE_IDS = tuple(f"SC{number:02d}" for number in range(1, 49))


def load_xmind(path: str | Path) -> list[dict[str, Any]]:
    """Load ``content.json`` while retaining its source ordering and fields."""

    source = Path(path)
    try:
        with zipfile.ZipFile(source) as archive:
            try:
                payload = archive.read("content.json")
            except KeyError as exc:
                raise ValueError(
                    f"XMind archive is missing content.json: {source}"
                ) from exc
    except zipfile.BadZipFile as exc:
        raise ValueError(f"invalid XMind ZIP archive: {source}") from exc

    try:
        workbook = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid XMind content.json: {source}: {exc}") from exc

    if not isinstance(workbook, list):
        raise ValueError("invalid XMind content.json: top level must be a sheet list")
    for position, sheet in enumerate(workbook, start=1):
        if not isinstance(sheet, dict):
            raise ValueError(f"invalid XMind sheet at position {position}: expected object")
        if not isinstance(sheet.get("title"), str):
            raise ValueError(f"invalid XMind sheet at position {position}: missing title")
        if not isinstance(sheet.get("rootTopic"), dict):
            raise ValueError(f"invalid XMind sheet at position {position}: missing rootTopic")
    return workbook


def _attached_children(topic: dict[str, Any]) -> list[dict[str, Any]]:
    children = topic.get("children")
    if not isinstance(children, dict):
        return []
    attached = children.get("attached")
    if not isinstance(attached, list):
        return []
    return attached


def walk_topic(topic: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """Yield a topic tree in XMind source order, parent before children."""

    yield topic
    for child in _attached_children(topic):
        yield from walk_topic(child)


def topic_note(topic: dict[str, Any]) -> str:
    """Return the readable note text from an XMind topic, or an empty string."""

    notes = topic.get("notes")
    if isinstance(notes, str):
        return notes
    if not isinstance(notes, dict):
        return ""
    for representation in ("plain", "html"):
        value = notes.get(representation)
        if isinstance(value, str):
            return value
        if isinstance(value, dict) and isinstance(value.get("content"), str):
            return value["content"]
    return ""


def scene_id(topic: dict[str, Any]) -> str | None:
    """Extract an ``SCnn`` identifier from a scenario topic title."""

    title = topic.get("title")
    if not isinstance(title, str):
        return None
    match = _SCENE_ID_PATTERN.search(title)
    return match.group(1) if match else None


def find_scenes(workbook: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return SC01-SC48 in source order and reject an incomplete scene set."""

    scenes: list[dict[str, Any]] = []
    seen: set[str] = set()
    for sheet in workbook:
        root = sheet.get("rootTopic")
        if not isinstance(root, dict):
            raise ValueError("invalid XMind workbook: sheet missing rootTopic")
        for topic in walk_topic(root):
            identifier = scene_id(topic)
            if identifier is None:
                continue
            if identifier in seen:
                raise ValueError(f"duplicate scene ID: {identifier}")
            seen.add(identifier)

            title = topic.get("title", "")
            header = _SCENE_HEADER_PATTERN.search(title)
            if header is None:
                raise ValueError(f"scene {identifier} is missing a P0/P1/P2 priority")
            sections = _attached_children(topic)
            if len(sections) != 7:
                raise ValueError(
                    f"scene {identifier} must contain 7 source sections; "
                    f"found {len(sections)}"
                )
            scenes.append({
                "scene_id": identifier,
                "priority": header.group(2),
                "title": title,
                "topic_id": topic.get("id"),
                "sections": sections,
            })

    expected = set(_EXPECTED_SCENE_IDS)
    missing = [identifier for identifier in _EXPECTED_SCENE_IDS if identifier not in seen]
    if missing:
        raise ValueError(f"missing scene IDs: {', '.join(missing)}")
    unexpected = sorted(seen - expected)
    if unexpected:
        raise ValueError(f"unexpected scene IDs: {', '.join(unexpected)}")
    return scenes


def source_stats(workbook: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize sheet, topic, scene, and priority counts."""

    topic_count = 0
    for sheet in workbook:
        root = sheet.get("rootTopic")
        if not isinstance(root, dict):
            raise ValueError("invalid XMind workbook: sheet missing rootTopic")
        topic_count += sum(1 for _ in walk_topic(root))

    scenes = find_scenes(workbook)
    counts = Counter(scene["priority"] for scene in scenes)
    return {
        "sheets": len(workbook),
        "topics": topic_count,
        "scenes": len(scenes),
        "priorities": {priority: counts[priority] for priority in ("P0", "P1", "P2")},
    }
