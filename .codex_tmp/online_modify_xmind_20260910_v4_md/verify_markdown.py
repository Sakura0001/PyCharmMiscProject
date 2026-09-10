"""Strict integrity verifier for the generated scenario-oriented Markdown plan."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterator
import zipfile


EXPECTED_SOURCE_SHA256 = (
    "8e2b1b212c52eb8c9456b83cba66dfcb8a9e2e85430addb376b270e6e4ced978"
)

_REQUIRED_SECTIONS = (
    "场景目标",
    "前置条件",
    "覆盖因子",
    "子运行组合",
    "执行步骤",
    "观测点",
    "预期结果与验收",
    "来源与追溯",
)
_EXPECTED_COUNTS = {
    "sheet_count": 3,
    "topic_count": 7317,
    "scenario_count": 48,
    "dimension_count": 96,
    "original_check_count": 302,
    "original_case_count": 1602,
    "syntax_count": 155,
    "common_factor_count": 35,
    "contract_count": 16,
}
_EXPECTED_PRIORITIES = {"P0": 44, "P1": 3, "P2": 1}
_SCENE_HEADER = re.compile(r"^### (SC\d{2}) (.+) \[(P[012])\]$")
_SOURCE_SCENE = re.compile(r"\[(SC\d{2})\s*·\s*(P[012])\]\s*$")
_DIMENSION_ID = re.compile(r"(?m)^维度编号：\s*([A-I]\d{2})\b")
_ORIGINAL_CHECK = re.compile(r"^T\d{2}\.\d{2}\b")
_OBSERVATION = re.compile(
    r"^- \*\*(?P<object>.+?)\*\*：证据：(?P<evidence>.*?)；判定：(?P<decision>.*)$"
)
_DIMENSION_LINK = re.compile(
    r"\[([^\]\n]+)\]\(#dimension-([^)]+)\)"
)
_INTERNAL_LINK = re.compile(r"\]\(#([^)]+)\)")
_ANCHOR = re.compile(r'<a id="([^"]+)"></a>')
_PLACEHOLDER = re.compile(
    r"(?i)\b(?:TODO|TBD|PLACEHOLDER)\b|"
    r"待填写|未填写|检查正常|正常则通过|通用检查|"
    r"\{\{[^{}\n]+\}\}"
)


def _empty_report() -> dict[str, Any]:
    return {
        "source_sha256": "",
        "source_unchanged": False,
        "sheet_count": 0,
        "topic_count": 0,
        "scenario_count": 0,
        "scenario_priorities": {"P0": 0, "P1": 0, "P2": 0},
        "dimension_count": 0,
        "original_check_count": 0,
        "original_case_count": 0,
        "syntax_count": 0,
        "common_factor_count": 0,
        "contract_count": 0,
        "missing_required_sections": [],
        "missing_source_ids": [],
        "unmapped_dimension_ids": [],
        "duplicate_scene_ids": [],
        "broken_internal_links": [],
        "placeholder_hits": [],
        "errors": [],
    }


def _append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


def _children(topic: dict[str, Any]) -> list[dict[str, Any]]:
    children = topic.get("children")
    if children is None:
        return []
    if not isinstance(children, dict):
        raise ValueError(f"topic {topic.get('id')!r} children is not an object")
    attached = children.get("attached", [])
    if not isinstance(attached, list) or not all(
            isinstance(child, dict) for child in attached):
        raise ValueError(f"topic {topic.get('id')!r} attached children is invalid")
    return attached


def _walk(root: dict[str, Any]) -> Iterator[dict[str, Any]]:
    stack = [root]
    while stack:
        topic = stack.pop()
        yield topic
        stack.extend(reversed(_children(topic)))


def _topic_note(topic: dict[str, Any]) -> str:
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


def _load_workbook(source_bytes: bytes, source: Path) -> list[dict[str, Any]]:
    try:
        from io import BytesIO

        with zipfile.ZipFile(BytesIO(source_bytes)) as archive:
            payload = archive.read("content.json")
    except (zipfile.BadZipFile, KeyError) as exc:
        raise ValueError(f"无法解析 XMind ZIP/content.json：{source}: {exc}") from exc
    try:
        workbook = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"XMind content.json 非法：{source}: {exc}") from exc
    if not isinstance(workbook, list):
        raise ValueError("XMind content.json 顶层不是 Sheet 列表")
    for position, sheet in enumerate(workbook, start=1):
        if not isinstance(sheet, dict) or not isinstance(sheet.get("rootTopic"), dict):
            raise ValueError(f"第 {position} 个 Sheet 缺少合法 rootTopic")
    return workbook


def _find_direct_branch(workbook: list[dict[str, Any]], prefix: str) -> dict[str, Any]:
    matches = [
        child
        for sheet in workbook
        for child in _children(sheet["rootTopic"])
        if str(child.get("title", "")).startswith(prefix)
    ]
    if len(matches) != 1:
        raise ValueError(f"来源分支 {prefix!r} 应恰好出现一次，实际 {len(matches)} 次")
    return matches[0]


def _collect_source_model(
        workbook: list[dict[str, Any]], report: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[str]]:
    topics = [
        topic
        for sheet in workbook
        for topic in _walk(sheet["rootTopic"])
    ]
    report["sheet_count"] = len(workbook)
    report["topic_count"] = len(topics)

    source_scenes: list[tuple[str, str]] = []
    for topic in topics:
        title = topic.get("title")
        match = _SOURCE_SCENE.search(title) if isinstance(title, str) else None
        if match:
            source_scenes.append(match.groups())
    report["scenario_count"] = len(source_scenes)
    priorities = Counter(priority for _, priority in source_scenes)
    report["scenario_priorities"] = {
        priority: priorities[priority] for priority in ("P0", "P1", "P2")
    }

    dimensions: list[str] = []
    # The canonical 96-dimension taxonomy lives on Sheet 1.  Scenario and
    # appendix notes intentionally repeat dimension numbers for traceability.
    for topic in _walk(workbook[0]["rootTopic"]):
        match = _DIMENSION_ID.search(_topic_note(topic))
        if match:
            dimensions.append(match.group(1))
    report["dimension_count"] = len(dimensions)

    cases = _find_direct_branch(workbook, "原始用例全量索引")
    report["original_case_count"] = sum(
        len(_children(chunk))
        for case_family in _children(cases)
        for chunk in _children(case_family)
    )

    syntax = _find_direct_branch(workbook, "语法覆盖索引")
    report["syntax_count"] = sum(
        len(_children(group)) for group in _children(syntax)
    )

    common = _find_direct_branch(workbook, "公共测试因子")
    report["common_factor_count"] = len(_children(common))

    contracts = _find_direct_branch(workbook, "产品契约与待决")
    report["contract_count"] = len(_children(contracts))

    checks = _find_direct_branch(workbook, "原编号检查点")
    report["original_check_count"] = sum(
        bool(_ORIGINAL_CHECK.match(str(topic.get("title", ""))))
        for topic in _walk(checks)
    )

    for key, expected in _EXPECTED_COUNTS.items():
        actual = report[key]
        if actual != expected:
            _append_unique(
                report["errors"],
                f"来源统计 {key} 应为 {expected}，实际为 {actual}",
            )
    if report["scenario_priorities"] != _EXPECTED_PRIORITIES:
        _append_unique(
            report["errors"],
            "来源场景优先级应为 "
            f"{_EXPECTED_PRIORITIES}，实际为 {report['scenario_priorities']}",
        )

    duplicate_topic_ids = [
        identifier
        for identifier, count in Counter(
            str(topic.get("id", "")) for topic in topics
        ).items()
        if not identifier or count != 1
    ]
    if duplicate_topic_ids:
        _append_unique(
            report["errors"],
            f"来源 topic ID 缺失或重复：{', '.join(duplicate_topic_ids[:10])}",
        )
    duplicate_dimensions = [
        identifier for identifier, count in Counter(dimensions).items() if count != 1
    ]
    if duplicate_dimensions:
        _append_unique(
            report["errors"],
            f"来源维度编号重复：{', '.join(duplicate_dimensions)}",
        )
    return topics, dimensions


def _outside_fenced_lines(markdown_text: str) -> list[str]:
    """Return Markdown lines excluding fenced code, where source notes are data."""

    lines: list[str] = []
    fence_character = ""
    fence_length = 0
    for raw_line in markdown_text.splitlines():
        fence = re.match(r"^\s*(`{3,}|~{3,})(?:[^`]*)$", raw_line)
        if fence_character:
            stripped = raw_line.lstrip()
            if stripped.startswith(fence_character * fence_length):
                run = len(stripped) - len(stripped.lstrip(fence_character))
                if run >= fence_length:
                    fence_character = ""
                    fence_length = 0
            continue
        if fence:
            marker = fence.group(1)
            fence_character = marker[0]
            fence_length = len(marker)
            continue
        lines.append(raw_line)
    return lines


def _slug(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value).strip().lower()).strip("-")


def _scene_blocks(lines: list[str]) -> tuple[
        list[tuple[int, str, str]], dict[str, list[list[str]]]
]:
    headings: list[tuple[int, str, str]] = []
    for position, line in enumerate(lines):
        match = _SCENE_HEADER.match(line)
        if match:
            headings.append((position, match.group(1), match.group(3)))

    blocks: dict[str, list[list[str]]] = {}
    for heading_position, (line_number, identifier, _) in enumerate(headings):
        next_scene = (
            headings[heading_position + 1][0]
            if heading_position + 1 < len(headings)
            else len(lines)
        )
        next_level_two = next(
            (
                position
                for position in range(line_number + 1, next_scene)
                if re.match(r"^## (?!#)", lines[position])
            ),
            next_scene,
        )
        blocks.setdefault(identifier, []).append(lines[line_number + 1:next_level_two])
    return headings, blocks


def _section_content(block: list[str], heading: str) -> list[str] | None:
    marker = f"#### {heading}"
    try:
        start = block.index(marker) + 1
    except ValueError:
        return None
    end = next(
        (position for position in range(start, len(block))
         if block[position].startswith("#### ")),
        len(block),
    )
    return block[start:end]


def _verify_markdown(
        markdown_text: str,
        topics: list[dict[str, Any]],
        dimensions: list[str],
        report: dict[str, Any],
) -> None:
    lines = _outside_fenced_lines(markdown_text)
    visible_text = "\n".join(lines)

    anchors = _ANCHOR.findall(visible_text)
    anchor_counts = Counter(anchors)
    for anchor, count in anchor_counts.items():
        if count > 1:
            _append_unique(report["errors"], f"Markdown anchor 重复 {count} 次：{anchor}")

    if topics:
        expected_topic_anchors = {
            f"topic-{_slug(str(topic.get('id', '')))}" for topic in topics
        }
        for topic in topics:
            topic_id = str(topic.get("id", ""))
            expected_anchor = f"topic-{_slug(topic_id)}"
            if anchor_counts[expected_anchor] != 1:
                report["missing_source_ids"].append(topic_id)
                _append_unique(
                    report["errors"],
                    f"源 topic {topic_id} 的 anchor 应恰好出现一次，实际 "
                    f"{anchor_counts[expected_anchor]} 次",
                )
        extra_topic_anchors = sorted(
            anchor
            for anchor in anchor_counts
            if anchor.startswith("topic-") and anchor not in expected_topic_anchors
        )
        for anchor in extra_topic_anchors:
            _append_unique(report["errors"], f"发现额外 topic anchor：{anchor}")

    unique_dimensions = list(dict.fromkeys(dimensions))
    expected_dimension_anchors = {
        f"dimension-{identifier.lower()}" for identifier in unique_dimensions
    }
    for identifier in unique_dimensions:
        anchor = f"dimension-{identifier.lower()}"
        if anchor_counts[anchor] != 1:
            _append_unique(
                report["errors"],
                f"维度 {identifier} 的 anchor 应恰好出现一次，实际 "
                f"{anchor_counts[anchor]} 次",
            )
    extra_dimension_anchors = sorted(
        anchor
        for anchor in anchor_counts
        if anchor.startswith("dimension-")
        and anchor not in expected_dimension_anchors
    )
    for anchor in extra_dimension_anchors:
        _append_unique(report["errors"], f"发现额外 dimension anchor：{anchor}")

    headings, blocks = _scene_blocks(lines)
    markdown_scene_counts = Counter(identifier for _, identifier, _ in headings)
    report["duplicate_scene_ids"] = sorted(
        identifier
        for identifier, count in markdown_scene_counts.items()
        if count > 1
    )
    for identifier in report["duplicate_scene_ids"]:
        _append_unique(
            report["errors"],
            f"场景标题 {identifier} 重复 {markdown_scene_counts[identifier]} 次",
        )

    expected_scene_ids = [f"SC{number:02d}" for number in range(1, 49)]
    unexpected = sorted(set(markdown_scene_counts) - set(expected_scene_ids))
    if unexpected:
        _append_unique(report["errors"], f"出现未知场景标题：{', '.join(unexpected)}")

    source_priorities = {
        match.group(1): match.group(2)
        for topic in topics
        if isinstance(topic.get("title"), str)
        if (match := _SOURCE_SCENE.search(topic["title"]))
    }
    source_dimension_ids = set(unique_dimensions)
    linked_dimensions: set[str] = set()
    coverage_dimension_ids: set[str] = set()
    for identifier in expected_scene_ids:
        occurrences = blocks.get(identifier, [])
        if not occurrences:
            report["missing_required_sections"].append(f"{identifier}:场景")
            _append_unique(report["errors"], f"缺少场景标题：{identifier}")
            continue

        heading_priorities = [
            priority for _, scene_id, priority in headings if scene_id == identifier
        ]
        expected_priority = source_priorities.get(identifier)
        if expected_priority and any(
                priority != expected_priority for priority in heading_priorities):
            _append_unique(
                report["errors"],
                f"{identifier} Markdown 优先级与来源 {expected_priority} 不一致："
                f"{heading_priorities}",
            )

        for occurrence, block in enumerate(occurrences, start=1):
            section_headings = [
                line[len("#### "):]
                for line in block
                if line.startswith("#### ")
            ]
            section_counts = Counter(section_headings)
            for section in _REQUIRED_SECTIONS:
                if section_counts[section] == 0:
                    item = f"{identifier}:{section}"
                    if item not in report["missing_required_sections"]:
                        report["missing_required_sections"].append(item)
                elif section_counts[section] > 1:
                    _append_unique(
                        report["errors"],
                        f"{identifier} 第 {occurrence} 个场景块的小节 {section} "
                        f"重复 {section_counts[section]} 次",
                    )
            extras = [
                section for section in section_headings
                if section not in _REQUIRED_SECTIONS
            ]
            if extras:
                _append_unique(
                    report["errors"],
                    f"{identifier} 第 {occurrence} 个场景块含未知小节："
                    f"{', '.join(extras)}",
                )
            if section_headings != list(_REQUIRED_SECTIONS):
                _append_unique(
                    report["errors"],
                    f"{identifier} 第 {occurrence} 个场景块须按规定顺序且各一次包含 8 个小节",
                )

            observation_lines = _section_content(block, "观测点")
            if observation_lines is not None:
                nonempty = [line for line in observation_lines if line.strip()]
                bullets = [line for line in nonempty if line.startswith("- ")]
                if len(bullets) < 5:
                    _append_unique(
                        report["errors"],
                        f"{identifier} 观测点至少需要 5 项，实际 {len(bullets)} 项",
                    )
                if len(bullets) != len(nonempty):
                    _append_unique(
                        report["errors"],
                        f"{identifier} 观测点存在非 bullet 内容",
                    )
                for bullet_number, bullet in enumerate(bullets, start=1):
                    match = _OBSERVATION.match(bullet)
                    if not match or not all(
                            match.group(field).strip()
                            for field in ("object", "evidence", "decision")
                    ):
                        _append_unique(
                            report["errors"],
                            f"{identifier} 第 {bullet_number} 个观测点不符合"
                            "“- **对象**：证据：非空；判定：非空”",
                        )

            coverage_lines = _section_content(block, "覆盖因子")
            if coverage_lines is not None:
                for link_label, target in _DIMENSION_LINK.findall(
                        "\n".join(coverage_lines)):
                    label_match = re.match(r"^([A-Z]\d+)\s+", link_label)
                    target_identifier = target.upper()
                    coverage_dimension_ids.add(target_identifier)
                    if label_match is None:
                        _append_unique(
                            report["errors"],
                            f"{identifier} 覆盖维度链接标签缺少维度编号：{link_label}",
                        )
                        continue
                    label = label_match.group(1)
                    coverage_dimension_ids.add(label)
                    if (label not in source_dimension_ids
                            or target_identifier not in source_dimension_ids):
                        _append_unique(
                            report["errors"],
                            f"{identifier} 覆盖维度 {label}/dimension-{target} "
                            "不属于源 96 维度",
                        )
                    if label.lower() != target:
                        _append_unique(
                            report["errors"],
                            f"{identifier} 维度链接标签 {label} 与目标 {target} 不一致",
                        )
                    elif label in source_dimension_ids:
                        linked_dimensions.add(label)

    for item in report["missing_required_sections"]:
        _append_unique(report["errors"], f"缺少必需场景小节：{item}")

    report["unmapped_dimension_ids"] = [
        identifier
        for identifier in unique_dimensions
        if identifier not in linked_dimensions
    ]
    if report["unmapped_dimension_ids"]:
        _append_unique(
            report["errors"],
            "场景覆盖因子未挂载维度："
            + ", ".join(report["unmapped_dimension_ids"]),
        )
    extra_linked_dimensions = sorted(
        coverage_dimension_ids - source_dimension_ids
    )
    if extra_linked_dimensions:
        _append_unique(
            report["errors"],
            "场景覆盖因子出现源集合以外维度："
            + ", ".join(extra_linked_dimensions),
        )

    report["broken_internal_links"] = list(dict.fromkeys(
        target
        for target in _INTERNAL_LINK.findall(visible_text)
        if anchor_counts[target] == 0
    ))
    for target in report["broken_internal_links"]:
        _append_unique(report["errors"], f"内部链接没有目标 anchor：{target}")

    report["placeholder_hits"] = list(dict.fromkeys(
        match.group(0) for match in _PLACEHOLDER.finditer(visible_text)
    ))
    for placeholder in report["placeholder_hits"]:
        _append_unique(report["errors"], f"发现明确占位符：{placeholder}")


def verify(source_path: str | Path, markdown_text: str) -> dict[str, Any]:
    """Return a complete JSON-serializable source and Markdown integrity report."""

    report = _empty_report()
    source = Path(source_path)
    topics: list[dict[str, Any]] = []
    dimensions: list[str] = []

    try:
        source_bytes = source.read_bytes()
        report["source_sha256"] = hashlib.sha256(source_bytes).hexdigest()
        report["source_unchanged"] = (
            report["source_sha256"] == EXPECTED_SOURCE_SHA256
        )
        if not report["source_unchanged"]:
            _append_unique(
                report["errors"],
                "来源 XMind SHA-256 已变化："
                f"期望 {EXPECTED_SOURCE_SHA256}，实际 {report['source_sha256']}",
            )
        workbook = _load_workbook(source_bytes, source)
        topics, dimensions = _collect_source_model(workbook, report)
    except Exception as exc:  # Report parse/I/O failures instead of aborting verification.
        _append_unique(report["errors"], f"来源 XMind 校验失败：{exc}")

    try:
        if not isinstance(markdown_text, str):
            raise TypeError("markdown_text 必须是字符串")
        _verify_markdown(markdown_text, topics, dimensions, report)
    except Exception as exc:  # Preserve the complete schema for malformed Markdown.
        _append_unique(report["errors"], f"Markdown 校验失败：{exc}")

    return report


def main() -> None:
    from render_markdown import OUTPUT_MARKDOWN, SOURCE_XMIND

    output_path = Path(__file__).with_name("verification.json")
    markdown_text = ""
    read_error = ""
    try:
        markdown_text = OUTPUT_MARKDOWN.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        read_error = f"无法读取 Markdown {OUTPUT_MARKDOWN}：{exc}"

    report = verify(SOURCE_XMIND, markdown_text)
    if read_error:
        _append_unique(report["errors"], read_error)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if report["errors"]:
        print(
            f"FAIL: {len(report['errors'])} 个问题；"
            f"报告已写入 {output_path}"
        )
        raise SystemExit(1)
    print(
        "PASS: 3 sheets, 7317 topics, 96 dimensions, 48 scenarios; "
        f"报告已写入 {output_path}"
    )


if __name__ == "__main__":
    main()
