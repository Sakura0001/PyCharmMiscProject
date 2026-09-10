"""Contract tests for explicit, reviewable scenario coverage policies."""

from copy import deepcopy
import unittest
from unittest.mock import patch

from scenario_policies import FACTOR_CATEGORIES, SCENARIO_POLICIES


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

    def test_all_scenarios_have_complete_policies(self):
        expected = {f"SC{i:02d}" for i in range(1, 49)}
        self.assertEqual(expected, set(SCENARIO_POLICIES))
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
            for observation in policy["observation_points"]:
                self.assertEqual({"object", "evidence", "decision"}, set(observation), scene_id)
                self.assertTrue(all(str(value).strip() for value in observation.values()), scene_id)
                self.assertTrue(any(token in observation["decision"] for token in
                                    ("通过", "失败", "BLOCKED", "范围外")), scene_id)

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
