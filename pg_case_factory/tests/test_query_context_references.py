from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROMPT_SCRIPT = ROOT / "tools" / "build_factor_planning_prompt.py"


def load_prompt_module():
    spec = importlib.util.spec_from_file_location("build_factor_planning_prompt", PROMPT_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class QueryContextReferencesTest(unittest.TestCase):
    def test_query_context_policy_documents_required_query_associations(self):
        path = ROOT / "skills" / "pg-sql-generation" / "references" / "common" / "query_context_policy.md"

        text = path.read_text(encoding="utf-8")

        for required in [
            "query_context",
            "query_role",
            "query_shape",
            "data_fixture",
            "data_distribution",
            "index_context",
            "hint_context",
            "statistics_context",
            "optimizer_guc_context",
            "parameterization_context",
            "transaction_visibility_context",
            "parallel_execution_context",
            "null_semantics_context",
            "collation_context",
            "function_volatility_context",
            "rewrite_context",
            "oracle_context",
            "feature_to_query_context_rules",
            "no_hint",
            "extension_hint_available",
            "enable_seqscan",
            "generic_plan",
            "custom_plan",
            "metamorphic_equivalence",
        ]:
            self.assertIn(required, text)

    def test_select_prompt_includes_query_context_references(self):
        module = load_prompt_module()

        prompt = module.build_prompt(ROOT, "select")

        self.assertIn("references/common/query_context_policy.md", prompt)
        self.assertIn("query_context", prompt)
        self.assertIn("data_distribution", prompt)
        self.assertIn("hint_context", prompt)
        self.assertIn("optimizer_guc_context", prompt)
        self.assertIn("parameterization_context", prompt)
        self.assertIn("oracle_context", prompt)
        self.assertIn("没有 ORDER BY，不允许断言行顺序", prompt)

    def test_skill_navigation_points_to_query_context_policy(self):
        text = (ROOT / "skills" / "pg-sql-generation" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("query_context_policy.md", text)
        self.assertIn("查询", text)


if __name__ == "__main__":
    unittest.main()
