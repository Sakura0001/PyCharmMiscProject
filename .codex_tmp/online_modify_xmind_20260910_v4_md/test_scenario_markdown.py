"""Contract tests for explicit, reviewable scenario coverage policies."""

import unittest

from scenario_policies import FACTOR_CATEGORIES, SCENARIO_POLICIES


class ScenarioPolicyTests(unittest.TestCase):
    def test_all_scenarios_have_complete_policies(self):
        expected = {f"SC{i:02d}" for i in range(1, 49)}
        self.assertEqual(expected, set(SCENARIO_POLICIES))
        required = {
            "goal", "risk", "prerequisites", "factor_scopes",
            "observation_points", "acceptance_additions",
        }
        self.assertEqual(9, len(FACTOR_CATEGORIES))
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
        for field in ("goal", "risk"):
            values = [policy[field] for policy in SCENARIO_POLICIES.values()]
            self.assertEqual(48, len(set(values)), field)
        for scene_id, policy in SCENARIO_POLICIES.items():
            objects = [point["object"] for point in policy["observation_points"]]
            self.assertEqual(len(objects), len(set(objects)), scene_id)

    def test_future_scope_cannot_count_as_current_pass(self):
        policy = SCENARIO_POLICIES["SC48"]
        self.assertTrue(all(scope["requirement"] == "不适用"
                            for scope in policy["factor_scopes"].values()))
        self.assertIn("不计当前 PASS", "；".join(policy["acceptance_additions"]))


if __name__ == "__main__":
    unittest.main()
