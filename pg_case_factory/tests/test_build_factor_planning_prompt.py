from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "build_factor_planning_prompt.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_factor_planning_prompt", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class BuildFactorPlanningPromptTest(unittest.TestCase):
    def test_insert_prompt_requires_factor_association_answer_shape(self):
        module = load_module()

        prompt = module.build_prompt(ROOT, "insert")

        self.assertIn("clean-context subagent", prompt)
        self.assertIn("Do not generate SQL", prompt)
        self.assertIn("Do not modify files", prompt)
        self.assertIn("skills/pg-sql-generation/references/mainflow/plan_factor_association_from_statement.md", prompt)
        self.assertIn("skills/pg-sql-generation/references/statements/dml/table/insert.md", prompt)
        self.assertIn("skills/pg-sql-generation/references/combinations/dml/table/insert.yaml", prompt)
        self.assertIn("skills/pg-sql-generation/references/common/factor_policy.md", prompt)
        self.assertIn("skills/pg-sql-generation/references/combinations/_shared/coverage_inventory.yaml", prompt)
        self.assertIn("skills/pg-sql-generation/references/common/pg16_type_catalog.md", prompt)
        self.assertIn("impact chain", prompt)
        self.assertIn("factor dimensions", prompt)
        self.assertIn("factor-to-factor trigger rules", prompt)
        self.assertIn("YAML association graph", prompt)
        self.assertIn("source attribution", prompt)
        self.assertIn("catalog facts", prompt)
        self.assertIn("derived extensions", prompt)
        self.assertIn("请使用中文", prompt)
        self.assertIn("语法形式 -> 目标对象 -> 输入数据来源 -> 列映射 -> 数据类型转换", prompt)
        self.assertIn("约束校验 -> 分区/继承/路由 -> 触发器/规则/RLS", prompt)
        self.assertIn("索引/冲突处理 -> 事务/并发 -> 存储/WAL/复制 -> 返回值与可观测结果", prompt)
        self.assertIn("如果看到目标对象是分区表", prompt)
        self.assertIn("如果看到 unique/primary key", prompt)
        self.assertIn("如果列里有 identity/generated/default", prompt)
        self.assertIn("如果有 FK/deferrable", prompt)

    def test_cli_prints_insert_prompt(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(ROOT), "--statement", "insert"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("clean-context subagent", completed.stdout)
        self.assertIn("YAML association graph", completed.stdout)
        self.assertIn("skills/pg-sql-generation/references/statements/dml/table/insert.md", completed.stdout)


if __name__ == "__main__":
    unittest.main()
