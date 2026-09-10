"""Deterministically render the V3 XMind test plan as scenario-oriented Markdown."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Iterable, Iterator

from scenario_policies import FACTOR_CATEGORIES, SCENARIO_POLICIES
from xmind_model import find_scenes, load_xmind, source_stats, topic_note, walk_topic


SOURCE_XMIND = Path(
    "/Users/yuyu/PyCharmMiscProject/outputs/online_modify_xmind_20260910_v3/"
    "RDS_MySQL_8.0.45_测试计划反串讲_V3_逐项通俗说明版.xmind"
)
OUTPUT_MARKDOWN = SOURCE_XMIND.with_name(
    "RDS_MySQL_8.0.45_测试计划_V4_场景化完整覆盖版.md"
)

SUPPLEMENTAL_DIMENSIONS_BY_SCENE = {
    "SC01": ("B02",),
    "SC25": ("B08",),
    "SC46": ("B09",),
    "SC31": ("B10",),
    "SC13": ("D07", "D22"),
}

_DIMENSION_PATTERN = re.compile(r"(?m)^维度编号：\s*([A-I]\d{2})\b")
_SCENE_SUFFIX_PATTERN = re.compile(r"\s*\[SC\d{2}\s*·\s*P[012]\]\s*$")


def md_text(value: Any) -> str:
    """Escape a value for an inline Markdown/table cell."""

    if value is None:
        return ""
    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    return (
        text.replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("\n", "<br>")
    )


def md_anchor(value: Any) -> str:
    """Create a stable lowercase ASCII Markdown anchor identifier."""

    slug = re.sub(r"[^a-z0-9]+", "-", str(value).strip().lower()).strip("-")
    if not slug:
        raise ValueError(f"cannot create Markdown anchor from {value!r}")
    return slug


def _raw_block(label: str, content: str) -> list[str]:
    if not content:
        return [f"**{label}：**（无）"]
    longest = max((len(run) for run in re.findall(r"`+", content)), default=0)
    fence = "`" * max(3, longest + 1)
    return [f"**{label}：**", "", f"{fence}text", content, fence]


def _href_markdown(href: str) -> str:
    label = md_text(href)
    if href.startswith("xmind:#"):
        target_id = href[len("xmind:#"):]
        return f"[{label}](#topic-{md_anchor(target_id)})"
    if href.startswith(("https://", "http://")):
        return f"[{label}]({href})"
    return f"`{label}`"


def _children(topic: dict[str, Any]) -> list[dict[str, Any]]:
    children = topic.get("children")
    if children is None:
        return []
    attached = children.get("attached")
    return attached if attached is not None else []


def _walk_with_depth(topic: dict[str, Any], depth: int = 0) -> Iterator[tuple[dict[str, Any], int]]:
    yield topic, depth
    for child in _children(topic):
        yield from _walk_with_depth(child, depth + 1)


def _dimension_records(workbook: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not workbook:
        raise ValueError("XMind workbook has no sheets")
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for topic in walk_topic(workbook[0]["rootTopic"]):
        note = topic_note(topic)
        match = _DIMENSION_PATTERN.search(note)
        if match is None:
            continue
        identifier = match.group(1)
        if identifier in seen:
            raise ValueError(f"duplicate dimension ID: {identifier}")
        seen.add(identifier)
        records.append({
            "dimension_id": identifier,
            "title": topic["title"].splitlines()[0],
            "topic": topic,
            "values": _children(topic),
        })
    if len(records) != 96:
        raise ValueError(f"expected 96 dimensions; found {len(records)}")
    return records


def render_factor_table(policy: dict[str, Any]) -> str:
    """Render all nine explicit factor scopes for one scenario."""

    lines = [
        "| 因子类别 | 覆盖要求 | 具体范围或例外 | 执行策略 |",
        "|---|---|---|---|",
    ]
    scopes = policy["factor_scopes"]
    for category in FACTOR_CATEGORIES:
        scope = scopes[category]
        lines.append(
            f"| {md_text(category)} | {md_text(scope['requirement'])} | "
            f"{md_text(scope['range'])} | {md_text(scope['strategy'])} |"
        )
    return "\n".join(lines)


def render_observations(policy: dict[str, Any]) -> str:
    """Render concrete observation evidence and decision conditions."""

    lines = []
    for point in policy["observation_points"]:
        lines.append(
            f"- **{md_text(point['object'])}**："
            f"证据：{md_text(point['evidence'])}；"
            f"判定：{md_text(point['decision'])}"
        )
    return "\n".join(lines)


def render_global_scope(workbook: list[dict[str, Any]]) -> str:
    """Render the fixed test scope and prerequisites shared by all scenarios."""

    source_note = topic_note(workbook[0]["rootTopic"])
    lines = [
        "## 范围",
        "",
        "- 本轮验收 INPLACE 在线修改列类型与 Online DDL 唯一键冲突优化。",
        "- 类型 INSTANT 为后续范围，不计入当前 PASS。",
        "- 阿里环境作为主机功能对照；我方主机、备机分别对独立预期核验。",
        "- “全部覆盖”表示全局因子目录中所有兼容且适用的取值，"
        "不做无意义的全笛卡尔积；不适用/例外/专属子运行须显式说明。",
        "",
        *_raw_block("源范围声明", source_note),
        "",
        "## 全局前置条件",
        "",
        "- 记录准确的 MySQL 8.0.45 版本、内核构建、实例拓扑、权限和全部关键配置。",
        "- 两项本轮功能固定 ON，阿里类型 INSTANT 增强固定 OFF，测试期间不改这些开关。",
        "- 同一子运行使用同构源表、同逻辑初始数据、同目标操作及同算法锁要求。",
        "- 先运行阿里主机，再运行我方主机；我方备机追平位点后独立校验。",
        "- 所有并发、持续时间、资源、超时、停止、恢复和清理条件均须有界且留证。",
    ]
    return "\n".join(lines)


def _render_catalog_value(value: dict[str, Any], position: int) -> list[str]:
    lines = [
        f"- 直接取值 {position}：{md_text(value.get('title', ''))}",
        f"  - 原始 ID：`{md_text(value.get('id', ''))}`",
    ]
    lines.extend(_raw_block("取值 notes", topic_note(value)))
    if value.get("href"):
        lines.append(f"- 原始 href：{_href_markdown(value['href'])}")
    else:
        lines.append("- 原始 href：（无）")
    return lines


def render_factor_catalog(workbook: list[dict[str, Any]]) -> str:
    """Render the 96 source dimensions and their direct values."""

    lines = [
        "## 96 维度目录",
        "",
        "维度按第一张 Sheet 的源顺序排列；场景链接使用稳定的 dimension 锚点。",
    ]
    for dimension in _dimension_records(workbook):
        identifier = dimension["dimension_id"]
        topic = dimension["topic"]
        lines.extend([
            "",
            f'<a id="dimension-{identifier.lower()}"></a>',
            f"### {identifier} {md_text(dimension['title'])}",
            "",
            f"- 原始 topic ID：`{md_text(topic['id'])}`",
            f"- 原始标题：{md_text(topic['title'])}",
        ])
        lines.extend(_raw_block("维度 notes", topic_note(topic)))
        if topic.get("href"):
            lines.append(f"- 原始 href：{_href_markdown(topic['href'])}")
        else:
            lines.append("- 原始 href：（无）")
        lines.append(f"- 直接取值数：{len(dimension['values'])}")
        for position, value in enumerate(dimension["values"], start=1):
            lines.extend(_render_catalog_value(value, position))
    return "\n".join(lines)


def _render_topic_tree(topics: Iterable[dict[str, Any]]) -> str:
    lines: list[str] = []
    for root in topics:
        for topic, depth in _walk_with_depth(root):
            indent = "  " * depth
            lines.append(f"{indent}- 标题：{md_text(topic.get('title', ''))}")
            lines.append(f"{indent}  - 原始 ID：`{md_text(topic.get('id', ''))}`")
            note = topic_note(topic)
            if note:
                lines.extend(_raw_block(f"topic {topic.get('id', '')} notes", note))
            else:
                lines.append(f"{indent}  - notes：（无）")
            if topic.get("href"):
                lines.append(f"{indent}  - 原始 href：{_href_markdown(topic['href'])}")
            else:
                lines.append(f"{indent}  - 原始 href：（无）")
    return "\n".join(lines)


def _linked_dimensions(
        scene: dict[str, Any], dimensions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_topic_id = {dimension["topic"]["id"]: dimension for dimension in dimensions}
    by_id = {dimension["dimension_id"]: dimension for dimension in dimensions}
    linked: list[dict[str, Any]] = []
    seen: set[str] = set()
    for reference in scene["references"]:
        href = reference["href"]
        target = href[len("xmind:#"):] if href.startswith("xmind:#") else None
        dimension = by_topic_id.get(target)
        if dimension and dimension["dimension_id"] not in seen:
            linked.append(dimension)
            seen.add(dimension["dimension_id"])
    for identifier in SUPPLEMENTAL_DIMENSIONS_BY_SCENE.get(scene["scene_id"], ()):
        if identifier not in seen:
            linked.append(by_id[identifier])
            seen.add(identifier)
    return linked


def render_scene(
        scene: dict[str, Any],
        policy: dict[str, Any],
        dimensions: list[dict[str, Any]],
) -> str:
    """Render one normalized source scene into exactly eight subsections."""

    name = _SCENE_SUFFIX_PATTERN.sub("", scene["title"]).strip()
    sections = scene["sections"]
    linked_dimensions = _linked_dimensions(scene, dimensions)
    dimensions_by_id = {
        dimension["dimension_id"]: dimension for dimension in dimensions
    }
    supplemental_dimensions = [
        dimensions_by_id[identifier]
        for identifier in SUPPLEMENTAL_DIMENSIONS_BY_SCENE.get(scene["scene_id"], ())
    ]
    dimension_links = "、".join(
        f"[{dimension['dimension_id']} {md_text(dimension['title'])}]"
        f"(#dimension-{dimension['dimension_id'].lower()})"
        for dimension in linked_dimensions
    ) or "（无）"

    lines = [
        f"### {scene['scene_id']} {md_text(name)} [{scene['priority']}]",
        "",
        "#### 场景目标",
        "",
        f"- 业务目标：{md_text(policy['goal'])}",
        f"- 风险假设：{md_text(policy['risk'])}",
        "- 原第 1 节（场景条件，无损保留）：",
        _render_topic_tree([sections[0]]),
        "",
        "#### 前置条件",
        "",
        *[f"- {md_text(item)}" for item in policy["prerequisites"]],
        "",
        "#### 覆盖因子",
        "",
        f"- 关联维度：{dimension_links}",
        "",
        render_factor_table(policy),
        "",
        "#### 子运行组合",
        "",
        "- 原第 4 节（必跑变体，无损保留）：",
        _render_topic_tree([sections[3]]),
        "",
        "#### 执行步骤",
        "",
        "- 原第 2 节（执行顺序，无损保留）：",
        _render_topic_tree([sections[1]]),
        "",
        "#### 观测点",
        "",
        render_observations(policy),
        "",
        "#### 预期结果与验收",
        "",
        "- 原第 3 节（预期与校验，无损保留）：",
        _render_topic_tree([sections[2]]),
        "- 补充验收条件：",
        *[f"  - {md_text(item)}" for item in policy["acceptance_additions"]],
        "",
        "#### 来源与追溯",
        "",
        f"- 场景原始 topic ID：`{md_text(scene['topic_id'])}`",
        f"- 场景原始标题：{md_text(scene['title'])}",
    ]
    lines.extend(_raw_block("场景原始 notes", scene["notes"]))
    supplemental_links = "、".join(
        f"[{dimension['dimension_id']} {md_text(dimension['title'])}]"
        f"(#dimension-{dimension['dimension_id'].lower()})"
        for dimension in supplemental_dimensions
    ) or "（无）"
    lines.extend([
        f"- 补充挂载维度：{supplemental_links}",
        "- 原第 5/6/7 节（关联维度、原始用例、原编号技术核对，无损保留）：",
        _render_topic_tree(sections[4:7]),
        "- 场景 references（保持源顺序及重复项）：",
    ])
    for reference in scene["references"]:
        lines.append(
            f"  - [{md_text(reference['title'])}]"
            f"(#topic-{md_anchor(reference['topic_id'])})；"
            f"源 topic ID：`{md_text(reference['topic_id'])}`；"
            f"原始 href：`{md_text(reference['href'])}`"
        )
    if not scene["references"]:
        lines.append("  - （无）")
    return "\n".join(lines)


def render_source_appendix(workbook: list[dict[str, Any]]) -> str:
    """Render all source topics exactly once, with stable target anchors."""

    lines = [
        "## 完整 3-Sheet 来源附录",
        "",
        "以下按 Sheet、topic 的原始顺序深度优先展开。所有原始链接均显示原 href。",
    ]
    anchored: set[str] = set()
    sequence = 0
    for sheet_number, sheet in enumerate(workbook, start=1):
        lines.extend([
            "",
            f"### Sheet {sheet_number}: {md_text(sheet['title'])}",
            "",
            f"- Sheet 原始 ID：`{md_text(sheet.get('id', ''))}`",
            f"- 根 topic ID：`{md_text(sheet['rootTopic'].get('id', ''))}`",
        ])
        for topic, depth in _walk_with_depth(sheet["rootTopic"]):
            sequence += 1
            topic_id = str(topic.get("id", ""))
            anchor = f"topic-{md_anchor(topic_id)}"
            if anchor in anchored:
                raise ValueError(f"duplicate topic anchor: {anchor}")
            anchored.add(anchor)
            lines.extend([
                "",
                f'<a id="{anchor}"></a>',
                f"- Topic {sequence}（源层级 {depth}）",
                f"  - 原始 ID：`{md_text(topic_id)}`",
                f"  - 标题：{md_text(topic.get('title', ''))}",
            ])
            note = topic_note(topic)
            if note:
                lines.extend(_raw_block(f"topic {topic_id} notes", note))
            else:
                lines.append("  - notes：（无）")
            if topic.get("href"):
                lines.append(f"  - 原始 href：{_href_markdown(topic['href'])}")
            else:
                lines.append("  - 原始 href：（无）")
    return "\n".join(lines)


def render_document(
        workbook: list[dict[str, Any]],
        policies: dict[str, dict[str, Any]] = SCENARIO_POLICIES,
) -> str:
    """Render the complete V4 document with exactly one trailing newline."""

    dimensions = _dimension_records(workbook)
    scenes = find_scenes(workbook)
    parts = [
        "\n".join([
            "# RDS MySQL 8.0.45 测试计划 V4 · 场景化完整覆盖版",
            "",
            "> 声明：本文由指定 V3 XMind 与显式场景覆盖策略确定性生成；"
            "计划覆盖不等于实测通过。",
        ]),
        render_global_scope(workbook),
        render_factor_catalog(workbook),
        "## 48 综合场景",
        *[render_scene(scene, policies[scene["scene_id"]], dimensions) for scene in scenes],
        render_source_appendix(workbook),
    ]
    stats = source_stats(workbook)
    parts.append("\n".join([
        "## 完整性摘要",
        "",
        f"- {stats['sheets']} 张 Sheet。",
        f"- {len(dimensions)} 个维度。",
        f"- {stats['scenes']} 个场景。",
        f"- {stats['topics']} 个 topic，且每个 topic anchor 唯一。",
        f"- {len(scenes) * 8} 个场景小节；每场景恰好 8 节、9 类覆盖因子。",
        "- 所有 xmind 内部链接均转换为本文 topic anchor，同时显示原始 href。",
    ]))
    return "\n\n".join(part.strip("\n") for part in parts) + "\n"


def main() -> None:
    workbook = load_xmind(SOURCE_XMIND)
    OUTPUT_MARKDOWN.write_text(render_document(workbook), encoding="utf-8")


if __name__ == "__main__":
    main()
