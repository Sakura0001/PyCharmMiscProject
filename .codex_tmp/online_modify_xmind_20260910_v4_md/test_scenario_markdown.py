"""Contract tests for explicit, reviewable scenario coverage policies."""

from copy import deepcopy
import re
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
