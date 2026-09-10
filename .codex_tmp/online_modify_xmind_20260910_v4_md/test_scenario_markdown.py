"""Contract tests for explicit, reviewable scenario coverage policies."""

from copy import deepcopy
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from scenario_policies import FACTOR_CATEGORIES, SCENARIO_POLICIES, _policy

try:
    from xmind_model import (
        find_scenes,
        load_xmind,
        scene_id,
        source_stats,
        topic_note,
        walk_topic,
    )
except ModuleNotFoundError as exc:
    if exc.name != "xmind_model":
        raise
    find_scenes = load_xmind = scene_id = source_stats = topic_note = walk_topic = None

try:
    from render_markdown import (
        OUTPUT_MARKDOWN as RENDER_OUTPUT_MARKDOWN,
        SOURCE_XMIND as RENDER_SOURCE_XMIND,
        _raw_block,
        _render_topic_tree,
        _walk_with_depth,
        md_anchor,
        md_text,
        render_document,
        render_factor_catalog,
        render_factor_table,
        render_global_scope,
        render_observations,
        render_scene,
        render_source_appendix,
    )
except ModuleNotFoundError as exc:
    if exc.name != "render_markdown":
        raise
    RENDER_OUTPUT_MARKDOWN = RENDER_SOURCE_XMIND = None
    _raw_block = _render_topic_tree = _walk_with_depth = None
    md_anchor = md_text = render_document = render_factor_catalog = None
    render_factor_table = render_global_scope = render_observations = None
    render_scene = render_source_appendix = None

try:
    from render_markdown import SUPPLEMENTAL_DIMENSIONS_BY_SCENE
except (ImportError, ModuleNotFoundError):
    SUPPLEMENTAL_DIMENSIONS_BY_SCENE = None

try:
    from verify_markdown import EXPECTED_SOURCE_SHA256, main as verify_main, verify
except ModuleNotFoundError as exc:
    if exc.name != "verify_markdown":
        raise
    EXPECTED_SOURCE_SHA256 = None
    verify_main = None
    verify = None


SOURCE_XMIND = Path(
    "/Users/yuyu/PyCharmMiscProject/outputs/online_modify_xmind_20260910_v3/"
    "RDS_MySQL_8.0.45_测试计划反串讲_V3_逐项通俗说明版.xmind"
)


# Independently authored from the SC01–SC48 source mechanisms. Do not derive
# this oracle from scenario_policies: a production rename must not rewrite it.
SCENARIO_MECHANISM_TERMS = {
    "SC01": ("自增", "旧上限", "二级"),
    "SC02": ("复合主键", "扫描", "row log"),
    "SC03": ("隐藏 row_id", "nullable UNIQUE", "聚簇"),
    "SC04": ("完整类型值域", "同符号", "SIGNED"),
    "SC05": ("255/256", "utf8mb4", "前缀"),
    "SC06": ("PAD", "保存点", "尾空格"),
    "SC07": ("BINARY", "补零", "前缀"),
    "SC08": ("VARBINARY", "页外", "Lmax"),
    "SC09": ("DECIMAL", "D 不变", "9 位"),
    "SC10": ("CHANGE", "FIRST/AFTER", "旧句柄"),
    "SC11": ("复合前缀", "DROP/ADD", "冲突集合"),
    "SC12": ("字节限额", "复合总长", "原子"),
    "SC13": ("降序", "不可见", "覆盖"),
    "SC14": ("MVI", "四行", "SQL NULL", "崩溃"),
    "SC15": ("FULLTEXT", "SPATIAL", "已有", "新增"),
    "SC16": ("虚拟列", "表达式不变", "SHARED", "NONE"),
    "SC17": ("基列", "生成结果", "溢出", "BIGINT"),
    "SC18": ("函数索引", "表达式", "改基列名"),
    "SC19": ("外键", "父先", "第二侧", "中间态"),
    "SC20": ("子先", "自引用", "扇出", "级联"),
    "SC21": ("BINARY", "VARBINARY", "单侧", "拒绝"),
    "SC22": ("非分区列", "跨叶", "路由"),
    "SC23": ("一级", "二级", "间接", "分区键", "拒绝"),
    "SC24": ("64", "48", "320", "CREATE", "扩展"),
    "SC25": ("多列", "ADD", "DROP", "调序"),
    "SC26": ("安全扩宽", "压缩列", "表达式", "原子"),
    "SC27": ("ADD/DROP/RENAME KEY", "索引", "同句"),
    "SC28": ("UNIQUE", "CHECK", "FK", "最终违规"),
    "SC29": ("FORCE", "ENGINE", "ROW_FORMAT", "字符集"),
    "SC30": ("155", "PREPARE", "EXECUTE", "第一失败阶段"),
    "SC31": ("扫描前后", "重插", "保存点", "row log"),
    "SC32": ("非唯一", "临时回放冲突", "最终", "合法"),
    "SC33": ("唯一列自身", "多 UNIQUE", "REPLACE/IODKU"),
    "SC34": ("真实重复", "排除", "原定义", "后续"),
    "SC35": ("MDL", "read view", "队列", "取消"),
    "SC36": ("XA", "PREPARED", "COMMIT/ROLLBACK", "重启"),
    "SC37": ("row log", "越限", "容量", "四轮"),
    "SC38": ("持久提交", "崩溃", "响应前", "恢复"),
    "SC39": ("二次", "恢复回滚", "幂等"),
    "SC40": ("临时文件", "中间表", "内存分配", "原子"),
    "SC41": ("ROW", "STATEMENT", "MIXED", "精确", "追平"),
    "SC42": ("主备", "切换", "新主", "原主"),
    "SC43": ("备份", "PITR", "恢复点", "DDL 前"),
    "SC44": ("响应丢失", "预处理", "幂等", "对账"),
    "SC45": ("大表", "性能", "无 DDL", "SHARED"),
    "SC46": ("连续", "克隆", "资源", "趋势"),
    "SC47": ("跨厂商", "缺陷", "增强", "独立期望"),
    "SC48": ("INSTANT", "OFF/ON", "范围外", "不计当前 PASS"),
}


# Independently authored observation mechanisms/evidence. Goals and scopes must
# never supply the words required by this observation-only oracle.
OBSERVATION_KEYWORDS_BY_SCENE = {
    "SC01": ("自增", "旧上限", "回表", "提交位点"),
    "SC02": ("扫描", "旧键/新键", "复合键", "事务时间线"),
    "SC03": ("聚簇", "NULL", "稳定标识", "事务回执"),
    "SC04": ("范围包含", "不安全边", "64 位", "errno/SQLSTATE"),
    "SC05": ("CHAR_LENGTH", "OCTET_LENGTH", "前缀", "SHOW INDEX"),
    "SC06": ("排序规则", "SAVEPOINT", "尾空格", "账本"),
    "SC07": ("补零", "HEX/LENGTH", "255→256", "前缀"),
    "SC08": ("Lmax", "页外", "HEX/LENGTH", "长值提交账本"),
    "SC09": ("M/D", "十进制", "精度/标度", "重复回执"),
    "SC10": ("FIRST/AFTER", "不可见", "旧新句柄", "SHOW CREATE"),
    "SC11": ("SUB_PART", "扩大组", "复合唯一", "SHOW INDEX"),
    "SC12": ("字节限额", "页大小", "同句原子性", "errno/SQLSTATE"),
    "SC13": ("EXPLAIN", "ASC/DESC", "不可见", "SHOW INDEX"),
    "SC14": ("MVI", "四行", "崩溃", "错误日志"),
    "SC15": ("已有与新增", "词项", "SRID", "写等待", "回执"),
    "SC16": ("NONE", "SHARED", "写等待链", "表达式不变"),
    "SC17": ("窄结果", "溢出", "BIGINT", "提交回执"),
    "SC18": ("CAST", "函数索引", "文本依赖", "调用回执"),
    "SC19": ("父侧提交", "第二侧失败", "过渡规则", "FK 索引"),
    "SC20": ("子先中间态", "级联", "全图", "删除/更新账本"),
    "SC21": ("BINARY", "VARBINARY", "两侧拒绝", "HEX/LENGTH"),
    "SC22": ("非路由", "跨叶", "剪枝", "执行计划"),
    "SC23": ("p/s", "受限键", "安全 c", "分区定义快照"),
    "SC24": ("64", "320", "48", "CREATE", "执行阶段"),
    "SC25": ("同句动作类", "全列", "默认写入", "第一错误阶段"),
    "SC26": ("压缩映射", "表达式", "安全子句", "提交账本"),
    "SC27": ("SHOW INDEX", "重名/缺失/超限", "ADD/DROP", "回执"),
    "SC28": ("最终违规", "CHECK/FK", "约束前后快照", "提交账本"),
    "SC29": ("charset/collation", "物理选项", "转换字节", "快照"),
    "SC30": ("155", "PREPARE/EXECUTE", "第一失败阶段", "回执"),
    "SC31": ("扫描屏障", "ROLLBACK TO", "旧新键", "等待链"),
    "SC32": ("临时回放冲突", "最终无重复", "事件时间线", "等待队列"),
    "SC33": ("UK", "REPLACE/IODKU", "回放记录", "回执"),
    "SC34": ("排除契约", "真实重复", "原子性", "提交证据"),
    "SC35": ("MDL", "取消", "旧快照", "残留锁清单"),
    "SC36": ("XA", "PREPARED", "COMMIT/ROLLBACK", "MDL", "回执"),
    "SC37": ("容量", "越限", "row log", "四轮", "负载时间线"),
    "SC38": ("持久化证据", "成功回执", "恢复 schema", "提交账本"),
    "SC39": ("二次故障", "恢复回滚", "清理幂等", "恢复日志"),
    "SC40": ("目标调用", "分配点", "注入回执", "配额恢复记录"),
    "SC41": ("日志顺序", "提交位点", "BIGINT/DECIMAL/HEX", "复制追平"),
    "SC42": ("切换记录", "新主", "原主回归", "提交账本"),
    "SC43": ("备份清单", "恢复目标", "点位结构", "事务账本"),
    "SC44": ("丢响应位置", "幂等键", "旧句柄", "提交记录"),
    "SC45": ("无 DDL", "SHARED", "延迟分布", "原始采样"),
    "SC46": ("每轮源定义", "资源趋势", "时间序列", "临时对象"),
    "SC47": ("阿里支持我方不支持", "增强", "缺陷复现包", "错误日志"),
    "SC48": ("INSTANT", "范围外", "不计当前 PASS", "执行清单"),
}


class XMindModelApiTests(unittest.TestCase):
    def test_xmind_model_api_is_available(self):
        functions = (
            load_xmind,
            walk_topic,
            topic_note,
            scene_id,
            find_scenes,
            source_stats,
        )
        self.assertTrue(all(callable(function) for function in functions),
                        "xmind_model parser API is not implemented")


@unittest.skipIf(load_xmind is None, "xmind_model parser API is not implemented")
class XMindModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workbook = load_xmind(SOURCE_XMIND)

    @staticmethod
    def _synthetic_workbook(numbers):
        scenes = []
        for position, number in enumerate(numbers):
            scene = f"SC{number:02d}"
            scenes.append({
                "class": "topic",
                "id": f"topic-{scene}-{position}",
                "title": f"Synthetic scene [{scene} · P0]",
                "children": {"attached": [
                    {
                        "class": "topic",
                        "id": f"topic-{scene}-{position}-section-{section}",
                        "title": f"{section} section",
                    }
                    for section in range(1, 8)
                ]},
            })
        return [{
            "class": "sheet",
            "id": "synthetic-sheet",
            "title": "Synthetic scenes",
            "rootTopic": {
                "class": "topic",
                "id": "synthetic-root",
                "title": "Synthetic root",
                "children": {"attached": scenes},
            },
        }]

    def test_load_preserves_source_workbook_and_topic_order(self):
        with zipfile.ZipFile(SOURCE_XMIND) as archive:
            source_content = json.loads(archive.read("content.json"))
        self.assertEqual(source_content, self.workbook)
        self.assertEqual([
            "01 测试点（逐项通俗说明）",
            "02 综合场景（由简到繁）",
            "03 附录（原用例与检查点）",
        ], [sheet["title"] for sheet in self.workbook])
        self.assertEqual([
            "RDS MySQL 8.0.45\n测试点 · 逐项通俗说明版",
            "RDS MySQL 8.0.45\n综合场景 · 48 组",
            "追溯附录\n1602 用例 · 302 检查点 · 155 语法",
        ], [sheet["rootTopic"]["title"] for sheet in self.workbook])

    def test_walk_topic_and_topic_note_cover_the_source_model(self):
        topics = [
            topic
            for sheet in self.workbook
            for topic in walk_topic(sheet["rootTopic"])
        ]
        self.assertEqual(7317, len(topics))
        self.assertEqual(7317, len({topic["id"] for topic in topics}))
        self.assertIn("本轮仅 INPLACE 在线修改列类型",
                      topic_note(self.workbook[0]["rootTopic"]))
        linked = next(topic for topic in topics if topic.get("href"))
        self.assertEqual("xmind:#c67b1b61153f536b865032242f82032a",
                         linked["href"])
        self.assertEqual("", topic_note({"id": "no-note", "title": "No note"}))

    def test_find_scenes_returns_source_order_priority_and_original_sections(self):
        scenes = find_scenes(self.workbook)
        self.assertEqual([f"SC{number:02d}" for number in range(1, 49)],
                         [scene["scene_id"] for scene in scenes])
        self.assertEqual({"P0": 44, "P1": 3, "P2": 1}, {
            priority: sum(scene["priority"] == priority for scene in scenes)
            for priority in ("P0", "P1", "P2")
        })
        for scene in scenes:
            self.assertEqual({
                "scene_id", "priority", "title", "topic_id", "notes",
                "references", "sections",
            }, set(scene))
            self.assertEqual(7, len(scene["sections"]), scene["scene_id"])
            self.assertEqual(
                [str(section) for section in range(1, 8)],
                [topic["title"].split(maxsplit=1)[0]
                 for topic in scene["sections"]],
                scene["scene_id"],
            )
        self.assertEqual("SC01", scene_id({"title": scenes[0]["title"]}))
        self.assertIsNone(scene_id({"title": "not a scenario"}))

    def test_scene_id_requires_one_complete_trailing_header(self):
        self.assertEqual(
            "SC01",
            scene_id({"title": "参考 [SC02] Real scene [SC01 · P0]"}),
        )
        for title in (
                "参考 [SC01]",
                "Scene [SC01 · P0] trailing text",
                "Scene [SC01 · P3]",
                "Scene [SC01 · P0",
                "Scene SC01 · P0]",
        ):
            with self.subTest(title=title):
                self.assertIsNone(scene_id({"title": title}))

    def test_find_scenes_does_not_confuse_swapped_prefixed_references(self):
        workbook = self._synthetic_workbook(range(1, 49))
        topics = workbook[0]["rootTopic"]["children"]["attached"]
        topics[0]["title"] = f"前置参考 [SC02] {topics[0]['title']}"
        topics[1]["title"] = f"前置参考 [SC01] {topics[1]['title']}"
        self.assertEqual(
            [f"SC{number:02d}" for number in range(1, 49)],
            [scene["scene_id"] for scene in find_scenes(workbook)],
        )

    def test_find_scenes_ignores_a_plain_scene_reference_leaf(self):
        workbook = self._synthetic_workbook(range(1, 49))
        workbook[0]["rootTopic"]["children"]["attached"].append({
            "class": "topic",
            "id": "plain-reference",
            "title": "参考 [SC01]",
        })
        self.assertEqual(
            [f"SC{number:02d}" for number in range(1, 49)],
            [scene["scene_id"] for scene in find_scenes(workbook)],
        )

    def test_walk_topic_requires_well_formed_attached_children(self):
        empty_topics = [
            {"id": "no-children", "title": "No children"},
            {"id": "no-attached", "title": "No attached", "children": {}},
        ]
        for topic in empty_topics:
            with self.subTest(topic=topic["id"]):
                self.assertEqual([topic], list(walk_topic(topic)))

        malformed = [
            (
                {"id": "bad-children", "title": "Bad children", "children": []},
                r"bad-children.*Bad children.*children.*dict",
            ),
            (
                {
                    "id": "bad-attached",
                    "title": "Bad attached",
                    "children": {"attached": {}},
                },
                r"bad-attached.*Bad attached.*attached.*list",
            ),
            (
                {
                    "id": "bad-child-item",
                    "title": "Bad child item",
                    "children": {"attached": [None]},
                },
                r"bad-child-item.*Bad child item.*attached.*dict",
            ),
        ]
        for topic, message in malformed:
            with self.subTest(topic=topic["id"]):
                with self.assertRaisesRegex(ValueError, message):
                    list(walk_topic(topic))

    def test_find_scenes_preserves_non_numeric_source_order(self):
        source_order = [2, 1, *range(3, 49)]
        scenes = find_scenes(self._synthetic_workbook(source_order))
        self.assertEqual(
            [f"SC{number:02d}" for number in source_order],
            [scene["scene_id"] for scene in scenes],
        )

    def test_scene_notes_and_references_preserve_source_content_and_order(self):
        scene = find_scenes(self.workbook)[0]
        self.assertIn("优先级：P0", scene["notes"])
        self.assertTrue(scene["references"])
        self.assertEqual({
            "topic_id": "07bf687c05bf562b924d529ddde87b88",
            "title": "表类型",
            "href": "xmind:#b05ef04946a05825ad640665d6fe4eb6",
        }, scene["references"][0])
        self.assertTrue(all(
            set(reference) == {"topic_id", "title", "href"}
            for reference in scene["references"]
        ))

        source_topic = next(
            topic
            for sheet in self.workbook
            for topic in walk_topic(sheet["rootTopic"])
            if topic["id"] == scene["topic_id"]
        )
        expected_references = [
            {
                "topic_id": topic["id"],
                "title": topic["title"],
                "href": topic["href"],
            }
            for topic in walk_topic(source_topic)
            if topic.get("href")
        ]
        self.assertEqual(expected_references, scene["references"])

    def test_nested_references_keep_source_order_and_duplicate_entries(self):
        workbook = self._synthetic_workbook(range(1, 49))
        topic = workbook[0]["rootTopic"]["children"]["attached"][0]
        topic["href"] = "xmind:#scene"
        first_section, second_section = topic["children"]["attached"][:2]
        first_section.update({
            "id": "duplicate-topic",
            "title": "Repeated reference",
            "href": "xmind:#same-target",
            "children": {"attached": [
                {
                    "id": "branch",
                    "title": "Branch without reference",
                    "children": {"attached": [{
                        "id": "nested-topic",
                        "title": "Nested reference",
                        "href": "xmind:#nested-target",
                    }]},
                },
                {
                    "id": "duplicate-topic",
                    "title": "Repeated reference",
                    "href": "xmind:#same-target",
                },
            ]},
        })
        second_section["href"] = "xmind:#second-section"

        self.assertEqual([
            {
                "topic_id": "topic-SC01-0",
                "title": "Synthetic scene [SC01 · P0]",
                "href": "xmind:#scene",
            },
            {
                "topic_id": "duplicate-topic",
                "title": "Repeated reference",
                "href": "xmind:#same-target",
            },
            {
                "topic_id": "nested-topic",
                "title": "Nested reference",
                "href": "xmind:#nested-target",
            },
            {
                "topic_id": "duplicate-topic",
                "title": "Repeated reference",
                "href": "xmind:#same-target",
            },
            {
                "topic_id": "topic-SC01-0-section-2",
                "title": "2 section",
                "href": "xmind:#second-section",
            },
        ], find_scenes(workbook)[0]["references"])

    def test_source_stats_match_the_known_v3_counts(self):
        self.assertEqual({
            "sheets": 3,
            "topics": 7317,
            "scenes": 48,
            "priorities": {"P0": 44, "P1": 3, "P2": 1},
        }, source_stats(self.workbook))

    def test_load_rejects_a_corrupt_zip_with_a_clear_value_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "corrupt.xmind"
            path.write_bytes(b"this is not a ZIP archive")
            with self.assertRaisesRegex(ValueError, "invalid XMind ZIP"):
                load_xmind(path)

    def test_load_rejects_an_archive_without_content_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing-content.xmind"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("metadata.json", "{}")
            with self.assertRaisesRegex(ValueError, "missing content.json"):
                load_xmind(path)

    def test_find_scenes_rejects_duplicate_scene_ids(self):
        workbook = self._synthetic_workbook([*range(1, 49), 1])
        with self.assertRaisesRegex(ValueError, "duplicate scene ID: SC01"):
            find_scenes(workbook)

    def test_find_scenes_rejects_missing_scene_ids(self):
        workbook = self._synthetic_workbook(range(1, 48))
        with self.assertRaisesRegex(ValueError, "missing scene IDs: SC48"):
            find_scenes(workbook)


class RendererApiTests(unittest.TestCase):
    def test_renderer_public_api_is_available(self):
        functions = (
            md_text,
            md_anchor,
            render_factor_table,
            render_observations,
            render_global_scope,
            render_factor_catalog,
            render_scene,
            render_source_appendix,
            render_document,
        )
        self.assertTrue(all(callable(function) for function in functions),
                        "render_markdown API is not implemented")

    def test_raw_block_and_topic_tree_indent_every_commonmark_line(self):
        self.assertEqual([
            "    **notes：**",
            "    ",
            "    ````text",
            "    first",
            "    ```",
            "    last",
            "    ````",
        ], _raw_block("notes", "first\n```\nlast", indent="    "))

        topic = {
            "id": "root",
            "title": "Root",
            "notes": {"plain": {"content": "root line 1\nroot line 2"}},
            "children": {"attached": [{
                "id": "child",
                "title": "Child",
                "notes": {"plain": {"content": "child note"}},
            }]},
        }
        self.assertEqual("\n".join([
            "- 标题：Root",
            "  - 原始 ID：`root`",
            "    **topic root notes：**",
            "    ",
            "    ```text",
            "    root line 1",
            "    root line 2",
            "    ```",
            "  - 原始 href：（无）",
            "  - 标题：Child",
            "    - 原始 ID：`child`",
            "      **topic child notes：**",
            "      ",
            "      ```text",
            "      child note",
            "      ```",
            "    - 原始 href：（无）",
        ]), _render_topic_tree([topic]))

    def test_walk_with_depth_is_iterative_and_preserves_deep_dfs_order(self):
        root = {"id": "topic-0000", "title": "0"}
        current = root
        for number in range(1, 1501):
            child = {"id": f"topic-{number:04d}", "title": str(number)}
            current["children"] = {"attached": [child]}
            current = child

        visited = list(_walk_with_depth(root))
        self.assertEqual(1501, len(visited))
        self.assertEqual(("topic-0000", 0), (visited[0][0]["id"], visited[0][1]))
        self.assertEqual(("topic-1500", 1500), (visited[-1][0]["id"], visited[-1][1]))


@unittest.skipIf(render_document is None, "render_markdown API is not implemented")
class MarkdownRendererTests(unittest.TestCase):
    SCENE_SECTION_HEADINGS = (
        "场景目标",
        "前置条件",
        "覆盖因子",
        "子运行组合",
        "执行步骤",
        "观测点",
        "预期结果与验收",
        "来源与追溯",
    )

    @classmethod
    def setUpClass(cls):
        cls.workbook = load_xmind(SOURCE_XMIND)
        cls.scenes = find_scenes(cls.workbook)
        cls.document = render_document(cls.workbook)

    @classmethod
    def _scene_block(cls, identifier):
        match = re.search(rf"(?m)^### {identifier} .+ \[P[012]\]$", cls.document)
        if match is None:
            raise AssertionError(f"missing scene heading: {identifier}")
        next_scene = re.search(r"(?m)^### SC\d{2} .+ \[P[012]\]$",
                               cls.document[match.end():])
        end = (match.end() + next_scene.start()) if next_scene else cls.document.index(
            "## 完整 3-Sheet 来源附录", match.end())
        return cls.document[match.start():end]

    def test_markdown_helpers_are_deterministic_and_safe_for_tables(self):
        self.assertEqual("a\\|b<br>c", md_text("a|b\nc"))
        self.assertEqual("dimension-b01", md_anchor(" Dimension B01 "))

    def test_cli_paths_are_the_requested_absolute_paths(self):
        self.assertEqual(SOURCE_XMIND, RENDER_SOURCE_XMIND)
        self.assertEqual(
            SOURCE_XMIND.with_name(
                "RDS_MySQL_8.0.45_测试计划_V4_场景化完整覆盖版.md"
            ),
            RENDER_OUTPUT_MARKDOWN,
        )

    def test_document_sections_scenes_and_factor_rows_have_exact_counts(self):
        expected_sections = (
            "# RDS MySQL 8.0.45 测试计划 V4 · 场景化完整覆盖版",
            "## 范围",
            "## 全局前置条件",
            "## 96 维度目录",
            "## 48 综合场景",
            "## 完整 3-Sheet 来源附录",
            "## 完整性摘要",
        )
        positions = [self.document.index(heading) for heading in expected_sections]
        self.assertEqual(sorted(positions), positions)

        headings = re.findall(
            r"(?m)^### (SC\d{2}) (.+) \[(P[012])\]$", self.document
        )
        self.assertEqual([f"SC{number:02d}" for number in range(1, 49)],
                         [identifier for identifier, _, _ in headings])
        self.assertEqual(384, len(re.findall(r"(?m)^#### ", self.document)))
        for identifier, _, _ in headings:
            block = self._scene_block(identifier)
            self.assertEqual(
                list(self.SCENE_SECTION_HEADINGS),
                re.findall(r"(?m)^#### (.+)$", block),
                identifier,
            )
            for category in FACTOR_CATEGORIES:
                self.assertEqual(1, block.count(f"| {md_text(category)} |"),
                                 (identifier, category))

    def test_factor_and_observation_tables_are_explicit(self):
        policy = SCENARIO_POLICIES["SC01"]
        factors = render_factor_table(policy)
        self.assertIn(
            "| 因子类别 | 覆盖要求 | 具体范围或例外 | 执行策略 |",
            factors,
        )
        self.assertEqual(9, sum(
            factors.count(f"| {md_text(category)} |")
            for category in FACTOR_CATEGORIES
        ))
        observations = render_observations(policy)
        for point in policy["observation_points"]:
            self.assertIn(
                f"- **{md_text(point['object'])}**："
                f"证据：{md_text(point['evidence'])}；"
                f"判定：{md_text(point['decision'])}",
                observations,
            )

    def test_global_scope_explains_complete_coverage_without_cartesian_product(self):
        scope = render_global_scope(self.workbook)
        for term in (
                "全部覆盖",
                "全局因子目录中所有兼容且适用的取值",
                "不做无意义的全笛卡尔积",
                "不适用/例外/专属子运行须显式说明",
        ):
            self.assertIn(term, scope)

    def test_sc01_preserves_all_seven_source_sections_note_id_and_references(self):
        source = self.scenes[0]
        block = self._scene_block("SC01")
        self.assertIn(source["topic_id"], block)
        self.assertIn(source["notes"], block)
        for section in source["sections"]:
            for topic in walk_topic(section):
                self.assertIn(md_text(topic["title"]), block)
                note = topic_note(topic)
                if note:
                    for note_line in note.splitlines():
                        self.assertIn(note_line, block)
                if topic.get("href"):
                    self.assertIn(topic["href"], block)
        for reference in source["references"]:
            self.assertIn(reference["topic_id"], block)
            self.assertIn(reference["href"], block)

    def test_factor_catalog_has_96_unique_dimensions_and_direct_values(self):
        anchors = re.findall(
            r'<a id="dimension-([a-z]\d{2})"></a>', self.document
        )
        self.assertEqual(96, len(anchors))
        self.assertEqual(96, len(set(anchors)))
        catalog = render_factor_catalog(self.workbook)
        dimension = next(
            topic for topic in walk_topic(self.workbook[0]["rootTopic"])
            if "维度编号：B02" in topic_note(topic)
        )
        self.assertIn(md_text(dimension["title"]), catalog)
        self.assertIn(topic_note(dimension), catalog)
        for value in dimension["children"]["attached"]:
            self.assertIn(md_text(value["title"]), catalog)
            for note_line in topic_note(value).splitlines():
                self.assertIn(note_line, catalog)
            if value.get("href"):
                self.assertIn(value["href"], catalog)

    def test_factor_catalog_distinguishes_18_subcategories_and_36_actual_values(self):
        dimensions = {}
        for topic in walk_topic(self.workbook[0]["rootTopic"]):
            match = re.search(
                r"(?m)^维度编号：\s*([A-I]\d{2})\s*$", topic_note(topic)
            )
            if match:
                dimensions[match.group(1)] = topic
        self.assertEqual(96, len(dimensions))

        expected_nested_counts = {
            "C08": 9,
            "C09": 7,
            "C13": 7,
            "C14": 8,
            "C19": 5,
        }
        containers = []
        nested_values = []
        executable_values = []
        for dimension_id, dimension in dimensions.items():
            dimension_nested = []
            direct_values = dimension.get("children", {}).get("attached", [])
            for direct_position, value in enumerate(direct_values, start=1):
                note = topic_note(value)
                if "本维度：" in note and "子分类：" in note:
                    containers.append((dimension_id, direct_position, value))
                    actual_values = value.get("children", {}).get("attached", [])
                    for actual_position, actual_value in enumerate(actual_values, start=1):
                        record = (
                            dimension_id,
                            direct_position,
                            actual_position,
                            actual_value,
                        )
                        nested_values.append(record)
                        dimension_nested.append(record)
                        executable_values.append(actual_value)
                else:
                    executable_values.append(value)
            if dimension_id in expected_nested_counts:
                self.assertEqual(
                    expected_nested_counts[dimension_id],
                    len(dimension_nested),
                    dimension_id,
                )
            else:
                self.assertEqual([], dimension_nested, dimension_id)

        self.assertEqual(18, len(containers))
        self.assertEqual(36, len(nested_values))
        self.assertEqual(515, len(executable_values))

        catalog = render_factor_catalog(self.workbook)
        self.assertEqual(
            18,
            len(re.findall(r"(?m)^- 子分类 \d+：", catalog)),
        )
        self.assertEqual(
            36,
            len(re.findall(r"(?m)^  - 实际取值 \d+\.\d+：", catalog)),
        )
        self.assertEqual(
            515,
            len(re.findall(r"(?m)^\s*- (?:直接取值|实际取值) ", catalog)),
        )

        for dimension_id, position, container in containers:
            self.assertIn(
                f"- 子分类 {position}：{md_text(container['title'])}", catalog
            )
            self.assertIn(
                f"  - 原始 ID：`{md_text(container['id'])}`", catalog
            )
            for note_line in topic_note(container).splitlines():
                self.assertIn(f"    {note_line}", catalog)
        for dimension_id, parent_position, position, value in nested_values:
            self.assertIn(
                f"  - 实际取值 {parent_position}.{position}："
                f"{md_text(value['title'])}",
                catalog,
            )
            self.assertIn(f"    - 原始 ID：`{md_text(value['id'])}`", catalog)
            for note_line in topic_note(value).splitlines():
                self.assertIn(f"      {note_line}", catalog)

    def test_supplemental_dimensions_are_linked_by_id_and_name(self):
        expected = {
            "SC01": (("B02", "存储引擎"),),
            "SC25": (("B08", "列数量"),),
            "SC46": (("B09", "表历史"),),
            "SC31": (("B10", "数据页状态"),),
            "SC13": (("D07", "索引数量"), ("D22", "索引之间的覆盖关系")),
        }
        self.assertEqual({
            "SC01": ("B02",),
            "SC25": ("B08",),
            "SC46": ("B09",),
            "SC31": ("B10",),
            "SC13": ("D07", "D22"),
        }, SUPPLEMENTAL_DIMENSIONS_BY_SCENE)
        for identifier, dimensions in expected.items():
            block = self._scene_block(identifier)
            coverage = block.split("#### 覆盖因子", maxsplit=1)[1].split(
                "#### 子运行组合", maxsplit=1
            )[0]
            traceability = block.split("#### 来源与追溯", maxsplit=1)[1]
            for dimension_id, title in dimensions:
                link = f"[{dimension_id} {title}](#dimension-{dimension_id.lower()})"
                self.assertIn(link, coverage)
                self.assertIn(link, traceability)

    def test_scene_coverage_dimension_union_is_exactly_the_96_catalog_dimensions(self):
        catalog_ids = set(re.findall(
            r'<a id="dimension-([a-i]\d{2})"></a>',
            render_factor_catalog(self.workbook),
        ))
        self.assertEqual(96, len(catalog_ids))

        linked_ids = set()
        for scene_number in range(1, 49):
            block = self._scene_block(f"SC{scene_number:02d}")
            coverage = block.split("#### 覆盖因子", maxsplit=1)[1].split(
                "#### 子运行组合", maxsplit=1
            )[0]
            links = re.findall(
                r"\[([A-I]\d{2}) [^\]]+\]\(#dimension-([a-i]\d{2})\)",
                coverage,
            )
            self.assertTrue(links, f"SC{scene_number:02d}")
            for label_id, target_id in links:
                self.assertEqual(label_id.lower(), target_id)
                self.assertIn(target_id, catalog_ids)
                linked_ids.add(target_id)
        self.assertEqual(catalog_ids, linked_ids)

    def test_source_appendix_has_every_topic_anchor_once_and_all_sheet_roots(self):
        anchors = re.findall(r'<a id="topic-([^"]+)"></a>', self.document)
        self.assertEqual(7317, len(anchors))
        self.assertEqual(7317, len(set(anchors)))
        appendix = render_source_appendix(self.workbook)
        self.assertEqual(3, len(re.findall(r"(?m)^### Sheet \d+: ", appendix)))
        for sheet in self.workbook:
            self.assertIn(md_text(sheet["title"]), appendix)
            self.assertIn(md_text(sheet["rootTopic"]["title"]), appendix)
            self.assertIn(sheet["rootTopic"]["id"], appendix)
            note = topic_note(sheet["rootTopic"])
            if note:
                self.assertIn(note, appendix)

    def test_source_appendix_preserves_nested_fields_and_converts_internal_links(self):
        workbook = [{
            "id": "sheet-one",
            "title": "Sheet | one",
            "rootTopic": {
                "id": "root-one",
                "title": "Root\nTitle",
                "notes": {"plain": {"content": "root note\nline two"}},
                "href": "xmind:#child-one",
                "children": {"attached": [{
                    "id": "child-one",
                    "title": "Child | title",
                    "notes": {"plain": {"content": "child note"}},
                    "href": "https://example.invalid/reference",
                }]},
            },
        }]
        appendix = render_source_appendix(workbook)
        self.assertIn('<a id="topic-root-one"></a>', appendix)
        self.assertIn('<a id="topic-child-one"></a>', appendix)
        self.assertIn("Root<br>Title", appendix)
        self.assertIn("root note\nline two", appendix)
        self.assertIn("[xmind:#child-one](#topic-child-one)", appendix)
        self.assertIn("Child \\| title", appendix)
        self.assertIn("child note", appendix)
        self.assertIn("https://example.invalid/reference", appendix)

    def test_every_internal_link_has_a_rendered_target(self):
        anchors = set(re.findall(r'<a id="([^"]+)"></a>', self.document))
        links = re.findall(r"\]\(#([^)]+)\)", self.document)
        self.assertTrue(links)
        self.assertEqual(set(), set(links) - anchors)

    def test_render_is_deterministic_and_has_exactly_one_trailing_newline(self):
        second = render_document(self.workbook)
        self.assertEqual(self.document, second)
        self.assertTrue(self.document.endswith("\n"))
        self.assertFalse(self.document.endswith("\n\n"))
        for term in ("3 张 Sheet", "96 个维度", "48 个场景", "7317 个 topic",
                     "384 个场景小节"):
            self.assertIn(term, self.document)


class MarkdownVerifierApiTests(unittest.TestCase):
    def test_verifier_public_api_is_available(self):
        self.assertTrue(callable(verify), "verify_markdown API is not implemented")
        self.assertEqual(
            "8e2b1b212c52eb8c9456b83cba66dfcb8a9e2e85430addb376b270e6e4ced978",
            EXPECTED_SOURCE_SHA256,
        )


@unittest.skipIf(verify is None, "verify_markdown API is not implemented")
class MarkdownVerifierTests(unittest.TestCase):
    CANONICAL_ERROR = "Markdown 与来源和场景策略的规范确定性渲染不一致"
    REPORT_KEYS = {
        "source_sha256",
        "source_unchanged",
        "sheet_count",
        "topic_count",
        "scenario_count",
        "scenario_priorities",
        "dimension_count",
        "original_check_count",
        "original_case_count",
        "syntax_count",
        "common_factor_count",
        "contract_count",
        "missing_required_sections",
        "missing_source_ids",
        "unmapped_dimension_ids",
        "duplicate_scene_ids",
        "broken_internal_links",
        "placeholder_hits",
        "errors",
    }

    @classmethod
    def setUpClass(cls):
        cls.workbook = load_xmind(SOURCE_XMIND)
        cls.document = render_document(cls.workbook)
        cls.report = verify(SOURCE_XMIND, cls.document)

    def _assert_rejected(self, markdown_text):
        report = verify(SOURCE_XMIND, markdown_text)
        self.assertEqual(self.REPORT_KEYS, set(report))
        self.assertTrue(report["errors"], report)
        return report

    def _assert_canonical_rejected(self, markdown_text):
        report = self._assert_rejected(markdown_text)
        self.assertIn(self.CANONICAL_ERROR, report["errors"])
        return report

    @staticmethod
    def _scene_bounds(document, identifier, next_identifier):
        start = document.index(f"### {identifier} ")
        end = document.index(f"### {next_identifier} ", start)
        return start, end

    def test_complete_render_is_accepted_with_exact_independent_source_counts(self):
        self.assertEqual(self.REPORT_KEYS, set(self.report))
        self.assertEqual(EXPECTED_SOURCE_SHA256, self.report["source_sha256"])
        self.assertTrue(self.report["source_unchanged"])
        self.assertEqual(3, self.report["sheet_count"])
        self.assertEqual(7317, self.report["topic_count"])
        self.assertEqual(48, self.report["scenario_count"])
        self.assertEqual(
            {"P0": 44, "P1": 3, "P2": 1},
            self.report["scenario_priorities"],
        )
        self.assertEqual(96, self.report["dimension_count"])
        self.assertEqual(302, self.report["original_check_count"])
        self.assertEqual(1602, self.report["original_case_count"])
        self.assertEqual(155, self.report["syntax_count"])
        self.assertEqual(35, self.report["common_factor_count"])
        self.assertEqual(16, self.report["contract_count"])
        for key in (
                "missing_required_sections", "missing_source_ids",
                "unmapped_dimension_ids", "duplicate_scene_ids",
                "broken_internal_links", "placeholder_hits", "errors"):
            self.assertEqual([], self.report[key], key)

    def test_missing_scene_section_is_rejected(self):
        mutated = self.document.replace("#### 观测点", "#### 观测点已删除", 1)
        report = self._assert_rejected(mutated)
        self.assertIn("SC01:观测点", report["missing_required_sections"])

    def test_missing_source_topic_anchor_is_rejected(self):
        topic_id = self.workbook[0]["rootTopic"]["id"]
        anchor = f'<a id="topic-{topic_id}"></a>'
        self.assertEqual(1, self.document.count(anchor))
        report = self._assert_rejected(self.document.replace(anchor, "", 1))
        self.assertIn(topic_id, report["missing_source_ids"])

    def test_extra_topic_anchor_is_rejected(self):
        report = self._assert_rejected(
            self.document + '\n<a id="topic-not-from-source"></a>\n'
        )
        self.assertTrue(any("额外 topic anchor" in error
                            and "topic-not-from-source" in error
                            for error in report["errors"]), report["errors"])

    def test_extra_dimension_anchor_is_rejected(self):
        report = self._assert_rejected(
            self.document + '\n<a id="dimension-a99"></a>\n'
        )
        self.assertTrue(any("额外 dimension anchor" in error
                            and "dimension-a99" in error
                            for error in report["errors"]), report["errors"])

    def test_empty_observation_evidence_is_rejected(self):
        mutated, changes = re.subn(
            r"(?m)^(- \*\*[^*]+\*\*：证据：)[^；]+(；判定：[^\n]+)$",
            r"\1\2",
            self.document,
            count=1,
        )
        self.assertEqual(1, changes)
        report = self._assert_rejected(mutated)
        self.assertTrue(any("SC01" in error and "观测" in error
                            for error in report["errors"]), report["errors"])

    def test_explicit_placeholder_is_rejected_without_false_positive_for_source_term(self):
        self.assertIn("待补变化", self.document)
        self.assertEqual([], self.report["placeholder_hits"])
        report = self._assert_rejected(self.document + "\nTODO：待填写 {{value}}\n")
        self.assertIn("TODO", report["placeholder_hits"])
        self.assertIn("待填写", report["placeholder_hits"])
        self.assertIn("{{value}}", report["placeholder_hits"])

    def test_duplicate_scene_heading_is_rejected(self):
        heading = re.search(r"(?m)^### SC01 .+ \[P0\]$", self.document).group(0)
        mutated = self.document.replace(heading, f"{heading}\n{heading}", 1)
        report = self._assert_rejected(mutated)
        self.assertIn("SC01", report["duplicate_scene_ids"])

    def test_removed_b02_scene_mapping_is_rejected(self):
        link = "[B02 存储引擎](#dimension-b02)"
        self.assertGreaterEqual(self.document.count(link), 2)
        mutated = self.document.replace(link, "B02 存储引擎", 1)
        report = self._assert_rejected(mutated)
        self.assertIn("B02", report["unmapped_dimension_ids"])

    def test_unknown_a99_scene_mapping_with_matching_anchor_is_rejected(self):
        scene_start = self.document.index("### SC01 ")
        insertion = self.document.index("#### 子运行组合", scene_start)
        mutated = (
            self.document[:insertion]
            + "- 伪造维度：[A99 非来源维度](#dimension-a99)\n"
            + '<a id="dimension-a99"></a>\n\n'
            + self.document[insertion:]
        )
        report = self._assert_rejected(mutated)
        self.assertTrue(any("A99" in error and "源 96 维度" in error
                            for error in report["errors"]), report["errors"])

    def test_deleted_sc01_factor_row_is_canonically_rejected(self):
        start, end = self._scene_bounds(self.document, "SC01", "SC02")
        scene = self.document[start:end]
        changed_scene, changes = re.subn(
            r"(?m)^\| 环境与功能范围 \|.*\n",
            "",
            scene,
            count=1,
        )
        self.assertEqual(1, changes)
        self._assert_canonical_rejected(
            self.document[:start] + changed_scene + self.document[end:]
        )

    def test_changed_sc01_factor_category_is_canonically_rejected(self):
        start, end = self._scene_bounds(self.document, "SC01", "SC02")
        scene = self.document[start:end]
        changed_scene = scene.replace(
            "| 环境与功能范围 |", "| 被篡改的因子类别 |", 1
        )
        self.assertNotEqual(scene, changed_scene)
        self._assert_canonical_rejected(
            self.document[:start] + changed_scene + self.document[end:]
        )

    def test_removed_topic_source_fields_with_anchor_retained_is_canonically_rejected(self):
        topic_id = self.workbook[0]["rootTopic"]["id"]
        anchor = f'<a id="topic-{topic_id}"></a>'
        start = self.document.index(anchor)
        end = self.document.index('<a id="topic-', start + len(anchor))
        original = self.document[start:end]
        id_line = next(
            line for line in original.splitlines() if "原始 ID：" in line
        )
        replacement = f"{anchor}\n- Topic 来源字段已删除\n{id_line}\n\n"
        mutated = self.document[:start] + replacement + self.document[end:]
        self.assertEqual(1, mutated.count(anchor))
        self._assert_canonical_rejected(mutated)

    def test_changed_sc01_title_is_canonically_rejected(self):
        mutated, changes = re.subn(
            r"(?m)^### SC01 .+ \[P0\]$",
            "### SC01 被篡改但格式合法的标题 [P0]",
            self.document,
            count=1,
        )
        self.assertEqual(1, changes)
        self._assert_canonical_rejected(mutated)

    def test_swapped_sc01_sc02_blocks_are_canonically_rejected(self):
        sc01_start, sc02_start = self._scene_bounds(self.document, "SC01", "SC02")
        _, sc03_start = self._scene_bounds(self.document, "SC02", "SC03")
        sc01 = self.document[sc01_start:sc02_start]
        sc02 = self.document[sc02_start:sc03_start]
        mutated = (
            self.document[:sc01_start] + sc02 + sc01 + self.document[sc03_start:]
        )
        self._assert_canonical_rejected(mutated)

    def test_broken_observation_bold_markup_is_canonically_rejected(self):
        start, end = self._scene_bounds(self.document, "SC01", "SC02")
        scene = self.document[start:end]
        changed_scene, changes = re.subn(
            r"(?m)^- \*\*([^*]+)\*\*：证据：",
            r"- \1：证据：",
            scene,
            count=1,
        )
        self.assertEqual(1, changes)
        self._assert_canonical_rejected(
            self.document[:start] + changed_scene + self.document[end:]
        )

    def test_five_duplicate_observations_are_canonically_rejected(self):
        start, end = self._scene_bounds(self.document, "SC01", "SC02")
        scene = self.document[start:end]
        observation_start = scene.index("#### 观测点")
        acceptance_start = scene.index("#### 预期结果与验收", observation_start)
        observation = scene[observation_start:acceptance_start]
        first_bullet = re.search(r"(?m)^- \*\*.+$", observation).group(0)
        replacement = "#### 观测点\n\n" + "\n".join([first_bullet] * 5) + "\n\n"
        changed_scene = (
            scene[:observation_start] + replacement + scene[acceptance_start:]
        )
        self._assert_canonical_rejected(
            self.document[:start] + changed_scene + self.document[end:]
        )

    def test_tampered_closing_fence_is_canonically_rejected(self):
        marker = "\n```\n\n## 全局前置条件"
        self.assertIn(marker, self.document)
        mutated = self.document.replace(
            marker, "\n~~~~\n\n## 全局前置条件", 1
        )
        self._assert_canonical_rejected(mutated)

    def test_unclosed_trailing_fence_is_canonically_rejected(self):
        self._assert_canonical_rejected(self.document + "```text\n")

    def test_html_comment_wrapped_sc01_is_canonically_rejected(self):
        start, end = self._scene_bounds(self.document, "SC01", "SC02")
        mutated = (
            self.document[:start]
            + "<!--\n"
            + self.document[start:end]
            + "-->\n"
            + self.document[end:]
        )
        self._assert_canonical_rejected(mutated)

    def test_changed_integrity_summary_is_canonically_rejected(self):
        marker = "- 7317 个 topic，且每个 topic anchor 唯一。"
        self.assertEqual(1, self.document.count(marker))
        self._assert_canonical_rejected(
            self.document.replace(marker, marker.replace("7317", "7318"), 1)
        )

    def test_deleted_nested_actual_factor_value_is_canonically_rejected(self):
        mutated, changes = re.subn(
            r"(?m)^  - 实际取值 \d+\.\d+：.*\n",
            "",
            self.document,
            count=1,
        )
        self.assertEqual(1, changes)
        self._assert_canonical_rejected(mutated)

    def test_broken_internal_link_is_rejected(self):
        report = self._assert_rejected(
            self.document + "\n[故意断链](#missing-verifier-target)\n"
        )
        self.assertIn("missing-verifier-target", report["broken_internal_links"])

    def test_valid_zip_with_changed_hash_is_rejected_after_full_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            mutated_source = Path(directory) / "changed-but-valid.xmind"
            with zipfile.ZipFile(SOURCE_XMIND) as source_archive, \
                    zipfile.ZipFile(mutated_source, "w") as target_archive:
                for entry in source_archive.infolist():
                    target_archive.writestr(entry, source_archive.read(entry.filename))
                target_archive.writestr("verification-marker.txt", "hash mutation")

            report = verify(mutated_source, self.document)

        self.assertEqual(self.REPORT_KEYS, set(report))
        self.assertNotEqual(EXPECTED_SOURCE_SHA256, report["source_sha256"])
        self.assertFalse(report["source_unchanged"])
        self.assertEqual(7317, report["topic_count"])
        self.assertEqual(1, len(report["errors"]), report["errors"])
        self.assertIn("SHA-256", report["errors"][0])
        for key in (
                "missing_required_sections", "missing_source_ids",
                "unmapped_dimension_ids", "duplicate_scene_ids",
                "broken_internal_links", "placeholder_hits"):
            self.assertEqual([], report[key], key)

    def test_main_success_atomically_writes_verification_json(self):
        self.assertTrue(callable(verify_main))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            markdown_path = root / "plan.md"
            markdown_path.write_text(self.document, encoding="utf-8")
            verification_path = root / "verification.json"
            with patch("render_markdown.SOURCE_XMIND", SOURCE_XMIND), \
                    patch("render_markdown.OUTPUT_MARKDOWN", markdown_path), \
                    patch("verify_markdown.__file__", str(root / "verify_markdown.py")), \
                    patch.object(Path, "write_text", side_effect=AssertionError(
                        "verification.json must not be written directly")), \
                    patch("builtins.print"):
                verify_main()
            report = json.loads(verification_path.read_text(encoding="utf-8"))
            self.assertEqual([], report["errors"])
            self.assertEqual([], list(root.glob("verification.json.*.tmp")))

    def test_main_missing_markdown_writes_report_and_exits_one(self):
        self.assertTrue(callable(verify_main))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            missing_markdown = root / "missing.md"
            verification_path = root / "verification.json"
            with patch("render_markdown.SOURCE_XMIND", SOURCE_XMIND), \
                    patch("render_markdown.OUTPUT_MARKDOWN", missing_markdown), \
                    patch("verify_markdown.__file__", str(root / "verify_markdown.py")), \
                    patch("builtins.print"):
                with self.assertRaises(SystemExit) as raised:
                    verify_main()
            self.assertEqual(1, raised.exception.code)
            report = json.loads(verification_path.read_text(encoding="utf-8"))
            self.assertTrue(report["errors"])
            self.assertTrue(any("无法读取 Markdown" in error
                                for error in report["errors"]), report["errors"])


class ScenarioPolicyTests(unittest.TestCase):
    def _assert_mutation_rejected(self, policies, validator, categories=FACTOR_CATEGORIES):
        # Isolate mutations from the imported production records and other tests.
        with patch(f"{__name__}.SCENARIO_POLICIES", policies), \
                patch(f"{__name__}.FACTOR_CATEGORIES", categories):
            with self.assertRaises(AssertionError):
                getattr(self, validator)()

    def test_contract_rejects_consistently_renamed_category(self):
        policies = deepcopy(SCENARIO_POLICIES)
        categories = ("错误分类",) + FACTOR_CATEGORIES[1:]
        for policy in policies.values():
            scopes = policy["factor_scopes"]
            scopes["错误分类"] = scopes.pop(FACTOR_CATEGORIES[0])
        self._assert_mutation_rejected(
            policies, "test_all_scenarios_have_complete_policies", categories)

    def test_contract_rejects_duplicate_prerequisites(self):
        policies = deepcopy(SCENARIO_POLICIES)
        policy = policies["SC01"]
        policy["prerequisites"] = [policy["prerequisites"][0]] * 4
        self._assert_mutation_rejected(
            policies, "test_scenario_text_is_not_a_shared_placeholder")

    def test_contract_rejects_generic_phrases(self):
        for phrase in ("检查正常", "正常则通过", "通用检查"):
            with self.subTest(phrase=phrase):
                policies = deepcopy(SCENARIO_POLICIES)
                policies["SC01"]["acceptance_additions"].append(phrase)
                self._assert_mutation_rejected(
                    policies, "test_scenario_text_is_not_a_shared_placeholder")

    def test_contract_rejects_numbered_placeholders(self):
        policies = deepcopy(SCENARIO_POLICIES)
        for scene_id, policy in policies.items():
            policy["goal"] = f"目标 {scene_id}"
            policy["risk"] = f"风险 {scene_id}"
            policy["prerequisites"] = [f"前置 {number}" for number in range(4)]
            for scope in policy["factor_scopes"].values():
                scope["range"] = f"范围 {scene_id}"
                scope["strategy"] = f"策略 {scene_id}"
            policy["observation_points"] = [
                {"object": f"对象 {number}", "evidence": "检查记录", "decision": "通过"}
                for number in range(5)
            ]
            policy["acceptance_additions"] = [f"验收 {scene_id}"]
        self._assert_mutation_rejected(
            policies, "test_scenario_text_is_not_a_shared_placeholder")

    def test_contract_rejects_swapped_scenario_mechanism(self):
        policies = deepcopy(SCENARIO_POLICIES)
        policies["SC01"] = deepcopy(policies["SC02"])
        # Keep the old uniqueness-only guard satisfied while replacing the mechanism.
        policies["SC01"]["goal"] += " SC01"
        policies["SC01"]["risk"] += " SC01"
        self._assert_mutation_rejected(
            policies, "test_scenario_text_is_not_a_shared_placeholder")

    def test_contract_rejects_observation_only_placeholders(self):
        policies = deepcopy(SCENARIO_POLICIES)
        policies["SC01"]["observation_points"] = [
            {"object": f"对象编号{number}", "evidence": "检查记录", "decision": "通过"}
            for number in range(5)
        ]
        self._assert_mutation_rejected(
            policies, "test_all_scenarios_have_complete_policies")

    def test_contract_rejects_short_observation_fields(self):
        for field, value in (("object", "锁"), ("evidence", "记录"), ("decision", "通过")):
            with self.subTest(field=field):
                policies = deepcopy(SCENARIO_POLICIES)
                policies["SC01"]["observation_points"][0][field] = value
                self._assert_mutation_rejected(
                    policies, "test_all_scenarios_have_complete_policies")

    def test_contract_rejects_generic_observation_fields(self):
        for field, value in (
                ("object", "观测对象编号0001"),
                ("evidence", "检查记录：测试结果符合要求"),
                ("decision", "该观测项目符合要求，判定通过")):
            with self.subTest(field=field):
                policies = deepcopy(SCENARIO_POLICIES)
                policies["SC01"]["observation_points"][0][field] = value
                self._assert_mutation_rejected(
                    policies, "test_all_scenarios_have_complete_policies")

    def test_contract_rejects_wrong_observation_mechanism(self):
        policies = deepcopy(SCENARIO_POLICIES)
        policies["SC01"]["observation_points"] = deepcopy(
            policies["SC02"]["observation_points"])
        # Keep every other SC01 field intact, including its correct mechanism words.
        self._assert_mutation_rejected(
            policies, "test_all_scenarios_have_complete_policies")

    def test_policy_rejects_malformed_factor_scope_triplets(self):
        valid_rows = ["全部覆盖 | 有效范围 | 独立子运行策略"] * len(FACTOR_CATEGORIES)
        observations = "观测对象 | 可复核的原始证据记录 | 满足明确条件才通过，否则失败"
        for malformed in (
                "全部覆盖 | 有效范围",
                "全部覆盖 | 有效范围 | 独立子运行策略 | 多余字段",
                "全部覆盖 |  | 独立子运行策略"):
            with self.subTest(malformed=malformed):
                rows = list(valid_rows)
                rows[0] = malformed
                with self.assertRaisesRegex(ValueError, "factor scope"):
                    _policy("目标", "风险", "前置条件", "\n".join(rows),
                            observations, "验收条件")

    def test_policy_rejects_malformed_observation_triplets(self):
        scopes = "\n".join(
            ["全部覆盖 | 有效范围 | 独立子运行策略"] * len(FACTOR_CATEGORIES))
        for malformed in (
                "观测对象 | 可复核的原始证据记录",
                "观测对象 | 可复核的原始证据记录 | 明确判定条件 | 多余字段",
                "观测对象 |  | 明确判定条件"):
            with self.subTest(malformed=malformed):
                with self.assertRaisesRegex(ValueError, "observation"):
                    _policy("目标", "风险", "前置条件", scopes,
                            malformed, "验收条件")

    def test_sc17_locks_sql_mode_and_statement_transaction_semantics(self):
        text = repr(SCENARIO_POLICIES["SC17"])
        for term in (
                "STRICT_TRANS_TABLES", "STRICT_ALL_TABLES", "普通非 IGNORE",
                "非严格模式", "IGNORE", "失败语句", "显式 ROLLBACK",
                "此前成功语句", "BLOCKED"):
            self.assertIn(term, text, ("SC17", term))

    def test_all_scenarios_have_complete_policies(self):
        expected = {f"SC{i:02d}" for i in range(1, 49)}
        self.assertEqual(expected, set(SCENARIO_POLICIES))
        self.assertEqual(expected, set(OBSERVATION_KEYWORDS_BY_SCENE))
        required = {
            "goal", "risk", "prerequisites", "factor_scopes",
            "observation_points", "acceptance_additions",
        }
        self.assertEqual((
            "环境与功能范围",
            "表结构、存储与物理状态",
            "列类型、属性与非目标列",
            "索引、约束与对象依赖",
            "数据值、规模与分布",
            "ALTER 语法、算法、锁与同句动作",
            "并发、事务、DDL 阶段与 row log",
            "主备、故障、恢复与客户端",
            "结构、数据、索引、性能与交付判定",
        ), FACTOR_CATEGORIES)
        for scene_id, policy in SCENARIO_POLICIES.items():
            self.assertEqual(required, set(policy), scene_id)
            self.assertTrue(policy["goal"].strip(), scene_id)
            self.assertTrue(policy["risk"].strip(), scene_id)
            self.assertTrue(policy["acceptance_additions"], scene_id)
            self.assertGreaterEqual(len(policy["prerequisites"]), 4, scene_id)
            self.assertTrue(all(item.strip() for item in policy["prerequisites"]), scene_id)
            self.assertGreaterEqual(len(policy["observation_points"]), 5, scene_id)
            self.assertEqual(set(FACTOR_CATEGORIES), set(policy["factor_scopes"]), scene_id)
            observation_text = []
            for observation in policy["observation_points"]:
                self.assertEqual({"object", "evidence", "decision"}, set(observation), scene_id)
                self.assertTrue(all(str(value).strip() for value in observation.values()), scene_id)
                for field, minimum_length in (("object", 3), ("evidence", 8), ("decision", 12)):
                    value = observation[field].strip()
                    context = (scene_id, observation["object"], field)
                    self.assertGreaterEqual(len(value), minimum_length, context)
                    self.assertNotRegex(
                        value,
                        r"^(?:观测|检查|测试)?(?:对象|项目|证据|记录|结果)(?:编号)?[\s\d:：#._-]*$",
                        context)
                    for phrase in ("检查正常", "正常则通过", "通用检查", "检查记录",
                                   "符合要求", "结果正常", "测试通过"):
                        self.assertNotIn(phrase, value, context)
                    observation_text.append(value)
                self.assertTrue(any(token in observation["decision"] for token in
                                    ("通过", "失败", "BLOCKED", "范围外")), scene_id)
                # Verdict words and punctuation are not an acceptance condition.
                condition = re.sub(r"通过|失败|BLOCKED|范围外|[\W\d_]", "",
                                   observation["decision"])
                self.assertGreaterEqual(len(condition), 4,
                                        (scene_id, observation["object"], "missing condition"))
            combined_observations = "；".join(observation_text)
            for keyword in OBSERVATION_KEYWORDS_BY_SCENE[scene_id]:
                self.assertIn(keyword, combined_observations,
                              (scene_id, "missing observation mechanism/evidence", keyword))

    def test_scope_values_are_explicit(self):
        allowed = {"全部覆盖", "指定覆盖", "边界覆盖", "专属子运行", "不适用"}
        for scene_id, policy in SCENARIO_POLICIES.items():
            for category, scope in policy["factor_scopes"].items():
                self.assertEqual({"requirement", "range", "strategy"}, set(scope), (scene_id, category))
                self.assertIn(scope["requirement"], allowed, (scene_id, category))
                self.assertTrue(scope["range"].strip(), (scene_id, category))
                self.assertTrue(scope["strategy"].strip(), (scene_id, category))

    def test_online_and_fault_runs_have_operational_bounds(self):
        bounded = [f"SC{i:02d}" for i in range(1, 48)]
        for scene_id in bounded:
            text = "；".join(SCENARIO_POLICIES[scene_id]["prerequisites"])
            for term in ("并发", "持续", "资源", "超时", "停止", "恢复", "清理"):
                self.assertIn(term, text, (scene_id, term))

    def test_scenario_text_is_not_a_shared_placeholder(self):
        self.assertEqual({f"SC{i:02d}" for i in range(1, 49)},
                         set(SCENARIO_MECHANISM_TERMS))
        for field in ("goal", "risk"):
            values = [policy[field] for policy in SCENARIO_POLICIES.values()]
            self.assertEqual(48, len(set(values)), field)
        for scene_id, policy in SCENARIO_POLICIES.items():
            prerequisites = [" ".join(item.split()) for item in policy["prerequisites"]]
            self.assertEqual(len(prerequisites), len(set(prerequisites)),
                             (scene_id, "duplicate prerequisites"))
            objects = [point["object"] for point in policy["observation_points"]]
            self.assertEqual(len(objects), len(set(objects)), scene_id)
            # Include all six policy fields, not just goal/risk or an ID suffix.
            text_parts = [policy["goal"], policy["risk"], *policy["prerequisites"],
                          *policy["acceptance_additions"]]
            for scope in policy["factor_scopes"].values():
                text_parts.extend(scope.values())
            for observation in policy["observation_points"]:
                text_parts.extend(observation.values())
            text = "；".join(text_parts)
            for phrase in ("检查正常", "正常则通过", "通用检查"):
                self.assertNotIn(phrase, text, (scene_id, "generic wording", phrase))
            for term in SCENARIO_MECHANISM_TERMS[scene_id]:
                self.assertIn(term, text, (scene_id, "missing mechanism", term))

    def test_future_scope_cannot_count_as_current_pass(self):
        policy = SCENARIO_POLICIES["SC48"]
        self.assertTrue(all(scope["requirement"] == "不适用"
                            for scope in policy["factor_scopes"].values()))
        self.assertIn("不计当前 PASS", "；".join(policy["acceptance_additions"]))


if __name__ == "__main__":
    unittest.main()
