# pg_case_factory

这个项目现在只保留一个**最小通用引擎**，并把 SQL 生成知识整理成一个标准 Codex skill。

它不再把 `create_index`、生命周期、计划链路写死在常驻 Python 里，而是把 SQL 生成知识收敛为一个标准 Codex skill：

- `skills/pg-sql-generation/SKILL.md`
  Codex skill 入口，负责触发说明和导航。
- `skills/pg-sql-generation/references/mainflow/`
  主流程 reference，指导 agent 如何从自然语言请求推导对象、statement、生命周期、计划和动态脚本。
- `skills/pg-sql-generation/references/common/`
  公共规则 reference，定义 SQL 输出风格、命名、因子组合、生命周期和验证清理策略。
- `skills/pg-sql-generation/references/statements/`
  statement reference，按 SQL category/domain 存放语句因子、默认值、渲染模板和约束。
- `skills/pg-sql-generation/references/combinations/`
  statement combination matrix，按 SQL category/domain 存放可审计的 baseline SQL
  组合。AI/runner 只能在 baseline 审计通过后追加 marked derived extensions。
- `skills/pg-sql-generation/assets/objects/`
  基础对象 SQL 模板，随 skill 一起发布。
- `src/pg_case_factory/`
  极小常驻 Python 引擎，只提供发现、加载、渲染和 `artifacts/` 管理能力。

## 当前目录

- `skills/pg-sql-generation/`
  标准 Codex skill 目录，包含 `SKILL.md`、`agents/`、`references/`、`assets/templates/` 和 `assets/objects/`。
- `src/pg_case_factory/`
  最小通用引擎。

## 引擎职责

常驻 Python 只负责：

- 搜索对象模板
- 搜索 statement reference
- 读取 reference 中的结构化 YAML
- 按因子规则展开绑定
- 渲染单条 statement SQL
- 组合统一模板 SQL 脚本
- 清空并管理 `artifacts/`

它**不负责**：

- 从自然语言里写死解析 `create_index`
- 写死生命周期
- 写死计划链路
- 写死某个 statement 的前置/后置动作

这些都应该由 agent 读取 `pg-sql-generation` skill 后动态决定。

## `pg-sql-generation` 分层约定

- `skills/pg-sql-generation/references/mainflow/generate_sql_from_request.md`
  总入口：请求识别、计划 TSV、审计、生成程序、批量 SQL。
- `skills/pg-sql-generation/references/mainflow/audit_lifecycle_plan.md`
  只审计生命周期计划是否完整、可归因、可生成。
- `skills/pg-sql-generation/references/mainflow/write_sql_program.md`
  约束生成程序如何根据计划、对象模板、statement reference、combination matrix
  和公共规则输出 SQL。
- `skills/pg-sql-generation/references/mainflow/create_statement_reference.md`
  创建或补齐 `skills/pg-sql-generation/references/statements/<category>/<domain>/<statement_key>.md`。
- `skills/pg-sql-generation/references/common/factor_policy.md`
  因子组合规则入口。
- `skills/pg-sql-generation/references/common/output_script_style.md`
  SQL 输出风格入口。
- `skills/pg-sql-generation/references/combinations/README.md`
  组合矩阵入口；正式矩阵优先于自由推理，derived extension 不能替代 required coverage。

## Python 适配状态

当前目录已经迁移为 Codex skill 标准形态，`.skill` 文件已改为 `.md` reference。常驻 Python discovery 会递归发现 `skills/pg-sql-generation/references/statements/**/*.md`，并读取分层路径中的 category/domain。
基础对象模板也已经迁移到 `skills/pg-sql-generation/assets/objects/`，discovery 会从该路径发现对象模板。

## 独立发布

如果只发布 skill，请只上传 `skills/pg-sql-generation/` 对应的目录内容，独立仓库中建议保留为：

```text
pg-sql-generation/
├── SKILL.md
├── agents/
├── references/
└── assets/
```

## artifacts 约定

每次运行前应清空 `artifacts/`，然后只保留：

- `artifacts/generated_programs/`
- `artifacts/generated_sql/`
- `artifacts/test_plans/`
- `artifacts/evaluations/`
- `artifacts/intermediates/`

## 典型用法

动态生成的 Python 批量脚本应放在 `artifacts/generated_programs/`，并调用引擎提供的函数，例如：

```python
from pg_case_factory import (
    build_bindings,
    build_name_context,
    compose_sql_script,
    discover_request_candidates,
    load_statement_skill,
    render_object_template,
    render_statement,
)
```

更多结构说明见：
[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
